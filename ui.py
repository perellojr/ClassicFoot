"""
ClassicFoot - Interface visual estilo Elifoot 2
Terminal colorido com colorama + box-drawing characters
"""
from typing import List, Optional
from colorama import Back, Fore, Style
from models import Team, Player, Position, Formation, Postura, MatchResult, CupTie
from season import Season, sort_standings
from term import (
    clear, pause, rule, box, Table, fmt_fans, fmt_money,
    ovr_color, form_color, cond_color, colored_score,
    GG, YY, Y, C, BB, RR, R, WW, W, M, DIM, RST, G,
    term_width, pad, _visible_len, hline,
    TL, TR, BL, BR, H, V, ML, MR, TM, BM, X,
    tl, tr, bl, br, h, v, ml, mr,
)

RENDA_TORCIDA_FACTOR = 0.00015


# ═══════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════
def banner():
    clear()
    logo_lines = [
        "  ██████╗██╗      █████╗ ███████╗███████╗██╗ ██████╗    ███████╗ ██████╗  ██████╗ ████████╗",
        " ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝    ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝",
        " ██║     ██║     ███████║███████╗███████╗██║██║         █████╗  ██║   ██║██║   ██║   ██║   ",
        " ██║     ██║     ██╔══██║╚════██║╚════██║██║██║         ██╔══╝  ██║   ██║██║   ██║   ██║   ",
        " ╚██████╗███████╗██║  ██║███████║███████║██║╚██████╗    ██║     ╚██████╔╝╚██████╔╝   ██║   ",
        "  ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝    ╚═╝      ╚═════╝  ╚═════╝    ╚═╝  ",
    ]
    w = term_width()
    print(GG + TL + H * (w - 2) + TR + RST)
    for line in logo_lines:
        vis = _visible_len(line)
        pad_l = (w - 2 - vis) // 2
        print(GG + V + RST + " " * pad_l + GG + line + RST + " " * max(0, w - 2 - vis - pad_l) + GG + V + RST)
    sub = "Brasileirão Edition  •  v1.0"
    vis = _visible_len(sub)
    pad_l = (w - 2 - vis) // 2
    print(GG + V + RST + " " * pad_l + DIM + sub + RST + " " * max(0, w - 2 - vis - pad_l) + GG + V + RST)
    print(GG + BL + H * (w - 2) + BR + RST)
    print()


# ═══════════════════════════════════════════════════════════════
# MENU PRINCIPAL
# ═══════════════════════════════════════════════════════════════
def main_menu() -> str:
    lines = [
        "",
        YY + "  [1]" + RST + "  Nova Temporada",
        YY + "  [2]" + RST + "  Carregar Jogo",
        YY + "  [3]" + RST + "  Créditos",
        YY + "  [0]" + RST + "  Sair",
        "",
    ]
    print(box(lines, title="MENU PRINCIPAL", width=36, border_color=GG, title_color=YY))
    return input("\n  Escolha: ").strip()


# ═══════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPAL — estilo Elifoot (menu lateral + elenco)
# ═══════════════════════════════════════════════════════════════
def season_dashboard(season: Season, player_team: Team | None):
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

    # ── Monta menu lateral (col esquerda, ~30 chars) ──────────
    t = player_team
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
        f"Copa: {WW}{t.copa_phase.capitalize()}{RST}",
        GG + h * 26 + RST,
        Y  + f"💰 {fmt_money(t.caixa)}" + RST,
        R  + f"💸 {fmt_money(t.salario_mensal)}/mês" + RST,
        G  + f"👥 {fmt_fans(t.torcida)}" + RST,
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
        YY + "[R]" + RST + " Renovar Contrato",
        YY + "[T]" + RST + " Transferências",
        YY + "[A]" + RST + " Artilheiros",
        YY + "[S]" + RST + " Salvar Jogo",
        YY + "[0]" + RST + " Menu Principal",
    ]

    # ── Monta elenco (col direita) ─────────────────────────────
    pos_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
    players = sorted(t.players, key=lambda p: (pos_order.get(p.position, 9), -p.overall))

    squad_header = (
        DIM + f"{'#':>3} " + RST +
        WW + f"{'Nome':<20}" + RST +
        C  + f"{'Pos':^5}" + RST +
        YY + f"{'OVR':^5}" + RST +
        G  + f"{'FOR':^5}" + RST +
        M  + f"{'MOR':^5}" + RST +
        BB + f"{'FÍS':^5}" + RST +
        DIM + f"{'Cont':^6}" + RST +
        Y  + f"{'Salário':>9}" + RST +
        G  + f"{'G/A':^7}" + RST +
        R  + f"{'SUS':^4}" + RST
    )

    squad_lines = [squad_header, C + "─" * 70 + RST]
    for i, p in enumerate(players, 1):
        sus_str = RR + str(p.suspenso) + RST if p.suspenso > 0 else DIM + "-" + RST
        squad_lines.append(
            DIM + f"{i:>3} " + RST +
            WW + pad(p.name, 20) + RST +
            C  + f"{p.pos_label():^5}" + RST +
            ovr_color(p.overall) + f"{p.overall:^5}" + RST +
            form_color(p.forma) + f"{p.forma:^5}" + RST +
            M  + f"{p.moral:^5}" + RST +
            cond_color(p.condicao_fisica) + f"{p.condicao_fisica:^5}" + RST +
            DIM + f"{p.contrato_rodadas:^4}r" + RST +
            Y  + f"{'R$'+str(p.salario)+'k':>9}" + RST +
            G  + f"{str(p.gols_temp)+'/'+str(p.assist_temp):^7}" + RST +
            sus_str
        )

    menu_width = max(32, max(_visible_len(line) for line in menu_lines) + 4)
    menu_box_str = box(menu_lines, border_color=GG, title_color=GG, width=menu_width)
    squad_box = box(
        squad_lines,
        title=f"ELENCO — {t.name}",
        border_color=C,
        title_color=C,
    )

    # Usa duas colunas só quando isso realmente cabe no terminal.
    gap = 2
    if _box_width(menu_box_str) + gap + _box_width(squad_box) <= w:
        _print_side_by_side(menu_box_str, squad_box, gap=gap)
    else:
        print(menu_box_str)
        print()
        print(squad_box)


