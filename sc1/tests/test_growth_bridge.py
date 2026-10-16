"""Growth extension compatibility, publication races, and owned-memory guards."""
import ctypes
import os
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sc1.bridge.protocol import (
    BridgeError, Dispatcher, UnstableMailbox, read_request, response_payload,
    publish_response, validate_header,
)
from sc1.bridge.windows import WindowsProcess
from sc1.tests.test_bridge import BASE, FakeMemory, FakeStore, fixture


def growth_fixture():
    data = fixture(101)
    # Independent wire fixture, not the constants under test.
    struct.pack_into('<II', data, 68, 0x47525731, 1)
    return data


class GrowthMemory(FakeMemory):
    def __init__(self):
        super().__init__(growth_fixture())

    def write(self, address, data):
        offset = address - BASE
        if not 128 <= offset < offset + len(data) <= 256:
            raise BridgeError('outside growth response')
        self.writes.append((address, bytes(data)))
        self.data[offset:offset+len(data)] = data
        if self.on_write:
            self.on_write(address, data)


class GrowthStore(FakeStore):
    words = [1, 0x80000001] + [0] * 14 + [0x80000000, 0x04030201, 0, 0, 0xFF000000]

    def restore_growth(self, mission, catalog_version):
        self.calls.append(('restore_growth', mission, catalog_version))
        return {**self.snapshot(), 'growth_words': self.words}


class GrowthWireTests(unittest.TestCase):
    def test_real_store_choices_wire_restart_commit_and_frozen_replay(self):
        from sc1.manager.store import open_campaign_store
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'campaign.sqlite3'
            store = open_campaign_store(path)
            memory = GrowthMemory()
            dispatch = Dispatcher(memory, BASE, store)
            dispatch.poll()
            memory.set(6, 1)
            self.assertEqual(dispatch.poll()['status'], 'waiting_for_choices')
            first_offer = store.growth_status()['offer']
            self.assertEqual(len(first_offer['candidates']), 4)
            store = open_campaign_store(path)
            self.assertEqual(store.growth_status()['offer'], first_offer)
            for index in range(5):
                state = store.growth_status()
                offer = state['offer']
                self.assertEqual(offer['kind'], 'talent' if index < 3 else 'curse')
                self.assertEqual(len(offer['candidates']), 4 if index < 3 else 3)
                store.choose_growth(offer['offer_id'], offer['candidates'][0]['id'], offer['revision'])
            expected = store.growth_status()['growth_words']
            self.assertEqual(sum(value.bit_count() for value in expected[1:17]), 3)
            self.assertEqual(sum(struct.pack('<4I', *expected[17:])), 2)
            memory.set(6, 2)
            self.assertEqual(dispatch.poll()['status'], 'restored')
            self.assertEqual(struct.unpack_from('<21I', memory.data, 172), tuple(expected))
            nonce = memory.data[144:160].hex()
            memory.set(19, 1)
            memory.commit_request(nonce, delta=0, observed=0)
            self.assertEqual(dispatch.poll()['status'], 'committed')
            self.assertEqual(store.growth_status()['upcoming'], {'talent':2, 'curse':2})
            # A lost completion ACK and restarted manager cannot award twice.
            restarted = Dispatcher(memory, BASE, open_campaign_store(path))
            restarted.poll()
            memory.set(6, 3)
            self.assertTrue(restarted.poll()['duplicate'])
            self.assertEqual(open_campaign_store(path).growth_status()['upcoming'], {'talent':2, 'curse':2})
            # Replaying this completed map restores its original loadout.
            replay = GrowthMemory()
            replay_dispatch = Dispatcher(replay, BASE, open_campaign_store(path))
            replay_dispatch.poll()
            replay.set(6, 1)
            self.assertEqual(replay_dispatch.poll()['status'], 'restored')
            self.assertEqual(struct.unpack_from('<21I', replay.data, 172), tuple(expected))
            self.assertEqual(replay.get(41) & 1, 1)

    def test_legacy_payload_stays_ten_words_even_if_store_has_growth(self):
        memory = FakeMemory(fixture(101))
        payload = response_payload(read_request(memory, BASE),
                                   {**FakeStore().snapshot(), 'growth_words': GrowthStore.words}, 1)
        self.assertEqual(len(payload), 40)
        publish_response(memory, BASE, read_request(memory, BASE), payload)
        self.assertEqual(memory.data[172:], bytes(84))

    def test_capability_requires_original_mission_and_known_version(self):
        for word, value in ((5, 1), (17, 17), (18, 2)):
            data = growth_fixture()
            struct.pack_into('<I', data, word*4, value)
            with self.subTest(word=word), self.assertRaises(BridgeError):
                validate_header(bytes(data), BASE)

    def test_complete_snapshot_is_inside_same_seqlock(self):
        memory = GrowthMemory()
        request = read_request(memory, BASE)
        payload = response_payload(request, {**FakeStore().snapshot(), 'growth_words': GrowthStore.words}, 1)
        self.assertEqual(len(payload), 124)
        publish_response(memory, BASE, request, payload)
        self.assertEqual([len(data) for _, data in memory.writes], [4, 124, 4])
        self.assertEqual(struct.unpack_from('<21I', memory.data, 172), tuple(GrowthStore.words))
        self.assertEqual(memory.get(32), 2)
        self.assertEqual(memory.get(63), 0xFF000000)

    def test_capability_change_during_save_prevents_even_publication(self):
        memory = GrowthMemory()
        request = read_request(memory, BASE)
        payload = response_payload(request, {**FakeStore().snapshot(), 'growth_words': GrowthStore.words}, 1)
        def change(address, _data):
            if address == BASE + 132:
                memory.set(17, 0)
        memory.on_write = change
        with self.assertRaises(UnstableMailbox):
            publish_response(memory, BASE, request, payload)
        self.assertEqual(memory.get(32) % 2, 1)

    def test_invalid_growth_data_never_reaches_publisher(self):
        request = read_request(GrowthMemory(), BASE)
        for words in (None, [1], [2]+[0]*20, [1, -1]+[0]*19, [1, True]+[0]*19):
            with self.subTest(words=words), self.assertRaises(BridgeError):
                response_payload(request, {**FakeStore().snapshot(), 'growth_words': words}, 1)

    def test_completion_does_not_resend_or_apply_growth(self):
        request = read_request(GrowthMemory(), BASE)
        payload = response_payload(request, FakeStore().snapshot(), 2)
        self.assertEqual(struct.unpack_from('<21I', payload, 40), (1,)+(0,)*20)

    def test_pending_choices_wait_without_publishing_or_creating_legacy_attempt(self):
        from sc1.manager.store import GrowthChoicesPending
        memory, store = GrowthMemory(), GrowthStore()
        def pending(*_):
            raise GrowthChoicesPending()
        store.restore_growth = pending
        dispatch = Dispatcher(memory, BASE, store)
        self.assertEqual(dispatch.poll()['status'], 'waiting_for_heartbeat')
        memory.set(6, 1)
        self.assertEqual(dispatch.poll()['status'], 'waiting_for_choices')
        self.assertFalse(memory.writes)
        self.assertFalse(store.calls)
        store.restore_growth = GrowthStore.restore_growth.__get__(store)
        memory.set(6, 2)
        self.assertEqual(dispatch.poll()['status'], 'restored')
        self.assertEqual(store.calls, [('restore_growth', 101, 1)])


