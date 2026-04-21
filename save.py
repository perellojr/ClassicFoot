"""
ClassicFoot - Sistema de save/load
Usa JSON como formato primário desde a versão 4.

O save é gravado em ~/.classicfoot/save.json.
Um backup automático (save.bak.json) é criado antes de cada nova gravação.
Saves legados em pickle são carregados e convertidos automaticamente.

Migração de schema: _migrate_loaded_state aplica todas as normalizações
necessárias para saves antigos, incluindo backfill de histórico mundial.
"""
import json
import pickle
import shutil
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models import CareerState

# ── Diretório de dados do usuário ─────────────────────────────
SAVE_DIR = Path.home() / ".classicfoot"
# Formato primário (JSON)
JSON_SAVE_FILE  = SAVE_DIR / "save.json"
JSON_BAK_FILE   = SAVE_DIR / "save.bak.json"
# Legado (pickle) — apenas leitura para saves antigos
SAVE_FILE    = SAVE_DIR / "save.pkl"
BACKUP_FILE  = SAVE_DIR / "save.bak.pkl"
# Exportação legível para humanos (sumário simplificado)
JSON_BACKUP_FILE = SAVE_DIR / "save_backup.json"
SAVE_VERSION = 4


def _ensure_dir():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


# ── Gestão do histórico mundial ────────────────────────────────

def ensure_world_history(career: "CareerState") -> dict:
    """Garante que career.world_history existe com todas as chaves esperadas."""
    if not isinstance(getattr(career, "world_history", None), dict):
        career.world_history = {}
    history = career.world_history
    history.setdefault("division_champions", [])
    history.setdefault("team_goals_record", {"goals": 0, "team": "-", "year": 0})
    history.setdefault("player_goals_record", {"goals": 0, "player": "-", "team": "-", "year": 0})
    history.setdefault("team_goals_cumulative", {})
    history.setdefault("player_goals_cumulative", {})
    history.setdefault("league_points_cumulative", {})
    history.setdefault("league_points_record", {"points": 0, "team": "-", "year": 0})
    history.setdefault("div1_titles_by_club", {})
    history.setdefault("copa_titles_by_club", {})
    history.setdefault("div1_champion_coaches_history", [])
    history.setdefault("copa_champion_coaches_history", [])
    history.setdefault("recorded_years", [])
    history.setdefault("recorded_champion_years", [])
    history.setdefault("recorded_aggregate_years", [])
    history.setdefault("biggest_win", {"diff": 0, "score": "-", "winner": "-", "loser": "-", "year": 0})
    history.setdefault("max_attendance", {"attendance": 0, "home": "-", "away": "-", "year": 0})
    history.setdefault("max_income", {"income": 0, "home": "-", "away": "-", "year": 0})
    history.setdefault("coach_titles", {})
    return history


