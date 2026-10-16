"""Offline functional mineral lines and worker lanes for campaign resource fields.

The mutable surface is exactly existing mineral/geyser x/y words.  A successful
field has a resource-clear existing depot or a buildable expansion footprint and
one common worker component reaching the HQ-facing edge of every mineral.
Unused potential depot positions and inaccessible pockets need not be retained.
This checks extracted terrain and unit geometry, not native mining simulation.
"""
from __future__ import annotations

from collections import defaultdict, deque
from functools import lru_cache
from itertools import islice
import hashlib
import math
import struct

try:
    from . import mineral_layout as geometry
    from . import resource_depot_placement as depot
    from . import mining_layout_audit as mining
except ImportError:
    import mineral_layout as geometry
    import resource_depot_placement as depot
    import mining_layout_audit as mining

MINERALS = geometry.MINERALS
GEYSER = 188
MOVABLE_RESOURCES = MINERALS | {GEYSER}
HEADQUARTERS = geometry.HEADQUARTERS
MAX_DISPLACEMENT = 768
ALGORITHM_VERSION = "functional_resource_ladder_v3_joint_arc_gas"
WORKER_DIAMETER = 24
# Reviewed source expansion sites supplement the regular cardinal search at a
# diagonal cliff-side field. They still pass every construction/access guard.
REVIEWED_EXPANSION_ANCHORS = {206: ((3392, 976), (3456, 1072), (3392, 1008))}


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _snap(x, y):
    return round(x / 32) * 32, round((y - 16) / 32) * 32 + 16


def _direction(center, point):
    dx, dy = point[0] - center[0], point[1] - center[1]
    if abs(dx) > abs(dy):
        return (1 if dx >= 0 else -1, 0)
    return (0, 1 if dy >= 0 else -1)


