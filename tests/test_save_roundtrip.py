"""
Testes de round-trip do sistema de save JSON.

Verifica que salvar e recarregar um game_state completo preserva:
- estrutura da temporada (year, matchday, copa, calendar)
- times e jogadores (stats, contratos, finanças)
- carreira (histórico, world_history, notificações)
- mercado (bid_stats, transfer_records)
"""
import tempfile
import unittest
from pathlib import Path

import save
from data import create_teams
from models import (
    CareerState, Coach, CupTie, MatchResult,
)
from season import create_season
from transfers import TransferMarket


def _make_full_state():
    """Cria um game_state representativo com season, career e market."""
    teams = create_teams()
    player_team = teams[0]
    season = create_season(2025, teams, player_team.id)
    coach = Coach(name="Técnico Round-Trip", nationality="Brasileiro",
                  tactical=80, motivation=75, experience=70, reputation=65)
    career = CareerState(
        player_coach=coach,
        current_team_id=player_team.id,
        unemployed=False,
    )
    career.season_history = [{"year": 2024, "team": player_team.name, "division": 4, "position": 1}]
    career.seen_notifications = {"notif_1", "notif_2"}
    career.event_log = [{"type": "hired", "year": 2025}]
    market = TransferMarket()
    market.bid_stats_by_ovr_bucket = {"70-79": {"count": 3, "sum": 8100}}
    market.transfer_records = [{"round": 2, "player": "Jogador X", "from": "Time A", "to": "Time B", "value": 2700, "salary": 180}]
    return {
        "season": season,
        "player_team": player_team,
        "market": market,
        "career": career,
    }


