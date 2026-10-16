"""Owned subprocess/heap/native pages and temporary SQLite, never a game DB."""
import ctypes
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from sc1.bridge.__main__ import inspect_candidates, run_connected
from sc1.bridge.protocol import BridgeError, Dispatcher, validate_header
from sc1.bridge.windows import MailboxUnavailable, Region, WindowsProcess, WriterBusyError, find_mailboxes
from sc1.manager.store import CampaignStore
from sc1.tests.test_bridge import BASE
from sc1.tests.test_phased_bridge import PhaseMemory

ROOT = Path(__file__).resolve().parents[2]
FLAGS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class LifetimeSubprocessTests(unittest.TestCase):
    def run_with_parent_pipe_open(self, code, expected):
        process = subprocess.Popen([sys.executable, "-B", "-c", code], cwd=ROOT,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=FLAGS, close_fds=True)
        try:
            # wait(), not communicate(): parent's write end deliberately stays
            # open through the child's complete interpreter teardown.
            self.assertEqual(process.wait(timeout=5), expected)
            self.assertFalse(process.stdin.closed)
            stderr = process.stderr.read().decode("utf-8", errors="replace")
            self.assertNotIn("Fatal Python error", stderr)
            self.assertNotIn("finalizing", stderr)
            return process.stdout.read().decode("utf-8", errors="replace")
        finally:
            if process.poll() is None:
                process.terminate(); process.wait(timeout=5)
            for stream in (process.stdin, process.stdout, process.stderr):
                stream.close()

    def test_watcher_can_cancel_and_exit_while_parent_still_holds_pipe(self):
        output = self.run_with_parent_pipe_open('''
import sys, threading
from sc1.bridge.lifetime import watch_manager
before = len(threading.enumerate())
stopped = watch_manager(sys.stdin.buffer)
assert not stopped.wait(.12)
assert len(threading.enumerate()) == before
stopped.close()
assert stopped.wait(0) and not sys.stdin.closed
print("cancelled without daemon")
''', 0)
        self.assertIn("cancelled without daemon", output)

    def test_unhandled_error_has_normal_exit_code_with_open_parent_pipe(self):
        self.run_with_parent_pipe_open('''
import sys
from sc1.bridge.lifetime import watch_manager
stopped=watch_manager(sys.stdin.buffer)
assert not stopped.wait(.08)
raise RuntimeError("synthetic bridge error")
''', 1)

    def test_cli_open_error_does_not_deadlock_stdin_finalization(self):
        output = self.run_with_parent_pipe_open('''
import sys
from unittest.mock import patch
from sc1.bridge.__main__ import main
with patch("sc1.bridge.__main__.WindowsProcess", side_effect=PermissionError("synthetic access denial")):
    sys.exit(main(["run", "--pid", "123", "--attach-write", "--exit-with-manager"]))
''', 1)
        self.assertEqual(json.loads(output)["type"], "PermissionError")

    def test_cli_duration_exit_keeps_parent_pipe_open_without_opening_store(self):
        output = self.run_with_parent_pipe_open('''
import sys
from unittest.mock import MagicMock, patch
from sc1.bridge.__main__ import main
memory=MagicMock();memory.__enter__.return_value=memory
memory.image_path="synthetic.exe";memory.architecture="x86_64"
with patch("sc1.bridge.__main__.WindowsProcess",return_value=memory), patch("sc1.bridge.__main__.inspect_candidates",return_value=[]), patch("sc1.manager.store.open_campaign_store") as store:
    result=main(["run","--pid","123","--attach-write","--exit-with-manager","--duration",".05"])
    store.assert_not_called()
    sys.exit(result)
''', 0)
        self.assertIn('"reason": "duration"', output)


class ClockStop:
    def __init__(self, memory):
        self.now = 0.0
        self.done = False
        self.memory = memory
        self.advance = True

    def is_set(self):
        return self.done

    def wait(self, delay):
        self.now += delay
        if self.advance:
            for page in self.memory.pages.values():
                page.set(6, page.get(6) + 1)
        return self.done


