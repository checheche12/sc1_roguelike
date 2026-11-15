"""Execute the repaired ordinary trigger on movable actors, without a game."""
import copy
import struct
import unittest
from sc1.native_campaign import build_all_campaigns as b, campaign_objectives


class FinalHiveTests(unittest.TestCase):
    def setUp(self):
        spec=next(x for x in b.roster_specs() if x['mission_id']==601)
        source=b.SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path']
        self.chk=b.CHK(source.read_bytes())
        self.before=b.triggers(self.chk)
        self.row=b.metadata(spec,self.chk,source)
        self.result=campaign_objectives.apply(self.chk,self.row)
        self.repair=b.triggers(self.chk)[-1]

    def run_trigger(self,trigger,actors,final):
        for _,c in b.conditions(trigger):
            if c[15]==11 and (c[16]!=16 or not final):return
        for _,a in b.actions(trigger):
            loc,_,_,_,owner,_,unit,kind,modifier,_,_,_=struct.unpack('<IIIIIIHBBBBH',a)
            if kind!=43:continue
            left,top,right,bottom=struct.unpack_from('<4I',self.chk.getsection('MRGN'),(loc-1)*20)
            for actor in actors:
                if (owner==17 or actor['owner']==owner) and (unit==229 or unit==230 and actor['unit']<106 or actor['unit']==unit):
                    if left<=actor['x']<=right and top<=actor['y']<=bottom:
                        actor['invincible']=modifier!=5

    def test_final_release_repairs_returning_and_late_created_hostiles(self):
        actors=[dict(unit=37,owner=5,x=1180,y=3070,invincible=True),
                dict(unit=38,owner=5,x=1200,y=3080,invincible=True)]
        self.run_trigger(self.before[51],actors,True)
        self.assertTrue(all(x['invincible'] for x in actors))
        for actor in actors:actor.update(x=2180,y=3800)
        self.run_trigger(self.repair,actors,True)
        self.assertTrue(all(not x['invincible'] for x in actors))
        actors.append(dict(unit=38,owner=4,x=2050,y=3100,invincible=True))
        self.run_trigger(self.repair,actors,True)
        self.assertFalse(actors[-1]['invincible'])
        self.assertIn(3,[a[26] for _,a in b.actions(self.repair)])

    def test_early_stage_buildings_and_other_factions_remain_protected(self):
        actors=[dict(unit=u,owner=p,x=2208,y=3856,invincible=True)
                for u,p in [(37,5),(133,1),(133,3),(134,5),(37,3),(38,0)]]
        expected=copy.deepcopy(actors)
        self.run_trigger(self.repair,actors,False)
        self.assertEqual(actors,expected)
        self.run_trigger(self.repair,actors,True)
        self.assertFalse(actors[0]['invincible'])
        self.assertEqual(actors[1:],expected[1:])

    def test_original_events_and_victory_save_gate_are_preserved(self):
        self.assertEqual(b.triggers(self.chk)[:-1],self.before)
        progress=b.patch_progression(self.chk,self.row)
        route=next(x for x in progress['routes'] if x['source_trigger']==59)
        ending=b.triggers(self.chk)[route['ending_trigger_index']]
        switches={c[16] for _,c in b.conditions(ending) if c[15]==11}
        self.assertTrue({242,243}<=switches)


if __name__=='__main__':unittest.main()
