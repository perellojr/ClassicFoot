"""
ClassicFoot - Sistema de save/load
Usa pickle para persistir o estado completo do jogo.
"""
import pickle
import os
from typing import Optional

SAVE_FILE = "classicfoot_save.pkl"


def save_game(game_state: dict) -> bool:
    """Salva o estado do jogo no disco."""
    try:
        with open(SAVE_FILE, "wb") as f:
            pickle.dump(game_state, f)
        return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False


def load_game() -> Optional[dict]:
    """Carrega um jogo salvo. Retorna None se não existir."""
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Erro ao carregar: {e}")
        return None


def save_exists() -> bool:
    return os.path.exists(SAVE_FILE)
