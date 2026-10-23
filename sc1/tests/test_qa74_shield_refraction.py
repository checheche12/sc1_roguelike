import copy
import json
import sqlite3
import unittest

from sc1.campaign import rework_growth, talent_balance, effect_copy
from sc1.campaign.runtime_catalog import load_catalog


class ShieldRefraction(unittest.TestCase):
    def test_effect_copy_and_rebuild_keep_exact_three(self):
        catalog=load_catalog(expected_version=2)
        item=catalog['talents'][351]
        self.assertEqual(item['effect']['shield_armor_bonus'],3)
        self.assertIn('+3',item['description'])
        self.assertEqual(effect_copy.describe_effect(item),item['description'])
        rebuilt=talent_balance.decorate(copy.deepcopy(catalog))['talents'][351]
        self.assertEqual(rebuilt,item)

    def test_existing_ownership_refreshes_without_rewriting_issued_copy(self):
        catalog=load_catalog(expected_version=2);old=copy.deepcopy(catalog)
        item=old['talents'][351]
        item['description']=item['description'].replace('+3','+2')
        item['effect'].pop('shield_armor_bonus');item['effect']['qa_revision']=2026101610
        issued=json.dumps(item,ensure_ascii=False)
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
            conn.execute('CREATE TABLE issued_copy (text TEXT)');conn.execute('INSERT INTO issued_copy VALUES (?)',(issued,))
            rework_growth.enable(conn);current=rework_growth.overlay(conn,old)
            self.assertEqual(current['talents'][351]['effect']['shield_armor_bonus'],3)
            self.assertEqual(current['talents'][351]['id'],item['id'])
            self.assertEqual(current['talents'][351]['source_description'],item['source_description'])
            self.assertEqual(conn.execute('SELECT text FROM issued_copy').fetchone()[0],issued)

    def test_fresh_catalog_build_preserves_the_original_baseline(self):
        item=copy.deepcopy(load_catalog(expected_version=2)['talents'][351])
        item.pop('balance_revision')
        item['description']=item['pre_balance_description']
        item['effect']=copy.deepcopy(item['pre_balance_effect'])
        text,effect=item['description'],copy.deepcopy(item['effect'])
        result=talent_balance.decorate(dict(talents=[item],curses=[]))['talents'][0]
        self.assertEqual(result['pre_balance_description'],text)
        self.assertEqual(result['pre_balance_effect'],effect)
        self.assertEqual(result['effect']['shield_armor_bonus'],3)
        self.assertEqual(result['effect']['qa_revision'],2026102378)
        self.assertIn('+3',result['description'])
