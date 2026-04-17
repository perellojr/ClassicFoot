import unittest

from engine import finalize_match_result, simulate_penalty_series
from models import Position
from tests.helpers import make_player, make_team


class EngineTests(unittest.TestCase):
    def test_finalize_match_result_updates_players_and_embeds_used_names(self):
        home_players = [
            make_player(1, "Home GK", Position.GK, 75),
            make_player(2, "Home ST", Position.ATK, 78),
        ]
        away_players = [
            make_player(3, "Away GK", Position.GK, 74),
            make_player(4, "Away ST", Position.ATK, 77),
        ]
        home = make_team(1, "Home", division=1, players=home_players)
        away = make_team(2, "Away", division=1, players=away_players)

        result = finalize_match_result(
            home=home,
            away=away,
            competition="Liga",
            matchday=1,
            home_goals=1,
            away_goals=0,
            home_scorers=["Home ST"],
            away_scorers=[],
            attendance=10000,
            events=[{"type": "red", "side": "away", "player_name": "Away ST"}],
            home_used=home_players,
            away_used=away_players,
        )

        self.assertEqual("Liga", result.competition)
        self.assertIn("Home ST", result.home_used_names)
        self.assertIn("Away ST", result.away_used_names)
        self.assertEqual(1, home_players[1].gols_temp)
        self.assertEqual(1, home_players[1].partidas_temp)
        self.assertEqual(1, away_players[1].vermelhos_temp)
        self.assertGreaterEqual(away_players[1].suspenso, 1)

    def test_penalty_series_returns_winner_and_valid_score(self):
        team_a = make_team(11, "A", division=1, players=[make_player(10, "A GK", Position.GK)])
        team_b = make_team(12, "B", division=1, players=[make_player(20, "B GK", Position.GK)])

        winner, score, log = simulate_penalty_series(team_a, team_b)

        self.assertIn(winner.id, {team_a.id, team_b.id})
        self.assertIsInstance(score, tuple)
        self.assertEqual(2, len(score))
        self.assertGreater(len(log), 0)


if __name__ == "__main__":
    unittest.main()