def _box_width(rendered_box: str) -> int:
    lines = rendered_box.split("\n")
    return max((_visible_len(line) for line in lines), default=0)


def _print_side_by_side(left: str, right: str, gap: int = 1):
    """Imprime duas caixas lado a lado."""
    left_lines  = left.split("\n")
    right_lines = right.split("\n")
    max_lines   = max(len(left_lines), len(right_lines))
    left_vis_w  = max(_visible_len(l) for l in left_lines) if left_lines else 0

    for i in range(max_lines):
        l = left_lines[i]  if i < len(left_lines)  else ""
        r = right_lines[i] if i < len(right_lines) else ""
        l_pad = left_vis_w - _visible_len(l)
        print(l + " " * (l_pad + gap) + r)


def game_menu() -> str:
    choice = input("\n  ► Opção: ").strip().upper()
    return choice or "6"


def prompt_contract_renewal(team: Team):
    clear()
    print(rule(f"RENOVAÇÃO DE CONTRATO — {team.name}"))
    print()

    players = sorted(team.players, key=lambda p: (p.contrato_rodadas, -p.overall, p.name))

    tbl = Table(title="ELENCO", border_color=C, header_color=YY, title_color=C)
    tbl.add_column("N", width=4, align="r", color=DIM)
    tbl.add_column("Nome", width=24, align="l", color=WW)
    tbl.add_column("Pos", width=5, align="c", color=C)
    tbl.add_column("OVR", width=5, align="c", color=YY)
    tbl.add_column("Cont", width=6, align="c", color=DIM)
    tbl.add_column("Salário", width=12, align="r", color=Y)

    for idx, player in enumerate(players, start=1):
        tbl.add_row(
            str(idx),
            player.name,
            player.pos_label(),
            str(player.overall),
            f"{player.contrato_rodadas}r",
            f"R${player.salario:,}k",
        )
    tbl.print()

    choice = input("\n  Jogador para renovar (ENTER cancela): ").strip()
    if not choice:
        return None, None
    if not choice.isdigit() or int(choice) not in range(1, len(players) + 1):
        print(RR + "\n  Jogador inválido." + RST)
        pause()
        return None, None

    player = players[int(choice) - 1]
    offer = input(f"  Novo salário para {player.name} (atual R${player.salario:,}k): ").strip()
    if not offer:
        return None, None
    offer = offer.replace(".", "").replace(",", "")
    if not offer.isdigit():
        print(RR + "\n  Valor inválido." + RST)
        pause()
        return None, None

    return player, int(offer)


# ═══════════════════════════════════════════════════════════════
# PRÓXIMA RODADA
# ═══════════════════════════════════════════════════════════════
def _pick_probable_lineup(team: Team) -> List[Player]:
    available = [p for p in team.players if p.suspenso <= 0]
    if not available:
        available = list(team.players)

    slots = team.formation.slots()
    lineup: List[Player] = []
    used_ids = set()

    def player_score(player: Player) -> float:
        return player.overall + (player.forma * 0.15) + (player.condicao_fisica * 0.10) + (player.moral * 0.05)

    def take_best(position: Position, amount: int) -> None:
        candidates = [p for p in available if p.position == position and p.id not in used_ids]
        candidates.sort(key=player_score, reverse=True)
        for player in candidates[:amount]:
            lineup.append(player)
            used_ids.add(player.id)

    for position in [Position.GK, Position.DEF, Position.MID, Position.ATK]:
        take_best(position, slots.get(position, 0))

    if len(lineup) < 11:
        leftovers = [p for p in available if p.id not in used_ids]
        leftovers.sort(key=player_score, reverse=True)
        for player in leftovers[: 11 - len(lineup)]:
            lineup.append(player)
            used_ids.add(player.id)

    position_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
    return sorted(lineup, key=lambda p: (position_order.get(p.position, 9), -player_score(p), p.name))


