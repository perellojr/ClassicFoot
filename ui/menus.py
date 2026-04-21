"""Banner, menus principal e de jogo, créditos e onboarding."""
from models import Formation, Postura
from term import (
    clear, pause, box,
    GG, YY, WW, DIM, M, RST,
    term_width, _visible_len,
    TL, TR, BL, BR, H, V,
    is_msdos_mode,
)

from ui.common import _e


def banner() -> None:
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


def game_menu() -> str:
    choice = input("\n  ► Opção: ").strip().upper()
    return choice or "6"


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


def show_onboarding() -> None:
    """Tela de boas-vindas exibida ao iniciar uma nova carreira."""
    clear()
    trophy = _e("🏆", "[CAMPEAO]")
    bolt   = _e("⚡", ">>")
    medal  = _e("🏅", ">>")
    money  = _e("💰", "$$")
    from term import C, WW, GG  # noqa: F401 — já importados acima; aqui para legibilidade
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


def show_credits() -> None:
    clear()
    from term import C, WW, GG  # noqa: F401
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
