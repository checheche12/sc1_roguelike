"""Offline behavior model for actual difficulty hooks, plus source preservation.

Does not emulate placement physics, AI, combat or native StarCraft execution.
"""
import ast
import json
from pathlib import Path
import struct
import unittest

from sc1.tests.test_original_campaign import CampaignRuntime, CampaignValue, SC1, builder
from sc1.tests.test_official_probe_plugin import number
from sc1.tools import terran01_difficulty as difficulty

CONFIG=json.loads((SC1/'campaign/build/terran01/difficulty.json').read_text(encoding='utf-8'))
HELPER=SC1/'plugins/original_terran01_hard.py'

class HardValue(CampaignValue):
    def __le__(self,other):return self.value <= number(other)

class HardRuntime(CampaignRuntime):
    EUDVariable=HardValue
    P3,P5,P7,AllPlayers=2,4,6,17
    AtMost,Enemy,Ally,Attack,Cleared=1,0,1,0,3

    def __init__(self, growth=False, choices=False):
        self.units=[];self.created=[];self.orders=[];self.pings=[];self.alliances=[];self.elapsed=0;self.global_override=None
        c=builder.make_chk((builder.BUILD/'input.chk').read_bytes())
        self.locations={i+1:list(struct.unpack_from('<4I',c.getsection('MRGN'),i*20)) for i in range(255)}
        for r in difficulty.records(c.getsection('UNIT')):
            x,y,u,p=difficulty.unit_info(r)
            if u != 214:self.units.append({'player':p,'unit':u,'x':x,'y':y})
        settings={'difficulty':str(builder.BUILD/'difficulty.json'),'difficulty_plugin':str(HELPER)}
        if growth:
            settings.update({'talent_catalog':str(builder.TALENT_CATALOG),'talent_plugin':str(builder.TALENT_PLUGIN)})
        if choices:
            settings.update({'choices':str(builder.BUILD/'choices.json'),'choices_plugin':str(builder.CHOICE_PLUGIN)})
        super().__init__(settings)
        self.h=self.plugin.difficulty

    def f_getcurpl(self):return HardValue(self.cp)
    def f_setloc(self,index,*rect):self.locations[index]=list(rect)
    def SetAllianceStatus(self,target,status):
        player=self.cp
        return lambda:self.alliances.append((player,target,status))
    def Switch(self,index,value):
        assert index==255
        return self.switch if value==self.Set else not self.switch
    def compare(self,count,comparison,target):
        if comparison==self.Exactly:return count==target
        if comparison==self.AtLeast:return count>=target
        if comparison==self.AtMost:return count<=target
        raise AssertionError(comparison)
    def matching(self,player,unit):
        return [u for u in self.units if (player==self.AllPlayers or u['player']==player)
                and (unit=='Any unit' or (unit=='Men' and u['unit']<106) or u['unit']==unit)]
    def Bring(self,player,comparison,count,unit,location):
        left,top,right,bottom=self.locations[location]
        found=0
        for u in self.matching(player,unit):
            hx,hy=(64,48) if u['unit']==106 else ((48,32) if u['unit']==109 else (0,0))
            if u['x']+hx>=left and u['x']-hx<=right and u['y']+hy>=top and u['y']-hy<=bottom:found+=1
        return self.compare(found,comparison,count)
    def Command(self,player,comparison,count,unit):
        found=len(self.matching(player,unit))
        if player==self.AllPlayers and self.global_override is not None:found=self.global_override
        return self.compare(found,comparison,count)
    def ElapsedTime(self,comparison,seconds):return self.compare(self.elapsed,comparison,seconds)
    def MinimapPing(self,location):
        rect=tuple(self.locations[location])
        return lambda:self.pings.append((self.cp,rect))
    def CreateUnit(self,count,unit,location,player):
        rect=self.locations[location];assert count==1 and rect[0]==rect[2] and rect[1]==rect[3]
        def action():
            row={'player':player,'unit':unit,'x':rect[0],'y':rect[1]}
            self.units.append(row);self.created.append(row.copy())
        return action
    def Order(self,unit,player,location,order,target):
        value=(unit,player,tuple(self.locations[location]),order,tuple(self.locations[target]))
        return lambda:self.orders.append(value)
    def ready(self):
        self.elapsed=180;self.h['home_seen'] << 1;self.h['home_ticks'] << 1440
    def run(self,count):
        for _ in range(count):self.tick()
    def leave_entry(self):
        for u in self.units:
            if u['player']==6:u['x'],u['y']=1056,1480
    def block_origin(self,index,player=1):
        x,y=CONFIG['origins'][index]['center'];self.units.append({'player':player,'unit':0,'x':x,'y':y})

