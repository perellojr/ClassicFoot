"""Classificação, calendário e artilheiros."""
from typing import List

from models import Team
from season import Season, sort_standings
from term import (
    clear, pause, rule, box, GG, YY, C, RR, WW, DIM, RST,
    term_width, pad,
    h,
)

from ui.common import _box_width, _print_side_by_side


def show_standings(season: Season, player_team: Team | None, division: int = 0) -> None:
    clear()
    print(rule("CLASSIFICAÇÃO"))
    division_tables = {}
    for current_division in [1, 2, 3, 4]:
        div_teams = [t for t in season.all_teams if t.division == current_division]
        ranked = sort_standings(div_teams)
        lines = []
        header = (
            DIM + pad("", 2) + RST +
            YY + pad("TIME", 18) + RST +
            DIM + pad("J", 3, "r") + RST +
            DIM + pad("V", 3, "r") + pad("E", 3, "r") + pad("D", 3, "r") + RST +
            C + pad("GP:GC", 7, "r") + RST +
            YY + pad("PTS", 4, "r") + RST
        )
        lines.append(header)
        lines.append(C + "─" * 45 + RST)

        for pos, t in enumerate(ranked, 1):
            is_promoted = (current_division == 1 and pos == 1) or (current_division > 1 and pos <= 2)
            is_relegated = pos >= len(ranked) - 1

            if is_promoted:
                marker = GG + "▲" + RST
                name_color = GG
            elif is_relegated:
                marker = RR + "▼" + RST
                name_color = RR
            else:
                marker = DIM + str(pos) + RST
                name_color = WW

            if player_team is not None and t.id == player_team.id:
                if not (is_promoted or is_relegated):
                    name_color = YY

            team_name = name_color + pad(t.name[:18], 18) + RST
            line = (
                marker + " " +
                team_name +
                DIM + pad(str(t.div_played), 3, "r") + RST +
                GG + pad(str(t.div_wins), 3, "r") + RST +
                YY + pad(str(t.div_draws), 3, "r") + RST +
                RR + pad(str(t.div_losses), 3, "r") + RST +
                C + pad(f"{t.div_gf}:{t.div_ga}", 7, "r") + RST +
                (GG if is_promoted else RR if is_relegated else YY) +
                pad(str(t.div_points), 4, "r") + RST
            )
            lines.append(line)

        division_tables[current_division] = box(
            lines, title=f"{current_division}ª DIVISÃO",
            border_color=C, title_color=GG, width=50,
        )

    gap = 2
    layout_pairs = [(1, 2), (3, 4)]
    for left_div, right_div in layout_pairs:
        left = division_tables.get(left_div, "")
        right = division_tables.get(right_div, "")
        if right and _box_width(left) + gap + _box_width(right) <= term_width():
            _print_side_by_side(left, right, gap=gap)
        else:
            print(left)
            if right:
                print()
                print(right)
        print()

    print(GG + "  ▲ Promoção" + RST + "   " + RR + "▼ Rebaixamento" + RST)
    pause()


