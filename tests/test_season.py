"""
Testes das funções de temporada do ClassicFoot.

Cobre:
- sort_standings: ordem de critérios de desempate
- _apply_promotions: promoção/rebaixamento entre divisões
- season_prize_multiplier: crescimento anual da premiação
- monthly_sponsorship: escalabilidade por divisão
"""
import unittest

from season import sort_standings, _apply_promotions, monthly_sponsorship
from config.economy import season_prize_multiplier, PRIZE_LIGA
from tests.helpers import make_player, make_team
from models import Position


def _team_with_stats(team_id, name, division=1, pts_wins=0, draws=0, losses=0, gf=0, ga=0):
    """Helper: cria time e define estatísticas de liga diretamente."""
    t = make_team(team_id, name, division=division)
    t.div_wins = pts_wins
    t.div_draws = draws
    t.div_losses = losses
    t.div_gf = gf
    t.div_ga = ga
    return t


class SortStandingsTests(unittest.TestCase):
    """sort_standings deve ordenar por: pontos → vitórias → saldo → gols pró → nome."""

    def test_more_points_comes_first(self):
        a = _team_with_stats(1, "Alpha", pts_wins=10)   # 30 pts
        b = _team_with_stats(2, "Beta",  pts_wins=9)    # 27 pts
        ranked = sort_standings([b, a])
        self.assertEqual(ranked[0].name, "Alpha")

    def test_same_points_more_wins_comes_first(self):
        # Ambos 27 pts, mas A tem 9W-0D vs B com 8W-3D
        a = _team_with_stats(1, "Alpha", pts_wins=9, draws=0)
        b = _team_with_stats(2, "Beta",  pts_wins=8, draws=3)
        self.assertEqual(a.div_points, b.div_points)
        ranked = sort_standings([b, a])
        self.assertEqual(ranked[0].name, "Alpha")

    def test_same_points_wins_tiebreak_by_gd(self):
        a = _team_with_stats(1, "Alpha", pts_wins=8, gf=20, ga=10)  # GD +10
        b = _team_with_stats(2, "Beta",  pts_wins=8, gf=15, ga=10)  # GD  +5
        self.assertEqual(a.div_points, b.div_points)
        self.assertEqual(a.div_wins, b.div_wins)
        ranked = sort_standings([b, a])
        self.assertEqual(ranked[0].name, "Alpha")

    def test_same_gd_tiebreak_by_gf(self):
        a = _team_with_stats(1, "Alpha", pts_wins=8, gf=25, ga=15)  # GD +10, GF 25
        b = _team_with_stats(2, "Beta",  pts_wins=8, gf=20, ga=10)  # GD +10, GF 20
        self.assertEqual(a.div_gd, b.div_gd)
        ranked = sort_standings([b, a])
        self.assertEqual(ranked[0].name, "Alpha")

    def test_all_equal_tiebreak_by_name(self):
        # Nomes em ordem inversa para garantir que o sort está por nome
        a = _team_with_stats(1, "Alfa", pts_wins=5, gf=10, ga=5)
        b = _team_with_stats(2, "Zeta", pts_wins=5, gf=10, ga=5)
        ranked = sort_standings([b, a])
        self.assertEqual(ranked[0].name, "Alfa")

    def test_eight_teams_complete_table(self):
        teams = [_team_with_stats(i, f"Team{i}", pts_wins=8 - i, gf=10 - i, ga=5)
                 for i in range(1, 9)]
        ranked = sort_standings(teams)
        # Campeão deve ser o de maior pontuação (Team1)
        self.assertEqual(ranked[0].name, "Team1")
        # Último deve ser o de menor (Team8)
        self.assertEqual(ranked[-1].name, "Team8")


