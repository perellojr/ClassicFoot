"""Renderização de partidas ao vivo, resultado e substituições."""
import time
from typing import List, Optional

from models import Team, MatchResult
from season import Season
from term import (
    clear, pause, rule, box, Table,
    GG, YY, C, BB, RR, WW, DIM, RST,
    term_width, pad, _visible_len,
    TL, TR, BL, BR, H, V,
    paint_team,
)

from ui.common import _fit_team_name, _fit_text, _division_label


# ── Helpers de placar ao vivo ─────────────────────────────────────

def _score_at_minute(live_game: dict, minute: int):
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


def _first_leg_text(game: dict) -> Optional[str]:
    first_leg = game.get("first_leg_result")
    if first_leg is None:
        return None
    return f"{first_leg.away_goals}x{first_leg.home_goals}"


def _aggregate_text(game: dict, minute: int) -> Optional[str]:
    first_leg = game.get("first_leg_result")
    if first_leg is None:
        return None
    home_goals, away_goals, _ = _score_at_minute(game, minute)
    agg_home = first_leg.away_goals + home_goals
    agg_away = first_leg.home_goals + away_goals
    return f"{agg_home}x{agg_away}"


def _latest_event_text(events: list) -> str:
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


def _format_live_fixture(home_team: Team, away_team: Team, home_goals: int, away_goals: int) -> str:
    home_name = pad(_fit_team_name(home_team.name, 18), 18)
    away_name = pad(_fit_team_name(away_team.name, 18), 18)
    score = f"{home_goals}x{away_goals}"
    return (
        paint_team(home_team, home_name)
        + " "
        + YY + f"{score:^5}" + RST
        + " "
        + paint_team(away_team, away_name)
    )


def _current_aggregate(focus_game: dict, minute: int):
    first_leg = focus_game.get("first_leg_result")
    if first_leg is None:
        return None
    home_goals, away_goals, _ = _score_at_minute(focus_game, minute)
    team_a_total = first_leg.home_goals + away_goals
    team_b_total = first_leg.away_goals + home_goals
    return team_a_total, team_b_total


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


# ── Tela de resultado final ────────────────────────────────────────

def show_match_result(result: MatchResult, player_team: Team) -> None:
    clear()
    comp = result.competition.upper()
    print(rule(f"  {comp}  "))
    print()

    hg = result.home_goals
    ag = result.away_goals
    player_won  = result.winner() and result.winner().id == player_team.id  # type: ignore[union-attr]
    player_drew = result.winner() is None

    if player_won:    sc = GG; msg = "VITÓRIA! 🎉"
    elif player_drew: sc = YY; msg = "EMPATE"
    else:             sc = RR; msg = "DERROTA"

    w = term_width()
    home_name = WW + result.home_team.name + RST
    away_name = WW + result.away_team.name + RST
    score      = sc + f"  {hg}  ×  {ag}  " + RST

    print(GG + TL + H * (w - 2) + TR + RST)
    print(GG + V + RST + pad("", w - 2) + GG + V + RST)
    print(GG + V + RST + pad(home_name + "  " + score + "  " + away_name, w - 2, "c") + GG + V + RST)
    print(GG + V + RST + pad(sc + msg + RST, w - 2, "c") + GG + V + RST)
    print(GG + V + RST + pad("", w - 2) + GG + V + RST)
    print(GG + BL + H * (w - 2) + BR + RST)
    print()

    if result.home_scorers or result.away_scorers:
        print(C + "  ⚽ GOLS:" + RST)
        col_w = 35
        for i in range(max(len(result.home_scorers), len(result.away_scorers))):
            hl = GG + result.home_scorers[i] + RST if i < len(result.home_scorers) else ""
            al = RR + result.away_scorers[i] + RST if i < len(result.away_scorers) else ""
            l_pad = col_w - _visible_len(hl)
            print(f"  {hl}" + " " * l_pad + f"  {al}")

    pause()


# ── Placar ao vivo (todos os jogos) ───────────────────────────────

