"""Opening build choices use disposable records, including old issued offers."""
import copy
from contextlib import closing
import json
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from sc1.campaign import legendary_bundles as bundles, progression, rework_growth
from sc1.campaign import talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import load_catalog
from sc1.manager.store import GrowthChoicesPending, open_campaign_store


STARTS = (101, 201, 301, 401, 501, 601)


class OpeningLegendTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(expected_version=2)
        self.by_id = {item['id']: item for item in self.catalog['talents']}

    def usable(self, item, mission):
        entry = progression.metadata(mission)
        units = set(entry.get('available_unit_ids', entry.get('starting_unit_ids', ())))
        return (progression.item_eligible(item, mission, 'talent')
                and bool(units & set(item['target_units'])))

    def test_opening_and_midpoint_first_phase_have_guarantees(self):
        for first, midpoint in zip(STARTS, (106, 206, 306, 405, 505, 606)):
            actual = [(mission, phase) for mission in progression.campaign_missions(first)
                      for phase in (1, 2, 3)
                      if policy.reward_policy(mission, phase).guaranteed_legendary]
            self.assertEqual(actual, [(first, 1), (midpoint, 1)] + ([(515, 1)] if first==501 else []))
            self.assertFalse(policy.reward_policy(first, 2).guaranteed_legendary)
        self.assertFalse(any(policy.reward_policy(611, phase).guaranteed_legendary
                             for phase in (1, 2, 3)))

    def test_four_distinct_choices_include_future_units_and_at_most_one_global(self):
        before = copy.deepcopy(self.catalog)
        for first in STARTS:
            seen = set()
            for seed in range(40):
                draw = rework_growth.candidates(self.catalog, first, 1, [], random.Random(seed))
                self.assertEqual(len(draw), 4)
                pairs = set()
                globals_seen=0
                for candidate in draw:
                    members = bundles.member_ids(candidate, self.catalog)
                    if candidate['race']=='shared':
                        globals_seen+=1;self.assertEqual(len(members),1);continue
                    self.assertEqual(len(members), 2)
                    pairs.add(frozenset(members))
                    left, right = (self.by_id[identity] for identity in members)
                    self.assertTrue(bundles.compatible(left, right))
                    for item in (left, right):
                        self.assertEqual(item['race'], progression.metadata(first)['race'])
                        self.assertTrue(any(self.usable(item, mission)
                                            for mission in progression.campaign_missions(first)))
                    seen.update(members)
                self.assertLessEqual(globals_seen,1)
                self.assertEqual(len(pairs),4-globals_seen)
            expected = {item['id'] for item in self.catalog['talents']
                        if bundles.unit_legendary(item)
                        and item['race'] == progression.metadata(first)['race']}
            self.assertEqual(seen, expected)
            if first in (401, 601):
                self.assertTrue(any(not self.usable(self.by_id[identity], first) for identity in seen))
        self.assertEqual(self.catalog, before)

    def test_unusable_future_component_cannot_sneak_in_as_partner(self):
        catalog = copy.deepcopy(self.catalog)
        removed = next(item for item in catalog['talents']
                       if bundles.unit_legendary(item) and item['race'] == 'terran')
        removed['missions'] = []
        for seed in range(40):
            draw = rework_growth.candidates(catalog, 101, 1, [], random.Random(seed))
            self.assertEqual(len(draw), 4)
            self.assertTrue(all(removed['id'] not in bundles.member_ids(item, catalog) for item in draw))

    def test_natural_start_persists_pair_and_both_bits_in_both_checkpoint_protocols(self):
        for first in STARTS:
            for version in (1, 2):
                with self.subTest(first=first, version=version), tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / 'record.sqlite3'
                    store = open_campaign_store(path, curses_per_mission=0)

                    def load():
                        try:
                            return store.restore_growth_phase(first, 2, 1, phase_version=version)
                        except GrowthChoicesPending as pending:
                            return pending.state

                    state = load()
                    offer = copy.deepcopy(state['offer'])
                    self.assertEqual(offer['kind'], 'talent')
                    self.assertEqual(len(offer['candidates']), 4)
                    self.assertTrue(all(item['rarity'] == 'legendary' for item in offer['candidates']))
                    unit_slot=next(i+1 for i,x in enumerate(offer['candidates']) if x['race']!='shared')
                    members = bundles.member_ids(offer['candidates'][unit_slot-1], self.catalog)
                    self.assertEqual(len(members), 2)
                    store = open_campaign_store(path)
                    with patch.object(rework_growth, 'candidates', side_effect=AssertionError('No redraw')):
                        self.assertEqual(load()['offer'], offer)
                    result = store.choose_growth_phase_slot(offer['offer_id'], unit_slot, offer['revision'],
                        first, 2, choice_kind=1, phase=1, phase_version=version)
                    duplicate = store.choose_growth_phase_slot(offer['offer_id'], unit_slot, offer['revision'],
                        first, 2, choice_kind=1, phase=1, phase_version=version)
                    self.assertTrue(duplicate['duplicate'])
                    while result.get('offer'):
                        curse = result['offer']
                        self.assertEqual(curse['kind'], 'curse')
                        result = store.choose_growth_phase_slot(curse['offer_id'], 1, curse['revision'],
                            first, 2, choice_kind=2, phase=1, phase_version=version)
                    words = load()['growth_words']
                    for identity in members:
                        card = self.by_id[identity]
                        if field := card.get('wire_storage'):
                            self.assertTrue(words[field['word']] & (1 << field['shift']))
                        else:
                            bit = card['bit_index']
                            self.assertTrue(words[1 + bit // 32] & (1 << (bit % 32)))
                    store = open_campaign_store(path)
                    self.assertEqual(load()['growth_words'], words)
                    with closing(sqlite3.connect(path)) as conn:
                        saved = conn.execute('SELECT candidates_json FROM growth_offers WHERE offer_id=?',
                                             (offer['offer_id'],)).fetchone()[0]
                        self.assertEqual(json.loads(saved), offer['candidates'])

    def test_previously_issued_ordinary_start_remains_exact_without_retroactive_grant(self):
        ordinary = next(item for item in self.catalog['talents']
                        if item.get('rework_revision') == 5 and item['rarity'] == 'common'
                        and item['race'] in ('terran', 'shared') and item.get('repeatable'))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'record.sqlite3'
            store = open_campaign_store(path, curses_per_mission=0)

            def load():
                try:
                    return store.restore_growth_phase(101, 2, 1, phase_version=2)
                except GrowthChoicesPending as pending:
                    return pending.state

            with patch.object(rework_growth, 'candidates', return_value=[ordinary]):
                old = copy.deepcopy(load()['offer'])
            store = open_campaign_store(path)
            with patch.object(rework_growth, 'candidates', side_effect=AssertionError('No redraw')):
                self.assertEqual(load()['offer'], old)
            result = store.choose_growth_phase_slot(old['offer_id'], 1, old['revision'],
                101, 2, choice_kind=1, phase=1, phase_version=2)
            words = result['growth_words']
            self.assertTrue(words[1 + ordinary['bit_index'] // 32] & (1 << (ordinary['bit_index'] % 32)))
            for item in self.catalog['talents']:
                if bundles.unit_legendary(item):
                    bit = item['bit_index']
                    self.assertFalse(words[1 + bit // 32] & (1 << (bit % 32)))
            store = open_campaign_store(path)
            self.assertEqual(load()['growth_words'], words)
