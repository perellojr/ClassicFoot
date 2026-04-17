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


def sale_price(player: Player) -> int:
    """Preço de venda direta do jogador (acima do valor de mercado)."""
    bonus_factor = 1.30 if getattr(player, "is_star", False) else 1.18
    return int(round(player.valor_mercado * bonus_factor))


@dataclass
class AuctionItem:
    player: Player
    origin_team: Team
    base_bid: int         # 50% do valor de mercado
    current_bid: int      # lance mais alto atual
    current_bidder: Optional[Team] = None
    resolved: bool = False
    manual_listing: bool = False

    def accept_bid(self, team: Team, amount: int) -> bool:
        if team.caixa < 0:
            return False
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
        if len(self.origin_team.players) <= 16:
            self.player.salario = int(self.player.salario * 1.30)
            self.player.contrato_rodadas = 20
            return (
                f"{self.origin_team.name} manteve {self.player.name} para preservar elenco mínimo (16). "
                f"Renovação automática por 20 rodadas com salário de R${self.player.salario:,} mil/mês.",
                0,
            )
        if self.current_bidder is None:
            if self.manual_listing:
                return (
                    f"Nenhum clube se interessou por {self.player.name}. "
                    f"O jogador permanece no {self.origin_team.name}.",
                    0,
                )
            # Ninguém fez oferta → renova com origem
            self.player.salario = int(self.player.salario * 1.20)
            self.player.contrato_rodadas = 12
            return (
                f"Nenhuma proposta. {self.player.name} renova com "
                f"{self.origin_team.name} por +20% (R${self.player.salario:,} mil/mês).",
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
                f"{buyer.name} contratou {self.player.name} por "
                f"R${self.current_bid:,} mil (salário: R${self.player.salario:,} mil/mês).",
                self.current_bid,
            )


