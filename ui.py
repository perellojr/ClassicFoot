"""
ClassicFoot - Interface visual estilo Elifoot 2
Terminal colorido com colorama + box-drawing characters
"""
import time
from typing import List, Optional
from colorama import Back, Fore, Style
from models import Team, Player, Position, Formation, Postura, MatchResult, CupTie, RENDA_TORCIDA_FACTOR
from season import (
    Season, sort_standings, take_loan, settle_loan, monthly_sponsorship,
    CUSTO_MANUTENCAO, stadium_maintenance_cost, PRIZE_LIGA, PRIZE_COPA,
)
from transfers import sale_price
from term import (
    clear, pause, rule, box, Table, fmt_fans, fmt_money,
    ovr_color, form_color, cond_color, colored_score,
    GG, YY, Y, C, BB, RR, R, WW, W, M, DIM, RST, G,
    term_width, pad, _visible_len, _clip_visible, hline,
    is_msdos_mode,
    TL, TR, BL, BR, H, V, ML, MR, TM, BM, X,
    tl, tr, bl, br, h, v, ml, mr,
    paint_team,
)


def _ovr_text(value: float) -> str:
    return str(int(round(value)))


def _ellipsize_visible(text: str, max_visible: int) -> str:
    if max_visible <= 0:
        return ""
    if _visible_len(text) <= max_visible:
        return text
    if max_visible <= 3:
        return "." * max_visible
    return _clip_visible(text, max_visible - 3) + "..."


# ═══════════════════════════════════════════════════════════════
# BANNER
# ═══════════════════════════════════════════════════════════════
def banner():
    clear()
    if is_msdos_mode():
        logo_lines = [
            "  #####   #        #    ####   ####  #  ####   ####  #####  ###   ###  ##### ",
            " #       # #      # #  #      #      # #      #      #     #   # #   #   #   ",
            " #      #####    #####  ###    ###   # #      ####   ###   #   # #   #   #   ",
            " #      #   #    #   #     #      #  # #      #      #     #   # #   #   #   ",
            "  ##### #   #    #   # ####   ####   #  ####   ####  #      ###   ###    #   ",
        ]
    else:
        logo_lines = [
            "  ██████╗██╗      █████╗ ███████╗███████╗██╗ ██████╗    ███████╗ ██████╗  ██████╗ ████████╗",
            " ██╔════╝██║     ██╔══██╗██╔════╝██╔════╝██║██╔════╝    ██╔════╝██╔═══██╗██╔═══██╗╚══██╔══╝",
            " ██║     ██║     ███████║███████╗███████╗██║██║         █████╗  ██║   ██║██║   ██║   ██║   ",
            " ██║     ██║     ██╔══██║╚════██║╚════██║██║██║         ██╔══╝  ██║   ██║██║   ██║   ██║   ",
            " ╚██████╗███████╗██║  ██║███████║███████╗██║╚██████╗    ██║     ╚██████╔╝╚██████╔╝   ██║   ",
            "  ╚═════╝╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝    ╚═╝      ╚═════╝  ╚═════╝    ╚═╝  ",
        ]
    w = term_width()
    print(GG + TL + H * (w - 2) + TR + RST)
    for line in logo_lines:
        vis = _visible_len(line)
        pad_l = (w - 2 - vis) // 2
        print(GG + V + RST + " " * pad_l + GG + line + RST + " " * max(0, w - 2 - vis - pad_l) + GG + V + RST)
    sub = "Brasileirao Edition  -  v0.9" if is_msdos_mode() else "Brasileirão Edition  •  v0.9"
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

    # ── Monta menu lateral (col esquerda, ~30 chars) ──────────
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

    # ── Monta elenco (col direita) ─────────────────────────────
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

    squad_lines = [squad_header, C + "─" * 70 + RST]
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

    # Mantém largura estável da coluna lateral e evita quebra com valores gigantes.
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
            _ovr_text(player.overall),
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


def show_training(team: Team):
    """Seleciona até 5 jogadores para treino da rodada."""
    clear()
    print(rule(f"TREINO DA RODADA — {team.name}"))
    print()

    players = sorted(team.players, key=lambda p: (-p.overall, p.name))
    selected_ids = set(team.training_targets or [])

    tbl = Table(title="ELENCO (ATÉ 5 JOGADORES)", border_color=C, header_color=YY, title_color=C)
    tbl.add_column("N", width=4, align="r", color=DIM)
    tbl.add_column("Nome", width=24, align="l", color=WW)
    tbl.add_column("Pos", width=5, align="c", color=C)
    tbl.add_column("OVR", width=5, align="c", color=YY)
    tbl.add_column("Craque", width=8, align="c", color=G)
    tbl.add_column("Treino", width=8, align="c", color=M)

    for idx, player in enumerate(players, start=1):
        tbl.add_row(
            str(idx),
            player.name[:24],
            player.pos_label(),
            _ovr_text(player.overall),
            "SIM" if getattr(player, "is_star", False) else "-",
            "ATIVO" if player.id in selected_ids else "",
        )
    tbl.print()

    print()
    print(DIM + "  Informe números separados por vírgula. ENTER mantém a lista atual." + RST)
    raw = input("  Seleção (máx 5): ").strip()
    if not raw:
        return team

    tokens = [token.strip() for token in raw.replace(";", ",").split(",") if token.strip()]
    picks = []
    for token in tokens:
        if not token.isdigit():
            continue
        index = int(token)
        if 1 <= index <= len(players):
            player_id = players[index - 1].id
            if player_id not in picks:
                picks.append(player_id)
        if len(picks) >= 5:
            break

    team.training_targets = picks
    return team


