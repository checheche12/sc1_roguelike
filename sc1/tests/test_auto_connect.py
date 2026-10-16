"""Launcher/manager handoff without touching a running game or user records."""
import contextlib
import io
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
import uuid

from sc1.bridge.discovery import GameProcess
from sc1.manager.__main__ import main
from sc1.manager.auto_connect import AutoConnectTarget, publish_request, read_request
from sc1.manager.lifecycle import ManagerInstance
from sc1.manager.ui import ManagerWindow, launch


IMAGE = "D:/Games/StarCraft/x86_64/StarCraft.exe"


def game(pid=42, started_at=200, image=IMAGE, architecture="x86_64"):
    return GameProcess(pid, image, architecture, started_at)


def window():
    app = ManagerWindow.__new__(ManagerWindow)
    app.root = Mock()
    app.database = Path("selected_record.sqlite3")
    app.store = object()
    app.closed = False
    app.process = None
    app.last_connection_error = None
    app.events = queue.Queue()
    app.discovery_token = 7
    app.discovering = False
    app.discovery_automatic = False
    app.auto_connect_enabled = True
    app.auto_connect_target = AutoConnectTarget(IMAGE, 100)
    app.command_channel = None
    app.command_token = None
    app.connection = Mock()
    app.connect_button = Mock()
    app.inspect_button = Mock()
    app.append = Mock()
    app.refresh = Mock()
    app.choose_game = Mock()
    app.launch_bridge = Mock()
    return app


class AutoConnectRequestTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sc1-autoconnect-test-")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "request.json"

    def test_atomic_handoff_roundtrips_target_and_fresh_request_token(self):
        target = AutoConnectTarget(IMAGE, 100)
        first = publish_request(self.path, target, clock=lambda: 10)
        self.assertEqual(read_request(self.path, clock=lambda: 11), (first, target))
        second = publish_request(self.path, target, clock=lambda: 12)
        self.assertNotEqual(first, second)
        self.assertEqual(read_request(self.path, clock=lambda: 13), (second, target))
        self.assertEqual(list(Path(self.temporary.name).iterdir()), [self.path])

    def test_stale_future_truncated_oversized_and_invalid_requests_are_ignored(self):
        publish_request(self.path, AutoConnectTarget(IMAGE), clock=lambda: 10)
        valid = self.path.read_bytes()
        self.assertIsNone(read_request(self.path, clock=lambda: 131))
        self.assertIsNone(read_request(self.path, clock=lambda: 9))
        cases = [b"{", b"x" * 4097]
        original = json.loads(valid)
        for field, value in (("image", "C:/other.exe"), ("started_after", -1),
                             ("started_after", True), ("created_at", True),
                             ("token", "invalid"), ("version", 2)):
            changed = {**original, field: value}
            cases.append(json.dumps(changed).encode())
        for raw in cases:
            with self.subTest(raw=raw[:50]):
                self.path.write_bytes(raw)
                self.assertIsNone(read_request(self.path, clock=lambda: 11))
        self.path.unlink()
        self.assertIsNone(read_request(self.path))

    def test_already_open_manager_receives_request_without_second_window_or_store(self):
        target = AutoConnectTarget(IMAGE, 100)
        instance = Mock(acquired=False)
        instance.__enter__ = Mock(return_value=instance)
        instance.__exit__ = Mock(return_value=False)
        root = Mock()
        with (patch("sc1.manager.ui.request_path", return_value=self.path),
              patch("sc1.manager.ui.ManagerInstance", return_value=instance),
              patch("sc1.manager.ui.tk.Tk", return_value=root) as tk,
              patch("sc1.manager.ui.ManagerWindow") as constructor,
              patch("sc1.manager.ui.messagebox.showinfo") as message):
            launch(Path("unused.sqlite3"), auto_connect_target=target)
        self.assertEqual(read_request(self.path)[1], target)
        constructor.assert_not_called()
        message.assert_not_called()
        tk.assert_not_called()
        root.mainloop.assert_not_called()

    def test_existing_window_handoff_preserves_selected_record_and_ignores_replay(self):
        app = window()
        app.auto_connect_enabled = False
        app.command_channel = self.path
        child = Mock()
        child.poll.return_value = None
        app.process = child
        selected_store, selected_path = app.store, app.database
        target = AutoConnectTarget(IMAGE, 300)
        token = publish_request(self.path, target)
        app.auto_connect_tick()
        self.assertTrue(app.auto_connect_enabled)
        self.assertEqual((app.command_token, app.auto_connect_target), (token, target))
        self.assertIs(app.store, selected_store)
        self.assertEqual(app.database, selected_path)
        child.stdin.close.assert_called_once()
        app.auto_connect_tick()
        child.stdin.close.assert_called_once()


