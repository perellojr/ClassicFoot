import tempfile
import unittest
from pathlib import Path

import save


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
            finally:
                save.SAVE_DIR = original_dir
                save.SAVE_FILE = original_file
                save.BACKUP_FILE = original_backup


if __name__ == "__main__":
    unittest.main()

