"""Ranked offers preserve saves and give every short campaign useful choices."""
import copy
import json
from pathlib import Path
import random
import unittest

from sc1.campaign import progression, talent_pool, talent_ranks
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog, validate_catalog
from sc1.tests import test_all_campaign_growth as campaign_tests


class TalentRankTests(unittest.TestCase):
    def test_append_only_layout_and_rank_prerequisites(self):
        catalog = load_catalog()
        ranked = [item for item in catalog['talents'] if item.get('offer_family')]
        self.assertEqual(len(ranked), 132)
        self.assertEqual([x['bit_index'] for x in ranked], list(range(106, 238)))
        for race in ('terran','zerg','protoss'):
            self.assertEqual(len({x['offer_family'] for x in ranked if x['race'] == race}), 13)
        first = ranked[0]
        second = next(x for x in ranked if x['offer_family']==first['offer_family'] and x['rank']==2)
        self.assertTrue(talent_ranks.eligible(first, [], catalog))
        self.assertFalse(talent_ranks.eligible(second, [], catalog))
        self.assertTrue(talent_ranks.eligible(second, [first['id']], catalog))
        with self.assertRaises(GrowthError): encode_growth(catalog,[second['id']],{})
        self.assertFalse(talent_ranks.eligible(catalog['talents'][0], [], catalog))
        damaged = copy.deepcopy(catalog)
        damaged['talents'][107]['requires_talent_id'] = 'missing'
        with self.assertRaises(GrowthError): validate_catalog(damaged)

    def test_legacy_and_rank_bits_are_both_encoded_without_replacing_ownership(self):
        catalog = load_catalog()
        old = catalog['talents'][0]
        new = catalog['talents'][106]
        words = encode_growth(catalog,[old['id'],new['id']],{})
        self.assertEqual(words[1],1)
        self.assertEqual(words[4],1<<10)
        base = copy.deepcopy(catalog)
        base['talents'] = base['talents'][:106]
        base['talent_pool_revision'] = 2
        before = copy.deepcopy(base)
        result = talent_ranks.merge(base,talent_ranks.additions())
        self.assertEqual(base,before)
        self.assertEqual(result['talents'][:106],base['talents'])
        bad = copy.deepcopy(talent_ranks.additions())
        bad[0]['effect']['patches'][0]['value'] += 1
        with self.assertRaises(GrowthError): talent_ranks.merge(base,bad)

    def test_30_picks_cannot_exhaust_four_families_even_with_concentrated_choices(self):
        catalog = load_catalog()
        for mission in (101,201,301):
            owned = []
            for _ in range(30):
                eligible = [x for x in catalog['talents'] if progression.item_eligible(x,mission,'talent')
                            and x['id'] not in owned and talent_ranks.eligible(x,owned,catalog)]
                self.assertGreaterEqual(len({x['offer_family'] for x in eligible}),4)
                # Finish one family before moving on: the strongest possible
                # adversarial depletion of the number of available families.
                best = max(x['rank'] for x in eligible)
                owned.append(next(x['id'] for x in eligible if x['rank']==best))
            self.assertEqual(len(owned),30)

    def test_hero_only_bw_terran_mission_has_four_effective_squad_families(self):
        catalog = load_catalog()
        squad = [x for x in catalog['talents'] if x.get('target_scope')=='army_and_heroes']
        owned = []
        for mission in (502,507):
            for _ in range(3):
                active = [x for x in squad if x['id'] not in owned
                          and progression.item_eligible(x,mission,'talent')
                          and talent_ranks.eligible(x,owned,catalog)]
                if mission==507:
                    self.assertGreaterEqual(len({x['offer_family'] for x in active}),4)
                    self.assertTrue(all({37,99} <= set(x['target_units']) for x in active))
                best=max(x['rank'] for x in active)
                owned.append(next(x['id'] for x in active if x['rank']==best))

    def test_actual_offer_changes_only_after_old_issued_offer_is_consumed(self):
        helper=campaign_tests.AllCampaignGrowthTests()
        helper.setUp()
        try:
            from sc1.manager.store import open_campaign_store
            legacy=Path(__file__).resolve().parents[1]/'campaign/runtime_talents.json'
            helper.store=open_campaign_store(helper.path,runtime_catalog_path=legacy)
            original=helper.load(101,1)
            pin=helper.rows('SELECT catalog_json FROM growth_state')
            helper.store=open_campaign_store(helper.path)
            self.assertEqual(helper.load(101,1)['offer'],original['offer'])
            state=original
            for _ in range(2):
                offer=state['offer']
                state=helper.store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],101,1,
                     choice_kind=1 if offer['kind']=='talent' else 2,phase=1)
            response=helper.load(101,1)
            state=helper.load(101,2,response['nonce'])
            self.assertTrue(all(x.get('offer_family') and x['rank']==1 for x in state['offer']['candidates']))
            self.assertEqual(len({x['offer_family'] for x in state['offer']['candidates']}),4)
            self.assertEqual(helper.rows('SELECT catalog_json FROM growth_state'),pin)
            restored=helper.load(101,2,response['nonce'])
            self.assertEqual(restored['offer'],state['offer'])
        finally: helper.tearDown()


if __name__=='__main__': unittest.main()
