"""
ClassicFoot - Sistema de save/load
Usa pickle para persistir o estado completo do jogo.

O save é gravado em ~/.classicfoot/save.pkl para que o caminho seja
independente do diretório de trabalho. Um backup automático (save.bak.pkl)
é criado antes de cada nova gravação.
"""
import pickle
import shutil
from pathlib import Path
from typing import Optional

# ── Diretório de dados do usuário ─────────────────────────────
SAVE_DIR = Path.home() / ".classicfoot"
SAVE_FILE = SAVE_DIR / "save.pkl"
BACKUP_FILE = SAVE_DIR / "save.bak.pkl"


def _ensure_dir():
    SAVE_DIR.mkdir(parents=True, exist_ok=True)


def save_game(game_state: dict) -> bool:
    """Salva o estado do jogo no disco.

    Antes de gravar, faz backup do save anterior em save.bak.pkl.
    Retorna True em caso de sucesso.
    """
    try:
        _ensure_dir()
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

    market = state.get("market")
    if market is not None:
        if not hasattr(market, "bid_stats_by_ovr_bucket") or not isinstance(getattr(market, "bid_stats_by_ovr_bucket"), dict):
            market.bid_stats_by_ovr_bucket = {}

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
