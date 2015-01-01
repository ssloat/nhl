from sqlalchemy import func
from sqlalchemy.orm import joinedload

from nhl import session
from nhl.tables import Player, Game, GameLog, FantasyTeam, Owner

import operator
import datetime
import re
import numpy


def team_file():
    date = session.query(func.max(FantasyTeam.date)).first()[0]

    q = session.query(FantasyTeam)\
            .options(joinedload(FantasyTeam.player)).options(joinedload(FantasyTeam.owner))\
            .filter(FantasyTeam.date == date)

    return dict([(r.player.name, r.owner.team_name) for r in q.all()])

def ratings(teams, start, end):
    gamelogs = session.query(GameLog).options(joinedload(GameLog.player)).join(Game)\
                .filter(Game.date >= start, Game.date <= end).all()

    if not gamelogs: return
    skaters = [x for x in gamelogs if x.player.pos != 'G']
    goalies = [x for x in gamelogs if x.player.pos == 'G']

    players = dict([(x.player, len(x.stats())*[0]) for x in skaters])
    for gl in skaters:
        #players[gl.player] = [sum(x) for x in zip(players[gl.player][:10], gl.stats()[:10])]
        players[gl.player] = map(operator.add, players[gl.player], gl.stats())


    ratings = dict([(x.player.name, len(x.stats())*[0] + [0]) for x in skaters])
    values  = [x for p, x in players.iteritems() if p.name in teams]
    means   = numpy.mean(values, axis=0)
    stddevs = numpy.std(values, axis=0)

    for i in range(len(values[0])):
        for player, stats in players.iteritems():
            ratings[player.name][i] = (stats[i] - means[i]) / stddevs[i]
            ratings[player.name][-1] += ratings[player.name][i] 

    return ratings

if __name__ == '__main__':
    teams    = team_file()

    numdays = 21
    today = datetime.datetime.now().date()
    rs = [
        ratings(teams, today - datetime.timedelta(days=3*numdays), today - datetime.timedelta(days=2*numdays+1)),
        ratings(teams, today - datetime.timedelta(days=2*numdays), today - datetime.timedelta(days=numdays+1)),
        ratings(teams, today - datetime.timedelta(days=numdays), today),
    ]
    rs = [x for x in rs if x]

    names = set(reduce(lambda x, y: x+y.keys(), rs, []))

#    team_stats = dict([(x, 11 * [0]) for x in set(teams.values())])
    names = sorted(names, key=lambda x: sum([r.get(x, [0])[-1] for r in rs]))
    for i, name in enumerate(names):
        team = teams.get(names[i], 'FA')
        print len(names)-i, team, name, \
            ", ".join([
                    #"%.3f|%.3f|%.3f" % tuple( [r.get(names[i], 11*[0])[stat] for r in rs] ) 
                    "|".join(["%.3f" % r.get(name, 11*[0])[stat] for r in rs]) 
                    for stat in range(11)
                ])

#        if team == 'FA': continue
#
#        for _ in range(11):
#            team_stats[team][_] += x[_+1]
#        
#    for team, stats in team_stats.iteritems():
#        print team, ["%.3f" % _ for _ in stats]


