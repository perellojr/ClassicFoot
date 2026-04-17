"""
ClassicFoot - Brasileirão Edition
Loop principal do jogo
"""
import random
import sys
import time
import os

from data import create_teams
from manager_market import (
    accept_player_offer,
    check_last_division_relegation_firing,
    check_player_firing,
    create_free_coaches,
    current_player_team,
    generate_player_offers,
    process_coach_market,
    reject_player_offer,
)
from models import CareerState, Coach, Postura
from engine import finalize_match_result, select_bench, select_starting_lineup, simulate_half, simulate_penalty_series
from season import Season, advance_season_after_matchday, create_season, pay_monthly_salaries, sort_standings
from transfers import TransferMarket
from transfers import negotiate_contract, run_immediate_contract_auction
from ui import (
    banner, main_menu, season_dashboard, game_menu,
    show_standings, show_copa, show_tactics, show_finances,
    show_torcida, show_stadium, show_next_round, choose_postura, show_calendar,
    show_transfer_market, show_top_scorers, show_match_result, prompt_contract_renewal,
    show_season_end, show_credits, confirm_play, show_notifications, prompt_job_offer,
    manage_player_sales, show_history, show_training, show_auction_results, show_copa_draw,
    show_onboarding,
)
from save import save_game, load_game, save_exists
from term import BB, C, G, GG, RR, R, RST, W, WW, Y, YY, DIM, Table, pause, clear, rule, pad, box, term_width, _visible_len, paint_team

YEAR_START = 2025
HALF_DURATION_SECONDS = float(os.getenv("CLASSICFOOT_HALF_DURATION_SECONDS", "21.9"))

# Confrontos clássicos (por id dos clubes).
CLASSIC_PAIRS = {
    frozenset((1, 5)),   # Fla-Flu
    frozenset((1, 15)),  # Fla-Vasco
    frozenset((1, 6)),   # Fla-Botafogo
    frozenset((4, 2)),   # Corinthians-Palmeiras
    frozenset((4, 9)),   # Corinthians-São Paulo
    frozenset((2, 9)),   # Palmeiras-São Paulo
    frozenset((8, 7)),   # Grêmio-Inter
    frozenset((3, 10)),  # Atlético-MG-Cruzeiro
    frozenset((14, 19)), # Bahia-Vitória
    frozenset((11, 23)), # Fortaleza-Ceará
    frozenset((13, 25)), # Athletico-Coritiba
    frozenset((26, 18)), # Goiás-Atlético-GO
}


def _prompt_nonempty(label: str) -> str:
    while True:
        value = input(label).strip()
        if value:
            return value
        print(RR + "  Campo obrigatório." + RST)


def _create_manager() -> Coach:
    clear()
    print(YY + "  NOVA CARREIRA" + RST)
    print(C + "  Informe o nome do treinador.\n" + RST)
    first_name = _prompt_nonempty("  Nome: ")
    last_name = _prompt_nonempty("  Sobrenome: ")
    full_name = f"{first_name} {last_name}"
    return Coach(
        name=full_name,
        nationality="Brasileiro",
        tactical=random.randint(68, 76),
        motivation=random.randint(70, 80),
        experience=random.randint(58, 70),
    )


def _assign_random_last_division_team(teams, coach: Coach):
    candidates = [team for team in teams if team.division == 4]
    player_team = random.choice(candidates)
    player_team.coach = coach
    return player_team


def _append_notifications(career: CareerState, messages):
    if not hasattr(career, "seen_notifications"):
        career.seen_notifications = set()
    for message in messages:
        if message and message not in career.seen_notifications:
            career.notifications.append(message)
            career.seen_notifications.add(message)


def _apply_training_if_due(round_marker: int, team):
    """Aplica treino de até 5 jogadores uma vez por rodada do calendário."""
    if team is None:
        return []
    if team.training_round_applied == round_marker:
        return []

    selected_ids = list(dict.fromkeys(team.training_targets or []))[:5]
    auto_selected = False
    if not selected_ids:
        pool = [player.id for player in team.players]
        random.shuffle(pool)
        selected_ids = pool[: min(5, len(pool))]
        auto_selected = True

    improved = []
    for player in team.players:
        if player.id not in selected_ids:
            continue
        gain_factor = 1.0 + random.uniform(0.0, 0.05)
        old_ovr = float(player.overall)
        player.overall = round(min(99.0, old_ovr * gain_factor), 1)
        improved.append((player.name, old_ovr, player.overall))

    team.training_round_applied = round_marker
    if not improved:
        return []

    lines = [f"{team.name} concluiu o treino técnico da rodada:"]
    if auto_selected:
        lines.append("• Seleção automática aplicada (nenhum jogador fixado para treino).")
    for name, old_ovr, new_ovr in improved:
        lines.append(f"• {name}: OVR {int(round(old_ovr))} → {int(round(new_ovr))}")
    return lines


def _ensure_world_history(career: CareerState):
    if not isinstance(getattr(career, "world_history", None), dict):
        career.world_history = {}
    history = career.world_history
    history.setdefault("division_champions", [])
    history.setdefault("team_goals_record", {"goals": 0, "team": "-", "year": 0})
    history.setdefault("player_goals_record", {"goals": 0, "player": "-", "team": "-", "year": 0})
    history.setdefault("team_goals_cumulative", {})
    history.setdefault("player_goals_cumulative", {})
    history.setdefault("league_points_cumulative", {})
    history.setdefault("league_points_record", {"points": 0, "team": "-", "year": 0})
    history.setdefault("div1_titles_by_club", {})
    history.setdefault("copa_titles_by_club", {})
    history.setdefault("div1_champion_coaches_history", [])
    history.setdefault("copa_champion_coaches_history", [])
    history.setdefault("recorded_years", [])
    history.setdefault("recorded_champion_years", [])
    history.setdefault("recorded_aggregate_years", [])
    history.setdefault("biggest_win", {"diff": 0, "score": "-", "winner": "-", "loser": "-", "year": 0})
    history.setdefault("max_attendance", {"attendance": 0, "home": "-", "away": "-", "year": 0})
    history.setdefault("max_income", {"income": 0, "home": "-", "away": "-", "year": 0})
    history.setdefault("coach_titles", {})
    return history


