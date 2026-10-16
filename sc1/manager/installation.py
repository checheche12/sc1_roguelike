"""Managed campaign deployment. Importing this module never installs or launches.

Only an explicit manager action calls the mutating APIs. Original CASC and the
StarCraft executable are read-only inputs. All tests use workspace fixtures.
"""
from __future__ import annotations

from contextlib import contextmanager
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import struct
import subprocess
import sys
import time
import uuid

WORKSPACE = Path(__file__).resolve().parents[2]
NATIVE = WORKSPACE / "sc1/native_campaign"
PIN_PATH = NATIVE / "loader_pin.json"
INSTALL_NAME = "SC1CampaignGrowth"
OWNER = "sc1-campaign-growth-managed-v1"
PREFIXES = ("Locales/koKR/Assets", "", "SD")
DAT_NAMES = {"units", "weapons", "flingy", "sprites", "images", "upgrades", "techdata", "mapdata", "orders", "portdata", "buttons"}


class InstallationError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def _fail(code, message):
    raise InstallationError(code, message)


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _pe64(path):
    data = Path(path).read_bytes()
    if len(data) < 64 or data[:2] != b"MZ":
        _fail("architecture", "64비트 스타크래프트 실행 파일이 아닙니다.")
    offset = struct.unpack_from("<I", data, 0x3C)[0]
    if offset + 26 > len(data) or data[offset:offset + 4] != b"PE\0\0":
        _fail("architecture", "실행 파일의 PE 정보를 읽을 수 없습니다.")
    if struct.unpack_from("<H", data, offset + 4)[0] != 0x8664 or struct.unpack_from("<H", data, offset + 24)[0] != 0x20B:
        _fail("architecture", "x86_64 폴더의 64비트 StarCraft.exe를 선택해 주세요.")
    return data


def _file_version(path):
    version = ctypes.WinDLL("version", use_last_error=True)
    version.GetFileVersionInfoSizeW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.DWORD)]
    version.GetFileVersionInfoSizeW.restype = wintypes.DWORD
    version.GetFileVersionInfoW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    version.GetFileVersionInfoW.restype = wintypes.BOOL
    version.VerQueryValueW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.UINT)]
    version.VerQueryValueW.restype = wintypes.BOOL
    ignored = wintypes.DWORD()
    size = version.GetFileVersionInfoSizeW(str(path), ctypes.byref(ignored))
    if not size:
        _fail("version", "스타크래프트 버전 정보를 읽을 수 없습니다.")
    data = ctypes.create_string_buffer(size)
    if not version.GetFileVersionInfoW(str(path), 0, size, data):
        _fail("version", "스타크래프트 버전 정보를 읽을 수 없습니다.")
    pointer, length = ctypes.c_void_p(), wintypes.UINT()
    if not version.VerQueryValueW(data, "\\", ctypes.byref(pointer), ctypes.byref(length)) or length.value < 52:
        _fail("version", "스타크래프트 버전 정보가 올바르지 않습니다.")
    values = ctypes.cast(pointer, ctypes.POINTER(wintypes.DWORD))
    if values[0] != 0xFEEF04BD:
        _fail("version", "스타크래프트 버전 서명이 올바르지 않습니다.")
    return ".".join(str(v) for v in (values[2] >> 16, values[2] & 65535, values[3] >> 16, values[3] & 65535))


