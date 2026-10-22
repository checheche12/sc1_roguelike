"""A refreshed Mutalisk card must not rewrite an already issued offer."""
import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from sc1.campaign import rework_growth
from sc1.campaign.runtime_catalog import load_catalog
from sc1.manager.store import CampaignStore, GrowthChoicesPending


class MutaliskLegendTests(unittest.TestCase):
    def test_new_damage_description_refreshes_without_rewriting_issued_offer(self):
        current = load_catalog(expected_version=2)
        card = current['talents'][238 + 105]
        self.assertGreaterEqual(card['effect']['qa_revision'], 2026101932)
        self.assertEqual(card['effect']['projectile_damage_percent'], 200)
        self.assertEqual(card['effect']['projectile_count'], 1)
        self.assertIn('+100%', card['description'])
        self.assertIn('6번',card['description'])
        self.assertEqual(card['effect']['bounce_damage_numerators'],[7,6,5,4,3,2,1])
        self.assertNotIn('240%', card['description'])
        prior = copy.deepcopy(current)
        old = prior['talents'][238 + 105]
        old['description'] = card['description'].replace('+100%', '+240%')
        old['effect']['qa_revision'] = 2026101610
        old['effect'].pop('projectile_damage_percent')
        old['effect'].pop('projectile_count')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'catalog.json'
            db = Path(folder) / 'record.sqlite3'
            path.write_text(json.dumps(prior), encoding='utf8')
            store = CampaignStore(db, new_profile='original', runtime_catalog_path=path)

            def load():
                try:
                    return store.restore_growth_phase(201, 2, 1)
                except GrowthChoicesPending as pending:
                    return pending.state

            with patch.object(rework_growth, 'candidates', return_value=[old]):
                offer = copy.deepcopy(load()['offer'])
            with closing(sqlite3.connect(db)) as conn:
                issued = conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall()
            path.write_text(json.dumps(current), encoding='utf8')
            self.assertEqual(load()['offer'], offer)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall(), issued)
                pinned = json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            refreshed = pinned['talents'][238 + 105]
            for field in ('description', 'effect', 'source_description', 'bit_index', 'id'):
                self.assertEqual(refreshed[field], card[field])
            self.assertEqual(refreshed['source_description'], old['source_description'])


if __name__ == '__main__':
    unittest.main()
