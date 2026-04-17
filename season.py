"""
ClassicFoot - Gerenciamento da Temporada
Liga (4 divisões) + Copa mata-mata + Finanças
"""
import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from models import Team, Fixture, CupTie, MatchResult
from engine import simulate_match, simulate_penalty_shootout, simulate_all_fixtures_in_round

# ═══════════════════════════════════════════════════════════════
# PRÊMIOS FINANCEIROS (R$ mil)
# ═══════════════════════════════════════════════════════════════
def _build_gradual_liga_prizes(top_prize: int = 250, bottom_prize: int = 30) -> Dict[int, Dict[int, int]]:
    """
    Gera uma tabela gradual de premiação para 4 divisões x 8 posições.
    Valores em R$ mil.
    """
    total_slots = 32
    step = (top_prize - bottom_prize) / max(1, total_slots - 1)
    values = [int(round(top_prize - (idx * step))) for idx in range(total_slots)]

    prizes: Dict[int, Dict[int, int]] = {1: {}, 2: {}, 3: {}, 4: {}}
    cursor = 0
    for division in [1, 2, 3, 4]:
        for position in range(1, 9):
            prizes[division][position] = values[cursor]
            cursor += 1
    return prizes


PRIZE_LIGA = _build_gradual_liga_prizes(top_prize=12_000, bottom_prize=2_500)
PRIZE_COPA = {
    "primeira_fase":    600,
    "oitavas":        1_600,
    "quartas":        4_000,
    "semi":           8_000,
    "final":         15_000,
    "campeão":       35_000,
    "vice":          15_000,
}
PRIZE_BEST_ATTACK = 3_000
PRIZE_BEST_DEFENSE = 3_000
CUSTO_MANUTENCAO = 80   # R$ mil/mês por estádio
BASE_PRIZE_YEAR = 2025

SPONSOR_BASE_BY_DIV = {
    1: 3_000,  # R$ mil/mês
    2: 1_800,
    3: 1_000,
    4: 600,
}


def _season_prize_multiplier(year: int) -> float:
    """
    Premiação cresce 5% a cada temporada (correção monetária realista).
    2025 = 1.00, 2030 = 1.28, 2035 = 1.63
    """
    seasons_passed = max(0, year - BASE_PRIZE_YEAR)
    return 1.05 ** seasons_passed


def stadium_maintenance_cost(team: "Team") -> int:
    """Custo de manutenção do estádio por ciclo de faturamento (≈ 1 mês).
    Escala com o nível do estádio: nível 1 = R$80k, cada nível adicional +R$20k.
    """
    return CUSTO_MANUTENCAO + (team.stadium_level - 1) * 20


def monthly_sponsorship(team: Team) -> int:
    """
    Aporte mensal de patrocínio baseado em:
    - Divisão (base)
    - Prestígio
    - Torcida
    Valor em R$ mil/mês.
    """
    base = SPONSOR_BASE_BY_DIV.get(team.division, 500)
    prestige_factor = 0.65 + (team.prestige / 100.0)  # 0.85..1.65 tipicamente
    fan_factor = max(0.70, min(2.40, team.torcida / 3_000_000))
    sponsor_market = int(round(base * prestige_factor * fan_factor))

    # Piso próximo da folha salarial para evitar patrocínio irrealmente baixo.
    # Em divisões menores fica levemente abaixo da folha; nas maiores pode aproximar/superar.
    folha = int(team.salario_mensal or 0)
    if folha <= 0:
        folha = int(sum(max(0, int(getattr(player, "salario", 0))) for player in team.players))
    coverage_by_div = {
        1: 1.00,
        2: 0.95,
        3: 0.90,
        4: 0.85,
    }
    coverage = coverage_by_div.get(team.division, 0.85)
    floor_near_payroll = int(round(folha * coverage))

    sponsor = max(sponsor_market, floor_near_payroll)
    return max(250, sponsor)


# ═══════════════════════════════════════════════════════════════
# TABELA DE CLASSIFICAÇÃO
# ═══════════════════════════════════════════════════════════════
def sort_standings(teams: List[Team], copa: bool = False) -> List[Team]:
    """Ordena por pontos → vitórias → saldo → gols pró → nome."""
    def key(t: Team):
        if copa:
            return (-t.copa_points, -t.copa_wins, -t.copa_gd, -t.copa_gf, t.name)
        return (-t.div_points, -t.div_wins, -t.div_gd, -t.div_gf, t.name)
    return sorted(teams, key=key)


