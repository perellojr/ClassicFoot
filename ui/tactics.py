"""Táticas, formação, postura, treino e renovação de contrato."""
from typing import List

from models import Team, Formation, Postura, Position
from term import (
    clear, pause, rule, Table,
    GG, YY, C, RR, WW, DIM, M, RST, G,
)

from ui.common import _ovr_text
from ui.lineup import _pick_probable_lineup, _render_probable_lineup


def prompt_contract_renewal(team: Team):
    clear()
    print(rule(f"RENOVAÇÃO DE CONTRATO — {team.name}"))
    print()

    players = sorted(team.players, key=lambda p: (p.contrato_rodadas, -p.overall, p.name))

    tbl = Table(title="ELENCO", border_color=C, header_color=YY, title_color=C)
    tbl.add_column("N",       width=4,  align="r", color=DIM)
    tbl.add_column("Nome",    width=24, align="l", color=WW)
    tbl.add_column("Pos",     width=5,  align="c", color=C)
    tbl.add_column("OVR",     width=5,  align="c", color=YY)
    tbl.add_column("Cont",    width=6,  align="c", color=DIM)
    tbl.add_column("Salário", width=12, align="r", color=YY)

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


def show_training(team: Team) -> Team:
    """Seleciona até 5 jogadores para treino da rodada."""
    clear()
    print(rule(f"TREINO DA RODADA — {team.name}"))
    print()

    players = sorted(team.players, key=lambda p: (-p.overall, p.name))
    selected_ids = set(team.training_targets or [])

    tbl = Table(title="ELENCO (ATÉ 5 JOGADORES)", border_color=C, header_color=YY, title_color=C)
    tbl.add_column("N",      width=4, align="r", color=DIM)
    tbl.add_column("Nome",   width=24, align="l", color=WW)
    tbl.add_column("Pos",    width=5,  align="c", color=C)
    tbl.add_column("OVR",    width=5,  align="c", color=YY)
    tbl.add_column("Craque", width=8,  align="c", color=G)
    tbl.add_column("Treino", width=8,  align="c", color=M)

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
    picks: List[int] = []
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
        original = team.formation
        team.formation = f
        fit_ovr = f.fit_ovr(_pick_probable_lineup(team))
        team.formation = original
        cur = YY + " ◄" + RST if f == team.formation else ""
        enabled = f.can_use(team)
        label_color = YY if enabled else DIM
        lock = RR + " [indisponível]" + RST if not enabled else ""
        print(f"  {YY}[{i}]{RST} {label_color}{f.value:<8}{RST}  {DIM}{desc}{RST}  OVR:{YY}{_ovr_text(fit_ovr):>3}{RST}  ATK:[{atk_bar}]{cur}{lock}")

    c = input("\n  Escolha formação (ENTER = manter): ").strip()
    if c.isdigit() and 1 <= int(c) <= len(formations):
        selected = formations[int(c) - 1]
        if selected.can_use(team):
            team.formation = selected
            print(GG + f"\n  Formação alterada para {team.formation.value}" + RST)
        else:
            print(RR + "\n  Não há jogadores suficientes por posição para essa formação." + RST)

    base_ovr = team.formation.fit_ovr(_pick_probable_lineup(team))
    print()
    print(C + "  IMPACTO DA POSTURA (OVR):" + RST)
    for postura in [Postura.DEFENSIVO, Postura.EQUILIBRADO, Postura.OFENSIVO]:
        simulated = postura.fit_ovr(base_ovr)
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
