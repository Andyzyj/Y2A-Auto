import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from modules import config_manager
from modules.config_manager import load_config, save_config, update_config


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

    def test_corrupt_config_recovers_latest_valid_backup_instead_of_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config_dir = root / "config"
            backup_dir = config_dir / "backups"
            backup_dir.mkdir(parents=True)
            (config_dir / "config.json").write_text('{"OPENAI_API_KEY":', encoding="utf-8")
            expected = dict(config_manager.DEFAULT_CONFIG)
            expected["OPENAI_MODEL_NAME"] = "kept-model"
            expected["AUTO_MODE_ENABLED"] = True
            (backup_dir / "config.20260101-000000-1.json").write_text(
                json.dumps(expected), encoding="utf-8"
            )

            with mock.patch.object(config_manager, "get_app_subdir", return_value=str(config_dir)):
                recovered = load_config()

            self.assertEqual(recovered["OPENAI_MODEL_NAME"], "kept-model")
            self.assertTrue(recovered["AUTO_MODE_ENABLED"])
            self.assertEqual(
                json.loads((config_dir / "config.json").read_text(encoding="utf-8"))["OPENAI_MODEL_NAME"],
                "kept-model",
            )

    def test_concurrent_partial_updates_do_not_erase_each_other(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_dir = Path(tmp) / "config"
            config_dir.mkdir(parents=True)
            initial = dict(config_manager.DEFAULT_CONFIG)
            (config_dir / "config.json").write_text(json.dumps(initial), encoding="utf-8")
            barrier = threading.Barrier(3)

            def worker(payload):
                barrier.wait()
                update_config(payload)

            with mock.patch.object(config_manager, "get_app_subdir", return_value=str(config_dir)):
                first = threading.Thread(target=worker, args=({"OPENAI_MODEL_NAME": "model-a"},))
                second = threading.Thread(target=worker, args=({"AUTO_MODE_ENABLED": "on"},))
                first.start()
                second.start()
                barrier.wait()
                first.join()
                second.join()
                final = load_config()

            self.assertEqual(final["OPENAI_MODEL_NAME"], "model-a")
            self.assertTrue(final["AUTO_MODE_ENABLED"])


if __name__ == "__main__":
    unittest.main()
