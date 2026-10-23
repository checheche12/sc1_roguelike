import copy
import json
import sqlite3
import unittest

from sc1.campaign import rework_growth,effect_copy,unit_growth
from sc1.campaign.runtime_catalog import load_catalog


class ProtossChanges(unittest.TestCase):
    def test_retaliation_still_stores_thirty_percent_and_adds_elevenfold_regeneration(self):
        item=load_catalog(expected_version=2)['talents'][377];effect=item['effect']
        self.assertEqual((effect['focus_proc_percent'],effect['focus_limit'],effect['base_bonus_percent']),(30,200,100))
        self.assertEqual((effect['shield_regen_bonus_percent'],effect['shield_regen_multiplier']),(1000,11))
        self.assertIn('11배',item['description'])

    def test_shadow_tooltip_six_then_five_repeat_fallback_cross_return_and_ground_only(self):
        item=load_catalog(expected_version=2)['talents'][559];effect=item['effect'];text=item['description']
        for phrase in ('공격 시','명령 무시','6타일','5타일','다른 적 우선·없으면 재타격','매 타격 반대편 이동','건물','원위치','대공 강화','지상 전용','일반 공격 200%'):
            self.assertIn(phrase,text)
        self.assertEqual((effect['shadow_trigger_radius_pixels'],effect['shadow_chain_radius_pixels']),(192,160))
        self.assertFalse(effect['shadow_requires_first_hit'])
        self.assertTrue(effect['shadow_requires_attack_order'] and effect['shadow_commands_ignored_while_casting'])
        self.assertEqual(effect['shadow_damage_percent'],200)
        self.assertTrue(effect['shadow_repeat_last_only_without_alternative'] and effect['shadow_moves_to_opposite_side'])
        self.assertTrue(effect['shadow_can_target_buildings'] and effect['shadow_returns_to_cast_origin'])
        self.assertEqual(effect['shadow_target_layer'],'ground')
        self.assertEqual(effect_copy.describe_effect(item),text)
        self.assertEqual(item['source_description'],unit_growth.SHADOW_FURY_ORIGINAL_DESCRIPTION)

    def test_reaver_speed_keeps_scarab_cost_and_damage(self):
        item=load_catalog(expected_version=2)['talents'][379];effect=item['effect']
        self.assertEqual((effect['reaver_move_speed_bonus_percent'],effect['reaver_move_speed_multiplier']),(100,2))
        self.assertEqual(effect['reaver_move_speed_units'],[81,83])
        self.assertEqual((effect['scarab_mineral_cost'],effect['base_bonus_percent']),(0,150))
        self.assertIn('이동 속도 +100%',item['description'])

    def test_catalog_refresh_preserves_all_previously_issued_copies_and_ids(self):
        catalog=load_catalog(expected_version=2);old=copy.deepcopy(catalog)
        for index in (377,379,559):
            old['talents'][index]['effect']['qa_revision']=2026102038
            old['talents'][index]['description']='previously issued description'
        saved=json.dumps([old['talents'][i] for i in (377,379,559)],ensure_ascii=False)
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
            conn.execute('CREATE TABLE issued_copy (text TEXT)');conn.execute('INSERT INTO issued_copy VALUES (?)',(saved,))
            rework_growth.enable(conn);current=rework_growth.overlay(conn,old)
            for index in (377,379,559):
                self.assertEqual(current['talents'][index]['effect'],catalog['talents'][index]['effect'])
                self.assertEqual(current['talents'][index]['id'],old['talents'][index]['id'])
                self.assertEqual(current['talents'][index]['source_description'],old['talents'][index]['source_description'])
            self.assertEqual(conn.execute('SELECT text FROM issued_copy').fetchone()[0],saved)
