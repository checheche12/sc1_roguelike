"""Append missing main-base geysers from campaign mission five onward.

Original records stay byte-for-byte intact. Placement uses extracted terrain,
refinery foundations, worker fronts and the existing large-army route guard.
These are offline checks; native mining is not simulated.
"""
from collections import defaultdict
import math
import struct

try:
    from . import resource_layout as rules, ladder_resource_layout as ladder
except ImportError:
    import resource_layout as rules, ladder_resource_layout as ladder

VERSION = "main_base_two_gases_v2_original_amount"
GAS_TYPES = frozenset((188, 110, 149, 157))
RADIUS = 512
# Original opening bases acquired after the opening sequence. Never choose an
# arbitrary enemy expansion just because the player initially has no HQ.
ACQUIRED_BASES = {105: (2720, 464), 106: (320, 2544), 207: (1824, 3344),
                  506: (1248, 3088), 605: (2464, 368)}


def eligible(row):
    return row["ordinal"] >= 5 and not row["no_production"]


def main_anchor(info, row, fields):
    owner = row["owner"]
    anchors = {tuple(f["anchor"]["center"]): dict(f["anchor"]) for f in fields if "anchor" in f}
    acquired = ACQUIRED_BASES.get(row["mission_id"])
    if acquired:
        if acquired not in anchors:
            raise ValueError("Reviewed opening base is missing its resource anchor")
        return anchors[acquired], "reviewed_opening_resource_base"
    starts = [p[:2] for p in info if p[2] == 214 and p[3] == owner]
    own = [a for a in anchors.values() if a.get("owner") == owner]
    if not own and row["mission_id"] not in (108, 309):
        own = [{"kind": "existing_depot", "unit_index": i, "center": list(p[:2]),
                "depot_type": p[2], "owner": owner}
               for i, p in enumerate(info) if p[2] in rules.HEADQUARTERS and p[3] == owner]
    if own:
        # Resource anchors avoid choosing a macro hatchery without a mineral line.
        start = starts[0] if starts else own[0]["center"]
        return min(own, key=lambda a: (math.dist(start, a["center"]), a["center"])), "initial_player_resource_base"
    expansions = [a for a in anchors.values() if a["kind"] == "expansion"]
    if row["mission_id"] in (108, 309) and starts and expansions:
        return min(expansions, key=lambda a: (math.dist(starts[0], a["center"]), a["center"])), "initial_settlement_resource_field"
    raise ValueError(f"No reviewed starting production base for mission {row['mission_id']}")


def gas_indices(info, anchor, worker, boxes):
    center = anchor["center"]
    bounds = rules._bounds([center], worker, 88)
    model = list(info)
    if anchor["kind"] == "expansion":
        model.append((*center, anchor["depot_type"], 0))
    labels, _, _ = rules._components(worker, model, bounds, boxes)
    hq = rules._perimeter_labels((*center, anchor["depot_type"], 0), labels, bounds)
    return [i for i, p in enumerate(info) if p[2] in GAS_TYPES and math.dist(p[:2], center) <= RADIUS
            and hq & rules._perimeter_labels(p, labels, bounds)]


def candidates(anchor, info):
    ax, ay = anchor["center"]
    existing = [p[:2] for p in info if p[2] in GAS_TYPES and math.dist(p[:2], (ax, ay)) <= RADIUS]
    points = [(x, y) for y in range(math.ceil((ay-RADIUS)/32)*32, ay+RADIUS+1, 32)
              for x in range(math.ceil((ax-RADIUS)/32)*32, ax+RADIUS+1, 32)
              if 160 <= math.dist((ax, ay), (x, y)) <= RADIUS]
    # Prefer short trips, then spread new gas away from the existing gas.
    return sorted(points, key=lambda p: (round(math.dist(p, (ax, ay))/32),
                  -min((math.dist(p, e) for e in existing), default=0), math.dist(p, (ax, ay)), p))


def reference_gas(records, info, anchor, nearby, layout):
    """Match the original local gas, including a prebuilt refinery's amount."""
    indices = list(nearby)
    scope = "existing_main_base_gas"
    if not indices:
        indices = [g["unit_index"] for g in layout["gas_fields"]
                   if g.get("anchor", {}).get("center") == anchor["center"]]
        scope = "existing_gas_assigned_to_settlement"
    if not indices:
        indices = [i for i, p in enumerate(info) if p[2] in GAS_TYPES]
        scope = "nearest_original_gas_to_settlement"
    if not indices:
        raise ValueError("No original gas amount to copy")
    index = min(indices, key=lambda i: (math.dist(info[i][:2], anchor["center"]), i))
    amount = struct.unpack_from("<I", records[index], 20)[0]
    if not struct.unpack_from("<H", records[index], 14)[0] & 16:
        raise ValueError("Reference gas lacks an explicit original resource amount")
    return dict(unit_index=index, unit_type=info[index][2], position=list(info[index][:2]),
                resources=amount, selection=scope)