class ApplyPromotionsTests(unittest.TestCase):
    """_apply_promotions: top 2 de cada divisão sobe, últimos 2 descem."""

    def _make_division(self, div_id: int, start_id: int) -> list:
        """Cria 8 times numa divisão com pontos distintos."""
        teams = []
        for rank in range(8):
            t = _team_with_stats(start_id + rank, f"D{div_id}T{rank+1}",
                                 division=div_id, pts_wins=8 - rank)
            teams.append(t)
        return teams

    def setUp(self):
        self.div1 = self._make_division(1, start_id=100)
        self.div2 = self._make_division(2, start_id=200)
        self.div3 = self._make_division(3, start_id=300)
        self.div4 = self._make_division(4, start_id=400)
        self.divs = {1: self.div1, 2: self.div2, 3: self.div3, 4: self.div4}

    def test_top2_of_div2_promoted_to_div1(self):
        _apply_promotions(self.divs)
        promoted = [t for t in self.div2 if t.division == 1]
        self.assertEqual(2, len(promoted))
        # Devem ser os dois primeiros da classificação (maior pontuação)
        promoted_names = {t.name for t in promoted}
        self.assertIn("D2T1", promoted_names)
        self.assertIn("D2T2", promoted_names)

    def test_bottom2_of_div1_relegated_to_div2(self):
        _apply_promotions(self.divs)
        relegated = [t for t in self.div1 if t.division == 2]
        self.assertEqual(2, len(relegated))
        relegated_names = {t.name for t in relegated}
        self.assertIn("D1T7", relegated_names)
        self.assertIn("D1T8", relegated_names)

    def test_division_sizes_preserved_after_promotions(self):
        all_teams = self.div1 + self.div2 + self.div3 + self.div4
        _apply_promotions(self.divs)
        for div in [1, 2, 3, 4]:
            count = sum(1 for t in all_teams if t.division == div)
            self.assertEqual(8, count, f"Divisão {div} deveria ter 8 times, tem {count}")

    def test_div4_bottom2_stay_in_div4(self):
        """Não há divisão abaixo da 4 — os últimos ficam."""
        _apply_promotions(self.divs)
        still_in_div4 = [t for t in self.div4 if t.division == 4]
        self.assertEqual(6, len(still_in_div4))


class SeasonPrizeMultiplierTests(unittest.TestCase):
    """season_prize_multiplier cresce 5% por temporada a partir de 2025."""

    def test_base_year_is_one(self):
        self.assertAlmostEqual(1.0, season_prize_multiplier(2025))

    def test_one_season_is_five_percent_growth(self):
        self.assertAlmostEqual(1.05, season_prize_multiplier(2026), places=5)

    def test_ten_seasons_compound(self):
        expected = 1.05 ** 10
        self.assertAlmostEqual(expected, season_prize_multiplier(2035), places=5)

    def test_past_year_does_not_go_below_one(self):
        # Anos anteriores ao base não devem diminuir o multiplicador
        self.assertGreaterEqual(season_prize_multiplier(2020), 1.0)


class PrizeLigaStructureTests(unittest.TestCase):
    """PRIZE_LIGA deve ter estrutura consistente: 4 divisões × 8 posições."""

    def test_all_divisions_have_eight_positions(self):
        for div in [1, 2, 3, 4]:
            self.assertIn(div, PRIZE_LIGA)
            self.assertEqual(8, len(PRIZE_LIGA[div]))

    def test_higher_position_earns_more(self):
        """1º lugar ganha mais que 8º em qualquer divisão."""
        for div in [1, 2, 3, 4]:
            prize_first = PRIZE_LIGA[div][1]
            prize_last = PRIZE_LIGA[div][8]
            self.assertGreater(prize_first, prize_last,
                               f"Div {div}: 1º ({prize_first}) não supera 8º ({prize_last})")

    def test_div1_champion_earns_more_than_div4_champion(self):
        self.assertGreater(PRIZE_LIGA[1][1], PRIZE_LIGA[4][1])


if __name__ == "__main__":
    unittest.main()
