"""Build/run a private real-engine combat audit and verify its JSONL evidence.

Usage: python -m sc1.diagnostics.live_combat prepare --output PATH --game EXE
       python -m sc1.diagnostics.live_combat run --build PATH
       python -m sc1.diagnostics.live_combat analyze --build PATH
       python -m sc1.diagnostics.live_combat check --output PATH --game EXE

No campaign database, installed patch, manager pointer, or campaign map is
modified. A live StarCraft process blocks launch. Only the process created by
this run may be stopped on timeout. Reports distinguish crash, timeout, missing
evidence and numerical mismatch; process survival alone is never a pass.
"""
from __future__ import annotations
import argparse
import ctypes as C
import ctypes.wintypes as W
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import statistics
import struct
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def events(path):
    rows, malformed = [], 0
    if Path(path).exists():
        for line in Path(path).read_bytes().splitlines():
            try:
                rows.append(json.loads(line))
            except (ValueError, UnicodeError):
                malformed += 1
    return rows, malformed


def inventory():
    kernel = C.WinDLL("kernel32", use_last_error=True)
    class Entry(C.Structure):
        _fields_ = [("size", W.DWORD), ("usage", W.DWORD), ("pid", W.DWORD),
                    ("heap", C.c_size_t), ("module", W.DWORD), ("threads", W.DWORD),
                    ("parent", W.DWORD), ("priority", W.LONG), ("flags", W.DWORD), ("exe", W.WCHAR * 260)]
    kernel.CreateToolhelp32Snapshot.argtypes = [W.DWORD, W.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = W.HANDLE
    kernel.Process32FirstW.argtypes = kernel.Process32NextW.argtypes = [W.HANDLE, C.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [W.HANDLE]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == C.c_void_p(-1).value:
        raise C.WinError(C.get_last_error())
    result = []
    try:
        entry = Entry(); entry.size = C.sizeof(entry)
        okay = kernel.Process32FirstW(handle, C.byref(entry))
        while okay:
            if entry.exe.casefold() == "starcraft.exe":
                result.append(dict(pid=entry.pid, parent_pid=entry.parent))
            okay = kernel.Process32NextW(handle, C.byref(entry))
    finally:
        kernel.CloseHandle(handle)
    return result


def prepare(output: Path, game: Path, *, probe_source: Path | None = None):
    from sc1.build_environment import msvc_environment
    game = game.resolve()
    if not game.is_file() or game.name.casefold() != "starcraft.exe":
        raise ValueError("Select the installed x86_64/StarCraft.exe")
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    build = output.resolve() / stamp
    build.mkdir(parents=True)
    plugin = ROOT / "sc1/native_campaign/plugin"
    source = {p.relative_to(plugin).as_posix(): sha(p) for p in plugin.rglob("*")
              if p.is_file() and p.suffix in (".cpp", ".h")}
    for name in source:
        dest = build / "snapshot/plugin" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(plugin / name, dest)
        if sha(dest) != source[name]:
            raise RuntimeError("Source changed while taking the audit snapshot")
    shutil.copytree(ROOT / "sc1/native_campaign/dialog_assets", build / "snapshot/dialog_assets",
                    ignore=shutil.ignore_patterns("*.py", "*.png", "__pycache__"))
    pointer = read(ROOT / "sc1/manager_release.json")
    release = (ROOT / "sc1" / pointer["directory"]).resolve()
    if not release.is_relative_to(ROOT / "sc1/dist"):
        raise ValueError("Manager release points outside sc1/dist")
    native = release / "sc1/native_campaign"
    manifest = native / read(native / "current_build.json")["manifest"]
    shutil.copytree(manifest.parent / "overlay", build / "overlay")
    loader = next((native / "vendor").glob("**/samase64*.exe"))
    shutil.copy2(loader, build / "samase64.exe")
    shutil.copy2(ROOT / "sc1/effect_lab/SC1_Effect_Lab.scx", build / "SC1_Effect_Lab.scx")
    shutil.copy2(probe_source or Path(__file__).with_name("live_combat_probe.cpp"), build / "probe.cpp")
    shutil.copy2(__file__, build / "verifier.py")
    (build / "paths.generated.h").write_text('#define AUDIT_LOG L"' + (build / "engine.jsonl").as_posix() + '"\n', encoding="utf-8")
    compiler, env = msvc_environment(ROOT)
    objects = build / "objects"; objects.mkdir()
    dll = build / "overlay/samase/live_audit.dll"
    command = [str(compiler), "/nologo", "/std:c++17", "/EHsc", "/MT", "/utf-8", "/W4", "/WX", "/O2", "/LD",
               str(build / "probe.cpp"), *[str(build / "snapshot/plugin" / name) for name in
               ("mailbox_protocol.cpp", "wave_runtime.cpp", "dialog_ui.cpp")],
               "/Fo:" + str(objects) + os.sep, "/Fe:" + str(dll), "/link", "/MACHINE:X64",
               "/IMPLIB:" + str(objects / "audit.lib"), "user32.lib"]
    result = subprocess.run(command, cwd=build, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (build / "compile.log").write_bytes(result.stdout)
    if result.returncode:
        raise RuntimeError(result.stdout.decode("utf-8", "replace"))
    (build / "overlay/samase/plugins").write_text("samase/live_audit.dll\n", encoding="ascii")
    if any(sha(plugin / name) != value for name, value in source.items()):
        raise RuntimeError("Production source changed during audit compilation")
    proof = dict(schema=1, build=str(build), source_files=source,
                 game=str(game), game_sha256=sha(game), dll_sha256=sha(dll),
                 loader_sha256=sha(build / "samase64.exe"), map_sha256=sha(build / "SC1_Effect_Lab.scx"),
                 probe_sha256=sha(build / "probe.cpp"), verifier_sha256=sha(build / "verifier.py"), contract_revision=3,
                 source_copy_byte_identical=True,
                 production_behavior_overrides=False, private_fixture_mutations=True,
                 game_installation_modified=False, campaign_database_accessed=False,
                 controls=["no talents", "A only", "B only", "A+B"],
                 cases=["marine warmup", "ghost normal type with armor-ignore",
                        "Scourge +120 attack with armor-ignore", "free triple Yamato",
                        "Dark Swarm boundary damage", "Ensnare boundary and strong effect",
                        "Lockdown mechanical and biological duration", "spread amplified acid",
                        "Vulture generated splash with armor-ignore"],
                 overlay_files={p.relative_to(build).as_posix(): sha(p) for p in (build / "overlay").rglob("*") if p.is_file()})
    write(build / "manifest.json", proof)
    print(json.dumps(dict(build=str(build), prepared=True, dll_sha256=proof["dll_sha256"])), flush=True)
    return build


def dump_summary(path):
    data = Path(path).read_bytes()
    if data[:4] != b"MDMP":
        return None
    count, table = struct.unpack_from("<II", data, 8)
    streams = {struct.unpack_from("<I", data, table + i * 12)[0]:
               struct.unpack_from("<II", data, table + i * 12 + 4) for i in range(count)}
    result = {"sha256": hashlib.sha256(data).hexdigest(), "pid": None}
    if 15 in streams:
        size, offset = streams[15]
        if size >= 12 and struct.unpack_from("<I", data, offset + 4)[0] & 1:
            result["pid"] = struct.unpack_from("<I", data, offset + 8)[0]
    if 6 in streams:
        _, offset = streams[6]
        result.update(exception_code=hex(struct.unpack_from("<I", data, offset + 8)[0]),
                      exception_address=hex(struct.unpack_from("<Q", data, offset + 24)[0]))
    return result


def run(build: Path, timeout=940):
    build = build.resolve(); manifest = read(build / "manifest.json")
    if (build / "run.json").exists():
        raise ValueError("Each execution needs a fresh prepared directory")
    if (build / "engine.jsonl").exists():
        raise ValueError("A fresh run must not have preexisting engine log evidence")
    if inventory():
        raise RuntimeError("A StarCraft session already exists; it will not be interrupted")
    for name, value in manifest["overlay_files"].items():
        path = (build / name).resolve()
        if not path.is_relative_to(build) or sha(path) != value:
            raise ValueError("Private overlay hash mismatch")
    for path, key in [(Path(manifest["game"]), "game_sha256"), (build / "samase64.exe", "loader_sha256"),
                      (build / "SC1_Effect_Lab.scx", "map_sha256")]:
        if sha(path) != manifest[key]:
            raise ValueError("Pinned engine/loader/map changed")
    temp = Path(os.environ["LOCALAPPDATA"]) / "Temp/samase"
    before_dumps = {str(p): p.stat().st_mtime_ns for p in temp.rglob("*.dmp")}
    kernel = C.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]; kernel.OpenProcess.restype = W.HANDLE
    kernel.GetExitCodeProcess.argtypes = [W.HANDLE, C.POINTER(W.DWORD)]
    kernel.TerminateProcess.argtypes = [W.HANDLE, W.UINT]; kernel.CloseHandle.argtypes = [W.HANDLE]
    command = [str(build / "samase64.exe"), str(build / "overlay"), "--starcraft-exe", manifest["game"],
               "--map", str(build / "SC1_Effect_Lab.scx"), "--log", "--no-debug"]
    with (build / "loader_stdout.log").open("wb") as output:
        child = subprocess.Popen(command, cwd=build, stdin=subprocess.DEVNULL, stdout=output,
                                 stderr=subprocess.STDOUT, creationflags=0x08000000)
    record = dict(started_at_utc=dt.datetime.now(dt.timezone.utc).isoformat(), loader_pid=child.pid,
                  command=command, game_launched=True, game_installation_modified=False,
                  campaign_database_accessed=False, owned_game_pid=None)
    write(build / "run.json", record)
    print(json.dumps(record), flush=True)
    deadline, last_progress = time.monotonic() + timeout, 0.0
    handle = None; game_pid = None; game_exit = None; timed_out = False
    try:
        while time.monotonic() < deadline:
            rows, _ = events(build / "engine.jsonl")
            current = inventory()
            if handle is None:
                candidates = [p for p in current if p["parent_pid"] == child.pid]
                if len(candidates) == 1:
                    game_pid = candidates[0]["pid"]
                    handle = kernel.OpenProcess(0x1000 | 0x100000 | 1, False, game_pid)
                    if not handle:
                        raise C.WinError(C.get_last_error())
                    record["owned_game_pid"] = game_pid; write(build / "run.json", record)
            if handle:
                value = W.DWORD()
                if not kernel.GetExitCodeProcess(handle, C.byref(value)):
                    raise C.WinError(C.get_last_error())
                if value.value != 259:
                    game_exit = value.value; break
            elif child.poll() is not None and not current:
                break
            if time.monotonic() - last_progress >= 15:
                last_progress = time.monotonic()
                state = next((r for r in reversed(rows) if r.get("event") in ("heartbeat", "phase_start", "terminal")), {})
                print(json.dumps(dict(progress=state, log_rows=len(rows), game_pid=game_pid)), flush=True)
            time.sleep(0.5)
        else:
            timed_out = True
        if timed_out and handle:
            kernel.TerminateProcess(handle, 73)
        record.update(game_exit_code=game_exit, loader_exit_code=child.poll(), timed_out=timed_out,
                      only_owned_process_stopped=bool(timed_out and handle), completed_at_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    except BaseException as error:
        if handle:
            kernel.TerminateProcess(handle, 73)
        record.update(controller_error=type(error).__name__, only_owned_process_stopped=bool(handle))
        write(build / "run.json", record)
        raise
    finally:
        if handle:
            kernel.CloseHandle(handle)
    dumps = []
    for path in temp.rglob("*.dmp"):
        if before_dumps.get(str(path)) == path.stat().st_mtime_ns:
            continue
        try:
            info = dump_summary(path)
        except (ValueError, IndexError, struct.error):
            continue
        if info and info.get("pid") == game_pid and game_pid is not None:
            dest = build / ("crash_" + str(len(dumps)) + ".dmp")
            shutil.copy2(path, dest); info["path"] = str(dest); dumps.append(info)
    record["crash_dumps"] = dumps
    native_log = temp / "plugins/sc1_native.log"
    if native_log.is_file():
        shutil.copy2(native_log, build / "sc1_native.log")
    write(build / "run.json", record)
    return analyze(build)


def analyze_rows(rows, run_record, malformed=0):
    checks = []
    def check(name, passed, observed, expected):
        checks.append(dict(name=name, passed=bool(passed), observed=observed, expected=expected))
    terminal = next((r for r in reversed(rows) if r.get("event") == "terminal"), None)
    complete = {r["phase"] for r in rows if r.get("event") == "phase_complete"}
    entry_pids={r.get("pid") for r in rows if r.get("event")=="entry"}
    owned_pid=run_record.get("owned_game_pid")
    identity_matches=owned_pid is not None and entry_pids=={owned_pid} and terminal is not None and terminal.get("pid")==owned_pid
    check("complete_evidence", terminal is not None and terminal.get("status") == "complete" and complete == {0,1,2,3} and malformed == 0 and identity_matches,
          dict(terminal=terminal, phases=sorted(complete), malformed=malformed,owned_game_pid=owned_pid,entry_pids=sorted(entry_pids)), "four completed controls and terminal from the exact launched process")
    check("process_exit", run_record.get("game_exit_code") == 0 and not run_record.get("timed_out") and not run_record.get("crash_dumps"),
          {k: run_record.get(k) for k in ("game_exit_code", "timed_out", "crash_dumps")}, "exit 0, no timeout or matching crash dump")
    def hits(p, c, victim=0, weapon=None, generated=None):
        return [r for r in rows if r.get("event")=="hit" and r["phase"]==p and r["case"]==c and r["victim"]==victim
                and (weapon is None or r["weapon"]==weapon) and (generated is None or bool(r["generated"])==generated)]
    def targets(p,c,v=0):
        return [r for r in rows if r.get("event")=="target" and r["phase"]==p and r["case"]==c and r["victim"]==v]
    def damage(r):
        return r["hp_before"]-r["hp_after"]+r["shields_before"]-r["shields_after"]
    # Independent stock-data + catalog contracts: SCV armor0, Goliath armor1
    # and large size, Dropship armor1. Q8 preserves fractional native damage.
    for case, name, expected, minimum in [(0,"marine_damage",[1536]*4,5),
                  (1,"ghost_normal_type",[576,4864,640,5120],5),
                  (2,"scourge_rank4",[27904,58624,28160,58880],3)]:
        for p in range(4):
            sample=hits(p,case,generated=False)
            values=sorted({damage(r) for r in sample})
            check(name+"_"+str(p),len(sample)>=minimum and values==[expected[p]] and all(r["target_identity_retained"] for r in sample),
                  dict(hits=len(sample),q8=values),dict(min_hits=minimum,q8=expected[p]))
    for p, expected in [(1,2304),(3,2560)]:
        sample=hits(p,8,victim=1,generated=True)
        values=sorted({damage(r) for r in sample})
        check("generated_vulture_splash_"+str(p),len(sample)>=3 and values==[expected],dict(hits=len(sample),q8=values),expected)
    cadence=[];medians=[];cooldown_peaks=[]
    for p in range(4):
        phase_start=next((r["frame"] for r in rows if r.get("event")=="phase_start" and r["phase"]==p),0)
        frames=sorted({r["frame"] for r in hits(p,0,generated=False) if 240<=r["frame"]-phase_start<=1200})
        intervals=[b-a for a,b in zip(frames,frames[1:])]
        cadence.append(statistics.mean(intervals) if len(intervals)>=10 else None)
        medians.append(statistics.median(intervals) if len(intervals)>=10 else None)
        cooldown_peaks.append(max((r['ground_cd'] for r in rows if r.get('event')=='actor' and r['phase']==p and r['case']==0 and 240<=r['elapsed']<=1200),default=0))
    # Fractions of a frame in a short random-jitter sample do not prove synergy.
    check("both_warmups_change_actual_cadence",all(x is not None for x in medians) and medians[3]<=medians[1]*0.7+1 and medians[3]<min(medians[1],medians[2]),
          dict(mean_frames=cadence,median_frames=medians,observed_cooldown_peaks=cooldown_peaks),
          "combined steady attack interval reflects the additional30% reduction, allowing one frame of jitter; equal medians are not a pass")
    for p in range(4):
        sample=hits(p,3,weapon=30)
        actors=[r for r in rows if r.get("event")=="actor" and r["phase"]==p and r["case"]==3]
        primaries=max((r["primary_attacks"] for r in actors),default=0)
        expected_count=(primaries//4)*(3 if p==3 else 1) if p&1 else 0
        # Yamato's native explosive type halves HP damage against the small SCV.
        # Raw native inputs are260/520; actual HP loss must be130/260.
        expected_damage=66560 if p==3 else 33280
        values=sorted({damage(r) for r in sample})
        okay=(len(sample)==0) if not p&1 else (len(sample)>=3 and abs(len(sample)-expected_count)<=(3 if p==3 else 1) and values==[expected_damage])
        check("free_yamato_"+str(p),okay,dict(hits=len(sample),primary_attacks=primaries,q8=values),dict(hits_approx=expected_count,q8=expected_damage))
    swarm=[]
    for p in range(4):
        losses=[]
        for v in range(2):
            sample=[r for r in targets(p,4,v) if 240<=r["elapsed"]<=600]
            losses.append(sample[0]["hp_q8"]-sample[-1]["hp_q8"] if len(sample)>2 else None)
        swarm.append(losses)
    check("swarm_240px_actual_protection",all(a is not None and b is not None and b>0 for a,b in swarm)
          and all(swarm[p][0]>0 for p in (0,1,2)) and swarm[3][0]==0,swarm,"200px target protected only with both; 270px control always damaged")
    for p in range(4):
        observed=[]
        for v in range(3):
            sample=targets(p,5,v)
            observed.append(dict(timer=max((r["ensnare"] for r in sample),default=0),strong=max((r["strong_ensnare"] for r in sample),default=0)))
        expected=150 if p&1 else 75
        okay=expected-3<=observed[0]["timer"]<=expected and bool(observed[0]["strong"])==bool(p&2)
        okay=okay and bool(observed[1]["timer"])==bool(p&1) and observed[2]["timer"]==0
        if p==3:okay=okay and observed[1]["strong"]==1
        check("ensnare_boundary_"+str(p),okay,observed,dict(center_timer=expected,mid_96px=bool(p&1),outside_144px=False,strong=bool(p&2)))
    for p in range(4):
        for v,expected in [(0,262 if p&1 else 131),(1,524 if p==3 else 262 if p==2 else 0)]:
            sample=targets(p,6,v)
            maximum=max((r["lockdown"]+r["lockdown_reserve"] for r in sample),default=0)
            okay=expected-3<=maximum<=expected if expected else maximum==0
            if p==3:okay=okay and bool(sample) and sample[-1]["lockdown"]==0 and sample[-1]["lockdown_reserve"]==0
            check("lockdown_"+str(p)+"_"+str(v),okay,dict(maximum=maximum,last=sample[-1] if sample else None),dict(total_native_ticks=expected,expires_in_combined_control=p==3))
    acid=targets(3,7,1)
    check("spread_acid_amplified",any(r["acid"]>0 and r["double_acid"] for r in acid),
          dict(peak_spores=max((r["acid"] for r in acid),default=0),amplified_samples=sum(bool(r["double_acid"]) for r in acid)),"secondary enemy receives amplified spores in A+B")
    passed=all(r["passed"] for r in checks)
    exit_code=run_record.get("game_exit_code")
    execution_status=("timeout" if run_record.get("timed_out") or (terminal and terminal.get("status")=="watchdog_timeout") else
                      "engine_crash" if run_record.get("crash_dumps") or exit_code not in (None,0,73) else
                      "incomplete" if not checks[0]["passed"] or exit_code!=0 else
                      "passed" if passed else "measurement_mismatch")
    return dict(passed=passed,execution_status=execution_status,checks=checks,checks_passed=sum(r["passed"] for r in checks),checks_total=len(checks),
                actual_engine_executed=any(r.get("event")=="phase_start" for r in rows),
                limits=["Isolated scripted combat scenarios, not campaign completion or all talent loadouts.",
                        "Private observer DLL built from hashed production sources; not byte-identical to the packaged DLL.",
                        "Exit is controlled by the audit; normal game shutdown and UI appearance are not tested."])


def analyze(build):
    build=Path(build);rows, malformed=events(build/"engine.jsonl")
    result=analyze_rows(rows,read(build/"run.json"),malformed)
    result.update(build=str(build.resolve()),manifest_sha256=sha(build/"manifest.json"),verifier_sha256=sha(__file__),contract_revision=3,
                  log_sha256=sha(build/"engine.jsonl") if (build/"engine.jsonl").exists() else None)
    write(build/"verification.json",result)
    print(json.dumps(dict(passed=result["passed"],checks_passed=result["checks_passed"],checks_total=result["checks_total"],report=str(build/"verification.json"))),flush=True)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    sub=parser.add_subparsers(dest="action",required=True)
    p=sub.add_parser("prepare");p.add_argument("--output",type=Path,required=True);p.add_argument("--game",type=Path,required=True);p.add_argument("--probe",type=Path)
    p=sub.add_parser("run");p.add_argument("--build",type=Path,required=True);p.add_argument("--timeout",type=int,default=940)
    p=sub.add_parser("analyze");p.add_argument("--build",type=Path,required=True)
    p=sub.add_parser("check");p.add_argument("--output",type=Path,required=True);p.add_argument("--game",type=Path,required=True)
    args=parser.parse_args()
    if args.action=="prepare":prepare(args.output,args.game,probe_source=args.probe)
    elif args.action=="run":run(args.build,args.timeout)
    elif args.action=="analyze":analyze(args.build)
    else:
        if inventory():raise RuntimeError("Close the existing StarCraft session before starting the isolated audit")
        build=prepare(args.output,args.game);result=run(build)
        write(args.output/"latest_result.json",result)


if __name__=="__main__":main()
