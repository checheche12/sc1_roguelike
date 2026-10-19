"""Guardian manual description refresh keeps the stored source and old offer."""
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


class GuardianManualTests(unittest.TestCase):
    def test_manual_refresh_preserves_old_candidate_and_both_guardian_variants(self):
        current = load_catalog(expected_version=2)
        manual = current['talents'][238 + 72]
        self.assertEqual(manual['effect']['mutalisk_guardian_attack_per_rank'], 6)
        self.assertEqual(manual['effect']['other_air_attack_per_rank'], 3)
        self.assertTrue({43, 44, 55, 56} <= set(manual['target_units']))
        prior = copy.deepcopy(current)
        old = prior['talents'][238 + 72]
        old['description'] = 'Previous Guardian +3 description'
        old['effect']['qa_revision'] = 2026101610
        old['effect'].pop('mutalisk_guardian_attack_per_rank')
        old['effect'].pop('other_air_attack_per_rank')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'catalog.json'
            db = Path(folder) / 'record.sqlite3'
            path.write_text(json.dumps(prior), encoding='utf8')
            store = CampaignStore(db, new_profile='original', runtime_catalog_path=path)

            def load():
                try:
                    return store.restore_growth_phase(101, 2, 1)
                except GrowthChoicesPending as pending:
                    return pending.state

            with patch.object(rework_growth, 'candidates', return_value=[old]):
                offer = copy.deepcopy(load()['offer'])
            path.write_text(json.dumps(current), encoding='utf8')
            self.assertEqual(load()['offer'], offer)
            with closing(sqlite3.connect(db)) as conn:
                pin = json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
                updated = pin['talents'][238 + 72]
                self.assertEqual(updated['description'], manual['description'])
                self.assertEqual(updated['effect'], manual['effect'])
                self.assertEqual(updated['source_description'], old['source_description'])
