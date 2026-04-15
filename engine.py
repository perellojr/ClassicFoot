"""
ClassicFoot - Motor de simulação de partidas
Estilo Elifoot: resultado rápido, com goleadores
Inclui: formações, postura tática, forma e moral dos jogadores
"""
import math
import random
from typing import List, Tuple
from models import Team, Player, Position, MatchResult, Formation, Postura


# ── Poisson sem numpy ──────────────────────────────────────────
def _poisson(lam: float) -> int:
    lam = max(0.1, min(lam, 8.0))
    L = math.exp(-lam)
    k, p = 0, 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def select_starting_lineup(team: Team) -> List[Player]:
    """Escolhe os 11 titulares com base na formação atual."""
    available = [p for p in team.players if p.suspenso <= 0 and p.condicao_fisica >= 40]
    if len(available) < 11:
        available = [p for p in team.players if p.suspenso <= 0] or list(team.players)

    slots = team.formation.slots()
    lineup: List[Player] = []
    used_ids = set()

    def score(player: Player) -> float:
        return player.overall + player.forma * 0.15 + player.moral * 0.10 + player.condicao_fisica * 0.08

    for position in [Position.GK, Position.DEF, Position.MID, Position.ATK]:
        needed = slots.get(position, 0)
        candidates = [p for p in available if p.position == position and p.id not in used_ids]
        candidates.sort(key=score, reverse=True)
        for player in candidates[:needed]:
            lineup.append(player)
            used_ids.add(player.id)

    if len(lineup) < 11:
        leftovers = [p for p in available if p.id not in used_ids]
        leftovers.sort(key=score, reverse=True)
        lineup.extend(leftovers[: 11 - len(lineup)])

    pos_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
    return sorted(lineup[:11], key=lambda p: (pos_order.get(p.position, 9), -score(p), p.name))


def select_bench(team: Team, starters: List[Player], limit: int = 12) -> List[Player]:
    starter_ids = {p.id for p in starters}
    available = [p for p in team.players if p.id not in starter_ids and p.suspenso <= 0]
    available.sort(key=lambda p: (-(p.overall + p.forma * 0.1 + p.condicao_fisica * 0.1), p.name))
    return available[:limit]


# ── Calcula XG da equipe ───────────────────────────────────────
def _team_xg(team: Team, vs_defense: float, is_home: bool, lineup: List[Player] | None = None) -> float:
    """
    Calcula gols esperados levando em conta:
    - Força do elenco
    - Formação tática (viés ofensivo)
    - Postura (defensivo/equilibrado/ofensivo)
    - Forma + moral dos jogadores
    - Mando de campo
    """
    top11 = lineup[:] if lineup else sorted(
        [p for p in team.players if p.suspenso == 0 and p.condicao_fisica >= 40],
        key=lambda p: p.overall, reverse=True
    )[:11]
    if not top11:
        top11 = sorted(team.players, key=lambda p: p.overall, reverse=True)[:11]

    atk = sum(p.attack_rating() for p in top11) / len(top11) if top11 else team.attack_strength()
    atk *= team.coach.bonus()

    avg_forma  = sum(p.forma  for p in top11) / len(top11) if top11 else 70
    avg_moral  = sum(p.moral  for p in top11) / len(top11) if top11 else 70
    form_factor = ((avg_forma + avg_moral) / 2 - 60) / 200  # -0.3 a +0.2
    atk = atk * (1 + form_factor)

    # Formação
    atk = atk * team.formation.atk_bias()

    # Postura
    atk_mod, _ = team.postura.modifiers()
    atk = atk * atk_mod

    # Mando
    if is_home:
        atk *= 1.08

    base_rate = 1.30
    xg = base_rate * (atk / max(vs_defense, 20.0))
    return max(0.35, min(xg, 5.0))


