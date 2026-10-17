import copy
import unittest
from sc1.campaign import talent_balance as balance
from sc1.campaign.runtime_catalog import load_catalog
from sc1.native_campaign.build_native_runtime import catalog_inputs

class TalentBalanceTests(unittest.TestCase):
    def test_wire_and_frozen_mechanics_remain_recoverable(self):
        current=load_catalog(expected_version=2);old=load_catalog()
        self.assertEqual([balance.historical(x) for x in current['talents'][:238]],old['talents'])
        self.assertEqual(current['curses'][:15],old['curses'])
        for item in current['talents']:
            self.assertEqual(item['effect']['benefit_power_quarters'],balance.power_quarters(item))
            before=balance.historical(item)
            for key in ('id','bit_index','rank_slot','repeatable','source_description','missions'):
                self.assertEqual(item.get(key),before.get(key))
        restored=copy.deepcopy(current);restored['talents']=[balance.historical(x) for x in current['talents']]
        self.assertEqual(balance.decorate(restored),current)

    def test_qualitative_effects_have_concrete_bonus_display(self):
        current=load_catalog(expected_version=2)
        qualitative=(19,46,47,54,60,63,65,85,87,90,92,93,94,97,98,100,102,103,106,116,132,133,134,135,136,142)
        for ordinal in qualitative:
            item=current['talents'][238+ordinal]
            self.assertNotEqual(item['description'],item['pre_balance_description'],ordinal)
            self.assertEqual(item['description'],balance.DESCRIPTIONS[ordinal])
        for item in current['talents'][:238]:
            if item['effect']['type']=='multi_target':self.assertIn('+25%',item['description'])

    def test_native_power_table_and_catalog_pins_match(self):
        contract,pins=catalog_inputs();self.assertEqual(contract['implemented_talents'],400);self.assertEqual(len(pins),3)

    def test_economic_descriptions_and_powers_are_original(self):
        current=load_catalog(expected_version=2)
        economy=[x for x in current['talents'] if x.get('category')=='economy']
        self.assertEqual(len(economy),25)
        for item in economy:
            self.assertEqual(balance.power_quarters(item),4)
            if item.get('effect_ordinal')==5:self.assertEqual(item['description'],balance.DESCRIPTIONS[5])
            else:self.assertEqual(item['description'],item['pre_balance_description'])
        for bit in (15,56,65,79,84):
            self.assertEqual(balance.power_quarters(current['talents'][bit]),4)