# ═══════════════════════════════════════════════════════════════
# GERAÇÃO DO CALENDÁRIO
# ═══════════════════════════════════════════════════════════════
def _round_robin(teams: List[Team]) -> List[List[Tuple[Team, Team]]]:
    """
    Gera todos os confrontos de todos contra todos (2 turnos).
    Retorna lista de rodadas, cada rodada é uma lista de (casa, fora).
    """
    n = len(teams)
    if n % 2 != 0:
        teams = teams + [None]   # BYE
        n += 1

    rounds = []
    for r in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            j = n - 1 - i
            t1 = teams[i]
            t2 = teams[j]
            if t1 is not None and t2 is not None:
                round_matches.append((t1, t2))
        rounds.append(round_matches)
        # Rotacionar: fixa teams[0], rotaciona o resto
        teams = [teams[0]] + [teams[-1]] + teams[1:-1]

    # 2º turno: invertendo mandante/visitante
    second_leg = [[(b, a) for (a, b) in r] for r in rounds]
    return rounds + second_leg


# ═══════════════════════════════════════════════════════════════
# DADOS DE UMA TEMPORADA
# ═══════════════════════════════════════════════════════════════
@dataclass
class Season:
    year: int
    all_teams: List[Team]
    player_team_id: int   # ID do time controlado pelo jogador

    # Fixtures gerados
    league_fixtures: List[Fixture] = field(default_factory=list)  # todas as divs
    # Histórico de resultados
    results_history: List[MatchResult] = field(default_factory=list)

    # Calendário: lista ordenada de rodadas
    # Cada item: {"label": str, "fixtures": List[Fixture], "ties": List[CupTie]}
    calendar: List[dict] = field(default_factory=list)
    current_matchday: int = 0   # índice no calendar
    season_over: bool = False

    # Copa — fases eliminatórias
    copa_primeira_fase: List[CupTie] = field(default_factory=list)
    copa_oitavas:  List[CupTie] = field(default_factory=list)
    copa_quartas:  List[CupTie] = field(default_factory=list)
    copa_semi:     List[CupTie] = field(default_factory=list)
    copa_final:    Optional[CupTie] = None
    copa_champion: Optional[Team] = None

    # Artilheiro/premiações calculados no fim
    top_scorers: List[Tuple[str, str, int]] = field(default_factory=list)
    division_champions: Dict[int, str] = field(default_factory=dict)
    division_champion_coaches: Dict[int, str] = field(default_factory=dict)
    best_team_goals: Dict[str, int | str] = field(default_factory=dict)
    best_player_goals: Dict[str, int | str] = field(default_factory=dict)
    max_attendance: Dict[str, int | str] = field(default_factory=dict)
    max_income: Dict[str, int | str] = field(default_factory=dict)
    final_positions: Dict[int, Dict[str, int]] = field(default_factory=dict)
    shown_cup_draws: List[str] = field(default_factory=list)


