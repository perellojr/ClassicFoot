"""
Testes para estimate_attendance, apply_red_card_effects e apply_auto_injury_substitutions.
"""
import unittest

from engine import (
    estimate_attendance,
    apply_red_card_effects,
    apply_auto_injury_substitutions,
    pick_injury_replacement,
)
from models import Position
from tests.helpers import make_player, make_team


def _make_live_game(home_team, away_team, events=None, subs_home=0, subs_away=0):
    """Helper: monta um live_game dict mínimo para os testes de estado."""
    gk_home = make_player(901, "GK Home", Position.GK, 75)
    gk_away = make_player(902, "GK Away", Position.GK, 74)
    mid_home = make_player(903, "MID Home", Position.MID, 72)
    mid_away = make_player(904, "MID Away", Position.MID, 71)
    bench_home = [make_player(905, "Bench Home", Position.GK, 68)]
    bench_away = [make_player(906, "Bench Away", Position.GK, 67)]

    return {
        "home_lineup": [gk_home, mid_home],
        "away_lineup": [gk_away, mid_away],
        "home_bench": bench_home,
        "away_bench": bench_away,
        "home_used": [gk_home, mid_home],
        "away_used": [gk_away, mid_away],
        "home_subs_used": subs_home,
        "away_subs_used": subs_away,
        "half1": {
            "events": events or [],
        },
    }


class EstimateAttendanceTests(unittest.TestCase):

    def _team(self, tid, prestige, torcida):
        return make_team(tid, f"T{tid}", prestige=prestige, players=[
            make_player(tid * 100, f"P{tid}", Position.GK, 70)
        ] * 11)

    def setUp(self):
        # Prestige moderado para que state rivalry ainda mova a agulha (não bata no cap 0.99 logo)
        self.high = self._team(1, prestige=60, torcida=3_000_000)
        self.low  = self._team(2, prestige=50, torcida=500_000)
        # Time de alto prestígio para testes de cap
        self.elite = self._team(3, prestige=95, torcida=30_000_000)

    def test_classic_fills_stadium(self):
        attendance = estimate_attendance(self.elite, self.low, is_classic=True)
        self.assertEqual(self.elite.stadium_capacity, attendance)

    def test_copa_final_fills_stadium(self):
        attendance = estimate_attendance(self.elite, self.low, competition="Copa", phase="final")
        self.assertEqual(self.elite.stadium_capacity, attendance)

    def test_state_rivalry_higher_than_plain_league(self):
        # Usa time de prestige moderado para que a rivalidade mova a ocupação antes do cap
        plain = estimate_attendance(self.high, self.low, competition="Liga", is_state_rivalry=False)
        rival = estimate_attendance(self.high, self.low, competition="Liga", is_state_rivalry=True)
        self.assertGreater(rival, plain)

    def test_attendance_never_exceeds_capacity(self):
        for team, is_classic in [(self.high, True), (self.high, False), (self.elite, True)]:
            att = estimate_attendance(team, self.low, is_classic=is_classic)
            self.assertLessEqual(att, team.stadium_capacity)

    def test_copa_semi_higher_than_primeira_fase(self):
        att_pf = estimate_attendance(self.high, self.low, competition="Copa", phase="primeira_fase")
        att_sf = estimate_attendance(self.high, self.low, competition="Copa", phase="semi")
        self.assertGreater(att_sf, att_pf)

    def test_low_prestige_team_still_positive(self):
        att = estimate_attendance(self.low, self.high, competition="Liga")
        self.assertGreater(att, 0)


class PickInjuryReplacementTests(unittest.TestCase):

    def test_returns_none_when_bench_empty(self):
        injured = make_player(1, "Injured", Position.ATK, 80)
        self.assertIsNone(pick_injury_replacement([], injured))

    def test_prefers_same_position(self):
        injured = make_player(1, "Injured GK", Position.GK, 80)
        bench = [
            make_player(2, "ATK Bench", Position.ATK, 75),
            make_player(3, "GK Bench", Position.GK, 65),
        ]
        replacement = pick_injury_replacement(bench, injured)
        self.assertEqual(Position.GK, replacement.position)

    def test_falls_back_to_best_ovr_when_no_same_position(self):
        injured = make_player(1, "Injured GK", Position.GK, 80)
        bench = [
            make_player(2, "MID Bench", Position.MID, 72),
            make_player(3, "ATK Bench", Position.ATK, 78),
        ]
        replacement = pick_injury_replacement(bench, injured)
        self.assertEqual(78, int(replacement.overall))


