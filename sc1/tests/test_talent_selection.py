"""New-offer selection remains useful, varied and compatible with small pools."""
import copy
import random
import unittest

from sc1.campaign import progression
from sc1.campaign.missions import load_missions
from sc1.campaign.runtime_catalog import GrowthError, load_catalog
from sc1.campaign.talent_selection import select_candidates


def talent(identity, units, rarity="common", **metadata):
    return {"id": identity, "target_units": units, "rarity": rarity, **metadata}


class FirstRandom:
    """Make the old repeated-target failure deterministic, recording the odds."""
    def __init__(self):
        self.draws = []

    def choices(self, values, weights=None, k=1):
        self.draws.append((list(values), list(weights), k))
        return [values[0]]

    def choice(self, values):
        return values[0]


class TalentSelectionTests(unittest.TestCase):
    def test_four_slots_prefer_different_troops_over_four_same_troop_talents(self):
        pool = [talent(f"hydra-{i}", [38]) for i in range(4)]
        pool += [talent("zergling", [37]), talent("mutalisk", [43]), talent("guardian", [44])]
        before = copy.deepcopy(pool)
        candidates = select_candidates(pool, 201, FirstRandom())
        self.assertEqual([item["id"] for item in candidates],
                         ["hydra-0", "zergling", "mutalisk", "guardian"])
        self.assertEqual(pool, before)
        self.assertIs(candidates[0], pool[0])

    def test_turrets_tank_modes_and_ammunition_share_parent_families(self):
        for first, related in (([3], [3, 4]), ([5, 6], [30, 31]),
                               ([83], [85]), ([72], [73])):
            with self.subTest(first=first, related=related):
                pool = [talent("first", first), talent("related", related),
                        talent("other-1", [1]), talent("other-2", [2]), talent("other-3", [8])]
                candidates = select_candidates(pool, 101, FirstRandom())
                self.assertEqual([item["id"] for item in candidates],
                                 ["first", "other-1", "other-2", "other-3"])

    def test_declared_offer_family_takes_precedence_over_unit_targets(self):
        pool = [talent("first", [0], offer_family="bundle-a"),
                talent("same-bundle", [32], offer_family="bundle-a"),
                talent("other-bundle", [0], offer_family="bundle-b"),
                talent("other-1", [1]), talent("other-2", [2])]
        candidates = select_candidates(pool, 101, FirstRandom())
        self.assertEqual([item["id"] for item in candidates],
                         ["first", "other-bundle", "other-1", "other-2"])

    def test_squad_usable_talents_take_precedence_over_unused_family(self):
        # Mission 104 has regular Marines and Firebats. Their six usable
        # upgrades must precede an irrelevant, previously unseen Goliath.
        pool = [talent("marine-1", [0]), talent("marine-2", [0]),
                talent("marine-3", [0]), talent("goliath", [3]),
                talent("firebat-1", [32]), talent("firebat-2", [32])]
        candidates = select_candidates(pool, 104, FirstRandom())
        self.assertEqual([item["id"] for item in candidates],
                         ["marine-1", "firebat-1", "marine-2", "marine-3"])

    def test_squad_single_usable_family_can_fill_all_four_slots(self):
        # Mission 205 supplies regular Zerglings; its heroes are not mapped
        # onto the other regular troops' effect targets.
        pool = [talent("hydra", [38])]
        pool += [talent(f"zergling-{i}", [37]) for i in range(4)]
        candidates = select_candidates(pool, 205, FirstRandom())
        self.assertEqual([item["id"] for item in candidates],
                         [f"zergling-{i}" for i in range(4)])

    def test_squad_uses_other_troops_after_usable_talents_run_out(self):
        pool = [talent("hydra", [38]), talent("mutalisk", [43]),
                talent("guardian", [44]), talent("zergling", [37])]
        candidates = select_candidates(pool, 205, FirstRandom())
        self.assertEqual([item["id"] for item in candidates],
                         ["zergling", "hydra", "mutalisk", "guardian"])

    def test_missing_active_targets_does_not_invent_hero_effects(self):
        # Mission 507 has no regular Terran target for these effects. Keep
        # the existing fallback, without claiming that Marine buffs aid Duran.
        pool = [talent("marine-1", [0]), talent("marine-2", [0]),
                talent("ghost", [1]), talent("goliath", [3]), talent("wraith", [8])]
        candidates = select_candidates(pool, 507, FirstRandom())
        self.assertEqual([item["id"] for item in candidates],
                         ["marine-1", "ghost", "goliath", "wraith"])

    def test_rarity_draws_keep_campaign_weights_and_only_available_tiers(self):
        pool = [talent("common", [0]), talent("rare", [1], "rare"),
                talent("epic", [2], "epic"), talent("legendary", [8], "legendary")]
        for mission in (101, 104, 110):
            with self.subTest(mission=mission):
                rng = FirstRandom()
                select_candidates(pool, mission, rng)
                expected = progression.rarity_weights(mission)
                for tiers, weights, count in rng.draws:
                    self.assertEqual(weights, [expected[tier] for tier in tiers])
                    self.assertEqual(count, 1)
                self.assertNotIn("uncommon", rng.draws[0][0])

    def test_current_catalog_has_four_distinct_choices_for_every_mission(self):
        catalog = load_catalog()
        for mission in load_missions():
            identity = mission["mission_id"]
            eligible = [item for item in catalog["talents"]
                        if progression.item_eligible(item, identity, "talent")]
            with self.subTest(mission=identity):
                candidates = select_candidates(eligible, identity, random.Random(identity))
                self.assertEqual(len(candidates), 4)
                self.assertEqual(len({item["id"] for item in candidates}), 4)
                self.assertTrue(all(item in eligible for item in candidates))

    def test_small_and_exhausted_pools_preserve_unique_choice_count(self):
        pool = [talent(str(i), [0]) for i in range(4)]
        self.assertEqual(select_candidates(pool, 101, FirstRandom()), pool)
        with self.assertRaises(GrowthError) as caught:
            select_candidates(pool[:3], 101, FirstRandom())
        self.assertEqual(caught.exception.code, "choice_pool_unavailable")
        self.assertEqual(select_candidates(pool, 101, FirstRandom(), count=0), [])
        self.assertEqual(len(select_candidates(pool, 101, FirstRandom(), count=2)), 2)


if __name__ == "__main__":
    unittest.main()
