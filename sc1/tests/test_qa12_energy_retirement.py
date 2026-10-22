"""QA12 uses disposable records; retired wire identities remain historical."""
from contextlib import closing
import copy
import json
import random
import sqlite3
import unittest
from unittest.mock import patch
from sc1.campaign import rework_growth, talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import GrowthError, encode_growth
from sc1.tests import test_rework_growth as fixtures


class Qa12Tests(unittest.TestCase):
    setUp=fixtures.ReworkGrowthTests.setUp
    load=fixtures.ReworkGrowthTests.load
    pick=fixtures.ReworkGrowthTests.pick
    finish=fixtures.ReworkGrowthTests.finish
    query=fixtures.ReworkGrowthTests.query

    def test_energy_metadata_names_acquisition_and_completed_production(self):
        for ordinal in (36,76,118):
            item=self.catalog['talents'][238+ordinal]
            self.assertIn('생산 완료',item['description'])
            self.assertIn('200을 한 번',item['description'])
            self.assertTrue(item['effect']['energy_grant_on_production'])
            self.assertTrue(item['effect']['energy_grant_on_acquisition'])

    def test_retired_card_never_drawn_even_from_an_old_pinned_catalog(self):
        old=copy.deepcopy(self.catalog);card=old['talents'][252];card['effect'].pop('retired',None)
        for mission in (101,201,301,401,501,601):
            for phase in (1,2,3):
                with patch.object(policy,'rolled_rarity',return_value='epic'):
                    chosen=rework_growth.candidates(old,mission,phase,[],random.Random(12))
                self.assertNotIn(card['id'],{x['id'] for x in chosen})

    def test_retired_acquisition_rejected_but_old_owned_wire_bit_survives(self):
        card=self.catalog['talents'][252]
        self.assertTrue(card['effect']['retired'])
        with closing(sqlite3.connect(':memory:')) as conn:
            with self.assertRaises(GrowthError) as caught:
                rework_growth.acquire(conn,101,self.catalog,[],card['id'])
        self.assertEqual(caught.exception.code,'retired_talent')
        words=encode_growth(self.catalog,[card['id']],{})
        self.assertTrue(words[1+252//32]&(1<<(252%32)))

    def test_pending_retired_offer_reissued_with_original_json_archived(self):
        card=self.catalog['talents'][252]
        with patch.object(rework_growth,'candidates',return_value=[card]):state=self.load()
        original=state['offer'];raw=self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(original['offer_id'],))[0][0]
        resumed=self.load()
        self.assertNotEqual(resumed['offer']['offer_id'],original['offer_id'])
        self.assertNotIn(card['id'],{x['id'] for x in resumed['offer']['candidates']})
        self.assertEqual(self.query('SELECT candidates_json FROM growth_offer_retirement_history WHERE offer_id=?',(original['offer_id'],)),[(raw,)])
        self.assertEqual(json.loads(raw)[0]['id'],card['id'])

    def test_high_health_infest_retired_in_old_catalog_and_pending_offer(self):
        card=self.catalog['talents'][323]
        self.assertTrue(card['effect']['retired'])
        self.assertTrue(card['effect']['runtime_disabled'])
        old=copy.deepcopy(self.catalog)
        for flag in ('retired','runtime_disabled','offer_retired'):
            old['talents'][323]['effect'].pop(flag,None)
        for phase in (1,2,3):
            with patch.object(policy,'rolled_rarity',return_value='rare'):
                chosen=rework_growth.candidates(old,201,phase,[],random.Random(71))
            self.assertNotIn(card['id'],{x['id'] for x in chosen})
        with closing(sqlite3.connect(':memory:')) as conn:
            with self.assertRaises(GrowthError) as caught:
                rework_growth.acquire(conn,201,old,[],card['id'])
        self.assertEqual(caught.exception.code,'retired_talent')
        words=encode_growth(self.catalog,[card['id']],{})
        self.assertTrue(words[1+323//32]&(1<<(323%32)))
        with patch.object(rework_growth,'candidates',return_value=[card]):
            state=self.load(mission=201)
        original=state['offer']
        raw=self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(original['offer_id'],))[0][0]
        resumed=self.load(mission=201)
        self.assertNotEqual(resumed['offer']['offer_id'],original['offer_id'])
        self.assertNotIn(card['id'],{x['id'] for x in resumed['offer']['candidates']})
        self.assertEqual(self.query('SELECT candidates_json FROM growth_offer_retirement_history WHERE offer_id=?',(original['offer_id'],)),[(raw,)])
