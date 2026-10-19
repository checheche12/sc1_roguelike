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
from sc1.manager.store import CampaignStore,GrowthChoicesPending

class AirBalanceTests(unittest.TestCase):
    def test_ground_air_and_interceptor_profiles_are_explicit(self):
        c=load_catalog(expected_version=2)
        for bit,expected in ((269,{'wraith_ground_attack_per_rank':6,'wraith_air_attack_per_rank':12}),
                            (350,{'scout_ground_attack_per_rank':6,'scout_air_projectile_attack_per_rank':6,'scout_air_salvo_attack_per_rank':12,'interceptor_attack_per_rank':1})):
            card=c['talents'][bit]
            self.assertGreaterEqual(card['effect']['qa_revision'],2026102037)
            for key,value in expected.items():self.assertEqual(card['effect'][key],value)
            self.assertEqual(card['max_rank'],4)
            self.assertIn('지상',card['description']);self.assertIn('공중',card['description'])

    def test_illusion_blast_includes_shields_expiry_and_all_enemies(self):
        card=load_catalog(expected_version=2)['talents'][385];effect=card['effect']
        self.assertGreaterEqual(effect['qa_revision'],2026102037)
        self.assertEqual(effect['death_blast_radius_pixels'],128)
        self.assertTrue(effect['death_blast_all_enemies']);self.assertTrue(effect['death_blast_on_expiry'])
        self.assertEqual(effect['death_blast_max_hp_percent'],50);self.assertEqual(effect['death_blast_max_shield_percent'],50)
        self.assertEqual(effect['death_blast_damage_cap'],150)
        self.assertIn('모든 적',card['description']);self.assertIn('수명 만료',card['description'])

    def test_current_descriptions_refresh_without_rewriting_issued_offers(self):
        current=load_catalog(expected_version=2)
        for bit,mission in ((269,101),(350,301),(385,301)):
            with self.subTest(bit=bit),tempfile.TemporaryDirectory() as folder:
                prior=copy.deepcopy(current);old=prior['talents'][bit];old['description']='Previous issued text for '+str(bit)
                old['effect']={'type':'rework_v5','ordinal':old['effect_ordinal'],'source_id':old['id'],'qa_revision':2026101929}
                path=Path(folder)/'catalog.json';db=Path(folder)/'disposable.sqlite3';path.write_text(json.dumps(prior),encoding='utf8')
                store=CampaignStore(db,new_profile='original',runtime_catalog_path=path)
                def load():
                    try:return store.restore_growth_phase(mission,2,1)
                    except GrowthChoicesPending as pending:return pending.state
                with patch.object(rework_growth,'candidates',return_value=[old]):offer=copy.deepcopy(load()['offer'])
                with closing(sqlite3.connect(db)) as conn:issued=conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall()
                path.write_text(json.dumps(current),encoding='utf8');self.assertEqual(load()['offer'],offer)
                with closing(sqlite3.connect(db)) as conn:
                    self.assertEqual(conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall(),issued)
                    pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
                for field in ('id','bit_index','description','effect','source_description'):
                    self.assertEqual(pinned['talents'][bit][field],current['talents'][bit][field])
