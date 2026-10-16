"""Offline transport verification. These tests never attach to StarCraft."""
import struct
import tempfile
import unittest
from pathlib import Path

from sc1.bridge.protocol import (BridgeError, Dispatcher, MAGIC, MAILBOX_SIZE,
                                 UnstableMailbox, read_request, validate_header)
from sc1.bridge.windows import Region, find_mailboxes
from sc1.bridge.__main__ import inspect_candidates, wait_for_active, wait_for_probe
from sc1.manager.store import CampaignStore


BASE = 0x10000


def fixture(mission=1):
    # Independent bytes fixture: avoids using protocol.MAGIC or WORDS to create
    # the header that their own validation would then inspect.
    data = bytearray(256)
    data[:16] = bytes.fromhex("53433143414d502d50524f42452d5631")
    struct.pack_into("<5I", data, 16, 1, mission, 0, 1, 2)
    struct.pack_into("<I", data, 36, 1)
    struct.pack_into("<I", data, 64, 64)
    return data


class FakeMemory:
    def __init__(self, data=None):
        self.data = bytearray(fixture() if data is None else data)
        self.writes = []
        self.on_read = None
        self.on_write = None

    def regions(self):
        yield Region(BASE, len(self.data))

    def read(self, address, size):
        if self.on_read:
            self.on_read(address, size)
        offset = address - BASE
        if offset < 0 or offset + size > len(self.data):
            raise BridgeError("out of bounds")
        return bytes(self.data[offset:offset + size])

    def write(self, address, data):
        offset = address - BASE
        if not 128 <= offset < offset + len(data) <= 172:
            raise BridgeError("outside manager response")
        self.writes.append((address, bytes(data)))
        self.data[offset:offset + len(data)] = data
        if self.on_write:
            self.on_write(address, data)

    def set(self, word, value):
        struct.pack_into("<I", self.data, word * 4, value)

    def get(self, word):
        return struct.unpack_from("<I", self.data, word * 4)[0]

    def commit_request(self, nonce, *, sequence=6, delta=123, observed=0):
        self.set(8, sequence - 1)
        self.set(7, 3)
        self.set(9, 2)
        self.data[40:56] = bytes.fromhex(nonce)
        self.set(14, delta)
        self.set(15, observed)
        self.set(8, sequence)


