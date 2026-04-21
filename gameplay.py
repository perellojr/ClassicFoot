"""Simulação ao vivo de rodadas — preparação, execução e finalização de partidas."""
import os
import time

from engine import (
    select_starting_lineup, select_bench, simulate_half,
    simulate_penalty_series, estimate_attendance,
    apply_red_card_effects, finalize_match_result,
)
from season import Season, advance_season_after_matchday
from rivalries import is_classic, is_state_rivalry, league_rivalry_context, register_dynamic_rivalry
from ui import (
    _render_live_scores, _render_penalty_shootout,
    _render_substitution_screen,
)
from term import GG, RR, RST

HALF_DURATION_SECONDS = float(os.getenv("CLASSICFOOT_HALF_DURATION_SECONDS", "21.9"))


def collect_current_match_objects(season: Season, player_team):
    """Retorna (matchday_dict, lista de game_dicts) para a rodada atual."""
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
            "is_player": player_team is not None and (
                fixture.home_team.id == player_team.id or fixture.away_team.id == player_team.id
            ),
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
            "is_player": player_team is not None and (
                tie.team_a.id == player_team.id or tie.team_b.id == player_team.id
            ),
        })
    return matchday, games


def prepare_live_games(season: Season, player_team):
    """Seleciona lineups e simula o primeiro tempo de todos os jogos."""
    matchday, games = collect_current_match_objects(season, player_team)
    live_games = []
    for game in games:
        home = game["home"]
        away = game["away"]
        if game["competition"] == "Liga":
            game.update(league_rivalry_context(season, home, away, int(game.get("round_num", 0))))
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
                home, away, game["competition"],
                is_classic=is_classic(home, away),
                is_state_rivalry=is_state_rivalry(home, away),
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


def handle_halftime_substitutions(player_team, live_game) -> None:
    """Permite ao jogador fazer até 5 substituições no intervalo."""
    lineup_key = "home_lineup" if live_game["home"].id == player_team.id else "away_lineup"
    bench_key  = "home_bench"  if live_game["home"].id == player_team.id else "away_bench"
    used_key   = "home_used"   if live_game["home"].id == player_team.id else "away_used"
    subs_key   = "home_subs_used" if live_game["home"].id == player_team.id else "away_subs_used"

    lineup = list(live_game[lineup_key])
    bench  = list(live_game[bench_key])
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
        in_idx  = int(incoming) - 1
        if out_idx not in range(len(lineup)) or in_idx not in range(len(bench)):
            print(RR + "\n  Índice inválido." + RST)
            time.sleep(1.2)
            continue

        leaving  = lineup[out_idx]
        entering = bench.pop(in_idx)

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
    live_game[bench_key]  = bench
    live_game[subs_key]   = subs_done


def play_live_half(label: str, phase: str, start_minute: int, end_minute: int, live_games, focus_game) -> None:
    """Renderiza o placar ao vivo minuto a minuto."""
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


def finalize_live_games(season: Season, live_games):
    """Consolida resultados, registra rivalidades e popula results_history."""
    player_result = None
    other_results = []

    for game in live_games:
        first  = game["events_first"]
        second = game["events_second"]
        home_goals   = first["home_goals"]   + second["home_goals"]
        away_goals   = first["away_goals"]   + second["away_goals"]
        home_scorers = first["home_scorers"] + second["home_scorers"]
        away_scorers = first["away_scorers"] + second["away_scorers"]

        result = finalize_match_result(
            home=game["home"], away=game["away"],
            competition=game["competition"],
            matchday=season.current_matchday,
            home_goals=home_goals, away_goals=away_goals,
            home_scorers=home_scorers, away_scorers=away_scorers,
            attendance=game.get("attendance", 0),
            events=first["events"] + second["events"],
            home_used=game["home_used"], away_used=game["away_used"],
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
        register_dynamic_rivalry(game["home"], game["away"], rivalry_delta)

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


def play_live_matchday(season: Season, player_team) -> dict:
    """Executa uma rodada completa ao vivo e retorna informações do resultado."""
    matchday, live_games = prepare_live_games(season, player_team)
    focus_game = next((game for game in live_games if game["is_player"]), None)

    play_live_half(matchday["label"], "1º TEMPO", 0, 45, live_games, focus_game)

    if focus_game:
        handle_halftime_substitutions(player_team, focus_game)
        focus_game["events_second"] = simulate_half(
            focus_game["home"], focus_game["away"],
            focus_game["home_lineup"], focus_game["away_lineup"],
            46, 90, focus_game["competition"],
        )
        apply_red_card_effects(focus_game, "events_second")

    play_live_half(matchday["label"], "2º TEMPO", 46, 90, live_games, focus_game)

    for game in live_games:
        first  = game["events_first"]
        second = game["events_second"]
        game["final_home_goals"] = first["home_goals"] + second["home_goals"]
        game["final_away_goals"] = first["away_goals"] + second["away_goals"]
        if game["kind"] != "tie":
            continue
        tie = game["ref"]
        final_home_goals = game["final_home_goals"]
        final_away_goals = game["final_away_goals"]
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
            if not tie.single_leg and game.get("cup_leg") == 2:
                mapped_winner = tie.team_b if winner.id == game["home"].id else tie.team_a
            else:
                mapped_winner = winner
            tie.set_penalty_winner(mapped_winner, score)
            game["penalties"] = {
                "winner": mapped_winner, "score": score,
                "log": [
                    {**kick, "side": "home" if kick["team"] == game["home"].name else "away"}
                    for kick in log
                ],
            }

    if focus_game and focus_game.get("penalties"):
        _render_penalty_shootout(focus_game)

    player_result, other_results = finalize_live_games(season, live_games)
    advance_season_after_matchday(season)
    return {
        "done": False,
        "label": matchday["label"],
        "type": matchday["type"],
        "player_result": player_result,
        "other_results": other_results,
        "matchday_num": season.current_matchday,
    }
