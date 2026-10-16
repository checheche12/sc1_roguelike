"""Installer tests: workspace fake installations, mocked processes and launches."""
import ctypes
import os
import threading
import time
import hashlib
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from sc1.manager import installation as app
from sc1.campaign.missions import load_missions


def pe():
    raw = bytearray(256); raw[:2] = b"MZ"; struct.pack_into("<I", raw, 0x3c, 128)
    raw[128:132] = b"PE\0\0"; struct.pack_into("<H", raw, 132, 0x8664); struct.pack_into("<H", raw, 152, 0x20b)
    return bytes(raw)


class RealSealedPackageTests(unittest.TestCase):
    def test_installer_accepts_actual_sealed_package_file_contract(self):
        """Read real production assets, independently of fake fixture constants."""
        from sc1.native_campaign.package_native_plugin import REQUIRED_DAT_NAMES
        path = app.WORKSPACE / "sc1/native_campaign/builds/all_campaigns_20261015_044207_441138_de686d254eb3/manifest.json"
        manifest = json.loads(path.read_text(encoding="utf8"))
        self.assertEqual(manifest["mode"], "native_all_campaigns")
        self.assertEqual(manifest["scenario_count"], 63)
        rows = manifest["files"]
        self.assertEqual(len(rows), 202)
        actual_dat = {r["path"].removeprefix("overlay/") for r in rows if r["path"].startswith("overlay/arr/")}
        self.assertEqual(actual_dat, set(REQUIRED_DAT_NAMES))
        self.assertEqual(actual_dat, {"arr/" + name + ".dat" for name in app.DAT_NAMES})
        self.assertIn("arr/mapdata.dat", actual_dat)
        self.assertNotIn("arr/sfxdata.dat", actual_dat)
        self.assertEqual(len({row["path"] for row in rows}), 202)
        for row in rows:
            with self.subTest(asset=row["path"]):
                raw = (path.parent / row["path"]).read_bytes()
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(app._sha(raw), row["sha256"])
        # Source hashes in the sealed manager manifest deliberately remain
        # immutable. This asset-closure test needs no manager-pin bypass when
        # source changes are awaiting the parent's separate resealing step.


class CampaignInstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sc1-inst-")
        self.root = Path(self.temp.name).resolve(); self.native = self.root / "native"; self.native.mkdir()
        self.game = self.root / "game"; (self.game / "x86_64").mkdir(parents=True)
        self.exe = self.game / "x86_64/StarCraft.exe"; self.exe.write_bytes(pe())
        (self.game / "original-casc-sentinel").write_bytes(b"original game data")
        self.manager = self.root / "manager.py"; self.manager.write_bytes(b"manager version1")
        (self.native / "samase64.exe").write_bytes(pe())
        self.pin = {"game_file_version_observed": "1.23.10.13515", "local_filename": "samase64.exe", "sha256": app._sha(pe())}
        self.pin_path = self.native / "pin.json"; self.pin_path.write_text(json.dumps(self.pin), encoding="utf8")
        self.package = self.root / "package"; self.package.mkdir()
        self.manifest_path = self.package / "manifest.json"
        self.manifest = {"mode": "native_all_campaigns", "schema_version": 3, "scenario_count": 63, "loader_sha256": self.pin["sha256"],
                         "inputs": {"manager_sources": [{"path": self.manager.relative_to(self.root).as_posix(), "sha256": app._sha(self.manager.read_bytes())}]},
                         "missions": [], "files": []}
        for m in load_missions():
            raw = ("mission " + str(m["mission_id"])).encode()
            self.manifest["missions"].append({"mission_id": m["mission_id"], "asset_path": m["asset_path"], "sha256": app._sha(raw)})
            for prefix in app.PREFIXES:
                self.add_file("overlay/" + (prefix + "/" if prefix else "") + m["asset_path"], raw)
        for name in app.DAT_NAMES:
            self.add_file("overlay/arr/" + name + ".dat", (name + " v1").encode())
        self.add_file("overlay/samase/native_plugin.dll", pe())
        self.add_file("overlay/samase/plugins", b"samase/native_plugin.dll\n")
        self.write_manifest()
        self.patches = [patch.object(app, "WORKSPACE", self.root), patch.object(app, "PIN_PATH", self.pin_path), patch.object(app, "NATIVE", self.native),
                        patch.object(app, "_file_version", return_value=self.pin["game_file_version_observed"]),
                        patch.object(app, "_running_game_processes", return_value=[])]
        for item in self.patches: item.start()

    def tearDown(self):
        for item in reversed(self.patches): item.stop()
        self.temp.cleanup()

    def add_file(self, name, raw):
        target = self.package / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        self.manifest["files"] = [f for f in self.manifest["files"] if f["path"] != name]
        self.manifest["files"].append({"path": name, "sha256": app._sha(raw), "bytes": len(raw)})

    def write_manifest(self):
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf8")

    def install(self):
        return app.install_package(self.game, self.manifest_path)

    def test_install_update_restore_preserve_original_and_previous_patch(self):
        original = self.exe.read_bytes()
        result = self.install(); target = Path(result["install_root"])
        self.assertEqual(result["files"], 202)
        self.assertEqual(app.inspect_installation(self.exe)["status"], "installed")
        old_manifest = (target / "manifest.json").read_bytes()
        self.add_file("overlay/arr/units.dat", b"units version 2"); self.write_manifest()
        self.assertTrue(self.install()["backup_available"])
        restored = app.restore_installation(self.game)
        self.assertEqual((target / "manifest.json").read_bytes(), old_manifest)
        self.assertEqual((Path(restored["retained_previous_install"]) / "overlay/arr/units.dat").read_bytes(), b"units version 2")
        self.assertEqual(self.exe.read_bytes(), original)
        self.assertEqual((self.game / "original-casc-sentinel").read_bytes(), b"original game data")

    def test_unmanaged_destination_is_never_overwritten(self):
        target = self.game / app.INSTALL_NAME; target.mkdir(); sentinel = target / "user.txt"; sentinel.write_bytes(b"keep")
        with self.assertRaises(app.InstallationError): self.install()
        self.assertEqual(sentinel.read_bytes(), b"keep")
        self.assertFalse((target / "overlay").exists())

    def test_changed_package_loader_or_manager_is_rejected(self):
        for kind in ("asset", "loader", "manager"):
            with self.subTest(kind=kind):
                path = {"asset": self.package / self.manifest["files"][0]["path"], "loader": self.native / "samase64.exe", "manager": self.manager}[kind]
                original = path.read_bytes(); path.write_bytes(original + b"changed")
                try:
                    with self.assertRaises(app.InstallationError): self.install()
                finally: path.write_bytes(original)
        self.assertFalse((self.game / app.INSTALL_NAME).exists())

    def test_partial_roster_and_path_traversal_are_rejected(self):
        original = list(self.manifest["files"]); self.manifest["files"].pop(); self.write_manifest()
        with self.assertRaises(app.InstallationError): self.install()
        self.manifest["files"] = original; self.manifest["files"][0]["path"] = "../escape"; self.write_manifest()
        with self.assertRaises(app.InstallationError): self.install()
        self.assertFalse((self.root / "escape").exists())

    def test_running_game_blocks_install_restore_and_launch(self):
        self.install()
        with patch.object(app, "_running_game_processes", return_value=[12345]):
            for call in (self.install, lambda: app.restore_installation(self.game), lambda: app.launch_installed(self.game)):
                with self.assertRaisesRegex(app.InstallationError, "실행 중"): call()

    def test_game_started_during_staging_prevents_commit(self):
        with patch.object(app, "_running_game_processes", side_effect=[[], [12345]]):
            with self.assertRaises(app.InstallationError): self.install()
        self.assertFalse((self.game / app.INSTALL_NAME).exists())
        self.assertFalse(list(self.game.glob(".SC1CampaignGrowth.staging.*")))
        self.assertFalse(list(self.game.glob("*.lock")))

    @staticmethod
    def sharing_error(code=32):
        error=OSError('fixture sharing violation');error.winerror=code;return error

    def test_transient_directory_lock_retries_without_overwriting_active_files(self):
        self.install();target=self.game/app.INSTALL_NAME;before=(target/'manifest.json').read_bytes();rename=Path.rename;attempts=[]
        def locked(source,destination):
            if source==target:
                attempts.append(source)
                if len(attempts)<3:raise self.sharing_error()
            return rename(source,destination)
        with patch.object(Path,'rename',locked),patch.object(app.time,'sleep') as pause:
            result=self.install()
        self.assertEqual(len(attempts),3);self.assertEqual(pause.call_count,2)
        backup=Path(json.loads((target/'installation.json').read_text())['previous_backup'])
        self.assertEqual((backup/'manifest.json').read_bytes(),before);self.assertTrue(result['backup_available'])

    def test_persistent_directory_lock_keeps_old_patch_and_cleans_staging(self):
        self.install();target=self.game/app.INSTALL_NAME;before=(target/'manifest.json').read_bytes();rename=Path.rename
        def locked(source,destination):
            if source==target:raise self.sharing_error()
            return rename(source,destination)
        with patch.object(Path,'rename',locked),patch.object(app.time,'sleep') as pause:
            with self.assertRaises(app.InstallationError) as error:self.install()
        self.assertEqual(error.exception.code,'files_in_use');self.assertIn('관리자도 종료',str(error.exception));self.assertEqual(pause.call_count,9)
        self.assertEqual((target/'manifest.json').read_bytes(),before)
        self.assertFalse(list(self.game.glob('.SC1CampaignGrowth.staging.*')));self.assertFalse(list(self.game.glob('*.lock')))

    def test_staging_lock_rolls_back_verified_old_directory(self):
        self.install();target=self.game/app.INSTALL_NAME;before=(target/'manifest.json').read_bytes();rename=Path.rename
        def locked(source,destination):
            if '.staging.' in source.name:raise self.sharing_error(33)
            return rename(source,destination)
        with patch.object(Path,'rename',locked),patch.object(app.time,'sleep'):
            with self.assertRaises(app.InstallationError):self.install()
        self.assertEqual((target/'manifest.json').read_bytes(),before)
        self.assertEqual(app.inspect_installation(self.game)['status'],'installed')

    def test_game_appearing_during_retry_prevents_directory_swap(self):
        self.install();target=self.game/app.INSTALL_NAME;before=(target/'manifest.json').read_bytes();rename=Path.rename
        def locked(source,destination):
            if source==target:raise self.sharing_error()
            return rename(source,destination)
        with patch.object(Path,'rename',locked),patch.object(app.time,'sleep'),patch.object(app,'_running_game_processes',side_effect=[[],[],[],[123]]):
            with self.assertRaises(app.InstallationError) as error:self.install()
        self.assertEqual(error.exception.code,'game_running');self.assertEqual((target/'manifest.json').read_bytes(),before)

    def test_non_sharing_error_is_not_retried_or_misreported(self):
        self.install();target=self.game/app.INSTALL_NAME;rename=Path.rename
        def denied(source,destination):
            if source==target:raise self.sharing_error(5)
            return rename(source,destination)
        with patch.object(Path,'rename',denied),patch.object(app.time,'sleep') as pause:
            with self.assertRaises(OSError) as error:self.install()
        self.assertEqual(error.exception.winerror,5);pause.assert_not_called()

    @unittest.skipUnless(os.name=='nt','Requires a real Windows directory handle')
    def test_real_windows_directory_handle_is_retried_after_release(self):
        self.install();target=self.game/app.INSTALL_NAME
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.CreateFileW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_void_p]
        kernel.CreateFileW.restype=ctypes.c_void_p;kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        handle=kernel.CreateFileW(str(target),1,3,None,3,0x02000000,None)
        if handle==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
        released=threading.Event()
        def release():
            time.sleep(0.3);kernel.CloseHandle(handle);released.set()
        worker=threading.Thread(target=release);worker.start()
        try:result=self.install()
        finally:worker.join(5)
        self.assertTrue(released.is_set());self.assertEqual(result['status'],'installed')

    def test_failed_atomic_update_recovers_previous_install(self):
        self.install(); target = self.game / app.INSTALL_NAME; before = (target / "manifest.json").read_bytes()
        self.add_file("overlay/arr/units.dat", b"updated"); self.write_manifest(); rename = Path.rename
        def fail_commit(source, destination):
            if ".staging." in source.name: raise OSError("simulated commit failure")
            return rename(source, destination)
        with patch.object(Path, "rename", fail_commit):
            with self.assertRaises(OSError): self.install()
        self.assertEqual((target / "manifest.json").read_bytes(), before)
        self.assertEqual(app.inspect_installation(self.game)["status"], "installed")

    def test_explicit_launch_uses_installed_loader_and_returns_filetime(self):
        self.install()
        with patch.object(app, "_popen", return_value=SimpleNamespace(pid=4321)) as popen:
            result = app.launch_installed(self.game, with_manager=False)
        self.assertEqual(result["status"], "started"); self.assertEqual(result["process_id"], 4321)
        self.assertGreater(result["started_after"], 116444736000000000)
        self.assertEqual(str(popen.call_args.args[0][0]), str(self.game / app.INSTALL_NAME / "samase64.exe"))
        self.assertIn(str(self.exe), [str(x) for x in popen.call_args.args[0]])
        self.assertEqual(popen.call_count, 1)

    def test_installed_hash_and_same_version_game_change_block_launch(self):
        self.install(); path = self.game / app.INSTALL_NAME / "overlay/arr/units.dat"; original = path.read_bytes(); path.write_bytes(b"tamper")
        with patch.object(app, "_popen") as launch:
            with self.assertRaises(app.InstallationError): app.launch_installed(self.game)
            launch.assert_not_called()
        path.write_bytes(original); self.exe.write_bytes(pe() + b"same-version change")
        with self.assertRaises(app.InstallationError): app.launch_installed(self.game)

    def test_relative_manager_pins_survive_portable_relocation(self):
        import shutil
        portable = self.root / "portable"; portable.mkdir(); (portable / "sc1/manager").mkdir(parents=True)
        manager = portable / "sc1/manager/installation.py"; manager.write_bytes(b"portable manager")
        self.manifest["inputs"]["manager_sources"] = [{"path": "sc1/manager/installation.py", "sha256": app._sha(manager.read_bytes())}]
        self.write_manifest()
        shutil.copytree(self.package, portable / "package"); shutil.copytree(self.native, portable / "native")
        with patch.object(app, "WORKSPACE", portable), patch.object(app, "NATIVE", portable / "native"), patch.object(app, "PIN_PATH", portable / "native/pin.json"):
            app.install_package(self.game, portable / "package/manifest.json")
        moved = self.root / "moved-portable"; portable.rename(moved)
        with patch.object(app, "WORKSPACE", moved), patch.object(app, "NATIVE", moved / "native"), patch.object(app, "PIN_PATH", moved / "native/pin.json"), patch.object(app, "_popen", return_value=SimpleNamespace(pid=22)):
            self.assertEqual(app.inspect_installation(self.game)["status"], "installed")
            self.assertEqual(app.launch_installed(self.game)["status"], "started")
            self.assertEqual(app.install_package(self.game, moved / "package/manifest.json")["status"], "installed")

    def test_wrong_architecture_and_version_are_rejected(self):
        with patch.object(app, "_file_version", return_value="0.0.0.0"):
            with self.assertRaises(app.InstallationError): app.inspect_installation(self.game)
        raw = bytearray(pe()); struct.pack_into("<H", raw, 132, 0x14c); self.exe.write_bytes(raw)
        with self.assertRaises(app.InstallationError): app.inspect_installation(self.game)

    def test_original_restore_retains_verified_patch_and_growth_records(self):
        self.install()
        target = self.game / app.INSTALL_NAME
        before = {q.relative_to(target).as_posix(): q.read_bytes() for q in target.rglob("*") if q.is_file()}
        record = self.root / "campaign.sqlite3"; record.write_bytes(b"keep player growth")
        result = app.restore_original_campaign(self.game)
        retained = Path(result["retained_installation"])
        self.assertEqual(result["status"], "original")
        self.assertFalse(result["auto_connect"])
        self.assertFalse(target.exists())
        self.assertEqual(retained.parent, self.game)
        self.assertTrue(retained.name.startswith(".SC1CampaignGrowth.disabled."))
        self.assertEqual({q.relative_to(retained).as_posix(): q.read_bytes() for q in retained.rglob("*") if q.is_file()}, before)
        self.assertEqual(record.read_bytes(), b"keep player growth")
        self.assertEqual(self.exe.read_bytes(), pe())
        self.assertEqual((self.game / "original-casc-sentinel").read_bytes(), b"original game data")
        self.assertEqual(app.inspect_installation(self.game)["status"], "not_installed")
        self.install()
        self.assertTrue(retained.is_dir())
        self.assertEqual((retained / "manifest.json").read_bytes(), before["manifest.json"])
        self.assertEqual(record.read_bytes(), b"keep player growth")

    def test_original_restore_without_install_is_idempotent(self):
        for _ in range(2):
            result = app.restore_original_campaign(self.game)
            self.assertEqual(result["status"], "original")
            self.assertIsNone(result["retained_installation"])
        self.assertFalse(list(self.game.glob(".SC1CampaignGrowth.*")))

    def test_original_restore_does_not_require_current_manager_or_game_version(self):
        self.install(); self.manager.write_bytes(b"new manager revision")
        with patch.object(app, "_file_version", return_value="1.23.11.99999"):
            result = app.restore_original_campaign(self.game)
        self.assertTrue(Path(result["retained_installation"]).is_dir())

    def test_original_restore_rejects_extra_and_corrupt_managed_files(self):
        self.install(); target = self.game / app.INSTALL_NAME
        extra = target / "user-notes.txt"; extra.write_bytes(b"must not move")
        with self.assertRaises(app.InstallationError): app.restore_original_campaign(self.game)
        self.assertEqual(extra.read_bytes(), b"must not move")
        extra.unlink()
        payload = target / "overlay/arr/units.dat"; payload.write_bytes(b"tampered")
        with self.assertRaises(app.InstallationError): app.restore_original_campaign(self.game)
        self.assertTrue(target.is_dir())
        self.assertFalse(list(self.game.glob(".SC1CampaignGrowth.disabled.*")))

    def test_failed_original_rename_preserves_active_patch(self):
        self.install(); target = self.game / app.INSTALL_NAME
        before = (target / "manifest.json").read_bytes()
        rename = Path.rename
        def fail_disable(source, destination):
            if source == target: raise OSError("simulated rename failure")
            return rename(source, destination)
        with patch.object(Path, "rename", fail_disable):
            with self.assertRaises(OSError): app.restore_original_campaign(self.game)
        self.assertEqual((target / "manifest.json").read_bytes(), before)
        self.assertFalse(list(self.game.glob(".SC1CampaignGrowth.*")))

    def test_running_or_newly_started_game_blocks_original_restore(self):
        self.install(); target = self.game / app.INSTALL_NAME
        for states in ([ [12] ], [ [], [12] ]):
            with patch.object(app, "_running_game_processes", side_effect=states):
                with self.assertRaisesRegex(app.InstallationError, "실행 중"):
                    app.restore_original_campaign(self.game)
            self.assertTrue(target.is_dir())
        self.assertFalse(list(self.game.glob(".SC1CampaignGrowth.disabled.*")))

    def test_uninstalled_launch_is_original_and_needs_no_growth_profile_or_manager(self):
        with patch.object(app, "_popen", return_value=SimpleNamespace(pid=456)) as launch, \
             patch.object(app, "_package", side_effect=AssertionError("must not load a mod package")), \
             patch.object(app, "_file_version", return_value="1.23.11.99999"):
            result = app.launch_campaign(self.game, with_manager=True, allow_growth=False)
        self.assertEqual(result["mode"], "original")
        self.assertFalse(result["auto_connect"])
        self.assertGreater(result["started_after"], 116444736000000000)
        launch.assert_called_once_with([self.exe], cwd=self.exe.parent)
        self.assertFalse((self.game / app.INSTALL_NAME).exists())

    def test_installed_launch_keeps_growth_checks_and_never_falls_back_on_corruption(self):
        self.install()
        with patch.object(app, "_popen", return_value=SimpleNamespace(pid=456)) as launch:
            with self.assertRaisesRegex(app.InstallationError, "캠페인 기록"):
                app.launch_campaign(self.game, allow_growth=False)
            launch.assert_not_called()
            result = app.launch_campaign(self.game)
            self.assertEqual(result["mode"], "growth")
            self.assertTrue(result["auto_connect"])
            self.assertEqual(launch.call_args.args[0][0], self.game / app.INSTALL_NAME / "samase64.exe")
            launch.reset_mock()
            (self.game / app.INSTALL_NAME / "overlay/arr/units.dat").write_bytes(b"tamper")
            with self.assertRaises(app.InstallationError): app.launch_campaign(self.game)
            launch.assert_not_called()

    def test_disabled_install_uses_original_launch_and_preserves_retained_payload(self):
        self.install(); retained = Path(app.restore_original_campaign(self.game)["retained_installation"])
        before = (retained / "manifest.json").read_bytes()
        with patch.object(app, "_popen", return_value=SimpleNamespace(pid=456)) as launch:
            result = app.launch_campaign(self.game)
        self.assertEqual(result["mode"], "original")
        launch.assert_called_once_with([self.exe], cwd=self.exe.parent)
        self.assertEqual((retained / "manifest.json").read_bytes(), before)

    def test_original_launch_is_blocked_while_game_runs_or_install_is_locked(self):
        with patch.object(app, "_popen") as launch:
            with patch.object(app, "_running_game_processes", return_value=[12]):
                with self.assertRaises(app.InstallationError): app.launch_original(self.game)
            lock = self.game / ".SC1CampaignGrowth.install.lock"; lock.write_text("another installer")
            with self.assertRaises(app.InstallationError): app.launch_campaign(self.game)
            self.assertEqual(lock.read_text(), "another installer")
            launch.assert_not_called()

    def test_real_manager_dispatch_disables_patch_then_launches_original_without_bridge(self):
        import tkinter as tk
        from sc1.manager.ui import ManagerWindow
        self.install()
        window = tk.Tk(); window.withdraw()
        ui = ManagerWindow(window, self.root / "private-growth.sqlite3", preferences_path=self.root / "private-preferences.json")
        ui.game_path.set(str(self.game))
        before = ui.database.read_bytes()
        def immediate_thread(*args, **kwargs):
            return SimpleNamespace(start=kwargs["target"])
        try:
            with patch("sc1.manager.ui.threading.Thread", side_effect=immediate_thread), \
                 patch("sc1.manager.ui.messagebox.showerror") as error, \
                 patch.object(app, "_popen", return_value=SimpleNamespace(pid=777)) as launch:
                ui.installation_action("original"); ui.drain_events()
                launch.assert_not_called()
                self.assertFalse((self.game / app.INSTALL_NAME).exists())
                ui.installation_action("launch"); ui.drain_events()
                launch.assert_called_once_with([self.exe], cwd=self.exe.parent)
                error.assert_not_called()
            self.assertFalse(ui.auto_connect_enabled)
            self.assertIsNone(ui.auto_connect_target)
            self.assertEqual(ui.database.read_bytes(), before)
            self.assertEqual(ui.process, None)
            self.assertIn("원본 캠페인", ui.connection.get())
        finally:
            ui.closed = True
            for timer in window.tk.call("after", "info"): window.after_cancel(timer)
            window.update_idletasks(); window.destroy()


if __name__ == "__main__": unittest.main()
