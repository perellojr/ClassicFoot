"""
ClassicFoot - Carregador de dados dos times.

Fonte primária: data/teams.json
Para regenerar o JSON após alterar dados dos times:
    python scripts/build_teams_json.py
"""
import json
from pathlib import Path
from models import Player, Team, Coach, Formation, Postura, Position as P

_JSON_PATH = Path(__file__).parent / "data" / "teams.json"


def _create_teams_from_json() -> list:
    """Carrega times a partir de data/teams.json."""
    with open(_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    formation_map = {fm.value: fm for fm in Formation}
    postura_map = {ps.value: ps for ps in Postura}
    position_map = {pos.value: pos for pos in P}

    teams = []
    for td in data:
        coach_d = td["coach"]
        coach = Coach(
            name=coach_d["name"],
            nationality=coach_d.get("nationality", "Brasileiro"),
            tactical=coach_d.get("tactical", 75),
            motivation=coach_d.get("motivation", 75),
            experience=coach_d.get("experience", 75),
            reputation=coach_d.get("reputation", 70),
        )
        players = []
        for pd in td.get("players", []):
            players.append(Player(
                id=pd["id"],
                name=pd["name"],
                position=position_map[pd["position"]],
                age=pd["age"],
                nationality=pd.get("nationality", "Brasileiro"),
                overall=float(pd["overall"]),
                salario=pd.get("salario", 100),
                valor_mercado=pd.get("valor_mercado", 500),
                is_star=pd.get("is_star", False),
            ))
        team = Team(
            id=td["id"],
            name=td["name"],
            short_name=td.get("short_name", td["name"][:3].upper()),
            city=td.get("city", ""),
            state=td.get("state", ""),
            stadium=td.get("stadium", ""),
            division=td["division"],
            prestige=td.get("prestige", 70),
            torcida=td.get("torcida", 1_000_000),
            caixa=td.get("caixa", 50_000),
            salario_mensal=td.get("salario_mensal", 5_000),
            stadium_level=td.get("stadium_level", 1),
            primary_color=td.get("primary_color", "green"),
            secondary_color=td.get("secondary_color", "white"),
            formation=formation_map.get(td.get("formation", "4-4-2"), Formation.F442),
            postura=postura_map.get(td.get("postura", "Equilibrado"), Postura.EQUILIBRADO),
            coach=coach,
            players=players,
        )
        teams.append(team)
    return teams


def create_teams() -> list:
    """Retorna a lista completa de times carregada do JSON."""
    return _create_teams_from_json()


def get_teams_by_division(teams: list, division: int) -> list:
    return [t for t in teams if t.division == division]
