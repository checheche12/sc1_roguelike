"""Durable in-game choices through the real store, bridge and map hooks.

Uses owned offline memory and temporary SQLite only. The mouse action is a
modeled civilian move; this does not claim native rendering/pathing validation.
"""
from copy import deepcopy
import json
from pathlib import Path
import struct
import tempfile
import unittest
import uuid
from unittest.mock import patch

from sc1.bridge.protocol import BridgeError, Dispatcher, UnstableMailbox, read_request
from sc1.manager.store import CampaignStore
from sc1.tests.test_bridge import BASE
from sc1.tests.test_growth_bridge import GrowthMemory
from sc1.tests.test_original_talents import GrowthRuntime
from sc1.tests.test_official_probe_plugin import number
from sc1.tests.test_original_campaign import builder


class ChoiceMemory(GrowthMemory):
    def __init__(self):
        super().__init__()
        self.set(20,0x43484331);self.set(21,1)

    def choose(self, slot=1):
        sequence=self.get(8)
        self.set(8,sequence+1)
        self.set(7,1);self.set(9,3);self.set(22,slot)
        for i in range(4):self.set(23+i,self.get(51+i))
        self.set(27,self.get(45));self.set(28,self.get(44))
        self.set(8,sequence+2);self.set(6,self.get(6)+1)