def normalize_world_history(career: "CareerState") -> None:
    """
    Migra/normaliza estrutura de histórico para saves antigos, sem exigir novo jogo.
    Também recalcula recordes acumulados a partir dos dados disponíveis.
    """
    world = ensure_world_history(career)
    if not isinstance(career.season_history, list):
        career.season_history = []

    # Backfill de campeões da Divisão 1 por clube e técnicos a partir do histórico existente.
    if (not world.get("div1_titles_by_club")) and world.get("division_champions"):
        rebuilt_titles: dict = {}
        rebuilt_coaches = []
        for item in world.get("division_champions", []):
            if int(item.get("division", 0) or 0) != 1:
                continue
            team_name = item.get("team")
            coach_name = item.get("coach")
            if team_name:
                rebuilt_titles[team_name] = int(rebuilt_titles.get(team_name, 0)) + 1
            if coach_name:
                rebuilt_coaches.append(coach_name)
        world["div1_titles_by_club"] = rebuilt_titles
        if not world.get("div1_champion_coaches_history"):
            world["div1_champion_coaches_history"] = rebuilt_coaches

    # Backfill de campeões da Copa por clube via season_history (quando disponível).
    if (not world.get("copa_titles_by_club")) and career.season_history:
        rebuilt_copa_titles: dict = {}
        for entry in career.season_history:
            champion = entry.get("copa_champion")
            if champion:
                rebuilt_copa_titles[champion] = int(rebuilt_copa_titles.get(champion, 0)) + 1
        world["copa_titles_by_club"] = rebuilt_copa_titles

    # Recalcula ranking de técnicos campeões: campeão Div 1 + campeão Copa.
    coach_counter: dict = {}
    for coach_name in world.get("div1_champion_coaches_history", []):
        if coach_name:
            coach_counter[coach_name] = int(coach_counter.get(coach_name, 0)) + 1
    for coach_name in world.get("copa_champion_coaches_history", []):
        if coach_name:
            coach_counter[coach_name] = int(coach_counter.get(coach_name, 0)) + 1
    world["coach_titles"] = coach_counter

    # Reconstrói anos gravados de forma robusta.
    years_from_history = {
        int(entry.get("year") or 0)
        for entry in career.season_history
        if isinstance(entry, dict) and entry.get("year") is not None
    }
    years_from_champions = {
        int(item.get("year") or 0)
        for item in world.get("division_champions", [])
        if isinstance(item, dict) and item.get("year") is not None
    }
    world["recorded_champion_years"] = sorted(
        set(world.get("recorded_champion_years", [])) | years_from_champions
    )
    world["recorded_aggregate_years"] = sorted(
        set(world.get("recorded_aggregate_years", []))
    )
    world["recorded_years"] = sorted(
        set(world.get("recorded_years", []))
        | years_from_history
        | set(world.get("recorded_champion_years", []))
        | set(world.get("recorded_aggregate_years", []))
    )

    # Migração: semeia acumulados vazios a partir do season_history.
    if not world.get("league_points_cumulative") and career.season_history:
        points_seed: dict = {}
        for entry in career.season_history:
            if not isinstance(entry, dict):
                continue
            team = entry.get("league_points_best_team")
            points = int(entry.get("league_points_best_points", 0) or 0)
            if team and points > 0:
                points_seed[team] = int(points_seed.get(team, 0)) + points
        world["league_points_cumulative"] = points_seed

    if not world.get("team_goals_cumulative") and career.season_history:
        goals_seed: dict = {}
        for entry in career.season_history:
            if not isinstance(entry, dict):
                continue
            team = entry.get("league_best_attack_team")
            goals = int(entry.get("league_best_attack_goals", 0) or 0)
            if team and goals > 0:
                goals_seed[team] = int(goals_seed.get(team, 0)) + goals
        world["team_goals_cumulative"] = goals_seed

    if not world.get("player_goals_cumulative") and career.season_history:
        player_seed: dict = {}
        for entry in career.season_history:
            if not isinstance(entry, dict):
                continue
            top = entry.get("top_scorer")
            if not isinstance(top, (tuple, list)) or len(top) < 3:
                continue
            player_name, team_name, goals = top[0], top[1], int(top[2] or 0)
            if player_name and team_name and goals > 0:
                key = f"{player_name}::{team_name}"
                player_seed[key] = int(player_seed.get(key, 0)) + goals
        world["player_goals_cumulative"] = player_seed

    # Fallbacks para saves sem base acumulada.
    if not world.get("league_points_cumulative"):
        rec = world.get("league_points_record", {}) or {}
        team = rec.get("team")
        pts = int(rec.get("points", 0) or 0)
        if team and team != "-" and pts > 0:
            world["league_points_cumulative"] = {team: pts}

    if not world.get("team_goals_cumulative"):
        rec = world.get("team_goals_record", {}) or {}
        team = rec.get("team")
        goals_val = int(rec.get("goals", 0) or 0)
        if team and team != "-" and goals_val > 0:
            world["team_goals_cumulative"] = {team: goals_val}

    if not world.get("player_goals_cumulative"):
        rec = world.get("player_goals_record", {}) or {}
        player = rec.get("player")
        team = rec.get("team")
        goals_val = int(rec.get("goals", 0) or 0)
        if player and team and player != "-" and team != "-" and goals_val > 0:
            world["player_goals_cumulative"] = {f"{player}::{team}": goals_val}

    # Recalcula recordes a partir dos acumulados.
    if world.get("league_points_cumulative"):
        club_name, total_points = max(world["league_points_cumulative"].items(), key=lambda item: item[1])
        world["league_points_record"] = {
            "points": int(total_points),
            "team": club_name,
            "year": world.get("league_points_record", {}).get("year", 0),
        }

    if world.get("team_goals_cumulative"):
        team_name, total_goals = max(world["team_goals_cumulative"].items(), key=lambda item: item[1])
        world["team_goals_record"] = {
            "goals": int(total_goals),
            "team": team_name,
            "year": world.get("team_goals_record", {}).get("year", 0),
        }

    if world.get("player_goals_cumulative"):
        player_key, total_goals = max(world["player_goals_cumulative"].items(), key=lambda item: item[1])
        player_name, team_name = player_key.split("::", 1)
        world["player_goals_record"] = {
            "goals": int(total_goals),
            "player": player_name,
            "team": team_name,
            "year": world.get("player_goals_record", {}).get("year", 0),
        }

    career.world_history = world


# ── Serialização para JSON ─────────────────────────────────────