def create_season(year: int, all_teams: List[Team], player_team_id: int) -> Season:
    """Inicializa uma temporada completa com calendário e Copa."""
    season = Season(year=year, all_teams=all_teams, player_team_id=player_team_id)

    # Pré-temporada: para temporadas já iniciadas, aplica variação suave de OVR (máx. +-2).
    if any(p.partidas_total > 0 for t in all_teams for p in t.players):
        _apply_offseason_ovr_adjustment(all_teams)

    # Reset stats
    for t in all_teams:
        t.reset_season_stats()
        t.training_round_applied = -1
        for p in t.players:
            p.season_base_ovr = float(p.overall)
    for t in all_teams:
        _auto_salary_market(t)

    # Rebalanceamento inicial de OVR por divisão:
    # aplicar somente no início da carreira para evitar quedas bruscas a cada nova temporada.
    if all(p.partidas_total == 0 for t in all_teams for p in t.players):
        _clamp_division_ovr(all_teams)

    # Divisões
    divs = {1: [], 2: [], 3: [], 4: []}
    for t in all_teams:
        divs[t.division].append(t)

    # Gera fixtures de liga para cada divisão
    league_fixtures: List[Fixture] = []
    div_rounds: Dict[int, List[List[Tuple[Team, Team]]]] = {}
    for d, teams in divs.items():
        rounds = _round_robin(teams)
        div_rounds[d] = rounds
        md = 1
        for rnd in rounds:
            for (home, away) in rnd:
                league_fixtures.append(
                    Fixture(home, away, "Liga", md)
                )
            md += 1
    season.league_fixtures = league_fixtures

    # Sorteio da Copa: 32 clubes em mata-mata, ida e volta até a final
    season.copa_primeira_fase = _draw_knockout_round(all_teams, "primeira_fase", single_leg=False)
    for team in all_teams:
        team.copa_phase = "primeira_fase"

    calendar = []
    liga_by_round: Dict[int, List[Fixture]] = {}
    for f in league_fixtures:
        liga_by_round.setdefault(f.matchday, []).append(f)

    cup_slots = {
        1: ("copa_primeira_fase", "1ª Fase", 1),
        2: ("copa_primeira_fase", "1ª Fase", 2),
        4: ("copa_oitavas", "Oitavas", 1),
        5: ("copa_oitavas", "Oitavas", 2),
        7: ("copa_quartas", "Quartas", 1),
        8: ("copa_quartas", "Quartas", 2),
        10: ("copa_semi", "Semifinal", 1),
        11: ("copa_semi", "Semifinal", 2),
        14: ("copa_final", "Final", 1),
        15: ("copa_final", "Final", 2),
    }

    max_round = max(max(liga_by_round.keys()), max(cup_slots.keys()))
    for round_num in range(1, max_round + 1):
        if round_num in liga_by_round:
            calendar.append({
                "label": f"Rodada {round_num} — Liga",
                "type": "liga",
                "round_num": round_num,
                "fixtures": liga_by_round[round_num],
                "ties": [],
            })
        if round_num in cup_slots:
            cup_type, cup_label, leg = cup_slots[round_num]
            calendar.append({
                "label": f"{cup_label} da Copa — {'Ida' if leg == 1 else 'Volta'}",
                "type": cup_type,
                "round_num": round_num,
                "fixtures": [],
                "ties": getattr(season, cup_type),
                "cup_leg": leg,
            })

    season.calendar = calendar
    return season


def _draw_knockout_round(teams: List[Team], phase: str, single_leg: bool) -> List[CupTie]:
    shuffled = list(teams)
    random.shuffle(shuffled)
    ties = []
    for idx in range(0, len(shuffled), 2):
        ties.append(CupTie(shuffled[idx], shuffled[idx + 1], phase, single_leg=single_leg))
    return ties


def _auto_salary_market(t: Team):
    """Calcula salário e valor de mercado dos jogadores automaticamente."""
    for p in t.players:
        ovr = p.overall
        # Salário em R$ mil/mês (log-scale)
        if ovr >= 88:
            sal = random.randint(3500, 7000)
        elif ovr >= 82:
            sal = random.randint(1200, 3500)
        elif ovr >= 76:
            sal = random.randint(450, 1200)
        elif ovr >= 70:
            sal = random.randint(150, 450)
        elif ovr >= 64:
            sal = random.randint(70, 150)
        else:
            sal = random.randint(30, 70)
        p.salario = sal

        # Valor de mercado: salário × 36, sem fator etário.
        p.valor_mercado = int(sal * 36 / 10) * 10

        # Contrato inicial: rodadas restantes (variado para criar leilões ao longo da temporada)
        # Temporada dura ~24 rodadas; contratos escalonados
        p.contrato_rodadas = random.randint(4, 24)


def _clamp_division_ovr(teams: List[Team]):
    """
    Reescala OVRs dos jogadores por divisão usando interpolação linear.
    Mantém a distribuição relativa (melhor jogador continua melhor)
    mas mapeia tudo para o intervalo correto da divisão.
    """
    target_ranges = {
        1: (72, 97),   # Div 1: elite
        2: (56, 82),   # Div 2: bons
        3: (38, 68),   # Div 3: médios
        4: (18, 52),   # Div 4: fracos
    }

    divs: Dict[int, List] = {1: [], 2: [], 3: [], 4: []}
    for t in teams:
        divs[t.division].append(t)

    for div, div_teams in divs.items():
        if not div_teams:
            continue
        t_min, t_max = target_ranges.get(div, (10, 99))
        all_players = [p for t in div_teams for p in t.players]
        if not all_players:
            continue
        src_min = min(p.overall for p in all_players)
        src_max = max(p.overall for p in all_players)
        src_range = src_max - src_min if src_max != src_min else 1
        t_range = t_max - t_min
        for p in all_players:
            # Normaliza para [0,1] e mapeia para [t_min, t_max]
            normalized = (p.overall - src_min) / src_range
            p.overall = round(t_min + normalized * t_range, 1)


