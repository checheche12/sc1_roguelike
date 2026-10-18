"""Seal all original and Brood War scenarios with their matched native runtime.

This writes a separate workspace overlay. Activation only changes the launcher's
workspace pointer; it never starts the game or changes installed CASC or saves.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path, PurePosixPath
import sys
import uuid

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
sys.path.insert(0, str(WORKSPACE))
from sc1.native_campaign import package_native_plugin as legacy
from sc1.native_campaign.build_plain_chk import CHK, strings
from sc1.native_campaign import build_all_campaigns as map_builder
from sc1.native_campaign import mineral_layout
from sc1.native_campaign import resource_layout
from sc1.native_campaign import ladder_resource_layout
from sc1.native_campaign import mining_layout_audit
from sc1.native_campaign import resource_depot_placement
from sc1.native_campaign import main_base_gas, mineral_amount_bonus, addon_placement
from sc1.campaign.missions import load_missions

DEFAULT_MAP_RECEIPT = ROOT / "all_campaign_maps_evidence.json"
DEFAULT_DLL_RECEIPT = ROOT / "plugin/all_campaign_native_build_evidence.json"


def manager_inputs(dll):
    from sc1.native_campaign.build_native_runtime import manager_source_entries
    current=manager_source_entries(WORKSPACE)
    if dll.get('growth_protocol')=='PHC1 v2':
        if (dll.get('manager_sources_unchanged_across_compile') is not True
                or dll.get('manager_sources')!=current):
            raise ValueError('Manager source/catalog closure changed after native interoperability verification')
    return current


def runtime_catalog_inputs(dll):
    """Read exactly the catalog version compiled into this native receipt."""
    if dll.get('growth_protocol')=='PHC1 v2':
        from sc1.native_campaign.build_native_runtime import validate_catalog_bundle,CATALOG_NAMES
        if dll.get('growth_wire_version')!=2:
            raise ValueError('Revision-five native receipt must advertise wire version two')
        pinned=dll.get('catalogs',{})
        if set(pinned)!=set(CATALOG_NAMES):raise ValueError('All three historical/current catalogs must be pinned')
        values={};pins=[]
        for name in CATALOG_NAMES:
            path,raw=legacy.checked_file(pinned[name]['path'],pinned[name]['sha256'])
            if path!=(ROOT.parent/'campaign'/name).resolve():raise ValueError('Unexpected runtime catalog path')
            values[name]=json.loads(raw);pins.append((path,raw))
        contract=validate_catalog_bundle(*(values[name] for name in CATALOG_NAMES))
        if dll.get('growth_contract')!=contract:raise ValueError('Native growth layout/policy receipt differs from its catalog')
        if not any(row.get('name')=='rework_v2_python_native' and row.get('result',{}).get('passed') is True
                   for row in dll.get('mailbox_offline_tests',[])):
            raise ValueError('Revision-five Python/native wire interoperability must pass before publication')
        ui=dll.get('native_dialog_ui_tests',{})
        if ui.get('passed') is not True or ui.get('groups',0)<19 or ui.get('production_translation_units_used') is not True:
            raise ValueError('Native dialog UI including standalone revision-five confirmation must pass before publication')
        path,raw=pins[-1]
        if (dll.get('rework_catalog')!=str(path) or dll.get('rework_catalog_sha256')!=legacy.sha(raw)):
            raise ValueError('Native revision-five catalog hash differs')
        return path,raw,pins,contract
    if dll.get('growth_protocol')!='PHC1 v1':raise ValueError('Unsupported native growth protocol')
    path,raw=legacy.checked_file(dll['expanded_catalog'],dll['expanded_catalog_sha256'])
    return path,raw,[(ROOT.parent/'campaign/runtime_talents.json',(ROOT.parent/'campaign/runtime_talents.json').read_bytes()),(path,raw)],{'growth_protocol':'PHC1 v1','growth_wire_version':1}


def safe_asset(name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or "\\" in name or ":" in name:
        raise ValueError("Invalid campaign asset path")
    if len(path.parts) != 5 or path.parts[0] != "campaign" or path.parts[-2:] != ("staredit", "scenario.chk"):
        raise ValueError("Only explicit campaign scenario paths may be overridden")
    return path.as_posix()


def _verify_base_resource_layout(source_chk, output_chk, mission, row):
    """Replay the constrained edit; a receipt cannot authorize arbitrary units."""
    if row.get("resource_layout") != row.get("mineral_layout"):
        raise ValueError("Resource layout report and its compatibility copy differ")
    layout = row.get("resource_layout") or {}
    if (layout.get("functional_cluster_count") != layout.get("cluster_count")
            or layout.get("functional_geyser_count") != layout.get("geyser_count")):
        raise ValueError("A resource field or useful gas expansion is still unresolved")
    original_units = source_chk.getsection("UNIT")
    output_units = output_chk.getsection("UNIT")
    try:
        map_builder.assert_original_units_preserved(original_units, output_units, mineral_bonus=500)
    except AssertionError as error:
        raise ValueError("Original placed units changed beyond resource coordinates") from error
    baseline = CHK(source_chk.save())
    for tag in ("OWNR", "SIDE", "FORC"):
        baseline.setsection(tag, output_chk.getsection(tag))
    additions = len((row.get("main_base_gas") or {}).get("added", [])) * 36
    resource_output_units = output_units[:-additions] if additions else output_units
    baseline.setsection("UNIT", original_units + resource_output_units[len(original_units):])
    if mission["mission_id"] == 101:
        plain_raw, _, _ = map_builder.make_plain_chk(source_chk.save())
        plain = CHK(plain_raw)
        for tag in ("UNIT", "OWNR", "SIDE", "FORC"):
            baseline.setsection(tag, plain.getsection(tag))
    expected_report = resource_layout.apply_layout(
        baseline, mission, reserved_points=map_builder.mineral_reserved_points(row["difficulty"]))
    if expected_report != row.get("mineral_layout"):
        raise ValueError("Resource layout differs from the exact constrained transformation")
    expected_gas = main_base_gas.apply(baseline, mission, expected_report,
        reserved_points=map_builder.mineral_reserved_points(row["difficulty"]))
    expected_amounts=mineral_amount_bonus.apply(baseline)
    if expected_amounts != row.get("mineral_amount_bonus"):
        raise ValueError("Mineral amounts differ from the exact +500 transformation")
    if baseline.getsection("UNIT") != output_units or expected_gas != row.get("main_base_gas"):
        raise ValueError("Main-base gas differs from the exact constrained transformation")


def verify_mineral_layout(source_chk, output_chk, mission, row):
    from . import mission_balance,corner_resource_layout,scripted_openings,courtyard_resource_layout
    report = row.get('mission_balance')
    if not report:raise ValueError('Mission-specific balance proof missing')
    baseline = CHK(output_chk.save())
    try:
        courtyard_resource_layout.undo(baseline,row['courtyard_resource_layout'])
        mission_balance.undo(baseline, report)
        corner_resource_layout.undo(baseline,row['corner_resource_layout'])
        _verify_base_resource_layout(source_chk, baseline, mission, row)
        corners=corner_resource_layout.apply(baseline,mission,row['resource_layout'],
            reserved_points=map_builder.mineral_reserved_points(row['difficulty']))
        expected = mission_balance.apply(baseline, mission, row['difficulty'])
        courtyard=courtyard_resource_layout.apply(baseline,mission,row['resource_layout'],row['main_base_gas'],corners,
            reserved_points=map_builder.mineral_reserved_points(row['difficulty']))
        if courtyard!=row['courtyard_resource_layout']:raise ValueError('Joint resource court differs from deterministic replay')
        if corners!=row['corner_resource_layout'] or row.get('scripted_opening')!=scripted_openings.evidence(mission):
            raise ValueError('Corner resources/scripted opening differ from deterministic replay')
        if scripted_openings.excluded_factions(mission)&set(row['difficulty']['hostile_owners']):
            raise ValueError('Scripted event faction was reinforced')
        if expected != report or baseline.save() != output_chk.save():
            raise ValueError('Mission balance differs from deterministic replay')
    except AssertionError as error:
        raise ValueError('Invalid mission-specific unit transformation') from error


def verify_checkpoint_layout(source_chk, output_chk, mission, row):
    """A four-stage receipt cannot authorize different mission trigger code."""
    from . import mission_balance, campaign_objectives,corner_resource_layout,courtyard_resource_layout
    baseline=CHK(source_chk.save());units=CHK(output_chk.save())
    try:
        courtyard_resource_layout.undo(units,row['courtyard_resource_layout'])
        mission_balance.undo(units,row['mission_balance'])
        corner_resource_layout.undo(units,row['corner_resource_layout'])
    except AssertionError as error:raise ValueError('Invalid checkpoint base units') from error
    baseline.setsection('UNIT',units.getsection('UNIT'))
    for tag in ('OWNR','SIDE','FORC'):baseline.setsection(tag,output_chk.getsection(tag))
    correction=campaign_objectives.apply(baseline,mission)
    progression=map_builder.patch_progression(baseline,mission);progression['objective_correction']=correction
    progression=json.loads(json.dumps(progression))
    baseline.setsection('STR ',map_builder.append_marker(baseline.getsection('STR '),mission['fingerprint'].encode('ascii')))
    if (baseline.getsection('TRIG')!=output_chk.getsection('TRIG')
            or baseline.getsection('STR ')!=output_chk.getsection('STR ')
            or progression!=row['progression']):
        differences=[tag for tag in ('TRIG','STR ') if baseline.getsection(tag)!=output_chk.getsection(tag)]
        if progression!=row['progression']:differences.append('progression receipt')
        raise ValueError(f"Checkpoint layout differs on mission {mission['mission_id']}: {differences}")


def validate_maps(receipt_path):
    receipt_path = legacy.owned_file(receipt_path)
    receipt = legacy.read_json(receipt_path)
    if receipt.get("map_builder_sha256") != legacy.sha(Path(map_builder.__file__).read_bytes()):
        raise ValueError("Map builder changed after its evidence")
    layout_path, _ = legacy.checked_file(receipt["mineral_layout_source"], receipt["mineral_layout_source_sha256"])
    if layout_path != Path(mineral_layout.__file__).resolve():
        raise ValueError("Unexpected mineral layout implementation")
    resource_path, _ = legacy.checked_file(receipt["resource_layout_source"], receipt["resource_layout_source_sha256"])
    if resource_path != Path(resource_layout.__file__).resolve():
        raise ValueError("Unexpected resource layout implementation")
    ladder_path, _ = legacy.checked_file(receipt['ladder_resource_layout_source'], receipt['ladder_resource_layout_source_sha256'])
    if ladder_path != Path(ladder_resource_layout.__file__).resolve():
        raise ValueError('Unexpected joint mineral/gas layout implementation')
    addon_path, _ = legacy.checked_file(receipt['addon_placement_source'], receipt['addon_placement_source_sha256'])
    if addon_path != Path(addon_placement.__file__).resolve():
        raise ValueError('Unexpected addon landing guard implementation')
    gas_path, _ = legacy.checked_file(receipt['main_base_gas_source'], receipt['main_base_gas_source_sha256'])
    if gas_path != Path(main_base_gas.__file__).resolve():
        raise ValueError('Unexpected main-base gas implementation')
    amount_path, _ = legacy.checked_file(receipt['mineral_amount_bonus_source'], receipt['mineral_amount_bonus_source_sha256'])
    if amount_path != Path(mineral_amount_bonus.__file__).resolve():
        raise ValueError('Unexpected mineral amount implementation')
    audit_path, _ = legacy.checked_file(receipt["mining_layout_audit_source"], receipt["mining_layout_audit_source_sha256"])
    if audit_path != Path(mining_layout_audit.__file__).resolve():
        raise ValueError("Unexpected mining layout auditor")
    guard_path, _ = legacy.checked_file(receipt["resource_depot_guard_source"], receipt["resource_depot_guard_source_sha256"])
    if guard_path != Path(resource_depot_placement.__file__).resolve():
        raise ValueError("Unexpected resource depot placement guard")
    from . import mission_balance
    balance_path, _ = legacy.checked_file(receipt['mission_balance_source'], receipt['mission_balance_source_sha256'])
    if balance_path != Path(mission_balance.__file__).resolve():raise ValueError('Unexpected mission balance implementation')
    from . import corner_resource_layout,scripted_openings,courtyard_resource_layout
    for module in (corner_resource_layout,scripted_openings,courtyard_resource_layout):
        name=module.__name__.rsplit('.',1)[-1]
        pinned,_=legacy.checked_file(receipt[name+'_source'],receipt[name+'_source_sha256'])
        if pinned!=Path(module.__file__).resolve():raise ValueError('Unexpected '+name+' implementation')
    rows = receipt["maps"]
    expected = {row["mission_id"]: row for row in load_missions()}
    if len(rows) != len(expected) or {row["mission_id"] for row in rows} != set(expected):
        raise ValueError("Map receipt does not cover the entire campaign roster exactly once")
    # Reject changed immutable inputs before replaying every resource layout.
    header_path = receipt.get("generated_header") or receipt.get("header")
    header_hash = receipt.get("generated_header_sha256") or receipt.get("header_sha256")
    if not header_path or not header_hash:
        raise ValueError("Map receipt must pin its generated native mission header")
    header, _ = legacy.checked_file(header_path, header_hash)
    legacy.checked_file(receipt["wave_generated_header"], receipt["wave_generated_header_sha256"])
    metadata, _ = legacy.checked_file(receipt["mission_metadata"], receipt["mission_metadata_sha256"])
    if metadata != (ROOT.parent / "campaign/missions.json").resolve():
        raise ValueError("Map roster metadata does not match the manager")
    outputs = {}
    for row in rows:
        mission = expected[row["mission_id"]]
        asset = safe_asset(row["asset_path"])
        if asset != mission["asset_path"] or asset.casefold() in {name.casefold() for name in outputs}:
            raise ValueError("Map receipt contains an unexpected or duplicated campaign path")
        if (Path(row["source"]).resolve() != Path(mission["source"]).resolve()
                or row["source_sha256"] != mission["source_sha256"]):
            raise ValueError("Map original differs from the independent mission source pin")
        _, original = legacy.checked_file(row["source"], row["source_sha256"])
        _, output = legacy.checked_file(row["output"], row["sha256"])
        source_chk, output_chk = CHK(original), CHK(output)
        if source_chk.getsection("VER ") != output_chk.getsection("VER "):
            raise ValueError("Scenario format version changed")
        if source_chk.order != output_chk.order:
            raise ValueError("Original section order/tags changed")
        for tag in ("DIM ", "ERA ", "MTXM", "MASK", "MRGN", "MBRF", "WAV "):
            if tag.encode() in source_chk.sections and source_chk.getsection(tag) != output_chk.getsection(tag):
                raise ValueError("Original terrain/locations/briefing/audio changed: " + asset + ":" + tag)
        before_strings, after_strings = strings(source_chk.getsection("STR ")), strings(output_chk.getsection("STR "))
        if after_strings[:len(before_strings)] != before_strings or mission["fingerprint"].encode() not in after_strings:
            raise ValueError("Original string IDs or runtime authentication marker changed")
        if receipt.get('phase_capability')==2:verify_checkpoint_layout(source_chk,output_chk,mission,row)
        verify_mineral_layout(source_chk, output_chk, mission, row)
        outputs[asset] = output
        print(json.dumps({'resource_map_verified':row['mission_id']}),flush=True)
    return receipt_path, receipt, outputs, header


def inputs(map_receipt, dll_receipt):
    map_path, maps, outputs, header = validate_maps(map_receipt)
    dll_receipt = legacy.owned_file(dll_receipt)
    dll = legacy.read_json(dll_receipt)
    if maps.get('phase_capability')==2:
        if dll.get('phase_capability')!=2 or dll.get('phase_count')!=4:
            raise ValueError('Four-checkpoint maps require the matching native capability')
        interop=next((x.get('result',{}) for x in dll.get('mailbox_offline_tests',[]) if x.get('name')=='checkpoint_v2_python_native'),{})
        if not interop.get('passed') or {x.get('curses') for x in interop.get('modes',[])}!=set(range(5)):
            raise ValueError('All five curse difficulty modes require native/manager interop')
    # Reuse all eleven stock DAT transformations and PE/source/lifecycle checks.
    _, plugin, native = legacy.native_inputs(ROOT / "plain_chk_evidence.json", dll_receipt)
    compiled = {str(legacy.owned_file(row["path"])): row["sha256"] for row in dll["sources"]}
    if dll.get('growth_protocol')=='PHC1 v2':
        required={'rework_catalog.generated.h','rework_combat_v5.h','rework_economy_v5.h','rework_wave_native.h','rework_cargo_v5.h',
                  'rework_economy_ui_v5.h','rework_economy_ui_host_tests.h','rework_economy_ui_specs.generated.h'}
        if not required<={Path(path).name for path in compiled}:raise ValueError('Revision-five native mechanism sources are incomplete')
    if compiled.get(str(header)) != legacy.sha(header.read_bytes()):
        raise ValueError("DLL was not compiled with this map roster")
    wave_header = legacy.owned_file(maps["wave_generated_header"])
    if compiled.get(str(wave_header)) != maps["wave_generated_header_sha256"]:
        raise ValueError("DLL was not compiled with these wave origins")
    catalog_path,catalog_raw,catalog_pins,growth_contract=runtime_catalog_inputs(dll)
    catalog = json.loads(catalog_raw)
    available = set(row["mission_id"] for row in maps["maps"])
    if any(not set(row["missions"]) <= available for row in catalog["talents"] + catalog["curses"]):
        raise ValueError("Expanded catalog references an unpackaged mission")
    if dll.get("sources_unchanged_across_compile") is not True or dll.get("offline_host_tests", {}).get("passed") is not True:
        raise ValueError("Matching native host validation is required")
    manager_sources=manager_inputs(dll)
    from sc1.native_campaign import build_all_requirements as requirements
    requirement_receipt_path = ROOT / "all_requirements/all_requirements_evidence.json"
    requirement_receipt = legacy.read_json(requirement_receipt_path)
    if requirement_receipt["builder_sha256"] != legacy.sha(Path(requirements.__file__).read_bytes()):
        raise ValueError("All-campaign requirement builder changed after its evidence")
    expected_requirements = requirements.expected_assets()
    requirement_assets = requirement_receipt["assets"]
    if len(requirement_assets) != len(expected_requirements) or {r["name"] for r in requirement_assets} != set(expected_requirements):
        raise ValueError("All-campaign requirement assets are incomplete")
    normalized_requirements = []
    for row in requirement_assets:
        path = Path(row["path"])
        path = path if path.is_absolute() else WORKSPACE / path
        path, raw = legacy.checked_file(path, row["sha256"])
        if raw != expected_requirements[row["name"]]:
            raise ValueError("All-campaign production requirements differ from exact transformation")
        legacy.verify_loader_dat(raw, row["name"])
        normalized_requirements.append({**row, "path": str(path)})
    native.update(all_requirements_receipt=str(requirement_receipt_path),
                  all_requirements_receipt_sha256=legacy.sha(requirement_receipt_path.read_bytes()),
                  all_requirements_assets=normalized_requirements)
    native.update(map_receipt=str(map_path), map_receipt_sha256=legacy.sha(map_path.read_bytes()),
                  map_builder_sha256=maps["map_builder_sha256"],
                  mission_balance_source=maps["mission_balance_source"],
                  mission_balance_source_sha256=maps["mission_balance_source_sha256"],
                  mineral_layout_source=maps["mineral_layout_source"],
                  mineral_layout_source_sha256=maps["mineral_layout_source_sha256"],
                  resource_layout_source=maps["resource_layout_source"],
                  resource_layout_source_sha256=maps["resource_layout_source_sha256"],
                  ladder_resource_layout_source=maps['ladder_resource_layout_source'],
                  ladder_resource_layout_source_sha256=maps['ladder_resource_layout_source_sha256'],
                  mineral_amount_bonus_source=maps['mineral_amount_bonus_source'],
                  mineral_amount_bonus_source_sha256=maps['mineral_amount_bonus_source_sha256'],
                  addon_placement_source=maps['addon_placement_source'],
                  addon_placement_source_sha256=maps['addon_placement_source_sha256'],
                  main_base_gas_source=maps['main_base_gas_source'],
                  main_base_gas_source_sha256=maps['main_base_gas_source_sha256'],
                  mining_layout_audit_source=maps["mining_layout_audit_source"],
                  mining_layout_audit_source_sha256=maps["mining_layout_audit_source_sha256"],
                  resource_depot_guard_source=maps["resource_depot_guard_source"],
                  resource_depot_guard_source_sha256=maps["resource_depot_guard_source_sha256"],
                  expanded_catalog=str(catalog_path), expanded_catalog_sha256=legacy.sha(catalog_raw),
                  legacy_expanded_catalog=dll['expanded_catalog'],legacy_expanded_catalog_sha256=dll['expanded_catalog_sha256'],
                  catalog_pins=[{'path':str(path),'sha256':legacy.sha(raw)} for path,raw in catalog_pins],
                  growth_contract=growth_contract,
                  phase_capability=maps.get('phase_capability',1),
                  checkpoint_count=maps.get('checkpoint_count',3),
                  talent_phases=[1,3,4] if maps.get('phase_capability')==2 else [1,2,3],
                  curses_per_mission=[0,1,2,3,4] if maps.get('phase_capability')==2 else [3],
                  mission_metadata=str(ROOT.parent / "campaign/missions.json"),
                  mission_metadata_sha256=legacy.sha((ROOT.parent / "campaign/missions.json").read_bytes()),
                  manager_sources=manager_sources,
                  implemented_talents=sum(row["implemented"] for row in catalog["talents"]),
                  implemented_curses=sum(row["implemented"] for row in catalog["curses"]))
    return outputs, plugin, native, maps


def build(map_receipt=DEFAULT_MAP_RECEIPT, dll_receipt=DEFAULT_DLL_RECEIPT, *, activate=False):
    outputs, plugin, native, maps = inputs(map_receipt, dll_receipt)
    members = {}
    for asset, raw in outputs.items():
        for prefix in legacy.PREFIXES:
            members[(prefix + "/" if prefix else "") + asset] = raw
    members["samase/native_plugin.dll"] = plugin
    members["samase/plugins"] = b"samase/native_plugin.dll\n"
    assets = native["managed_dat_assets"] + native["support_dat_assets"]
    if len(assets) != 11 or {row["name"] for row in assets} != set(legacy.REQUIRED_DAT_NAMES):
        raise ValueError("All eleven Dat+ tables are required")
    for row in assets:
        _, raw = legacy.checked_file(row["path"], row["sha256"])
        legacy.verify_loader_dat(raw, row["name"])
        members[row["name"]] = raw
    # Derived requirements remove only the expansion-mode gate. Building,
    # add-on, research and resource requirements remain exactly as validated.
    for row in native["all_requirements_assets"]:
        _, raw = legacy.checked_file(row["path"], row["sha256"])
        members[row["name"]] = raw
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    folder = ROOT / "builds" / ("all_" + stamp)
    folder.mkdir(parents=True, exist_ok=False)
    files = []
    for name, data in sorted(members.items()):
        path = folder / "overlay" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files.append({"path": path.relative_to(folder).as_posix(), "bytes": len(data), "sha256": legacy.sha(data)})
    manifest = {
        "schema_version": 3, "mode": "native_all_campaigns", "status": "prepared_live_validation_pending",
        "inputs": native, "files": files, "loader_sha256": legacy.read_json(ROOT / "loader_pin.json")["sha256"],
        "loader_options": ["--log", "--no-debug"], "scenario_count": len(outputs),
        "campaign_scope": "StarCraft original and Brood War; alternate branches and secret mission included",
        "missions": [{key: row[key] for key in ("mission_id", "asset_path", "sha256")} for row in maps["maps"]],
        "in_game_choices": True, "choice_interface": "native CTEXT with numeric buttons and explicit confirmation",
        "growth_protocol": native['growth_contract']['growth_protocol'],
        'growth_wire_version':native['growth_contract']['growth_wire_version'],
        'growth_contract':native['growth_contract'],"choices_per_mission": {"talent": 3, "curse": 3},
        'final_no_production_curse_choices':0,
        "growth_checkpoints": ["start", "original mission progress", "before original ending"],
        "native_playtest_verified": False, "campaign_progression_verified": False,
        "installed_casc_modified": False, "player_saves_modified": False,
        "game_executed_by_packager": False, "global_bare_chk_alias": False,
        "audio_policy": "Original CASC audio and original scenario string IDs are retained.",
        "dll": legacy.verify_dll(plugin),
    }
    legacy.write_json(folder / "manifest.json", manifest)
    for row in files:
        if legacy.sha((folder / row["path"]).read_bytes()) != row["sha256"]:
            raise ValueError("Written overlay differs from validated inputs")
    previous_pointer = ROOT / "current_build.json"
    if activate:
        if previous_pointer.exists():
            (folder / "previous_build.json").write_bytes(previous_pointer.read_bytes())
        legacy.write_json(previous_pointer, {"manifest": (folder / "manifest.json").relative_to(ROOT).as_posix()})
    return {"manifest": str(folder / "manifest.json"), "maps": len(outputs), "files": len(files),
            "activated": activate, "live_verified": False, "dll_sha256": legacy.sha(plugin)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map-receipt", type=Path, default=DEFAULT_MAP_RECEIPT)
    parser.add_argument("--dll-receipt", type=Path, default=DEFAULT_DLL_RECEIPT)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    print(json.dumps(build(args.map_receipt, args.dll_receipt, activate=args.activate), ensure_ascii=False, indent=2))
