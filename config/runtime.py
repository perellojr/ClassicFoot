"""Configurações de runtime (seed, flags de execução)."""
import os
import random


def apply_random_seed_from_env() -> int | None:
    """
    Aplica semente global opcional para tornar a simulação reproduzível.
    Use: CLASSICFOOT_SEED=12345 python main.py
    """
    raw = os.getenv("CLASSICFOOT_SEED", "").strip()
    if not raw:
        return None
    try:
        seed = int(raw)
    except ValueError:
        return None
    random.seed(seed)
    return seed

