"""Reserve a small choice area on inspected, connected Terran01 terrain.

This helper changes only six previously empty extended locations. It never
creates units in the CHK, changes an original unit or accesses a game process.
The runtime creates and removes its own civilian and four neutral beacons.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'campaign_sources/raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk'
sys.path.insert(0, str(ROOT / 'campaign_sources'))
from analyze_terran01_paths import load_grid

SELECTOR_UNIT = 15  # Official eudplib EncodeUnit('Terran Civilian').
BEACON_UNIT = 195  # Official eudplib EncodeUnit('Terran Beacon').
LOCATIONS = {'arena': 71, 'home': 72, 'slots': [73, 74, 75, 76]}


def _sections(raw):
    sections = {}
    offset = 0
    while offset < len(raw):
        name = raw[offset:offset + 4]
        length = struct.unpack_from('<I', raw, offset + 4)[0]
        sections[name] = raw[offset + 8:offset + 8 + length]
        offset += 8 + length
    assert offset == len(raw)
    return sections


def _units(data):
    assert len(data) % 36 == 0
    return [(struct.unpack_from('<HHH', data, i + 4), data[i + 16])
            for i in range(0, len(data), 36)]


def _footprint(unit):
    if unit == 106:
        return 64, 48
    if unit == 109:
        return 48, 32
    if unit == 188:
        return 64, 32
    if unit in (176, 177, 178):
        return 32, 16
    return 16, 16


def _connected(clear, point):
    start = point[0] // 8, point[1] // 8
    assert clear[start[1]][start[0]], 'Exact original starting point must be walkable'
    seen = {start}
    pending = deque([start])
    while pending:
        x, y = pending.popleft()
        for a, b in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= b < len(clear) and 0 <= a < len(clear[0]) and clear[b][a] and (a, b) not in seen:
                seen.add((a, b))
                pending.append((a, b))
    return seen


def make_config(chk):
    """Called after legacy conversion/difficulty additions by the map builder."""
    source = _sections(SOURCE.read_bytes())
    original = source[b'UNIT']
    current = chk.getsection('UNIT')
    assert len(original) == 49 * 36
    assert current[:len(original)] == original, 'Original49 unit records must remain byte-identical'
    original_info, current_info = _units(original), _units(current)
    assert not any(unit in (SELECTOR_UNIT, BEACON_UNIT) for (_, _, unit), _ in original_info)
    assert not any(unit in (SELECTOR_UNIT, BEACON_UNIT) for (_, _, unit), _ in current_info), \
        'Choice unit types must be exclusive to the runtime selector'
    assert chk.getsection('MTXM') == source[b'MTXM']
    assert chk.getsection('DIM ') == source[b'DIM '] == struct.pack('<HH', 64, 64)
    _, clear = load_grid()

    # Reserve a 24px gap around the known original buildings/resources before
    # checking connectivity, including the difficulty helper's new geyser.
    for (x, y, unit), _ in current_info:
        if unit not in (106, 109, 176, 177, 178, 188):
            continue
        hx, hy = _footprint(unit)
        for yy in range(max(0, (y - hy - 24) // 8), min(len(clear), (y + hy + 24) // 8 + 1)):
            for xx in range(max(0, (x - hx - 24) // 8), min(len(clear[0]), (x + hx + 24) // 8 + 1)):
                clear[yy][xx] = False
    connected = _connected(clear, (128, 128))

    choices = []
    for cy in range(264, 505, 16):
        for cx in range(184, 425, 16):
            slots = [[cx + dx, cy - 48] for dx in (-144, -48, 48, 144)]
            home = [cx, cy + 64]
            points = slots + [home]
            if not all((x // 8, y // 8) in connected for x, y in points):
                continue
            # The whole interior is walkable, so choosing any beacon is not
            # dependent on an accidental narrow route around terrain/objects.
            if not all(clear[y // 8][x // 8]
                       for y in range(cy - 72, cy + 89, 8)
                       for x in range(cx - 168, cx + 169, 8)):
                continue
            if any((x - ux) ** 2 + (y - uy) ** 2 < 80 ** 2
                   for x, y in points
                   for (ux, uy, unit), _ in current_info if unit != 214):
                continue
            choices.append(((cx - 232) ** 2 + (cy - 320) ** 2, cy, cx, slots, home))
    assert choices, 'No safe connected starting-area layout for four choices'
    _, cy, cx, slots, home = min(choices)
    arena = [cx - 192, cy - 96, cx + 192, cy + 112]
    rectangles = [(LOCATIONS['arena'], arena), (LOCATIONS['home'], home * 2)]
    rectangles += [(location, [x - 18, y - 18, x + 18, y + 18])
                   for location, (x, y) in zip(LOCATIONS['slots'], slots)]
    locations = bytearray(chk.getsection('MRGN'))
    assert len(locations) == 255 * 20
    for location, rectangle in rectangles:
        assert locations[(location - 1) * 20:location * 20] == bytes(20), \
            ('Choice location was already used', location)
        struct.pack_into('<4IHH', locations, (location - 1) * 20, *rectangle, 0, 0)
    chk.setsection('MRGN', locations)
    return {
        'schema_version': 1,
        'mission': 101,
        'revision': 'ingame-choices-t01-v1',
        'selector_unit': SELECTOR_UNIT,
        'selector_owner_zero_based': 1,
        'beacon_unit': BEACON_UNIT,
        'beacon_owner_zero_based': 11,
        'locations': LOCATIONS,
        'arena_rectangle': arena,
        'center': [cx, cy],
        'home': home,
        'slots_left_to_right': slots,
        'slot_capture_half_width_pixels': 18,
        'original_units_preserved': 49,
        'source_has_no_selector_types': True,
        'terrain_clearance_pixels': 24,
        'connected_after_static_building_and_resource_blocking': True,
        'minimum_original_or_added_unit_distance_pixels': 80,
        'text_refresh_ticks': 48,
        'interaction': 'Select the new civilian; right-click a beacon from left1 to right4. Curse offers use1..3.',
        'cleanup': 'Remove only the unique P2 civilian15 and P12 beacon195 types; original T01 has neither.',
        'limits': ['Offline terrain/footprint checks do not emulate native unit pathing or verify the screen layout.'],
    }
