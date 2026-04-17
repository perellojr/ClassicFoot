import unittest

import main
from tests.helpers import make_team


class RivalryTests(unittest.TestCase):
    def test_register_dynamic_rivalry_promotes_to_classic_when_threshold_reached(self):
        team_a = make_team(1, "Alpha")
        team_b = make_team(2, "Beta")

        for _ in range(4):
            main._register_dynamic_rivalry(team_a, team_b, 2.2)

        self.assertIn(team_b.id, team_a.dynamic_rivals)
        self.assertIn(team_a.id, team_b.dynamic_rivals)
        self.assertTrue(main._is_classic(team_a, team_b))

    def test_state_rivalry_boosts_attendance_without_full_classic_cap(self):
        home = make_team(10, "Casa")
        away_same_state = make_team(11, "VisitanteMesmoEstado")
        away_other_state = make_team(12, "VisitanteOutroEstado")

        home.state = "SP"
        away_same_state.state = "SP"
        away_other_state.state = "RJ"

        # Evita clássico fixo/dinâmico interferindo no cenário.
        home.dynamic_rivals = []
        away_same_state.dynamic_rivals = []
        away_other_state.dynamic_rivals = []

        attendance_state = main._estimate_attendance(home, away_same_state, competition="Liga")
        attendance_other = main._estimate_attendance(home, away_other_state, competition="Liga")

        self.assertTrue(main._is_state_rivalry(home, away_same_state))
        self.assertFalse(main._is_state_rivalry(home, away_other_state))
        self.assertGreater(attendance_state, attendance_other)
        self.assertLessEqual(attendance_state, home.stadium_capacity)


if __name__ == "__main__":
    unittest.main()