def _effective_defense(team: Team, is_home: bool, lineup: List[Player] | None = None) -> float:
    top11 = lineup[:] if lineup else sorted(
        [p for p in team.players if p.suspenso == 0 and p.condicao_fisica >= 40],
        key=lambda p: p.overall, reverse=True
    )[:11]
    if not top11:
        top11 = sorted(team.players, key=lambda p: p.overall, reverse=True)[:11]

    dfs = sum(p.defense_rating() for p in top11) / len(top11) if top11 else team.defense_strength()
    dfs *= team.coach.bonus()

    avg_forma = sum(p.forma  for p in top11) / len(top11) if top11 else 70
    avg_moral = sum(p.moral  for p in top11) / len(top11) if top11 else 70
    form_factor = ((avg_forma + avg_moral) / 2 - 60) / 200
    dfs = dfs * (1 + form_factor)

    dfs = dfs * team.formation.def_bias()
    _, def_mod = team.postura.modifiers()
    dfs = dfs * def_mod

    if is_home:
        dfs *= 1.05

    return max(20.0, dfs)


# ── Escolha de goleadores ──────────────────────────────────────
def _weighted_scorers(players: List[Player], num_goals: int) -> List[Player]:
    if num_goals == 0 or not players:
        return []

    weights = []
    for p in players:
        if p.position == Position.ATK:
            w = p.shooting * 1.5 + p.heading * 0.5
        elif p.position == Position.MID:
            w = p.shooting * 0.7 + p.technique * 0.4
        elif p.position == Position.DEF:
            w = p.heading * 0.4 + p.technique * 0.15
        else:
            w = 0.5  # GK raramente marca
        weights.append(max(0.5, w))

    total = sum(weights)
    probs = [w / total for w in weights]

    scorers: List[Player] = []
    for _ in range(num_goals):
        r = random.random()
        cumul = 0.0
        chosen = players[-1]
        for p, prob in zip(players, probs):
            cumul += prob
            if r <= cumul:
                chosen = p
                break
        scorers.append(chosen)
    return scorers


# ── Cartões aleatórios ─────────────────────────────────────────
def _generate_cards(players: List[Player], is_aggressor: bool = False):
    """Sorteia eventualmente amarelos para jogadores."""
    prob_yellow = 0.15 if not is_aggressor else 0.22
    for p in players:
        if random.random() < prob_yellow / 11:
            p.amarelos_temp  += 1
            p.amarelos_total += 1
            if p.amarelos_temp % 3 == 0:   # 3 amarelos → 1 jogo suspenso
                p.suspenso = max(p.suspenso, 1)


# ── Atualiza forma/moral ───────────────────────────────────────
def _update_form_and_morale(players: List[Player], won: bool, drew: bool):
    delta_forma  = 4 if won else (0 if drew else -3)
    delta_moral  = 5 if won else (1 if drew else -4)
    delta_cond   = -3  # desgaste físico

    for p in players:
        p.forma         = max(10, min(99, p.forma  + delta_forma  + random.randint(-2, 2)))
        p.moral         = max(10, min(99, p.moral  + delta_moral  + random.randint(-1, 2)))
        p.condicao_fisica = max(30, min(100, p.condicao_fisica + delta_cond + random.randint(-2, 1)))
        if p.suspenso > 0:
            p.suspenso -= 1  # descontando jogo suspenso


def _update_team_stats(home, away, hg, ag, competition):
    if competition == "Copa":
        home.copa_gf += hg; home.copa_ga += ag
        away.copa_gf += ag; away.copa_ga += hg
        if hg > ag:
            home.copa_wins += 1;  away.copa_losses += 1
        elif hg < ag:
            away.copa_wins += 1;  home.copa_losses += 1
        else:
            home.copa_draws += 1; away.copa_draws  += 1
    else:
        home.div_gf += hg; home.div_ga += ag
        away.div_gf += ag; away.div_ga += hg
        if hg > ag:
            home.div_wins += 1;  away.div_losses += 1
        elif hg < ag:
            away.div_wins += 1;  home.div_losses += 1
        else:
            home.div_draws += 1; away.div_draws  += 1


def _push_recent_result(team: Team, gf: int, ga: int):
    if gf > ga:
        team.last_results.append("W")
    elif gf < ga:
        team.last_results.append("L")
    else:
        team.last_results.append("D")
    team.last_results = team.last_results[-5:]


