"""Worker lanes and parent/addon landing footprints are independent guards."""
import unittest
from sc1.native_campaign import main_base_gas as gas,addon_placement as addons

class GasMiningAndAddonsTests(unittest.TestCase):
    def test_worker_route_rejects_mineral_barrier(self):
        boxes,_=gas.rules.geometry.load_unit_geometry();worker=[bytearray([1])*128 for _ in range(128)]
        anchor=dict(center=[320,320],depot_type=131)
        info=[(320,320,131,0),(640,320,188,11),(480,320,176,11)]
        self.assertFalse(gas.direct_lane(anchor,(640,320),info,1,worker,boxes))
        self.assertTrue(gas.direct_lane(anchor,(320,512),info,1,worker,boxes))

    def test_existing_parent_reserves_full_addon_tiles(self):
        reserved=addons.reservations([(320,336,113,0)])
        self.assertIn((256,288,384,384),reserved)
        self.assertIn((384,320,448,384),reserved)
        self.assertFalse(addons.resource_clear((416,352),188,reserved))
        self.assertTrue(addons.resource_clear((160,512),188,reserved))

    def test_orphan_addon_reserves_matching_parent_landing(self):
        for unit,parent in addons.ADDONS.items():
            with self.subTest(addon=unit):
                reserved=addons.reservations([(416,352,unit,11)])
                self.assertIn((256,288,384,384),reserved)
                self.assertFalse(addons.resource_clear((320,336),188,reserved))

    def test_every_liftable_addon_parent_is_guarded(self):
        for unit in (106,113,114,116):
            with self.subTest(parent=unit):
                reserved=addons.reservations([(320,336,unit,0)])
                self.assertFalse(addons.resource_clear((416,352),188,reserved))

if __name__=='__main__':unittest.main()