class AutoConnectFlowTests(unittest.TestCase):
    def setUp(self):
        self.app = window()

    def tick_and_discover(self, games):
        with (patch("sc1.manager.ui.threading.Thread") as thread,
              patch("sc1.manager.ui.discover_games", return_value=games)):
            self.app.auto_connect_tick()
            thread.call_args.kwargs["target"]()
            self.app.drain_events()

    def test_launcher_can_start_manager_before_game_then_attach_without_manual_input(self):
        self.tick_and_discover([])
        self.app.launch_bridge.assert_not_called()
        self.assertTrue(self.app.auto_connect_enabled)
        self.app.append.assert_not_called()
        self.tick_and_discover([game()])
        self.app.launch_bridge.assert_called_once_with(game(), True)
        self.app.choose_game.assert_not_called()

    def test_old_game_other_install_and_unsupported_image_are_ignored(self):
        old = game(started_at=99)
        other = game(43, image="E:/Other/StarCraft.exe")
        arm = game(44, architecture="arm64")
        self.tick_and_discover([old, other, arm])
        self.app.launch_bridge.assert_not_called()
        self.tick_and_discover([old, other, arm, game(45)])
        self.app.launch_bridge.assert_called_once_with(game(45), True)

    def test_image_match_uses_windows_path_rules_and_creation_cutoff(self):
        target = AutoConnectTarget(IMAGE, 100)
        self.assertTrue(target.matches(game(image=r"d:\GAMES\STARCRAFT\x86_64\StarCraft.exe")))
        self.assertTrue(target.matches(game(started_at=100)))
        self.assertFalse(target.matches(game(started_at=99)))

    def test_tick_does_not_duplicate_inflight_discovery_or_existing_bridge(self):
        for attr in ("discovering", "process"):
            with self.subTest(attr=attr):
                app = window()
                setattr(app, attr, True if attr == "discovering" else Mock())
                with patch.object(app, "start_bridge") as start:
                    app.auto_connect_tick()
                    start.assert_not_called()

    def test_stop_disables_reconnect_and_invalidates_pending_discovery(self):
        with patch("sc1.manager.ui.threading.Thread"):
            self.app.auto_connect_tick()
        token = self.app.discovery_token
        self.app.stop_bridge()
        self.app.discovered(token, True, [game()])
        self.app.launch_bridge.assert_not_called()
        with patch.object(self.app, "start_bridge") as start:
            self.app.auto_connect_tick()
            start.assert_not_called()
        self.assertFalse(self.app.auto_connect_enabled)

    def test_manual_read_only_inspection_disables_automatic_writes(self):
        with (patch("sc1.manager.ui.threading.Thread") as thread,
              patch("sc1.manager.ui.discover_games", return_value=[game()])):
            self.app.start_bridge(False)
            thread.call_args.kwargs["target"]()
            self.app.drain_events()
        self.app.launch_bridge.assert_called_once_with(game(), False)
        self.assertFalse(self.app.auto_connect_enabled)

    def test_automatic_discovery_failure_stops_retry_loop(self):
        self.app.discovering = True
        self.app.events.put(("discovery_error", 7, "snapshot unavailable"))
        self.app.drain_events()
        self.assertFalse(self.app.auto_connect_enabled)
        self.assertFalse(self.app.discovering)
        with patch.object(self.app, "start_bridge") as start:
            self.app.auto_connect_tick()
            start.assert_not_called()

    def test_profile_and_writer_errors_stop_automatic_retry(self):
        for kind, message in (("WriterBusyError", "busy"), ("BridgeError", "profile_mismatch"),
                              ("OperationalError", "disk full")):
            with self.subTest(kind=kind):
                self.app.auto_connect_enabled = True
                self.app.update_connection_status(json.dumps({"event": "error", "type": kind, "message": message}))
                self.assertFalse(self.app.auto_connect_enabled)

    def test_map_restart_reconnects_after_child_releases_writer(self):
        child = Mock()
        self.app.process = child
        self.app.events.put(("output", child, json.dumps({"event": "error", "type": "BridgeError",
                                                        "message": "Mailbox signature or protocol version changed"})))
        self.app.events.put(("exit", child, 1))
        self.app.drain_events()
        self.assertTrue(self.app.auto_connect_enabled)
        self.assertIsNone(self.app.process)
        self.tick_and_discover([game()])
        self.app.launch_bridge.assert_called_once_with(game(), True)

    def test_old_child_error_cannot_cancel_new_launcher_request(self):
        old_child, current_child = Mock(), Mock()
        self.app.process = current_child
        self.app.events.put(("output", old_child, json.dumps({"event": "error", "type": "WriterBusyError", "message": "old"})))
        self.app.events.put(("exit", old_child, 1))
        self.app.drain_events()
        self.assertTrue(self.app.auto_connect_enabled)
        self.assertIs(self.app.process, current_child)
        self.assertIsNone(self.app.last_connection_error)

    def test_unexplained_child_failure_does_not_retry_forever(self):
        child = Mock()
        self.app.process = child
        self.app.events.put(("exit", child, 1))
        self.app.drain_events()
        self.assertFalse(self.app.auto_connect_enabled)


