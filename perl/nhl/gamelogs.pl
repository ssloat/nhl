use strict;
use warnings;

use DateTime;
use List::MoreUtils 'uniq';
use WWW::Mechanize;

my $mech = WWW::Mechanize->new;

my $start = _date($ARGV[0]);
my $end   = _date($ARGV[1] // $ARGV[0]);

for (; $start <= $end; $start->add(days => 1)) {
    scoreboard($start->ymd(q{}));
}

sub _date {
    my ($str) = @_;

    return DateTime->today if !defined $str;
    
    my ($y, $m, $d) = split /-/, $str;
    return DateTime->new(year => $y, month => $m, day => $d);
}

sub scoreboard {
    my ($ymd) = @_;

    my $html = $mech->get("http://scores.espn.go.com/nhl/scoreboard?date=$ymd")->decoded_content;

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
        game($gameid, \%winners);
    }
}

sub game {
    my ($gameid, $winners) = @_;

    my $html = $mech->get("http://scores.espn.go.com/nhl/boxscore?gameId=$gameid")->decoded_content;

    my ($title) = ($html =~ m#<title>(.*)</title>#);
    my @teams = ($title =~ m#(.*) vs. (.*) - Boxscore#);
    print "Title: ($gameid) $title\n";

    my $ppps = power_play($html);
    my ($pstats, $gstats) = ($html =~ /Player Summary(.*)Goaltending Summary(.*)Shots On Goal/);

    my $i = -1;
    my @rows = split "</tr>", $gstats;
    for my $row (@rows) {
        next if $row !~ m#espn.go.com/nhl/player/_/id#;
        $row =~ s#<td .*?>#<td>#g;
        $row =~ s#<tr .*?>##;
        $row =~ s#</td>##g;

        my @stats = split "<td>", $row;
        my $head = shift @stats;
        $i++ if $head;
        my ($id, $name) = ($stats[0] =~ m#espn.go.com/nhl/player/_/id/(\d+)/([^"]+)#);
        my $win = defined $winners->{$id} ? 1 : 0;
        print join(q{, },  $gameid, $teams[$i], $id, $name, 'G', $win, @stats[1..$#stats]) .  "\n";
    }

    $i = -1;
    @rows = split "</tr>", $pstats;
    for my $row (@rows) {
        next if $row !~ m#espn.go.com/nhl/player/_/id#;
        $row =~ s#<td .*?>#<td>#g;
        $row =~ s#<tr .*?>##;
        $row =~ s#</td>##g;

        my @stats = split "<td>", $row;
        my $head = shift @stats;
        $i++ if $head;
        my ($id, $name, $pos) = ($stats[0] =~ m#espn.go.com/nhl/player/_/id/(\d+)/([^"]+).* ([A-Z]+) ?$#);
        print join(q{, }, $gameid, $teams[$i], $id, $name, $pos, @stats[1..$#stats], ($ppps->{$name} // 0)) . "\n";
    }
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
