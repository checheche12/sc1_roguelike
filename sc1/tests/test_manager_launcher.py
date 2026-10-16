"""Withdrawn manager tests with mocked installer; never launch or patch a game."""
import gc
import json
from pathlib import Path
import sys
import tempfile
import tkinter as tk
import types
import unittest
from unittest.mock import Mock, patch

from sc1.manager import preferences
from sc1.manager.ui import ManagerWindow


class ManagerLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sc1-manager-launch-")
        self.base = Path(self.tmp.name)
        self.prefs = self.base / "preferences.json"
        self.root = tk.Tk()
        self.root.withdraw()
        self.backend = types.ModuleType("sc1.manager.installation")
        self.backend.inspect_installation = Mock(return_value={"status": "ready", "message": "설치 확인"})
        self.backend.install_package = Mock(return_value={"status": "installed", "message": "패치 설치 완료"})
        self.backend.restore_installation = Mock(return_value={"status": "restored", "message": "이전 패치 복원"})
        self.backend.restore_original_campaign = Mock(return_value={"status": "original", "mode": "original", "message": "원본 복귀"})
        self.backend.launch_campaign = Mock(return_value={
            "status": "started", "message": "게임 시작",
            "executable": str(self.base / "StarCraft.exe"), "started_after": 12345})
        self.app = ManagerWindow(self.root, self.base / "first.sqlite3", preferences_path=self.prefs)
        self.app.game_path.set(str(self.base))

    def tearDown(self):
        self.app.closed = True
        for timer in self.root.tk.call("after", "info"):
            self.root.after_cancel(timer)
        self.root.update_idletasks()
        self.root.destroy()
        self.app = self.root = None
        gc.collect()
        self.tmp.cleanup()

    def act(self, action):
        def immediate_thread(*args, **kwargs):
            return Mock(start=kwargs["target"])
        with patch.dict(sys.modules, {"sc1.manager.installation": self.backend}), \
             patch("sc1.manager.ui.threading.Thread", side_effect=immediate_thread):
            self.app.installation_action(action)
        self.app.drain_events()

    def test_opening_manager_does_not_start_or_install_game(self):
        self.assertFalse(self.app.auto_connect_enabled)
        for callback in (self.backend.launch_campaign, self.backend.install_package,
                         self.backend.restore_installation):
            callback.assert_not_called()

    def test_record_can_be_switched_before_explicit_start(self):
        second = self.base / "second.sqlite3"
        self.assertTrue(self.app.switch_database(second))
        before = second.read_bytes()
        self.act("launch")
        self.backend.launch_campaign.assert_called_once_with(str(self.base), with_manager=False, allow_growth=True)
        self.assertEqual(self.app.database, second)
        self.assertEqual(second.read_bytes(), before)
        self.assertEqual(preferences.startup_database(preferences_path=self.prefs), second)
        self.assertEqual(preferences.startup_game_path(preferences_path=self.prefs), self.base)
        self.assertTrue(self.app.auto_connect_enabled)
        self.assertEqual(self.app.auto_connect_target.started_after, 12345)
        self.assertEqual(self.app.auto_connect_target.image, str(self.base / "StarCraft.exe"))

    def test_install_and_restore_are_explicit_and_never_start_game(self):
        before = self.app.database.read_bytes()
        for action in ("inspect", "install", "restore"):
            self.act(action)
        self.backend.inspect_installation.assert_called_once()
        self.backend.install_package.assert_called_once()
        self.backend.restore_installation.assert_called_once()
        self.backend.launch_campaign.assert_not_called()
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertEqual(self.app.database.read_bytes(), before)

    def test_busy_install_blocks_record_switch_and_duplicate_action(self):
        def delayed_thread(*args, **kwargs):
            return Mock(start=lambda: None)
        with patch("sc1.manager.ui.threading.Thread", side_effect=delayed_thread):
            self.app.installation_action("install")
            self.assertTrue(self.app.installation_busy)
            self.assertFalse(self.app.switch_database(self.base / "other.sqlite3"))
            self.app.installation_action("launch")
        self.backend.launch_campaign.assert_not_called()
        self.assertFalse((self.base / "other.sqlite3").exists())
        self.assertEqual(str(self.app.open_record_button.cget("state")), "disabled")

    def test_failed_launch_does_not_rebind_or_modify_record(self):
        self.backend.launch_campaign.side_effect = ValueError("게임 버전이 다릅니다")
        before = self.app.database.read_bytes()
        with patch("sc1.manager.ui.messagebox.showerror") as error:
            self.act("launch")
        error.assert_called_once()
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertFalse(self.app.installation_busy)
        self.assertEqual(self.app.database.read_bytes(), before)

    def test_probe_record_cannot_launch_campaign(self):
        probe = self.base / "probe.sqlite3"
        from sc1.manager.store import CampaignStore
        CampaignStore(probe)
        self.app.switch_database(probe)
        self.backend.launch_campaign.side_effect = ValueError("성장 모드를 시작하려면 캠페인 기록을 열어 주세요.")
        with patch("sc1.manager.ui.messagebox.showerror") as error:
            self.act("launch")
        error.assert_called_once()
        self.backend.launch_campaign.assert_called_once_with(str(self.base), with_manager=False, allow_growth=False)
        self.assertFalse(self.app.auto_connect_enabled)

    def test_settings_preserve_both_paths_and_unknown_fields(self):
        payload = json.loads(self.prefs.read_text(encoding="utf-8"))
        payload["other_setting"] = {"keep": True}
        self.prefs.write_text(json.dumps(payload), encoding="utf-8")
        preferences.remember_game_path(self.base, preferences_path=self.prefs)
        preferences.remember_database(self.app.database, preferences_path=self.prefs)
        updated = json.loads(self.prefs.read_text(encoding="utf-8"))
        self.assertEqual(updated["other_setting"], {"keep": True})
        self.assertEqual(updated["game_path"], str(self.base))
        self.assertEqual(updated["last_database"], str(self.app.database))


    def test_missing_backend_is_graceful_and_never_launches(self):
        def immediate_thread(*args, **kwargs):
            return Mock(start=kwargs["target"])
        with patch("sc1.manager.ui.threading.Thread", side_effect=immediate_thread), \
             patch("sc1.manager.ui.messagebox.showerror") as error, \
             patch("sc1.manager.ui.importlib.import_module",
                   side_effect=ModuleNotFoundError(name="sc1.manager.installation")):
            self.app.installation_action("launch")
            self.app.drain_events()
        error.assert_not_called()
        self.assertIn("준비 중", self.app.installation_hint.get())
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertFalse(self.app.closed)
        self.backend.launch_campaign.assert_not_called()

    def test_cli_has_explicit_isolated_preferences_path(self):
        from sc1.manager.__main__ import main
        with patch("sc1.manager.ui.launch") as launch:
            self.assertEqual(main(["--db", str(self.app.database), "--preferences", str(self.prefs), "ui"]), 0)
        self.assertEqual(launch.call_args.args[0], self.app.database)
        self.assertEqual(launch.call_args.kwargs["preferences_path"], self.prefs)

    def test_original_restore_stops_bridge_without_changing_growth_record(self):
        before = self.app.database.read_bytes()
        self.app.auto_connect_enabled = True
        self.act("original")
        self.backend.restore_original_campaign.assert_called_once_with(str(self.base))
        self.backend.launch_campaign.assert_not_called()
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertIsNone(self.app.auto_connect_target)
        self.assertEqual(self.app.database.read_bytes(), before)
        self.assertIn("원본 캠페인", self.app.connection.get())

    def test_original_start_does_not_auto_connect_even_with_probe_record(self):
        from sc1.manager.store import CampaignStore
        probe = self.base / "probe.sqlite3"; CampaignStore(probe)
        self.app.switch_database(probe)
        before = probe.read_bytes()
        self.backend.launch_campaign.return_value.update(mode="original", auto_connect=False)
        self.act("launch")
        self.backend.launch_campaign.assert_called_once_with(str(self.base), with_manager=False, allow_growth=False)
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertIsNone(self.app.auto_connect_target)
        self.assertEqual(probe.read_bytes(), before)

    def test_five_installation_buttons_are_on_two_rows(self):
        buttons = self.app.installation_buttons
        self.assertEqual(len(buttons), 5)
        self.assertEqual([int(b.grid_info()["row"]) for b in buttons], [0, 0, 0, 1, 1])
        self.assertIn("원본 캠페인으로 되돌리기", [b.cget("text") for b in buttons])
        self.app.root.update_idletasks()
        self.assertLessEqual(buttons[0].master.winfo_reqwidth(), 680)

    def test_original_failure_keeps_connection_off_and_restores_controls(self):
        self.backend.restore_original_campaign.side_effect = ValueError("관리 폴더에 별도 파일")
        before = self.app.database.read_bytes()
        self.app.auto_connect_enabled = True
        with patch("sc1.manager.ui.messagebox.showerror") as error:
            self.act("original")
        error.assert_called_once()
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertFalse(self.app.installation_busy)
        self.assertEqual(self.app.database.read_bytes(), before)
        self.assertEqual(str(self.app.open_record_button.cget("state")), "normal")


if __name__ == "__main__":
    unittest.main()
