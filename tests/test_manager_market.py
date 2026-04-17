import unittest
from unittest.mock import patch

from manager_market import process_coach_market
from models import CareerState, Coach
from tests.helpers import make_team


class ManagerMarketTests(unittest.TestCase):
    def _career(self):
        return CareerState(
            player_coach=Coach("Player Coach"),
            current_team_id=None,
            unemployed=True,
            free_coaches=[],
        )

    def test_process_market_runs_once_per_round_marker(self):
        team = make_team(1, "Time A", division=1, coach_name="Coach A")
        team.div_wins = 0
        team.div_draws = 0
        team.div_losses = 5
        team.last_results = ["L", "L", "L", "L", "L"]

        career = self._career()
        career.free_coaches = [Coach("Livre 1"), Coach("Livre 2")]

        with patch("manager_market._team_pressure", return_value=6), patch("manager_market.random.random", return_value=0.0):
            notifications_first = process_coach_market([team], career, round_marker=10)
            notifications_second = process_coach_market([team], career, round_marker=10)

        self.assertGreater(len(notifications_first), 0)
        self.assertEqual([], notifications_second)

    def test_team_does_not_rehire_just_fired_coach_immediately(self):
        fired_name = "Coach Demitido"
        team = make_team(1, "Time A", division=1, coach_name=fired_name)
        team.div_wins = 0
        team.div_draws = 0
        team.div_losses = 5
        team.last_results = ["L", "L", "L", "L", "L"]

        career = self._career()
        # Inclui o técnico demitido no pool e um candidato alternativo melhor.
        career.free_coaches = [Coach(fired_name, tactical=99, motivation=99, experience=99), Coach("Coach Novo", tactical=90, motivation=90, experience=90)]

        with patch("manager_market._team_pressure", return_value=6), patch("manager_market.random.random", return_value=0.0):
            process_coach_market([team], career, round_marker=1)

        self.assertNotEqual(fired_name, team.coach.name)


if __name__ == "__main__":
    unittest.main()

