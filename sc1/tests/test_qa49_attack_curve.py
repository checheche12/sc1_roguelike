"""Rebalance accumulated attack without changing progression or wire counts."""
import copy
from contextlib import closing
import json
import sqlite3
import tempfile
from pathlib import Path
import unittest

from sc1.campaign import rework_growth
from sc1.campaign.curse_balance import ATTACK_REVISION
from sc1.campaign.runtime_catalog import encode_growth, load_catalog
from sc1.manager.store import open_campaign_store, GrowthChoicesPending


class AttackCurve(unittest.TestCase):
    def test_totals_and_display_match_the_reduced_curve(self):
        card = load_catalog(expected_version=2)['curses'][17]
        effect = card['effect']
        self.assertEqual(effect['qa_revision'], ATTACK_REVISION)
        self.assertTrue(effect['unlimited_stacks'])
        first, step = effect['first_increment_percent'], effect['increment_step_percent']
        for count, total in ((0,0),(1,10),(2,22),(3,36),(5,70),(10,190)):
            self.assertEqual(sum(first + step*i for i in range(count)), total)
        self.assertIn('+10/+22/+36%', card['description'])
        self.assertIn('+70%', card['description'])

    def test_qa48_record_refresh_preserves_frozen_snapshots_and_progress(self):
        catalog = load_catalog(expected_version=2)
        prior = copy.deepcopy(catalog)
        prior['curses'][17]['effect'].update(qa_revision=2026102038,
            first_increment_percent=15, increment_step_percent=4)
        prior['curses'][17]['description'] = 'Prior attack curve +15/+34/+57%'
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'temporary.sqlite3'
            store = open_campaign_store(path)
            try:
                state = store.restore_growth_phase(101,2,1,phase_version=2)
            except GrowthChoicesPending as pending:
                state = pending.state
            while state['state'] == 'choosing':
                offer = state['offer']
                state = store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],
                    101,2,choice_kind=1 if offer['kind']=='talent' else 2,
                    phase=1,nonce=None,phase_version=2)
            with closing(sqlite3.connect(path)) as conn:
                self.assertGreater(conn.execute('SELECT COUNT(*) FROM growth_checkpoint_snapshots').fetchone()[0],0)
                conn.execute('UPDATE growth_rework_catalog SET catalog_json=?', (json.dumps(prior),))
                identity = catalog['curses'][17]['id']
                conn.execute('UPDATE growth_state SET revision=7,curses_json=?', (json.dumps({identity:5}),))
                conn.commit()
                before = list(conn.iterdump())
                rework_growth.enable(conn)
                refreshed = rework_growth.overlay(conn, load_catalog())
                after = list(conn.iterdump())
                self.assertEqual([x for x in before if not x.startswith('INSERT INTO "growth_rework_catalog"')],
                                 [x for x in after if not x.startswith('INSERT INTO "growth_rework_catalog"')])
                self.assertEqual(refreshed['curses'][17], catalog['curses'][17])
                for kind in ('talents','curses'):
                    for old, new in zip(prior[kind], refreshed[kind]):
                        if kind == 'curses' and old['byte_index'] == 17:
                            self.assertEqual(old['id'], new['id'])
                            self.assertEqual(old['source_description'], new['source_description'])
                        else:
                            self.assertEqual(old,new)
                for count in (5,255,256,1000,0xffffffff):
                    self.assertEqual(encode_growth(prior, [], {identity:count}),
                                     encode_growth(catalog, [], {identity:count}))


if __name__ == '__main__':
    unittest.main()
