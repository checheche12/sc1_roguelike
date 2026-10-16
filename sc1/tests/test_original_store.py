"""Real temporary SQLite files, separate processes and a bounded fake mailbox.

These checks establish durable records and wire behavior, not native gameplay.
No user database or StarCraft process is opened.
"""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock

from sc1.bridge.protocol import BridgeError, Dispatcher, validate_header
from sc1.campaign.catalog import MISSIONS
from sc1.campaign.missions import load_missions
from sc1.manager.__main__ import DEFAULT_DATABASE
from sc1.manager.store import CampaignStore, ProtocolError, open_campaign_store
from sc1.manager.ui import ManagerWindow, record_summary
from sc1.tests.test_bridge import BASE, FakeMemory, fixture


class OriginalStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "original.sqlite3"
        self.store = open_campaign_store(self.path)

    def assert_protocol_error(self, code, operation, *args):
        with self.assertRaises(ProtocolError) as caught:
            operation(*args)
        self.assertEqual(caught.exception.code, code)

    def test_application_and_library_defaults_are_separate_and_persisted(self):
        self.assertEqual(DEFAULT_DATABASE.name, "original.sqlite3")
        self.assertEqual(self.store.status()["profile"], "original")
        self.assertEqual(self.store.status()["supported_missions"], [m["mission_id"] for m in load_missions()])
        self.assertFalse(self.store.status()["sample_only"])
        self.assertEqual(CampaignStore(self.path).profile, "original")
        library_file = Path(self.tmp.name) / "probe.sqlite3"
        self.assertEqual(CampaignStore(library_file).profile, "probe")
        self.assertEqual(open_campaign_store(library_file).profile, "probe")
        with closing(sqlite3.connect(self.path)) as conn:
            self.assertEqual(conn.execute("SELECT value FROM metadata WHERE key='profile'").fetchone(), ("original",))

    def test_first_completion_survives_restart_and_completed_replay_is_read_only(self):
        first = self.store.restore(101)
        self.assertEqual(open_campaign_store(self.path).restore(101)["nonce"], first["nonce"])
        complete = self.store.complete(101, first["nonce"], 0, 0)
        self.assertEqual((complete["gold"], complete["revision"], complete["completed_mask"]), (0, 1, 1))
        before = self.path.read_bytes()
        reopened = open_campaign_store(self.path)
        replay = reopened.restore(101)
        self.assertTrue(replay["already_completed"])
        self.assertEqual(replay["nonce"], first["nonce"])
        self.assertEqual((replay["gold"], replay["revision"], replay["completed_mask"]), (0, 1, 1))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(len(reopened.status()["attempts"]), 1)

    def test_lost_ack_retry_is_deduplicated_in_separate_manager_process(self):
        root = Path(__file__).resolve().parents[2]

        def cli(*args):
            output = subprocess.check_output([sys.executable, "-m", "sc1.manager", "--db", str(self.path), *args], cwd=root)
            return json.loads(output)

        first = cli("restore", "--mission", "101")
        arguments = ("complete", "--mission", "101", "--nonce", first["nonce"],
                     "--gold-delta", "0", "--observed-gold", "0")
        initial = cli(*arguments)
        duplicate = cli(*arguments)
        self.assertFalse(initial["duplicate"])
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(duplicate["revision"], 1)
        replay = cli("restore", "--mission", "101")
        self.assertTrue(replay["already_completed"])
        self.assertEqual((replay["nonce"], replay["completed_mask"]), (first["nonce"], 1))

    def test_concurrent_completion_records_once(self):
        first = self.store.restore(101)
        with ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(pool.map(lambda _: open_campaign_store(self.path).complete(101, first["nonce"], 0, 0), range(8)))
        self.assertEqual(sum(not response["duplicate"] for response in replies), 1)
        self.assertEqual(self.store.status()["revision"], 1)
        self.assertEqual(self.store.status()["completed_mask"], 1)

    def test_failed_disk_commit_rolls_back_completion_then_retry_succeeds(self):
        first = self.store.restore(101)

        def disk_full(_connection):
            raise sqlite3.OperationalError("injected disk full")

        self.store._commit_result = disk_full
        with self.assertRaises(sqlite3.OperationalError):
            self.store.complete(101, first["nonce"], 0, 0)
        reopened = open_campaign_store(self.path)
        self.assertEqual(reopened.status()["completed_mask"], 0)
        self.assertEqual(reopened.status()["attempts"][0]["state"], "active")
        self.assertEqual(reopened.restore(101)["nonce"], first["nonce"])
        self.assertFalse(reopened.complete(101, first["nonce"], 0, 0)["duplicate"])

    def test_mismatched_profiles_reject_load_and_commit_without_mutation(self):
        probe_path = Path(self.tmp.name) / "probe.sqlite3"
        probe = CampaignStore(probe_path)
        probe_attempt = probe.restore(1)
        original_attempt = self.store.restore(101)
        for target, mission, nonce, reward in ((self.store, 1, probe_attempt["nonce"], 123),
                                               (probe, 101, original_attempt["nonce"], 0)):
            with self.subTest(profile=target.profile):
                before = target.path.read_bytes()
                self.assert_protocol_error("profile_mismatch", target.restore, mission)
                self.assert_protocol_error("profile_mismatch", target.complete, mission, nonce, reward, 0)
                self.assertEqual(target.path.read_bytes(), before)

    def test_nonzero_reward_unknown_mission_and_changed_retry_are_rejected(self):
        first = self.store.restore(101)
        self.assert_protocol_error("invalid_reward", self.store.complete, 101, first["nonce"], 123, 0)
        self.assert_protocol_error("mission_locked", self.store.restore, 102)
        self.assert_protocol_error("snapshot_mismatch", self.store.complete, 101, first["nonce"], 0, 50)
        self.assertEqual(self.store.status()["completed_mask"], 0)
        self.store.complete(101, first["nonce"], 0, 0)
        self.assert_protocol_error("conflicting_duplicate", self.store.complete, 101, first["nonce"], 1, 0)
        self.assertEqual(self.store.status()["gold"], 0)

    def test_legacy_probe_metadata_and_saved_balance_are_preserved_verbatim(self):
        legacy_path = Path(self.tmp.name) / "legacy.sqlite3"
        legacy = CampaignStore(legacy_path)
        first = legacy.restore(1)
        legacy.complete(1, first["nonce"], 123, 0)
        with closing(sqlite3.connect(legacy_path)) as conn:
            with conn:
                conn.execute("DELETE FROM metadata WHERE key='profile'")
        before = legacy_path.read_bytes()
        reopened = open_campaign_store(legacy_path)
        self.assertEqual(reopened.profile, "probe")
        self.assertEqual((reopened.status()["gold"], reopened.status()["completed_mask"]), (123, 1))
        self.assert_protocol_error("mission_complete", reopened.restore, 1)
        self.assert_protocol_error("profile_mismatch", reopened.restore, 101)
        self.assertEqual(legacy_path.read_bytes(), before)
        with closing(sqlite3.connect(legacy_path)) as conn:
            self.assertIsNone(conn.execute("SELECT value FROM metadata WHERE key='profile'").fetchone())
        self.assertEqual(reopened.restore(2)["gold"], 123)

    def test_unknown_profile_is_rejected_without_migration(self):
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute("UPDATE metadata SET value='future' WHERE key='profile'")
        before = self.path.read_bytes()
        self.assert_protocol_error("unknown_profile", open_campaign_store, self.path)
        self.assertEqual(self.path.read_bytes(), before)


class OriginalBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "original.sqlite3"

    def start_dispatch(self, memory, store):
        dispatch = Dispatcher(memory, BASE, store)
        self.assertEqual(dispatch.poll()["status"], "waiting_for_heartbeat")
        memory.set(6, memory.get(6) + 1)
        return dispatch

    def test_catalog_headers_allow_only_registered_ids(self):
        self.assertEqual(set(MISSIONS), {1, 2} | {m["mission_id"] for m in load_missions()})
        for mission in MISSIONS:
            self.assertEqual(validate_header(bytes(fixture(mission)), BASE)[5], mission)
        for mission in (0, 3, 100, 999, 0xFFFFFFFF):
            with self.subTest(mission=mission), self.assertRaises(BridgeError):
                validate_header(bytes(fixture(mission)), BASE)

    def test_original_restore_commit_ack_loss_and_replay_on_wire(self):
        memory = FakeMemory(fixture(101))
        dispatch = self.start_dispatch(memory, open_campaign_store(self.path))
        self.assertEqual(dispatch.poll()["status"], "restored")
        nonce = memory.data[144:160].hex()
        self.assertEqual((memory.get(33), memory.get(35), memory.get(41)), (1, 0, 0))
        memory.commit_request(nonce, delta=0)
        self.assertEqual(dispatch.poll()["status"], "committed")
        self.assertEqual((memory.get(33), memory.get(35), memory.get(40), memory.get(41)), (2, 0, 1, 1))
        restarted = self.start_dispatch(memory, open_campaign_store(self.path))
        self.assertTrue(restarted.poll()["duplicate"])
        replay_memory = FakeMemory(fixture(101))
        replay = self.start_dispatch(replay_memory, open_campaign_store(self.path))
        self.assertEqual(replay.poll()["status"], "restored")
        self.assertEqual((replay_memory.get(33), replay_memory.get(35), replay_memory.get(40), replay_memory.get(41)), (1, 0, 1, 1))
        self.assertEqual(replay_memory.data[144:160].hex(), nonce)

    def test_wrong_profile_publishes_rejection_without_saving(self):
        probe = CampaignStore(self.path)
        before = self.path.read_bytes()
        memory = FakeMemory(fixture(101))
        dispatch = self.start_dispatch(memory, probe)
        with self.assertRaisesRegex(BridgeError, "profile_mismatch"):
            dispatch.poll()
        self.assertEqual((memory.get(33), memory.get(42)), (3, 1))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(probe.status()["attempts"], [])


class OriginalPresentationTests(unittest.TestCase):
    def test_summary_distinguishes_completion_record_from_probe_balance(self):
        initial = {"profile": "original", "completed_mask": 0, "gold": 0, "revision": 0}
        self.assertIn("완료 0/57", record_summary(initial))
        complete = {**initial, "completed_mask": 1, "revision": 1}
        self.assertIn("완료 1/57", record_summary(complete))
        self.assertNotIn("골드", record_summary(complete))
        probe = {**complete, "profile": "probe", "gold": 123}
        self.assertIn("시험 기록", record_summary(probe))
        self.assertIn("골드 123", record_summary(probe))

    def test_profile_error_explains_which_record_to_open(self):
        window = ManagerWindow.__new__(ManagerWindow)
        window.connection = Mock()
        window.update_connection_status(json.dumps({"event": "error", "type": "BridgeError",
                                                   "message": "Manager rejected request (profile_mismatch)"}))
        self.assertIn("본편 기록", window.connection.set.call_args.args[0])
        self.assertIn("기존 시험 기록", window.connection.set.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