@dataclass
class TransferMarket:
    auctions: List[AuctionItem] = field(default_factory=list)
    history: List[str]          = field(default_factory=list)   # log de transações
    bid_stats_by_ovr_bucket: dict = field(default_factory=dict)  # {"70-79": {"count": 3, "sum": 9000}}
    transfer_records: List[dict] = field(default_factory=list)   # histórico estruturado da temporada

    @staticmethod
    def ovr_bucket_label(ovr_value: int) -> str:
        ovr = max(0, min(99, int(ovr_value)))
        start = (ovr // 10) * 10
        end = 99 if start == 90 else start + 9
        return f"{start:02d}-{end:02d}"

    @staticmethod
    def estimated_average_for_bucket(bucket_label: str) -> int:
        """
        Estimativa inicial em R$ mil para quando ainda não houver histórico na faixa.
        """
        try:
            start = int(str(bucket_label).split("-")[0])
        except Exception:
            start = 50
        # Escada simples por faixa de OVR (10 em 10).
        table = {
            0: 60,
            10: 120,
            20: 220,
            30: 380,
            40: 650,
            50: 1_050,
            60: 1_700,
            70: 2_700,
            80: 4_300,
            90: 6_800,
        }
        return int(table.get(start, 1_200))

    def average_bid_for_ovr(self, ovr_value: int) -> int:
        bucket = self.ovr_bucket_label(ovr_value)
        stats = dict(getattr(self, "bid_stats_by_ovr_bucket", {}) or {})
        item = stats.get(bucket, {}) if isinstance(stats.get(bucket, {}), dict) else {}
        count = int(item.get("count", 0) or 0)
        total = int(item.get("sum", 0) or 0)
        if count > 0 and total > 0:
            return int(round(total / count))
        return self.estimated_average_for_bucket(bucket)

    def _record_resolved_bid(self, player: Player, final_value: int):
        if final_value <= 0:
            return
        stats = dict(getattr(self, "bid_stats_by_ovr_bucket", {}) or {})
        bucket = self.ovr_bucket_label(int(round(getattr(player, "overall", 50))))
        item = stats.get(bucket)
        if not isinstance(item, dict):
            item = {"count": 0, "sum": 0}
        item["count"] = int(item.get("count", 0) or 0) + 1
        item["sum"] = int(item.get("sum", 0) or 0) + int(final_value)
        stats[bucket] = item
        self.bid_stats_by_ovr_bucket = stats

    def has_player_in_auction(self, player: Player) -> bool:
        return any((not auction.resolved) and auction.player.id == player.id for auction in self.auctions)

    def list_player_for_auction(self, origin_team: Team, player: Player, min_bid: int | None = None) -> tuple[bool, str]:
        if self.has_player_in_auction(player):
            return False, f"{player.name} já está listado em leilão."
        if len(origin_team.players) <= 16:
            return False, f"Não é possível listar {player.name}: elenco mínimo de 16 jogadores."
        if player not in origin_team.players:
            return False, "Jogador inválido para este clube."

        minimum = max(1, int(min_bid if min_bid is not None else sale_price(player)))
        self.auctions.append(
            AuctionItem(
                player=player,
                origin_team=origin_team,
                base_bid=minimum,
                current_bid=minimum,
                manual_listing=True,
            )
        )
        return True, f"{player.name} foi listado em leilão com lance mínimo de R${minimum:,} mil."

    def generate_auctions(self, all_teams: List[Team]) -> List[AuctionItem]:
        """
        Gera leilões para jogadores com contrato expirando (0 rodadas).
        Goleiro é protegido: se for o único, renova automaticamente.
        1 a 3 leilões simultâneos para não sobrecarregar.
        """
        expired = []
        for team in all_teams:
            for p in team.players:
                p.contrato_rodadas = max(0, p.contrato_rodadas - 1)
                if p.contrato_rodadas == 0:
                    expired.append((team, p))

        # Proteção do goleiro: garante que cada time tenha ao menos 1 GK
        # Se todos os GKs de um time expiraram, o melhor deles é renovado automaticamente
        from collections import defaultdict
        expiring_gks_by_team: dict = defaultdict(list)
        for team, p in expired:
            if p.position == Position.GK:
                expiring_gks_by_team[team.id].append((team, p))

        protected = set()
        for team_id, gk_list in expiring_gks_by_team.items():
            team = gk_list[0][0]
            active_gks = [p for p in team.players
                          if p.position == Position.GK and p.contrato_rodadas > 0]
            if not active_gks:
                # Nenhum GK com contrato ativo → protege o de maior OVR
                best_gk = max(gk_list, key=lambda x: x[1].overall)[1]
                best_gk.salario = int(best_gk.salario * 1.15)
                best_gk.contrato_rodadas = 20
                protected.add(id(best_gk))

        expired = [(t, p) for (t, p) in expired if id(p) not in protected]

        # Quantidade aleatória de leilões simultâneos para variar a rodada
        random.shuffle(expired)
        new_auctions = []
        lot_count = random.randint(1, min(5, len(expired))) if expired else 0
        for team, p in expired[:lot_count]:
            base = int(p.valor_mercado * 0.50)
            auction = AuctionItem(
                player=p,
                origin_team=team,
                base_bid=base,
                current_bid=base,
            )
            new_auctions.append(auction)

        # Mantém leilões manuais já existentes e adiciona novos lotes automáticos sem duplicar jogador.
        existing_active = [auction for auction in self.auctions if not auction.resolved]
        existing_player_ids = {auction.player.id for auction in existing_active}
        merged = list(existing_active)
        for auction in new_auctions:
            if auction.player.id in existing_player_ids:
                continue
            merged.append(auction)
            existing_player_ids.add(auction.player.id)

        self.auctions = merged
        return new_auctions

    def ai_bidding(self, all_teams: List[Team], blocked_team_ids: set[int] | None = None):
        """Simula as propostas automáticas dos clubes da IA."""
        blocked_team_ids = blocked_team_ids or set()
        for auction in self.auctions:
            if auction.resolved:
                continue
            player = auction.player
            # Clubes concorrentes (excluindo a origem)
            candidates = [
                t for t in all_teams
                if t.id != auction.origin_team.id
                and t.id not in blocked_team_ids
                and t.caixa >= 0
                and t.caixa > auction.current_bid * 1.2
                and len(t.players) < 45
            ]
            random.shuffle(candidates)
            for club in candidates[:8]:    # mais clubes tentam para aquecer o mercado
                need = _club_needs_position(club, player.position)
                budget_factor = club.caixa / max(auction.current_bid, 1)
                if (need and budget_factor > 1.15) or (budget_factor > 2.2 and random.random() < 0.45):
                    # Faz proposta com 10-25% de incremento
                    increment = random.uniform(0.10, 0.25)
                    bid = int(auction.current_bid * (1 + increment))
                    if bid <= club.caixa:
                        auction.accept_bid(club, bid)

    def resolve_all(self, round_num: int | None = None) -> List[str]:
        """Encerra todos os leilões ativos e retorna log de resultados."""
        messages = []
        for auction in self.auctions:
            if not auction.resolved:
                msg, final_value = auction.resolve()
                messages.append(msg)
                self.history.append(msg)
                self._record_resolved_bid(auction.player, final_value)
                if final_value > 0 and auction.current_bidder is not None:
                    self.transfer_records.append(
                        {
                            "round": int(round_num or 0),
                            "player": auction.player.name,
                            "from": auction.origin_team.name,
                            "to": auction.current_bidder.name,
                            "value": int(final_value),
                            "salary": int(auction.player.salario),
                        }
                    )
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
    if player_team.caixa < 0:
        return False, "Clube com caixa negativo não pode participar de leilões."
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
    Após recusa de renovação, aplica renovação automática forçada.
    """
    player.salario = max(30, int(player.salario * 1.30))
    player.contrato_rodadas = 20
    return [
        f"{player.name} recusou a proposta. Renovação automática com o {origin_team.name}: "
        f"20 rodadas e salário ajustado para R${player.salario:,} mil/mês."
    ]


def sell_player_to_club(player: Player, origin_team: Team, all_teams: List[Team]) -> Tuple[bool, str, Optional[Team]]:
    if len(origin_team.players) <= 16:
        return False, f"Não é possível vender {player.name}: elenco mínimo de 16 jogadores.", None
    asking_price = sale_price(player)
    candidates = [
        team for team in all_teams
        if team.id != origin_team.id
        and team.caixa >= asking_price
        and len(team.players) < 45
    ]
    random.shuffle(candidates)
    candidates.sort(
        key=lambda team: (
            not _club_needs_position(team, player.position),
            team.division,
            -team.caixa,
        )
    )
    buyer = candidates[0] if candidates else None
    if buyer is None:
        return False, f"Nenhum clube apresentou proposta por {player.name}.", None

    origin_team.players.remove(player)
    buyer.players.append(player)
    buyer.caixa -= asking_price
    origin_team.caixa += asking_price
    player.contrato_rodadas = 16
    player.salario = int(player.salario * 1.10)
    message = f"{player.name} foi vendido para o {buyer.name} por R${asking_price:,} mil."
    return True, message, buyer
