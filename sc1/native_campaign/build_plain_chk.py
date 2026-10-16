"""Build a plain, original-format T01 CHK; never starts/opens StarCraft.

Preserves VER59/IVER10, all original IDs/audio references, 64 locations and
legacy settings. Runtime effects/choices/waves are supplied by the separate
native plugin, not an embedded EUD payload. This script uses only Python.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parent
SC1 = ROOT.parent
SOURCE = SC1 / 'campaign_sources/raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk'
SOURCE_SHA256 = '79d22b2fc00db3289528c2a70eef378d4ccf73880dcaaea36c6263145a20b381'
DEFAULT_OUTPUT = ROOT / 'build/plain_t01/scenario.chk'
DEFAULT_RECEIPT = ROOT / 'plain_chk_evidence.json'
DEFAULT_DIFFICULTY = ROOT / 'build/plain_t01/difficulty.json'
WAVE_HEADER = ROOT / 'plugin/include/wave_config.generated.h'
FINGERPRINT = b'SC1_NATIVE_T01_V1_R469_C1'
COUNTER_OWNER = 11
COUNTERS = {'growth_ready': 225, 'goal': 226, 'ack': 227}
BW_ONLY_UNITS = {34, 58, 60, 61, 62, 63, 103}
sys.path.insert(0, str(SC1 / 'tools'))
import terran01_difficulty as difficulty


def digest(data):
    return hashlib.sha256(data).hexdigest()


class CHK:
    """Strict ordinary section reader retaining original order and sections."""
    def __init__(self, raw):
        self.sections = {}
        self.order = []
        offset = 0
        while offset < len(raw):
            if len(raw) - offset < 8:
                raise ValueError('Truncated ordinary CHK header')
            name, size = struct.unpack_from('<4sI', raw, offset)
            if size & 0x80000000 or size > len(raw) - offset - 8:
                raise ValueError('Out-of-file ordinary CHK section')
            if name in self.sections:
                raise ValueError('Duplicate section is not permitted by this deterministic builder')
            self.sections[name] = raw[offset + 8:offset + 8 + size]
            self.order.append(name)
            offset += 8 + size

    def getsection(self, name):
        return self.sections[name.encode() if isinstance(name, str) else name]

    def setsection(self, name, data):
        name = name.encode() if isinstance(name, str) else name
        if name not in self.sections:
            self.order.append(name)
        self.sections[name] = bytes(data)

    def save(self):
        return b''.join(struct.pack('<4sI', name, len(self.sections[name])) + self.sections[name]
                        for name in self.order)


def strings(data):
    count = struct.unpack_from('<H', data)[0]
    header = 2 + 2 * count
    if header > len(data):
        raise ValueError('Truncated legacy STR offset table')
    offsets = struct.unpack_from('<' + 'H' * count, data, 2)
    result = []
    for offset in offsets:
        if offset < header or offset >= len(data):
            raise ValueError('Legacy STR entry offset is outside its string data')
        end = data.find(b'\0', offset)
        if end < 0:
            raise ValueError('Legacy STR entry is not null terminated')
        result.append(data[offset:end])
    return result


def append_fingerprint(data):
    original = strings(data)
    if FINGERPRINT in original:
        raise ValueError('Fingerprint already exists in original source')
    count = len(original)
    assert count < 32766 and len(data) + 2 + len(FINGERPRINT) + 1 < 65536
    offsets = struct.unpack_from('<' + 'H' * count, data, 2)
    # One new offset shifts the original data by exactly two bytes. Preserve
    # every original alias and all bytes in the string payload, including gaps.
    result = (struct.pack('<H', count + 1)
              + struct.pack('<' + 'H' * (count + 1), *[offset + 2 for offset in offsets], len(data) + 2)
              + data[2 + 2 * count:] + FINGERPRINT + b'\0')
    assert strings(result) == original + [FINGERPRINT]
    return result, count + 1


def audit_counters(chk):
    trigger = chk.getsection('TRIG')
    assert len(trigger) == 9 * 2400
    death_conditions, death_actions = [], []
    for base in range(0, len(trigger), 2400):
        for index in range(16):
            at = base + index * 20
            if trigger[at + 15] == 15:
                death_conditions.append({'trigger': base // 2400, 'condition': index,
                                         'player': struct.unpack_from('<I', trigger, at + 4)[0],
                                         'unit': struct.unpack_from('<H', trigger, at + 12)[0]})
        for index in range(64):
            at = base + 320 + index * 32
            if trigger[at + 26] == 45:
                death_actions.append({'trigger': base // 2400, 'action': index,
                                      'player': struct.unpack_from('<I', trigger, at + 16)[0],
                                      'unit': struct.unpack_from('<H', trigger, at + 24)[0]})
    # A stricter complete-source audit prevents aliases such as CurrentPlayer,
    # Force1 or AllPlayers from making an apparently unused pair unsafe.
    assert not death_conditions and not death_actions, 'Source already uses death counters'
    assert not any(difficulty.unit_info(record)[2] in COUNTERS.values()
                   for record in difficulty.records(chk.getsection('UNIT')))
    return {'owner_zero_based': COUNTER_OWNER, 'unit_ids': COUNTERS,
            'source_deaths_condition_count': 0, 'source_setdeaths_action_count': 0,
            'source_physical_reserved_unit_types_count': 0,
            'all_original_trigger_death_operations_absent': True,
            'ordinary_unit_id_range': [0, 227], 'eud_memory_addressing': False}


def _death_condition(unit):
    return struct.pack('<IIIHBBBBH', 0, COUNTER_OWNER, 1, unit, 0, 15, 0, 0, 0)


def patch_victory(chk):
    data = bytearray(chk.getsection('TRIG'))
    victories = [(base // 2400, index) for base in range(0, len(data), 2400)
                 for index in range(64) if data[base + 320 + index * 32 + 26] == 1]
    assert victories == [(1, 0)]
    offset = 2400 + 320
    before = bytes(data[offset:offset + 32])
    replacement = struct.pack('<IIIIIIHBBBBH', 0, 0, 0, 0, COUNTER_OWNER, 1,
                              COUNTERS['goal'], 45, 7, 20, 0, 0)
    data[offset:offset + 32] = replacement
    gate = bytearray(2400)
    for index, name in enumerate(('growth_ready', 'goal', 'ack')):
        gate[index * 20:(index + 1) * 20] = _death_condition(COUNTERS[name])
    gate[320:352] = struct.pack('<IIIIIIHBBBBH', 0, 0, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0)
    gate[2372 + 1] = 1  # Explicit P2, the original mission's human owner.
    chk.setsection('TRIG', data + gate)
    original_owner = list(data[2400 + 2372:2400 + 2399])
    assert original_owner[18] == 1 and sum(original_owner) == 1
    return {'original_trigger_index': 1, 'original_action_index': 0,
            'original_action_hex': before.hex(), 'replacement_action_hex': replacement.hex(),
            'only_original_trigger_patch_bytes': [offset, offset + 32],
            'original_condition_bytes_preserved': True, 'original_trigger_owners_preserved': True,
            'original_owner_index': 18, 'original_owner_name': 'Force1',
            'gate_trigger_index': 9, 'gate_owner_zero_based': 1,
            'gate_condition': 'P12 units225/226/227 each AtLeast1',
            'gate_actions': ['Victory'], 'gate_preserved': False,
            'schema_reference': 'eudplib/core/rawtrigger/constenc.py:Force1=18,AllPlayers=17'}


def _expand_rows(data, old_size, new_size):
    assert len(data) == 38 * old_size
    return b''.join(data[row * old_size:(row + 1) * old_size] + bytes(new_size - old_size)
                    for row in range(38))


def apply_difficulty(chk):
    # Use the inspected existing algorithm only in an in-memory adapter. The
    # temporary expansion sections/locations are never serialized in the result.
    temporary = CHK(chk.save())
    temporary.setsection('PUPx', _expand_rows(chk.getsection('UPGR'), 46, 61))
    temporary.setsection('PTEx', _expand_rows(chk.getsection('PTEC'), 24, 44))
    temporary.setsection('MRGN', chk.getsection('MRGN') + bytes(3820))
    config = difficulty.apply(temporary)
    for name in ('UNIT', 'OWNR', 'SIDE', 'FORC'):
        chk.setsection(name, temporary.getsection(name))

    units = tuple(unit for unit in difficulty.TERRAN_UNITS if unit not in BW_ONLY_UNITS)
    puni = bytearray(chk.getsection('PUNI'))
    for unit in units:
        puni[228 + unit] = 1
        puni[14 * 228 + unit] = 0
    chk.setsection('PUNI', puni)
    upgrades = {index: level for index, level in difficulty.TERRAN_UPGRADES.items() if index < 46}
    upgr = bytearray(chk.getsection('UPGR'))
    for index, maximum in upgrades.items():
        upgr[46 + index] = maximum
        upgr[13 * 46 + index] = 0
        upgr[27 * 46 + index] = 0
    chk.setsection('UPGR', upgr)
    technologies = tuple(index for index in difficulty.TERRAN_TECH if index < 24)
    ptec = bytearray(chk.getsection('PTEC'))
    for index in technologies:
        ptec[24 + index] = 1
        ptec[13 * 24 + index] = int(index in difficulty.INNATE_TECH)
        ptec[27 * 24 + index] = 0
    chk.setsection('PTEC', ptec)
    config['native_route'] = {
        'map_settings_format': 'VER59 original legacy fields',
        'native_wave_component': 'portable C++ WaveRuntime, no added CHK locations',
        'map_location_count': 64,
        'legacy_unlocked_unit_ids': list(units),
        'legacy_upgrade_maximums': {str(index): level for index, level in upgrades.items()},
        'legacy_available_technology_ids': list(technologies),
        'bw_unit_ids_not_changed_in_chk': sorted(BW_ONLY_UNITS),
        'bw_only_upgrade_ids_not_serialized': [index for index in difficulty.TERRAN_UPGRADES if index >= 46],
        'bw_only_technology_ids_not_serialized': [index for index in difficulty.TERRAN_TECH if index >= 24],
        'bw_original_mode_production_verified': False,
        'warning': 'Native text warning only; minimap-ping API is not supplied.',
    }
    config['unlock'] = {
        'player': 'P2', 'unit_ids': list(units),
        'upgrade_maximums': {str(index): level for index, level in upgrades.items()},
        'available_technology_ids': list(technologies),
        'innate_researched_ids': [index for index in difficulty.INNATE_TECH if index < 24],
        'researched_purchasable_techs': False, 'initial_upgrade_levels': 0,
        'normal_costs_and_prerequisites': True,
        'bw_original_mode_unlock_runtime_pending': True,
    }
    # These locations belonged to the prior embedded-EUD implementation. Native
    # code queries the same coordinates directly and must not use nonexistent
    # editor locations65..70 in the preserved64-location campaign asset.
    config['source_eud_only_locations_not_serialized'] = config.pop('locations')
    config['native_coordinate_regions'] = {'home': [896, 1504, 1408, 1952], 'target': [1056, 1600]}
    return config


def make_plain_chk(raw):
    if digest(raw) != SOURCE_SHA256:
        raise ValueError('Original T01 source hash does not match the frozen asset')
    chk = CHK(raw)
    original = dict(chk.sections)
    assert chk.getsection('VER ') == struct.pack('<H', 59)
    assert chk.getsection('IVER') == struct.pack('<H', 10)
    assert len(chk.getsection('MRGN')) == 64 * 20
    counter_audit = audit_counters(chk)
    config = apply_difficulty(chk)
    fingerprint_data, fingerprint_id = append_fingerprint(chk.getsection('STR '))
    chk.setsection('STR ', fingerprint_data)
    victory = patch_victory(chk)
    permitted = {b'UNIT', b'OWNR', b'SIDE', b'FORC', b'PUNI', b'UPGR', b'PTEC', b'STR ', b'TRIG'}
    assert chk.order == list(original)
    assert all(chk.sections[name] == value for name, value in original.items() if name not in permitted)
    assert chk.getsection('UNIT')[:len(original[b'UNIT'])] == original[b'UNIT']
    assert strings(chk.getsection('STR '))[:-1] == strings(original[b'STR '])
    assert chk.getsection('TRIG')[:2400 + 320] == original[b'TRIG'][:2400 + 320]
    assert chk.getsection('TRIG')[2400 + 352:9 * 2400] == original[b'TRIG'][2400 + 352:]
    result = chk.save()
    assert CHK(result).save() == result
    report = {
        'schema_version': 1, 'mission_id': 101,
        'status': 'plain_original_format_chk_built_native_runtime_playtest_pending',
        'source': str(SOURCE), 'source_sha256': SOURCE_SHA256,
        'sha256': digest(result), 'bytes': len(result),
        'version': 59, 'iver': 10, 'original_section_order_preserved': True,
        'original_section_tags_preserved': True, 'legacy_string_ids_preserved': True,
        'fingerprint': FINGERPRINT.decode('ascii'), 'fingerprint_string_id': fingerprint_id,
        'original_string_count': fingerprint_id - 1,
        'original_unit_records_preserved': 49, 'added_unit_records': 47,
        'original_triggers_preserved_except_victory_action': 9, 'added_triggers': 1,
        'victory': victory, 'death_counter_audit': counter_audit,
        'location_count': 64, 'locations_byte_identical': True,
        'unaltered_sections': [name.decode('ascii') for name in original if name not in permitted],
        'sections': [{'name': name.decode('ascii'), 'bytes': len(chk.sections[name]),
                      'sha256': digest(chk.sections[name])} for name in chk.order],
        'difficulty_scope': config['native_route'],
        'game_files_modified': False, 'game_process_accessed': False,
        'existing_campaign_database_accessed': False,
        'native_load_verified': False, 'native_gameplay_verified': False,
        'euddraft_called': False, 'embedded_eud_payload': False,
        'limits': ['Native runtime attachment, choices, DAT effects, waves and victory/next mission require live confirmation.',
                   'Brood War-only production/technology cannot be asserted from these legacy CHK settings.'],
    }
    return result, report, config


def wave_header(config):
    """Static typed data from the exact terrain-checked difficulty config."""
    origins = []
    for origin in config['origins']:
        assert len(origin['cells']) == 90
        cells = ',\n        '.join('{' + ', '.join(map(str, point)) + '}' for point in origin['cells'])
        origins.append('    {\n        {' + ', '.join(map(str, origin['center'])) + '},\n'
                       + '        {' + ', '.join(map(str, origin['bounds'])) + '},\n'
                       + '        {' + ', '.join(map(str, origin['guard'])) + '},\n'
                       + '        {\n        ' + cells + '\n        }\n    }')
    compositions = ', '.join('{' + ', '.join(map(str, pair)) + '}' for pair in config['wave_compositions'])
    return ('// Generated by build_plain_chk.py from terrain-checked difficulty data.\n'
            '#pragma once\n#include <cstdint>\n#include "../wave_runtime.h"\n\n'
            'namespace sc1_native { namespace wave_config {\n'
            'struct Origin { WavePoint center; WaveRect bounds; WaveRect guard; WavePoint cells[90]; };\n'
            'struct Composition { std::uint32_t lings; std::uint32_t hydras; };\n'
            'inline constexpr Origin kOrigins[4] = {\n' + ',\n'.join(origins) + '\n};\n'
            'inline constexpr Composition kWaves[7] = {' + compositions + '};\n'
            'inline constexpr WaveRect kHome = {' + ', '.join(map(str, config['native_coordinate_regions']['home'])) + '};\n'
            'inline constexpr WavePoint kTarget = {' + ', '.join(map(str, config['native_coordinate_regions']['target'])) + '};\n'
            'inline constexpr std::uint32_t kHomeGraceTicks = ' + str(config['base_arrival_grace_ticks']) + ';\n'
            'inline constexpr std::uint32_t kFirstElapsedSeconds = ' + str(config['first_elapsed_seconds']) + ';\n'
            'inline constexpr std::uint32_t kIntervalTicks = ' + str(config['interval_ticks']) + ';\n'
            'inline constexpr std::uint32_t kWarningTicks = ' + str(config['warning_ticks']) + ';\n'
            'inline constexpr std::uint32_t kRetryTicks = ' + str(config['stuck_order_interval_ticks']) + ';\n'
            '} } // namespace sc1_native::wave_config\n')


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build(output=DEFAULT_OUTPUT, receipt=DEFAULT_RECEIPT, difficulty_config=DEFAULT_DIFFICULTY,
          generated_header=WAVE_HEADER):
    output, receipt, difficulty_config, generated_header = map(Path, (output, receipt, difficulty_config, generated_header))
    for path in (output, receipt, difficulty_config, generated_header):
        if not path.resolve().is_relative_to(SC1.resolve()):
            raise ValueError('Plain CHK build outputs must stay inside sc1')
    raw, report, config = make_plain_chk(SOURCE.read_bytes())
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(raw)
    _write_json(difficulty_config, config)
    generated_header.parent.mkdir(parents=True, exist_ok=True)
    generated_header.write_text(wave_header(config), encoding='utf-8')
    report.update({'built_at_utc': datetime.now(timezone.utc).isoformat(), 'output': str(output.resolve()),
                   'difficulty_config': str(difficulty_config.resolve()),
                   'difficulty_config_sha256': digest(difficulty_config.read_bytes()),
                   'wave_generated_header': str(generated_header.resolve()),
                   'wave_generated_header_sha256': digest(generated_header.read_bytes())})
    _write_json(receipt, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument('--receipt', type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument('--difficulty-config', type=Path, default=DEFAULT_DIFFICULTY)
    parser.add_argument('--generated-header', type=Path, default=WAVE_HEADER)
    args = parser.parse_args()
    report = build(args.output, args.receipt, args.difficulty_config, args.generated_header)
    print(json.dumps({'output': report['output'], 'sha256': report['sha256'], 'version': report['version'],
                      'receipt': str(args.receipt.resolve()), 'native_load_verified': False}, indent=2))


if __name__ == '__main__':
    main()
