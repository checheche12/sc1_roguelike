"""Native subprocess/handle tests. These never open or control a game."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock
import uuid

from sc1.bridge.__main__ import wait_for_probe
from sc1.manager.lifecycle import ManagerInstance


ROOT = Path(__file__).resolve().parents[2]
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class CancellationTests(unittest.TestCase):
    def test_manager_stop_during_map_wait_prevents_rescan_and_bind(self):
        memory = Mock()
        inspect = Mock()
        cancelled = False

        def stop(_delay):
            nonlocal cancelled
            cancelled = True

        self.assertIsNone(wait_for_probe(memory, [], sleep=stop, inspect=inspect,
                                        stopped=lambda: cancelled, report=lambda _: None))
        inspect.assert_not_called()
        memory.bind_mailbox.assert_not_called()

    def test_closed_manager_does_not_use_even_an_active_map(self):
        memory = Mock()
        self.assertIsNone(wait_for_probe(memory, [{"active": True}], stopped=lambda: True))
        memory.is_running.assert_not_called()


@unittest.skipUnless(os.name == "nt", "Windows manager lock")
class NativeManagerLifecycleTests(unittest.TestCase):
    def test_second_process_cannot_start_manager_and_lock_releases(self):
        name = "Local\\SC1ManagerTest-" + uuid.uuid4().hex
        code = "from sc1.manager.lifecycle import ManagerInstance; import sys; m=ManagerInstance(sys.argv[1]); print(m.acquired); m.close()"
        with ManagerInstance(name) as first:
            self.assertTrue(first.acquired)
            result = subprocess.run([sys.executable, "-c", code, name], cwd=ROOT,
                                    capture_output=True, text=True, creationflags=FLAGS, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), "False")
        with ManagerInstance(name) as restarted:
            self.assertTrue(restarted.acquired)

    def test_abrupt_parent_exit_stops_child_and_releases_its_lock(self):
        name = "Local\\SC1OrphanTest-" + uuid.uuid4().hex
        child_code = '''
from pathlib import Path
import sys
from sc1.bridge.lifetime import watch_manager
from sc1.manager.lifecycle import ManagerInstance
with ManagerInstance(sys.argv[1]) as lock:
    assert lock.acquired
    print("ready", flush=True)
    stopped = watch_manager(sys.stdin.buffer)
    if not stopped.wait(10):
        sys.exit(2)
Path(sys.argv[2]).write_text("parent closed")
'''
        parent_code = '''
import subprocess, sys
child = subprocess.Popen([sys.executable, "-c", sys.argv[1], sys.argv[2], sys.argv[3]],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, close_fds=True, creationflags=subprocess.CREATE_NO_WINDOW)
assert child.stdout.readline().strip() == "ready"
print("ready", flush=True)
sys.stdin.read()
'''
        with tempfile.TemporaryDirectory() as temporary:
            receipt = Path(temporary) / "stopped.txt"
            parent = subprocess.Popen([sys.executable, "-c", parent_code, child_code, name, str(receipt)],
                                      cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True, creationflags=FLAGS, close_fds=True)
            try:
                self.assertEqual(parent.stdout.readline().strip(), "ready")
                with ManagerInstance(name) as concurrent:
                    self.assertFalse(concurrent.acquired)
                parent.terminate()  # Only this test's parent; simulates a manager crash.
                parent.wait(timeout=5)
                deadline = time.monotonic() + 5
                while not receipt.exists() and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(receipt.exists(), "child did not observe parent pipe closure")
                self.assertEqual(receipt.read_text(), "parent closed")
                with ManagerInstance(name) as restarted:
                    self.assertTrue(restarted.acquired)
            finally:
                if parent.poll() is None:
                    parent.terminate()
                    parent.wait(timeout=5)
                for stream in (parent.stdin, parent.stdout, parent.stderr):
                    stream.close()


if __name__ == "__main__":
    unittest.main()
