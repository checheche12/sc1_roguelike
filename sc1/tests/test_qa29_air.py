"""Current air tuning and future-offer migration; disposable SQLite only."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from sc1.campaign.runtime_catalog import load_catalog
from sc1.campaign import rework_growth


class AirBalanceTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog(expected_version=2)
        self.items={x['effect_ordinal']:x for x in self.catalog['talents'] if x.get('rework_revision')==5}

    def test_marine_has_one_normal_and_two_small_shots(self):
        effect=self.items[53]['effect']
        self.assertEqual((effect['primary_attack_percent'],effect['extra_attack_percent'],effect['extra_attack_count'],effect['total_attack_percent']),(100,35,2,170))
        self.assertIn('100%',self.items[53]['description'])
        self.assertIn('35%',self.items[53]['description'])

    def test_air_control_starts_uncommon_without_stacking_mobility(self):
        for ordinal in (47,69,110):
            item=self.items[ordinal]
            self.assertEqual(item['rarity'],'uncommon')
            self.assertFalse(item['effect']['air_control_stacks'])
            self.assertEqual(item['effect']['air_control_range_tiles'],1)
            self.assertEqual(item['effect']['air_control_speed_percent'],20)
        for ordinal in (153,157,160):
            self.assertEqual(self.items[ordinal]['effect']['production_time_reduction_percent'],20)

    def test_bc_legend_has_unconditional_primary_attack_trigger(self):
        effect=self.items[65]['effect']
        self.assertEqual(effect['auto_yamato_every_primary_attacks'],4)
        self.assertEqual(effect['auto_yamato_energy'],0)
        self.assertEqual(effect['secondary_layer_percent'],100)

    def test_future_offer_catalog_refreshes_rarity_without_touching_saved_offer(self):
        prior=copy.deepcopy(self.catalog)
        item=next(x for x in prior['talents'] if x['id']==self.items[47]['id'])
        item['rarity']='rare';item['effect']['qa_revision']=2026101610
        item['description']='Previous immutable candidate'
        with tempfile.TemporaryDirectory() as folder,sqlite3.connect(':memory:') as conn:
            path=Path(folder)/'catalog.json';path.write_text(json.dumps(prior),encoding='utf8')
            rework_growth.enable(conn,path)
            conn.execute('CREATE TABLE saved_offer (candidate_json TEXT NOT NULL)')
            saved=json.dumps(item,sort_keys=True);conn.execute('INSERT INTO saved_offer VALUES (?)',(saved,))
            path.write_text(json.dumps(self.catalog),encoding='utf8');rework_growth.enable(conn,path)
            pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            updated=next(x for x in pinned['talents'] if x['id']==item['id'])
            self.assertEqual(updated['rarity'],'uncommon')
            self.assertEqual(updated['source_description'],item['source_description'])
            self.assertEqual(conn.execute('SELECT candidate_json FROM saved_offer').fetchone()[0],saved)

    def test_both_yamato_legends_include_nonstacking_cast_speed(self):
        for ordinal in (64,65):
            effect=self.items[ordinal]['effect']
            self.assertEqual(effect['yamato_cast_speed_approx_multiplier'],3)
            self.assertEqual(effect['yamato_prelaunch_wait_frames'],0)
            self.assertFalse(effect['yamato_cast_speed_stacks'])
            self.assertIn('준비 동작 약 3배',self.items[ordinal]['description'])


if __name__=='__main__':
    unittest.main()