def manage_player_sales(team: Team, market):
    """Tela contínua para listar jogadores em leilão até o usuário sair."""
    clear()
    while True:
        clear()
        print(rule(f"VENDER JOGADOR — {team.name}"))
        print()

        if len(team.players) <= 16:
            print(DIM + "\n  Elenco mínimo atingido (16 jogadores). Venda bloqueada.\n" + RST)
            pause()
            return

        available = [p for p in team.players if p.contrato_rodadas == 0 and not market.has_player_in_auction(p)]
        available.sort(key=lambda player: (player.overall, player.name))

        if not available:
            print(DIM + "\n  Nenhum jogador elegível para novo leilão neste momento.\n" + RST)
            print(DIM + "  Dica: jogadores já listados não aparecem novamente até o leilão encerrar." + RST)
            print()
            cmd = input("  [0] sair: ").strip()
            if cmd == "0" or cmd == "":
                return
            continue

        tbl = Table(title="JOGADORES DISPONÍVEIS", border_color=C, header_color=YY, title_color=C)
        tbl.add_column("N", width=4, align="r", color=DIM)
        tbl.add_column("Nome", width=22, align="l", color=WW)
        tbl.add_column("★", width=3, align="c", color=M)
        tbl.add_column("Pos", width=5, align="c", color=C)
        tbl.add_column("OVR", width=5, align="c", color=YY)
        tbl.add_column("J", width=4, align="c", color=DIM)
        tbl.add_column("G", width=4, align="c", color=G)
        tbl.add_column("Lance Min", width=14, align="r", color=Y)

        for idx, player in enumerate(available, start=1):
            asking_price = sale_price(player)
            tbl.add_row(
                str(idx),
                player.name[:22],
                "*" if getattr(player, "is_star", False) else "-",
                player.pos_label(),
                _ovr_text(player.overall),
                str(player.partidas_total),
                str(player.gols_total),
                f"R${asking_price:,}k",
            )
        tbl.print()

        choice = input("\n  Jogador para listar no leilão ([0] sair): ").strip()
        if choice == "0" or choice == "":
            return
        if not choice.isdigit() or int(choice) not in range(1, len(available) + 1):
            print(RR + "\n  Jogador inválido." + RST)
            pause()
            continue

        player = available[int(choice) - 1]
        minimum_bid = sale_price(player)
        confirm = input(f"\n  Listar {player.name} no leilão com mínimo de R${minimum_bid:,}k? [S/N]: ").strip().upper()
        if confirm != "S":
            print(YY + "\n  Ação cancelada." + RST)
            pause()
            continue

        ok, message = market.list_player_for_auction(team, player, min_bid=minimum_bid)
        print((GG if ok else RR) + f"\n  {message}" + RST)
        pause()


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
        # Escalação provável segue os melhores por posição por OVR.
        return float(player.overall)

    if team.formation == Formation.BEST11:
        gks = [p for p in available if p.position == Position.GK]
        gks.sort(key=player_score, reverse=True)
        if gks:
            lineup.append(gks[0])
            used_ids.add(gks[0].id)
        leftovers = [p for p in available if p.id not in used_ids and p.position != Position.GK]
        leftovers.sort(key=player_score, reverse=True)
        for player in leftovers[: 11 - len(lineup)]:
            lineup.append(player)
            used_ids.add(player.id)
        position_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
        return sorted(lineup, key=lambda p: (position_order.get(p.position, 9), -player_score(p), p.name))

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
        for player in leftovers:
            if player.position == Position.GK and any(p.position == Position.GK for p in lineup):
                continue
            lineup.append(player)
            used_ids.add(player.id)
            if len(lineup) >= 11:
                break

    position_order = {Position.GK: 0, Position.DEF: 1, Position.MID: 2, Position.ATK: 3}
    return sorted(lineup, key=lambda p: (position_order.get(p.position, 9), -player_score(p), p.name))


def _formation_fit_ovr(team: Team, formation: Formation) -> float:
    original = team.formation
    team.formation = formation
    lineup = _pick_probable_lineup(team)
    team.formation = original
    if not lineup:
        return 0.0
    avg = sum(player.overall for player in lineup) / len(lineup)
    fit = avg * (formation.atk_bias() + formation.def_bias()) / 2
    return round(fit, 1)


def _can_use_formation(team: Team, formation: Formation) -> bool:
    if len(team.players) < 11:
        return False
    if formation == Formation.BEST11:
        return sum(1 for p in team.players if p.position == Position.GK) >= 1
    slots = formation.slots()
    for position in [Position.GK, Position.DEF, Position.MID, Position.ATK]:
        required = slots.get(position, 0)
        have = sum(1 for p in team.players if p.position == position)
        if have < required:
            return False
    return True


def _postura_fit_ovr(base_ovr: float, postura: Postura) -> float:
    atk_mod, def_mod = postura.modifiers()
    return round(base_ovr * ((atk_mod + def_mod) / 2), 1)


def _find_player_next_match(season: Season, player_team: Team):
    for matchday in season.calendar[season.current_matchday:]:
        for fixture in matchday.get("fixtures", []):
            if fixture.home_team.id == player_team.id or fixture.away_team.id == player_team.id:
                return matchday, fixture, None
        for tie in (matchday.get("ties") or []):
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
            f"{YY}{_ovr_text(player.overall):>2}{RST}"
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


def show_standings(season: Season, player_team: Team | None, division: int = 0):
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
            # Critério de coloração por divisão
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

            # Destaca o time do jogador se aplicável
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

        division_tables[current_division] = box(lines, title=f"{current_division}ª DIVISÃO", border_color=C, title_color=GG, width=50)

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


