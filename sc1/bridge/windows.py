"""Windows x86/x64 transport, separate from the DWORD mailbox protocol.

SC-REPL's documented approach is used as a reference, not copied code:
https://github.com/mighty1231/screpl/wiki/Bridge
https://github.com/mighty1231/screpl/blob/master/bridge-client/worker.cpp

No API is loaded or process opened on import. Open by explicit PID, verify its
image is StarCraft.exe and its PE machine is x86 or x64, scan read/write private data
pages. Writes are limited to the response words of a validated mailbox.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import os
from pathlib import Path
import struct

from .protocol import (BridgeError, MAGIC, MAILBOX_SIZE, MAX_ADDRESS,
                       RESPONSE_SEQUENCE, RESPONSE_END, GROWTH_RESPONSE_END, GROWTH_V2_RESPONSE_END,
                       growth_version, validate_header)


@dataclass(frozen=True)
class Region:
    base: int
    size: int


class WriterBusyError(BridgeError):
    """Another live bridge holds the single-writer guard."""


class MailboxUnavailable(BridgeError):
    """The bound map-owned allocation was retired; writer ownership is retained."""


def pe_machine(path: str | Path) -> int:
    with open(path, "rb") as source:
        if source.read(2) != b"MZ":
            raise BridgeError("Process image does not have a DOS header")
        source.seek(60)
        offset = struct.unpack("<I", source.read(4))[0]
        source.seek(offset)
        if source.read(4) != b"PE\0\0":
            raise BridgeError("Process image does not have a PE header")
        return struct.unpack("<H", source.read(2))[0]


def validate_image(path: str) -> int:
    if Path(path).name.casefold() != "starcraft.exe":
        raise BridgeError("Only an explicit StarCraft.exe process is supported")
    machine = pe_machine(path)
    if machine not in (0x14C, 0x8664):
        raise BridgeError("Only x86 or x64 StarCraft.exe images are supported")
    return machine


def target_address_limit(machine: int, host_pointer_bytes: int, system_max: int) -> int:
    if machine == 0x14C:
        return 0x1_0000_0000
    if machine != 0x8664:
        raise BridgeError("Unsupported target architecture")
    if host_pointer_bytes != 8:
        raise BridgeError("64비트 스타1에 연결하려면 관리자를 64비트 Python으로 실행해야 합니다.")
    limit = min(system_max + 1, MAX_ADDRESS)
    if limit <= 0x1_0000_0000:
        raise BridgeError("The system did not report a usable x64 address range")
    return limit


def find_mailboxes(memory, *, chunk_size: int = 1024 * 1024, stopped=lambda: False) -> list[int]:
    """Read-only scan. Retains overlaps so a magic spanning chunks is found."""
    if chunk_size < MAILBOX_SIZE:
        raise ValueError("Scan chunk must fit one mailbox")
    found = set()
    for region in memory.regions():
        if stopped():
            break
        tail = b""
        cursor = region.base
        end = min(region.base + region.size, getattr(memory, "max_address", MAX_ADDRESS))
        while cursor < end:
            if stopped():
                return sorted(found)
            amount = min(chunk_size, end - cursor)
            try:
                data = memory.read(cursor, amount)
            except OSError as exc:
                if getattr(exc, "winerror", None) not in (None, 299, 487, 998):
                    raise
                tail = b""
                cursor += amount
                continue
            except BridgeError:
                # A region may vanish during a scan. It is never a write target.
                tail = b""
                cursor += amount
                continue
            combined = tail + data
            start = 0
            while True:
                index = combined.find(MAGIC, start)
                if index < 0:
                    break
                candidate = cursor - len(tail) + index
                if candidate + MAILBOX_SIZE <= end:
                    try:
                        validate_header(memory.read(candidate, MAILBOX_SIZE), candidate)
                        found.add(candidate)
                    except OSError as exc:
                        if getattr(exc, "winerror", None) not in (None, 299, 487, 998):
                            raise
                    except BridgeError:
                        pass
                start = index + 1
            tail = combined[-(MAILBOX_SIZE - 1):]
            cursor += amount
    return sorted(found)


class WindowsProcess:
    def __init__(self, pid: int, *, allow_write: bool = False, expected_start_time: int | None = None):
        if os.name != "nt":
            raise BridgeError("The live memory adapter requires Windows")
        if isinstance(pid, bool) or not isinstance(pid, int) or not 0 < pid <= 0xFFFFFFFF:
            raise BridgeError("Supply an explicit positive process ID")
        if expected_start_time is not None and (type(expected_start_time) is not int or expected_start_time <= 0):
            raise BridgeError("Expected process start time must be a positive FILETIME")
        self.pid, self.allow_write, self.mailbox = pid, allow_write, None
        self.writer_mutex = None
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self._configure_api()
        rights = 0x0400 | 0x0010  # QUERY_INFORMATION | VM_READ
        if allow_write:
            rights |= 0x0020 | 0x0008  # VM_WRITE | VM_OPERATION
        self.handle = self.kernel.OpenProcess(rights, False, pid)
        if not self.handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            length = wintypes.DWORD(32768)
            image = ctypes.create_unicode_buffer(length.value)
            if not self.kernel.QueryFullProcessImageNameW(self.handle, 0, image, ctypes.byref(length)):
                raise ctypes.WinError(ctypes.get_last_error())
            self.image_path = image.value
            self.machine = validate_image(self.image_path)
            self.architecture = "x86" if self.machine == 0x14C else "x86_64"
            info = self.SYSTEM_INFO()
            self.kernel.GetSystemInfo(ctypes.byref(info))
            self.max_address = target_address_limit(self.machine, ctypes.sizeof(ctypes.c_void_p),
                                                    info.lpMaximumApplicationAddress or 0)
            self.started_at = self._start_time()
            if expected_start_time is not None and self.started_at != expected_start_time:
                raise BridgeError("선택한 게임이 종료되거나 다시 실행되었습니다. '스타1 찾아 연결'을 다시 눌러 주세요.")
            if allow_write:
                self._claim_writer()
        except BaseException:
            self.close()
            raise

    def _configure_api(self):
        k = self.kernel
        k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        k.OpenProcess.restype = wintypes.HANDLE
        k.CloseHandle.argtypes = [wintypes.HANDLE]
        k.CloseHandle.restype = wintypes.BOOL
        k.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
        k.CreateMutexW.restype = wintypes.HANDLE
        k.ReleaseMutex.argtypes = [wintypes.HANDLE]
        k.ReleaseMutex.restype = wintypes.BOOL
        k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
        k.QueryFullProcessImageNameW.restype = wintypes.BOOL
        k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        k.GetProcessTimes.restype = wintypes.BOOL
        k.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        k.GetExitCodeProcess.restype = wintypes.BOOL
        class SYSTEM_INFO(ctypes.Structure):
            _fields_ = [("wProcessorArchitecture", wintypes.WORD), ("wReserved", wintypes.WORD),
                        ("dwPageSize", wintypes.DWORD), ("lpMinimumApplicationAddress", ctypes.c_void_p),
                        ("lpMaximumApplicationAddress", ctypes.c_void_p), ("dwActiveProcessorMask", ctypes.c_size_t),
                        ("dwNumberOfProcessors", wintypes.DWORD), ("dwProcessorType", wintypes.DWORD),
                        ("dwAllocationGranularity", wintypes.DWORD), ("wProcessorLevel", wintypes.WORD),
                        ("wProcessorRevision", wintypes.WORD)]
        self.SYSTEM_INFO = SYSTEM_INFO
        k.GetSystemInfo.argtypes = [ctypes.POINTER(SYSTEM_INFO)]
        k.GetSystemInfo.restype = None
        # Native host layout: 48 bytes on 64-bit Python, 28 on 32-bit Python.
        class MBI(ctypes.Structure):
            _fields_ = [("BaseAddress", ctypes.c_void_p),
                        ("AllocationBase", ctypes.c_void_p),
                        ("AllocationProtect", wintypes.DWORD),
                        ("RegionSize", ctypes.c_size_t),
                        ("State", wintypes.DWORD),
                        ("Protect", wintypes.DWORD),
                        ("Type", wintypes.DWORD)]
        self.MBI = MBI
        k.VirtualQueryEx.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                     ctypes.POINTER(MBI), ctypes.c_size_t]
        k.VirtualQueryEx.restype = ctypes.c_size_t
        for name in ("ReadProcessMemory", "WriteProcessMemory"):
            api = getattr(k, name)
            api.argtypes = [wintypes.HANDLE, ctypes.c_void_p, ctypes.c_void_p,
                            ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
            api.restype = wintypes.BOOL

    def _start_time(self):
        creation, exit_time, kernel_time, user_time = (wintypes.FILETIME() for _ in range(4))
        if not self.kernel.GetProcessTimes(self.handle, ctypes.byref(creation), ctypes.byref(exit_time),
                                            ctypes.byref(kernel_time), ctypes.byref(user_time)):
            raise ctypes.WinError(ctypes.get_last_error())
        return (creation.dwHighDateTime << 32) | creation.dwLowDateTime

    def is_running(self):
        code = wintypes.DWORD()
        if not self.handle or not self.kernel.GetExitCodeProcess(self.handle, ctypes.byref(code)):
            return False
        return code.value == 259  # STILL_ACTIVE

    def close(self):
        if self.writer_mutex:
            self.kernel.ReleaseMutex(self.writer_mutex)
            self.kernel.CloseHandle(self.writer_mutex)
            self.writer_mutex = None
        if self.handle:
            self.kernel.CloseHandle(self.handle)
            self.handle = None

    def _claim_writer(self):
        # The seqlock assumes a single writer. Prevent a second instance of this
        # bridge (including another manager database) from publishing to a PID.
        ctypes.set_last_error(0)
        mutex = self.kernel.CreateMutexW(None, True, f"Local\\SC1CampaignProbeBridge-{self.pid}")
        if not mutex:
            raise ctypes.WinError(ctypes.get_last_error())
        if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
            self.kernel.CloseHandle(mutex)
            raise WriterBusyError("다른 관리자에서 이미 이 스타1에 연결 중입니다. 기존 관리자에서 연결을 중지한 뒤 다시 연결해 주세요.")
        self.writer_mutex = mutex

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _query(self, address: int):
        mbi = self.MBI()
        if self.kernel.VirtualQueryEx(self.handle, address, ctypes.byref(mbi), ctypes.sizeof(mbi)) != ctypes.sizeof(mbi):
            raise ctypes.WinError(ctypes.get_last_error())
        return mbi

    def regions(self):
        cursor = 0x10000
        while cursor < self.max_address:
            try:
                mbi = self._query(cursor)
            except OSError as exc:
                # Reaching the target's highest valid address ends enumeration.
                if getattr(exc, "winerror", None) == 87:
                    break
                raise
            base = mbi.BaseAddress or 0
            end = base + mbi.RegionSize
            if end <= cursor:
                raise BridgeError("VirtualQueryEx returned a non-advancing region")
            if mbi.State == 0x1000 and mbi.Type == 0x20000 and mbi.Protect == 0x04:
                yield Region(base, mbi.RegionSize)
            cursor = end

    def read(self, address: int, size: int) -> bytes:
        if not self.handle or size < 1 or address < 0x10000 or address + size > self.max_address:
            raise BridgeError("Read is outside the open target process bounds")
        data = ctypes.create_string_buffer(size)
        transferred = ctypes.c_size_t()
        ok = self.kernel.ReadProcessMemory(self.handle, address, data, size,
                                           ctypes.byref(transferred))
        if not ok or transferred.value != size:
            error = ctypes.get_last_error()
            if (self.mailbox is not None and self.mailbox <= address < address + size <= self.mailbox + MAILBOX_SIZE
                    and error in (299, 487, 998)):
                raise MailboxUnavailable("Bound mailbox allocation is no longer readable") from ctypes.WinError(error)
            raise ctypes.WinError(error)
        return data.raw

    def bind_mailbox(self, address: int):
        """Allowlist one mailbox after the caller confirms advancing heartbeat."""
        try:
            data = self.read(address, MAILBOX_SIZE)
            if data[:16] == bytes(16):
                raise MailboxUnavailable("Candidate mailbox was retired before binding")
            words = validate_header(data, address)
            self._validate_region(address, candidate=True)
        except OSError as exc:
            if getattr(exc, "winerror", None) in (299, 487, 998):
                raise MailboxUnavailable("Candidate mailbox disappeared before binding") from exc
            raise
        self.mailbox = address
        self.bound_growth_version = growth_version(words)
        self.response_end = GROWTH_V2_RESPONSE_END if self.bound_growth_version==2 else GROWTH_RESPONSE_END if self.bound_growth_version else RESPONSE_END
        self._validate_region(address)

    def unbind_mailbox(self):
        """Revoke writes during map discovery without releasing the PID mutex."""
        self.mailbox = None
        self.bound_growth_version = 0
        self.response_end = RESPONSE_END

    def bound_header(self):
        if self.mailbox is None:
            raise BridgeError("No validated mailbox is bound")
        self._validate_region(self.mailbox)
        data = self.read(self.mailbox, MAILBOX_SIZE)
        if data[:16] == bytes(16):
            raise MailboxUnavailable("Map explicitly retired its mailbox signature")
        words = validate_header(data, self.mailbox)
        if growth_version(words) != self.bound_growth_version:
            raise BridgeError("Bound mailbox growth capability changed; reconnect")
        return words

    def _validate_region(self, address: int, *, candidate=False):
        try:
            mbi = self._query(address)
        except OSError as exc:
            if (candidate or self.mailbox == address) and getattr(exc, "winerror", None) in (299, 487, 998):
                raise MailboxUnavailable("Bound mailbox allocation disappeared") from exc
            raise
        if (candidate or self.mailbox == address) and (mbi.State != 0x1000 or mbi.Protect == 0x01):
            raise MailboxUnavailable("Bound mailbox allocation was released or quarantined")
        if (mbi.State != 0x1000 or mbi.Type != 0x20000 or mbi.Protect != 0x04
                or address + (512 if getattr(self,'bound_growth_version',0)==2 else MAILBOX_SIZE) > (mbi.BaseAddress or 0) + mbi.RegionSize):
            raise BridgeError("Mailbox is no longer inside one private read/write region")

    def write(self, address: int, data: bytes) -> None:
        if not self.allow_write:
            raise BridgeError("Process was opened read-only")
        if self.mailbox is None:
            raise BridgeError("No validated mailbox is bound for writing")
        start = self.mailbox + RESPONSE_SEQUENCE * 4
        end = self.mailbox + getattr(self, "response_end", RESPONSE_END) * 4
        if not data or address % 4 or len(data) % 4 or not start <= address < address + len(data) <= end:
            raise BridgeError("Write is outside manager-owned mailbox response words")
        self.bound_header()
        transferred = ctypes.c_size_t()
        buffer = ctypes.create_string_buffer(data)
        ok = self.kernel.WriteProcessMemory(self.handle, address, buffer, len(data),
                                            ctypes.byref(transferred))
        if not ok or transferred.value != len(data):
            error = ctypes.get_last_error()
            if error in (299, 487, 998):
                raise MailboxUnavailable("Bound mailbox disappeared during response publication") from ctypes.WinError(error)
            raise ctypes.WinError(error)
