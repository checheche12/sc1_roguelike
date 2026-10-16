"""Prepare a T01 campaign-menu overlay; never launches or modifies StarCraft.

Run with sc1/vendor/eud-venv/Scripts/python.exe -B. The explicit build command
requires a freshly compiled map and its exact receipt hash. No existing map is
automatically selected. A separate fetch-loader command only downloads the
pinned binary and checks its hash/PE headers; it never executes the loader.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import struct
import sys
import urllib.request

ROOT = Path(__file__).resolve().parent
SC1 = ROOT.parent
PIN_PATH = ROOT / 'loader_pin.json'
PREFIXES = ('Locales/koKR/Assets', '', 'SD')
MISSION_PATH = 'campaign/Terran/Terran01'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify_loader(data, pin):
    if len(data) != pin['bytes'] or digest(data) != pin['sha256']:
        raise ValueError('Pinned Samase64 download hash/size mismatch')
    if data[:2] != b'MZ':
        raise ValueError('Not a Windows PE executable')
    offset = struct.unpack_from('<I', data, 0x3C)[0]
    if data[offset:offset + 4] != b'PE\0\0':
        raise ValueError('Invalid PE signature')
    if struct.unpack_from('<H', data, offset + 4)[0] != pin['pe_machine']:
        raise ValueError('Expected x64 Samase executable')
    if struct.unpack_from('<H', data, offset + 24)[0] != pin['pe_optional_magic']:
        raise ValueError('Expected PE32+ executable')


def fetch_loader():
    pin = read_json(PIN_PATH)
    destination = ROOT / pin['local_filename']
    if destination.exists():
        verify_loader(destination.read_bytes(), pin)
        return {'path': str(destination), 'already_present': True, 'executed': False}
    request = urllib.request.Request(pin['url'], headers={'User-Agent': 'SC1-native-campaign-packager'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(pin['bytes'] + 1)
    verify_loader(data, pin)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    return {'path': str(destination), 'sha256': digest(data), 'executed': False}


def safe_member(name):
    path = PurePosixPath(name.replace('\\', '/'))
    if path.is_absolute() or '..' in path.parts or ':' in str(path):
        raise ValueError('Unsafe archive member path')
    if len(path.parts) != 3 or path.parts[:2] != ('staredit', 'wav') or path.suffix.lower() != '.wav':
        raise ValueError('Only the eight mission WAV members are allowed')
    return str(path)


def campaign_chk(raw):
    """Remove only eudplib's final eight-byte editor protection header.

    Campaign assets are loose CHKs, not the MPQ reader used by UMS. Do not
    expose an out-of-file/negative section length to that loader. Everything
    before this optional tail stays at the exact same byte offset: notably the
    complete STRx trigger/data payload, version, settings and original audio
    references. No legacy conversion or pointer rewriting is attempted.
    """
    offset = 0
    sections = []
    tail = None
    while offset < len(raw):
        if len(raw) - offset < 8:
            raise ValueError('Truncated campaign CHK section header')
        name, size = struct.unpack_from('<4sI', raw, offset)
        if size > len(raw) - offset - 8:
            if name == b'ISOM' and size & 0x80000000 and len(raw) - offset == 8:
                tail = {'offset': offset, 'bytes': 8, 'tag': 'ISOM',
                        'declared_unsigned_length': size,
                        'declared_signed_length': size - (1 << 32),
                        'hex': raw[offset:].hex()}
                break
            raise ValueError('Campaign CHK section extends outside the file')
        sections.append((name, size))
        offset += 8 + size
    result = raw[:offset] if tail else raw
    # A second, strict walk must consume the entire native asset.
    end = 0
    while end < len(result):
        _, size = struct.unpack_from('<4sI', result, end)
        if size & 0x80000000 or size > len(result) - end - 8:
            raise ValueError('Invalid section length in native campaign CHK')
        end += 8 + size
    assert end == len(result)
    return result, {'normalization': 'strip_final_eudplib_editor_protection_header_only',
                    'source_bytes': len(raw), 'output_bytes': len(result),
                    'source_sha256': digest(raw), 'output_sha256': digest(result),
                    'removed_tail': tail, 'all_real_sections_byte_identical': True,
                    'payload_offsets_preserved': True,
                    'strict_section_lengths_valid': True,
                    'sections': [{'name': name.decode('ascii', 'replace'), 'bytes': size}
                                 for name, size in sections]}


def write_overlay(chk_bytes, audio, source, receipt_path, source_hash, receipt):
    """Write a new directory; preserve every actual compiled CHK section."""
    chk_bytes, normalization = campaign_chk(chk_bytes)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    destination = ROOT / 'builds' / ('terran01_' + stamp + '_' + source_hash[:12])
    destination.mkdir(parents=True, exist_ok=False)
    entries = []
    members = {'staredit/scenario.chk': chk_bytes, **audio}
    for prefix in PREFIXES:
        for member, data in members.items():
            relative = PurePosixPath(prefix) / MISSION_PATH / member
            path = destination / 'overlay' / Path(relative)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            entries.append({'path': str(path.relative_to(destination)).replace('\\', '/'),
                            'bytes': len(data), 'sha256': digest(data)})
    pin = read_json(PIN_PATH)
    loader = ROOT / pin['local_filename']
    overlay = destination / 'overlay'
    manifest = {
        'schema_version': 1, 'status': 'campaign_overlay_prepared_native_playtest_pending',
        'source_map': str(source), 'source_map_sha256': source_hash,
        'source_build_receipt': str(receipt_path), 'source_receipt_sha256': digest(receipt_path.read_bytes()),
        'source_compiler': {'euddraft': receipt['official_cli_version'], 'eudplib': receipt['eudplib_version']},
        'scenario_chk_sha256': digest(chk_bytes),
        'scenario_chk_preserved_byte_for_byte': normalization['removed_tail'] is None,
        'all_real_sections_byte_identical': True, 'chk_normalization': normalization,
        'files': entries, 'campaign_slot': 'Original/Terran/Terran01',
        'override_prefixes': list(PREFIXES), 'audio_members': sorted(audio),
        'game_files_modified': False, 'game_process_accessed': False,
        'native_playtest_verified': False, 'campaign_progression_verified': False,
        'eud_in_native_campaign_verified': False, 'original_mode_bw_units_verified': False,
        'loader_pin': str(PIN_PATH), 'loader_sha256': pin['sha256'],
        'launch_argv': [str(loader), str(overlay), '--starcraft-exe', pin['game_executable'], '--log'],
        'pack_argv_not_executed': [str(loader), str(overlay), '--pack', str(destination / 'SC1_T01_Native.exe')],
        'notes': [
            'Enter Single Player > StarCraft > Terran > Wasteland after a user-initiated loader launch.',
            'Do not use --map: that is single-player UMS and does not verify campaign-menu loading.',
            'Only the T01 asset path is replaced. Native campaign tables, mission IDs and game flags are not patched.',
            'The compiled VER206/UNIx/STRx payload is preserved; only the dangling eight-byte editor protection header is removed.',
            'Native original-mode compatibility and resolution of the reported load error still need live confirmation.',
            'SD and plain paths are documented fallback candidates. Runtime file resolution must be checked in samase.log.',
            'This overlay does not implement an in-game choice interface; that must already exist in the input map.',
        ],
    }
    write_json(destination / 'manifest.json', manifest)
    for entry in entries:
        assert digest((destination / entry['path']).read_bytes()) == entry['sha256']
    write_json(ROOT / 'current_build.json', {'manifest': str((destination / 'manifest.json').relative_to(ROOT))})
    return {'manifest': str(destination / 'manifest.json'), 'source_map_sha256': source_hash,
            'files': len(entries), 'native_playtest_verified': False, 'executed': False}


def build(source, source_hash, receipt_path):
    source, receipt_path = source.resolve(), receipt_path.resolve()
    if not source.is_relative_to(SC1) or not receipt_path.is_relative_to(SC1):
        raise ValueError('Build inputs must be workspace files under sc1')
    if digest(source.read_bytes()) != source_hash:
        raise ValueError('Source map hash does not match explicit build input')
    receipt = read_json(receipt_path)
    if receipt['sha256'] != source_hash or receipt['mission_id'] != 101:
        raise ValueError('Receipt is not for this exact T01 map')
    if (receipt['official_cli_version'], receipt['eudplib_version']) != ('0.11.0.0', '0.81.0'):
        raise ValueError('Expected the official compiler recipe')
    sys.path.insert(0, str(SC1 / 'tools'))
    from build_official_euddraft_baseline import read_chk
    from eudplib.bindings._rust import mpqapi
    chk, raw = read_chk(source)
    if chk.getsection('VER ') != struct.pack('<H', 206):
        raise ValueError('Expected compiled Remastered VER206 payload; never rewrite this field')
    if chk.getsection('OWNR')[1] != 6 or chk.getsection('SIDE')[1] != 1:
        raise ValueError('T01 must retain human P2/Terran')
    audio = {}
    archive = mpqapi.MPQ.open(str(source))
    try:
        for item in receipt['audio']:
            member = safe_member(item['archive_name'])
            data = archive.extract_file(item['archive_name'])
            if digest(data) != item['sha256']:
                raise ValueError('Compiled audio hash differs from build receipt')
            audio[member] = data
    finally:
        del archive
    if len(audio) != 8:
        raise ValueError('Expected all eight preserved T01 audio members')
    return write_overlay(raw, audio, source, receipt_path, source_hash, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('fetch-loader')
    task = commands.add_parser('build')
    task.add_argument('--source-map', type=Path, required=True)
    task.add_argument('--source-sha256', required=True)
    task.add_argument('--build-receipt', type=Path, required=True)
    args = parser.parse_args()
    result = (fetch_loader() if args.command == 'fetch-loader' else
              build(args.source_map, args.source_sha256.lower(), args.build_receipt))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
