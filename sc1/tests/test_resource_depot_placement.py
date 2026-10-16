"""Resource-depot exclusion boundaries and preservation regressions."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sc1.native_campaign import resource_depot_placement as depot
from sc1.native_campaign.build_plain_chk import CHK


def chk_for_size(width=32, height=32):
    body = struct.pack('<HH', width, height)
    return CHK(struct.pack('<4sI', b'DIM ', len(body)) + body)


def oracle(info, tile, depot_type):
    """Literal per-footprint-tile search, independent of envelope arithmetic."""
    resources, sizes, collision, _ = depot._stock_geometry()
    tx, ty = tile
    width, height = sizes[depot_type]
    for y in range(ty, ty + height // 32):
        for x in range(tx, tx + width // 32):
            a, b, c, d = 32 * (x - 3), 32 * (y - 3), 32 * (x + 4), 32 * (y + 4)
            for px, py, unit, _ in info:
                if unit not in resources:
                    continue
                left, top, right, bottom = collision[unit]
                if px - left < c and px + right >= a and py - top < d and py + bottom >= b:
                    return True
    return False


class ResourceDepotPlacementTests(unittest.TestCase):
    def test_actual_bounds_exact_clearance_boundary(self):
        forbidden = depot.resource_forbidden_tiles([(320, 336, 176, 11)])
        # Resource [288..351,320..351]. Equality at the query's exclusive
        # right/bottom edge is allowed; equality at its left/top is forbidden.
        self.assertNotIn((2, 8), forbidden)
        self.assertIn((3, 8), forbidden)
        self.assertIn((13, 8), forbidden)
        self.assertNotIn((14, 8), forbidden)
        self.assertNotIn((8, 4), forbidden)
        self.assertIn((8, 5), forbidden)
        self.assertIn((8, 13), forbidden)
        self.assertNotIn((8, 14), forbidden)

    def test_pixel_offsets_match_literal_primary_source_loop(self):
        # Off-grid, asymmetric refinery bounds and boundary equality expose
        # incorrect tile-center or symmetric-placement-box approximations.
        for unit in depot.resource_type_ids():
            for px, py in ((320, 336), (319, 335), (321, 337)):
                info = [(px, py, unit, 11)]
                for kind in depot.DEPOT_TYPES:
                    forbidden = depot.resource_forbidden_tiles(info, kind, (24, 24))
                    for ty in range(22):
                        for tx in range(21):
                            self.assertEqual((tx, ty) in forbidden, oracle(info, (tx, ty), kind),
                                             (unit, kind, px, py, tx, ty))

    def test_all_resource_flag_types_include_refineries(self):
        self.assertEqual(depot.resource_type_ids(),
                         frozenset((110, 145, 149, 157, 176, 177, 178, 179, 180, 188)))
        for unit in (110, 149, 157, 188):
            self.assertTrue(depot.resource_forbidden_tiles([(320, 336, unit, 11)]))
        self.assertFalse(depot.resource_forbidden_tiles([(320, 336, 106, 1)]))

    def test_outer_resource_move_is_rejected(self):
        before = [(320, 336, 176, 11)]
        after = [(352, 336, 176, 11)]
        guard = depot.prepare_guard(chk_for_size(), before)
        accepted, proof = guard.check(after)
        self.assertFalse(accepted)
        self.assertGreater(proof['newly_blocked_tile_count'], 0)
        self.assertEqual(depot.newly_blocked_depot_tiles(before, after, map_size=(32, 32)),
                         sorted(depot.resource_forbidden_tiles(after, map_size=(32, 32))
                                - depot.resource_forbidden_tiles(before, map_size=(32, 32))))

    def test_interior_cleanup_under_existing_global_envelope_is_allowed(self):
        points = [(160, 80), (192, 112), (256, 112), (160, 144), (224, 144), (256, 176)]
        before = [(x, y, 176, 11) for x, y in points]
        after = list(before)
        after[1] = (160, 112, 176, 11)
        after[4] = (256, 144, 176, 11)
        accepted, proof = depot.prepare_guard(chk_for_size(), before).check(after)
        self.assertTrue(accepted)
        self.assertEqual(proof['newly_blocked_tile_count'], 0)
        self.assertEqual(proof['changed_resource_count'], 2)

    def test_hint_cannot_omit_an_earlier_sequential_move(self):
        before = [(320, 336, 176, 11), (384, 336, 177, 11)]
        after = [(352, 336, 176, 11), (416, 336, 177, 11)]
        guard = depot.prepare_guard(chk_for_size(), before)
        with self.assertRaisesRegex(ValueError, 'omitted'):
            guard.check(after, [1])
        _, proof = guard.check(after)
        self.assertEqual(proof['changed_resource_count'], 2)

    def test_map_clips_to_complete_depot_footprints(self):
        forbidden = depot.resource_forbidden_tiles([(64, 48, 188, 11)], map_size=(4, 3))
        self.assertEqual(forbidden, frozenset({(0, 0)}))
        self.assertFalse(depot.resource_forbidden_tiles([(64, 48, 188, 11)], map_size=(3, 3)))

    def test_original_t01_cc_is_blocked_by_old_added_gas(self):
        path = ROOT/'sc1/campaign_sources/raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk'
        chk = CHK(path.read_bytes())
        raw = chk.getsection('UNIT')
        original = [(*struct.unpack_from('<HHH', raw, i + 4), raw[i + 16]) for i in range(0, len(raw), 36)]
        self.assertEqual(original[42][:3], (1056, 1744, 106))
        size = struct.unpack('<HH', chk.getsection('DIM '))
        for kind in depot.DEPOT_TYPES:
            self.assertNotIn((31, 53), depot.resource_forbidden_tiles(original, kind, size))
            self.assertIn((31, 53), depot.resource_forbidden_tiles(original + [(1056, 1856, 188, 11)], kind, size))

    def test_resource_identity_changes_fail_closed(self):
        guard = depot.prepare_guard(chk_for_size(), [(320, 336, 176, 11)])
        with self.assertRaises(ValueError):
            guard.check([(320, 336, 188, 11)])
        with self.assertRaises(ValueError):
            guard.check([])


if __name__ == '__main__':
    unittest.main()