class FakeStore:
    nonce = "0123456789abcdef1020304050607080"

    def __init__(self):
        self.gold = 0
        self.completed = False
        self.calls = []

    def restore(self, mission):
        self.calls.append(("restore", mission))
        return self.snapshot()

    def complete(self, mission, nonce, gold_delta, observed_gold):
        self.calls.append(("complete", mission, nonce, gold_delta, observed_gold))
        if nonce != self.nonce or gold_delta != 123 or observed_gold != 0:
            raise ValueError("invalid fixture result")
        duplicate = self.completed
        if not duplicate:
            self.gold += gold_delta
            self.completed = True
        return {**self.snapshot(), "duplicate": duplicate}

    def snapshot(self):
        return {"nonce": self.nonce, "gold": self.gold,
                "revision": 1 if self.completed else 0,
                "completed_mask": 1 if self.completed else 0}


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.memory = FakeMemory()
        self.store = FakeStore()
        self.now = 0.0
        self.dispatch = Dispatcher(self.memory, BASE, self.store, clock=lambda: self.now)

    def restore(self):
        self.assertEqual(self.dispatch.poll()["status"], "waiting_for_heartbeat")
        self.memory.set(6, 1)
        return self.dispatch.poll()

    def test_independent_fixed_layout_fixture(self):
        self.assertEqual(len(fixture()), 256)
        self.assertEqual(len(MAGIC), 16)
        header = validate_header(bytes(fixture()), BASE)
        self.assertEqual((header[4], header[5], header[8], header[16]), (1, 1, 2, 64))
        request = read_request(self.memory, BASE)
        self.assertEqual((request.sequence, request.operation, request.nonce), (2, 1, "00" * 16))

    def test_header_rejects_signature_version_length_mission_address(self):
        for word, value in ((0, 0), (4, 2), (5, 99), (16, 65)):
            with self.subTest(word=word):
                data = fixture()
                struct.pack_into("<I", data, word * 4, value)
                with self.assertRaises(BridgeError):
                    validate_header(bytes(data), BASE)
        with self.assertRaises(BridgeError):
            validate_header(bytes(fixture()), BASE + 1)
        with self.assertRaises(BridgeError):
            validate_header(bytes(fixture())[:-1], BASE)

    def test_no_storage_or_write_before_heartbeat_advances(self):
        self.dispatch.poll()
        self.dispatch.poll()
        self.assertEqual(self.store.calls, [])
        self.assertEqual(self.memory.writes, [])

    def test_initial_frozen_heartbeat_times_out_without_writes(self):
        self.assertEqual(self.dispatch.poll()["status"], "waiting_for_heartbeat")
        self.now = 4.0
        with self.assertRaisesRegex(BridgeError, "heartbeat stopped"):
            self.dispatch.poll()
        self.assertEqual(self.store.calls, [])
        self.assertEqual(self.memory.writes, [])

    def test_restore_publishes_nonce_snapshot_and_sequence_last(self):
        self.assertEqual(self.restore()["status"], "restored")
        self.assertEqual(self.store.calls, [("restore", 1)])
        self.assertEqual([address - BASE for address, _ in self.memory.writes], [128, 132, 128])
        self.assertEqual(struct.unpack("<I", self.memory.writes[0][1])[0], 1)
        self.assertEqual(self.memory.get(32), 2)
        self.assertEqual((self.memory.get(33), self.memory.get(34), self.memory.get(35)), (1, 2, 0))
        self.assertEqual(self.memory.data[144:160].hex(), self.store.nonce)
        self.dispatch.poll()
        self.assertEqual(len(self.store.calls), 1)

    def test_store_commits_before_saved_then_duplicate_does_not_add_gold(self):
        self.restore()
        self.memory.commit_request(self.store.nonce)
        writes_before = len(self.memory.writes)
        real_complete = self.store.complete

        def assert_before_write(*args):
            self.assertEqual(len(self.memory.writes), writes_before)
            return real_complete(*args)

        self.store.complete = assert_before_write
        event = self.dispatch.poll()
        self.assertEqual((event["status"], self.memory.get(33), self.memory.get(35)), ("committed", 2, 123))
        self.assertEqual(self.memory.get(40), 1)
        self.assertEqual(self.memory.get(41), 1)
        # Simulated manager restart before the map consumes the acknowledgment.
        self.store.complete = real_complete
        restarted = Dispatcher(self.memory, BASE, self.store)
        restarted.poll()
        self.memory.set(6, 2)
        self.assertTrue(restarted.poll()["duplicate"])
        self.assertEqual(self.store.gold, 123)

    def test_odd_or_changing_map_sequence_is_never_dispatched(self):
        self.memory.set(8, 3)
        with self.assertRaises(UnstableMailbox):
            self.dispatch.poll()
        self.memory.set(8, 2)

        def mutate_on_full_read(address, size):
            if size == MAILBOX_SIZE:
                self.memory.set(8, 4)

        self.memory.on_read = mutate_on_full_read
        with self.assertRaises(UnstableMailbox):
            self.dispatch.poll()
        self.assertEqual(self.store.calls, [])

    def test_io_failure_never_publishes_saved(self):
        self.restore()
        self.memory.commit_request(self.store.nonce)
        writes_before = len(self.memory.writes)

        def disk_full(*_):
            raise OSError("disk full")

        self.store.complete = disk_full
        with self.assertRaises(OSError):
            self.dispatch.poll()
        self.assertEqual(len(self.memory.writes), writes_before)
        self.assertEqual(self.memory.get(33), 1)

    def test_manager_rejection_publishes_error_and_stops(self):
        self.restore()
        self.memory.commit_request(self.store.nonce, delta=999)
        with self.assertRaisesRegex(BridgeError, "rejected"):
            self.dispatch.poll()
        self.assertEqual((self.memory.get(33), self.memory.get(42)), (3, 1))
        self.assertEqual(self.store.gold, 0)

    def test_stopped_heartbeat_disables_writes(self):
        self.restore()
        self.memory.commit_request(self.store.nonce)
        writes_before = len(self.memory.writes)
        self.now = 4.0
        with self.assertRaisesRegex(BridgeError, "heartbeat stopped"):
            self.dispatch.poll()
        self.assertEqual(len(self.memory.writes), writes_before)
        self.assertEqual(self.store.gold, 0)

    def test_changed_request_while_saving_does_not_publish(self):
        self.restore()
        self.memory.commit_request(self.store.nonce)
        writes_before = len(self.memory.writes)
        real_complete = self.store.complete

        def changed_map(*args):
            result = real_complete(*args)
            self.memory.set(8, 8)
            return result

        self.store.complete = changed_map
        with self.assertRaises(UnstableMailbox):
            self.dispatch.poll()
        self.assertEqual(len(self.memory.writes), writes_before)
        self.assertEqual(self.store.gold, 123)  # Durable; retry is deduplicated.

    def test_interrupted_publication_leaves_odd_sequence(self):
        self.restore()
        self.memory.commit_request(self.store.nonce)

        def changed_map(address, _data):
            if address == BASE + 132:
                self.memory.set(8, 8)

        self.memory.on_write = changed_map
        with self.assertRaises(UnstableMailbox):
            self.dispatch.poll()
        self.assertEqual(self.memory.get(32) % 2, 1)

    def test_idle_states_do_not_dispatch(self):
        self.restore()
        calls_before = len(self.store.calls)
        for state, result in ((2, "running"), (4, "saved"), (5, "map_error")):
            self.memory.set(7, state)
            self.memory.set(9, 0)
            self.assertEqual(self.dispatch.poll()["status"], result)
        self.assertEqual(len(self.store.calls), calls_before)

    def test_read_only_scanner_finds_chunk_boundary_and_rejects_bad_length(self):
        # Signature starts at 252 and crosses the 256-byte scanning boundary.
        memory = FakeMemory(bytes(252) + fixture() + bytes(260))
        self.assertEqual(find_mailboxes(memory, chunk_size=256), [BASE + 252])
        self.assertEqual(memory.writes, [])
        struct.pack_into("<I", memory.data, 252 + 64, 63)
        self.assertEqual(find_mailboxes(memory, chunk_size=256), [])

    def test_candidate_liveness_distinguishes_stale_copy(self):
        memory = FakeMemory(fixture() + fixture())

        def advance_first(_delay):
            memory.set(6, 1)

        candidates = inspect_candidates(memory, sleep=advance_first)
        self.assertEqual([c["active"] for c in candidates], [True, False])
        self.assertEqual(memory.writes, [])

    def test_wait_for_active_gives_user_time_to_unpause_without_writes(self):
        candidates = inspect_candidates(self.memory, sleep=lambda _: None)
        elapsed = [0.0]

        def unpause_after_half_second(delay):
            elapsed[0] += delay
            if elapsed[0] >= 0.5:
                self.memory.set(6, 1)

        result = wait_for_active(self.memory, candidates, timeout=1,
                                 clock=lambda: elapsed[0], sleep=unpause_after_half_second)
        self.assertTrue(result[0]["active"])
        self.assertEqual(self.memory.writes, [])

    def test_real_store_a_commit_restart_duplicate_and_b_restore(self):
        with tempfile.TemporaryDirectory() as temporary:
            database = Path(temporary) / "growth.sqlite3"
            first_store = CampaignStore(database)
            first_map = FakeMemory(fixture(1))
            first_dispatch = Dispatcher(first_map, BASE, first_store)
            first_dispatch.poll()
            first_map.set(6, 1)
            self.assertEqual(first_dispatch.poll()["status"], "restored")
            first_nonce = first_map.data[144:160].hex()
            first_map.commit_request(first_nonce)
            self.assertEqual(first_dispatch.poll()["gold"], 123)

            # Ack loss + process restart uses the same durable record exactly once.
            restart_store = CampaignStore(database)
            retry_dispatch = Dispatcher(first_map, BASE, restart_store)
            retry_dispatch.poll()
            first_map.set(6, 2)
            self.assertTrue(retry_dispatch.poll()["duplicate"])
            self.assertEqual(restart_store.status()["gold"], 123)

            # A new map and manager instance restore from disk, not shared objects.
            second_store = CampaignStore(database)
            second_map = FakeMemory(fixture(2))
            second_dispatch = Dispatcher(second_map, BASE, second_store)
            second_dispatch.poll()
            second_map.set(6, 1)
            self.assertEqual(second_dispatch.poll()["gold"], 123)
            self.assertEqual((second_map.get(33), second_map.get(35), second_map.get(41)), (1, 123, 1))
            second_nonce = second_map.data[144:160].hex()
            self.assertNotEqual(first_nonce, second_nonce)
            second_map.commit_request(second_nonce, delta=0, observed=123)
            self.assertEqual(second_dispatch.poll()["status"], "committed")
            self.assertEqual((second_map.get(35), second_map.get(41)), (123, 3))
            self.assertEqual(CampaignStore(database).status()["completed_mask"], 3)


