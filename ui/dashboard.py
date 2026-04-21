"""Dashboard principal da temporada e tela de próxima rodada."""
from typing import List, Optional
from models import Fixture, CupTie  # noqa: F401 — usados via lineup helpers

from models import Team, Position
from season import Season, sort_standings
from term import (
    clear, pause, rule, box, Table,
    ovr_color, fmt_money, fmt_fans,
    GG, YY, Y, C, RR, R, WW, M, DIM, G, RST,
    term_width, pad, _visible_len,
    h, BB,
)

from ui.common import (
    _ovr_text, _ellipsize_visible, _mini_form,
    _box_width, _print_side_by_side,
)
from ui.lineup import _find_player_next_match, _render_probable_lineup


def season_dashboard(season: Season, player_team: Optional[Team]) -> None:
    clear()
    w = term_width()
    print(rule(f"⚽ CLASSICFOOT  ─  TEMPORADA {season.year}  ─  "
               f"RODADA {season.current_matchday}/{len(season.calendar)}"))
    print()

    if player_team is None:
        menu_lines = [
            RR + "Sem clube no momento" + RST,
            DIM + "Acompanhe as rodadas" + RST,
            DIM + "e aguarde propostas." + RST,
            GG + h * 26 + RST,
            WW + "MENU:" + RST,
            GG + "[6]" + RST + GG + " ▶ AVANÇAR RODADA" + RST,
            YY + "[2]" + RST + " Classificação",
            YY + "[3]" + RST + " Tabela da Copa",
            YY + "[C]" + RST + " Calendário",
            YY + "[A]" + RST + " Artilheiros",
            YY + "[S]" + RST + " Salvar Jogo",
            YY + "[0]" + RST + " Menu Principal",
        ]
        status_lines = [
            "",
            WW + "  Carreira em aberto." + RST,
            DIM + "  Você segue disponível no mercado" + RST,
            DIM + "  e novas ofertas podem aparecer" + RST,
            DIM + "  após as próximas rodadas." + RST,
            "",
        ]
        menu_box = box(menu_lines, border_color=GG, title_color=GG, width=36)
        status_box = box(status_lines, title="SITUAÇÃO DO TREINADOR", border_color=C, title_color=C, width=44)
        if _box_width(menu_box) + 2 + _box_width(status_box) <= w:
            _print_side_by_side(menu_box, status_box, gap=2)
        else:
            print(menu_box)
            print()
            print(status_box)
        return

    # ── Monta menu lateral ────────────────────────────────────────
    t = player_team
    ranked_division = sort_standings([club for club in season.all_teams if club.division == t.division])
    current_position = next((idx + 1 for idx, club in enumerate(ranked_division) if club.id == t.id), 0)

    next_league = None
    next_cup = None
    next_league_team = None
    next_cup_team = None
    for matchday in season.calendar[season.current_matchday:]:
        if next_league is None:
            for fixture in matchday.get("fixtures", []):
                if fixture.home_team.id == t.id or fixture.away_team.id == t.id:
                    opponent = fixture.away_team if fixture.home_team.id == t.id else fixture.home_team
                    venue = "Casa" if fixture.home_team.id == t.id else "Fora"
                    next_league = f"{opponent.name[:16]} ({venue})"
                    next_league_team = opponent
                    break
        if next_cup is None:
            for tie in (matchday.get("ties") or []):
                if tie.team_a.id == t.id or tie.team_b.id == t.id:
                    opponent = tie.team_b if tie.team_a.id == t.id else tie.team_a
                    next_cup = f"{opponent.name[:16]}"
                    next_cup_team = opponent
                    break
        if next_league and next_cup:
            break

    recent_form = _mini_form(season.results_history, t) or DIM + "sem jogos" + RST
    next_league_form = _mini_form(season.results_history, next_league_team) if next_league_team else None
    next_cup_form = _mini_form(season.results_history, next_cup_team) if next_cup_team else None

    menu_lines = [
        WW + t.name[:24] + RST,
        DIM + f"{t.city}/{t.state}" + RST,
        DIM + t.stadium[:22] + RST,
        DIM + f"Div {t.division}  │  Prestígio {t.prestige}" + RST,
        GG + h * 26 + RST,
        C  + "Técnico: " + RST + WW + t.coach.name[:16] + RST,
        C  + "Form.: " + RST + YY + t.formation.value + RST +
        C  + "  Post.: " + RST + M + t.postura.value[:11] + RST,
        GG + h * 26 + RST,
        f"Liga: {GG}V{t.div_wins}{RST} {YY}E{t.div_draws}{RST} {RR}D{t.div_losses}{RST}  {C}{t.div_points}pts{RST}  SG:{t.div_gd:+d}",
        f"Posição: {YY}{current_position}º{RST}  Copa: {WW}{t.copa_phase.capitalize()}{RST}",
        f"Próx. Liga: {WW}{(next_league or '—')}{RST}",
        f"Hist. Advers. Liga: {next_league_form or DIM + '—' + RST}",
        f"Próx. Copa: {WW}{(next_cup or '—')}{RST}",
        f"Hist. Advers. Copa: {next_cup_form or DIM + '—' + RST}",
        f"Histórico: {recent_form}",
        GG + h * 26 + RST,
        Y  + f"Saldo: {fmt_money(t.caixa)}" + RST,
        R  + f"Despesas: {fmt_money(t.salario_mensal)}/mês" + RST,
        G  + f"Torcida: {fmt_fans(t.torcida)}" + RST,
        GG + h * 26 + RST,
        WW + "MENU:" + RST,
        YY + "[1]" + RST + " Próxima rodada",
        YY + "[2]" + RST + " Classificação",
        YY + "[3]" + RST + " Tabela da Copa",
        YY + "[4]" + RST + " Ajustar Formação",
        YY + "[5]" + RST + " Postura Tática",
        GG + "[6]" + RST + GG + " ▶ JOGAR PARTIDA" + RST,
        YY + "[7]" + RST + " Extrato Bancário",
        YY + "[8]" + RST + " Torcida",
        YY + "[9]" + RST + " Estádio",
        YY + "[C]" + RST + " Calendário",
        YY + "[R]" + RST + " Renovar Contrato",
        YY + "[T]" + RST + " Transferências",
        YY + "[E]" + RST + " Treino (5 jogadores)",
        YY + "[A]" + RST + " Artilheiros",
        YY + "[V]" + RST + " Vender Jogador",
        YY + "[H]" + RST + " Histórico",
        YY + "[S]" + RST + " Salvar Jogo",
        YY + "[0]" + RST + " Menu Principal",
    ]

    # ── Monta elenco ─────────────────────────────────────────────
    pos_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
    players = sorted(t.players, key=lambda p: (pos_order.get(p.position, 9), -p.overall))

    squad_header = (
        DIM + f"{'#':>3} " + RST +
        WW + f"{'Nome':<20}" + RST +
        M  + f"{'★':^3}" + RST +
        C  + f"{'Pos':^5}" + RST +
        YY + f"{'OVR':^5}" + RST +
        DIM + f"{'Cont':^6}" + RST +
        Y  + f"{'Salário':>9}" + RST +
        G  + f"{'Gols':^5}" + RST +
        R  + f"{'SUS':^4}" + RST
    )

    squad_lines: List[str] = [squad_header, C + "─" * 70 + RST]
    for i, p in enumerate(players, 1):
        sus_str = RR + str(p.suspenso) + RST if p.suspenso > 0 else DIM + "-" + RST
        squad_lines.append(
            DIM + f"{i:>3} " + RST +
            WW + pad(p.name, 20) + RST +
            (M + f"{'*' if getattr(p, 'is_star', False) else '-':^3}" + RST) +
            C  + f"{p.pos_label():^5}" + RST +
            ovr_color(int(round(p.overall))) + f"{_ovr_text(p.overall):^5}" + RST +
            DIM + f"{p.contrato_rodadas:^4}r" + RST +
            Y  + f"{'R$'+str(p.salario)+'k':>9}" + RST +
            G  + f"{str(p.gols_temp):^5}" + RST +
            sus_str
        )

    max_menu_width = 44
    min_menu_width = 32
    menu_content_width = max_menu_width - 4
    menu_lines = [_ellipsize_visible(line, menu_content_width) for line in menu_lines]
    menu_width = max(min_menu_width, min(max_menu_width, max(_visible_len(line) for line in menu_lines) + 4))
    menu_box_str = box(menu_lines, border_color=GG, title_color=GG, width=menu_width)
    squad_box = box(
        squad_lines,
        title=f"ELENCO — {t.name}",
        border_color=C,
        title_color=C,
    )

    gap = 2
    if _box_width(menu_box_str) + gap + _box_width(squad_box) <= w:
        _print_side_by_side(menu_box_str, squad_box, gap=gap)
    else:
        print(menu_box_str)
        print()
        print(squad_box)


