"""Parâmetros financeiros e helpers de balanceamento econômico."""
from typing import Dict


BASE_PRIZE_YEAR = 2025
CUSTO_MANUTENCAO = 80  # R$ mil/mês por estádio (nível 1)

PRIZE_COPA = {
    "primeira_fase":    600,
    "oitavas":        1_600,
    "quartas":        4_000,
    "semi":           8_000,
    "final":         15_000,
    "campeão":       35_000,
    "vice":          15_000,
}

PRIZE_BEST_ATTACK = 3_000
PRIZE_BEST_DEFENSE = 3_000

SPONSOR_BASE_BY_DIV = {
    1: 3_000,  # R$ mil/mês
    2: 1_800,
    3: 1_000,
    4: 600,
}


def build_gradual_liga_prizes(top_prize: int = 12_000, bottom_prize: int = 2_500) -> Dict[int, Dict[int, int]]:
    """Gera uma tabela gradual de premiação para 4 divisões x 8 posições."""
    total_slots = 32
    step = (top_prize - bottom_prize) / max(1, total_slots - 1)
    values = [int(round(top_prize - (idx * step))) for idx in range(total_slots)]

    prizes: Dict[int, Dict[int, int]] = {1: {}, 2: {}, 3: {}, 4: {}}
    cursor = 0
    for division in [1, 2, 3, 4]:
        for position in range(1, 9):
            prizes[division][position] = values[cursor]
            cursor += 1
    return prizes


PRIZE_LIGA = build_gradual_liga_prizes()


def season_prize_multiplier(year: int) -> float:
    """Premiação cresce 5% por temporada (BASE_PRIZE_YEAR = 1.0)."""
    seasons_passed = max(0, int(year) - BASE_PRIZE_YEAR)
    return 1.05 ** seasons_passed

