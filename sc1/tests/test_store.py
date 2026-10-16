from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from sc1.manager.store import CampaignStore, ProtocolError


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "campaign.sqlite3"
        self.store = CampaignStore(self.db)

    def test_persist_restore_and_duplicate_after_restart(self):
        run = self.store.restore(1)
        first = self.store.complete(1, run["nonce"], 123, 0)
        restarted = CampaignStore(self.db)
        duplicate = restarted.complete(1, run["nonce"], 123, 0)
        self.assertTrue(duplicate["duplicate"])
        self.assertEqual(first["revision"], duplicate["revision"])
        restored = restarted.restore(2)
        self.assertEqual(restored["gold"], 123)
        final = restarted.complete(2, restored["nonce"], 0, 123)
        self.assertEqual((final["gold"], final["revision"], final["completed_mask"]), (123, 2, 3))

    def test_separate_manager_processes_keep_gold(self):
        root = Path(__file__).resolve().parents[2]
        def cli(*args):
            raw = subprocess.check_output([sys.executable, "-m", "sc1.manager", "--db", str(self.db), *args], cwd=root)
            return json.loads(raw)
        first = cli("restore", "--mission", "1")
        cli("complete", "--mission", "1", "--nonce", first["nonce"], "--gold-delta", "123", "--observed-gold", "0")
        self.assertEqual(cli("restore", "--mission", "2")["gold"], 123)

    def test_retry_unfinished_map_keeps_nonce(self):
        first = self.store.restore(1)
        self.assertEqual(first["nonce"], CampaignStore(self.db).restore(1)["nonce"])

    def test_concurrent_result_retries_award_once(self):
        run = self.store.restore(1)
        def commit(_):
            return CampaignStore(self.db).complete(1, run["nonce"], 123, 0)
        with ThreadPoolExecutor(max_workers=4) as pool:
            replies = list(pool.map(commit, range(8)))
        self.assertEqual(sum(not r["duplicate"] for r in replies), 1)
        self.assertEqual(self.store.status()["gold"], 123)
        self.assertEqual(self.store.status()["revision"], 1)

    def test_protocol_map_nonce_and_snapshot_rejected(self):
        run = self.store.restore(1)
        cases = [
            (dict(mission=1, nonce=run["nonce"], gold_delta=123, observed_gold=0, protocol_version=2), "protocol_version"),
            (dict(mission=2, nonce=run["nonce"], gold_delta=0, observed_gold=0), "attempt_mismatch"),
            (dict(mission=1, nonce="0"*32, gold_delta=123, observed_gold=0), "unknown_attempt"),
            (dict(mission=1, nonce=run["nonce"], gold_delta=124, observed_gold=0), "invalid_reward"),
            (dict(mission=1, nonce=run["nonce"], gold_delta=123, observed_gold=12), "snapshot_mismatch"),
        ]
        for kwargs, code in cases:
            with self.subTest(code=code), self.assertRaises(ProtocolError) as cm:
                self.store.complete(**kwargs)
            self.assertEqual(cm.exception.code, code)
        self.assertEqual(self.store.status()["gold"], 0)

    def test_duplicate_cannot_change_payload(self):
        run = self.store.restore(1)
        self.store.complete(1, run["nonce"], 123, 0)
        with self.assertRaises(ProtocolError) as cm:
            self.store.complete(1, run["nonce"], 123, 1)
        self.assertEqual(cm.exception.code, "conflicting_duplicate")

    def test_failed_disk_commit_rolls_back_and_never_returns_ack(self):
        run = self.store.restore(1)
        def disk_full(_):
            raise sqlite3.OperationalError("injected disk full at commit")
        self.store._commit_result = disk_full
        with self.assertRaises(sqlite3.OperationalError):
            self.store.complete(1, run["nonce"], 123, 0)
        reopened = CampaignStore(self.db)
        self.assertEqual(reopened.status()["gold"], 0)
        self.assertEqual(reopened.status()["attempts"][0]["state"], "active")
        self.assertFalse(reopened.complete(1, run["nonce"], 123, 0)["duplicate"])

    def test_wrong_schema_is_preserved_and_rejected(self):
        with closing(sqlite3.connect(self.db)) as conn:
            with conn:
                conn.execute("UPDATE metadata SET value='999' WHERE key='schema_version'")
        before = self.db.read_bytes()
        with self.assertRaises(ProtocolError) as cm:
            CampaignStore(self.db)
        self.assertEqual(cm.exception.code, "schema_version")
        self.assertEqual(before, self.db.read_bytes())

    def test_invalid_values_and_locked_completed_maps(self):
        for mission, version in [(True, 1), (1, True), (3, 1)]:
            with self.assertRaises(ProtocolError):
                self.store.restore(mission, version)
        with self.assertRaises(ProtocolError):
            self.store.restore(2)
        first = self.store.restore(1)
        self.store.complete(1, first["nonce"], 123, 0)
        with self.assertRaises(ProtocolError) as cm:
            self.store.restore(1)
        self.assertEqual(cm.exception.code, "mission_complete")


if __name__ == "__main__":
    unittest.main()
