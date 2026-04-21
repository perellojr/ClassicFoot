"""
ClassicFoot - Brasileirão Edition
Loop principal do jogo
"""
import random
import sys

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
from models import CareerState, Coach
from season import Season, create_season, pay_monthly_salaries
from transfers import TransferMarket, negotiate_contract, run_immediate_contract_auction
from ui import (
    banner, main_menu, season_dashboard, game_menu,
    show_standings, show_copa, show_tactics, show_finances,
    show_torcida, show_stadium, show_next_round, choose_postura, show_calendar,
    show_transfer_market, show_top_scorers, prompt_contract_renewal,
    show_season_end, show_credits, confirm_play, show_notifications, prompt_job_offer,
    manage_player_sales, show_history, show_training, show_auction_results, show_copa_draw,
    show_onboarding,
    _matchday_has_player_game,
)
from save import save_game, load_game, save_exists
from application.events import append_career_notifications
from application.history import record_season_history
from application.orchestrator import CareerOrchestrator, UIAdapter, GameAdapter
from config.runtime import apply_random_seed_from_env
from gameplay import play_live_matchday
from term import C, GG, RR, RST, WW, YY, DIM, pause, clear, rule, pad

YEAR_START = 2025


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
    return Coach(
        name=f"{first_name} {last_name}",
        nationality="Brasileiro",
        tactical=random.randint(68, 76),
        motivation=random.randint(70, 80),
        experience=random.randint(58, 70),
    )


def _assign_random_last_division_team(teams, coach: Coach):
    player_team = random.choice([t for t in teams if t.division == 4])
    player_team.coach = coach
    return player_team


def _apply_training_if_due(round_marker: int, team):
    """Aplica treino de até 5 jogadores uma vez por rodada do calendário."""
    if team is None or team.training_round_applied == round_marker:
        return []

    selected_ids = list(dict.fromkeys(team.training_targets or []))[:5]
    auto_selected = False
    if not selected_ids:
        pool = [p.id for p in team.players]
        random.shuffle(pool)
        selected_ids = pool[:min(5, len(pool))]
        auto_selected = True

    improved = []
    for player in team.players:
        if player.id not in selected_ids:
            continue
        old_ovr = float(player.overall)
        player.overall = round(min(99.0, old_ovr * (1.0 + random.uniform(0.0, 0.05))), 1)
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
        if sum(1 for p in team.players if getattr(p, "is_star", False)) >= 3:
            continue
        for p in team.players:
            p.is_star = False
        for p in sorted(team.players, key=lambda p: p.overall, reverse=True)[:3]:
            p.is_star = True


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
        if phase_key in shown or not ties:
            continue
        if any((tie.leg1 is not None or tie.leg2 is not None) for tie in ties):
            shown.add(phase_key)
            continue
        show_copa_draw(phase_title, ties, season.all_teams)
        shown_any = True
        shown.add(phase_key)

    season.shown_cup_draws = list(shown)
    if shown_any:
        show_copa(season, player_team)
    return shown_any