def _bounds(points, walk, margin=24):
    return (max(0, min(x for x, y in points) // 8 - margin),
            max(0, min(y for x, y in points) // 8 - margin),
            min(len(walk[0]), max(x for x, y in points) // 8 + margin + 1),
            min(len(walk), max(y for x, y in points) // 8 + margin + 1))


def _worker_terrain(raw):
    height, width = len(raw), len(raw[0])
    clear = [bytearray(width) for _ in range(height)]
    for y in range(1, height - 1):
        a, b, c = raw[y - 1:y + 2]
        out = clear[y]
        for x in range(1, width - 1):
            out[x] = int(a[x - 1] and a[x] and a[x + 1] and b[x - 1] and b[x] and b[x + 1] and c[x - 1] and c[x] and c[x + 1])
    return clear


@lru_cache(maxsize=1)
def _worker_boxes():
    # Engine movement uses DAT dimensions, not the larger placement foundation.
    return {unit: (l, t, r + 1, b + 1) for unit, (l, t, r, b) in mining.stock_geometry()[1].items()}


def _perimeter_labels(item, labels, bounds, boxes=None):
    x, y, unit, owner = item
    left, top, _, _ = bounds
    l, t, r, b = geometry._rect(x, y, unit, _worker_boxes())
    x1, x2 = (l - 16) // 8, (r + 15) // 8
    y1, y2 = (t - 16) // 8, (b + 15) // 8
    cells = ([(xx, y1) for xx in range(x1, x2 + 1)] + [(xx, y2) for xx in range(x1, x2 + 1)]
             + [(x1, yy) for yy in range(y1, y2 + 1)] + [(x2, yy) for yy in range(y1, y2 + 1)])
    return {labels[yy - top][xx - left] for xx, yy in cells
            if 0 <= yy - top < len(labels) and 0 <= xx - left < len(labels[0]) and labels[yy - top][xx - left]}


def _components(clear, info, bounds, boxes, radius=12):
    """24px workers sampled at 8*x+4; touching a footprint is allowed."""
    left, top, right, bottom = bounds
    width, height = right - left, bottom - top
    free = [bytearray(row[left:right]) for row in clear[top:bottom]]
    for x, y, unit, owner in info:
        if unit < 106 or unit == 214:
            continue
        l, t, r, b = geometry._rect(x, y, unit, _worker_boxes())
        x1, x2 = max(0, (l - radius - 4) // 8 + 1 - left), min(width - 1, (r + radius - 5) // 8 - left)
        y1, y2 = max(0, (t - radius - 4) // 8 + 1 - top), min(height - 1, (b + radius - 5) // 8 - top)
        if x2 < x1 or y2 < y1:
            continue
        for yy in range(y1, y2 + 1):
            free[yy][x1:x2 + 1] = bytes(x2 - x1 + 1)
    labels, sizes, boundary = [[0] * width for _ in range(height)], {}, set()
    label = 0
    for y in range(height):
        for x in range(width):
            if not free[y][x] or labels[y][x]:
                continue
            label += 1
            labels[y][x] = label
            queue, size = deque(((x, y),)), 0
            while queue:
                xx, yy = queue.popleft()
                size += 1
                if xx in (0, width - 1) or yy in (0, height - 1):
                    boundary.add(label)
                for nx, ny in ((xx - 1, yy), (xx + 1, yy), (xx, yy - 1), (xx, yy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and free[ny][nx] and not labels[ny][nx]:
                        labels[ny][nx] = label
                        queue.append((nx, ny))
            sizes[label] = size
    return labels, sizes, boundary


def _army_route_ok(before, after, indices, army_walk, boxes, cache):
    """Preserve large connected army routes without preserving every old cell."""
    points = [before[i][:2] for i in indices] + [after[i][:2] for i in indices]
    bounds = _bounds(points, army_walk, 24)
    baseline = cache.setdefault("baseline", before)
    whole = (0, 0, len(army_walk[0]), len(army_walk))
    if "components" not in cache:
        cache["components"] = _components(army_walk, baseline, whole, boxes, radius=24)
    original_labels, original_sizes, _ = cache["components"]
    new, new_sizes, new_boundary = _components(army_walk, after, bounds, boxes, radius=24)
    possible = defaultdict(set)
    left, top, right, bottom = bounds
    for yy, brow in enumerate(new):
        arow = original_labels[top + yy]
        for xx, b in enumerate(brow):
            a = arow[left + xx]
            if a and b and (b in new_boundary or new_sizes[b] >= 512):
                possible[a].add(b)
    if not any(len(values) > 1 for values in possible.values()):
        return True
    old, old_sizes = original_labels, original_sizes
    new, new_sizes, _ = _components(army_walk, after, whole, boxes, radius=24)
    overlap = defaultdict(lambda: defaultdict(int))
    for arow, brow in zip(old, new):
        for a, b in zip(arow, brow):
            if a and b and old_sizes[a] >= 512 and new_sizes[b] >= 512:
                overlap[a][b] += 1
    return not any(sum(count >= 512 for count in values.values()) > 1 for values in overlap.values())


def _true_mining_gate(info, indices, walk, boxes):
    bounds = _bounds([info[i][:2] for i in indices], walk, 64)
    old, old_sizes, old_boundary = _components(walk, info, bounds, boxes)
    relevant = {label for label in old_boundary if old_sizes[label] >= 512}
    if len(relevant) < 2:
        return False
    removed = list(info)
    for i in indices:
        removed[i] = (*removed[i][:2], 214, removed[i][3])
    new, _, _ = _components(walk, removed, bounds, boxes)
    joined = defaultdict(set)
    for arow, brow in zip(old, new):
        for a, b in zip(arow, brow):
            if a in relevant and b:
                joined[b].add(a)
                if len(joined[b]) > 1:
                    # The two crop edges may reconnect outside this window.
                    # Only distinct large WHOLE-MAP regions can be a gate.
                    whole = (0, 0, len(walk[0]), len(walk))
                    labels, sizes, _ = _components(walk, info, whole, boxes)
                    adjacent = set().union(*(_perimeter_labels(info[i], labels, whole, boxes) for i in indices))
                    large = {c for c in adjacent if sizes[c] >= 512}
                    if len(large) < 2:
                        return False
                    labels_removed, _, _ = _components(walk, removed, whole, boxes)
                    merged = defaultdict(set)
                    for xrow, yrow in zip(labels, labels_removed):
                        for x, y in zip(xrow, yrow):
                            if x in large and y:
                                merged[y].add(x)
                                if len(merged[y]) > 1:
                                    return True
                    return False
    return False


def _critical_locations(chk, info):
    """Only selectors that can actually select neutral resources constrain XY."""
    protected, locations = set(), set()
    try:
        raw, regions = chk.getsection("TRIG"), chk.getsection("MRGN")
    except KeyError:
        return protected, locations
    for start in range(0, len(raw), 2400):
        trigger = raw[start:start + 2400]
        for ci in range(16):
            c = trigger[ci * 20:ci * 20 + 20]
            if len(c) < 20 or not c[15] or c[17] & 2:
                continue
            loc, player = struct.unpack_from("<II", c)
            unit = struct.unpack_from("<H", c, 12)[0]
            if c[15] in (3, 7, 16, 17) and (unit in MINERALS or unit == 229 and player in (11, 17, 26)):
                locations.add(loc)
        for ai in range(64):
            a = trigger[320 + ai * 32:352 + ai * 32]
            if len(a) < 32 or not a[26] or a[28] & 2:
                continue
            player = struct.unpack_from("<I", a, 16)[0]
            unit = struct.unpack_from("<H", a, 24)[0]
            if a[26] in (23, 25, 38, 39, 43, 44, 46, 48, 49, 50, 51, 52, 53) and (unit in MOVABLE_RESOURCES or unit == 229 and player in (11, 17, 26)):
                locations.add(struct.unpack_from("<I", a)[0])
    for loc in locations:
        if not 0 < loc <= len(regions) // 20:
            continue
        l, t, r, b = struct.unpack_from("<4I", regions, (loc - 1) * 20)
        l, r, t, b = min(l, r), max(l, r), min(t, b), max(t, b)
        # Anywhere / the entire map is not coordinate-sensitive.
        width, height = struct.unpack("<HH", chk.getsection("DIM "))
        if l == t == 0 and r >= width * 32 and b >= height * 32:
            continue
        collision = mining.stock_geometry()[1]
        protected.update(i for i, (x, y, unit, _) in enumerate(info) if unit in MOVABLE_RESOURCES
                         and x + collision[unit][2] >= l and x - collision[unit][0] <= r
                         and y + collision[unit][3] >= t and y - collision[unit][1] <= b)
    return protected, locations


def _critical_membership(chk, before, after, indices, locations):
    if not locations:
        return True
    regions = chk.getsection("MRGN")
    boxes = mining.stock_geometry()[1]
    rects = [struct.unpack_from("<4I", regions, (loc - 1) * 20) for loc in locations
             if 0 < loc <= len(regions) // 20]
    def signature(item, rect):
        x, y, unit, _ = item
        l, t, r, b = rect
        l, r, t, b = min(l, r), max(l, r), min(t, b), max(t, b)
        a, c, d, e = boxes[unit]
        return x + d >= l and x - a <= r and y + e >= t and y - c <= b
    return all(signature(before[i], rect) == signature(after[i], rect) for i in indices for rect in rects)


def _assignment(points, targets, limit=MAX_DISPLACEMENT):
    """Minimum displacement assignment with an explicit per-resource bound."""
    n, huge = len(points), 10 ** 10
    costs = [[(x - a) ** 2 + (y - b) ** 2 if (x - a) ** 2 + (y - b) ** 2 <= limit ** 2 else huge
              for a, b in targets] for x, y in points]
    if any(min(row) == huge for row in costs):
        return None
    if any(min(row[j] for row in costs) == huge for j in range(n)):
        return None
    u, v, p, way = [0] * (n + 1), [0] * (n + 1), [0] * (n + 1), [0] * (n + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minimum, used = [huge * 10] * (n + 1), [False] * (n + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], huge * 10, 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = costs[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minimum[j]:
                        minimum[j], way[j] = cur, j0
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
    result, total = [None] * n, 0
    for j in range(1, n + 1):
        if costs[p[j] - 1][j - 1] >= huge:
            return None
        result[p[j] - 1] = targets[j - 1]
        total += costs[p[j] - 1][j - 1]
    return result, total


def _resource_clear(center, info):
    tx, ty = (center[0] - 64) // 32, (center[1] - 48) // 32
    return all((tx, ty) not in depot._resource_tiles(x, y, unit, 106, None)
               for x, y, unit, _ in info if unit in depot.resource_type_ids())


def _foundation(chk, center, unit, buildable):
    return mining.foundation_buildable(chk, center, unit, buildable)


def _fixed_collision(rect, info, ignore, boxes, mobile=True):
    return any(i not in ignore and unit != 214 and (mobile or unit >= 106)
               and geometry._overlap(rect, geometry._rect(x, y, unit, boxes))
               for i, (x, y, unit, _) in enumerate(info))


def _anchors(chk, info, indices, walk, boxes, buildable, race, accepted_anchors=(), required_depot=None, anchor_hints=()):
    points = [info[i][:2] for i in indices]
    cx, cy = sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)
    existing = sorted(((math.dist((cx, cy), (x, y)), i, x, y, unit, owner)
                       for i, (x, y, unit, owner) in enumerate(info) if unit in HEADQUARTERS))
    if required_depot is not None:
        x, y, unit, owner = info[required_depot]
        yield {"kind": "existing_depot", "unit_index": required_depot, "center": [x, y], "depot_type": unit,
               "owner": owner, "top_left_tile": [(x - 64) // 32, (y - 48) // 32]}
        return
    for distance, i, x, y, unit, owner in existing[:3]:
        if distance <= 768:
            yield {"kind": "existing_depot", "unit_index": i, "center": [x, y], "depot_type": unit,
                   "owner": owner, "top_left_tile": [(x - 64) // 32, (y - 48) // 32]}
    for anchor in sorted((a for a in accepted_anchors if a["kind"] == "expansion"),
                         key=lambda a: (math.dist(a["center"], (cx, cy)), a["center"])):
        if math.dist(anchor["center"], (cx, cy)) <= 768:
            yield dict(anchor)
    unit = {"terran": 106, "zerg": 131, "protoss": 154}.get(race, 106)
    for x, y in anchor_hints:
        if math.dist((x, y), (cx, cy)) > 1024 or not _foundation(chk, (x, y), unit, buildable):
            continue
        if _fixed_collision(geometry._rect(x, y, unit, boxes), info, set(indices), boxes, mobile=False):
            continue
        yield {"kind": "expansion", "center": [x, y], "depot_type": unit, "owner": None,
               "top_left_tile": [(x - 64) // 32, (y - 48) // 32], "reviewed_source_anchor": True}
    candidates = []
    for distance in (224, 288, 352, 416, 512, 640, 768, 896, 1024):
        for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
            for tangent in (0, -64, 64, -128, 128):
                x, y = _snap(cx + dx * distance + dy * tangent, cy + dy * distance + dx * tangent)
                if not _foundation(chk, (x, y), unit, buildable):
                    continue
                if _fixed_collision(geometry._rect(x, y, unit, boxes), info, set(indices), boxes, mobile=False):
                    continue
                candidates.append((distance ** 2 + tangent ** 2, x, y))
    seen = set()
    for _, x, y in sorted(candidates):
        if (x, y) not in seen:
            seen.add((x, y))
            yield {"kind": "expansion", "center": [x, y], "depot_type": unit, "owner": None,
                   "top_left_tile": [(x - 64) // 32, (y - 48) // 32]}


def _formations(points, anchor):
    n = len(points)
    cx, cy = sum(p[0] for p in points) / n, sum(p[1] for p in points) / n
    ax, ay = anchor["center"]
    primary = _direction((ax, ay), (cx, cy))
    directions = sorted(((0, -1), (0, 1), (-1, 0), (1, 0)),
                        key=lambda d: (d != primary, -(d[0] * (cx - ax) + d[1] * (cy - ay))))
    row_options = (1,) if n == 1 else ((1, 2) if n <= 12 else (2, 1))
    for dx, dy in directions:
        vertical = bool(dx)
        along = cy if vertical else cx
        anchor_along = ay if vertical else ax
        along = min(anchor_along + 256, max(anchor_along - 256, along))
        base_distance = abs(cx - ax) if vertical else abs(cy - ay)
        minimum = 224 if vertical else 192
        distances = sorted(range(minimum, 481, 32), key=lambda d: (abs(d - base_distance), d))
        for rows in row_options:
            lengths = [n // rows + (i < n % rows) for i in range(rows)]
            for distance in distances:
                for shift in (0, -32, 32, -64, 64, -96, 96, -128, 128):
                    for skew in (0, -1, 1):
                        targets = []
                        for row, size in enumerate(lengths):
                            line_center = along + shift
                            normal = distance + row * (128 if vertical else 96)
                            gap_center = round(line_center / 32) * 32
                            if size == 1:
                                tangent_positions = [_snap(0, line_center)[1] if vertical else _snap(line_center, 0)[0]]
                            else:
                                left_count = size // 2
                                if vertical:
                                    tangent_positions = [gap_center - 48 - (left_count - 1 - k) * 32 for k in range(left_count)]
                                    tangent_positions += [gap_center + 48 + k * 32 for k in range(size - left_count)]
                                else:
                                    tangent_positions = [gap_center - 64 - (left_count - 1 - k) * 64 for k in range(left_count)]
                                    tangent_positions += [gap_center + 64 + k * 64 for k in range(size - left_count)]
                            for tangent in tangent_positions:
                                if vertical:
                                    targets.append(_snap(ax + dx * normal + skew * (tangent - gap_center), tangent))
                                else:
                                    targets.append(_snap(tangent, ay + dy * normal + skew * (tangent - gap_center) / 2))
                        if len(set(targets)) == n:
                            yield targets, {"direction": [dx, dy], "rows": rows,
                                            "row_lengths": lengths, "row_spacing_pixels": 128 if vertical else 96,
                                            "line_step_pixels": [skew * 32, 32] if vertical else [64, skew * 32],
                                            "central_army_aisle_pixels": 64 if max(lengths) > 1 else 0,
                                            "central_army_aisle_coordinate": round((along + shift) / 32) * 32,
                                            "normal_distance_pixels": distance}


def _front_labels(item, direction, labels, bounds, boxes):
    x, y, unit, _ = item
    dx, dy = direction
    left, top, _, _ = bounds
    collision = _worker_boxes()[unit]
    hx = max(collision[0], collision[2])
    hy = max(collision[1], collision[3])
    cx, cy = x - dx * (hx + 12), y - dy * (hy + 12)
    offsets = (-8, 0, 8) if dx else (-24, -16, -8, 0, 8, 16, 24)
    cells = [(int(cx + (0 if dx else off)) // 8 - left,
              int(cy + (off if dx else 0)) // 8 - top) for off in offsets]
    return {labels[yy][xx] for xx, yy in cells if 0 <= yy < len(labels) and 0 <= xx < len(labels[0]) and labels[yy][xx]}


def _access(info, indices, anchor, direction, walk, boxes, before=None, virtual_anchors=()):
    points = [info[i][:2] for i in indices] + [anchor["center"]]
    bounds = _bounds(points, walk, 32)
    model = list(info)
    hq = (*anchor["center"], anchor["depot_type"], anchor.get("owner") or 0)
    virtual = {tuple(a["center"]): a for a in virtual_anchors if a["kind"] == "expansion"}
    if anchor["kind"] == "expansion":
        virtual[tuple(anchor["center"])] = anchor
    model.extend((*a["center"], a["depot_type"], 0) for a in virtual.values())
    labels, sizes, boundary = _components(walk, model, bounds, boxes)
    hq_components = _perimeter_labels(hq, labels, bounds, boxes)
    common = set(hq_components)
    blocked = []
    for i in indices:
        labels_at_front = _front_labels(info[i], direction, labels, bounds, boxes)
        if not labels_at_front & hq_components:
            blocked.append(i)
        common &= labels_at_front
    if blocked or not common:
        return False, {"all_mineral_fronts_reachable": False, "blocked_unit_indices": blocked,
                       "worker_clearance_pixels": WORKER_DIAMETER}
    if before is not None:
        old_model = list(before)
        old_model.extend((*a["center"], a["depot_type"], 0) for a in virtual.values())
        old, old_sizes, old_boundary = _components(walk, old_model, bounds, boxes)
        relevant_new = {c for c in boundary if sizes[c] >= 512}
        splits = defaultdict(set)
        for arow, brow in zip(old, labels):
            for a, b in zip(arow, brow):
                if a and b in relevant_new:
                    splits[a].add(b)
        if any(a in old_boundary and old_sizes[a] >= 512 and len(cs) > 1 for a, cs in splits.items()):
            return False, {"all_mineral_fronts_reachable": True, "reason": "new_boundary_route_barrier"}
    return True, {"all_mineral_fronts_reachable": True, "worker_clearance_pixels": WORKER_DIAMETER,
                  "common_depot_worker_component": min(common), "local_bounds_8px": list(bounds),
                  "blocked_unit_indices": [], "native_mining_verified": False}


def _collision_index(info, ignored, boxes):
    result = defaultdict(list)
    ignored = set(ignored)
    for i, (x, y, unit, owner) in enumerate(info):
        if i in ignored or unit == 214:
            continue
        rect = geometry._rect(x, y, unit, boxes)
        for yy in range(rect[1] // 64, (rect[3] - 1) // 64 + 1):
            for xx in range(rect[0] // 64, (rect[2] - 1) // 64 + 1):
                result[xx, yy].append(rect)
    return result


def _geometry_ok(info, indices, points, walk, boxes, reserved, occupied=None):
    ignore = set(indices)
    rectangles = [geometry._rect(x, y, 176, boxes) for x, y in points]
    for (x, y), rect in zip(points, rectangles):
        if not geometry._walkable_rect(walk, rect):
            return False
        if any(rect[0] - 24 < a < rect[2] + 24 and rect[1] - 24 < b < rect[3] + 24 for a, b in reserved):
            return False
        if occupied is None:
            if _fixed_collision(rect, info, ignore, boxes):
                return False
        elif any(geometry._overlap(rect, other)
                 for yy in range(rect[1] // 64, (rect[3] - 1) // 64 + 1)
                 for xx in range(rect[0] // 64, (rect[2] - 1) // 64 + 1)
                 for other in occupied.get((xx, yy), ())):
            return False
    return not any(geometry._overlap(a, b) for i, a in enumerate(rectangles) for b in rectangles[i + 1:])


def verify_only_resource_coordinates(before, after):
    if len(before) != len(after) or len(before) % 36:
        raise ValueError("Resource layout changed UNIT record count")
    changed = []
    for i in range(len(before) // 36):
        a, b = before[i * 36:(i + 1) * 36], after[i * 36:(i + 1) * 36]
        if a == b:
            continue
        if struct.unpack_from("<H", a, 8)[0] not in MOVABLE_RESOURCES or a[:4] != b[:4] or a[8:] != b[8:]:
            raise ValueError(f"Non-resource-coordinate UNIT change at {i}")
        changed.append(i)
    return changed


def _gas_state(info, anchors, worker_walk, boxes):
    """Whole-map gas return access, including every planned depot footprint."""
    virtual = {tuple(a["center"]): a for a in anchors if a["kind"] == "expansion"}
    model = list(info) + [(*a["center"], a["depot_type"], 0) for a in virtual.values()]
    bounds = (0, 0, len(worker_walk[0]), len(worker_walk))
    labels, _, _ = _components(worker_walk, model, bounds, boxes)
    all_anchors = [{"kind": "existing_depot", "unit_index": i, "center": [x, y], "depot_type": unit,
                    "owner": owner, "top_left_tile": [(x - 64) // 32, (y - 48) // 32]}
                   for i, (x, y, unit, owner) in enumerate(info) if unit in HEADQUARTERS] + list(virtual.values())
    hq_components = [(a, _perimeter_labels((*a["center"], a["depot_type"], 0), labels, bounds, boxes))
                     for a in all_anchors]
    result = {}
    for i, item in enumerate(info):
        if item[2] != GEYSER:
            continue
        adjacent = _perimeter_labels(item, labels, bounds, boxes)
        compatible = [(math.dist(item[:2], a["center"]), a) for a, comps in hq_components
                      if adjacent & comps and math.dist(item[:2], a["center"]) <= 768]
        if compatible:
            distance, anchor = min(compatible, key=lambda pair: (pair[0], pair[1]["center"]))
            result[i] = {"anchor": anchor, "depot_distance_pixels": round(distance, 6)}
    return result


def _gas_anchors(chk, info, index, raw_walk, boxes, buildable, race, anchors):
    """Try the existing search, then every nearby aligned depot foundation.

    Geysers can sit diagonally across a cliff from the nearest expansion. A
    cardinal search can miss the few usable sites even when mining needs no
    resource relocation. The complete fallback remains bounded to 768 pixels.
    """
    seen = set()
    for anchor in islice(_anchors(chk, info, [index], raw_walk, boxes, buildable, race, anchors), 80):
        seen.add(tuple(anchor["center"]))
        yield anchor
    gx, gy = info[index][:2]
    unit = {"terran": 106, "zerg": 131, "protoss": 154}.get(race, 106)
    candidates = []
    for tx in range((gx - 64) // 32 - 24, (gx - 64) // 32 + 25):
        for ty in range((gy - 48) // 32 - 24, (gy - 48) // 32 + 25):
            x, y = tx * 32 + 64, ty * 32 + 48
            distance = (x - gx) ** 2 + (y - gy) ** 2
            if distance <= 768 ** 2 and (x, y) not in seen:
                candidates.append((distance, x, y))
    for _, x, y in sorted(candidates):
        if not _foundation(chk, (x, y), unit, buildable):
            continue
        if _fixed_collision(geometry._rect(x, y, unit, boxes), info, {index}, boxes, mobile=False):
            continue
        yield {"kind": "expansion", "center": [x, y], "depot_type": unit, "owner": None,
               "top_left_tile": [(x - 64) // 32, (y - 48) // 32], "gas_anchor_search": "complete_local_grid"}


def _finish_gas(chk, info, fields, anchors, clear_depots, worker_walk, army_walk, raw_walk, boxes, buildable, row, critical_locations, reserved, army_cache):
    gases = [i for i, item in enumerate(info) if item[2] == GEYSER]
    if not gases:
        return info, []
    state = _gas_state(info, anchors, worker_walk, boxes)
    protected = set(state)
    reports = []
    for index in gases:
        initial = info[index]
        if index not in state:
            for anchor in _gas_anchors(chk, info, index, raw_walk, boxes, buildable, row.get("race"), anchors):
                if not _resource_clear(anchor["center"], info):
                    continue
                if anchor["kind"] == "expansion" and any(tuple(a["center"]) != tuple(anchor["center"])
                        and geometry._overlap(geometry._rect(*anchor["center"], anchor["depot_type"], boxes),
                                              geometry._rect(*a["center"], a["depot_type"], boxes)) for a in anchors):
                    continue
                proposed = anchors + [anchor]
                if any(not _access(info, f["unit_indices"], f["anchor"], f["direction"], worker_walk, boxes,
                                   virtual_anchors=proposed)[0] for f in fields):
                    continue
                candidate_state = _gas_state(info, proposed, worker_walk, boxes)
                if index not in candidate_state or not protected <= set(candidate_state):
                    continue
                if tuple(anchor["center"]) not in {tuple(a["center"]) for a in anchors}:
                    anchors.append(anchor)
                if tuple(anchor["center"]) not in clear_depots:
                    clear_depots.append(tuple(anchor["center"]))
                state, protected = candidate_state, set(candidate_state)
                break
        if index not in state:
            # Reposition gas only when a nearby drop-off footprint cannot make
            # the existing geyser usable.  Keep its exact record and amount.
            occupied = _collision_index(info, [index], boxes)
            targets = []
            all_anchors = list(anchors) + [{"kind": "existing_depot", "unit_index": i, "center": [x, y],
                    "depot_type": unit, "owner": owner} for i, (x, y, unit, owner) in enumerate(info) if unit in HEADQUARTERS]
            anchor_choices = [a for a in all_anchors if math.dist(a["center"], initial[:2]) <= MAX_DISPLACEMENT + 768]
            for anchor in anchor_choices:
                ax, ay = anchor["center"]
                for distance in (256, 320, 384, 448):
                    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                        for tangent in (0, -64, 64, -128, 128):
                            x = round((ax + dx * distance + dy * tangent) / 32) * 32
                            y = round((ay + dy * distance + dx * tangent) / 32) * 32
                            cost = (x - initial[0]) ** 2 + (y - initial[1]) ** 2
                            if cost <= MAX_DISPLACEMENT ** 2:
                                targets.append((cost, x, y))
            for _, x, y in sorted(set(targets)):
                if not _foundation(chk, (x, y), GEYSER, buildable):
                    continue
                rect = geometry._rect(x, y, GEYSER, boxes)
                if _fixed_collision(rect, info, {index}, boxes):
                    continue
                if any(rect[0] - 24 < px < rect[2] + 24 and rect[1] - 24 < py < rect[3] + 24 for px, py in reserved):
                    continue
                candidate = list(info)
                candidate[index] = (x, y, GEYSER, initial[3])
                if not _critical_membership(chk, info, candidate, [index], critical_locations):
                    continue
                if any(not _resource_clear(center, candidate) for center in clear_depots):
                    continue
                if not _army_route_ok(info, candidate, [index], army_walk, boxes, army_cache):
                    continue
                if any(not _access(candidate, f["unit_indices"], f["anchor"], f["direction"], worker_walk, boxes,
                                   virtual_anchors=anchors)[0] for f in fields):
                    continue
                candidate_state = _gas_state(candidate, anchors, worker_walk, boxes)
                if index in candidate_state and protected <= set(candidate_state):
                    info, state, protected = candidate, candidate_state, set(candidate_state)
                    break
        snapped = (info[index][0] // 32 * 32, info[index][1] // 32 * 32)
        reports.append({"unit_index": index, "status": "functional_geyser" if index in state else "no_verified_gas_anchor",
                        "position": list(info[index][:2]), "changed": info[index][:2] != initial[:2],
                        "refinery_foundation_buildable": _foundation(chk, snapped, GEYSER, buildable),
                        "worker_clearance_pixels": WORKER_DIAMETER, **state.get(index, {})})
    for field in fields:
        okay, proof = _access(info, field["unit_indices"], field["anchor"], field["direction"], worker_walk, boxes,
                              virtual_anchors=anchors)
        if not okay:
            raise ValueError("Final gas planning invalidated a verified mineral field")
        field["front_access"] = proof
    final_state = _gas_state(info, anchors, worker_walk, boxes)
    for report in reports:
        index = report["unit_index"]
        report.update(status="functional_geyser" if index in final_state else "no_verified_gas_anchor", **final_state.get(index, {}))
    return info, reports


def plan_layout(chk, row=None, *, reserved_points=(), protected_indices=(), terrain=None):
    row = dict(row or {})
    anchor_hints = REVIEWED_EXPANSION_ANCHORS.get(row.get("mission_id"), ())
    if "owner" not in row and "player_slot" not in row:
        try:
            humans = [i for i, owner in enumerate(chk.getsection("OWNR")) if owner == 6]
            if len(humans) == 1:
                row["owner"] = humans[0]
        except KeyError:
            pass
    records = geometry._records(chk)
    original = list(map(geometry._info, records))
    info = list(original)
    walk, terrain_proof = geometry.load_terrain(chk) if terrain is None else terrain
    worker_walk = _worker_terrain(walk)
    army_walk = _worker_terrain(_worker_terrain(worker_walk))
    army_cache = {"baseline": original}
    boxes, dat_proof = geometry.load_unit_geometry()
    buildable = mining.load_buildable_grid(chk)
    known_gas_access = set(_gas_state(info, [], worker_walk, boxes)) if any(p[2] == GEYSER for p in info) else set()
    explicit, critical_locations = _critical_locations(chk, original)
    explicit.update(protected_indices)
    # A position-sensitive patch cannot move into a line. Keep a worker-sized
    # approach on its depot-facing edge clear while moving its neighbours.
    protected_approaches = []
    for index in sorted(explicit):
        if original[index][2] not in MINERALS:
            continue
        x, y, unit, _ = original[index]
        near = sorted((math.dist((x, y), item[:2]), i) for i, item in enumerate(original) if item[2] in HEADQUARTERS)
        if not near or near[0][0] > 768:
            continue
        dx, dy = _direction(original[near[0][1]][:2], (x, y))
        left, top, right, bottom = _worker_boxes()[unit]
        protected_approaches.append((x - dx * (max(left, right) + 12), y - dy * (max(top, bottom) + 12)))
    layout_reserved_points = tuple(reserved_points) + tuple(protected_approaches)
    forbidden = depot.resource_forbidden_tiles(original)
    clear_depots = [(x, y) for x, y, unit, _ in original if unit in HEADQUARTERS
                    and ((x - 64) // 32, (y - 48) // 32) not in forbidden]
    original_clear_depots = list(clear_depots)
    groups = sorted(geometry._clusters(original), key=lambda group: (-len(group), min(group)))
    # Large dense pools use multiple independent strips, never a solid rectangle.
    split_groups, source_depots, source_worker_components = [], {}, None
    for group in groups:
        center = (sum(original[i][0] for i in group) / len(group), sum(original[i][1] for i in group) / len(group))
        near = sorted((math.dist(center, item[:2]), i) for i, item in enumerate(original) if item[2] in HEADQUARTERS)
        required = near[0][1] if near and near[0][0] <= 640 else None
        if required is not None and original[required][3] != row.get("owner", row.get("player_slot")):
            same_owner = [i for distance, i in near if distance <= 1024 and original[i][3] == original[required][3]]
            if len(same_owner) > 1:
                whole = (0, 0, len(worker_walk[0]), len(worker_walk))
                if source_worker_components is None:
                    source_worker_components = _components(worker_walk, original, whole, boxes)
                labels = source_worker_components[0]
                mineral_components = [_perimeter_labels(original[i], labels, whole, boxes) for i in group]
                scores = {}
                for i in same_owner:
                    hq_components = _perimeter_labels(original[i], labels, whole, boxes)
                    scores[i] = sum(bool(c & hq_components) for c in mineral_components)
                best = min(same_owner, key=lambda i: (-scores[i], math.dist(center, original[i][:2]), i))
                if scores[best] > scores[required]:
                    required = best
        for i in group:
            source_depots[i] = required
        fixed = sorted(set(group) & explicit)
        if fixed:
            split_groups.append(fixed)
            group = sorted(set(group) - explicit)
            if not group:
                continue
        if len(group) <= 32:
            split_groups.append(group)
        else:
            xs, ys = [original[i][0] for i in group], [original[i][1] for i in group]
            axis = 0 if max(xs) - min(xs) >= max(ys) - min(ys) else 1
            ordered = sorted(group, key=lambda i: (original[i][axis], original[i][1 - axis], i))
            parts = math.ceil(len(group) / 24)
            split_groups.extend(sorted(ordered[k * len(group) // parts:(k + 1) * len(group) // parts]) for k in range(parts))
    reports, accepted_fields, accepted_anchors, split_attempts = [], [], [], []
    pending = deque((indices, 0) for indices in split_groups)
    while pending:
        indices, split_depth = pending.popleft()
        report = {"unit_indices": indices, "mineral_count": len(indices), "changed": False, "status": "unchanged"}
        reports.append(report)
        if explicit & set(indices):
            report["status"] = "protected_resource_trigger"
            continue
        if _true_mining_gate(info, indices, worker_walk, boxes):
            report["status"] = "protected_true_boundary_mining_gate"
            continue
        points = [info[i][:2] for i in indices]
        occupied = _collision_index(info, indices, boxes)
        required_depot = source_depots[indices[0]]
        hq_distance_limit = None
        if required_depot is not None:
            source_center = original[required_depot][:2]
            old_max = max(math.dist(original[i][:2], source_center) for i in indices)
            hq_distance_limit = min(old_max + 128, 512) if old_max <= 512 else old_max + 128
            if original[required_depot][3] == row.get("owner", row.get("player_slot")):
                hq_distance_limit = min(hq_distance_limit, 512)
            report.update(required_original_depot_index=required_depot,
                          max_original_depot_distance_pixels=round(old_max, 6),
                          max_allowed_depot_distance_pixels=round(hq_distance_limit, 6))
        failures = defaultdict(int)
        accepted = False
        for anchor_index, anchor in enumerate(_anchors(chk, info, indices, walk, boxes, buildable, row.get("race"), accepted_anchors, required_depot, anchor_hints)):
            if anchor_index >= 256:
                break
            if anchor["kind"] == "expansion" and any(tuple(a["center"]) != tuple(anchor["center"])
                    and geometry._overlap(geometry._rect(*anchor["center"], anchor["depot_type"], boxes),
                                          geometry._rect(*a["center"], a["depot_type"], boxes)) for a in accepted_anchors):
                continue
            for targets, shape in _formations(points, anchor):
                if hq_distance_limit is not None and any(math.dist(point, anchor["center"]) > hq_distance_limit for point in targets):
                    continue
                if not _geometry_ok(info, indices, targets, walk, boxes, layout_reserved_points, occupied):
                    continue
                assignment = _assignment(points, targets)
                if assignment is None:
                    continue
                chosen, cost = assignment
                candidate = list(info)
                for i, (x, y) in zip(indices, chosen):
                    candidate[i] = (x, y, *info[i][2:])
                if not _resource_clear(anchor["center"], candidate):
                    failures["anchor_resource_exclusion"] += 1
                    continue
                if any(not _resource_clear(center, candidate) for center in clear_depots):
                    failures["placed_depot_rebuild_preservation"] += 1
                    continue
                if not _critical_membership(chk, info, candidate, indices, critical_locations):
                    failures["critical_resource_location"] += 1
                    continue
                okay, access = _access(candidate, indices, anchor, shape["direction"], worker_walk, boxes,
                                      before=info, virtual_anchors=accepted_anchors)
                if not okay:
                    failures[access.get("reason", "worker_front_unreachable")] += 1
                    continue
                previous_access = []
                for previous in accepted_fields:
                    prior_okay, prior_access = _access(candidate, previous["unit_indices"], previous["anchor"],
                                                      previous["direction"], worker_walk, boxes,
                                                      virtual_anchors=accepted_anchors + [anchor])
                    if not prior_okay:
                        failures["previous_field_worker_lane_blocked"] += 1
                        break
                    previous_access.append(prior_access)
                else:
                    prior_okay = True
                if not prior_okay:
                    continue
                if not _army_route_ok(info, candidate, indices, army_walk, boxes, army_cache):
                    failures["large_army_route_barrier"] += 1
                    continue
                candidate_gas = _gas_state(candidate, accepted_anchors + [anchor], worker_walk, boxes) if known_gas_access else {}
                if not known_gas_access <= set(candidate_gas):
                    failures["existing_gas_return_lane_blocked"] += 1
                    continue
                report.update(status="functional_line", changed=any(info[i][:2] != candidate[i][:2] for i in indices),
                              anchor=anchor, front_access=access, squared_displacement_total=cost,
                              large_army_routes_preserved=True, **shape)
                for previous, prior_access in zip(accepted_fields, previous_access):
                    previous["front_access"] = prior_access
                accepted_fields.append(report)
                if tuple(anchor["center"]) not in {tuple(a["center"]) for a in accepted_anchors}:
                    accepted_anchors.append(anchor)
                if tuple(anchor["center"]) not in clear_depots:
                    clear_depots.append(tuple(anchor["center"]))
                known_gas_access.update(candidate_gas)
                info, accepted = candidate, True
                break
            if accepted:
                break
        if not accepted:
            if len(indices) > 1 and split_depth < 4:
                xs, ys = [info[i][0] for i in indices], [info[i][1] for i in indices]
                axis = 0 if max(xs) - min(xs) >= max(ys) - min(ys) else 1
                ordered = sorted(indices, key=lambda i: (info[i][axis], info[i][1 - axis], i))
                middle = len(ordered) // 2
                pending.appendleft((sorted(ordered[middle:]), split_depth + 1))
                pending.appendleft((sorted(ordered[:middle]), split_depth + 1))
                split_attempts.append({"unit_indices": indices, "reason": "two_independent_short_lines_required",
                                       "candidate_rejections": dict(failures)})
                reports.remove(report)
                continue
            # Do not mislabel an already working small source strip as broken
            # solely because its original silhouette is not a straight line.
            for anchor_index, anchor in enumerate(_anchors(chk, info, indices, walk, boxes, buildable, row.get("race"), accepted_anchors, required_depot, anchor_hints)):
                if anchor_index >= 256:
                    break
                if anchor["kind"] == "expansion" and any(tuple(a["center"]) != tuple(anchor["center"])
                        and geometry._overlap(geometry._rect(*anchor["center"], anchor["depot_type"], boxes),
                                              geometry._rect(*a["center"], a["depot_type"], boxes)) for a in accepted_anchors):
                    continue
                if not _resource_clear(anchor["center"], info):
                    continue
                point = (sum(info[i][0] for i in indices) / len(indices), sum(info[i][1] for i in indices) / len(indices))
                direction = _direction(anchor["center"], point)
                okay, access = _access(info, indices, anchor, direction, worker_walk, boxes,
                                      virtual_anchors=accepted_anchors)
                if not okay:
                    continue
                previous_access = []
                for previous in accepted_fields:
                    prior_okay, prior_access = _access(info, previous["unit_indices"], previous["anchor"], previous["direction"],
                                                      worker_walk, boxes, virtual_anchors=accepted_anchors + [anchor])
                    if not prior_okay:
                        break
                    previous_access.append(prior_access)
                else:
                    prior_okay = True
                if not prior_okay:
                    continue
                candidate_gas = _gas_state(info, accepted_anchors + [anchor], worker_walk, boxes) if known_gas_access else {}
                if not known_gas_access <= set(candidate_gas):
                    continue
                report.update(status="functional_existing_field", changed=False, anchor=anchor,
                              direction=list(direction), front_access=access, rows=None,
                              source_layout_preserved=True, candidate_rejections=dict(failures))
                for previous, prior_access in zip(accepted_fields, previous_access):
                    previous["front_access"] = prior_access
                accepted_fields.append(report)
                if tuple(anchor["center"]) not in {tuple(a["center"]) for a in accepted_anchors}:
                    accepted_anchors.append(anchor)
                if tuple(anchor["center"]) not in clear_depots:
                    clear_depots.append(tuple(anchor["center"]))
                known_gas_access.update(candidate_gas)
                accepted = True
                break
            if not accepted:
                report.update(status="no_verified_line_found", candidate_rejections=dict(failures))
    # A trigger-protected patch can remain at its original position and still
    # become usable after the surrounding ordinary ore is put into lines.
    for field in reports:
        if field["status"] != "protected_resource_trigger":
            continue
        indices = field["unit_indices"]
        required = source_depots[indices[0]]
        for anchor in _anchors(chk, info, indices, walk, boxes, buildable, row.get("race"), accepted_anchors, required, anchor_hints):
            if not _resource_clear(anchor["center"], info):
                continue
            center = (sum(info[i][0] for i in indices) / len(indices), sum(info[i][1] for i in indices) / len(indices))
            direction = _direction(anchor["center"], center)
            okay, access = _access(info, indices, anchor, direction, worker_walk, boxes, virtual_anchors=accepted_anchors)
            if okay:
                field.update(status="functional_protected_resource", anchor=anchor, direction=list(direction),
                             rows=1, front_access=access, resource_trigger_position_preserved=True)
                accepted_fields.append(field)
                break
    info, gas_reports = _finish_gas(chk, info, accepted_fields, accepted_anchors, clear_depots, worker_walk, army_walk, walk, boxes,
                                    buildable, row, critical_locations, layout_reserved_points, army_cache)
    try:
        from . import ladder_resource_layout as ladder
    except ImportError:
        import ladder_resource_layout as ladder
    info, ladder_bases = ladder.refine(chk, info, original, accepted_fields, accepted_anchors, clear_depots,
        worker_walk, army_walk, walk, boxes, buildable, explicit, critical_locations, layout_reserved_points, army_cache)
    final_gas = _gas_state(info, accepted_anchors, worker_walk, boxes)
    for gas in gas_reports:
        index = gas['unit_index']
        gas.update(position=list(info[index][:2]), changed=info[index][:2] != original[index][:2], **final_gas.get(index, {}))
    moves = [{"unit_index": i, "unit_type": a[2], "owner": a[3], "from": list(a[:2]), "to": list(b[:2]),
              "displacement_pixels": round(math.dist(a[:2], b[:2]), 6)}
             for i, (a, b) in enumerate(zip(original, info)) if a[:2] != b[:2]]
    raw = bytearray(chk.getsection("UNIT"))
    for move in moves:
        struct.pack_into("<HH", raw, move["unit_index"] * 36 + 4, *move["to"])
    return {"schema_version": 1, "algorithm": ALGORITHM_VERSION, "mission_id": row.get("mission_id"),
            "source_unit_sha256": _hash(chk.getsection("UNIT")), "output_unit_sha256": _hash(raw),
            "changed": bool(moves), "mineral_count": sum(u in MINERALS for x, y, u, p in original),
            "geyser_count": sum(u == GEYSER for x, y, u, p in original), "moved_count": len(moves),
            "moved_indices": [move["unit_index"] for move in moves], "moves": moves, "clusters": reports,
            "cluster_count": len(reports), "changed_cluster_count": sum(r["changed"] for r in reports),
            "functional_cluster_count": sum(r["status"].startswith("functional_") for r in reports),
            "split_attempts": split_attempts,
            "gas_fields": gas_reports,
            "ladder_bases": ladder_bases,
            "functional_geyser_count": sum(g["status"] == "functional_geyser" for g in gas_reports),
            "protected_indices": sorted(explicit), "reserved_points": [list(p) for p in sorted(set(map(tuple, reserved_points)))],
            "protected_resource_worker_approach_points": [list(p) for p in protected_approaches],
            "preserved_original_depot_centers": [list(p) for p in original_clear_depots],
            "reserved_resource_depot_centers": [list(p) for p in clear_depots],
            "army_route_guard": {"clearance_pixels": 48, "minimum_component_cells": 512,
                                 "minimum_shared_original_cells_per_region": 512,
                                 "virtual_hqs_included": False, "new_large_component_splits_allowed": False,
                                 "native_large_unit_pathfinder_verified": False},
            "limits": {"max_displacement_pixels": MAX_DISPLACEMENT, "only_UNIT_resource_xy_words_changed": True,
                       "resource_count_type_owner_amount_serial_preserved": True, "native_mining_verified": False,
                       "native_can_build_verified": False}, "unit_geometry": dat_proof, "terrain": terrain_proof}


def apply_layout(chk, row=None, *, reserved_points=(), protected_indices=(), terrain=None):
    report = plan_layout(chk, row, reserved_points=reserved_points, protected_indices=protected_indices, terrain=terrain)
    before = chk.getsection("UNIT")
    after = bytearray(before)
    for move in report["moves"]:
        struct.pack_into("<HH", after, move["unit_index"] * 36 + 4, *move["to"])
    verify_only_resource_coordinates(before, after)
    chk.setsection("UNIT", after)
    return report
