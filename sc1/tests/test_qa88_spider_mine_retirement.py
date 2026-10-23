"""Spider Mine legend retirement uses disposable records, never player saves."""
import copy
import json
import random
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from sc1.campaign import legendary_bundles as bundles, rework_growth
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog


class SpiderMineRetirement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(expected_version=2)
        cls.card = cls.catalog['talents'][298]

    def prior_catalog(self):
        old = copy.deepcopy(self.catalog)
        card = old['talents'][298]
        for flag in ('retired', 'runtime_disabled', 'offer_retired'):
            card['effect'].pop(flag, None)
        card['effect']['qa_revision'] = 2026102046
        card['description'] = '스파이더 마인의 일반 공격 피해 +150%.'
        return old

    def test_current_legend_disabled_and_fragment_epic_retained(self):
        self.assertEqual(self.card['name'], '대형 성형 지뢰')
        self.assertEqual(self.card['rarity'], 'legendary')
        for flag in ('retired', 'runtime_disabled', 'offer_retired'):
            self.assertTrue(self.card['effect'][flag])
        self.assertNotIn(60, self.catalog['single_target_legend_ordinals'])
        fragment = next(x for x in self.catalog['talents'] if x['name'] == '지뢰 파편')
        self.assertEqual(fragment['rarity'], 'epic')
        self.assertFalse(rework_growth.retired(fragment))
        from sc1.campaign.legend_focus import generate_header
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / 'sc1/native_campaign/plugin/include/legend_focus.generated.h'
            target.parent.mkdir(parents=True)
            generate_header(self.catalog, root)
            self.assertNotIn('{60u,', target.read_text(encoding='utf8'))

    def test_current_and_old_pins_never_offer_mine_as_either_member(self):
        for catalog in (self.catalog, self.prior_catalog()):
            for mission in (101, 106, 109, 501, 505, 508):
                for phase in (1, 2, 3):
                    for seed in range(20):
                        for item in rework_growth.candidates(catalog, mission, phase, [], random.Random(seed)):
                            self.assertNotIn(self.card['id'], bundles.member_ids(item, catalog))
            with closing(sqlite3.connect(':memory:')) as conn:
                with self.assertRaises(GrowthError) as error:
                    rework_growth.acquire(conn, 101, catalog, [], self.card['id'])
                self.assertEqual(error.exception.code, 'retired_talent')

    def test_owned_wire_bit_and_historical_pair_still_decode(self):
        partner = self.catalog['talents'][296]
        pair = dict(self.card, bundled_talent_ids=[self.card['id'], partner['id']])
        self.assertEqual(bundles.member_ids(pair, self.catalog), (self.card['id'], partner['id']))
        ids = [self.card['id'], partner['id']]
        before = encode_growth(self.prior_catalog(), ids, {})
        after = encode_growth(self.catalog, ids, {})
        self.assertEqual(before, after)
        self.assertTrue(after[1 + 298 // 32] & (1 << (298 % 32)))

    def test_pinned_catalog_migration_retains_identity_source_and_other_entries(self):
        old = self.prior_catalog()
        with closing(sqlite3.connect(':memory:')) as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)', (json.dumps(old, ensure_ascii=False),))
            rework_growth.enable(conn)
            migrated = json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            self.assertEqual(migrated['talents'][298], self.card)
            for index, item in enumerate(old['talents']):
                if index != 298:
                    self.assertEqual(migrated['talents'][index], item)
            self.assertEqual(migrated['curses'], old['curses'])
            for field in ('id', 'bit_index', 'source_description'):
                self.assertEqual(migrated['talents'][298][field], old['talents'][298][field])
