"""Tabela da Copa, sorteio de fases e chaveamento."""
import time
from typing import List, Optional

from models import Team, CupTie
from season import Season
from term import (
    clear, pause, rule, box,
    GG, YY, C, WW, DIM, RST,
    pad, paint_team,
)

from ui.common import _ellipsize_visible


def _fit_bracket_team_name(name: str, limit: int = 20) -> str:
    if len(name) <= limit:
        return name
    return name[: limit - 1].rstrip() + "…"


def _paint_team_box(team: Team, text: str) -> str:
    """Alias para paint_team centralizado em term.py."""
    return paint_team(team, text)


def _format_bracket_fixture(team_a: Team, team_b: Team, score: str = "vs") -> str:
    left  = _paint_team_box(team_a, pad(_fit_bracket_team_name(team_a.name, 20), 20))
    right = _paint_team_box(team_b, pad(_fit_bracket_team_name(team_b.name, 20), 20))
    return f"{left} {score:^7} {right}"


def _pair_bracket_labels(labels: List[str]) -> List[str]:
    paired = []
    for idx in range(0, len(labels), 2):
        paired.append(f"Venc. {labels[idx]} x Venc. {labels[idx + 1]}")
    return paired


def _print_knockout(season: Season, player_team: Optional[Team]) -> None:
    phases = [
        ("1ª Fase",        season.copa_primeira_fase, 1,  16),
        ("Oitavas de Final", season.copa_oitavas,     17,  8),
        ("Quartas de Final", season.copa_quartas,     25,  4),
        ("Semifinal",        season.copa_semi,        29,  2),
    ]
    for phase_name, ties, start_game_num, expected_ties in phases:
        print(C + f"\n  {phase_name}:" + RST)
        if ties:
            for idx, tie in enumerate(ties, start=1):
                game_num = start_game_num + idx - 1
                prefix = f"{DIM}{pad(f'Jogo {game_num}:', 12)}{RST} "
                if tie.leg1 and tie.leg2:
                    a, b = tie.aggregate()
                    winner = tie.winner()
                    winner_name = (
                        _paint_team_box(winner, _fit_bracket_team_name(winner.name, 20))
                        if winner else YY + "Pênaltis" + RST
                    )
                    fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{a}x{b}")
                    pens = f"  [pên. {tie.penalty_score[0]}x{tie.penalty_score[1]}]" if tie.penalty_score else ""
                    print(
                        f"  {prefix}{WW}{fixture}{RST}  "
                        f"[ida {tie.leg1.home_goals}x{tie.leg1.away_goals} / "
                        f"volta {tie.leg2.home_goals}x{tie.leg2.away_goals}]{pens}  → {winner_name}"
                    )
                elif tie.leg1:
                    fixture = _format_bracket_fixture(tie.team_a, tie.team_b,
                                                      f"{tie.leg1.home_goals}x{tie.leg1.away_goals}")
                    print(f"  {prefix}{WW}{fixture}{RST}  [ida]")
                else:
                    label = "final" if tie.single_leg else "ida/volta"
                    print(f"  {prefix}{DIM}{_format_bracket_fixture(tie.team_a, tie.team_b)}  ({label}){RST}")
        else:
            for i in range(1, expected_ties + 1):
                game_num = start_game_num + i - 1
                print(f"  {DIM}Jogo {game_num}: Pendente{RST}")

    if season.copa_final:
        print(C + "\n  Final:" + RST)
        tie = season.copa_final
        if tie.leg1 and tie.leg2:
            winner = season.copa_champion or tie.winner()
            winner_name = (
                _paint_team_box(winner, _fit_bracket_team_name(winner.name, 20))
                if winner else YY + "Pênaltis" + RST
            )
            a, b = tie.aggregate()
            fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{a}x{b}")
            pens = f"  [pên. {tie.penalty_score[0]}x{tie.penalty_score[1]}]" if tie.penalty_score else ""
            print(
                f"  {DIM}Jogo 31/32:{RST} {WW}{fixture}{RST}  "
                f"[ida {tie.leg1.home_goals}x{tie.leg1.away_goals} / "
                f"volta {tie.leg2.home_goals}x{tie.leg2.away_goals}]{pens}  → {winner_name}"
            )
        elif tie.leg1:
            fixture = _format_bracket_fixture(tie.team_a, tie.team_b,
                                               f"{tie.leg1.home_goals}x{tie.leg1.away_goals}")
            print(f"  {DIM}Jogo 31:{RST} {WW}{fixture}{RST}  [ida]")
        else:
            print(f"  {DIM}Jogo 31:{RST} {DIM}{_format_bracket_fixture(tie.team_a, tie.team_b)}  (ida e volta){RST}")
    else:
        print(C + "\n  Final:" + RST)
        print(f"  {DIM}Jogo 31/32: Pendente{RST}")

    if season.copa_champion:
        champ = season.copa_champion
        print()
        print(box([
            "",
            YY + f"  🏆 CAMPEÃO: {champ.name} 🏆  " + RST,
            "",
        ], border_color=YY, title_color=YY, width=50))


