"""PHC1 transactions use disposable SQLite files, never a player record."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import uuid

from sc1.campaign import phased_growth
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog
from sc1.manager.store import CampaignStore, GrowthChoicesPending, ProtocolError, open_campaign_store


class PhasedGrowthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sc1-phased-test-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.sqlite3"
        self.store = open_campaign_store(self.path)

    def query(self, sql, args=()):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute(sql, args).fetchall()

    def mutate(self, sql, args=()):
        with closing(sqlite3.connect(self.path)) as conn, conn:
            conn.execute(sql, args)

    def error(self, code, call, *args, **kw):
        before = self.path.read_bytes()
        with self.assertRaises((GrowthError, ProtocolError)) as caught:
            call(*args, **kw)
        self.assertEqual(caught.exception.code, code)
        self.assertEqual(self.path.read_bytes(), before)

    def load(self, phase=1, nonce=None, store=None):
        try:
            return (store or self.store).restore_growth_phase(101, 1, phase, nonce=nonce)
        except GrowthChoicesPending as pending:
            self.assertNotIsInstance(pending, ValueError)
            return pending.state

    def pick(self, state, slot=1, nonce=None, store=None):
        offer = state["offer"]
        return (store or self.store).choose_growth_phase_slot(
            offer["offer_id"], slot, offer["revision"], phase=state["requested_phase"],
            choice_kind=1 if offer["kind"] == "talent" else 2, nonce=nonce)

    def finish(self, phase=1, nonce=None):
        state = self.load(phase, nonce)
        while state.get("offer"):
            state = self.pick(state, nonce=nonce)
        return self.load(phase, nonce)

    def finish_all(self):
        result = self.finish()
        for phase in (2, 3):
            result = self.finish(phase, result["nonce"])
        return result

    def legacy_choices(self, count=5):
        state = self.store.prepare_growth()
        for _ in range(count):
            offer = state["offer"]
            state = self.store.choose_growth(offer["offer_id"], offer["candidates"][0]["id"], offer["revision"])
        return state

    def test_read_and_unprepared_choice_never_initialize(self):
        before = self.path.read_bytes()
        self.store.status(); self.store.growth_status()
        self.assertEqual(before, self.path.read_bytes())
        self.error("growth_not_prepared", self.store.choose_growth_phase_slot,
                   str(uuid.uuid4()), 1, 0, choice_kind=1, phase=1)
        self.error("growth_not_prepared", self.store.restore_growth_phase, 101, 1, 2, nonce="1" * 32)
        self.assertFalse(self.query("SELECT name FROM sqlite_master WHERE name LIKE 'growth_%'"))

    def test_initial_pair_only_is_issued_and_restart_is_identical(self):
        state = self.load()
        self.assertEqual(state["pending"], {"talent": 3, "curse": 3})
        self.assertEqual(state["phase_pending"], {"talent": 1, "curse": 1})
        self.assertEqual((state["requested_phase"], state["completed_phase"], state["total_phases"]), (1, 0, 3))
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_offers WHERE candidates_json IS NOT NULL"), [(1,)])
        self.assertEqual(self.store.status()["attempts"], [])
        before = self.path.read_bytes()
        self.assertEqual(self.load(store=open_campaign_store(self.path)), state)
        self.assertEqual(before, self.path.read_bytes())

    def test_three_pairs_cumulative_immutable_snapshots_one_nonce(self):
        expected_ids, expected_curses, snapshots = [], {}, []
        nonce = None
        for phase in (1, 2, 3):
            state = self.load(phase, nonce)
            self.assertEqual(state["offer"]["kind"], "talent")
            self.assertFalse(set(expected_ids) & {i["id"] for i in state["offer"]["candidates"]})
            expected_ids.append(state["offer"]["candidates"][0]["id"])
            state = self.pick(state, nonce=nonce)
            self.assertEqual(state["offer"]["kind"], "curse")
            curse = state["offer"]["candidates"][0]["id"]
            expected_curses[curse] = expected_curses.get(curse, 0) + 1
            self.assertEqual(state["completed_phase"], phase - 1)
            if snapshots:
                self.assertEqual(state["growth_words"], snapshots[-1])
            else:
                self.assertEqual(state["growth_words"], [1] + [0] * 20)
            state = self.pick(state, nonce=nonce)
            self.assertEqual(state["completed_phase"], phase)
            self.assertIsNone(state["offer"])
            result = self.load(phase, nonce)
            if nonce:
                self.assertEqual(result["nonce"], nonce)
            nonce = result["nonce"]
            words = encode_growth(load_catalog(), expected_ids, expected_curses)
            self.assertEqual(result["growth_words"], words)
            snapshots.append(words)
            self.assertEqual(self.load()["growth_words"], words)
        rows = self.query("SELECT words_json,nonce FROM growth_phase_snapshots ORDER BY phase")
        self.assertEqual([json.loads(r[0]) for r in rows], snapshots)
        self.assertEqual({r[1] for r in rows}, {nonce})
        self.assertEqual(json.loads(self.query("SELECT words_json FROM growth_snapshots")[0][0]), snapshots[0])
        self.assertEqual(self.store.status()["revision"], 0)
        self.assertEqual(self.store.growth_status()["revision"], 6)

    def test_future_stage_and_wrong_nonce_cannot_mutate_or_issue(self):
        self.load()
        self.error("phase_nonce_mismatch", self.store.restore_growth_phase, 101, 1, 2, nonce="1" * 32)
        first = self.finish()
        self.error("phase_out_of_order", self.store.restore_growth_phase, 101, 1, 3, nonce=first["nonce"])
        self.error("phase_nonce_mismatch", self.store.restore_growth_phase, 101, 1, 2, nonce="2" * 32)
        future = self.query("SELECT offer_id FROM growth_phase_offers WHERE phase=2 AND kind='talent'")[0][0]
        self.error("offer_not_ready", self.store.choose_growth_phase_slot, future, 1, 2,
                   phase=2, nonce=first["nonce"], choice_kind=1)
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_offers WHERE candidates_json IS NOT NULL"), [(2,)])

    def test_phase_types_and_nonce_validation_are_strict(self):
        for phase in (0, 4, True, "1", None):
            self.error("invalid_phase", self.store.restore_growth_phase, 101, 1, phase)
        self.error("phase_nonce_mismatch", self.store.restore_growth_phase, 101, 1, 1, nonce="0" * 32)
        for nonce in (None, True, "ABC", "A" * 32, "1" * 31):
            self.error("phase_nonce_mismatch", self.store.restore_growth_phase, 101, 1, 2, nonce=nonce)

    def test_cas_slot_kind_phase_validation_and_retry(self):
        offer = self.load()["offer"]
        defaults = dict(offer_id=offer["offer_id"], choice_slot=1, expected_revision=0, phase=1, choice_kind=1)
        cases = [("invalid_choice_slot", {"choice_slot": value}) for value in (0, 5, True, "1")]
        cases += [("invalid_choice_kind", {"choice_kind": value}) for value in (0, 3, True)]
        cases += [("invalid_choice_revision", {"expected_revision": value}) for value in (-1, True, 2**32)]
        cases += [("invalid_offer_id", {"offer_id": "bad"}), ("unknown_offer", {"offer_id": str(uuid.uuid4())}),
                  ("choice_kind_mismatch", {"choice_kind": 2}), ("stale_choice", {"expected_revision": 8})]
        for code, changes in cases:
            with self.subTest(code=code, changes=changes):
                self.error(code, self.store.choose_growth_phase_slot, **{**defaults, **changes})
        state = self.store.choose_growth_phase_slot(**defaults)
        before = self.path.read_bytes()
        self.assertTrue(open_campaign_store(self.path).choose_growth_phase_slot(**defaults)["duplicate"])
        self.assertEqual(before, self.path.read_bytes())
        self.error("conflicting_choice", self.store.choose_growth_phase_slot, **{**defaults, "choice_slot": 2})
        curse = state["offer"]
        self.error("invalid_choice_slot", self.store.choose_growth_phase_slot, curse["offer_id"], 4, curse["revision"], choice_kind=2, phase=1)

    def test_concurrent_choice_and_result_are_exactly_once(self):
        state = self.load()
        with ThreadPoolExecutor(max_workers=4) as pool:
            values = list(pool.map(lambda _: self.pick(state, store=open_campaign_store(self.path)), range(6)))
        self.assertEqual(sum(not value["duplicate"] for value in values), 1)
        final = self.finish_all()
        with ThreadPoolExecutor(max_workers=4) as pool:
            values = list(pool.map(lambda _: open_campaign_store(self.path).complete(101, final["nonce"], 0, 0), range(6)))
        self.assertEqual(sum(not value["duplicate"] for value in values), 1)
        self.assertEqual(self.query("SELECT talent_choices,curse_choices FROM growth_rewards"), [(3, 3)])
        self.assertEqual(self.store.growth_status()["upcoming"], {"talent": 3, "curse": 3})

    def test_selected_slot_retries_after_later_phase_and_completion_are_read_only(self):
        state = self.load(); first_offer = state["offer"]
        self.pick(state)
        final = self.finish_all()
        self.store.complete(101, final["nonce"], 0, 0)
        before = self.path.read_bytes()
        result = open_campaign_store(self.path).choose_growth_phase_slot(
            first_offer["offer_id"], 1, first_offer["revision"], phase=1, choice_kind=1)
        self.assertTrue(result["duplicate"])
        self.assertEqual(result["completed_phase"], 3)
        self.assertEqual(result["growth_words"], final["growth_words"])
        self.assertEqual(before, self.path.read_bytes())
        self.error("phase_mismatch", self.store.choose_growth_phase_slot,
                   first_offer["offer_id"], 1, first_offer["revision"],
                   phase=2, choice_kind=1, nonce=final["nonce"])

    def test_status_during_future_half_pair_is_read_only(self):
        first = self.finish()
        state = self.load(2, first["nonce"])
        self.pick(state, nonce=first["nonce"])
        before = self.path.read_bytes()
        direct = self.store.growth_status()
        combined = self.store.status()["growth_selection"]
        self.assertEqual(direct, combined)
        self.assertEqual((direct["requested_phase"], direct["completed_phase"]), (2, 1))
        self.assertEqual(direct["phase_pending"], {"talent": 0, "curse": 1})
        self.assertEqual(direct["growth_words"], first["growth_words"])
        self.assertEqual(before, self.path.read_bytes())

    def test_resume_keeps_last_complete_pair_and_pending_uuid(self):
        first = self.finish()
        state = self.load(2, first["nonce"])
        state = self.pick(state, nonce=first["nonce"])
        before = self.path.read_bytes()
        fresh = self.load(store=open_campaign_store(self.path))
        self.assertEqual(fresh["completed_phase"], 1)
        self.assertEqual(fresh["growth_words"], first["growth_words"])
        self.assertEqual(self.load(2, first["nonce"])["offer"], state["offer"])
        self.assertEqual(before, self.path.read_bytes())

    def test_early_commit_is_rejected_then_next_mission_three_plus_three(self):
        first = self.finish()
        self.error("phase_incomplete", self.store.complete, 101, first["nonce"], 0, 0)
        self.finish(2, first["nonce"])
        self.error("phase_incomplete", self.store.complete, 101, first["nonce"], 0, 0)
        final = self.finish(3, first["nonce"])
        self.store.complete(101, final["nonce"], 0, 0)
        self.assertEqual(self.store.growth_status()["upcoming"], {"talent": 3, "curse": 3})
        self.assertIsNone(self.store.growth_status()["offer"])
        replay = self.load()
        self.assertTrue(replay["already_completed"])
        self.assertEqual(replay["completed_phase"], 3)
        self.assertEqual(replay["growth_words"], final["growth_words"])
        before = self.path.read_bytes()
        self.assertTrue(self.store.complete(101, final["nonce"], 0, 0)["duplicate"])
        self.assertEqual(before, self.path.read_bytes())
        with self.assertRaises(GrowthChoicesPending) as pending:
            self.store.restore_growth_phase(102, 1, 1)
        self.assertEqual(pending.exception.state["mission"], 102)
        self.assertEqual(pending.exception.state["pending"], {"talent":3,"curse":3})

    def test_selected_history_and_frozen_snapshot_are_immutable(self):
        first = self.finish()
        history = self.query("SELECT offer_id,selected_id,selected_revision,selected_at FROM growth_offers WHERE selected_id IS NOT NULL")
        frozen = self.query("SELECT * FROM growth_phase_snapshots")
        self.finish(2, first["nonce"]); self.finish(3, first["nonce"])
        self.assertEqual(self.query("SELECT * FROM growth_phase_snapshots WHERE phase=1"), frozen)
        self.assertEqual(self.query("SELECT offer_id,selected_id,selected_revision,selected_at FROM growth_offers WHERE selected_id IS NOT NULL ORDER BY sequence LIMIT 2"), history)

    def test_last_choice_snapshot_failure_rolls_back_selection_and_attempt(self):
        state = self.pick(self.load())
        before = self.path.read_bytes()
        original = phased_growth._freeze
        def failure(*args, **kwargs):
            original(*args, **kwargs)
            raise sqlite3.OperationalError("injected disk failure")
        with patch.object(phased_growth, "_freeze", side_effect=failure), self.assertRaises(sqlite3.OperationalError):
            self.pick(state)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(self.store.status()["attempts"], [])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_phase_snapshots"), [(0,)])

    def test_commit_and_three_plus_three_reward_roll_back_together(self):
        final = self.finish_all()
        before = self.path.read_bytes()
        with patch.object(self.store, "_commit_result", side_effect=sqlite3.OperationalError("disk failure")), self.assertRaises(sqlite3.OperationalError):
            self.store.complete(101, final["nonce"], 0, 0)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(0,)])
        self.assertEqual(self.store.status()["attempts"][0]["state"], "active")

    def test_unfinished_c1_candidates_history_and_baseline_are_preserved(self):
        old = self.legacy_choices(1)
        old_offer = old["offer"]
        old_history = self.query("SELECT offer_id,selected_id,selected_revision,selected_at FROM growth_offers WHERE selected_id IS NOT NULL")
        state = self.load()
        self.assertEqual(state["offer"]["kind"], "curse")
        self.pick(state)
        first = self.load()
        state = self.load(2, first["nonce"])
        self.assertEqual(state["offer"]["offer_id"], old_offer["offer_id"])
        self.assertEqual(state["offer"]["candidates"], old_offer["candidates"])
        self.assertEqual(state["offer"]["revision"], 2)
        self.assertEqual(self.query("SELECT offer_id,selected_id,selected_revision,selected_at FROM growth_offers WHERE selected_revision=1"), old_history)

    def test_c1_future_selected_talents_do_not_apply_before_their_pair(self):
        old = self.legacy_choices(3)
        history = copy.deepcopy(old["history"])
        state = self.load()
        self.assertEqual(state["growth_words"], [1] + [0] * 20)
        curse = state["offer"]["candidates"][0]["id"]
        self.pick(state)
        first = self.load()
        expected = encode_growth(load_catalog(), [history[0]["selected_id"]], {curse: 1})
        self.assertEqual(first["growth_words"], expected)
        self.assertEqual(len(self.store.growth_status()["talents"]), 3)
        self.assertEqual(self.store.growth_status()["history"][:3], history)
        state = self.load(2, first["nonce"])
        self.assertEqual(state["offer"]["kind"], "curse")
        second_curse = state["offer"]["candidates"][0]["id"]
        self.pick(state, nonce=first["nonce"])
        second = self.load()
        self.assertEqual(second["completed_phase"], 2)
        self.assertEqual(second["growth_words"], encode_growth(load_catalog(), [h["selected_id"] for h in history[:2]], dict(Counter([curse, second_curse]))))

    def test_c1_complete_pairs_restore_highest_without_inventing_extra_choices(self):
        old = self.legacy_choices(5)
        old_rows = self.query("SELECT * FROM growth_offers")
        loaded = self.load()
        self.assertEqual(loaded["completed_phase"], 2)
        self.assertEqual(self.query("SELECT * FROM growth_offers WHERE sequence<=5"), old_rows)
        self.assertEqual(self.query("SELECT phase FROM growth_phase_snapshots ORDER BY phase"), [(1,), (2,)])
        self.assertEqual(loaded["growth_words"], encode_growth(load_catalog(), [h["selected_id"] for h in old["history"][:2]], dict(Counter(h["selected_id"] for h in old["history"] if h["kind"] == "curse"))))
        state = self.load(3, loaded["nonce"])
        self.assertEqual(state["offer"]["kind"], "curse")
        self.pick(state, nonce=loaded["nonce"])
        self.assertEqual(self.load()["completed_phase"], 3)

    def test_frozen_c1_loadout_is_legacy_complete_without_new_selection(self):
        self.legacy_choices()
        old = self.store.restore_growth(101)
        frozen = self.query("SELECT * FROM growth_snapshots")
        offers = self.query("SELECT * FROM growth_offers")
        restored = self.load()
        self.assertEqual(restored["growth_words"], old["growth_words"])
        self.assertEqual(restored["nonce"], old["nonce"])
        self.assertEqual(restored["completed_phase"], 3)
        self.assertEqual(self.query("SELECT * FROM growth_snapshots"), frozen)
        self.assertEqual(self.query("SELECT * FROM growth_offers"), offers)
        self.store.complete(101, old["nonce"], 0, 0)
        self.assertEqual(self.store.growth_status()["upcoming"], {"talent": 3, "curse": 3})

    def test_old_completed_receipt_and_empty_loadout_remain_unchanged(self):
        old = self.store.restore(101)
        self.store.complete(101, old["nonce"], 0, 0)
        receipt = self.query("SELECT * FROM results")
        loaded = self.load()
        self.assertEqual((loaded["nonce"], loaded["completed_phase"]), (old["nonce"], 3))
        self.assertEqual(loaded["growth_words"], [1] + [0] * 20)
        self.assertEqual(self.query("SELECT * FROM results"), receipt)
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_offers"), [(0,)])
        self.assertTrue(self.store.complete(101, old["nonce"], 0, 0)["duplicate"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(0,)])

    def test_old_completed_c1_keeps_its_original_two_plus_two_reward(self):
        self.legacy_choices()
        old = self.store.restore_growth(101)
        self.store.complete(101, old["nonce"], 0, 0)
        offers = self.query("SELECT * FROM growth_offers")
        receipt = self.query("SELECT * FROM results")
        loaded = self.load()
        self.assertEqual(loaded["growth_words"], old["growth_words"])
        self.assertEqual(loaded["completed_phase"], 3)
        self.assertEqual(self.query("SELECT * FROM growth_offers"), offers)
        self.assertEqual(self.query("SELECT * FROM results"), receipt)
        self.assertEqual(self.store.growth_status()["upcoming"], {"talent": 2, "curse": 2})
        self.assertTrue(self.store.complete(101, old["nonce"], 0, 0)["duplicate"])
        self.assertEqual(self.query("SELECT talent_choices,curse_choices FROM growth_rewards"), [(2, 2)])

    def test_existing_attempt_identity_and_revision_are_preserved(self):
        old = self.store.restore(101)
        restored = self.finish_all()
        self.assertEqual((restored["nonce"], restored["revision"]), (old["nonce"], 0))
        self.assertEqual(self.store.status()["attempts"][0]["start_revision"], 0)

    def test_catalog_edits_do_not_reroll_offers_or_change_phase_bits(self):
        path = Path(self.tmp.name) / "catalog.json"
        path.write_text(json.dumps(load_catalog()), encoding="utf-8")
        self.store = open_campaign_store(self.path, runtime_catalog_path=path)
        state = self.load()
        path.write_text("invalid JSON", encoding="utf-8")
        self.assertEqual(self.load(), state)
        final = self.finish_all()
        status = self.store.growth_status()
        self.assertEqual(final["growth_words"], encode_growth(load_catalog(), [i["id"] for i in status["talents"]], {i["id"]: i["stacks"] for i in status["curses"]}))

    def test_bad_catalog_and_later_pool_shortage_roll_back(self):
        path = Path(self.tmp.name) / "catalog.json"
        path.write_text("invalid JSON", encoding="utf-8")
        self.store = open_campaign_store(self.path, runtime_catalog_path=path)
        self.error("catalog_unavailable", self.store.restore_growth_phase, 101, 1, 1)
        catalog = load_catalog(); catalog["talents"] = catalog["talents"][:4]
        catalog['talent_pool_revision'] = 1  # Deliberately exercise a tiny legacy/custom pool.
        path.write_text(json.dumps(catalog), encoding="utf-8")
        first = self.finish()
        self.error("choice_pool_unavailable", self.store.restore_growth_phase, 101, 1, 2, nonce=first["nonce"])
        self.assertEqual(self.load()["growth_words"], first["growth_words"])

    def test_invalid_persisted_candidates_and_snapshots_are_rejected(self):
        state = self.load()
        self.mutate("UPDATE growth_offers SET candidates_json='[]' WHERE offer_id=?", (state["offer"]["offer_id"],))
        self.error("invalid_growth", self.pick, state)
        # This separate fixture intentionally damages only its own snapshot.
        other_path = Path(self.tmp.name) / "damaged.sqlite3"
        other = open_campaign_store(other_path)
        state = self.load(store=other)
        state = self.pick(state, store=other); self.pick(state, store=other)
        with closing(sqlite3.connect(other_path)) as conn, conn:
            conn.execute("UPDATE growth_phase_snapshots SET words_json='[]'")
        before = other_path.read_bytes()
        with self.assertRaises(GrowthError):
            other.restore_growth_phase(101, 1, 1)
        self.assertEqual(before, other_path.read_bytes())

    def test_c1_calls_cannot_bypass_phased_checkpoint(self):
        state = self.load(); offer = state["offer"]
        self.error("phased_protocol_required", self.store.prepare_growth)
        self.error("phased_protocol_required", self.store.restore_growth, 101)
        self.error("phased_protocol_required", self.store.choose_growth, offer["offer_id"], offer["candidates"][0]["id"], 0)
        self.error("phased_protocol_required", self.store.choose_growth_slot, offer["offer_id"], 1, 0, choice_kind=1)

    def test_probe_profile_never_migrates(self):
        path = Path(self.tmp.name) / "probe.sqlite3"
        probe = CampaignStore(path)
        before = path.read_bytes()
        with self.assertRaises(ProtocolError):
            probe.restore_growth_phase(101, 1, 1)
        self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main()
