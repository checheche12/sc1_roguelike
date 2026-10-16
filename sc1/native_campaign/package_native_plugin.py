"""Package original-format native campaign files without starting StarCraft.

Stock controls use the exact extracted Korean T01 and keep the active mod
pointer unchanged. Native plugin packages require explicit CHK/DLL receipts.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys
import uuid

ROOT = Path(__file__).resolve().parent
SC1 = ROOT.parent
SOURCE = SC1 / 'campaign_sources/raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk'
SOURCE_HASH = '79d22b2fc00db3289528c2a70eef378d4ccf73880dcaaea36c6263145a20b381'
CATALOG_HASH = '041b43f74cb4dc0533768d59eaf202dbc1de3b08610695b792c870af8eb5d40b'
MANAGED_DAT_NAMES = {'arr/units.dat': 228, 'arr/weapons.dat': 130}
SUPPORT_DAT_NAMES = {
    'arr/flingy.dat': 209, 'arr/sprites.dat': 517, 'arr/images.dat': 999,
    'arr/upgrades.dat': 62, 'arr/techdata.dat': 45, 'arr/portdata.dat': 110,
    'arr/mapdata.dat': 65, 'arr/orders.dat': 189, 'arr/buttons.dat': 99,
}
# Tatti's stock Dat+ representation reserves 228..260 for special command
# groups. The compiled baseline remains the original 228 playable unit rows.
REQUIRED_DAT_NAMES = {**MANAGED_DAT_NAMES, **SUPPORT_DAT_NAMES,
                      'arr/units.dat': 261, 'arr/weapons.dat': 131}
REQUIRED_DAT_FIELDS = {
    'arr/units.dat': set(range(54)) | set(range(0x40, 0x56)),
    'arr/weapons.dat': set(range(24)),
    'arr/flingy.dat': set(range(7)),
    'arr/sprites.dat': set(range(6)),
    'arr/images.dat': set(range(14)),
    'arr/upgrades.dat': set(range(12)) | set(range(0x10, 0x1c)),
    'arr/techdata.dat': set(range(11)) | set(range(0x10, 0x15)),
    'arr/portdata.dat': set(range(6)),
    'arr/mapdata.dat': {0},
    'arr/orders.dat': set(range(19)) | {0x20},
    'arr/buttons.dat': set(range(10)),
}
PREFIXES = ('Locales/koKR/Assets', '', 'SD')
MISSION = 'campaign/Terran/Terran01/staredit/scenario.chk'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path)
    temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def sections(raw):
    offset = 0
    result = {}
    while offset < len(raw):
        if len(raw) - offset < 8:
            raise ValueError('Truncated section header')
        name, size = struct.unpack_from('<4sI', raw, offset)
        if size & 0x80000000 or size > len(raw) - offset - 8 or name in result:
            raise ValueError('Invalid or duplicate native CHK section')
        result[name] = raw[offset + 8:offset + 8 + size]
        offset += size + 8
    return result


def verify_plain_chk(raw):
    value = sections(raw)
    if value.get(b'VER ') != struct.pack('<H', 59) or value.get(b'IVER') != struct.pack('<H', 10):
        raise ValueError('Native package must retain original VER59/IVER10')
    if b'STRx' in value or len(value.get(b'MRGN', b'')) != 1280:
        raise ValueError('Expansion/EUD format is not allowed in this native route')
    for name, length in ((b'UNIS', 4048), (b'UPGR', 1748), (b'PTEC', 912),
                         (b'UPGS', 598), (b'TECS', 216), (b'IOWN', 12)):
        if len(value.get(name, b'')) != length:
            raise ValueError('Original format section missing or resized: ' + repr(name))
    data = value.get(b'STR ', b'')
    if len(data) < 2 or len(data) > 65535:
        raise ValueError('Invalid legacy STR length')
    count = struct.unpack_from('<H', data)[0]
    if 2 + count * 2 > len(data):
        raise ValueError('Truncated legacy STR offsets')
    for index in range(count):
        offset = struct.unpack_from('<H', data, 2 + index * 2)[0]
        if offset < 2 + count * 2 or offset >= len(data) or data.find(b'\0', offset) < 0:
            raise ValueError('Invalid legacy STR string')
    return value


def verify_dll(raw):
    if len(raw) < 256 or raw[:2] != b'MZ':
        raise ValueError('Native plugin is not a PE file')
    pe = struct.unpack_from('<I', raw, 0x3c)[0]
    if pe + 264 > len(raw) or raw[pe:pe + 4] != b'PE\0\0':
        raise ValueError('Invalid native plugin PE header')
    machine, section_count = struct.unpack_from('<HH', raw, pe + 4)
    optional_length, characteristics = struct.unpack_from('<HH', raw, pe + 20)
    optional = pe + 24
    if machine != 0x8664 or struct.unpack_from('<H', raw, optional)[0] != 0x20b or not characteristics & 0x2000:
        raise ValueError('Expected an x64 PE32+ DLL')
    section_table = optional + optional_length
    table = [struct.unpack_from('<8sIIIIIIHHI', raw, section_table + index * 40)
             for index in range(section_count)]

    def at(rva, length):
        for row in table:
            virtual_size, virtual, file_size, file_offset = row[1:5]
            if virtual <= rva and rva + length <= virtual + min(file_size, max(virtual_size, file_size)):
                offset = file_offset + rva - virtual
                if offset + length <= len(raw):
                    return offset
        raise ValueError('PE RVA is outside the file')

    export_rva, export_size = struct.unpack_from('<II', raw, optional + 112)
    if export_size < 40:
        raise ValueError('Native plugin export table is missing')
    directory = at(export_rva, 40)
    names_count = struct.unpack_from('<I', raw, directory + 24)[0]
    names_rva = struct.unpack_from('<I', raw, directory + 32)[0]
    if names_count > 10000:
        raise ValueError('Unexpected PE export table')
    names = []
    names_offset = at(names_rva, names_count * 4)
    for index in range(names_count):
        rva = struct.unpack_from('<I', raw, names_offset + index * 4)[0]
        offset = at(rva, 1)
        end = raw.find(b'\0', offset, min(len(raw), offset + 256))
        if end < 0:
            raise ValueError('Invalid PE export name')
        names.append(raw[offset:end].decode('ascii'))
    if 'samase_plugin_init' not in names:
        raise ValueError('SAMASE plugin entry point is not exported')
    return {'machine': '0x8664', 'optional_magic': '0x20b', 'dll': True, 'exports': names}


def verify_managed_dat(raw, name, *, expected_entries=None):
    """Reject missing/legacy DAT and malformed Dat+ before writing an overlay."""
    if name not in REQUIRED_DAT_NAMES or len(raw) < 16 or raw[:4] != b'Dat+':
        raise ValueError('Expected an explicit loader-required Dat+ asset')
    major, minor, entries, fields = struct.unpack_from('<HHII', raw, 4)
    expected_entries = REQUIRED_DAT_NAMES[name] if expected_entries is None else expected_entries
    if major != 1 or minor == 0 or entries != expected_entries or not 0 < fields <= 256:
        raise ValueError('Dat+ version/count differs from the frozen stock roster')
    header_end = 16 + fields * 12
    if header_end > len(raw):
        raise ValueError('Truncated Dat+ field directory')
    seen = set()
    regions = []
    for index in range(fields):
        field, flags, offset, length = struct.unpack_from('<HHII', raw, 16 + index * 12)
        if field in seen or offset < header_end or offset + length > len(raw):
            raise ValueError('Invalid Dat+ field storage')
        seen.add(field)
        if length:
            regions.append((offset, offset + length))
    regions.sort()
    if any(left[1] > right[0] for left, right in zip(regions, regions[1:])):
        raise ValueError('Overlapping Dat+ fields')
    return {'format': 'Dat+', 'major': major, 'minor': minor, 'entries': entries, 'fields': fields}


def verify_loader_dat(raw, name):
    """Final overlay must also contain fields dereferenced by the loader."""
    info = verify_managed_dat(raw, name)
    present = {struct.unpack_from('<H', raw, 16 + index * 12)[0]
               for index in range(info['fields'])}
    # Validate the full stock editor schema, including defaults beyond the
    # first fatal lookup. Checking only fields seen in earlier error logs lets
    # the next missing field reach the user on every retry.
    required = REQUIRED_DAT_FIELDS[name]
    if not required <= present:
        missing = ', '.join(hex(field) for field in sorted(required - present))
        raise ValueError(name + ': missing loader-required fields: ' + missing)
    return info


def write_package(raw, *, mode, inputs, plugin=None, activate=False):
    verify_plain_chk(raw)
    if mode not in ('stock_control', 'native_plugin'):
        raise ValueError('Unknown native package mode')
    if mode == 'stock_control' and (activate or plugin is not None):
        raise ValueError('Stock controls cannot replace the active mod or include a plugin')
    if mode == 'stock_control' and sha(raw) != SOURCE_HASH:
        raise ValueError('Stock control must use exact original T01 bytes')
    if mode == 'native_plugin' and plugin is None:
        raise ValueError('Growth/Victory gated map requires its native plugin')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
    build = ROOT / 'builds' / (mode + '_' + stamp + '_' + sha(raw)[:12])
    build.mkdir(parents=True, exist_ok=False)
    members = {(prefix + '/' if prefix else '') + MISSION: raw for prefix in PREFIXES}
    dll_meta = None
    if plugin is not None:
        dll_meta = verify_dll(plugin)
        members['samase/native_plugin.dll'] = plugin
        members['samase/plugins'] = b'samase/native_plugin.dll\n'
        dat_assets = inputs.get('managed_dat_assets', []) + inputs.get('support_dat_assets', [])
        if {entry.get('name') for entry in dat_assets} != set(REQUIRED_DAT_NAMES) or len(dat_assets) != 11:
            raise ValueError('Native growth package requires the complete 11-file Dat+ set')
        for entry in dat_assets:
            _, data = checked_file(entry['path'], entry['sha256'])
            verify_loader_dat(data, entry['name'])
            members[entry['name']] = data
    files = []
    for name, data in members.items():
        path = build / 'overlay' / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files.append({'path': path.relative_to(build).as_posix(), 'bytes': len(data), 'sha256': sha(data)})
    manifest = {'schema_version': 2, 'mode': mode,
                'status': 'prepared_native_load_pending', 'inputs': inputs,
                'campaign_slot': 'Original/Terran/Terran01', 'files': files,
                'scenario_chk_sha256': sha(raw), 'scenario_chk_bytes': len(raw),
                'original_format': True, 'ver': 59, 'iver': 10,
                'loader_sha256': read_json(ROOT / 'loader_pin.json')['sha256'],
                'loader_options': ['--log', '--no-debug'],
                'dll': dll_meta, 'in_game_choices': plugin is not None,
                'managed_dat_assets': inputs.get('managed_dat_assets', []),
                'base_managed_dat_assets': inputs.get('base_managed_dat_assets', []),
                'support_dat_assets': inputs.get('support_dat_assets', []),
                'required_dat_files': list(REQUIRED_DAT_NAMES) if plugin is not None else [],
                'choice_interface': 'native GameMenu button dialog' if plugin is not None else None,
                'choice_dialog_opener': 'automatic native Stat_F10 activation' if plugin is not None else None,
                'automatic_popup_live_verified': False,
                'choice_details': 'native CTEXT explanation panel; lower numeric choices and confirmation' if plugin is not None else None,
                'custom_menu_json': plugin is not None,
                'native_upper_text_control': plugin is not None,
                'choice_number_buttons': plugin is not None,
                'growth_protocol': 'PHC1 v1' if plugin is not None else None,
                'growth_checkpoints': ['start', 'completed Barracks', 'before original Victory']
                    if plugin is not None else [],
                'choices_per_checkpoint': {'talent': 1, 'curse': 1} if plugin is not None else None,
                'choices_per_mission': {'talent': 3, 'curse': 3} if plugin is not None else None,
                'physical_choice_units': False,
                'audio_policy': 'Keep original CASC audio and original WAV string references; no sound overrides.',
                'global_bare_chk_alias': False, 'installed_casc_modified': False,
                'native_playtest_verified': False, 'campaign_progression_verified': False,
                'game_executed_by_packager': False}
    write_json(build / 'manifest.json', manifest)
    for entry in files:
        assert sha((build / entry['path']).read_bytes()) == entry['sha256']
    pointer = {'manifest': (build / 'manifest.json').relative_to(ROOT).as_posix()}
    if mode == 'stock_control':
        write_json(ROOT / 'stock_control_build.json', pointer)
    elif activate:
        write_json(ROOT / 'current_build.json', pointer)
    return {'manifest': str(build / 'manifest.json'), 'files': len(files), 'activated': activate,
            'scenario_chk_sha256': sha(raw), 'native_playtest_verified': False}


def stock_control():
    raw = SOURCE.read_bytes()
    if sha(raw) != SOURCE_HASH:
        raise ValueError('Original extracted Korean T01 hash changed')
    return write_package(raw, mode='stock_control', inputs={'source': str(SOURCE), 'sha256': SOURCE_HASH})


def owned_file(path):
    path = Path(path).resolve()
    if not path.is_relative_to(SC1.resolve()) or not path.is_file():
        raise ValueError('Package inputs must be existing workspace files under sc1')
    return path


def checked_file(path, expected_hash):
    path = owned_file(path)
    raw = path.read_bytes()
    if sha(raw) != expected_hash:
        raise ValueError('Input changed since its build receipt: ' + str(path))
    return path, raw


def native_inputs(plain_receipt_path, dll_receipt_path):
    plain_receipt_path, dll_receipt_path = map(owned_file, (plain_receipt_path, dll_receipt_path))
    plain, dll = map(read_json, (plain_receipt_path, dll_receipt_path))
    if dll.get('growth_protocol')=='PHC1 v2' and dll.get('growth_wire_version')!=2:
        raise ValueError('Revision-five native receipt requires wire version two')
    if (dll.get('growth_protocol') not in ('PHC1 v1','PHC1 v2') or dll.get('automatic_popup') is not True
            or dll.get('custom_menu_json') is not True or dll.get('native_upper_text_control') is not True
            or dll.get('choice_number_buttons') is not True or dll.get('phase_count') != 3
            or dll.get('choices_per_phase') != {'talent': 1, 'curse': 1}):
        raise ValueError('Native DLL receipt must identify the phased automatic popup candidate')
    lifecycle = dll.get('api_lifecycle', {})
    if (lifecycle.get('factories_resolved_during_plugin_init') is not True
            or lifecycle.get('runtime_plugin_api_object_retained') is not False):
        raise ValueError('Native DLL receipt must verify initialization-only factory lifetime')
    if (plain['mission_id'], plain['version'], plain['iver'], plain['source_sha256']) != (101, 59, 10, SOURCE_HASH):
        raise ValueError('Expected the frozen original-format T01 build receipt')
    chk_path, chk = checked_file(plain['output'], plain['sha256'])
    # Compare to a fresh deterministic source transformation, without rewriting
    # the CHK, generated headers, runtime files or the active package pointer.
    if str(SC1.parent) not in sys.path:
        sys.path.insert(0, str(SC1.parent))
    from sc1.native_campaign.build_plain_chk import make_plain_chk, wave_header
    from sc1.native_campaign import build_managed_dat as dat_builder
    dat_receipt_path = owned_file(dll['managed_dat_receipt'])
    if sha(dat_receipt_path.read_bytes()) != dll['managed_dat_receipt_sha256']:
        raise ValueError('Managed DAT receipt changed after the native build')
    dat_receipt = read_json(dat_receipt_path)
    if (dat_receipt.get('stock_values_preserved') is not True
            or dat_receipt.get('requirements_preserved') is not True
            or dat_receipt.get('entry_counts') != {'units': 228, 'weapons': 130}):
        raise ValueError('Managed DAT receipt must preserve stock stats and unit requirements')
    for entry in dat_receipt['sources']:
        checked_file(entry['path'], entry['sha256'])
    offsets, requirements, _ = dat_builder.original_requirements()
    dat_assets = dat_receipt['managed_dat_assets']
    if dll.get('managed_dat_assets') != dat_assets or {item['name'] for item in dat_assets} != set(MANAGED_DAT_NAMES) or len(dat_assets) != 2:
        raise ValueError('Native DLL must pin both managed DAT assets')
    for entry in dat_assets:
        _, data = checked_file(entry['path'], entry['sha256'])
        name = Path(entry['name']).stem
        fields = dat_builder.legacy_fields(name, dat_builder.source_bytes(name))
        if name == 'units':
            fields[43] = (1, offsets)
            fields[64] = (1, requirements)
        if data != dat_builder.encode(dat_builder.SOURCES[name][0], fields):
            raise ValueError('Managed DAT differs from the preserved source transformation')
        verify_managed_dat(data, entry['name'], expected_entries=MANAGED_DAT_NAMES[entry['name']])
    # Dat+ mode is global in the pinned loader: it reads all eleven tables,
    # even though gameplay currently mutates only units and weapons.
    from sc1.native_campaign import build_support_dat as support_builder
    support_receipt_path = owned_file(ROOT / 'support_dat/support_dat_evidence.json')
    support_receipt = read_json(support_receipt_path)
    if any(support_receipt.get(key) is not True for key in (
            'stock_values_preserved', 'requirements_preserved', 'buttons_preserved')):
        raise ValueError('Support DAT receipt must preserve original values, requirements and buttons')
    for entry in support_receipt['sources']:
        checked_file(entry['path'], entry['sha256'])
    support_assets = support_receipt['support_dat_assets']
    if {entry['name'] for entry in support_assets} != set(SUPPORT_DAT_NAMES) or len(support_assets) != 9:
        raise ValueError('Support DAT receipt omits a required loader dependency')
    expected_support = support_builder.expected_assets()
    if set(expected_support) != set(SUPPORT_DAT_NAMES):
        raise ValueError('Support DAT source transformation omits a required loader dependency')
    for entry in support_assets:
        _, data = checked_file(entry['path'], entry['sha256'])
        if data != expected_support[entry['name']]:
            raise ValueError('Support DAT differs from the preserved source transformation')
        verify_managed_dat(data, entry['name'])
    # Keep the compiled runtime's original two-table receipt immutable. Final
    # assets add the stock editor defaults and reserved command-group rows;
    # integer widening preserves the original playable-unit/weapon values.
    base_dat_assets = dat_assets
    dat_assets = support_receipt['derived_managed_assets']
    expected_managed = support_builder.expected_managed_assets()
    if len(dat_assets) != 2 or {entry['name'] for entry in dat_assets} != set(MANAGED_DAT_NAMES):
        raise ValueError('Derived DAT receipt must provide both managed tables')
    for entry in dat_assets:
        baseline = next(row for row in base_dat_assets if row['name'] == entry['name'])
        if entry['base_sha256'] != baseline['sha256']:
            raise ValueError('Derived DAT does not pin the compiled baseline')
        _, data = checked_file(entry['path'], entry['sha256'])
        if data != expected_managed[entry['name']]:
            raise ValueError('Derived DAT differs from the preserved source transformation')
        verify_loader_dat(data, entry['name'])
    expected, _, config = make_plain_chk(SOURCE.read_bytes())
    if chk != expected:
        raise ValueError('Native CHK differs from the audited source transformation')
    header_path, header = checked_file(plain['wave_generated_header'], plain['wave_generated_header_sha256'])
    if header.replace(b'\r\n', b'\n') != wave_header(config).encode('utf-8'):
        raise ValueError('Wave positions differ from the exact CHK difficulty build')
    checked_file(plain['difficulty_config'], plain['difficulty_config_sha256'])
    dll_path, plugin = checked_file(dll['dll_path'], dll['dll_sha256'])
    if len(plugin) != dll['dll_bytes']:
        raise ValueError('Native DLL build length mismatch')
    catalog_path, _ = checked_file(SC1 / 'campaign/runtime_talents.json', CATALOG_HASH)
    if dll['runtime_catalog_sha256'] != CATALOG_HASH:
        raise ValueError('Native DLL and manager catalog do not match')
    required = {'native_plugin.cpp', 'mailbox_protocol.cpp', 'mailbox_protocol.h',
                'wave_runtime.cpp', 'wave_runtime.h', 'samase_api44.h', 'bw_dat_x64.h',
                'frozen_catalog.generated.h', 'wave_config.generated.h',
                'dialog_ui.cpp', 'dialog_ui.h', 'dialog_x64.h',
                'plain_panel_templates.generated.h'}
    seen = set()
    sources = []
    # The combat build also pins its generated iscript and objective guards.
    # These explicit inputs remain hash checked just like compiled headers.
    generated_inputs = {(ROOT / name).resolve() for name in (
        'build_effect_iscript.py', 'build_objective_guards.py', 'build_native_runtime.py',
        'dialog_assets/plain_panel_templates.generated.h',
        'dialog_assets/wave_timer_statfluf.ui.json',
        'iscript_effects/iscript.bin', 'iscript_effects/iscript_effects_evidence.json',
        'objective_guards_evidence.json',
    )}
    generated_inputs.add((SC1 / 'build_environment.py').resolve())
    for entry in dll['sources']:
        path, raw = checked_file(entry['path'], entry['sha256'])
        if (not path.is_relative_to((ROOT / 'plugin').resolve())
                and path not in generated_inputs):
            raise ValueError('Native DLL source is outside its plugin folder')
        seen.add(path.name)
        sources.append({'path': str(path), 'sha256': sha(raw)})
    if not required <= seen:
        raise ValueError('Native DLL receipt omits a required compiled source/header')
    verify_dll(plugin)
    inputs = {'plain_chk': str(chk_path), 'plain_chk_sha256': sha(chk),
              'plain_receipt': str(plain_receipt_path), 'plain_receipt_sha256': sha(plain_receipt_path.read_bytes()),
              'native_dll': str(dll_path), 'native_dll_sha256': sha(plugin),
              'dll_receipt': str(dll_receipt_path), 'dll_receipt_sha256': sha(dll_receipt_path.read_bytes()),
              'runtime_catalog': str(catalog_path), 'runtime_catalog_sha256': CATALOG_HASH,
              'managed_dat_receipt': str(dat_receipt_path),
              'managed_dat_receipt_sha256': sha(dat_receipt_path.read_bytes()),
              'managed_dat_assets': dat_assets,
              'base_managed_dat_assets': base_dat_assets,
              'support_dat_receipt': str(support_receipt_path),
              'support_dat_receipt_sha256': sha(support_receipt_path.read_bytes()),
              'support_dat_assets': support_assets,
              'sources': sources, 'wave_header': str(header_path),
              'implemented_talents': 17, 'implemented_curses': 3}
    return chk, plugin, inputs


def build_native(plain_receipt_path, dll_receipt_path, *, activate=False):
    chk, plugin, inputs = native_inputs(plain_receipt_path, dll_receipt_path)
    return write_package(chk, mode='native_plugin', inputs=inputs, plugin=plugin, activate=activate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('stock-control')
    build = commands.add_parser('build')
    build.add_argument('--plain-receipt', type=Path, required=True)
    build.add_argument('--dll-receipt', type=Path, required=True)
    build.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    if args.command == 'stock-control':
        print(json.dumps(stock_control(), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(build_native(args.plain_receipt, args.dll_receipt, activate=args.activate),
                         ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
