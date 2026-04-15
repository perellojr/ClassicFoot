"""
ClassicFoot - Modelos de dados do jogo
"""
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Set
from enum import Enum
import math
import random


class Position(Enum):
    GK  = "GOL"
    DEF = "ZAG"
    MID = "MEI"
    ATK = "ATA"


class Formation(Enum):
    F442 = "4-4-2"
    F433 = "4-3-3"
    F352 = "3-5-2"
    F532 = "5-3-2"
    F451 = "4-5-1"
    F4231 = "4-2-3-1"
    F343 = "3-4-3"
    BEST11 = "BEST XI"

    def slots(self) -> dict:
        """Retorna quantos jogadores em cada posição."""
        mapping = {
            Formation.F442:  {Position.GK:1, Position.DEF:4, Position.MID:4, Position.ATK:2},
            Formation.F433:  {Position.GK:1, Position.DEF:4, Position.MID:3, Position.ATK:3},
            Formation.F352:  {Position.GK:1, Position.DEF:3, Position.MID:5, Position.ATK:2},
            Formation.F532:  {Position.GK:1, Position.DEF:5, Position.MID:3, Position.ATK:2},
            Formation.F451:  {Position.GK:1, Position.DEF:4, Position.MID:5, Position.ATK:1},
            Formation.F4231: {Position.GK:1, Position.DEF:4, Position.MID:5, Position.ATK:1},
            Formation.F343:  {Position.GK:1, Position.DEF:3, Position.MID:4, Position.ATK:3},
            Formation.BEST11: {Position.GK:1, Position.DEF:0, Position.MID:0, Position.ATK:0},
        }
        return mapping[self]

    def atk_bias(self) -> float:
        """Fator de viés ofensivo (multiplicador extra no ataque)."""
        return {
            Formation.F442:  1.00,
            Formation.F433:  1.10,
            Formation.F352:  1.02,
            Formation.F532:  0.88,
            Formation.F451:  0.92,
            Formation.F4231: 1.05,
            Formation.F343:  1.14,
            Formation.BEST11: 1.04,
        }[self]

    def def_bias(self) -> float:
        """Fator de viés defensivo."""
        return {
            Formation.F442:  1.00,
            Formation.F433:  0.92,
            Formation.F352:  0.96,
            Formation.F532:  1.15,
            Formation.F451:  1.10,
            Formation.F4231: 0.98,
            Formation.F343:  0.88,
            Formation.BEST11: 0.96,
        }[self]


class Postura(Enum):
    DEFENSIVO   = "Defensivo"
    EQUILIBRADO = "Equilibrado"
    OFENSIVO    = "Ofensivo"

    def modifiers(self) -> tuple:
        """Retorna (bonus_ataque, bonus_defesa)."""
        return {
            Postura.DEFENSIVO:   (0.88, 1.14),
            Postura.EQUILIBRADO: (1.00, 1.00),
            Postura.OFENSIVO:    (1.14, 0.88),
        }[self]


@dataclass
class Player:
    id: int
    name: str
    position: Position
    age: int
    nationality: str
    # Atributos 0-99
    overall: int
    pace: int        # VEL
    technique: int   # TEC
    shooting: int    # FIN
    passing: int     # PAS
    physical: int    # FIS
    defending: int   # DEF
    heading: int     # CAB
    goalkeeping: int # GOL (só para goleiros)


    # Finanças
    salario: int = 100        # salário mensal em R$ mil
    valor_mercado: int = 500  # valor de mercado em R$ mil

    # Status
    suspenso: int = 0           # nº de jogos suspenso (0 = disponível)
    contrato_rodadas: int = 20  # rodadas restantes de contrato

    # Estatísticas da TEMPORADA
    gols_temp: int = 0
    partidas_temp: int = 0
    amarelos_temp: int = 0
    vermelhos_temp: int = 0

    # Estatísticas TOTAIS (carreira)
    gols_total: int = 0
    partidas_total: int = 0
    amarelos_total: int = 0
    vermelhos_total: int = 0
    season_base_ovr: float | None = None

    def pos_label(self) -> str:
        return self.position.value

    def attack_rating(self) -> float:
        """Contribuição ofensiva baseada somente em OVR."""
        return float(self.overall)

    def defense_rating(self) -> float:
        """Contribuição defensiva baseada somente em OVR."""
        return float(self.overall)