def _normalize_world_history(career: CareerState):
    """
    Migra/normaliza estrutura de histórico para saves antigos, sem exigir novo jogo.
    """
    world = _ensure_world_history(career)
    if not isinstance(career.season_history, list):
        career.season_history = []

    # Backfill de campeões da Divisão 1 por clube e técnicos a partir do histórico existente.
    if (not world.get("div1_titles_by_club")) and world.get("division_champions"):
        rebuilt_titles = {}
        rebuilt_coaches = []
        for item in world.get("division_champions", []):
            if int(item.get("division", 0) or 0) != 1:
                continue
            team_name = item.get("team")
            coach_name = item.get("coach")
            if team_name:
                rebuilt_titles[team_name] = int(rebuilt_titles.get(team_name, 0)) + 1
            if coach_name:
                rebuilt_coaches.append(coach_name)
        world["div1_titles_by_club"] = rebuilt_titles
        if not world.get("div1_champion_coaches_history"):
            world["div1_champion_coaches_history"] = rebuilt_coaches

    # Backfill de campeões da Copa por clube via season_history (quando disponível).
    if (not world.get("copa_titles_by_club")) and career.season_history:
        rebuilt_copa_titles = {}
        for entry in career.season_history:
            champion = entry.get("copa_champion")
            if champion:
                rebuilt_copa_titles[champion] = int(rebuilt_copa_titles.get(champion, 0)) + 1
        world["copa_titles_by_club"] = rebuilt_copa_titles

    # Recalcula ranking de técnicos campeões somente com critério válido:
    # campeão Divisão 1 + campeão da Copa.
    coach_counter = {}
    for coach_name in world.get("div1_champion_coaches_history", []):
        if coach_name:
            coach_counter[coach_name] = int(coach_counter.get(coach_name, 0)) + 1
    for coach_name in world.get("copa_champion_coaches_history", []):
        if coach_name:
            coach_counter[coach_name] = int(coach_counter.get(coach_name, 0)) + 1
    world["coach_titles"] = coach_counter

    # Reconstrói anos gravados de forma robusta para evitar bloqueio indevido dos recordes.
    years_from_history = {
        int(entry.get("year"))
        for entry in career.season_history
        if isinstance(entry, dict) and entry.get("year") is not None
    }
    years_from_champions = {
        int(item.get("year"))
        for item in world.get("division_champions", [])
        if isinstance(item, dict) and item.get("year") is not None
    }
    world["recorded_champion_years"] = sorted(
        set(world.get("recorded_champion_years", [])) | years_from_champions
    )
    world["recorded_aggregate_years"] = sorted(
        set(world.get("recorded_aggregate_years", []))
    )
    world["recorded_years"] = sorted(
        set(world.get("recorded_years", []))
        | years_from_history
        | set(world.get("recorded_champion_years", []))
        | set(world.get("recorded_aggregate_years", []))
    )

    # Migração de saves antigos: se acumulados estiverem vazios, tenta semear via season_history.
    if not world.get("league_points_cumulative") and career.season_history:
        points_seed = {}
        for entry in career.season_history:
            if not isinstance(entry, dict):
                continue
            team = entry.get("league_points_best_team")
            points = int(entry.get("league_points_best_points", 0) or 0)
            if team and points > 0:
                points_seed[team] = int(points_seed.get(team, 0)) + points
        world["league_points_cumulative"] = points_seed

    if not world.get("team_goals_cumulative") and career.season_history:
        goals_seed = {}
        for entry in career.season_history:
            if not isinstance(entry, dict):
                continue
            team = entry.get("league_best_attack_team")
            goals = int(entry.get("league_best_attack_goals", 0) or 0)
            if team and goals > 0:
                goals_seed[team] = int(goals_seed.get(team, 0)) + goals
        world["team_goals_cumulative"] = goals_seed

    if not world.get("player_goals_cumulative") and career.season_history:
        player_seed = {}
        for entry in career.season_history:
            if not isinstance(entry, dict):
                continue
            top = entry.get("top_scorer")
            if not isinstance(top, (tuple, list)) or len(top) < 3:
                continue
            player_name, team_name, goals = top[0], top[1], int(top[2] or 0)
            if player_name and team_name and goals > 0:
                key = f"{player_name}::{team_name}"
                player_seed[key] = int(player_seed.get(key, 0)) + goals
        world["player_goals_cumulative"] = player_seed

    # Fallback final para manter recordes legíveis mesmo em saves sem base acumulada.
    if not world.get("league_points_cumulative"):
        rec = world.get("league_points_record", {}) or {}
        team = rec.get("team")
        pts = int(rec.get("points", 0) or 0)
        if team and team != "-" and pts > 0:
            world["league_points_cumulative"] = {team: pts}

    if not world.get("team_goals_cumulative"):
        rec = world.get("team_goals_record", {}) or {}
        team = rec.get("team")
        goals = int(rec.get("goals", 0) or 0)
        if team and team != "-" and goals > 0:
            world["team_goals_cumulative"] = {team: goals}

    if not world.get("player_goals_cumulative"):
        rec = world.get("player_goals_record", {}) or {}
        player = rec.get("player")
        team = rec.get("team")
        goals = int(rec.get("goals", 0) or 0)
        if player and team and player != "-" and team != "-" and goals > 0:
            world["player_goals_cumulative"] = {f"{player}::{team}": goals}

    if world.get("league_points_cumulative"):
        club_name, total_points = max(world["league_points_cumulative"].items(), key=lambda item: item[1])
        world["league_points_record"] = {
            "points": int(total_points),
            "team": club_name,
            "year": world.get("league_points_record", {}).get("year", 0),
        }

    if world.get("team_goals_cumulative"):
        team_name, total_goals = max(world["team_goals_cumulative"].items(), key=lambda item: item[1])
        world["team_goals_record"] = {
            "goals": int(total_goals),
            "team": team_name,
            "year": world.get("team_goals_record", {}).get("year", 0),
        }

    if world.get("player_goals_cumulative"):
        player_key, total_goals = max(world["player_goals_cumulative"].items(), key=lambda item: item[1])
        player_name, team_name = player_key.split("::", 1)
        world["player_goals_record"] = {
            "goals": int(total_goals),
            "player": player_name,
            "team": team_name,
            "year": world.get("player_goals_record", {}).get("year", 0),
        }
    career.world_history = world


def _ensure_stars_in_all_teams(all_teams):
    for team in all_teams:
        stars = [player for player in team.players if getattr(player, "is_star", False)]
        if len(stars) >= 3:
            continue
        for player in team.players:
            player.is_star = False
        for player in sorted(team.players, key=lambda p: p.overall, reverse=True)[:3]:
            player.is_star = True


def _ensure_rivalry_fields(team):
    if not hasattr(team, "rivalry_points") or not isinstance(getattr(team, "rivalry_points"), dict):
        team.rivalry_points = {}
    if not hasattr(team, "dynamic_rivals") or not isinstance(getattr(team, "dynamic_rivals"), list):
        team.dynamic_rivals = []


def _register_dynamic_rivalry(team_a, team_b, delta: float):
    if delta <= 0:
        return
    _ensure_rivalry_fields(team_a)
    _ensure_rivalry_fields(team_b)

    for source, target in ((team_a, team_b), (team_b, team_a)):
        old_score = float(source.rivalry_points.get(target.id, 0.0))
        source.rivalry_points[target.id] = round(min(30.0, old_score + delta), 2)
        if source.rivalry_points[target.id] >= 8.0 and target.id not in source.dynamic_rivals:
            source.dynamic_rivals.append(target.id)


def _league_rivalry_context(season: Season, home, away, round_num: int) -> dict:
    division_teams = [club for club in season.all_teams if club.division == home.division]
    ranked = sort_standings(division_teams)
    position_by_id = {club.id: idx + 1 for idx, club in enumerate(ranked)}
    pos_home = int(position_by_id.get(home.id, len(ranked)))
    pos_away = int(position_by_id.get(away.id, len(ranked)))

    # Divisão com 8 clubes: 14 rodadas de liga (ida e volta).
    is_late_round = round_num >= 10
    title_clash = is_late_round and pos_home <= 2 and pos_away <= 2
    promotion_clash = is_late_round and home.division > 1 and pos_home <= 3 and pos_away <= 3
    return {
        "league_title_clash": title_clash,
        "league_promotion_clash": promotion_clash,
    }


