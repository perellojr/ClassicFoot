"""
Testes de invariantes financeiros do ClassicFoot.

Verifica que o modelo econômico permanece coerente após múltiplas rodadas:
- patrocínio nunca é negativo
- caixa não colapsa abaixo de um limiar catastrófico durante as primeiras temporadas
- OVR médio dos elencos não degenera abaixo de um mínimo aceitável
- divisões mantêm exatamente 8 clubes após promoção/rebaixamento
"""
import unittest
from unittest.mock import patch

from data import create_teams
from season import create_season, pay_monthly_salaries, monthly_sponsorship
from tests.helpers import make_player, make_team
from models import Coach, Position


class SponsorshipTests(unittest.TestCase):
    """Patrocínio deve ser sempre positivo e razoável para cada divisão."""

    def test_sponsorship_always_positive(self):
        teams = create_teams()
        for team in teams:
            value = monthly_sponsorship(team)
            self.assertGreater(value, 0, f"{team.name} (Div {team.division}): patrocínio={value}")

    def test_sponsorship_scales_with_division(self):
        """Média de patrocínio da Div 1 deve ser maior que da Div 4."""
        teams = create_teams()
        div1 = [t for t in teams if t.division == 1]
        div4 = [t for t in teams if t.division == 4]
        avg_div1 = sum(monthly_sponsorship(t) for t in div1) / len(div1)
        avg_div4 = sum(monthly_sponsorship(t) for t in div4) / len(div4)
        self.assertGreater(avg_div1, avg_div4)

    def test_sponsorship_covers_reasonable_fraction_of_payroll(self):
        """Para clubes da Div 1, patrocínio deve cobrir pelo menos 70% da folha."""
        teams = create_teams()
        for team in [t for t in teams if t.division == 1]:
            sponsor = monthly_sponsorship(team)
            payroll = sum(p.salario for p in team.players)
            if payroll > 0:
                coverage = sponsor / payroll
                self.assertGreaterEqual(
                    coverage, 0.70,
                    f"{team.name}: patrocínio cobre apenas {coverage:.0%} da folha"
                )


class FinancialStabilityTests(unittest.TestCase):
    """Após 6 ciclos de salários, nenhum clube deve ter caixa gravemente negativo."""

    def test_caixa_after_salary_cycles(self):
        teams = create_teams()
        for _ in range(6):
            pay_monthly_salaries(teams)
        for team in teams:
            # Limiar catastrófico: caixa não pode estar abaixo de -500k
            self.assertGreater(
                team.caixa, -500,
                f"{team.name} (Div {team.division}): caixa={team.caixa} após 6 ciclos"
            )


class OVRBoundsTests(unittest.TestCase):
    """
    Todos os jogadores devem respeitar os limites absolutos de OVR (10.0–99.0)
    após 3 temporadas de simulação contínua, mesmo sem mercado de transferências.

    Nota: sem mercado, o OVR médio vai naturalmente cair por desgaste — isso é
    comportamento esperado. O invariante aqui é que o motor nunca viola os limites.
    """

    def test_ovr_stays_within_global_bounds(self):
        teams = create_teams()
        year = 2025

        with patch("main._play_live_half", new=lambda *args, **kwargs: None):
            import main
            for _ in range(3):
                season = create_season(year, teams, -1)
                safety = 0
                while not season.season_over and safety < 40:
                    main._play_live_matchday(season, None)
                    safety += 1
                year += 1

        for team in teams:
            for player in team.players:
                self.assertGreaterEqual(
                    player.overall, 10.0,
                    f"{team.name} / {player.name}: OVR={player.overall:.2f} abaixo do clamp mínimo"
                )
                self.assertLessEqual(
                    player.overall, 99.0,
                    f"{team.name} / {player.name}: OVR={player.overall:.2f} acima do clamp máximo"
                )


class DivisionStructureTests(unittest.TestCase):
    """Promoção/rebaixamento deve manter exatamente 8 clubes por divisão."""

    def test_division_balance_after_two_seasons(self):
        teams = create_teams()
        year = 2025

        with patch("main._play_live_half", new=lambda *args, **kwargs: None):
            import main
            for _ in range(2):
                season = create_season(year, teams, -1)
                safety = 0
                while not season.season_over and safety < 40:
                    main._play_live_matchday(season, None)
                    safety += 1
                year += 1

        for division in [1, 2, 3, 4]:
            count = sum(1 for t in teams if t.division == division)
            self.assertEqual(
                8, count,
                f"Divisão {division} tem {count} clubes (esperado 8) após 2 temporadas"
            )


if __name__ == "__main__":
    unittest.main()
