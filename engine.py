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
    available = [p for p in team.players if p.suspenso <= 0]
    if not available:
        available = list(team.players)

    slots = team.formation.slots()
    lineup: List[Player] = []
    used_ids = set()

    def score(player: Player) -> float:
        # Escalação sempre prioriza o melhor OVR por posição.
        return float(player.overall)

    if team.formation == Formation.BEST11:
        gks = [p for p in available if p.position == Position.GK]
        gks.sort(key=score, reverse=True)
        if gks:
            lineup.append(gks[0])
            used_ids.add(gks[0].id)
        leftovers = [p for p in available if p.id not in used_ids and p.position != Position.GK]
        leftovers.sort(key=score, reverse=True)
        lineup.extend(leftovers[: 11 - len(lineup)])
        pos_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
        return sorted(lineup[:11], key=lambda p: (pos_order.get(p.position, 9), -score(p), p.name))

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
        for player in leftovers:
            # Em qualquer tática, manter no máximo 1 goleiro entre os 11.
            if player.position == Position.GK and any(p.position == Position.GK for p in lineup):
                continue
            lineup.append(player)
            if len(lineup) >= 11:
                break

    pos_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
    return sorted(lineup[:11], key=lambda p: (pos_order.get(p.position, 9), -score(p), p.name))


def select_bench(team: Team, starters: List[Player], limit: int = 12) -> List[Player]:
    starter_ids = {p.id for p in starters}
    available = [p for p in team.players if p.id not in starter_ids and p.suspenso <= 0]
    available.sort(key=lambda p: (-p.overall, p.name))
    return available[:limit]


# ── Calcula XG da equipe ───────────────────────────────────────
def _team_xg(team: Team, vs_defense: float, is_home: bool, lineup: List[Player] | None = None) -> float:
    """
    Calcula gols esperados levando em conta:
    - Força do elenco
    - Formação tática (viés ofensivo)
    - Postura (defensivo/equilibrado/ofensivo)
    - Efeito do contrato (motivação)
    - Mando de campo
    """
    top11 = lineup[:] if lineup else sorted(
        [p for p in team.players if p.suspenso == 0],
        key=lambda p: p.overall, reverse=True
    )[:11]
    if not top11:
        top11 = sorted(team.players, key=lambda p: p.overall, reverse=True)[:11]

    atk = sum(p.attack_rating() for p in top11) / len(top11) if top11 else team.attack_strength()
    atk *= team.coach.bonus()

    # Efeito do contrato na performance
    contract_effect = 0.0
    for p in top11:
        if p.contrato_rodadas == 0:
            contract_effect += 1.05  # quer mostrar serviço
        elif 1 <= p.contrato_rodadas <= 15:
            contract_effect += 1.00  # normal
        else:
            contract_effect += 0.97  # contrato vencido, menos motivado
    contract_factor = contract_effect / len(top11)
    atk = atk * contract_factor

    # Craques elevam o impacto ofensivo da equipe na partida.
    star_bonus = 1.0
    for player in top11:
        if getattr(player, "is_star", False):
            star_bonus += min(0.06, max(0.02, float(player.overall) / 2000))
    atk *= star_bonus

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
        [p for p in team.players if p.suspenso == 0],
        key=lambda p: p.overall, reverse=True
    )[:11]
    if not top11:
        top11 = sorted(team.players, key=lambda p: p.overall, reverse=True)[:11]

    dfs = sum(p.defense_rating() for p in top11) / len(top11) if top11 else team.defense_strength()
    dfs *= team.coach.bonus()

    # Efeito do contrato na performance
    contract_effect = 0.0
    for p in top11:
        if p.contrato_rodadas == 0:
            contract_effect += 1.05  # quer mostrar serviço
        elif 1 <= p.contrato_rodadas <= 15:
            contract_effect += 1.00  # normal
        else:
            contract_effect += 0.97  # contrato vencido, menos motivado
    contract_factor = contract_effect / len(top11)
    dfs = dfs * contract_factor

    # Craques também impactam organização defensiva (efeito menor).
    star_bonus = 1.0
    for player in top11:
        if getattr(player, "is_star", False):
            star_bonus += min(0.03, max(0.01, float(player.overall) / 3000))
    dfs *= star_bonus

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
        base = max(1.0, float(p.overall))
        if p.position == Position.ATK:
            w = base * 1.25
        elif p.position == Position.MID:
            w = base * 1.00
        elif p.position == Position.DEF:
            w = base * 0.75
        else:
            w = base * 0.15  # GK raramente marca
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


