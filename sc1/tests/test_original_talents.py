"""Run the actual T01 growth hooks with offline DAT/CUnit values.

Checks data mutations, damaged/dead units, coherent mailbox publication and
wave accounting. This is not the StarCraft emulator or a native playtest.
"""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from sc1.bridge.protocol import Dispatcher, read_request
from sc1.manager.store import CampaignStore
from sc1.tests.test_bridge import BASE
from sc1.tests.test_growth_bridge import GrowthMemory
from sc1.tests.test_official_probe_plugin import number
from sc1.tests.test_original_campaign import CampaignValue
from sc1.tests.test_terran01_difficulty import HardRuntime, CONFIG


class StatRow:
    def __init__(self, values):object.__setattr__(self, '_values', values)
    def __getattr__(self, field):return CampaignValue(self._values[field])
    def __setattr__(self, field, value):self._values[field] = number(value)


class GrowthRuntime(HardRuntime):
    EUDVariable = CampaignValue

    def __init__(self, choices=False):
        # Golden starting values deliberately include both small integer fields
        # and the engine's 1/256HP representation. Unrelated fields are sentinels.
        hp = {0:40, 1:45, 2:80, 3:125, 7:60, 8:120, 19:200, 32:50, 37:35, 38:80}
        self.dat_units = {i:{'maxHp':value*256,'seekRange':7,'mineralCost':75,
                             'supplyUsed':4,'timeCost':300,'sentinel':913}
                          for i,value in hp.items()}
        for i in (5, 6, 12, 30, 31):
            self.dat_units[i] = {'maxHp':150*256, 'seekRange':7, 'sentinel':913}
        self.dat_weapons = {i:{'maxRange':128,'cooldown':30,'damageType':1,
                               'damage':10,'sentinel':917}
                            for i in (0,2,4,5,11,15,16,19,20,27,35,38,103)}
        self.dat_weapons[0]['cooldown'] = 15
        self.dat_weapons[35]['damage'] = 5
        self.players = {1:{'terranSupplyUsed':20}}
        self.living_units = []
        super().__init__(growth=True, choices=choices)
        self.g = self.plugin.talents

    def TrgUnit(self, index):return StatRow(self.dat_units[number(index)])
    def Db(self, data):
        self.memory = GrowthMemory()
        return super().Db(data)
    def Weapon(self, index):return StatRow(self.dat_weapons[number(index)])
    def TrgPlayer(self, index):return StatRow(self.players[number(index)])
    def EUDLoopCUnit(self):return [StatRow(u) for u in self.living_units]
    def add_unit(self, unit, hp, owner=1):
        value={'unitType':unit,'hp':hp,'owner':owner}
        self.living_units.append(value)
        return value
    def response(self, *, bits=0, counts=(0,0,0), catalog=1, **kwargs):
        super().response(**kwargs)
        self.memory.set(43, catalog)
        for i in range(16):self.memory.set(44+i, (bits >> (32*i)) & 0xffffffff)
        for i in range(4):self.memory.set(60+i, 0)
        self.memory.set(60, sum(value << (8*i) for i,value in enumerate(counts)))
    def load(self, **kwargs):
        self.response(**kwargs);self.tick()
        assert self.memory.get(7) == 2
    def force_wave(self):
        self.units=[u for u in self.units if u['player'] != 6]
        self.h['active'] << 1;self.h['due'] << 1
        before=len(self.created);self.run(96)
        return self.created[before:]