def _apply_offseason_ovr_adjustment(teams: List[Team]):
    """
    Ajuste entre temporadas: preserva a evolução da temporada anterior,
    mudando no máximo +-2 no início da nova temporada.
    """
    for team in teams:
        for player in team.players:
            delta = random.uniform(-2.0, 2.0)
            player.overall = round(max(10, min(99, player.overall + delta)), 1)


def advance_season_after_matchday(season: Season):
    """Avança ponteiros e efeitos de fim de rodada após resultados já aplicados."""
    season.current_matchday += 1

    _check_advance_copa_knockout(season)

    if season.current_matchday >= len(season.calendar):
        season.season_over = True
        _end_of_season(season)

    if season.current_matchday % 4 == 0:
        for t in season.all_teams:
            t.caixa -= stadium_maintenance_cost(t)


def _check_advance_copa_knockout(season: Season):
    """Avança as fases após cada rodada de mata-mata."""
    if season.copa_primeira_fase and not season.copa_oitavas:
        first_phase_done = all(tie.leg1 is not None and tie.leg2 is not None for tie in season.copa_primeira_fase)
        if first_phase_done:
            winners = []
            for tie in season.copa_primeira_fase:
                winner = tie.winner()
                if winner is None:
                    winner = simulate_penalty_shootout(tie.team_a, tie.team_b)
                    tie.set_penalty_winner(winner)
                winners.append(winner)
                winner.copa_phase = "oitavas"
            season.copa_oitavas = _draw_knockout_round(winners, "oitavas", single_leg=False)
            for md in season.calendar:
                if md["type"] == "copa_oitavas":
                    md["ties"] = season.copa_oitavas

    # Oitavas → Quartas
    if season.copa_oitavas and not season.copa_quartas:
        oitavas_done = all(t.leg1 is not None and t.leg2 is not None for t in season.copa_oitavas)
        if oitavas_done:
            winners = []
            for tie in season.copa_oitavas:
                w = tie.winner()
                if w is None:
                    w = simulate_penalty_shootout(tie.team_a, tie.team_b)
                    tie.set_penalty_winner(w)
                winners.append(w)
                w.copa_phase = "quartas"
            season.copa_quartas = _draw_knockout_round(winners, "quartas", single_leg=False)
            for md in season.calendar:
                if md["type"] == "copa_quartas":
                    md["ties"] = season.copa_quartas

    # Quartas → Semi
    if season.copa_quartas and not season.copa_semi:
        quartas_done = all(t.leg1 is not None and t.leg2 is not None for t in season.copa_quartas)
        if quartas_done:
            winners = []
            for tie in season.copa_quartas:
                w = tie.winner()
                if w is None:
                    w = simulate_penalty_shootout(tie.team_a, tie.team_b)
                    tie.set_penalty_winner(w)
                winners.append(w)
                w.copa_phase = "semi"
            season.copa_semi = _draw_knockout_round(winners, "semi", single_leg=False)
            for md in season.calendar:
                if md["type"] == "copa_semi":
                    md["ties"] = season.copa_semi

    if season.copa_semi and season.copa_final is None:
        semi_done = all(t.leg1 is not None and t.leg2 is not None for t in season.copa_semi)
        if semi_done:
            finalists = []
            for tie in season.copa_semi:
                w = tie.winner()
                if w is None:
                    w = simulate_penalty_shootout(tie.team_a, tie.team_b)
                    tie.set_penalty_winner(w)
                finalists.append(w)
            if len(finalists) >= 2:
                for f in finalists:
                    f.copa_phase = "final"
                final = CupTie(finalists[0], finalists[1], "final", single_leg=False)
                season.copa_final = final
                for md in season.calendar:
                    if md["type"] == "copa_final":
                        md["ties"] = [final]
    if season.copa_final and season.copa_final.leg1 is not None and season.copa_final.leg2 is not None:
        winner = season.copa_final.winner()
        if winner is None:
            winner = simulate_penalty_shootout(season.copa_final.team_a, season.copa_final.team_b)
            season.copa_final.set_penalty_winner(winner)
        season.copa_champion = winner
        winner.copa_phase = "campeão"