# ── Atualiza OVR após partida (desgaste/recuperação) ────────────
def _update_ovr_after_match(players: List[Player], players_used: List[Player]):
    """
    Titulares que jogaram: desgaste linear pequeno (-0.05 a -0.15 por partida).
    Reservas que não jogaram: recuperação leve (+0.02 a +0.06 por partida).

    Com ~25 partidas por temporada, o decay máximo acumulado é ~3.75 pontos,
    o que preserva a competitividade sem colapsar elencos em temporadas longas.
    """
    used_ids = {p.id for p in players_used}

    for p in players:
        if p.id in used_ids:
            p.overall -= random.uniform(0.05, 0.15)
        else:
            p.overall += random.uniform(0.02, 0.06)

        # Clamp global: nenhum jogador sai dos limites absolutos.
        p.overall = round(max(10.0, min(99.0, p.overall)), 2)


def _serve_suspensions(players: List[Player], players_used: List[Player]):
    used_ids = {p.id for p in players_used}
    for p in players:
        if p.suspenso > 0 and p.id not in used_ids:
            p.suspenso -= 1


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


def _push_recent_result(team: Team, gf: int, ga: int, is_liga: bool = False):
    """Registra o resultado recente APENAS para jogos de Liga.
    Copa não deve contaminar a pressão do técnico — time pode perder Copa
    para um adversário de divisão superior sem que isso reflita mal na gestão.
    """
    if not is_liga:
        return
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
    attendance: int = 0,
    events: List[dict] | None = None,
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

    red_events = [event for event in (events or []) if event.get("type") == "red"]
    for event in red_events:
        if event.get("side") == "home":
            player = by_name_home.get(event.get("player_name"))
        else:
            player = by_name_away.get(event.get("player_name"))
        if player:
            player.vermelhos_temp += 1
            player.vermelhos_total += 1
            player.suspenso = max(player.suspenso, 1)

    _generate_cards(home_used)
    _generate_cards(away_used)

    for p in home_used:
        p.partidas_temp += 1
        p.partidas_total += 1
    for p in away_used:
        p.partidas_temp += 1
        p.partidas_total += 1

    _update_ovr_after_match(home.players, home_used)
    _update_ovr_after_match(away.players, away_used)
    _serve_suspensions(home.players, home_used)
    _serve_suspensions(away.players, away_used)
    match_income = _apply_match_income(home, attendance, competition)
    if competition == "Liga":
        if home_goals > away_goals:
            home.caixa += int(match_income * 0.50)
        elif away_goals > home_goals:
            away.caixa += int(match_income * 1.00)
    _update_team_stats(home, away, home_goals, away_goals, competition)
    is_liga = (competition == "Liga")
    _push_recent_result(home, home_goals, away_goals, is_liga=is_liga)
    _push_recent_result(away, away_goals, home_goals, is_liga=is_liga)

    return MatchResult(
        home_team=home,
        away_team=away,
        home_goals=home_goals,
        away_goals=away_goals,
        home_scorers=home_scorers,
        away_scorers=away_scorers,
        competition=competition,
        matchday=matchday,
        attendance=attendance,
        income=match_income,
        home_used_names=[player.name for player in home_used],
        away_used_names=[player.name for player in away_used],
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
    home_used = list(home_lineup)
    away_used = list(away_lineup)
    first_half = simulate_half(home, away, home_lineup, away_lineup, 0, 45, competition)
    home_lineup = _remove_sent_off_players(home_lineup, first_half["events"], "home")
    away_lineup = _remove_sent_off_players(away_lineup, first_half["events"], "away")
    second_half = simulate_half(home, away, home_lineup, away_lineup, 46, 90, competition)
    all_events = first_half["events"] + second_half["events"]

    attendance = _estimate_match_attendance(home, away, competition)
    return finalize_match_result(
        home=home,
        away=away,
        competition=competition,
        matchday=matchday,
        home_goals=first_half["home_goals"] + second_half["home_goals"],
        away_goals=first_half["away_goals"] + second_half["away_goals"],
        home_scorers=first_half["home_scorers"] + second_half["home_scorers"],
        away_scorers=first_half["away_scorers"] + second_half["away_scorers"],
        attendance=attendance,
        events=all_events,
        home_used=home_used,
        away_used=away_used,
    )


def _estimate_match_attendance(home: Team, away: Team, competition: str) -> int:
    capacity = home.stadium_capacity
    occupation = min(0.97, max(0.35, 0.44 + (home.prestige / 220)))
    if competition == "Liga":
        occupation *= 1.20
    else:
        occupation *= 1.28
    if home.id == away.id:
        occupation *= 0.95
    return max(8_000, min(capacity, int(capacity * min(0.99, occupation))))


def _apply_match_income(home: Team, attendance: int, competition: str):
    """Renda do jogo baseada em público e preço médio do ingresso."""
    ticket_price_by_div = {
        1: 0.135,  # R$ 135 por torcedor (em mil => 0.135)
        2: 0.105,
        3: 0.080,
        4: 0.060,
    }
    ticket = ticket_price_by_div.get(home.division, 0.070)
    comp_factor = 1.00 if competition == "Liga" else 1.12
    raw_income = attendance * ticket * comp_factor
    income = int(max(250, round(raw_income)))
    home.caixa += income
    return income


def simulate_penalty_series(team_a: Team, team_b: Team) -> Tuple[Team, Tuple[int, int], List[dict]]:
    a_skill = team_a.squad_overall()
    b_skill = team_b.squad_overall()
    prob_a  = a_skill / max(a_skill + b_skill, 1)

    a_score = 0
    b_score = 0
    log: List[dict] = []
    round_num = 1
    taker_idx = {"a": 0, "b": 0}

    def next_taker(team: Team, side: str) -> str:
        candidates = [player for player in team.players if player.position != Position.GK]
        if not candidates:
            candidates = list(team.players)
        if not candidates:
            return "Desconhecido"
        candidates.sort(key=lambda player: player.overall, reverse=True)
        idx = taker_idx[side] % len(candidates)
        taker_idx[side] += 1
        return candidates[idx].name

    def kick(team: Team, side: str, sudden: bool = False) -> bool:
        skill = a_skill if side == "a" else b_skill
        chance = max(0.55, min(0.92, 0.72 + ((skill - 60) / 220)))
        scored = random.random() < chance
        taker_name = next_taker(team, side)
        log.append({
            "round": round_num,
            "team": team.name,
            "side": side,
            "scored": scored,
            "sudden": sudden,
            "player": taker_name,
        })
        return scored

    for round_num in range(1, 6):
        if kick(team_a, "a"):
            a_score += 1
        if kick(team_b, "b"):
            b_score += 1

    while a_score == b_score:
        round_num += 1
        if kick(team_a, "a", sudden=True):
            a_score += 1
        if kick(team_b, "b", sudden=True):
            b_score += 1

    winner = team_a if a_score > b_score else team_b
    return winner, (a_score, b_score), log


def simulate_penalty_shootout(team_a: Team, team_b: Team) -> Team:
    winner, _, _ = simulate_penalty_series(team_a, team_b)
    return winner


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


# ── Presença com contexto de rivalidade ───────────────────────

def estimate_attendance(
    home: Team,
    away: Team,
    competition: str = "Liga",
    is_classic: bool = False,
    is_state_rivalry: bool = False,
    phase: str | None = None,
) -> int:
    """
    Calcula presença para partidas ao vivo, considerando rivalidade e fase da copa.

    Para partidas simuladas pela IA (sem contexto de rivalidade) use
    _estimate_match_attendance, que já é chamada internamente por simulate_match.
    """
    capacity = home.stadium_capacity
    occupation = min(0.96, max(0.28, 0.42 + (home.prestige / 200)))

    if is_classic:
        return capacity

    if is_state_rivalry:
        occupation = max(occupation, 0.62 if competition == "Liga" else 0.56)
        occupation *= 1.18

    if competition == "Liga":
        occupation *= 1.25
    else:
        cup_weights = {
            "primeira_fase": 1.10,
            "oitavas": 1.20,
            "quartas": 1.30,
            "semi": 1.45,
            "final": 1.65,
        }
        phase_key = (phase or "").strip().lower()
        occupation *= cup_weights.get(phase_key, 1.08)
        if phase_key == "final":
            return capacity

    return min(capacity, int(capacity * min(0.99, occupation)))


# ── Funções de estado de partida ao vivo ──────────────────────

def pick_injury_replacement(bench: List[Player], injured_player: Player) -> "Player | None":
    """Escolhe o melhor reserva para substituir um jogador lesionado/expulso."""
    if not bench:
        return None
    same_position = [p for p in bench if p.position == injured_player.position]
    pool = same_position or list(bench)
    pool.sort(key=lambda p: p.overall, reverse=True)
    return pool[0]


def apply_red_card_effects(live_game: dict, events_key: str) -> None:
    """
    Remove jogadores expulsos da escalação de um live_game e aplica
    substituição automática de goleiro se houver reserva disponível.
    live_game é um dict com home_lineup, away_lineup, home_bench, etc.
    """
    package = live_game.get(events_key)
    if not package:
        return

    for event in package["events"]:
        if event.get("type") != "red":
            continue
        side = event.get("side")
        if side not in ("home", "away"):
            continue

        lineup_key = f"{side}_lineup"
        lineup = list(live_game[lineup_key])
        player_name = event.get("player_name")
        player = next((p for p in lineup if p.name == player_name), None)
        if player is None:
            continue
        lineup.remove(player)
        live_game[lineup_key] = lineup

        # Substituição automática se goleiro for expulso.
        if getattr(player, "position", None) is not None and player.position.name == "GK":
            bench_key = f"{side}_bench"
            used_key = f"{side}_used"
            subs_key = f"{side}_subs_used"
            if live_game[subs_key] < 5 and live_game[bench_key]:
                replacement = pick_injury_replacement(live_game[bench_key], player)
                if replacement is not None:
                    bench = list(live_game[bench_key])
                    bench.remove(replacement)
                    live_game[lineup_key].append(replacement)
                    live_game[bench_key] = bench
                    live_game[used_key].append(replacement)
                    live_game[subs_key] += 1
                    package["events"].append({
                        "minute": event["minute"],
                        "side": side,
                        "type": "substitution",
                        "player_name": f"{replacement.name} no lugar de {player.name}",
                        "team_name": event.get("team_name"),
                        "short_name": event.get("short_name"),
                    })

    package["events"].sort(key=lambda e: (e.get("minute", 0), 0 if e.get("type") != "substitution" else 1))


def apply_auto_injury_substitutions(live_game: dict, events_key: str) -> None:
    """
    Aplica substituições automáticas para jogadores lesionados (evento 'injury').
    live_game é o mesmo dict mutável usado por apply_red_card_effects.
    """
    package = live_game.get(events_key)
    if not package:
        return

    updated_events = []
    for event in package["events"]:
        updated_events.append(event)
        if event.get("type") != "injury":
            continue
        side = event.get("side")
        if side not in ("home", "away"):
            continue

        lineup_key = f"{side}_lineup"
        bench_key = f"{side}_bench"
        used_key = f"{side}_used"
        subs_key = f"{side}_subs_used"

        if live_game[subs_key] >= 5 or not live_game[bench_key]:
            continue

        injured_name = event.get("player_name")
        lineup = list(live_game[lineup_key])
        injured_player = next((p for p in lineup if p.name == injured_name), None)
        if injured_player is None:
            continue

        replacement = pick_injury_replacement(live_game[bench_key], injured_player)
        if replacement is None:
            continue

        bench = list(live_game[bench_key])
        bench.remove(replacement)
        lineup[lineup.index(injured_player)] = replacement
        live_game[lineup_key] = lineup
        live_game[bench_key] = bench
        live_game[used_key].append(replacement)
        live_game[subs_key] += 1
        updated_events.append({
            "minute": event["minute"],
            "side": side,
            "type": "substitution",
            "player_name": f"{replacement.name} no lugar de {injured_player.name}",
            "team_name": event.get("team_name"),
            "short_name": event.get("short_name"),
        })

    updated_events.sort(key=lambda e: (e["minute"], 0 if e.get("type") != "substitution" else 1))
    package["events"] = updated_events