def simulate_half(
    home: Team,
    away: Team,
    home_lineup: List[Player],
    away_lineup: List[Player],
    minute_start: int,
    minute_end: int,
    competition: str = "Liga",
) -> dict:
    """Simula um tempo de jogo sem aplicar estatísticas permanentes."""
    half_minutes = max(1, minute_end - minute_start + 1)
    home_red_minute = None
    away_red_minute = None
    home_red_player = None
    away_red_player = None

    if home_lineup and random.random() < 0.06:
        home_red_player = random.choice(home_lineup)
        home_red_minute = random.randint(minute_start, minute_end)
    if away_lineup and random.random() < 0.06:
        away_red_player = random.choice(away_lineup)
        away_red_minute = random.randint(minute_start, minute_end)

    home_def = _effective_defense(home, is_home=True, lineup=home_lineup)
    away_def = _effective_defense(away, is_home=False, lineup=away_lineup)

    half_factor = max(0.10, half_minutes / 90)
    if minute_start == 0:
        half_factor *= 1.02
    elif minute_start >= 46:
        half_factor *= 0.98

    home_xg = _team_xg(home, away_def, is_home=True, lineup=home_lineup) * half_factor
    away_xg = _team_xg(away, home_def, is_home=False, lineup=away_lineup) * half_factor

    if home_red_minute is not None:
        remaining_share = (minute_end - home_red_minute + 1) / half_minutes
        home_xg *= max(0.45, 1 - (0.28 * remaining_share))
        away_xg *= 1 + (0.22 * remaining_share)
    if away_red_minute is not None:
        remaining_share = (minute_end - away_red_minute + 1) / half_minutes
        away_xg *= max(0.45, 1 - (0.28 * remaining_share))
        home_xg *= 1 + (0.22 * remaining_share)

    home_goals = _poisson(home_xg)
    away_goals = _poisson(away_xg)

    home_scorers = _weighted_scorers(home_lineup, home_goals)
    away_scorers = _weighted_scorers(away_lineup, away_goals)

    events = []
    for scorer in home_scorers:
        events.append({
            "minute": random.randint(minute_start, minute_end),
            "side": "home",
            "type": "goal",
            "scorer": scorer.name,
            "player_name": scorer.name,
            "team_name": home.name,
            "short_name": home.short_name,
        })
    for scorer in away_scorers:
        events.append({
            "minute": random.randint(minute_start, minute_end),
            "side": "away",
            "type": "goal",
            "scorer": scorer.name,
            "player_name": scorer.name,
            "team_name": away.name,
            "short_name": away.short_name,
        })

    for side, team, lineup in (
        ("home", home, home_lineup),
        ("away", away, away_lineup),
    ):
        if lineup and random.random() < 0.35:
            booked = random.choice(lineup)
            events.append({
                "minute": random.randint(minute_start, minute_end),
                "side": side,
                "type": "yellow",
                "player_name": booked.name,
                "team_name": team.name,
                "short_name": team.short_name,
            })
        if lineup and random.random() < 0.08:
            injured = random.choice(lineup)
            events.append({
                "minute": random.randint(minute_start, minute_end),
                "side": side,
                "type": "injury",
                "player_name": injured.name,
                "team_name": team.name,
                "short_name": team.short_name,
            })

    if home_red_player is not None:
        events.append({
            "minute": home_red_minute,
            "side": "home",
            "type": "red",
            "player_name": home_red_player.name,
            "team_name": home.name,
            "short_name": home.short_name,
        })
    if away_red_player is not None:
        events.append({
            "minute": away_red_minute,
            "side": "away",
            "type": "red",
            "player_name": away_red_player.name,
            "team_name": away.name,
            "short_name": away.short_name,
        })
    events.sort(key=lambda event: event["minute"])

    return {
        "home_goals": home_goals,
        "away_goals": away_goals,
        "home_scorers": [p.name for p in home_scorers],
        "away_scorers": [p.name for p in away_scorers],
        "events": events,
    }


def _remove_sent_off_players(lineup: List[Player], events: List[dict], side: str) -> List[Player]:
    remaining = list(lineup)
    expelled = {event.get("player_name") for event in events if event.get("type") == "red" and event.get("side") == side}
    return [player for player in remaining if player.name not in expelled]