def show_calendar(season: Season, player_team: Team | None):
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

    # Exibe todo o calendário em uma única tela, em duas colunas.
    left_col = blocks[::2]
    right_col = blocks[1::2]
    left_lines = []
    right_lines = []
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
        if f == Formation.BEST11:
            desc = "GOL:1 + 10 melhores OVR"
        else:
            desc = f"DEF:{slots[Position.DEF]}  MEI:{slots[Position.MID]}  ATA:{slots[Position.ATK]}"
        atk_bar = GG + "█" * int(f.atk_bias() * 5) + RST + DIM + "░" * (5 - int(f.atk_bias() * 5)) + RST
        fit_ovr = _formation_fit_ovr(team, f)
        cur = YY + " ◄" + RST if f == team.formation else ""
        enabled = _can_use_formation(team, f)
        label_color = YY if enabled else DIM
        lock = RR + " [indisponível]" + RST if not enabled else ""
        print(f"  {YY}[{i}]{RST} {label_color}{f.value:<8}{RST}  {DIM}{desc}{RST}  OVR:{YY}{_ovr_text(fit_ovr):>3}{RST}  ATK:[{atk_bar}]{cur}{lock}")

    c = input("\n  Escolha formação (ENTER = manter): ").strip()
    if c.isdigit() and 1 <= int(c) <= len(formations):
        selected = formations[int(c) - 1]
        if _can_use_formation(team, selected):
            team.formation = selected
            print(GG + f"\n  Formação alterada para {team.formation.value}" + RST)
        else:
            print(RR + "\n  Não há jogadores suficientes por posição para essa formação." + RST)

    base_ovr = _formation_fit_ovr(team, team.formation)
    print()
    print(C + "  IMPACTO DA POSTURA (OVR):" + RST)
    for postura in [Postura.DEFENSIVO, Postura.EQUILIBRADO, Postura.OFENSIVO]:
        simulated = _postura_fit_ovr(base_ovr, postura)
        marker = YY + " ◄ atual" + RST if postura == team.postura else ""
        print(f"  {WW}{postura.value:<12}{RST} → {YY}{_ovr_text(simulated)}{RST}{marker}")

    print()
    print(_render_probable_lineup(team))
    print(f"\n{C}  POSTURA ATUAL: {RST}{M}{team.postura.value}{RST}\n")
    print(f"  {YY}[1]{RST} Defensivo   {YY}[2]{RST} Equilibrado   {YY}[3]{RST} Ofensivo")
    p = input("  Escolha postura (ENTER = manter): ").strip()
    mapping = {"1": Postura.DEFENSIVO, "2": Postura.EQUILIBRADO, "3": Postura.OFENSIVO}
    if p in mapping:
        team.postura = mapping[p]
        print(GG + f"\n  Postura alterada para {team.postura.value}" + RST)

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


def show_copa_draw(phase_title: str, ties: List[CupTie], all_teams: List[Team]):
    """Exibe o sorteio da fase da Copa de forma progressiva."""
    if not ties:
        return

    participants = []
    seen_ids = set()
    for tie in ties:
        for team in (tie.team_a, tie.team_b):
            if team.id in seen_ids:
                continue
            seen_ids.add(team.id)
            participants.append(team)

    remaining = list(participants)
    # slots[i] = [team_a|None, team_b|None]
    slots: list[list[Team | None]] = [[None, None] for _ in ties]

    def _remove_remaining(team: Team):
        for idx, item in enumerate(remaining):
            if item.id == team.id:
                remaining.pop(idx)
                return

    def _division_pool_lines() -> List[str]:
        lines: List[str] = []
        grouped = {1: [], 2: [], 3: [], 4: []}
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
        # Sorteia um time por vez no confronto para ficar visualmente progressivo.
        slots[idx][0] = tie.team_a
        _remove_remaining(tie.team_a)
        clear()
        print(rule("🎲 SORTEIO DA COPA"))
        print()
        top_box = box(_top_draw_lines(), title=f"SORTEIO — {phase_title}", border_color=YY, title_color=YY, width=112)
        pool_box = box(_division_pool_lines(), title="TIMES RESTANTES (POR DIVISÃO)", border_color=C, title_color=C, width=112)
        print(top_box)
        print()
        print(pool_box)
        time.sleep(0.35)

        slots[idx][1] = tie.team_b
        _remove_remaining(tie.team_b)
        clear()
        print(rule("🎲 SORTEIO DA COPA"))
        print()
        top_box = box(_top_draw_lines(), title=f"SORTEIO — {phase_title}", border_color=YY, title_color=YY, width=112)
        pool_box = box(_division_pool_lines(), title="TIMES RESTANTES (POR DIVISÃO)", border_color=C, title_color=C, width=112)
        print(top_box)
        print()
        print(pool_box)
        time.sleep(0.45)

    clear()
    print(rule("🎲 SORTEIO DA COPA"))
    print()
    print(GG + f"  ✓ Sorteio da fase {phase_title} concluído." + RST)
    time.sleep(0.55)


def _fit_bracket_team_name(name: str, limit: int = 20) -> str:
    if len(name) <= limit:
        return name
    return name[: limit - 1].rstrip() + "…"


def _paint_team_box(team: Team, text: str) -> str:
    """Alias para paint_team centralizado em term.py."""
    return paint_team(team, text)


def _format_bracket_fixture(team_a: Team, team_b: Team, score: str = "vs") -> str:
    left = _paint_team_box(team_a, pad(_fit_bracket_team_name(team_a.name, 20), 20))
    right = _paint_team_box(team_b, pad(_fit_bracket_team_name(team_b.name, 20), 20))
    return f"{left} {score:^7} {right}"


def _pair_bracket_labels(labels: List[str]) -> List[str]:
    paired = []
    for idx in range(0, len(labels), 2):
        paired.append(f"Venc. {labels[idx]} x Venc. {labels[idx + 1]}")
    return paired