def show_calendar(season: Season, player_team: Team | None) -> None:
    clear()
    print(rule("CALENDÁRIO DA TEMPORADA"))
    print()
    if player_team is None:
        print(DIM + "  Sem clube no momento. Não há calendário de time para exibir." + RST)
        print()
        pause()
        return

    blocks = []
    for idx, matchday in enumerate(season.calendar, start=1):
        entries = []
        for fixture in matchday.get("fixtures", []):
            if fixture.home_team.id != player_team.id and fixture.away_team.id != player_team.id:
                continue
            prefix = GG + "► " + RST
            if fixture.result:
                score = f"{fixture.result.home_goals}x{fixture.result.away_goals}"
                entries.append(f"{prefix}{fixture.home_team.name} {score} {fixture.away_team.name}")
            else:
                entries.append(f"{prefix}{fixture.home_team.name} x {fixture.away_team.name}")
        cup_leg = matchday.get("cup_leg", 1)
        for tie in (matchday.get("ties") or []):
            if tie.team_a.id != player_team.id and tie.team_b.id != player_team.id:
                continue
            home = tie.team_a if cup_leg == 1 or tie.single_leg else tie.team_b
            away = tie.team_b if cup_leg == 1 or tie.single_leg else tie.team_a
            prefix = GG + "► " + RST
            result = tie.leg1 if cup_leg == 1 or tie.single_leg else tie.leg2
            if result:
                entries.append(f"{prefix}{home.name} {result.home_goals}x{result.away_goals} {away.name}")
            else:
                entries.append(f"{prefix}{home.name} x {away.name}")
        if not entries:
            continue
        block = [C + f"{idx:>2}. {matchday['label']}" + RST]
        block.extend(entries[:8])
        if len(entries) > 8:
            block.append(DIM + f"  ... e mais {len(entries) - 8} jogos" + RST)
        blocks.append("\n".join(block))

    if not blocks:
        print(DIM + "  Nenhum jogo encontrado para este time no calendário." + RST)
        print()
        pause()
        return

    left_col = blocks[::2]
    right_col = blocks[1::2]
    left_lines: List[str] = []
    right_lines: List[str] = []
    for item in left_col:
        left_lines.extend(item.split("\n"))
        left_lines.append("")
    for item in right_col:
        right_lines.extend(item.split("\n"))
        right_lines.append("")

    left_width = min(58, max(44, (term_width() - 6) // 2))
    max_lines = max(len(left_lines), len(right_lines))
    for i in range(max_lines):
        left = left_lines[i] if i < len(left_lines) else ""
        right = right_lines[i] if i < len(right_lines) else ""
        print(pad(left, left_width) + "  " + right)
    print()
    pause()


def show_top_scorers(season: Season) -> None:
    clear()
    print(rule("ARTILHEIROS DA TEMPORADA"))
    print()
    all_players = [(t, p) for t in season.all_teams for p in t.players]
    top_global = sorted(all_players, key=lambda x: (-x[1].gols_temp, x[1].name))[:33]
    key_to_division = {(player.name, team.name): team.division for team, player in all_players}

    left_lines: List[str] = [
        DIM + "  #  " + WW + pad("Nome", 21) + C + pad("Time", 20) + YY + " G  J" + RST,
        C + "  " + h * 51 + RST,
    ]
    for i, (team, player) in enumerate(top_global, 1):
        left_lines.append(
            DIM + f"  {i:>2} " + RST +
            WW + pad(player.name, 21) + RST +
            C + pad(team.name, 20) + RST +
            GG + f"{int(player.gols_temp):>2}" + RST +
            DIM + f"{int(player.partidas_temp):>3}" + RST
        )
    left_box = box(left_lines, title="GLOBAL (TEMPORADA)", border_color=C, title_color=C, width=58)

    right_lines: List[str] = [
        DIM + "  #  " + WW + pad("Nome", 21) + C + pad("Time", 20) + YY + " G  J" + RST,
        C + "  " + h * 51 + RST,
    ]

    player_lookup = {(player.name, team.name): player for team, player in all_players}

    def _competition_stats(prefix: str):
        goals: dict = {}
        games: dict = {}
        for result in season.results_history:
            competition = str(getattr(result, "competition", "") or "").lower()
            if not competition.startswith(prefix):
                continue

            home_team_name = result.home_team.name
            away_team_name = result.away_team.name
            home_used = list(getattr(result, "home_used_names", []) or [])
            away_used = list(getattr(result, "away_used_names", []) or [])

            if not home_used:
                home_used = list(getattr(result, "home_scorers", []) or [])
            if not away_used:
                away_used = list(getattr(result, "away_scorers", []) or [])

            for player_name in home_used:
                key = (player_name, home_team_name)
                games[key] = int(games.get(key, 0)) + 1
            for player_name in away_used:
                key = (player_name, away_team_name)
                games[key] = int(games.get(key, 0)) + 1

            for scorer in getattr(result, "home_scorers", []) or []:
                key = (scorer, home_team_name)
                goals[key] = int(goals.get(key, 0)) + 1
            for scorer in getattr(result, "away_scorers", []) or []:
                key = (scorer, away_team_name)
                goals[key] = int(goals.get(key, 0)) + 1
        return goals, games

    league_goals, league_games = _competition_stats("liga")
    cup_goals, cup_games = _competition_stats("copa")

    def _append_right_section(title: str, rows: list) -> None:
        right_lines.append(YY + f"  {title}" + RST)
        if not rows:
            right_lines.append(DIM + "  -- sem dados --" + RST)
            right_lines.append("")
            return
        for idx, (player_name, team_name, goals, games) in enumerate(rows, start=1):
            right_lines.append(
                DIM + f"  {idx:>2} " + RST +
                WW + pad(player_name, 21) + RST +
                C + pad(team_name, 20) + RST +
                GG + f"{int(goals):>2}" + RST +
                DIM + f"{int(games):>3}" + RST
            )
        right_lines.append("")

    for div in [1, 2, 3, 4]:
        league_candidates = []
        for (player_name, team_name), goals in league_goals.items():
            if int(key_to_division.get((player_name, team_name), 0)) != div:
                continue
            league_candidates.append((player_name, team_name, int(goals), int(league_games.get((player_name, team_name), 0))))
        league_candidates.sort(key=lambda item: (-item[2], item[0]))
        _append_right_section(f"DIVISÃO {div}", league_candidates[:5])

    cup_top = sorted(cup_goals.items(), key=lambda item: (-item[1], item[0][0]))[:5]
    cup_rows = []
    for (player_name, team_name), goals in cup_top:
        games = int(cup_games.get((player_name, team_name), 0))
        if games <= 0:
            found = player_lookup.get((player_name, team_name))
            games = int(found.partidas_temp) if found is not None else 0
        cup_rows.append((player_name, team_name, int(goals), int(games)))
    _append_right_section("COPA (TOP 5)", cup_rows)

    right_box = box(right_lines, title="LIGAS E COPA", border_color=C, title_color=C, width=58)

    if _box_width(left_box) + 2 + _box_width(right_box) <= term_width():
        _print_side_by_side(left_box, right_box, gap=2)
    else:
        print(left_box)
        print()
        print(right_box)
    pause()
