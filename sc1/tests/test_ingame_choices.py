"""Real choice helper control flow against a synchronized offline action model.

This checks the emitted helper's latching/cleanup and original CHK preservation.
It does not emulate StarCraft's native pathfinder, text renderer or game engine.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import struct
import sys
import types
import unittest
from unittest.mock import patch

from sc1.tools import terran01_choices as placement

SC1 = Path(__file__).resolve().parents[1]
PLUGIN = SC1 / 'plugins/original_choices.py'
CATALOG = json.loads((SC1 / 'campaign/runtime_talents.json').read_text(encoding='utf-8'))


def number(value):
    return value.value if isinstance(value, Value) else value


class Value:
    def __init__(self, value=0):
        self.value = number(value)

    def __lshift__(self, other):
        self.value = number(other)
        return self

    def __iadd__(self, other):
        self.value += number(other)
        return self

    def __eq__(self, other):
        return self.value == number(other)

    def __ge__(self, other):
        return self.value >= number(other)

    def __and__(self, other):
        return Value(self.value & number(other))

    def __rshift__(self, other):
        return Value(self.value >> number(other))


class Check:
    def __init__(self, raw):
        self.sections = placement._sections(raw)

    def getsection(self, name):
        return self.sections[name.encode()]

    def setsection(self, name, data):
        self.sections[name.encode()] = bytes(data)


def configured():
    chk = Check(placement.SOURCE.read_bytes())
    chk.setsection('MRGN', chk.getsection('MRGN') + bytes(5100 - len(chk.getsection('MRGN'))))
    # Include the already-configured difficulty records when available without
    # depending on the map builder module or changing any on-disk artifact.
    prepared = SC1 / 'campaign/build/terran01/input.chk'
    if prepared.is_file():
        current = Check(prepared.read_bytes()).getsection('UNIT')
        assert current[:49 * 36] == chk.getsection('UNIT')
        chk.setsection('UNIT', current)
    before = dict(chk.sections)
    config = placement.make_config(chk)
    return chk, config, before


class Runtime(types.ModuleType):
    P2, P12, AtLeast, Move = 1, 11, 0, 0
    EUDVariable = Value

    def __init__(self):
        super().__init__('eudplib')
        self.chk, self.config, self.before = configured()
        self.locations = {i + 1: list(struct.unpack_from('<4I', self.chk.getsection('MRGN'), i * 20))
                          for i in range(255)}
        self.units = [{'x': x, 'y': y, 'unit': unit, 'player': player}
                      for (x, y, unit), player in placement._units(self.chk.getsection('UNIT')) if unit != 214]
        self.original_units = [dict(unit) for unit in self.units]
        self.cp = 7
        self.branches = []
        self.texts = []
        self.lines = {}
        self.orders = []
        self.views = []
        self.created = []
        self.removed = []
        self.helper = types.ModuleType('original_choices_under_test')
        self.helper.CONFIG = self.config
        self.helper.CATALOG = CATALOG
        with patch.dict(sys.modules, {'eudplib': self}):
            exec(compile(PLUGIN.read_text(encoding='utf-8'), str(PLUGIN), 'exec'), self.helper.__dict__)
        self.helper.start()

    def f_getcurpl(self):
        return Value(self.cp)

    def f_setcurpl(self, player):
        self.cp = number(player)

    def EUDAnd(self, *conditions):
        return all(conditions)

    def EUDIf(self):
        def begin(condition):
            self.branches.append(bool(condition))
            return bool(condition)
        return begin

    def EUDElse(self):
        def alternate():
            active = not self.branches[-1]
            self.branches[-1] = True
            return active
        return alternate

    def EUDEndIf(self):
        self.branches.pop()

    def DisplayTextAt(self, line, text):
        self.lines[line] = text.decode('utf-8') if isinstance(text, bytes) else text

    def DisplayText(self, text):
        value = text.decode('utf-8') if isinstance(text, bytes) else text
        return lambda: self.texts.append((self.cp, value))

    def StringBuffer(self, capacity):
        assert capacity >= 160
        runtime = self

        class Buffer:
            def printfAt(self, line, text, *arguments):
                runtime.lines[line] = text.format(*[number(arg) for arg in arguments])

        return Buffer()

    def UnitProperty(self, **properties):
        return properties

    def DoActions(self, actions):
        for action in actions if isinstance(actions, list) else [actions]:
            action()

    def matching(self, player, unit, location='Anywhere'):
        result = [row for row in self.units if row['player'] == player and row['unit'] == unit]
        if location == 'Anywhere':
            return result
        left, top, right, bottom = self.locations[location]
        return [row for row in result if left <= row['x'] <= right and top <= row['y'] <= bottom]

    def Bring(self, player, comparison, count, unit, location):
        assert comparison == self.AtLeast
        return len(self.matching(player, unit, location)) >= count

    def CreateUnitWithProperties(self, count, unit, location, player, properties):
        assert count == 1 and properties == {'invincible': True}
        left, top, right, bottom = self.locations[location]

        def action():
            row = {'x': (left + right) // 2, 'y': (top + bottom) // 2,
                   'unit': unit, 'player': player, **properties}
            self.units.append(row)
            self.created.append(dict(row))

        return action

    def MoveUnit(self, count, unit, owner, source, destination):
        left, top, right, bottom = self.locations[destination]

        def action():
            for row in self.matching(owner, unit, source)[:count]:
                row['x'], row['y'] = (left + right) // 2, (top + bottom) // 2

        return action

    def Order(self, unit, player, location, order, target):
        assert order == self.Move

        def action():
            rows = self.matching(player, unit, location)
            self.orders.append((unit, player, location, target, len(rows)))
            for row in rows:
                row['order_target'] = target

        return action

    def CenterView(self, location):
        return lambda: self.views.append((self.cp, location))

    def RemoveUnit(self, unit, player):
        def action():
            rows = self.matching(player, unit)
            self.removed.extend(dict(row) for row in rows)
            self.units = [row for row in self.units if row not in rows]

        return action

    def show(self, kind=1, candidates=(1, 2, 3, 4), stacks=0):
        self.helper.show(Value(kind), [Value(candidate) for candidate in candidates], Value(stacks))
        assert self.cp == 7 and not self.branches

    def move_to_slot(self, slot):
        row = self.matching(self.P2, 15)[0]
        row['x'], row['y'] = self.config['slots_left_to_right'][slot - 1]

    def poll(self):
        result = number(self.helper.selected_slot())
        assert self.cp == 7 and not self.branches
        return result


class ChoicePlacementTests(unittest.TestCase):
    def test_only_previously_zero_locations_are_reserved_originals_unchanged(self):
        chk, config, before = configured()
        self.assertEqual(set(config['locations']), {'arena', 'home', 'slots'})
        for name, data in before.items():
            if name != b'MRGN':
                self.assertEqual(chk.sections[name], data)
        old, new = before[b'MRGN'], chk.getsection('MRGN')
        self.assertEqual(new[:70 * 20], old[:70 * 20])
        self.assertEqual(old[70 * 20:76 * 20], bytes(120))
        self.assertEqual(new[76 * 20:], old[76 * 20:])
        self.assertEqual(config['original_units_preserved'], 49)
        self.assertTrue(config['source_has_no_selector_types'])

    def test_rejects_preexisting_choice_species_or_nonempty_location(self):
        for species in (15, 195):
            chk = Check(placement.SOURCE.read_bytes())
            chk.setsection('MRGN', chk.getsection('MRGN') + bytes(3820))
            record = bytearray(chk.getsection('UNIT')[:36])
            struct.pack_into('<H', record, 8, species)
            chk.setsection('UNIT', chk.getsection('UNIT') + record)
            with self.assertRaises(AssertionError):
                placement.make_config(chk)
        chk, _, _ = configured()
        with self.assertRaises(AssertionError):
            placement.make_config(chk)

    def test_layout_has_connected_24px_clearance_and_separate_capture_zones(self):
        _, config, _ = configured()
        _, clear = placement.load_grid()
        connected = placement._connected(clear, (128, 128))
        points = [config['home'], *config['slots_left_to_right']]
        self.assertTrue(all((x // 8, y // 8) in connected for x, y in points))
        xs = [point[0] for point in config['slots_left_to_right']]
        self.assertEqual(xs, sorted(xs))
        self.assertTrue(all(b - a >= 96 for a, b in zip(xs, xs[1:])))
        self.assertGreater(config['home'][1], config['slots_left_to_right'][0][1] + 80)
        self.assertEqual(config['terrain_clearance_pixels'], 24)


class ChoiceRuntimeTests(unittest.TestCase):
    def test_lazy_start_preserves_all_original_units_and_has_no_selection(self):
        runtime = Runtime()
        self.assertEqual(runtime.created, [])
        self.assertEqual(runtime.units, runtime.original_units)
        self.assertEqual(runtime.poll(), 0)
        runtime.lines[0] = '원래 임무 안내'
        runtime.helper.finish()
        self.assertEqual(runtime.removed, [])
        self.assertEqual(runtime.lines[0], '원래 임무 안내')

    def test_first_show_creates_only_one_invincible_civilian_and_four_beacons(self):
        runtime = Runtime()
        runtime.show()
        self.assertEqual([(row['unit'], row['player']) for row in runtime.created], [(15, 1)] + [(195, 11)] * 4)
        self.assertTrue(all(row['invincible'] for row in runtime.created))
        self.assertEqual(runtime.units[:len(runtime.original_units)], runtime.original_units)
        self.assertEqual(runtime.views, [(1, 71)])
        self.assertEqual(runtime.orders[-1], (15, 1, 72, 72, 1))
        self.assertIn('조준경', runtime.lines[2])
        self.assertIn('마린 사거리 +1', runtime.lines[3])
        self.assertIn('화염갑옷', runtime.lines[8])
        self.assertEqual(runtime.poll(), 0)

    def test_each_number_selects_correct_slot_and_latches_until_ack(self):
        for slot in range(1, 5):
            with self.subTest(slot=slot):
                runtime = Runtime()
                runtime.show()
                runtime.move_to_slot(slot)
                self.assertEqual(runtime.poll(), slot)
                texts = list(runtime.texts)
                runtime.move_to_slot(1 if slot != 1 else 4)
                for _ in range(100):
                    self.assertEqual(runtime.poll(), slot)
                self.assertEqual(runtime.texts, texts)
                runtime.helper.acknowledge()
                self.assertEqual(runtime.poll(), 0)
                runtime.move_to_slot(2)
                self.assertEqual(runtime.poll(), 0)

    def test_next_show_reuses_selector_and_cancels_prior_order(self):
        runtime = Runtime()
        runtime.show()
        runtime.move_to_slot(3)
        self.assertEqual(runtime.poll(), 3)
        selector = runtime.matching(1, 15)[0]
        selector['order_target'] = 75
        runtime.helper.acknowledge()
        runtime.show(candidates=(5, 6, 7, 8))
        self.assertEqual(len(runtime.created), 5)
        self.assertEqual([selector['x'], selector['y']], runtime.config['home'])
        self.assertEqual(selector['order_target'], 72)
        self.assertEqual(runtime.poll(), 0)

    def test_zero_candidate_cannot_be_selected_and_curses_show_current_stacks(self):
        runtime = Runtime()
        runtime.show(kind=2, candidates=(1, 2, 3, 0), stacks=0x030201)
        self.assertIn('끝없는 증원', runtime.lines[2])
        self.assertIn('군비 경쟁', runtime.lines[4])
        self.assertIn('악마의 생명력', runtime.lines[6])
        self.assertIn('증원 1 / 군비 2 / 체력 3', runtime.lines[8])
        self.assertIn('비활성', runtime.lines[9])
        runtime.move_to_slot(4)
        self.assertEqual(runtime.poll(), 0)
        runtime.move_to_slot(2)
        self.assertEqual(runtime.poll(), 2)

    def test_worker_text_describes_only_implemented_scv_effects(self):
        runtime = Runtime()
        runtime.show(candidates=(16, 17, 1, 2))
        self.assertIn('SCV 생산 시간 50%', runtime.lines[3])
        self.assertIn('SCV 최대 체력 +20', runtime.lines[5])
        self.assertNotIn('드론', runtime.lines[3])
        self.assertNotIn('프로브', runtime.lines[5])

    def test_all_talent_rows_show_complete_short_t01_values_preserve_catalog(self):
        runtime = Runtime()
        before = json.dumps(CATALOG, ensure_ascii=False, sort_keys=True)
        expected = (
            '마린 사거리 +1.', '마린 최대 체력 +10.',
            '마린 공격 주기 ×100÷130 (프레임 반올림).', '파이어뱃 최대 체력 100.',
            '고스트 최대 체력 +30.', '고스트의 공격 피해형을 일반으로 변경.',
            '벌처 공격 주기 20% 감소 (프레임 반올림).',
            '벌처: 미네랄 50 · 인구 1 · 최대 체력 50.',
            '탱크 모드 사거리 +1.', '시즈 모드 사거리 +2.', '골리앗 최대 체력 +20.',
            '레이스 사거리 +2.', '레이스 최대 체력 +30.',
            '발키리 공격 주기 20% 감소 (프레임 반올림).', '배틀크루저 사거리 +2.',
            'SCV 생산 시간 50% 감소 (프레임 반올림).', 'SCV 최대 체력 +20.',
        )
        for index, text in enumerate(expected):
            with self.subTest(bit_index=index):
                runtime.show(candidates=(index + 1, 0, 0, 0))
                self.assertEqual(runtime.lines[3], '\x04' + text)
                self.assertNotIn('\n', runtime.lines[3])
                self.assertIn(CATALOG['talents'][index]['name'], runtime.lines[2])
        self.assertEqual(json.dumps(CATALOG, ensure_ascii=False, sort_keys=True), before)

    def test_text_refreshes_without_recentring_or_changing_selection(self):
        runtime = Runtime()
        runtime.show()
        runtime.lines.clear()
        for _ in range(47):
            self.assertEqual(runtime.poll(), 0)
        self.assertEqual(runtime.lines, {})
        self.assertEqual(runtime.poll(), 0)
        self.assertIn('조준경', runtime.lines[2])
        self.assertEqual(runtime.views, [(1, 71)])
        self.assertEqual(len(runtime.created), 5)

    def test_finish_removes_only_selector_types_and_is_idempotent(self):
        runtime = Runtime()
        runtime.show()
        runtime.move_to_slot(4)
        self.assertEqual(runtime.poll(), 4)
        runtime.helper.finish()
        self.assertEqual(runtime.units, runtime.original_units)
        self.assertEqual(len(runtime.removed), 5)
        self.assertEqual(runtime.lines, {line: ' ' for line in range(11)})
        runtime.lines[0] = '캠페인 기록 연결 완료'
        runtime.helper.finish()
        self.assertEqual(len(runtime.removed), 5)
        self.assertEqual(runtime.lines[0], '캠페인 기록 연결 완료')
        self.assertEqual(runtime.poll(), 0)
        self.assertEqual(runtime.cp, 7)

    def test_official_hooks_no_raw_keyboard_or_global_battle_writes(self):
        tree = ast.parse(PLUGIN.read_text(encoding='utf-8'))
        calls = {node.func.attr for node in ast.walk(tree)
                 if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertFalse(calls & {'SetResources', 'SetDeaths', 'SetMemory', 'f_dwwrite', 'f_dwread',
                                 'EUDInfLoop', 'EUDDoEvents', 'RunTrigTrigger', 'SaveMap', 'LoadMap', 'Victory'})
        self.assertTrue({'Bring', 'MoveUnit', 'Order', 'CreateUnitWithProperties', 'RemoveUnit', 'DisplayTextAt'} <= calls)


if __name__ == '__main__':
    unittest.main()