def _find_player_next_match(season: Season, player_team: Team):
    for matchday in season.calendar[season.current_matchday:]:
        for fixture in matchday.get("fixtures", []):
            if fixture.home_team.id == player_team.id or fixture.away_team.id == player_team.id:
                return matchday, fixture, None
        for tie in matchday.get("ties", []):
            if tie.team_a.id == player_team.id or tie.team_b.id == player_team.id:
                return matchday, None, tie
    return None, None, None


def _render_probable_lineup(team: Team) -> str:
    lineup = _pick_probable_lineup(team)
    rows = []
    for index, player in enumerate(lineup, start=1):
        rows.append(
            f"{DIM}{index:>2}.{RST} {WW}{pad(player.name, 20)}{RST} "
            f"{C}{player.pos_label():^5}{RST} "
            f"{YY}{player.overall:>2}{RST} "
            f"{G}F{player.forma:>2}{RST} "
            f"{BB}C{player.condicao_fisica:>2}{RST}"
        )

    return box(
        rows,
        title=f"ESCALAÇÃO PROVÁVEL — {team.formation.value}",
        border_color=GG,
        title_color=YY,
        width=48,
    )


def show_next_round(season: Season, player_team: Team):
    clear()
    print(rule("📅 PRÓXIMA RODADA"))
    if season.current_matchday >= len(season.calendar):
        print(DIM + "\n  Temporada encerrada.\n" + RST)
        pause()
        return

    md = season.calendar[season.current_matchday]
    print(f"\n  {WW}{md['label']}{RST}\n")

    tbl = Table(border_color=BB, header_color=YY)
    tbl.add_column("Comp",     width=8,  align="c", color=C)
    tbl.add_column("Mandante", width=24, align="l", color=WW)
    tbl.add_column("vs",       width=4,  align="c", color=DIM)
    tbl.add_column("Visitante",width=24, align="l", color=WW)
    tbl.add_column("OVR M",    width=7,  align="c", color=Y)
    tbl.add_column("OVR V",    width=7,  align="c", color=Y)

    for f in md.get("fixtures", []):
        home, away = f.home_team, f.away_team
        comp = "Liga" if md["type"] == "liga" else "Copa"
        hs = GG + home.name + RST if home.id == player_team.id else WW + home.name + RST
        as_ = GG + away.name + RST if away.id == player_team.id else WW + away.name + RST
        tbl.add_row(comp, hs, "×", as_,
                    ovr_color(int(home.squad_overall())) + f"{home.squad_overall():.0f}" + RST,
                    ovr_color(int(away.squad_overall())) + f"{away.squad_overall():.0f}" + RST)

    for tie in md.get("ties", []):
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
        if next_fixture:
            opponent = next_fixture.away_team if next_fixture.home_team.id == player_team.id else next_fixture.home_team
            venue = "Casa" if next_fixture.home_team.id == player_team.id else "Fora"
            print(
                C + f"  Seu próximo jogo: {player_team.name} x {opponent.name}  "
                f"({venue}, {next_md['label']})" + RST
            )
        elif next_tie:
            opponent = next_tie.team_b if next_tie.team_a.id == player_team.id else next_tie.team_a
            print(
                C + f"  Seu próximo jogo: {player_team.name} x {opponent.name}  "
                f"({next_md['label']})" + RST
            )
        print(_render_probable_lineup(player_team))

    pause()


# ═══════════════════════════════════════════════════════════════
# CLASSIFICAÇÃO
# ═══════════════════════════════════════════════════════════════
def _mini_form(history: List[MatchResult], team: Team) -> str:
    recent = [r for r in history
              if r.home_team.id == team.id or r.away_team.id == team.id][-5:]
    parts = []
    for r in recent:
        w = r.winner()
        if w is None:      parts.append(YY + "E" + RST)
        elif w.id == team.id: parts.append(GG + "V" + RST)
        else:              parts.append(RR + "D" + RST)
    return " ".join(parts)


