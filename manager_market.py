"""
ClassicFoot - Mercado de treinadores e notificações de carreira.
"""
from __future__ import annotations

import random
from typing import List, Tuple

from models import CareerState, Coach, Team
from season import sort_standings


def create_free_coaches() -> List[Coach]:
    names = [
        "Tite", "Dorival Júnior", "Cuca", "Abel Braga", "Vanderlei Luxemburgo",
        "Felipão", "Jair Ventura", "Guto Ferreira", "Enderson Moreira",
        "Claudinei Oliveira", "Renato Paiva", "Fernando Diniz",
    ]
    pool = []
    for name in names:
        pool.append(
            Coach(
                name=name,
                nationality="Brasileiro",
                tactical=random.randint(68, 86),
                motivation=random.randint(68, 84),
                experience=random.randint(70, 92),
                reputation=random.randint(68, 90),
            )
        )
    return pool


def create_caretaker_coach(team: Team) -> Coach:
    return Coach(
        name=f"Interino do {team.short_name}",
        tactical=max(58, team.prestige - 8),
        motivation=66,
        experience=55,
        reputation=max(50, team.prestige - 12),
    )


def current_player_team(career: CareerState, all_teams: List[Team]) -> Team | None:
    if career.current_team_id is None:
        return None
    return next((team for team in all_teams if team.id == career.current_team_id), None)


def _team_position(team: Team, all_teams: List[Team]) -> int:
    ranked = sort_standings([club for club in all_teams if club.division == team.division])
    return next((idx + 1 for idx, club in enumerate(ranked) if club.id == team.id), len(ranked))


def _team_pressure(team: Team, all_teams: List[Team]) -> int:
    position = _team_position(team, all_teams)
    division_teams = [club for club in all_teams if club.division == team.division]
    pressure = 0
    if team.div_played >= 4:
        if position >= len(division_teams) - 1:
            pressure += 3
        elif position >= len(division_teams) - 3:
            pressure += 2
        if team.div_points / max(1, team.div_played) < 1.0:
            pressure += 2
        if len(team.last_results) >= 4 and "W" not in team.last_results[-4:]:
            pressure += 2
        if team.last_results[-3:].count("L") >= 2:
            pressure += 1
        if team.prestige >= 75 and position > len(division_teams) // 2:
            pressure += 1
    return pressure


def _coach_value(coach: Coach) -> float:
    return coach.tactical * 0.4 + coach.motivation * 0.2 + coach.experience * 0.25 + coach.reputation * 0.15


def _poachable_coaches(hiring_team: Team, all_teams: List[Team], excluded_ids: set[int]) -> List[Tuple[Team, Coach]]:
    candidates = []
    for team in all_teams:
        if team.id == hiring_team.id or team.id in excluded_ids:
            continue
        if hiring_team.division < team.division or hiring_team.prestige >= team.prestige + 8:
            candidates.append((team, team.coach))
    candidates.sort(key=lambda item: _coach_value(item[1]), reverse=True)
    return candidates


def _hire_replacement(team: Team, all_teams: List[Team], free_coaches: List[Coach], notifications: List[str], excluded_ids: set[int] | None = None):
    excluded_ids = excluded_ids or set()
    if free_coaches:
        best = max(free_coaches, key=_coach_value)
        free_coaches.remove(best)
        team.coach = best
        notifications.append(f"{team.name} contratou {best.name} (mercado de técnicos).")
        return

    poachable = _poachable_coaches(team, all_teams, excluded_ids)
    if poachable:
        source_team, hired = poachable[0]
        team.coach = hired
        source_team.coach = create_caretaker_coach(source_team)
        notifications.append(f"{team.name} tirou {hired.name} do {source_team.name}.")
        notifications.append(f"{source_team.name} ficou com {source_team.coach.name} como interino.")
        return

    team.coach = create_caretaker_coach(team)
    notifications.append(f"{team.name} ficou com {team.coach.name} como treinador interino.")


def process_coach_market(all_teams: List[Team], career: CareerState) -> List[str]:
    notifications: List[str] = []
    fired_teams: List[Team] = []

    for team in all_teams:
        if career.current_team_id == team.id:
            continue
        pressure = _team_pressure(team, all_teams)
        if pressure >= 5 and random.random() < min(0.9, 0.25 + pressure * 0.1):
            old_coach = team.coach
            career.free_coaches.append(old_coach)
            fired_teams.append(team)
            notifications.append(f"{team.name} demitiu {old_coach.name} após maus resultados.")

    for team in fired_teams:
        _hire_replacement(team, all_teams, career.free_coaches, notifications, excluded_ids={club.id for club in fired_teams})

    return notifications


