"""Build a stock-map baseline with the unmodified official euddraft CLI.

Run with sc1/vendor/eud-venv/Scripts/python.exe. The local eudplib is used only
to prepare/read MPQs; compilation runs the separately pinned release EXE.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import time
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "maps"
SOURCE = MAPS / "SC1_Control_Test.scx"
SOURCE_SHA256 = "94488bd058c30423fdff5e16715f28bc073935977259b6b15ced0ebc21147b1b"
BUILD = MAPS / "build" / "official_euddraft_baseline"
DESTINATION = MAPS / "SC1_Official_EUD_Baseline.scx"
VENDOR = ROOT / "vendor" / "euddraft-official-0.11.0.0"
PACKAGE = VENDOR / "euddraft0.11.0.0.zip"
RELEASE_DIR = VENDOR / "release"
RELEASE_URL = "https://github.com/armoha/euddraft/releases/tag/v0.11.0.0"
ASSET_URL = "https://github.com/armoha/euddraft/releases/download/v0.11.0.0/euddraft0.11.0.0.zip"
ASSET_SHA256 = "cfc153e8e35218383835bffe586f06ac067cd3690772982c079fd0f6db013f8f"
SOURCE_COMMIT = "d723e1f08cc8e32da9a8efacec9e785d910e7d3a"
INFO_PREFIX = "SC1_OFFICIAL_BUILD_INFO="


PLUGIN = '''"""Minimal official-euddraft plugin; no mailbox, manager, or injector patch."""
import json
import sys
import types

import eudplib as ep


def onPluginStart():
    import applyeuddraft
    import pluginLoader

    def names(code):
        found = set(code.co_names)
        for value in code.co_consts:
            if isinstance(value, types.CodeType):
                found.update(names(value))
        return found

    wrapper_names = names(applyeuddraft.createPayloadMain.__code__)
    assert {"RunTrigTrigger", "EUDDoEvents", "EUDInfLoop"} <= wrapper_names
    assert "_set_game_loop_start" in names(pluginLoader.loadPluginsFromConfig.__code__)
    assert not pluginLoader.isFreezeIssued()
    assert ep.eudplibVersion() == "0.81.0"
    print("SC1_OFFICIAL_BUILD_INFO=" + json.dumps({
        "eudplib_version": ep.eudplibVersion(),
        "python_version": sys.version,
        "python_executable": sys.executable,
        "official_wrapper_names": sorted(wrapper_names),
        "official_game_loop_start_present": True,
        "freeze_enabled": pluginLoader.isFreezeIssued(),
    }))
    ep.DoActions([
        ep.SetResources(ep.P1, ep.SetTo, 1001, ep.Ore),
        ep.SetResources(ep.P1, ep.SetTo, 0, ep.Gas),
    ])


def afterTriggerExec():
    # RunTrigTrigger has just run the stock setup, which sets minerals to 123.
    # Publish the intended visible marker once, after that setup is complete.
    if ep.EUDExecuteOnce()():
        ep.DoActions([
            ep.SetResources(ep.P1, ep.SetTo, 1001, ep.Ore),
            ep.DisplayText("OFFICIAL EUD BASELINE: minerals 1001, increasing gas.\\nSelect, drag, move, and scroll to test normal controls. No manager or saving."),
        ])
    ep.EUDEndExecuteOnce()
    ep.DoActions(ep.SetResources(ep.P1, ep.Add, 1, ep.Gas))
'''


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_chk(path: Path):
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata.chktok import CHK

    archive = mpqapi.MPQ.open(str(path))
    try:
        raw = archive.extract_file("staredit\\scenario.chk")
        if not raw:
            # Official sector-size SaveMap puts an empty decoy in locale0.
            archive.set_file_locale(0x409)
            raw = archive.extract_file("staredit\\scenario.chk")
        assert raw, "No real scenario.chk found in neutral or0x409 locale"
        chk = CHK()
        chk.loadchk(raw)
        return chk, raw
    finally:
        archive.set_file_locale(0)
        del archive


def write_chk_copy(source_bytes: bytes, destination: Path, chk) -> None:
    from eudplib.bindings._rust import mpqapi

    destination.write_bytes(source_bytes)
    with tempfile.NamedTemporaryFile(delete=False, dir=destination.parent, suffix=".chk") as temp:
        temp.write(chk.savechk())
        temporary = Path(temp.name)
    try:
        archive = mpqapi.MPQ.open(str(destination))
        try:
            archive.add_file("staredit\\scenario.chk", str(temporary))
            archive.compact()
        finally:
            del archive
    finally:
        temporary.unlink()


def setup_release() -> dict:
    VENDOR.mkdir(parents=True, exist_ok=True)
    if not PACKAGE.exists():
        with urllib.request.urlopen(ASSET_URL, timeout=60) as response:
            content = response.read()
        assert digest(content) == ASSET_SHA256, "Official release asset hash mismatch"
        PACKAGE.write_bytes(content)
    assert digest(PACKAGE.read_bytes()) == ASSET_SHA256
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    with zipfile.ZipFile(PACKAGE) as archive:
        for entry in archive.infolist():
            destination = (RELEASE_DIR / entry.filename).resolve()
            assert destination.is_relative_to(RELEASE_DIR.resolve()), "Unsafe ZIP path"
            assert (entry.external_attr >> 16) & 0o170000 != 0o120000, "Unexpected ZIP symlink"
            if entry.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue
            content = archive.read(entry)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                assert destination.read_bytes() == content, f"Pinned release file changed: {entry.filename}"
            else:
                destination.write_bytes(content)
            manifest[entry.filename] = digest(content)
    executable = RELEASE_DIR / "euddraft.exe"
    assert executable.is_file()
    # Official updater cache only. No code is patched. Record the currently
    # published version so the pinned build does not open an update prompt.
    with urllib.request.urlopen("https://raw.githubusercontent.com/armoha/euddraft/main/latest/VERSION", timeout=30) as response:
        checked_version = response.read().decode("utf-8").strip()
    assert all(part.isdecimal() for part in checked_version.split("."))
    checkpoint = f"{checked_version} {int(time.time())}"
    (RELEASE_DIR / "vcheckpoint.dat").write_text(checkpoint, encoding="ascii")
    result = {
        "release_url": RELEASE_URL, "asset_url": ASSET_URL,
        "source_commit": SOURCE_COMMIT, "package_path": str(PACKAGE),
        "package_sha256": ASSET_SHA256, "package_bytes": PACKAGE.stat().st_size,
        "executable": str(executable), "executable_sha256": digest(executable.read_bytes()),
        "file_sha256": manifest,
        "updater_cache": {"path": str(RELEASE_DIR / "vcheckpoint.dat"), "content": checkpoint,
                          "purpose": "Suppress updater prompt while retaining the pinned official release", "code_modified": False},
    }
    (VENDOR / "provenance.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def prepare_input() -> tuple[Path, bytes, object]:
    source_bytes = SOURCE.read_bytes()
    assert digest(source_bytes) == SOURCE_SHA256, "Working stock baseline changed; review before building"
    chk, _ = read_chk(SOURCE)
    original = dict(chk.sections)
    raw = chk.getsection("STR ")
    count = struct.unpack_from("<H", raw)[0]
    strings = []
    for index in range(1, count + 1):
        offset = struct.unpack_from("<H", raw, index * 2)[0]
        strings.append(raw[offset:raw.index(b"\0", offset)])
    strings[0] = b"Official EUD Baseline"
    strings[1] = b"Official euddraft 0.11.0.0 / eudplib 0.81.0, stock triggers, minimal plugin, eudTurbo, freeze disabled. Input diagnostic only."
    strings[7] = b"OFFICIAL EUD BASELINE: Stock unit setup has run.\nExpect minerals 1001 and increasing gas.\nTest Marine selection, dragging, movement, and camera scrolling. No manager or saving."
    strings[8] = b"BEACON REACHED. Stock Bring trigger executed. No progress is saved."
    offset, offsets = 2 + 2 * count, []
    for string in strings:
        offsets.append(offset)
        offset += len(string) + 1
    chk.setsection("STR ", struct.pack("<" + "H" * (count + 1), count, *offsets) + b"\0".join(strings) + b"\0")
    for name, value in original.items():
        if name != b"STR ":
            assert chk.sections[name] == value, name
    baseline = BUILD / "official_input.scx"
    write_chk_copy(source_bytes, baseline, chk)
    inspected, _ = read_chk(baseline)
    assert inspected.getsection("TRIG") == original[b"TRIG"]
    return baseline, source_bytes, inspected


def build() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    release = setup_release()
    baseline, source_bytes, prepared = prepare_input()
    plugin = BUILD / "baseline.py"
    plugin.write_text(PLUGIN, encoding="utf-8")
    config = BUILD / "baseline.eds"
    config.write_text("[main]\ninput: official_input.scx\noutput: ../../SC1_Official_EUD_Baseline.scx\n\n[baseline.py]\n\n[eudTurbo]\n\n[freeze]\nfreeze: 0\n", encoding="utf-8")
    command = [release["executable"], str(config)]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started_ns = time.time_ns()
    process = subprocess.run(command, cwd=BUILD, input="\n", capture_output=True, text=True,
                             encoding="utf-8", errors="replace", timeout=180,
                             env=environment, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log = process.stdout + ("\nSTDERR:\n" + process.stderr if process.stderr else "")
    log_path = BUILD / "official_cli_build.log"
    log_path.write_text(log, encoding="utf-8")
    print(log)
    assert process.returncode == 0 and "[Error]" not in log, "Official CLI failed; inspect build log"
    assert "euddraft 0.11.0.0" in log
    assert DESTINATION.exists() and DESTINATION.stat().st_mtime_ns >= started_ns
    info_lines = [line for line in log.splitlines() if line.startswith(INFO_PREFIX)]
    assert len(info_lines) == 1
    build_info = json.loads(info_lines[0][len(INFO_PREFIX):])
    assert build_info["eudplib_version"] == "0.81.0" and not build_info["freeze_enabled"]
    for name, expected in release["file_sha256"].items():
        assert digest((RELEASE_DIR / name).read_bytes()) == expected, f"Official package changed: {name}"
    assert SOURCE.read_bytes() == source_bytes

    output, output_raw = read_chk(DESTINATION)
    assert struct.unpack_from("<H", DESTINATION.read_bytes(), 14)[0] == 15
    original_triggers = prepared.getsection("TRIG")
    compiled_triggers = output.getsection("TRIG")
    assert len(compiled_triggers) > len(original_triggers) and len(compiled_triggers) % 2400 == 0
    # The official default inliner moves stock triggers into STRx. Verify the
    # complete action sequence, nontrivial condition, and one-shot flag there.
    strings = output.getsection("STRx")
    retained_offsets = []
    for offset in range(0, len(original_triggers), 2400):
        original = original_triggers[offset:offset + 2400]
        actions = [original[pos:pos + 32] for pos in range(320, 2368, 32) if original[pos + 26]]
        action_bytes = b"".join(actions)
        action_offset = strings.find(action_bytes)
        assert action_offset >= 328 and strings.find(action_bytes, action_offset + 1) == -1
        trigger_offset = action_offset - 328
        conditions = [original[pos:pos + 20] for pos in range(0, 320, 20)
                      if original[pos + 15] not in (0, 22)]  # Always is intentionally omitted.
        assert strings[trigger_offset + 8:trigger_offset + 8 + 20 * len(conditions)] == b"".join(conditions)
        assert strings[trigger_offset + 8 + 20 * len(conditions) + 15] == 0
        assert struct.unpack_from("<I", strings, trigger_offset + 2376)[0] == 0, "Original stock triggers must stay one-shot"
        retained_offsets.append(trigger_offset)
    assert struct.unpack_from("<I", strings, retained_offsets[0] + 4)[0] == 0x191943C8 + retained_offsets[1], "Stock trigger sequence changed"
    dispatcher, terminator = compiled_triggers[-4800:-2400], compiled_triggers[-2400:]
    assert struct.unpack_from("<I", dispatcher)[0] == 1024
    assert struct.unpack_from("<I", dispatcher, 2368)[0] == 0x10000008
    assert dispatcher[2372:2400] == bytes([1]) + bytes(27)
    assert struct.unpack_from("<I", terminator, 2368)[0] == 12
    assert terminator[2372 + 17] == 1
    unchanged = ["OWNR", "SIDE", "FORC", "DIM ", "ERA ", "MTXM", "MASK", "UNIT", "PUNI", "PUPx", "PTEx",
                 "UNIx", "UPGx", "TECx", "THG2", "UPRP", "COLR", "MBRF", "VCOD"]
    for section in unchanged:
        assert output.getsection(section) == prepared.getsection(section), section
    assert output.getsection("VER ") == struct.pack("<H", 206)
    title_id = struct.unpack_from("<H", output.getsection("SPRP"))[0]
    title_offset = struct.unpack_from("<I", strings, 4 * title_id)[0]
    assert strings[title_offset:strings.index(b"\0", title_offset)] == b"Official EUD Baseline"
    assert b"SC1CAMP-PROBE-V1" not in output_raw
    assert b"OFFICIAL EUD BASELINE: minerals 1001, increasing gas." in output_raw
    evidence = {
        "schema_version": 1, "status": "official_cli_compiled_and_structurally_checked_native_runtime_pending",
        "path": str(DESTINATION), "sha256": digest(DESTINATION.read_bytes()), "bytes": DESTINATION.stat().st_size,
        "source": str(SOURCE), "source_sha256": SOURCE_SHA256, "source_unchanged": True,
        "prepared_input": str(baseline), "prepared_input_sha256": digest(baseline.read_bytes()),
        "prepared_input_stock_trig_byte_identical": True,
        "official_cli": {"version": "0.11.0.0", "executable": release["executable"],
                         "executable_sha256": release["executable_sha256"], "asset_url": ASSET_URL,
                         "asset_sha256": ASSET_SHA256, "source_commit": SOURCE_COMMIT,
                         "command": command, "cwd": str(BUILD), "exit_code": process.returncode,
                         "package_files_unchanged": True, "provenance": str(VENDOR / "provenance.json")},
        "build_info": build_info,
        "plugin": str(plugin), "plugin_sha256": digest(plugin.read_bytes()),
        "config": str(config), "config_sha256": digest(config.read_bytes()), "log": str(log_path),
        "freeze": {"explicit_option": "[freeze] freeze: 0", "actual_enabled": False,
                   "reason": "pluginLoader defaults freeze_enabled=True; an explicit freeze key sets it False",
                   "source": f"https://github.com/armoha/euddraft/blob/{SOURCE_COMMIT}/pluginLoader.py"},
        "mpq_sector_size": {"explicit_option": None, "official_default": 15, "bytes": 16777216,
                            "header_verified": True,
                            "real_chk_locale": "0x409", "neutral_locale_contains_empty_decoy": True,
                            "reader_resolution": "Select0x409 to avoid the intended neutral-locale empty decoy",
                            "initial_reader_observation": str(BUILD / "default_sector15_validation.json"),
                            "intermediate_sector3_attempt": str(BUILD / "sector3_intermediate_validation.json")},
        "runtime_flow_source": f"https://github.com/armoha/euddraft/blob/{SOURCE_COMMIT}/applyeuddraft.py",
        "expected_runtime_flow": ["onPluginStart", "_set_game_loop_start", "RunTrigTrigger", "eudTurbo.afterTriggerExec", "baseline.afterTriggerExec", "EUDDoEvents"],
        "stock_triggers": len(original_triggers) // 2400,
        "compiled_chk_triggers": len(compiled_triggers) // 2400,
        "stock_trigger_retention": "Official default inliner moves both records into STRx; complete original action sequences, Bring condition, one-shot flags, and next-pointer order verified",
        "stock_payload_trigger_strx_offsets": retained_offsets,
        "stock_dispatcher_and_terminator_verified": True,
        "unchanged_gameplay_sections": unchanged,
        "ver": 206, "string_section": "STRx", "internal_title": "Official EUD Baseline",
        "expected_minerals": 1001,
        "mineral_marker_order": "onPluginStart sets1001; stock setup sets123; first afterTriggerExec sets1001 once",
        "expected_gas": "Starts at0, increments by1 every afterTriggerExec; eudTurbo enabled",
        "uses_official_injector": True, "injector_monkeypatch": False,
        "mailbox": False, "manager_required": False, "writes_campaign_growth": False,
        "installed": False, "game_started": False, "native_verified": False,
        "native_input_verified": False, "native_stock_trigger_execution_verified": False,
    }
    evidence_path = MAPS / "official_euddraft_baseline_build_evidence.json"
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    build()
