"""Append missing main-base geysers from campaign mission five onward.

Existing geysers move to short direct worker lanes; amounts and other record
fields stay intact. Placement uses extracted terrain,
refinery foundations, worker fronts and the existing large-army route guard.
These are offline checks; native mining is not simulated.
"""
from collections import defaultdict
import math
import struct

try:
    from . import resource_layout as rules, ladder_resource_layout as ladder, addon_placement as addons
except ImportError:
    import resource_layout as rules, ladder_resource_layout as ladder, addon_placement as addons

VERSION = "main_base_two_gases_v3_direct_mining_lane"
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


def candidates(anchor, info, ignore=None):
    ax, ay = anchor["center"]
    existing = [p[:2] for i,p in enumerate(info) if i!=ignore and p[2] in GAS_TYPES and math.dist(p[:2], (ax, ay)) <= RADIUS]
    points = [(x, y) for y in range(math.ceil((ay-RADIUS)/32)*32, ay+RADIUS+1, 32)
              for x in range(math.ceil((ax-RADIUS)/32)*32, ax+RADIUS+1, 32)
              if 160 <= math.dist((ax, ay), (x, y)) <= RADIUS]
    # Prefer short trips, then spread new gas away from the existing gas.
    return sorted(points, key=lambda p: (round(math.dist(p, (ax, ay))/32),
                  -min((math.dist(p, e) for e in existing), default=0), math.dist(p, (ax, ay)), p))


def direct_lane(anchor, point, info, moving, worker, boxes):
    """A worker-width straight route between HQ and gas, without mineral detours."""
    center = anchor['center']
    hq = rules.geometry._rect(*center, anchor['depot_type'], boxes)
    gas = rules.geometry._rect(*point, 188, boxes)
    obstacles = [rules.geometry._rect(*p[:2], p[2], boxes) for i,p in enumerate(info)
                 if i != moving and p[2] >= 106 and p[2] != 214
                 and not (p[2] in rules.HEADQUARTERS and tuple(p[:2]) == tuple(center))]
    steps = max(1, math.ceil(math.dist(center, point) / 4))
    for step in range(steps+1):
        x = center[0] + (point[0]-center[0])*step/steps
        y = center[1] + (point[1]-center[1])*step/steps
        if any(l-12 <= x <= r+12 and t-12 <= y <= b+12 for l,t,r,b in (hq,gas)):
            continue
        xx, yy = int(x)//8, int(y)//8
        if not (0 <= yy < len(worker) and 0 <= xx < len(worker[0]) and worker[yy][xx]):
            return False
        if any(l-12 < x < r+12 and t-12 < y < b+12 for l,t,r,b in obstacles):
            return False
    return True


