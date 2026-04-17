import unittest

from data import create_teams
from season import create_season


class DataAndSeasonTests(unittest.TestCase):
    def test_create_teams_has_expected_structure(self):
        teams = create_teams()
        self.assertEqual(32, len(teams))

        for division in [1, 2, 3, 4]:
            clubs = [team for team in teams if team.division == division]
            self.assertEqual(8, len(clubs), f"Divisão {division} deveria ter 8 clubes")

        for team in teams:
            self.assertGreaterEqual(len(team.players), 25, f"{team.name} deveria ter ao menos 25 jogadores")
            stars = [player for player in team.players if getattr(player, "is_star", False)]
            self.assertEqual(3, len(stars), f"{team.name} deveria ter exatamente 3 craques")

    def test_create_season_generates_calendar_and_initial_cup_round(self):
        teams = create_teams()
        player_team = next(team for team in teams if team.division == 4)
        season = create_season(2025, teams, player_team.id)

        self.assertEqual(24, len(season.calendar))
        self.assertEqual(16, len(season.copa_primeira_fase))
        self.assertEqual("liga", season.calendar[0]["type"])
        self.assertEqual("copa_primeira_fase", season.calendar[1]["type"])
        self.assertEqual(0, season.current_matchday)
        self.assertFalse(season.season_over)


if __name__ == "__main__":
    unittest.main()

