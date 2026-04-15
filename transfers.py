"""
ClassicFoot - Mercado de Transferências
Sistema de leilão estilo Elifoot 2.

A cada rodada:
  1. Jogadores com contrato = 0 vão para o leilão
  2. Lance inicial = 50% do valor de mercado
  3. Clubes da IA fazem propostas baseadas em necessidade + caixa
  4. Se alguém vencer: jogador vai para o novo clube com salário +15%
  5. Se ninguém vencer: jogador renova com clube de origem, salário +20%, contrato por 12 rodadas
"""
import random
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from models import Player, Team, Position


@dataclass
class AuctionItem:
    player: Player
    origin_team: Team
    base_bid: int         # 50% do valor de mercado
    current_bid: int      # lance mais alto atual
    current_bidder: Optional[Team] = None
    resolved: bool = False

    def accept_bid(self, team: Team, amount: int) -> bool:
        if amount > self.current_bid and team.caixa >= amount:
            self.current_bid = amount
            self.current_bidder = team
            return True
        return False

    def resolve(self) -> Tuple[str, int]:
        """
        Encerra o leilão.
        Retorna (mensagem, valor_final).
        """
        self.resolved = True
        if self.current_bidder is None:
            # Ninguém fez oferta → renova com origem
            self.player.salario = int(self.player.salario * 1.20)
            self.player.contrato_rodadas = 12
            return (
                f"Nenhuma proposta. {self.player.name} renova com "
                f"{self.origin_team.short_name} por +20% (R${self.player.salario:,} mil/mês).",
                0,
            )
        else:
            # Vencedor leva o jogador
            buyer = self.current_bidder
            buyer.caixa -= self.current_bid
            self.origin_team.players.remove(self.player)
            buyer.players.append(self.player)
            self.player.salario = int(self.player.salario * 1.15)
            self.player.contrato_rodadas = 16
            self.origin_team.caixa += self.current_bid
            return (
                f"{buyer.short_name} contratou {self.player.name} por "
                f"R${self.current_bid:,} mil (salário: R${self.player.salario:,} mil/mês).",
                self.current_bid,
            )


@dataclass
class TransferMarket:
    auctions: List[AuctionItem] = field(default_factory=list)
    history: List[str]          = field(default_factory=list)   # log de transações

    def generate_auctions(self, all_teams: List[Team]) -> List[AuctionItem]:
        """
        Gera leilões para jogadores com contrato expirando (0 rodadas).
        1 a 3 jogadores por rodada.
        """
        expired = []
        for team in all_teams:
            for p in team.players:
                p.contrato_rodadas = max(0, p.contrato_rodadas - 1)
                if p.contrato_rodadas == 0:
                    expired.append((team, p))

        # Máximo de 3 leilões simultâneos para não sobrecarregar
        random.shuffle(expired)
        new_auctions = []
        for team, p in expired[:3]:
            base = int(p.valor_mercado * 0.50)
            auction = AuctionItem(
                player=p,
                origin_team=team,
                base_bid=base,
                current_bid=base,
            )
            new_auctions.append(auction)

        self.auctions = new_auctions
        return new_auctions

    def ai_bidding(self, all_teams: List[Team]):
        """Simula as propostas automáticas dos clubes da IA."""
        for auction in self.auctions:
            if auction.resolved:
                continue
            player = auction.player
            # Clubes concorrentes (excluindo a origem)
            candidates = [
                t for t in all_teams
                if t.id != auction.origin_team.id
                and t.caixa > auction.current_bid * 1.2
                and len(t.players) < 30
            ]
            random.shuffle(candidates)
            for club in candidates[:4]:    # máx 4 clubes tentam
                need = _club_needs_position(club, player.position)
                budget_factor = club.caixa / max(auction.current_bid, 1)
                if need and budget_factor > 1.3:
                    # Faz proposta com 10-25% de incremento
                    increment = random.uniform(0.10, 0.25)
                    bid = int(auction.current_bid * (1 + increment))
                    if bid <= club.caixa:
                        auction.accept_bid(club, bid)

    def resolve_all(self) -> List[str]:
        """Encerra todos os leilões ativos e retorna log de resultados."""
        messages = []
        for auction in self.auctions:
            if not auction.resolved:
                msg, _ = auction.resolve()
                messages.append(msg)
                self.history.append(msg)
        self.auctions = []
        return messages


def _club_needs_position(team: Team, pos: Position) -> bool:
    """Verifica se o clube precisa de jogador nessa posição."""
    count = sum(1 for p in team.players if p.position == pos)
    minimums = {Position.GK: 2, Position.DEF: 5, Position.MID: 5, Position.ATK: 4}
    return count < minimums.get(pos, 3)


def player_bid(
    market: TransferMarket,
    auction_index: int,
    player_team: Team,
    bid_amount: int,
) -> Tuple[bool, str]:
    """
    O jogador (humano) faz uma proposta.
    Retorna (sucesso, mensagem).
    """
    if auction_index >= len(market.auctions):
        return False, "Leilão inválido."
    auction = market.auctions[auction_index]
    if auction.resolved:
        return False, "Este leilão já foi encerrado."
    if bid_amount <= auction.current_bid:
        return False, f"Lance deve ser maior que R$ {auction.current_bid:,} mil."
    if player_team.caixa < bid_amount:
        return False, f"Caixa insuficiente (R$ {player_team.caixa:,} mil disponíveis)."
    auction.accept_bid(player_team, bid_amount)
    return True, f"Lance de R$ {bid_amount:,} mil aceito para {auction.player.name}."


def negotiate_contract(player: Player, offered_salary: int) -> Tuple[bool, str]:
    """
    Tenta renovar contrato de um jogador.
    Salários maiores aumentam a chance de aceitar; menores aumentam a chance de recusar.
    """
    current_salary = max(1, player.salario)
    ratio = offered_salary / current_salary
    accept_chance = max(0.05, min(0.95, 0.20 + ((ratio - 0.70) * 1.10)))

    if random.random() < accept_chance:
        player.salario = offered_salary
        player.contrato_rodadas = 15
        return True, (
            f"{player.name} aceitou renovar por R${offered_salary:,} mil/mês "
            f"até o fim de 15 rodadas."
        )

    return False, (
        f"{player.name} recusou a renovação por R${offered_salary:,} mil/mês."
    )


def run_immediate_contract_auction(player: Player, origin_team: Team, all_teams: List[Team]) -> List[str]:
    """
    Coloca o jogador imediatamente em leilão após recusa de renovação.
    Se ninguém comprar, ele renova automaticamente com 20% menos por 15 rodadas.
    """
    auction = AuctionItem(
        player=player,
        origin_team=origin_team,
        base_bid=int(player.valor_mercado * 0.50),
        current_bid=int(player.valor_mercado * 0.50),
    )

    market = TransferMarket(auctions=[auction])
    market.ai_bidding(all_teams)

    if auction.current_bidder is None:
        player.salario = max(30, int(player.salario * 0.80))
        player.contrato_rodadas = 15
        msg = (
            f"Nenhum clube levou {player.name} no leilão imediato. "
            f"Ele renovou automaticamente com o {origin_team.short_name} por 15 rodadas "
            f"com salário reduzido para R${player.salario:,} mil/mês."
        )
        return [msg]

    msg, _ = auction.resolve()
    return [msg]
