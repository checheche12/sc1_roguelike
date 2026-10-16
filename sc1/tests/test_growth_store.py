"""Growth transactions against real temporary SQLite files, never player saves."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import copy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import uuid

from sc1.campaign import growth
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog, validate_catalog
from sc1.manager.store import CampaignStore, GrowthChoicesPending, ProtocolError, open_campaign_store
from sc1.manager.ui import growth_summary


class GrowthStoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sc1-growth-test-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "original.sqlite3"
        self.store = open_campaign_store(self.path)

    def query(self, statement, args=()):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute(statement, args).fetchall()

    def mutate(self, statement, args=()):
        with closing(sqlite3.connect(self.path)) as conn:
            with conn:
                conn.execute(statement, args)

    def catalog_store(self, catalog):
        catalog_path = Path(self.tmp.name) / "runtime.json"
        catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
        return open_campaign_store(self.path, runtime_catalog_path=catalog_path), catalog_path

    def assert_error(self, code, operation, *args, **kwargs):
        with self.assertRaises((GrowthError, ProtocolError)) as caught:
            operation(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def choose_first(self, state, store=None, candidate_id=None):
        offer = state["offer"]
        return (store or self.store).choose_growth(offer["offer_id"], candidate_id or offer["candidates"][0]["id"], offer["revision"])

    def finish_choices(self, store=None):
        store = store or self.store
        state = store.prepare_growth()
        while state["offer"]:
            state = self.choose_first(state, store)
        return state


class GrowthStoreTests(GrowthStoreTestCase):
    def test_reads_and_unprepared_click_do_not_migrate_old_record(self):
        before = self.path.read_bytes()
        self.assertEqual(self.store.growth_status()["state"], "not_started")
        self.assertEqual(self.store.status()["growth_selection"]["state"], "not_started")
        self.assert_error("growth_not_prepared", self.store.choose_growth, "missing", "missing", 0)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(any(name.startswith("growth_") for (name,) in self.query("SELECT name FROM sqlite_master WHERE type='table'")))

    def test_restore_wait_persists_offer_without_creating_attempt(self):
        self.assertNotIsInstance(GrowthChoicesPending(), ValueError)
        with self.assertRaises(GrowthChoicesPending) as caught:
            self.store.restore_growth(101)
        saved = caught.exception.state
        self.assertEqual(saved["pending"], {"talent": 3, "curse": 2})
        self.assertEqual(len(saved["offer"]["candidates"]), 4)
        before = self.path.read_bytes()
        for _ in range(3):
            with self.assertRaises(GrowthChoicesPending) as retry:
                open_campaign_store(self.path).restore_growth(101)
            self.assertEqual(retry.exception.state, saved)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.store.status()["attempts"], [])

    def test_offer_survives_separate_process_restart(self):
        expected = self.store.prepare_growth()
        command = "import json,sys; from sc1.manager.store import open_campaign_store; print(json.dumps(open_campaign_store(sys.argv[1]).prepare_growth()))"
        actual = json.loads(subprocess.check_output([sys.executable, "-c", command, str(self.path)], cwd=Path(__file__).resolve().parents[2]))
        self.assertEqual(actual, expected)

    def test_three_unique_talents_and_two_stackable_common_curses(self):
        catalog = load_catalog()
        catalog["curses"] = catalog["curses"][:3]
        self.store, _ = self.catalog_store(catalog)
        state = self.store.prepare_growth()
        chosen_talents = []
        for _ in range(3):
            offer = state["offer"]
            self.assertEqual(offer["kind"], "talent")
            candidates = offer["candidates"]
            ids = [item["id"] for item in candidates]
            self.assertEqual(len(set(ids)), 4)
            self.assertFalse(set(ids) & set(chosen_talents))
            self.assertTrue(all(item["implemented"] and 101 in item["missions"] and item["race"] in ("terran", "shared") for item in candidates))
            chosen_talents.append(ids[0])
            state = self.choose_first(state)
        first_curses = state["offer"]["candidates"]
        self.assertEqual(len(first_curses), 3)
        self.assertEqual({item["rarity"] for item in first_curses}, {"common"})
        curse_id = first_curses[0]["id"]
        state = self.choose_first(state)
        self.assertEqual(state["offer"]["candidates"], first_curses)
        state = self.choose_first(state, candidate_id=curse_id)
        self.assertEqual((state["state"], state["revision"]), ("ready", 5))
        self.assertEqual(len(state["talents"]), 3)
        self.assertEqual([(item["id"], item["stacks"]) for item in state["curses"]], [(curse_id, 2)])
        self.assertEqual(len(state["history"]), 5)
        self.assertEqual(self.store.status()["revision"], 0)

    def test_choice_cas_invalid_candidate_and_conflicting_retry(self):
        state = self.store.prepare_growth()
        offer = state["offer"]
        args = (offer["offer_id"], offer["candidates"][0]["id"], offer["revision"])
        before = self.path.read_bytes()
        self.assert_error("stale_choice", self.store.choose_growth, args[0], args[1], 9)
        self.assert_error("invalid_choice", self.store.choose_growth, args[0], "not-a-candidate", args[2])
        self.assertEqual(self.path.read_bytes(), before)
        self.store.choose_growth(*args)
        before = self.path.read_bytes()
        self.assertTrue(open_campaign_store(self.path).choose_growth(*args)["duplicate"])
        self.assert_error("conflicting_choice", self.store.choose_growth, args[0], offer["candidates"][1]["id"], args[2])
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.store.growth_status()["revision"], 1)

    def test_concurrent_identical_click_records_one_choice(self):
        offer = self.store.prepare_growth()["offer"]
        args = (offer["offer_id"], offer["candidates"][0]["id"], offer["revision"])
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: open_campaign_store(self.path).choose_growth(*args), range(8)))
        self.assertEqual(sum(not result["duplicate"] for result in results), 1)
        self.assertEqual(len(self.store.growth_status()["history"]), 1)

    def test_concurrent_different_clicks_only_one_wins(self):
        offer = self.store.prepare_growth()["offer"]
        def choose(item):
            try:
                return open_campaign_store(self.path).choose_growth(offer["offer_id"], item["id"], offer["revision"])
            except GrowthError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(choose, offer["candidates"][:2]))
        self.assertEqual(sum(isinstance(result, dict) for result in results), 1)
        self.assertEqual(results.count("conflicting_choice"), 1)

    def test_catalog_file_edits_cannot_change_saved_candidates_or_bit_mapping(self):
        original = load_catalog()
        store, path = self.catalog_store(original)
        first = store.prepare_growth()
        changed = copy.deepcopy(original)
        for item in changed["talents"]:
            item["bit_index"] += 100
            item["name"] = "replaced"
        path.write_text(json.dumps(changed), encoding="utf-8")
        reopened = open_campaign_store(self.path, runtime_catalog_path=path)
        self.assertEqual(reopened.prepare_growth(), first)
        selected = self.finish_choices(reopened)
        expected_words = encode_growth(original, [item["id"] for item in selected["talents"]], {item["id"]: item["stacks"] for item in selected["curses"]})
        loaded = reopened.restore_growth(101)
        self.assertEqual(loaded["growth_words"], expected_words)
        path.write_text("not json", encoding="utf-8")
        self.assertEqual(open_campaign_store(self.path, runtime_catalog_path=path).restore_growth(101), loaded)

    def test_legacy_active_attempt_revision_and_nonce_survive_growth_selection(self):
        old_attempt = self.store.restore(101)
        self.finish_choices()
        loaded = self.store.restore_growth(101)
        self.assertEqual((loaded["nonce"], loaded["revision"]), (old_attempt["nonce"], 0))
        self.assertEqual(self.store.status()["attempts"][0]["start_revision"], 0)
        self.assertEqual(self.store.complete(101, loaded["nonce"], 0, 0)["revision"], 1)

    def test_frozen_snapshot_reconnect_replay_and_rewards_once(self):
        selected = self.finish_choices()
        loaded = self.store.restore_growth(101)
        self.assertEqual(loaded["growth_words"], selected["growth_words"])
        self.assertEqual(self.store.growth_status()["state"], "in_mission")
        self.assertEqual(open_campaign_store(self.path).restore_growth(101), loaded)
        self.store.complete(101, loaded["nonce"], 0, 0)
        replay = open_campaign_store(self.path).restore_growth(101)
        self.assertTrue(replay["already_completed"])
        self.assertEqual(replay["nonce"], loaded["nonce"])
        self.assertEqual(replay["growth_words"], loaded["growth_words"])
        before = self.path.read_bytes()
        self.assertTrue(self.store.complete(101, loaded["nonce"], 0, 0)["duplicate"])
        self.assertEqual(self.path.read_bytes(), before)
        state = self.store.prepare_growth()
        self.assertEqual(state["state"], "waiting_next_map")
        self.assertEqual(state["upcoming"], {"talent": 2, "curse": 2})
        self.assertIsNone(state["offer"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(1,)])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_snapshots"), [(1,)])
        self.assert_error("phased_protocol_required", self.store.prepare_growth, 102)

    def test_completion_and_future_rights_roll_back_together(self):
        self.finish_choices()
        loaded = self.store.restore_growth(101)
        before = self.path.read_bytes()
        with patch.object(self.store, "_commit_result", side_effect=sqlite3.OperationalError("injected disk full")):
            with self.assertRaises(sqlite3.OperationalError):
                self.store.complete(101, loaded["nonce"], 0, 0)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(0,)])
        reopened = open_campaign_store(self.path)
        self.assertEqual(reopened.growth_status()["upcoming"], {"talent": 0, "curse": 0})
        self.assertEqual(reopened.status()["attempts"][0]["state"], "active")
        reopened.complete(101, loaded["nonce"], 0, 0)
        self.assertEqual(reopened.growth_status()["upcoming"], {"talent": 2, "curse": 2})

    def test_failed_load_snapshot_rolls_back_attempt_and_snapshot_together(self):
        self.finish_choices()
        before = self.path.read_bytes()
        original_freeze = growth.freeze
        def disk_failure(*args, **kwargs):
            original_freeze(*args, **kwargs)
            raise sqlite3.OperationalError("injected failure before load commit")
        with patch.object(growth, "freeze", side_effect=disk_failure):
            with self.assertRaises(sqlite3.OperationalError):
                self.store.restore_growth(101)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.store.status()["attempts"], [])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_snapshots"), [(0,)])
        self.assertEqual(self.store.growth_status()["state"], "ready")
        loaded = open_campaign_store(self.path).restore_growth(101)
        self.assertEqual(self.query("SELECT nonce FROM growth_snapshots"), [(loaded["nonce"],)])

    def test_frozen_loadout_does_not_follow_later_campaign_growth(self):
        selected = self.finish_choices()
        loaded = self.store.restore_growth(101)
        owned = [item["id"] for item in selected["talents"]]
        next_talent = next(item["id"] for item in load_catalog()["talents"] if item["id"] not in owned)
        # Represents later campaign growth. The current build deliberately does
        # not expose next-map selections until another map is supported.
        self.mutate("UPDATE growth_state SET talents_json=?,revision=revision+1 WHERE id=1", (json.dumps(owned + [next_talent]),))
        replay = open_campaign_store(self.path).restore_growth(101)
        self.assertEqual(replay["growth_words"], loaded["growth_words"])
        self.assertEqual(replay["nonce"], loaded["nonce"])

    def test_concurrent_completion_awards_future_rights_once(self):
        self.finish_choices()
        loaded = self.store.restore_growth(101)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: open_campaign_store(self.path).complete(101, loaded["nonce"], 0, 0), range(8)))
        self.assertEqual(sum(not result["duplicate"] for result in results), 1)
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(1,)])
        self.assertEqual(self.store.growth_status()["upcoming"], {"talent": 2, "curse": 2})

    def test_old_completed_record_gets_empty_replay_without_new_rewards(self):
        old = self.store.restore(101)
        receipt = self.store.complete(101, old["nonce"], 0, 0)
        old_result = self.query("SELECT * FROM results")
        before = self.path.read_bytes()
        self.assertEqual(self.store.growth_status()["state"], "legacy_complete")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertIn("당시 저장한 성장", growth_summary(self.store.prepare_growth()))
        replay = self.store.restore_growth(101)
        self.assertEqual(replay["growth_words"], [1] + [0] * 20)
        self.assertEqual(replay["nonce"], old["nonce"])
        self.assertEqual(replay["revision"], receipt["revision"])
        self.assertEqual(self.query("SELECT * FROM results"), old_result)
        self.assertTrue(self.store.complete(101, old["nonce"], 0, 0)["duplicate"])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(0,)])
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_offers"), [(0,)])

    def test_legacy_load_and_completion_do_not_award_prepared_growth(self):
        self.finish_choices()
        legacy = self.store.restore(101)
        self.store.complete(101, legacy["nonce"], 0, 0)
        self.assertEqual(self.query("SELECT COUNT(*) FROM growth_rewards"), [(0,)])
        self.assertEqual(self.store.restore_growth(101)["growth_words"], [1] + [0] * 20)

    def test_legacy_probe_file_is_never_migrated(self):
        path = Path(self.tmp.name) / "probe.sqlite3"
        probe = CampaignStore(path)
        attempt = probe.restore(1)
        probe.complete(1, attempt["nonce"], 123, 0)
        with closing(sqlite3.connect(path)) as conn:
            with conn:
                conn.execute("DELETE FROM metadata WHERE key='profile'")
        before = path.read_bytes()
        reopened = open_campaign_store(path)
        self.assertEqual(reopened.status()["growth_selection"], {"state": "unsupported"})
        self.assert_error("profile_mismatch", reopened.prepare_growth)
        self.assert_error("profile_mismatch", reopened.restore_growth, 101)
        self.assert_error("profile_mismatch", reopened.choose_growth, "bad", "bad", 0)
        self.assertEqual(path.read_bytes(), before)

    def test_bad_catalog_and_version_fail_without_partial_tables(self):
        store, path = self.catalog_store(load_catalog())
        before = self.path.read_bytes()
        path.write_text("{invalid", encoding="utf-8")
        self.assert_error("catalog_unavailable", store.prepare_growth)
        self.assert_error("catalog_version", store.prepare_growth, 101, 2)
        self.assert_error("protocol_version", store.restore_growth, 101, protocol_version=2)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(any(name.startswith("growth_") for (name,) in self.query("SELECT name FROM sqlite_master WHERE type='table'")))

    def test_initial_candidate_shortage_rolls_back_all_growth_tables(self):
        catalog = load_catalog()
        catalog["talents"] = catalog["talents"][:3]
        store, _ = self.catalog_store(catalog)
        before = self.path.read_bytes()
        self.assert_error("choice_pool_unavailable", store.prepare_growth)
        self.assertEqual(self.path.read_bytes(), before)

    def test_next_candidate_shortage_rolls_back_choice_and_keeps_offer(self):
        catalog = load_catalog()
        catalog["talents"] = catalog["talents"][:4]
        catalog['talent_pool_revision'] = 1  # An intentionally tiny legacy/custom pool.
        store, _ = self.catalog_store(catalog)
        state = store.prepare_growth()
        before = self.path.read_bytes()
        self.assert_error("choice_pool_unavailable", self.choose_first, state, store)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(store.growth_status(), state)

    def test_curse_tier_shortage_never_falls_back_to_other_rarity(self):
        catalog = load_catalog()
        catalog["curses"] = catalog["curses"][:3]
        catalog["curses"][0]["rarity"] = "uncommon"
        store, _ = self.catalog_store(catalog)
        state = store.prepare_growth()
        state = self.choose_first(state, store)
        state = self.choose_first(state, store)
        before = self.path.read_bytes()
        self.assert_error("choice_pool_unavailable", self.choose_first, state, store)
        self.assertEqual(self.path.read_bytes(), before)

    def test_unsupported_races_missions_and_unimplemented_items_are_excluded(self):
        catalog = load_catalog()
        for index, changes in enumerate(({"implemented": False}, {"race": "zerg"}, {"missions": [102]})):
            item = copy.deepcopy(catalog["talents"][0])
            item.update(id=f"unsupported-{index}", bit_index=400 + index, rarity="legendary", **changes)
            catalog["talents"].append(item)
        store, _ = self.catalog_store(catalog)
        state = store.prepare_growth()
        for _ in range(3):
            self.assertTrue(all(not item["id"].startswith("unsupported-") for item in state["offer"]["candidates"]))
            state = self.choose_first(state, store)

    def test_rarity_draw_uses_available_tier_weights_without_zero_pool_tiers(self):
        catalog = load_catalog()
        catalog["talents"] = catalog["talents"][:8]
        catalog['talent_pool_revision'] = 1
        for index, item in enumerate(catalog["talents"]):
            item["rarity"] = "common" if index < 4 else "rare"
        store, _ = self.catalog_store(catalog)
        calls = []
        class InspectRandom:
            def choices(self, values, weights, k):
                calls.append((list(values), list(weights), k))
                return [values[0]]
            def choice(self, values):
                return values[0]
        with patch.object(growth.secrets, "SystemRandom", return_value=InspectRandom()):
            store.prepare_growth()
        self.assertEqual(calls, [(["common", "rare"], [40, 20], 1)] * 2
                         + [(["rare"], [20], 1)] * 2)

    def test_corrupt_saved_catalog_and_partial_schema_fail_read_only(self):
        self.store.prepare_growth()
        self.mutate("UPDATE growth_state SET catalog_json='{' WHERE id=1")
        before = self.path.read_bytes()
        self.assert_error("invalid_growth", self.store.growth_status)
        self.assert_error("invalid_growth", self.store.prepare_growth)
        self.assertEqual(self.path.read_bytes(), before)
        self.mutate("DROP TABLE growth_rewards")
        before = self.path.read_bytes()
        self.assert_error("invalid_growth", self.store.growth_status)
        self.assertEqual(self.path.read_bytes(), before)

    def test_corrupt_immutable_words_are_rejected_before_restore(self):
        self.finish_choices()
        self.store.restore_growth(101)
        self.mutate("UPDATE growth_snapshots SET words_json=?", (json.dumps([1] + [0] * 19),))
        before = self.path.read_bytes()
        self.assert_error("invalid_growth", self.store.restore_growth, 101)
        self.assertEqual(self.path.read_bytes(), before)


class GameChoiceSlotTests(GrowthStoreTestCase):
    """The map submits an offer UUID and a displayed 1-based candidate slot."""

    def test_game_slots_resolve_saved_order_for_three_talents_two_curses(self):
        state = self.store.prepare_growth()
        chosen = []
        for kind, slot in ((1, 4), (1, 3), (1, 2), (2, 3), (2, 3)):
            offer = state["offer"]
            chosen.append(offer["candidates"][slot - 1]["id"])
            state = self.store.choose_growth_slot(offer["offer_id"], slot, offer["revision"], choice_kind=kind)
        self.assertEqual(state["state"], "ready")
        self.assertEqual([item["selected_id"] for item in state["history"]], chosen)
        self.assertEqual({item["id"]: item["stacks"] for item in state["curses"]}, dict(Counter(chosen[-2:])))
        self.assertEqual(self.store.status()["revision"], 0)

    def test_same_slot_retry_is_idempotent_after_restart_and_frozen_replay(self):
        state = self.store.prepare_growth()
        offer = state["offer"]
        args = (offer["offer_id"], 2, offer["revision"])
        self.store.choose_growth_slot(*args, choice_kind=1)
        before = self.path.read_bytes()
        self.assertTrue(open_campaign_store(self.path).choose_growth_slot(*args, choice_kind=1)["duplicate"])
        self.assertEqual(self.path.read_bytes(), before)
        self.finish_choices()
        loaded = self.store.restore_growth(101)
        self.store.complete(101, loaded["nonce"], 0, 0)
        before = self.path.read_bytes()
        self.assertTrue(open_campaign_store(self.path).choose_growth_slot(*args, choice_kind=1)["duplicate"])
        self.assertEqual(self.path.read_bytes(), before)

    def test_invalid_slot_kind_revision_and_uuid_leave_offer_unchanged(self):
        offer = self.store.prepare_growth()["offer"]
        defaults = {"offer_id": offer["offer_id"], "choice_slot": 1, "expected_revision": offer["revision"], "choice_kind": 1}
        cases = [
            ("invalid_choice_slot", {"choice_slot": value}) for value in (0, -1, 5, True, "1")
        ] + [
            ("invalid_choice_kind", {"choice_kind": value}) for value in (0, 3, True, "1")
        ] + [
            ("invalid_choice_revision", {"expected_revision": value}) for value in (-1, True, "0", 0x100000000)
        ] + [
            ("choice_kind_mismatch", {"choice_kind": 2}),
            ("stale_choice", {"expected_revision": offer["revision"] + 1}),
            ("invalid_offer_id", {"offer_id": "bad"}),
            ("invalid_offer_id", {"offer_id": None}),
            ("unknown_offer", {"offer_id": str(uuid.uuid4())}),
        ]
        before = self.path.read_bytes()
        for code, changes in cases:
            with self.subTest(code=code, changes=changes):
                self.assert_error(code, self.store.choose_growth_slot, **{**defaults, **changes})
                self.assertEqual(self.path.read_bytes(), before)

    def test_curse_fourth_slot_and_forged_selected_kind_are_rejected(self):
        state = self.store.prepare_growth()
        for _ in range(3):
            state = self.choose_first(state)
        offer = state["offer"]
        before = self.path.read_bytes()
        self.assert_error("invalid_choice_slot", self.store.choose_growth_slot, offer["offer_id"], 4, offer["revision"], choice_kind=2)
        self.assertEqual(self.path.read_bytes(), before)
        self.store.choose_growth_slot(offer["offer_id"], 1, offer["revision"], choice_kind=2)
        before = self.path.read_bytes()
        self.assert_error("choice_kind_mismatch", self.store.choose_growth_slot, offer["offer_id"], 1, offer["revision"], choice_kind=1)
        self.assert_error("conflicting_choice", self.store.choose_growth_slot, offer["offer_id"], 2, offer["revision"], choice_kind=2)
        self.assertEqual(self.path.read_bytes(), before)

    def test_slot_request_cannot_prepare_missing_or_unissued_offer(self):
        before = self.path.read_bytes()
        self.assert_error("growth_not_prepared", self.store.choose_growth_slot, str(uuid.uuid4()), 1, 0, choice_kind=1)
        self.assertEqual(self.path.read_bytes(), before)
        self.store.prepare_growth()
        unissued = self.query("SELECT offer_id FROM growth_offers WHERE candidates_json IS NULL AND kind='talent' ORDER BY sequence LIMIT 1")[0][0]
        before = self.path.read_bytes()
        self.assert_error("offer_not_ready", self.store.choose_growth_slot, unissued, 1, 0, choice_kind=1)
        self.assertEqual(self.path.read_bytes(), before)

    def test_concurrent_slot_retries_award_only_once(self):
        offer = self.store.prepare_growth()["offer"]
        def choose(_):
            return open_campaign_store(self.path).choose_growth_slot(offer["offer_id"], 4, offer["revision"], choice_kind=1)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(choose, range(8)))
        self.assertEqual(sum(not value["duplicate"] for value in results), 1)
        self.assertEqual(len(self.store.growth_status()["history"]), 1)

    def test_concurrent_different_slots_cannot_change_the_winning_choice(self):
        offer = self.store.prepare_growth()["offer"]
        def choose(slot):
            try:
                return open_campaign_store(self.path).choose_growth_slot(offer["offer_id"], slot, offer["revision"], choice_kind=1)
            except GrowthError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(choose, (1, 4)))
        self.assertEqual(sum(isinstance(value, dict) for value in results), 1)
        self.assertEqual(results.count("conflicting_choice"), 1)
        self.assertEqual(len(self.store.growth_status()["history"]), 1)

    def test_slot_choice_and_next_offer_failure_roll_back_together(self):
        catalog = load_catalog()
        catalog["talents"] = catalog["talents"][:4]
        catalog['talent_pool_revision'] = 1
        store, _ = self.catalog_store(catalog)
        offer = store.prepare_growth()["offer"]
        before = self.path.read_bytes()
        self.assert_error("choice_pool_unavailable", store.choose_growth_slot, offer["offer_id"], 4, offer["revision"], choice_kind=1)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(store.growth_status()["offer"], offer)

    def test_slot_mapping_rejects_corrupt_persisted_candidates(self):
        offer = self.store.prepare_growth()["offer"]
        for corrupt in ("{", "null", "[]", '[{"id":"same"},{"id":"same"},{"id":"x"},{"id":"y"}]'):
            with self.subTest(corrupt=corrupt):
                self.mutate("UPDATE growth_offers SET candidates_json=? WHERE offer_id=?", (corrupt, offer["offer_id"]))
                before = self.path.read_bytes()
                self.assert_error("invalid_growth", self.store.choose_growth_slot, offer["offer_id"], 1, offer["revision"], choice_kind=1)
                self.assertEqual(self.path.read_bytes(), before)


class CatalogValidationTests(unittest.TestCase):
    def test_catalog_rejects_duplicate_slots_ids_and_bad_types(self):
        mutations = [
            lambda c: c["talents"][0].update(bit_index=512),
            lambda c: c["talents"][0].update(bit_index=True),
            lambda c: c["talents"][1].update(bit_index=c["talents"][0]["bit_index"]),
            lambda c: c["curses"][0].update(id=c["talents"][0]["id"]),
            lambda c: c["curses"][0].update(byte_index=16),
            lambda c: c["curses"][0].update(max_stacks=256),
            lambda c: c["talents"][0].update(implemented="yes"),
            lambda c: c["talents"][0].update(missions=[True]),
            lambda c: c["talents"][0].update(name=" "),
            lambda c: c["talents"][0].update(rarity="mythic"),
            lambda c: c["talents"][0].update(race="neutral"),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                catalog = load_catalog()
                mutation(catalog)
                with self.assertRaises(GrowthError):
                    validate_catalog(catalog)

    def test_encode_exact_dword_boundaries_and_curse_byte_order(self):
        catalog = load_catalog()
        catalog["talents"] = catalog["talents"][:4]
        for item, bit in zip(catalog["talents"], (0, 31, 32, 511)):
            item["bit_index"] = bit
        catalog["curses"] = catalog["curses"][:3]
        for item, index in zip(catalog["curses"], (0, 3, 15)):
            item["byte_index"] = index
        catalog = validate_catalog(catalog)
        words = encode_growth(catalog, [item["id"] for item in catalog["talents"]], {item["id"]: count for item, count in zip(catalog["curses"], (1, 2, 255))})
        expected = [1] + [0] * 20
        expected[1], expected[2], expected[16] = 0x80000001, 1, 0x80000000
        expected[17], expected[20] = 0x02000001, 0xFF000000
        self.assertEqual(words, expected)

    def test_encode_rejects_corrupt_owned_values(self):
        catalog = load_catalog()
        talent, curse = catalog["talents"][0]["id"], catalog["curses"][0]["id"]
        for owned, curses in (([talent, talent], {}), ([{}], {}), (talent, {}), ([], []), (["unknown"], {}), ([], {curse: True}), ([], {curse: 256}), ([], {"unknown": 1})):
            with self.subTest(owned=owned, curses=curses), self.assertRaises(GrowthError):
                encode_growth(catalog, owned, curses)


if __name__ == "__main__":
    unittest.main()