class Generations:
    def __init__(self, page=None):
        self.pages = {BASE: page or PhaseMemory()}
        self.mailbox = None
        self.bindings = []
        self.unbindings = 0
        self.writes = []
        self.retire_on_write = False

    def is_running(self):
        return True

    def regions(self):
        return [Region(address, 256) for address in self.pages]

    def read(self, address, size):
        for base, page in self.pages.items():
            if base <= address < address + size <= base + 256:
                return page.read(BASE + address - base, size)
        raise MailboxUnavailable("synthetic old allocation retired")

    def write(self, address, data):
        if self.mailbox is None:
            raise AssertionError("write while unbound")
        if self.retire_on_write:
            self.retire_on_write = False
            self.restart(retry=True)
            raise MailboxUnavailable("synthetic lost durable response")
        self.writes.append((self.mailbox, address, len(data)))
        self.pages[self.mailbox].write(BASE + address - self.mailbox, data)

    def bind_mailbox(self, address):
        validate_header(self.read(address, 256), address)
        self.mailbox = address
        self.bindings.append(address)

    def bound_header(self):
        return validate_header(self.read(self.mailbox, 256), self.mailbox)

    def unbind_mailbox(self):
        self.mailbox = None
        self.unbindings += 1

    def restart(self, *, retry=False):
        old = self.pages[self.mailbox]
        new = PhaseMemory()
        if retry:
            new.data[:128] = old.data[:128]
        new.set(6, old.get(6) + 1)
        self.pages = {max(self.pages) + 4096: new}


class ReconnectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sc1-rebind-")
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.sqlite3"
        self.store = CampaignStore(self.path, new_profile="original")
        self.memory = Generations()
        self.stop = ClockStop(self.memory)
        self.factory = Mock(return_value=self.store)
        self.events = []

    def inspect(self, memory):
        self.assertIsNone(memory.mailbox, "all writes must be revoked before discovery")
        return [{"address": base, "active": True} for base in memory.pages]

    def run_session(self, report=None, inspect=None):
        return run_connected(self.memory, {"address": BASE, "active": True}, self.factory,
                             stopped=self.stop, deadline=8, clock=lambda: self.stop.now,
                             inspect=inspect or self.inspect, report=report or self.events.append)

    def test_lost_choice_ack_rebinds_new_dispatcher_and_reuses_persisted_offer(self):
        expected = None
        def report(event):
            nonlocal expected
            self.events.append(event)
            if event["status"] == "choice_offered":
                page = self.memory.pages[self.memory.mailbox]
                if self.memory.mailbox == BASE:
                    page.request(3, slot=1)
                    self.memory.retire_on_write = True
                else:
                    self.assertEqual(self.store.growth_status()["offer"], expected)
                    self.assertEqual(len(self.store.growth_status()["history"]), 1)
                    self.stop.done = True
            elif event["status"] == "rebinding_map":
                expected = self.store.growth_status()["offer"]
        self.run_session(report)
        self.assertTrue(self.stop.done)
        self.factory.assert_called_once()
        self.assertEqual(self.memory.bindings, [BASE, BASE + 4096])
        self.assertEqual(self.memory.unbindings, 1)
        self.assertIn("map_rebound", [event["status"] for event in self.events])
        self.assertTrue(all(base + 128 <= addr < addr + length <= base + 256 for base, addr, length in self.memory.writes))

    def test_restart_restores_same_completed_snapshot_and_nonce_from_same_store(self):
        page = self.memory.pages[BASE]
        dispatch = Dispatcher(page, BASE, self.store)
        dispatch.poll(); page.set(6, 1); dispatch.poll()
        for _ in range(2):
            page.request(3, slot=1); dispatch.poll()
        expected = bytes(page.data[144:256])
        self.memory.pages[BASE] = PhaseMemory()
        snapshots = []
        def report(event):
            if event["status"] == "restored":
                snapshots.append(bytes(self.memory.pages[self.memory.mailbox].data[144:256]))
                if len(snapshots) == 1:
                    self.memory.restart()
                else:
                    self.stop.done = True
        self.run_session(report)
        self.assertEqual(snapshots, [expected, expected])
        self.assertEqual(len(self.store.growth_status()["history"]), 2)
        self.factory.assert_called_once()

    def test_paused_heartbeat_waits_read_only_and_cancel_does_not_rebind(self):
        self.stop.advance = False
        def inspect(memory):
            self.assertIsNone(memory.mailbox)
            self.stop.done = True
            return []
        self.run_session(inspect=inspect)
        self.assertEqual(self.memory.bindings, [BASE])
        self.assertEqual(self.memory.unbindings, 1)
        self.assertEqual(self.memory.writes, [])

    def test_permission_storage_and_abi_errors_remain_fatal(self):
        for error in (PermissionError("access denied"), sqlite3.OperationalError("disk full"), BridgeError("unsupported ABI")):
            with self.subTest(error=type(error).__name__):
                self.memory.bound_header = Mock(side_effect=error)
                inspector = Mock()
                with self.assertRaises(type(error)):
                    self.run_session(inspect=inspector)
                inspector.assert_not_called()
                self.assertEqual(self.memory.unbindings, 0)

    def test_invalid_real_header_is_not_a_retired_generation(self):
        self.memory.pages[BASE].set(18, 99)
        with self.assertRaisesRegex(BridgeError, "Unsupported growth"):
            self.run_session()
        self.factory.assert_not_called()
        self.assertEqual(self.memory.unbindings, 0)

    def test_actual_dispatch_storage_error_is_not_retried_or_acknowledged(self):
        self.store.restore_growth_phase = Mock(side_effect=sqlite3.OperationalError("synthetic disk failure"))
        inspector = Mock()
        with self.assertRaises(sqlite3.OperationalError):
            self.run_session(inspect=inspector)
        self.store.restore_growth_phase.assert_called_once()
        inspector.assert_not_called()
        self.assertEqual(self.memory.writes, [])
        self.assertEqual(self.memory.unbindings, 0)

    @unittest.skipUnless(os.name == "nt", "Win32 permission code")
    def test_scan_and_candidate_probe_do_not_suppress_access_denial(self):
        memory = Mock()
        memory.max_address = BASE + 4096
        memory.regions.return_value = [Region(BASE, 4096)]
        memory.read.side_effect = ctypes.WinError(5)
        with self.assertRaises(PermissionError):
            find_mailboxes(memory)
        with self.assertRaises(PermissionError):
            inspect_candidates(memory, addresses=[BASE])

    def test_discovery_rejects_two_active_generations_without_rebinding(self):
        def report(event):
            if event["status"] == "choice_offered":
                self.memory.restart()
                self.memory.pages[BASE + 8192] = PhaseMemory()
        with self.assertRaises(BridgeError):
            self.run_session(report)
        self.assertEqual(self.memory.bindings, [BASE])
        self.assertIsNone(self.memory.mailbox)

    def test_scan_cancellation_stops_before_next_large_chunk(self):
        memory = Mock()
        memory.max_address = BASE + 4 * 1024 * 1024
        memory.regions.return_value = [Region(BASE, 4 * 1024 * 1024)]
        memory.read.return_value = bytes(1024 * 1024)
        self.assertEqual(find_mailboxes(memory, stopped=lambda: memory.read.call_count >= 1), [])
        self.assertEqual(memory.read.call_count, 1)


