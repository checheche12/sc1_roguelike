"""Build and verify a launcher-included ZIP without installing or starting the game."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable_zip(manifest, output):
    from sc1.build_portable import build
    output = Path(output).resolve()
    result = build(output, Path(manifest))
    subprocess.run([str(output / 'Start_Campaign.exe'), '--self-test'], cwd=output, check=True, timeout=120)
    smoke = json.loads((output / 'portable_self_test.json').read_text(encoding='utf8'))
    if not smoke['passed'] or smoke['game_started'] or smoke['user_database_accessed']:
        raise ValueError('Portable launcher self-test failed')
    for cache in (output / 'sc1').rglob('__pycache__'):
        if not cache.resolve().is_relative_to(output) or cache.is_symlink():
            raise ValueError('Unexpected cache path')
        for child in cache.iterdir():
            if child.suffix != '.pyc' or not child.is_file() or child.is_symlink():
                raise ValueError('Unexpected cache content')
            child.unlink()
        cache.rmdir()
    files = {p.relative_to(output).as_posix(): p for p in sorted(output.rglob('*')) if p.is_file()}
    if any(n.lower().endswith(('.lnk', '.sqlite3', '.db')) or n.startswith('sc1/data/') for n in files):
        raise ValueError('User records or shortcuts must not be distributed')
    archive = output.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as zipped:
        for name, path in files.items():
            zipped.write(path, output.name + '/' + name)
    with zipfile.ZipFile(archive) as zipped:
        if set(zipped.namelist()) != {output.name + '/' + name for name in files}:
            raise ValueError('ZIP membership differs')
        for name, path in files.items():
            if hashlib.sha256(zipped.read(output.name + '/' + name)).hexdigest() != sha(path):
                raise ValueError('ZIP content differs: ' + name)
    return dict(**result, archive=str(archive), archive_sha256=sha(archive), archive_bytes=archive.stat().st_size,
        manifest=str(manifest), manifest_sha256=sha(manifest), portable_self_test=smoke,
        archive_readback_verified=True, lnk_files_in_zip=0, external_python_required=False,
        installed=False, activated=False, user_database_modified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, help='Use an already sealed package; skip native/map builds.')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--receipt', type=Path)
    args = parser.parse_args()
    manifest = args.manifest
    if manifest is None:
        from sc1.native_campaign import build_plain_chk, build_all_campaigns, build_native_runtime, package_all_campaigns
        build_plain_chk.build(build_plain_chk.DEFAULT_OUTPUT, build_plain_chk.DEFAULT_RECEIPT,
                              build_plain_chk.DEFAULT_DIFFICULTY, build_plain_chk.WAVE_HEADER)
        build_all_campaigns.build()
        build_native_runtime.build()
        manifest = Path(package_all_campaigns.build()['manifest'])
    output = args.output or ROOT / 'sc1/dist' / ('SC1_Roguelike_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    record = portable_zip(manifest.resolve(), output)
    record['built_at_utc'] = datetime.now(timezone.utc).isoformat()
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(json.dumps({k: record[k] for k in ('archive', 'archive_sha256', 'archive_bytes', 'installed')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