def show_standings(season: Season, player_team: Team, division: int = 0):
    clear()
    print(rule("CLASSIFICAÇÃO"))
    division_tables = []
    for current_division in [1, 2, 3, 4]:
        div_teams = [t for t in season.all_teams if t.division == current_division]
        ranked = sort_standings(div_teams)
        lines = []
        header = (
            DIM + pad("", 2) + RST +
            YY + pad("TIME", 18) + RST +
            DIM + pad("V", 3, "r") + pad("E", 3, "r") + pad("D", 3, "r") + RST +
            C + pad("GP:GC", 7, "r") + RST +
            YY + pad("PTS", 4, "r") + RST
        )
        lines.append(header)
        lines.append(C + "─" * 40 + RST)

        for pos, t in enumerate(ranked, 1):
            if pos <= 2:
                marker = GG + "▲" + RST
                name_color = GG
            elif pos >= len(ranked) - 1:
                marker = RR + "▼" + RST
                name_color = RR
            else:
                marker = DIM + str(pos) + RST
                name_color = WW

            if t.id == player_team.id:
                name_color = YY if pos not in (1, 2) and pos < len(ranked) - 1 else name_color

            team_name = name_color + pad(t.name[:18], 18) + RST
            line = (
                marker + " " +
                team_name +
                GG + pad(str(t.div_wins), 3, "r") + RST +
                YY + pad(str(t.div_draws), 3, "r") + RST +
                RR + pad(str(t.div_losses), 3, "r") + RST +
                C + pad(f"{t.div_gf}:{t.div_ga}", 7, "r") + RST +
                (GG if pos <= 2 else RR if pos >= len(ranked) - 1 else YY) +
                pad(str(t.div_points), 4, "r") + RST
            )
            lines.append(line)

        division_tables.append(
            box(lines, title=f"{current_division}ª DIVISÃO", border_color=C, title_color=GG, width=44)
        )

    gap = 2
    for i in range(0, len(division_tables), 2):
        left = division_tables[i]
        right = division_tables[i + 1] if i + 1 < len(division_tables) else ""
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


# ═══════════════════════════════════════════════════════════════
# POSTURA
# ═══════════════════════════════════════════════════════════════
def choose_postura(current: Postura) -> Postura:
    clear()
    print(rule("POSTURA TÁTICA"))
    print(f"\n  Postura atual: {C}{current.value}{RST}\n")
    print(f"  {YY}[1]{RST} {RR}Defensivo  {RST} — protege o resultado, menos gols")
    print(f"  {YY}[2]{RST} {YY}Equilibrado{RST} — balanço entre ataque e defesa")
    print(f"  {YY}[3]{RST} {GG}Ofensivo   {RST} — mais pressão, mais risco\n")
    c = input("  Escolha (ENTER = manter): ").strip()
    mapping = {"1": Postura.DEFENSIVO, "2": Postura.EQUILIBRADO, "3": Postura.OFENSIVO}
    return mapping.get(c, current)


# ═══════════════════════════════════════════════════════════════
# RESULTADO DE PARTIDA
# ═══════════════════════════════════════════════════════════════
def show_match_result(result: MatchResult, player_team: Team):
    clear()
    comp = result.competition.upper()
    print(rule(f"  {comp}  "))
    print()

    hg = result.home_goals
    ag = result.away_goals
    player_home = result.home_team.id == player_team.id
    player_won  = result.winner() and result.winner().id == player_team.id
    player_drew = result.winner() is None

    if player_won:   sc = GG; msg = "VITÓRIA! 🎉"
    elif player_drew: sc = YY; msg = "EMPATE"
    else:            sc = RR; msg = "DERROTA"

    # Placar central
    w = term_width()
    home_name = WW + result.home_team.name + RST
    away_name = WW + result.away_team.name + RST
    score     = sc + f"  {hg}  ×  {ag}  " + RST

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


# ═══════════════════════════════════════════════════════════════
# TÁTICAS
# ═══════════════════════════════════════════════════════════════
def show_tactics(team: Team) -> Team:
    clear()
    print(rule("TÁTICAS"))
    print(f"\n  {WW}{team.name}{RST}  │  Técnico: {C}{team.coach.name}{RST}  (Tático: {team.coach.tactical})\n")

    formations = list(Formation)
    print(C + "  FORMAÇÃO ATUAL: " + RST + YY + team.formation.value + RST + "\n")
    for i, f in enumerate(formations, 1):
        slots = f.slots()
        desc = f"DEF:{slots[Position.DEF]}  MEI:{slots[Position.MID]}  ATA:{slots[Position.ATK]}"
        atk_bar = GG + "█" * int(f.atk_bias() * 5) + RST + DIM + "░" * (5 - int(f.atk_bias() * 5)) + RST
        cur = YY + " ◄" + RST if f == team.formation else ""
        print(f"  {YY}[{i}]{RST} {YY}{f.value:<8}{RST}  {DIM}{desc}{RST}  ATK:[{atk_bar}]{cur}")

    c = input("\n  Escolha formação (ENTER = manter): ").strip()
    if c.isdigit() and 1 <= int(c) <= len(formations):
        team.formation = formations[int(c) - 1]
        print(GG + f"\n  Formação alterada para {team.formation.value}" + RST)

    print(f"\n{C}  POSTURA ATUAL: {RST}{M}{team.postura.value}{RST}\n")
    print(f"  {YY}[1]{RST} Defensivo   {YY}[2]{RST} Equilibrado   {YY}[3]{RST} Ofensivo")
    p = input("  Escolha postura (ENTER = manter): ").strip()
    mapping = {"1": Postura.DEFENSIVO, "2": Postura.EQUILIBRADO, "3": Postura.OFENSIVO}
    if p in mapping:
        team.postura = mapping[p]
        print(GG + f"\n  Postura alterada para {team.postura.value}" + RST)

    pause()
    return team


