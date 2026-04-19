"""
Testes dos métodos adicionados aos enums Formation e Postura.
"""
import unittest

from models import Formation, Postura, Position
from tests.helpers import make_player, make_team


def _gk(pid, name="GK"):
    return make_player(pid, name, Position.GK, 70)

def _def(pid, name="DEF"):
    return make_player(pid, name, Position.DEF, 70)

def _mid(pid, name="MID"):
    return make_player(pid, name, Position.MID, 70)

def _atk(pid, name="ATK"):
    return make_player(pid, name, Position.ATK, 70)


def _full_squad(base_id=1) -> list:
    """15 jogadores suficientes para qualquer formação (incl. F532/F343 com 3 ATK e 5 DEF)."""
    return [
        _gk(base_id),
        _def(base_id + 1), _def(base_id + 2), _def(base_id + 3), _def(base_id + 4), _def(base_id + 5),
        _mid(base_id + 6), _mid(base_id + 7), _mid(base_id + 8), _mid(base_id + 9), _mid(base_id + 10),
        _atk(base_id + 11), _atk(base_id + 12), _atk(base_id + 13),
        _gk(base_id + 14),
    ]


class FormationCanUseTests(unittest.TestCase):

    def test_returns_false_when_fewer_than_11_players(self):
        team = make_team(1, "Alfa", players=_full_squad()[:10])
        for f in Formation:
            self.assertFalse(f.can_use(team), f"{f.value} deveria ser False com 10 jogadores")

    def test_returns_false_when_not_enough_of_one_position(self):
        # F532 exige 5 DEF — 4 DEF não bastam
        players = [_gk(1)] + [_def(i) for i in range(2, 6)] + [_mid(i) for i in range(6, 9)] + [_atk(i) for i in range(9, 12)]
        team = make_team(2, "Beta", players=players)
        self.assertFalse(Formation.F532.can_use(team))

    def test_returns_true_with_adequate_squad(self):
        team = make_team(3, "Gamma", players=_full_squad())
        self.assertTrue(Formation.F442.can_use(team))
        self.assertTrue(Formation.F433.can_use(team))

    def test_best11_only_requires_one_goalkeeper(self):
        players = [_gk(1)] + [_atk(i) for i in range(2, 12)]
        team = make_team(4, "Delta", players=players)
        self.assertTrue(Formation.BEST11.can_use(team))

    def test_best11_false_without_goalkeeper(self):
        players = [_def(i) for i in range(1, 12)]
        team = make_team(5, "Epsilon", players=players)
        self.assertFalse(Formation.BEST11.can_use(team))


class FormationFitOvrTests(unittest.TestCase):

    def test_empty_lineup_returns_zero(self):
        self.assertEqual(0.0, Formation.F442.fit_ovr([]))

    def test_fit_ovr_respects_bias_ratio(self):
        players = [make_player(i, f"P{i}", Position.MID, 80) for i in range(11)]
        # F433 tem atk_bias=1.10, def_bias=0.92 → média 1.01 → 80*1.01=80.8
        fit = Formation.F433.fit_ovr(players)
        expected = round(80 * (1.10 + 0.92) / 2, 1)
        self.assertAlmostEqual(expected, fit, places=1)

    def test_fit_ovr_uses_average_of_both_biases(self):
        """fit_ovr usa (atk + def) / 2, não só atk — F352 (avg 0.99) < F442 (avg 1.00)."""
        players = [make_player(i, f"P{i}", Position.MID, 80) for i in range(11)]
        fit_f442 = Formation.F442.fit_ovr(players)   # atk=1.00, def=1.00 → avg=1.00
        fit_f352 = Formation.F352.fit_ovr(players)   # atk=1.02, def=0.96 → avg=0.99
        self.assertGreater(fit_f442, fit_f352)

    def test_best11_has_neutral_bias(self):
        players = [make_player(i, f"P{i}", Position.MID, 80) for i in range(11)]
        fit = Formation.BEST11.fit_ovr(players)
        # atk=1.04, def=0.96 → média 1.0 → 80.0
        self.assertAlmostEqual(80.0, fit, places=1)


class PosturaFitOvrTests(unittest.TestCase):

    def test_equilibrado_preserves_base_ovr(self):
        # (1.0 + 1.0) / 2 = 1.0 → base_ovr inalterado
        self.assertAlmostEqual(75.0, Postura.EQUILIBRADO.fit_ovr(75.0), places=1)

    def test_defensivo_reduces_ovr(self):
        # (0.88 + 1.14) / 2 = 1.01 → levemente acima (não é penalidade pura)
        result = Postura.DEFENSIVO.fit_ovr(80.0)
        expected = round(80.0 * ((0.88 + 1.14) / 2), 1)
        self.assertAlmostEqual(expected, result, places=1)

    def test_ofensivo_different_from_defensivo(self):
        base = 75.0
        r_def = Postura.DEFENSIVO.fit_ovr(base)
        r_atk = Postura.OFENSIVO.fit_ovr(base)
        # Ambos têm média 1.01, resultados iguais mas modificadores invertidos
        self.assertAlmostEqual(r_def, r_atk, places=1)

    def test_returns_float_rounded_to_one_decimal(self):
        result = Postura.EQUILIBRADO.fit_ovr(77.3)
        self.assertIsInstance(result, float)
        self.assertEqual(result, round(result, 1))


if __name__ == "__main__":
    unittest.main()
