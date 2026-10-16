"""Launcher-to-manager connection requests; never opens game memory or records."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
import json
import ntpath
import os
from pathlib import Path, PureWindowsPath
import tempfile
import time
import uuid


@dataclass(frozen=True)
class AutoConnectTarget:
    image: str | None = None
    started_after: int = 0

    def __post_init__(self):
        if self.started_after < 0:
            raise ValueError('Game start time must be nonnegative')
        if self.image is not None and PureWindowsPath(self.image).name.casefold() != 'starcraft.exe':
            raise ValueError('Automatic connection target must be StarCraft.exe')

    def matches(self, game):
        if game.architecture not in ('x86', 'x86_64') or game.started_at < self.started_after:
            return False
        return self.image is None or ntpath.normcase(ntpath.normpath(game.image_path)) == ntpath.normcase(ntpath.normpath(self.image))


def request_path():
    session = 0
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.ProcessIdToSessionId.argtypes = [wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
        kernel.ProcessIdToSessionId.restype = wintypes.BOOL
        value = wintypes.DWORD()
        if not kernel.ProcessIdToSessionId(os.getpid(), ctypes.byref(value)):
            raise ctypes.WinError(ctypes.get_last_error())
        session = value.value
    return Path(tempfile.gettempdir()) / f'sc1-campaign-manager-connect-{session}.json'


def publish_request(path, target, *, clock=time.time):
    path = Path(path)
    request = {'version': 1, 'token': uuid.uuid4().hex, 'created_at': clock(),
               'image': target.image, 'started_after': target.started_after}
    temporary = path.with_name(path.name + '.' + request['token'] + '.tmp')
    try:
        temporary.write_text(json.dumps(request, ensure_ascii=True), encoding='utf-8')
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return request['token']


def read_request(path, *, clock=time.time):
    try:
        with Path(path).open('rb') as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return None
        value = json.loads(raw)
        token = value['token']
        created = value['created_at']
        if value['version'] != 1 or not isinstance(token, str) or uuid.UUID(hex=token).hex != token:
            return None
        if isinstance(created, bool) or not isinstance(created, (float, int)) or not 0 <= clock() - created <= 120:
            return None
        after = value['started_after']
        if isinstance(after, bool) or not isinstance(after, int):
            return None
        target = AutoConnectTarget(value['image'], after)
        return token, target
    except (OSError, ValueError, TypeError, KeyError, AttributeError):
        return None