def _player_to_dict(p) -> dict:
    return {
        "id": p.id,
        "name": p.name,
        "position": p.position.value,
        "age": p.age,
        "nationality": p.nationality,
        "overall": round(float(p.overall), 2),
        "salario": p.salario,
        "valor_mercado": p.valor_mercado,
        "suspenso": p.suspenso,
        "contrato_rodadas": p.contrato_rodadas,
        "gols_temp": p.gols_temp,
        "partidas_temp": p.partidas_temp,
        "amarelos_temp": p.amarelos_temp,
        "vermelhos_temp": p.vermelhos_temp,
        "gols_total": p.gols_total,
        "partidas_total": p.partidas_total,
        "amarelos_total": p.amarelos_total,
        "vermelhos_total": p.vermelhos_total,
        "season_base_ovr": float(p.season_base_ovr) if p.season_base_ovr is not None else None,
        "is_star": getattr(p, "is_star", False),
    }


def _coach_to_dict(c) -> dict:
    return {
        "name": c.name,
        "nationality": c.nationality,
        "tactical": c.tactical,
        "motivation": c.motivation,
        "experience": c.experience,
        "reputation": c.reputation,
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
        "primary_color": getattr(t, "primary_color", "green"),
        "secondary_color": getattr(t, "secondary_color", "white"),
        "torcida": t.torcida,
        "caixa": t.caixa,
        "salario_mensal": getattr(t, "salario_mensal", 5_000),
        "stadium_level": t.stadium_level,
        "loan_balance": getattr(t, "loan_balance", 0),
        "loan_monthly_payment": getattr(t, "loan_monthly_payment", 0),
        "loan_months_left": getattr(t, "loan_months_left", 0),
        "formation": t.formation.value,
        "postura": t.postura.value,
        "coach": _coach_to_dict(t.coach),
        "players": [_player_to_dict(p) for p in t.players],
        "training_targets": list(getattr(t, "training_targets", []) or []),
        "training_round_applied": getattr(t, "training_round_applied", -1),
        "rivalry_points": {str(k): v for k, v in (getattr(t, "rivalry_points", {}) or {}).items()},
        "dynamic_rivals": list(getattr(t, "dynamic_rivals", []) or []),
        "div_wins": t.div_wins,
        "div_draws": t.div_draws,
        "div_losses": t.div_losses,
        "div_gf": t.div_gf,
        "div_ga": t.div_ga,
        "last_results": list(t.last_results or []),
        "copa_wins": t.copa_wins,
        "copa_draws": t.copa_draws,
        "copa_losses": t.copa_losses,
        "copa_gf": t.copa_gf,
        "copa_ga": t.copa_ga,
        "copa_group": t.copa_group,
        "copa_phase": t.copa_phase,
    }


def _career_to_dict(career) -> dict:
    seen: set = getattr(career, "seen_notifications", set()) or set()
    return {
        "player_coach": _coach_to_dict(career.player_coach),
        "current_team_id": career.current_team_id,
        "unemployed": career.unemployed,
        "fired": getattr(career, "fired", False),
        "last_fired_team_id": getattr(career, "last_fired_team_id", None),
        "games_in_charge": career.games_in_charge,
        "rounds_unemployed": getattr(career, "rounds_unemployed", 0),
        "season_history": list(career.season_history or []),
        "world_history": dict(career.world_history or {}),
        "free_coaches": [_coach_to_dict(c) for c in (career.free_coaches or [])],
        "notifications": list(getattr(career, "notifications", []) or []),
        "seen_notifications": list(seen),
        "event_log": list(getattr(career, "event_log", []) or []),
        "coach_market_last_round": getattr(career, "coach_market_last_round", -1),
        "coach_market_cooldown": dict(getattr(career, "coach_market_cooldown", {}) or {}),
    }


def _match_result_to_dict(mr) -> Optional[dict]:
    if mr is None:
        return None
    return {
        "home_team_id": mr.home_team.id,
        "home_team_name": mr.home_team.name,
        "away_team_id": mr.away_team.id,
        "away_team_name": mr.away_team.name,
        "home_goals": mr.home_goals,
        "away_goals": mr.away_goals,
        "home_scorers": list(mr.home_scorers or []),
        "away_scorers": list(mr.away_scorers or []),
        "competition": mr.competition,
        "matchday": mr.matchday,
        "attendance": mr.attendance,
        "income": mr.income,
        "home_used_names": list(getattr(mr, "home_used_names", []) or []),
        "away_used_names": list(getattr(mr, "away_used_names", []) or []),
    }


def _fixture_to_dict(f) -> dict:
    return {
        "home_team_id": f.home_team.id,
        "away_team_id": f.away_team.id,
        "competition": f.competition,
        "matchday": f.matchday,
        "result": _match_result_to_dict(f.result),
    }


