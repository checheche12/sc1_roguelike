"""Durable multi-campaign growth tests use temporary databases only."""
import json
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest
from sc1.campaign.missions import load_missions
from sc1.campaign import progression
from sc1.campaign.runtime_catalog import load_catalog
from sc1.manager.store import open_campaign_store, GrowthChoicesPending, ProtocolError
from sc1.bridge.protocol import Request, response_payload, WORDS

class AllCampaignGrowthTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'campaign.sqlite3'
        self.store=open_campaign_store(self.path)
    def tearDown(self): self.tmp.cleanup()
    def rows(self,sql,args=()):
        with closing(sqlite3.connect(self.path)) as c:return c.execute(sql,args).fetchall()
    def load(self,mission,phase,nonce=None,store=None):
        try:return (store or self.store).restore_growth_phase(mission,1,phase,nonce=nonce)
        except GrowthChoicesPending as pending:return pending.state
    def finish(self,mission):
        nonce=None
        for phase in (1,2,3):
            state=self.load(mission,phase,nonce)
            while state.get('state')=='choosing':
                offer=state['offer']; kind=1 if offer['kind']=='talent' else 2
                self.assertEqual(len(offer['candidates']),4 if kind==1 else 3)
                self.assertEqual(len({x['id'] for x in offer['candidates']}),len(offer['candidates']))
                if kind==2:self.assertEqual({x['rarity'] for x in offer['candidates']},{progression.curse_tier(mission)})
                else:
                    self.assertTrue(all(x['race'] in ('shared',progression.metadata(mission)['race']) for x in offer['candidates']))
                    if progression.metadata(mission)['no_production']:
                        self.assertTrue(all(not x.get('requirements',{}).get('production') for x in offer['candidates']))
                reopened=open_campaign_store(self.path)
                self.assertEqual(self.load(mission,phase,nonce,store=reopened)['offer'],offer)
                args=(offer['offer_id'],1,offer['revision'],mission,1)
                kwargs=dict(choice_kind=kind,phase=phase,nonce=nonce)
                state=reopened.choose_growth_phase_slot(*args,**kwargs)
                before=self.path.read_bytes()
                self.assertTrue(reopened.choose_growth_phase_slot(*args,**kwargs)['duplicate'])
                self.assertEqual(self.path.read_bytes(),before)
            result=self.load(mission,phase,nonce)
            if nonce:self.assertEqual(result['nonce'],nonce)
            nonce=result['nonce']
        saved=self.store.complete(mission,nonce,0,result['gold'])
        self.assertTrue(self.store.complete(mission,nonce,0,result['gold'])['duplicate'])
        self.assertEqual(self.load(mission,1)['growth_words'],result['growth_words'])
        return result,saved
    def test_expanded_catalog_preserves_original_text_and_wire_positions(self):
        original=load_catalog(Path(__file__).resolve().parents[1]/'campaign/runtime_talents.json')
        expanded=load_catalog()
        for kind,key in (('talents','bit_index'),('curses','byte_index')):
            current={item['id']:item for item in expanded[kind]}
            for old in original[kind]:
                item=current[old['id']]
                self.assertEqual((item[key],item['name'],item['rarity'],item['source_description']),
                                 (old[key],old['name'],old['rarity'],old['source_description']))
                self.assertEqual(item['legacy_effect'],old['effect'])
        for race in ('terran','zerg','protoss'):
            self.assertGreaterEqual(sum(i['race'] in (race,'shared') for i in expanded['talents']),33)
        for rarity in ('common','uncommon','rare'):
            self.assertGreaterEqual(sum(i['rarity']==rarity for i in expanded['curses']),3)
        # Every alternative source asset uses the same exact effect catalog.
        for m in load_missions():
            eligible=[i for i in expanded['talents'] if progression.item_eligible(i,m['mission_id'],'talent')]
            self.assertGreaterEqual(len(eligible),4)

    def test_all_campaigns_end_to_end_and_replay(self):
        canonical=[m for m in load_missions() if m['shared_reward_mission_id']==m['mission_id']]
        for cid in range(1,8):
            entries=sorted((m for m in canonical if m['campaign_id']==cid),key=lambda m:m['ordinal'])
            for index,m in enumerate(entries,1):
                with self.subTest(campaign=cid,mission=m['mission_id']):
                    final,saved=self.finish(m['mission_id'])
                    state=self.store.growth_status(m['mission_id'])
                    self.assertEqual(len(state['talents']),index*3)
                    self.assertEqual(sum(x['stacks'] for x in state['curses']),index*3)
                    self.assertEqual(len(state['history']),index*6)
                    if m['final']:self.assertEqual(state['upcoming'],{'talent':0,'curse':0})
                    # BW completion bits exceed32, but the native wire consumes
                    # only this mission's completed flag, never a truncated mask.
                    request=Request(m['mission_id'],1,1,2,1,'0'*32,0,0,growth_version=1)
                    import struct
                    payload=struct.unpack('<31I',response_payload(request,final,1))
                    self.assertEqual(payload[8],0) # issued before this mission's completion
                    after={**final,**saved}
                    self.assertEqual(struct.unpack('<31I',response_payload(request,after,1))[8],1)
        self.assertGreater(self.store.status()['completed_mask'],2**32)
    def test_paused_campaign_survives_other_campaign_completion(self):
        state=self.load(101,1)
        for _ in range(2):
            offer=state['offer']
            state=self.store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],101,1,
                choice_kind=1 if offer['kind']=='talent' else 2,phase=1)
        original=self.load(101,1)
        self.finish(201)
        restored=self.load(101,1)
        self.assertEqual(restored['nonce'],original['nonce'])
        self.assertEqual(restored['growth_words'],original['growth_words'])
        final,_=self.finish(101)
        self.assertEqual(final['nonce'],original['nonce'])

    def test_pending_legacy_mission_keeps_its_pin_when_another_campaign_expands(self):
        old=Path(__file__).resolve().parents[1]/'campaign/runtime_talents.json'
        self.store=open_campaign_store(self.path,runtime_catalog_path=old)
        first=self.load(101,1)
        old_ids={item['id'] for item in load_catalog(old)['talents']}
        self.store=open_campaign_store(self.path)
        self.finish(201)
        self.assertEqual(self.load(101,1)['offer'],first['offer'])
        for phase in (1,2,3):
            nonce=None if phase==1 else snapshot['nonce']
            state=self.load(101,phase,nonce)
            while state.get('state')=='choosing':
                offer=state['offer']
                if offer['kind']=='talent':
                    if phase == 1:
                        self.assertTrue({item['id'] for item in offer['candidates']} <= old_ids)
                    else:
                        self.assertTrue(all(item.get('offer_family') for item in offer['candidates']))
                state=self.store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],101,1,
                    choice_kind=1 if offer['kind']=='talent' else 2,phase=phase,nonce=nonce)
            snapshot=self.load(101,phase,nonce)

    def test_campaign_read_only_inspection_does_not_initialize_state(self):
        self.finish(201)
        before=self.path.read_bytes()
        self.assertEqual(self.store.growth_status()['mission'],201)
        self.assertEqual(self.store.status()['growth_selection']['mission'],201)
        for cid in range(1,8):
            state=self.store.growth_status_for_campaign(cid)
            self.assertEqual(progression.metadata(state['mission'])['campaign_id'],cid)
        self.assertEqual(self.path.read_bytes(),before)

    def test_locked_map_cannot_create_growth_or_reroll_state(self):
        before=self.path.read_bytes()
        with self.assertRaises(ProtocolError) as e:self.load(110,1)
        self.assertEqual(e.exception.code,'mission_locked')
        self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(self.rows("SELECT name FROM sqlite_master WHERE name='growth_state'"))
    def test_variant_reward_is_shared(self):
        for mission in (501,502,503,504,505):self.finish(mission)
        original=self.store.growth_status(505)
        restored=self.load(515,1)
        self.assertTrue(restored['already_completed'])
        self.assertEqual(restored['growth_words'],self.load(505,1)['growth_words'])
        self.assertEqual(self.store.growth_status(515),original)
        self.assertFalse(self.rows('SELECT nonce FROM attempts WHERE mission=515'))
    def test_old_catalog_offer_and_snapshot_preserved_on_expansion(self):
        old=Path(__file__).resolve().parents[1]/'campaign/runtime_talents.json'
        self.store=open_campaign_store(self.path,runtime_catalog_path=old)
        self.finish(101)
        prior_catalog=self.rows('SELECT catalog_json FROM growth_state')
        snapshots=self.rows('SELECT * FROM growth_phase_snapshots')
        offers=self.rows('SELECT * FROM growth_offers WHERE mission=101')
        self.store=open_campaign_store(self.path)
        self.finish(102)
        self.assertEqual(self.rows('SELECT catalog_json FROM growth_state'),prior_catalog)
        self.assertEqual(self.rows('SELECT * FROM growth_phase_snapshots WHERE mission=101'),snapshots)
        self.assertEqual(self.rows('SELECT * FROM growth_offers WHERE mission=101'),offers)
        self.assertEqual(len(self.rows('SELECT * FROM growth_catalog_extensions')),1)
    def test_independent_campaign_can_own_same_shared_talent(self):
        for mission in (101,201):
            state=self.load(mission,1)
            self.assertEqual(state['talents'],[])
            self.assertEqual(state['curses'],[])
            self.assertEqual(state['revision'],0)
        self.assertEqual(self.store.growth_status(101)['revision'],0)
        self.assertEqual(self.store.growth_status(201)['revision'],0)

if __name__=='__main__':unittest.main()