class IngameRuntime(GrowthRuntime):
    P12,Move = 11, 2

    def __init__(self):
        self.lines={};self.views=[];self.removed=[]
        super().__init__(choices=True)
        self.c=self.plugin.choices
        self.config=json.loads((builder.BUILD/'choices.json').read_text(encoding='utf-8'))

    def DisplayTextAt(self,line,text):self.lines[line]=text.decode('utf-8') if isinstance(text,bytes) else text
    def StringBuffer(self,capacity):
        runtime=self
        class Buffer:
            def printfAt(self,line,text,*args):runtime.lines[line]=text.format(*[number(arg) for arg in args])
        return Buffer()
    def UnitProperty(self,**properties):return properties
    def inside(self,row,location):
        if location=='Anywhere':return True
        a,b,c,d=self.locations[location]
        return a<=row['x']<=c and b<=row['y']<=d
    def CreateUnitWithProperties(self,count,unit,location,player,properties):
        x,y,a,b=self.locations[location]
        def action():
            row={'player':player,'unit':unit,'x':(x+a)//2,'y':(y+b)//2,**properties}
            self.units.append(row);self.created.append(row.copy())
        return action
    def MoveUnit(self,count,unit,player,source,target):
        x,y,a,b=self.locations[target]
        def action():
            rows=[u for u in self.units if u['player']==player and u['unit']==unit and self.inside(u,source)]
            for row in rows[:count]:row['x'],row['y']=(x+a)//2,(y+b)//2
        return action
    def RemoveUnit(self,unit,player):
        def action():
            self.removed.extend(u.copy() for u in self.units if u['player']==player and u['unit']==unit)
            self.units[:]=[u for u in self.units if not(u['player']==player and u['unit']==unit)]
        return action
    def CenterView(self,location):return lambda:self.views.append((self.cp,location))
    def move_to_slot(self,slot):
        selector=next(u for u in self.units if u['player']==1 and u['unit']==15)
        selector['x'],selector['y']=self.config['slots_left_to_right'][slot-1]


class ChoiceWireTests(unittest.TestCase):
    def test_initial_saved_offer_and_five_slot_requests_then_frozen_load(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CampaignStore(Path(folder)/'campaign.sqlite3',new_profile='original')
            m=ChoiceMemory();d=Dispatcher(m,BASE,store)
            d.poll();m.set(6,1)
            before=bytes(m.data[:128])
            self.assertEqual(d.poll()['status'],'choice_offered')
            self.assertEqual(bytes(m.data[:128]),before)
            for index in range(5):
                state=store.growth_status();offer=state['offer']
                self.assertEqual((m.get(33),m.get(43),m.get(44),m.get(46)),(4,1,1 if index<3 else 2,4 if index<3 else 3))
                self.assertEqual(m.data[51*4:55*4],uuid.UUID(offer['offer_id']).bytes)
                key='bit_index' if index<3 else 'byte_index'
                self.assertEqual([m.get(47+i) for i in range(m.get(46))],[c[key]+1 for c in offer['candidates']])
                m.choose(1)
                self.assertEqual(d.poll()['status'],'choice_offered' if index<4 else 'restored')
            self.assertEqual(m.get(33),1)
            self.assertEqual(sum(m.get(i).bit_count() for i in range(44,60)),3)
            self.assertEqual(sum(m.data[240:256]),2)
            self.assertEqual(CampaignStore(Path(folder)/'campaign.sqlite3').growth_status()['state'],'in_mission')
            self.assertTrue(all(BASE+128<=address and address+len(data)<=BASE+256 for address,data in m.writes))

    def test_lost_choice_ack_and_reconnect_keep_offer_without_reroll_or_second_reward(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'campaign.sqlite3';store=CampaignStore(path,new_profile='original')
            m=ChoiceMemory();d=Dispatcher(m,BASE,store);d.poll();m.set(6,1);d.poll()
            m.choose(2);d.poll()
            next_offer=store.growth_status()['offer'];before=path.read_bytes()
            restarted=Dispatcher(m,BASE,CampaignStore(path));restarted.poll();m.set(6,3)
            self.assertEqual(restarted.poll()['status'],'choice_offered')
            self.assertEqual(CampaignStore(path).growth_status()['offer'],next_offer)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(m.data[51*4:55*4],uuid.UUID(next_offer['offer_id']).bytes)

    def test_bad_slot_kind_or_token_never_writes_or_changes_saved_selection(self):
        for field,value in ((22,0),(22,5),(28,0),(28,3)):
            with self.subTest(field=field,value=value), tempfile.TemporaryDirectory() as folder:
                path=Path(folder)/'campaign.sqlite3';store=CampaignStore(path,new_profile='original')
                m=ChoiceMemory();d=Dispatcher(m,BASE,store);d.poll();m.set(6,1);d.poll();m.choose()
                m.set(field,value);before=path.read_bytes();writes=len(m.writes)
                with self.assertRaises(BridgeError):d.poll()
                self.assertEqual(path.read_bytes(),before);self.assertEqual(len(m.writes),writes)

    def test_store_failure_sends_no_choice_ack_and_same_request_can_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CampaignStore(Path(folder)/'campaign.sqlite3',new_profile='original')
            m=ChoiceMemory();d=Dispatcher(m,BASE,store);d.poll();m.set(6,1);d.poll();m.choose()
            before=bytes(m.data[128:]);offer=store.growth_status()['offer']
            with patch.object(store,'choose_growth_slot',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):d.poll()
            self.assertEqual(bytes(m.data[128:]),before);self.assertEqual(store.growth_status()['offer'],offer)
            self.assertEqual(d.poll()['status'],'choice_offered')

    def test_request_race_after_durable_selection_leaves_response_unpublished(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CampaignStore(Path(folder)/'campaign.sqlite3',new_profile='original')
            m=ChoiceMemory();d=Dispatcher(m,BASE,store);d.poll();m.set(6,1);d.poll();m.choose()
            actual=store.choose_growth_slot;before=bytes(m.data[128:])
            def mutate(*args,**kwargs):
                result=actual(*args,**kwargs);m.set(8,m.get(8)+2);return result
            with patch.object(store,'choose_growth_slot',side_effect=mutate):
                with self.assertRaises(UnstableMailbox):d.poll()
            self.assertEqual(bytes(m.data[128:]),before)
            self.assertEqual(len(store.growth_status()['talents']),1)

    def test_missing_or_unknown_choice_capability_is_rejected(self):
        m=ChoiceMemory();m.set(21,2)
        with self.assertRaises(BridgeError):read_request(m,BASE)
        m.set(21,1);m.set(17,0)
        with self.assertRaises(BridgeError):read_request(m,BASE)


class ActualChoiceMapTests(unittest.TestCase):
    def test_real_game_offer_move_save_next_offer_effects_cleanup_victory_and_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            # Match the emulated historical17-talent EUD map, rather than the
            # current expanded native catalog used by new native records.
            path=Path(folder)/'campaign.sqlite3';store=CampaignStore(path,new_profile='original',runtime_catalog_path=builder.TALENT_CATALOG)
            r=IngameRuntime();original=deepcopy(r.units);d=Dispatcher(r.memory,BASE,store)
            d.poll();r.tick();self.assertEqual(d.poll()['status'],'choice_offered');r.tick()
            for index in range(5):
                kind=1 if index<3 else 2
                self.assertEqual((number(r.c['active']),number(r.c['kind']),r.cp),(1,kind,7))
                self.assertIn('선택',r.lines[0]);self.assertIn('[1]',r.lines[2])
                self.assertEqual(len([u for u in r.units if u['unit'] in (15,195)]),5)
                r.move_to_slot(1);r.tick()
                request=read_request(r.memory,BASE)
                self.assertEqual((request.state,request.operation,request.choice_slot,request.choice_kind),(1,3,1,kind))
                old_sequence=request.sequence;r.run(5)
                self.assertEqual(read_request(r.memory,BASE).sequence,old_sequence)
                self.assertEqual(d.poll()['status'],'choice_offered' if index<4 else 'restored');r.tick()
            self.assertEqual((r.memory.get(7),r.memory.get(19),number(r.c['created'])),(2,1,0))
            self.assertEqual(r.units,original);self.assertEqual(len(r.removed),5)
            self.assertEqual((r.minerals,r.gas,r.cp),(40,0,7))
            self.assertTrue(all(text==' ' for text in r.lines.values()))
            self.assertEqual(len(store.growth_status()['talents']),3)
            self.assertEqual(sum(c['stacks'] for c in store.growth_status()['curses']),2)
            before=deepcopy((r.dat_units,r.dat_weapons));r.switch=True;r.tick()
            self.assertEqual(d.poll()['status'],'committed');r.run(48)
            self.assertEqual(r.victories,[1]);self.assertEqual((r.dat_units,r.dat_weapons),before)
            self.assertEqual(store.growth_status()['upcoming'],{'talent':2,'curse':2})
            replay=IngameRuntime();d2=Dispatcher(replay.memory,BASE,CampaignStore(path))
            d2.poll();replay.tick();self.assertEqual(d2.poll()['status'],'restored');replay.tick()
            self.assertEqual((replay.memory.get(7),number(replay.c['created']),len(replay.created)),(2,0,0))
            self.assertEqual(replay.dat_units,r.dat_units);self.assertEqual(replay.dat_weapons,r.dat_weapons)

    def test_torn_offer_never_creates_selector_or_mutates_stats(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CampaignStore(Path(folder)/'campaign.sqlite3',new_profile='original')
            r=IngameRuntime();before=deepcopy((r.dat_units,r.dat_weapons));d=Dispatcher(r.memory,BASE,store)
            d.poll();r.tick();d.poll()
            def tear(address,size):
                if address==BASE+63*4:r.memory.set(32,r.memory.get(32)+2)
            r.memory.on_read=tear;r.tick()
            self.assertEqual((number(r.c['created']),r.memory.get(7)),(0,1))
            self.assertEqual((r.dat_units,r.dat_weapons),before)

    def test_unknown_candidate_or_duplicate_candidates_enter_error_without_creation(self):
        for mutations in ({47:18},{48:1,47:1},{51:0,52:0,53:0,54:0}):
            with self.subTest(mutations=mutations), tempfile.TemporaryDirectory() as folder:
                store=CampaignStore(Path(folder)/'campaign.sqlite3',new_profile='original')
                r=IngameRuntime();d=Dispatcher(r.memory,BASE,store);d.poll();r.tick();d.poll()
                for word,value in mutations.items():r.memory.set(word,value)
                r.tick()
                self.assertEqual((number(r.c['created']),r.memory.get(7),r.memory.get(19)),(0,5,0))


if __name__=='__main__':unittest.main()
