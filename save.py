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


def load_game() -> Optional[dict]:
    """Carrega um jogo salvo. Retorna None se não existir."""
    if not SAVE_FILE.exists():
        return None
    try:
        with open(SAVE_FILE, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Erro ao carregar save principal: {e}")
        # Tenta recuperar o backup automaticamente
        if BACKUP_FILE.exists():
            try:
                print("  Tentando carregar backup...")
                with open(BACKUP_FILE, "rb") as f:
                    return pickle.load(f)
            except Exception as e2:
                print(f"Erro ao carregar backup: {e2}")
        return None


def save_exists() -> bool:
    return SAVE_FILE.exists()
