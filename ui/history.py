"""Notificações, fim de temporada, histórico da carreira e propostas de emprego."""
from typing import List, Optional

from models import Team
from season import Season, sort_standings, PRIZE_LIGA, PRIZE_COPA
from term import (
    clear, pause, rule, box, Table,
    GG, YY, C, RR, WW, DIM, G, RST,
    term_width, pad,
    TL, TR, BL, BR, H, V,
)

from ui.common import _e


def _team_position(team: Team, all_teams: List[Team]) -> int:
    ranked = sort_standings([club for club in all_teams if club.division == team.division])
    return next((idx + 1 for idx, club in enumerate(ranked) if club.id == team.id), len(ranked))


def show_notifications(messages: List[str], title: str = "NOTIFICAÇÕES") -> None:
    if not messages:
        return
    clear()
    print(rule(title))
    for index, msg in enumerate(messages, start=1):
        lines = [
            "",
            f"  {msg}",
            "",
        ]
        print(box(lines, title=f"{title} {index}", border_color=YY, title_color=YY, width=90))
        print()
    messages.clear()
    pause()


def prompt_job_offer(coach_name: str, team: Team, all_teams: Optional[List[Team]] = None) -> bool:
    clear()
    print(rule("PROPOSTA DE EMPREGO"))
    all_teams = all_teams or [team]
    position = _team_position(team, all_teams)
    division_size = len([club for club in all_teams if club.division == team.division]) or 1
    top11 = sorted(team.players, key=lambda p: p.overall, reverse=True)[:11]
    top11_ovr = int(round(sum(p.overall for p in top11) / len(top11))) if top11 else 0
    squad_size = len(team.players)
    recent = " ".join(team.last_results[-5:]) if team.last_results else "sem jogos recentes"
    destaque = ", ".join(p.name for p in sorted(team.players, key=lambda p: p.overall, reverse=True)[:3])
    lines = [
        "",
        f"  {WW}{coach_name}{RST}, o {GG}{team.name}{RST} quer contratar você.",
        f"  Divisão: {C}{team.division}{RST}  │  Classificação: {YY}{position}º/{division_size}{RST}  │  Prestígio: {YY}{team.prestige}{RST}",
        f"  Cidade: {WW}{team.city}/{team.state}{RST}  │  Estádio: {WW}{team.stadium}{RST}",
        f"  Elenco: {C}{squad_size} jogadores{RST}  │  OVR base (Top 11): {YY}{top11_ovr}{RST}",
        f"  Histórico recente: {WW}{recent}{RST}",
        f"  Destaques do elenco: {GG}{destaque}{RST}",
        "",
        f"  {YY}[1]{RST} Aceitar proposta",
        f"  {YY}[0]{RST} Recusar",
        "",
    ]
    print(box(lines, title="MERCADO DE TREINADORES", border_color=GG, title_color=GG, width=100))
    return input("  Escolha: ").strip() == "1"