def show_next_round(season: Season, player_team: Team) -> None:
    clear()
    print(rule("📅 PRÓXIMA RODADA"))
    if season.current_matchday >= len(season.calendar):
        print(DIM + "\n  Temporada encerrada.\n" + RST)
        pause()
        return

    md = season.calendar[season.current_matchday]
    print(f"\n  {WW}{md['label']}{RST}\n")

    tbl = Table(border_color=BB, header_color=YY)
    tbl.add_column("Comp",      width=8,  align="c", color=C)
    tbl.add_column("Mandante",  width=24, align="l", color=WW)
    tbl.add_column("vs",        width=4,  align="c", color=DIM)
    tbl.add_column("Visitante", width=24, align="l", color=WW)
    tbl.add_column("OVR M",     width=7,  align="c", color=Y)
    tbl.add_column("OVR V",     width=7,  align="c", color=Y)

    for f in md.get("fixtures", []):
        home, away = f.home_team, f.away_team
        comp = "Liga" if md["type"] == "liga" else "Copa"
        hs = GG + home.name + RST if home.id == player_team.id else WW + home.name + RST
        as_ = GG + away.name + RST if away.id == player_team.id else WW + away.name + RST
        tbl.add_row(comp, hs, "×", as_,
                    ovr_color(int(home.squad_overall())) + f"{home.squad_overall():.0f}" + RST,
                    ovr_color(int(away.squad_overall())) + f"{away.squad_overall():.0f}" + RST)

    for tie in (md.get("ties") or []):
        a, b = tie.team_a, tie.team_b
        as_ = GG + a.name + RST if a.id == player_team.id else WW + a.name + RST
        bs_ = GG + b.name + RST if b.id == player_team.id else WW + b.name + RST
        tbl.add_row("Copa", as_, "×", bs_,
                    ovr_color(int(a.squad_overall())) + f"{a.squad_overall():.0f}" + RST,
                    ovr_color(int(b.squad_overall())) + f"{b.squad_overall():.0f}" + RST)

    tbl.print()
    next_md, next_fixture, next_tie = _find_player_next_match(season, player_team)

    if next_md:
        print()
        if next_fixture is not None:
            opponent = next_fixture.away_team if next_fixture.home_team.id == player_team.id else next_fixture.home_team
            venue = "Casa" if next_fixture.home_team.id == player_team.id else "Fora"
            print(
                C + f"  Seu próximo jogo: {player_team.name} x {opponent.name}  "
                f"({venue}, {next_md['label']})" + RST
            )
        elif next_tie is not None:
            opponent = next_tie.team_b if next_tie.team_a.id == player_team.id else next_tie.team_a
            print(
                C + f"  Seu próximo jogo: {player_team.name} x {opponent.name}  "
                f"({next_md['label']})" + RST
            )
        print(_render_probable_lineup(player_team))

    pause()
