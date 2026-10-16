"""Connection flow without opening a GUI or any game process."""
import queue
import json
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from sc1.bridge.discovery import GameProcess
from sc1.manager.ui import ManagerWindow


def game(pid=42, architecture="x86_64", started_at=134000000000000000):
    return GameProcess(pid, f"C:/Games/StarCraft/{architecture}/StarCraft.exe", architecture, started_at)


class ManagerConnectionTests(unittest.TestCase):
    def setUp(self):
        self.window = ManagerWindow.__new__(ManagerWindow)
        self.window.root = Mock()
        self.window.closed = False
        self.window.discovery_token = 7
        self.window.discovering = True
        self.window.process = None
        self.window.last_connection_error = None
        self.window.connection = Mock()
        self.window.connect_button = Mock()
        self.window.inspect_button = Mock()
        self.window.append = Mock()
        self.window.refresh = Mock()
        self.window.choose_game = Mock()
        self.window.launch_bridge = Mock()
        self.window.events = queue.Queue()

    def test_one_game_connects_without_user_selection_for_both_architectures(self):
        for architecture in ("x86", "x86_64"):
            with self.subTest(architecture=architecture):
                candidate = game(architecture=architecture)
                self.window.discovered(7, True, [candidate])
                self.window.launch_bridge.assert_called_with(candidate, True)
        self.window.choose_game.assert_not_called()

    def test_multiple_games_require_explicit_choice(self):
        candidates = [game(), game(43, "x86")]
        self.window.choose_game.return_value = candidates[1]
        self.window.discovered(7, True, candidates)
        self.window.choose_game.assert_called_once_with(candidates)
        self.window.launch_bridge.assert_called_once_with(candidates[1], True)

    def test_cancel_and_empty_list_do_not_attach(self):
        self.window.choose_game.return_value = None
        self.window.discovered(7, True, [game(), game(43)])
        self.window.discovered(7, True, [])
        self.window.launch_bridge.assert_not_called()
        self.assertIn("배틀넷", self.window.connection.set.call_args.args[0])

    def test_unknown_architecture_is_not_attached(self):
        self.window.discovered(7, True, [game(architecture="arm64")])
        self.window.launch_bridge.assert_not_called()

    def test_stop_invalidates_delayed_discovery_result(self):
        self.window.stop_bridge()
        self.window.discovered(7, True, [game()])
        self.window.launch_bridge.assert_not_called()
        self.assertFalse(self.window.discovering)

    def test_discovery_runs_in_worker_and_result_is_processed_on_event_queue(self):
        self.window.discovering = False
        with patch("sc1.manager.ui.threading.Thread") as thread, patch(
            "sc1.manager.ui.discover_games", return_value=[game()]
        ) as discover:
            self.window.start_bridge(True)
            discover.assert_not_called()
            self.assertTrue(self.window.discovering)
            thread.call_args.kwargs["target"]()
            self.window.launch_bridge.assert_not_called()
            self.window.drain_events()
        self.window.launch_bridge.assert_called_once_with(game(), True)

    def test_failed_discovery_unlocks_retry_without_attach(self):
        self.window.events.put(("discovery_error", 7, "snapshot unavailable"))
        self.window.drain_events()
        self.assertFalse(self.window.discovering)
        self.window.connect_button.configure.assert_called_with(state="normal")
        self.window.launch_bridge.assert_not_called()

    def test_selected_identity_is_passed_to_bridge_internally(self):
        self.window.database = Path("probe.sqlite3")
        with patch("sc1.manager.ui.subprocess.Popen") as popen, patch("sc1.manager.ui.threading.Thread"):
            ManagerWindow.launch_bridge(self.window, game(), True)
        command = popen.call_args.args[0]
        self.assertEqual(command[command.index("--pid") + 1], "42")
        self.assertEqual(command[command.index("--expected-start-time") + 1], str(game().started_at))
        self.assertIn("--attach-write", command)
        self.assertIn("--exit-with-manager", command)
        self.assertIsNotNone(popen.call_args.kwargs["stdin"])
        self.assertTrue(popen.call_args.kwargs["close_fds"])
        self.assertNotIn("shell", popen.call_args.kwargs)

    def test_stop_signals_only_our_child_then_allows_time_to_release_writer(self):
        child = Mock()
        child.poll.return_value = None
        self.window.process = child
        self.window.stop_bridge()
        child.stdin.close.assert_called_once()
        child.terminate.assert_not_called()
        self.window.root.after.call_args.args[1]()
        child.terminate.assert_called_once()

    def test_duplicate_writer_advice_survives_process_exit(self):
        child = Mock()
        self.window.process = child
        self.window.events.put(json.dumps({"event": "error", "type": "WriterBusyError", "message": "busy"}))
        self.window.events.put(("exit", child, 1))
        self.window.drain_events()
        self.assertIn("기존 창", self.window.connection.set.call_args.args[0])
        self.assertIsNone(self.window.process)

    def test_same_game_map_restart_status_preserves_selected_connection(self):
        child = Mock()
        self.window.process = child
        self.window.update_connection_status(json.dumps({"event": "bridge", "status": "rebinding_map"}))
        self.assertIn("현재 기록", self.window.connection.set.call_args.args[0])
        self.window.update_connection_status(json.dumps({"event": "bridge", "status": "map_rebound"}))
        self.assertIn("복원", self.window.connection.set.call_args.args[0])
        self.assertIs(self.window.process, child)
        self.assertIsNone(self.window.last_connection_error)

    def test_close_waits_for_our_child_to_exit(self):
        child = Mock()
        self.window.process = child
        self.window.finish_bridge()
        child.stdin.close.assert_called_once()
        child.wait.assert_called_once_with(timeout=3)


if __name__ == "__main__":
    unittest.main()
