"""Build a stock-trigger mailbox/LOAD diagnostic, without an EUD loader.

The 64 DWORDs use ordinary death counters: unit = 220 + word // 12,
player = word % 12.  This native layout is supported by public SC:R tooling
source, but must still be verified in the user's actual game process.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import tempfile


MAPS = Path(__file__).resolve().parents[1] / "maps"
SOURCE = MAPS / "SC1_Control_Test.scx"
DESTINATION = MAPS / "SC1_Stock_Mailbox_Test.scx"
MAGIC = b"SC1CAMP-PROBE-V1"
WORD_COUNT = 64
FIRST_UNIT = 220


def counter(word: int) -> tuple[int, int]:
    assert 0 <= word < WORD_COUNT
    return word % 12, FIRST_UNIT + word // 12


def read_chk(path: Path):
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata.chktok import CHK

    archive = mpqapi.MPQ.open(str(path))
    try:
        raw = archive.extract_file("staredit\\scenario.chk")
        chk = CHK()
        chk.loadchk(raw)
        return chk, raw
    finally:
        del archive


def make_strings(strings: list[bytes]) -> bytes:
    offset = 2 + 2 * len(strings)
    offsets = []
    for string in strings:
        offsets.append(offset)
        offset += len(string) + 1
    assert offset < 65536
    return struct.pack("<" + "H" * (len(strings) + 1), len(strings), *offsets) + b"\0".join(strings) + b"\0"


def one_shot(trigger: bytes) -> bytes:
    return trigger[:2368] + bytes(4) + trigger[2372:]


def inspect_and_simulate(triggers: bytes) -> dict:
    """Check serialized CHK, then execute only its ordinary counter semantics.

    This is an offline fixture interpreter, not the StarCraft engine. Unknown
    actions/conditions fail the check instead of being silently simulated.
    """
    assert len(triggers) == 5 * 2400
    chunks = [triggers[i:i + 2400] for i in range(0, len(triggers), 2400)]
    action_counts: dict[int, int] = {}
    deaths_conditions = 0
    parsed = []
    for index, chunk in enumerate(chunks):
        assert chunk[2372:2400] == bytes([1]) + bytes(27), "P1 must own every trigger"
        preserved = struct.unpack_from("<I", chunk, 2368)[0]
        assert preserved == (4 if index == 2 else 0), "Only the heartbeat may repeat"
        conditions, actions = [], []
        for offset in range(0, 320, 20):
            condition = chunk[offset:offset + 20]
            kind = condition[15]
            if not kind:
                assert condition == bytes(20)
                continue
            assert kind in (3, 15, 22), f"Unexpected condition {kind}"
            if kind == 15:
                location, player, amount, unit, comparison = struct.unpack_from("<IIIHB", condition)
                assert location == 0 and condition[16:] == bytes(4), "No extended/masked Deaths"
                assert 0 <= player < 12 and FIRST_UNIT <= unit <= 225
                assert comparison == 10, "Only ordinary Exactly is needed"
                deaths_conditions += 1
            conditions.append(condition)
        for offset in range(320, 2368, 32):
            action = chunk[offset:offset + 32]
            kind = action[26]
            if not kind:
                assert action == bytes(32)
                continue
            assert kind in (9, 10, 12, 26, 43, 44, 45), f"Unexpected action {kind}"
            action_counts[kind] = action_counts.get(kind, 0) + 1
            if kind == 45:
                player, amount, unit, _, modifier = struct.unpack_from("<IIHBB", action, 16)
                assert action[:16] == bytes(16) and action[29:] == bytes(3)
                assert action[28] == 20 and modifier in (7, 8)
                assert 0 <= player < 12 and FIRST_UNIT <= unit <= 225
                assert (unit - FIRST_UNIT) * 12 + player < WORD_COUNT
            actions.append(action)
        parsed.append((conditions, actions, bool(preserved)))
    assert action_counts == {45: 70, 44: 3, 43: 2, 26: 2, 10: 1, 12: 1, 9: 3}
    assert deaths_conditions == 5

    words = [0] * WORD_COUNT
    enabled = [True] * len(parsed)
    runtime = {"minerals": 0, "camera_centers": 0, "created_units": 0, "texts": []}

    def tick():
        for index, (conditions, actions, preserved) in enumerate(parsed):
            if not enabled[index]:
                continue
            matches = True
            for condition in conditions:
                if condition[15] == 3:  # The simulated Marine never reaches Finish.
                    matches = False
                elif condition[15] == 15:
                    _, player, amount, unit = struct.unpack_from("<IIIH", condition)
                    matches &= words[(unit - FIRST_UNIT) * 12 + player] == amount
            if not matches:
                continue
            for action in actions:
                kind = action[26]
                if kind == 45:
                    player, amount, unit, _, modifier = struct.unpack_from("<IIHBB", action, 16)
                    word = (unit - FIRST_UNIT) * 12 + player
                    words[word] = amount if modifier == 7 else (words[word] + amount) & 0xFFFFFFFF
                elif kind == 26:
                    assert action[27] == 7
                    runtime["minerals"] = struct.unpack_from("<I", action, 20)[0]
                elif kind == 10:
                    runtime["camera_centers"] += 1
                elif kind == 44:
                    runtime["created_units"] += 1
                elif kind == 9:
                    runtime["texts"].append(struct.unpack_from("<I", action, 4)[0])
            if not preserved:
                enabled[index] = False

    tick()
    assert struct.pack("<4I", *words[:4]) == MAGIC
    assert words[4:10] == [1, 1, 1, 1, 2, 1]
    assert words[16] == 64 and words[10:16] == [0] * 6
    assert words[32:43] == [0] * 11
    assert runtime == {"minerals": 123, "camera_centers": 1, "created_units": 3, "texts": [8]}
    for seq, status, echo in ((1, 1, 2), (2, 2, 2), (2, 1, 4)):
        words[32:35] = [seq, status, echo]
        tick()
        assert words[7:10] == [1, 2, 1] and runtime["minerals"] == 123
    words[32:35] = [2, 1, 2]
    tick()
    assert words[7:10] == [2, 4, 0] and runtime["minerals"] == 321
    assert words[10:16] == [0] * 6, "This diagnostic deliberately does not copy nonce or gold"
    assert runtime["texts"] == [8, 9]
    tick()
    assert words[6] == 6 and words[7:10] == [2, 4, 0]
    assert runtime["camera_centers"] == 1 and runtime["created_units"] == 3
    assert runtime["texts"] == [8, 9], "ACK should display exactly once"
    return {
        "stock_triggers": len(parsed),
        "ordinary_set_deaths_actions": action_counts[45],
        "ordinary_deaths_conditions": deaths_conditions,
        "action_type_counts": action_counts,
        "offline_checked_cases": ["valid_player_and_unit_bounds", "no_extended_or_masked_deaths",
                                  "one_shot_initialization", "contiguous_64_word_header",
                                  "heartbeat_repeats", "odd_response_rejected", "wrong_status_rejected",
                                  "wrong_echo_rejected", "valid_load_ack", "ack_runs_once",
                                  "camera_and_unit_creation_run_once", "nonce_gold_copy_absent"],
        "offline_simulation_only": True,
    }


def build() -> None:
    from eudplib.bindings._rust import mpqapi
    from eudplib.trigtrg import trigtrg as tt

    source_bytes = SOURCE.read_bytes()
    chk, _ = read_chk(SOURCE)
    original_sections = dict(chk.sections)
    original_triggers = chk.getsection("TRIG")
    assert len(original_triggers) == 4800

    strings = [
        b"SC1 Stock Mailbox Test - No EUD",
        b"Standard-trigger mailbox discovery and LOAD ACK test only. No reward, completion, or campaign-gold restore.",
        b"Start", b"Finish", b"Anywhere", b"Probe Player", b"Computer",
        b"STOCK MAILBOX TEST: Select and move the Marine.\nMinerals 123 is a FIXED test value, not saved gold.\nOptional manager LOAD ACK changes it to fixed 321. No progress is committed.",
        b"LOAD ACK RECEIVED. Minerals 321 is a FIXED diagnostic value.\nNonce and campaign gold are NOT copied. No reward or completion is saved.",
        b"CONTROL CHECK: Marine reached the beacon. No result is sent or saved. You may exit.",
    ]
    chk.setsection("STR ", make_strings(strings))
    assert chk.getsection("VER ") == struct.pack("<H", 205)

    def write(word: int, value: int, modifier=tt.SetTo) -> bytes:
        player, unit = counter(word)
        return tt.SetDeaths(player, modifier, value, unit)

    def equal(word: int, value: int) -> bytes:
        player, unit = counter(word)
        return tt.Deaths(player, tt.Exactly, value, unit)

    initial = [0] * WORD_COUNT
    initial[:4] = struct.unpack("<4I", MAGIC)
    initial[4:10] = [1, 1, 0, 1, 1, 1]
    initial[16] = 64
    initialize = one_shot(tt.Trigger(players=[tt.P1], conditions=[tt.Always()],
                                    actions=[write(i, value) for i, value in enumerate(initial)]))

    # Keep the working stock map's gameplay setup byte-for-byte; publish only
    # after all 64 initialization writes, including response zeros, are done.
    start = bytearray(original_triggers[:2400])
    assert start[320 + 9 * 32:320 + 10 * 32] == bytes(32)
    start[320 + 9 * 32:320 + 10 * 32] = write(8, 2)
    heartbeat = tt.Trigger(players=[tt.P1], conditions=[tt.Always()], actions=[write(6, 1, tt.Add)])
    acknowledge = one_shot(tt.Trigger(
        players=[tt.P1],
        conditions=[equal(7, 1), equal(8, 2), equal(32, 2), equal(33, 1), equal(34, 2)],
        actions=[write(8, 3), write(7, 2), write(9, 0), write(8, 4),
                 tt.SetResources(tt.P1, tt.SetTo, 321, tt.Ore), tt.DisplayText(9)],
    ))
    finish = bytearray(original_triggers[2400:])
    assert finish[320 + 26] == 9
    struct.pack_into("<I", finish, 320 + 4, 10)
    triggers = initialize + bytes(start) + heartbeat + acknowledge + bytes(finish)
    checks = inspect_and_simulate(triggers)
    chk.setsection("TRIG", triggers)
    for name, section in original_sections.items():
        if name not in (b"TRIG", b"STR "):
            assert chk.sections[name] == section, name

    # Direct MPQ update only: no LoadMap, SaveMap, main_starter, or injector.
    DESTINATION.write_bytes(source_bytes)
    with tempfile.NamedTemporaryFile(delete=False, dir=MAPS, suffix=".chk") as temp:
        temp.write(chk.savechk())
        temporary = Path(temp.name)
    try:
        archive = mpqapi.MPQ.open(str(DESTINATION))
        try:
            archive.add_file("staredit\\scenario.chk", str(temporary))
            archive.compact()
        finally:
            del archive
    finally:
        temporary.unlink()
    inspected, _ = read_chk(DESTINATION)
    assert inspected.getsection("TRIG") == triggers
    assert inspected.getsection("STR ") == chk.getsection("STR ")
    assert set(inspected.sections) == set(original_sections)
    for name, section in original_sections.items():
        if name not in (b"TRIG", b"STR "):
            assert inspected.sections[name] == section, name
    inspect_and_simulate(inspected.getsection("TRIG"))
    assert SOURCE.read_bytes() == source_bytes

    evidence = {
        "schema_version": 1,
        "status": "built_and_offline_checked_native_runtime_pending",
        "purpose": "Native mailbox discovery, LOAD acknowledgment, and ordinary input controls only",
        "path": str(DESTINATION),
        "sha256": hashlib.sha256(DESTINATION.read_bytes()).hexdigest(),
        "bytes": DESTINATION.stat().st_size,
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_unchanged": True,
        "unchanged_sections": [name.decode("ascii") for name in original_sections if name not in (b"TRIG", b"STR ")],
        "ver": 205,
        "string_section": "STR ",
        "eud_payload": False,
        "save_map_used": False,
        "main_starter": False,
        "injector": False,
        "extended_or_masked_deaths": False,
        "mailbox": {"magic": MAGIC.decode(), "version": 1, "mission": 1, "words": 64,
                    "mapping": "unit_id = 220 + word_index // 12; player_index = word_index % 12",
                    "reserved_unit_ids": list(range(220, 226)), "reserved_players": list(range(1, 13)),
                    "last_used_cell": {"unit_id": 225, "player": 4},
                    "native_unit_major_contiguous_layout_verified": False,
                    "source_support": ["https://github.com/neivv/aise/blob/master/bw_dat/src/bw/structs.rs",
                                       "https://github.com/neivv/aise/blob/master/bw_dat/src/game.rs"],
                    "initial_state": 1, "initial_sequence": 2, "initial_operation": 1,
                    "response_required": {"sequence": 2, "status": 1, "echo": 2},
                    "ack_state": 2, "ack_sequence": 4, "ack_operation": 0},
        "fixed_initial_minerals": 123,
        "fixed_ack_minerals": 321,
        "copies_restored_nonce": False,
        "copies_restored_gold": False,
        "sends_commit": False,
        "writes_campaign_growth": False,
        "manager_caveat": "An existing manager LOAD may create attempt metadata; this map sends no COMMIT or reward.",
        "native_scan_caveat": "Native region type is unverified; a private-RW-only scanner could miss image-backed Game data.",
        **checks,
        "installed": False,
        "native_verified": False,
        "native_input_verified": False,
        "native_mailbox_verified": False,
        "manager_started": False,
        "game_started": False,
    }
    evidence_path = MAPS / "stock_mailbox_build_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    build()