def _print_knockout(season: Season, player_team: Team | None):
    phases = [
        ("1ª Fase", season.copa_primeira_fase, 1, 16),
        ("Oitavas de Final", season.copa_oitavas, 17, 8),
        ("Quartas de Final", season.copa_quartas, 25, 4),
        ("Semifinal",        season.copa_semi, 29, 2),
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
                    winner_name = _paint_team_box(winner, _fit_bracket_team_name(winner.name, 20)) if winner else YY + "Pênaltis" + RST
                    fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{a}x{b}")
                    pens = ""
                    if tie.penalty_score:
                        pens = f"  [pên. {tie.penalty_score[0]}x{tie.penalty_score[1]}]"
                    print(
                        f"  {prefix}{WW}{fixture}{RST}  "
                        f"[ida {tie.leg1.home_goals}x{tie.leg1.away_goals} / volta {tie.leg2.home_goals}x{tie.leg2.away_goals}]{pens}  → {winner_name}"
                    )
                elif tie.leg1:
                    fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{tie.leg1.home_goals}x{tie.leg1.away_goals}")
                    print(
                        f"  {prefix}{WW}{fixture}{RST}  [ida]"
                    )
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
            winner_name = _paint_team_box(winner, _fit_bracket_team_name(winner.name, 20)) if winner else YY + "Pênaltis" + RST
            a, b = tie.aggregate()
            fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{a}x{b}")
            pens = f"  [pên. {tie.penalty_score[0]}x{tie.penalty_score[1]}]" if tie.penalty_score else ""
            print(
                f"  {DIM}Jogo 31/32:{RST} {WW}{fixture}{RST}  [ida {tie.leg1.home_goals}x{tie.leg1.away_goals} / volta {tie.leg2.home_goals}x{tie.leg2.away_goals}]{pens}  → {winner_name}"
            )
        elif tie.leg1:
            fixture = _format_bracket_fixture(tie.team_a, tie.team_b, f"{tie.leg1.home_goals}x{tie.leg1.away_goals}")
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


# ═══════════════════════════════════════════════════════════════
# FINANÇAS
# ═══════════════════════════════════════════════════════════════
def _annual_budget_forecast(team: Team, season: Season | None):
    """Previsão simples de caixa até o fim da temporada."""
    if season is None:
        return None

    remaining_rounds = max(0, len(season.calendar) - season.current_matchday)
    months_left = max(0, (remaining_rounds + 3) // 4)

    sponsor_monthly = monthly_sponsorship(team)
    monthly_expenses = sum(player.salario for player in team.players) + CUSTO_MANUTENCAO + team.loan_monthly_payment
    projected_expenses = monthly_expenses * months_left

    # Receita esperada: estimativa conservadora de bilheteria por jogos em casa restantes.
    # Aproxima por metade dos jogos da liga restantes para o clube.
    home_games_left = 0
    for matchday in season.calendar[season.current_matchday:]:
        for fixture in matchday.get("fixtures", []):
            if fixture.home_team.id == team.id:
                home_games_left += 1
    avg_home_income = int((team.torcida * RENDA_TORCIDA_FACTOR) + (team.prestige * 20))
    projected_income = (home_games_left * avg_home_income) + (sponsor_monthly * months_left)

    projected_final_cash = team.caixa + projected_income - projected_expenses
    return {
        "remaining_rounds": remaining_rounds,
        "months_left": months_left,
        "projected_income": projected_income,
        "projected_expenses": projected_expenses,
        "projected_final_cash": projected_final_cash,
    }


def show_finances(team: Team, season: Season | None = None):
    while True:
        clear()
        print(rule(f"EXTRATO BANCÁRIO — {team.name}"))
        folha = sum(p.salario for p in team.players)
        team.salario_mensal = folha
        forecast = _annual_budget_forecast(team, season)

        lines = [
            "",
            WW + f"  {'CAIXA ATUAL':.<28}" + RST + YY + f"  R${team.caixa:>10,}" + RST,
            WW + f"  {'FOLHA SALARIAL':.<28}" + RST + RR + f"  R${folha:>10,}/mês" + RST,
            WW + f"  {'MANUTENÇÃO ESTÁDIO':.<28}" + RST + RR + f"  R${CUSTO_MANUTENCAO:>10,}/mês" + RST,
            WW + f"  {'PATROCÍNIO MENSAL':.<28}" + RST + GG + f"  R${monthly_sponsorship(team):>10,}/mês" + RST,
            WW + f"  {'SALDO DE EMPRÉSTIMOS':.<28}" + RST + Y + f"  R${team.loan_balance:>10,}" + RST,
            WW + f"  {'PARCELA MENSAL':.<28}" + RST + Y + f"  R${team.loan_monthly_payment:>10,}" + RST,
            DIM + h * 46 + RST,
            WW + f"  {'TORCIDA':.<28}" + RST + G  + f"  {fmt_fans(team.torcida):>12}" + RST,
            WW + f"  {'PRESTÍGIO':.<28}" + RST + C  + f"  {team.prestige:>11}/100" + RST,
            "",
            C + "  TOP 5 SALÁRIOS DO ELENCO:" + RST,
        ]
        top5 = sorted(team.players, key=lambda p: -p.salario)[:5]
        for p in top5:
            bar = GG + "█" * min(int(p.salario / 400), 18) + RST + DIM + "░" * (18 - min(int(p.salario / 400), 18)) + RST
            lines.append(f"  {WW}{pad(p.name, 22)}{RST}  {Y}R${p.salario:,}{RST}  {bar}")
        if forecast:
            lines.extend([
                "",
                C + "  PREVISÃO ORÇAMENTÁRIA (FIM DA TEMPORADA):" + RST,
                WW + f"  {'Rodadas restantes':.<28}" + RST + C + f"  {forecast['remaining_rounds']:>10}" + RST,
                WW + f"  {'Meses restantes':.<28}" + RST + C + f"  {forecast['months_left']:>10}" + RST,
                WW + f"  {'Receitas previstas':.<28}" + RST + G + f"  R${forecast['projected_income']:>10,}" + RST,
                WW + f"  {'Despesas previstas':.<28}" + RST + RR + f"  R${forecast['projected_expenses']:>10,}" + RST,
                WW + f"  {'Caixa projetado':.<28}" + RST + (GG if forecast["projected_final_cash"] >= 0 else RR) + f"  R${forecast['projected_final_cash']:>10,}" + RST,
            ])
        lines.append("")
        lines.append(f"  {YY}[E]{RST} Pegar empréstimo")
        if team.loan_balance > 0:
            lines.append(f"  {YY}[Q]{RST} Quitar empréstimo à vista")
        lines.append("")

        print(box(lines, title="FINANÇAS", border_color=YY, title_color=YY, width=60))
        choice = input("\n  Opção (ENTER para sair): ").strip().upper()
        if choice == "":
            return
        if choice == "E":
            amount = input("  Valor do empréstimo em R$: ").strip().replace(".", "").replace(",", "")
            if amount.isdigit():
                ok, message = take_loan(team, int(amount))
                print((GG if ok else RR) + f"\n  {message}" + RST)
            else:
                print(RR + "\n  Valor inválido." + RST)
            pause()
            continue
        if choice == "Q":
            ok, message = settle_loan(team)
            print((GG if ok else RR) + f"\n  {message}" + RST)
            pause()
            continue
        print(YY + "\n  Opção inválida." + RST)
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
    while True:
        clear()
        print(rule(f"🏟  ESTÁDIO — {team.stadium}"))
        renda = int(team.torcida * RENDA_TORCIDA_FACTOR * team.prestige / 80)

        current_capacity = team.stadium_capacity
        maintenance = stadium_maintenance_cost(team)

        lines = [
            "",
            WW + f"  Nome:          {WW}{team.stadium}{RST}",
            WW + f"  Cidade:        {C}{team.city}/{team.state}{RST}",
            WW + f"  Nível:         {YY}{team.stadium_level}/5{RST}",
            WW + f"  Capacidade:    {G}{fmt_fans(current_capacity)}{RST}",
            WW + f"  Manutenção:    {RR}R${maintenance} mil/ciclo{RST}",
            "",
            C + "  RECEITAS ESTIMADAS:" + RST,
            WW + f"  Bilheteria/jogo: {Y}R${renda:,} mil{RST}",
            DIM + f"  (Baseado em ~{int(current_capacity*0.65):,} ingressos a R${int(renda*1000/max(current_capacity*0.65,1))}/un.)" + RST,
            "",
            WW + f"  Custo/temporada: {RR}R${maintenance * 3:,} mil{RST}",
            "",
        ]

        if team.stadium_level < 5:
            next_level = team.stadium_level + 1
            upgrade_cost = team.stadium_level * 5_000
            next_capacity = min(80_000, current_capacity + 5_000)
            lines.append(C + "  UPGRADE DISPONÍVEL:" + RST)
            lines.append(WW + f"  Próx. nível:    {YY}{next_level}/5{RST}")
            lines.append(WW + f"  Nova capacidade: {G}{fmt_fans(next_capacity)}{RST}")
            lines.append(WW + f"  Custo upgrade:  {Y}R${upgrade_cost} mil{RST}")
            lines.append(WW + f"  Nova manutenção: {RR}R${maintenance + 20} mil/ciclo{RST}")
            lines.append("")
            lines.append(f"  {YY}[U]{RST} Fazer upgrade")
        else:
            lines.append(C + "  Estádio no nível máximo" + RST)
            lines.append("")

        print(box(lines, title="ESTÁDIO", border_color=C, title_color=C, width=60))
        if team.stadium_level >= 5:
            pause()
            return
        choice = input("\n  Opção (ENTER para sair): ").strip().upper()
        if choice == "":
            return
        if choice == "U":
            upgrade_cost = team.stadium_level * 5_000
            if team.caixa >= upgrade_cost:
                team.caixa -= upgrade_cost
                team.stadium_level += 1
                print(GG + f"\n  Estádio atualizado para nível {team.stadium_level}!" + RST)
            else:
                print(RR + f"\n  Caixa insuficiente (R${team.caixa} mil disponíveis, necessários R${upgrade_cost} mil)" + RST)
            pause()
            continue
        print(YY + "\n  Opção inválida." + RST)
        pause()


# ═══════════════════════════════════════════════════════════════
# MERCADO DE TRANSFERÊNCIAS
# ═══════════════════════════════════════════════════════════════
def _show_transfer_history(market):
    history = list(getattr(market, "history", []))
    clear()
    print(rule("📜 HISTÓRICO DE TRANSFERÊNCIAS"))
    print()

    if not history:
        print(DIM + "  Nenhuma transferência registrada nesta temporada." + RST)
        print()
        pause()
        return

    page_size = 16
    total_pages = (len(history) + page_size - 1) // page_size
    page = 0
    while True:
        clear()
        print(rule("📜 HISTÓRICO DE TRANSFERÊNCIAS"))
        print(DIM + f"  Página {page + 1}/{total_pages}" + RST)
        print()
        start = page * page_size
        end = start + page_size
        for idx, message in enumerate(history[start:end], start=start + 1):
            print(f"  {YY}{idx:>3}.{RST} {WW}{message}{RST}")
        print()
        cmd = input("  ENTER próxima  |  [V] voltar  |  [0] sair: ").strip().upper()
        if cmd == "0":
            break
        if cmd == "V":
            page = max(0, page - 1)
        else:
            page = (page + 1) % total_pages


def show_auction_results(messages: List[str]):
    if not messages:
        return
    clear()
    print(rule("RESULTADO DOS LEILÕES"))
    print()
    for idx, message in enumerate(messages, start=1):
        print(box(["", f"  {message}", ""], title=f"LEILÃO {idx}", border_color=YY, title_color=YY, width=96))
        print()
    pause()


def show_transfer_market(market, player_team: Team):
    clear()
    if not market.auctions:
        print(rule("MERCADO DE TRANSFERÊNCIAS"))
        print(DIM + "\n  Nenhum jogador no mercado nesta rodada.\n" + RST)
        input("  ENTER para voltar: ")
        return

    visible_auctions = list(market.auctions)

    while visible_auctions:
        clear()
        print(rule("MERCADO DE TRANSFERÊNCIAS"))
        print()

        total = len(visible_auctions)
        auction = visible_auctions[0]
        p = auction.player
        bidder = auction.current_bidder.name if auction.current_bidder else "—"
        market_index = market.auctions.index(auction)
        own_player_auction = auction.origin_team.id == player_team.id
        ovr_value = int(round(p.overall))
        bucket_label = market.ovr_bucket_label(ovr_value)
        avg_bid_hint = market.average_bid_for_ovr(ovr_value)
        avg_line = f"  Referência faixa OVR {bucket_label}: {YY}R${avg_bid_hint:,}k{RST}"

        if player_team.caixa < 0:
            lines = [
                "",
                f"  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  "
                f"{DIM}{p.nationality}{RST}",
                f"  Lance atual: {GG}R${auction.current_bid:,}k{RST}  │  Líder: {M}{bidder}{RST}",
                avg_line,
                "",
                RR + "  Clube com caixa negativo não pode participar de leilões." + RST,
                "",
            ]
            print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=78))
            c = input(f"\n  ENTER próximo  |  {YY}[H]{RST} histórico  |  {YY}[0]{RST} sair: ").strip().upper()
            if c == "0":
                break
            if c == "H":
                _show_transfer_history(market)
                continue
            visible_auctions.pop(0)
            continue

        if own_player_auction:
            lines = [
                "",
                f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  "
                f"{DIM}{p.nationality}{RST}",
                f"  Origem: {C}{auction.origin_team.name}{RST}  │  "
                f"Lance atual: {GG}R${auction.current_bid:,}k{RST}  │  "
                f"Líder: {M}{bidder}{RST}",
                avg_line,
                "",
                YY + "  Jogador do seu clube: lance manual bloqueado" + RST,
                "",
            ]
            print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=84))
            c = input(f"\n  ENTER próximo  |  {YY}[H]{RST} histórico  |  {YY}[0]{RST} sair: ").strip().upper()
            if c == "0":
                break
            if c == "H":
                _show_transfer_history(market)
                continue
            visible_auctions.pop(0)
            continue

        # Verifica se tem caixa para participar
        if player_team.caixa < auction.base_bid:
            lines = [
                "",
                f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  "
                f"{DIM}{p.nationality}{RST}",
                f"  Origem: {C}{auction.origin_team.name}{RST}  │  "
                f"Lance base: {Y}R${auction.base_bid:,}k{RST}",
                avg_line,
                "",
                RR + f"  Saldo insuficiente para participar deste leilão" + RST,
                "",
            ]
            print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=72))
            print(f"\n  Caixa disponível: {Y}{fmt_money(player_team.caixa)}{RST}")
            c = input(f"\n  ENTER próximo  |  {YY}[H]{RST} histórico  |  {YY}[0]{RST} sair: ").strip().upper()
            if c == "0":
                break
            if c == "H":
                _show_transfer_history(market)
                continue
            visible_auctions.pop(0)
            continue

        # Verifica se elenco está cheio
        if len(player_team.players) >= 45:
            lines = [
                "",
                f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  "
                f"{DIM}{p.nationality}{RST}",
                f"  Origem: {C}{auction.origin_team.name}{RST}",
                avg_line,
                "",
                RR + f"  Elenco cheio (45/45)" + RST,
                "",
            ]
            print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=72))
            print(f"\n  Caixa disponível: {Y}{fmt_money(player_team.caixa)}{RST}")
            c = input(f"\n  ENTER próximo  |  {YY}[H]{RST} histórico  |  {YY}[0]{RST} sair: ").strip().upper()
            if c == "0":
                break
            if c == "H":
                _show_transfer_history(market)
                continue
            visible_auctions.pop(0)
            continue

        lines = [
            "",
            f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  "
            f"{DIM}{p.nationality}{RST}",
            f"  Origem: {C}{auction.origin_team.name}{RST}  │  "
            f"Lance base: {Y}R${auction.base_bid:,}k{RST}  │  "
            f"Lance atual: {GG}R${auction.current_bid:,}k{RST}  │  "
            f"Líder: {M}{bidder}{RST}",
            f"  Salário: {RR}R${p.salario:,}k/mês{RST}  │  VM: {C}R${p.valor_mercado:,}k{RST}",
            avg_line,
            "",
        ]
        print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=72))
        print(f"\n  Caixa disponível: {Y}{fmt_money(player_team.caixa)}{RST}")
        print(f"  Digite o valor do lance e pressione ENTER para ofertar.")
        print(f"  ENTER vazio avança para o próximo jogador.  {YY}[H]{RST} histórico  {YY}[0]{RST} sair.")
        raw = input(f"  Valor da proposta (> R${auction.current_bid:,}k): ").strip()
        c = raw.replace(".", "").replace(",", "").upper()

        if c == "0":
            break
        if c == "H":
            _show_transfer_history(market)
            continue
        if c == "":
            visible_auctions.pop(0)
            continue

        try:
            valor = int(c)
            from transfers import player_bid
            ok, msg = player_bid(market, market_index, player_team, valor)
            print((GG if ok else RR) + f"  {msg}" + RST)
        except ValueError:
            print(RR + "  Valor inválido." + RST)
        pause()
        visible_auctions.pop(0)


