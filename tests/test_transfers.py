import unittest

from models import Position
from transfers import AuctionItem, TransferMarket, player_bid
from tests.helpers import make_player, make_team


class TransferTests(unittest.TestCase):
    def test_ai_bidding_respects_blocked_team_ids(self):
        origin_player = make_player(1, "Origem ST", Position.ATK, 80)
        origin = make_team(1, "Origem", division=1, players=[origin_player])
        blocked = make_team(2, "Bloqueado", division=1, players=[])
        allowed = make_team(3, "Permitido", division=1, players=[])

        blocked.caixa = 1_000_000
        allowed.caixa = 1_000_000
        origin.caixa = 1_000_000

        market = TransferMarket(
            auctions=[
                AuctionItem(
                    player=origin_player,
                    origin_team=origin,
                    base_bid=100,
                    current_bid=100,
                )
            ]
        )

        market.ai_bidding([origin, blocked, allowed], blocked_team_ids={blocked.id})
        bidder = market.auctions[0].current_bidder
        self.assertNotEqual(blocked.id, bidder.id if bidder else None)

    def test_player_bid_rejects_low_bid_and_accepts_higher_bid(self):
        player = make_player(5, "Atleta", Position.ATK, 75)
        origin = make_team(1, "Origem", players=[player])
        buyer = make_team(2, "Comprador", players=[])
        buyer.caixa = 10_000

        market = TransferMarket(
            auctions=[
                AuctionItem(
                    player=player,
                    origin_team=origin,
                    base_bid=500,
                    current_bid=500,
                )
            ]
        )

        ok, _ = player_bid(market, 0, buyer, 500)
        self.assertFalse(ok)

        ok, _ = player_bid(market, 0, buyer, 600)
        self.assertTrue(ok)
        self.assertEqual(600, market.auctions[0].current_bid)
        self.assertEqual(buyer.id, market.auctions[0].current_bidder.id)

    def test_resolve_preserves_minimum_squad_size(self):
        players = [make_player(i, f"P{i}", Position.ATK, 65) for i in range(1, 17)]
        origin = make_team(1, "Origem", players=players)
        auction = AuctionItem(
            player=players[0],
            origin_team=origin,
            base_bid=100,
            current_bid=100,
        )
        message, value = auction.resolve()

        self.assertEqual(0, value)
        self.assertIn("elenco mínimo", message.lower())
        self.assertEqual(16, len(origin.players))


if __name__ == "__main__":
    unittest.main()

