"""Metadata-only discovery checks; mock APIs never open a real process."""
import ctypes
from ctypes import wintypes
from dataclasses import FrozenInstanceError
from datetime import timedelta
import os
import struct
import unittest
from unittest.mock import patch

from sc1.bridge import discovery as d


START = 134000000012345679  # Deliberately not an exact microsecond.


class ApiFunction:
    def __init__(self, callback):
        self.callback = callback

    def __call__(self, *args):
        return self.callback(*args)


class FakeKernel:
    """Only the permitted process-metadata APIs exist on this fake object."""
    SNAPSHOT = 777

    def __init__(self, entries, records=None, *, snapshot_error=0, iteration_error=18):
        self.entries = entries
        self.records = records or {}
        self.snapshot_error = snapshot_error
        self.iteration_error = iteration_error
        self.index = 0
        self.opens, self.closed, self.queries = [], [], []
        self.CreateToolhelp32Snapshot = ApiFunction(self.snapshot)
        self.Process32FirstW = ApiFunction(self.first)
        self.Process32NextW = ApiFunction(self.next)
        self.OpenProcess = ApiFunction(self.open)
        self.QueryFullProcessImageNameW = ApiFunction(self.image)
        self.GetProcessTimes = ApiFunction(self.times)
        self.GetExitCodeProcess = ApiFunction(self.exit_code)
        self.CloseHandle = ApiFunction(lambda handle: self.closed.append(handle) or 1)

    def snapshot(self, flags, pid):
        if (flags, pid) != (2, 0):
            raise AssertionError("Discovery must snapshot process names only")
        if self.snapshot_error:
            ctypes.set_last_error(self.snapshot_error)
            return d.INVALID_HANDLE_VALUE
        return self.SNAPSHOT

    def fill(self, snapshot, pointer):
        if snapshot != self.SNAPSHOT:
            raise AssertionError("Unexpected snapshot handle")
        entry = ctypes.cast(pointer, ctypes.POINTER(d.PROCESSENTRY32W)).contents
        if entry.dwSize != ctypes.sizeof(d.PROCESSENTRY32W):
            raise AssertionError("PROCESSENTRY32W.dwSize was not initialized")
        if self.index >= len(self.entries):
            ctypes.set_last_error(self.iteration_error)
            return 0
        pid, name = self.entries[self.index]
        entry.th32ProcessID, entry.szExeFile = pid, name
        return 1

    def first(self, snapshot, pointer):
        self.index = 0
        return self.fill(snapshot, pointer)

    def next(self, snapshot, pointer):
        self.index += 1
        return self.fill(snapshot, pointer)

    def open(self, rights, inherit, pid):
        self.opens.append((rights, inherit, pid))
        if rights != 0x1000 or inherit:
            raise AssertionError("Only non-inheritable QUERY_LIMITED_INFORMATION is allowed")
        if self.records[pid].get("denied"):
            ctypes.set_last_error(5)
            return None
        return pid + 10000

    def record(self, handle):
        return self.records[handle - 10000]

    def image(self, handle, flags, buffer, length_pointer):
        self.queries.append(handle)
        record = self.record(handle)
        if record.get("image_fail"):
            ctypes.set_last_error(5)
            return 0
        if flags != 0:
            raise AssertionError("Expected a Win32 image path")
        buffer.value = record["path"]
        ctypes.cast(length_pointer, ctypes.POINTER(wintypes.DWORD)).contents.value = len(record["path"])
        return 1

    def times(self, handle, creation_pointer, *_):
        record = self.record(handle)
        if record.get("times_fail"):
            return 0
        creation = ctypes.cast(creation_pointer, ctypes.POINTER(wintypes.FILETIME)).contents
        value = record.get("start", START)
        creation.dwLowDateTime = value & 0xFFFFFFFF
        creation.dwHighDateTime = value >> 32
        return 1

    def exit_code(self, handle, pointer):
        record = self.record(handle)
        if record.get("exit_fail"):
            return 0
        ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD)).contents.value = record.get("exit", 259)
        return 1


