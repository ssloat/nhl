from nose.tools import assert_equals
import datetime

from nhl.tables import Player, Game, GameLog

class TestPlayer:
    def setUp(self):
        self.p = Player(123, 'steven-stamkos', 'RW', 'Boston')

        self.g_1 = Game(456, datetime.date(2014, 12, 20), 'Title', 'Boston', 'Home')
        self.g_2 = Game(457, datetime.date(2014, 12, 25), 'Title', 'Away', 'Boston')

        self.gl_1 = GameLog(self.p, self.g_1, goals=2, assists=1, ppp=1, hits=5)
        self.gl_2 = GameLog(self.p, self.g_2, goals=1, assists=0, ppp=0, hits=9)

    def tearDown(self):
        pass

    def test_case_1(self):
        assert_equals(self.p.num_stats(), 10)
        assert_equals(self.p.total_stats()[:3], [3, 1, 4])
        assert_equals(self.p.avg_stats(2)[:3], [1.5, 0.5, 2])

def test_goalie():
    p = Player(123, 'generic-goalie', 'G', 'Washington')
    assert_equals(p.num_stats(), 5)

