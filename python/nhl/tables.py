from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

from nhl import Base

import datetime

class Player(Base):
    __tablename__ = 'players'

    id   = Column(Integer, primary_key=True)
    name = Column(String)
    pos  = Column(String)
    team = Column(String)

    gamelogs = relationship("GameLog", backref='player')

    def __init__(self, id, name, pos, team):
        self.id   = id
        self.name = name
        self.pos  = pos
        self.team = team

    def __repr__(self):
       return "<Player('%d, %s, %s, %s')>" % ((self.id or 0), self.name,
               self.pos, self.team)

class Game(Base):
    __tablename__ = 'games'

    id    = Column(Integer, primary_key=True)
    date  = Column(Date)
    title = Column(String)

    def __init__(self, id, date, title):
        self.id    = id
        self.date  = date
        self.title = title

    def __repr__(self):
       return "<Game('%d, %s, %s')>" % ((self.id or 0), self.title, self.date)

class GameLog(Base):
    __tablename__ = 'gamelogs'

    id        = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    game_id   = Column(Integer, ForeignKey('games.id'))

    gp        = Column(Integer)

    goals     = Column(Integer)
    assists   = Column(Integer)
    ppp       = Column(Integer)
    plusminus = Column(Integer)
    pim       = Column(Integer)
    sog       = Column(Integer)
    hits      = Column(Integer)
    blocks    = Column(Integer)

    wins     = Column(Integer)
    saves    = Column(Integer)
    ga       = Column(Integer)
    mins     = Column(Integer)
    sos      = Column(Integer)

    game   = relationship("Game")

    def __init__(self, player, game, gp=0, goals=0, assists=0, ppp=0,
            plusminus=0, pim=0, sog=0, hits=0, blocks=0, wins=0, 
            saves=0, ga=0, mins=0, sos=0):

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
        self.sos      = sos
    
        self.player = player
        self.game   = game

    def __repr__(self):
       return "<GameLog('%d, %s')>" % ((self.id or 0), self.stats())

    def stats(self):
        return [self.goals, self.assists, self.goals + self.assists,
                self.plusminus, self.pim, self.ppp, self.sog, self.hits,
                self.blocks, 
                (self.goals + self.assists if self.player.pos == 'D' else 0), 
                self.wins, self.saves, self.sos,
                self.mins / 60.0 * self.ga, 
                (float(self.saves) / float(self.saves + self.ga) 
                    if float(self.saves + self.ga) > 0 else 0
                ),
        ]

if __name__ == '__main__':
    p = Player(123, 'steven-stamkos', 'RW', 'Boston')
    print p

    g = Game(456, datetime.date(2014, 12, 20), 'Title')
    print g

    l = GameLog(p, g, goals=2, ppp=1)

    print l