def _cup_tie_to_dict(ct) -> dict:
    ps = ct.penalty_score
    return {
        "team_a_id": ct.team_a.id,
        "team_b_id": ct.team_b.id,
        "phase": ct.phase,
        "leg1": _match_result_to_dict(ct.leg1),
        "leg2": _match_result_to_dict(ct.leg2),
        "single_leg": ct.single_leg,
        "penalty_winner_id": ct.penalty_winner_id,
        "penalty_score": list(ps) if ps is not None else None,
    }


def _season_to_dict(season) -> dict:
    def _ties(lst):
        return [_cup_tie_to_dict(ct) for ct in (lst or [])]

    calendar_data = []
    for matchday in (season.calendar or []):
        calendar_data.append({
            "label": matchday.get("label", ""),
            "cup_leg": matchday.get("cup_leg", 1),
            "fixtures": [_fixture_to_dict(f) for f in (matchday.get("fixtures") or [])],
            "ties": [_cup_tie_to_dict(ct) for ct in (matchday.get("ties") or [])],
        })

    return {
        "year": season.year,
        "player_team_id": season.player_team_id,
        "current_matchday": season.current_matchday,
        "season_over": season.season_over,
        "calendar": calendar_data,
        "results_history": [_match_result_to_dict(r) for r in (season.results_history or [])],
        "copa_primeira_fase": _ties(season.copa_primeira_fase),
        "copa_oitavas": _ties(season.copa_oitavas),
        "copa_quartas": _ties(season.copa_quartas),
        "copa_semi": _ties(season.copa_semi),
        "copa_final": _cup_tie_to_dict(season.copa_final) if season.copa_final else None,
        "copa_champion_id": season.copa_champion.id if season.copa_champion else None,
        "top_scorers": list(season.top_scorers or []),
        "division_champions": {str(k): v for k, v in (season.division_champions or {}).items()},
        "division_champion_coaches": {str(k): v for k, v in (season.division_champion_coaches or {}).items()},
        "best_team_goals": dict(season.best_team_goals or {}),
        "best_player_goals": dict(season.best_player_goals or {}),
        "max_attendance": dict(season.max_attendance or {}),
        "max_income": dict(season.max_income or {}),
        "final_positions": {str(k): v for k, v in (season.final_positions or {}).items()},
        "shown_cup_draws": list(getattr(season, "shown_cup_draws", []) or []),
    }


def _market_to_dict(market) -> dict:
    """Serializa apenas o estado não-transiente do mercado (sem leilões ativos)."""
    return {
        "history": list(getattr(market, "history", []) or []),
        "bid_stats_by_ovr_bucket": dict(getattr(market, "bid_stats_by_ovr_bucket", {}) or {}),
        "transfer_records": list(getattr(market, "transfer_records", []) or []),
    }


def _game_state_to_dict(game_state: dict) -> dict:
    """Converte todo o estado do jogo para um dict serializável em JSON."""
    season = game_state.get("season")
    career = game_state.get("career")
    market = game_state.get("market")
    all_teams = list(getattr(season, "all_teams", []) or []) if season else []

    return {
        "__save_meta__": {
            "version": SAVE_VERSION,
            "saved_at": time.time(),
            "format": "classicfoot-json-v2",
        },
        "teams": [_team_to_dict(t) for t in all_teams],
        "career": _career_to_dict(career) if career else None,
        "season": _season_to_dict(season) if season else None,
        "market": _market_to_dict(market) if market else None,
    }


# ── Desserialização de JSON ────────────────────────────────────

def _dict_to_coach(d: dict):
    from models import Coach
    return Coach(
        name=d.get("name", "Técnico"),
        nationality=d.get("nationality", "Brasileiro"),
        tactical=int(d.get("tactical", 75)),
        motivation=int(d.get("motivation", 75)),
        experience=int(d.get("experience", 75)),
        reputation=int(d.get("reputation", 70)),
    )


def _dict_to_player(d: dict):
    from models import Player, Position
    return Player(
        id=int(d["id"]),
        name=d["name"],
        position=Position(d["position"]),
        age=int(d["age"]),
        nationality=d.get("nationality", "Brasileiro"),
        overall=float(d["overall"]),
        salario=int(d.get("salario", 100)),
        valor_mercado=int(d.get("valor_mercado", 500)),
        suspenso=int(d.get("suspenso", 0)),
        contrato_rodadas=int(d.get("contrato_rodadas", 20)),
        gols_temp=int(d.get("gols_temp", 0)),
        partidas_temp=int(d.get("partidas_temp", 0)),
        amarelos_temp=int(d.get("amarelos_temp", 0)),
        vermelhos_temp=int(d.get("vermelhos_temp", 0)),
        gols_total=int(d.get("gols_total", 0)),
        partidas_total=int(d.get("partidas_total", 0)),
        amarelos_total=int(d.get("amarelos_total", 0)),
        vermelhos_total=int(d.get("vermelhos_total", 0)),
        season_base_ovr=float(d["season_base_ovr"]) if d.get("season_base_ovr") is not None else None,
        is_star=bool(d.get("is_star", False)),
    )