@unittest.skipUnless(os.name == 'nt' and ctypes.sizeof(ctypes.c_void_p) == 8,
                     'Owned x64 allocation requires Windows')
class GrowthNativeMemoryTests(unittest.TestCase):
    def test_extended_response_bounds_and_reused_mailbox(self):
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.VirtualAlloc.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
        kernel.VirtualAlloc.restype = ctypes.c_void_p
        kernel.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32]
        kernel.VirtualFree.restype = ctypes.c_int
        address = kernel.VirtualAlloc(None, 4096, 0x103000, 0x04)
        self.assertTrue(address)
        try:
            ctypes.memmove(address, bytes(growth_fixture()), 256)
            # Test only our own allocated Python memory. Never open StarCraft.
            with patch('sc1.bridge.windows.validate_image', return_value=0x8664):
                with WindowsProcess(os.getpid(), allow_write=True) as memory:
                    memory.bind_mailbox(address)
                    request = read_request(memory, address)
                    payload = response_payload(request, {**FakeStore().snapshot(), 'growth_words': GrowthStore.words}, 1)
                    publish_response(memory, address, request, payload)
                    self.assertEqual(memory.read(address+172, 84), struct.pack('<21I', *GrowthStore.words))
                    for offset, size in ((0,4), (124,8), (252,8), (256,4)):
                        with self.subTest(offset=offset), self.assertRaises(BridgeError):
                            memory.write(address+offset, bytes(size))
                    ctypes.c_uint32.from_address(address+68).value = 0
                    with self.assertRaisesRegex(BridgeError, 'capability changed'):
                        memory.write(address+128, bytes(4))
                    memory.bind_mailbox(address)
                    with self.assertRaises(BridgeError):
                        memory.write(address+172, bytes(4))
        finally:
            self.assertTrue(kernel.VirtualFree(address, 0, 0x8000))
