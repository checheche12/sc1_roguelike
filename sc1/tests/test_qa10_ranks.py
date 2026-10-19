"""QA10 rank changes use disposable records, including a real pre-cap offer."""
import copy
import json
import random
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from sc1.tests import test_rework_growth as fixtures
from sc1.campaign import growth, progression, rank_policy, rework_growth, talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import GrowthError, encode_growth


class Qa10RankTests(unittest.TestCase):
    setUp=fixtures.ReworkGrowthTests.setUp
    load=fixtures.ReworkGrowthTests.load
    pick=fixtures.ReworkGrowthTests.pick
    finish=fixtures.ReworkGrowthTests.finish
    query=fixtures.ReworkGrowthTests.query

    def test_slots_cap_and_health_repeatability(self):
        old=(8,9,11,12,29,30,31,70,71,72,111,112)
        for slot,ordinal in enumerate(old+rank_policy.HEALTH_ORDINALS):
            item=self.catalog['talents'][238+ordinal]
            self.assertEqual((item['rank_slot'],item['repeatable'],item['max_rank']),(slot,True,4))
        item=self.catalog['talents'][238+26]
        self.assertEqual(encode_growth(self.catalog,[item['id']],{})[33+12],1)

    def test_cap_keeps_raw_historical_rank_and_filters_future_offers(self):
        item=self.catalog['talents'][238+8];owned=[item['id']]
        with closing(sqlite3.connect(':memory:')) as conn:
            rework_growth.save_ranks(conn,101,{item['id']:9})
            with self.assertRaises(GrowthError) as caught:
                rework_growth.acquire(conn,101,self.catalog,owned,item['id'])
            self.assertEqual(caught.exception.code,'talent_rank_limit')
            self.assertEqual(rework_growth.ranks(conn,101),{item['id']:9})
            self.assertEqual(rework_growth.encode(conn,101,self.catalog,owned,{})[33],4)
        for seed in range(30):
            draw=rework_growth.candidates(self.catalog,101,1,owned,random.Random(seed),rank_counts={item['id']:9})
            self.assertNotIn(item['id'],{x['id'] for x in draw})

    def test_pre_qa10_unique_health_becomes_rank_two_without_snapshot_rewrite(self):
        health=self.catalog['talents'][238+26];prior=copy.deepcopy(self.catalog)
        for item in prior['talents']:
            if item.get('effect_ordinal') in rank_policy.HEALTH_ORDINALS:
                item['repeatable']=False;item.pop('rank_slot',None);item.pop('max_rank',None)
            item['effect']['qa_revision']=2026101609
        self.catalog_path.write_text(json.dumps(prior),encoding='utf8')
        with patch.object(rework_growth,'candidates',return_value=[prior['talents'][238+26]]):
            first=self.finish()
        before=self.query('SELECT words_json FROM growth_phase_snapshots')
        self.assertEqual(first['growth_words'][33+12],0)
        self.catalog_path.write_text(json.dumps(self.catalog),encoding='utf8')
        self.load()  # A new manager reconnects using the current v2 catalog.
        with patch.object(rework_growth,'candidates',return_value=[health]):
            second=self.finish(phase=2,nonce=first['nonce'])
        self.assertEqual(second['growth_words'][33+12],2)
        self.assertEqual(self.query('SELECT words_json FROM growth_phase_snapshots WHERE phase=1'),before)
        self.assertEqual(self.query('SELECT rank FROM growth_manual_ranks'),[(2,)])

    def test_all_capped_pending_offer_archived_and_reissued_with_new_id(self):
        manual=self.catalog['talents'][238+8]
        with patch.object(rework_growth,'candidates',return_value=[manual]):state=self.load()
        original=state['offer'];serialized=self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(original['offer_id'],))[0][0]
        with closing(sqlite3.connect(self.path)) as conn:
            conn.row_factory=sqlite3.Row
            row=growth._state(conn,101)
            growth._save_state(conn,101,row['revision'],[manual['id']],{})
            rework_growth.save_ranks(conn,101,{manual['id']:4});conn.commit()
        resumed=self.load();self.assertNotEqual(resumed['offer']['offer_id'],original['offer_id'])
        self.assertNotIn(manual['id'],{x['id'] for x in resumed['offer']['candidates']})
        self.assertEqual(self.query('SELECT candidates_json FROM growth_offer_cap_history'),[(serialized,)])
        with self.assertRaises(GrowthError):self.pick(state)
        with closing(sqlite3.connect(self.path)) as conn:self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])

    def test_six_campaigns_reach_final_without_caps_or_reward_deadlocks(self):
        for first in (101,201,301,401,501,601):
            for seed in range(12):
                rng=random.Random(seed);owned=[];counts={}
                for reward in policy.campaign_schedule(first):
                    mission=next(m for m in progression.campaign_missions(first) if progression.metadata(m)['ordinal']==reward.ordinal)
                    choices=rework_growth.candidates(self.catalog,mission,reward.phase,owned,rng,rank_counts=counts)
                    self.assertTrue(choices,(first,seed,reward))
                    self.assertTrue(all(not rank_policy.exhausted(x,owned,counts) for x in choices))
                    if reward.guaranteed_legendary:self.assertTrue(all(x['rarity']=='legendary' for x in choices))
                    chosen=next((x for x in choices if x.get('repeatable')),choices[0])
                    if chosen.get('repeatable'):
                        counts[chosen['id']]=counts.get(chosen['id'],0)+1
                        self.assertLessEqual(counts[chosen['id']],4)
                    if chosen['id'] not in owned:owned.append(chosen['id'])

    def test_depleted_ordinary_tiers_can_use_remaining_military_reward(self):
        candidate=policy.Candidate('remaining','rare')
        with patch.object(policy,'rolled_rarity',return_value='common'):
            self.assertEqual(policy.draw_candidates(policy.reward_policy(102,1),[candidate],[],random.Random(1),exhausted_fallback=True),(candidate,))
