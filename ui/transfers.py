"""Mercado de transferências, leilões e vendas de jogadores."""
from typing import List

from models import Team
from transfers import sale_price, TransferMarket, player_bid
from term import (
    clear, pause, rule, box, Table,
    ovr_color, fmt_money,
    GG, YY, C, RR, WW, DIM, M, RST,
)

from ui.common import _ellipsize_visible, _ovr_text


def _show_transfer_history(market: TransferMarket) -> None:
    records = list(getattr(market, "transfer_records", []))
    history = list(getattr(market, "history", []))
    clear()
    print(rule("📜 HISTÓRICO DE TRANSFERÊNCIAS"))
    print()

    if not records and not history:
        print(DIM + "  Nenhuma transferência registrada nesta temporada." + RST)
        print()
        pause()
        return

    if records:
        page_size = 12
        total_pages = (len(records) + page_size - 1) // page_size
        page = 0
        while True:
            clear()
            print(rule("📜 HISTÓRICO DE TRANSFERÊNCIAS"))
            print(DIM + f"  Página {page + 1}/{total_pages}" + RST)
            print()

            table = Table(border_color=C, header_color=YY)
            table.add_column("Rodada",       width=7,  align="r")
            table.add_column("Jogador",      width=24, align="l")
            table.add_column("Clube Antigo", width=22, align="l")
            table.add_column("Clube Novo",   width=22, align="l")
            table.add_column("Valor",        width=14, align="r")
            table.add_column("Salário",      width=14, align="r")

            start = page * page_size
            end = start + page_size
            for rec in records[start:end]:
                round_num = int(rec.get("round", 0) or 0)
                table.add_row(
                    str(round_num),
                    _ellipsize_visible(str(rec.get("player", "-")), 24),
                    _ellipsize_visible(str(rec.get("from", "-")), 22),
                    _ellipsize_visible(str(rec.get("to", "-")), 22),
                    fmt_money(int(rec.get("value", 0) or 0)),
                    fmt_money(int(rec.get("salary", 0) or 0)),
                )

            table.print()
            print()
            cmd = input("  ENTER próxima  |  [V] voltar  |  [0] sair: ").strip().upper()
            if cmd == "0":
                break
            if cmd == "V":
                page = max(0, page - 1)
            else:
                page = (page + 1) % total_pages
        return

    # Fallback para saves legados sem histórico estruturado.
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


def show_auction_results(messages: List[str]) -> None:  # noqa: F401
    if not messages:
        return
    clear()
    print(rule("RESULTADO DOS LEILÕES"))
    print()
    for idx, message in enumerate(messages, start=1):
        print(box(["", f"  {message}", ""], title=f"LEILÃO {idx}", border_color=YY, title_color=YY, width=96))
        print()
    pause()