class SaveRoundTripTests(unittest.TestCase):

    def setUp(self):
        self._original_dir = save.SAVE_DIR

    def tearDown(self):
        save.SAVE_DIR = self._original_dir

    def _with_tmp(self, fn):
        with tempfile.TemporaryDirectory() as tmp:
            save.SAVE_DIR = Path(tmp)
            fn(Path(tmp))

    # ── Season ────────────────────────────────────────────────────

    def test_season_year_and_matchday_preserved(self):
        state = _make_full_state()
        state["season"].current_matchday = 3

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual(2025, loaded["season"].year)
            self.assertEqual(3, loaded["season"].current_matchday)

        self._with_tmp(check)

    def test_season_all_teams_count_preserved(self):
        state = _make_full_state()
        n_teams = len(state["season"].all_teams)

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual(n_teams, len(loaded["season"].all_teams))

        self._with_tmp(check)

    def test_season_calendar_preserved(self):
        state = _make_full_state()
        n_matchdays = len(state["season"].calendar)
        self.assertGreater(n_matchdays, 0)

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual(n_matchdays, len(loaded["season"].calendar))

        self._with_tmp(check)

    def test_season_copa_primeira_fase_preserved(self):
        state = _make_full_state()
        n_ties = len(state["season"].copa_primeira_fase)
        self.assertGreater(n_ties, 0)

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual(n_ties, len(loaded["season"].copa_primeira_fase))
            first = loaded["season"].copa_primeira_fase[0]
            self.assertIsNotNone(first.team_a)
            self.assertIsNotNone(first.team_b)
            self.assertIsInstance(first, CupTie)

        self._with_tmp(check)

    def test_season_results_history_round_trip(self):
        state = _make_full_state()
        team_a = state["season"].all_teams[0]
        team_b = state["season"].all_teams[1]
        result = MatchResult(
            home_team=team_a, away_team=team_b,
            home_goals=2, away_goals=1,
            home_scorers=["Gabigol"], away_scorers=[],
            competition="Liga", matchday=1,
            attendance=40_000, income=7_000,
            home_used_names=["Gabigol", "Pedro"],
            away_used_names=["Neymar"],
        )
        state["season"].results_history.append(result)

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            history = loaded["season"].results_history
            self.assertEqual(1, len(history))
            r = history[0]
            self.assertIsInstance(r, MatchResult)
            self.assertEqual(2, r.home_goals)
            self.assertEqual(1, r.away_goals)
            self.assertEqual("Gabigol", r.home_scorers[0])
            self.assertEqual(40_000, r.attendance)
            self.assertIn("Gabigol", r.home_used_names)

        self._with_tmp(check)

    def test_league_fixtures_reconstructed(self):
        state = _make_full_state()
        n_fixtures = len(state["season"].league_fixtures)
        self.assertGreater(n_fixtures, 0)

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual(n_fixtures, len(loaded["season"].league_fixtures))

        self._with_tmp(check)

    # ── Teams e Players ───────────────────────────────────────────

    def test_team_finances_preserved(self):
        state = _make_full_state()
        team = state["season"].all_teams[0]
        team.caixa = 123_456
        team.salario_mensal = 7_890

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            t = next(t for t in loaded["season"].all_teams if t.id == team.id)
            self.assertEqual(123_456, t.caixa)
            self.assertEqual(7_890, t.salario_mensal)

        self._with_tmp(check)

    def test_player_season_stats_preserved(self):
        state = _make_full_state()
        player = state["season"].all_teams[0].players[0]
        player.gols_temp = 7
        player.partidas_temp = 10
        player.amarelos_temp = 2
        player.vermelhos_temp = 1

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            p = loaded["season"].all_teams[0].players[0]
            self.assertEqual(7, p.gols_temp)
            self.assertEqual(10, p.partidas_temp)
            self.assertEqual(2, p.amarelos_temp)
            self.assertEqual(1, p.vermelhos_temp)

        self._with_tmp(check)

    def test_team_colors_preserved(self):
        state = _make_full_state()
        team = state["season"].all_teams[0]
        self.assertIsNotNone(team.primary_color)

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            t = next(t for t in loaded["season"].all_teams if t.id == team.id)
            self.assertEqual(team.primary_color, t.primary_color)
            self.assertEqual(team.secondary_color, t.secondary_color)

        self._with_tmp(check)

    # ── Career ────────────────────────────────────────────────────

    def test_career_coach_name_preserved(self):
        state = _make_full_state()

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual("Técnico Round-Trip", loaded["career"].player_coach.name)

        self._with_tmp(check)

    def test_career_team_id_preserved(self):
        state = _make_full_state()
        team_id = state["career"].current_team_id

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual(team_id, loaded["career"].current_team_id)

        self._with_tmp(check)

    def test_career_seen_notifications_preserved(self):
        state = _make_full_state()

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            seen = loaded["career"].seen_notifications
            self.assertIsInstance(seen, set)
            self.assertIn("notif_1", seen)
            self.assertIn("notif_2", seen)

        self._with_tmp(check)

    def test_career_season_history_preserved(self):
        state = _make_full_state()

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            hist = loaded["career"].season_history
            self.assertEqual(1, len(hist))
            self.assertEqual(2024, hist[0]["year"])

        self._with_tmp(check)

    def test_career_event_log_preserved(self):
        state = _make_full_state()

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertEqual([{"type": "hired", "year": 2025}], loaded["career"].event_log)

        self._with_tmp(check)

    # ── Market ────────────────────────────────────────────────────

    def test_market_bid_stats_preserved(self):
        state = _make_full_state()

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            stats = loaded["market"].bid_stats_by_ovr_bucket
            self.assertIn("70-79", stats)
            self.assertEqual(3, stats["70-79"]["count"])

        self._with_tmp(check)

    def test_market_transfer_records_preserved(self):
        state = _make_full_state()

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            records = loaded["market"].transfer_records
            self.assertEqual(1, len(records))
            self.assertEqual("Jogador X", records[0]["player"])

        self._with_tmp(check)

    # ── player_team ───────────────────────────────────────────────

    def test_player_team_resolved_from_career(self):
        state = _make_full_state()
        team_id = state["player_team"].id

        def check(tmp):
            save.save_game(state)
            loaded = save.load_game()
            self.assertIsNotNone(loaded["player_team"])
            self.assertEqual(team_id, loaded["player_team"].id)

        self._with_tmp(check)

    # ── Idempotência ──────────────────────────────────────────────

    def test_double_save_load_idempotent(self):
        """Salvar duas vezes e carregar deve retornar os mesmos dados."""
        state = _make_full_state()
        state["season"].current_matchday = 5

        def check(tmp):
            save.save_game(state)
            loaded1 = save.load_game()
            save.save_game(loaded1)
            loaded2 = save.load_game()
            self.assertEqual(loaded1["season"].year, loaded2["season"].year)
            self.assertEqual(loaded1["season"].current_matchday, loaded2["season"].current_matchday)
            self.assertEqual(
                loaded1["career"].player_coach.name,
                loaded2["career"].player_coach.name,
            )

        self._with_tmp(check)


if __name__ == "__main__":
    unittest.main()