class AutoConnectCliTests(unittest.TestCase):
    def test_launcher_arguments_reach_ui_with_spaced_path(self):
        image = "D:/Game Files/StarCraft/x86_64/StarCraft.exe"
        with patch("sc1.manager.ui.launch") as ui:
            result = main(["--db", "test.sqlite3", "ui", "--auto-connect", "--game-image", image,
                           "--game-start-after", "134000000000000000"])
        self.assertEqual(result, 0)
        self.assertEqual(ui.call_args.kwargs["auto_connect_target"], AutoConnectTarget(image, 134000000000000000))

    def test_invalid_target_reports_cli_error_before_opening_any_store_or_ui(self):
        cases = [["ui", "--auto-connect", "--game-start-after", "-1"],
                 ["ui", "--auto-connect", "--game-image", "other.exe"],
                 ["ui", "--game-start-after", "10"]]
        for args in cases:
            with self.subTest(args=args), patch("sc1.manager.ui.launch") as ui, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
                ui.assert_not_called()


@unittest.skipUnless(os.name == "nt", "Windows single-manager handoff")
class NativeAutoConnectHandoffTests(unittest.TestCase):
    def test_console_free_second_process_hands_off_request_and_exits_without_ui(self):
        name = "Local\\SC1AutoHandoffTest-" + uuid.uuid4().hex
        code = '''
import sys
from pathlib import Path
from sc1.manager import ui
from sc1.manager.auto_connect import AutoConnectTarget
from sc1.manager.lifecycle import ManagerInstance
ui.ManagerInstance = lambda: ManagerInstance(sys.argv[1])
ui.request_path = lambda: Path(sys.argv[2])
def no_window(*args, **kwargs):
    raise AssertionError("Automatic duplicate must not create a UI")
ui.tk.Tk = no_window
ui.launch(Path("unused_record.sqlite3"), auto_connect_target=AutoConnectTarget(sys.argv[3], 100))
print("handed-off", flush=True)
'''
        executable = Path(sys.executable).with_name("pythonw.exe")
        with tempfile.TemporaryDirectory(prefix="sc1-native-handoff-test-") as temporary:
            channel = Path(temporary) / "request.json"
            with ManagerInstance(name) as first:
                self.assertTrue(first.acquired)
                result = subprocess.run([str(executable), "-B", "-u", "-c", code, name, str(channel), IMAGE],
                                        cwd=Path(__file__).resolve().parents[2], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                        encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "handed-off")
                self.assertEqual(read_request(channel)[1], AutoConnectTarget(IMAGE, 100))

    def test_powershell_launcher_arguments_preserve_spaced_image_and_filetime(self):
        executable = Path(sys.executable).with_name("pythonw.exe")
        image = "D:/Game Files/StarCraft/x86_64/StarCraft.exe"
        cutoff = "134000000000000000"

        def quoted(value):
            return "'" + str(value).replace("'", "''") + "'"

        with tempfile.TemporaryDirectory(prefix="sc1 launcher arguments ") as temporary:
            folder = Path(temporary)
            (folder / "argument_probe.py").write_text(
                "import sys,json\nfrom pathlib import Path\n"
                "Path('observed.json').write_text(json.dumps(sys.argv[1:]),encoding='utf-8')\n",
                encoding="utf-8")
            script = "$campaignGameImageArgument = '\"' + " + quoted(image) + " + '\"'\n"
            script += "$campaignChild = Start-Process -FilePath " + quoted(executable)
            script += " -ArgumentList '-m','argument_probe','ui','--auto-connect','--game-image',$campaignGameImageArgument,'--game-start-after'," + quoted(cutoff)
            script += " -WorkingDirectory " + quoted(folder) + " -WindowStyle Hidden -Wait -PassThru\n"
            script += "exit $campaignChild.ExitCode\n"
            result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", script],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, creationflags=subprocess.CREATE_NO_WINDOW, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads((folder / "observed.json").read_text(encoding="utf-8")),
                             ["ui", "--auto-connect", "--game-image", image, "--game-start-after", cutoff])


if __name__ == "__main__":
    unittest.main()