class TalentEffectTests(unittest.TestCase):
    def test_all17_apply_actual_stat_fields_and_leave_hero_unchanged(self):
        r=GrowthRuntime();hero=deepcopy(r.dat_units[19]);hero_weapon=deepcopy(r.dat_weapons[5])
        r.load(bits=(1<<17)-1)
        expected_units={0:{'maxHp':50*256,'seekRange':8}, 1:{'maxHp':75*256},
                        2:{'maxHp':50*256,'mineralCost':50,'supplyUsed':2},
                        3:{'maxHp':145*256}, 5:{'seekRange':8}, 6:{'seekRange':8},
                        7:{'maxHp':80*256,'timeCost':150}, 8:{'maxHp':150*256,'seekRange':9},
                        12:{'seekRange':9}, 30:{'seekRange':9}, 31:{'seekRange':9}, 32:{'maxHp':100*256}}
        expected_weapons={0:{'maxRange':160,'cooldown':12}, 2:{'damageType':3},
                          4:{'cooldown':24}, 11:{'maxRange':160}, 27:{'maxRange':192},
                          15:{'maxRange':192}, 16:{'maxRange':192}, 19:{'maxRange':192},
                          20:{'maxRange':192}, 103:{'cooldown':24}}
        for table, expected in ((r.dat_units,expected_units),(r.dat_weapons,expected_weapons)):
            for index,fields in expected.items():
                for field,value in fields.items():
                    self.assertEqual(table[index][field],value,(index,field))
        self.assertEqual(r.dat_units[19],hero);self.assertEqual(r.dat_weapons[5],hero_weapon)
        self.assertTrue(all(row['sentinel']==913 for row in r.dat_units.values()))
        self.assertTrue(all(row['sentinel']==917 for row in r.dat_weapons.values()))
        self.assertEqual((r.memory.get(19), number(r.g['applied']), r.cp, r.minerals, r.gas),(1,1,7,40,0))

    def test_damaged_friendly_hp_ratio_and_vulture_supply_adjust_once(self):
        r=GrowthRuntime()
        marine=r.add_unit(0,20*256);worker=r.add_unit(7,30*256);vulture=r.add_unit(2,40*256)
        full_vulture=r.add_unit(2,80*256);dead=r.add_unit(2,0)
        enemy=r.add_unit(0,20*256,owner=4);hero=r.add_unit(19,90*256)
        r.load(bits=(1<<1)|(1<<7)|(1<<16))
        self.assertEqual([u['hp'] for u in (marine,worker,vulture,full_vulture,dead,enemy,hero)],
                         [25*256,40*256,25*256,50*256,0,20*256,90*256])
        self.assertEqual(r.players[1]['terranSupplyUsed'],16)
        before=deepcopy((r.dat_units,r.dat_weapons,r.living_units,r.players))
        # A repeated direct application and a late response cannot heal or stack.
        r.g['apply_once']([CampaignValue((1<<1)|(1<<7)|(1<<16))]+[CampaignValue(0) for _ in range(15)],
                          [CampaignValue(0) for _ in range(4)])
        r.response(seq=4, echo=2, bits=(1<<17)-1, counts=(2,2,2));r.run(10)
        self.assertEqual((r.dat_units,r.dat_weapons,r.living_units,r.players),before)

    def test_enemy_curses_scale_original_hp_and_round_damage_once(self):
        r=GrowthRuntime();ling=r.add_unit(37,10*256,owner=4);hydra=r.add_unit(38,40*256,owner=6)
        unrelated=r.add_unit(37,10*256,owner=1);dead=r.add_unit(37,0,owner=4)
        r.load(counts=(0,2,2))
        self.assertEqual((r.dat_units[37]['maxHp'],r.dat_units[38]['maxHp']),(42*256,96*256))
        self.assertEqual((ling['hp'],hydra['hp'],unrelated['hp'],dead['hp']),(12*256,48*256,10*256,0))
        self.assertEqual((r.dat_weapons[35]['damage'],r.dat_weapons[38]['damage']),(6,12))

    def test_small_ratio_rounds_to_minimum1_and_max_curse_count_does_not_overflow(self):
        r=GrowthRuntime();r.dat_units[7]['timeCost']=1
        unit=r.add_unit(38,80*256,owner=6);r.load(bits=1<<15,counts=(255,255,255))
        self.assertEqual(r.dat_units[7]['timeCost'],1)
        self.assertEqual((r.dat_units[38]['maxHp'],unit['hp']),(2120*256,2120*256))
        self.assertEqual(r.dat_weapons[38]['damage'],202)