def _dict_to_team(d: dict):
    from models import Team, Formation, Postura
    formation_map = {f.value: f for f in Formation}
    postura_map = {p.value: p for p in Postura}
    return Team(
        id=int(d["id"]),
        name=d["name"],
        short_name=d.get("short_name", d["name"][:3].upper()),
        city=d.get("city", ""),
        state=d.get("state", ""),
        stadium=d.get("stadium", ""),
        division=int(d["division"]),
        prestige=int(d.get("prestige", 70)),
        primary_color=d.get("primary_color", "green"),
        secondary_color=d.get("secondary_color", "white"),
        torcida=int(d.get("torcida", 1_000_000)),
        caixa=int(d.get("caixa", 50_000)),
        salario_mensal=int(d.get("salario_mensal", 5_000)),
        stadium_level=int(d.get("stadium_level", 1)),
        loan_balance=int(d.get("loan_balance", 0)),
        loan_monthly_payment=int(d.get("loan_monthly_payment", 0)),
        loan_months_left=int(d.get("loan_months_left", 0)),
        formation=formation_map.get(d.get("formation", "4-4-2"), Formation.F442),
        postura=postura_map.get(d.get("postura", "Equilibrado"), Postura.EQUILIBRADO),
        coach=_dict_to_coach(d["coach"]),
        players=[_dict_to_player(p) for p in d.get("players", [])],
        training_targets=list(d.get("training_targets") or []),
        training_round_applied=int(d.get("training_round_applied", -1)),
        rivalry_points={int(k): float(v) for k, v in (d.get("rivalry_points") or {}).items()},
        dynamic_rivals=[int(x) for x in (d.get("dynamic_rivals") or [])],
        div_wins=int(d.get("div_wins", 0)),
        div_draws=int(d.get("div_draws", 0)),
        div_losses=int(d.get("div_losses", 0)),
        div_gf=int(d.get("div_gf", 0)),
        div_ga=int(d.get("div_ga", 0)),
        last_results=list(d.get("last_results") or []),
        copa_wins=int(d.get("copa_wins", 0)),
        copa_draws=int(d.get("copa_draws", 0)),
        copa_losses=int(d.get("copa_losses", 0)),
        copa_gf=int(d.get("copa_gf", 0)),
        copa_ga=int(d.get("copa_ga", 0)),
        copa_group=int(d.get("copa_group", 0)),
        copa_phase=d.get("copa_phase", "grupos"),
    )


def _make_stub_team(team_id: int, name: str):
    """Time mínimo para resultados históricos sem o time original."""
    from models import Team, Coach
    label = name or "?"
    return Team(
        id=team_id,
        name=label,
        short_name=label[:3].upper() if label != "?" else "???",
        city="", state="", stadium="",
        division=1, prestige=50,
        coach=Coach(name="Técnico"),
    )


def _dict_to_match_result(d: dict, team_by_id: dict):
    from models import MatchResult
    home_id = int(d.get("home_team_id", 0))
    away_id = int(d.get("away_team_id", 0))
    home_team = team_by_id.get(home_id) or _make_stub_team(home_id, d.get("home_team_name", "?"))
    away_team = team_by_id.get(away_id) or _make_stub_team(away_id, d.get("away_team_name", "?"))
    return MatchResult(
        home_team=home_team,
        away_team=away_team,
        home_goals=int(d.get("home_goals", 0)),
        away_goals=int(d.get("away_goals", 0)),
        home_scorers=list(d.get("home_scorers") or []),
        away_scorers=list(d.get("away_scorers") or []),
        competition=d.get("competition", "Liga"),
        matchday=int(d.get("matchday", 0)),
        attendance=int(d.get("attendance", 0)),
        income=int(d.get("income", 0)),
        home_used_names=list(d.get("home_used_names") or []),
        away_used_names=list(d.get("away_used_names") or []),
    )


def _dict_to_fixture(d: dict, team_by_id: dict):
    from models import Fixture
    home_id = int(d.get("home_team_id", 0))
    away_id = int(d.get("away_team_id", 0))
    home_team = team_by_id.get(home_id) or _make_stub_team(home_id, "?")
    away_team = team_by_id.get(away_id) or _make_stub_team(away_id, "?")
    result_data = d.get("result")
    result = _dict_to_match_result(result_data, team_by_id) if result_data else None
    return Fixture(
        home_team=home_team,
        away_team=away_team,
        competition=d.get("competition", "Liga"),
        matchday=int(d.get("matchday", 1)),
        result=result,
    )


