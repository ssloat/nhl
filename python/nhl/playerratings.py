from sqlalchemy import func
from sqlalchemy.orm import joinedload, contains_eager

from nhl import Session
from nhl.tables import Player, Game, GameLog, FantasyTeam, Owner

import operator
import datetime
import re
import numpy


def fantasy_teams():
    date = Session().query(func.max(FantasyTeam.date)).first()[0]

    q = Session().query(FantasyTeam)\
            .options(joinedload(FantasyTeam.player)).options(joinedload(FantasyTeam.owner))\
            .filter(FantasyTeam.date == date)

    return dict([(r.player.name, r.owner.team_name) for r in q.all()])

def ratings(teams, start, end):
    team_games = dict()
    for game in Session().query(Game).filter(Game.date >= start, Game.date <= end):
        for team in [game.home, game.away]:
            team_games[team] = team_games.get(team, 0) + 1

    skaters = Session().query(Player).join(Player.gamelogs).join(Game)\
                .options(contains_eager(Player.gamelogs).contains_eager(GameLog.game))\
                .filter(Player.pos!='G', Game.date>=start, Game.date<=end).all()

    values  = [s.avg_stats(team_games[s.team]) for s in skaters if s.name in teams]
    means   = numpy.mean(values, axis=0)
    stddevs = numpy.std(values, axis=0)

    return dict([(s.name, s.ratings(team_games[s.team], means, stddevs)) for s in skaters])

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
        for i in range(2)[::-1]
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

