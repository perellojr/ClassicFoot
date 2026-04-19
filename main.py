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
from engine import (
    finalize_match_result, select_bench, select_starting_lineup, simulate_half,
    simulate_penalty_series, estimate_attendance,
    apply_red_card_effects, apply_auto_injury_substitutions, pick_injury_replacement,
)
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
    # Rendering de partidas ao vivo
    _render_live_scores, _render_penalty_shootout,
    _render_substitution_screen, _matchday_has_player_game,
    _score_at_minute, _format_live_fixture,
)
from save import save_game, load_game, save_exists, ensure_world_history, normalize_world_history
from application.events import append_career_notifications
from application.orchestrator import CareerOrchestrator, UIAdapter, GameAdapter
from config.runtime import apply_random_seed_from_env
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
    normalize_world_history(career)
    world_history = ensure_world_history(career)
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

    append_career_notifications(
        career,
        transfer_messages,
        kind="transfer",
        round_num=round_marker,
        season_year=season.year,
    )
    if round_type == "liga":
        append_career_notifications(
            career,
            process_coach_market(season.all_teams, career, round_marker=round_marker),
            kind="coach_market",
            round_num=round_marker,
            season_year=season.year,
        )

    firing_msg = check_player_firing(season.all_teams, career)
    if firing_msg:
        append_career_notifications(
            career,
            [firing_msg],
            kind="firing",
            round_num=round_marker,
            season_year=season.year,
        )
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
                append_career_notifications(
                    career,
                    messages,
                    kind="job_change",
                    round_num=round_marker,
                    season_year=season.year,
                )
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
            "attendance": estimate_attendance(
                home,
                away,
                game["competition"],
                is_classic=_is_classic(home, away),
                is_state_rivalry=_is_state_rivalry(home, away),
                phase=game["ref"].phase if game["kind"] == "tie" else None,
            ),
            "events_first": simulate_half(home, away, home_lineup, away_lineup, 0, 45, game["competition"]),
            "events_second": None,
        }
        apply_red_card_effects(live_game, "events_first")
        if not game["is_player"]:
            live_game["events_second"] = simulate_half(
                home, away, live_game["home_lineup"], live_game["away_lineup"], 46, 90, game["competition"]
            )
            apply_red_card_effects(live_game, "events_second")
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
        apply_red_card_effects(focus_game, "events_second")

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
    orchestrator = CareerOrchestrator(
        ui=UIAdapter(
            maybe_show_pending_cup_draws=_maybe_show_pending_cup_draws,
            show_copa=show_copa,
            show_notifications=show_notifications,
            prompt_job_offer=prompt_job_offer,
        ),
        game=GameAdapter(
            run_game=run_game,
            record_season_history=_record_season_history,
            check_last_division_relegation_firing=check_last_division_relegation_firing,
            generate_player_offers=generate_player_offers,
            accept_player_offer=accept_player_offer,
            reject_player_offer=reject_player_offer,
            create_season=create_season,
            current_player_team=current_player_team,
        ),
    )
    orchestrator.run_career_loop(season, player_team, market, career)


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
    apply_random_seed_from_env()
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