def _dict_to_cup_tie(d: dict, team_by_id: dict):
    from models import CupTie
    a_id = int(d.get("team_a_id", 0))
    b_id = int(d.get("team_b_id", 0))
    team_a = team_by_id.get(a_id) or _make_stub_team(a_id, "?")
    team_b = team_by_id.get(b_id) or _make_stub_team(b_id, "?")
    leg1_data = d.get("leg1")
    leg2_data = d.get("leg2")
    ps_raw = d.get("penalty_score")
    return CupTie(
        team_a=team_a,
        team_b=team_b,
        phase=d.get("phase", "oitavas"),
        leg1=_dict_to_match_result(leg1_data, team_by_id) if leg1_data else None,
        leg2=_dict_to_match_result(leg2_data, team_by_id) if leg2_data else None,
        single_leg=bool(d.get("single_leg", True)),
        penalty_winner_id=d.get("penalty_winner_id"),
        penalty_score=tuple(ps_raw) if ps_raw is not None else None,
    )


def _dict_to_season(d: dict, team_by_id: dict):
    from season import Season

    all_teams = list(team_by_id.values())

    results_history = [
        _dict_to_match_result(r, team_by_id)
        for r in (d.get("results_history") or [])
    ]

    calendar = []
    for md in (d.get("calendar") or []):
        fixtures = [_dict_to_fixture(f, team_by_id) for f in (md.get("fixtures") or [])]
        ties = [_dict_to_cup_tie(ct, team_by_id) for ct in (md.get("ties") or [])]
        calendar.append({
            "label": md.get("label", ""),
            "cup_leg": md.get("cup_leg", 1),
            "fixtures": fixtures,
            "ties": ties,
        })

    # league_fixtures é a lista plana de todas as fixtures de liga do calendário
    league_fixtures = [
        f for md in calendar
        for f in md.get("fixtures", [])
        if f.competition == "Liga"
    ]

    def _load_ties(key: str) -> list:
        return [_dict_to_cup_tie(ct, team_by_id) for ct in (d.get(key) or [])]

    copa_final_data = d.get("copa_final")
    copa_final = _dict_to_cup_tie(copa_final_data, team_by_id) if copa_final_data else None

    copa_champion_id = d.get("copa_champion_id")
    copa_champion = team_by_id.get(copa_champion_id) if copa_champion_id is not None else None

    return Season(
        year=int(d.get("year", 2024)),
        all_teams=all_teams,
        player_team_id=int(d.get("player_team_id", -1)),
        league_fixtures=league_fixtures,
        results_history=results_history,
        calendar=calendar,
        current_matchday=int(d.get("current_matchday", 0)),
        season_over=bool(d.get("season_over", False)),
        copa_primeira_fase=_load_ties("copa_primeira_fase"),
        copa_oitavas=_load_ties("copa_oitavas"),
        copa_quartas=_load_ties("copa_quartas"),
        copa_semi=_load_ties("copa_semi"),
        copa_final=copa_final,
        copa_champion=copa_champion,
        top_scorers=list(d.get("top_scorers") or []),
        division_champions={int(k): v for k, v in (d.get("division_champions") or {}).items()},
        division_champion_coaches={int(k): v for k, v in (d.get("division_champion_coaches") or {}).items()},
        best_team_goals=dict(d.get("best_team_goals") or {}),
        best_player_goals=dict(d.get("best_player_goals") or {}),
        max_attendance=dict(d.get("max_attendance") or {}),
        max_income=dict(d.get("max_income") or {}),
        final_positions={int(k): v for k, v in (d.get("final_positions") or {}).items()},
        shown_cup_draws=list(d.get("shown_cup_draws") or []),
    )


def _dict_to_career(d: dict):
    from models import CareerState
    seen_raw = d.get("seen_notifications") or []
    return CareerState(
        player_coach=_dict_to_coach(d["player_coach"]),
        current_team_id=d.get("current_team_id"),
        unemployed=bool(d.get("unemployed", False)),
        fired=bool(d.get("fired", False)),
        last_fired_team_id=d.get("last_fired_team_id"),
        games_in_charge=int(d.get("games_in_charge", 0)),
        rounds_unemployed=int(d.get("rounds_unemployed", 0)),
        season_history=list(d.get("season_history") or []),
        world_history=dict(d.get("world_history") or {}),
        free_coaches=[_dict_to_coach(c) for c in (d.get("free_coaches") or [])],
        notifications=list(d.get("notifications") or []),
        seen_notifications=set(seen_raw),
        event_log=list(d.get("event_log") or []),
        coach_market_last_round=int(d.get("coach_market_last_round", -1)),
        coach_market_cooldown=dict(d.get("coach_market_cooldown") or {}),
    )


