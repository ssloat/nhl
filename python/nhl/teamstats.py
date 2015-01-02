from nhl.playerratings import fantasy_teams, ratings

import datetime
import operator


if __name__ == '__main__':
    teams = fantasy_teams()

    numdays = 21
    today = datetime.datetime.now().date()
    rs = ratings(
            teams, 
            today - datetime.timedelta(days=(3)*numdays), 
            today - datetime.timedelta(days=1)
        )

    team_stats = dict([(x, 11 * [0]) for x in set(teams.values())])

    for name, stats in rs.iteritems():
        team = teams.get(name, 'FA')

        if team == 'FA': continue

        team_stats[team] = map(operator.add, team_stats[team], stats)
        
    for team, stats in team_stats.iteritems():
        print "%5s" % team, ["%7s" % ("%6.3f" % _) for _ in stats]


