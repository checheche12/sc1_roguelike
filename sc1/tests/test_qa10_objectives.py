"""Source trigger checks for Z06 base clear and reviewed vision coverage."""
from pathlib import Path
import struct
import unittest
from sc1.native_campaign import build_all_campaigns as b,campaign_objectives as objectives
from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine,cs


class Qa10ObjectivesTests(unittest.TestCase):
    def fixture(self):
        spec=next(x for x in b.roster_specs() if x['mission_id']==206)
        path=b.SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path']
        source=b.CHK(path.read_bytes());row=b.metadata(spec,source,path)
        output=b.CHK(source.save());receipt=objectives.apply(output,row)
        progression=b.patch_progression(output,row)
        return source,output,row,receipt,progression

    def test_z06_buildings_finish_without_mobile_units_or_tassadar_visit(self):
        source,output,row,receipt,p=self.fixture();route=p['routes'][0]
        latch=b.triggers(output)[route['goal_trigger_index']]
        machine=OrdinaryTriggerMachine();machine.satisfy(cs(latch))
        machine.values[2,19,229,0,0]=100;machine.values[2,17,79,0,0]=1
        self.assertTrue(machine.run(latch))
        ending=b.triggers(output)[route['ending_trigger_index']]
        self.assertFalse(machine.run(ending));machine.switches[242]=machine.switches[243]=True
        self.assertTrue(machine.run(ending));self.assertTrue(machine.victory)
        self.assertEqual([a[26] for _,a in b.actions(ending)],[1])
        self.assertTrue(receipt['final_cinematic_removed'])
        self.assertFalse(receipt['mobile_units_required']);self.assertFalse(receipt['tassadar_encounter_required'])

    def test_any_remaining_building_or_dead_kerrigan_prevents_win(self):
        _,output,row,_,p=self.fixture();latch=b.triggers(output)[p['routes'][0]['goal_trigger_index']]
        machine=OrdinaryTriggerMachine();machine.satisfy(cs(latch))
        machine.values[2,19,231,0,0]=1;self.assertFalse(machine.run(latch))
        machine.values[2,19,231,0,0]=0;machine.values[2,row['owner'],51,0,0]=0
        self.assertFalse(machine.run(latch))

    def test_objective_text_append_and_obsolete_transition_disabled(self):
        source,output,_,receipt,p=self.fixture()
        old=b.strings(source.getsection('STR '));new=b.strings(output.getsection('STR '))
        self.assertEqual(new[:len(old)],old)
        self.assertIn('프로토스 건물 모두 파괴',new[receipt['objective_string_id']-1].decode('utf8'))
        transition=b.triggers(output)[p['original_trigger_indices'][2]]
        self.assertEqual(cs(transition)[0][15],23)
        for index in (0,6):self.assertEqual(b.triggers(output)[p['original_trigger_indices'][index]],b.triggers(source)[index])

    def test_all_direct_global_building_victories_and_reviewed_chains_have_vision(self):
        for spec in b.roster_specs():
            path=b.SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path'];source=b.CHK(path.read_bytes())
            for t in b.triggers(source):
                if any(a[26]==1 for _,a in b.actions(t)) and any(b.cf(c)['type']==2 and b.cf(c)['unit']==231 and b.cf(c)['amount']==0 for _,c in b.conditions(t)):
                    self.assertIn(spec['mission_id'],objectives.FULL_VISION_MISSIONS)
        self.assertTrue({203,206,604,614,615,616,617,618,609,610}<=objectives.FULL_VISION_MISSIONS)
        self.assertFalse({101,104,205,209,401,502,507,611}&objectives.FULL_VISION_MISSIONS)
