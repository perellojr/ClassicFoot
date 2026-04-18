"""
ClassicFoot - Sistema de save/load
Usa pickle para persistir o estado completo do jogo.

O save é gravado em ~/.classicfoot/save.pkl para que o caminho seja
independente do diretório de trabalho. Um backup automático (save.bak.pkl)
é criado antes de cada nova gravação.

Migração de schema: _migrate_loaded_state aplica todas as normalizações
necessárias para saves antigos, incluindo backfill de histórico mundial.
"""
import pickle
import shutil
import time
from pathlib import Path
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from models import CareerState

# ── Diretório de dados do usuário ─────────────────────────────
SAVE_DIR = Path.home() / ".classicfoot"
SAVE_FILE = SAVE_DIR / "save.pkl"
BACKUP_FILE = SAVE_DIR / "save.bak.pkl"
SAVE_VERSION = 3


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
        rebuilt_titles = {}
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
        rebuilt_copa_titles = {}
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
        int(entry.get("year"))
        for entry in career.season_history
        if isinstance(entry, dict) and entry.get("year") is not None
    }
    years_from_champions = {
        int(item.get("year"))
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


def save_game(game_state: dict) -> bool:
    """Salva o estado do jogo no disco.

    Antes de gravar, faz backup do save anterior em save.bak.pkl.
    Retorna True em caso de sucesso.
    """
    try:
        _ensure_dir()
        if isinstance(game_state, dict):
            meta = dict(game_state.get("__save_meta__", {}) or {})
            meta["version"] = SAVE_VERSION
            meta["saved_at"] = time.time()
            game_state["__save_meta__"] = meta
        if SAVE_FILE.exists():
            shutil.copy2(SAVE_FILE, BACKUP_FILE)
        with open(SAVE_FILE, "wb") as f:
            pickle.dump(game_state, f)
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
    """Carrega um jogo salvo. Retorna None se não existir."""
    if not SAVE_FILE.exists():
        return None
    try:
        with open(SAVE_FILE, "rb") as f:
            state = pickle.load(f)
        state = _migrate_loaded_state(state)
        # Persiste migração para evitar retrabalho no próximo load.
        save_game(state)
        return state
    except Exception as e:
        print(f"Erro ao carregar save principal: {e}")
        # Tenta recuperar o backup automaticamente
        if BACKUP_FILE.exists():
            try:
                print("  Tentando carregar backup...")
                with open(BACKUP_FILE, "rb") as f:
                    state = pickle.load(f)
                state = _migrate_loaded_state(state)
                save_game(state)
                return state
            except Exception as e2:
                print(f"Erro ao carregar backup: {e2}")
        return None


def save_exists() -> bool:
    return SAVE_FILE.exists()
