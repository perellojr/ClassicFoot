"""Registro de histórico de temporada e estatísticas mundiais."""
from season import Season, sort_standings
from save import ensure_world_history, normalize_world_history


def record_season_history(season: Season, player_team, career) -> None:
    """Persiste resultados da temporada em career.season_history e world_history."""
    normalize_world_history(career)
    world_history = ensure_world_history(career)
    season_year = int(season.year)

    has_year_entry = any(
        isinstance(entry, dict) and int(entry.get("year", 0) or 0) == season_year
        for entry in career.season_history
    )
    if player_team is not None and not has_year_entry:
        final_data = season.final_positions.get(player_team.id, {})
        division = int(final_data.get("division", player_team.division))
        position = int(final_data.get("position", 0) or 0)
        if position <= 0:
            division_teams = [team for team in season.all_teams if team.division == division]
            ranked = sort_standings(division_teams)
            position = next((idx + 1 for idx, team in enumerate(ranked) if team.id == player_team.id), 0)

        top_scorer = season.top_scorers[0] if season.top_scorers else None
        best_points_team = max(season.all_teams, key=lambda t: int(t.div_points), default=None)
        best_attack_team = max(season.all_teams, key=lambda t: int(t.div_gf), default=None)

        career.season_history.append({
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
        })

    champion_years = set(world_history.get("recorded_champion_years", []))
    aggregate_years = set(world_history.get("recorded_aggregate_years", []))

    if season_year not in champion_years:
        for div in sorted(season.division_champions.keys()):
            world_history["division_champions"].append({
                "year": season.year,
                "division": div,
                "team": season.division_champions.get(div, "-"),
                "coach": season.division_champion_coaches.get(div, "-"),
            })

        div1_champion = season.division_champions.get(1)
        if div1_champion:
            titles = world_history["div1_titles_by_club"]
            titles[div1_champion] = int(titles.get(div1_champion, 0)) + 1

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
            world_history["league_points_record"] = {"points": int(total_points), "team": club_name, "year": season.year}

        for team in season.all_teams:
            cumulative = world_history["team_goals_cumulative"]
            cumulative[team.name] = int(cumulative.get(team.name, 0)) + int(team.div_gf)
        if world_history["team_goals_cumulative"]:
            team_name, total_goals = max(world_history["team_goals_cumulative"].items(), key=lambda item: item[1])
            world_history["team_goals_record"] = {"goals": int(total_goals), "team": team_name, "year": season.year}

        for team in season.all_teams:
            for player in team.players:
                key = f"{player.name}::{team.name}"
                cumulative = world_history["player_goals_cumulative"]
                cumulative[key] = int(cumulative.get(key, 0)) + int(player.gols_temp)
        if world_history["player_goals_cumulative"]:
            player_key, total_goals = max(world_history["player_goals_cumulative"].items(), key=lambda item: item[1])
            player_name, team_name = player_key.split("::", 1)
            world_history["player_goals_record"] = {"goals": int(total_goals), "player": player_name, "team": team_name, "year": season.year}

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
                "diff": diff, "score": f"{result.home_goals}x{result.away_goals}",
                "winner": winner, "loser": loser, "year": season.year,
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
