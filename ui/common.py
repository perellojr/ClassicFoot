"""Helpers compartilhados entre os sub-módulos de UI."""
from typing import List

from models import MatchResult, Team
from term import (
    _visible_len, _clip_visible, is_msdos_mode,
    GG, YY, RR, BB, WW, W, RST,
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


def _e(emoji: str, ascii_alt: str) -> str:
    """Retorna emoji em terminais coloridos, fallback ASCII em modo MSDOS."""
    return ascii_alt if is_msdos_mode() else emoji


def _team_color(team: object) -> str:
    return {
        "red": RR,
        "dark_red": RR,
        "green": GG,
        "blue": BB,
        "yellow": YY,
        "black": W,
        "white": WW,
    }.get(getattr(team, "primary_color", "white"), WW)


def _division_label(division: int) -> str:
    return f"DIVISÃO {division}"


def _fit_team_name(name: str, limit: int = 17) -> str:
    if len(name) <= limit:
        return name
    if limit <= 3:
        return name[:limit]
    return name[: limit - 3].rstrip() + "..."


def _fit_text(text: str, limit: int = 40) -> str:
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return text[: limit - 3].rstrip() + "..."


def _box_width(rendered_box: str) -> int:
    lines = rendered_box.split("\n")
    return max((_visible_len(line) for line in lines), default=0)


def _print_side_by_side(left: str, right: str, gap: int = 1) -> None:
    """Imprime duas caixas lado a lado."""
    left_lines = left.split("\n")
    right_lines = right.split("\n")
    max_lines = max(len(left_lines), len(right_lines))
    left_vis_w = max(_visible_len(l) for l in left_lines) if left_lines else 0

    for i in range(max_lines):
        l = left_lines[i] if i < len(left_lines) else ""
        r = right_lines[i] if i < len(right_lines) else ""
        l_pad = left_vis_w - _visible_len(l)
        print(l + " " * (l_pad + gap) + r)


def _mini_form(history: List[MatchResult], team: Team) -> str:
    recent = [r for r in history
              if r.home_team.id == team.id or r.away_team.id == team.id][-5:]
    parts = []
    for r in recent:
        w = r.winner()
        if w is None:
            parts.append(YY + "E" + RST)
        elif w.id == team.id:
            parts.append(GG + "V" + RST)
        else:
            parts.append(RR + "D" + RST)
    return " ".join(parts)