class ProcessDescriptionTests(unittest.TestCase):
    def test_label_hides_pid_and_preserves_full_identity(self):
        game = d.GameProcess(987654321, r"D:\Games\StarCraft\x86\StarCraft.exe", "x86", START)
        expected_time = (d.FILETIME_EPOCH + timedelta(microseconds=START // 10)).astimezone().strftime("%H:%M:%S")
        self.assertIn("32비트", game.label)
        self.assertIn(expected_time, game.label)
        self.assertIn(r"D:\Games\StarCraft\x86", game.label)
        self.assertNotIn(str(game.pid), game.label)
        self.assertEqual(game.started_at, START)
        with self.assertRaises(FrozenInstanceError):
            game.pid = 1
        self.assertIn("64비트", d.GameProcess(2, game.image_path, "x86_64", START).label)


@unittest.skipUnless(os.name == "nt", "Native Windows ctypes layout required")
class DiscoveryTests(unittest.TestCase):
    def run_discovery(self, kernel, machines=None):
        machines = machines or {}
        def machine(path):
            value = machines.get(path, 0x014C)
            if isinstance(value, Exception):
                raise value
            return value
        with patch.object(d, "_load_kernel", return_value=kernel), patch.object(d, "pe_machine", side_effect=machine):
            return d.discover_games()

    def test_win32_structure_and_function_signatures(self):
        width = ctypes.sizeof(ctypes.c_void_p)
        self.assertEqual(ctypes.sizeof(d.PROCESSENTRY32W), 568 if width == 8 else 556)
        self.assertEqual(d.PROCESSENTRY32W.szExeFile.offset, 44 if width == 8 else 36)
        self.assertEqual(ctypes.sizeof(wintypes.FILETIME), 8)
        fake = FakeKernel([])
        with patch.object(d.ctypes, "WinDLL", return_value=fake) as loader:
            self.assertIs(d._load_kernel(), fake)
        loader.assert_called_once_with("kernel32", use_last_error=True)
        self.assertEqual(fake.OpenProcess.argtypes, [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD])
        self.assertEqual(fake.Process32FirstW.argtypes[1], ctypes.POINTER(d.PROCESSENTRY32W))
        self.assertEqual(fake.GetProcessTimes.argtypes, [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4)
        self.assertFalse(hasattr(fake, "ReadProcessMemory"))
        self.assertFalse(hasattr(fake, "WriteProcessMemory"))

    def test_collects_both_architectures_and_never_opens_other_programs(self):
        path32, path64 = r"D:\SC\x86\StarCraft.exe", r"D:\SC\x86_64\StarCraft.exe"
        kernel = FakeKernel([(0, "System"), (50, "SC2_x64.exe"), (7, "StarCraft.exe"), (8, "STARCRAFT.EXE"), (9, "StarCraft II.exe")],
                            {7: {"path": path32, "start": START}, 8: {"path": path64, "start": START + 1}})
        games = self.run_discovery(kernel, {path32: 0x014C, path64: 0x8664})
        self.assertEqual([(g.pid, g.architecture, g.started_at) for g in games], [(8, "x86_64", START + 1), (7, "x86", START)])
        self.assertEqual(kernel.opens, [(0x1000, False, 7), (0x1000, False, 8)])
        self.assertCountEqual(kernel.closed, [10007, 10008, kernel.SNAPSHOT])

    def test_per_process_failures_leave_other_games_discoverable(self):
        records = {
            1: {"path": r"D:\SC\StarCraft.exe", "denied": True},
            2: {"path": r"D:\SC\StarCraft.exe", "image_fail": True},
            3: {"path": r"D:\SC\StarCraft.exe", "times_fail": True},
            4: {"path": r"D:\SC\StarCraft.exe", "exit": 0},
            5: {"path": r"D:\SC\StarCraft.exe", "exit_fail": True},
            6: {"path": r"D:\SC\StarCraft.exe"},
        }
        kernel = FakeKernel([(pid, "StarCraft.exe") for pid in records], records)
        self.assertEqual([game.pid for game in self.run_discovery(kernel)], [6])
        self.assertCountEqual(kernel.closed, [10002, 10003, 10004, 10005, 10006, kernel.SNAPSHOT])

    def test_stale_snapshot_name_invalid_pe_and_unknown_architecture_are_excluded(self):
        paths = {1: r"D:\SC\SC2.exe", 2: r"D:\Bad\StarCraft.exe", 3: r"D:\ARM\StarCraft.exe", 4: r"D:\Gone\StarCraft.exe"}
        kernel = FakeKernel([(pid, "StarCraft.exe") for pid in paths], {pid: {"path": path} for pid, path in paths.items()})
        games = self.run_discovery(kernel, {paths[2]: struct.error("truncated PE"), paths[3]: 0xAA64, paths[4]: FileNotFoundError()})
        self.assertEqual(games, [])
        self.assertCountEqual(kernel.closed, [10001, 10002, 10003, 10004, kernel.SNAPSHOT])

    def test_no_games_returns_empty_and_closes_snapshot(self):
        kernel = FakeKernel([])
        self.assertEqual(self.run_discovery(kernel), [])
        self.assertEqual(kernel.opens, [])
        self.assertEqual(kernel.closed, [kernel.SNAPSHOT])

    def test_snapshot_failure_raises_without_closing_invalid_handle(self):
        kernel = FakeKernel([], snapshot_error=5)
        with self.assertRaises(OSError):
            self.run_discovery(kernel)
        self.assertEqual(kernel.closed, [])

    def test_enumeration_failure_raises_and_closes_all_acquired_handles(self):
        kernel = FakeKernel([(7, "StarCraft.exe")], {7: {"path": r"D:\SC\StarCraft.exe"}}, iteration_error=5)
        with self.assertRaises(OSError):
            self.run_discovery(kernel)
        self.assertCountEqual(kernel.closed, [10007, kernel.SNAPSHOT])

    def test_unexpected_inspection_exception_still_closes_game_and_snapshot(self):
        kernel = FakeKernel([(7, "StarCraft.exe")], {7: {"path": r"D:\SC\StarCraft.exe"}})
        with patch.object(d, "_load_kernel", return_value=kernel), patch.object(d, "pe_machine", side_effect=RuntimeError("injected unexpected failure")):
            with self.assertRaisesRegex(RuntimeError, "unexpected failure"):
                d.discover_games()
        self.assertCountEqual(kernel.closed, [10007, kernel.SNAPSHOT])


if __name__ == "__main__":
    unittest.main()
