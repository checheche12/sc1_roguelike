"""Read-only StarCraft process discovery for the local manager.

Only process metadata and on-disk PE headers are read. This module never reads
or writes another process's memory, starts games, or changes window focus.
`started_at` preserves GetProcessTimes' creation FILETIME without rounding, so
callers can reject a recycled PID when they later connect.

Win32 contracts:
https://learn.microsoft.com/windows/win32/api/tlhelp32/ns-tlhelp32-processentry32w
https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes
https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-queryfullprocessimagenamew
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import os
from pathlib import PureWindowsPath
import struct

from .protocol import BridgeError
from .windows import pe_machine

TH32CS_SNAPPROCESS = 0x00000002
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
ERROR_NO_MORE_FILES = 18
STILL_ACTIVE = 259
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value
FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=timezone.utc)


class PROCESSENTRY32W(ctypes.Structure):
    # ULONG_PTR follows the Python host's pointer width, not the target game's.
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", wintypes.WCHAR * 260),
    ]


@dataclass(frozen=True)
class GameProcess:
    pid: int
    image_path: str
    architecture: str  # "x86" or "x86_64"; unknown/unreadable images are omitted.
    started_at: int  # Raw 64-bit FILETIME: 100 ns since 1601-01-01T00:00:00Z.

    @property
    def label(self) -> str:
        bits = {"x86": "32비트", "x86_64": "64비트"}.get(self.architecture, "형식 미확인")
        try:
            local_start = (FILETIME_EPOCH + timedelta(microseconds=self.started_at // 10)).astimezone()
            start = local_start.strftime("%H:%M:%S")
        except (OverflowError, OSError, ValueError):
            start = "시각 미확인"
        # Full image directory distinguishes installations without exposing PID.
        return f"스타크래프트 · {bits} · 시작 {start} · {PureWindowsPath(self.image_path).parent}"


def _load_kernel():
    if os.name != "nt":
        raise OSError("StarCraft process discovery requires Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    for name in ("Process32FirstW", "Process32NextW"):
        method = getattr(kernel, name)
        method.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
        method.restype = wintypes.BOOL
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes = [
        wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    kernel.QueryFullProcessImageNameW.restype = wintypes.BOOL
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    kernel.GetProcessTimes.restype = wintypes.BOOL
    kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    return kernel


def _inspect_game(kernel, pid: int) -> GameProcess | None:
    handle = kernel.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return None  # Exited between snapshot and query, or access denied.
    try:
        image = ctypes.create_unicode_buffer(32768)
        length = wintypes.DWORD(len(image))
        if not kernel.QueryFullProcessImageNameW(handle, 0, image, ctypes.byref(length)):
            return None
        path = image.value
        # Snapshot names may be stale after PID reuse; verify the opened image.
        if PureWindowsPath(path).name.casefold() != "starcraft.exe":
            return None
        creation, exit_time, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
        if not kernel.GetProcessTimes(handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                      ctypes.byref(kernel_time), ctypes.byref(user_time)):
            return None
        started_at = (int(creation.dwHighDateTime) << 32) | int(creation.dwLowDateTime)
        if not started_at:
            return None
        try:
            architecture = {0x014C: "x86", 0x8664: "x86_64"}.get(pe_machine(path))
        except (OSError, BridgeError, ValueError, struct.error):
            return None  # Executable removed/replaced or unreadable while polling.
        if architecture is None:
            return None
        exit_code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(exit_code)) or exit_code.value != STILL_ACTIVE:
            return None
        return GameProcess(pid, path, architecture, started_at)
    finally:
        kernel.CloseHandle(handle)


def discover_games() -> list[GameProcess]:
    """Return accessible, running x86/x64 StarCraft images, newest first.

    Per-process failures are skipped so one inaccessible game does not hide a
    second usable instance. Snapshot/enumeration failures raise OSError instead
    of incorrectly reporting an empty or incomplete list. Every acquired handle
    is closed; callers receive data only. Discovery is not a live bridge test.
    """
    kernel = _load_kernel()
    snapshot = kernel.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snapshot in (None, 0, INVALID_HANDLE_VALUE):
        raise ctypes.WinError(ctypes.get_last_error())
    found: dict[tuple[int, int], GameProcess] = {}
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(entry)
    try:
        ok = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while ok:
            if entry.szExeFile.casefold() == "starcraft.exe" and entry.th32ProcessID:
                game = _inspect_game(kernel, int(entry.th32ProcessID))
                if game is not None:
                    found[(game.pid, game.started_at)] = game
            entry.dwSize = ctypes.sizeof(entry)
            ok = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        error = ctypes.get_last_error()
        if error != ERROR_NO_MORE_FILES:
            raise ctypes.WinError(error)
    finally:
        kernel.CloseHandle(snapshot)
    return sorted(found.values(), key=lambda game: (-game.started_at, game.image_path.casefold(), game.pid))