# ═══════════════════════════════════════════════════════════════
# FIM DE TEMPORADA: PREMIAÇÃO E PROMOÇÃO/REBAIXAMENTO
# ═══════════════════════════════════════════════════════════════
def _end_of_season(season: Season):
    """Distribui prêmios, promoção/rebaixamento, artilheiros."""
    prize_multiplier = _season_prize_multiplier(season.year)
    divs = {1: [], 2: [], 3: [], 4: []}
    for t in season.all_teams:
        divs[t.division].append(t)

    # Prêmios por posição e vitórias na liga
    for div, teams in divs.items():
        ranked = sort_standings(teams)
        if ranked:
            season.division_champions[div] = ranked[0].name
            season.division_champion_coaches[div] = ranked[0].coach.name
        for pos, ranked_team in enumerate(ranked, start=1):
            season.final_positions[ranked_team.id] = {"division": div, "position": pos}
        for pos, t in enumerate(ranked, start=1):
            prize = PRIZE_LIGA.get(div, {}).get(pos, 0)
            t.caixa += int(round(prize * prize_multiplier))

    # Prêmio copa
    _award_copa_prizes(season)

    # Encontra artilheiro e distribui bônus
    top_scorer = None
    max_goals = 0
    for t in season.all_teams:
        for p in t.players:
            if p.gols_temp > max_goals:
                max_goals = p.gols_temp
                top_scorer = (p, t)

    if top_scorer:
        player, team = top_scorer
        team.caixa += int(round(500 * prize_multiplier))  # bônus acompanha inflação da premiação
        player.overall = min(99, player.overall + 1)  # +1 OVR para o artilheiro
        season.best_player_goals = {"player": player.name, "team": team.name, "goals": player.gols_temp}

    # Melhor ataque da temporada (mais gols pró na liga).
    best_attack_team = max(season.all_teams, key=lambda club: (club.div_gf, club.div_gd, -club.div_ga))
    best_attack_team.caixa += int(round(PRIZE_BEST_ATTACK * prize_multiplier))
    season.best_team_goals = {"team": best_attack_team.name, "goals": best_attack_team.div_gf}

    # Melhor defesa da temporada (menos gols sofridos na liga).
    best_defense_team = min(season.all_teams, key=lambda club: (club.div_ga, -club.div_gd, -club.div_gf))
    best_defense_team.caixa += int(round(PRIZE_BEST_DEFENSE * prize_multiplier))

    if season.results_history:
        max_att = max(season.results_history, key=lambda result: int(getattr(result, "attendance", 0)))
        season.max_attendance = {
            "attendance": int(getattr(max_att, "attendance", 0)),
            "home": max_att.home_team.name,
            "away": max_att.away_team.name,
            "score": f"{max_att.home_goals}x{max_att.away_goals}",
            "competition": max_att.competition,
            "year": season.year,
        }
        max_inc = max(season.results_history, key=lambda result: int(getattr(result, "income", 0)))
        season.max_income = {
            "income": int(getattr(max_inc, "income", 0)),
            "home": max_inc.home_team.name,
            "away": max_inc.away_team.name,
            "score": f"{max_inc.home_goals}x{max_inc.away_goals}",
            "competition": max_inc.competition,
            "year": season.year,
        }

    # Promoção / Rebaixamento (2 sobem, 2 descem por divisão)
    previous_divisions = {team.id: team.division for team in season.all_teams}
    _apply_promotions(divs)
    _update_support_after_division_change(season.all_teams, previous_divisions)

    # Top artilheiros
    all_players = []
    for t in season.all_teams:
        for p in t.players:
            all_players.append((p.name, t.name, p.gols_temp))
    season.top_scorers = sorted(all_players, key=lambda x: -x[2])[:10]


def _update_support_after_division_change(all_teams: List[Team], previous_divisions: Dict[int, int]):
    """Ajusta torcida/prestígio com base na variação de divisão."""
    for team in all_teams:
        old_div = previous_divisions.get(team.id, team.division)
        new_div = team.division

        if new_div < old_div:
            # Subiu de divisão: torcida cresce e clube ganha visibilidade.
            growth = random.uniform(0.08, 0.18)
            team.torcida = int(team.torcida * (1.0 + growth))
            team.prestige = min(100, team.prestige + random.randint(2, 5))
        elif new_div > old_div:
            # Caiu de divisão: público desanima.
            drop = random.uniform(0.06, 0.14)
            team.torcida = max(80_000, int(team.torcida * (1.0 - drop)))
            team.prestige = max(20, team.prestige - random.randint(2, 5))
        else:
            # Permaneceu: pequeno crescimento orgânico.
            growth = random.uniform(0.005, 0.03)
            team.torcida = int(team.torcida * (1.0 + growth))
            team.prestige = min(100, max(20, team.prestige + random.choice([0, 1])))


