from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

from nhl import Base

import datetime

class EspnCred(Base):
    __tablename__ = 'espncreds'

    id       = Column(Integer, primary_key=True)
    username = Column(String)
    password = Column(String)

    def __init__(self, username, password):
        self.username = username
        self.password = password

class Owner(Base):
    __tablename__ = 'owners'

    id        = Column(Integer, primary_key=True)
    name      = Column(String)
    team_name = Column(String)

    def __init__(self, id, name, team_name):
        self.id        = id
        self.name      = name
        self.team_name = team_name

    def __repr__(self):
       return "<Owner('%d, %s, %s')>" % ((self.id or 0), self.name, self.team_name)


class FantasyTeam(Base):
    __tablename__ = 'fantasyteams'

    id        = Column(Integer, primary_key=True)
    owner_id  = Column(Integer, ForeignKey('owners.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    date      = Column(Date)

    owner    = relationship("Owner", backref='fantasy_team')
    player   = relationship("Player", backref='fantasy_team')

    def __init__(self, date, owner, player):
        self.date      = date
        self.team_name = name
        self.player    = player

    def __repr__(self):
       return "<FantasyTeam('%d, %s, %s')>" % ((self.id or 0), self.owner.team_name, self.player.name)

class Player(Base):
    __tablename__ = 'players'

    id        = Column(Integer, primary_key=True)
    name      = Column(String)
    pos       = Column(String)
    team      = Column(String)

    gamelogs = relationship("GameLog", backref='player')

    def __init__(self, id, name, pos, team):
        self.id   = id
        self.name = name
        self.pos  = pos
        self.team = team

    def __repr__(self):
       return "<Player('%d, %s, %s, %s')>" % ((self.id or 0), self.name, self.pos, self.team)

class Game(Base):
    __tablename__ = 'games'

    id    = Column(Integer, primary_key=True)
    date  = Column(Date)
    title = Column(String)
    away  = Column(String)
    home  = Column(String)

    def __init__(self, id, date, title, away, home):
        self.id    = id
        self.date  = date
        self.title = title
        self.away  = away
        self.home  = home

    def __repr__(self):
       return "<Game('%d, %s, %s')>" % ((self.id or 0), self.title, self.date)

class GameLog(Base):
    __tablename__ = 'gamelogs'

    id        = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    game_id   = Column(Integer, ForeignKey('games.id'))

    goals     = Column(Integer, default=0)
    assists   = Column(Integer, default=0)
    ppp       = Column(Integer, default=0)
    plusminus = Column(Integer, default=0)
    pim       = Column(Integer, default=0)
    sog       = Column(Integer, default=0)
    hits      = Column(Integer, default=0)
    blocks    = Column(Integer, default=0)

    wins     = Column(Integer, default=0)
    saves    = Column(Integer, default=0)
    ga       = Column(Integer, default=0)
    mins     = Column(Integer, default=0)

    game   = relationship("Game")

    def __init__(self, player, game, gp=0, goals=0, assists=0, ppp=0,
            plusminus=0, pim=0, sog=0, hits=0, blocks=0, wins=0, 
            saves=0, ga=0, mins=0):

        self.gp        = gp

        self.goals     = goals
        self.assists   = assists
        self.ppp       = ppp
        self.plusminus = plusminus
        self.pim       = pim
        self.sog       = sog
        self.hits      = hits
        self.blocks    = blocks

        self.wins     = wins
        self.saves    = saves
        self.ga       = ga
        self.mins     = mins
    
        self.player = player
        self.game   = game

    def __repr__(self):
       return "<GameLog('%d, %s')>" % ((self.id or 0), self.stats())

    def skater_stats(self):
        return [
                self.goals, self.assists, self.goals + self.assists,
                self.plusminus, self.pim, self.ppp, self.sog, self.hits,
                self.blocks, 
                (self.goals + self.assists if self.player.pos == 'D' else 0), 
        ]

    def goalie_stats(self):
        return [
                self.wins, self.saves, 
                (1 if self.wins == 1 and self.ga == 0 else 0),
                3600 / self.mins * self.ga, 
                (float(self.saves) / float(self.saves + self.ga) 
                    if float(self.saves + self.ga) > 0 else 0
                ),
        ]

    def stats(self):
        return self.goalie_stats() if self.player.pos == 'G' else self.skater_stats()

if __name__ == '__main__':
    p = Player(123, 'steven-stamkos', 'RW', 'Boston')
    print p

    g = Game(456, datetime.date(2014, 12, 20), 'Title')
    print g

    l = GameLog(p, g, goals=2, ppp=1)

    print l