def apply(chk, row, layout, *, reserved_points=()):
    report = dict(algorithm=VERSION, mission_id=row["mission_id"], ordinal=row["ordinal"],
                  eligible=eligible(row), added=[], original_records_unchanged=True,
                  native_mining_verified=False)
    if not report["eligible"]:
        report["status"] = "no_production" if row["no_production"] else "before_mission_five"
        return report
    records = rules.geometry._records(chk)
    info = list(map(rules.geometry._info, records))
    anchor, selection = main_anchor(info, row, layout["clusters"])
    report.update(anchor=anchor, selection=selection)
    walk, _ = rules.geometry.load_terrain(chk)
    worker = rules._worker_terrain(walk)
    boxes, _ = rules.geometry.load_unit_geometry()
    buildable = rules.mining.load_buildable_grid(chk)
    before = gas_indices(info, anchor, worker, boxes)
    report["gas_count_before"] = len(before)
    if len(before) >= 2:
        report.update(status="already_has_two_gases", gas_count_after=len(before), gas_indices=before)
        return report
    reference = reference_gas(records, info, anchor, before, layout)
    report["resource_amount_reference"] = reference
    all_anchors = {tuple(f["anchor"]["center"]): f["anchor"] for f in layout["clusters"] if "anchor" in f}
    all_anchors[tuple(anchor["center"])] = anchor
    virtual = [a for a in all_anchors.values() if a["kind"] == "expansion"]
    army = rules._worker_terrain(rules._worker_terrain(worker))
    clear_depots = layout["reserved_resource_depot_centers"]
    known_gas = set(rules._gas_state(info, list(all_anchors.values()), worker, boxes))
    templates = [r for r in records if rules.geometry._info(r)[2] == 188]
    template = templates[0] if templates else next(r for r in records if rules.geometry._info(r)[2] in rules.MINERALS)
    serial = max(struct.unpack_from("<I", r)[0] for r in records) + 1
    failures = defaultdict(int)
    while len(gas_indices(info, anchor, worker, boxes)) < 2:
        accepted = False
        army_cache = {"baseline": info}
        for point in candidates(anchor, info):
            index = len(info)
            baseline = info + [(*point, 214, 11)]
            proposed = info + [(*point, 188, 11)]
            if not ladder._geometry(proposed, [index], [point], walk, boxes, reserved_points, buildable, chk, failures):
                continue
            # Keep rebuildable HQs and every planned mineral drop-off footprint.
            centers = list(clear_depots) + [a["center"] for a in virtual]
            centers = [c for c in centers if rules._resource_clear(c, info)]
            if (any(not rules._resource_clear(c, proposed) for c in centers)
                    or not rules._resource_clear(anchor["center"], [proposed[-1]])):
                failures["depot_rebuilding"] += 1
                continue
            if len(gas_indices(proposed, anchor, worker, boxes)) != len(gas_indices(info, anchor, worker, boxes)) + 1:
                failures["main_gas_return_access"] += 1
                continue
            affected = [f for f in layout["clusters"] if "anchor" in f
                        and any(math.dist(point, info[i][:2]) < 768 for i in f["unit_indices"])]
            if any(not rules._access(proposed, f["unit_indices"], f["anchor"], f["direction"], worker, boxes,
                                     virtual_anchors=virtual)[0] for f in affected):
                failures["mineral_front_access"] += 1
                continue
            if not known_gas <= set(rules._gas_state(proposed, list(all_anchors.values()), worker, boxes)):
                failures["existing_gas_access"] += 1
                continue
            if not rules._army_route_ok(baseline, proposed, [index], army, boxes, army_cache):
                failures["large_army_route"] += 1
                continue
            record = bytearray(template)
            struct.pack_into("<IHHH", record, 0, serial, *point, 188)
            record[16] = 11
            struct.pack_into("<I", record, 20, reference["resources"])
            struct.pack_into("<H", record, 14, struct.unpack_from("<H", record, 14)[0] | 16)
            # No transport/building link may be inherited from a source record.
            struct.pack_into("<H", record, 10, 0)
            struct.pack_into("<HII", record, 26, 0, 0, 0)
            records.append(bytes(record));info = proposed;serial += 1
            report["added"].append(dict(unit_index=index, position=list(point), resources=reference["resources"],
                                       owner=11, unit_type=188, distance_pixels=round(math.dist(point, anchor["center"]), 6)))
            accepted = True
            break
        if not accepted:
            raise ValueError(f"No safe second gas position for mission {row['mission_id']}: {dict(failures)}")
    original = chk.getsection("UNIT")
    output = b"".join(records)
    assert output[:len(original)] == original
    chk.setsection("UNIT", output)
    report.update(status="two_gases_verified", gas_count_after=len(gas_indices(info, anchor, worker, boxes)),
                  gas_indices=gas_indices(info, anchor, worker, boxes), rejected_candidates=dict(failures),
                  refinery_foundations_verified=True, mineral_fronts_preserved=True,
                  existing_gas_access_preserved=True, large_army_routes_preserved=True)
    return report
