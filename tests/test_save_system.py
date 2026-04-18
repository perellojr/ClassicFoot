import pickle
import tempfile
import unittest
from pathlib import Path

import save
from models import CareerState, Coach


def _make_legacy_career_v1() -> CareerState:
    """
    Simula um CareerState de save antigo (versão 1) sem os campos novos:
    world_history sem as chaves acumuladas, season_history com 2 entradas.
    """
    coach = Coach(name="Técnico Legado")
    career = CareerState(player_coach=coach, current_team_id=1)
    career.season_history = [
        {
            "year": 2025,
            "team": "Flamengo",
            "division": 1,
            "position": 1,
            "copa_phase": "campeão",
            "top_scorer": ("Gabi", "Flamengo", 18),
            "copa_champion": "Flamengo",
            "league_points_best_team": "Flamengo",
            "league_points_best_points": 72,
            "league_best_attack_team": "Flamengo",
            "league_best_attack_goals": 85,
        },
    ]
    # world_history sem chaves acumuladas — estado antigo típico
    career.world_history = {
        "division_champions": [{"year": 2025, "division": 1, "team": "Flamengo", "coach": "Técnico Legado"}],
        "biggest_win": {"diff": 0, "score": "-", "winner": "-", "loser": "-", "year": 0},
        "max_attendance": {"attendance": 0, "home": "-", "away": "-", "year": 0},
        "max_income": {"income": 0, "home": "-", "away": "-", "year": 0},
    }
    return career


class SaveSystemTests(unittest.TestCase):
    def test_save_and_load_with_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_dir = save.SAVE_DIR
            original_file = save.SAVE_FILE
            original_backup = save.BACKUP_FILE
            try:
                save.SAVE_DIR = tmp_path
                save.SAVE_FILE = tmp_path / "save.pkl"
                save.BACKUP_FILE = tmp_path / "save.bak.pkl"

                self.assertTrue(save.save_game({"value": 1}))
                self.assertTrue(save.SAVE_FILE.exists())

                self.assertTrue(save.save_game({"value": 2}))
                self.assertTrue(save.BACKUP_FILE.exists())

                loaded = save.load_game()
                self.assertEqual(2, loaded["value"])
                self.assertIn("__save_meta__", loaded)
                self.assertGreaterEqual(int(loaded["__save_meta__"].get("version", 0)), save.SAVE_VERSION)
            finally:
                save.SAVE_DIR = original_dir
                save.SAVE_FILE = original_file
                save.BACKUP_FILE = original_backup


class SaveMigrationTests(unittest.TestCase):
    """Verifica que saves antigos são migrados correctamente ao carregar."""

    def _save_legacy(self, tmp_path: Path, state: dict) -> None:
        """Grava um save sem metadados de versão — simula save v1."""
        with open(tmp_path / "save.pkl", "wb") as f:
            pickle.dump(state, f)

    def test_legacy_save_migration_adds_world_history_keys(self):
        """Um save antigo sem chaves acumuladas deve ganhar as chaves após load."""
        career = _make_legacy_career_v1()
        state = {"career": career}

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            original_dir, original_file, original_backup = save.SAVE_DIR, save.SAVE_FILE, save.BACKUP_FILE
            try:
                save.SAVE_DIR = tmp_path
                save.SAVE_FILE = tmp_path / "save.pkl"
                save.BACKUP_FILE = tmp_path / "save.bak.pkl"

                self._save_legacy(tmp_path, state)
                loaded = save.load_game()

                migrated_career = loaded["career"]
                world = migrated_career.world_history

                # Chaves acumuladas devem existir após migração.
                self.assertIn("div1_titles_by_club", world)
                self.assertIn("league_points_cumulative", world)
                self.assertIn("team_goals_cumulative", world)
                self.assertIn("player_goals_cumulative", world)
                self.assertIn("coach_titles", world)

                # Títulos da Div 1 devem ter sido reconstruídos.
                self.assertEqual(1, world["div1_titles_by_club"].get("Flamengo", 0))

                # Recordes devem estar preenchidos (não "{team: '-'}").
                self.assertNotEqual("-", world.get("league_points_record", {}).get("team"))

            finally:
                save.SAVE_DIR = original_dir
                save.SAVE_FILE = original_file
                save.BACKUP_FILE = original_backup

    def test_legacy_save_migration_idempotent(self):
        """Chamar normalize_world_history duas vezes não duplica dados."""
        career = _make_legacy_career_v1()
        save.normalize_world_history(career)
        titles_after_first = dict(career.world_history.get("div1_titles_by_club", {}))

        save.normalize_world_history(career)
        titles_after_second = career.world_history.get("div1_titles_by_club", {})

        self.assertEqual(titles_after_first, titles_after_second)


if __name__ == "__main__":
    unittest.main()
