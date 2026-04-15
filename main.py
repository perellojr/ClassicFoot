"""
ClassicFoot - Brasileirão Edition
Loop principal do jogo
"""
import random
import sys
import time
import os
from colorama import Back, Fore, Style

from data import create_teams
from manager_market import (
    accept_player_offer,
    check_last_division_relegation_firing,
    check_player_firing,
    create_free_coaches,
    current_player_team,
    generate_player_offers,
    process_coach_market,
)
from models import CareerState, Coach, Postura
from engine import finalize_match_result, select_bench, select_starting_lineup, simulate_half
from season import Season, advance_season_after_matchday, create_season, play_matchday, pay_monthly_salaries
from transfers import TransferMarket
from transfers import negotiate_contract, run_immediate_contract_auction
from ui import (
    banner, main_menu, season_dashboard, game_menu,
    show_standings, show_copa, show_tactics, show_finances,
    show_torcida, show_stadium, show_next_round, choose_postura,
    show_transfer_market, show_top_scorers, show_match_result, prompt_contract_renewal,
    show_season_end, show_credits, confirm_play, show_notifications, prompt_job_offer,
)
from save import save_game, load_game, save_exists
from term import BB, C, G, GG, RR, R, RST, W, WW, Y, YY, DIM, Table, pause, clear, rule, pad

YEAR_START = 2025
HALF_DURATION_SECONDS = float(os.getenv("CLASSICFOOT_HALF_DURATION_SECONDS", "27"))


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
    for message in messages:
        if message:
            career.notifications.append(message)


def _post_round_updates(season: Season, player_team, career: CareerState, transfer_messages):
    _append_notifications(career, transfer_messages)
    _append_notifications(career, process_coach_market(season.all_teams, career))

    firing_msg = check_player_firing(season.all_teams, career)
    if firing_msg:
        _append_notifications(career, [firing_msg])
        show_notifications(career.notifications, title="CENTRAL DE NOTÍCIAS")
        career.notifications.clear()
        offers = generate_player_offers(season.all_teams, career)
        if offers:
            for offer in offers:
                accepted = prompt_job_offer(career.player_coach.name, offer)
                if accepted:
                    player_team, messages = accept_player_offer(offer, season.all_teams, career)
                    show_notifications(messages, title="MERCADO DE TREINADORES")
                    return player_team, False
            return player_team, False
        return player_team, False

    offers = generate_player_offers(season.all_teams, career)
    if offers:
        for offer in offers:
            accepted = prompt_job_offer(career.player_coach.name, offer)
            if accepted:
                player_team, messages = accept_player_offer(offer, season.all_teams, career)
                _append_notifications(career, messages)
                break

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
    games = []
    for fixture in matchday.get("fixtures", []):
        games.append({
            "kind": "fixture",
            "ref": fixture,
            "home": fixture.home_team,
            "away": fixture.away_team,
            "competition": fixture.competition,
            "is_player": player_team is not None and (fixture.home_team.id == player_team.id or fixture.away_team.id == player_team.id),
        })
    for tie in matchday.get("ties", []):
        home = tie.team_a if cup_leg == 1 or tie.single_leg else tie.team_b
        away = tie.team_b if cup_leg == 1 or tie.single_leg else tie.team_a
        games.append({
            "kind": "tie",
            "ref": tie,
            "home": home,
            "away": away,
            "competition": "Copa",
            "cup_leg": cup_leg,
            "is_player": player_team is not None and (tie.team_a.id == player_team.id or tie.team_b.id == player_team.id),
        })
    return matchday, games


def _prepare_live_games(season: Season, player_team):
    matchday, games = _collect_current_match_objects(season, player_team)
    live_games = []
    for game in games:
        home = game["home"]
        away = game["away"]
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
            "attendance": _estimate_attendance(home),
            "events_first": simulate_half(home, away, home_lineup, away_lineup, 0, 45, game["competition"]),
            "events_second": None,
        }
        _apply_red_card_effects(live_game, "events_first")
        _apply_auto_injury_substitutions(live_game, "events_first")
        if not game["is_player"]:
            live_game["events_second"] = simulate_half(
                home, away, live_game["home_lineup"], live_game["away_lineup"], 46, 90, game["competition"]
            )
            _apply_red_card_effects(live_game, "events_second")
            _apply_auto_injury_substitutions(live_game, "events_second")
        live_games.append(live_game)
    return matchday, live_games


