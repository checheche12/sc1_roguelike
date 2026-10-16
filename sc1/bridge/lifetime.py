"""Cancellable manager-pipe liveness without a blocking Python I/O thread.

Never call BufferedReader.read() on a daemon: interpreter finalization may need
that reader's lock while its thread is still blocked on the live parent's pipe.
The polling thread only observes pipe readiness/EOF; it consumes no bytes, owns
no extra handles and can stop while the parent keeps stdin open.
"""
from __future__ import annotations

import os
import threading
import time


def _pipe_probe(stream):
    descriptor = stream.fileno()
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes
        import msvcrt

        handle = msvcrt.get_osfhandle(descriptor)
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.GetFileType.argtypes = [wintypes.HANDLE]
        kernel.GetFileType.restype = wintypes.DWORD
        kernel.PeekNamedPipe.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                        ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
        kernel.PeekNamedPipe.restype = wintypes.BOOL
        if kernel.GetFileType(handle) != 3:  # FILE_TYPE_PIPE
            raise ValueError("Manager lifetime input must be an inherited pipe")

        def ready():
            available = wintypes.DWORD()
            if kernel.PeekNamedPipe(handle, None, 0, None, ctypes.byref(available), None):
                return bool(available.value)
            error = ctypes.get_last_error()
            if error in (109, 232):  # ERROR_BROKEN_PIPE / ERROR_NO_DATA
                return True
            raise ctypes.WinError(error)
    else:
        import select
        import stat
        if not stat.S_ISFIFO(os.fstat(descriptor).st_mode):
            raise ValueError("Manager lifetime input must be an inherited pipe")

        def ready():
            return bool(select.select([descriptor], [], [], 0)[0])
    return ready


class ManagerLifetime:
    """Event-like stop signal; close() cancels locally without closing stdin."""
    def __init__(self, stream):
        self._probe = _pipe_probe(stream)
        self._cancelled = threading.Event()

    def is_set(self):
        if not self._cancelled.is_set() and self._probe():
            self._cancelled.set()
        return self._cancelled.is_set()

    def wait(self, timeout=None):
        deadline = None if timeout is None else time.monotonic() + max(0, timeout)
        while not self.is_set():
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                return False
            self._cancelled.wait(0.05 if remaining is None else min(0.05, remaining))
        return True

    def close(self):
        self._cancelled.set()

    set = close


def watch_manager(stream):
    return ManagerLifetime(stream)