def _maybe_show_pending_cup_draws(season: Season, player_team=None) -> bool:
    if not hasattr(season, "shown_cup_draws") or not isinstance(getattr(season, "shown_cup_draws"), list):
        season.shown_cup_draws = []

    shown = set(season.shown_cup_draws)
    shown_any = False
    phases = [
        ("primeira_fase", "1ª Fase", season.copa_primeira_fase),
        ("oitavas", "Oitavas de Final", season.copa_oitavas),
        ("quartas", "Quartas de Final", season.copa_quartas),
        ("semi", "Semifinal", season.copa_semi),
        ("final", "Final", [season.copa_final] if season.copa_final else []),
    ]

    for phase_key, phase_title, ties in phases:
        if phase_key in shown:
            continue
        if not ties:
            continue
        has_started = any((tie.leg1 is not None or tie.leg2 is not None) for tie in ties)
        if has_started:
            shown.add(phase_key)
            continue
        show_copa_draw(phase_title, ties, season.all_teams)
        shown_any = True
        shown.add(phase_key)

    season.shown_cup_draws = list(shown)
    if shown_any:
        show_copa(season, player_team)
    return shown_any


def _record_season_history(season: Season, player_team, career: CareerState):
    _normalize_world_history(career)
    world_history = _ensure_world_history(career)
    season_year = int(season.year)

    # Histórico do técnico (uma linha por temporada/ano).
    has_year_entry = any(
        isinstance(entry, dict) and int(entry.get("year", 0) or 0) == season_year
        for entry in career.season_history
    )
    if player_team is not None and not has_year_entry:
        final_data = season.final_positions.get(player_team.id, {})
        division = int(final_data.get("division", player_team.division))
        position = int(final_data.get("position", 0) or 0)
        if position <= 0:
            # Fallback para saves legados sem final_positions.
            division_teams = [team for team in season.all_teams if team.division == division]
            ranked = sort_standings(division_teams)
            position = next((idx + 1 for idx, team in enumerate(ranked) if team.id == player_team.id), 0)

        top_scorer = None
        if season.top_scorers:
            top_scorer = season.top_scorers[0]

        best_points_team = max(season.all_teams, key=lambda t: int(t.div_points), default=None)
        best_attack_team = max(season.all_teams, key=lambda t: int(t.div_gf), default=None)

        history_entry = {
            "year": season.year,
            "team": player_team.name,
            "division": division,
            "position": position,
            "copa_phase": player_team.copa_phase,
            "top_scorer": top_scorer,
            "copa_champion": season.copa_champion.name if season.copa_champion else None,
            "league_points_best_team": best_points_team.name if best_points_team else None,
            "league_points_best_points": int(best_points_team.div_points) if best_points_team else 0,
            "league_best_attack_team": best_attack_team.name if best_attack_team else None,
            "league_best_attack_goals": int(best_attack_team.div_gf) if best_attack_team else 0,
        }
        career.season_history.append(history_entry)

    champion_years = set(world_history.get("recorded_champion_years", []))
    aggregate_years = set(world_history.get("recorded_aggregate_years", []))

    if season_year not in champion_years:
        for div in sorted(season.division_champions.keys()):
            champion_entry = {
                "year": season.year,
                "division": div,
                "team": season.division_champions.get(div, "-"),
                "coach": season.division_champion_coaches.get(div, "-"),
            }
            world_history["division_champions"].append(champion_entry)

        div1_champion = season.division_champions.get(1)
        if div1_champion:
            titles = world_history["div1_titles_by_club"]
            titles[div1_champion] = int(titles.get(div1_champion, 0)) + 1

        # Títulos de técnico: somente campeão da Divisão 1 e campeão da Copa.
        div1_coach = season.division_champion_coaches.get(1)
        if div1_coach:
            world_history["div1_champion_coaches_history"].append(div1_coach)
            world_history["coach_titles"][div1_coach] = world_history["coach_titles"].get(div1_coach, 0) + 1
        if season.copa_champion is not None:
            coach_name = season.copa_champion.coach.name
            world_history["copa_champion_coaches_history"].append(coach_name)
            world_history["coach_titles"][coach_name] = world_history["coach_titles"].get(coach_name, 0) + 1
            copa_titles = world_history["copa_titles_by_club"]
            copa_titles[season.copa_champion.name] = int(copa_titles.get(season.copa_champion.name, 0)) + 1

        world_history["recorded_champion_years"] = sorted(champion_years | {season_year})

    if season_year not in aggregate_years:
        for team in season.all_teams:
            points_cumulative = world_history["league_points_cumulative"]
            points_cumulative[team.name] = int(points_cumulative.get(team.name, 0)) + int(team.div_points)
        if world_history["league_points_cumulative"]:
            club_name, total_points = max(world_history["league_points_cumulative"].items(), key=lambda item: item[1])
            world_history["league_points_record"] = {
                "points": int(total_points),
                "team": club_name,
                "year": season.year,
            }

        for team in season.all_teams:
            cumulative = world_history["team_goals_cumulative"]
            cumulative[team.name] = int(cumulative.get(team.name, 0)) + int(team.div_gf)
        if world_history["team_goals_cumulative"]:
            team_name, total_goals = max(world_history["team_goals_cumulative"].items(), key=lambda item: item[1])
            world_history["team_goals_record"] = {
                "goals": int(total_goals),
                "team": team_name,
                "year": season.year,
            }

        for team in season.all_teams:
            for player in team.players:
                key = f"{player.name}::{team.name}"
                cumulative = world_history["player_goals_cumulative"]
                cumulative[key] = int(cumulative.get(key, 0)) + int(player.gols_temp)
        if world_history["player_goals_cumulative"]:
            player_key, total_goals = max(world_history["player_goals_cumulative"].items(), key=lambda item: item[1])
            player_name, team_name = player_key.split("::", 1)
            world_history["player_goals_record"] = {
                "goals": int(total_goals),
                "player": player_name,
                "team": team_name,
                "year": season.year,
            }

        world_history["recorded_aggregate_years"] = sorted(aggregate_years | {season_year})

        for result in season.results_history:
            diff = abs(int(result.home_goals) - int(result.away_goals))
            if diff <= int(world_history["biggest_win"].get("diff", 0)):
                continue
            if result.home_goals > result.away_goals:
                winner, loser = result.home_team.name, result.away_team.name
            elif result.away_goals > result.home_goals:
                winner, loser = result.away_team.name, result.home_team.name
            else:
                winner, loser = "-", "-"
            world_history["biggest_win"] = {
                "diff": diff,
                "score": f"{result.home_goals}x{result.away_goals}",
                "winner": winner,
                "loser": loser,
                "year": season.year,
            }

        max_attendance = season.max_attendance or {}
        if int(max_attendance.get("attendance", 0)) > int(world_history["max_attendance"].get("attendance", 0)):
            world_history["max_attendance"] = dict(max_attendance)

        max_income = season.max_income or {}
        if int(max_income.get("income", 0)) > int(world_history["max_income"].get("income", 0)):
            world_history["max_income"] = dict(max_income)

    world_history["recorded_years"] = sorted(
        set(world_history.get("recorded_years", []))
        | set(world_history.get("recorded_champion_years", []))
        | set(world_history.get("recorded_aggregate_years", []))
        | {season_year}
    )


