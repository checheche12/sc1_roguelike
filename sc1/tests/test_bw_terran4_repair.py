"""Korhal silo relocation, destruction route, and real-map collision regressions."""
import json
import struct
import unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as b,terran4_repair as repair
from sc1.native_campaign import mineral_layout as geo,scripted_openings,base_defenses
from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine,cs

ROOT=Path(__file__).resolve().parents[2]


class Terran4RepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=next(r for r in json.loads(b.RECEIPT.read_text(encoding='utf8'))['maps'] if r['mission_id']==504)
        cls.fixed=b.CHK(Path(cls.report['output']).read_bytes())
        cls.source=b.CHK(Path(cls.report['source']).read_bytes())
        # Reconstruct the three verified 1.0.12 blockers from ordinary records;
        # a fresh checkout/build does not need an archived development folder.
        cls.old=b.CHK(cls.source.save())
        blockers=[base_defenses.record(u,1,x,y,900000+i) for i,(u,x,y) in enumerate(
            ((124,3136,3552),(124,3296,3552),(0,3428,3588)))]
        cls.old.setsection('UNIT',cls.old.getsection('UNIT')+b''.join(blockers))
        cls.ts=b.triggers(cls.fixed)
        cls.progress=cls.report['progression']
        cls.route=next(r for r in cls.progress['routes'] if r['route']==2)
        cls.latch=cls.ts[cls.route['goal_trigger_index']]
        cls.ending=cls.ts[cls.route['ending_trigger_index']]
        cls.correction=cls.progress['objective_correction']
        cls.seen=cls.ts[cls.progress['original_trigger_indices'][cls.correction['seen_trigger']]]

    def machine(self,count=6):
        engine=OrdinaryTriggerMachine()
        engine.values[2,1,108,0,0]=count
        return engine

    def test_original_buildings_and_silo_move_actions_preserved(self):
        original=b.units(self.source);fixed=b.units(self.fixed)
        for i,unit in enumerate(original):
            if b.unit_info(unit)[2] not in (110,149,157,176,177,178,188):self.assertEqual(unit,fixed[i])
        self.assertEqual(sum(b.unit_info(r)[2]==108 for r in fixed),6)
        self.assertIn(b.triggers(self.source)[8],self.ts)
        self.assertEqual(self.source.getsection('MRGN'),self.fixed.getsection('MRGN'))
        self.assertEqual(self.source.getsection('MTXM'),self.fixed.getsection('MTXM'))

    def test_old_added_turrets_obstruct_silos_fixed_destinations_are_empty(self):
        boxes,_=geo.load_unit_geometry();old_info=list(map(b.unit_info,b.units(self.old)))
        blocked=[]
        for x,y in repair.destination_centers(self.old):
            rect=geo._rect(x,y,108,boxes)
            blocked.extend((i,u) for i,(xx,yy,u,_) in enumerate(old_info)
                           if u!=214 and geo._overlap(rect,geo._rect(xx,yy,u,boxes)))
        self.assertEqual(sum(i>=456 and u==124 for i,u in blocked),2)
        repair.verify_silo_destinations(self.fixed)
        for record in b.units(self.fixed)[456:]:
            x,y,u,_=b.unit_info(record)
            if u not in (176,177,178,188):
                self.assertTrue(scripted_openings.additional_spawn_allowed({'mission_id':504},x,y))

    def test_no_empty_start_or_remaining_silo_can_trigger_success(self):
        empty=self.machine(0)
        self.assertFalse(empty.run(self.seen))
        self.assertFalse(empty.run(self.latch))
        engine=self.machine()
        self.assertTrue(engine.run(self.seen))
        for remaining in (6,5,4,3,2,1):
            engine.values[2,1,108,0,0]=remaining
            self.assertFalse(engine.run(self.latch))
            self.assertFalse(engine.run(self.ending))

    def test_destroyed_silos_finish_even_when_original_move_initialization_failed(self):
        engine=self.machine()
        self.assertTrue(engine.run(self.seen))
        engine.values[2,1,108,0,0]=0
        self.assertFalse(engine.switches.get(1,False))
        self.assertFalse(engine.run(b.triggers(self.source)[22]))
        self.assertTrue(engine.run(self.latch))
        self.assertEqual(engine.deaths[11,223],2)
        self.assertTrue(engine.switches[b.SWITCHES['goal']])
        self.assertFalse(engine.run(self.ending))
        engine.switches[b.SWITCHES['growth_ready']]=True
        self.assertFalse(engine.run(self.ending))
        engine.switches[b.SWITCHES['ack']]=True
        self.assertTrue(engine.run(self.ending))
        self.assertTrue(engine.victory)
        self.assertEqual(b.strings(self.fixed.getsection('STR '))[engine.next_scenario-1],b'Terran05b.scx')
        self.assertFalse(engine.run(self.latch))

    def test_physics_lab_route_and_original_victory_actions_remain(self):
        source=b.triggers(self.source)
        for route in self.progress['routes']:
            self.assertEqual(self.ts[route['ending_trigger_index']][320:],source[route['source_trigger']][320:])
        physics=next(r for r in self.progress['routes'] if r['route']==1)
        self.assertEqual(cs(self.ts[physics['goal_trigger_index']])[:-1],cs(source[4]))

    def test_every_new_wave_cell_has_building_clear_route_and_original_enemy_anchor(self):
        grid=repair.route_grid(self.fixed)
        connected,_=b.connected_cells(grid,self.report['difficulty']['wave_origins'][0]['target'])
        original=list(map(b.unit_info,b.units(self.source)))
        self.assertEqual([o['owner'] for o in self.report['difficulty']['wave_origins']],[0,0,1,1])
        for origin in self.report['difficulty']['wave_origins']:
            self.assertIn((*origin['center'],origin['source_unit'],origin['owner']),original)
            self.assertGreaterEqual(len(origin['cells']),4)
            for x,y in origin['cells']:
                self.assertTrue(connected[y//8][x//8],(origin['center'],x,y))
                self.assertTrue(scripted_openings.additional_spawn_allowed({'mission_id':504},x,y))
                if origin['owner']==0:self.assertGreaterEqual(y,origin['north_barracks_front_y'])
            self.assertLessEqual(sum((a-bb)**2 for a,bb in zip(origin['target'],origin['player_base_target'])),256**2)
        # The old east-side pocket fails after buildings are accounted for.
        old_cells=((4052,692),)
        self.assertTrue(all(not connected[y//8][x//8] for x,y in old_cells))


if __name__=='__main__':unittest.main()
