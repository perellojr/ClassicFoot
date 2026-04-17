"""Gera um relatorio completo de simulacao multitemporada."""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import main
from data import create_teams
from models import Position
from season import create_season


POSITION_ORDER = {
    Position.GK: 0,
    Position.DEF: 1,
    Position.MID: 2,
    Position.ATK: 3,
}


def _fmt_money(value: int) -> str:
    return f"R$ {int(value):,} mil"


def _fmt_fans(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.0f}K"
    return str(int(value))


def _safe_int(value) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _team_roster_lines(team) -> list[str]:
    roster = sorted(
        list(team.players),
        key=lambda p: (
            POSITION_ORDER.get(p.position, 99),
            -float(p.overall),
            p.name,
        ),
    )
    lines = []
    for player in roster:
        star = "*" if getattr(player, "is_star", False) else "-"
        lines.append(
            f"      - {player.pos_label():<3} {player.name:<24} "
            f"OVR {int(round(float(player.overall))):>2}  "
            f"Sal {int(player.salario):>5}  "
            f"G {int(player.gols_temp):>2}  "
            f"J {int(player.partidas_temp):>2}  "
            f"Craque {star}"
        )
    return lines


def _season_team_block(team, season) -> list[str]:
    pos_info = season.final_positions.get(team.id, {})
    prev_div = _safe_int(pos_info.get("division", team.division))
    prev_pos = _safe_int(pos_info.get("position", 0))
    move = "="
    if team.division < prev_div:
        move = "PROMOVIDO"
    elif team.division > prev_div:
        move = "REBAIXADO"

    squad_avg = 0.0
    if team.players:
        squad_avg = sum(float(player.overall) for player in team.players) / len(team.players)

    header = (
        f"  - {team.name} | Div final {team.division} | Pos {prev_pos} na Div {prev_div} | "
        f"Movimento {move} | Caixa {_fmt_money(team.caixa)} | Folha {_fmt_money(team.salario_mensal)} | "
        f"Torcida {_fmt_fans(team.torcida)} | Prestigio {team.prestige} | "
        f"Emprestimo {_fmt_money(team.loan_balance)} | Media elenco {squad_avg:.1f}"
    )
    return [header, "    Elenco:"] + _team_roster_lines(team)