def check_player_firing(all_teams: List[Team], career: CareerState) -> str | None:
    team = current_player_team(career, all_teams)
    if team is None:
        return None

    position = _team_position(team, all_teams)
    division_teams = [club for club in all_teams if club.division == team.division]
    pressure = _team_pressure(team, all_teams)

    if team.division == 4 and len(team.last_results) >= 5 and position >= len(division_teams) - 1 and pressure >= 5:
        career.unemployed = True
        career.fired = True
        career.last_fired_team_id = team.id
        career.current_team_id = None
        return f"{team.name} demitiu {career.player_coach.name}. Lanterna da última divisão e sem reação."

    if pressure >= 6 and random.random() < min(0.8, 0.2 + pressure * 0.08):
        career.unemployed = True
        career.fired = True
        career.last_fired_team_id = team.id
        career.current_team_id = None
        return f"{team.name} demitiu {career.player_coach.name} após sequência ruim."

    return None


def check_last_division_relegation_firing(season, career: CareerState) -> str | None:
    team = current_player_team(career, season.all_teams)
    if team is None or team.division != 4:
        return None
    ranked = sort_standings([club for club in season.all_teams if club.division == 4])
    pos = next((idx + 1 for idx, club in enumerate(ranked) if club.id == team.id), len(ranked))
    if pos >= len(ranked) - 1:
        career.unemployed = True
        career.fired = True
        career.last_fired_team_id = team.id
        career.current_team_id = None
        return f"{career.player_coach.name} foi demitido do {team.name} por terminar no Z-2 da última divisão."
    return None


def generate_player_offers(all_teams: List[Team], career: CareerState) -> List[Team]:
    offers: List[Team] = []
    player_team = current_player_team(career, all_teams)

    if career.unemployed:
        candidates = sorted(all_teams, key=lambda team: (team.division, -team.prestige))
        for team in candidates:
            if career.last_fired_team_id == team.id:
                continue
            if team.coach.name.startswith("Interino") or _team_pressure(team, all_teams) >= 5:
                offers.append(team)
            if len(offers) >= 3:
                break
        return offers

    if player_team is None or player_team.div_played < 4:
        return offers

    position = _team_position(player_team, all_teams)
    points_per_game = player_team.div_points / max(1, player_team.div_played)
    recent_results = player_team.last_results[-5:]
    recent_wins = recent_results.count("W")
    recent_losses = recent_results.count("L")
    is_flying_high = position <= 2 and points_per_game >= 2.0 and recent_wins >= 3 and recent_losses == 0
    is_going_well = position <= 3 and points_per_game >= 1.7 and recent_wins >= 2 and recent_losses <= 1

    if not is_going_well:
        return offers

    candidates = []
    for team in all_teams:
        if team.id == player_team.id:
            continue
        if _team_pressure(team, all_teams) < 4:
            continue

        if team.division < player_team.division:
            if is_flying_high:
                candidates.append(team)
            continue

        if team.division == player_team.division and team.prestige >= player_team.prestige + 6:
            candidates.append(team)
    candidates.sort(key=lambda team: (team.division, -team.prestige))
    return candidates[:2]


def accept_player_offer(target_team: Team, all_teams: List[Team], career: CareerState) -> Tuple[Team, List[str]]:
    notifications: List[str] = []
    previous_team = current_player_team(career, all_teams)
    old_target_coach = target_team.coach
    career.free_coaches.append(old_target_coach)
    target_team.coach = career.player_coach
    career.current_team_id = target_team.id
    career.unemployed = False
    career.fired = False
    career.last_fired_team_id = None

    notifications.append(f"{career.player_coach.name} aceitou proposta do {target_team.name}.")
    notifications.append(f"{old_target_coach.name} deixou o comando do {target_team.name}.")

    if previous_team and previous_team.id != target_team.id:
        _hire_replacement(previous_team, all_teams, career.free_coaches, notifications, excluded_ids={target_team.id})

    return target_team, notifications
