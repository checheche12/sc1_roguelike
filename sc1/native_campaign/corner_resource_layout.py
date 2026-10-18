"""Compact mineral banks on two perpendicular sides of a legal depot site."""
from __future__ import annotations

from collections import defaultdict
import copy
import math
from pathlib import Path
import struct

from . import resource_layout as rules
from . import mining_layout_audit as mining
from . import resource_depot_placement as depots

VERSION = 'compact_corner_minerals_v1'


def _formations_for_rows(count, center, rows):
    """A mineral occupies 64x32px; every third/fourth node leaves an aisle."""
    ax, ay = center
    lengths = [count // rows + (i < count % rows) for i in range(rows)]
    seen = set()
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        for extra_x, extra_y in ((0, 0), (32, 0), (0, 32), (32, 32), (64, 0), (0, 64), (64, 64)):
            for horizontal_delta in (0, -1, 1, -2, 2):
                points = []
                arms = []
                for row, size in enumerate(lengths):
                    horizontal = max(2, min(size - 1, round(size * .42) + horizontal_delta))
                    vertical = size - horizontal
                    x = 192 + extra_x + row * 128
                    y = 160 + extra_y + row * 96
                    for i in range(horizontal):
                        tangent = i * 64 + (32 if i else 0) + (i // 3) * 32
                        points.append((ax + sx * (x - tangent), ay + sy * y))
                    for i in range(vertical):
                        tangent = (i + 2) * 32 + ((i + 1) // 4) * 32
                        points.append((ax + sx * x, ay + sy * (y - tangent)))
                    arms.append([horizontal, vertical])
                points = tuple(rules._snap(x, y) for x, y in points)
                if len(set(points)) != count or points in seen:
                    continue
                seen.add(points)
                yield points, dict(formation='mineral_corner', corner=[sx, sy], rows=rows,
                                  arm_lengths=arms, horizontal_step=64, vertical_step=32,
                                  worker_aisle_pixels=32)
    # Cliff-side bases may have room on only one side. Bend the end of that
    # bank outward instead of requiring two adjacent sides of the headquarters.
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        horizontal = not dx
        step = 64 if horizontal else 32
        normal_minimum = 160 if horizontal else 192
        for hook in (2, 3, 4, 1, 5, 6):
            if any(size <= hook + 1 for size in lengths):
                continue
            for sign in (-1, 1):
                for distance in (normal_minimum, normal_minimum+32, normal_minimum+64):
                    for shift in (0, -64, 64, -128, 128, -192, 192):
                        points = []
                        arms = []
                        for row, size in enumerate(lengths):
                            bank = size-hook
                            span = (bank-1)*step + ((bank-1)//3)*32
                            edge = sign*round(span/2/32)*32 + shift
                            normal = distance+row*(96 if horizontal else 128)
                            for i in range(bank):
                                tangent = edge-sign*(i*step+(i//3)*32)
                                points.append((ax+tangent, ay+dy*normal) if horizontal
                                              else (ax+dx*normal, ay+tangent))
                            for i in range(hook):
                                outward = normal+(i+2)*(32 if horizontal else 64)
                                hook_edge=edge+sign*(96 if horizontal else 64)
                                points.append((ax+hook_edge, ay+dy*outward) if horizontal
                                              else (ax+dx*outward, ay+hook_edge))
                            arms.append([bank,hook])
                        points = tuple(rules._snap(x,y) for x,y in points)
                        if len(set(points))!=count or points in seen:
                            continue
                        seen.add(points)
                        yield points,dict(formation='mineral_corner_bank',direction=[dx,dy],
                            bend_side=sign,rows=rows,arm_lengths=arms,worker_aisle_pixels=32)


def formations(count, center):
    row_options=(1,2) if 12<=count<=20 else (2,3) if count>30 else (2,) if count>20 else (1,)
    for rows in row_options:
        yield from _formations_for_rows(count,center,rows)


def terrain_fitted_formations(info, indices, center, walk, boxes, reserved, occupied):
    """Skip cliff/building cells along the two arms instead of rejecting a bank."""
    ax, ay = center
    count = len(indices)
    for sx, sy in ((-1,-1),(1,-1),(-1,1),(1,1)):
        for gap_x, gap_y in ((96,64),(64,64),(96,32),(64,32)):
            for offset_x,offset_y in ((0,0),(32,0),(0,16),(32,16),(64,0),(0,64),(64,64),(96,0),(0,96),(32,64),(64,32)):
                pool = []
                for row in range(4 if count>20 else 3):
                    xwall = ax+sx*(192+row*128+offset_x)
                    ywall = ay+sy*(160+row*96+offset_y)
                    for k in range(-7,8):
                        for point,arm in (((ax+k*gap_x,ywall),'horizontal'),
                                          ((xwall,ay+k*gap_y),'vertical')):
                            point=rules._snap(*point)
                            if rules._geometry_ok(info,indices,[point],walk,boxes,reserved,occupied):
                                pool.append((math.dist(center,point),point,arm))
                for preference in (0,1,2):
                    chosen=[]
                    counts=defaultdict(int)
                    for _,point,arm in sorted(set(pool),key=lambda p:(p[0]+(24 if preference==1 and p[2]=='vertical' or preference==2 and p[2]=='horizontal' else 0),p[1],p[2])):
                        rect=rules.geometry._rect(*point,176,boxes)
                        if any(rules.geometry._overlap(rect,rules.geometry._rect(*p,176,boxes)) for p in chosen):
                            continue
                        chosen.append(point)
                        counts[arm]+=1
                        if len(chosen)==count:
                            break
                    if len(chosen)==count and min(counts.values(),default=0)>=2 and len(counts)==2:
                        yield tuple(chosen),dict(formation='terrain_fitted_corner',corner=[sx,sy],
                            arm_lengths=dict(counts),worker_aisle_pixels=min(gap_x-64,gap_y-32),
                            terrain_cells_skipped=True)


def worker_access(info, indices, anchor, walk, boxes):
    center = anchor['center']
    bounds = rules._bounds([info[i][:2] for i in indices] + [center], walk, 32)
    model = list(info)
    if anchor['kind'] == 'expansion':
        model.append((*center, anchor['depot_type'], 12))
    labels, _, _ = rules._components(walk, model, bounds, boxes)
    common = rules._perimeter_labels((*center, anchor['depot_type'], 12), labels, bounds, boxes)
    blocked = []
    for i in indices:
        direction = rules._direction(center, info[i][:2])
        front = rules._front_labels(info[i], direction, labels, bounds, boxes)
        if not front & common:
            blocked.append(i)
        common &= front
    return not blocked and bool(common), dict(all_mineral_fronts_reachable=not blocked and bool(common),
        blocked_indices=blocked, worker_clearance_pixels=24, bounds_8px=list(bounds))


def depot_sites(chk, info, anchor, buildable, boxes):
    center = anchor['center']
    tile = ((center[0] - 64) // 32, (center[1] - 48) // 32)
    size = struct.unpack('<HH', chk.getsection('DIM '))
    results = []
    for unit in depots.DEPOT_TYPES:
        terrain = mining.foundation_buildable(chk, center, unit, buildable)
        resources = tile not in depots.resource_forbidden_tiles(info, unit, size)
        occupied = []
        foundation = (center[0]-64,center[1]-48,center[0]+64,center[1]+48)
        placements=mining.stock_geometry()[0]
        for x, y, other, owner in info:
            if other < 106 or other == 214 or (x, y) == tuple(center) and other in rules.HEADQUARTERS:
                continue
            width,height=placements[other]
            if rules.geometry._overlap(foundation,(x-width//2,y-height//2,x+width//2,y+height//2)):
                occupied.append([x, y, other, owner])
        results.append(dict(unit=unit, center=list(center), top_left_tile=list(tile),
                            terrain_buildable=terrain, resource_clear=resources,
                            fixed_occupancy_clear=not occupied, blockers=occupied))
    return all(r['terrain_buildable'] and r['resource_clear'] and r['fixed_occupancy_clear'] for r in results), results


def apply(chk, mission, resource_report, *, reserved_points=()):
    before = chk.getsection('UNIT')
    records = rules.geometry._records(chk)
    info = list(map(rules.geometry._info, records))
    from .build_plain_chk import CHK
    source = rules.geometry._records(CHK(Path(mission['source']).read_bytes()))
    original = list(map(rules.geometry._info, source))
    walk, _ = rules.geometry.load_terrain(chk)
    worker = rules._worker_terrain(walk)
    army = rules._worker_terrain(rules._worker_terrain(worker))
    boxes, _ = rules.geometry.load_unit_geometry()
    buildable = mining.load_buildable_grid(chk)
    explicit, locations = rules._critical_locations(chk, original)
    groups = {}
    for field in resource_report['clusters']:
        if not field['status'].startswith('functional_') or 'anchor' not in field:
            continue
        key = tuple(field['anchor']['center'])
        group = groups.setdefault(key, dict(anchor=field['anchor'], indices=set()))
        group['indices'].update(field['unit_indices'])
    anchors = [group['anchor'] for group in groups.values()]
    gas_before = set(rules._gas_state(info, anchors, worker, boxes))
    reserved = tuple(map(tuple, reserved_points))
    army_cache = {'baseline': list(info)}
    reports = []
    for center, group in groups.items():
        indices = sorted(group['indices'])
        anchor = group['anchor']
        distances_before = [math.dist(center,info[i][:2]) for i in indices]
        report = dict(anchor=copy.deepcopy(anchor), indices=indices, status='pending', reasons={},
                      distance_before=[round(d,3) for d in distances_before])
        reports.append(report)
        if mission['mission_id']==201 and tuple(center)==(384,1680):
            report.update(status='opening_compact_bank_follows',reason='Zerg01 reviewed 11-node opening bank is applied after this pass')
            continue
        if len(indices) < 3 or set(indices) & explicit:
            report.update(status='small_or_scripted_field_preserved')
            continue
        failures = defaultdict(int)
        occupied = rules._collision_index(info, indices, boxes)
        candidates = list(terrain_fitted_formations(info,indices,center,walk,boxes,reserved,occupied))
        candidates += list(formations(len(indices), center))
        candidates.sort(key=lambda item: (max(math.dist(center, p) for p in item[0]),
                                           sum(math.dist(center, p) for p in item[0]),
                                           item[1].get('corner',item[1].get('direction'))))
        for points, shape in candidates:
            distances = [math.dist(center,p) for p in points]
            if (max(distances)>max(distances_before)+16 or
                    sum(distances)>sum(distances_before)*1.15+.01 or
                    sum(distances)>sum(distances_before)+.01 and max(distances)>max(distances_before)*.85):
                failures['longer_mining_distance'] += 1
                continue
            if not rules._geometry_ok(info, indices, points, walk, boxes, reserved, occupied):
                failures['terrain_or_occupancy'] += 1
                continue
            assignment = rules._assignment([info[i][:2] for i in indices], points)
            if assignment is None:
                failures['assignment'] += 1
                continue
            chosen = assignment[0]
            if any(math.dist(original[i][:2], p) > rules.MAX_DISPLACEMENT for i, p in zip(indices, chosen)):
                failures['original_displacement'] += 1
                continue
            candidate = list(info)
            for i, p in zip(indices, chosen):
                candidate[i] = (*p, *info[i][2:])
            if not rules._critical_membership(chk, info, candidate, indices, locations):
                failures['scripted_location'] += 1
                continue
            legal, sites = depot_sites(chk, candidate, anchor, buildable, boxes)
            if not legal:
                failures['depot_foundation'] += 1
                continue
            if any(not rules._resource_clear(a['center'], candidate) for a in anchors):
                failures['other_depot_blocked'] += 1
                continue
            accessible, access = worker_access(candidate, indices, anchor, worker, boxes)
            if not accessible:
                failures['worker_access'] += 1
                continue
            if not rules._army_route_ok(info, candidate, indices, army, boxes, army_cache):
                failures['army_route'] += 1
                continue
            if not gas_before <= set(rules._gas_state(candidate, anchors, worker, boxes)):
                failures['gas_access'] += 1
                continue
            report.update(status='compact_corner', positions=[list(candidate[i][:2]) for i in indices],
                distance_before=[round(math.dist(center, info[i][:2]),3) for i in indices],
                distance_after=[round(math.dist(center, candidate[i][:2]),3) for i in indices],
                depot_sites=sites, worker_access=access, **shape)
            info = candidate
            break
        if report['status'] == 'pending':
            report['status'] = 'compact_existing_bank' if max(distances_before)<=320 else 'constrained_field_retained'
            report['depot_sites'] = depot_sites(chk, info, anchor, buildable, boxes)[1]
        report['reasons'] = dict(failures)
    raw = bytearray(before)
    for i, item in enumerate(info):
        struct.pack_into('<HH', raw, i * 36 + 4, *item[:2])
    rules.verify_only_resource_coordinates(before, raw)
    amounts=[];mineral_amounts=[]
    if mission['mission_id']==402:
        # Original NW settlement geyser, independent of mineral/expansion order.
        index=20
        assert struct.unpack_from('<H',raw,index*36+8)[0]==188
        old=bytes(raw[index*36:(index+1)*36])
        struct.pack_into('<H',raw,index*36+14,struct.unpack_from('<H',raw,index*36+14)[0]|16)
        struct.pack_into('<I',raw,index*36+20,7000)
        amounts.append(dict(index=index,before_record=old.hex(),after_record=bytes(raw[index*36:(index+1)*36]).hex(),amount=7000))
        for index in (7,8,9,10,11,12,13,14,15,16,19):
            assert struct.unpack_from('<H',raw,index*36+8)[0] in mining.MINERALS
            old=bytes(raw[index*36:(index+1)*36])
            struct.pack_into('<H',raw,index*36+14,struct.unpack_from('<H',raw,index*36+14)[0]|16)
            struct.pack_into('<I',raw,index*36+20,5000)
            mineral_amounts.append(dict(index=index,before_record=old.hex(),after_record=bytes(raw[index*36:(index+1)*36]).hex(),amount=5000))
    moves = [dict(index=i, before=list(a[:2]), after=list(b[:2]))
             for i, (a, b) in enumerate(zip(map(rules.geometry._info, records), info)) if a[:2] != b[:2]]
    chk.setsection('UNIT', raw)
    return dict(version=VERSION, mission=mission['mission_id'], bases=reports, moves=moves,gas_amount_changes=amounts,mineral_amount_changes=mineral_amounts,
                input_unit_sha256=rules._hash(before), output_unit_sha256=rules._hash(raw),
                resource_counts_preserved=True,other_resource_amounts_preserved=True, native_mining_verified=False,
                native_can_build_verified=False)


def undo(chk, report):
    raw = bytearray(chk.getsection('UNIT'))
    assert rules._hash(raw) == report['output_unit_sha256']
    for change in report['gas_amount_changes']+report['mineral_amount_changes']:
        index=change['index'];assert raw[index*36:(index+1)*36].hex()==change['after_record']
        raw[index*36:(index+1)*36]=bytes.fromhex(change['before_record'])
    for move in report['moves']:
        assert list(struct.unpack_from('<HH', raw, move['index'] * 36 + 4)) == move['after']
        struct.pack_into('<HH', raw, move['index'] * 36 + 4, *move['before'])
    assert rules._hash(raw) == report['input_unit_sha256']
    chk.setsection('UNIT', raw)
