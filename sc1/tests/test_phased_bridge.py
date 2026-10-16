"""PHC1 checkpoints through real durable SQLite and owned fake wire memory."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from sc1.bridge.protocol import BridgeError, Dispatcher, UnstableMailbox, read_request, response_payload
from sc1.manager.store import CampaignStore
from sc1.tests.test_bridge import BASE
from sc1.tests.test_growth_bridge import GrowthMemory


class PhaseMemory(GrowthMemory):
    def __init__(self):
        super().__init__()
        self.set(20, 0x43484331); self.set(21, 1)
        self.set(29, 0x50484331); self.set(30, 1); self.set(31, 1)

    def request(self, operation, *, stage=None, slot=0):
        seq = self.get(8)
        token = [self.get(51+i) for i in range(4)] if operation == 3 else [0]*4
        revision, kind = (self.get(45), self.get(44)) if operation == 3 else (0, 0)
        self.set(8, seq+1)
        self.set(7, 3 if operation == 2 else 1)
        self.set(9, operation)
        if stage is not None: self.set(31, stage)
        self.set(22, slot)
        for i, word in enumerate(token): self.set(23+i, word)
        self.set(27, revision); self.set(28, kind)
        self.set(8, seq+2); self.set(6, self.get(6)+1)

    def resume(self):
        for i in range(4): self.set(10+i, self.get(36+i))
        self.set(15, self.get(35)); self.set(19, 1)
        seq = self.get(8)
        self.set(8, seq+1); self.set(7, 2); self.set(9, 0)
        for i in range(22, 29): self.set(i, 0)
        self.set(8, seq+2); self.set(6, self.get(6)+1)


class PhaseWireTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="sc1-phase-wire-")
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)/"campaign.sqlite3"
        self.store = CampaignStore(self.path, new_profile="original")
        self.memory = PhaseMemory()
        self.dispatch = Dispatcher(self.memory, BASE, self.store, clock=lambda: 0)
        self.assertEqual(self.dispatch.poll()["status"], "waiting_for_heartbeat")
        self.memory.set(6, 1)

    def complete_pair(self, stage):
        m = self.memory
        self.assertEqual(self.dispatch.poll()["status"], "choice_offered")
        self.assertEqual((m.get(44), m.get(46), m.get(58), m.get(59), m.get(60), m.get(61), m.get(62), m.get(63)),
                         (1, 4, 0x50484331, 1, stage, stage-1, 3, 0))
        self.assertEqual((m.get(55), m.get(56)), (1, 1))
        m.request(3, slot=1)
        self.assertEqual(self.dispatch.poll()["status"], "choice_offered")
        self.assertEqual((m.get(44), m.get(46), m.get(60)), (2, 3, stage))
        self.assertEqual((m.get(55), m.get(56)), (0, 1))
        m.request(3, slot=1)
        self.assertEqual(self.dispatch.poll()["status"], "restored")
        self.assertEqual((m.get(33), m.get(42)), (1, 0x50480000 | stage << 8 | stage))
        self.assertEqual(sum(m.get(i).bit_count() for i in range(44, 60)), stage)
        self.assertEqual(sum(m.data[240:256]), stage)
        m.resume()

    def test_one_pair_per_checkpoint_then_final_commit_and_three_next_mission_rights(self):
        m = self.memory
        self.complete_pair(1)
        nonce = bytes(m.data[40:56])
        before = self.path.read_bytes()
        self.assertEqual(self.dispatch.poll()["status"], "running")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIsNone(self.store.growth_status()["offer"])
        for stage in (2, 3):
            m.request(4, stage=stage)
            self.complete_pair(stage)
            self.assertEqual(bytes(m.data[40:56]), nonce)
        m.request(2)
        self.assertEqual(self.dispatch.poll()["status"], "committed")
        self.assertEqual((m.get(33), m.get(42)), (2, 0))
        self.assertEqual(self.store.growth_status()["upcoming"], {"talent": 3, "curse": 3})
        self.assertEqual(len(self.store.growth_status()["history"]), 6)
        self.assertTrue(all(BASE+128 <= addr and addr+len(data) <= BASE+256 for addr, data in m.writes))

    def test_midmission_lost_snapshot_ack_resends_identical_nonce_and_growth(self):
        m = self.memory
        self.complete_pair(1)
        m.request(4, stage=2)
        self.complete_pair(2)
        snapshot = bytes(m.data[144:256])
        m.request(4, stage=2)
        self.dispatch = Dispatcher(m, BASE, CampaignStore(self.path), clock=lambda: 0)
        self.dispatch.poll(); m.set(6, m.get(6)+1)
        self.assertEqual(self.dispatch.poll()["status"], "restored")
        self.assertEqual(bytes(m.data[144:256]), snapshot)
        self.assertEqual(len(self.store.growth_status()["history"]), 4)

    def test_fresh_restart_restores_highest_completed_pair_without_issuing_future_offer(self):
        self.complete_pair(1)
        self.memory.request(4, stage=2); self.complete_pair(2)
        expected = bytes(self.memory.data[144:256])
        restart = PhaseMemory(); d = Dispatcher(restart, BASE, CampaignStore(self.path), clock=lambda: 0)
        d.poll(); restart.set(6, 1)
        self.assertEqual(d.poll()["status"], "restored")
        self.assertEqual(restart.get(42), 0x50480201)
        self.assertEqual(bytes(restart.data[144:168]), expected[:24])
        self.assertEqual(bytes(restart.data[172:256]), expected[28:])
        self.assertIsNone(self.store.growth_status()["offer"])

    def test_later_choice_cannot_change_issued_attempt(self):
        self.complete_pair(1)
        self.memory.request(4, stage=2); self.dispatch.poll()
        self.memory.request(3, slot=1)
        self.memory.set(10, self.memory.get(10) ^ 1)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(BridgeError, "phase_nonce_mismatch"):
            self.dispatch.poll()
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(len(self.store.growth_status()["history"]), 2)

    def test_phase_change_while_saving_never_publishes_for_old_checkpoint(self):
        self.dispatch.poll(); self.memory.request(3, slot=1)
        actual = self.store.choose_growth_phase_slot
        before = bytes(self.memory.data[128:])
        def changed(*args, **kwargs):
            result = actual(*args, **kwargs)
            self.memory.set(31, 2)
            return result
        with patch.object(self.store, "choose_growth_phase_slot", side_effect=changed):
            with self.assertRaises(UnstableMailbox): self.dispatch.poll()
        self.assertEqual(bytes(self.memory.data[128:]), before)
        self.assertEqual(len(self.store.growth_status()["history"]), 1)

    def test_missing_capability_bad_stage_or_early_commit_has_no_store_side_effect(self):
        for field, value in ((29, 0), (29, 0x12345678), (30, 2), (31, 0), (31, 4)):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/"record.sqlite3"; store = CampaignStore(path, new_profile="original")
                m = PhaseMemory(); d = Dispatcher(m, BASE, store, clock=lambda: 0)
                d.poll(); m.set(6, 1); m.set(field, value)
                before = path.read_bytes()
                with self.assertRaises(BridgeError): d.poll()
                self.assertEqual(path.read_bytes(), before)
                self.assertEqual(m.writes, [])
        self.complete_pair(1)
        self.memory.request(2)
        before = self.path.read_bytes()
        with self.assertRaisesRegex(BridgeError, "final growth checkpoint"): self.dispatch.poll()
        self.assertEqual(self.path.read_bytes(), before)

    def test_server_snapshot_cannot_swap_nonce_or_checkpoint(self):
        self.complete_pair(1); self.memory.request(4, stage=2)
        # A valid response fixture for the request, without preparing or
        # selecting the next phase in any user/store file.
        request = read_request(self.memory, BASE)
        result = {"nonce": request.nonce, "gold": 0, "revision": 0, "completed_mask": 0,
                  "growth_words": [1]+[0]*20, "requested_phase": 2, "completed_phase": 2, "total_phases": 3}
        self.assertEqual(struct.unpack_from("<I", response_payload(request, result, 1), 36)[0], 0x50480202)
        for field, value in (("nonce", "12"*16), ("requested_phase", 3), ("completed_phase", 1)):
            with self.subTest(field=field), self.assertRaises(BridgeError):
                response_payload(request, {**result, field: value}, 1)


if __name__ == "__main__": unittest.main()
