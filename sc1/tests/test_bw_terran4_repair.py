"""Korhal silo relocation, destruction route, and real-map collision regressions."""
import json
import struct
import unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as b,terran4_repair as repair
from sc1.native_campaign import mineral_layout as geo,scripted_openings,base_defenses
from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine,cs

ROOT=Path(__file__).resolve().parents[2]


class SiloOpeningMachine(OrdinaryTriggerMachine):
    """CHK unit/region fixture including addon neutralization, not a game engine.

    Execute the stock opening's Remove Unit, Wait and Move Unit actions in
    order. Bring counts use live unit rectangles, including neutral addons.
    Combat, collision resolution, AI and asynchronous waits are not emulated.
    """
    def __init__(self,chk):
        super().__init__()
        self.chk=chk
        self.units=[list(b.unit_info(u)) for u in b.units(chk)]
        self.boxes,_=geo.load_unit_geometry()

    def in_location(self,unit,location):
        bounds=struct.unpack_from('<4I',self.chk.getsection('MRGN'),(location-1)*20)
        return geo._overlap(geo._rect(*unit[:3],self.boxes),bounds)

    def matching(self,player,kind,location=0):
        return [u for u in self.units if (player==17 or u[3]==(6 if player==13 else player))
                and (u[2]==kind or kind==231 and 106<=u[2]<176)
                and (not location or self.in_location(u,location))]

    def condition(self,c):
        loc,p,n,u,op,kind,extra,flags,mask=self.unpack(c)
        if kind in (2,3):return self.compare(len(self.matching(p,u,loc if kind==3 else 0)),n,op)
        return super().condition(c)

    def opening_steps(self,trigger):
        yield 'loaded'
        for _,a in b.actions(trigger):
            loc,text,wav,time,p,value,u,kind,mod,flags,pad,mask=struct.unpack('<IIIIIIHBBBBH',a)
            if kind==47:continue # Editor comment, no game effect.
            if kind==25:
                for parent in self.matching(p,u,loc):
                    # These six stock CC/addon pairs are 96px/16px apart.
                    for addon in self.matching(parent[3],108):
                        if addon[:2]==[parent[0]+96,parent[1]+16]:addon[3]=11
                    self.units.remove(parent)
                yield 'parents_removed_addons_neutral'
            elif kind==4:
                self.clock_ms+=time
                yield 'opening_wait'
            elif kind==39:
                left,top,right,bottom=struct.unpack_from('<4I',self.chk.getsection('MRGN'),(value-1)*20)
                moving=self.matching(p,u,loc)
                assert len(moving)==1,(loc,moving)
                moving[0][:2]=[(left+right)//2,(top+bottom)//2]
                yield 'moved_to_'+str(value)
            else:raise AssertionError(('Unexpected opening action',kind))


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
        cls.objective=[cls.ts[cls.progress['original_trigger_indices'][i]] for i in range(9,22)]

    def machine(self,relocated=False):
        engine=SiloOpeningMachine(self.fixed)
        if relocated:
            list(engine.opening_steps(b.triggers(self.source)[8]))
            self.objective_pass(engine)
        return engine

    def objective_pass(self,engine):
        for t in self.objective:engine.run(t)

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

    def test_original_objective_bytes_preserved_without_enemy_count_shortcut(self):
        original=b.CHK(self.source.save());before=original.getsection('TRIG')
        repair.correct_objective(original,{'mission_id':504,'owner':6})
        self.assertEqual(original.getsection('TRIG'),before)
        self.assertEqual(cs(self.latch)[:-1],cs(b.triggers(self.source)[22]))
        for i in range(8,22):
            self.assertEqual(self.ts[self.progress['original_trigger_indices'][i]],b.triggers(self.source)[i])

    def test_startup_neutralization_wait_and_every_move_cannot_win(self):
        engine=self.machine()
        engine.switches[b.SWITCHES['growth_ready']]=True
        engine.switches[b.SWITCHES['ack']]=True
        for step in engine.opening_steps(b.triggers(self.source)[8]):
            with self.subTest(step=step):
                self.objective_pass(engine)
                self.assertEqual(len(engine.matching(17,108)),6)
                self.assertFalse(engine.run(self.latch))
                self.assertFalse(engine.run(self.ending))
                self.assertFalse(engine.victory)
                if step!='loaded':self.assertEqual(len(engine.matching(1,108)),0)
        self.assertTrue(engine.switches[1])
        self.assertEqual([len(engine.matching(17,108,loc)) for loc in range(46,52)],[1]*6)
        # Reproduce 1.0.13's exact bad condition against surviving neutral silos.
        engine.switches[252]=True
        bad=b.new_trigger([b.switch_condition(0,False),b.switch_condition(252),b.cond(2,1,0,108,10)],
                          [],b.owner_bytes(6))
        self.assertTrue(engine.eligible(bad))
        for _ in range(20):
            self.objective_pass(engine)
            self.assertFalse(engine.run(self.latch))

    def test_empty_or_incompletely_initialized_world_does_not_win(self):
        for missing in range(7):
            engine=self.machine()
            for u in engine.matching(17,108)[:missing]:engine.units.remove(u)
            for _ in range(3):self.objective_pass(engine)
            self.assertFalse(engine.switches.get(1,False))
            self.assertFalse(engine.run(self.latch))

    def test_each_of_six_targets_must_be_destroyed_or_captured(self):
        # Every combination of destruction and player capture is a stock route.
        for capture_mask in range(64):
            engine=self.machine(relocated=True)
            targets=engine.matching(17,108)
            for i,target in enumerate(targets):
                self.assertFalse(engine.run(self.latch),(capture_mask,i))
                if capture_mask&(1<<i):target[3]=6
                else:engine.units.remove(target)
                self.objective_pass(engine)
            self.assertTrue(engine.run(self.latch),capture_mask)
            self.assertEqual(engine.deaths[11,223],2)
            self.assertTrue(engine.switches[b.SWITCHES['goal']])
            self.assertFalse(engine.run(self.ending))
        # An actual completed route still waits for reward readiness and save ACK.
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
