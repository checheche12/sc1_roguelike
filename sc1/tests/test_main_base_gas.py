"""Real campaign transformations, resource access and publication tamper checks."""
from copy import deepcopy
from pathlib import Path
import struct
import unittest

from sc1.campaign.missions import mission_for_id
from sc1.native_campaign import main_base_gas as gas, build_all_campaigns as builder
from sc1.native_campaign import package_all_campaigns as package
from sc1.native_campaign.build_plain_chk import CHK


class MainBaseGasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.row = mission_for_id(105)
        cls.source = Path(cls.row['source']).read_bytes()
        cls.output, cls.report = builder.make_map(cls.source, cls.row)

    def test_threshold_uses_campaign_ordinal_and_excludes_infiltration(self):
        for mission, expected in ((104, False), (105, True), (205, False), (305, True),
                                  (405, False), (505, True), (515, True), (614, False),
                                  (605, True), (611, False)):
            with self.subTest(mission=mission):
                self.assertEqual(gas.eligible(mission_for_id(mission)), expected)

    def test_fifth_terran_mission_uses_acquired_antiga_base(self):
        report = self.report['main_base_gas']
        self.assertEqual(report['anchor']['center'], [2720, 464])
        self.assertEqual((report['gas_count_before'], report['gas_count_after']), (1, 2))
        self.assertEqual(len(report['added']), 1)
        entry = report['added'][0]
        raw = CHK(self.output).getsection('UNIT')[entry['unit_index']*36:(entry['unit_index']+1)*36]
        self.assertEqual(struct.unpack_from('<H', raw, 8)[0], 188)
        self.assertEqual(raw[16], 11)
        self.assertEqual(struct.unpack_from('<I', raw, 20)[0], 8766)
        self.assertEqual(report['resource_amount_reference']['unit_index'], 28)
        self.assertEqual(entry['resources'], report['resource_amount_reference']['resources'])
        builder.assert_original_units_preserved(CHK(self.source).getsection('UNIT'), CHK(self.output).getsection('UNIT'), mineral_bonus=500)

    def test_second_application_never_duplicates_gas(self):
        chk = CHK(self.output);before = chk.getsection('UNIT')
        report = gas.apply(chk, self.row, self.report['resource_layout'])
        self.assertEqual(report['added'], [])
        self.assertEqual(report['gas_count_after'], 2)
        self.assertEqual(chk.getsection('UNIT'), before)

    def test_existing_refineries_count_toward_two_gases(self):
        chk = CHK(self.output);raw = bytearray(chk.getsection('UNIT'))
        for index in self.report['main_base_gas']['gas_indices']:
            struct.pack_into('<H', raw, index*36+8, 110)
            raw[index*36+16] = self.row['owner']
        chk.setsection('UNIT', raw)
        report = gas.apply(chk, self.row, self.report['resource_layout'])
        self.assertEqual(report['added'], [])
        self.assertEqual(report['gas_count_after'], 2)
        self.assertEqual(chk.getsection('UNIT'), raw)

    def test_floating_command_centers_use_initial_settlement_field(self):
        row = mission_for_id(108)
        _, report = builder.make_map(Path(row['source']).read_bytes(), row)
        self.assertEqual(report['main_base_gas']['selection'], 'initial_settlement_resource_field')
        self.assertEqual(report['main_base_gas']['anchor']['kind'], 'expansion')
        self.assertEqual(report['main_base_gas']['gas_count_after'], 2)
        reference = report['main_base_gas']['resource_amount_reference']
        self.assertEqual(reference['resources'], 7214)
        self.assertTrue(all(a['resources'] == reference['resources'] for a in report['main_base_gas']['added']))

    def test_shared_two_hatchery_main_keeps_both_mineral_lines_and_two_gases(self):
        row = mission_for_id(607)
        _, report = builder.make_map(Path(row['source']).read_bytes(), row)
        self.assertEqual(report['main_base_gas']['anchor']['center'], [3584, 3536])
        self.assertEqual(report['main_base_gas']['gas_count_after'], 2)
        fields = report['resource_layout']['clusters']
        self.assertEqual(sum(len(f['unit_indices']) for f in fields
                             if f.get('anchor', {}).get('center') == [3648, 3376]), 9)

    def test_publication_replays_and_rejects_added_amount_or_record_changes(self):
        source, output = CHK(self.source), CHK(self.output)
        package.verify_mineral_layout(source, output, self.row, self.report)
        for offset in (4, 8, 16, 20):
            changed = CHK(self.output);raw = bytearray(changed.getsection('UNIT'))
            raw[self.report['main_base_gas']['added'][0]['unit_index']*36+offset] ^= 1
            changed.setsection('UNIT', raw)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                package.verify_mineral_layout(source, changed, self.row, self.report)
        altered = deepcopy(self.report);altered['main_base_gas']['added'] = []
        with self.assertRaises(ValueError):
            package.verify_mineral_layout(source, output, self.row, altered)


if __name__ == '__main__':
    unittest.main()
