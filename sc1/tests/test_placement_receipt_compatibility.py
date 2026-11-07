"""Historical labels cannot conceal a changed placement or resource proof."""
from copy import deepcopy
from pathlib import Path
import json
import unittest

from sc1.native_campaign import package_all_campaigns as package
from sc1.campaign.missions import mission_for_id


class PlacementReceiptCompatibilityTests(unittest.TestCase):
    def fixture(self):
        saved = dict(output_unit_sha256='kept', bases=[dict(mineral_positions=[[1, 2]])],
                     playtest_placement=dict(version='campaign_playtest_20261030_v2',
                                             changes=[dict(index=2, after=[30, 40])]))
        replayed = deepcopy(saved)
        replayed['playtest_placement']['version'] = 'campaign_playtest_20261103_v3'
        return replayed, saved

    def test_label_only_accepts_without_mutating_the_historical_receipt(self):
        replayed, saved = self.fixture()
        before = deepcopy(saved)
        self.assertTrue(package.same_bank_receipt(replayed, saved))
        self.assertEqual(saved, before)
        self.assertTrue(package.same_bank_receipt(saved, saved))

    def test_coordinate_hash_and_unrelated_proof_changes_still_fail(self):
        for change in ('unit', 'mineral', 'hash', 'new_field'):
            replayed, saved = self.fixture()
            if change == 'unit':replayed['playtest_placement']['changes'][0]['after'][0] += 1
            if change == 'mineral':replayed['bases'][0]['mineral_positions'][0][0] += 1
            if change == 'hash':replayed['output_unit_sha256'] = 'changed'
            if change == 'new_field':replayed['new_field'] = True
            with self.subTest(change=change):
                self.assertFalse(package.same_bank_receipt(replayed, saved))

    def test_unknown_or_reverse_label_migrations_fail(self):
        replayed, saved = self.fixture()
        self.assertFalse(package.same_bank_receipt(saved, replayed))
        replayed['playtest_placement']['version'] = 'unknown'
        self.assertFalse(package.same_bank_receipt(replayed, saved))

    def test_terran3_original_sealed_receipt_replays_exactly(self):
        receipt = json.loads(package.DEFAULT_MAP_RECEIPT.read_text(encoding='utf-8'))
        row = next(r for r in receipt['maps'] if r['mission_id'] == 103)
        # Keep exercising the historical label after future fresh builds
        # regenerate the default receipt with the current label.
        row['ladder_resource_banks']['playtest_placement']['version'] = 'campaign_playtest_20261030_v2'
        package.verify_mineral_layout(package.CHK(Path(row['source']).read_bytes()),
            package.CHK(Path(row['output']).read_bytes()), mission_for_id(103), row)


if __name__ == '__main__':
    unittest.main()
