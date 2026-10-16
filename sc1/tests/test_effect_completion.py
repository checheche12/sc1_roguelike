"""Regressions for the all-campaign effects completion pass."""
import unittest
from sc1.campaign.runtime_catalog import load_catalog
from sc1.campaign.build_runtime_catalog import REGULAR_COMBAT_UNITS
from sc1.native_campaign.build_objective_guards import derive

class EffectCompletionTests(unittest.TestCase):
    def test_expanded_curses_describe_native_targets_and_keep_legacy_contract(self):
        catalog=load_catalog();damage,hp=catalog['curses'][1:3]
        self.assertEqual(hp['effect']['units'],REGULAR_COMBAT_UNITS)
        self.assertTrue({0,37,38,40,50,65,70}.issubset(damage['effect']['units']))
        self.assertNotIn(84,damage['effect']['units']) # Observer has no weapon.
        self.assertTrue({0,35,38,64}.issubset(damage['effect']['weapons']))
        for item in (damage,hp):
            self.assertEqual(item['legacy_effect']['units'],[37,38])
            self.assertEqual(item['effect']['owner_scope'],'hostile_only')
            self.assertTrue(item['effect']['exclude_hallucinations'])
            self.assertEqual(item['target_units'],item['effect']['units'])

    def test_original_mission_survivors_do_not_include_training_or_army_quotas(self):
        guarded,sources=derive()
        self.assertEqual(len(sources),63)
        self.assertEqual(guarded,[
            {'mission_id':608,'unit_id':61,'owner':1,'x':976,'y':1949},
            {'mission_id':608,'unit_id':61,'owner':1,'x':926,'y':2064}])
        self.assertTrue(all(len(s['sha256'])==64 for s in sources))

if __name__=='__main__':unittest.main()
