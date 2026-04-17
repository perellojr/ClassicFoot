import unittest
from unittest.mock import patch

import main
from data import create_teams
from season import create_season


class LongSimulationTests(unittest.TestCase):
    def test_simulate_40_full_seasons_without_crash(self):
        teams = create_teams()
        year = 2025

        # Desliga render ao vivo para teste de estresse ficar rápido.
        with patch("main._play_live_half", new=lambda *args, **kwargs: None):
            for season_index in range(40):
                season = create_season(year, teams, -1)

                safety = 0
                while not season.season_over and safety < 40:
                    main._play_live_matchday(season, None)
                    safety += 1

                self.assertTrue(season.season_over, f"Temporada {year} não encerrou")
                self.assertEqual(24, season.current_matchday, f"Temporada {year} terminou com rodada inesperada")
                self.assertIsNotNone(season.copa_champion, f"Temporada {year} sem campeão da copa")
                self.assertEqual(4, len(season.division_champions), f"Temporada {year} sem campeões de todas divisões")
                self.assertGreater(len(season.results_history), 0, f"Temporada {year} sem resultados")

                # Invariante estrutural: 8 clubes por divisão.
                for division in [1, 2, 3, 4]:
                    clubs = [club for club in teams if club.division == division]
                    self.assertEqual(8, len(clubs), f"Temporada {year}: divisão {division} com tamanho inválido")

                # Invariante de elenco mínimo.
                for club in teams:
                    self.assertGreaterEqual(len(club.players), 16, f"{club.name} ficou abaixo do mínimo de elenco")

                year += 1


if __name__ == "__main__":
    unittest.main()

