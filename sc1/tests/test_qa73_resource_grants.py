"""Exercise all 63 stock scenarios and every resource-action execution context."""
import random
import struct
import unittest
from pathlib import Path

from sc1.campaign.missions import load_missions
from sc1.native_campaign import build_all_campaigns as maps, campaign_resource_grants as grants


def contexts(chk, human):
    return [(p, t) for t in maps.triggers(chk) for p in grants._executors(chk, t, human)]


def banks(chk, human, seed, skip_terminal=False, reverse=False):
    values = [list(seed) for _ in range(12)]
    rows = contexts(chk, human)
    for player in sorted({p for p, _ in rows}, reverse=reverse):
        for executor, trigger in rows:
            if executor != player:
                continue
            for _, a in maps.actions(trigger):
                if a[26] != 26:
                    continue
                amount = struct.unpack_from('<I', a, 20)[0]
                if skip_terminal and amount == 10500:
                    continue
                resource = struct.unpack_from('<H', a, 24)[0]
                for target in grants._targets(chk, a, executor, human):
                    for kind in ([0, 1] if resource == 2 else [resource]):
                        if a[27] == 7:
                            values[target][kind] = amount
                        elif a[27] == 8:
                            values[target][kind] += amount
                        elif a[27] == 9:
                            values[target][kind] = max(0, values[target][kind] - amount)
    return values


class ResourceGrantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = load_missions()

    def pair(self, row):
        before = maps.CHK(Path(row['source']).read_bytes())
        self.assertEqual(maps.digest(before.save()), row['source_sha256'])
        after = maps.CHK(before.save())
        report = grants.apply(after, row)
        return before, after, report

    def test_every_asset_all_resource_selectors_and_computer_banks(self):
        changed = actions = splits = objectives = 0
        rng = random.Random(73)
        for row in self.rows:
            with self.subTest(mission=row['mission_id']):
                before, after, report = self.pair(row)
                changed += bool(report['grants_preserving_balance'])
                actions += report['grants_preserving_balance']
                splits += len(report['shared_trigger_splits'])
                objectives += report['terminal_objectives_preserved']
                self.assertEqual(before.order, after.order)
                for tag in before.order:
                    if tag != b'TRIG':
                        self.assertEqual(before.sections[tag], after.sections[tag])
                for seed in [(0, 0), (500, 500), (rng.randrange(20000), rng.randrange(20000))]:
                    for reverse in [False, True]:
                        old, new = banks(before, row['owner'], seed, reverse=reverse), banks(after, row['owner'], seed, reverse=reverse)
                        self.assertTrue(all(a == b for p, (a, b) in enumerate(zip(old, new)) if p != row['owner']))
                # Zero-bank stock income is unchanged, including group actions
                # run by multiple original force members (P05 and P09).
                self.assertEqual(banks(before, row['owner'], (0, 0)), banks(after, row['owner'], (0, 0)))
                for executor, t in contexts(after, row['owner']):
                    for _, a in maps.actions(t):
                        if a[26] == 26 and row['owner'] in grants._targets(after, a, executor, row['owner']):
                            self.assertTrue(a[27] == 8 or row['mission_id'] == 603 and struct.unpack_from('<I', a, 20)[0] == 10500)
        self.assertEqual((len(self.rows), changed, actions, splits, objectives), (63, 55, 85, 2, 1))

    def test_each_executors_original_conditions_waits_and_other_actions(self):
        for row in self.rows:
            with self.subTest(mission=row['mission_id']):
                before, after, _ = self.pair(row)
                def script(chk):
                    result = {}
                    for executor, t in contexts(chk, row['owner']):
                        result.setdefault(executor, []).append((t[:320], t[2368:2372], [a for _, a in maps.actions(t) if a[26] != 26]))
                    return result
                self.assertEqual(script(before), script(after))

    def test_base_discovery_and_rescues_preserve_bonus_and_spending(self):
        for mission, source_trigger, amounts in [(304, 5, (50, 0)), (602, 43, (850, 200)), (611, 19, (100, 100))]:
            row = next(r for r in self.rows if r['mission_id'] == mission)
            before, after, _ = self.pair(row)
            # These original cinematic triggers keep their indices and waits.
            original, patched = maps.triggers(before)[source_trigger], maps.triggers(after)[source_trigger]
            bank = [375, 425]  # starting support less legitimate spending
            for _, a in maps.actions(patched):
                if a[26] != 26:
                    continue
                self.assertEqual(a[27], 8)
                resource = struct.unpack_from('<H', a, 24)[0]
                for index in ([0, 1] if resource == 2 else [resource]):
                    bank[index] += struct.unpack_from('<I', a, 20)[0]
            self.assertEqual(bank, [375 + amounts[0], 425 + amounts[1]])
            self.assertEqual([a for _, a in maps.actions(original) if a[26] != 26], [a for _, a in maps.actions(patched) if a[26] != 26])

    def test_terminal_mining_objective_and_existing_add_rewards_stay_exact(self):
        for row in self.rows:
            before, after, _ = self.pair(row)
            old = [a for _, t in contexts(before, row['owner']) for _, a in maps.actions(t) if a[26] == 26 and a[27] == 8]
            new = [a for _, t in contexts(after, row['owner']) for _, a in maps.actions(t) if a[26] == 26 and a[27] == 8]
            self.assertTrue(all(new.count(a) >= old.count(a) for a in old))
            if row['mission_id'] == 603:
                self.assertEqual(maps.actions(maps.triggers(before)[21]), maps.actions(maps.triggers(after)[21]))

    def test_repeating_resource_resets_require_explicit_review(self):
        row = next(r for r in self.rows if r['mission_id'] == 304)
        chk = maps.CHK(Path(row['source']).read_bytes())
        trigger = bytearray(maps.triggers(chk)[5])
        trigger[320 + 25 * 32 + 26] = 3  # Preserve Trigger
        raw = bytearray(chk.getsection('TRIG'))
        raw[5 * 2400:6 * 2400] = trigger
        chk.setsection('TRIG', bytes(raw))
        with self.assertRaisesRegex(AssertionError, 'Repeating resource reset'):
            grants.apply(chk, row)

    def test_all_current_ending_routes_keep_their_acknowledged_gate(self):
        import json
        from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine
        receipt = json.loads((maps.ROOT / 'all_campaign_maps_evidence.json').read_text(encoding='utf8'))
        routes = 0
        for row in receipt['maps']:
            patched = maps.triggers(maps.CHK(Path(row['output']).read_bytes()))
            for route in row['progression']['routes']:
                with self.subTest(mission=row['mission_id'], route=route['route']):
                    latch, ending = patched[route['goal_trigger_index']], patched[route['ending_trigger_index']]
                    engine = OrdinaryTriggerMachine()
                    engine.satisfy([c for _, c in maps.conditions(latch)])
                    self.assertFalse(engine.run(ending))
                    self.assertTrue(engine.run(latch))
                    for ready, ack in [(False, False), (True, False), (False, True)]:
                        engine.switches[242], engine.switches[243] = ready, ack
                        self.assertFalse(engine.run(ending))
                    engine.switches[242] = engine.switches[243] = True
                    self.assertTrue(engine.run(ending))
                    self.assertTrue(engine.victory)
                    routes += 1
        self.assertGreaterEqual(routes, 71)


if __name__ == '__main__':
    unittest.main()
