import copy
import itertools
import json
import random
import sqlite3
import unittest
from unittest.mock import patch

from sc1.campaign import legendary_bundles as bundles, rework_growth, talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import load_catalog, encode_growth, GrowthError


class TowerBundles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(expected_version=2)
        cls.tower = cls.catalog['talents'][560]
        cls.by = {x['id']: x for x in cls.catalog['talents']}

    def pool(self, race):
        return [x for x in self.catalog['talents'] if x['race'] in (race, 'shared') and x['rarity'] == 'common'
                and bundles.paired_unit(x) and not x['effect'].get('offer_retired')]

    def test_tower_mixes_with_two_different_unit_manuals_in_each_race(self):
        self.assertEqual(bundles.bundle_size(self.tower), 3)
        for race in ('terran', 'zerg', 'protoss'):
            pairs = set()
            for seed in range(20):
                option = bundles.pair_options([self.tower], self.pool(race), random.Random(seed))[0]
                ids = bundles.member_ids(option, self.catalog)
                self.assertEqual(len(ids), 3)
                self.assertIn(self.tower['id'], ids)
                members = [self.by[x] for x in ids]
                self.assertEqual({x['race'] for x in members}, {race, 'shared'})
                self.assertTrue(all(bundles.bundle_size(x) == 3 for x in members))
                self.assertTrue(all(bundles.compatible(a, b) for a, b in itertools.combinations(members, 2)))
                pairs.add(tuple(ids))
            self.assertGreater(len(pairs), 1)

    def test_six_campaigns_offer_tower_only_in_a_triple(self):
        with patch.object(policy, 'rolled_rarity', return_value='common'):
            for mission in (109, 209, 309, 407, 506, 609):
                seen = False
                for seed in range(40):
                    for option in rework_growth.candidates(self.catalog, mission, 3, [], random.Random(seed)):
                        ids = bundles.member_ids(option, self.catalog)
                        if self.tower['id'] in ids:
                            seen = True
                            self.assertEqual(len(ids), 3)
                self.assertTrue(seen, mission)

    def test_triple_grants_all_ranks_native_wire_and_tower_cap_atomically(self):
        for mission, race in [(101, 'terran'), (201, 'zerg'), (301, 'protoss')]:
            option = bundles.pair_options([self.tower], self.pool(race), random.Random(73))[0]
            ids = bundles.member_ids(option, self.catalog)
            owned = []
            with sqlite3.connect(':memory:') as conn:
                for rank in (1, 2):
                    rework_growth.acquire_option(conn, mission, self.catalog, owned, option)
                    ranks = rework_growth.ranks(conn, mission)
                    self.assertTrue(all(ranks[x] == rank for x in ids))
                    words = encode_growth(self.catalog, owned, {}, ranks)
                    for identity in ids:
                        field = self.by[identity]['wire_storage']
                        self.assertEqual(words[field['word']] >> field['shift'] & ((1 << field['width']) - 1), rank)
                saved = copy.deepcopy(ranks)
                with self.assertRaises(GrowthError):
                    rework_growth.acquire_option(conn, mission, self.catalog, owned, option)
                self.assertEqual(rework_growth.ranks(conn, mission), saved)

    def test_catalog_refresh_keeps_issued_standalone_tower_exact(self):
        old = copy.deepcopy(self.catalog)
        item = old['talents'][560]
        item.pop('bundle_family')
        item.pop('bundle_families')
        item['effect']['qa_revision'] = 2026102265
        issued = json.dumps(item, ensure_ascii=False)
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)', (json.dumps(old),))
            conn.execute('CREATE TABLE issued_copy (text TEXT)')
            conn.execute('INSERT INTO issued_copy VALUES (?)', (issued,))
            rework_growth.save_ranks(conn, 101, {item['id']: 1})
            rework_growth.enable(conn)
            current = rework_growth.overlay(conn, old)
            self.assertEqual(bundles.bundle_size(current['talents'][560]), 3)
            self.assertEqual(bundles.member_ids(json.loads(issued), current), (item['id'],))
            self.assertEqual(conn.execute('SELECT text FROM issued_copy').fetchone()[0], issued)
            self.assertEqual(rework_growth.ranks(conn, 101), {item['id']: 1})
