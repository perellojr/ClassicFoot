"""
Script para (re)gerar data/teams.json a partir das definições Python em data.py.

Executar sempre que os dados dos times forem alterados no código Python:

    python scripts/build_teams_json.py

O arquivo data/teams.json é a fonte primária de dados — create_teams() carrega
dele diretamente. Este script é o gerador, não o carregador.
"""
import json
import sys
from pathlib import Path

# Garante que o diretório raiz do projeto está no path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_builder import create_all_teams, apply_snapshot_2026, apply_finances, _ensure_minimum_rosters, _assign_team_stars  # noqa: E402


def _player_to_dict(p) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "position": p.position.value,
        "age": p.age,
        "nationality": p.nationality,
        "overall": round(float(p.overall), 1),
        "salario": p.salario,
        "valor_mercado": p.valor_mercado,
        "is_star": p.is_star,
    }


def _team_to_dict(t) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "short_name": t.short_name,
        "city": t.city,
        "state": t.state,
        "stadium": t.stadium,
        "division": t.division,
        "prestige": t.prestige,
        "torcida": t.torcida,
        "caixa": t.caixa,
        "salario_mensal": t.salario_mensal,
        "stadium_level": t.stadium_level,
        "primary_color": t.primary_color,
        "secondary_color": t.secondary_color,
        "formation": t.formation.value,
        "postura": t.postura.value,
        "coach": {
            "name": t.coach.name,
            "nationality": t.coach.nationality,
            "tactical": t.coach.tactical,
            "motivation": t.coach.motivation,
            "experience": t.coach.experience,
            "reputation": t.coach.reputation,
        },
        "players": [_player_to_dict(p) for p in t.players],
    }


def build(dest: Path | None = None) -> Path:
    dest = dest or ROOT / "data" / "teams.json"
    dest.parent.mkdir(parents=True, exist_ok=True)

    teams = create_all_teams()
    apply_snapshot_2026(teams)
    apply_finances(teams)
    _ensure_minimum_rosters(teams, 25)
    _assign_team_stars(teams, stars_per_team=3)

    data = [_team_to_dict(t) for t in teams]
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    n_players = sum(len(t["players"]) for t in data)
    print(f"✓ {len(data)} times | {n_players} jogadores → {dest}")
    return dest


if __name__ == "__main__":
    build()
