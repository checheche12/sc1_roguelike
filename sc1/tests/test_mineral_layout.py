"""Offline mineral-placement safety checks; no game or installed files touched."""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest

NATIVE = Path(__file__).resolve().parents[1] / "native_campaign"
sys.path.insert(0, str(NATIVE))
from build_plain_chk import CHK
import mineral_layout as layout


def unit(x, y, kind=176, amount=1500, owner=11):
    # Nonzero unrelated fields expose accidental reconstruction of UNIT data.
    record = bytearray(range(36))
    struct.pack_into("<HHH", record, 4, x, y, kind)
    record[16] = owner
    struct.pack_into("<I", record, 20, amount)
    return bytes(record)


def fixture(points=((160, 112), (256, 144), (160, 176), (224, 176)), amounts=None, extra=(), regions=None):
    amounts = amounts or [1500] * len(points)
    raw_units = b"".join(unit(x, y, 176 + i % 3, amounts[i]) for i, (x, y) in enumerate(points)) + b"".join(extra)
    regions = regions if regions is not None else [(0, 0, 512, 512)]
    sections = [(b"DIM ", struct.pack("<HH", 16, 16)), (b"UNIT", raw_units),
                (b"TRIG", bytes(2400)), (b"MRGN", b"".join(struct.pack("<4IHH", *rect, 0, 0) for rect in regions)),
                (b"TEST", b"other original bytes")]
    chk = CHK(b"".join(struct.pack("<4sI", key, len(value)) + value for key, value in sections))
    terrain = ([bytearray(b"\x01" * 64) for _ in range(64)], {"test": "open raw 8px walk grid"})
    return chk, terrain


