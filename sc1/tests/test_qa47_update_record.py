"""Portable updates recover the record selection without opening a player save."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from sc1.manager.preferences import startup_database
from sc1.manager.ui import ManagerWindow


class UpdateRecord(unittest.TestCase):
    def test_first_launch_reuses_latest_existing_sibling_selection_without_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            saved = root / 'existing.sqlite3'
            saved.write_bytes(b'opaque player record; must never be opened as SQLite')
            current = root / 'SC1_Roguelike_QA47/sc1/data/manager_preferences.json'
            for revision in (45, 46):
                path = root / f'SC1_Roguelike_QA{revision}/sc1/data/manager_preferences.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(dict(version=1, last_database=str(saved))), encoding='utf8')
            before = saved.read_bytes()
            self.assertEqual(startup_database(preferences_path=current), saved)
            self.assertFalse(current.exists())
            self.assertEqual(saved.read_bytes(), before)

    def test_explicit_current_selection_wins_and_missing_current_save_never_falls_back(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            old = root / 'old.sqlite3'; old.write_bytes(b'old')
            current_save = root / 'new.sqlite3'; current_save.write_bytes(b'new')
            for name, db in (('QA46', old), ('QA47', current_save)):
                path = root / f'SC1_Roguelike_{name}/sc1/data/manager_preferences.json'
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps(dict(version=1, last_database=str(db))), encoding='utf8')
            prefs = root / 'SC1_Roguelike_QA47/sc1/data/manager_preferences.json'
            self.assertEqual(startup_database(preferences_path=prefs), current_save)
            self.assertEqual(startup_database(old, preferences_path=prefs), old)
            current_save.unlink()
            with self.assertRaises(FileNotFoundError):
                startup_database(preferences_path=prefs)

    def test_missing_or_corrupt_sibling_settings_are_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'SC1_Roguelike_QA46/sc1/data/manager_preferences.json'
            path.parent.mkdir(parents=True)
            current = root / 'SC1_Roguelike_QA47/sc1/data/manager_preferences.json'
            default = root / 'default.sqlite3'
            for value in ('{', '[]', json.dumps(dict(version=1, last_database=str(root / 'missing.sqlite3')))):
                path.write_text(value, encoding='utf8')
                with patch('sc1.manager.preferences.DEFAULT_DATABASE', default):
                    self.assertEqual(startup_database(preferences_path=current), default)

    def test_locked_mission_status_explains_how_to_recover_the_record(self):
        from unittest.mock import Mock
        app = Mock()
        ManagerWindow.update_connection_status(app, json.dumps(dict(status='map_request_rejected', error_code='mission_locked')))
        self.assertIn('기존에 진행하던 기록', app.connection.set.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
