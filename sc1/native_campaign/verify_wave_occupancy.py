"""Audit first/repeat wave creation with every built map's placed-unit occupancy.

Uses synthetic native callbacks and normalized working economies on scripted
acquisition maps. Does not claim engine CreateUnit or live pathfinder coverage.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sc1.build_environment import msvc_environment
from sc1.native_campaign.build_all_campaigns import CHK, units, unit_info


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def audit(receipt):
    out = ROOT / 'sc1/native_campaign/build/wave_occupancy'
    out.mkdir(parents=True, exist_ok=True)
    maps = json.loads(Path(receipt).read_text(encoding='utf8'))['maps']
    flat, fixtures, evidence = [], [], []
    for row in maps:
        path = Path(row['output'])
        if sha(path) != row['sha256']: raise ValueError('Changed map: ' + str(path))
        chk = CHK(path.read_bytes()); start = len(flat)
        for raw in units(chk):
            x, y, uid, owner = unit_info(raw)
            if uid == 214: continue
            valid, state = struct.unpack_from('<H', raw, 12)[0], struct.unpack_from('<H', raw, 26)[0]
            flat.append((uid, owner, x, y, valid & state))
        owners = list(chk.getsection('OWNR')[:8]); forces = list(chk.getsection('FORC')[:8]); flags = list(chk.getsection('FORC')[16:20])
        fixtures.append(((row['mission_id'], start, len(flat)-start), owners, forces, flags))
        evidence.append(dict(mission=row['mission_id'], sha256=row['sha256'], placed_units=len(flat)-start))
    if len(fixtures) != 63: raise ValueError('Expected all 63 maps')
    lines = ['#pragma once', 'namespace original_spawn_fixture {',
        'struct Placed {unsigned id,owner,x,y,state;};',
        'struct Scenario {unsigned mission,offset,count;unsigned char owners[8],forces[8],force_flags[4];};',
        'inline constexpr Placed units[]={']
    lines += ['{'+','.join(map(str, u))+'},' for u in flat]
    lines += ['};', 'inline constexpr Scenario scenarios[]={']
    for first, owners, forces, flags in fixtures:
        lines.append('{'+','.join(map(str, first))+','+','.join('{'+','.join(map(str, v))+'}' for v in (owners,forces,flags))+'},')
    lines += ['};', '}']
    (out/'fixtures.generated.h').write_text('\n'.join(lines)+'\n', encoding='utf8')
    shutil.copy2(ROOT/'sc1/tests/wave_occupancy/audit_host.h', out/'audit_host.h')
    plugin = ROOT/'sc1/native_campaign/plugin'
    source = (plugin/'native_plugin.cpp').read_text(encoding='utf8')
    entry = '#define main baseline_host_main\n#include "include/native_host_tests.h"\n#undef main\n#include "'+(out/'audit_host.h').as_posix()+'"\nint main(){int baseline=baseline_host_main();if(baseline)return baseline;try{host_test::installed_spawn_audit::audit_all_installed_scenarios();return 0;}catch(const std::exception& error){std::fprintf(stderr,"FAIL occupancy audit: %s\\n",error.what());return 1;}}'
    if source.count('#include "include/native_host_tests.h"') != 1: raise ValueError('Host entry changed')
    (out/'probe.cpp').write_text(source.replace('#include "include/native_host_tests.h"',entry), encoding='utf8')
    compiler, env = msvc_environment(ROOT)
    command = [str(compiler),'/nologo','/std:c++17','/EHsc','/MT','/utf-8','/W4','/WX','/DSC1_NATIVE_HOST_TEST',str(out/'probe.cpp'),
        *[str(plugin/name) for name in ('mailbox_protocol.cpp','wave_runtime.cpp','dialog_ui.cpp')],
        '/I'+str(plugin),'/I'+str(plugin/'include'),'/Fo:'+str(out)+'/', '/Fe:'+str(out/'audit.exe'),'/link','/MACHINE:X64','user32.lib']
    compile_result = subprocess.run(command, cwd=plugin, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out/'compile.log').write_bytes(compile_result.stdout)
    if compile_result.returncode: raise RuntimeError(compile_result.stdout.decode('utf8', errors='replace'))
    run = subprocess.run([str(out/'audit.exe')], cwd=plugin, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out/'tests.log').write_bytes(run.stdout)
    output = run.stdout.decode('utf8', errors='replace')
    if run.returncode: raise RuntimeError(output)
    record = dict(passed=True, maps=63, placed_units=len(flat), scenarios=evidence,
        map_receipt_sha256=sha(receipt), fixture_sha256=sha(out/'fixtures.generated.h'),
        production_source_sha256=sha(plugin/'native_plugin.cpp'),
        summaries=[line for line in output.splitlines() if line.startswith('PASS')],
        actual_engine_verified=False, game_process_accessed=False)
    (out/'verification.json').write_text(json.dumps(record,indent=2)+'\n', encoding='utf8')
    print(json.dumps({k:record[k] for k in ('passed','maps','placed_units','summaries')}))
    return record


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--map-receipt', type=Path, default=ROOT/'sc1/native_campaign/all_campaign_maps_evidence.json')
    audit(parser.parse_args().map_receipt)
