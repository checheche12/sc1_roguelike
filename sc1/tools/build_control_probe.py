"""Build a stock-trigger input diagnostic, without compiling any EUD payload."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile

from build_probes import base_map, MAPS, MAGIC


def build():
    from eudplib import LoadMap
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata.chktok import CHK
    from eudplib.trigtrg import trigtrg as tt

    source = base_map(1)
    LoadMap(str(source))  # Names for stock actions only; SaveMap/EUD injector is never used.
    archive = mpqapi.MPQ.open(str(source))
    chk = CHK()
    chk.loadchk(archive.extract_file("staredit\\scenario.chk"))
    del archive
    strings = [b"SC1 Control Test - No EUD", b"Input diagnostic only. No manager or saving. Select and move the Marine.",
               b"Start", b"Finish", b"Anywhere", b"Probe Player", b"Computer",
               b"CONTROL TEST: Select the Marine and move to the beacon on the right.\nMinerals 123 is a fixed test display, NOT saved campaign gold.\nThis map does not need the manager.",
               b"CONTROL TEST PASSED: Marine reached the beacon. You may exit."]
    offset = 2 + 2 * len(strings)
    offsets = []
    for string in strings:
        offsets.append(offset)
        offset += len(string) + 1
    chk.setsection("STR ", struct.pack("<" + "H" * (len(strings) + 1), len(strings), *offsets)
                   + b"\0".join(strings) + b"\0")
    chk.setsection("VER ", struct.pack("<H", 205))
    triggers = [
        tt.Trigger(players=[tt.P1], conditions=[tt.Always()], actions=[
            tt.CreateUnit(1, "Terran Marine", 1, tt.P1),
            tt.CreateUnit(1, "Terran Beacon", 2, tt.P12),
            tt.CreateUnit(1, "Terran Command Center", 3, tt.P2),
            tt.SetInvincibility(tt.Enable, "Men", tt.P1, 64),
            tt.SetInvincibility(tt.Enable, "Buildings", tt.P2, 64),
            tt.SetResources(tt.P1, tt.SetTo, 123, tt.Ore),
            tt.CenterView(1), tt.SetMissionObjectives(8), tt.DisplayText(8),
        ]),
        tt.Trigger(players=[tt.P1], conditions=[tt.Bring(tt.P1, tt.AtLeast, 1, "Terran Marine", 2)],
                   actions=[tt.DisplayText(9)]),
    ]
    # trigtrg.Trigger defaults to preserved (flag 4). These stock triggers must
    # run once: repeating CreateUnit/CenterView would itself break this test.
    triggers = [trigger[:2368] + bytes(4) + trigger[2372:] for trigger in triggers]
    chk.setsection("TRIG", b"".join(triggers))
    destination = MAPS / "SC1_Control_Test.scx"
    destination.write_bytes(source.read_bytes())
    with tempfile.NamedTemporaryFile(delete=False, dir=destination.parent, suffix=".chk") as temp:
        temp.write(chk.savechk())
        temp_path = Path(temp.name)
    try:
        archive = mpqapi.MPQ.open(str(destination))
        archive.add_file("staredit\\scenario.chk", str(temp_path))
        archive.compact()
        del archive
    finally:
        temp_path.unlink()
    archive = mpqapi.MPQ.open(str(destination))
    raw = archive.extract_file("staredit\\scenario.chk")
    inspected = CHK()
    inspected.loadchk(raw)
    trig = inspected.getsection("TRIG")
    assert MAGIC not in raw
    assert len(trig) == 2 * 2400
    assert inspected.getsection("OWNR") == bytes([6, 5] + [0] * 10)
    action_types = []
    for index in range(2):
        chunk = trig[index * 2400:(index + 1) * 2400]
        assert chunk[2372:2400] == bytes([1]) + bytes(27), "Only P1 owns stock triggers"
        assert struct.unpack_from("<I", chunk, 2368)[0] == 0, "One-time triggers"
        action_types.extend(chunk[320 + action * 32 + 26] for action in range(64)
                            if chunk[320 + action * 32 + 26])
    assert action_types == [44, 44, 44, 43, 43, 26, 10, 12, 9, 9], action_types
    evidence = {"schema_version": 1, "status": "built_and_structurally_checked_runtime_pending",
                "purpose": "Separate stock-map input from EUD execution and manager connection issues",
                "path": str(destination), "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "bytes": destination.stat().st_size, "stock_triggers": 2,
                "action_types": action_types, "eud_payload": False, "manager_required": False,
                "fixed_mineral_display": 123, "writes_campaign_save": False,
                "camera_center_count": 1, "native_input_verified": False}
    (MAPS / "control_build_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    build()
