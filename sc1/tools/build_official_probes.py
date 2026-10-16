"""Build the A/B growth probes through the pinned official euddraft CLI."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import struct
import subprocess
import time

from build_official_euddraft_baseline import (
    ASSET_SHA256, ASSET_URL, RELEASE_DIR, SOURCE, SOURCE_COMMIT, SOURCE_SHA256,
    VENDOR as OFFICIAL_VENDOR, digest, read_chk, setup_release, write_chk_copy,
)


ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "maps"
PLUGIN = ROOT / "plugins" / "growth_probe.py"
NAMES = {1: "SC1_Probe_A_Save.scx", 2: "SC1_Probe_B_Restore.scx"}
MAGIC = b"SC1CAMP-PROBE-V1"
MIGRATION_BACKUP = "backups/official_probes_migration_20261014_132924_188352/manifest.json"
UNCHANGED_SECTIONS = ("OWNR", "SIDE", "FORC", "DIM ", "ERA ", "MTXM", "MASK", "UNIT", "PUNI", "PUPx", "PTEx",
                      "UNIx", "UPGx", "TECx", "THG2", "UPRP", "COLR", "MBRF", "VCOD")


def workdir(mission):
    return MAPS / "build" / f"official_probe_{mission}"


def backup_previous(missions):
    destination = ROOT / "backups" / ("official_probes_build_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    paths = [MAPS / NAMES[m] for m in missions] + [MAPS / "build_evidence.json"]
    paths += [workdir(m) / "compile_receipt.json" for m in missions]
    rows = []
    for source in paths:
        if not source.exists():
            continue
        data = source.read_bytes()
        target = destination / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        assert digest(target.read_bytes()) == digest(data)
        rows.append({"path": str(source.relative_to(ROOT)), "sha256": digest(data), "bytes": len(data)})
    destination.mkdir(parents=True, exist_ok=True)
    receipt = destination / "manifest.json"
    receipt.write_text(json.dumps({"schema_version": 1, "files": rows, "migration_source_backup": MIGRATION_BACKUP}, indent=2) + "\n", encoding="utf-8")
    return str(receipt)


def release_info():
    provenance = OFFICIAL_VENDOR / "provenance.json"
    if not provenance.exists():
        return setup_release()
    info = json.loads(provenance.read_text(encoding="utf-8"))
    assert info["package_sha256"] == ASSET_SHA256
    for name, expected in info["file_sha256"].items():
        assert digest((RELEASE_DIR / name).read_bytes()) == expected, f"Official file changed: {name}"
    # Refresh only the official updater cache; leave the baseline/provenance
    # files intact. This release remains pinned; no runtime code is patched.
    (RELEASE_DIR / "vcheckpoint.dat").write_text(f"0.11.0.1 {int(time.time())}", encoding="ascii")
    return info


def prepare_input(mission):
    source_bytes = SOURCE.read_bytes()
    assert digest(source_bytes) == SOURCE_SHA256
    chk, _ = read_chk(SOURCE)
    original = dict(chk.sections)
    data = chk.getsection("STR ")
    count = struct.unpack_from("<H", data)[0]
    strings = []
    for index in range(1, count + 1):
        offset = struct.unpack_from("<H", data, index * 2)[0]
        strings.append(data[offset:data.index(b"\0", offset)])
    title = f"SC1 Growth {'A - Save +123' if mission == 1 else 'B - Restore'} (Official)"
    strings[0] = title.encode("ascii")
    strings[1] = b"Sample growth-storage mission. Official euddraft plugin build. Connect the local manager, then reach the right beacon. No mid-battle save."
    strings[7] = b"GROWTH PROBE: Waiting for the local manager to restore growth.\nAfter GROWTH RESTORED, move the Marine to the beacon on the RIGHT.\nWait for SAVE ACKNOWLEDGED before exiting. This is a sample mission."
    strings[8] = b"BEACON REACHED. Wait for the plugin's SAVE ACKNOWLEDGED message before exiting."
    offset, offsets = 2 + 2 * count, []
    for string in strings:
        offsets.append(offset)
        offset += len(string) + 1
    chk.setsection("STR ", struct.pack("<" + "H" * (count + 1), count, *offsets) + b"\0".join(strings) + b"\0")
    triggers = bytearray(chk.getsection("TRIG"))
    assert len(triggers) == 4800 and triggers[320 + 5 * 32 + 26] == 26
    assert struct.unpack_from("<I", triggers, 320 + 5 * 32 + 20)[0] == 123
    struct.pack_into("<I", triggers, 320 + 5 * 32 + 20, 0)
    chk.setsection("TRIG", bytes(triggers))
    for name, value in original.items():
        if name not in (b"STR ", b"TRIG"):
            assert chk.sections[name] == value, name
    folder = workdir(mission)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "input.scx"
    write_chk_copy(source_bytes, path, chk)
    return path, title


def inspect_one(mission):
    path = MAPS / NAMES[mission]
    output, raw = read_chk(path)
    prepared, _ = read_chk(workdir(mission) / "input.scx")
    assert raw.count(MAGIC) == 1
    mailbox_offset = raw.index(MAGIC)
    words = struct.unpack_from("<64I", raw, mailbox_offset)
    assert words[4:6] == (1, mission) and words[6:16] == (0,) * 10
    assert words[16] == 64 and words[17:] == (0,) * 47
    assert struct.unpack_from("<H", path.read_bytes(), 14)[0] == 15
    assert output.getsection("VER ") == struct.pack("<H", 206)
    for section in UNCHANGED_SECTIONS:
        assert output.getsection(section) == prepared.getsection(section), section
    strings = output.getsection("STRx")
    assert strings.count(MAGIC) == 1
    assert strings.index(MAGIC) % 4 == 0
    title_id = struct.unpack_from("<H", output.getsection("SPRP"))[0]
    title_offset = struct.unpack_from("<I", strings, 4 * title_id)[0]
    title = strings[title_offset:strings.index(b"\0", title_offset)].decode("ascii")
    assert title == f"SC1 Growth {'A - Save +123' if mission == 1 else 'B - Restore'} (Official)"
    trigger_offsets = []
    original_triggers = prepared.getsection("TRIG")
    for offset in (0, 2400):
        original = original_triggers[offset:offset + 2400]
        actions = b"".join(original[i:i + 32] for i in range(320, 2368, 32) if original[i + 26])
        action_offset = strings.find(actions)
        assert action_offset >= 328 and strings.find(actions, action_offset + 1) == -1
        trigger_offset = action_offset - 328
        conditions = b"".join(original[i:i + 20] for i in range(0, 320, 20) if original[i + 15] not in (0, 22))
        assert strings[trigger_offset + 8:trigger_offset + 8 + len(conditions)] == conditions
        assert strings[trigger_offset + 8 + len(conditions) + 15] == 0
        assert struct.unpack_from("<I", strings, trigger_offset + 2376)[0] == 0
        trigger_offsets.append(trigger_offset)
    assert struct.unpack_from("<I", strings, trigger_offsets[0] + 4)[0] == 0x191943C8 + trigger_offsets[1]
    compiled_triggers = output.getsection("TRIG")
    assert len(compiled_triggers) == 72 * 2400
    dispatcher = compiled_triggers[-4800:-2400]
    assert struct.unpack_from("<I", dispatcher)[0] == 1024
    assert struct.unpack_from("<I", dispatcher, 2368)[0] == 0x10000008
    assert dispatcher[2372:2400] == bytes([1]) + bytes(27)
    return {
        "path": "maps/" + NAMES[mission], "mission": mission, "reward": 123 if mission == 1 else 0,
        "bytes": path.stat().st_size, "sha256": digest(path.read_bytes()), "internal_title": title,
        "scenario_chk_bytes": len(raw), "mailbox_matches": 1,
        "mailbox_file_offset_not_runtime_address": mailbox_offset,
        "mailbox_strx_offset_not_runtime_address": strings.index(MAGIC),
        "mailbox_initial_words_verified": True,
        "trigger_section_bytes": len(compiled_triggers), "stock_trigger_count": 2,
        "stock_payload_trigger_strx_offsets": trigger_offsets,
        "stock_action_condition_one_shot_order_verified": True,
        "mpq_sector_size": 15, "real_chk_locale": "0x409",
        "human_players": 1, "computer_players": 1, "start_locations": 2, "computer_ai_script": False,
        "native_verified": False, "live_bridge_verified": False,
    }


def build_one(mission):
    assert mission in NAMES
    protected = {p: digest(p.read_bytes()) for p in MAPS.glob("*.scx") if p.name not in NAMES.values()}
    official = release_info()
    baseline, title = prepare_input(mission)
    folder = workdir(mission)
    config = folder / "growth.eds"
    config.write_text(f"[main]\ninput: input.scx\noutput: ../../{NAMES[mission]}\n\n[../../../plugins/growth_probe.py]\nmission: {mission}\n\n[eudTurbo]\n\n[freeze]\nfreeze: 0\n", encoding="utf-8")
    command = [official["executable"], str(config)]
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    started_ns = time.time_ns()
    result = subprocess.run(command, cwd=folder, input="\n", capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=180, env=environment,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    log = result.stdout + ("\nSTDERR:\n" + result.stderr if result.stderr else "")
    log_path = folder / "official_cli_build.log"
    log_path.write_text(log, encoding="utf-8")
    print(log)
    assert result.returncode == 0 and "[Error]" not in log and "euddraft 0.11.0.0" in log
    assert (MAPS / NAMES[mission]).stat().st_mtime_ns >= started_ns
    prefix = "SC1_GROWTH_BUILD_INFO="
    info_lines = [line for line in log.splitlines() if line.startswith(prefix)]
    assert len(info_lines) == 1
    info = json.loads(info_lines[0][len(prefix):])
    assert info["mission"] == mission and info["eudplib_version"] == "0.81.0" and info["freeze_enabled"] is False
    for path, before in protected.items():
        assert digest(path.read_bytes()) == before, f"Diagnostic/baseline changed: {path}"
    for name, expected in official["file_sha256"].items():
        assert digest((RELEASE_DIR / name).read_bytes()) == expected
    evidence = inspect_one(mission)
    evidence.update({
        "official_cli_version": "0.11.0.0", "official_cli_command": command,
        "official_asset_url": ASSET_URL, "official_asset_sha256": ASSET_SHA256,
        "official_source_commit": SOURCE_COMMIT, "official_package_files_unchanged": True,
        "official_executable_sha256": official["executable_sha256"],
        "build_info": info, "plugin": str(PLUGIN), "plugin_sha256": digest(PLUGIN.read_bytes()),
        "config": str(config), "config_sha256": digest(config.read_bytes()), "log": str(log_path),
        "input": str(baseline), "input_sha256": digest(baseline.read_bytes()),
        "stock_source": str(SOURCE), "stock_source_sha256": SOURCE_SHA256,
        "stock_changes": ["Scenario/instruction strings", "Initial fixed mineral diagnostic123 changed to0"],
        "preserved_gameplay_sections": list(UNCHANGED_SECTIONS),
        "official_baseline_and_diagnostics_unchanged": True,
        "eudTurbo": True, "freeze_enabled": False, "injector_monkeypatch": False,
        "plugin_custom_infinite_loop": False, "plugin_direct_SaveMap": False,
        "current_player_preserved_at_both_hooks": True, "formatted_printing": False,
        "game_started": False, "installed_in_game": False,
    })
    (folder / "compile_receipt.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def inspect_maps():
    outputs = []
    for mission in (1, 2):
        inspected = inspect_one(mission)
        receipt = json.loads((workdir(mission) / "compile_receipt.json").read_text(encoding="utf-8"))
        assert receipt["sha256"] == inspected["sha256"]
        assert receipt["plugin_sha256"] == digest(PLUGIN.read_bytes())
        outputs.append(receipt)
    protocol_path = MAPS / "official_probe_protocol_verification.json"
    protocol_evidence = json.loads(protocol_path.read_text(encoding="utf-8")) if protocol_path.exists() else None
    protocol_current = protocol_evidence and protocol_evidence.get("plugin_sha256") == digest(PLUGIN.read_bytes())
    return {
        "schema_version": 2, "status": "official_cli_built_and_offline_inspected_AB_native_retest_pending",
        "euddraft_version": "0.11.0.0", "eudplib_version": "0.81.0", "maps": outputs,
        "mailbox_protocol": {"magic_ascii": MAGIC.decode(), "version": 1, "word_count": 64,
                             "map_owned_words": [0, 31], "manager_owned_words": [32, 42],
                             "states": {"load": 1, "running": 2, "commit": 3, "saved": 4, "error": 5},
                             "nonce_bits": 128, "request_publication": "odd,data,even",
                             "response_checks": "even/nonzero,stable double read,request echo,status,nonce on commit"},
        "original_migration_backup": MIGRATION_BACKUP,
        "offline_protocol_verification": str(protocol_path) if protocol_current else None,
        "official_baseline_user_report": "User reported Official EUD Baseline controls working; A/B changes require separate retest",
        "game_started": False, "installed_in_game": False, "live_bridge_verified": False,
        "limitations": ["New official-plugin A/B native controls and full LOAD-COMMIT-ACK cycle are not yet tested.",
                        "Offline plugin tests model EUD calls; they do not execute the StarCraft EUD emulator.",
                        "Only sample growth records are persisted; no battle save or production campaign balance/content."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mission", type=int, choices=(1, 2))
    parser.add_argument("--inspect-only", action="store_true")
    args = parser.parse_args()
    if args.inspect_only:
        print(json.dumps(inspect_maps(), indent=2))
        return
    missions = (args.mission,) if args.mission else (1, 2)
    backup = backup_previous(missions)
    for mission in missions:
        build_one(mission)
    if args.mission:
        print("Backup: " + backup)
        return
    evidence = inspect_maps()
    evidence["prebuild_backup"] = backup
    (MAPS / "build_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": str(MAPS / "build_evidence.json"), "backup": backup,
                      "maps": [{"path": x["path"], "sha256": x["sha256"]} for x in evidence["maps"]]}, indent=2))


if __name__ == "__main__":
    main()
