"""Normalize the stock control map to VER 206/STRx without any EUD runtime."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import tempfile


MAPS = Path(__file__).resolve().parents[1] / "maps"
SOURCE = MAPS / "SC1_Control_Test.scx"
DESTINATION = MAPS / "SC1_Format_Control_Test.scx"


def read_chk(path: Path):
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata.chktok import CHK

    archive = mpqapi.MPQ.open(str(path))
    try:
        raw = archive.extract_file("staredit\\scenario.chk")
        chk = CHK()
        chk.loadchk(raw)
        return chk, raw, archive.get_file_names_from_listfile()
    finally:
        del archive


def string_at(chk, index: int) -> bytes:
    extended = b"STRx" in chk.sections
    data = chk.getsection("STRx" if extended else "STR ")
    width, code = (4, "<I") if extended else (2, "<H")
    count = struct.unpack_from(code, data)[0]
    assert 0 < index <= count
    offset = struct.unpack_from(code, data, width * index)[0]
    return data[offset:data.index(b"\0", offset)]


def build() -> None:
    from eudplib import LoadMap
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata import fixmapdata, mapdata
    from eudplib.core.mapdata.stringmap import ForceAddString

    source_bytes = SOURCE.read_bytes()
    original, _, _ = read_chk(SOURCE)
    LoadMap(str(SOURCE))
    chk = mapdata.GetChkTokenized()

    # Only the scenario label changes. All existing gameplay text and IDs stay
    # intact so the original two stock triggers can be compared byte for byte.
    title = ForceAddString("SC1 Format Control - No EUD")
    description = ForceAddString(
        "VER 206 / STRx format comparison only. Standard triggers; no EUD "
        "loader, mailbox, manager, or saving. Minerals remain fixed at 123."
    )
    mapdata.update_map_data()
    chk.setsection("SPRP", struct.pack("<HH", title, description))
    fixmapdata._fix_map_data(chk)
    chk.optimize()

    unchanged_sections = (
        "TRIG", "MRGN", "OWNR", "SIDE", "FORC", "DIM ", "ERA ", "MTXM",
        "MASK", "UNIT", "PUNI", "PUPx", "PTEx", "UNIx", "UPGx", "TECx",
        "THG2", "UPRP", "COLR", "MBRF", "VCOD",
    )
    for section in unchanged_sections:
        assert chk.getsection(section) == original.getsection(section), section
    assert chk.getsection("VER ") == struct.pack("<H", 206)
    assert b"STR " not in chk.sections and b"STRx" in chk.sections
    gameplay_string_ids = (1, 2, 6, 7, 8, 9)
    # eudplib deliberately discards editor-only location names during LoadMap.
    # Keep that normalizer behavior as part of this format comparison.
    for index in (3, 4, 5):
        assert string_at(chk, index) == b""
    for index in gameplay_string_ids:
        assert string_at(chk, index) == string_at(original, index), index

    # Deliberately do not call SaveMap, main_starter, or apply_injector.
    DESTINATION.write_bytes(source_bytes)
    with tempfile.NamedTemporaryFile(delete=False, dir=MAPS, suffix=".chk") as temp:
        temp.write(chk.savechk())
        temp_path = Path(temp.name)
    try:
        archive = mpqapi.MPQ.open(str(DESTINATION))
        try:
            archive.add_file("staredit\\scenario.chk", str(temp_path))
            archive.compact()
        finally:
            del archive
    finally:
        temp_path.unlink()

    inspected, raw, entries = read_chk(DESTINATION)
    for section in unchanged_sections:
        assert inspected.getsection(section) == original.getsection(section), section
    triggers = inspected.getsection("TRIG")
    assert len(triggers) == 2 * 2400
    action_types = []
    for offset in range(0, len(triggers), 2400):
        trigger = triggers[offset:offset + 2400]
        assert struct.unpack_from("<I", trigger, 2368)[0] == 0
        assert trigger[2372:2400] == bytes([1]) + bytes(27)
        action_types.extend(trigger[320 + 32 * action + 26] for action in range(64)
                            if trigger[320 + 32 * action + 26])
    assert action_types == [44, 44, 44, 43, 43, 26, 10, 12, 9, 9]
    assert inspected.getsection("VER ") == struct.pack("<H", 206)
    assert len(inspected.getsection("STRx")) < 4096
    assert b"SC1CAMP-PROBE-V1" not in raw
    assert string_at(inspected, title) == b"SC1 Format Control - No EUD"
    for index in gameplay_string_ids:
        assert string_at(inspected, index) == string_at(original, index)
    assert all(entry in ("staredit\\scenario.chk", "(listfile)") for entry in entries)
    assert SOURCE.read_bytes() == source_bytes, "Stock control map was changed"

    evidence = {
        "schema_version": 1,
        "status": "built_and_structurally_checked_runtime_pending",
        "kind": "stock_triggers_with_remastered_format_normalization",
        "path": str(DESTINATION),
        "sha256": hashlib.sha256(DESTINATION.read_bytes()).hexdigest(),
        "bytes": DESTINATION.stat().st_size,
        "source": str(SOURCE),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "source_unchanged": True,
        "eudplib_version": importlib.metadata.version("eudplib"),
        "pipeline": ["LoadMap", "scenario_label_only", "mapdata.update_map_data",
                     "fixmapdata._fix_map_data", "CHK.optimize", "MPQ_write"],
        "ver": 206,
        "string_section": "STRx",
        "string_section_bytes": len(inspected.getsection("STRx")),
        "stock_triggers": 2,
        "stock_trigger_bytes_unchanged": True,
        "trigger_action_types": action_types,
        "unchanged_gameplay_sections": list(unchanged_sections),
        "original_gameplay_string_ids_preserved": list(gameplay_string_ids),
        "editor_location_string_ids_cleared_by_normalizer": [3, 4, 5],
        "eud_payload": False,
        "main_starter": False,
        "injector": False,
        "mailbox": False,
        "manager_required": False,
        "fixed_minerals": 123,
        "installed": False,
        "native_verified": False,
        "game_started": False,
    }
    evidence_path = MAPS / "format_control_build_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    build()
