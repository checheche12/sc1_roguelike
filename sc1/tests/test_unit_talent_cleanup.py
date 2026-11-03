"""Retired unit cards preserve saved identities, but cannot grant new rewards."""
import copy
import json
import random
import sqlite3
import unittest
from contextlib import closing
from unittest.mock import patch

from sc1.campaign import legendary_bundles as bundles, rework_growth
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog
from sc1.campaign.talent_retirement import UNIT_CLEANUP_ORDINALS
from sc1.tests import test_rework_growth as fixtures


class UnitTalentCleanup(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(expected_version=2)
        self.ids = {self.catalog['talents'][238+n]['id'] for n in UNIT_CLEANUP_ORDINALS}

    def prior_catalog(self):
        old = copy.deepcopy(self.catalog)
        for n in UNIT_CLEANUP_ORDINALS:
            card = old['talents'][238+n]
            for flag in ('retired', 'runtime_disabled', 'offer_retired'):
                card['effect'].pop(flag, None)
            card['effect']['qa_revision'] = 2026102038
            card['description'] = card['source_description']
        for n in (72, 244):
            old['talents'][238+n]['effect']['qa_revision'] = 2026102038
            old['talents'][238+n]['description'] = 'Previous manual description'
        return old

    def test_exact_scope_and_useful_reaver_scourge_cards_retained(self):
        self.assertEqual(UNIT_CLEANUP_ORDINALS, {164,173,210,211,245,246,264,265,283,303,314})
        for n in UNIT_CLEANUP_ORDINALS:
            card = self.catalog['talents'][238+n]
            for flag in ('retired', 'runtime_disabled', 'offer_retired'):
                self.assertTrue(card['effect'][flag])
            self.assertNotEqual(card['description'], card['source_description'])
        for n in (87,96,117,141,174,181,244):
            card = self.catalog['talents'][238+n]
            self.assertFalse(rework_growth.retired(card), card['name'])
            self.assertFalse(card['effect'].get('offer_retired'), card['name'])
        for card in self.catalog['talents'][238:]:
            if card.get('target_units') == [50]:
                self.assertTrue(rework_growth.retired(card), card['name'])

    def test_current_and_old_pins_never_offer_deleted_bundle_members(self):
        for catalog in (self.catalog, self.prior_catalog()):
            for mission in (201,205,210,601,608,610,301,305,310,402,408):
                for phase in (1,2,3):
                    for seed in range(8):
                        choices = rework_growth.candidates(catalog,mission,phase,[],random.Random(seed))
                        for card in choices:
                            self.assertTrue(self.ids.isdisjoint(bundles.member_ids(card,catalog)))
            with closing(sqlite3.connect(':memory:')) as conn:
                for identity in self.ids:
                    with self.assertRaises(GrowthError) as caught:
                        rework_growth.acquire(conn,201,catalog,[],identity)
                    self.assertEqual(caught.exception.code,'retired_talent')

    def test_owned_wire_and_historical_pairs_survive(self):
        old = self.prior_catalog()
        for n in UNIT_CLEANUP_ORDINALS:
            card = old['talents'][238+n]
            partner = next(x for x in old['talents'][238:]
                           if x['id'] not in self.ids and bundles.compatible(card,x))
            pair = dict(card,bundled_talent_ids=[card['id'],partner['id']])
            self.assertEqual(bundles.member_ids(pair,self.catalog),(card['id'],partner['id']))
            ids = [card['id'],partner['id']]
            ranks = {x['id']:4 for x in (card,partner) if x.get('repeatable')}
            self.assertEqual(encode_growth(old,ids,{},ranks),encode_growth(self.catalog,ids,{},ranks))
            self.assertTrue(rework_growth.option_has_retired(pair,old))

    def test_migration_preserves_every_identity_and_unrelated_card(self):
        old = self.prior_catalog()
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old,ensure_ascii=False),))
            rework_growth.enable(conn)
            actual = json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            for before,after in zip(old['talents'],actual['talents']):
                for field in ('id','bit_index','wire_storage','source_description'):
                    self.assertEqual(before.get(field),after.get(field))
                if before.get('effect_ordinal') in UNIT_CLEANUP_ORDINALS | {72,244} and before.get('rework_revision')==5:
                    self.assertEqual(after,self.catalog['talents'][after['bit_index']])
                else:
                    self.assertEqual(before,after)
            self.assertEqual(actual['curses'],old['curses'])
            first = conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0]
            rework_growth.enable(conn)
            self.assertEqual(first,conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])

    def test_scourge_description_and_old_manual_agree(self):
        card = self.catalog['talents'][238+244]
        self.assertEqual(card['rarity'],'common')
        self.assertEqual(card['max_rank'],4)
        self.assertEqual(card['effect']['attack_per_rank'],30)
        self.assertIn('+120',card['description'])
        self.assertNotIn('공격 간격',card['description'])
        old_manual = self.catalog['talents'][238+72]
        self.assertEqual(old_manual['effect']['scourge_attack_per_rank'],30)
        self.assertEqual(old_manual['effect']['mutalisk_attack_per_rank'],5)
        self.assertEqual(old_manual['effect']['guardian_attack_per_rank'],6)


class PendingUnitRetirement(unittest.TestCase):
    setUp = fixtures.ReworkGrowthTests.setUp
    load = fixtures.ReworkGrowthTests.load
    query = fixtures.ReworkGrowthTests.query

    def test_pending_pair_reissued_and_original_json_archived(self):
        card = copy.deepcopy(self.catalog['talents'][238+245])
        partner = next(x for x in self.catalog['talents'][238:]
                       if x.get('target_units')==[37,54] and x.get('effect',{}).get('unit_growth',{}).get('kind')=='health')
        # The removed talent may be the second member of an old offer.
        pair = dict(partner,bundled_talent_ids=[partner['id'],card['id']])
        with patch.object(rework_growth,'candidates',return_value=[pair]):
            state = self.load(mission=201)
        original = state['offer']
        raw = self.query('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(original['offer_id'],))[0][0]
        resumed = self.load(mission=201)
        self.assertNotEqual(resumed['offer']['offer_id'],original['offer_id'])
        for choice in resumed['offer']['candidates']:
            self.assertNotIn(card['id'],bundles.member_ids(choice,self.catalog))
        self.assertEqual(self.query('SELECT candidates_json FROM growth_offer_retirement_history WHERE offer_id=?',
                                    (original['offer_id'],)),[(raw,)])

