"""Curve geometry and real-map preservation, without game or player records."""
import math
import unittest
from sc1.native_campaign import ladder_resource_layout as ladder
from sc1.tests import test_resource_layout as fixtures


class LadderResourceTests(unittest.TestCase):
    def test_one_gas_keeps_one_side_two_gases_keep_both_sides(self):
        anchor = {'center': (1024, 1024)}
        for count in (3, 10, 13, 25, 36):
            for direction in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                for gases in (0, 1, 2):
                    choices = list(ladder.formations(count, gases, anchor, direction))
                    self.assertTrue(choices)
                    for minerals, gas, shape in choices:
                        self.assertEqual(len(set(minerals)), count)
                        self.assertEqual(len(gas), gases)
                        self.assertTrue(all(math.dist(p, anchor['center']) <= 560 for p in minerals))
                        self.assertGreaterEqual(shape['central_army_aisle_pixels'], 64)
                        if gases == 2:
                            axis = 1 if direction[0] else 0
                            self.assertLess((gas[0][axis]-1024)*(gas[1][axis]-1024), 0)

    def test_real_terran_main_uses_joint_curve_with_original_gas_count(self):
        # Reuse the real-map fixture, including its independent front-access audit.
        fixtures.ResourceLayoutTests.setUpClass()
        report = fixtures.ResourceLayoutTests.report
        center = next(f['anchor']['center'] for f in report['clusters'] if f['anchor'].get('unit_index') == 160)
        main = next(b for b in report['ladder_bases'] if b['anchor'] == center)
        self.assertEqual(main['status'], 'joint_ladder_arc')
        self.assertEqual(len(main['mineral_positions']), 10)
        self.assertEqual(len(main['gas_positions']), 1)
        self.assertEqual(report['functional_geyser_count'], report['geyser_count'])


if __name__ == '__main__':
    unittest.main()
