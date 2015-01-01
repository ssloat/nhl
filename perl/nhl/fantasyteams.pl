use strict;
use warnings;

use DateTime;
use WWW::Mechanize;
use Data::Dumper;
use List::MoreUtils 'uniq';
use DBI;

my $ymd = DateTime->today(time_zone => 'America/Chicago')->ymd;

my $dbh = DBI->connect("dbi:SQLite:dbname=$ARGV[0]","","", {});
$dbh->do("delete from fantasyteams where date='$ymd'");

my $sth = $dbh->prepare("select id from owners");
$sth->execute();
my @ids = map {$_->[0]} @{ $sth->fetchall_arrayref() };

$sth = $dbh->prepare("select username, password from espncreds");
$sth->execute();
my @creds = @{ $sth->fetchall_arrayref()->[0] };

$sth = $dbh->prepare('select name, id from players');
$sth->execute();
my %players = map {$_->[0] => $_->[1]} @{ $sth->fetchall_arrayref() };

my $mech = WWW::Mechanize->new;
$mech->get('https://r.espn.go.com/espn/memberservices/pc/login');
$mech->form_name('form-signin');
$mech->set_fields(username => $creds[0], password => $creds[1]);
$mech->click;

for my $id (@ids) {
    my $html = $mech->get("http://games.espn.go.com/fhl/clubhouse?leagueId=44843&teamId=$id&seasonId=2015")->decoded_content;

    while ($html =~ m#playerId="\d+".*?>([a-zA-Z.-]+ [ 'a-zA-Z.-]+?)<#g) {
        my $name = lc($1);
        $name =~ s/['.]//g;
        $name =~ s/ /-/g;

        next if !defined $players{$name};
        $dbh->do("insert into fantasyteams(owner_id, player_id, date) values ($id, '$players{$name}', '$ymd')");
    }
}


