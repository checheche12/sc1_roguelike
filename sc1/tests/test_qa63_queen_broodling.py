import unittest
from sc1.campaign.runtime_catalog import load_catalog
from sc1.campaign import legend_focus,legendary_expansion
import copy

class QueenBroodling(unittest.TestCase):
 def test_current_effects_and_frozen_source(self):
  c=load_catalog(expected_version=2);q=c['talents'][342];ling=c['talents'][428]
  self.assertEqual(q['effect_ordinal'],104)
  self.assertEqual([q['effect'][x] for x in ('broodlings_per_target','additional_cast_targets','additional_cast_radius_pixels','broodling_energy_cost')],[6,3,128,100])
  self.assertIn('100',q['description']);self.assertIn('24',q['description']);self.assertIn('2배',q['description'])
  self.assertEqual(ling['effect']['focus_target_units'],[37,40,54]);self.assertEqual(ling['effect']['armor_erosion_per_hit'],0.33)
  self.assertIn('브루들링',ling['description']);self.assertNotIn('100',q['source_description'])
 def test_source_decorators_retain_queen_cost_and_broodling_focus(self):
  c=copy.deepcopy(load_catalog(expected_version=2));legendary_expansion.decorate(c);legend_focus.decorate(c)
  q=c['talents'][342];ling=c['talents'][428]
  self.assertEqual(q['effect']['broodling_energy_cost'],100);self.assertEqual(q['effect']['additional_cast_targeting'],'native_weapon_flags');self.assertIn('에너지 소모 100',q['description'])
  self.assertEqual(ling['effect']['focus_target_units'],[37,40,54]);self.assertIn('브루들링',ling['description'])
if __name__=='__main__':unittest.main()
