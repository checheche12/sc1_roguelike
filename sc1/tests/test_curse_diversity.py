"""New curse options are additive; issued choices and loadouts stay immutable."""
import copy
import json
from contextlib import closing
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from sc1.campaign import growth, phased_growth, progression
from sc1.campaign.missions import load_missions
from sc1.campaign.runtime_catalog import load_catalog, encode_growth, GrowthError
from sc1.manager.store import open_campaign_store, GrowthChoicesPending

HERE = Path(__file__).resolve().parents[1] / "campaign"
OLD_ALL = HERE / "design_snapshots/runtime_all_before_curse_diversity/runtime_talents_all.json"


class CurseDiversityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "run.sqlite3"
        self.store = open_campaign_store(self.path, runtime_catalog_path=OLD_ALL)

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self, query, args=()):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute(query, args).fetchall()

    def load(self, phase=1, nonce=None, mission=101):
        try:
            return self.store.restore_growth_phase(mission, 1, phase, nonce=nonce)
        except GrowthChoicesPending as pending:
            return pending.state

    def choose(self, state, phase=1, nonce=None, slot=1, mission=101):
        offer = state["offer"]
        return self.store.choose_growth_phase_slot(
            offer["offer_id"], slot, offer["revision"], mission, 1,
            choice_kind=1 if offer["kind"] == "talent" else 2,
            phase=phase, nonce=nonce)

    def test_each_tier_has_five_and_original_nine_preserve_effects_and_wire_ids(self):
        before, after = load_catalog(OLD_ALL), load_catalog()
        without_display = lambda rows: [{k: v for k, v in item.items() if k != "description"} for item in rows]
        comparable=copy.deepcopy(after['curses'][:9])
        for index in (1,2):
            # The expanded native target metadata now covers all campaigns.
            # Numeric mechanics and the frozen historical contract stay exact.
            previous,current=before['curses'][index],comparable[index]
            self.assertEqual(current['legacy_effect'],previous['effect'])
            omit={'units','weapons','owner_scope','exclude_hallucinations'}
            self.assertEqual({k:v for k,v in current['effect'].items() if k not in omit},
                             {k:v for k,v in previous['effect'].items() if k not in omit})
            current['effect']=previous['effect'];current['target_units']=previous['target_units']
        self.assertEqual(without_display(comparable), without_display(before["curses"]))
        self.assertEqual(without_display(after["talents"][:104]), without_display(before["talents"]))
        self.assertEqual([i["byte_index"] for i in after["curses"]], list(range(15)))
        for tier in ("common", "uncommon", "rare"):
            self.assertEqual(sum(x["rarity"] == tier for x in after["curses"]), 5)
        contract = json.loads((HERE / "curse_diversity_contract.json").read_text(encoding="utf-8"))
        for row in contract["curses"]:
            item = after["curses"][row["slot"]]
            self.assertEqual(item["source_description"], row["source"]["description"])
            self.assertEqual(item["source_numbers"], row["source"]["numbers"])
            self.assertEqual(item["rarity"], row["source"]["rarity"])
            self.assertEqual(item["max_stacks"], row["max_stacks"])

    def test_all_maps_have_five_initial_and_three_after_capped_options(self):
        catalog = load_catalog()
        for mission in load_missions():
            tier = progression.curse_tier(mission["mission_id"])
            pool = [x for x in catalog["curses"]
                    if x["rarity"] == tier and progression.item_eligible(x, mission["mission_id"], "curse")]
            self.assertEqual(len(pool), 5, mission["mission_id"])
            self.assertGreaterEqual(sum(x["max_stacks"] == 255 for x in pool), 3)

    def test_existing_offer_pin_and_snapshot_survive_future_phase_upgrade(self):
        state = self.choose(self.load())  # old issued common curse offer
        old_offer = copy.deepcopy(state["offer"])
        pinned = self.rows("SELECT catalog_json FROM growth_state")
        phase_pinned = self.rows("SELECT * FROM growth_phase_catalogs")
        self.store = open_campaign_store(self.path)
        self.assertEqual(self.load()["offer"], old_offer)
        self.choose(self.load())
        snapshot = self.load()
        snapshots = self.rows("SELECT * FROM growth_phase_snapshots")
        selected = self.rows("SELECT * FROM growth_offers WHERE selected_id IS NOT NULL")
        # Force the actual unissued pool sampler to choose the newly appended
        # slots. This verifies eligibility, selection, encoding and replay.
        with patch.object(phased_growth.secrets, "SystemRandom", return_value=random.Random(2)):
            second = self.load(2, snapshot["nonce"])
            with patch.object(phased_growth.secrets, "SystemRandom") as rng:
                rng.return_value.sample.side_effect = lambda values, k: values[-k:]
                second = self.choose(second, 2, snapshot["nonce"])
        self.assertTrue(any(x["byte_index"] >= 9 for x in second["offer"]["candidates"]))
        new_slot = next(i + 1 for i, x in enumerate(second["offer"]["candidates"]) if x["byte_index"] >= 9)
        new_curse = second["offer"]["candidates"][new_slot - 1]
        self.choose(second, 2, snapshot["nonce"], new_slot)
        restored = self.load(2, snapshot["nonce"])
        index = new_curse["byte_index"]
        self.assertEqual((restored["growth_words"][17 + index // 4] >> (index % 4 * 8)) & 255, 1)
        self.assertEqual(self.rows("SELECT catalog_json FROM growth_state"), pinned)
        self.assertEqual(self.rows("SELECT * FROM growth_phase_catalogs"), phase_pinned)
        self.assertEqual(self.rows("SELECT * FROM growth_phase_snapshots WHERE phase=1"), snapshots)
        self.assertEqual(self.rows("SELECT * FROM growth_offers WHERE selected_id IS NOT NULL ORDER BY sequence")[:2], selected)
        self.assertEqual(self.rows("SELECT candidates_json FROM growth_offers WHERE offer_id=?", (old_offer["offer_id"],))[0][0],
                         json.dumps(old_offer["candidates"], ensure_ascii=False, sort_keys=True))
        self.assertEqual(len(self.rows("SELECT * FROM growth_curse_pool_updates")), 1)
        before = self.path.read_bytes()
        self.store.growth_status(101)
        self.assertEqual(self.path.read_bytes(), before)

    def test_curse_upgrade_only_adds_separately_authorized_talent_ids(self):
        self.store = open_campaign_store(self.path, runtime_catalog_path=HERE / "runtime_talents.json")
        initial = self.load()
        old_ids = {x["id"] for x in load_catalog(HERE / "runtime_talents.json")["talents"]}
        from sc1.campaign.talent_pool import APPENDED
        allowed_ids = old_ids | APPENDED.keys()
        self.store = open_campaign_store(self.path)
        self.assertEqual(self.load()["offer"], initial["offer"])
        state = self.choose(initial)
        self.choose(state)
        snapshot = self.load()
        second = self.load(2, snapshot["nonce"])
        self.assertTrue({x["id"] for x in second["offer"]["candidates"]} <= allowed_ids)

    def test_custom_catalog_and_read_only_inspection_do_not_migrate(self):
        self.load()
        self.assertFalse(self.rows("SELECT name FROM sqlite_master WHERE name='growth_curse_pool_updates'"))
        self.store = open_campaign_store(self.path)
        before = self.path.read_bytes()
        self.store.growth_status(101)
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(self.rows("SELECT name FROM sqlite_master WHERE name='growth_curse_pool_updates'"))

    def test_capped_entries_are_excluded_before_sampling(self):
        self.store = open_campaign_store(self.path)
        state = self.choose(self.load())
        with closing(sqlite3.connect(self.path)) as conn:
            conn.row_factory = sqlite3.Row
            current = growth._state(conn)
            stacks = {x["id"]: x["max_stacks"] for x in load_catalog()["curses"] if x["max_stacks"] < 255}
            conn.execute("UPDATE growth_state SET curses_json=?", (json.dumps(stacks),))
            conn.execute("UPDATE growth_offers SET candidates_json=NULL WHERE offer_id=?", (state["offer"]["offer_id"],))
            phased_growth._issue(conn, 101, 1, load_catalog())
            offered = json.loads(conn.execute("SELECT candidates_json FROM growth_offers WHERE offer_id=?", (state["offer"]["offer_id"],)).fetchone()[0])
            self.assertEqual({x["byte_index"] for x in offered}, {0, 1, 2})
            conn.rollback()

    def test_wire_slots_9_through_14_and_max_stacks_are_enforced(self):
        catalog = load_catalog()
        counts = {x["id"]: x["max_stacks"] for x in catalog["curses"][9:]}
        encoded = encode_growth(catalog, [], counts)
        for item in catalog["curses"][9:]:
            i = item["byte_index"]
            self.assertEqual((encoded[17 + i // 4] >> ((i % 4) * 8)) & 255, item["max_stacks"])
        bad = dict(counts)
        bad[catalog["curses"][9]["id"]] = 4
        with self.assertRaises(GrowthError):
            encode_growth(catalog, [], bad)

    def test_mutated_old_effect_or_slot_is_rejected(self):
        old, new = load_catalog(OLD_ALL), load_catalog()
        for key, value in [("byte_index", 15), ("rarity", "rare"), ("effect", {"invented": True})]:
            altered = copy.deepcopy(new["curses"])
            altered[0][key] = value
            altered[0].pop("legacy_effect", None)
            with self.assertRaises(GrowthError):
                growth._merge_curse_pool(old, altered, 2)

    def test_unissued_curse_draw_can_cover_all_five_distinct_options(self):
        self.store = open_campaign_store(self.path)
        state = self.choose(self.load())
        seen, sets = set(), set()
        with closing(sqlite3.connect(self.path)) as conn:
            conn.row_factory = sqlite3.Row
            for seed in range(12):
                conn.execute("UPDATE growth_offers SET candidates_json=NULL WHERE offer_id=?", (state["offer"]["offer_id"],))
                with patch.object(phased_growth.secrets, "SystemRandom", return_value=random.Random(seed)):
                    phased_growth._issue(conn, 101, 1, load_catalog())
                offered = json.loads(conn.execute("SELECT candidates_json FROM growth_offers WHERE offer_id=?", (state["offer"]["offer_id"],)).fetchone()[0])
                ids = frozenset(x["byte_index"] for x in offered)
                self.assertEqual(len(ids), 3)
                seen |= ids
                sets.add(ids)
            conn.rollback()
        self.assertEqual(seen, {0, 1, 2, 9, 10})
        self.assertGreater(len(sets), 1)

    def test_native_text_uses_original_percent_not_cooldown_fraction(self):
        header = (HERE.parent / "native_campaign/plugin/include/frozen_catalog.generated.h").read_text(encoding="utf-8")
        self.assertNotIn("100/130", header)
        catalog = load_catalog()
        marine = next(x for x in catalog["talents"] if x["bit_index"] == 2)
        self.assertIn("30%", marine["description"])
        cooldown = next(p for p in marine["effect"]["patches"] if p["field"] == "cooldown")
        n, d = cooldown["value"]
        self.assertAlmostEqual((d / n - 1) * 100, 30)


if __name__ == "__main__":
    unittest.main()