class GrowthMapProtocolTests(unittest.TestCase):
    def test_capability_and_applied_flag_are_in_coherent_map_request(self):
        r=GrowthRuntime();q=read_request(r.memory,BASE)
        self.assertEqual((q.growth_version,q.growth_applied),(1,0))
        r.load(bits=1<<1);q=read_request(r.memory,BASE)
        self.assertEqual((q.state,q.growth_applied),(2,1))
        self.assertTrue(all(sequence&1 for word,value,sequence in r.map_writes if word==19))

    def test_unknown_version_bits_or_curse_bytes_rejected_before_any_stat_mutation(self):
        for payload in ({'catalog':2},{'bits':1<<17},{'bits':1<<64},{'counts':(0,0,0,1)}):
            with self.subTest(payload=payload):
                r=GrowthRuntime();before=deepcopy((r.dat_units,r.dat_weapons))
                r.response(**payload);r.tick()
                self.assertEqual((r.memory.get(7),r.memory.get(19),r.created,r.victories),(5,0,[],[]))
                self.assertEqual((r.dat_units,r.dat_weapons),before)
        r=GrowthRuntime();r.response(bits=1<<1);r.memory.set(63,1);r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(19)),(5,0))

    def test_torn_extended_response_and_odd_sequence_never_apply(self):
        r=GrowthRuntime();r.response(bits=1<<1,counts=(2,2,2))
        before=deepcopy((r.dat_units,r.dat_weapons))
        def tear(address,size):
            if address==BASE+63*4:r.memory.set(32,4)
        r.memory.on_read=tear;r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(19)),(1,0))
        self.assertEqual((r.dat_units,r.dat_weapons),before)
        r.memory.on_read=None;r.response(seq=3,bits=1<<1);r.tick()
        self.assertEqual((r.dat_units,r.dat_weapons),before)

    def test_growth_map_pauses_only_added_waves_until_selection_load(self):
        r=GrowthRuntime();r.ready();r.run(2000)
        self.assertEqual((r.created,r.pings,number(r.h['home_ticks'])),([],[],1440))
        # Ready() deliberately sets the grace counter; gating means it stays put.
        r.load(counts=(2,0,0));r.run(95)
        self.assertEqual(([u['unit'] for u in r.created].count(37),[u['unit'] for u in r.created].count(38)),(21,3))

    def test_commit_ack_ignores_growth_payload_and_never_reapplies(self):
        r=GrowthRuntime();r.load(bits=1<<1,counts=(0,1,1))
        before=deepcopy((r.dat_units,r.dat_weapons,r.living_units))
        r.switch=True;r.tick();self.assertEqual(r.memory.get(7),3)
        r.response(seq=4,status=2,echo=6,bits=(1<<512)-1,counts=(255,255,255),catalog=99)
        r.run(48)
        self.assertEqual((r.dat_units,r.dat_weapons,r.living_units),before)
        self.assertEqual(r.victories,[1])

    def test_real_manager_choices_apply_and_complete_once_with_pending_next_map_rewards(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CampaignStore(Path(folder)/'campaign.sqlite3',new_profile='original')
            r=GrowthRuntime();d=Dispatcher(r.memory,BASE,store)
            d.poll();r.tick();self.assertEqual(d.poll()['status'],'waiting_for_choices')
            for _ in range(5):
                status=store.prepare_growth(101);offer=status['offer']
                store.choose_growth(offer['offer_id'],offer['candidates'][0]['id'],offer['revision'],mission=101)
            self.assertEqual(d.poll()['status'],'restored');r.tick()
            self.assertEqual((r.memory.get(7),r.memory.get(19)),(2,1))
            before=deepcopy((r.dat_units,r.dat_weapons,r.living_units))
            r.switch=True;r.tick();self.assertEqual(d.poll()['status'],'committed');r.tick()
            self.assertEqual((r.dat_units,r.dat_weapons,r.living_units),before)
            reopened=CampaignStore(Path(folder)/'campaign.sqlite3')
            self.assertEqual(reopened.status()['completed_mask'],1)
            next_status=reopened.growth_status(101)
            self.assertEqual(next_status['upcoming'],{'talent':2,'curse':2})
            self.assertEqual(next_status['state'],'waiting_next_map')


class GrowthWaveTests(unittest.TestCase):
    def test_quarters_carry_by_type_and_two_stacks_cap_at90(self):
        r=GrowthRuntime();r.load(counts=(1,0,0));r.ready()
        amounts=[]
        for _ in range(4):
            r.h['stage'] << 0;wave=r.force_wave()
            amounts.append((sum(u['unit']==37 for u in wave),sum(u['unit']==38 for u in wave)))
        self.assertEqual(amounts,[(17,2),(18,3),(17,2),(18,3)])
        for stacks in (2,255):
            r=GrowthRuntime();r.load(counts=(stacks,0,0));r.ready();r.h['stage'] << 6
            wave=r.force_wave()
            self.assertEqual((sum(u['unit']==37 for u in wave),sum(u['unit']==38 for u in wave)),(72,18))

    def test_reserved_capacity_hits160_units40_hydras_but_no_more(self):
        r=GrowthRuntime();r.load(counts=(2,0,0));r.ready();r.h['stage'] << 6
        r.units.extend({'player':6,'unit':37 if i<48 else 38,'x':1056,'y':1480} for i in range(70))
        r.run(96)
        self.assertEqual((len(r.matching(6,'Men')),len(r.matching(6,38))),(160,40))
        self.assertEqual(len(r.created),90)
        r.h['due'] << 1;r.run(96);self.assertEqual(len(r.created),90)

    def test_skipped_wave_never_accumulates_whole_units_or_fraction(self):
        r=GrowthRuntime();r.load(counts=(1,0,0));r.ready()
        for index in range(4):r.block_origin(index)
        for _ in range(10):r.h['due'] << 1;r.tick()
        self.assertEqual((r.created,number(r.h['ling_remainder']),number(r.h['hydra_remainder'])),([],0,0))
        r.units=[u for u in r.units if not(u['player']==1 and u['unit']==0)]
        wave=r.force_wave();self.assertEqual(len(wave),19)


if __name__=='__main__':unittest.main()
