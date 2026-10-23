"""The real Protoss09 terrain, refinery collision, and new-base timings."""
import struct
import unittest
from pathlib import Path
from sc1.campaign.missions import load_missions
from sc1.native_campaign import build_all_campaigns as maps
from sc1.native_campaign import settlement_terrain as terrain
from sc1.native_campaign import mining_layout_audit as mining
from sc1.native_campaign import resource_layout as resources
from sc1.native_campaign.build_rework_wave_profiles import derive


class SettlementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mission=next(m for m in load_missions() if m['mission_id']==309)
        cls.before=maps.CHK(Path(cls.mission['source']).read_bytes())
        cls.after=maps.CHK(cls.before.save())
        cls.report=terrain.apply(cls.after,cls.mission)

    def test_only_bounded_hill_and_decorations_change(self):
        self.assertGreater(len(self.report['changed_tiles']),100)
        self.assertEqual(self.before.order,self.after.order)
        for tag in self.before.order:
            if tag.decode() not in terrain.TAGS:self.assertEqual(self.before.sections[tag],self.after.sections[tag],tag)
        terrain.verify(self.before,self.after,self.mission,self.report)
        x1,y1,x2,y2=terrain.BOUNDS
        cv5,vf4=mining._terrain_bytes(4)
        before=struct.unpack('<16384H',self.before.getsection('MTXM'))
        after=struct.unpack('<16384H',self.after.getsection('MTXM'))
        for y in range(128):
            for x in range(128):
                if x1<=x<x2 and y1<=y<y2:
                    self.assertTrue(all((f&7)==1 for f in terrain._tile_flags(after[y*128+x],cv5,vf4)))
                else:self.assertEqual(before[y*128+x],after[y*128+x])
        again=maps.CHK(self.after.save());terrain.apply(again,self.mission)
        self.assertEqual(again.save(),self.after.save())

    def test_refinery_southern_exit_connects_to_settlement(self):
        # Current settlement layout: a Nexus at(352,3888), gas at(576,3872).
        # Test the smaller built Assimilator, which exposes the trapped pocket.
        info=[(352,3888,154,7),(576,3872,157,7)]
        labels,_=mining.worker_components(self.after,info)
        main=mining._perimeter_labels(info[0],labels)
        exits=mining._perimeter_labels(info[1],labels)
        self.assertEqual(len(main),1)
        self.assertEqual(exits,main)
        self.assertIn(labels[3920//8][576//8],main)

    def test_no_other_mission_terrain_changes(self):
        for mission in load_missions():
            if mission['mission_id']==309:continue
            chk=maps.CHK(Path(mission['source']).read_bytes());raw=chk.save()
            self.assertIsNone(terrain.apply(chk,mission));self.assertEqual(chk.save(),raw)

    def test_new_base_missions_start_at_360_seconds(self):
        affected=[]
        for profile in derive():
            if profile['enabled'] and not profile['starting_headquarters']:
                affected.append(profile['mission_id']);self.assertEqual(profile['normal_first_seconds'],360)
            elif profile['enabled']:self.assertIn(profile['normal_first_seconds'],range(240,301,10))
            else:self.assertEqual(profile['normal_first_seconds'],360)
            self.assertEqual(profile['normal_interval_seconds'],120)
        self.assertEqual(affected,[105,106,207,301,304,309,402,404,503,506,602,603,605])


if __name__=='__main__':unittest.main()