@dataclass
class Coach:
    name: str
    nationality: str = "Brasileiro"
    tactical: int = 75    # 0-99
    motivation: int = 75  # 0-99
    experience: int = 75  # 0-99
    reputation: int = 70  # 0-99

    def bonus(self) -> float:
        """Bônus multiplicador para a equipe"""
        avg = (self.tactical + self.motivation + self.experience) / 3
        return 1.0 + (avg - 70) / 500


@dataclass
class Team:
    id: int
    name: str
    short_name: str   # 3 letras
    city: str
    state: str
    stadium: str
    division: int     # 1-4
    prestige: int     # 0-100
    coach: Coach
    players: List[Player] = field(default_factory=list)
    primary_color: str = "green"
    secondary_color: str = "white"

    # Táticas
    formation: Formation = Formation.F442
    postura: Postura = Postura.EQUILIBRADO

    # Finanças e torcida
    torcida: int = 1_000_000      # número de torcedores
    caixa: int = 50_000           # caixa em R$ mil
    salario_mensal: int = 5_000   # folha salarial mensal em R$ mil
    stadium_level: int = 1        # nível de upgrade do estádio (1-5)
    loan_balance: int = 0
    loan_monthly_payment: int = 0
    loan_months_left: int = 0

    # Estatísticas da divisão (temporada)
    div_wins: int = 0
    div_draws: int = 0
    div_losses: int = 0
    div_gf: int = 0
    div_ga: int = 0
    last_results: List[str] = field(default_factory=list)

    # Estatísticas da Copa (grupos)
    copa_wins: int = 0
    copa_draws: int = 0
    copa_losses: int = 0
    copa_gf: int = 0
    copa_ga: int = 0
    copa_group: int = 0          # 1-4
    copa_phase: str = "grupos"   # grupos / oitavas / quartas / semi / final / campeão / eliminado

    @property
    def div_points(self) -> int:
        return self.div_wins * 3 + self.div_draws

    @property
    def div_played(self) -> int:
        return self.div_wins + self.div_draws + self.div_losses

    @property
    def div_gd(self) -> int:
        return self.div_gf - self.div_ga

    @property
    def copa_points(self) -> int:
        return self.copa_wins * 3 + self.copa_draws

    @property
    def copa_played(self) -> int:
        return self.copa_wins + self.copa_draws + self.copa_losses

    @property
    def copa_gd(self) -> int:
        return self.copa_gf - self.copa_ga

    @property
    def stadium_capacity(self) -> int:
        """Estimativa realista de capacidade do estádio, limitada a 60 mil."""
        estimated = max(8_000, int((self.torcida / 250) + (self.prestige * 220)))
        rounded = int(round(estimated / 1000) * 1000)
        return min(60_000, rounded)

    def squad_overall(self) -> float:
        """Média geral do elenco (top 11)"""
        if not self.players:
            return 50.0
        top = sorted(self.players, key=lambda p: p.overall, reverse=True)[:11]
        return sum(p.overall for p in top) / len(top)

    def attack_strength(self) -> float:
        top = sorted(self.players, key=lambda p: p.overall, reverse=True)[:11]
        if not top:
            return 50.0
        raw = sum(p.attack_rating() for p in top) / 11
        return raw * self.coach.bonus()

    def defense_strength(self) -> float:
        top = sorted(self.players, key=lambda p: p.overall, reverse=True)[:11]
        if not top:
            return 50.0
        raw = sum(p.defense_rating() for p in top) / 11
        return raw * self.coach.bonus()

    def reset_season_stats(self):
        self.div_wins = self.div_draws = self.div_losses = 0
        self.div_gf = self.div_ga = 0
        self.last_results = []
        self.copa_wins = self.copa_draws = self.copa_losses = 0
        self.copa_gf = self.copa_ga = 0
        self.copa_phase = "grupos"
        for p in self.players:
            p.gols_temp = p.partidas_temp = 0
            p.amarelos_temp = p.vermelhos_temp = 0


