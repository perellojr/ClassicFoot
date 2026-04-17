import unittest
from unittest.mock import MagicMock, patch

import main
from data import create_teams
from season import create_season


class MainFlowTests(unittest.TestCase):
    def test_maybe_show_pending_cup_draws_shows_draw_then_copa(self):
        teams = create_teams()
        player_team = next(team for team in teams if team.division == 4)
        season = create_season(2025, teams, player_team.id)
        season.shown_cup_draws = []

        with patch("main.show_copa_draw") as mock_draw, patch("main.show_copa") as mock_copa:
            shown = main._maybe_show_pending_cup_draws(season, player_team)

        self.assertTrue(shown)
        self.assertTrue(mock_draw.called)
        self.assertTrue(mock_copa.called)
        self.assertIn("primeira_fase", season.shown_cup_draws)

    def test_play_next_match_blocks_player_team_in_ai_bidding(self):
        teams = create_teams()
        player_team = next(team for team in teams if team.division == 4)
        season = create_season(2025, teams, player_team.id)

        market = MagicMock()
        market.generate_auctions.return_value = [object()]
        market.auctions = [object()]
        market.resolve_all.return_value = []

        with patch("main._matchday_has_player_game", return_value=False), \
             patch("main._play_live_matchday", return_value={"done": True, "matchday_num": season.current_matchday, "type": "liga"}), \
             patch("main.show_transfer_market"), \
             patch("main.show_auction_results"):
            main._play_next_match(season, player_team, market)

        self.assertGreaterEqual(market.ai_bidding.call_count, 1)
        for call in market.ai_bidding.call_args_list:
            kwargs = call.kwargs
            self.assertIn("blocked_team_ids", kwargs)
            self.assertIn(player_team.id, kwargs["blocked_team_ids"])


if __name__ == "__main__":
    unittest.main()