def finalize_match_result(
    home: Team,
    away: Team,
    competition: str,
    matchday: int,
    home_goals: int,
    away_goals: int,
    home_scorers: List[str],
    away_scorers: List[str],
    home_used: List[Player] | None = None,
    away_used: List[Player] | None = None,
) -> MatchResult:
    """Aplica um resultado já simulado ao estado dos times e jogadores."""
    home_used = home_used or select_starting_lineup(home)
    away_used = away_used or select_starting_lineup(away)

    by_name_home = {player.name: player for player in home_used}
    by_name_away = {player.name: player for player in away_used}
    for scorer in home_scorers:
        player = by_name_home.get(scorer)
        if player:
            player.gols_temp += 1
            player.gols_total += 1
    for scorer in away_scorers:
        player = by_name_away.get(scorer)
        if player:
            player.gols_temp += 1
            player.gols_total += 1

    _generate_cards(home_used)
    _generate_cards(away_used)

    for p in home_used:
        p.partidas_temp += 1
        p.partidas_total += 1
    for p in away_used:
        p.partidas_temp += 1
        p.partidas_total += 1

    won_home = home_goals > away_goals
    won_away = away_goals > home_goals
    drew = home_goals == away_goals
    _update_form_and_morale(home_used, won=won_home, drew=drew)
    _update_form_and_morale(away_used, won=won_away, drew=drew)
    _apply_match_income(home)
    _update_team_stats(home, away, home_goals, away_goals, competition)
    _push_recent_result(home, home_goals, away_goals)
    _push_recent_result(away, away_goals, home_goals)

    return MatchResult(
        home_team=home,
        away_team=away,
        home_goals=home_goals,
        away_goals=away_goals,
        home_scorers=home_scorers,
        away_scorers=away_scorers,
        competition=competition,
        matchday=matchday,
    )


# ── Simulação principal ────────────────────────────────────────
def simulate_match(
    home: Team,
    away: Team,
    competition: str = "Liga",
    matchday: int = 0,
) -> MatchResult:
    """
    Simula uma partida completa. Retorna MatchResult.
    Considera: formação, postura, forma, moral, suspensões.
    """
    home_lineup = select_starting_lineup(home)
    away_lineup = select_starting_lineup(away)
    first_half = simulate_half(home, away, home_lineup, away_lineup, 0, 45, competition)
    home_lineup = _remove_sent_off_players(home_lineup, first_half["events"], "home")
    away_lineup = _remove_sent_off_players(away_lineup, first_half["events"], "away")
    second_half = simulate_half(home, away, home_lineup, away_lineup, 46, 90, competition)

    return finalize_match_result(
        home=home,
        away=away,
        competition=competition,
        matchday=matchday,
        home_goals=first_half["home_goals"] + second_half["home_goals"],
        away_goals=first_half["away_goals"] + second_half["away_goals"],
        home_scorers=first_half["home_scorers"] + second_half["home_scorers"],
        away_scorers=first_half["away_scorers"] + second_half["away_scorers"],
        home_used=home_lineup,
        away_used=away_lineup,
    )


def _apply_match_income(home: Team):
    """Renda do jogo baseada na torcida e prestígio."""
    base = home.torcida * 0.0001   # 0.01% da torcida vão ao estádio em R$ mil
    income = int(max(50, base * (home.prestige / 80)))
    home.caixa += income
    # Paga salários no dia de jogo (simplificado: 1/4 do mensal)
    home.caixa -= max(0, home.salario_mensal // 4)


def simulate_penalty_shootout(team_a: Team, team_b: Team) -> Team:
    a_skill = team_a.squad_overall()
    b_skill = team_b.squad_overall()
    prob_a  = a_skill / (a_skill + b_skill)
    return team_a if random.random() < prob_a else team_b


def simulate_all_fixtures_in_round(fixtures) -> List[MatchResult]:
    """Simula todas as partidas de uma rodada (exceto a do jogador)."""
    results = []
    for f in fixtures:
        if not f.played:
            f.result = simulate_match(
                f.home_team, f.away_team,
                competition=f.competition,
                matchday=f.matchday,
            )
            results.append(f.result)
    return results