def _estimate_attendance(home_team) -> int:
    capacity_estimate = home_team.stadium_capacity
    occupation = min(0.96, max(0.28, 0.42 + (home_team.prestige / 200)))
    return min(capacity_estimate, int(capacity_estimate * occupation))


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


def _team_bg_color(team) -> str:
    return {
        "red": Back.RED,
        "dark_red": Back.RED,
        "green": Back.GREEN,
        "blue": Back.BLUE,
        "yellow": Back.YELLOW,
        "black": Back.BLACK,
        "white": Back.WHITE,
    }.get(getattr(team, "primary_color", "white"), Back.WHITE)


def _team_fg_color(team) -> str:
    return {
        "red": Fore.RED,
        "dark_red": Fore.RED,
        "green": Fore.GREEN,
        "blue": Fore.BLUE,
        "yellow": Fore.YELLOW,
        "black": Fore.BLACK,
        "white": Fore.WHITE,
    }.get(getattr(team, "secondary_color", "white"), Fore.WHITE)


def _paint_team(team, text: str | None = None) -> str:
    label = text if text is not None else team.name
    return _team_bg_color(team) + _team_fg_color(team) + Style.BRIGHT + label + RST


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


def _latest_event_text(events):
    if not events:
        return DIM + "sem lance capital" + RST
    event = events[-1]
    prefix = f"{event['minute']:>2}' "
    event_type = event.get("type", "goal" if event.get("scorer") or event.get("player_name") else "event")
    player_name = event.get("player_name") or event.get("scorer") or "evento"
    if event_type == "goal":
        return GG + prefix + RST + WW + f"{player_name}" + RST
    if event_type == "yellow":
        return YY + prefix + RST + WW + f"cartão: {player_name}" + RST
    if event_type == "red":
        return RR + prefix + RST + WW + f"expulso: {player_name}" + RST
    if event_type == "injury":
        return RR + prefix + RST + WW + f"lesão: {player_name}" + RST
    if event_type == "substitution":
        return BB + prefix + RST + WW + f"sub: {player_name}" + RST
    return WW + prefix + player_name + RST


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


def _pick_injury_replacement(bench, injured_player):
    if not bench:
        return None
    same_position = [player for player in bench if player.position == injured_player.position]
    pool = same_position or list(bench)
    pool.sort(key=lambda player: (player.overall, player.forma, player.condicao_fisica), reverse=True)
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
    return name[: limit - 1].rstrip() + "…"


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
        tbl = Table(title=title, border_color=C, header_color=YY, title_color=C)
        tbl.add_column("Jogo", width=52, align="l", color=WW)
        tbl.add_column("Lance Capital", width=38, align="l", color=WW)
        tbl.add_column("Público", width=10, align="r", color=G)

        for game in grouped[key]:
            hg, ag, recent = _score_at_minute(game, minute)
            game_str = _format_live_fixture(game["home"], game["away"], hg, ag)
            if game["is_player"]:
                game_str = GG + "► " + RST + game_str
            else:
                game_str = "  " + game_str
            tbl.add_row(
                game_str,
                _latest_event_text(recent),
                f"{game['attendance']:,}",
            )
        tbl.print()
        print()

    if focus_game:
        print(C + f"  Seu jogo: {focus_game['home'].name} x {focus_game['away'].name}" + RST)