def _award_copa_prizes(season: Season):
    prize_multiplier = _season_prize_multiplier(season.year)
    for t in season.all_teams:
        phase = t.copa_phase
        prize = PRIZE_COPA.get(phase, 0)
        t.caixa += int(round(prize * prize_multiplier))


def _apply_promotions(divs: Dict[int, List[Team]]):
    """Top 2 de cada divisão sobe; últimos 2 descem."""
    for div in [1, 2, 3]:
        ranked_this = sort_standings(divs[div])
        ranked_above = sort_standings(divs[div - 1]) if div > 1 else None
        below_div = div + 1

        # Rebaixados desta divisão
        relegated = ranked_this[-2:]
        for t in relegated:
            t.division = below_div

        # Promovidos da divisão de baixo
        if below_div <= 4:
            ranked_below = sort_standings(divs[below_div])
            promoted = ranked_below[:2]
            for t in promoted:
                t.division = div


# ═══════════════════════════════════════════════════════════════
# FINANÇAS: TRANSAÇÕES
# ═══════════════════════════════════════════════════════════════
def pay_monthly_salaries(teams: List[Team]):
    """Paga a folha salarial de todos os times."""
    for t in teams:
        t.caixa += monthly_sponsorship(t)
        total_sal = sum(p.salario for p in t.players)
        t.caixa -= total_sal
        t.salario_mensal = total_sal
        if t.loan_months_left > 0 and t.loan_monthly_payment > 0:
            installment = min(t.loan_balance, t.loan_monthly_payment)
            t.caixa -= installment
            t.loan_balance = max(0, t.loan_balance - installment)
            t.loan_months_left = max(0, t.loan_months_left - 1)
            if t.loan_balance == 0:
                t.loan_monthly_payment = 0
                t.loan_months_left = 0


def sell_player(team: Team, player_index: int) -> Tuple[bool, str, int]:
    """Vende um jogador. Retorna (sucesso, mensagem, valor)."""
    if player_index >= len(team.players):
        return False, "Jogador inválido.", 0
    p = team.players[player_index]
    valor = p.valor_mercado
    team.players.pop(player_index)
    team.caixa += valor
    return True, f"{p.name} vendido por R$ {valor:,} mil.", valor


def buy_player(team: Team, player, price: int) -> Tuple[bool, str]:
    """Contrata um jogador livre."""
    if team.caixa < price:
        return False, f"Caixa insuficiente (R$ {team.caixa:,} mil disponíveis)."
    if len(team.players) >= 45:
        return False, "Elenco já está no limite de 45 jogadores."
    team.caixa -= price
    team.players.append(player)
    return True, f"{player.name} contratado por R$ {price:,} mil."


def take_loan(team: Team, amount: int, months: int = 12) -> Tuple[bool, str]:
    """O clube toma um empréstimo com 3% ao mês."""
    if amount <= 0:
        return False, "Valor inválido."
    total_due = int(round(amount * ((1.03) ** months)))
    monthly_payment = max(1, math.ceil(total_due / months))
    team.caixa += amount
    team.loan_balance += total_due
    team.loan_monthly_payment += monthly_payment
    team.loan_months_left = max(team.loan_months_left, months)
    return True, (
        f"Empréstimo de R$ {amount:,} mil recebido. "
        f"Saldo devedor: R$ {team.loan_balance:,} mil em até {team.loan_months_left} meses "
        f"(parcela: R$ {team.loan_monthly_payment:,} mil)."
    )


def settle_loan(team: Team) -> Tuple[bool, str]:
    """Quita o empréstimo à vista com juros reduzidos."""
    if team.loan_balance <= 0:
        return False, "O clube não possui empréstimos ativos."
    payoff = max(1, int(round(team.loan_balance * 0.97)))
    if team.caixa < payoff:
        return False, f"Caixa insuficiente para quitar. Necessário: R$ {payoff:,} mil."
    team.caixa -= payoff
    team.loan_balance = 0
    team.loan_monthly_payment = 0
    team.loan_months_left = 0
    return True, f"Empréstimo quitado à vista por R$ {payoff:,} mil."