def show_season_end(season: Season, player_team: Team) -> None:
    clear()
    w = term_width()
    print(GG + TL + H * (w - 2) + TR + RST)
    title = YY + f"  FIM DA TEMPORADA {season.year}  " + RST
    print(GG + V + RST + pad(title, w - 2, "c") + GG + V + RST)
    print(GG + BL + H * (w - 2) + BR + RST)
    print()

    final_data = season.final_positions.get(player_team.id, {}) if hasattr(season, "final_positions") else {}
    original_div = int(final_data.get("division", player_team.division))
    pos = int(final_data.get("position", 0) or 0)
    if pos <= 0:
        div_teams = [t for t in season.all_teams if t.division == original_div]
        ranked = sort_standings(div_teams)
        pos = next((i + 1 for i, t in enumerate(ranked) if t.id == player_team.id), 1)

    liga_lines = []
    if pos <= 2 and original_div > 1:
        liga_lines.append(GG + f"  {_e('🎉','>>>')} PROMOVIDO! {player_team.name} subiu para a Divisão {original_div - 1}!" + RST)
    elif pos >= 7 and original_div < 4:
        liga_lines.append(RR + f"  {_e('😢','...')} REBAIXADO. {player_team.name} foi para a Divisão {original_div + 1}." + RST)
    else:
        liga_lines.append(WW + f"  {player_team.name} terminou em {YY}{pos}º lugar{RST} na Divisão {original_div}." + RST)

    from season import _season_prize_multiplier  # type: ignore[attr-defined]
    multiplier = _season_prize_multiplier(season.year)
    liga_prize = int(PRIZE_LIGA.get(original_div, {}).get(pos, 0) * multiplier)

    copa_phase = getattr(player_team, "copa_phase", "grupos")
    _copa_phase_labels = {
        "campeão":       (_e("🏆", "[CAMPEAO]") + " CAMPEÃO DA COPA!", YY),
        "final":         ("Vice-campeão da Copa",               C),
        "semi":          ("Semifinalista da Copa",              C),
        "quartas":       ("Quartas de final da Copa",           WW),
        "oitavas":       ("Oitavas de final da Copa",           DIM),
        "primeira_fase": ("Eliminado na 1ª Fase da Copa",       DIM),
        "eliminado":     ("Eliminado na Copa",                  DIM),
    }
    copa_label, copa_color = _copa_phase_labels.get(copa_phase, ("—", DIM))
    copa_prize_key = {
        "campeão": "campeão", "final": "vice",
        "semi": "semi", "quartas": "quartas",
        "oitavas": "oitavas", "primeira_fase": "primeira_fase",
    }.get(copa_phase)
    copa_prize = int(PRIZE_COPA.get(copa_prize_key, 0) * multiplier) if copa_prize_key else 0
    copa_champ_line: Optional[str] = None
    if season.copa_champion and season.copa_champion.id != player_team.id:
        copa_champ_line = WW + f"  {_e('🏆','>>>')} Copa: Campeão — {YY}{season.copa_champion.name}{RST}"

    players_with_base = [p for p in player_team.players if p.season_base_ovr is not None]
    ovr_line: Optional[str] = None
    if players_with_base:
        top_start = sorted(players_with_base, key=lambda p: p.season_base_ovr or 0.0, reverse=True)[:11]
        top_end   = sorted(player_team.players, key=lambda p: p.overall, reverse=True)[:11]
        avg_start = sum(p.season_base_ovr or 0.0 for p in top_start) / len(top_start)
        avg_end   = sum(p.overall for p in top_end) / len(top_end)
        ovr_diff  = avg_end - avg_start
        ovr_arrow = (GG + f"+{ovr_diff:+.1f}") if ovr_diff >= 0 else (RR + f"{ovr_diff:+.1f}")
        ovr_line = WW + f"  OVR médio (top-11): {YY}{avg_start:.1f}{RST} → {YY}{avg_end:.1f} {ovr_arrow}{RST}"

    scorer_line: Optional[str] = None
    if season.top_scorers:
        sc_name, sc_club, sc_goals = season.top_scorers[0]
        scorer_line = GG + f"  {_e('⚽','->')} Artilheiro: {sc_name} ({sc_club}) — {sc_goals} gols" + RST

    for line in liga_lines:
        print(line)

    if copa_champ_line:
        print(copa_champ_line)
    print(copa_color + f"  Copa: {copa_label}" + RST)

    print()
    if ovr_line:
        print(ovr_line)
    if scorer_line:
        print(scorer_line)

    total_prize = liga_prize + copa_prize
    if total_prize > 0:
        print(YY + f"  {_e('💰','$')} Premiação estimada: R${total_prize:,} mil" + RST)

    print(WW + f"  Caixa atual: {GG if player_team.caixa >= 0 else RR}R${player_team.caixa:,} mil{RST}")
    print()
    pause()