def _render_live_scores(
    label: str,
    minute: int,
    live_games: list,
    focus_game: Optional[dict] = None,
    phase: str = "1º TEMPO",
) -> None:
    clear()
    print(rule(f"{label}  •  {phase}  •  {minute:02d}'"))
    print(pad(_time_progress_bar(minute, phase), 100, "c"))
    print()
    grouped: dict = {}
    for game in live_games:
        key = game["home"].division if game["competition"] == "Liga" else "COPA"
        grouped.setdefault(key, []).append(game)

    ordered_keys = sorted([k for k in grouped if isinstance(k, int)]) + [k for k in grouped if not isinstance(k, int)]
    for key in ordered_keys:
        title = _division_label(key) if isinstance(key, int) else str(key)
        show_first_leg_column = any(_first_leg_text(game) for game in grouped[key])
        tbl = Table(title=title, border_color=C, header_color=YY, title_color=C)
        tbl.add_column("Jogo",         width=46, align="l", color=WW)
        tbl.add_column("Lance Capital", width=56, align="l", color=WW)
        if show_first_leg_column:
            tbl.add_column("Ida",      width=8,  align="c", color=DIM)
            tbl.add_column("Agregado", width=10, align="c", color=YY)
        tbl.add_column("Público",      width=9,  align="r", color=GG)

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
                print(DIM + f"  Ida: {ida.home_team.name} {ida.home_goals}x{ida.away_goals} {ida.away_team.name}"
                      f"  │  Agregado: {focus_game['ref'].team_a.name} {agg[0]}x{agg[1]} {focus_game['ref'].team_b.name}" + RST)


# ── Pênaltis ──────────────────────────────────────────────────────

def _render_penalty_shootout(focus_game: dict) -> None:
    penalties = focus_game.get("penalties")
    if not penalties:
        return
    clear()
    print(rule("DISPUTA DE PÊNALTIS"))
    print()
    print(pad(_format_live_fixture(focus_game["home"], focus_game["away"],
                                   focus_game["final_home_goals"], focus_game["final_away_goals"]), 100, "c"))
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


# ── Substituições no intervalo ────────────────────────────────────

def _matchday_has_player_game(season: Season, player_team: Optional[Team]) -> bool:
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


def _render_substitution_screen(
    player_team: Team,
    live_game: dict,
    lineup: list,
    bench: list,
    subs_done: int,
) -> None:
    def _print_side_by_side_blocks(left: str, right: str, gap: int = 2) -> None:
        left_lines = left.split("\n")
        right_lines = right.split("\n")
        max_lines = max(len(left_lines), len(right_lines))
        left_w = max((_visible_len(line) for line in left_lines), default=0)
        for i in range(max_lines):
            l = left_lines[i] if i < len(left_lines) else ""
            r = right_lines[i] if i < len(right_lines) else ""
            print(l + " " * (left_w - _visible_len(l) + gap) + r)

    def _halftime_goal_lines(match: dict) -> List[str]:
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
    left_box  = box(left_lines,  title="SUBSTITUIÇÕES", border_color=GG, title_color=YY, width=46)
    right_box = box(right_lines, title="JOGO",          border_color=C,  title_color=YY, width=78)

    print()
    if _visible_len(left_box.split("\n")[0]) + 2 + _visible_len(right_box.split("\n")[0]) <= term_width():
        _print_side_by_side_blocks(left_box, right_box, gap=2)
    else:
        print(left_box)
        print()
        print(right_box)
    print()

    starters = Table(title="TITULARES", border_color=GG, header_color=YY, title_color=GG)
    starters.add_column("N",    width=3,  align="r", color=DIM)
    starters.add_column("Nome", width=22, align="l", color=WW)
    starters.add_column("Pos",  width=5,  align="c", color=C)
    starters.add_column("OVR",  width=5,  align="c", color=YY)
    for idx, player in enumerate(lineup, start=1):
        starters.add_row(str(idx), player.name, player.pos_label(), str(int(round(player.overall))))
    starters.print()

    print()
    reserves = Table(title="RESERVAS (MAX 12)", border_color=BB, header_color=YY, title_color=BB)
    reserves.add_column("N",    width=3,  align="r", color=DIM)
    reserves.add_column("Nome", width=22, align="l", color=WW)
    reserves.add_column("Pos",  width=5,  align="c", color=C)
    reserves.add_column("OVR",  width=5,  align="c", color=YY)
    for idx, player in enumerate(bench, start=1):
        reserves.add_row(str(idx), player.name, player.pos_label(), str(int(round(player.overall))))
    reserves.print()