def _running_game_processes(executable):
    """Fail closed on a StarCraft process whose executable cannot be inspected."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    class Entry(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", wintypes.LONG), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", wintypes.WCHAR * 260)]
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(Entry)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
    if snapshot == ctypes.c_void_p(-1).value:
        _fail("process_check", "실행 중인 게임을 확인할 수 없어 작업을 중단했습니다.")
    found = []
    try:
        entry = Entry(); entry.dwSize = ctypes.sizeof(entry)
        active = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while active:
            # Block any running StarCraft installation. This also covers an
            # inaccessible image and avoids updating shared-loader sessions.
            if entry.szExeFile.casefold() == "starcraft.exe" or entry.szExeFile.casefold().startswith("samase64"):
                # The loader may be alive before StarCraft has a process ID.
                found.append(int(entry.th32ProcessID))
            active = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return found


def _game(game_path, *, require_supported=True):
    pin = _read_json(PIN_PATH)
    chosen = Path(game_path).expanduser().resolve()
    if chosen.is_file():
        executable = chosen
    elif chosen.name.casefold() == "x86_64":
        executable = chosen / "StarCraft.exe"
    else:
        executable = chosen / "x86_64/StarCraft.exe"
    if not executable.is_file() or executable.name.casefold() != "starcraft.exe" or executable.parent.name.casefold() != "x86_64":
        _fail("game_path", "스타크래프트 설치 폴더 또는 x86_64/StarCraft.exe를 선택해 주세요.")
    executable = executable.resolve()
    raw = _pe64(executable)
    version = _file_version(executable)
    if require_supported and version != pin["game_file_version_observed"]:
        _fail("version", "지원하는 스타크래프트 버전은 " + pin["game_file_version_observed"] + "입니다. 선택한 버전: " + version)
    return {"executable": executable, "root": executable.parent.parent, "version": version, "sha256": _sha(raw), "pin": pin}


def _not_running(game):
    if _running_game_processes(game["executable"]):
        _fail("game_running", "스타크래프트가 실행 중입니다. 게임을 닫은 뒤 다시 시도해 주세요.")


def _relative(name):
    if not isinstance(name, str) or "\\" in name or ":" in name:
        _fail("asset_path", "패키지 파일 경로가 올바르지 않습니다.")
    path = PurePosixPath(name)
    if path.is_absolute() or not path.parts or any(part in ("..", ".") for part in path.parts) or path.as_posix() != name:
        _fail("asset_path", "패키지 파일 경로가 올바르지 않습니다.")
    return path


def _contained(root, name):
    relative = _relative(name)
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        _fail("asset_path", "패키지 파일이 관리 폴더 밖을 가리킵니다.")
    return target


def _manager_pins(manifest):
    entries = manifest.get("inputs", {}).get("manager_sources", [])
    if not entries:
        _fail("manager_pin", "패키지에 관리자 버전 확인 정보가 없습니다. 패키지를 다시 빌드해 주세요.")
    seen = set()
    for row in entries:
        source = Path(row["path"])
        path = (source if source.is_absolute() else WORKSPACE / source).resolve()
        if not path.is_relative_to(WORKSPACE.resolve()) or path in seen or not path.is_file() or _sha(path.read_bytes()) != row["sha256"]:
            _fail("manager_pin", "패키지와 관리자의 버전이 다릅니다. 최신 패키지를 다시 설치해 주세요.")
        seen.add(path)


def _package(manifest_path=None):
    pin = _read_json(PIN_PATH)
    if manifest_path is None:
        pointer = _read_json(NATIVE / "current_build.json")
        manifest_path = _contained(NATIVE, pointer["manifest"])
    path = Path(manifest_path).resolve()
    if not path.is_relative_to(WORKSPACE.resolve()):
        _fail("package_path", "작업 폴더에서 검증된 캠페인 패키지를 선택해 주세요.")
    manifest_raw = path.read_bytes(); manifest = json.loads(manifest_raw)
    if manifest.get("mode") != "native_all_campaigns" or manifest.get("schema_version") != 3 or manifest.get("scenario_count") != 63:
        _fail("package_scope", "본편·브루드워 전체 63개 지도 패키지가 아직 준비되지 않았습니다.")
    if manifest.get("loader_sha256") != pin["sha256"]:
        _fail("loader_pin", "패키지와 Samase 실행기의 버전이 다릅니다.")
    _manager_pins(manifest)
    from sc1.campaign.missions import load_missions
    roster = {m["mission_id"]: m["asset_path"] for m in load_missions()}
    rows = manifest.get("missions", [])
    if len(rows) != 63 or {r["mission_id"]: r["asset_path"] for r in rows} != roster:
        _fail("package_scope", "임무 목록 또는 분기 지도 구성이 올바르지 않습니다.")
    expected = {"overlay/" + (prefix + "/" if prefix else "") + asset for asset in roster.values() for prefix in PREFIXES}
    expected |= {"overlay/arr/" + name + ".dat" for name in DAT_NAMES}
    expected |= {"overlay/samase/native_plugin.dll", "overlay/samase/plugins"}
    files = manifest.get("files", [])
    if len(files) != 202 or {r["path"] for r in files} != expected:
        _fail("package_files", "패키지의 202개 필수 파일 구성이 올바르지 않습니다.")
    payload = {}
    for row in files:
        source = _contained(path.parent, row["path"])
        data = source.read_bytes()
        if _sha(data) != row["sha256"] or len(data) != row["bytes"]:
            _fail("package_hash", "패키지 파일이 변경되었습니다: " + row["path"])
        payload[row["path"]] = data
    for mission in rows:
        for prefix in PREFIXES:
            name = "overlay/" + (prefix + "/" if prefix else "") + mission["asset_path"]
            if _sha(payload[name]) != mission["sha256"]:
                _fail("package_hash", "지도 목록과 실제 파일이 다릅니다.")
    loader = _contained(NATIVE, pin["local_filename"])
    data = _pe64(loader)
    if _sha(data) != pin["sha256"]:
        _fail("loader_pin", "검증된 Samase 실행기가 변경되었습니다.")
    payload["samase64.exe"] = data
    payload["manifest.json"] = manifest_raw
    return {"path": path, "manifest": manifest, "payload": payload, "sha256": _sha(manifest_raw)}


def _installed(directory, *, manager=True):
    if directory.is_symlink() or directory.resolve() != directory:
        _fail("managed_path", "관리 폴더의 연결 경로에는 설치할 수 없습니다.")
    receipt_path = directory / "installation.json"
    if not receipt_path.is_file():
        _fail("unmanaged", "SC1CampaignGrowth 폴더에 관리되지 않는 파일이 있습니다. 기존 폴더는 덮어쓰지 않습니다.")
    receipt = _read_json(receipt_path)
    if receipt.get("owner") != OWNER or receipt.get("schema_version") != 1:
        _fail("unmanaged", "기존 폴더가 이 도구에서 설치한 캠페인 패치가 아닙니다.")
    rows = receipt.get("files", [])
    names = {r["path"] for r in rows}
    if len(rows) != 204 or len(names) != 204 or not {"samase64.exe", "manifest.json"} <= names:
        _fail("installed_hash", "설치된 파일 목록이 올바르지 않습니다.")
    for row in rows:
        path = _contained(directory, row["path"])
        if not path.is_file() or _sha(path.read_bytes()) != row["sha256"]:
            _fail("installed_hash", "설치된 파일이 변경되었습니다: " + row["path"])
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
    if actual - names - {"installation.json", "samase.log"}:
        _fail("unmanaged", "관리 폴더에 별도 파일이 있어 덮어쓰지 않습니다. 추가 파일을 다른 폴더로 옮겨 주세요.")
    manifest = _read_json(directory / "manifest.json")
    pin = _read_json(PIN_PATH)
    if manifest.get("mode") != "native_all_campaigns" or _sha((directory / "samase64.exe").read_bytes()) != manifest.get("loader_sha256"):
        _fail("loader_pin", "설치된 패키지의 실행기 파일이 변경되었습니다.")
    if manager and manifest.get("loader_sha256") != pin["sha256"]:
        _fail("loader_pin", "설치된 패키지와 현재 실행기 버전이 다릅니다.")
    if manager:
        _manager_pins(manifest)
    return receipt, manifest


def _backup_path(game, receipt):
    value = receipt.get("previous_backup")
    if not value:
        return None
    path = Path(value).resolve()
    if path.parent != game["root"] or not path.name.startswith("." + INSTALL_NAME + ".backup."):
        _fail("backup_path", "이전 버전의 백업 경로가 올바르지 않습니다.")
    return path


@contextmanager
def _installation_lock(game):
    path = game["root"] / ("." + INSTALL_NAME + ".install.lock")
    token = uuid.uuid4().hex
    try:
        with path.open("x", encoding="ascii") as stream:
            stream.write(token)
    except FileExistsError:
        _fail("busy", "다른 설치 또는 복원 작업이 진행 중입니다.")
    try:
        yield
    finally:
        if path.is_file() and path.read_text(encoding="ascii") == token:
            path.unlink()


def inspect_installation(game_path):
    game = _game(game_path); directory = game["root"] / INSTALL_NAME
    result = {"status": "not_installed", "message": "원본 캠페인을 시작할 수 있습니다. 성장 모드를 사용하려면 캠페인 패치를 설치해 주세요.",
              "executable": str(game["executable"]), "game_version": game["version"], "install_root": str(directory),
              "backup_available": False, "running": bool(_running_game_processes(game["executable"]))}
    if directory.exists():
        receipt, _ = _installed(directory)
        backup = _backup_path(game, receipt)
        result.update(status="installed", message="본편·브루드워 캠페인 패치가 설치되어 있습니다.",
                      manifest=str(directory / "manifest.json"), backup_available=bool(backup and backup.is_dir()))
    return result


def install_package(game_path, manifest_path=None):
    game = _game(game_path); _not_running(game)
    package = _package(manifest_path)
    target = game["root"] / INSTALL_NAME
    with _installation_lock(game):
        old = _installed(target, manager=False)[0] if target.exists() else None
        suffix = uuid.uuid4().hex
        staging = game["root"] / ("." + INSTALL_NAME + ".staging." + suffix)
        backup = game["root"] / ("." + INSTALL_NAME + ".backup." + suffix) if old else None
        staging.mkdir()
        try:
            entries = []
            for name, data in sorted(package["payload"].items()):
                destination = _contained(staging, name); destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(data)
                entries.append({"path": name, "sha256": _sha(data), "bytes": len(data)})
            receipt = {"schema_version": 1, "owner": OWNER, "installed_at_utc": datetime.now(timezone.utc).isoformat(),
                       "game_executable": str(game["executable"]), "game_version": game["version"], "game_sha256": game["sha256"],
                       "source_manifest": str(package["path"]), "source_manifest_sha256": package["sha256"],
                       "files": entries, "previous_backup": str(backup) if backup else None,
                       "original_game_files_modified": False}
            (staging / "installation.json").write_bytes(_json_bytes(receipt))
            _installed(staging); _not_running(game)
            if _sha(game["executable"].read_bytes()) != game["sha256"]:
                _fail("game_changed", "설치 도중 게임 파일이 변경되어 중단했습니다.")
            if old:
                _installed(target, manager=False)
                target.rename(backup)
            try:
                staging.rename(target)
            except BaseException:
                if backup and backup.exists() and not target.exists():
                    backup.rename(target)
                raise
        finally:
            # Only the freshly created, resolved staging child may be removed.
            if staging.exists() and staging.resolve().parent == game["root"] and staging.name == "." + INSTALL_NAME + ".staging." + suffix:
                shutil.rmtree(staging)
    return {"status": "installed", "message": "캠페인 패치를 설치했습니다.", "install_root": str(target),
            "manifest": str(target / "manifest.json"), "executable": str(game["executable"]), "backup_available": bool(backup), "files": 202}


def restore_installation(game_path):
    game = _game(game_path); _not_running(game); target = game["root"] / INSTALL_NAME
    with _installation_lock(game):
        receipt, _ = _installed(target, manager=False)
        backup = _backup_path(game, receipt)
        if backup is None or not backup.is_dir():
            _fail("no_backup", "복원할 이전 패치 버전이 없습니다.")
        _installed(backup, manager=False); _not_running(game)
        retained = game["root"] / ("." + INSTALL_NAME + ".replaced." + uuid.uuid4().hex)
        target.rename(retained)
        try:
            backup.rename(target)
        except BaseException:
            retained.rename(target)
            raise
    return {"status": "restored", "message": "이전 패치 버전으로 복원했습니다.", "install_root": str(target),
            "manifest": str(target / "manifest.json"), "executable": str(game["executable"]), "retained_previous_install": str(retained)}


def restore_original_campaign(game_path):
    """Disable only this tool's verified deployment; preserve every file and DB.

    The original game has never been replaced. Moving the managed loader/overlay
    aside makes the ordinary launch action use StarCraft directly. The retained
    folder remains a complete verified copy; installing again is independent of
    it and does not discard either it or the player's growth records.
    """
    game = _game(game_path, require_supported=False)
    _not_running(game)
    target = game["root"] / INSTALL_NAME
    with _installation_lock(game):
        if not target.exists() and not target.is_symlink():
            return {"status": "original", "mode": "original", "auto_connect": False,
                    "message": "이미 원본 캠페인 상태입니다. 스타크래프트 시작을 누르면 원본 게임이 실행됩니다.",
                    "executable": str(game["executable"]), "install_root": str(target),
                    "retained_installation": None}
        _installed(target, manager=False)
        retained = game["root"] / ("." + INSTALL_NAME + ".disabled." + uuid.uuid4().hex)
        if retained.exists() or retained.is_symlink() or retained.resolve().parent != game["root"]:
            _fail("managed_path", "캠페인 패치를 보관할 경로가 올바르지 않습니다.")
        _not_running(game)
        _installed(target, manager=False)
        # Same-parent rename is atomic. Original game files and the managed
        # receipt are unchanged, and no recursive deletion occurs.
        target.rename(retained)
    return {"status": "original", "mode": "original", "auto_connect": False,
            "message": "원본 캠페인으로 되돌렸습니다. 성장 기록은 유지되며, 패치 파일은 보관했습니다. 다시 사용하려면 패치 설치를 누르세요.",
            "executable": str(game["executable"]), "install_root": str(target),
            "retained_installation": str(retained)}


def _popen(arguments, *, cwd):
    return subprocess.Popen([str(v) for v in arguments], cwd=str(cwd), stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def launch_installed(game_path, with_manager=False):
    game = _game(game_path); _not_running(game); directory = game["root"] / INSTALL_NAME
    receipt, _ = _installed(directory)
    _not_running(game)
    if receipt["game_sha256"] != game["sha256"] or Path(receipt["game_executable"]).resolve() != game["executable"]:
        _fail("game_changed", "설치 후 게임 파일이 변경되었습니다. 호환성을 확인하고 패치를 다시 설치해 주세요.")
    # Excludes already-running games from the manager's automatic attachment.
    started_after = time.time_ns() // 100 + 116444736000000000
    process = _popen([directory / "samase64.exe", directory / "overlay", "--starcraft-exe", game["executable"], "--log", "--no-debug"], cwd=directory)
    if with_manager:
        python = Path(sys.executable).with_name("pythonw.exe")
        if not python.is_file():
            python = Path(sys.executable)
        _popen([python, "-m", "sc1.manager", "ui", "--auto-connect", "--game-image", game["executable"], "--game-start-after", str(started_after)], cwd=WORKSPACE)
    return {"status": "started", "message": "스타크래프트를 시작했습니다.", "executable": str(game["executable"]),
            "started_after": started_after, "process_id": process.pid, "install_root": str(directory),
            "mode": "growth", "auto_connect": True}


def _launch_original(game):
    _not_running(game)
    if _sha(game["executable"].read_bytes()) != game["sha256"]:
        _fail("game_changed", "실행 준비 중 게임 파일이 변경되어 중단했습니다.")
    started_after = time.time_ns() // 100 + 116444736000000000
    process = _popen([game["executable"]], cwd=game["executable"].parent)
    return {"status": "started", "mode": "original", "auto_connect": False,
            "message": "원본 스타크래프트를 시작했습니다. 성장 기록은 연결하지 않습니다.",
            "executable": str(game["executable"]), "started_after": started_after,
            "process_id": process.pid}


def launch_original(game_path):
    """Explicit ordinary executable launch, with no loader or manager bridge."""
    game = _game(game_path, require_supported=False)
    with _installation_lock(game):
        return _launch_original(game)


def launch_campaign(game_path, with_manager=False, *, allow_growth=True):
    """Launch the verified installed mode, or the original game if uninstalled.

    A corrupt/unmanaged deployment is never treated as an absent deployment.
    allow_growth lets the UI reject an incompatible record before mod launch;
    an original launch needs no growth record and never starts another manager.
    """
    game = _game(game_path, require_supported=False)
    _not_running(game)
    directory = game["root"] / INSTALL_NAME
    with _installation_lock(game):
        if directory.exists() or directory.is_symlink():
            if not allow_growth:
                _fail("growth_profile", "성장 모드를 시작하려면 본편·브루드워 캠페인 기록을 열어 주세요.")
            return launch_installed(game_path, with_manager=with_manager)
        return _launch_original(game)