def _dict_to_market(d: dict):
    from transfers import TransferMarket
    return TransferMarket(
        history=list(d.get("history") or []),
        bid_stats_by_ovr_bucket=dict(d.get("bid_stats_by_ovr_bucket") or {}),
        transfer_records=list(d.get("transfer_records") or []),
    )


def _dict_to_game_state(data: dict) -> dict:
    """Reconstrói o estado completo do jogo a partir de um dict JSON."""
    teams_data = data.get("teams") or []
    teams = [_dict_to_team(d) for d in teams_data]
    team_by_id = {t.id: t for t in teams}

    career = None
    career_data = data.get("career")
    if career_data:
        career = _dict_to_career(career_data)
        normalize_world_history(career)

    season = None
    season_data = data.get("season")
    if season_data:
        season = _dict_to_season(season_data, team_by_id)

    market = None
    market_data = data.get("market")
    if market_data:
        market = _dict_to_market(market_data)

    player_team = None
    if career and not getattr(career, "unemployed", False) and career.current_team_id is not None:
        player_team = team_by_id.get(career.current_team_id)

    return {
        "season": season,
        "player_team": player_team,
        "market": market,
        "career": career,
        "__save_meta__": dict(data.get("__save_meta__", {})),
    }


# ── Save e Load ────────────────────────────────────────────────

def save_game(game_state: dict) -> bool:
    """Salva o estado do jogo em JSON.

    Cria backup (save.bak.json) antes de cada nova gravação.
    Retorna True em caso de sucesso.
    """
    try:
        _ensure_dir()
        if isinstance(game_state, dict):
            meta = dict(game_state.get("__save_meta__", {}) or {})
            meta["version"] = SAVE_VERSION
            meta["saved_at"] = time.time()
            game_state["__save_meta__"] = meta

        json_save = SAVE_DIR / "save.json"
        json_bak  = SAVE_DIR / "save.bak.json"
        if json_save.exists():
            shutil.copy2(json_save, json_bak)

        payload = _game_state_to_dict(game_state)
        with open(json_save, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))

        # Exportação legível (resumo simplificado) — falha silenciosa
        try:
            export_save_json(game_state)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False


def _migrate_loaded_state(state: dict) -> dict:
    """Normaliza campos novos em saves legados sem exigir novo jogo."""
    if not isinstance(state, dict):
        return state

    meta = dict(state.get("__save_meta__", {}) or {})
    if "version" not in meta:
        meta["version"] = 1
    state["__save_meta__"] = meta

    season = state.get("season")
    if season is not None:
        if not hasattr(season, "shown_cup_draws") or not isinstance(getattr(season, "shown_cup_draws"), list):
            season.shown_cup_draws = []
        results = list(getattr(season, "results_history", []) or [])
        for result in results:
            if not hasattr(result, "home_used_names") or not isinstance(getattr(result, "home_used_names"), list):
                result.home_used_names = []
            if not hasattr(result, "away_used_names") or not isinstance(getattr(result, "away_used_names"), list):
                result.away_used_names = []

    career = state.get("career")
    if career is not None:
        if not hasattr(career, "coach_market_last_round"):
            career.coach_market_last_round = -1
        if not hasattr(career, "coach_market_cooldown") or not isinstance(getattr(career, "coach_market_cooldown"), dict):
            career.coach_market_cooldown = {}
        if not hasattr(career, "notifications") or not isinstance(getattr(career, "notifications"), list):
            career.notifications = []
        if not hasattr(career, "seen_notifications") or not isinstance(getattr(career, "seen_notifications"), set):
            career.seen_notifications = set()
        if not hasattr(career, "event_log") or not isinstance(getattr(career, "event_log"), list):
            career.event_log = []

    market = state.get("market")
    if market is not None:
        if not hasattr(market, "bid_stats_by_ovr_bucket") or not isinstance(getattr(market, "bid_stats_by_ovr_bucket"), dict):
            market.bid_stats_by_ovr_bucket = {}
        if not hasattr(market, "transfer_records") or not isinstance(getattr(market, "transfer_records"), list):
            market.transfer_records = []

    all_teams = []
    if season is not None:
        all_teams = list(getattr(season, "all_teams", []) or [])
    elif state.get("player_team") is not None:
        all_teams = [state["player_team"]]

    for team in all_teams:
        if not hasattr(team, "training_targets") or not isinstance(getattr(team, "training_targets"), list):
            team.training_targets = []
        if not hasattr(team, "training_round_applied"):
            team.training_round_applied = -1
        if not hasattr(team, "rivalry_points") or not isinstance(getattr(team, "rivalry_points"), dict):
            team.rivalry_points = {}
        if not hasattr(team, "dynamic_rivals") or not isinstance(getattr(team, "dynamic_rivals"), list):
            team.dynamic_rivals = []
        if not hasattr(team, "loan_balance"):
            team.loan_balance = 0
        if not hasattr(team, "loan_monthly_payment"):
            team.loan_monthly_payment = 0
        if not hasattr(team, "loan_months_left"):
            team.loan_months_left = 0
        for player in list(getattr(team, "players", []) or []):
            if not hasattr(player, "is_star"):
                player.is_star = False
            if not hasattr(player, "season_base_ovr"):
                player.season_base_ovr = None

    # Migra histórico mundial para saves antigos.
    if career is not None:
        normalize_world_history(career)

    return state


