import json
import tempfile
import unittest
from pathlib import Path

from modules.config_manager import save_config


class ConfigSaveSafetyTests(unittest.TestCase):
    def test_save_is_atomic_and_backs_up_previous_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.json"
            old = {"OPENAI_MODEL_NAME": "old-model", "marker": "before"}
            new = {"OPENAI_MODEL_NAME": "new-model", "marker": "after"}
            path.write_text(json.dumps(old), encoding="utf-8")

            self.assertTrue(save_config(new, str(path)))
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), new)

            backups = list((Path(tmp) / "backups").glob("config.*.json"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(
                json.loads(backups[0].read_text(encoding="utf-8")), old
            )
            self.assertEqual(list(Path(tmp).glob(".config.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