def move_existing(chk, row, layout, reserved_points):
    if row['no_production']:
        return []
    records = rules.geometry._records(chk);info = list(map(rules.geometry._info, records))
    try:anchor, _ = main_anchor(info, row, layout['clusters'])
    except ValueError:
        if not eligible(row):return []
        raise
    anchors = {tuple(f['anchor']['center']): f['anchor'] for f in layout['clusters'] if 'anchor' in f}
    targets = {tuple(anchor['center']): anchor}
    targets.update({c:a for c,a in anchors.items() if a.get('owner') == row['owner']})
    walk,_ = rules.geometry.load_terrain(chk);worker = rules._worker_terrain(walk)
    army = rules._worker_terrain(rules._worker_terrain(worker))
    boxes,_ = rules.geometry.load_unit_geometry();buildable = rules.mining.load_buildable_grid(chk)
    explicit, critical = rules._critical_locations(chk, info)
    virtual = [a for a in anchors.values() if a['kind'] == 'expansion']
    known = set(rules._gas_state(info, list(anchors.values()), worker, boxes))
    assigned = {g['unit_index']:tuple(g.get('anchor',{}).get('center',())) for g in layout['gas_fields']}
    origin = {m['unit_index']:m['from'] for m in layout['moves']}
    reports = [];claimed=set();reserved_addons=addons.reservations(info)
    for center, own in targets.items():
        indices = [i for i,p in enumerate(info) if p[2] == 188 and
                   (assigned.get(i) == center or (math.dist(p[:2],center)<=RADIUS and
                    min(anchors, key=lambda c:math.dist(p[:2],c), default=center)==center))]
        if center==tuple(anchor['center']):indices=sorted(set(indices)|{i for i in gas_indices(info,own,worker,boxes) if info[i][2]==188})
        for index in indices:
            if index in claimed:continue
            claimed.add(index)
            initial = info[index];failures = defaultdict(int);accepted = False
            if index in explicit:
                reports.append(dict(unit_index=index,status='scripted_resource_position_preserved'));continue
            if math.dist(initial[:2],center)<=224 and direct_lane(own,initial[:2],info,index,worker,boxes) and addons.resource_clear(initial[:2],188,reserved_addons):
                reports.append(dict(unit_index=index,anchor=list(center),from_position=list(initial[:2]),position=list(initial[:2]),status='direct_mining_lane',moved=False,distance_pixels=round(math.dist(initial[:2],center),6)))
                continue
            for point in candidates(own, info,index):
                if not addons.resource_clear(point,188,reserved_addons):
                    failures['addon_parent_landing_space'] += 1;continue
                if math.dist(point, origin.get(index, initial[:2])) > rules.MAX_DISPLACEMENT:
                    continue
                if not direct_lane(own, point, info, index, worker, boxes):
                    failures['mineral_or_building_detour'] += 1;continue
                if not ladder._geometry(info,[index],[point],walk,boxes,reserved_points,buildable,chk,failures):
                    continue
                proposed = list(info);proposed[index] = (*point,*initial[2:])
                centers = [c for c in layout['reserved_resource_depot_centers'] if rules._resource_clear(c, info)]
                if any(not rules._resource_clear(c,proposed) for c in centers):
                    failures['depot_rebuilding'] += 1;continue
                if not rules._critical_membership(chk,info,proposed,[index],critical):
                    failures['scripted_resource_location'] += 1;continue
                if index not in gas_indices(proposed,own,worker,boxes):
                    failures['gas_return_route'] += 1;continue
                affected = [f for f in layout['clusters'] if 'anchor' in f and
                            any(math.dist(point,info[i][:2])<768 for i in f['unit_indices'])]
                if any(not rules._access(proposed,f['unit_indices'],f['anchor'],f['direction'],worker,boxes,virtual_anchors=virtual)[0] for f in affected):
                    failures['mineral_front_access'] += 1;continue
                if not known <= set(rules._gas_state(proposed,list(anchors.values()),worker,boxes)):
                    failures['other_gas_access'] += 1;continue
                if not rules._army_route_ok(info,proposed,[index],army,boxes,{'baseline':info}):
                    failures['large_army_route'] += 1;continue
                raw = bytearray(records[index]);struct.pack_into('<HH',raw,4,*point);records[index] = bytes(raw);info = proposed
                reports.append(dict(unit_index=index,anchor=list(center),from_position=list(initial[:2]),position=list(point),
                                    status='direct_mining_lane',moved=tuple(point)!=tuple(initial[:2]),distance_pixels=round(math.dist(point,center),6),rejected_candidates=dict(failures)))
                accepted = True;break
            if not accepted:
                reports.append(dict(unit_index=index,anchor=list(center),position=list(initial[:2]),status='terrain_or_script_constraints',rejected_candidates=dict(failures)))
    chk.setsection('UNIT',b''.join(records));return reports


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
    report['positioning'] = move_existing(chk,row,layout,reserved_points)
    report['original_records_unchanged'] = not any(p.get('moved') for p in report['positioning'])
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
    reserved_addons=addons.reservations(info)
    while len(gas_indices(info, anchor, worker, boxes)) < 2:
        accepted = False
        army_cache = {"baseline": info}
        for point in candidates(anchor, info):
            if not addons.resource_clear(point,188,reserved_addons):
                failures['addon_parent_landing_space'] += 1;continue
            index = len(info)
            if not direct_lane(anchor,point,info,index,worker,boxes):
                failures['mineral_or_building_detour'] += 1
                continue
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