def show_copa(season: Season, player_team: Team) -> None:
    clear()
    print(rule("🏆 COPA DO BRASILEIRÃO"))
    print()
    _print_knockout(season, player_team)
    pause()


def show_copa_draw(phase_title: str, ties: List[CupTie], all_teams: List[Team]) -> None:
    """Exibe o sorteio da fase da Copa de forma progressiva."""
    if not ties:
        return

    participants: List[Team] = []
    seen_ids: set = set()
    for tie in ties:
        for team in (tie.team_a, tie.team_b):
            if team.id in seen_ids:
                continue
            seen_ids.add(team.id)
            participants.append(team)

    remaining = list(participants)
    slots: list = [[None, None] for _ in ties]

    def _remove_remaining(team: Team) -> None:
        for idx, item in enumerate(remaining):
            if item.id == team.id:
                remaining.pop(idx)
                return

    def _division_pool_lines() -> List[str]:
        lines: List[str] = []
        grouped: dict = {1: [], 2: [], 3: [], 4: []}
        for team in remaining:
            grouped.setdefault(team.division, []).append(team)
        for division in [1, 2, 3, 4]:
            teams = sorted(grouped.get(division, []), key=lambda club: club.name)
            lines.append(YY + f"  DIVISÃO {division}" + RST)
            if not teams:
                lines.append(DIM + "  —" + RST)
                lines.append("")
                continue
            row = "  "
            count = 0
            for team in teams:
                token = _paint_team_box(team, pad(_fit_bracket_team_name(team.name, 16), 16))
                if count > 0 and count % 4 == 0:
                    lines.append(_ellipsize_visible(row, 110))
                    row = "  "
                row += token + " "
                count += 1
            lines.append(_ellipsize_visible(row.rstrip(), 110))
            lines.append("")
        return lines

    def _top_draw_lines() -> List[str]:
        lines = [f"  Fase: {C}{phase_title}{RST}", ""]
        for idx, pair in enumerate(slots, start=1):
            left = pair[0]
            right = pair[1]
            if left and right:
                fixture = _format_bracket_fixture(left, right, "vs")
            elif left and not right:
                left_box = _paint_team_box(left, pad(_fit_bracket_team_name(left.name, 20), 20))
                right_box = DIM + pad("A sortear...", 20) + RST
                fixture = f"{left_box} {'vs':^7} {right_box}"
            else:
                fixture = DIM + "A sortear..." + RST
            lines.append(f"  Jogo {idx:>2}: {fixture}")
        pending_teams = len(remaining)
        pending = pending_teams // 2
        if pending > 0:
            lines.append("")
            lines.append(DIM + f"  Sorteando próximos confrontos... faltam {pending} jogo(s)" + RST)
        return lines

    for idx, tie in enumerate(ties):
        slots[idx][0] = tie.team_a
        _remove_remaining(tie.team_a)
        clear()
        print(rule("🎲 SORTEIO DA COPA"))
        print()
        top_box  = box(_top_draw_lines(),     title=f"SORTEIO — {phase_title}",          border_color=YY, title_color=YY, width=112)
        pool_box = box(_division_pool_lines(), title="TIMES RESTANTES (POR DIVISÃO)", border_color=C,  title_color=C,  width=112)
        print(top_box)
        print()
        print(pool_box)
        time.sleep(0.35)

        slots[idx][1] = tie.team_b
        _remove_remaining(tie.team_b)
        clear()
        print(rule("🎲 SORTEIO DA COPA"))
        print()
        top_box  = box(_top_draw_lines(),     title=f"SORTEIO — {phase_title}",          border_color=YY, title_color=YY, width=112)
        pool_box = box(_division_pool_lines(), title="TIMES RESTANTES (POR DIVISÃO)", border_color=C,  title_color=C,  width=112)
        print(top_box)
        print()
        print(pool_box)
        time.sleep(0.45)

    clear()
    print(rule("🎲 SORTEIO DA COPA"))
    print()
    print(GG + f"  ✓ Sorteio da fase {phase_title} concluído." + RST)
    time.sleep(0.55)
