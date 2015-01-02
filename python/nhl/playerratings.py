from sqlalchemy import func
from sqlalchemy.orm import joinedload

from nhl import session
from nhl.tables import Player, Game, GameLog, FantasyTeam, Owner

import operator
import datetime
import re
import numpy


def fantasy_teams():
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
        players[gl.player] = map(operator.add, players[gl.player], gl.stats())

    games = session.query(Game).filter(Game.date >= start, Game.date <= end).all()
    team_games = dict.fromkeys(set([x.home for x in games] + [x.away for x in games]), 0)
    for game in games:
        team_games[game.home] += 1
        team_games[game.away] += 1

    for player, stats in players.iteritems():
        players[player] = [float(x)/float(team_games[player.team]) for x in stats]

    values  = [x for p, x in players.iteritems() if p.name in teams]
    means   = numpy.mean(values, axis=0)
    stddevs = numpy.std(values, axis=0)

    ratings = dict([(x.player.name, len(x.stats())*[0] + [0]) for x in skaters])
    for i in range(len(values[0])):
        for player, stats in players.iteritems():
            ratings[player.name][i] = (stats[i] - means[i]) / stddevs[i]
            ratings[player.name][-1] += ratings[player.name][i] 

    return ratings

if __name__ == '__main__':
    teams = fantasy_teams()

    numdays = 21
    today = datetime.datetime.now().date()
    rs = [
        ratings(
            teams, 
            today - datetime.timedelta(days=(i+1)*numdays), 
            today - datetime.timedelta(days=i*numdays+1)
        )
        for i in range(3)[::-1]
    ]
    rs = [x for x in rs if x]

    names = set(reduce(lambda x, y: x+y.keys(), rs, []))

    names = sorted(names, key=lambda x: sum([r.get(x, [0])[-1] for r in rs]))
    for i, name in enumerate(names):
        team = teams.get(name, 'FA')
        print len(names)-i, team, name, \
            ", ".join([
                    "|".join(["%.3f" % r.get(name, 11*[0])[stat] for r in rs]) 
                    for stat in range(11)
                ])

