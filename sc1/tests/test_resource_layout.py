"""Functional resource-field regression checks; no installed file/game access."""
from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
import struct
import sys
import unittest

NATIVE = Path(__file__).resolve().parents[1] / "native_campaign"
sys.path.insert(0, str(NATIVE))
from build_plain_chk import CHK
import mineral_layout as geometry
import mining_layout_audit as audit
import resource_depot_placement as depot
import resource_layout as layout


def source(relative):
    return CHK((geometry.SOURCE_ROOT / "locales/koKR/Assets/campaign" / relative / "staredit/scenario.chk").read_bytes())


class ResourceLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t03 = source("Terran/Terran03")
        cls.edited = deepcopy(cls.t03)
        cls.report = layout.apply_layout(cls.edited, {"mission_id": 103, "race": "terran", "owner": 1})

    def test_real_human_t03_dense_main_is_fully_front_reachable(self):
        human = [field for field in self.report["clusters"] if field.get("anchor", {}).get("unit_index") == 160]
        self.assertEqual(sum(field["mineral_count"] for field in human), 10)
        info = list(map(geometry._info, geometry._records(self.edited)))
        for field in human:
            checked = audit.audit_field(self.edited, info, field["unit_indices"], field["anchor"], field["direction"])
            self.assertTrue(checked["foundation_terrain_buildable"])
            self.assertTrue(checked["resource_depot_clear"])
            self.assertEqual(checked["front_reachable_count"], field["mineral_count"])
        self.assertEqual(self.report["functional_cluster_count"], self.report["cluster_count"])

    def test_every_non_resource_coordinate_byte_and_section_is_preserved(self):
        before, after = self.t03.getsection("UNIT"), self.edited.getsection("UNIT")
        self.assertEqual(layout.verify_only_resource_coordinates(before, after), self.report["moved_indices"])
        self.assertGreater(self.report["moved_count"], 2)
        for i in range(len(before) // 36):
            a, b = before[36 * i:36 * i + 36], after[36 * i:36 * i + 36]
            self.assertEqual(a[:4] + a[8:], b[:4] + b[8:])
            if struct.unpack_from("<H", a, 8)[0] not in layout.MOVABLE_RESOURCES:
                self.assertEqual(a, b)
        self.assertEqual(self.t03.order, self.edited.order)
        for name in self.t03.order:
            if name != b"UNIT":
                self.assertEqual(self.t03.sections[name], self.edited.sections[name])

    def test_existing_resource_clear_placed_depots_remain_rebuildable(self):
        info = list(map(geometry._info, geometry._records(self.edited)))
        for center in self.report["preserved_original_depot_centers"]:
            self.assertTrue(layout._resource_clear(center, info))

    def test_all_formations_are_at_most_two_outer_rows_with_worker_aisles(self):
        for field in self.report["clusters"]:
            if field["status"] != "functional_line":
                continue
            self.assertIn(field["rows"], (1, 2))
            if field["rows"] == 2:
                footprint = 64 if field["direction"][0] else 32
                self.assertGreaterEqual(field["row_spacing_pixels"] - footprint, 64)
            self.assertTrue(field["front_access"]["all_mineral_fronts_reachable"])
        self.assertTrue(all(move["displacement_pixels"] <= layout.MAX_DISPLACEMENT for move in self.report["moves"]))

    def test_worker_can_fit_in_thirty_two_pixel_aisle(self):
        raw = [bytearray(b"\x01" * 64) for _ in range(64)]
        clear = layout._worker_terrain(raw)
        boxes, _ = geometry.load_unit_geometry()
        labels, _, _ = layout._components(clear, [(256, 240, 176, 11), (256, 304, 177, 11)], (0, 0, 64, 64), boxes)
        self.assertGreater(labels[33][32], 0)  # (260,268): exact edge contact is legal.
        self.assertGreater(labels[34][32], 0)  # (260,276).
        self.assertEqual(labels[32][32], 0)
        self.assertEqual(labels[35][32], 0)

    def test_enclosed_ore_pocket_does_not_freeze_entire_field_as_script_gate(self):
        info = [(x, y, 176, 11) for x, y in ((224, 208), (288, 208), (224, 304), (288, 304),
                                           (192, 240), (192, 272), (320, 240), (320, 272))]
        clear = layout._worker_terrain([bytearray(b"\x01" * 64) for _ in range(64)])
        boxes, _ = geometry.load_unit_geometry()
        self.assertFalse(layout._true_mining_gate(info, list(range(len(info))), clear, boxes))

    def test_real_low_amount_t01_resource_is_rearranged_in_functional_field(self):
        chk = source("Terran/Terran01")
        report = layout.apply_layout(chk, {"mission_id": 101, "race": "terran"})
        self.assertIn(27, report["moved_indices"])
        self.assertEqual(report["functional_cluster_count"], report["cluster_count"])

    def test_strict_verifier_rejects_amount_type_owner_serial_and_count_changes(self):
        before = self.t03.getsection("UNIT")
        index = self.report["moved_indices"][0]
        for offset in (0, 8, 16, 20):
            after = bytearray(before)
            after[index * 36 + offset] ^= 1
            with self.assertRaises(ValueError):
                layout.verify_only_resource_coordinates(before, after)
        with self.assertRaises(ValueError):
            layout.verify_only_resource_coordinates(before, before + bytes(36))

    def test_plan_is_deterministic(self):
        self.assertEqual(layout.plan_layout(self.t03, {"mission_id": 103, "race": "terran", "owner": 1}), self.report)

    def test_split_human_main_keeps_every_mineral_at_the_original_nexus(self):
        chk = source("EXPProtoss/Protoss07")
        report = layout.apply_layout(chk, {"mission_id": 407, "race": "protoss", "owner": 1})
        fields = [f for f in report["clusters"] if f.get("required_original_depot_index") == 333]
        self.assertEqual(sum(f["mineral_count"] for f in fields), 13)
        self.assertTrue(all(f["status"].startswith("functional_") for f in fields))
        self.assertTrue(all(f["anchor"].get("unit_index") == 333 for f in fields))
        self.assertTrue(all(f["anchor"]["kind"] == "existing_depot" for f in fields))

    def test_gas_reports_keep_close_dropoff_and_refinery_foundation(self):
        self.assertEqual(self.report["functional_geyser_count"], self.report["geyser_count"])
        for gas in self.report["gas_fields"]:
            self.assertTrue(gas["refinery_foundation_buildable"])
            self.assertLessEqual(gas["depot_distance_pixels"], 768)

    def test_far_blocked_zerg_main_ore_returns_to_same_original_hatchery(self):
        chk = source("EXPZerg/Zerg07")
        report = layout.apply_layout(chk, {"mission_id": 607, "race": "zerg", "owner": 3})
        fields = [f for f in report["clusters"] if f.get("required_original_depot_index") == 352]
        self.assertEqual(sum(f["mineral_count"] for f in fields), 9)
        self.assertTrue(all(f["status"].startswith("functional_") for f in fields))
        info = list(map(geometry._info, geometry._records(chk)))
        self.assertTrue(all(f["anchor"].get("unit_index") == 352 for f in fields))
        self.assertTrue(all(math.dist(info[i][:2], (3648, 3376)) <= 512
                            for f in fields for i in f["unit_indices"]))

    def test_rearrangement_cannot_cut_off_existing_terran_gas_return_lane(self):
        chk = source("Terran/Terran12")
        report = layout.apply_layout(chk, {"mission_id": 110, "race": "terran", "owner": 1})
        gas = next(g for g in report["gas_fields"] if g["unit_index"] == 305)
        self.assertEqual(gas["status"], "functional_geyser")
        self.assertEqual(gas["anchor"].get("unit_index"), 300)
        self.assertFalse(gas["changed"])

    def test_army_guard_rejects_worker_only_gap_that_splits_large_regions(self):
        raw = [bytearray(b"\x01" * 128) for _ in range(64)]
        workers = layout._worker_terrain(raw)
        army = layout._worker_terrain(layout._worker_terrain(workers))
        ys = list(range(32, 225, 32)) + list(range(320, 481, 32))
        before = [(512, y, 176, 11) for y in ys]
        after = list(before)
        changed = ys.index(320)
        after[changed] = (512, 288, 176, 11)
        boxes, _ = geometry.load_unit_geometry()
        labels, _, _ = layout._components(workers, after, (0, 0, 128, 64), boxes)
        self.assertEqual(labels[32][12], labels[32][112])
        self.assertGreater(labels[32][12], 0)
        self.assertFalse(layout._army_route_ok(before, after, [changed], army, boxes, {}))

    def test_reserved_wave_cells_clear_the_full_largest_unit_rectangle(self):
        raw = [bytearray(b"\x01" * 64) for _ in range(64)]
        boxes, _ = geometry.load_unit_geometry()
        info = [(256, 240, 176, 11)]
        # Outside the obsolete 40px circle but inside mineral64x32 + unit48x48.
        self.assertFalse(layout._geometry_ok(info, [0], [(256, 240)], raw, boxes, [(308, 272)]))
        self.assertTrue(layout._geometry_ok(info, [0], [(256, 240)], raw, boxes, [(312, 272)]))

    def test_army_guard_uses_immutable_original_component_after_prior_moves(self):
        raw = [bytearray(b"\x01" * 128) for _ in range(64)]
        workers = layout._worker_terrain(raw)
        army = layout._worker_terrain(layout._worker_terrain(workers))
        boxes, _ = geometry.load_unit_geometry()
        ys = list(range(32, 481, 32))
        prior = [(896, y, 176, 11) for y in ys]
        later = [(864, y, 176, 11) for y in ys]
        # The immutable original map had no barrier; comparing only the prior
        # wall could miss growth of its previously insignificant far-side pocket.
        self.assertFalse(layout._army_route_ok(prior, later, list(range(len(ys))), army, boxes, {"baseline": []}))


    def test_diagonal_source_expansion_has_verified_depot_for_every_patch(self):
        chk = source("Zerg/Zerg06")
        report = layout.apply_layout(chk, {"mission_id": 206, "race": "zerg"})
        self.assertEqual(report["functional_cluster_count"], report["cluster_count"])
        self.assertTrue(any(f.get("anchor", {}).get("reviewed_source_anchor") for f in report["clusters"]))
        info = list(map(geometry._info, geometry._records(chk)))
        for field in report["clusters"]:
            if set(field["unit_indices"]) & {36, 37, 40, 42}:
                checked = audit.audit_field(chk, info, field["unit_indices"], field["anchor"], field["direction"])
                self.assertTrue(checked["foundation_terrain_buildable"])
                self.assertTrue(checked["resource_depot_clear"])
                self.assertEqual(checked["front_reachable_count"], field["mineral_count"])

    def test_protected_resource_position_and_trigger_stay_exact_with_open_front(self):
        chk = source("EXPZerg/Zerg08")
        original = chk.getsection("UNIT")[19 * 36:20 * 36]
        report = layout.apply_layout(chk, {"mission_id": 608, "race": "zerg"})
        self.assertEqual(chk.getsection("UNIT")[19 * 36:20 * 36], original)
        field = next(f for f in report["clusters"] if 19 in f["unit_indices"])
        self.assertEqual(field["status"], "functional_protected_resource")
        self.assertEqual(field["anchor"]["unit_index"], 43)
        info = list(map(geometry._info, geometry._records(chk)))
        checked = audit.audit_field(chk, info, [19], field["anchor"], field["direction"])
        self.assertEqual(checked["front_reachable_count"], 1)

    def test_nonhuman_ore_uses_ground_connected_same_owner_depot(self):
        chk = source("EXPZerg/Zerg10")
        report = layout.apply_layout(chk, {"mission_id": 610, "race": "zerg"})
        indices = {280, 286, 292, 293, 296, 301, 302, 305, 310}
        fields = [f for f in report["clusters"] if set(f["unit_indices"]) & indices]
        self.assertEqual(sum(len(set(f["unit_indices"]) & indices) for f in fields), 9)
        self.assertTrue(all(f["status"].startswith("functional_") for f in fields))
        self.assertTrue(all(f["anchor"].get("unit_index") == 276 for f in fields))

    def test_diagonal_gas_depot_avoids_unnecessary_geyser_relocation(self):
        chk = source("Protoss/Protoss05")
        before = chk.getsection("UNIT")[87 * 36:88 * 36]
        report = layout.apply_layout(chk, {"mission_id": 305, "race": "protoss"})
        self.assertEqual(chk.getsection("UNIT")[87 * 36:88 * 36], before)
        self.assertEqual(report["functional_geyser_count"], 3)
        gas = next(g for g in report["gas_fields"] if g["unit_index"] == 87)
        self.assertEqual(gas["status"], "functional_geyser")
        self.assertEqual(gas["anchor"]["gas_anchor_search"], "complete_local_grid")
        self.assertLessEqual(gas["depot_distance_pixels"], 768)
        info = list(map(geometry._info, geometry._records(chk)))
        self.assertTrue(audit.foundation_buildable(chk, gas["anchor"]["center"], gas["anchor"]["depot_type"]))
        self.assertTrue(layout._resource_clear(gas["anchor"]["center"], info))
        self.assertEqual(report["functional_cluster_count"], report["cluster_count"])


if __name__ == "__main__":
    unittest.main()