@unittest.skipUnless(os.name == "nt", "Owned Win32 allocation transport")
class NativeGenerationTests(unittest.TestCase):
    def test_quarantine_unbind_new_allocation_preserves_exclusive_pid_writer(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
        kernel.VirtualAlloc.restype = ctypes.c_void_p
        kernel.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
        kernel.VirtualProtect.restype = ctypes.c_int
        kernel.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
        kernel.VirtualFree.restype = ctypes.c_int
        allocations = [kernel.VirtualAlloc(None, 4096, 0x3000, 4) for _ in range(2)]
        self.assertTrue(all(allocations))
        try:
            for address in allocations:
                ctypes.memmove(address, bytes(PhaseMemory().data), 256)
            with patch("sc1.bridge.windows.validate_image", return_value=0x8664):
                with WindowsProcess(os.getpid(), allow_write=True) as memory:
                    first, second = allocations
                    memory.bind_mailbox(first)
                    old = ctypes.c_uint32()
                    self.assertTrue(kernel.VirtualProtect(first, 4096, 1, ctypes.byref(old)))
                    with self.assertRaises(MailboxUnavailable):
                        memory.bound_header()
                    with self.assertRaises(MailboxUnavailable):
                        memory.read(first, 256)
                    memory.unbind_mailbox()
                    with self.assertRaisesRegex(BridgeError, "bound"):
                        memory.write(first + 128, bytes(4))
                    with self.assertRaises(WriterBusyError):
                        WindowsProcess(os.getpid(), allow_write=True)
                    memory.bind_mailbox(second)
                    self.assertEqual(memory.bound_header()[5], 101)
                    memory.write(second + 128, bytes(4))
                    self.assertTrue(kernel.VirtualProtect(second, 4096, 0x40, ctypes.byref(old)))
                    with self.assertRaises(BridgeError) as bad_region:
                        memory.bound_header()
                    self.assertNotIsInstance(bad_region.exception, MailboxUnavailable)
                    self.assertTrue(kernel.VirtualProtect(second, 4096, 4, ctypes.byref(old)))
                    ctypes.c_uint32.from_address(second + 16).value = 99
                    with self.assertRaises(BridgeError) as bad_abi:
                        memory.bound_header()
                    self.assertNotIsInstance(bad_abi.exception, MailboxUnavailable)
                    ctypes.memset(second, 0, 16)
                    with self.assertRaises(MailboxUnavailable):
                        memory.bound_header()
                with WindowsProcess(os.getpid(), allow_write=True):
                    pass
        finally:
            for address in allocations:
                if address:
                    self.assertTrue(kernel.VirtualFree(address, 0, 0x8000))


if __name__ == "__main__":
    unittest.main()
