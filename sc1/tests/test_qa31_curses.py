"""Four common stacking choices retain IDs and lossless wide wire counters."""
import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from sc1.campaign import rework_growth
from sc1.campaign.runtime_catalog import encode_growth, load_catalog


class FourCommonCurseTests(unittest.TestCase):
    def setUp(self):
        self.catalog = load_catalog(expected_version=2)

    def test_four_curves_caps_and_native_wire_storage_do_not_overlap(self):
        curves = {16: (20, 4), 17: (15, 4), 18: (20, 4), 19: (15, 1)}
        ids = {}
        for slot, (first, step) in curves.items():
            item = self.catalog['curses'][slot]
            ids[slot] = item['id']
            self.assertEqual(item['rarity'], 'common')
            self.assertEqual(item['max_stacks'], 0xffffffff)
            self.assertEqual(item['effect']['first_increment_percent'], first)
            self.assertEqual(item['effect']['increment_step_percent'], step)
            self.assertTrue(item['effect']['unlimited_stacks'])
        self.assertTrue(self.catalog['curses'][19]['effect']['attack_and_movement_speed'])
        self.assertTrue(self.catalog['curses'][18]['effect']['health_and_shields'])
        self.assertNotIn('speed_percent_per_stack', self.catalog['curses'][19]['effect'])
        manuals = [item for item in self.catalog['talents'] if item.get('repeatable') and not item.get('wire_storage')]
        self.assertTrue(all(item['rank_slot'] < 28 for item in manuals))
        ranks = {item['id']: 2 for item in manuals}
        for count in (1, 3, 4, 255, 256, 1000, 0xffffffff):
            curses = {identity: count for identity in ids.values()}
            words = encode_growth(self.catalog, list(ranks), curses, ranks)
            self.assertEqual(len(words), 65)
            for slot in curves:
                self.assertEqual(words[80 - slot], count)
                self.assertEqual((words[17 + slot // 4] >> (8 * (slot % 4))) & 255, min(count, 255))
            for item in manuals:
                self.assertEqual(words[33 + item['rank_slot']], 2)
            self.assertEqual(words[22], 0)

    def test_old_pin_refreshes_haste_and_health_shields_without_reindexing(self):
        old = copy.deepcopy(self.catalog)
        health = old['curses'][18]
        health['description'] = 'Previous health-only description'
        health['effect']['qa_revision'] = 2026101931
        health['effect'].pop('health_and_shields')
        haste = old['curses'][19]
        haste['rarity'] = 'uncommon'
        haste['max_stacks'] = 3
        haste['description'] = 'Previous attack and movement speed description'
        haste['effect'] = dict(type='rework_v5', ordinal=4, source_id=haste['id'],
                               qa_revision=2026101927, speed_percent_per_stack=10)
        with tempfile.TemporaryDirectory() as folder, closing(sqlite3.connect(':memory:')) as conn:
            path = Path(folder) / 'prior.json'
            path.write_text(json.dumps(old, ensure_ascii=False), encoding='utf8')
            rework_growth.enable(conn, path)
            rework_growth.enable(conn)
            updated = rework_growth.overlay(conn, load_catalog())
            current = next(item for item in updated['curses'] if item['id'] == haste['id'])
            self.assertEqual(current, self.catalog['curses'][19])
            self.assertEqual(current['source_description'], haste['source_description'])
            self.assertEqual(updated['curses'][18], self.catalog['curses'][18])
