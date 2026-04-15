"""
ClassicFoot - Utilitários de renderização no terminal
Usa colorama + caracteres Unicode box-drawing.
Reproduz estilo visual do Elifoot 2.
"""
import os
import sys
import shutil
from colorama import Fore, Back, Style, init

init(autoreset=True)

# ── Tamanho do terminal ────────────────────────────────────────
def term_width() -> int:
    return shutil.get_terminal_size((100, 30)).columns

# ── Constantes de cor ──────────────────────────────────────────
G  = Fore.GREEN
GG = Fore.GREEN  + Style.BRIGHT
YY = Fore.YELLOW + Style.BRIGHT
Y  = Fore.YELLOW
C  = Fore.CYAN   + Style.BRIGHT
BB = Fore.BLUE   + Style.BRIGHT
RR = Fore.RED    + Style.BRIGHT
R  = Fore.RED
WW = Fore.WHITE  + Style.BRIGHT
W  = Fore.WHITE
M  = Fore.MAGENTA + Style.BRIGHT
DIM= Style.DIM
RST= Style.RESET_ALL

# ── Box drawing ────────────────────────────────────────────────
TL="╔"; TR="╗"; BL="╚"; BR="╝"
H="═"; V="║"
ML="╠"; MR="╣"; TM="╦"; BM="╩"; X="╬"

tl="┌"; tr="┐"; bl="└"; br="┘"
h="─"; v="│"
ml="├"; mr="┤"; tm="┬"; bm="┴"; x="┼"

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def pause(msg: str = "Pressione ENTER para continuar..."):
    input(f"\n  {DIM}{msg}{RST}")

def pad(s: str, w: int, align: str = "l") -> str:
    """Pad string to width w. align: l/r/c. Strips ANSI for length calc."""
    vis = _visible_len(s)
    diff = w - vis
    if diff <= 0:
        return s
    if align == "r":
        return " " * diff + s
    if align == "c":
        lp = diff // 2
        rp = diff - lp
        return " " * lp + s + " " * rp
    return s + " " * diff

def _visible_len(s: str) -> int:
    """Comprimento visível (sem sequências ANSI)."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', s))

def color_len(s: str) -> int:
    return _visible_len(s)

# ── Linha horizontal ───────────────────────────────────────────
def hline(w: int = 0, char: str = H, color: str = GG) -> str:
    if w == 0:
        w = term_width()
    return color + char * w + RST

def rule(text: str = "", width: int = 0, color: str = GG) -> str:
    if width == 0:
        width = term_width()
    if not text:
        return color + H * width + RST
    text_vis = _visible_len(text)
    side = max(2, (width - text_vis - 2) // 2)
    return (color + H * side + " " + RST +
            WW + text + RST +
            color + " " + H * (width - side - text_vis - 2) + RST)

# ── Caixa / Panel ─────────────────────────────────────────────
def box(lines: list, title: str = "", width: int = 0,
        border_color: str = GG, title_color: str = YY) -> str:
    if width == 0:
        max_content = max((_visible_len(l) for l in lines), default=10)
        width = max_content + 4

    inner = width - 2
    result = []

    # Top border
    if title:
        tv = _visible_len(title)
        side_len = (inner - tv - 2) // 2
        top = (border_color + TL + H * side_len + " " + RST +
               title_color + title + RST +
               border_color + " " + H * (inner - side_len - tv - 2) + TR + RST)
    else:
        top = border_color + TL + H * inner + TR + RST
    result.append(top)

    for line in lines:
        result.append(border_color + V + RST + " " +
                      pad(line, inner - 2) + " " +
                      border_color + V + RST)

    result.append(border_color + BL + H * inner + BR + RST)
    return "\n".join(result)

# ── Tabela ────────────────────────────────────────────────────
class Table:
    def __init__(self, title: str = "", border_color: str = C,
                 header_color: str = YY, title_color: str = C):
        self.title = title
        self.border_color = border_color
        self.header_color = header_color
        self.title_color  = title_color
        self.columns = []   # list of dict: name, width, align, color
        self.rows    = []   # list of list of str

    def add_column(self, name: str, width: int = 12,
                   align: str = "l", color: str = W):
        self.columns.append({"name": name, "width": width,
                              "align": align, "color": color})

    def add_row(self, *cells):
        self.rows.append(list(cells))

    def render(self) -> str:
        bc = self.border_color
        hc = self.header_color
        tc = self.title_color
        cols = self.columns

        total_inner = sum(c["width"] for c in cols) + len(cols) - 1 + 2

        lines = []

        # Title
        if self.title:
            tv = _visible_len(self.title)
            side = (total_inner - tv - 2) // 2
            lines.append(
                bc + TL + H * side + " " + RST +
                tc + self.title + RST +
                bc + " " + H * (total_inner - side - tv - 2) + TR + RST
            )
        else:
            lines.append(bc + TL + H * total_inner + TR + RST)

        # Header separator
        _sep_top = bc + ML + MR.join(H * c["width"] for c in cols) + MR + RST

        # Header row
        header_cells = [pad(hc + c["name"] + RST, c["width"], c.get("align", "l"))
                        for c in cols]
        lines.append(bc + V + RST + (bc + V + RST).join(header_cells) + bc + V + RST)
        lines.append(_sep_top)

        # Data rows
        for row in self.rows:
            cells = []
            for i, col in enumerate(cols):
                val = str(row[i]) if i < len(row) else ""
                cells.append(pad(val, col["width"], col.get("align", "l")))
            lines.append(bc + V + RST + (bc + V + RST).join(cells) + bc + V + RST)

        lines.append(bc + BL + H * total_inner + BR + RST)
        return "\n".join(lines)

    def print(self):
        print(self.render())

# ── Helpers de cor dinâmica ────────────────────────────────────
def ovr_color(ovr: int) -> str:
    if ovr >= 85: return GG
    if ovr >= 75: return G
    if ovr >= 65: return Y
    return R

def form_color(f: int) -> str:
    if f >= 75: return GG
    if f >= 55: return Y
    return R

def cond_color(c: int) -> str:
    if c >= 80: return G
    if c >= 60: return Y
    return RR

def fmt_fans(n: int) -> str:
    if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
    return f"{n//1_000}K"

def fmt_money(v: int) -> str:
    return f"R${v:,}k"

def colored_score(hg: int, ag: int, is_home: bool) -> str:
    """Placar colorido do ponto de vista do time."""
    if (is_home and hg > ag) or (not is_home and ag > hg):
        return GG + f"{hg} x {ag}" + RST
    if hg == ag:
        return YY + f"{hg} x {ag}" + RST
    return RR + f"{hg} x {ag}" + RST