def _post_round_updates(
    season: Season,
    player_team,
    career: CareerState,
    transfer_messages,
    round_type: str | None = None,
    round_marker: int | None = None,
):
    if getattr(career, "unemployed", False):
        career.rounds_unemployed = getattr(career, "rounds_unemployed", 0) + 1

    append_career_notifications(
        career, transfer_messages, kind="transfer",
        round_num=round_marker, season_year=season.year,
    )
    if round_type == "liga":
        append_career_notifications(
            career,
            process_coach_market(season.all_teams, career, round_marker=round_marker),
            kind="coach_market", round_num=round_marker, season_year=season.year,
        )

    firing_msg = check_player_firing(season.all_teams, career)
    if firing_msg:
        append_career_notifications(career, [firing_msg], kind="firing",
                                    round_num=round_marker, season_year=season.year)
        show_notifications(career.notifications, "CENTRAL DE NOTÍCIAS")
        career.notifications.clear()
        offers = generate_player_offers(season.all_teams, career)
        if offers:
            for offer in offers:
                if prompt_job_offer(career.player_coach.name, offer, season.all_teams):
                    player_team, messages = accept_player_offer(offer, season.all_teams, career)
                    show_notifications(messages, "MERCADO DE TREINADORES")
                    return player_team, False
                show_notifications(
                    reject_player_offer(offer, season.all_teams, career),
                    "MERCADO DE TREINADORES",
                )
        return player_team, False

    offers = generate_player_offers(season.all_teams, career)
    if offers:
        for offer in offers:
            if prompt_job_offer(career.player_coach.name, offer, season.all_teams):
                player_team, messages = accept_player_offer(offer, season.all_teams, career)
                append_career_notifications(career, messages, kind="job_change",
                                            round_num=round_marker, season_year=season.year)
                break
            show_notifications(
                reject_player_offer(offer, season.all_teams, career),
                "MERCADO DE TREINADORES",
            )

    if career.notifications:
        show_notifications(career.notifications, "CENTRAL DE NOTÍCIAS")
        career.notifications.clear()

    current = current_player_team(career, season.all_teams)
    if current is not None:
        player_team = current
    return player_team, False


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
                season, player_team, career,
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
            if unemployed:
                print(YY + "\n  Sem clube no momento. Avance a rodada para buscar ofertas." + RST)
                pause()
            else:
                show_next_round(season, player_team)

        elif choice == "2":
            show_standings(season, player_team)
            show_top_scorers(season)

        elif choice == "3":
            show_copa(season, player_team)

        elif choice == "4":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                player_team = show_tactics(player_team)

        elif choice == "5":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                player_team.postura = choose_postura(player_team.postura)

        elif choice == "6":
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
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                show_finances(player_team, season)

        elif choice == "8":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                show_torcida(player_team)

        elif choice == "9":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                show_stadium(player_team)

        elif choice == "C":
            show_calendar(season, None if unemployed else player_team)

        elif choice == "R":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                target_player, offered_salary = prompt_contract_renewal(player_team)
                if target_player and offered_salary:
                    accepted, message = negotiate_contract(target_player, offered_salary)
                    messages = [message]
                    if not accepted:
                        messages.extend(run_immediate_contract_auction(target_player, player_team, season.all_teams))
                    show_notifications(messages, "RENOVAÇÃO DE CONTRATO")

        elif choice == "T":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                show_transfer_market(market, player_team)

        elif choice == "E":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                player_team = show_training(player_team)

        elif choice == "A":
            show_top_scorers(season)

        elif choice == "V":
            if unemployed:
                print(YY + "\n  Sem clube no momento." + RST); pause()
            else:
                manage_player_sales(player_team, market)

        elif choice == "H":
            show_history(career)

        elif choice == "S":
            state = {"season": season, "player_team": player_team, "market": market, "career": career}
            ok = save_game(state)
            print((GG if ok else RR) + ("  Jogo salvo!" if ok else "  Erro ao salvar.") + RST)
            pause()

        elif choice == "0":
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

    if player_team is not None and has_player_game:
        pre_match_choice = confirm_play(player_team.formation, player_team.postura)
        if pre_match_choice == "adjust":
            player_team = show_tactics(player_team)
        elif pre_match_choice == "back":
            return {"messages": [], "player_played": False, "cancelled": True}

    blocked_bidder_ids = {player_team.id} if player_team is not None else set()

    auctions = market.generate_auctions(season.all_teams)
    if auctions:
        market.ai_bidding(season.all_teams, blocked_team_ids=blocked_bidder_ids)
        if player_team is not None:
            show_transfer_market(market, player_team)

    if market.auctions:
        market.ai_bidding(season.all_teams, blocked_team_ids=blocked_bidder_ids)
        results = market.resolve_all(round_num=season.current_matchday + 1)
        if results:
            show_auction_results(results)

    info = play_live_matchday(season, player_team)

    if info.get("done"):
        return {"messages": [], "player_played": False, "round_type": None, "round_marker": season.current_matchday}

    played_round = max(0, int(info.get("matchday_num", 1)) - 1)
    training_messages = _apply_training_if_due(played_round, player_team) if player_team is not None else []
    if training_messages:
        show_notifications(training_messages, "CENTRO DE TREINAMENTO")

    other = info.get("other_results", [])
    if other:
        clear()
        print(rule(info["label"]))
        print(C + "\n  Outros Resultados:" + RST)
        for r in other:
            hg = r.home_goals; ag = r.away_goals
            if hg > ag:   sc = GG + f"{hg} × {ag}" + RST
            elif hg < ag: sc = RR + f"{hg} × {ag}" + RST
            else:         sc = YY + f"{hg} × {ag}" + RST
            print(f"  {WW}{r.home_team.name:<22}{RST} {sc} {WW}{r.away_team.name}{RST}")

        all_players = [(t, p) for t in season.all_teams for p in t.players]
        top_scorers = sorted(all_players, key=lambda x: -x[1].gols_temp)[:5]
        print()
        print(C + "  TOP ARTILHEIROS DA RODADA:" + RST)
        for i, (team, p) in enumerate(top_scorers, 1):
            if p.gols_temp > 0:
                print(f"  {DIM}{i}.{RST} {WW}{pad(p.name, 20)}{RST} ({C}{team.name}{RST}) — {GG}{p.gols_temp}{RST} gols")

    if info.get("type") == "liga":
        show_standings(season, player_team)
        show_top_scorers(season)
    else:
        if not _maybe_show_pending_cup_draws(season, player_team):
            show_copa(season, player_team)
        show_top_scorers(season)

    if season.current_matchday % 4 == 0:
        pay_monthly_salaries(season.all_teams)
        print(RR + "\n  💸 Salários mensais pagos!" + RST)
        pause()

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
            record_season_history=record_season_history,
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