class ApplyRedCardEffectsTests(unittest.TestCase):

    def test_red_card_removes_player_from_lineup(self):
        home = make_team(1, "Home")
        away = make_team(2, "Away")
        live = _make_live_game(home, away, events=[{
            "minute": 55,
            "type": "red",
            "side": "away",
            "player_name": "MID Away",
            "team_name": "Away",
            "short_name": "AWY",
        }])

        initial_away_count = len(live["away_lineup"])
        apply_red_card_effects(live, "half1")
        self.assertEqual(initial_away_count - 1, len(live["away_lineup"]))
        names = [p.name for p in live["away_lineup"]]
        self.assertNotIn("MID Away", names)

    def test_gk_red_card_triggers_auto_substitution(self):
        home = make_team(1, "Home")
        away = make_team(2, "Away")
        live = _make_live_game(home, away, events=[{
            "minute": 30,
            "type": "red",
            "side": "away",
            "player_name": "GK Away",
            "team_name": "Away",
            "short_name": "AWY",
        }])

        apply_red_card_effects(live, "half1")
        # O banco reserve GK deve ter sido chamado
        sub_events = [e for e in live["half1"]["events"] if e.get("type") == "substitution"]
        self.assertTrue(len(sub_events) >= 1)
        # GK expulso deve ter sido substituído
        away_names = [p.name for p in live["away_lineup"]]
        self.assertIn("Bench Away", away_names)

    def test_no_substitution_when_subs_exhausted(self):
        home = make_team(1, "Home")
        away = make_team(2, "Away")
        live = _make_live_game(home, away, subs_away=5, events=[{
            "minute": 60,
            "type": "red",
            "side": "away",
            "player_name": "GK Away",
            "team_name": "Away",
            "short_name": "AWY",
        }])

        apply_red_card_effects(live, "half1")
        sub_events = [e for e in live["half1"]["events"] if e.get("type") == "substitution"]
        self.assertEqual(0, len(sub_events))

    def test_no_effect_when_player_not_in_lineup(self):
        home = make_team(1, "Home")
        away = make_team(2, "Away")
        live = _make_live_game(home, away, events=[{
            "minute": 70,
            "type": "red",
            "side": "home",
            "player_name": "Jogador Fantasma",
        }])

        initial_count = len(live["home_lineup"])
        apply_red_card_effects(live, "half1")
        self.assertEqual(initial_count, len(live["home_lineup"]))


class ApplyAutoInjurySubstitutionsTests(unittest.TestCase):

    def test_injury_event_triggers_substitution(self):
        home = make_team(1, "Home")
        away = make_team(2, "Away")
        live = _make_live_game(home, away, events=[{
            "minute": 25,
            "type": "injury",
            "side": "home",
            "player_name": "MID Home",
            "team_name": "Home",
            "short_name": "HME",
        }])

        apply_auto_injury_substitutions(live, "half1")
        sub_events = [e for e in live["half1"]["events"] if e.get("type") == "substitution"]
        self.assertTrue(len(sub_events) >= 1)

    def test_no_substitution_when_subs_exhausted(self):
        home = make_team(1, "Home")
        away = make_team(2, "Away")
        live = _make_live_game(home, away, subs_home=5, events=[{
            "minute": 40,
            "type": "injury",
            "side": "home",
            "player_name": "MID Home",
            "team_name": "Home",
            "short_name": "HME",
        }])

        apply_auto_injury_substitutions(live, "half1")
        sub_events = [e for e in live["half1"]["events"] if e.get("type") == "substitution"]
        self.assertEqual(0, len(sub_events))


if __name__ == "__main__":
    unittest.main()