def _post_round_updates(
    season: Season,
    player_team,
    career: CareerState,
    transfer_messages,
    round_type: str | None = None,
    round_marker: int | None = None,
):
    # Contabiliza rodadas consecutivas sem clube para garantia de oferta
    if getattr(career, "unemployed", False):
        career.rounds_unemployed = getattr(career, "rounds_unemployed", 0) + 1

    _append_notifications(career, transfer_messages)
    if round_type == "liga":
        _append_notifications(
            career,
            process_coach_market(season.all_teams, career, round_marker=round_marker),
        )

    firing_msg = check_player_firing(season.all_teams, career)
    if firing_msg:
        _append_notifications(career, [firing_msg])
        show_notifications(career.notifications, title="CENTRAL DE NOTÍCIAS")
        career.notifications.clear()
        offers = generate_player_offers(season.all_teams, career)
        if offers:
            for offer in offers:
                accepted = prompt_job_offer(career.player_coach.name, offer, season.all_teams)
                if accepted:
                    player_team, messages = accept_player_offer(offer, season.all_teams, career)
                    show_notifications(messages, title="MERCADO DE TREINADORES")
                    return player_team, False
                reject_messages = reject_player_offer(offer, season.all_teams, career)
                show_notifications(reject_messages, title="MERCADO DE TREINADORES")
            return player_team, False
        return player_team, False

    offers = generate_player_offers(season.all_teams, career)
    if offers:
        for offer in offers:
            accepted = prompt_job_offer(career.player_coach.name, offer, season.all_teams)
            if accepted:
                player_team, messages = accept_player_offer(offer, season.all_teams, career)
                _append_notifications(career, messages)
                break
            reject_messages = reject_player_offer(offer, season.all_teams, career)
            show_notifications(reject_messages, title="MERCADO DE TREINADORES")

    if career.notifications:
        show_notifications(career.notifications, title="CENTRAL DE NOTÍCIAS")
        career.notifications.clear()

    current = current_player_team(career, season.all_teams)
    if current is not None:
        player_team = current
    return player_team, False


def _collect_current_match_objects(season: Season, player_team):
    matchday = season.calendar[season.current_matchday]
    cup_leg = matchday.get("cup_leg", 1)
    round_num = int(matchday.get("round_num", 0) or 0)
    games = []
    for fixture in matchday.get("fixtures", []):
        games.append({
            "kind": "fixture",
            "ref": fixture,
            "home": fixture.home_team,
            "away": fixture.away_team,
            "competition": fixture.competition,
            "round_num": round_num,
            "is_player": player_team is not None and (fixture.home_team.id == player_team.id or fixture.away_team.id == player_team.id),
        })
    for tie in (matchday.get("ties") or []):
        home = tie.team_a if cup_leg == 1 or tie.single_leg else tie.team_b
        away = tie.team_b if cup_leg == 1 or tie.single_leg else tie.team_a
        games.append({
            "kind": "tie",
            "ref": tie,
            "home": home,
            "away": away,
            "competition": "Copa",
            "cup_leg": cup_leg,
            "round_num": round_num,
            "first_leg_result": tie.leg1 if cup_leg == 2 and not tie.single_leg else None,
            "is_player": player_team is not None and (tie.team_a.id == player_team.id or tie.team_b.id == player_team.id),
        })
    return matchday, games


def _prepare_live_games(season: Season, player_team):
    matchday, games = _collect_current_match_objects(season, player_team)
    live_games = []
    for game in games:
        home = game["home"]
        away = game["away"]
        if game["competition"] == "Liga":
            game.update(_league_rivalry_context(season, home, away, int(game.get("round_num", 0))))
        home_lineup = select_starting_lineup(home)
        away_lineup = select_starting_lineup(away)
        live_game = {
            **game,
            "home_lineup": home_lineup,
            "away_lineup": away_lineup,
            "home_bench": select_bench(home, home_lineup, 12),
            "away_bench": select_bench(away, away_lineup, 12),
            "home_used": list(home_lineup),
            "away_used": list(away_lineup),
            "home_subs_used": 0,
            "away_subs_used": 0,
            "home_goals": 0,
            "away_goals": 0,
            "home_scorers": [],
            "away_scorers": [],
            "attendance": _estimate_attendance(
                home,
                away,
                game["competition"],
                phase=game["ref"].phase if game["kind"] == "tie" else None,
            ),
            "events_first": simulate_half(home, away, home_lineup, away_lineup, 0, 45, game["competition"]),
            "events_second": None,
        }
        _apply_red_card_effects(live_game, "events_first")
        if not game["is_player"]:
            live_game["events_second"] = simulate_half(
                home, away, live_game["home_lineup"], live_game["away_lineup"], 46, 90, game["competition"]
            )
            _apply_red_card_effects(live_game, "events_second")
        live_games.append(live_game)
    return matchday, live_games


def _is_classic(home_team, away_team) -> bool:
    if frozenset((home_team.id, away_team.id)) in CLASSIC_PAIRS:
        return True
    home_rivals = set(getattr(home_team, "dynamic_rivals", []) or [])
    away_rivals = set(getattr(away_team, "dynamic_rivals", []) or [])
    return (away_team.id in home_rivals) or (home_team.id in away_rivals)


def _is_state_rivalry(home_team, away_team) -> bool:
    """Rivalidade intermediária: clubes do mesmo estado."""
    return (
        home_team.id != away_team.id
        and str(getattr(home_team, "state", "")).strip().upper()
        and str(getattr(home_team, "state", "")).strip().upper()
        == str(getattr(away_team, "state", "")).strip().upper()
    )


def _estimate_attendance(home_team, away_team, competition: str = "Liga", phase: str | None = None) -> int:
    capacity_estimate = home_team.stadium_capacity
    occupation = min(0.96, max(0.28, 0.42 + (home_team.prestige / 200)))
    if _is_classic(home_team, away_team):
        return capacity_estimate
    if _is_state_rivalry(home_team, away_team):
        # Clássico estadual "médio": aumenta bem o interesse, sem lotação garantida.
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
            return capacity_estimate

    return min(capacity_estimate, int(capacity_estimate * min(0.99, occupation)))


def _team_color(team) -> str:
    return {
        "red": RR,
        "dark_red": RR,
        "green": GG,
        "blue": BB,
        "yellow": YY,
        "black": W,
        "white": WW,
    }.get(getattr(team, "primary_color", "white"), WW)


def _paint_team(team, text: str | None = None) -> str:
    """Alias para paint_team centralizado em term.py."""
    return paint_team(team, text)


def _score_at_minute(live_game, minute: int):
    home_goals = 0
    away_goals = 0
    recent = []
    all_events = live_game["events_first"]["events"] + (
        live_game["events_second"]["events"] if live_game["events_second"] else []
    )
    for event in all_events:
        if event["minute"] <= minute:
            if event.get("type") == "goal":
                if event["side"] == "home":
                    home_goals += 1
                else:
                    away_goals += 1
            recent.append(event)
    return home_goals, away_goals, recent[-8:]


def _first_leg_text(game) -> str | None:
    first_leg = game.get("first_leg_result")
    if first_leg is None:
        return None
    # Exibe na ordem dos times da linha atual (mandante da volta x visitante da volta).
    return f"{first_leg.away_goals}x{first_leg.home_goals}"


def _aggregate_text(game, minute: int) -> str | None:
    first_leg = game.get("first_leg_result")
    if first_leg is None:
        return None
    home_goals, away_goals, _ = _score_at_minute(game, minute)
    # Agregado também na ordem dos times da linha atual (volta: team_b x team_a).
    agg_home = first_leg.away_goals + home_goals
    agg_away = first_leg.home_goals + away_goals
    return f"{agg_home}x{agg_away}"


