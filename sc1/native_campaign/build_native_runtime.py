"""Build the campaign native runtime and test its production translation units.

No game process, installation or player database is opened. Receipts pin every
compiled source, all three catalog generations and the matching manager. Publication is a
separate step after the map/manager integration suite succeeds.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent.parent
PLUGIN = ROOT / "plugin"
OUTPUT = ROOT / "build/all_campaign_runtime"
BOOTSTRAP = WORKSPACE / "analysis/all_campaign_20261015/previous_native_build_evidence.json"
RECEIPT = PLUGIN / "all_campaign_native_build_evidence.json"
TRANSLATION_UNITS = ("native_plugin.cpp", "mailbox_protocol.cpp", "wave_runtime.cpp", "dialog_ui.cpp")
CATALOG_NAMES=("runtime_talents.json","runtime_talents_all.json","runtime_talents_v5.json")


def validate_catalog_bundle(original,legacy,rework,*,require_implemented=True):
    """A v2 release extends exact historical entries; no old bit is redefined."""
    from sc1.campaign.runtime_catalog import validate_catalog
    from sc1.campaign.talent_balance import decorate
    import copy
    validate_catalog(original,1);validate_catalog(legacy,1);validate_catalog(rework,2)
    count=len(rework['talents'])
    if (len(legacy['talents']),len(legacy['curses']),len(rework['curses']))!=(238,15,50) or not 400<=count<=1024:
        raise ValueError('Release requires legacy238/15 and an append-only revision-five catalog within 512 bits')
    if count>400:
        from sc1.campaign.legendary_expansion import entries,identity
        from sc1.campaign.unit_growth import specifications as unit_specs,identity as unit_identity
        specifications=entries(rework)
        if count!=437+123 or any(x['id']!=identity(s['ordinal']) or x.get('effect_ordinal')!=s['ordinal'] for x,s in zip(rework['talents'][400:437],specifications)):
            raise ValueError('Appended unit legends differ from their permanent wire contract')
        if any(x['id']!=unit_identity(s['ordinal']) or x['wire_storage']!=s['storage'] for x,s in zip(rework['talents'][437:],unit_specs())):
            raise ValueError('Per-unit growth storage differs from its permanent contract')
    for kind in ('talents','curses'):
        expected=decorate(copy.deepcopy(legacy)) if rework.get('balance_revision') in (6,7,9) else legacy
        old={x['id']:x for x in expected[kind]}
        actual={x['id']:x for x in rework[kind]}
        if any(actual.get(identity)!=item for identity,item in old.items()):
            raise ValueError('Revision-five catalog changed a historical entry')
    if rework.get('policy_revision')!=5 or rework.get('rework_revision')!=5:
        raise ValueError('Revision-five policy/catalog contract is required')
    talents=[x for x in rework['talents'] if x.get('rework_revision')==5]
    curses=[x for x in rework['curses'] if x.get('rework_revision')==5]
    if ([x['bit_index'] for x in talents]!=list(range(238,count))
            or [x['byte_index'] for x in curses]!=list(range(15,50))
            or len([x for x in talents if x.get('repeatable') and not x.get('wire_storage')])!=21):
        raise ValueError('Revision-five wire indices or manual rank layout differ')
    if require_implemented and any(not x['implemented'] for x in talents+curses):
        raise ValueError('Pending native effects cannot be published as a complete revision-five release')
    return dict(growth_protocol='PHC1 v2',growth_wire_version=2,legacy_wire_versions=[1],
                mailbox_words=128,snapshot_words=65,talent_bit_capacity=512,curse_byte_capacity=64,
                manual_rank_words=32,manual_rank_slots_used=21,policy_revision=5,
                legacy_talents=238,legacy_curses=15,new_talents=count-238,new_curses=35,
                implemented_talents=sum(x['implemented'] for x in rework['talents']),
                implemented_curses=sum(x['implemented'] for x in rework['curses']))


def catalog_inputs(*,require_implemented=True):
    from sc1.campaign.talent_balance import power_quarters
    paths={name:ROOT.parent/'campaign'/name for name in CATALOG_NAMES}
    catalogs={name:read_json(path) for name,path in paths.items()}
    contract=validate_catalog_bundle(*(catalogs[name] for name in CATALOG_NAMES),require_implemented=require_implemented)
    rework=catalogs['runtime_talents_v5.json']
    power=(PLUGIN/'include/talent_power.generated.h').read_text(encoding='utf8')
    actual_power=[int(x) for x in re.search(r'kPowerQuarters\[\d+\]=\{([^}]+)\}',power)[1].split(',')]
    if actual_power!=[power_quarters(x) for x in rework['talents']]:
        raise ValueError('Native talent strength differs from the release catalog')
    frozen=(PLUGIN/'include/frozen_catalog.generated.h').read_text(encoding='utf8')
    ranks=(PLUGIN/'include/rework_catalog.generated.h').read_text(encoding='utf8')
    expected_masks=[0]*16
    for item in rework['talents']:
        storage=item.get('wire_storage')
        if storage is None:expected_masks[item['bit_index']//32]|=1<<(item['bit_index']%32)
        elif storage['word']<=16:expected_masks[storage['word']-1]|=((1<<storage['width'])-1)<<storage['shift']
    def numbers(text,pattern):
        found=re.search(pattern,text)
        if not found:raise ValueError('Generated native catalog contract is missing')
        return [int(x.strip().rstrip('u')) for x in found[1].split(',')]
    if numbers(frozen,r'kTalentMasks\[16\] = \{([^}]+)\}')!=expected_masks:
        raise ValueError('Generated native talent masks differ from the release catalog')
    if numbers(frozen,r'kCurseMaxStacks\[kCurseCount\] = \{([^}]+)\}')!=[x['max_stacks'] for x in rework['curses']]:
        raise ValueError('Generated native curse caps differ from the release catalog')
    if numbers(ranks,r'kRankSlots\[(?:\d+|kTalentCount)\]=\{([^}]+)\}')!=[x.get('rank_slot',-1) for x in rework['talents'][238:]]:
        raise ValueError('Generated native manual rank mapping differs from the release catalog')
    if rework.get('unit_growth_revision'):
        actual_fields=[tuple(map(int,row)) for row in re.findall(r'\{(\d+),(\d+),(\d+),(\d+)\}',ranks)]
        expected_fields=[(x['effect_ordinal'],x['wire_storage']['word'],x['wire_storage']['shift'],x['wire_storage']['width']) for x in rework['talents'][437:]]
        if actual_fields!=expected_fields:raise ValueError('Generated per-unit packed fields differ from the release catalog')
    pins={name:{'path':str(path),'sha256':digest(path)} for name,path in paths.items()}
    return contract,pins


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_entries():
    files = [PLUGIN / name for name in (*TRANSLATION_UNITS,'dialog_ui_tests.cpp')]
    files += list(PLUGIN.glob("*.h")) + list((PLUGIN / "include").rglob("*.h"))
    files += [Path(__file__), WORKSPACE / 'sc1/build_environment.py', PLUGIN / "rework_protocol_driver.py", PLUGIN / "checkpoint_protocol_driver.py",
              ROOT / "dialog_assets/plain_panel_templates.generated.h",
              ROOT / "dialog_assets/wave_timer_statfluf.ui.json",
              ROOT / "build_effect_iscript.py",ROOT / "iscript_effects/iscript.bin",
              ROOT / "iscript_effects/iscript_effects_evidence.json",
              ROOT / "build_objective_guards.py",ROOT / "objective_guards_evidence.json"]
    return [{"path": str(path.resolve()), "sha256": digest(path)} for path in sorted(set(files))]


def manager_source_entries(root=None):
    """Pin the same explicit application closure that the portable builder copies."""
    from sc1.build_portable import runtime_sources
    root=Path(root or WORKSPACE).resolve()
    return [{"path":path.relative_to(root).as_posix(),"sha256":digest(path)}
            for path in sorted(runtime_sources(root))]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(argv, environment, log_name):
    result = subprocess.run([str(arg) for arg in argv], cwd=PLUGIN, env=environment,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=240)
    # MSVC uses the local Windows console code page for its diagnostic text.
    output = result.stdout.decode("utf-8", errors="replace")
    (OUTPUT / log_name).write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(f"{log_name} failed ({result.returncode}):\n{output}")
    return {"argv": [str(arg) for arg in argv], "cwd": str(PLUGIN),
            "returncode": result.returncode, "output": output,
            "log": str(OUTPUT / log_name)}


def build(*, receipt=RECEIPT, protocol=True):
    sys.path.insert(0,str(WORKSPACE))
    growth_contract,catalog_pins=catalog_inputs()
    from sc1.build_environment import msvc_environment
    compiler, environment = msvc_environment(WORKSPACE)
    for folder in (OUTPUT, OUTPUT / "host_objects", OUTPUT / "dll_objects", OUTPUT / "protocol_objects",OUTPUT/'ui_objects'):
        folder.mkdir(parents=True, exist_ok=True)
    before = source_entries()
    manager_before=manager_source_entries()
    catalogs = {name:row['sha256'] for name,row in catalog_pins.items()}
    flags = ["/nologo", "/std:c++17", "/EHsc", "/MT", "/utf-8", "/W4", "/WX", "/O2"]
    host = OUTPUT / "native_host_tests.exe"
    dll = OUTPUT / "native_plugin.dll"
    commands = []
    commands.append(run([compiler, *flags, "/DSC1_NATIVE_HOST_TEST", *TRANSLATION_UNITS,
                         "/Fo:" + str(OUTPUT / "host_objects") + "/", "/Fe:" + str(host),
                         "/link", "/MACHINE:X64", "user32.lib"], environment, "host_compile.log"))
    host_result = run([host], environment, "host_tests.log")
    commands.append(host_result)
    match = re.search(r"PASS native host integration: (\d+) groups, (\d+) checks", host_result["output"])
    if not match:
        raise ValueError("Host run did not produce its success summary")
    ui_exe=OUTPUT/'dialog_ui_tests.exe'
    commands.append(run([compiler,*flags,'dialog_ui_tests.cpp','dialog_ui.cpp',
                         '/Fo:'+str(OUTPUT/'ui_objects')+'/', '/Fe:'+str(ui_exe),
                         '/link','/MACHINE:X64','user32.lib'],environment,'ui_compile.log'))
    ui_result=run([ui_exe],environment,'ui_tests.log');commands.append(ui_result)
    ui_summary=json.loads(ui_result['output'])
    if ui_summary.get('passed') is not True or ui_summary.get('groups',0)<19:
        raise ValueError('Full dialog UI suite including standalone revision-five confirmation must pass')
    commands.append(run([compiler, *flags, "/LD", *TRANSLATION_UNITS,
                         "/Fo:" + str(OUTPUT / "dll_objects") + "/", "/Fe:" + str(dll),
                         "/link", "/MACHINE:X64", "/MAP:" + str(OUTPUT / "native_plugin.map"),
                         "user32.lib"], environment, "dll_compile.log"))
    protocol_results = []
    if protocol:
        protocol_exe = OUTPUT / "mailbox_tests.exe"
        commands.append(run([compiler, *flags, "/DSC1_MAILBOX_PROTOCOL_TEST", "mailbox_protocol.cpp",
                             "/Fo:" + str(OUTPUT / "protocol_objects") + "/", "/Fe:" + str(protocol_exe),
                             "/link", "/MACHINE:X64"], environment, "protocol_compile.log"))
        for name, arguments in (("legacy", []), ("phases", ["--phase-tests"])):
            result = run([protocol_exe, *arguments], environment, "protocol_" + name + ".log")
            commands.append(result)
            protocol_results.append({"name": name, "result": json.loads(result["output"])})
        result=run([sys.executable,'-B','-X','utf8',PLUGIN/'rework_protocol_driver.py',protocol_exe],environment,'protocol_rework_interop.log')
        commands.append(result)
        protocol_results.append({'name':'rework_v2_python_native','result':json.loads(result['output'])})
        result=run([sys.executable,'-B','-X','utf8',PLUGIN/'checkpoint_protocol_driver.py',protocol_exe],environment,'protocol_checkpoint_interop.log')
        commands.append(result)
        protocol_results.append({'name':'checkpoint_v2_python_native','result':json.loads(result['output'])})
    after = source_entries()
    manager_after=manager_source_entries()
    if before != after or manager_before != manager_after or catalogs != {name: digest(ROOT.parent / "campaign" / name) for name in catalogs}:
        raise ValueError("Sources changed during compilation: rebuild after integration settles")
    sys.path.insert(0, str(WORKSPACE))
    from sc1.native_campaign.package_native_plugin import verify_dll
    pe = verify_dll(dll.read_bytes())
    dat_receipt_path = ROOT / "managed_dat/managed_dat_evidence.json"
    dat = read_json(dat_receipt_path)
    record = {
        "schema_version": 1, "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "all_campaign_runtime_offline_verified_live_pending",
        "dll_path": str(dll), "dll_sha256": digest(dll), "dll_bytes": dll.stat().st_size,
        "runtime_catalog_sha256": catalogs["runtime_talents.json"],
        "expanded_catalog": str(ROOT.parent / "campaign/runtime_talents_all.json"),
        "expanded_catalog_sha256": catalogs["runtime_talents_all.json"],
        'catalogs':catalog_pins,'rework_catalog':catalog_pins['runtime_talents_v5.json']['path'],
        'rework_catalog_sha256':catalogs['runtime_talents_v5.json'],'growth_contract':growth_contract,
        "sources": after, "sources_unchanged_across_compile": True,
        'manager_sources':manager_after,'manager_sources_unchanged_across_compile':True,
        "compiler": {'path':str(compiler),'sha256':digest(compiler),
                     'environment':{key:environment[key] for key in ('INCLUDE','LIB','LIBPATH') if key in environment}},
        "commands": commands, "pe": pe,
        "offline_host_tests": {"passed": True, "groups": int(match[1]), "checks": int(match[2]),
                               "test_executable": str(host), "test_executable_sha256": digest(host),
                               "production_translation_units_used": True},
        "mailbox_offline_tests": protocol_results,
        'native_dialog_ui_tests':{**ui_summary,'test_executable':str(ui_exe),'test_executable_sha256':digest(ui_exe),
                                  'production_translation_units_used':True},
        "growth_protocol": "PHC1 v2",'growth_wire_version':2, "automatic_popup": True,
        "custom_menu_json": True, "native_upper_text_control": True, "choice_number_buttons": True,
        "phase_capability": 2, "phase_count": 4, "talent_phases": [1,3,4],
        "curses_per_mission": [0,1,2,3,4], "default_curses_per_mission": 3,
        "api_lifecycle": {"factories_resolved_during_plugin_init": True,
                          "runtime_plugin_api_object_retained": False},
        "managed_dat_receipt": str(dat_receipt_path),
        "managed_dat_receipt_sha256": digest(dat_receipt_path),
        "managed_dat_assets": dat["managed_dat_assets"],
        "game_process_accessed": False, "user_database_accessed": False,
        "live_verified": False,
        "limit": "Synthetic native host and temporary protocol fixtures; live map completion, visuals and balance unverified.",
    }
    write_json(Path(receipt), record)
    print(json.dumps({"passed": True, "groups": int(match[1]), "checks": int(match[2]),
                      "dll_sha256": record["dll_sha256"], "receipt": str(receipt)}))
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=RECEIPT)
    parser.add_argument("--skip-protocol", action="store_true")
    args = parser.parse_args()
    build(receipt=args.receipt, protocol=not args.skip_protocol)
