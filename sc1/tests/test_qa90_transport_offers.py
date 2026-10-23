"""Offer-only retirement, using disposable catalogs and in-memory records."""
import copy
import json
import random
import sqlite3
import unittest
from contextlib import closing

from sc1.campaign import rework_growth
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog


class TransportOffers(unittest.TestCase):
    def test_old_and_current_catalogs_exclude_all_three_transport_cards(self):
        current = load_catalog(expected_version=2)
        old = copy.deepcopy(current)
        cards = [old['talents'][238 + n] for n in (33, 74, 115)]
        for card in cards:
            for flag in ('offer_retired', 'transport_speed_offer_removed'):
                card['effect'].pop(flag, None)
            card['effect']['qa_revision'] = 2026102265
        removed = {card['id'] for card in cards}
        for catalog in (old, current):
            for mission in (101, 106, 201, 206, 301, 306, 501, 601):
                for phase in (1, 2, 3):
                    for seed in range(15):
                        options = rework_growth.candidates(catalog, mission, phase, [], random.Random(seed))
                        for option in options:
                            self.assertTrue(removed.isdisjoint(option.get('bundled_talent_ids', [option['id']])))
            with closing(sqlite3.connect(':memory:')) as conn:
                for card in cards:
                    with self.assertRaises(GrowthError) as error:
                        rework_growth.acquire(conn, 101, catalog, [], card['id'])
                    self.assertEqual(error.exception.code, 'retired_talent')
        # Removing future offers must not alter already-owned wire identities.
        self.assertEqual(encode_growth(old, list(removed), {}), encode_growth(current, list(removed), {}))
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)', (json.dumps(old),))
            rework_growth.enable(conn)
            migrated = json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            for card in cards:
                actual = migrated['talents'][card['bit_index']]
                self.assertTrue(actual['effect']['offer_retired'])
                self.assertEqual(actual['source_description'], card['source_description'])
                self.assertEqual(actual['effect']['movement_speed_bonus_percent'], 40)
                self.assertFalse(actual['effect'].get('runtime_disabled', False))

    def test_radiation_descriptions_and_combination_metadata(self):
        catalog = load_catalog(expected_version=2)
        chain, mechanical = (catalog['talents'][238 + n] for n in (61, 198))
        self.assertEqual(chain['effect']['mechanical_infection_requires_ordinal'], 198)
        self.assertTrue(mechanical['effect']['mechanical_chain_synergy'])
        self.assertNotIn('분자 붕괴', chain['description'])
        self.assertIn('전염', mechanical['description'])