def show_history(career: object) -> None:
    """Exibe o histórico de temporadas da carreira."""
    clear()
    print(rule("📜 HISTÓRICO DA CARREIRA"))
    total_seasons = len(career.season_history)  # type: ignore[attr-defined]
    current_team = "Sem clube" if career.unemployed else "Empregado"  # type: ignore[attr-defined]
    summary_lines = [
        f"  Técnico: {WW}{career.player_coach.name}{RST}",  # type: ignore[attr-defined]
        f"  Temporadas concluídas: {YY}{total_seasons}{RST}",
        f"  Situação atual: {C}{current_team}{RST}",
    ]
    print(box(summary_lines, title="RESUMO DA CARREIRA", border_color=C, title_color=YY, width=70))

    if career.season_history:  # type: ignore[attr-defined]
        print()
        recent = sorted(career.season_history, key=lambda entry: int(entry.get("year", 0) or 0))[-8:]  # type: ignore[attr-defined]
        tbl = Table(title="ÚLTIMAS TEMPORADAS", border_color=C, header_color=YY, title_color=C)
        tbl.add_column("Ano",  width=5,  align="c", color=DIM)
        tbl.add_column("Time", width=20, align="l", color=WW)
        tbl.add_column("Div",  width=4,  align="c", color=C)
        tbl.add_column("Pos",  width=4,  align="c", color=YY)
        tbl.add_column("Copa", width=14, align="l", color=G)
        for entry in recent:
            tbl.add_row(
                str(entry.get("year", "—")),
                str(entry.get("team", "—"))[:20],
                str(entry.get("division", "—")),
                str(entry.get("position", "—")) if int(entry.get("position", 0) or 0) > 0 else "—",
                str(entry.get("copa_phase", "—")).capitalize()[:14],
            )
        if recent:
            tbl.print()
        else:
            print(DIM + "  Sem temporadas válidas para exibir no formato atual." + RST)

    world = getattr(career, "world_history", {}) or {}
    if world:
        print()
        print(C + "  RECORDES HISTÓRICOS" + RST)
        print()

        team_goals    = world.get("team_goals_record", {})
        player_goals  = world.get("player_goals_record", {})
        points_record = world.get("league_points_record", {})
        max_att       = world.get("max_attendance", {})
        max_income    = world.get("max_income", {})
        biggest_win   = world.get("biggest_win", {})

        lines = [
            f"  Mais pontos na história da liga: {WW}{points_record.get('team', '-')} ({points_record.get('points', 0)} pts){RST}",
            f"  Melhor ataque (acumulado): {WW}{team_goals.get('team', '-')} ({team_goals.get('goals', 0)} gols){RST}",
            f"  Artilheiro (acumulado): {WW}{player_goals.get('player', '-')} - {player_goals.get('team', '-')} ({player_goals.get('goals', 0)} gols){RST}",
            f"  Maior goleada: {WW}{biggest_win.get('winner', '-')} {biggest_win.get('score', '-')} {biggest_win.get('loser', '-')} ({biggest_win.get('year', '-')}){RST}",
            f"  Maior público: {WW}{max_att.get('attendance', 0):,}{RST} em {max_att.get('home', '-')} x {max_att.get('away', '-')} ({max_att.get('year', '-')})",
            f"  Maior renda: {WW}R${int(max_income.get('income', 0)):,}k{RST} em {max_income.get('home', '-')} x {max_income.get('away', '-')} ({max_income.get('year', '-')})",
        ]
        print(box(lines, title="RECORDES", border_color=GG, title_color=GG, width=110))

        champions = world.get("division_champions", [])
        if champions:
            print()
            champ_tbl = Table(title="CAMPEÕES DAS DIVISÕES", border_color=C, header_color=YY, title_color=C)
            champ_tbl.add_column("Ano",     width=5,  align="c", color=DIM)
            champ_tbl.add_column("Div",     width=4,  align="c", color=C)
            champ_tbl.add_column("Clube",   width=24, align="l", color=WW)
            champ_tbl.add_column("Técnico", width=24, align="l", color=G)
            for item in champions[-24:]:
                champ_tbl.add_row(
                    str(item.get("year", "-")),
                    str(item.get("division", "-")),
                    str(item.get("team", "-"))[:24],
                    str(item.get("coach", "-"))[:24],
                )
            champ_tbl.print()

        coaches = world.get("coach_titles", {})
        if coaches:
            print()
            top_coaches = sorted(coaches.items(), key=lambda entry: (-entry[1], entry[0]))[:10]
            coach_lines = [f"  {WW}{name:<28}{RST} {YY}{titles} título(s){RST}" for name, titles in top_coaches]
            print(box(coach_lines, title="TÉCNICOS CAMPEÕES", border_color=YY, title_color=YY, width=50))

        div1_titles = world.get("div1_titles_by_club", {})
        if div1_titles:
            print()
            top_div1 = sorted(div1_titles.items(), key=lambda entry: (-entry[1], entry[0]))[:12]
            lines_div1 = [f"  {WW}{club:<28}{RST} {GG}{titles} título(s){RST}" for club, titles in top_div1]
            print(box(lines_div1, title="CAMPEÕES DA 1ª DIVISÃO (CLUBES)", border_color=GG, title_color=GG, width=56))

        copa_titles = world.get("copa_titles_by_club", {})
        if copa_titles:
            print()
            top_copa = sorted(copa_titles.items(), key=lambda entry: (-entry[1], entry[0]))[:12]
            lines_copa = [f"  {WW}{club:<28}{RST} {YY}{titles} título(s){RST}" for club, titles in top_copa]
            print(box(lines_copa, title="CAMPEÕES DA COPA (CLUBES)", border_color=C, title_color=C, width=56))
    pause()
