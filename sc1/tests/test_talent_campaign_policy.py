"""Reward totals and logical-campaign boundaries, independent of player data."""
import unittest

from sc1.campaign import talent_campaign_policy as policy
from sc1.campaign.missions import load_missions


class FixedRoll:
    def __init__(self, value):
        self.value = value
        self.calls = []

    def randrange(self, stop):
        self.calls.append(stop)
        return self.value


class TalentCampaignPolicyTests(unittest.TestCase):
    def test_six_campaigns_keep_24_or_30_awards_including_five_economy(self):
        for mission, total in ((101, 29), (201, 29), (301, 29),
                               (401, 23), (501, 23), (601, 29)):
            with self.subTest(mission=mission):
                schedule = policy.campaign_schedule(mission)
                self.assertEqual(len(schedule), total)
                economy = [x for x in schedule if x.category == "economy"]
                self.assertEqual(len(economy), 5)
                self.assertEqual(len({x.ordinal for x in economy}), 5)
                self.assertTrue(all(x.phase == 2 for x in economy))
                self.assertEqual(sum(x.category == "military" for x in schedule), total - 5)

    def test_economy_is_usable_and_earned_before_final_mission_for_all_assets(self):
        for mission in load_missions():
            for phase in (1, 2, 3):
                reward = policy.reward_policy(mission["mission_id"], phase)
                if reward.category == "economy":
                    self.assertFalse(mission.get("no_production"), mission)
                    self.assertFalse(mission["final"], mission)
                    self.assertFalse(reward.guaranteed_legendary)

    def test_legendary_once_at_campaign_opening_phase_one(self):
        for mission, ordinal in ((101, 1), (201, 1), (301, 1),
                                 (401, 1), (501, 1), (601, 1)):
            schedule = policy.campaign_schedule(mission)
            guaranteed = [x for x in schedule if x.guaranteed_legendary]
            self.assertEqual(len(guaranteed), 1)
            self.assertEqual((guaranteed[0].ordinal, guaranteed[0].phase), (ordinal, 1))
            self.assertEqual(guaranteed[0].category, "military")

    def test_branch_variants_share_policy_without_inflating_logical_totals(self):
        for left, right in ((505, 515), (604, 614), (604, 615),
                            (604, 616), (604, 617), (604, 618)):
            for phase in (1, 2, 3):
                self.assertEqual(policy.reward_policy(left, phase),
                                 policy.reward_policy(right, phase))
        self.assertEqual(policy.logical_mission_count(515), 8)
        self.assertEqual(policy.logical_mission_count(618), 10)

    def test_secret_campaign_is_independent_three_awards_without_guarantee(self):
        schedule = policy.campaign_schedule(611)
        self.assertEqual(len(schedule), 2)
        self.assertTrue(all(x.campaign_id == 7 and x.category == "military" for x in schedule))
        self.assertFalse(any(x.guaranteed_legendary for x in schedule))

    def test_ordinary_legendary_has_one_percent_per_slot(self):
        reward = policy.reward_policy(102, 1)
        for value, expected in ((0, 4), (99, 4), (100, 0), (9999, 0)):
            rng = FixedRoll(value)
            self.assertEqual(policy.legendary_candidate_count(reward, rng), expected)
            self.assertEqual(rng.calls, [10000] * 4)
        self.assertEqual(sum(policy.legendary_candidate_count(reward, FixedRoll(i))
                             for i in range(10000)), 400)

    def test_guarantee_is_four_economy_is_zero_and_neither_rolls_rarity(self):
        rng = FixedRoll(0)
        self.assertEqual(policy.legendary_candidate_count(policy.reward_policy(101, 1), rng), 4)
        self.assertEqual(policy.legendary_candidate_count(policy.reward_policy(102, 2), rng), 0)
        self.assertEqual(rng.calls, [])

    def test_invalid_phase_cannot_select_a_reward(self):
        for phase in (True, False, 0, 4, 1.0, "1", None):
            with self.assertRaises(ValueError):
                policy.reward_policy(101, phase)

    def test_exact_per_slot_weights_and_boundaries(self):
        from collections import Counter
        self.assertEqual(Counter(policy.rolled_rarity(i) for i in range(100)),
                         {"common": 40, "uncommon": 29, "rare": 25,
                          "epic": 5, "legendary": 1})
        for value, tier in ((39, "common"), (40, "uncommon"), (68, "uncommon"),
                            (69, "rare"), (93, "rare"), (94, "epic"),
                            (98, "epic"), (99, "legendary")):
            self.assertEqual(policy.rolled_rarity(value), tier)
        weights = policy.rarity_weights()
        weights["common"] = 0
        self.assertEqual(policy.rarity_weights()["common"], 40)

    def test_common_can_repeat_30_times_without_duplicate_cards_in_one_offer(self):
        cards = [policy.Candidate(str(i), "common") for i in range(7)]
        owned = set()
        for _ in range(30):
            offer = policy.draw_candidates(policy.reward_policy(102, 1), cards, owned, FixedRoll(0))
            self.assertEqual(len(offer), 4)
            self.assertEqual(len({x.id for x in offer}), 4)
            owned.add(offer[0].id)

    def test_depleted_low_tier_never_promotes_to_rare_or_epic(self):
        reward = policy.reward_policy(102, 1)
        cards = [policy.Candidate("rare", "rare"), policy.Candidate("epic", "epic")]
        self.assertEqual(policy.draw_candidates(reward, cards, (), FixedRoll(0)), ())
        cards.append(policy.Candidate("uncommon", "uncommon"))
        offer = policy.draw_candidates(reward, cards, (), FixedRoll(0))
        self.assertEqual([x.id for x in offer], ["uncommon"])

    def test_guarantee_only_shows_one_unowned_usable_legendary(self):
        cards = [policy.Candidate("owned", "legendary"),
                 policy.Candidate("unusable", "legendary", usable=False),
                 policy.Candidate("fresh", "legendary")]
        offer = policy.draw_candidates(policy.reward_policy(101, 1), cards, {"owned"}, FixedRoll(0))
        self.assertEqual([x.id for x in offer], ["fresh"])
        with self.assertRaises(ValueError):
            policy.draw_candidates(policy.reward_policy(101, 1), cards, {"owned", "fresh"}, FixedRoll(0))

    def test_guarantee_shows_four_distinct_unowned_usable_legendaries(self):
        cards = [policy.Candidate(str(i), 'legendary') for i in range(7)]
        cards.append(policy.Candidate('unusable', 'legendary', usable=False))
        offer = policy.draw_candidates(policy.reward_policy(101, 1), cards, {'0'}, FixedRoll(0))
        self.assertEqual([x.id for x in offer], ['1', '2', '3', '4'])
        self.assertTrue(all(x.rarity == 'legendary' for x in offer))

    def test_last_legendary_reserved_until_midpoint(self):
        class LastRoll:
            def randrange(self, stop):
                return stop - 1
        cards = [policy.Candidate("last", "legendary"), policy.Candidate("epic", "epic")]
        offer = policy.draw_candidates(policy.reward_policy(102, 1), cards, (), LastRoll(),
                                       midpoint_pending=True)
        self.assertEqual([x.id for x in offer], ["epic"])
        offer = policy.draw_candidates(policy.reward_policy(107, 1), cards, (), LastRoll())
        self.assertEqual(offer[0].id, "last")

    def test_economy_is_separate_and_owned_high_tiers_do_not_repeat(self):
        cards = [policy.Candidate("army", "common"),
                 policy.Candidate("owned", "rare", "economy"),
                 policy.Candidate("new", "rare", "economy")]
        offer = policy.draw_candidates(policy.reward_policy(102, 2), cards, {"owned"}, FixedRoll(0))
        self.assertEqual([x.id for x in offer], ["new"])
        self.assertFalse(policy.repeatable("uncommon", "combat"))
        self.assertFalse(policy.repeatable("common", "economy"))

    def test_three_percent_cooldown_stacks_multiplicatively_and_never_reaches_zero(self):
        self.assertAlmostEqual(policy.firepower_cooldown(10000, 10), 7374.241268949281)
        self.assertEqual(policy.firepower_cooldown(10000, 0), 10000)
        self.assertEqual(policy.firepower_cooldown(15, 10000), 1)
        for base, stacks in ((0, 1), (15, -1), (True, 1), (15, 1.0)):
            with self.assertRaises(ValueError):
                policy.firepower_cooldown(base, stacks)

    def test_fractional_carry_keeps_first_three_percent_rank_effective(self):
        base = policy.firepower_intervals(15, 0, 1000)
        buff = policy.firepower_intervals(15, 1, 1000)
        self.assertEqual(sum(base), 15000)
        self.assertEqual(sum(buff), 14550)
        self.assertEqual(set(buff), {14, 15})
        self.assertEqual(set(policy.firepower_intervals(15, 10000, 100)), {1})

    def test_each_slot_rolls_its_own_tier_with_no_one_legendary_per_offer_cap(self):
        class SequenceRoll:
            def __init__(self, values):
                self.values = iter(values)
            def randrange(self, stop):
                value = next(self.values)
                assert 0 <= value < stop
                return value
        cards = [policy.Candidate("c", "common"), policy.Candidate("u", "uncommon"),
                 policy.Candidate("e", "epic"), policy.Candidate("l1", "legendary"),
                 policy.Candidate("l2", "legendary")]
        reward = policy.reward_policy(102, 1)
        offer = policy.draw_candidates(reward, cards, (), SequenceRoll([39, 0, 40, 0, 94, 0, 99, 0]))
        self.assertEqual([x.rarity for x in offer], ["common", "uncommon", "epic", "legendary"])
        offer = policy.draw_candidates(reward, cards, (), SequenceRoll([99, 0, 99, 0]), limit=2)
        self.assertEqual([x.id for x in offer], ["l1", "l2"])


if __name__ == "__main__":
    unittest.main()
