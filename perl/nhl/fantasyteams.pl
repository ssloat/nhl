use WWW::Mechanize;
use Data::Dumper;
use List::MoreUtils 'uniq';

open my $fh, '<', 'espncreds.txt';
my @creds = <$fh>;
chomp(@creds);

my $mech = WWW::Mechanize->new;
$mech->get('https://r.espn.go.com/espn/memberservices/pc/login');
$mech->form_name('form-signin');
$mech->set_fields(username => $creds[0], password => $creds[1]);
$mech->click;


my @teams = qw/JENN WILS RAIN BMB ELLN SIEB PBX SLOAT LEON PAUL/;

for my $i (0..$#teams) {
    my $ii = $i+1;
    my $html = $mech->get("http://games.espn.go.com/fhl/clubhouse?leagueId=44843&teamId=$ii&seasonId=2015")->decoded_content;

    while ($html =~ m#playerId="\d+".*?>([a-zA-Z.-]+ [ 'a-zA-Z.-]+?)<#g) {
        print "$teams[$i]:$1\n";
    }
}


