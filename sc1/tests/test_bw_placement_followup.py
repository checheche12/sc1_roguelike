import json,math,struct,unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as maps,mission_placement_fixes as fixes,ladder_resource_banks as banks
from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine,cs

class BroodWarPlacementFollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={r['mission_id']:r for r in json.loads(maps.RECEIPT.read_text('utf8'))['maps']}

    def current(self,mid):
        row=self.rows[mid];chk=maps.CHK(Path(row['output']).read_bytes())
        return row,chk,fixes.units(chk)

    def test_terran3_expansion_is_on_the_lower_plaza(self):
        row,chk,info=self.current(503)
        group=next(g for g in row['ladder_resource_banks']['bases'] if g['parent_site_index']==6)
        heights=banks.terrain_heights(chk)
        self.assertEqual(heights[3728//8][1120//8],1)
        self.assertEqual(heights[3856//8][736//8],0)
        self.assertEqual(group['anchor']['center'],[736,3856])
        self.assertEqual(len(group['mineral_indices']),6)
        self.assertTrue(fixes.verify(chk,{'mission_id':503},row['ladder_resource_banks'])['expansion_on_lower_plaza'])

    def test_supply_depots_and_bunker_leave_direct_mining_lanes(self):
        for mid,indices in ((504,(203,206)),(505,(547,))):
            row,chk,info=self.current(mid);group=row['ladder_resource_banks']['bases'][0]
            for i in indices:
                rect=fixes.addons.rect(info[i][:2],info[i][2]);expanded=(rect[0]-24,rect[1]-24,rect[2]+24,rect[3]+24)
                for p in group['mineral_positions']+group['gas_positions']:
                    self.assertFalse(banks.court._segment_hits(group['anchor']['center'],p,expanded),(mid,i,p))

    def test_terran6_resources_serve_scripted_player_arrival(self):
        row,chk,info=self.current(506);group=next(g for g in row['ladder_resource_banks']['bases'] if g['parent_site_index']==4)
        self.assertEqual(struct.unpack_from('<4I',chk.getsection('MRGN'),13*20),(1248,3456,1376,3552))
        self.assertEqual(group['anchor']['center'],[1312,3504])
        self.assertEqual(info[479],(1248,3088,131,0))
        self.assertLess(max(math.dist(p,[1312,3504]) for p in group['mineral_positions']),300)
        self.assertTrue(banks.rules._resource_clear((1312,3504),info))
        self.assertTrue(fixes.verify(chk,{'mission_id':506},row['ladder_resource_banks'])['passed'])

    def test_zerg3_all_resource_corridors_remain_connected(self):
        row,chk,info=self.current(603)
        result=fixes.mineral_corridors(chk,info,row['ladder_resource_banks']['bases'])
        self.assertEqual(len(result),18);self.assertTrue(all(result))

    def test_all_brood_war_ending_routes_wait_for_save_then_execute(self):
        routes=0
        for mid,row in self.rows.items():
            if mid<400:continue
            chk=maps.CHK(Path(row['output']).read_bytes());triggers=maps.triggers(chk)
            for route in row['progression']['routes']:
                routes+=1;latch=triggers[route['goal_trigger_index']];ending=triggers[route['ending_trigger_index']]
                engine=OrdinaryTriggerMachine();engine.satisfy(cs(latch))
                self.assertFalse(engine.run(ending));self.assertTrue(engine.run(latch))
                # Original conditions may cease to hold during the final choice.
                engine.values.clear()
                self.assertFalse(engine.run(ending))
                engine.switches[maps.SWITCHES['growth_ready']]=True
                self.assertFalse(engine.run(ending))
                engine.switches[maps.SWITCHES['ack']]=True
                self.assertTrue(engine.run(ending),(mid,route));self.assertTrue(engine.victory)
        self.assertGreater(routes,30)

if __name__=='__main__':unittest.main()
