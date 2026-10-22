import copy
import json
import random
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

from sc1.campaign import rework_growth, rank_policy, talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import GrowthError, load_catalog, encode_growth, validate_catalog
from sc1.campaign.unit_growth import specifications


class Rolls:
    def __init__(self,*values):self.values=iter(values);self.stops=[]
    def randrange(self,stop):
        self.stops.append(stop);value=next(self.values)
        assert 0<=value<stop
        return value


class TowerDefense(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_catalog(expected_version=2)
        cls.tower=cls.catalog['talents'][560]

    def test_single_shared_common_card_has_exact_effects_and_spare_bits(self):
        x=self.tower
        self.assertEqual((x['name'],x['race'],x['rarity'],x['max_rank']),('대공 방어 교범','shared','common',2))
        self.assertEqual(x['target_units'],[124,144,162])
        self.assertTrue(x['repeatable']);self.assertNotIn('bundle_family',x)
        self.assertEqual(x['candidate_weight_percent'],300)
        self.assertEqual(x['wire_storage'],dict(word=16,shift=28,width=2))
        for name,value in dict(health_percent_per_rank=100,shield_percent_per_rank=100,air_damage_percent_per_rank=50,additional_air_targets_per_rank=1).items():
            self.assertEqual(x['effect'][name],value)
        self.assertEqual(specifications()[-2]['storage'],dict(word=16,shift=27,width=1))

    def test_acquire_twice_then_exclude_without_mutating_owned_or_ranks(self):
        x=self.tower;owned=[]
        with sqlite3.connect(':memory:') as conn:
            for rank in (1,2):
                rework_growth.acquire_option(conn,101,self.catalog,owned,x)
                ranks=rework_growth.ranks(conn,101)
                self.assertEqual(ranks,{x['id']:rank})
                words=encode_growth(self.catalog,owned,{},ranks)
                self.assertEqual(words[16],rank<<28)
                self.assertEqual(owned,[x['id']])
                self.assertEqual(rank_policy.exhausted(x,owned,ranks,self.catalog),rank==2)
            with self.assertRaises(GrowthError):rework_growth.acquire_option(conn,101,self.catalog,owned,x)
            self.assertEqual(rework_growth.ranks(conn,101),ranks)
            for seed in range(30):
                cards=rework_growth.candidates(self.catalog,102,1,owned,random.Random(seed),rank_counts=ranks)
                self.assertNotIn(x['id'],[c['id'] for c in cards])

    def test_shared_card_is_eligible_for_all_races_and_weight_is_forwarded(self):
        for mission in (102,202,302,402,503,602):
            seen=[]
            def capture(reward,cards,*args,**kwargs):
                seen.extend(cards);return tuple(x for x in cards if x.id==self.tower['id'])
            with patch.object(policy,'draw_candidates',capture):
                result=rework_growth.candidates(self.catalog,mission,1,[],random.Random(1))
            self.assertEqual([x['id'] for x in result],[self.tower['id']])
            self.assertEqual(next(x.sampling_weight for x in seen if x.id==self.tower['id']),300)

    def test_exact_triple_sampling_weight_preserves_rarity_and_recent_penalty(self):
        cards=[policy.Candidate('tower','common',sampling_weight=300),policy.Candidate('normal','common')]
        reward=policy.reward_policy(102,1)
        for recent,total,boundary in (((),40000,30000),(('tower',),38500,28500),(('tower','normal'),38000,28500)):
            for ticket,expected in ((0,'tower'),(boundary-1,'tower'),(boundary,'normal'),(total-1,'normal')):
                rng=Rolls(0,ticket)
                result=policy.draw_candidates(reward,cards,[],rng,limit=1,recent_manuals=recent)
                self.assertEqual(result[0].id,expected)
                self.assertEqual(rng.stops,[100,total])
        self.assertEqual(policy.rarity_weights(),dict(common=40,uncommon=29,rare=25,epic=5,legendary=1))

    def test_upgrade_adds_card_to_old_pinned_catalog_without_rewriting_old_rows(self):
        old=copy.deepcopy(self.catalog);old['talents'].pop()
        old['native_coverage']['items'].pop(self.tower['id'])
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(old),))
            rework_growth.enable(conn)
            current=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            self.assertEqual(current['talents'][:560],old['talents'])
            self.assertEqual(current['talents'][560],self.tower)
            self.assertEqual(current['curses'],old['curses'])

    def test_vulture_normal_type_and_reaver_free_cost_upgrade_pinned_metadata(self):
        prior=copy.deepcopy(self.catalog)
        for ordinal,field in ((54,'weapon_damage_type'),(141,'scarab_mineral_cost')):
            x=prior['talents'][238+ordinal];x['description']='previous legend copy';x['effect'].pop(field);x['effect']['qa_revision']=2026102046
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(prior),))
            rework_growth.enable(conn)
            current=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            for ordinal,field,value in ((54,'weapon_damage_type',3),(141,'scarab_mineral_cost',0)):
                self.assertEqual(current['talents'][238+ordinal]['effect'][field],value)
                self.assertEqual(current['talents'][238+ordinal]['source_description'],prior['talents'][238+ordinal]['source_description'])

    def test_description_refresh_preserves_effects_original_text_and_issued_offer(self):
        prior=copy.deepcopy(self.catalog)
        for index in (292,379,560):
            prior['talents'][index].update(description='Previously issued description',description_revision=2026102261)
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(prior),))
            conn.execute('CREATE TABLE issued_copy (text TEXT)')
            saved=json.dumps(prior['talents'][292]);conn.execute('INSERT INTO issued_copy VALUES(?)',(saved,))
            rework_growth.enable(conn)
            current=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            for index in (292,379,560):
                self.assertEqual(current['talents'][index]['description'],self.catalog['talents'][index]['description'])
                self.assertEqual(current['talents'][index]['effect'],prior['talents'][index]['effect'])
                self.assertEqual(current['talents'][index]['source_description'],prior['talents'][index]['source_description'])
            self.assertEqual(conn.execute('SELECT text FROM issued_copy').fetchone()[0],saved)

    def test_triple_weight_refreshes_old_pin_and_presentation_without_rewriting_issued_copy(self):
        prior=copy.deepcopy(self.catalog);old=prior['talents'][560]
        old['candidate_weight_percent']=150;old['effect']['qa_revision']=2026102261
        saved=json.dumps(old,ensure_ascii=False)
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
            conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(prior),))
            conn.execute('CREATE TABLE issued_copy (text TEXT)');conn.execute('INSERT INTO issued_copy VALUES(?)',(saved,))
            rework_growth.save_ranks(conn,101,{self.tower['id']:1})
            rework_growth.enable(conn)
            current=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            self.assertEqual(current['talents'][560]['candidate_weight_percent'],300)
            self.assertEqual(current['talents'][560]['effect'],self.tower['effect'])
            self.assertEqual(current['talents'][:560],prior['talents'][:560]);self.assertEqual(current['curses'],prior['curses'])
            self.assertEqual(rework_growth.ranks(conn,101),{self.tower['id']:1})
            self.assertEqual(conn.execute('SELECT text FROM issued_copy').fetchone()[0],saved)
            presented=rework_growth.overlay(conn,prior)
            self.assertEqual(presented['talents'][560]['candidate_weight_percent'],300)

    def test_rank_cap_validation_rejects_altered_limits_and_encoding_clamps_to_two(self):
        c=copy.deepcopy(self.catalog);c['talents'][560]['max_rank']=4
        with self.assertRaises(GrowthError):validate_catalog(c,2)
        self.assertEqual(encode_growth(self.catalog,[self.tower['id']],{},{self.tower['id']:3})[16],2<<28)


if __name__=='__main__':unittest.main()