# ═══════════════════════════════════════════════════════════════
# ARTILHEIROS
# ═══════════════════════════════════════════════════════════════
def show_top_scorers(season: Season):
    clear()
    print(rule("ARTILHEIROS DA TEMPORADA"))
    print()
    all_players = [(t, p) for t in season.all_teams for p in t.players]
    top_global = sorted(all_players, key=lambda x: (-x[1].gols_temp, x[1].name))[:33]
    key_to_division = {(player.name, team.name): team.division for team, player in all_players}

    # Painel da esquerda: ranking global (mantido).
    left_lines = [
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

    # Painel da direita: mesmo layout de tabela do global (liga + copa).
    right_lines = [
        DIM + "  #  " + WW + pad("Nome", 21) + C + pad("Time", 20) + YY + " G  J" + RST,
        C + "  " + h * 51 + RST,
    ]

    player_lookup = {(player.name, team.name): player for team, player in all_players}

    def _competition_stats(prefix: str):
        goals = {}
        games = {}
        for result in season.results_history:
            competition = str(getattr(result, "competition", "") or "").lower()
            if not competition.startswith(prefix):
                continue

            home_team_name = result.home_team.name
            away_team_name = result.away_team.name
            home_used = list(getattr(result, "home_used_names", []) or [])
            away_used = list(getattr(result, "away_used_names", []) or [])

            # Compatibilidade com saves antigos sem used_names:
            # ao menos contabiliza jogo para quem marcou.
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

    def _append_right_section(title: str, rows: list[tuple[str, str, int, int]]):
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
        rows = league_candidates[:5]
        _append_right_section(f"DIVISÃO {div}", rows)

    cup_top = sorted(cup_goals.items(), key=lambda item: (-item[1], item[0][0]))[:5]
    cup_rows = []
    for (player_name, team_name), goals in cup_top:
        games = int(cup_games.get((player_name, team_name), 0))
        # Se ainda não houver tracking de escalação (save antigo), fallback para total.
        if games <= 0:
            player = player_lookup.get((player_name, team_name))
            games = int(player.partidas_temp) if player is not None else 0
        cup_rows.append((player_name, team_name, int(goals), int(games)))
    _append_right_section("COPA (TOP 5)", cup_rows)

    right_box = box(right_lines, title="LIGAS E COPA", border_color=C, title_color=C, width=58)

    if _box_width(left_box) + 2 + _box_width(right_box) <= term_width():
        _print_side_by_side(left_box, right_box, gap=2)
    else:
        # Fallback para terminais estreitos.
        print(left_box)
        print()
        print(right_box)
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


def _team_position(team: Team, all_teams: List[Team]) -> int:
    ranked = sort_standings([club for club in all_teams if club.division == team.division])
    return next((idx + 1 for idx, club in enumerate(ranked) if club.id == team.id), len(ranked))


def prompt_job_offer(coach_name: str, team: Team, all_teams: List[Team] | None = None) -> bool:
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


# ═══════════════════════════════════════════════════════════════
# FIM DE TEMPORADA
# ═══════════════════════════════════════════════════════════════
def _e(emoji: str, ascii_alt: str) -> str:
    """Retorna emoji em terminais coloridos, fallback ASCII em modo MSDOS."""
    return ascii_alt if is_msdos_mode() else emoji


def show_season_end(season: Season, player_team: Team):
    clear()
    w = term_width()
    print(GG + TL + H * (w - 2) + TR + RST)
    title = YY + f"  FIM DA TEMPORADA {season.year}  " + RST
    print(GG + V + RST + pad(title, w - 2, "c") + GG + V + RST)
    print(GG + BL + H * (w - 2) + BR + RST)
    print()

    # ── Posição final na Liga ────────────────────────────────────
    final_data = season.final_positions.get(player_team.id, {}) if hasattr(season, "final_positions") else {}
    original_div = int(final_data.get("division", player_team.division))
    pos = int(final_data.get("position", 0) or 0)
    if pos <= 0:
        # Fallback: usa divisão atual (pode estar atualizada após promoção/rebaixamento)
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

    # ── Prêmio estimado da Liga ──────────────────────────────────
    from season import _season_prize_multiplier
    multiplier = _season_prize_multiplier(season.year)
    liga_prize = int(PRIZE_LIGA.get(original_div, {}).get(pos, 0) * multiplier)

    # ── Copa ─────────────────────────────────────────────────────
    copa_phase = getattr(player_team, "copa_phase", "grupos")
    _copa_phase_labels = {
        "campeão":      (_e("🏆", "[CAMPEAO]") + " CAMPEÃO DA COPA!", YY),
        "final":        ("Vice-campeão da Copa",                       C),
        "semi":         ("Semifinalista da Copa",                      C),
        "quartas":      ("Quartas de final da Copa",                   W),
        "oitavas":      ("Oitavas de final da Copa",                   DIM),
        "primeira_fase":("Eliminado na 1ª Fase da Copa",               DIM),
        "eliminado":    ("Eliminado na Copa",                          DIM),
    }
    copa_label, copa_color = _copa_phase_labels.get(copa_phase, ("—", DIM))
    copa_prize_key = {
        "campeão": "campeão", "final": "vice",
        "semi": "semi", "quartas": "quartas",
        "oitavas": "oitavas", "primeira_fase": "primeira_fase",
    }.get(copa_phase)
    copa_prize = int(PRIZE_COPA.get(copa_prize_key, 0) * multiplier) if copa_prize_key else 0
    if season.copa_champion and season.copa_champion.id != player_team.id:
        copa_champ_line = WW + f"  {_e('🏆','>>>')} Copa: Campeão — {YY}{season.copa_champion.name}{RST}"
    else:
        copa_champ_line = None

    # ── Evolução do elenco ───────────────────────────────────────
    players_with_base = [p for p in player_team.players if p.season_base_ovr is not None]
    if players_with_base:
        top_start = sorted(players_with_base, key=lambda p: p.season_base_ovr, reverse=True)[:11]
        top_end   = sorted(player_team.players, key=lambda p: p.overall, reverse=True)[:11]
        avg_start = sum(p.season_base_ovr for p in top_start) / len(top_start)
        avg_end   = sum(p.overall for p in top_end) / len(top_end)
        ovr_diff  = avg_end - avg_start
        ovr_arrow = (GG + f"+{ovr_diff:+.1f}") if ovr_diff >= 0 else (RR + f"{ovr_diff:+.1f}")
        ovr_line = (WW + f"  OVR médio (top-11): {YY}{avg_start:.1f}{RST} → {YY}{avg_end:.1f} {ovr_arrow}{RST}")
    else:
        ovr_line = None

    # ── Artilheiro ───────────────────────────────────────────────
    scorer_line = None
    if season.top_scorers:
        sc_name, sc_club, sc_goals = season.top_scorers[0]
        scorer_line = GG + f"  {_e('⚽','->')} Artilheiro: {sc_name} ({sc_club}) — {sc_goals} gols" + RST

    # ── Render ───────────────────────────────────────────────────
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


# ═══════════════════════════════════════════════════════════════
# CONFIRM PLAY
# ═══════════════════════════════════════════════════════════════
def confirm_play(formation: Formation, postura: Postura) -> str:
    print()
    print(box([
        "",
        f"  Formação: {YY}{formation.value}{RST}   Postura: {M}{postura.value}{RST}",
        "",
        f"  {WW}Confirma para jogar?{RST}",
        f"  {YY}[1]{RST} Sim   {YY}[2]{RST} Ajustar",
        f"  {YY}[0]{RST} Voltar",
        "",
    ], title="CONFIRMAÇÃO", border_color=YY, title_color=YY, width=50))
    c = input("  Escolha: ").strip()
    if c == "2":
        return "adjust"
    if c == "0":
        return "back"
    return "play"


# ═══════════════════════════════════════════════════════════════
# CRÉDITOS
# ═══════════════════════════════════════════════════════════════
def show_history(career):
    """Exibe o histórico de temporadas da carreira."""
    clear()
    print(rule("📜 HISTÓRICO DA CARREIRA"))
    total_seasons = len(career.season_history)
    current_team = "Sem clube" if career.unemployed else "Empregado"
    summary_lines = [
        f"  Técnico: {WW}{career.player_coach.name}{RST}",
        f"  Temporadas concluídas: {YY}{total_seasons}{RST}",
        f"  Situação atual: {C}{current_team}{RST}",
    ]
    print(box(summary_lines, title="RESUMO DA CARREIRA", border_color=C, title_color=YY, width=70))

    if career.season_history:
        print()
        recent = sorted(career.season_history, key=lambda entry: int(entry.get("year", 0) or 0))[-8:]
        tbl = Table(title="ÚLTIMAS TEMPORADAS", border_color=C, header_color=YY, title_color=C)
        tbl.add_column("Ano", width=5, align="c", color=DIM)
        tbl.add_column("Time", width=20, align="l", color=WW)
        tbl.add_column("Div", width=4, align="c", color=C)
        tbl.add_column("Pos", width=4, align="c", color=YY)
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

        team_goals = world.get("team_goals_record", {})
        player_goals = world.get("player_goals_record", {})
        points_record = world.get("league_points_record", {})
        max_att = world.get("max_attendance", {})
        max_income = world.get("max_income", {})
        biggest_win = world.get("biggest_win", {})

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
            champ_tbl.add_column("Ano", width=5, align="c", color=DIM)
            champ_tbl.add_column("Div", width=4, align="c", color=C)
            champ_tbl.add_column("Clube", width=24, align="l", color=WW)
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


def show_onboarding():
    """Tela de boas-vindas exibida ao iniciar uma nova carreira."""
    clear()
    trophy = _e("🏆", "[CAMPEAO]")
    bolt   = _e("⚡", ">>")
    medal  = _e("🏅", ">>")
    money  = _e("💰", "$$")
    lines = [
        "",
        C  + "  Bem-vindo ao ClassicFoot!" + RST,
        "",
        WW + "  Você é um técnico recém-contratado por um" + RST,
        WW + "  clube da Divisão 4. Seu objetivo:" + RST,
        "",
        YY + f"  {trophy} Chegar à Divisão 1 e conquistar o título!" + RST,
        "",
        GG + "  ─────────────────────────────────────────" + RST,
        "",
        C  + f"  {bolt} LIGA" + RST,
        WW + "  32 times em 4 divisões de 8 equipes." + RST,
        WW + "  Os 2 primeiros de cada divisão sobem," + RST,
        WW + "  os 2 últimos descem." + RST,
        "",
        C  + f"  {medal} COPA" + RST,
        WW + "  Torneio mata-mata com todos os 32 times," + RST,
        WW + "  disputado em paralelo à liga." + RST,
        "",
        C  + f"  {money} FINANÇAS" + RST,
        WW + "  Gerencie folha salarial, leilões de" + RST,
        WW + "  transferências e upgrades de estádio." + RST,
        "",
        DIM + "  Use o menu principal para acessar todas" + RST,
        DIM + "  as opções antes de jogar cada rodada." + RST,
        "",
    ]
    print(box(lines, title="COMO JOGAR", border_color=C, title_color=YY, width=48))
    pause("Pressione ENTER para começar sua carreira...")


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
        WW + "  32 times em 4 divisões" + RST,
        WW + "  Temporada 2025" + RST,
        "",
    ]
    print(box(lines, title="CRÉDITOS", border_color=GG, title_color=GG, width=44))
    pause()