def _latest_event_text(events):
    if not events:
        return ""
    event = events[-1]
    prefix = f"{event['minute']:>2}' "
    event_type = event.get("type", "goal" if event.get("scorer") or event.get("player_name") else "event")
    player_name = event.get("player_name") or event.get("scorer") or "evento"
    if event_type == "goal":
        return GG + prefix + RST + WW + f"{_fit_text(player_name, 46)}" + RST
    if event_type == "yellow":
        return YY + prefix + RST + WW + f"cartão: {_fit_text(player_name, 40)}" + RST
    if event_type == "red":
        return RR + prefix + RST + WW + f"expulso: {_fit_text(player_name, 39)}" + RST
    if event_type == "substitution":
        return BB + prefix + RST + WW + f"sub: {_fit_text(player_name, 43)}" + RST
    return WW + prefix + _fit_text(player_name, 46) + RST


def _apply_red_card_effects(live_game, events_key: str):
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
        player = next((athlete for athlete in lineup if athlete.name == player_name), None)
        if player is None:
            continue
        lineup.remove(player)
        live_game[lineup_key] = lineup

        # Em caso de expulsão do goleiro, faz troca automática se houver reservas.
        if getattr(player, "position", None) is not None and player.position.name == "GK":
            bench_key = f"{side}_bench"
            used_key = f"{side}_used"
            subs_key = f"{side}_subs_used"
            if live_game[subs_key] < 5 and live_game[bench_key]:
                replacement = _pick_injury_replacement(live_game[bench_key], player)
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


def _pick_injury_replacement(bench, injured_player):
    if not bench:
        return None
    same_position = [player for player in bench if player.position == injured_player.position]
    pool = same_position or list(bench)
    pool.sort(key=lambda player: player.overall, reverse=True)
    return pool[0]


def _apply_auto_injury_substitutions(live_game, events_key: str):
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
        injured_player = next((player for player in lineup if player.name == injured_name), None)
        if injured_player is None:
            continue

        replacement = _pick_injury_replacement(live_game[bench_key], injured_player)
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

    updated_events.sort(key=lambda event: (event["minute"], 0 if event.get("type") != "substitution" else 1))
    package["events"] = updated_events


def _division_label(division: int) -> str:
    return f"DIVISÃO {division}"


def _fit_team_name(name: str, limit: int = 17) -> str:
    if len(name) <= limit:
        return name
    if limit <= 3:
        return name[:limit]
    return name[: limit - 3].rstrip() + "..."


def _fit_text(text: str, limit: int = 40) -> str:
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def _format_live_fixture(home_team, away_team, home_goals: int, away_goals: int) -> str:
    home_name = pad(_fit_team_name(home_team.name, 18), 18)
    away_name = pad(_fit_team_name(away_team.name, 18), 18)
    score = f"{home_goals}x{away_goals}"
    return (
        _paint_team(home_team, home_name)
        + " "
        + YY + f"{score:^5}" + RST
        + " "
        + _paint_team(away_team, away_name)
    )


def _current_aggregate(focus_game, minute: int):
    first_leg = focus_game.get("first_leg_result")
    if first_leg is None:
        return None
    home_goals, away_goals, _ = _score_at_minute(focus_game, minute)
    team_a_total = first_leg.home_goals + away_goals
    team_b_total = first_leg.away_goals + home_goals
    return team_a_total, team_b_total


def _render_penalty_shootout(focus_game):
    penalties = focus_game.get("penalties")
    if not penalties:
        return
    clear()
    print(rule("DISPUTA DE PÊNALTIS"))
    print()
    print(pad(_format_live_fixture(focus_game["home"], focus_game["away"], focus_game["final_home_goals"], focus_game["final_away_goals"]), 100, "c"))
    print()
    for kick in penalties["log"]:
        side_team = focus_game["home"] if kick["side"] == "home" else focus_game["away"]
        result = GG + "GOL" + RST if kick["scored"] else RR + "ERROU" + RST
        sudden = "  (morte súbita)" if kick.get("sudden") else ""
        taker = kick.get("player", "Batedor")
        print(f"  {YY}{kick['round']:>2}ª cobrança{RST}  {side_team.name:<22}  {WW}{taker:<22}{RST}  {result}{sudden}")
        time.sleep(0.5)
    print()
    pen_home, pen_away = penalties["score"]
    winner = penalties["winner"]
    print(C + f"  Pênaltis: {focus_game['home'].name} {pen_home} x {pen_away} {focus_game['away'].name}" + RST)
    print(GG + f"  Classificado: {winner.name}" + RST)
    pause()


def _time_progress_bar(minute: int, phase: str) -> str:
    if phase == "1º TEMPO":
        start_minute, end_minute = 0, 45
    else:
        start_minute, end_minute = 46, 90
    total = max(1, end_minute - start_minute)
    progressed = max(0, min(total, minute - start_minute))
    bar_width = 30
    filled = int((progressed / total) * bar_width)
    return C + "[" + GG + "█" * filled + DIM + "░" * (bar_width - filled) + C + "]" + RST


def _render_live_scores(label: str, minute: int, live_games, focus_game=None, phase: str = "1º TEMPO"):
    clear()
    print(rule(f"{label}  •  {phase}  •  {minute:02d}'"))
    print(pad(_time_progress_bar(minute, phase), 100, "c"))
    print()
    grouped = {}
    for game in live_games:
        key = game["home"].division if game["competition"] == "Liga" else "COPA"
        grouped.setdefault(key, []).append(game)

    ordered_keys = sorted([k for k in grouped if isinstance(k, int)]) + [k for k in grouped if not isinstance(k, int)]
    for key in ordered_keys:
        title = _division_label(key) if isinstance(key, int) else str(key)
        show_first_leg_column = any(_first_leg_text(game) for game in grouped[key])
        tbl = Table(title=title, border_color=C, header_color=YY, title_color=C)
        tbl.add_column("Jogo", width=46, align="l", color=WW)
        tbl.add_column("Lance Capital", width=56, align="l", color=WW)
        if show_first_leg_column:
            tbl.add_column("Ida", width=8, align="c", color=DIM)
            tbl.add_column("Agregado", width=10, align="c", color=YY)
        tbl.add_column("Público", width=9, align="r", color=G)

        for game in grouped[key]:
            hg, ag, recent = _score_at_minute(game, minute)
            game_str = _format_live_fixture(game["home"], game["away"], hg, ag)
            if game["is_player"]:
                game_str = GG + "► " + RST + game_str
            else:
                game_str = "  " + game_str
            capital = _latest_event_text(recent)
            first_leg = _first_leg_text(game)
            if show_first_leg_column:
                tbl.add_row(
                    game_str,
                    _fit_text(capital, 54) if capital else "",
                    first_leg or "",
                    _aggregate_text(game, minute) or "",
                    f"{game['attendance']:,}",
                )
            else:
                tbl.add_row(
                    game_str,
                    _fit_text(capital, 54) if capital else "",
                    f"{game['attendance']:,}",
                )
        tbl.print()
        print()

    if focus_game:
        print(C + f"  Seu jogo: {focus_game['home'].name} x {focus_game['away'].name}" + RST)
        if focus_game.get("first_leg_result") is not None:
            ida = focus_game["first_leg_result"]
            agg = _current_aggregate(focus_game, minute)
            if agg is not None:
                print(DIM + f"  Ida: {ida.home_team.name} {ida.home_goals}x{ida.away_goals} {ida.away_team.name}  │  Agregado: {focus_game['ref'].team_a.name} {agg[0]}x{agg[1]} {focus_game['ref'].team_b.name}" + RST)


