"""Locate an x64 MSVC environment without committing machine-specific settings."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess


def msvc_environment(workspace):
    workspace = Path(workspace)
    saved = workspace / 'analysis/all_campaign_20261015/previous_native_build_evidence.json'
    if saved.is_file():
        compiler = json.loads(saved.read_text(encoding='utf8'))['compiler']
        path = Path(compiler['path'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != compiler['sha256']:
            raise ValueError('Pinned MSVC compiler changed')
        environment = dict(os.environ)
        environment.update(compiler['environment'])
    else:
        vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
        location = subprocess.check_output([str(vswhere), '-latest', '-products', '*', '-requires',
            'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-property', 'installationPath'], text=True).strip()
        if not location:
            raise RuntimeError('Install Visual Studio C++ Desktop build tools (x64).')
        vcvars = Path(location) / 'VC/Auxiliary/Build/vcvars64.bat'
        command = 'cmd.exe /d /s /c ""' + str(vcvars) + '" >nul && set"'
        output = subprocess.check_output(command, text=True, errors='replace')
        environment = dict(os.environ)
        environment.update(line.split('=', 1) for line in output.splitlines() if '=' in line and not line.startswith('='))
        candidates = sorted((Path(location) / 'VC/Tools/MSVC').glob('*/bin/Hostx64/x64/cl.exe'), reverse=True)
        path = candidates[0]
    environment['PATH'] = str(path.parent) + os.pathsep + environment.get('PATH', '')
    return path, environment
