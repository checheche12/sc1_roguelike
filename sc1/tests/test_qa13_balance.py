import unittest
from sc1.campaign.runtime_catalog import load_catalog
from sc1.campaign import talent_balance


class Qa13BalanceTests(unittest.TestCase):
    def test_live_manual_values_and_historical_inputs(self):
        catalog=load_catalog(expected_version=2)
        for n in (11,12):
            item=catalog['talents'][238+n]
            self.assertIn('+0.5',item['description'])
            self.assertEqual(item['effect']['armor_per_rank'],0.5)
        for n in (26,27,28,67,68,69,108,109,110):
            item=catalog['talents'][238+n]
            self.assertIn('+28%',item['description'])
            self.assertIn('+20%',item['pre_balance_description'])
            self.assertEqual(item['effect']['health_percent_per_rank'],28)
            if n>=108:self.assertEqual(item['effect']['shield_percent_per_rank'],28)
            original=talent_balance.historical(item)
            for key in ('id','bit_index','rank_slot','repeatable','max_rank','source_description'):
                self.assertEqual(item.get(key),original.get(key))

    def test_supply_box_reduced_without_rescaling_economy(self):
        catalog=load_catalog(expected_version=2)
        box=catalog['talents'][243]
        self.assertEqual(box['effect']['resources_per_curse'],37.5)
        self.assertEqual(box['effect']['resource_total_rounding'],'floor')
        self.assertIn('37.5',box['description'])
        self.assertIn('50씩',box['pre_balance_description'])
        self.assertEqual(box['effect']['benefit_power_quarters'],4)
        self.assertFalse(catalog['economy_talents_scaled'])
        for item in catalog['talents']:
            if item.get('category')=='economy' and item.get('effect_ordinal')!=5:
                self.assertEqual(item['description'],item['pre_balance_description'])