def load_game() -> Optional[dict]:
    """Carrega um jogo salvo. Tenta JSON primeiro, depois pickle legado."""
    json_save = SAVE_DIR / "save.json"
    json_bak  = SAVE_DIR / "save.bak.json"

    # 1. Tenta o save JSON primário
    if json_save.exists():
        try:
            with open(json_save, "r", encoding="utf-8") as f:
                data = json.load(f)
            state = _dict_to_game_state(data)
            # Persiste para atualizar versão / normalizar campos novos
            save_game(state)
            return state
        except Exception as e:
            print(f"Erro ao carregar save JSON: {e}")
            # Tenta o backup JSON
            if json_bak.exists():
                try:
                    print("  Tentando carregar backup JSON...")
                    with open(json_bak, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    state = _dict_to_game_state(data)
                    save_game(state)
                    return state
                except Exception as e2:
                    print(f"Erro ao carregar backup JSON: {e2}")

    # 2. Fallback: save pickle legado (converte automaticamente para JSON)
    if SAVE_FILE.exists():
        try:
            print("  Carregando save legado (pickle)...")
            with open(SAVE_FILE, "rb") as f:
                state = pickle.load(f)
            state = _migrate_loaded_state(state)
            # Converte para JSON e salva no novo formato
            save_game(state)
            return state
        except Exception as e:
            print(f"Erro ao carregar save pickle: {e}")
            if BACKUP_FILE.exists():
                try:
                    print("  Tentando carregar backup pickle...")
                    with open(BACKUP_FILE, "rb") as f:
                        state = pickle.load(f)
                    state = _migrate_loaded_state(state)
                    save_game(state)
                    return state
                except Exception as e2:
                    print(f"Erro ao carregar backup pickle: {e2}")

    return None


def save_exists() -> bool:
    return (SAVE_DIR / "save.json").exists() or SAVE_FILE.exists()


# ── Exportação JSON legível (sumário simplificado) ─────────────

def export_save_json(game_state: dict, path: Optional[Path] = None) -> Optional[Path]:
    """Exporta um sumário legível do jogo para JSON (teams + career apenas).

    Este arquivo é gerado como conveniência para leitura humana.
    O save completo e restaurável é o save.json gerado por save_game().

    Retorna o caminho do arquivo gerado ou None em caso de erro.
    """
    dest = Path(path) if path else JSON_BACKUP_FILE
    try:
        _ensure_dir()
        season = game_state.get("season")
        all_teams = list(getattr(season, "all_teams", []) or []) if season else []

        payload: dict = {
            "__save_meta__": {
                "version": SAVE_VERSION,
                "exported_at": time.time(),
                "format": "classicfoot-json-summary-v1",
            },
            "teams": [_team_to_dict(t) for t in all_teams],
            "career": _career_to_dict(game_state["career"]) if game_state.get("career") else None,
        }
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
        return dest
    except Exception as e:
        print(f"Erro ao exportar JSON: {e}")
        return None


def import_save_json(path: Optional[Path] = None):
    """Importa um backup JSON de sumário e reconstrói teams e career.

    Retorna um dict parcial com 'teams' e 'career' reconstituídos, ou None.
    Para carregar um save completo, use load_game().
    """
    src = Path(path) if path else JSON_BACKUP_FILE
    if not src.exists():
        return None
    try:
        with open(src, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Se for um save completo (v2+), usa o loader completo
        fmt = (data.get("__save_meta__") or {}).get("format", "")
        if fmt == "classicfoot-json-v2":
            return _dict_to_game_state(data)

        # Sumário legado: apenas teams + career
        teams_data = data.get("teams") or []
        teams = [_dict_to_team(d) for d in teams_data]

        career = None
        career_data = data.get("career")
        if career_data:
            career = _dict_to_career(career_data)
            normalize_world_history(career)

        return {"teams": teams, "career": career}
    except Exception as e:
        print(f"Erro ao importar JSON: {e}")
        return None
