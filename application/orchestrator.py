"""Orquestrador da carreira (camada de aplicação)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from models import CareerState
from transfers import TransferMarket


@dataclass
class CareerOrchestrator:
    maybe_show_pending_cup_draws: Callable[[Any, Any], bool]
    show_copa: Callable[[Any, Any], None]
    run_game: Callable[[Any, Any, TransferMarket, CareerState], Any]
    record_season_history: Callable[[Any, Any, CareerState], None]
    check_last_division_relegation_firing: Callable[[Any, CareerState], str | None]
    show_notifications: Callable[[list[str], str], None]
    generate_player_offers: Callable[[list, CareerState], list]
    prompt_job_offer: Callable[[str, Any, list], bool]
    accept_player_offer: Callable[[Any, list, CareerState], tuple[Any, list[str]]]
    reject_player_offer: Callable[[Any, list, CareerState], list[str]]
    create_season: Callable[[int, list, int], Any]
    current_player_team: Callable[[CareerState, list], Any]

    def run_career_loop(self, season, player_team, market: TransferMarket, career: CareerState):
        """
        Loop unificado de progressão de carreira.
        Mantém regra atual, mas isolada da UI/menu principal.
        """
        while True:
            current_pt = self.current_player_team(career, season.all_teams)
            if current_pt is not None:
                player_team = current_pt

            display_pt = None if career.unemployed else player_team
            if not self.maybe_show_pending_cup_draws(season, display_pt):
                self.show_copa(season, display_pt)

            player_team = self.run_game(season, player_team, market, career)

            if getattr(career, "back_to_main_menu", False):
                career.back_to_main_menu = False
                return

            self.record_season_history(season, player_team, career)

            end_firing = self.check_last_division_relegation_firing(season, career)
            if end_firing:
                self.show_notifications([end_firing], title="CENTRAL DE NOTÍCIAS")
                offers = self.generate_player_offers(season.all_teams, career)
                if offers:
                    for offer in offers:
                        if self.prompt_job_offer(career.player_coach.name, offer, season.all_teams):
                            player_team, messages = self.accept_player_offer(offer, season.all_teams, career)
                            self.show_notifications(messages, title="MERCADO DE TREINADORES")
                            break
                        self.show_notifications(
                            self.reject_player_offer(offer, season.all_teams, career),
                            title="MERCADO DE TREINADORES",
                        )

            teams = season.all_teams
            next_year = season.year + 1
            pt_id = player_team.id if (player_team is not None and not career.unemployed) else -1
            season = self.create_season(next_year, teams, pt_id)
            if player_team is not None:
                player_team = next((t for t in teams if t.id == player_team.id), player_team)