def _matchday_has_player_game(season: Season, player_team) -> bool:
    if player_team is None or season.current_matchday >= len(season.calendar):
        return False
    matchday = season.calendar[season.current_matchday]
    for fixture in matchday.get("fixtures", []):
        if fixture.home_team.id == player_team.id or fixture.away_team.id == player_team.id:
            return True
    for tie in (matchday.get("ties") or []):
        if tie.team_a.id == player_team.id or tie.team_b.id == player_team.id:
            return True
    return False


def _render_substitution_screen(player_team, live_game, lineup, bench, subs_done: int):
    def _print_side_by_side_blocks(left: str, right: str, gap: int = 2):
        left_lines = left.split("\n")
        right_lines = right.split("\n")
        max_lines = max(len(left_lines), len(right_lines))
        left_w = max((_visible_len(line) for line in left_lines), default=0)
        for i in range(max_lines):
            l = left_lines[i] if i < len(left_lines) else ""
            r = right_lines[i] if i < len(right_lines) else ""
            print(l + " " * (left_w - _visible_len(l) + gap) + r)

    def _halftime_goal_lines(match) -> list[str]:
        events = list(((match.get("events_first") or {}).get("events") or []))
        goals = [event for event in events if event.get("type") == "goal"]
        goals.sort(key=lambda event: int(event.get("minute", 0)))
        if not goals:
            return [DIM + "  Nenhum gol no 1º tempo." + RST]
        lines = []
        for event in goals[:10]:
            minute = int(event.get("minute", 0))
            scorer = event.get("player_name") or event.get("scorer") or "Desconhecido"
            team_name = event.get("team_name") or (
                match["home"].name if event.get("side") == "home" else match["away"].name
            )
            lines.append(f"  {YY}{minute:>2}'{RST} {WW}{scorer}{RST} ({C}{team_name}{RST})")
        if len(goals) > 10:
            lines.append(DIM + f"  ... e mais {len(goals) - 10} gol(s)." + RST)
        return lines

    clear()
    print(rule("INTERVALO"))
    home_goals, away_goals, _ = _score_at_minute(live_game, 45)
    scoreboard = _format_live_fixture(live_game["home"], live_game["away"], home_goals, away_goals)
    left_lines = [
        "",
        f"  {C}{player_team.name}{RST}",
        f"  Substituições usadas: {YY}{subs_done}/5{RST}",
        "",
        f"  {WW}Opções:{RST}",
        f"  {YY}Sai quem?{RST} número do titular",
        f"  {YY}Entra quem?{RST} número do reserva",
        f"  {DIM}ENTER vazio mantém o time.{RST}",
        "",
    ]
    right_lines = [
        "",
        f"  Placar: {scoreboard}",
        "",
        f"  {WW}Quem fez os gols:{RST}",
        *_halftime_goal_lines(live_game),
        "",
    ]
    left_box = box(left_lines, title="SUBSTITUIÇÕES", border_color=GG, title_color=YY, width=46)
    right_box = box(right_lines, title="JOGO", border_color=C, title_color=YY, width=78)

    print()
    if _visible_len(left_box.split("\n")[0]) + 2 + _visible_len(right_box.split("\n")[0]) <= term_width():
        _print_side_by_side_blocks(left_box, right_box, gap=2)
    else:
        print(left_box)
        print()
        print(right_box)
    print()

    starters = Table(title="TITULARES", border_color=GG, header_color=YY, title_color=GG)
    starters.add_column("N", width=3, align="r", color=DIM)
    starters.add_column("Nome", width=22, align="l", color=WW)
    starters.add_column("Pos", width=5, align="c", color=C)
    starters.add_column("OVR", width=5, align="c", color=YY)
    for idx, player in enumerate(lineup, start=1):
        starters.add_row(str(idx), player.name, player.pos_label(), str(int(round(player.overall))))
    starters.print()

    print()
    reserves = Table(title="RESERVAS (MAX 12)", border_color=BB, header_color=YY, title_color=BB)
    reserves.add_column("N", width=3, align="r", color=DIM)
    reserves.add_column("Nome", width=22, align="l", color=WW)
    reserves.add_column("Pos", width=5, align="c", color=C)
    reserves.add_column("OVR", width=5, align="c", color=YY)
    for idx, player in enumerate(bench, start=1):
        reserves.add_row(str(idx), player.name, player.pos_label(), str(int(round(player.overall))))
    reserves.print()
    print()


def _handle_halftime_substitutions(player_team, live_game):
    lineup_key = "home_lineup" if live_game["home"].id == player_team.id else "away_lineup"
    bench_key = "home_bench" if live_game["home"].id == player_team.id else "away_bench"
    used_key = "home_used" if live_game["home"].id == player_team.id else "away_used"
    subs_key = "home_subs_used" if live_game["home"].id == player_team.id else "away_subs_used"

    lineup = list(live_game[lineup_key])
    bench = list(live_game[bench_key])
    subs_done = live_game[subs_key]

    while subs_done < 5 and bench:
        _render_substitution_screen(player_team, live_game, lineup, bench, subs_done)
        outgoing = input("  Sai quem? (ENTER para manter o time): ").strip()
        if not outgoing:
            break
        incoming = input("  Entra quem? (número do banco): ").strip()
        if not (outgoing.isdigit() and incoming.isdigit()):
            print(RR + "\n  Escolha inválida." + RST)
            time.sleep(1.2)
            continue

        out_idx = int(outgoing) - 1
        in_idx = int(incoming) - 1
        if out_idx not in range(len(lineup)) or in_idx not in range(len(bench)):
            print(RR + "\n  Índice inválido." + RST)
            time.sleep(1.2)
            continue

        leaving = lineup[out_idx]
        entering = bench.pop(in_idx)

        # Regra rígida: sempre exatamente 1 goleiro em campo.
        # Não pode entrar goleiro no lugar de jogador de linha nem sair goleiro para entrar jogador de linha.
        if (leaving.position.name == "GK" and entering.position.name != "GK") or (
            leaving.position.name != "GK" and entering.position.name == "GK"
        ):
            print(RR + "\n  Substituição inválida: o time deve manter exatamente 1 goleiro em campo." + RST)
            time.sleep(1.2)
            bench.insert(in_idx, entering)
            continue

        lineup[out_idx] = entering
        live_game[used_key].append(entering)
        subs_done += 1

        print(GG + f"\n  Substituição: saiu {leaving.name}, entrou {entering.name}." + RST)
        time.sleep(1.2)

    live_game[lineup_key] = lineup
    live_game[bench_key] = bench
    live_game[subs_key] = subs_done


def _play_live_half(label: str, phase: str, start_minute: int, end_minute: int, live_games, focus_game):
    minute_span = max(1, end_minute - start_minute)
    if focus_game:
        half_duration = HALF_DURATION_SECONDS
        redraw_each = 1
    else:
        half_duration = min(4.0, max(1.0, HALF_DURATION_SECONDS / 8))
        redraw_each = 5

    sleep_step = half_duration / minute_span
    for minute in range(start_minute, end_minute + 1):
        if minute == start_minute or minute == end_minute or (minute - start_minute) % redraw_each == 0:
            _render_live_scores(label, minute, live_games, focus_game=focus_game, phase=phase)
        if minute < end_minute:
            time.sleep(sleep_step)