# ═══════════════════════════════════════════════════════════════
# COPA
# ═══════════════════════════════════════════════════════════════
def show_copa(season: Season, player_team: Team):
    clear()
    print(rule("🏆 COPA DO BRASILEIRÃO"))
    print()
    _print_knockout(season, player_team)
    pause()


def _fit_bracket_team_name(name: str, limit: int = 20) -> str:
    if len(name) <= limit:
        return name
    return name[: limit - 1].rstrip() + "…"


def _team_bg_color(team: Team) -> str:
    return {
        "red": Back.RED,
        "dark_red": Back.RED,
        "green": Back.GREEN,
        "blue": Back.BLUE,
        "yellow": Back.YELLOW,
        "black": Back.BLACK,
        "white": Back.WHITE,
    }.get(getattr(team, "primary_color", "white"), Back.WHITE)


def _team_fg_color(team: Team) -> str:
    return {
        "red": Fore.RED,
        "dark_red": Fore.RED,
        "green": Fore.GREEN,
        "blue": Fore.BLUE,
        "yellow": Fore.YELLOW,
        "black": Fore.BLACK,
        "white": Fore.WHITE,
    }.get(getattr(team, "secondary_color", "white"), Fore.WHITE)


def _paint_team_box(team: Team, text: str) -> str:
    return _team_bg_color(team) + _team_fg_color(team) + Style.BRIGHT + text + RST


def _format_bracket_fixture(team_a: Team, team_b: Team, score: str = "vs") -> str:
    left = _paint_team_box(team_a, pad(_fit_bracket_team_name(team_a.name, 20), 20))
    right = _paint_team_box(team_b, pad(_fit_bracket_team_name(team_b.name, 20), 20))
    return f"{left} {score:^7} {right}"


def _pair_bracket_labels(labels: List[str]) -> List[str]:
    paired = []
    for idx in range(0, len(labels), 2):
        paired.append(f"Venc. {labels[idx]} x Venc. {labels[idx + 1]}")
    return paired


