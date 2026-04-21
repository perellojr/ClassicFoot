"""Escalação provável e busca do próximo jogo do time do jogador."""
from typing import List, Optional, Tuple

from models import Team, Player, Position, Formation, Fixture, CupTie
from season import Season
from term import box, pad, GG, WW, DIM, C, YY, RST

from ui.common import _ovr_text


def _pick_probable_lineup(team: Team) -> List[Player]:
    available = [p for p in team.players if p.suspenso <= 0]
    if not available:
        available = list(team.players)

    slots = team.formation.slots()
    lineup: List[Player] = []
    used_ids: set = set()

    def player_score(player: Player) -> float:
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


def _find_player_next_match(
    season: Season, player_team: Team
) -> Tuple[Optional[dict], Optional[Fixture], Optional[CupTie]]:
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