def show_transfer_market(market: TransferMarket, player_team: Team) -> None:
    clear()
    auctions = getattr(market, "auctions", [])
    if not auctions:
        print(rule("MERCADO DE TRANSFERÊNCIAS"))
        print(DIM + "\n  Nenhum jogador no mercado nesta rodada.\n" + RST)
        input("  ENTER para voltar: ")
        return

    visible_auctions = list(auctions)

    while visible_auctions:
        clear()
        print(rule("MERCADO DE TRANSFERÊNCIAS"))
        print()

        total = len(visible_auctions)
        auction = visible_auctions[0]
        p = auction.player
        bidder = auction.current_bidder.name if auction.current_bidder else "—"
        market_index = auctions.index(auction)
        own_player_auction = auction.origin_team.id == player_team.id
        ovr_value = int(round(p.overall))
        bucket_label = market.ovr_bucket_label(ovr_value)
        avg_bid_hint = market.average_bid_for_ovr(ovr_value)
        avg_line = f"  Referência faixa OVR {bucket_label}: {YY}R${avg_bid_hint:,}k{RST}"

        if player_team.caixa < 0:
            lines = [
                "",
                f"  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  {DIM}{p.nationality}{RST}",
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
                f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  {DIM}{p.nationality}{RST}",
                f"  Origem: {C}{auction.origin_team.name}{RST}  │  Lance atual: {GG}R${auction.current_bid:,}k{RST}  │  Líder: {M}{bidder}{RST}",
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

        if player_team.caixa < auction.base_bid:
            lines = [
                "",
                f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  {DIM}{p.nationality}{RST}",
                f"  Origem: {C}{auction.origin_team.name}{RST}  │  Lance base: {YY}R${auction.base_bid:,}k{RST}",
                avg_line,
                "",
                RR + "  Saldo insuficiente para participar deste leilão" + RST,
                "",
            ]
            print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=72))
            print(f"\n  Caixa disponível: {YY}{fmt_money(player_team.caixa)}{RST}")
            c = input(f"\n  ENTER próximo  |  {YY}[H]{RST} histórico  |  {YY}[0]{RST} sair: ").strip().upper()
            if c == "0":
                break
            if c == "H":
                _show_transfer_history(market)
                continue
            visible_auctions.pop(0)
            continue

        if len(player_team.players) >= 45:
            lines = [
                "",
                f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  {DIM}{p.nationality}{RST}",
                f"  Origem: {C}{auction.origin_team.name}{RST}",
                avg_line,
                "",
                RR + "  Elenco cheio (45/45)" + RST,
                "",
            ]
            print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=72))
            print(f"\n  Caixa disponível: {YY}{fmt_money(player_team.caixa)}{RST}")
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
            f"  {ovr_color(ovr_value)}OVR {ovr_value}{RST}  {WW}{p.name}{RST}  [{C}{p.pos_label()}{RST}]  {DIM}{p.nationality}{RST}",
            f"  Origem: {C}{auction.origin_team.name}{RST}  │  Lance base: {YY}R${auction.base_bid:,}k{RST}  │  Lance atual: {GG}R${auction.current_bid:,}k{RST}  │  Líder: {M}{bidder}{RST}",
            f"  Salário: {RR}R${p.salario:,}k/mês{RST}  │  VM: {C}R${p.valor_mercado:,}k{RST}",
            avg_line,
            "",
        ]
        print(box(lines, title=f"LOTE 1 DE {total}", border_color=YY, title_color=YY, width=72))
        print(f"\n  Caixa disponível: {YY}{fmt_money(player_team.caixa)}{RST}")
        print("  Digite o valor do lance e pressione ENTER para ofertar.")
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
            ok, msg = player_bid(market, market_index, player_team, valor)
            print((GG if ok else RR) + f"  {msg}" + RST)
        except ValueError:
            print(RR + "  Valor inválido." + RST)
        pause()
        visible_auctions.pop(0)


def manage_player_sales(team: Team, market: TransferMarket) -> None:
    """Tela contínua para listar jogadores em leilão até o usuário sair."""
    while True:
        clear()
        print(rule(f"VENDER JOGADOR — {team.name}"))
        print()

        if len(team.players) <= 16:
            print(DIM + "\n  Elenco mínimo atingido (16 jogadores). Venda bloqueada.\n" + RST)
            pause()
            return

        available = [p for p in team.players
                     if p.contrato_rodadas == 0 and not market.has_player_in_auction(p)]
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
        tbl.add_column("N",        width=4,  align="r", color=DIM)
        tbl.add_column("Nome",     width=22, align="l", color=WW)
        tbl.add_column("★",        width=3,  align="c", color=M)
        tbl.add_column("Pos",      width=5,  align="c", color=C)
        tbl.add_column("OVR",      width=5,  align="c", color=YY)
        tbl.add_column("J",        width=4,  align="c", color=DIM)
        tbl.add_column("G",        width=4,  align="c", color=GG)
        tbl.add_column("Lance Min", width=14, align="r", color=YY)

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
