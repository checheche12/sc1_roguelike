"""Execute the real plugin hooks against an offline EUD-call model.

These tests exercise protocol control flow, not the StarCraft EUD emulator.
They never launch/open a game or use an existing campaign database.
"""
import ast
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from sc1.bridge.protocol import Dispatcher, read_request
from sc1.manager.store import CampaignStore
from sc1.tests.test_bridge import BASE, FakeMemory


PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "growth_probe.py"
NONCE = (0x12345678, 0x89ABCDEF, 0x80000000, 0xFFFFFFFF)


def number(value):
    return value.value if isinstance(value, Value) else value


class Value:
    def __init__(self, value=0):
        self.value = number(value)

    def __lshift__(self, other):
        self.value = number(other)
        return self

    def __iadd__(self, other):
        self.value = (self.value + number(other)) & 0xFFFFFFFF
        return self

    def __eq__(self, other):
        return self.value == number(other)

    def __ne__(self, other):
        return self.value != number(other)

    def __ge__(self, other):
        return self.value >= number(other)


class Runtime(types.ModuleType):
    P1, SetTo, Add, Exactly, AtLeast, Ore = 0, 7, 8, 10, 0, 0
    EUDVariable = Value

    def __init__(self, mission=1):
        super().__init__("eudplib")
        self.memory = FakeMemory()
        self.cp = 7
        self.at_beacon = False
        self.minerals = None
        self.texts = []
        self.branches = []
        self.map_writes = []
        module = types.ModuleType("growth_probe_under_test")
        module.settings = {"mission": str(mission)}
        with patch.dict(sys.modules, {"eudplib": self}):
            exec(compile(PLUGIN.read_text(encoding="utf-8"), str(PLUGIN), "exec"), module.__dict__)
        module.emit_build_info = lambda: None  # Build-time CLI receipt is not game logic.
        self.plugin = module
        module.onPluginStart()
        assert self.cp == 7 and not self.branches

    def Db(self, data):
        self.memory.data[:] = data
        return BASE

    def EPD(self, address):
        return address // 4

    def f_getcurpl(self):
        return Value(self.cp)

    def f_setcurpl(self, player):
        self.cp = number(player)

    def f_dwread_epd(self, address):
        return Value(struct.unpack("<I", self.memory.read(address * 4, 4))[0])

    def f_dwwrite_epd(self, address, value):
        word = address - BASE // 4
        assert 0 <= word < 32
        self.memory.set(word, number(value))
        self.map_writes.append((word, number(value), self.memory.get(8)))

    def SetMemory(self, address, modifier, value):
        def execute():
            word = (address - BASE) // 4
            before = self.memory.get(word)
            self.f_dwwrite_epd(address // 4, (before + number(value)) & 0xFFFFFFFF if modifier == self.Add else value)
        return execute

    def MemoryX(self, address, comparison, value, mask):
        assert comparison == self.Exactly
        return self.memory.get((address - BASE) // 4) & mask == value

    def SetResources(self, player, modifier, amount, resource):
        assert player == self.P1 and modifier == self.SetTo and resource == self.Ore
        return lambda: setattr(self, "minerals", number(amount))

    def DisplayText(self, text):
        return lambda: self.texts.append((self.cp, text))

    def DoActions(self, actions):
        for action in actions if isinstance(actions, list) else [actions]:
            action()

    def Bring(self, *args):
        return self.at_beacon

    def EUDAnd(self, *conditions):
        return all(conditions)

    def EUDOr(self, *conditions):
        return any(conditions)

    def EUDIf(self):
        def begin(condition):
            self.branches.append(bool(condition))
            return bool(condition)
        return begin

    def EUDElseIf(self):
        def alternate(condition):
            active = not self.branches[-1] and bool(condition)
            self.branches[-1] |= active
            return active
        return alternate

    def EUDEndIf(self):
        self.branches.pop()

    def tick(self):
        old_cp = self.cp
        self.plugin.afterTriggerExec()
        assert self.cp == old_cp and not self.branches

    def response(self, *, seq=2, status=1, echo=2, gold=37, nonce=NONCE):
        for index, value in enumerate((seq, status, echo, gold, *nonce, 0, 0, 0), 32):
            self.memory.set(index, value)

    def restored(self):
        self.response()
        self.tick()
        assert self.memory.get(7) == 2


class OfficialPluginTests(unittest.TestCase):
    def test_initial_load_has_original_protocol_and_no_nonce(self):
        for mission in (1, 2):
            with self.subTest(mission=mission):
                runtime = Runtime(mission)
                request = read_request(runtime.memory, BASE)
                self.assertEqual((request.mission, request.state, request.sequence, request.operation), (mission, 1, 2, 1))
                self.assertEqual((request.nonce, request.gold_delta, request.observed_gold), ("00" * 16, 0, 0))

    def test_hooks_restore_current_player_and_only_map_words_are_written(self):
        runtime = Runtime()
        runtime.cp = 5
        runtime.restored()
        runtime.at_beacon = True
        runtime.tick()
        self.assertEqual(runtime.cp, 5)
        self.assertEqual(runtime.memory.get(6), 2)
        self.assertTrue(all(index < 32 for index, _, _ in runtime.map_writes))
        self.assertTrue(all(seq & 1 for index, _, seq in runtime.map_writes if index in (7, 9, 10, 11, 12, 13, 14, 15)))
        self.assertTrue(all(player == 0 for player, _ in runtime.texts))

    def test_a_restores_nonce_commits123_and_acknowledges_once(self):
        runtime = Runtime()
        runtime.restored()
        request = read_request(runtime.memory, BASE)
        self.assertEqual((request.state, request.sequence, request.observed_gold, runtime.minerals), (2, 4, 37, 37))
        self.assertEqual(request.nonce, struct.pack("<4I", *NONCE).hex())
        runtime.at_beacon = True
        runtime.tick()
        request = read_request(runtime.memory, BASE)
        self.assertEqual((request.state, request.sequence, request.operation, request.gold_delta, request.observed_gold), (3, 6, 2, 123, 37))
        runtime.response(seq=4, status=2, echo=6, gold=160)
        runtime.tick()
        self.assertEqual((runtime.memory.get(7), runtime.memory.get(8), runtime.minerals), (4, 8, 160))
        texts = list(runtime.texts)
        runtime.tick()
        self.assertEqual(runtime.memory.get(8), 8)
        self.assertEqual(runtime.texts, texts)

    def test_b_sends_zero_reward(self):
        runtime = Runtime(2)
        runtime.restored()
        runtime.at_beacon = True
        runtime.tick()
        self.assertEqual((read_request(runtime.memory, BASE).mission, runtime.memory.get(14)), (2, 0))

    def test_load_rejects_odd_wrong_status_wrong_echo_and_zero_nonce(self):
        for response in ({"seq": 1}, {"status": 2}, {"echo": 4}, {"nonce": (0, 0, 0, 0)}):
            with self.subTest(response=response):
                runtime = Runtime()
                runtime.response(**response)
                runtime.tick()
                self.assertEqual((runtime.memory.get(7), runtime.memory.get(8), runtime.minerals), (1, 2, None))

    def test_torn_response_is_rejected(self):
        runtime = Runtime()
        runtime.response()
        reads = 0
        def change(address, size):
            nonlocal reads
            if address == BASE + 128:
                reads += 1
                if reads == 2:
                    runtime.memory.set(32, 4)
        runtime.memory.on_read = change
        runtime.tick()
        self.assertEqual(runtime.memory.get(7), 1)

    def test_commit_ack_requires_exact_nonce(self):
        runtime = Runtime()
        runtime.restored()
        runtime.at_beacon = True
        runtime.tick()
        runtime.response(seq=4, status=2, echo=6, gold=160, nonce=(1, *NONCE[1:]))
        runtime.tick()
        self.assertEqual((runtime.memory.get(7), runtime.memory.get(8), runtime.minerals), (3, 6, 37))

    def test_rejection_enters_error_without_saved_message(self):
        runtime = Runtime()
        runtime.response(status=3, nonce=(0, 0, 0, 0))
        runtime.tick()
        self.assertEqual((runtime.memory.get(7), runtime.memory.get(8), runtime.memory.get(9)), (5, 4, 0))
        self.assertFalse(any("SAVE ACKNOWLEDGED" in text for _, text in runtime.texts))

    def test_real_dispatcher_and_temporary_sqlite_store_a_then_b(self):
        with tempfile.TemporaryDirectory() as folder:
            database = Path(folder) / "test.sqlite3"
            for mission in (1, 2):
                runtime = Runtime(mission)
                dispatcher = Dispatcher(runtime.memory, BASE, CampaignStore(database))
                self.assertEqual(dispatcher.poll()["status"], "waiting_for_heartbeat")
                runtime.tick()
                self.assertEqual(dispatcher.poll()["status"], "restored")
                runtime.tick()
                self.assertEqual(runtime.minerals, 0 if mission == 1 else 123)
                runtime.at_beacon = True
                runtime.tick()
                committed = dispatcher.poll()
                self.assertEqual(committed["status"], "committed")
                self.assertEqual(CampaignStore(database).status()["gold"], 123)
                runtime.tick()
                self.assertEqual((runtime.memory.get(7), runtime.minerals), (4, 123))
            self.assertEqual(CampaignStore(database).status()["completed_mask"], 3)

    def test_storage_failure_does_not_publish_or_accept_saved_ack(self):
        with tempfile.TemporaryDirectory() as folder:
            store = CampaignStore(Path(folder) / "test.sqlite3")
            runtime = Runtime()
            dispatcher = Dispatcher(runtime.memory, BASE, store)
            dispatcher.poll()
            runtime.tick()
            dispatcher.poll()
            runtime.tick()
            runtime.at_beacon = True
            runtime.tick()
            response_before = bytes(runtime.memory.data[128:172])
            with patch.object(store, "complete", side_effect=OSError("simulated disk failure")):
                with self.assertRaises(OSError):
                    dispatcher.poll()
            self.assertEqual(bytes(runtime.memory.data[128:172]), response_before)
            runtime.tick()
            self.assertEqual(runtime.memory.get(7), 3)
            self.assertEqual(store.status()["gold"], 0)

    def test_plugin_has_only_hooks_and_never_runs_its_own_game_loop(self):
        tree = ast.parse(PLUGIN.read_text(encoding="utf-8"))
        calls = {node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)}
        self.assertTrue({"f_getcurpl", "f_setcurpl"} <= calls)
        self.assertFalse({"SaveMap", "LoadMap", "RunTrigTrigger", "EUDInfLoop", "EUDDoEvents"} & calls)


if __name__ == "__main__":
    unittest.main()
