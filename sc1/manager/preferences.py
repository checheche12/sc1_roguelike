"""Remember the last UI record without opening or changing its database."""
from __future__ import annotations

import json
import os
from pathlib import Path
import uuid


DATA_DIRECTORY = Path(__file__).resolve().parents[1] / "data"
DEFAULT_DATABASE = DATA_DIRECTORY / "original.sqlite3"
PREFERENCES_PATH = DATA_DIRECTORY / "manager_preferences.json"


def startup_database(explicit: Path | None = None, *, preferences_path: Path = PREFERENCES_PATH) -> Path:
    if explicit is not None:
        return Path(explicit).resolve()
    path = Path(preferences_path)
    try:
        with path.open("rb") as stream:
            raw = stream.read(16385)
    except FileNotFoundError:
        return DEFAULT_DATABASE.resolve()
    try:
        if len(raw) > 16384:
            raise ValueError("oversized preferences")
        value = json.loads(raw)
        selected = value["last_database"]
        if value["version"] != 1 or not isinstance(selected, str) or not selected:
            raise ValueError("invalid selection")
        database = Path(selected)
        if not database.is_absolute():
            raise ValueError("relative selection")
    except (ValueError, KeyError, TypeError) as exc:
        raise OSError("마지막 기록 설정을 읽을 수 없습니다. 사용할 기록 파일을 다시 선택해 주세요.") from exc
    if not database.is_file():
        raise FileNotFoundError(f"마지막 기록 파일을 찾을 수 없습니다.\n{database}\n\n이동한 기록 파일을 다시 선택해 주세요.")
    return database.resolve()


def remember_database(database: Path, *, preferences_path: Path = PREFERENCES_PATH) -> None:
    database = Path(database).resolve()
    if not database.is_file():
        raise FileNotFoundError(f"기록 파일이 없습니다: {database}")
    _save_preferences({"last_database": str(database)}, preferences_path)


def _save_preferences(changes, preferences_path):
    path = Path(preferences_path)
    try:
        current = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(current, dict) or current.get("version") != 1:
            current = {}
    except (OSError, ValueError):
        current = {}
    current.update(changes)
    current["version"] = 1
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temporary.write_text(json.dumps(current,
                                        ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _installed_game_candidates():
    """Read installer registration and common folders without launching anything."""
    try:
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
                for key_name, value_name in (
                    (r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\StarCraft", "InstallLocation"),
                    (r"SOFTWARE\Blizzard Entertainment\StarCraft", "InstallPath"),
                ):
                    try:
                        with winreg.OpenKey(hive, key_name, 0, winreg.KEY_READ | view) as key:
                            value, kind = winreg.QueryValueEx(key, value_name)
                            if isinstance(value, str) and value:
                                yield Path(os.path.expandvars(value))
                    except OSError:
                        pass
    except ImportError:
        pass
    for name in ("ProgramFiles(x86)", "ProgramFiles", "ProgramW6432"):
        folder = os.environ.get(name)
        if folder:
            yield Path(folder) / "StarCraft"
    # Preserve the local developer installation only when it actually exists.
    pin_path = Path(__file__).resolve().parents[1] / "native_campaign/loader_pin.json"
    yield Path(json.loads(pin_path.read_text(encoding="utf-8"))["game_executable"])


def startup_game_path(*, preferences_path: Path = PREFERENCES_PATH) -> Path | None:
    """A missing installation preference does not alter the selected record."""
    try:
        value = json.loads(Path(preferences_path).read_text(encoding="utf-8"))
        selected = value.get("game_path")
        if value.get("version") == 1 and isinstance(selected, str) and Path(selected).is_absolute():
            return Path(selected)
    except (OSError, ValueError, AttributeError):
        pass
    for candidate in _installed_game_candidates():
        executable = candidate if candidate.name.casefold() == "starcraft.exe" else candidate / "x86_64/StarCraft.exe"
        if executable.is_file():
            return executable.resolve()
    return None


def remember_game_path(game_path: Path, *, preferences_path: Path = PREFERENCES_PATH) -> None:
    """Remember only a path selected by the user; do not copy files or open DBs."""
    selected = Path(game_path).resolve()
    _save_preferences({"game_path": str(selected)}, preferences_path)