def _render_substitution_screen(player_team, live_game, lineup, bench, subs_done: int):
    clear()
    print(rule("INTERVALO"))
    home_goals, away_goals, _ = _score_at_minute(live_game, 45)
    scoreboard = _format_live_fixture(live_game["home"], live_game["away"], home_goals, away_goals)
    print()
    print(pad(scoreboard, 100, "c"))
    print(C + f"\n  {player_team.name}  •  substituições usadas: {subs_done}/5\n" + RST)

    starters = Table(title="TITULARES", border_color=GG, header_color=YY, title_color=GG)
    starters.add_column("N", width=3, align="r", color=DIM)
    starters.add_column("Nome", width=22, align="l", color=WW)
    starters.add_column("Pos", width=5, align="c", color=C)
    starters.add_column("OVR", width=5, align="c", color=YY)
    starters.add_column("FIS", width=5, align="c", color=GG)
    for idx, player in enumerate(lineup, start=1):
        starters.add_row(str(idx), player.name, player.pos_label(), str(player.overall), str(player.condicao_fisica))
    starters.print()

    print()
    reserves = Table(title="RESERVAS (MAX 12)", border_color=BB, header_color=YY, title_color=BB)
    reserves.add_column("N", width=3, align="r", color=DIM)
    reserves.add_column("Nome", width=22, align="l", color=WW)
    reserves.add_column("Pos", width=5, align="c", color=C)
    reserves.add_column("OVR", width=5, align="c", color=YY)
    reserves.add_column("FIS", width=5, align="c", color=GG)
    for idx, player in enumerate(bench, start=1):
        reserves.add_row(str(idx), player.name, player.pos_label(), str(player.overall), str(player.condicao_fisica))
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
            home_used=game["home_used"],
            away_used=game["away_used"],
        )

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
        _apply_auto_injury_substitutions(focus_game, "events_second")

    _play_live_half(matchday["label"], "2º TEMPO", 46, 90, live_games, focus_game)
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
    while not season.season_over:
        current = current_player_team(career, season.all_teams)
        unemployed = current is None and career.unemployed
        if current is not None:
            player_team = current
            season.player_team_id = current.id
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
            transfer_messages = _play_next_match(season, None if unemployed else player_team, market)
            player_team, career_end = _post_round_updates(season, player_team, career, transfer_messages or [])
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
                show_finances(player_team)

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

        elif choice == "A":
            # Artilheiros
            show_top_scorers(season)

        elif choice == "S":
            # Salvar
            state = {"season": season, "player_team": player_team, "market": market, "career": career}
            ok = save_game(state)
            print((GG if ok else RR) + ("  Jogo salvo!" if ok else "  Erro ao salvar.") + RST)
            pause()

        elif choice == "0":
            # Volta ao menu principal
            break

    if season.season_over and player_team is not None:
        show_season_end(season, player_team)

    return player_team


def _play_next_match(season: Season, player_team, market: TransferMarket):
    """Gerencia a jogada de uma rodada."""
    if season.current_matchday >= len(season.calendar):
        print(DIM + "  Temporada encerrada." + RST)
        pause()
        return

    # Confirmação de postura
    if player_team is not None and not confirm_play(player_team.formation, player_team.postura):
        player_team = show_tactics(player_team)

    # Gera leilões antes da rodada
    auctions = market.generate_auctions(season.all_teams)
    if auctions and player_team is not None:
        show_transfer_market(market, player_team)
        # IA faz lances
        market.ai_bidding(season.all_teams)
    elif auctions:
        market.ai_bidding(season.all_teams)

    # Resolve leilões anteriores
    transfer_messages = []
    if market.auctions:
        results = market.resolve_all()
        if results:
            transfer_messages.extend(results)

    # Simula a rodada ao vivo
    info = _play_live_matchday(season, player_team)

    if info.get("done"):
        return

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

    # Após a rodada, abre a visão macro da competição em vez do resultado isolado.
    if info.get("type") == "liga":
        show_standings(season, player_team)
    else:
        show_copa(season, player_team)

    # Paga salários a cada 4 rodadas (= ~1 mês)
    if season.current_matchday % 4 == 0:
        pay_monthly_salaries(season.all_teams)
        print(RR + "\n  💸 Salários mensais pagos!" + RST)
        pause()

    return transfer_messages


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

    print(GG + f"\n  ✓ Treinador: {coach.name}" + RST)
    print(C + f"  Clube sorteado da Divisão 4: {player_team.name}" + RST)
    pause()

    year = YEAR_START
    market = TransferMarket()

    while True:
        season = create_season(year, teams, player_team.id if player_team else -1)
        if player_team is not None:
            player_team = next((t for t in teams if t.id == player_team.id), player_team)
        show_copa(season, player_team)
        player_team = run_game(season, player_team, market, career)

        end_firing = check_last_division_relegation_firing(season, career)
        if end_firing:
            show_notifications([end_firing], title="CENTRAL DE NOTÍCIAS")
            offers = generate_player_offers(season.all_teams, career)
            if offers:
                for offer in offers:
                    if prompt_job_offer(career.player_coach.name, offer):
                        player_team, messages = accept_player_offer(offer, season.all_teams, career)
                        show_notifications(messages, title="MERCADO DE TREINADORES")
                        break

        # Confirma nova temporada
        clear()
        print(YY + f"\n  Nova temporada {year + 1}?  [1] Sim   [0] Não" + RST)
        if input("  Escolha: ").strip() != "1":
            break
        year += 1


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
                    season  = state["season"]
                    pt      = state["player_team"]
                    market  = state.get("market", TransferMarket())
                    career  = state.get("career")
                    if career is None:
                        career = CareerState(
                            player_coach=pt.coach,
                            current_team_id=pt.id,
                            unemployed=False,
                            free_coaches=create_free_coaches(),
                        )
                    run_game(season, pt, market, career)
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
