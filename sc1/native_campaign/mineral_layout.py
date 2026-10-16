"""Conservative, deterministic mineral-row cleanup for ordinary campaign CHKs.

Only the x/y words of existing mineral records (176..178) may change.  This is
an offline placement check, not a mining, pathfinder, or visual playtest.  Tidy
templates are accepted only if they improve aligned neighbouring pairs without
changing local worker-size free-space connectivity or hiding an approachable
mineral.  Crowded, scripted, narrow, and already orderly groups are left alone.
"""
from __future__ import annotations

from collections import deque
from functools import lru_cache
import hashlib
import math
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
SOURCE_ROOT = HERE.parent / "campaign_sources/raw"
MINERALS = frozenset((176, 177, 178))
HEADQUARTERS = frozenset((106, 131, 132, 133, 154))
TILESETS = ("badlands", "platform", "install", "ashworld", "jungle", "desert", "ice", "twilight")
MAX_DISPLACEMENT = 64
MAX_HQ_DISTANCE_CHANGE = 32
MAX_CENTER_SHIFT = 24
WORKER_RADIUS = 12
ALGORITHM_VERSION = "mineral_rows_v3_open_rows_depot_guard"


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _records(chk):
    raw = chk.getsection("UNIT")
    if len(raw) % 36:
        raise ValueError("Malformed UNIT section")
    return [raw[i:i + 36] for i in range(0, len(raw), 36)]


def _info(record):
    return (*struct.unpack_from("<HHH", record, 4), record[16])


