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
from sc1.campaign import talent_balance
from sc1.manager.store import CampaignStore, GrowthChoicesPending

class CarrierBurstTests(unittest.TestCase):
    def test_existing_identity_gets_new_explicit_effect(self):
        catalog=load_catalog(expected_version=2);card=catalog['talents'][368]
        self.assertEqual(card['id'],'f52833ba-5dad-5430-8ed7-6d2cf38d7290')
        self.assertEqual(card['effect_ordinal'],130)
        from sc1.campaign.effect_copy import clean_description
        self.assertEqual(card['description'],clean_description(talent_balance.DESCRIPTIONS[130]))
        self.assertIn('최대 8기',card['description'])
        self.assertNotIn('16기',card['description'])
        effect=card['effect']
        self.assertGreaterEqual(effect['qa_revision'],2026102035)
        self.assertEqual(effect['benefit_power_quarters'],4)
        self.assertEqual(effect['burst_launch_limit'],8)
        self.assertEqual(effect['capacity_bonus'],0)
        self.assertEqual(effect['interceptor_health_multiplier'],2)
        self.assertEqual(effect['interceptor_shield_multiplier'],2)
        self.assertTrue(effect['native_capacity_unchanged'])

    def test_original_text_and_all_legacy_wire_slots_stay_recoverable(self):
        card=load_catalog(expected_version=2)['talents'][368]
        original=talent_balance.historical(copy.deepcopy(card))
        self.assertEqual(original['source_description'],card['source_description'])
        self.assertIn('4기 추가',card['source_description'])
        self.assertEqual(original['id'],card['id'])
        self.assertEqual(original['bit_index'],368)
        self.assertFalse(card['repeatable'])

    def test_old_hangar_adapter_is_not_current_coverage(self):
        catalog=load_catalog(expected_version=2);card=catalog['talents'][368]
        coverage=catalog['native_coverage']['items'][card['id']]
        self.assertEqual(coverage['required_external_adapter_parts'],[])
        self.assertIn('carrier_native_burst_eight',coverage['adapter_parts_implemented_here'])
        self.assertFalse(coverage['actual_engine_verified'])

    def test_refresh_preserves_the_old_issued_hangar_offer(self):
        current=load_catalog(expected_version=2);card=current['talents'][368]
        prior=copy.deepcopy(current);old=prior['talents'][368]
        old['description']='캐리어의 인터셉터 한도가 8기 늘어납니다. 업그레이드 후 최대 16기.'
        old['effect']={'type':'rework_v5','ordinal':130,'source_id':card['id'],'qa_revision':2026101610,'benefit_power_quarters':8}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.json';db=Path(folder)/'disposable_record.sqlite3'
            path.write_text(json.dumps(prior),encoding='utf8')
            store=CampaignStore(db,new_profile='original',runtime_catalog_path=path)
            def load():
                try:return store.restore_growth_phase(301,2,1)
                except GrowthChoicesPending as pending:return pending.state
            with patch.object(rework_growth,'candidates',return_value=[old]):offer=copy.deepcopy(load()['offer'])
            self.assertIn('16기',json.dumps(offer,ensure_ascii=False))
            with closing(sqlite3.connect(db)) as conn:issued=conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall()
            path.write_text(json.dumps(current),encoding='utf8');self.assertEqual(load()['offer'],offer)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall(),issued)
                pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            for field in ('id','bit_index','description','effect','source_description'):self.assertEqual(pinned['talents'][368][field],card[field])