class MineralLayoutTests(unittest.TestCase):
    def test_improves_short_rows_and_preserves_every_other_byte(self):
        original, terrain = fixture(points=((160, 80), (192, 112), (256, 112), (160, 144), (224, 144), (256, 176)))
        edited = deepcopy(original)
        report = layout.apply_layout(edited, {"mission_id": 999}, terrain=terrain)
        self.assertGreater(report["moved_count"], 0)
        self.assertEqual(layout.verify_only_mineral_coordinates(original.getsection("UNIT"), edited.getsection("UNIT")), report["moved_indices"])
        self.assertTrue(layout.verify_layout(original, edited, {"mission_id": 999}, report, terrain=terrain)["passed"])
        for cluster in report["clusters"]:
            if cluster["changed"]:
                self.assertGreater(cluster["after_aligned_pairs"], cluster["before_aligned_pairs"])
                self.assertTrue(cluster["topology"]["original_mineral_approach_components_preserved"])
        self.assertTrue(all(move["displacement_pixels"] <= 64 for move in report["moves"]))
        self.assertEqual(layout.plan_layout(original, {"mission_id": 999}, terrain=terrain), report)

    def test_preserves_amount_owner_type_order_and_nonmineral_records(self):
        original, terrain = fixture(points=((160, 80), (192, 112), (256, 112), (160, 144), (224, 144), (256, 176)),
                                    amounts=[125, 250, 500, 1500, 1000, 750], extra=[unit(400, 400, 188, 5000), unit(420, 64, 0, 0, 0)])
        edited = deepcopy(original)
        report = layout.apply_layout(edited, terrain=terrain)
        self.assertGreater(report["moved_count"], 0)
        old, new = original.getsection("UNIT"), edited.getsection("UNIT")
        self.assertEqual(len(old), len(new))
        for start in range(0, len(old), 36):
            self.assertEqual(old[start:start + 4], new[start:start + 4])
            self.assertEqual(old[start + 8:start + 36], new[start + 8:start + 36])
        self.assertEqual(old[6 * 36:], new[6 * 36:])

    def test_layout_preserves_every_previously_resource_clear_depot_grid_position(self):
        chk, terrain = fixture(points=((160, 80), (192, 112), (256, 112), (160, 144), (224, 144), (256, 176)))
        before = list(map(layout._info, layout._records(chk)))
        report = layout.apply_layout(chk, terrain=terrain)
        self.assertGreater(report["moved_count"], 0)
        import resource_depot_placement as depot
        after = list(map(layout._info, layout._records(chk)))
        for unit_type in (106, 131, 154):
            self.assertEqual(depot.newly_blocked_depot_tiles(before, after, unit_type, (16, 16)), [])
        self.assertTrue(report["resource_depot_placement"]["all_original_resource_clear_grid_positions_preserved"])
        self.assertEqual(report["resource_depot_placement"]["newly_blocked_tile_count"], 0)

    def test_strict_verifier_rejects_resource_owner_type_and_count_tampering(self):
        chk, _ = fixture()
        before = chk.getsection("UNIT")
        for offset in (8, 16, 20, 35):
            with self.subTest(offset=offset):
                after = bytearray(before)
                after[offset] ^= 1
                with self.assertRaises(ValueError):
                    layout.verify_only_mineral_coordinates(before, after)
        with self.assertRaises(ValueError):
            layout.verify_only_mineral_coordinates(before, before + bytes(36))
        mobile = unit(96, 96, 0, 0, 0)
        moved = bytearray(mobile)
        struct.pack_into("<HH", moved, 4, 128, 96)
        with self.assertRaises(ValueError):
            layout.verify_only_mineral_coordinates(mobile, moved)

    def test_low_resource_or_explicit_protection_freezes_complete_cluster(self):
        for options, keywords, reason in (({"amounts": [1500, 100, 1500, 1500]}, {}, "potential_special_or_mine_out_resource"),
                                          ({}, {"protected_indices": [2]}, "protected_original_script_or_resource")):
            chk, terrain = fixture(**options)
            before = chk.save()
            report = layout.apply_layout(chk, terrain=terrain, **keywords)
            self.assertEqual(before, chk.save())
            self.assertEqual(report["clusters"][0]["reason"], reason)

    def test_possible_mining_gate_is_frozen_before_row_cleanup(self):
        points = ((256, 208), (256, 240), (256, 272), (256, 304))
        chk, _ = fixture(points=points)
        walk = [bytearray(64) for _ in range(64)]
        for y in range(24, 40):
            walk[y][:] = b"\x01" * 64
        report = layout.plan_layout(chk, terrain=(walk, {"test": "mineral wall across corridor"}))
        self.assertFalse(report["changed"])
        self.assertEqual(report["clusters"][0]["reason"], "potential_mining_route_gate")

    def test_cannot_enter_reserved_wave_cells(self):
        chk, terrain = fixture()
        reserved = [(x, y) for x in range(96, 321, 16) for y in range(48, 241, 16)]
        report = layout.plan_layout(chk, terrain=terrain, reserved_points=reserved)
        self.assertFalse(report["changed"])
        self.assertEqual(report["reserved_points"], [list(p) for p in sorted(set(reserved))])

    def test_candidate_requires_entire_64_by_32_terrain_footprint(self):
        chk, terrain = fixture()
        walk = terrain[0]
        # None of the mineral footprints is terrain-placeable.  Testing full
        # footprints (rather than only centres) must reject every candidate.
        for y in range(64):
            for x in range(64):
                walk[y][x] = int(x % 4 == 0 and y % 4 == 2)
        report = layout.plan_layout(chk, terrain=terrain)
        self.assertFalse(report["changed"])

    def test_normalized_location_membership_includes_footprints(self):
        chk, _ = fixture(regions=[(176, 80, 208, 192), (208, 192, 176, 80)])
        info = [(160, 112, 176, 11)]
        geometry, _ = layout.load_unit_geometry()
        # Both centres are outside this rectangle; the original footprint
        # intersects it, and the moved footprint does not.
        self.assertFalse(layout._same_location_membership(chk, info, [(128, 112, 176, 11)], [0], {1, 2}, geometry))

    def test_compact_block_cannot_replace_open_mineral_edges(self):
        chk, terrain = fixture()
        before = list(map(layout._info, layout._records(chk)))
        after = [(160, 144, 176, 11), (224, 144, 177, 11), (160, 176, 178, 11), (224, 176, 176, 11)]
        geometry, _ = layout.load_unit_geometry()
        okay, proof = layout._topology_check(before, after, list(range(4)), terrain[0], geometry)
        self.assertFalse(okay)
        self.assertEqual(proof["reason"], "exterior_mineral_approach_reduced")

    def test_terran_eight_large_field_does_not_become_nineteen_mineral_brick(self):
        source = layout.SOURCE_ROOT / "locales/koKR/Assets/campaign/Terran/Terran09/staredit/scenario.chk"
        chk = CHK(source.read_bytes())
        before = chk.getsection("UNIT")
        report = layout.apply_layout(chk, {"mission_id": 108})
        large = [c for c in report["clusters"] if c["mineral_count"] == 19]
        self.assertTrue(large)
        for cluster in large:
            self.assertFalse(cluster["changed"])
            self.assertEqual(cluster["reason"], "group_size_outside_conservative_range")
            for i in cluster["unit_indices"]:
                self.assertEqual(before[i * 36:(i + 1) * 36], chk.getsection("UNIT")[i * 36:(i + 1) * 36])

    def test_new_templates_leave_worker_aisles_between_short_rows(self):
        for target, shape in layout._templates([(160, 112), (256, 144), (160, 176), (224, 176)]):
            self.assertLessEqual(shape["rows"], 2)
            if shape["rows"] > 1:
                footprint = 64 if shape["kind"] == "short_columns" else 32
                self.assertGreaterEqual(shape["row_spacing_pixels"] - footprint, 32)

    def test_stock_geometry_matches_resource_and_headquarters_foundations(self):
        geometry, proof = layout.load_unit_geometry()
        self.assertEqual(geometry[176], (32, 16, 32, 16))
        self.assertEqual(geometry[177], geometry[176])
        self.assertEqual(geometry[178], geometry[176])
        self.assertEqual(geometry[106], (64, 48, 64, 48))
        self.assertEqual(proof["sha256"], "da2ee6f116b77329048ec6be9e02721a527fde23d4b05b1b1336e634490abcba")


if __name__ == "__main__":
    unittest.main()
