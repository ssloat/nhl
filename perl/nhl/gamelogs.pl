use strict;
use warnings;

use DateTime;
use DBI;
use List::MoreUtils 'uniq';
use WWW::Mechanize;
use Readonly;

Readonly my $MECH => WWW::Mechanize->new;
Readonly my $DBH  => DBI->connect("dbi:SQLite:dbname=$ARGV[0]","","", {});

MAIN: {
    my $start = _date($ARGV[1]);
    my $end   = _date($ARGV[2] // $ARGV[1]);

    my $start_ymd = $start->ymd;
    my $end_ymd   = $end->ymd;
    my $sql = <<HERE;
delete from gamelogs 
where exists (
    select 1 from games where gamelogs.game_id = games.id
        and games.date  >= '$start_ymd' and games.date <= '$end_ymd'
)
HERE
    $DBH->do($sql);
    $DBH->do("delete from games where date >= '$start_ymd' and date <= '$end_ymd'");

    my $sth = $DBH->prepare("select id from players");
    $sth->execute();
    my %players = map {$_->[0] => 1} @{$sth->fetchall_arrayref()};

    for (; $start <= $end; $start->add(days => 1)) {
        scoreboard($start, \%players);
    }
}

sub _date {
    my ($str) = @_;

    return DateTime->today if !defined $str;
    
    my ($y, $m, $d) = split /-/, $str;
    return DateTime->new(year => $y, month => $m, day => $d);
}

sub scoreboard {
    my ($date, $players) = @_;

    print $date->ymd . "\n";
    my $ymd  = $date->ymd(q{});
    my $html = $MECH->get("http://scores.espn.go.com/nhl/scoreboard?date=$ymd")->decoded_content;

    my %winners = map {$_ => 1} 
            ($html =~ m#>W: <.*?><a href="http://espn.go.com/nhl/player/_/id/(\d+)/#g);

    my @gameids;
    for my $line (split "\n", $html) {
        next if $line !~ /boxscore/;

        while ($line =~ m#/nhl/boxscore\?gameId=(\d+)#g) {
            push @gameids, $1;
        }
    }

    for my $gameid (uniq @gameids) {
        sleep 2;
        game($gameid, $date, $players, \%winners);
    }
}

sub game {
    my ($gameid, $date, $players, $winners) = @_;

    my $html = $MECH->get("http://scores.espn.go.com/nhl/boxscore?gameId=$gameid")->decoded_content;

    my ($title) = ($html =~ m#<title>(.*)</title>#);
    my @teams = ($title =~ m#(.*) vs. (.*) - Boxscore#);
    $DBH->do(sprintf "insert into games (id, date, title, away, home)"
                . " values ($gameid, '%s', '$title', '$teams[0]', '$teams[1]')", $date->ymd);

    my $ppps = power_play($html);
    my ($pstats, $gstats) = ($html =~ /Player Summary(.*)Goaltending Summary(.*)Shots On Goal/);

    for my $conf ([$pstats, \&_skater_insert], [$gstats, \&_goalie_insert]) {
        my ($stats, $insert_cb) = @$conf;

        my $i = -1;
        my @rows = split "</tr>", $stats;
        for my $row (@rows) {
            next if $row !~ m#espn.go.com/nhl/player/_/id#;

            my ($id, $name, $pos, @stats) = _parse_stats_row($row);
            my $head = shift @stats;
            $i++ if $head;

            if (!defined $players->{$id}) {
                $DBH->do("insert into players (id, name, pos, team) values ($id, '$name', '$pos', '$teams[$i]')");
                $players->{$id} = 1;
            }

            shift @stats;
            $insert_cb->($gameid, $teams[$i], $id, $name, $pos, $winners, $ppps, @stats);
        }
    }

}

sub _goalie_insert {
    my ($gameid, $team, $id, $name, $pos, $winners, $ppps, @stats) = @_;

    my ($sa, $ga, $saves, $sv_perc, $toi, $pim) = @stats;

    my $win = defined $winners->{$id} ? 1 : 0;

    my ($min, $sec) = split /:/, $toi;
    $toi = 60*$min + $sec;

    my $sql = <<HERE;
insert into gamelogs (player_id, game_id, wins, saves, ga, mins, goals, assists, ppp, plusminus, pim, sog, hits, blocks)
values ($id, $gameid, $win, $saves, $ga, $toi, 0, 0, 0, 0, 0, 0, 0, 0)
HERE
    $DBH->do($sql);
}

sub _skater_insert {
    my ($gameid, $team, $id, $name, $pos, $winners, $ppps, @stats) = @_;

    my ($g, $a, $pm, $sog, $ms, $bs, $pn, $pim, $ht, $tk, $gv, 
        $shf, $toi, $pp, $sh, $ev, 
        $fw, $fl, $fper) = @stats;

    my $ppp = $ppps->{$name} // 0;

    my $sql = <<HERE;
insert into gamelogs (player_id, game_id, goals, assists, ppp, plusminus, pim, sog, hits, blocks, wins, saves, ga, mins)
values ($id, $gameid, $g, $a, $ppp, $pm, $pim, $sog, $ht, $bs, 0, 0, 0, 0)
HERE
    $DBH->do($sql);
}

sub _parse_stats_row {
    my ($row) = @_;

    $row =~ s#<td .*?>#<td>#g;
    $row =~ s#<tr .*?>##;
    $row =~ s#</td>##g;

    my @stats = split "<td>", $row;
    my ($id, $name, undef, $pos) = ($stats[1] =~ m#espn.go.com/nhl/player/_/id/(\d+)/([^"]+).*?( ([A-Z]+) ?)?$#);
    $pos //= 'G';

    return ($id, $name, $pos, @stats);
}


sub power_play {
    my ($str) = @_;

    my %ppps;
    while ($str =~ m#([^>]+ \(Power Play\).*?)</td>#g) {
        my $rec = "$1\n";
        my ($goal) = ($rec =~ m#^(.*?) \(\d+\)#);
        
        my $name = name($goal);
        $ppps{$name} //= 0;
        $ppps{$name}++;

        my ($assist) = ($rec =~ m#Assists?: (.*)</i>#);
        next if !defined $assist;

        for my $a (split ", ", $assist) {
            $name = name($a);

            $ppps{$name} //= 0;
            $ppps{$name}++;
        }
    }

    return \%ppps;
}

sub name {
    my ($n) = @_;
    $n =~ s/ /-/g;
    $n =~ s/['.]//g;
    return lc $n;
}
