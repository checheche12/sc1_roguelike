"""QA16 uses only seeded draws and disposable campaign records."""
import copy
from contextlib import closing
import json
import random
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sc1.campaign import legendary_bundles as bundles, rework_growth, talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import GrowthError, load_catalog
from sc1.manager.store import open_campaign_store, GrowthChoicesPending


class LegendaryBalanceTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(expected_version=2)

    def test_fifty_percent_standalone_and_free_infest_descriptions(self):
        for ordinal in (18, 85, 107):
            item = self.catalog['talents'][238 + ordinal]
            self.assertGreaterEqual(item['effect']['qa_revision'], 2026102038 if ordinal==107 else 2026101816)
            if ordinal==107:self.assertTrue(rework_growth.retired(item))
            self.assertNotIn('에너지', item['description'])
            if ordinal == 18:
                self.assertIn('50%', item['description'])
                self.assertEqual(item['effect']['benefit_power_quarters'], 4)
                self.assertFalse(bundles.unit_legendary(item))
            else:
                self.assertEqual(item['effect']['energy_cost'], 0)

    def test_all_six_openings_randomize_different_units_preserve_catalog(self):
        before = copy.deepcopy(self.catalog)
        partners = {}
        for mission in (101, 201, 301, 401, 501, 601):
            for seed in range(30):
                draw = rework_growth.candidates(self.catalog, mission, 1, [], random.Random(seed))
                self.assertGreaterEqual(len(draw), 2)
                pair_sets = set()
                for item in draw:
                    self.assertEqual(item['rarity'], 'legendary')
                    identities = bundles.member_ids(item, self.catalog)
                    if bundles.unit_legendary(item):
                        self.assertEqual(len(identities), 2)
                        self.assertNotIn(frozenset(identities), pair_sets)
                        pair_sets.add(frozenset(identities))
                        partners.setdefault(identities[0], set()).add(identities[1])
                        for identity in identities:
                            original = next(x for x in self.catalog['talents'] if x['id'] == identity)
                            self.assertIn(original['description'], item['description'])
                            self.assertIn(mission, original['missions'])
                    else:
                        self.assertEqual(len(identities), 1)
                        self.assertNotIn('bundled_talent_ids', item)
        self.assertTrue(any(len(values) >= 3 for values in partners.values()))
        self.assertEqual(self.catalog, before)

    def test_owned_components_and_single_family_never_get_bundled(self):
        legends = [x for x in self.catalog['talents'] if bundles.unit_legendary(x) and x['race']=='terran']
        owned = [x['id'] for x in legends if x['effect_ordinal'] != 61]
        draw = rework_growth.candidates(self.catalog, 102, 1, owned, random.Random(0))
        self.assertTrue(all(not bundles.unit_legendary(item) for item in draw))
        for item in draw:
            self.assertFalse(set(bundles.member_ids(item, self.catalog)) & set(owned))

    def test_saved_pair_acquires_both_reconnects_and_freezes_both_protocols(self):
        for version in (1, 2):
            with self.subTest(version=version), tempfile.TemporaryDirectory() as folder:
                path = Path(folder) / 'record.sqlite3'
                store = open_campaign_store(path, curses_per_mission=0)
                def load():
                    try:
                        return store.restore_growth_phase(101, 2, 1, phase_version=version)
                    except GrowthChoicesPending as pending:
                        return pending.state
                original_draw=rework_growth.candidates
                def fixed(catalog,mission,phase,owned,rng,**kw):
                    return original_draw(catalog,101,1,owned,random.Random(3),**kw)
                with patch('sc1.campaign.rework_growth.candidates',side_effect=fixed):
                    state = load()
                original = copy.deepcopy(state['offer'])
                self.assertEqual(load()['offer'], original)
                slot, candidate = next((i, x) for i, x in enumerate(original['candidates'], 1)
                                       if x.get('bundled_talent_ids'))
                identities = bundles.member_ids(candidate, self.catalog)
                result = store.choose_growth_phase_slot(original['offer_id'], slot, original['revision'],
                    101, 2, choice_kind=1, phase=1, phase_version=version)
                duplicate = store.choose_growth_phase_slot(original['offer_id'], slot, original['revision'],
                    101, 2, choice_kind=1, phase=1, phase_version=version)
                self.assertTrue(duplicate['duplicate'])
                while result.get('offer'):
                    offer = result['offer']
                    result = store.choose_growth_phase_slot(offer['offer_id'], 1, offer['revision'],
                        101, 2, choice_kind=1 if offer['kind']=='talent' else 2,
                        phase=1, phase_version=version)
                frozen = load()['growth_words']
                for identity in identities:
                    item = next(x for x in self.catalog['talents'] if x['id']==identity)
                    bit = item['bit_index']
                    self.assertTrue(frozen[1+bit//32] & (1 << (bit%32)))
                store = open_campaign_store(path)
                self.assertEqual(load()['growth_words'], frozen)
                with closing(sqlite3.connect(path)) as conn:
                    saved = conn.execute('SELECT candidates_json FROM growth_offers WHERE offer_id=?',
                                         (original['offer_id'],)).fetchone()[0]
                    self.assertEqual(json.loads(saved), original['candidates'])

    def test_pair_validation_rejects_owned_or_invalid_partner_atomically(self):
        draw = rework_growth.candidates(self.catalog, 101, 1, [], random.Random(3))
        item = next(x for x in draw if x.get('bundled_talent_ids'))
        identities = bundles.member_ids(item, self.catalog)
        owned = [identities[1]]
        with sqlite3.connect(':memory:') as conn:
            with self.assertRaises(GrowthError):
                rework_growth.acquire_option(conn, 106, self.catalog, owned, item)
            self.assertEqual(owned, [identities[1]])
            broken = copy.deepcopy(item)
            broken['bundled_talent_ids'][1] = self.catalog['talents'][256]['id']
            with self.assertRaises(GrowthError):
                bundles.member_ids(broken, self.catalog)
        old = next(x for x in self.catalog['talents'] if x['id']==identities[0])
        self.assertEqual(bundles.member_ids(old, self.catalog), (identities[0],))
