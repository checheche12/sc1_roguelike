"""Large innate bonuses shrink without redefining acquired card identities."""
import json
import unittest
from pathlib import Path

from sc1.campaign.runtime_catalog import load_catalog
from sc1.campaign.legend_base_balance import BASE_BONUSES, SCALARS, REVISION


class LegendaryBases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(expected_version=2)
        cls.by = {x['effect_ordinal']: x for x in cls.catalog['talents'] if x.get('rework_revision') == 5}

    def test_attack_bases_and_triggered_components(self):
        for ordinal, bonus in BASE_BONUSES.items():
            item = self.by[ordinal]
            self.assertEqual(item['effect']['base_bonus_percent'], bonus)
            self.assertIn(f'+{bonus}%', item['description'])
        self.assertEqual(self.by[194]['effect']['focus_proc_percent'], 200)
        self.assertEqual(self.by[194]['effect']['focus_limit'], 50)
        self.assertEqual(self.by[54]['effect']['focus_proc_percent'], 100)
        self.assertIn('총300%', self.by[54]['description'])
        self.assertIn('총200%', self.by[54]['description'])
        self.assertEqual(self.by[105]['effect']['projectile_damage_percent'], 200)
        self.assertEqual(self.by[137]['effect']['focus_proc_percent'], 250)
        self.assertEqual(self.by[137]['effect']['focus_cadence'], 3)

    def test_spell_and_defense_bases_keep_qualitative_mechanics(self):
        for ordinal, key, value in ((61, 'damage_multiplier', 2), (63, 'organic_duration_multiplier', 2),
                                    (96, 'health_multiplier', 2), (102, 'damage_multiplier', 2),
                                    (106, 'ground_damage_percent', 200), (144, 'radius_bonus_percent', 100)):
            self.assertEqual(self.by[ordinal]['effect'][key], value)
            self.assertGreaterEqual(self.by[ordinal]['effect']['qa_revision'], REVISION)
        self.assertEqual(self.by[61]['effect']['infection_radius_pixels'], 192)
        self.assertEqual(self.by[63]['effect']['chain_total_targets'], 7)
        self.assertEqual(self.by[106]['effect']['acid_spore_effect_multiplier'], 2)
        self.assertIn('최대 13개', self.by[144]['description'])

    def test_generated_tuning_is_the_catalog_contract(self):
        root = Path(__file__).resolve().parents[2]
        header = (root / 'sc1/native_campaign/plugin/include/legend_base_balance.generated.h').read_text(encoding='utf8')
        for key, value in SCALARS.items():
            self.assertIn(f'{key}={value}u;', header)
        self.assertEqual(self.catalog['legend_base_balance_revision'], REVISION)
        self.assertEqual(len(self.catalog['talents']), 560)
        self.assertEqual(len(self.catalog['curses']), 50)


if __name__ == '__main__':
    unittest.main()
