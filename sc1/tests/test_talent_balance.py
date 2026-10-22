import copy
import unittest
from sc1.campaign import talent_balance as balance
from sc1.campaign import legendary_balance
from sc1.campaign import legendary_expansion
from sc1.campaign import unit_growth,talent_retirement,legend_focus,effect_copy
from sc1.campaign.runtime_catalog import load_catalog
from sc1.native_campaign.build_native_runtime import catalog_inputs

class TalentBalanceTests(unittest.TestCase):
    def test_carrier_legend_focus_ramp(self):
        item=load_catalog(expected_version=2)['talents'][238+148]
        self.assertEqual(item['id'],'e021408c-a180-5275-9f8b-1792e28b2524')
        self.assertEqual(item['effect']['focus_limit'],120)
        self.assertEqual(item['effect']['focus_step_percent'],20)
        self.assertIn('캐리어의 인터셉터',item['description'])

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
        self.assertEqual(effect_copy.decorate(legend_focus.decorate(talent_retirement.decorate(unit_growth.decorate(legendary_expansion.decorate(legendary_balance.decorate(balance.decorate(restored))))))),current)

    def test_qualitative_effects_have_concrete_bonus_display(self):
        current=load_catalog(expected_version=2)
        qualitative=(19,46,47,54,60,63,65,85,87,90,92,93,94,97,98,100,102,103,106,116,132,133,134,135,136,142)
        for ordinal in qualitative:
            item=current['talents'][238+ordinal]
            if ordinal!=85:self.assertNotEqual(item['description'],item['pre_balance_description'],ordinal)
            if ordinal==103:
                self.assertIn('초당 최대 체력 3%',item['description'])
                self.assertEqual(item['effect']['swarm_max_hp_regen_percent_per_second'],3)
            elif ordinal in (set(legend_focus.CONVERTED)|{92,97,106,136,140,149}):self.assertEqual(item['effect']['qa_revision'],2026102039)
            elif ordinal in (63,102):self.assertEqual(item['effect']['qa_revision'],2026102038)
            else:self.assertEqual(item['description'],effect_copy.with_subject(item,balance.DESCRIPTIONS[ordinal]))
        for item in current['talents'][:238]:
            if item['effect']['type']=='multi_target':self.assertIn('+25%',item['description'])

    def test_native_power_table_and_catalog_pins_match(self):
        contract,pins=catalog_inputs();self.assertEqual(contract['implemented_talents'],560);self.assertEqual(len(pins),3)

    def test_economic_descriptions_and_powers_are_original(self):
        current=load_catalog(expected_version=2)
        economy=[x for x in current['talents'] if x.get('category')=='economy']
        self.assertEqual(len(economy),24)
        ammo=current['talents'][355]
        self.assertEqual(ammo['category'],'combat')
        self.assertEqual(balance.power_quarters(ammo),4)
        for item in economy:
            self.assertEqual(balance.power_quarters(item),4)
            if item.get('effect_ordinal') in (5,153,157,160):self.assertEqual(item['description'],effect_copy.with_subject(item,balance.DESCRIPTIONS[item['effect_ordinal']]))
            else:self.assertEqual(item['description'],effect_copy.with_subject(item,item['pre_balance_description']))
        for bit in (15,56,65,79,84):
            self.assertEqual(balance.power_quarters(current['talents'][bit]),4)