@dataclass
class MatchResult:
    home_team: 'Team'
    away_team: 'Team'
    home_goals: int
    away_goals: int
    home_scorers: List[str] = field(default_factory=list)
    away_scorers: List[str] = field(default_factory=list)
    competition: str = "Liga"
    matchday: int = 0

    def winner(self) -> Optional['Team']:
        if self.home_goals > self.away_goals:
            return self.home_team
        elif self.away_goals > self.home_goals:
            return self.away_team
        return None

    def loser(self) -> Optional['Team']:
        if self.home_goals > self.away_goals:
            return self.away_team
        elif self.away_goals > self.home_goals:
            return self.home_team
        return None

    def score_str(self) -> str:
        return f"{self.home_goals} x {self.away_goals}"

    def full_str(self) -> str:
        return (f"{self.home_team.short_name} {self.home_goals} "
                f"x {self.away_goals} {self.away_team.short_name}")


@dataclass
class Fixture:
    home_team: 'Team'
    away_team: 'Team'
    competition: str    # "Liga" | "Copa"
    matchday: int
    result: Optional[MatchResult] = None

    @property
    def played(self) -> bool:
        return self.result is not None


@dataclass
class CupTie:
    """Jogo de copa (ida/volta ou jogo único)"""
    team_a: 'Team'
    team_b: 'Team'
    phase: str         # "oitavas" | "quartas" | "semi" | "final"
    leg1: Optional[MatchResult] = None
    leg2: Optional[MatchResult] = None
    single_leg: bool = True  # fase final: jogo único
    penalty_winner_id: Optional[int] = None
    penalty_score: Optional[Tuple[int, int]] = None

    def aggregate(self):
        """Retorna (gols_a, gols_b) no agregado"""
        if self.single_leg or self.leg1 is None:
            if self.leg1 is None:
                return (0, 0)
            # leg1: team_a é o mandante
            return (self.leg1.home_goals, self.leg1.away_goals)
        # Dois jogos
        a1 = self.leg1.home_goals  # team_a jogou em casa
        b1 = self.leg1.away_goals
        b2 = self.leg2.home_goals if self.leg2 else 0  # team_b joga em casa na volta
        a2 = self.leg2.away_goals if self.leg2 else 0
        return (a1 + a2, b1 + b2)

    def winner(self) -> Optional['Team']:
        if self.single_leg:
            if self.leg1 is None:
                return None
            if self.leg1.winner() is not None:
                return self.leg1.winner()
            if self.penalty_winner_id == self.team_a.id:
                return self.team_a
            if self.penalty_winner_id == self.team_b.id:
                return self.team_b
            return None
        if self.leg1 is None or self.leg2 is None:
            return None
        a, b = self.aggregate()
        if a > b:
            return self.team_a
        elif b > a:
            return self.team_b
        if self.penalty_winner_id == self.team_a.id:
            return self.team_a
        elif self.penalty_winner_id == self.team_b.id:
            return self.team_b
        return None

    def set_penalty_winner(self, winner: 'Team', score: Tuple[int, int] | None = None):
        self.penalty_winner_id = winner.id
        self.penalty_score = score


@dataclass
class CareerState:
    player_coach: Coach
    current_team_id: int | None
    unemployed: bool = False
    fired: bool = False
    last_fired_team_id: int | None = None
    free_coaches: List[Coach] = field(default_factory=list)
    notifications: List[str] = field(default_factory=list)
    seen_notifications: Set[str] = field(default_factory=set)
    games_in_charge: int = 0
    back_to_main_menu: bool = False
    season_history: List[dict] = field(default_factory=list)
