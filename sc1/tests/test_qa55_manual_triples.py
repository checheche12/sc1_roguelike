import copy
import itertools
import random
import sqlite3
import unittest

from sc1.campaign import legendary_bundles as bundles, rework_growth
from sc1.campaign.runtime_catalog import GrowthError, load_catalog, encode_growth


class ManualTriples(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(expected_version=2)
        cls.by = {x['id']: x for x in cls.catalog['talents']}

    def pool(self, race):
        return [x for x in self.catalog['talents'] if x['race']==race
                and x['rarity']=='common' and not x['effect'].get('offer_retired')
                and bundles.bundle_size(x)==3]

    def test_three_different_families_each_race_and_random_partners(self):
        for race in ('terran','zerg','protoss'):
            pool=self.pool(race);seen=set()
            for seed in range(20):
                option=bundles.pair_options(pool[:4],pool,random.Random(seed))[0]
                ids=bundles.member_ids(option,self.catalog);seen.add(tuple(ids))
                self.assertEqual(len(ids),3)
                rows=[self.by[x] for x in ids]
                self.assertEqual(len({x['bundle_family'] for x in rows}),3)
                self.assertEqual(option['description'].count('\n'),2)
                for a,b in itertools.combinations(rows,2):self.assertTrue(bundles.compatible(a,b))
            self.assertGreater(len(seen),1)

    def test_all_three_awarded_ranked_encoded_and_limited(self):
        pool=self.pool('protoss');option=bundles.pair_options(pool[:1],pool,random.Random(7))[0]
        ids=bundles.member_ids(option,self.catalog);owned=[]
        with sqlite3.connect(':memory:') as conn:
            for rank in range(1,5):
                rework_growth.acquire_option(conn,301,self.catalog,owned,option)
                ranks=rework_growth.ranks(conn,301)
                for identity in ids:self.assertEqual(ranks[identity],rank)
                words=encode_growth(self.catalog,owned,{},ranks)
                for identity in ids:
                    f=self.by[identity]['wire_storage']
                    self.assertEqual(words[f['word']]>>f['shift']&7,rank)
            before=copy.deepcopy(owned)
            with self.assertRaises(GrowthError):rework_growth.acquire_option(conn,301,self.catalog,owned,option)
            self.assertEqual(owned,before)
            self.assertEqual(rework_growth.ranks(conn,301),ranks)

    def test_third_at_cap_prevents_partial_award(self):
        pool=self.pool('terran');option=bundles.pair_options(pool[:1],pool,random.Random(1))[0]
        ids=bundles.member_ids(option,self.catalog);owned=[ids[2]]
        with sqlite3.connect(':memory:') as conn:
            rework_growth.save_ranks(conn,101,{ids[2]:4})
            with self.assertRaises(GrowthError):rework_growth.acquire_option(conn,101,self.catalog,owned,option)
            self.assertEqual(owned,[ids[2]])
            self.assertEqual(rework_growth.ranks(conn,101),{ids[2]:4})

    def test_saved_singles_pairs_and_legendary_pairs_remain_valid(self):
        for race in ('terran','zerg','protoss'):
            pool=self.pool(race);a=pool[0];b=next(x for x in pool if bundles.compatible(a,x))
            self.assertEqual(bundles.member_ids(a,self.catalog),(a['id'],))
            old=dict(a,bundled_talent_ids=[a['id'],b['id']])
            self.assertEqual(bundles.member_ids(old,self.catalog),(a['id'],b['id']))
        for option in rework_growth.candidates(self.catalog,301,1,[],random.Random(2)):
            self.assertEqual(len(bundles.member_ids(option,self.catalog)),2 if option['race']!='shared' else 1)

    def test_invalid_third_and_insufficient_families(self):
        pool=self.pool('terran');a=pool[0];b=next(x for x in pool if bundles.compatible(a,x))
        self.assertEqual(bundles.pair_options([a],[a,b],random.Random(1)),[])
        for third in (a,b,next(x for x in self.pool('zerg'))):
            bad=dict(a,bundled_talent_ids=[a['id'],b['id'],third['id']])
            with self.assertRaises(GrowthError):bundles.member_ids(bad,self.catalog)

    def test_goliath_catalog_matches_primary_and_secondary_damage(self):
        item=next(x for x in self.catalog['talents'] if x.get('rework_revision')==5 and x.get('effect_ordinal')==56)
        for key,value in dict(base_bonus_percent=0,primary_damage_percent=100,additional_targets=3,additional_target_damage_percent=50,additional_target_radius_pixels=96).items():
            self.assertEqual(item['effect'][key],value)
        self.assertIn('100%',item['description']);self.assertIn('50%',item['description'])
        self.assertNotIn('주 대상만',item['description'])


if __name__=='__main__':unittest.main()
