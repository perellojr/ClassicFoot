from __future__ import annotations

from models import Coach, Player, Position, Team


def make_player(player_id: int, name: str, position: Position, overall: int = 70) -> Player:
    return Player(
        id=player_id,
        name=name,
        position=position,
        age=24,
        nationality="Brasileiro",
        overall=float(overall),
        salario=100,
        valor_mercado=1000,
        contrato_rodadas=20,
    )


def make_team(
    team_id: int,
    name: str,
    division: int = 1,
    prestige: int = 70,
    coach_name: str | None = None,
    players: list[Player] | None = None,
) -> Team:
    return Team(
        id=team_id,
        name=name,
        short_name=name[:3].upper(),
        city="Cidade",
        state="ST",
        stadium=f"Estádio {name}",
        division=division,
        prestige=prestige,
        coach=Coach(coach_name or f"Técnico {name}"),
        players=players or [],
    )