def _print_knockout(season: Season, player_team: Team):
    phases = [
        ("1ª Fase", season.copa_primeira_fase),
        ("Oitavas de Final", season.copa_oitavas),
        ("Quartas de Final", season.copa_quartas),
        ("Semifinal",        season.copa_semi),
    ]
    source_labels = [f"Jogo {idx}" for idx in range(1, 17)]
    for phase_index, (phase_name, ties) in enumerate(phases):
        print(C + f"\n  {phase_name}:" + RST)
        if ties:
            for idx, tie in enumerate(ties, start=1):
                source = source_labels[idx - 1] if idx - 1 < len(source_labels) else ""
                prefix = f"{DIM}{pad(source + ':', 12)}{RST} " if source else ""
                if tie.leg1 and tie.leg2:
                    a, b = tie.aggregate()
                    winner = tie.winner()
                    winner_name = _paint_team_box(winner, _fit_bracket_team_name(winner.name, 20)) if winner else YY + "Pênaltis" + RST
                    fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{a}x{b}")
                    print(
                        f"  {prefix}{WW}{fixture}{RST}  "
                        f"[ida {tie.leg1.home_goals}x{tie.leg1.away_goals} / volta {tie.leg2.home_goals}x{tie.leg2.away_goals}]  → {winner_name}"
                    )
                elif tie.leg1:
                    fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{tie.leg1.home_goals}x{tie.leg1.away_goals}")
                    print(
                        f"  {prefix}{WW}{fixture}{RST}  [ida]"
                    )
                else:
                    label = "final" if tie.single_leg else "ida/volta"
                    print(f"  {prefix}{DIM}{_format_bracket_fixture(tie.team_a, tie.team_b)}  ({label}){RST}")
            source_labels = _pair_bracket_labels(source_labels) if phase_index == 0 else [f"Chave {idx}" for idx in range(1, len(ties) + 1)]
        elif source_labels:
            for label in source_labels:
                print(f"  {DIM}{label}{RST}")
            if len(source_labels) > 1:
                source_labels = [f"Chave {idx}" for idx in range(1, (len(source_labels) // 2) + 1)]
            else:
                source_labels = []

    if season.copa_final:
        print(C + "\n  Final:" + RST)
        tie = season.copa_final
        if tie.leg1:
            winner = season.copa_champion or tie.winner()
            winner_name = _paint_team_box(winner, _fit_bracket_team_name(winner.name, 20)) if winner else YY + "Pênaltis" + RST
            fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{tie.leg1.home_goals}x{tie.leg1.away_goals}")
            print(
                f"  {WW}{fixture}{RST}  → {winner_name}"
            )
        else:
            print(f"  {DIM}{_format_bracket_fixture(tie.team_a, tie.team_b)}  (jogo único){RST}")
    elif source_labels:
        print(C + "\n  Final:" + RST)
        final_label = source_labels[0] if len(source_labels) == 1 else f"Venc. {source_labels[0]} x Venc. {source_labels[1]}"
        print(f"  {DIM}{final_label}  (jogo único){RST}")

    if season.copa_champion:
        champ = season.copa_champion
        print()
        print(box([
            "",
            YY + f"  🏆 CAMPEÃO: {champ.name} 🏆  " + RST,
            "",
        ], border_color=YY, title_color=YY, width=50))


def _print_side_by_side(left: str, right: str, gap: int = 1):
    left_lines  = left.split("\n")
    right_lines = right.split("\n")
    max_lines   = max(len(left_lines), len(right_lines))
    lw = max((_visible_len(l) for l in left_lines), default=0)
    for i in range(max_lines):
        l = left_lines[i]  if i < len(left_lines)  else ""
        r = right_lines[i] if i < len(right_lines) else ""
        l_pad = lw - _visible_len(l)
        print(l + " " * (l_pad + gap) + r)


# ═══════════════════════════════════════════════════════════════
# FINANÇAS
# ═══════════════════════════════════════════════════════════════
def show_finances(team: Team):
    clear()
    print(rule(f"EXTRATO BANCÁRIO — {team.name}"))
    folha = sum(p.salario for p in team.players)
    team.salario_mensal = folha

    lines = [
        "",
        WW + f"  {'CAIXA ATUAL':.<28}" + RST + YY + f"  R${team.caixa:>10,} mil" + RST,
        WW + f"  {'FOLHA SALARIAL':.<28}" + RST + RR + f"  R${folha:>10,} mil/mês" + RST,
        WW + f"  {'MANUTENÇÃO ESTÁDIO':.<28}" + RST + RR + f"  R${200:>10,} mil/mês" + RST,
        DIM + h * 46 + RST,
        WW + f"  {'TORCIDA':.<28}" + RST + G  + f"  {fmt_fans(team.torcida):>12}" + RST,
        WW + f"  {'PRESTÍGIO':.<28}" + RST + C  + f"  {team.prestige:>11}/100" + RST,
        "",
        C + "  TOP 5 SALÁRIOS DO ELENCO:" + RST,
    ]
    top5 = sorted(team.players, key=lambda p: -p.salario)[:5]
    for p in top5:
        bar = GG + "█" * min(int(p.salario / 400), 18) + RST + DIM + "░" * (18 - min(int(p.salario / 400), 18)) + RST
        lines.append(f"  {WW}{pad(p.name, 22)}{RST}  {Y}R${p.salario:,}k{RST}  {bar}")
    lines.append("")

    print(box(lines, title="FINANÇAS", border_color=YY, title_color=YY, width=60))
    pause()


# ═══════════════════════════════════════════════════════════════
# TORCIDA
# ═══════════════════════════════════════════════════════════════
def show_torcida(team: Team):
    clear()
    print(rule(f"👥 TORCIDA — {team.name}"))
    torcida = team.torcida
    bar_len = min(int(torcida / 1_500_000), 20)
    fans_bar = GG + "█" * bar_len + RST + DIM + "░" * (20 - bar_len) + RST

    rank = ("Top 3 do Brasil" if torcida > 15_000_000 else
            "Top 10 do Brasil" if torcida > 5_000_000 else "Regional")

    renda = int(torcida * RENDA_TORCIDA_FACTOR * team.prestige / 80)
    lines = [
        "",
        WW + f"  Clube:       {GG}{team.name}{RST}",
        WW + f"  Torcida:     {GG}{torcida:,}{RST}" + WW + " torcedores" + RST,
        f"  Engajamento: [{fans_bar}]",
        "",
        WW + f"  Ranking:     {C}{rank}{RST}",
        WW + f"  Cap. Estádio:{DIM} aprox. {fmt_fans(team.stadium_capacity)}{RST}",
        WW + f"  Suporte/jogo:{DIM} ~{fmt_fans(int(torcida * 0.0003))}{RST}",
        "",
        WW + f"  Prestígio:   {C}{team.prestige}/100{RST}",
        WW + f"  Renda/jogo:  {Y}R${renda:,} mil{RST}",
        "",
    ]
    print(box(lines, title="INFORMAÇÕES DA TORCIDA", border_color=G, title_color=GG, width=50))
    pause()


# ═══════════════════════════════════════════════════════════════
# ESTÁDIO
# ═══════════════════════════════════════════════════════════════
def show_stadium(team: Team):
    clear()
    print(rule(f"🏟  ESTÁDIO — {team.stadium}"))
    capacidade = team.stadium_capacity
    renda = int(team.torcida * RENDA_TORCIDA_FACTOR * team.prestige / 80)
    lines = [
        "",
        WW + f"  Nome:          {WW}{team.stadium}{RST}",
        WW + f"  Cidade:        {C}{team.city}/{team.state}{RST}",
        WW + f"  Capacidade:    {G}{fmt_fans(capacidade)}{RST}",
        WW + f"  Manutenção:    {RR}R$200 mil/mês{RST}",
        "",
        C + "  RECEITAS ESTIMADAS:" + RST,
        WW + f"  Bilheteria/jogo: {Y}R${renda:,} mil{RST}",
        DIM + f"  (Baseado em ~{int(capacidade*0.65):,} ingressos a R${int(renda*1000/max(capacidade*0.65,1))}/un.)" + RST,
        "",
        WW + f"  Custo anual:     {RR}R${200 * 12:,} mil{RST}",
        "",
    ]
    print(box(lines, title="ESTÁDIO", border_color=C, title_color=C, width=52))
    pause()


# ═══════════════════════════════════════════════════════════════
# MERCADO DE TRANSFERÊNCIAS
# ═══════════════════════════════════════════════════════════════
def show_transfer_market(market, player_team: Team):
    clear()
    if not market.auctions:
        print(rule("🔄 MERCADO DE TRANSFERÊNCIAS"))
        print(DIM + "\n  Nenhum jogador no mercado nesta rodada.\n" + RST)
        pause()
        return

    index = 0
    total = len(market.auctions)

    while True:
        clear()
        print(rule("🔄 MERCADO DE TRANSFERÊNCIAS"))
        print()

        auction = market.auctions[index]
        p = auction.player
        bidder = auction.current_bidder.short_name if auction.current_bidder else "—"
        lines = [
            "",
            f"  {ovr_color(p.overall)}OVR {p.overall}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  "
            f"{DIM}{p.nationality}{RST}",
            f"  Origem: {C}{auction.origin_team.short_name}{RST}  │  "
            f"Lance base: {Y}R${auction.base_bid:,}k{RST}  │  "
            f"Lance atual: {GG}R${auction.current_bid:,}k{RST}  │  "
            f"Líder: {M}{bidder}{RST}",
            f"  Salário: {RR}R${p.salario:,}k/mês{RST}  │  VM: {C}R${p.valor_mercado:,}k{RST}",
            "",
        ]
        print(box(lines, title=f"LOTE {index + 1} DE {total}", border_color=YY, title_color=YY, width=72))
        print(f"\n  Caixa disponível: {Y}{fmt_money(player_team.caixa)}{RST}")
        print(f"  Digite o valor do lance e pressione ENTER para ofertar.")
        print(f"  ENTER vazio avança para o próximo jogador.  {YY}[0]{RST} sai do mercado.")
        c = input(f"  Valor da proposta (> R${auction.current_bid:,}k): ").strip().replace(".", "").replace(",", "")

        if c == "0":
            break
        if c == "":
            index = (index + 1) % total
            continue

        try:
            valor = int(c)
            from transfers import player_bid
            ok, msg = player_bid(market, index, player_team, valor)
            print((GG if ok else RR) + f"  {msg}" + RST)
        except ValueError:
            print(RR + "  Valor inválido." + RST)
        pause()
        index = (index + 1) % total


# ═══════════════════════════════════════════════════════════════
# ARTILHEIROS
# ═══════════════════════════════════════════════════════════════
def show_top_scorers(season: Season):
    clear()
    print(rule("⚽ ARTILHEIROS DA TEMPORADA"))
    print()
    all_players = [(t, p) for t in season.all_teams for p in t.players]
    top = sorted(all_players, key=lambda x: -x[1].gols_temp)[:20]

    tbl = Table(title="ARTILHEIROS", border_color=C, header_color=YY, title_color=C)
    tbl.add_column("Pos",  width=4,  align="r", color=DIM)
    tbl.add_column("Nome", width=22, align="l", color=WW)
    tbl.add_column("Time", width=6,  align="c", color=C)
    tbl.add_column("Pos.", width=5,  align="c", color=DIM)
    tbl.add_column("G",    width=4,  align="c", color=GG)
    tbl.add_column("A",    width=4,  align="c", color=G)
    tbl.add_column("J",    width=4,  align="c", color=DIM)

    for i, (team, p) in enumerate(top, 1):
        tbl.add_row(
            str(i), WW + p.name + RST, C + team.short_name + RST,
            p.pos_label(),
            GG + str(p.gols_temp) + RST,
            G  + str(p.assist_temp) + RST,
            str(p.partidas_temp),
        )
    tbl.print()
    pause()


def show_notifications(messages: List[str], title: str = "NOTIFICAÇÕES"):
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


def prompt_job_offer(coach_name: str, team: Team) -> bool:
    clear()
    print(rule("PROPOSTA DE EMPREGO"))
    lines = [
        "",
        f"  {WW}{coach_name}{RST}, o {GG}{team.name}{RST} quer contratar você.",
        f"  Divisão: {C}{team.division}{RST}  │  Prestígio: {YY}{team.prestige}{RST}",
        f"  Cidade: {WW}{team.city}/{team.state}{RST}",
        "",
        f"  {YY}[1]{RST} Aceitar proposta",
        f"  {YY}[0]{RST} Recusar",
        "",
    ]
    print(box(lines, title="MERCADO DE TREINADORES", border_color=GG, title_color=GG, width=68))
    return input("  Escolha: ").strip() == "1"


# ═══════════════════════════════════════════════════════════════
# FIM DE TEMPORADA
# ═══════════════════════════════════════════════════════════════
def show_season_end(season: Season, player_team: Team):
    clear()
    w = term_width()
    print(GG + TL + H * (w - 2) + TR + RST)
    title = YY + f"  FIM DA TEMPORADA {season.year}  " + RST
    print(GG + V + RST + pad(title, w - 2, "c") + GG + V + RST)
    print(GG + BL + H * (w - 2) + BR + RST)
    print()

    div = player_team.division
    div_teams = [t for t in season.all_teams if t.division == div]
    ranked = sort_standings(div_teams)
    pos = next((i + 1 for i, t in enumerate(ranked) if t.id == player_team.id), 0)

    if pos <= 2 and div > 1:
        print(GG + f"  🎉 PROMOVIDO! {player_team.name} subiu para a Divisão {div-1}!" + RST)
    elif pos >= len(ranked) - 1 and div < 4:
        print(RR + f"  😢 REBAIXADO. {player_team.name} foi para a Divisão {div+1}." + RST)
    else:
        print(WW + f"  {player_team.name} terminou em {pos}º lugar na Divisão {div}." + RST)

    if season.copa_champion:
        if season.copa_champion.id == player_team.id:
            print(YY + "  🏆 CAMPEÃO DA COPA DO BRASILEIRÃO! 🏆" + RST)
        else:
            print(WW + f"  Copa: Campeão — {YY}{season.copa_champion.name}{RST}")

    if season.top_scorers:
        name, club, goals = season.top_scorers[0]
        print(GG + f"  ⚽ Artilheiro: {name} ({club}) — {goals} gols" + RST)
    print()
    pause()


# ═══════════════════════════════════════════════════════════════
# CONFIRM PLAY
# ═══════════════════════════════════════════════════════════════
def confirm_play(formation: Formation, postura: Postura) -> bool:
    print(box([
        "",
        f"  Formação: {YY}{formation.value}{RST}   Postura: {M}{postura.value}{RST}",
        "",
        f"  {WW}Confirma para jogar?{RST}  {YY}[1]{RST} Sim   {YY}[2]{RST} Ajustar",
        "",
    ], title="CONFIRMAÇÃO", border_color=YY, title_color=YY, width=50))
    c = input("  Escolha: ").strip()
    return c != "2"


# ═══════════════════════════════════════════════════════════════
# CRÉDITOS
# ═══════════════════════════════════════════════════════════════
def show_credits():
    clear()
    lines = [
        "",
        C  + "  ClassicFoot — Brasileirão Edition" + RST,
        "",
        WW + "  Inspirado no clássico " + YY + "Elifoot 2" + RST,
        "",
        DIM + "  Desenvolvido com Python + Colorama" + RST,
        "",
        WW + "  Times e jogadores da Série A e B" + RST,
        WW + "  Temporada 2024/2025" + RST,
        "",
    ]
    print(box(lines, title="CRÉDITOS", border_color=GG, title_color=GG, width=44))
    pause()