def _collect_report(start_year: int, seasons_to_run: int, seed: int) -> tuple[str, list[dict]]:
    random.seed(seed)
    teams = create_teams()
    seasons_summary: list[dict] = []
    lines: list[str] = []
    lines.append("# Relatorio de Simulacao ClassicFoot")
    lines.append("")
    lines.append(f"- Temporadas simuladas: {seasons_to_run}")
    lines.append(f"- Ano inicial: {start_year}")
    lines.append(f"- Seed: {seed}")
    lines.append("")

    with patch("main._play_live_half", new=lambda *args, **kwargs: None):
        for offset in range(seasons_to_run):
            year = start_year + offset
            initial_divisions = {team.id: team.division for team in teams}
            season = create_season(year, teams, -1)

            safety = 0
            while not season.season_over and safety < 40:
                main._play_live_matchday(season, None)
                safety += 1

            promoted = sorted(
                [team for team in teams if team.division < initial_divisions.get(team.id, team.division)],
                key=lambda t: (t.division, t.name),
            )
            relegated = sorted(
                [team for team in teams if team.division > initial_divisions.get(team.id, team.division)],
                key=lambda t: (t.division, t.name),
            )

            top_scorer = season.best_player_goals or {}
            best_attack = season.best_team_goals or {}
            best_defense_team = min(
                teams,
                key=lambda club: (club.div_ga, -club.div_gd, -club.div_gf, club.name),
            )

            season_data = {
                "year": year,
                "div1": season.division_champions.get(1, "-"),
                "cup": season.copa_champion.name if season.copa_champion else "-",
                "top_scorer": top_scorer,
                "promoted": [team.name for team in promoted],
                "relegated": [team.name for team in relegated],
            }
            seasons_summary.append(season_data)

            lines.append(f"## Temporada {year}")
            lines.append("")
            lines.append("### Campeoes")
            lines.append(f"- Divisao 1: {season.division_champions.get(1, '-')}")
            lines.append(f"- Divisao 2: {season.division_champions.get(2, '-')}")
            lines.append(f"- Divisao 3: {season.division_champions.get(3, '-')}")
            lines.append(f"- Divisao 4: {season.division_champions.get(4, '-')}")
            lines.append(f"- Copa: {season.copa_champion.name if season.copa_champion else '-'}")
            lines.append("")

            lines.append("### Artilheiros")
            lines.append(
                f"- Artilheiro da temporada: {top_scorer.get('player', '-')} "
                f"({top_scorer.get('team', '-')}) - {top_scorer.get('goals', 0)} gols"
            )
            for idx, (player_name, team_name, goals) in enumerate(season.top_scorers, start=1):
                lines.append(f"- Top {idx}: {player_name} ({team_name}) - {int(goals)} gols")
            lines.append("")

            lines.append("### Promovidos")
            if promoted:
                for team in promoted:
                    old_div = initial_divisions.get(team.id, team.division)
                    lines.append(f"- {team.name}: {old_div} -> {team.division}")
            else:
                lines.append("- Nenhum")
            lines.append("")

            lines.append("### Rebaixados")
            if relegated:
                for team in relegated:
                    old_div = initial_divisions.get(team.id, team.division)
                    lines.append(f"- {team.name}: {old_div} -> {team.division}")
            else:
                lines.append("- Nenhum")
            lines.append("")

            lines.append("### Destaques Financeiros e Tecnicos")
            lines.append(
                f"- Melhor ataque: {best_attack.get('team', '-')} com {best_attack.get('goals', 0)} gols"
            )
            lines.append(
                f"- Melhor defesa: {best_defense_team.name} com {int(best_defense_team.div_ga)} gols sofridos"
            )
            if season.max_attendance:
                lines.append(
                    f"- Maior publico: {season.max_attendance.get('home', '-')} x "
                    f"{season.max_attendance.get('away', '-')} - {int(season.max_attendance.get('attendance', 0)):,}"
                )
            if season.max_income:
                lines.append(
                    f"- Maior renda: {season.max_income.get('home', '-')} x "
                    f"{season.max_income.get('away', '-')} - {_fmt_money(int(season.max_income.get('income', 0)))}"
                )
            lines.append("")

            lines.append("### Clubes, Financas e Elencos")
            for div in [1, 2, 3, 4]:
                lines.append(f"#### Divisao {div}")
                division_teams = [
                    team for team in teams
                    if _safe_int(season.final_positions.get(team.id, {}).get("division", team.division)) == div
                ]
                division_teams.sort(
                    key=lambda team: (
                        _safe_int(season.final_positions.get(team.id, {}).get("position", 99)),
                        team.name,
                    )
                )
                for team in division_teams:
                    lines.extend(_season_team_block(team, season))
                lines.append("")

    return "\n".join(lines), seasons_summary


def main_cli() -> None:
    parser = argparse.ArgumentParser(description="Gera relatorio completo de simulacao do ClassicFoot.")
    parser.add_argument("--start-year", type=int, default=2025)
    parser.add_argument("--seasons", type=int, default=10)
    parser.add_argument("--seed", type=int, default=20260417)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports") / "simulation_10_seasons.md",
    )
    args = parser.parse_args()

    report_text, summary = _collect_report(args.start_year, args.seasons, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report_text, encoding="utf-8")

    print(f"Relatorio gerado em: {args.output}")
    print("")
    for season in summary:
        top = season.get("top_scorer", {})
        print(
            f"{season['year']}: Div1 {season['div1']} | Copa {season['cup']} | "
            f"Artilheiro {top.get('player', '-')} ({top.get('team', '-')}) {top.get('goals', 0)}g"
        )


if __name__ == "__main__":
    main_cli()