def _finalize_live_games(season: Season, live_games):
    player_result = None
    other_results = []

    for game in live_games:
        first = game["events_first"]
        second = game["events_second"]
        home_goals = first["home_goals"] + second["home_goals"]
        away_goals = first["away_goals"] + second["away_goals"]
        home_scorers = first["home_scorers"] + second["home_scorers"]
        away_scorers = first["away_scorers"] + second["away_scorers"]

        result = finalize_match_result(
            home=game["home"],
            away=game["away"],
            competition=game["competition"],
            matchday=season.current_matchday,
            home_goals=home_goals,
            away_goals=away_goals,
            home_scorers=home_scorers,
            away_scorers=away_scorers,
            attendance=game.get("attendance", 0),
            events=first["events"] + second["events"],
            home_used=game["home_used"],
            away_used=game["away_used"],
        )

        rivalry_delta = 0.0
        if game["competition"] == "Liga":
            rivalry_delta += 0.40
            if game.get("league_title_clash"):
                rivalry_delta += 2.20
            if game.get("league_promotion_clash"):
                rivalry_delta += 1.80
        else:
            rivalry_delta += 1.00
            if game["kind"] == "tie":
                rivalry_delta += 0.80
                cup_leg = int(game.get("cup_leg", 1) or 1)
                tie = game.get("ref")
                if tie is not None and (getattr(tie, "single_leg", False) or cup_leg == 2):
                    rivalry_delta += 2.20
            if game.get("penalties"):
                rivalry_delta += 1.00
        _register_dynamic_rivalry(game["home"], game["away"], rivalry_delta)

        if game["kind"] == "fixture":
            game["ref"].result = result
        else:
            if game.get("cup_leg", 1) == 2 and not game["ref"].single_leg:
                game["ref"].leg2 = result
            else:
                game["ref"].leg1 = result

        season.results_history.append(result)
        if game["is_player"]:
            player_result = result
        else:
            other_results.append(result)

    return player_result, other_results


def _play_live_matchday(season: Season, player_team):
    matchday, live_games = _prepare_live_games(season, player_team)
    focus_game = next((game for game in live_games if game["is_player"]), None)

    _play_live_half(matchday["label"], "1º TEMPO", 0, 45, live_games, focus_game)

    if focus_game:
        _handle_halftime_substitutions(player_team, focus_game)
        focus_game["events_second"] = simulate_half(
            focus_game["home"],
            focus_game["away"],
            focus_game["home_lineup"],
            focus_game["away_lineup"],
            46,
            90,
            focus_game["competition"],
        )
        _apply_red_card_effects(focus_game, "events_second")

    _play_live_half(matchday["label"], "2º TEMPO", 46, 90, live_games, focus_game)

    for game in live_games:
        first = game["events_first"]
        second = game["events_second"]
        final_home_goals = first["home_goals"] + second["home_goals"]
        final_away_goals = first["away_goals"] + second["away_goals"]
        game["final_home_goals"] = final_home_goals
        game["final_away_goals"] = final_away_goals
        if game["kind"] != "tie":
            continue
        tie = game["ref"]
        needs_penalties = False
        if tie.single_leg:
            needs_penalties = final_home_goals == final_away_goals
        elif game.get("cup_leg") == 2 and game.get("first_leg_result") is not None:
            first_leg = game["first_leg_result"]
            agg_a = first_leg.home_goals + final_away_goals
            agg_b = first_leg.away_goals + final_home_goals
            needs_penalties = agg_a == agg_b
        if needs_penalties:
            winner, score, log = simulate_penalty_series(game["home"], game["away"])
            mapped_winner = winner
            if not tie.single_leg and game.get("cup_leg") == 2:
                mapped_winner = tie.team_b if winner.id == game["home"].id else tie.team_a
            elif tie.single_leg:
                mapped_winner = winner
            tie.set_penalty_winner(mapped_winner, score)
            game["penalties"] = {
                "winner": mapped_winner,
                "score": score,
                "log": [
                    {
                        **kick,
                        "side": "home" if kick["team"] == game["home"].name else "away",
                    }
                    for kick in log
                ],
            }

    if focus_game and focus_game.get("penalties"):
        _render_penalty_shootout(focus_game)

    player_result, other_results = _finalize_live_games(season, live_games)
    advance_season_after_matchday(season)
    return {
        "done": False,
        "label": matchday["label"],
        "type": matchday["type"],
        "player_result": player_result,
        "other_results": other_results,
        "matchday_num": season.current_matchday,
    }


def run_game(season: Season, player_team, market: TransferMarket, career: CareerState):
    """Loop principal de uma temporada."""
    _ensure_stars_in_all_teams(season.all_teams)
    if not hasattr(career, "back_to_main_menu"):
        career.back_to_main_menu = False
    while not season.season_over:
        current = current_player_team(career, season.all_teams)
        unemployed = current is None and career.unemployed
        if current is not None:
            player_team = current
            season.player_team_id = current.id
        _maybe_show_pending_cup_draws(season, None if unemployed else player_team)
        if not unemployed and not _matchday_has_player_game(season, player_team):
            round_data = _play_next_match(season, player_team, market)
            if round_data.get("player_played"):
                career.games_in_charge += 1
            player_team, career_end = _post_round_updates(
                season,
                player_team,
                career,
                round_data.get("messages") or [],
                round_type=round_data.get("round_type"),
                round_marker=round_data.get("round_marker"),
            )
            if career_end:
                return player_team
            continue
        season_dashboard(season, None if unemployed else player_team)
        choice = game_menu()

        if choice == "1":
            # Próxima rodada (preview)
            if unemployed:
                print(YY + "\n  Sem clube no momento. Avance a rodada para buscar ofertas." + RST)
                pause()
            else:
                show_next_round(season, player_team)

        elif choice == "2":
            # Classificação
            show_standings(season, player_team)
            show_top_scorers(season)

        elif choice == "3":
            # Copa
            show_copa(season, player_team)

        elif choice == "4":
            # Formação
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                player_team = show_tactics(player_team)

        elif choice == "5":
            # Postura
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                player_team.postura = choose_postura(player_team.postura)

        elif choice == "6":
            # Jogar partida
            round_data = _play_next_match(season, None if unemployed else player_team, market)
            if round_data.get("cancelled"):
                continue
            if round_data.get("player_played"):
                career.games_in_charge += 1
            player_team, career_end = _post_round_updates(season, player_team, career, round_data.get("messages") or [])
            season.player_team_id = player_team.id if player_team and not career.unemployed else season.player_team_id
            if career_end:
                print(RR + "\n  Sem clube após a rodada. Fim da carreira." + RST)
                pause()
                return player_team

        elif choice == "7":
            # Finanças
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                show_finances(player_team, season)

        elif choice == "8":
            # Torcida
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                show_torcida(player_team)

        elif choice == "9":
            # Estádio
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                show_stadium(player_team)

        elif choice == "C":
            # Calendário
            show_calendar(season, None if unemployed else player_team)

        elif choice == "R":
            # Renovação de contrato
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                target_player, offered_salary = prompt_contract_renewal(player_team)
                if target_player and offered_salary:
                    accepted, message = negotiate_contract(target_player, offered_salary)
                    messages = [message]
                    if not accepted:
                        messages.extend(run_immediate_contract_auction(target_player, player_team, season.all_teams))
                    show_notifications(messages, title="RENOVAÇÃO DE CONTRATO")

        elif choice == "T":
            # Transferências
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                show_transfer_market(market, player_team)

        elif choice == "E":
            # Treino
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                player_team = show_training(player_team)

        elif choice == "A":
            # Artilheiros
            show_top_scorers(season)

        elif choice == "V":
            # Vender jogador
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST)
                pause()
            else:
                manage_player_sales(player_team, market)

        elif choice == "H":
            # Histórico
            show_history(career)

        elif choice == "S":
            # Salvar
            state = {"season": season, "player_team": player_team, "market": market, "career": career}
            ok = save_game(state)
            print((GG if ok else RR) + ("  Jogo salvo!" if ok else "  Erro ao salvar.") + RST)
            pause()

        elif choice == "0":
            # Volta ao menu principal
            career.back_to_main_menu = True
            return player_team

    if season.season_over and player_team is not None:
        show_season_end(season, player_team)

    return player_team


