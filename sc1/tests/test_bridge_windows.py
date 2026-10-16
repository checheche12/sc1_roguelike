"""Image/permission guards and an owned Python-process x64 mailbox test.

No StarCraft process is opened. Native tests allocate/free their own data page.
"""
import ctypes
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sc1.bridge.protocol import BridgeError, Dispatcher, MAX_ADDRESS
from sc1.bridge.windows import WindowsProcess, validate_image, target_address_limit, find_mailboxes, Region
from sc1.manager.store import CampaignStore


def image_fixture(path, machine):
    data = bytearray(134)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 60, 128)
    data[128:132] = b"PE\0\0"
    struct.pack_into("<H", data, 132, machine)
    path.write_bytes(data)


class WindowsGuardTests(unittest.TestCase):
    def test_image_must_be_named_starcraft_and_supported_architecture(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "StarCraft.exe"
            image_fixture(target, 0x014C)
            self.assertEqual(validate_image(str(target)), 0x014C)
            image_fixture(target, 0x8664)
            self.assertEqual(validate_image(str(target)), 0x8664)
            image_fixture(target, 0xAA64)
            with self.assertRaisesRegex(BridgeError, "x86 or x64"):
                validate_image(str(target))
            other = Path(temporary) / "SC2.exe"
            image_fixture(other, 0x014C)
            with self.assertRaisesRegex(BridgeError, "StarCraft.exe"):
                validate_image(str(other))

    def test_write_refuses_read_only_unbound_and_map_owned_bytes(self):
        # Bypass constructor: no Win32 API is loaded, no process is attached.
        memory = WindowsProcess.__new__(WindowsProcess)
        memory.allow_write = False
        memory.mailbox = 0x10000
        with self.assertRaisesRegex(BridgeError, "read-only"):
            memory.write(0x10080, bytes(4))
        memory.allow_write = True
        memory.mailbox = None
        with self.assertRaisesRegex(BridgeError, "bound"):
            memory.write(0x10080, bytes(4))
        memory.mailbox = 0x10000
        for address, length in ((0x10000, 4), (0x1007C, 4), (0x100A8, 8),
                                (0x100AC, 4), (0x10081, 4), (0x10080, 3)):
            with self.subTest(address=address, length=length):
                with self.assertRaisesRegex(BridgeError, "outside"):
                    memory.write(address, bytes(length))

    def test_target_address_limits_and_32bit_host_rejects_x64(self):
        self.assertEqual(target_address_limit(0x14C, 8, MAX_ADDRESS - 1), 1 << 32)
        self.assertEqual(target_address_limit(0x8664, 8, MAX_ADDRESS - 1), MAX_ADDRESS)
        self.assertEqual(target_address_limit(0x8664, 8, (1 << 40) - 1), 1 << 40)
        with self.assertRaises(BridgeError):
            target_address_limit(0x8664, 4, MAX_ADDRESS - 1)
        with self.assertRaises(BridgeError):
            target_address_limit(0xAA64, 8, MAX_ADDRESS - 1)


def native_fixture(mission=1):
    data = bytearray(256)
    data[:16] = bytes.fromhex("53433143414d502d50524f42452d5631")
    struct.pack_into("<6I", data, 16, 1, mission, 0, 1, 2, 1)
    struct.pack_into("<I", data, 64, 64)
    return data


@unittest.skipUnless(os.name == "nt" and ctypes.sizeof(ctypes.c_void_p) == 8,
                     "Native owned-memory test requires 64-bit Windows Python")
class NativeX64TransportTests(unittest.TestCase):
    def test_owned_high_address_memory_a_save_restart_b_restore(self):
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
        kernel.VirtualAlloc.restype = ctypes.c_void_p
        kernel.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
        kernel.VirtualFree.restype = ctypes.c_int
        address = kernel.VirtualAlloc(None, 4096, 0x1000 | 0x2000 | 0x100000, 0x04)
        self.assertTrue(address)
        try:
            self.assertGreaterEqual(address, 1 << 32)
            ctypes.memmove(address, bytes(native_fixture()), 256)
            with tempfile.TemporaryDirectory() as temporary, patch(
                "sc1.bridge.windows.validate_image", return_value=0x8664
            ):
                # The name allowlist is bypassed only in this test to open OUR
                # Python PID. All WinAPI memory/region/bounds checks are real.
                db = Path(temporary) / "native.sqlite3"
                with WindowsProcess(os.getpid(), allow_write=True) as memory:
                    self.assertEqual(memory.architecture, "x86_64")
                    self.assertTrue(memory.is_running())
                    start_time = memory.started_at
                    self.assertGreater(memory.max_address, address + 256)
                    with patch.object(memory, "regions", return_value=iter([Region(address, 4096)])):
                        self.assertEqual(find_mailboxes(memory), [address])
                    memory.bind_mailbox(address)
                    store = CampaignStore(db)
                    dispatcher = Dispatcher(memory, address, store)
                    self.assertEqual(dispatcher.poll()["status"], "waiting_for_heartbeat")
                    ctypes.c_uint32.from_address(address + 24).value = 1
                    self.assertEqual(dispatcher.poll()["status"], "restored")
                    restored = memory.read(address, 256)
                    nonce = restored[144:160]
                    request = bytearray(restored[:128])
                    struct.pack_into("<3I", request, 28, 3, 6, 2)
                    request[40:56] = nonce
                    struct.pack_into("<2I", request, 56, 123, 0)
                    ctypes.memmove(address, bytes(request), 128)
                    self.assertEqual(dispatcher.poll()["status"], "committed")
                    self.assertEqual(struct.unpack_from("<I", memory.read(address, 256), 140)[0], 123)
                # Reopen the actual process handle and the durable database.
                with WindowsProcess(os.getpid(), allow_write=True, expected_start_time=start_time) as memory:
                    memory.bind_mailbox(address)
                    store = CampaignStore(db)
                    retry = Dispatcher(memory, address, store)
                    retry.poll()
                    ctypes.c_uint32.from_address(address + 24).value = 2
                    self.assertTrue(retry.poll()["duplicate"])
                    self.assertEqual(store.status()["gold"], 123)
                    ctypes.memmove(address, bytes(native_fixture(2)), 256)
                    second_map = Dispatcher(memory, address, CampaignStore(db))
                    second_map.poll()
                    ctypes.c_uint32.from_address(address + 24).value = 1
                    self.assertEqual(second_map.poll()["gold"], 123)
                    with self.assertRaises(BridgeError):
                        memory.write(address, bytes(4))
                    with self.assertRaises(BridgeError):
                        memory.read(memory.max_address - 4, 8)
                with self.assertRaisesRegex(BridgeError, "다시 실행"):
                    WindowsProcess(os.getpid(), allow_write=True, expected_start_time=start_time + 1)
        finally:
            self.assertTrue(kernel.VirtualFree(address, 0, 0x8000))


if __name__ == "__main__":
    unittest.main()