class DifficultyRuntimeTests(unittest.TestCase):
    def test_start_preserves_resources_cp_and_sides(self):
        r=HardRuntime()
        self.assertEqual((r.cp,r.minerals,r.gas),(7,40,0))
        self.assertIn((6,4,r.Ally),r.alliances);self.assertIn((4,6,r.Ally),r.alliances)
        self.assertIn((1,6,r.Enemy),r.alliances);self.assertEqual(r.created,[])

    def test_never_starts_before_base_arrival_even_after_elapsed_grace(self):
        r=HardRuntime();r.elapsed=9999;r.run(2000)
        self.assertEqual((number(r.h['home_ticks']),number(r.h['active']),r.created),(0,0,[]))

    def test_base_arrival_requires_scv_and_full_grace(self):
        r=HardRuntime();r.elapsed=200
        r.units.append({'player':1,'unit':0,'x':1056,'y':1600});r.tick()
        self.assertEqual(number(r.h['home_seen']),0)
        next(u for u in r.units if u['unit']==7 and u['player']==1).update(x=1056,y=1600)
        r.run(1439);self.assertEqual(number(r.h['pending']),0)
        r.tick();self.assertEqual(number(r.h['pending']),1)
        self.assertEqual(r.created,[])

    def test_elapsed_grace_and_warning_both_required(self):
        r=HardRuntime();r.ready();r.elapsed=179;r.run(10);self.assertEqual(r.pings,[])
        r.elapsed=180;r.tick();self.assertEqual((number(r.h['pending']),len(r.pings)),(1,1))
        r.run(94);self.assertEqual(r.created,[])
        r.tick();self.assertEqual([u['unit'] for u in r.created].count(37),14)
        self.assertEqual([u['unit'] for u in r.created].count(38),2)
        self.assertTrue(all(u['player']==6 for u in r.created))

    def test_allies_near_primary_use_alternate_entry(self):
        r=HardRuntime();r.ready();r.block_origin(0);r.tick()
        self.assertEqual(number(r.h['pending']),2)
        r.run(95);self.assertEqual(len(r.created),16)

    def test_all_blocked_attempt_skips_without_catchup(self):
        r=HardRuntime();r.ready()
        for i in range(4):r.block_origin(i)
        r.tick();self.assertEqual((number(r.h['pending']),number(r.h['due'])),(0,0))
        r.units=[u for u in r.units if not (u['player']==1 and u['unit']==0)]
        r.run(2878);self.assertEqual(r.pings,[])
        r.tick();self.assertEqual(len(r.pings),1)

    def test_proximity_rechecked_after_warning_and_cancelled(self):
        r=HardRuntime();r.ready();r.tick();r.block_origin(0);r.run(95)
        self.assertEqual((r.created,number(r.h['pending']),number(r.h['stage'])),([],0,0))

    def test_occupied_cell_is_skipped_without_moving_original_unit(self):
        r=HardRuntime();r.ready();r.tick();x,y=CONFIG['origins'][0]['cells'][0]
        blocker={'player':11,'unit':176,'x':x,'y':y};r.units.append(blocker);r.run(95)
        self.assertEqual(len(r.created),15);self.assertEqual((blocker['x'],blocker['y']),(x,y))

    def test_compositions_escalate_and_stop_at_sixty(self):
        r=HardRuntime();r.ready()
        for expected in CONFIG['wave_compositions']+[CONFIG['wave_compositions'][-1]]:
            r.units=[u for u in r.units if u['player']!=6];r.h['due'] << 1;r.h['active'] << 1
            before=len(r.created);r.run(96)
            wave=r.created[before:]
            self.assertEqual(([u['unit'] for u in wave].count(37),[u['unit'] for u in wave].count(38)),tuple(expected))
        self.assertEqual(number(r.h['stage']),6)

    def test_unit_hydra_and_global_caps_stop_attempts(self):
        for unit,amount in ((37,71),(38,23)):
            with self.subTest(unit=unit):
                r=HardRuntime();r.ready()
                r.units.extend({'player':6,'unit':unit,'x':1056,'y':1480} for _ in range(amount))
                r.run(100);self.assertEqual((r.pings,r.created),([],[]))
        r=HardRuntime();r.ready();r.global_override=1601;r.run(100);self.assertEqual(r.created,[])

    def test_largest_base_wave_leaves_reservation_for_curse_multiplier(self):
        r=HardRuntime();r.ready();r.h['stage'] << 6
        r.units.extend({'player':6,'unit':37 if i<48 else 38,'x':1056,'y':1480} for i in range(70))
        r.run(96)
        self.assertEqual((len(r.matching(6,'Men')),len(r.matching(6,38))),(130,34))
        r.h['due'] << 1;r.run(96);self.assertEqual(len(r.created),60)

    def test_previous_wave_at_exit_changes_entry_and_orders_only_p7(self):
        r=HardRuntime();r.ready();r.run(96)
        r.h['preference'] << 0;r.h['due'] << 1;r.tick();self.assertEqual(number(r.h['pending']),2)
        r.h['retry'] << 719;r.tick()
        self.assertTrue(r.orders);self.assertTrue(all(row[1]==6 for row in r.orders))

    def test_goal_save_wait_saved_and_error_stop_new_waves(self):
        for state in (1,2,3,4,5):
            with self.subTest(state=state):
                r=HardRuntime();r.ready();r.h['due'] << 1;r.plugin.state << state
                r.switch=True;r.run(100)
                self.assertEqual(r.created,[])
        r=HardRuntime();r.ready();r.plugin.state << 5;r.run(100);self.assertEqual(r.created,[])

class DifficultySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=builder.make_chk(builder.SOURCE.read_bytes())
        cls.converted=builder.make_chk(builder.SOURCE.read_bytes());builder.legacy_to_expansion(cls.converted)
        cls.before=dict(cls.converted.sections);cls.config=difficulty.apply(cls.converted)

    def test_original49_records_exact_plus46_lings_and_one_geyser(self):
        old=self.source.getsection('UNIT');new=self.converted.getsection('UNIT')
        self.assertEqual(new[:len(old)],old)
        extra=difficulty.records(new[len(old):]);self.assertEqual(len(extra),47)
        self.assertTrue(all(difficulty.unit_info(r)[2:]==(37,4) for r in extra[:46]))
        self.assertEqual(difficulty.unit_info(extra[-1])[2:],(188,11))
        self.assertEqual(struct.unpack_from('<I',extra[-1],20)[0],5000)
        serials=[struct.unpack_from('<I',r)[0] for r in difficulty.records(new)]
        self.assertEqual(len(serials),len(set(serials)))

    def test_unlisted_units_and_other_players_restrictions_unchanged(self):
        old=self.before[b'PUNI'];new=self.converted.getsection('PUNI')
        allowed={offset for u in difficulty.TERRAN_UNITS for offset in (228+u,14*228+u)}
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,new)) if i not in allowed))
        for u in difficulty.TERRAN_UNITS:self.assertEqual((new[228+u],new[14*228+u]),(1,0))
        self.assertIn(34,difficulty.TERRAN_UNITS);self.assertIn(58,difficulty.TERRAN_UNITS)
        self.assertFalse({20,60,61,62,63,103,106+22}&set(difficulty.TERRAN_UNITS))

    def test_purchased_research_starts_unresearched_with_normal_maximums(self):
        up=self.converted.getsection('PUPx');tech=self.converted.getsection('PTEx')
        for i,maximum in difficulty.TERRAN_UPGRADES.items():self.assertEqual((up[61+i],up[13*61+i],up[27*61+i]),(maximum,0,0))
        for i in difficulty.TERRAN_TECH:self.assertEqual((tech[44+i],tech[13*44+i],tech[27*44+i]),(1,int(i in difficulty.INNATE_TECH),0))
        self.assertEqual(tech[13*44+34],1)
        for name in ('UNIx','UPGx','TECx'):self.assertEqual(self.converted.getsection(name),self.before[name.encode()])

    def test_only_reserved_locations_and_p7_change(self):
        self.assertEqual(self.converted.getsection('MRGN')[:1280],self.source.getsection('MRGN'))
        for name in ('OWNR','SIDE','FORC'):
            old=self.before[name.encode()];new=self.converted.getsection(name)
            self.assertEqual(old[:6]+old[7:],new[:6]+new[7:])
        self.assertEqual(self.converted.getsection('OWNR')[6],5)
        for name in ('MTXM','MASK','THG2','TRIG','MBRF'):self.assertEqual(self.converted.getsection(name),self.source.getsection(name))

    def test_all_added_combat_positions_and_wave_cells_connected_to_home(self):
        grid,clear=difficulty.load_grid();connected=difficulty.accessible(clear)
        points=[point for row in self.config['static_reinforcements'] for point in row['added']]
        points += [point for origin in self.config['origins'] for point in origin['cells']]
        self.assertEqual(len(points),406)
        self.assertTrue(all((x//8,y//8) in connected for x,y in points))
        for origin in self.config['origins']:
            self.assertEqual(len({tuple(p) for p in origin['cells']}),90)
            self.assertGreater(origin['terrain_route_pixels'],0)

    def test_static_buildings_resources_and_new_geyser_leave_entry_routes_connected(self):
        grid,clear=difficulty.load_grid()
        for r in difficulty.records(self.converted.getsection('UNIT')):
            x,y,u,p=difficulty.unit_info(r)
            if u not in (106,109,176,177,178,188):continue
            hx,hy=(64,48) if u==106 else ((48,32) if u==109 else ((64,32) if u==188 else (32,16)))
            for yy in range(max(0,(y-hy-12)//8),min(len(clear),(y+hy+12)//8+1)):
                for xx in range(max(0,(x-hx-12)//8),min(len(clear[0]),(x+hx+12)//8+1)):clear[yy][xx]=False
        connected=difficulty.accessible(clear)
        for origin in self.config['origins']:
            self.assertTrue(all((x//8,y//8) in connected for x,y in origin['cells']),origin['name'])
        self.assertTrue(difficulty.route(clear,(128,128),(1056,1600)))

    def test_other_research_players_and_nonterran_entries_unchanged(self):
        for name,size,whitelist in (('PUPx',61,difficulty.TERRAN_UPGRADES),('PTEx',44,difficulty.TERRAN_TECH)):
            before=self.before[name.encode()];after=self.converted.getsection(name)
            allowed={row*size+i for row in (1,13,27) for i in whitelist}
            self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(before,after)) if i not in allowed))

    def test_no_extra_loop_stats_resource_rewards_or_original_enemy_orders(self):
        tree=ast.parse(HELPER.read_text(encoding='utf-8'))
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls & {'SetResources','SetDeaths','SetMemory','f_dwwrite','SaveMap','LoadMap','EUDDoEvents','EUDInfLoop','RunTrigTrigger'})
        self.assertTrue({'CreateUnit','Order','Bring','Command','ElapsedTime','MinimapPing'}<=calls)

if __name__=='__main__':unittest.main()
