"""Temporary records only: selection survives launches without resetting saves."""
import gc
import json
from pathlib import Path
import queue
import tempfile
import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from sc1.manager import preferences
from sc1.manager.__main__ import main
from sc1.manager.store import open_campaign_store
from sc1.manager.ui import ManagerWindow, launch
from sc1.manager.auto_connect import AutoConnectTarget


class RecordPreferencesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sc1-record-selection-")
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.preferences = self.folder / "settings" / "manager.json"
        self.first = self.folder / "old.sqlite3"
        self.second = self.folder / "새 본편 기록.sqlite3"
        self.first.write_bytes(b"old record remains untouched")
        self.second.write_bytes(b"new record remains untouched")

    def test_last_opened_record_survives_restart_and_never_changes_records(self):
        before = {p: p.read_bytes() for p in (self.first, self.second)}
        for selected in (self.first, self.second):
            preferences.remember_database(selected, preferences_path=self.preferences)
            self.assertEqual(preferences.startup_database(preferences_path=self.preferences), selected.resolve())
        for p, raw in before.items():
            self.assertEqual(p.read_bytes(), raw)
        self.assertEqual(list(self.preferences.parent.iterdir()), [self.preferences])

    def test_explicit_record_wins_without_silently_changing_preference(self):
        preferences.remember_database(self.second, preferences_path=self.preferences)
        before = self.preferences.read_bytes()
        self.assertEqual(preferences.startup_database(self.first, preferences_path=self.preferences), self.first)
        self.assertEqual(self.preferences.read_bytes(), before)

    def test_first_launch_uses_default_but_missing_remembered_file_never_falls_back(self):
        self.assertEqual(preferences.startup_database(preferences_path=self.preferences), preferences.DEFAULT_DATABASE.resolve())
        preferences.remember_database(self.second, preferences_path=self.preferences)
        self.second.unlink()
        with self.assertRaises(FileNotFoundError):
            preferences.startup_database(preferences_path=self.preferences)
        self.assertFalse(self.second.exists())

    def test_corrupt_or_relative_preference_requires_selection(self):
        self.preferences.parent.mkdir()
        for raw in ("{", "[]", json.dumps({"version": 1, "last_database": "relative.sqlite3"}),
                    json.dumps({"version": 2, "last_database": str(self.first)})):
            self.preferences.write_text(raw)
            with self.assertRaises(OSError):
                preferences.startup_database(preferences_path=self.preferences)

    def test_failed_atomic_write_preserves_previous_selection(self):
        preferences.remember_database(self.first, preferences_path=self.preferences)
        before = self.preferences.read_bytes()
        with patch("sc1.manager.preferences.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                preferences.remember_database(self.second, preferences_path=self.preferences)
        self.assertEqual(self.preferences.read_bytes(), before)
        self.assertEqual(list(self.preferences.parent.iterdir()), [self.preferences])

    def test_both_normal_and_campaign_launch_resolve_remembered_file(self):
        preferences.remember_database(self.second, preferences_path=self.preferences)
        for target in (None, AutoConnectTarget("D:/Games/StarCraft.exe", 123)):
            instance = Mock(acquired=True)
            instance.__enter__ = Mock(return_value=instance)
            instance.__exit__ = Mock(return_value=False)
            with (patch("sc1.manager.ui.ManagerInstance", return_value=instance),
                  patch("sc1.manager.ui.request_path", return_value=self.folder / "request.json"),
                  patch("sc1.manager.ui.tk.Tk", return_value=Mock(winfo_screenheight=Mock(return_value=1080))),
                  patch("sc1.manager.ui.ManagerWindow") as window):
                launch(auto_connect_target=target, preferences_path=self.preferences)
            self.assertEqual(window.call_args.args[1], self.second)
            self.assertEqual(window.call_args.kwargs["auto_connect_target"], target)

    def test_cli_default_ui_defers_selection_and_explicit_db_remains_supported(self):
        with patch("sc1.manager.ui.launch") as ui:
            self.assertEqual(main(["ui"]), 0)
            self.assertIsNone(ui.call_args.args[0])
            self.assertEqual(main(["--db", str(self.second), "ui"]), 0)
            self.assertEqual(ui.call_args.args[0], self.second)

    def test_missing_remembered_file_cancellation_never_opens_old_default(self):
        preferences.remember_database(self.second, preferences_path=self.preferences)
        self.second.unlink()
        instance = Mock(acquired=True)
        instance.__enter__ = Mock(return_value=instance)
        instance.__exit__ = Mock(return_value=False)
        with (patch("sc1.manager.ui.ManagerInstance", return_value=instance),
              patch("sc1.manager.ui.request_path", return_value=self.folder / "request.json"),
              patch("sc1.manager.ui.tk.Tk") as tk_root,
              patch("sc1.manager.ui.messagebox.showwarning"),
              patch("sc1.manager.ui.filedialog.askopenfilename", return_value=""),
              patch("sc1.manager.ui.ManagerWindow") as window):
            tk_root.return_value.winfo_screenheight.return_value = 1080
            launch(preferences_path=self.preferences)
        window.assert_not_called()
        tk_root.return_value.destroy.assert_called_once()


class RecordSelectionWindowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sc1-record-ui-")
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.preferences = self.folder / "preferences.json"
        self.root = tk.Tk()
        self.root.withdraw()
        self.app = ManagerWindow(self.root, self.folder / "old.sqlite3", preferences_path=self.preferences)

    def tearDown(self):
        self.app.closed = True
        for timer in self.root.tk.call("after", "info"):
            self.root.after_cancel(timer)
        self.root.destroy()
        self.app = self.root = None
        gc.collect()

    def test_new_record_and_open_record_persist_without_overwriting_old_growth(self):
        old = self.app.database
        self.app.store.prepare_growth()
        before = old.read_bytes()
        new = self.folder / "new.sqlite3"
        with patch("sc1.manager.ui.filedialog.asksaveasfilename", return_value=str(new)):
            self.app.new_database()
        self.assertEqual(self.app.database, new)
        self.assertEqual(self.app.store.growth_status()["state"], "not_started")
        self.assertEqual(preferences.startup_database(preferences_path=self.preferences), new)
        self.assertEqual(old.read_bytes(), before)
        with patch("sc1.manager.ui.filedialog.askopenfilename", return_value=str(old)):
            self.app.open_database()
        self.assertEqual(preferences.startup_database(preferences_path=self.preferences), old)
        self.assertNotEqual(self.app.store.growth_status()["state"], "not_started")
        self.assertEqual(old.read_bytes(), before)

    def test_failed_record_open_keeps_selection_and_existing_connection(self):
        bad = self.folder / "invalid.sqlite3"
        bad.write_bytes(b"not a database")
        before = self.preferences.read_bytes()
        old_store = self.app.store
        child = Mock()
        self.app.process = child
        with patch("sc1.manager.ui.messagebox.showerror"):
            self.assertFalse(self.app.switch_database(bad))
        self.assertIs(self.app.store, old_store)
        self.assertIs(self.app.process, child)
        child.stdin.close.assert_not_called()
        self.assertEqual(self.preferences.read_bytes(), before)

    def test_connected_switch_finishes_old_writer_and_ignores_stale_events(self):
        new = self.folder / "new.sqlite3"
        open_campaign_store(new)
        child = Mock()
        child.poll.return_value = None
        self.app.process = child
        self.app.auto_connect_enabled = True
        self.app.discovering = True
        old_token = self.app.discovery_token
        old = self.app.database
        before = old.read_bytes()
        self.assertTrue(self.app.switch_database(new))
        child.wait.assert_called_once_with(timeout=3)
        self.assertTrue(child.stdin.close.called)
        self.assertIsNone(self.app.process)
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertFalse(self.app.discovering)
        self.assertGreater(self.app.discovery_token, old_token)
        self.app.events.put(("output", child, '{"event":"error","message":"old error"}'))
        self.app.events.put(("exit", child, 1))
        self.app.drain_events()
        self.assertIsNone(self.app.last_connection_error)
        self.assertEqual(self.app.database, new)
        self.assertEqual(old.read_bytes(), before)
        self.assertEqual(preferences.startup_database(preferences_path=self.preferences), new)


if __name__ == "__main__":
    unittest.main()
