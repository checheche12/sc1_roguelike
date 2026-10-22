"""Revision-five integration uses disposable databases and synthetic coverage."""
import copy
from contextlib import closing
import json
from pathlib import Path
import random
import sqlite3
import struct
import tempfile
import unittest
from unittest.mock import patch

from sc1.campaign import rework_growth, talent_campaign_policy as policy, progression
from sc1.campaign.runtime_catalog import load_catalog,encode_growth,validate_growth_words,upgrade_growth_words,GrowthError
from sc1.manager.store import CampaignStore,GrowthChoicesPending
from sc1.bridge.protocol import Request,choice_payload,response_payload


class ReworkGrowthTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='sc1-rework-disposable-')
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'record.sqlite3'
        self.catalog=load_catalog(expected_version=2)
        for kind in ('talents','curses'):
            for item in self.catalog[kind]:item['implemented']=True
        self.catalog_path=Path(self.tmp.name)/'synthetic_coverage.json'
        self.catalog_path.write_text(json.dumps(self.catalog,ensure_ascii=False),encoding='utf8')
        self.store=CampaignStore(self.path,new_profile='original',runtime_catalog_path=self.catalog_path)

    def load(self,mission=101,phase=1,nonce=None):
        try:return self.store.restore_growth_phase(mission,2,phase,nonce=nonce)
        except GrowthChoicesPending as pending:return pending.state

    def pick(self,state,slot=1,nonce=None):
        offer=state['offer']
        return self.store.choose_growth_phase_slot(offer['offer_id'],slot,offer['revision'],
            state['mission'],2,choice_kind=1 if offer['kind']=='talent' else 2,
            phase=state['requested_phase'],nonce=nonce)

    def finish(self,mission=101,phase=1,nonce=None,seen=None):
        state=self.load(mission,phase,nonce)
        while state.get('offer'):
            if seen is not None:seen.append(copy.deepcopy(state['offer']))
            state=self.pick(state,nonce=nonce)
        return self.load(mission,phase,nonce)

    def query(self,sql,args=()):
        with closing(sqlite3.connect(self.path)) as conn:return conn.execute(sql,args).fetchall()

    def test_append_mapping_and_user_deletion(self):
        old=load_catalog()
        from sc1.campaign.talent_balance import historical
        self.assertEqual([historical(x) for x in self.catalog['talents'][:238]],old['talents'])
        self.assertEqual(self.catalog['curses'][:15],old['curses'])
        self.assertEqual([x['bit_index'] for x in self.catalog['talents'][238:]],list(range(238,len(self.catalog['talents']))))
        self.assertEqual([x['byte_index'] for x in self.catalog['curses'][15:]],list(range(15,50)))
        self.assertNotIn('rework-rule-special-wave',{x['id'] for x in self.catalog['curses']})

    def test_qa_source_corrections_refresh_future_catalog_preserve_issued_offer(self):
        prior=copy.deepcopy(self.catalog)
        patched=[]
        for kind in ('talents','curses'):
            for item in prior[kind]:
                if item.get('effect',{}).pop('qa_revision',None):
                    patched.append(item['id']);item['description']='Prior QA description'
        self.assertGreater(len(patched),0)
        self.catalog_path.write_text(json.dumps(prior,ensure_ascii=False),encoding='utf8')
        state=self.load();issued=self.query('SELECT offer_id,candidates_json FROM growth_offers')
        self.catalog_path.write_text(json.dumps(self.catalog,ensure_ascii=False),encoding='utf8')
        resumed=self.load();self.assertEqual(resumed['offer'],state['offer'])
        self.assertEqual(self.query('SELECT offer_id,candidates_json FROM growth_offers'),issued)
        pinned=json.loads(self.query('SELECT catalog_json FROM growth_rework_catalog')[0][0])
        for kind in ('talents','curses'):
            expected={item['id']:item for item in self.catalog[kind]}
            for item in pinned[kind]:
                if item['id'] in patched:
                    self.assertEqual(item['description'],expected[item['id']]['description'])
                    self.assertEqual(item['effect'],expected[item['id']]['effect'])
                    self.assertEqual(item.get('source_description'),expected[item['id']].get('source_description'))

    def test_four_opening_legends_are_available_before_ordinary_rolls(self):
        class LastRoll:
            def randrange(self,stop):return stop-1
            def shuffle(self,items):pass
        for first in (101,201,301,401,501,601):
            owned=[];mission=first;found=False
            while not found:
                for phase in (1,2,3):
                    draw=rework_growth.candidates(self.catalog,mission,phase,owned,LastRoll())
                    if policy.reward_policy(mission,phase).guaranteed_legendary:
                        self.assertEqual(len(draw),4,(first,mission));self.assertEqual(len({x['id'] for x in draw}),4)
                        self.assertTrue(all(x['rarity']=='legendary' for x in draw));found=True;break
                    from sc1.campaign.legendary_bundles import member_ids
                    for identity in member_ids(draw[0],self.catalog):
                        if identity not in owned:owned.append(identity)
                if not found:mission=progression.next_missions(mission)[0]

    def test_ammunition_bundle_update_keeps_issued_single_offer_exact(self):
        prior=copy.deepcopy(self.catalog);card=prior['talents'][355]
        for field in ('bundle_family','bundle_families'):card.pop(field,None)
        card['effect']['qa_revision']=2026101610
        self.catalog_path.write_text(json.dumps(prior,ensure_ascii=False),encoding='utf8')
        with patch.object(rework_growth,'candidates',return_value=[card]):state=self.load(mission=301)
        issued=copy.deepcopy(state['offer'])
        serialized=self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(issued['offer_id'],))[0][0]
        self.catalog_path.write_text(json.dumps(self.catalog,ensure_ascii=False),encoding='utf8')
        resumed=self.load(mission=301)
        self.assertEqual(resumed['offer'],issued)
        self.assertEqual(self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(issued['offer_id'],)),[(serialized,)])
        pinned=json.loads(self.query('SELECT catalog_json FROM growth_rework_catalog')[0][0])
        self.assertEqual(pinned['talents'][355]['bundle_families'],[72,81])
        picked=self.pick(resumed)
        while picked.get('offer'):picked=self.pick(picked)
        self.assertTrue(picked['growth_words'][1+355//32]&(1<<(355%32)))

    def test_economic_single_rule_keeps_previously_issued_pair_exact(self):
        card=self.catalog['talents'][355];partner=self.catalog['talents'][369]
        saved=dict(card,bundled_talent_ids=[card['id'],partner['id']])
        with patch.object(rework_growth,'candidates',return_value=[saved]):state=self.load(mission=301)
        issued=copy.deepcopy(state['offer'])
        serialized=self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(issued['offer_id'],))[0][0]
        resumed=self.load(mission=301)
        self.assertEqual(resumed['offer'],issued)
        self.assertEqual(self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(issued['offer_id'],)),[(serialized,)])
        picked=self.pick(resumed)
        while picked.get('offer'):picked=self.pick(picked)
        for item in (card,partner):
            bit=item['bit_index'];self.assertTrue(picked['growth_words'][1+bit//32]&(1<<(bit%32)))

    def test_displayed_unchosen_manuals_reach_next_offer_and_reconnect_is_immutable(self):
        opening=self.finish();nonce=opening['nonce']
        with patch.object(policy,'rolled_rarity',return_value='common'):
            state=self.load(phase=2,nonce=nonce)
        self.assertEqual(len(state['offer']['candidates']),4)
        displayed={identity for x in state['offer']['candidates'] if x.get('repeatable') for identity in x.get('bundled_talent_ids',[x['id']])}
        first_rows=self.query('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL')
        self.store=CampaignStore(self.path,runtime_catalog_path=self.catalog_path)
        with patch.object(rework_growth,'recent_manuals',side_effect=AssertionError('Existing offer must not redraw')):
            self.assertEqual(self.load(phase=2,nonce=nonce)['offer'],state['offer'])
        completed=self.finish(phase=2,nonce=nonce)
        with patch.object(policy,'draw_candidates',wraps=policy.draw_candidates) as sampler:
            self.load(phase=3,nonce=completed['nonce'])
        self.assertEqual(sampler.call_args.kwargs['recent_manuals'],displayed)
        for identity,serialized in first_rows:
            self.assertEqual(self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(identity,)),[(serialized,)])

    def test_wire_v2_caps_new_exports_preserves_high_curse_and_old_u32_rank(self):
        manual=next(x for x in self.catalog['talents'] if x.get('repeatable'))
        curse=self.catalog['curses'][-1]
        words=encode_growth(self.catalog,[manual['id']],{curse['id']:7},{manual['id']:100000})
        self.assertEqual((len(words),words[0],words[33+manual['rank_slot']]),(65,2,4))
        self.assertEqual(words[17+49//4]>>(8*(49%4))&255,7)
        self.assertEqual(validate_growth_words(words),words)
        historical=words.copy();historical[33+manual['rank_slot']]=100000
        self.assertEqual(validate_growth_words(historical),historical)
        old=encode_growth(load_catalog(),[load_catalog()['talents'][0]['id']],{})
        converted=upgrade_growth_words(old)
        self.assertEqual(converted[1:21],old[1:21]);self.assertEqual(len(converted),65)
        with self.assertRaises(GrowthError):encode_growth(self.catalog,[],{}, {manual['id']:1})

    def test_three_repeat_ranks_restart_and_immutable_checkpoints(self):
        manual=next(x for x in self.catalog['talents'] if x.get('repeatable'))
        def fixed(catalog,mission,phase,owned,rng,**kwargs):return [manual]
        nonce=None;snapshots=[]
        with patch('sc1.campaign.rework_growth.candidates',side_effect=fixed):
            for phase in (1,2,3):
                result=self.finish(phase=phase,nonce=nonce)
                nonce=result['nonce'];snapshots.append(result['growth_words'])
                self.assertEqual(snapshots[-1][33+manual['rank_slot']],phase)
                self.store=CampaignStore(self.path,runtime_catalog_path=self.catalog_path)
                self.assertEqual(self.load()['growth_words'],snapshots[-1])
        self.assertEqual(self.query('SELECT rank FROM growth_manual_ranks'),[(3,)])
        self.assertEqual([json.loads(x[0]) for x in self.query('SELECT words_json FROM growth_phase_snapshots ORDER BY phase')],snapshots)
        completed=self.store.complete(101,nonce,0,0)
        self.assertFalse(completed['duplicate'])
        self.assertTrue(self.store.complete(101,nonce,0,0)['duplicate'])
        self.assertEqual(self.query('SELECT COUNT(*) FROM growth_rewards'),[(1,)])

    def test_v1_issued_offer_and_snapshot_preserved_during_upgrade(self):
        self.store=CampaignStore(self.path,new_profile='original')
        def oldload(phase=1,nonce=None):
            try:return self.store.restore_growth_phase(101,1,phase,nonce=nonce)
            except GrowthChoicesPending as pending:return pending.state
        state=oldload()
        issued=self.query('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL')
        self.store=CampaignStore(self.path,runtime_catalog_path=self.catalog_path)
        current=self.load()
        self.assertEqual(current['offer'],state['offer'])
        self.assertEqual(self.query('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL'),issued)
        result=self.finish()
        frozen=self.query('SELECT words_json FROM growth_phase_snapshots WHERE phase=1')
        self.finish(phase=2,nonce=result['nonce'])
        self.assertEqual(self.query('SELECT words_json FROM growth_phase_snapshots WHERE phase=1'),frozen)
        self.assertEqual(json.loads(self.query('SELECT catalog_json FROM growth_state')[0][0])['catalog_version'],1)

    def test_issued_v2_offer_is_preserved_after_rarity_rebalance(self):
        old_weights = {'common': 40, 'uncommon': 29, 'rare': 20,
                       'epic': 10, 'legendary': 1}
        with patch.dict(policy.RARITY_WEIGHTS, old_weights, clear=True):
            state = self.load()
        issued = self.query('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL')
        self.store = CampaignStore(self.path, runtime_catalog_path=self.catalog_path)
        with patch.object(policy, 'rolled_rarity', side_effect=AssertionError('Issued offers must not reroll')):
            current = self.load()
        self.assertEqual(current['offer'], state['offer'])
        self.assertEqual(self.query('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL'), issued)

    def test_all_campaigns_keep_three_rewards_five_economy_and_four_legend_choices(self):
        for first in (101,201,301,401,501,601):
            mission=first;awards=[]
            while True:
                nonce=None
                for phase in (1,2,3):
                    result=self.finish(mission,phase,nonce,awards);nonce=result['nonce']
                self.store.complete(mission,nonce,0,0)
                following=progression.next_missions(mission)
                if not following:break
                mission=following[0]
            talents=[x for x in awards if x['kind']=='talent']
            self.assertEqual(len(talents),policy.logical_mission_count(first)*3-1)
            self.assertEqual(sum(x['candidates'][0]['category']=='economy' for x in talents),5)
            legends=[x for x in talents if len(x['candidates'])==4 and all(c['rarity']=='legendary' for c in x['candidates'])]
            self.assertEqual(len(legends),2)
            for offer in awards:
                candidates=offer['candidates']
                self.assertEqual(len({x['id'] for x in candidates}),len(candidates))
                if offer['kind']=='curse':self.assertEqual(len({x['rarity'] for x in candidates}),1)
            for mid,phase,tier in self.query("SELECT p.mission,p.phase,o.rarity FROM growth_phase_offers p JOIN growth_offers o USING(offer_id) WHERE o.kind='curse' AND o.candidates_json IS NOT NULL"):
                self.assertEqual(tier,rework_growth.curse_tier(mid,phase))

    def test_final_secret_no_production_skips_only_new_curses(self):
        from sc1.campaign.catalog import MISSIONS
        with closing(sqlite3.connect(self.path)) as conn,conn:
            conn.execute('UPDATE campaign SET completed_mask=? WHERE id=1',(MISSIONS[611].required_mask,))
        nonce=None;seen=[]
        for phase in (1,2,3):
            result=self.finish(611,phase,nonce,seen);nonce=result['nonce']
        self.assertEqual([x['kind'] for x in seen],['talent']*2)
        self.assertEqual(self.query('SELECT COUNT(*) FROM growth_offers WHERE selected_id=?',(rework_growth.SKIPPED_CURSE,)),[(2,)])
        self.assertEqual(self.query('SELECT COUNT(*) FROM growth_offers WHERE selected_id=?',(rework_growth.SKIPPED_FINAL,)),[(2,)])
        self.store.complete(611,nonce,0,0)
        self.assertEqual(self.query('SELECT COUNT(*) FROM growth_rewards'),[(1,)])

    def test_every_campaign_final_skips_only_phase_three_and_saves_completion(self):
        from sc1.campaign.catalog import MISSIONS
        for mission in (110,210,310,408,508,610,611):
            with closing(sqlite3.connect(self.path)) as conn,conn:
                conn.execute('UPDATE campaign SET completed_mask=? WHERE id=1',(MISSIONS[mission].required_mask,))
            nonce=None;seen=[]
            for phase in (1,2):
                result=self.finish(mission,phase,nonce,seen);nonce=result['nonce']
            self.assertEqual(sum(x['kind']=='talent' for x in seen),2)
            words=result['growth_words'];prior=len(seen)
            result=self.finish(mission,3,nonce,seen)
            self.assertEqual(len(seen),prior);self.assertEqual(result['completed_phase'],3)
            self.assertEqual(result['growth_words'],words)
            self.store.complete(mission,nonce,0,0)
            self.assertEqual(self.query("SELECT COUNT(*) FROM attempts WHERE mission=? AND state='complete'",(mission,)),[(1,)])

    def test_standalone_legend_and_extended_payload(self):
        state=self.load();state['offer']['candidates']=state['offer']['candidates'][:1]
        request=Request(101,1,1,2,1,'00'*16,0,0,growth_version=2,choice_version=1,phase_version=1,phase=1)
        data=choice_payload(request,state)
        self.assertEqual(len(data),380)
        self.assertEqual(struct.unpack_from('<I',data,13*4)[0],1)
        result={'nonce':'12'*16,'gold':0,'revision':0,'completed_mask':0,'growth_words':[1]+[0]*20,
                'requested_phase':1,'completed_phase':1,'total_phases':3}
        payload=response_payload(request,result,1)
        self.assertEqual((len(payload),struct.unpack_from('<I',payload,10*4)[0]),(380,2))

    def test_greedy_finite_caps_leave_three_same_tier_candidates(self):
        """Try to exhaust finite curses first, rather than evenly spreading picks."""
        from sc1.campaign.missions import load_missions
        for first in (101,201,301,401,501,601):
            counts={};rows={}
            for row in load_missions():
                if row['campaign_id']==progression.metadata(first)['campaign_id']:
                    rows.setdefault(row['ordinal'],row['mission_id'])
            for ordinal,mission in sorted(rows.items()):
                for phase in (1,2,3):
                    tier=rework_growth.curse_tier(mission,phase)
                    eligible=[x for x in self.catalog['curses'][15:] if x['rarity']==tier
                              and not rework_growth.retired(x) and counts.get(x['id'],0)<x.get('choice_max_stacks',x['max_stacks'])]
                    self.assertGreaterEqual(len(eligible),3,(first,ordinal,phase,tier))
                    selected=min(eligible,key=lambda x:(x['max_stacks'],-counts.get(x['id'],0),x['id']))
                    counts[selected['id']]=counts.get(selected['id'],0)+1
            legends=[counts.get(x['id'],0) for x in self.catalog['curses'][15:] if x['rarity']=='legendary']
            self.assertEqual(sum(legends),sum(rework_growth.curse_tier(m,2)=='legendary' for m in rows.values()))

    def test_common_curse_returns_between_upper_tier_phases(self):
        from sc1.campaign.missions import load_missions
        for mission in load_missions():
            mid=mission['mission_id']
            self.assertEqual(rework_growth.curse_tier(mid,1),'common')
            self.assertEqual(rework_growth.curse_tier(mid,3),'common')
            self.assertIn(rework_growth.curse_tier(mid,2),('uncommon','rare','epic','legendary'))
        for phase in (0,4,True,1.0):
            with self.assertRaises(ValueError):rework_growth.curse_tier(101,phase)

    def test_resource_economy_and_future_only_curse_eligibility(self):
        catalog=copy.deepcopy(self.catalog)
        for item in catalog['talents']:item['implemented']=False
        resource=next(x for x in catalog['talents'] if x.get('effect_ordinal')==2)
        resource['implemented']=True;resource['target_units']=[176,177,178,188]
        self.assertEqual([x['id'] for x in rework_growth.candidates(catalog,102,2,[],random.Random(1))],[resource['id']])
        curse=copy.deepcopy(catalog['curses'][15]);curse['missions']=[105]
        self.assertTrue(rework_growth.curse_eligible(curse,104))
        self.assertFalse(rework_growth.curse_eligible(curse,611))


if __name__=='__main__':unittest.main()
