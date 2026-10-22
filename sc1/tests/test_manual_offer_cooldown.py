"""Temporary appearance weighting uses only displayed, campaign-local offers."""
from collections import Counter
import json
import sqlite3
import unittest

from sc1.campaign import rework_growth, talent_campaign_policy as policy


class Rolls:
    def __init__(self, *values):
        self.values = iter(values)
        self.stops = []

    def randrange(self, stop):
        self.stops.append(stop)
        value = next(self.values)
        assert 0 <= value < stop
        return value


class ManualOfferCooldownTests(unittest.TestCase):
    def test_recent_manual_has_95_tickets_against_100_without_changing_rarity(self):
        cards = [policy.Candidate('seen', 'common'), policy.Candidate('fresh', 'common')]
        counts = Counter()
        for ticket in range(195):
            rng = Rolls(0, ticket)
            offer = policy.draw_candidates(policy.reward_policy(102, 1), cards, (), rng,
                limit=1, recent_manuals=['seen', 'seen'])
            counts[offer[0].id] += 1
            self.assertEqual(rng.stops, [100, 195])
        self.assertEqual(counts, {'seen': 95, 'fresh': 100})

    def test_expired_equal_and_depleted_pools_remain_usable(self):
        cards = [policy.Candidate('seen', 'common'), policy.Candidate('fresh', 'common')]
        for recent in ((), ('seen', 'fresh')):
            rng = Rolls(0, 1)
            offer = policy.draw_candidates(policy.reward_policy(102, 1), cards, (), rng,
                limit=1, recent_manuals=recent)
            self.assertEqual(offer[0].id, 'fresh')
            self.assertEqual(rng.stops, [100, 2])
        offer = policy.draw_candidates(policy.reward_policy(102, 1), cards[:1], {'seen'},
            Rolls(0, 0), limit=1, recent_manuals={'seen'})
        self.assertEqual([x.id for x in offer], ['seen'])

    def test_economy_and_other_rarities_keep_uniform_draws(self):
        for reward, cards, rarity in (
            (policy.reward_policy(102, 1), [policy.Candidate('a', 'rare'), policy.Candidate('b', 'rare')], 70),
            (policy.reward_policy(102, 2), [policy.Candidate('a', 'rare', 'economy'), policy.Candidate('b', 'rare', 'economy')], None),
        ):
            rng = Rolls(1) if rarity is None else Rolls(rarity, 1)
            offer = policy.draw_candidates(reward, cards, (), rng, limit=1, recent_manuals={'a'})
            self.assertEqual(offer[0].id, 'b')
            self.assertEqual(rng.stops, [2] if rarity is None else [100, 2])

    def test_window_ages_on_three_talent_rewards_and_refreshes_on_appearance(self):
        with sqlite3.connect(':memory:') as conn:
            conn.execute('CREATE TABLE growth_offers (sequence INTEGER PRIMARY KEY AUTOINCREMENT, offer_id TEXT, mission INTEGER, kind TEXT, candidates_json TEXT, selected_id TEXT)')
            def shown(identity, *, mission=101, kind='talent', manual=False, selected=None, issued=True):
                card = dict(id=identity, rarity='common' if manual else 'rare',
                            category='military' if manual else 'economy', repeatable=manual)
                conn.execute('INSERT INTO growth_offers(offer_id,mission,kind,candidates_json,selected_id) VALUES (?,?,?,?,?)',
                    (identity, mission, kind, json.dumps([card]) if issued else None, selected))
            def recent():
                return rework_growth.recent_manuals(conn, 101, 'current')
            shown('manual', manual=True, selected='different-card')
            shown('curse', kind='curse')
            shown('other-campaign', mission=201, manual=True)
            shown('placeholder', issued=False)
            self.assertEqual(recent(), {'manual'})
            shown('one'); shown('two')
            self.assertEqual(recent(), {'manual'})
            shown('three')
            self.assertEqual(recent(), set())
            shown('manual', manual=True)
            shown('four'); shown('five')
            self.assertEqual(recent(), {'manual'})
            shown('six')
            self.assertEqual(recent(), set())
            before = list(conn.execute('SELECT * FROM growth_offers'))
            for _ in range(10): recent()
            self.assertEqual(list(conn.execute('SELECT * FROM growth_offers')), before)


if __name__ == '__main__':
    unittest.main()