@lru_cache(maxsize=1)
def load_unit_geometry():
    """Read stock, pinned units.dat placement and collision boxes (36 and 38).

    The existing vanilla DAT decoder also verifies the complete source hash.
    Importing it here avoids any dependency on the campaign map builder.
    """
    try:
        from .build_managed_dat import legacy_fields, source_bytes
    except ImportError:
        from build_managed_dat import legacy_fields, source_bytes
    raw = source_bytes("units")
    fields = legacy_fields("units", raw)
    geometry = {}
    for unit in range(228):
        width, height = struct.unpack_from("<2H", fields[36][1], unit * 4)
        left, top, right, bottom = struct.unpack_from("<4H", fields[38][1], unit * 8)
        # Placement boxes reserve the complete foundation of a building or
        # resource, even when its engine collision dimensions are smaller.
        if unit >= 106:
            left = max(left, width // 2)
            top = max(top, height // 2)
            right = max(right + 1, width - width // 2)
            bottom = max(bottom + 1, height - height // 2)
        else:
            right += 1
            bottom += 1
        geometry[unit] = (left, top, right, bottom)
    return geometry, {"path": "sc1/campaign_sources/raw/arr/units.dat", "sha256": _sha(raw),
                      "placement_field": 36, "collision_field": 38,
                      "schema": "sc1/native_campaign/dat_sources/tatti3/GameData/LegacyDatDecl.cs"}


@lru_cache(maxsize=8)
def _tileset_data(era):
    name = TILESETS[era]
    cv5 = (SOURCE_ROOT / "TileSet" / f"{name}.cv5").read_bytes()
    vf4 = (SOURCE_ROOT / "TileSet" / f"{name}.vf4").read_bytes()
    return cv5, vf4, {"tileset": name, "cv5_sha256": _sha(cv5), "vf4_sha256": _sha(vf4),
                      "resolution_pixels": 8, "full_placement_footprint_checked": True,
                      "native_pathfinder_verified": False}


def load_terrain(chk):
    """Return raw (not pre-eroded) eight-pixel CV5/VF4 walk flags and pins."""
    width, height = struct.unpack("<HH", chk.getsection("DIM "))
    era = struct.unpack("<H", chk.getsection("ERA "))[0] & 7
    cv5, vf4, proof = _tileset_data(era)
    raw_tiles = chk.getsection("MTXM")
    if len(raw_tiles) != width * height * 2:
        raise ValueError("Malformed MTXM section")
    tiles = struct.unpack("<" + "H" * (width * height), raw_tiles)
    walk = [bytearray(width * 4) for _ in range(height * 4)]
    cache = {}
    for y in range(height):
        for x in range(width):
            tile = tiles[y * width + x]
            if tile not in cache:
                mega = struct.unpack_from("<H", cv5, (tile >> 4) * 52 + 20 + (tile & 15) * 2)[0]
                cache[tile] = tuple(int(bool(f & 1)) for f in struct.unpack_from("<16H", vf4, mega * 32))
            flags = cache[tile]
            for sy in range(4):
                walk[y * 4 + sy][x * 4:x * 4 + 4] = bytes(flags[sy * 4:sy * 4 + 4])
    return walk, dict(proof)


def _rect(x, y, unit, geometry, inflate=0):
    l, t, r, b = geometry[unit]
    return x - l - inflate, y - t - inflate, x + r + inflate, y + b + inflate


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _walkable_rect(walk, rect):
    left, top, right, bottom = rect
    if left < 0 or top < 0 or right > len(walk[0]) * 8 or bottom > len(walk) * 8:
        return False
    return all(all(walk[y][left // 8:(right + 7) // 8])
               for y in range(top // 8, (bottom + 7) // 8))


def _clusters(info):
    remaining = {i for i, (_, _, unit, _) in enumerate(info) if unit in MINERALS}
    groups = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        group, queue = [first], [first]
        for index in queue:
            x, y = info[index][:2]
            neighbours = sorted(i for i in remaining if (info[i][0] - x) ** 2 + (info[i][1] - y) ** 2 <= 128 ** 2)
            remaining.difference_update(neighbours)
            group.extend(neighbours)
            queue.extend(neighbours)
        groups.append(sorted(group))
    return groups


def aligned_pairs(points):
    """Number of contiguous, straight mineral neighbours on the original grid."""
    cells = set(points)
    return sum((x + 64, y) in cells for x, y in cells) + sum((x, y + 32) in cells for x, y in cells)


def _balanced_counts(count, rows, rounded):
    sizes = [count // rows] * rows
    order = sorted(range(rows), key=lambda i: (abs(i - (rows - 1) / 2), i)) if rounded else list(range(rows))
    for i in order[:count % rows]:
        sizes[i] += 1
    return sizes


def _templates(points):
    """Small straight/staggered rows near the existing centre, without rotation."""
    count = len(points)
    cx = sum(p[0] for p in points) / count
    cy = sum(p[1] for p in points) / count
    seen = set()
    # Horizontal rows and vertical short columns use the actual 64x32 mineral
    # footprint.  A 64px row gap leaves room for a worker between the rows.
    for vertical in (False, True):
        for rows in range(1, min(2, count // 2) + 1):
            for rounded in (True, False):
                sizes = _balanced_counts(count, rows, rounded)
                for row_step in ((96, 128) if vertical else (64,)):
                    for stagger in (False, True):
                        offsets = []
                        for row, size in enumerate(sizes):
                            shift = (row % 2) * 32 if stagger else 0
                            for column in range(size):
                                along = column * (32 if vertical else 64) + shift
                                across = row * row_step
                                offsets.append((across, along) if vertical else (along, across))
                        ox = sum(p[0] for p in offsets) / count
                        oy = sum(p[1] for p in offsets) / count
                        tx = round((cx - ox) / 32) * 32
                        ty = round((cy - oy - 16) / 32) * 32 + 16
                        for dx, dy in ((0, 0), (-32, 0), (32, 0), (0, -32), (0, 32)):
                            target = tuple(sorted((x + tx + dx, y + ty + dy) for x, y in offsets))
                            if target in seen:
                                continue
                            seen.add(target)
                            yield target, {"kind": "short_columns" if vertical else "short_rows", "rows": rows,
                                           "row_spacing_pixels": row_step, "staggered": stagger, "row_lengths": sizes}


def _assignment(points, targets):
    """Deterministic minimum squared displacement matching, Hungarian method."""
    n = len(points)
    huge = 10 ** 9
    costs = [[((x - a) ** 2 + (y - b) ** 2) if (x - a) ** 2 + (y - b) ** 2 <= MAX_DISPLACEMENT ** 2 else huge
              for a, b in targets] for x, y in points]
    if any(min(row) == huge for row in costs):
        return None
    u, v, p, way = [0] * (n + 1), [0] * (n + 1), [0] * (n + 1), [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minimum, used = [huge * 10] * (n + 1), [False] * (n + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], huge * 10, 0
            for j in range(1, n + 1):
                if not used[j]:
                    current = costs[i0 - 1][j - 1] - u[i0] - v[j]
                    if current < minimum[j]:
                        minimum[j], way[j] = current, j0
                    if minimum[j] < delta:
                        delta, j1 = minimum[j], j
            for j in range(n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minimum[j] -= delta
            j0 = j1
            if not p[j0]:
                break
        while True:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
            if not j0:
                break
    result = [None] * n
    total = 0
    for j in range(1, n + 1):
        if costs[p[j] - 1][j - 1] >= huge:
            return None
        result[p[j] - 1] = targets[j - 1]
        total += costs[p[j] - 1][j - 1]
    return result, total


def _grid_components(walk, info, bounds, geometry):
    left, top, right, bottom = bounds
    width, height = right - left, bottom - top
    free = [bytearray(width) for _ in range(height)]
    # A 24px worker must fit on the terrain too.  Samples at 8px resolution
    # deliberately round the worker clearance outwards.
    for yy in range(height):
        y = top + yy
        for xx in range(width):
            x = left + xx
            if 1 <= x < len(walk[0]) - 1 and 1 <= y < len(walk) - 1:
                free[yy][xx] = int(all(walk[cy][x - 1:x + 2] == b"\x01\x01\x01" for cy in range(y - 1, y + 2)))
    for x, y, unit, _ in info:
        if unit == 214 or unit < 106:
            continue
        rect = _rect(x, y, unit, geometry, WORKER_RADIUS)
        if rect[2] <= left * 8 or rect[0] >= right * 8 or rect[3] <= top * 8 or rect[1] >= bottom * 8:
            continue
        x1, y1 = max(0, rect[0] // 8 - left), max(0, rect[1] // 8 - top)
        x2, y2 = min(width, (rect[2] + 7) // 8 - left), min(height, (rect[3] + 7) // 8 - top)
        for yy in range(y1, y2):
            free[yy][x1:x2] = bytes(x2 - x1)
    labels = [[0] * width for _ in range(height)]
    component, sizes, boundary = 0, {}, set()
    for y in range(height):
        for x in range(width):
            if not free[y][x] or labels[y][x]:
                continue
            component += 1
            labels[y][x] = component
            queue = deque(((x, y),))
            size = 0
            while queue:
                xx, yy = queue.popleft()
                size += 1
                if xx in (0, width - 1) or yy in (0, height - 1):
                    boundary.add(component)
                for nx, ny in ((xx + 1, yy), (xx - 1, yy), (xx, yy + 1), (xx, yy - 1)):
                    if 0 <= nx < width and 0 <= ny < height and free[ny][nx] and not labels[ny][nx]:
                        labels[ny][nx] = component
                        queue.append((nx, ny))
            sizes[component] = size
    return labels, sizes, boundary


def _approach_components(item, labels, bounds, geometry):
    x, y, unit, _ = item
    left, top, _, _ = bounds
    a, b, c, d = _rect(x, y, unit, geometry, WORKER_RADIUS)
    # Adjacent free cells immediately outside the inflated harvest footprint.
    cells = [(xx, b // 8 - 1) for xx in range(a // 8, (c + 7) // 8)]
    cells += [(xx, (d + 7) // 8) for xx in range(a // 8, (c + 7) // 8)]
    cells += [(a // 8 - 1, yy) for yy in range(b // 8, (d + 7) // 8)]
    cells += [((c + 7) // 8, yy) for yy in range(b // 8, (d + 7) // 8)]
    return {labels[yy - top][xx - left] for xx, yy in cells
            if 0 <= yy - top < len(labels) and 0 <= xx - left < len(labels[0]) and labels[yy - top][xx - left]}


def _outer_approach_edges(item, labels, bounds, geometry, exterior):
    """Count exterior-connected worker approach cells on each mineral side."""
    x, y, unit, _ = item
    left, top, _, _ = bounds
    a, b, c, d = _rect(x, y, unit, geometry, WORKER_RADIUS)
    sides = [[(xx, b // 8 - 1) for xx in range(a // 8, (c + 7) // 8)],
             [(xx, (d + 7) // 8) for xx in range(a // 8, (c + 7) // 8)],
             [(a // 8 - 1, yy) for yy in range(b // 8, (d + 7) // 8)],
             [((c + 7) // 8, yy) for yy in range(b // 8, (d + 7) // 8)]]
    return [sum(0 <= yy - top < len(labels) and 0 <= xx - left < len(labels[0])
                and labels[yy - top][xx - left] in exterior for xx, yy in side)
            for side in sides]


def _topology_check(before, after, indices, walk, geometry):
    selected = [before[i][:2] for i in indices] + [after[i][:2] for i in indices]
    bounds = (max(0, min(x for x, y in selected) // 8 - 24),
              max(0, min(y for x, y in selected) // 8 - 24),
              min(len(walk[0]), max(x for x, y in selected) // 8 + 25),
              min(len(walk), max(y for x, y in selected) // 8 + 25))
    old, old_sizes, old_boundary = _grid_components(walk, before, bounds, geometry)
    new, new_sizes, new_boundary = _grid_components(walk, after, bounds, geometry)
    forward, backward = {}, {}
    for arow, brow in zip(old, new):
        for a, b in zip(arow, brow):
            if a and b:
                forward.setdefault(a, set()).add(b)
                backward.setdefault(b, set()).add(a)
    if set(forward) != set(old_sizes) or set(backward) != set(new_sizes):
        return False, {"reason": "isolated_free_space_changed"}
    if any(len(v) != 1 for v in forward.values()) or any(len(v) != 1 for v in backward.values()):
        return False, {"reason": "worker_route_connectivity_changed"}
    mapping = {a: next(iter(v)) for a, v in forward.items()}
    if {mapping[a] for a in old_boundary} != new_boundary:
        return False, {"reason": "local_boundary_access_changed"}
    for i in indices:
        original = _approach_components(before[i], old, bounds, geometry)
        candidate = _approach_components(after[i], new, bounds, geometry)
        if not {mapping[c] for c in original} <= candidate:
            return False, {"reason": "mineral_harvest_access_changed", "unit_index": i}
        old_edges = _outer_approach_edges(before[i], old, bounds, geometry, old_boundary)
        new_edges = _outer_approach_edges(after[i], new, bounds, geometry, new_boundary)
        if sum(new_edges) < sum(old_edges) or sum(bool(n) for n in new_edges) < sum(bool(n) for n in old_edges):
            return False, {"reason": "exterior_mineral_approach_reduced", "unit_index": i}
    return True, {"worker_clearance_pixels": WORKER_RADIUS * 2,
                  "local_bounds_8px": list(bounds), "before_components": len(old_sizes),
                  "after_components": len(new_sizes), "component_correspondence_preserved": True,
                  "original_mineral_approach_components_preserved": True,
                  "exterior_worker_approach_edge_cells_and_open_sides_not_reduced_per_mineral": True,
                  "native_pathfinder_verified": False}


def _potential_mining_gate(info, indices, walk, geometry):
    """Freeze a mineral group if mining it away could join existing regions."""
    points = [info[i][:2] for i in indices]
    bounds = (max(0, min(x for x, y in points) // 8 - 24),
              max(0, min(y for x, y in points) // 8 - 24),
              min(len(walk[0]), max(x for x, y in points) // 8 + 25),
              min(len(walk), max(y for x, y in points) // 8 + 25))
    original, _, _ = _grid_components(walk, info, bounds, geometry)
    removed = list(info)
    for i in indices:
        removed[i] = (*removed[i][:2], 214, removed[i][3])
    without, _, _ = _grid_components(walk, removed, bounds, geometry)
    joined = {}
    for old_row, new_row in zip(original, without):
        for a, b in zip(old_row, new_row):
            if a and b:
                joined.setdefault(b, set()).add(a)
                if len(joined[b]) > 1:
                    return True
    return False


def _valid_geometry(before, after, indices, walk, geometry, reserved_points=()):
    changed = [i for i in indices if before[i][:2] != after[i][:2]]
    fixed_rects = [(i, _rect(x, y, u, geometry)) for i, (x, y, u, p) in enumerate(after) if u != 214]
    for i in changed:
        x, y, unit, owner = after[i]
        bx, by = before[i][:2]
        if (x - bx) ** 2 + (y - by) ** 2 > MAX_DISPLACEMENT ** 2:
            return False, "displacement"
        if any((x - a) ** 2 + (y - b) ** 2 < 40 ** 2 for a, b in reserved_points):
            return False, "reserved_wave_cell"
        if not _walkable_rect(walk, _rect(x, y, unit, geometry)):
            return False, "terrain_footprint"
        rect = _rect(x, y, unit, geometry)
        if any(j != i and _overlap(rect, other) for j, other in fixed_rects):
            return False, "occupied_footprint"
        headquarters = [(hx, hy) for hx, hy, hu, hp in before if hu in HEADQUARTERS
                        and (hx - bx) ** 2 + (hy - by) ** 2 <= 960 ** 2]
        if headquarters:
            anchor = min(headquarters, key=lambda p: ((p[0] - bx) ** 2 + (p[1] - by) ** 2, p))
            if abs(math.dist((x, y), anchor) - math.dist((bx, by), anchor)) > MAX_HQ_DISTANCE_CHANGE:
                return False, "headquarters_distance"
    return True, None


def _fallback_protected(chk, info):
    """Fail closed on original triggers directly selecting minerals/resources.

    The broader campaign trigger audit can add protected indices.  Generic
    Any Unit selectors can include resources, so retain location membership for
    all referenced locations even when no direct resource selector appears.
    """
    direct = set()
    locations = set()
    try:
        raw = chk.getsection("TRIG")
        regions = chk.getsection("MRGN")
    except KeyError:
        return direct, locations
    if len(raw) % 2400 or len(regions) % 20:
        raise ValueError("Malformed original trigger/location sections")
    for offset in range(0, len(raw), 2400):
        trigger = raw[offset:offset + 2400]
        for index in range(16):
            cond = trigger[index * 20:(index + 1) * 20]
            if not cond[15] or cond[17] & 2:
                continue
            unit = struct.unpack_from("<H", cond, 12)[0]
            loc = struct.unpack_from("<I", cond)[0]
            if cond[15] in (3, 7, 16, 17) and loc:
                locations.add(loc)
            if unit in MINERALS and cond[15] in (2, 3, 7, 15, 16, 17):
                if cond[15] in (2, 15):
                    direct.update(i for i, (_, _, u, _) in enumerate(info) if u == unit)
                elif 0 < loc <= len(regions) // 20:
                    l, t, r, b = struct.unpack_from("<4I", regions, (loc - 1) * 20)
                    direct.update(i for i, (x, y, u, _) in enumerate(info) if u == unit and l <= x <= r and t <= y <= b)
        for index in range(64):
            action = trigger[320 + index * 32:352 + index * 32]
            kind = action[26]
            if not kind or action[28] & 2:
                continue
            loc = struct.unpack_from("<I", action)[0]
            if kind in (10, 11, 16, 23, 25, 28, 38, 39, 43, 44, 46, 48, 49, 50, 51, 52, 53) and loc:
                locations.add(loc)
            unit = struct.unpack_from("<H", action, 24)[0]
            if unit in MINERALS and kind in (23, 25, 43, 44, 46, 48, 49, 50, 51, 52, 53):
                direct.update(i for i, (_, _, u, _) in enumerate(info) if u == unit)
    return direct, locations


def _same_location_membership(chk, before, after, indices, locations, geometry):
    if not locations:
        return True
    regions = chk.getsection("MRGN")
    rects = sorted({struct.unpack_from("<4I", regions, (loc - 1) * 20) for loc in locations
                    if 0 < loc <= len(regions) // 20})
    def signature(item, region):
        x, y, unit, _ = item
        l, t, r, b = region
        l, r = min(l, r), max(l, r)
        t, b = min(t, b), max(t, b)
        a, c, d, e = _rect(x, y, unit, geometry)
        return (l <= x <= r and t <= y <= b,
                l < d and a < r and t < e and c < b,
                l <= a and t <= c and d <= r and e <= b)
    return all(signature(before[i], rect) == signature(after[i], rect)
               for i in indices if before[i][:2] != after[i][:2] for rect in rects)


def plan_layout(chk, row=None, *, protected_indices=(), protection_report=None, terrain=None, reserved_points=()):
    """Return an audit and proposed mineral coordinates, without mutating CHK.

    ``terrain`` may be the (raw walk grid, evidence dict) returned by this
    module's load_terrain.  The map builder's 24px pre-eroded grid is not raw
    terrain and must not be passed here.
    """
    records = _records(chk)
    original = list(map(_info, records))
    info = list(original)
    try:
        from . import resource_depot_placement
    except ImportError:
        import resource_depot_placement
    depot_guard = resource_depot_placement.prepare_guard(chk, original)
    geometry, dat_proof = load_unit_geometry()
    walk, terrain_proof = load_terrain(chk) if terrain is None else terrain
    protected, used_locations = _fallback_protected(chk, info)
    # Even currently unused locations can be moved or used by an AI script.
    # Preserve point, footprint-intersection, and containment membership for
    # every original MRGN rectangle, not merely the obvious trigger selectors.
    try:
        used_locations.update(range(1, len(chk.getsection("MRGN")) // 20 + 1))
    except KeyError:
        pass
    protected.update(protected_indices)
    clusters, moves = [], []
    for indices in _clusters(info):
        points = [info[i][:2] for i in indices]
        result = {"unit_indices": indices, "mineral_count": len(indices), "before_aligned_pairs": aligned_pairs(points),
                  "changed": False}
        clusters.append(result)
        if set(indices) & protected:
            result["reason"] = "protected_original_script_or_resource"
            continue
        if any(struct.unpack_from("<I", records[i], 20)[0] <= 100 for i in indices):
            result["reason"] = "potential_special_or_mine_out_resource"
            protected.update(indices)
            continue
        if not 3 <= len(indices) <= 10:
            result["reason"] = "group_size_outside_conservative_range"
            continue
        if _potential_mining_gate(info, indices, walk, geometry):
            result["reason"] = "potential_mining_route_gate"
            protected.update(indices)
            continue
        candidates = []
        cx, cy = sum(x for x, y in points) / len(points), sum(y for x, y in points) / len(points)
        for target, template in _templates(points):
            score = aligned_pairs(target)
            if score <= result["before_aligned_pairs"] or score < result["before_aligned_pairs"] * 1.2:
                continue
            tx, ty = sum(x for x, y in target) / len(target), sum(y for x, y in target) / len(target)
            if math.hypot(tx - cx, ty - cy) > MAX_CENTER_SHIFT:
                continue
            assignment = _assignment(points, target)
            if assignment is None:
                continue
            chosen, cost = assignment
            candidate = list(info)
            for index, (x, y) in zip(indices, chosen):
                candidate[index] = (x, y, *info[index][2:])
            if not _same_location_membership(chk, info, candidate, indices, used_locations, geometry):
                continue
            okay, reason = _valid_geometry(info, candidate, indices, walk, geometry, reserved_points)
            if okay:
                # Minimize movement first, then reward the straighter rows.
                # A >=20% improvement is mandatory before displacement matters.
                candidates.append((cost, -score, tuple(chosen), template, candidate))
        candidates.sort(key=lambda c: c[:3])
        rejected = {}
        for cost, negative_score, chosen, template, candidate in candidates:
            depot_okay, depot_proof = depot_guard.check(candidate)
            if not depot_okay:
                rejected["original_resource_depot_position_blocked"] = rejected.get("original_resource_depot_position_blocked", 0) + 1
                continue
            okay, proof = _topology_check(info, candidate, indices, walk, geometry)
            if not okay:
                rejected[proof["reason"]] = rejected.get(proof["reason"], 0) + 1
                continue
            result.update(changed=True, after_aligned_pairs=-negative_score, template=template,
                          squared_displacement_total=cost, topology=proof, resource_depot_placement=depot_proof)
            for index in indices:
                if info[index][:2] != candidate[index][:2]:
                    moves.append({"unit_index": index, "unit_type": info[index][2], "owner": info[index][3],
                                  "from": list(info[index][:2]), "to": list(candidate[index][:2]),
                                  "displacement_pixels": round(math.dist(info[index][:2], candidate[index][:2]), 6)})
            info = candidate
            break
        if not result["changed"]:
            result["reason"] = "no_safer_improved_short_row_template"
            if rejected:
                result["topology_rejections"] = rejected
    raw = bytearray(chk.getsection("UNIT"))
    for move in moves:
        struct.pack_into("<HH", raw, move["unit_index"] * 36 + 4, *move["to"])
    return {"schema_version": 1, "algorithm": ALGORITHM_VERSION, "mission_id": (row or {}).get("mission_id"),
            "source_unit_sha256": _sha(chk.getsection("UNIT")), "output_unit_sha256": _sha(raw),
            "changed": bool(moves), "mineral_count": sum(item[2] in MINERALS for item in original),
            "moved_count": len(moves), "moved_indices": sorted(m["unit_index"] for m in moves), "moves": moves,
            "cluster_count": len(clusters), "changed_cluster_count": sum(c["changed"] for c in clusters),
            "protected_indices": sorted(protected), "protection_report": protection_report,
            "reserved_points": [list(point) for point in sorted(set(map(tuple, reserved_points)))],
            "limits": {"max_displacement_pixels": MAX_DISPLACEMENT,
                       "max_nearest_headquarters_distance_change_pixels": MAX_HQ_DISTANCE_CHANGE,
                       "max_group_center_shift_pixels": MAX_CENTER_SHIFT,
                       "only_UNIT_xy_words_changed": True, "resource_count_type_owner_amount_preserved": True,
                       "original_locations_and_trigger_bytes_preserved": True,
                       "native_mining_pathfinder_or_visual_verified": False},
            "resource_depot_placement": {**depot_guard.check(info)[1], "rule_evidence": resource_depot_placement.rule_evidence()},
            "unit_geometry": dat_proof, "terrain": terrain_proof, "clusters": clusters}


def apply_layout(chk, row=None, *, protected_indices=(), protection_report=None, terrain=None, reserved_points=()):
    report = plan_layout(chk, row, protected_indices=protected_indices,
                         protection_report=protection_report, terrain=terrain, reserved_points=reserved_points)
    raw = bytearray(chk.getsection("UNIT"))
    for move in report["moves"]:
        struct.pack_into("<HH", raw, move["unit_index"] * 36 + 4, *move["to"])
    chk.setsection("UNIT", raw)
    return report


def verify_only_mineral_coordinates(before, after):
    """Reject every byte difference other than x/y of an existing mineral."""
    if len(before) != len(after) or len(before) % 36:
        raise ValueError("Mineral relocation changed UNIT record count")
    changed = []
    for i in range(len(before) // 36):
        a, b = before[i * 36:(i + 1) * 36], after[i * 36:(i + 1) * 36]
        if a == b:
            continue
        if struct.unpack_from("<H", a, 8)[0] not in MINERALS or a[:4] != b[:4] or a[8:] != b[8:]:
            raise ValueError(f"Unaudited UNIT record change at index {i}")
        changed.append(i)
    return changed


def verify_layout(original, edited, row, report, *, protected_indices=(), protection_report=None, terrain=None, reserved_points=()):
    """Check exact deterministic relocation against a pre-layout CHK snapshot."""
    expected = plan_layout(original, row, protected_indices=protected_indices,
                           protection_report=protection_report, terrain=terrain, reserved_points=reserved_points)
    if expected != report:
        raise ValueError("Mineral layout report does not match deterministic recomputation")
    wanted = bytearray(original.getsection("UNIT"))
    for move in expected["moves"]:
        struct.pack_into("<HH", wanted, move["unit_index"] * 36 + 4, *move["to"])
    if edited.getsection("UNIT") != bytes(wanted):
        raise ValueError("UNIT changes exceed the audited mineral coordinates")
    verify_only_mineral_coordinates(original.getsection("UNIT"), edited.getsection("UNIT"))
    if original.order != edited.order or any(original.sections[name] != edited.sections[name]
                                             for name in original.order if name != b"UNIT"):
        raise ValueError("Mineral layout altered another CHK section")
    return {"passed": True, "deterministic_recomputed": True, "moved_count": expected["moved_count"],
            "only_mineral_coordinates_changed": True, "native_mining_pathfinder_or_visual_verified": False}
