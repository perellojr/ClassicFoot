"""Extrato bancário, torcida e estádio."""
from typing import Optional

from models import Team, TICKET_PRICE_BY_DIV
from season import Season, take_loan, settle_loan, monthly_sponsorship, CUSTO_MANUTENCAO, stadium_maintenance_cost
from term import (
    clear, pause, rule, box,
    GG, YY, Y, C, RR, WW, DIM, G, RST,
    fmt_fans,
    h,
)


def _annual_budget_forecast(team: Team, season: Optional[Season]) -> Optional[dict]:
    """Previsão simples de caixa até o fim da temporada."""
    if season is None:
        return None

    remaining_rounds = max(0, len(season.calendar) - season.current_matchday)
    months_left = max(0, (remaining_rounds + 3) // 4)

    sponsor_monthly = monthly_sponsorship(team)
    monthly_expenses = sum(player.salario for player in team.players) + CUSTO_MANUTENCAO + team.loan_monthly_payment
    projected_expenses = monthly_expenses * months_left

    home_games_left = 0
    for matchday in season.calendar[season.current_matchday:]:
        for fixture in matchday.get("fixtures", []):
            if fixture.home_team.id == team.id:
                home_games_left += 1
    ticket = TICKET_PRICE_BY_DIV.get(team.division, 0.095)
    occupation = min(0.99, max(0.35, 0.44 + team.prestige / 220) * 1.20)
    avg_home_income = int(team.stadium_capacity * occupation * ticket)
    projected_income = (home_games_left * avg_home_income) + (sponsor_monthly * months_left)

    projected_final_cash = team.caixa + projected_income - projected_expenses
    return {
        "remaining_rounds": remaining_rounds,
        "months_left": months_left,
        "projected_income": projected_income,
        "projected_expenses": projected_expenses,
        "projected_final_cash": projected_final_cash,
    }


def show_finances(team: Team, season: Optional[Season] = None) -> None:
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
            lines.append(f"  {WW}{p.name:<22}{RST}  {Y}R${p.salario:,}{RST}  {bar}")
        if forecast:
            lines.extend([
                "",
                C + "  PREVISÃO ORÇAMENTÁRIA (FIM DA TEMPORADA):" + RST,
                WW + f"  {'Rodadas restantes':.<28}" + RST + C + f"  {forecast['remaining_rounds']:>10}" + RST,
                WW + f"  {'Meses restantes':.<28}" + RST + C + f"  {forecast['months_left']:>10}" + RST,
                WW + f"  {'Receitas previstas':.<28}" + RST + G + f"  R${forecast['projected_income']:>10,}" + RST,
                WW + f"  {'Despesas previstas':.<28}" + RST + RR + f"  R${forecast['projected_expenses']:>10,}" + RST,
                WW + f"  {'Caixa projetado':.<28}" + RST +
                (GG if forecast["projected_final_cash"] >= 0 else RR) +
                f"  R${forecast['projected_final_cash']:>10,}" + RST,
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


def show_torcida(team: Team) -> None:
    clear()
    print(rule(f"👥 TORCIDA — {team.name}"))
    torcida = team.torcida
    bar_len = min(int(torcida / 1_500_000), 20)
    fans_bar = GG + "█" * bar_len + RST + DIM + "░" * (20 - bar_len) + RST

    rank = (
        "Top 3 do Brasil" if torcida > 15_000_000 else
        "Top 10 do Brasil" if torcida > 5_000_000 else "Regional"
    )

    ticket = TICKET_PRICE_BY_DIV.get(team.division, 0.095)
    occupation = min(0.99, max(0.35, 0.44 + team.prestige / 220) * 1.20)
    renda = int(team.stadium_capacity * occupation * ticket)
    ticket_price_brl = int(ticket * 1000)
    lines = [
        "",
        WW + f"  Clube:       {GG}{team.name}{RST}",
        WW + f"  Torcida:     {GG}{torcida:,}{RST}" + WW + " torcedores" + RST,
        f"  Engajamento: [{fans_bar}]",
        "",
        WW + f"  Ranking:     {C}{rank}{RST}",
        WW + f"  Cap. Estádio:{DIM} aprox. {fmt_fans(team.stadium_capacity)}{RST}",
        WW + f"  Público med.:{DIM} ~{fmt_fans(int(team.stadium_capacity * occupation))}{RST}",
        "",
        WW + f"  Prestígio:   {C}{team.prestige}/100{RST}",
        WW + f"  Ingresso:    {DIM}R${ticket_price_brl}/pessoa (Div{team.division}){RST}",
        WW + f"  Renda/jogo:  {Y}R${renda:,} mil{RST}",
        "",
    ]
    print(box(lines, title="INFORMAÇÕES DA TORCIDA", border_color=G, title_color=GG, width=50))
    pause()


def show_stadium(team: Team) -> None:
    while True:
        clear()
        print(rule(f"🏟  ESTÁDIO — {team.stadium}"))
        ticket = TICKET_PRICE_BY_DIV.get(team.division, 0.095)
        ticket_price_brl = int(ticket * 1000)
        occupation = min(0.99, max(0.35, 0.44 + team.prestige / 220) * 1.20)
        estimated_crowd = int(team.stadium_capacity * occupation)
        renda = int(estimated_crowd * ticket)

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
            DIM + f"  (Baseado em ~{fmt_fans(estimated_crowd)} ingressos a R${ticket_price_brl}/un.)" + RST,
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
