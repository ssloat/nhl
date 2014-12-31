from sqlalchemy import create_engine

from nhl import session
from nhl.tables import Player, Game, GameLog

import operator
import datetime
import re
import numpy

months = {'October': 10, 'November': 11, 'December': 12}

def team_file(fn):
    teams = dict()
    fh = open(fn)
    for line in fh.readlines():
        team, name = line.split(':')
        teams[name[:-1].replace('.', '').replace("'", '').replace(' ', '-').lower()] = team

    return teams

def ratings(teams, start, end):
    gamelogs = session.query(GameLog).join(Player).join(Game)\
                .filter(Player.pos != 'G', Game.date >= start, Game.date <= end).all()

    players = dict([(x.player, 10*[0]) for x in gamelogs])
    for gl in gamelogs:
        #players[gl.player] = [sum(x) for x in zip(players[gl.player][:10], gl.stats()[:10])]
        players[gl.player] = map(operator.add, players[gl.player][:10], gl.stats()[:10])


    ratings = dict([(x.player.name, 11*[0]) for x in gamelogs])
    for i in range(10):
        values = [x[i] for p, x in players.iteritems() if p.name in teams]
        mean = numpy.mean(values)
        stddev = numpy.std(values)

        for player, stats in players.iteritems():
            ratings[player.name][i] = (stats[i] - mean) / stddev
            ratings[player.name][-1] += ratings[player.name][i] 

    return ratings

if __name__ == '__main__':
    teams    = team_file('teams.out.20141229')

    numdays = 21
    today = datetime.datetime.now().date()
    rs = [
        ratings(teams, today - datetime.timedelta(days=3*numdays), today - datetime.timedelta(days=2*numdays+1)),
        ratings(teams, today - datetime.timedelta(days=2*numdays), today - datetime.timedelta(days=numdays+1)),
        ratings(teams, today - datetime.timedelta(days=numdays), today),
    ]

    names = set(rs[0].keys() + rs[1].keys() + rs[2].keys())

#    team_stats = dict([(x, 11 * [0]) for x in set(teams.values())])
    names = sorted(names, key=lambda x: sum([r.get(x, [0])[-1] for r in rs]))
    for i in range(len(names)):
        team = teams.get(names[i], 'FA')
        print len(names)-i, team, names[i], \
            ", ".join([
                    "%.3f|%.3f|%.3f" % tuple( [r.get(names[i], 11*[0])[stat] for r in rs] ) 
                    for stat in range(11)
                ])

#        if team == 'FA': continue
#
#        for _ in range(11):
#            team_stats[team][_] += x[_+1]
#        
#    for team, stats in team_stats.iteritems():
#        print team, ["%.3f" % _ for _ in stats]


