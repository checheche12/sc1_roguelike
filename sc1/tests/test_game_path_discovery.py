"""First launch on another PC must not suggest a nonexistent developer path."""
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
from sc1.manager import preferences


class GamePathDiscoveryTests(unittest.TestCase):
    def test_no_installation_leaves_selection_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(preferences, "_installed_game_candidates", return_value=iter([root / "missing"])):
                self.assertIsNone(preferences.startup_game_path(preferences_path=root / "prefs.json"))

    def test_discovered_install_root_resolves_x64_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            game = root / "StarCraft/x86_64/StarCraft.exe"
            game.parent.mkdir(parents=True)
            game.write_bytes(b"path selection only")
            with patch.object(preferences, "_installed_game_candidates", return_value=iter([root / "missing", game.parent.parent])):
                self.assertEqual(preferences.startup_game_path(preferences_path=root / "prefs.json"), game.resolve())

    def test_explicit_saved_selection_has_priority(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            prefs = root / "prefs.json"
            prefs.write_text(json.dumps({"version": 1, "game_path": str(root / "chosen")}), "utf8")
            with patch.object(preferences, "_installed_game_candidates") as discover:
                self.assertEqual(preferences.startup_game_path(preferences_path=prefs), root / "chosen")
                discover.assert_not_called()


if __name__ == "__main__":
    unittest.main()