class WaitingForMapTests(unittest.TestCase):
    def setUp(self):
        from unittest.mock import Mock
        self.memory = Mock()
        self.memory.is_running.return_value = True
        self.elapsed = 0
        self.events = []

    def sleep(self, seconds):
        self.elapsed += seconds

    def wait(self, candidates, inspector, deadline=None):
        return wait_for_probe(self.memory, candidates, deadline=deadline,
                              clock=lambda: self.elapsed, sleep=self.sleep,
                              inspect=inspector, report=self.events.append)

    def test_menu_then_paused_map_then_live_map_is_not_an_error(self):
        paused = {"address": BASE, "active": False}
        active = {"address": BASE, "active": True}
        observations = iter([[], [paused], [active]])
        result = self.wait([], lambda _: next(observations))
        self.assertEqual(result, active)
        self.assertEqual([item["status"] for item in self.events],
                         ["waiting_for_map", "waiting_for_unpause"])
        self.memory.write.assert_not_called()
        self.memory.bind_mailbox.assert_not_called()

    def test_menu_wait_deadline_does_not_write_or_bind(self):
        result = self.wait([], lambda _: [], deadline=7)
        self.assertIsNone(result)
        self.assertEqual(self.elapsed, 7)
        self.assertEqual(len(self.events), 1)
        self.memory.write.assert_not_called()
        self.memory.bind_mailbox.assert_not_called()

    def test_game_exit_ends_wait(self):
        def exit_game(_):
            self.memory.is_running.return_value = False
            return []
        with self.assertRaises(BridgeError):
            self.wait([], exit_game)
        self.memory.write.assert_not_called()

    def test_multiple_active_mailboxes_are_not_chosen_arbitrarily(self):
        candidates = [{"address": BASE, "active": True},
                      {"address": BASE + 256, "active": True}]
        with self.assertRaises(BridgeError):
            self.wait(candidates, lambda _: self.fail("No further scan expected"))
        self.memory.write.assert_not_called()
        self.memory.bind_mailbox.assert_not_called()


if __name__ == "__main__":
    unittest.main()