def _play_next_match(season: Season, player_team, market: TransferMarket):
    """Gerencia a jogada de uma rodada."""
    if season.current_matchday >= len(season.calendar):
        print(DIM + "  Temporada encerrada." + RST)
        pause()
        return {"messages": [], "player_played": False}

    has_player_game = _matchday_has_player_game(season, player_team)

    # Confirmação de postura
    if player_team is not None and has_player_game:
        pre_match_choice = confirm_play(player_team.formation, player_team.postura)
        if pre_match_choice == "adjust":
            player_team = show_tactics(player_team)
        elif pre_match_choice == "back":
            return {"messages": [], "player_played": False, "cancelled": True}

    blocked_bidder_ids = {player_team.id} if player_team is not None else set()

    # Gera leilões antes da rodada
    auctions = market.generate_auctions(season.all_teams)
    if auctions:
        market.ai_bidding(season.all_teams, blocked_team_ids=blocked_bidder_ids)
        if player_team is not None:
            show_transfer_market(market, player_team)

    # Resolve leilões anteriores
    if market.auctions:
        market.ai_bidding(season.all_teams, blocked_team_ids=blocked_bidder_ids)
        results = market.resolve_all(round_num=season.current_matchday + 1)
        if results:
            show_auction_results(results)

    # Simula a rodada ao vivo
    info = _play_live_matchday(season, player_team)

    if info.get("done"):
        return {
            "messages": [],
            "player_played": False,
            "round_type": None,
            "round_marker": season.current_matchday,
        }

    # Aplica treino somente após a rodada ser concluída.
    played_round = max(0, int(info.get("matchday_num", 1)) - 1)
    training_messages = _apply_training_if_due(played_round, player_team) if player_team is not None else []
    if training_messages:
        show_notifications(training_messages, title="CENTRO DE TREINAMENTO")

    # Exibe resultados dos outros jogos
    other = info.get("other_results", [])
    if other:
        clear()
        print(rule(info['label']))
        print(C + "\n  Outros Resultados:" + RST)
        for r in other:
            hg = r.home_goals; ag = r.away_goals
            if hg > ag:   sc = GG + f"{hg} × {ag}" + RST
            elif hg < ag: sc = RR + f"{hg} × {ag}" + RST
            else:         sc = YY + f"{hg} × {ag}" + RST
            print(f"  {WW}{r.home_team.name:<22}{RST} {sc} {WW}{r.away_team.name}{RST}")

        # Exibe top 5 artilheiros da temporada
        all_players = [(t, p) for t in season.all_teams for p in t.players]
        top_scorers = sorted(all_players, key=lambda x: -x[1].gols_temp)[:5]

        print()
        print(C + "  TOP ARTILHEIROS DA RODADA:" + RST)
        for i, (team, p) in enumerate(top_scorers, 1):
            if p.gols_temp > 0:
                print(f"  {DIM}{i}.{RST} {WW}{pad(p.name, 20)}{RST} ({C}{team.name}{RST}) — {GG}{p.gols_temp}{RST} gols")

    # Após a rodada, abre a visão macro da competição em vez do resultado isolado.
    if info.get("type") == "liga":
        show_standings(season, player_team)
        show_top_scorers(season)
    else:
        if not _maybe_show_pending_cup_draws(season, player_team):
            show_copa(season, player_team)
        show_top_scorers(season)

    # Paga salários a cada 4 rodadas (= ~1 mês)
    if season.current_matchday % 4 == 0:
        pay_monthly_salaries(season.all_teams)
        print(RR + "\n  💸 Salários mensais pagos!" + RST)
        pause()

    # Resultado de leilão já foi exibido em tela própria.
    return {
        "messages": training_messages,
        "player_played": info.get("player_result") is not None,
        "round_type": info.get("type"),
        "round_marker": info.get("matchday_num"),
    }


def _run_career_loop(season: Season, player_team, market: TransferMarket, career: CareerState):
    """Loop unificado de progressão de carreira.

    Recebe a temporada já criada e itera: joga a temporada, registra histórico,
    verifica demissões/ofertas e cria a próxima temporada — até o jogador voltar
    ao menu principal.
    """
    while True:
        current_pt = current_player_team(career, season.all_teams)
        if current_pt is not None:
            player_team = current_pt

        display_pt = None if career.unemployed else player_team
        if not _maybe_show_pending_cup_draws(season, display_pt):
            show_copa(season, display_pt)

        player_team = run_game(season, player_team, market, career)

        if getattr(career, "back_to_main_menu", False):
            career.back_to_main_menu = False
            return

        _record_season_history(season, player_team, career)

        end_firing = check_last_division_relegation_firing(season, career)
        if end_firing:
            show_notifications([end_firing], title="CENTRAL DE NOTÍCIAS")
            offers = generate_player_offers(season.all_teams, career)
            if offers:
                for offer in offers:
                    if prompt_job_offer(career.player_coach.name, offer, season.all_teams):
                        player_team, messages = accept_player_offer(offer, season.all_teams, career)
                        show_notifications(messages, title="MERCADO DE TREINADORES")
                        break
                    show_notifications(reject_player_offer(offer, season.all_teams, career), title="MERCADO DE TREINADORES")

        # Avança para a próxima temporada
        teams = season.all_teams
        next_year = season.year + 1
        pt_id = player_team.id if (player_team is not None and not career.unemployed) else -1
        season = create_season(next_year, teams, pt_id)
        if player_team is not None:
            player_team = next((t for t in teams if t.id == player_team.id), player_team)


def new_game():
    """Inicia uma nova partida."""
    teams = create_teams()
    coach = _create_manager()
    player_team = _assign_random_last_division_team(teams, coach)
    career = CareerState(
        player_coach=coach,
        current_team_id=player_team.id,
        unemployed=False,
        free_coaches=create_free_coaches(),
    )

    show_onboarding()

    print(GG + f"\n  ✓ Treinador: {coach.name}" + RST)
    print(C + f"  Clube sorteado da Divisão 4: {player_team.name}" + RST)
    pause()

    season = create_season(YEAR_START, teams, player_team.id)
    _run_career_loop(season, player_team, TransferMarket(), career)


def main():
    while True:
        banner()
        choice = main_menu()

        if choice == "1":
            new_game()

        elif choice == "2":
            if save_exists():
                state = load_game()
                if state:
                    season = state["season"]
                    pt = state["player_team"]
                    market = state.get("market", TransferMarket())
                    career = state.get("career")
                    if career is None:
                        career = CareerState(
                            player_coach=pt.coach,
                            current_team_id=pt.id,
                            unemployed=False,
                            free_coaches=create_free_coaches(),
                        )
                    # Migra saves antigos uma única vez ao carregar
                    _normalize_world_history(career)
                    _run_career_loop(season, pt, market, career)
                else:
                    print(RR + "  Erro ao carregar o save." + RST)
                    pause()
            else:
                print(YY + "  Nenhum save encontrado." + RST)
                pause()

        elif choice == "3":
            show_credits()

        elif choice == "0":
            print("\n" + DIM + "  Até logo!\n" + RST)
            sys.exit(0)


if __name__ == "__main__":
    main()
