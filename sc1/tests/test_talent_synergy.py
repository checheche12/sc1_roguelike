import copy
import json
import sqlite3
import unittest

from sc1.campaign import rework_growth, talent_synergy
from sc1.campaign.runtime_catalog import load_catalog, encode_growth


class TalentSynergy(unittest.TestCase):
    def setUp(self):
        self.catalog=load_catalog(expected_version=2)

    def test_ghost_and_area_contracts(self):
        cards=self.catalog['talents'][238:]
        self.assertEqual(cards[49]['effect']['weapon_damage_type'],3)
        self.assertIn('일반형',cards[49]['description'])
        self.assertNotIn('weapon_damage_type',cards[63]['effect'])
        for n in (44,62,127,149):
            self.assertEqual(cards[n]['effect']['radius_bonus_stacking'],'additive')

    def test_followup_combination_contracts(self):
        cards=self.catalog['talents'][238:]
        for n in (64,65):self.assertTrue(cards[n]['effect']['free_yamato_combines_triple_cast'])
        for n in (83,103):self.assertTrue(cards[n]['effect']['cloud_radius_bonuses_add'])
        for n in (16,162):self.assertTrue(cards[n]['effect']['attack_interval_bonuses_multiply'])
        self.assertEqual(cards[80]['effect']['radius_pixels'],128)
        self.assertEqual(self.catalog['talent_synergy_revision'],talent_synergy.FOLLOWUP_REVISION)

    def test_omni_battleship_migration_preserves_owned_talents(self):
        old=copy.deepcopy(self.catalog)
        ship=old['talents'][238+65]
        ship['description']='Previous battleship description'
        ship['effect']['qa_revision']=talent_synergy.FOLLOWUP_REVISION
        for key in ('auto_yamato_counts_independent_batteries','auto_yamato_retries_until_valid_launch'):
            ship['effect'].pop(key)
        ids=[old['talents'][238+n]['id'] for n in (47,57,64,65)]
        before=encode_growth(old,ids,{}, {})
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
            rework_growth.enable(conn)
            upgraded=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            self.assertEqual(upgraded['talents'],self.catalog['talents'])
            self.assertEqual(before,encode_growth(upgraded,ids,{}, {}))
        effect=self.catalog['talents'][238+65]['effect']
        self.assertEqual(effect['auto_yamato_every_primary_attacks'],4)
        self.assertTrue(effect['auto_yamato_counts_independent_batteries'])
        self.assertTrue(effect['auto_yamato_retries_until_valid_launch'])
        self.assertTrue(effect['auto_yamato_simultaneous_with_fourth_attack'])
        self.assertFalse(effect['auto_yamato_replaces_normal_attack'])
        self.assertEqual(effect['auto_yamato_launch_delay_frames'],0)

    def test_qa7_pin_updates_only_changed_followup_cards(self):
        old=copy.deepcopy(self.catalog)
        for card in old['talents'][238:]:
            if card['effect'].get('qa_revision')==talent_synergy.FOLLOWUP_REVISION:
                card['effect']['qa_revision']=talent_synergy.REVISION
                card['description']='Prior QA7 description'
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
            rework_growth.enable(conn)
            upgraded=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            self.assertEqual(upgraded['talents'],self.catalog['talents'])
            self.assertEqual(upgraded['curses'],old['curses'])
            self.assertEqual(upgraded['talent_synergy_revision'],talent_synergy.FOLLOWUP_REVISION)

    def test_live_manuals_do_not_claim_combined_cap_or_max_only(self):
        for card in self.catalog['talents'][238:]:
            effect=card['effect'];spec=effect.get('unit_growth',{})
            if effect.get('retired') or spec.get('kind') not in ('health','attack'):continue
            self.assertEqual(card['max_rank'],4)
            self.assertTrue(effect['independent_manuals_stack'])
            self.assertNotIn('합산해 최대 4',spec['description'])
            self.assertNotIn('높은 쪽만',spec['description'])

    def test_decorator_idempotent_and_preserves_wire(self):
        original=copy.deepcopy(self.catalog)
        modified=talent_synergy.decorate(copy.deepcopy(original))
        self.assertEqual(modified,talent_synergy.decorate(copy.deepcopy(modified)))
        for a,b in zip(original['talents'],modified['talents']):
            for field in ('id','bit_index','wire_storage','source_description'):
                self.assertEqual(a.get(field),b.get(field))
        self.assertEqual(original['curses'],modified['curses'])

    def test_qa6_pin_migrates_descriptions_without_changing_owned_ranks(self):
        old=copy.deepcopy(self.catalog)
        for card in old['talents'][238:]:
            if card['effect'].get('qa_revision')==talent_synergy.REVISION:
                card['effect']['qa_revision']=2026110301
                card['description']='Prior QA6 description'
        ids=[old['talents'][238+n]['id'] for n in (49,164,210,211,268,271,283)]
        ranks={old['talents'][238+n]['id']:4 for n in (210,211,268,271)}
        before=encode_growth(old,ids,{},ranks)
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
            rework_growth.enable(conn)
            upgraded=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            self.assertEqual(upgraded['talents'],self.catalog['talents'])
            self.assertEqual(before,encode_growth(upgraded,ids,{},ranks))


if __name__=='__main__':unittest.main()
