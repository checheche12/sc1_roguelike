"""Joint mineral arcs and flanking gas, after the functional field planner.

Only existing resource coordinates move. Each accepted base retains mineral
front access, refinery foundations, depot rebuilding and original army routes.
"""
from __future__ import annotations
from collections import defaultdict
import copy
import math
from itertools import chain

try:
    from . import resource_layout as rules
except ImportError:
    import resource_layout as rules

VERSION = 'joint_ladder_arcs_flanking_gas_v1'


def formations(count, gas_count, anchor, direction, tangent_shift=0):
    ax, ay = anchor['center']
    dx, dy = direction
    vertical = bool(dx)
    rows = 1 if count <= 12 else 2 if count <= 24 else 3
    lengths = [count // rows + (row < count % rows) for row in range(rows)]
    distances = (288, 256, 320, 352) if vertical else (256, 224, 288, 320)
    for distance in distances:
        for depth in (64, 96):
            minerals = []
            for row, size in enumerate(lengths):
                step, inner = (32, 64) if vertical else (64, 64)
                left = size // 2
                tangents = [-inner - (left - 1 - i) * step for i in range(left)]
                tangents += [inner + i * step for i in range(size - left)]
                outer = max(map(abs, tangents), default=1)
                for tangent in tangents:
                    normal = distance + row * (128 if vertical else 96) - round(depth * (abs(tangent) / outer) ** 2 / 32) * 32
                    x = ax + dx * normal if vertical else ax + tangent + tangent_shift
                    y = ay + tangent + tangent_shift if vertical else ay + dy * normal
                    # A half-grid anchor must translate every row uniformly.
                    # Banker's rounding alternates ties and merges adjacent nodes.
                    minerals.append((math.floor(x / 32 + 0.5) * 32,
                                     math.floor((y - 16) / 32 + 0.5) * 32 + 16))
            if len(set(minerals)) != count or any(math.dist(p, (ax, ay)) > 560 for p in minerals):
                continue
            for extra, normal in ((0, 96), (32, 64), (64, 128)):
                tangent = (224 if vertical else 256) + extra
                flanks = [(round((ax + dx * normal if vertical else ax + sign * tangent) / 32) * 32,
                           round((ay + sign * tangent if vertical else ay + dy * normal) / 32) * 32) for sign in (-1, 1)]
                choices = [flanks] if gas_count == 2 else [[p] for p in flanks] if gas_count else [[]]
                for gases in choices:
                    yield minerals, gases, dict(formation='ladder_arc', direction=[dx, dy], rows=rows,
                        row_lengths=lengths, row_spacing_pixels=128 if vertical else 96,
                        curve_depth_pixels=depth, normal_distance_pixels=distance,
                        central_army_aisle_pixels=64, gas_flanks=True, tangent_shift_pixels=tangent_shift)


def _geometry(info, indices, points, walk, boxes, reserved, buildable, chk, failures):
    def reject(reason):failures[reason]+=1;return False
    occupied = rules._collision_index(info, indices, boxes)
    rectangles = []
    for index, point in zip(indices, points):
        unit = info[index][2]
        rect = rules.geometry._rect(*point, unit, boxes)
        if not rules.geometry._walkable_rect(walk, rect):
            return reject('terrain')
        if unit == rules.GEYSER and not rules._foundation(chk, point, unit, buildable):
            return reject('gas_foundation')
        if any(rect[0]-24 < x < rect[2]+24 and rect[1]-24 < y < rect[3]+24 for x,y in reserved):
            return reject('reserved_spawn_or_worker_point')
        if any(rules.geometry._overlap(rect, other)
               for yy in range(rect[1]//64, (rect[3]-1)//64+1)
               for xx in range(rect[0]//64, (rect[2]-1)//64+1) for other in occupied.get((xx,yy), ())):
            return reject('fixed_occupancy')
        if any(rules.geometry._overlap(rect, other) for other in rectangles):
            return reject('resource_overlap')
        rectangles.append(rect)
    return True


def refine(chk, info, original, fields, anchors, clear_depots, worker_walk, army_walk,
           raw_walk, boxes, buildable, explicit, critical_locations, reserved, army_cache):
    groups = defaultdict(list)
    for field in fields:
        if field['status'].startswith('functional_') and not field.get('resource_trigger_position_preserved'):
            groups[tuple(field['anchor']['center'])].append(field)
    centers = list(groups)
    gas_by_base = defaultdict(list)
    for index, item in enumerate(info):
        if item[2] != rules.GEYSER or index in explicit or not centers:
            continue
        center = min(centers, key=lambda p: math.dist(p, item[:2]))
        if math.dist(center, item[:2]) <= 768:
            gas_by_base[center].append(index)
    known_gas = set(rules._gas_state(info, anchors, worker_walk, boxes))
    reports = []
    for center, own_fields in groups.items():
        indices = sorted({i for field in own_fields for i in field['unit_indices']})
        report = dict(anchor=list(center), mineral_indices=indices, status='functional_layout_retained', reasons={})
        reports.append(report)
        if len(indices) < 3 or len(indices) > 36 or set(indices) & explicit:
            report['reason'] = 'small_or_protected_field'
            continue
        gases = sorted(gas_by_base[center], key=lambda i: math.dist(center, info[i][:2]))[:2]
        report['gas_indices'] = gases
        anchor = own_fields[0]['anchor']
        centroid = (sum(info[i][0] for i in indices)/len(indices), sum(info[i][1] for i in indices)/len(indices))
        primary = rules._direction(center, centroid)
        directions = sorted(((0,-1),(0,1),(-1,0),(1,0)), key=lambda d: (d != primary, d))
        failures = defaultdict(int)
        moving = indices + gases
        accepted = False
        for direction in directions:
            along = centroid[1]-center[1] if direction[0] else centroid[0]-center[0]
            preferred = max(-192,min(192,round(along/64)*64))
            shifts = list(dict.fromkeys((0,preferred,-64,64,-128,128,-192,192)))
            for minerals, gas_points, shape in chain.from_iterable(formations(len(indices), len(gases), anchor, direction, shift) for shift in shifts):
                chosen = rules._assignment([info[i][:2] for i in indices], minerals)
                gas_choice = rules._assignment([info[i][:2] for i in gases], gas_points) if gases else ([],0)
                if chosen is None or gas_choice is None:
                    continue
                points = chosen[0] + gas_choice[0]
                if any(math.dist(original[i][:2], p) > rules.MAX_DISPLACEMENT for i,p in zip(moving, points)):
                    continue
                if not _geometry(info, moving, points, raw_walk, boxes, reserved, buildable, chk, failures):
                    continue
                candidate = list(info)
                for i,p in zip(moving, points):candidate[i] = (*p, *info[i][2:])
                if any(not rules._resource_clear(p, candidate) for p in clear_depots):
                    failures['depot_rebuild'] += 1;continue
                if not rules._critical_membership(chk, info, candidate, moving, critical_locations):
                    failures['scripted_resource_location'] += 1;continue
                proofs = []
                for field in fields:
                    axis = shape['direction'] if field in own_fields else field['direction']
                    okay, proof = rules._access(candidate, field['unit_indices'], field['anchor'], axis,
                                                worker_walk, boxes, virtual_anchors=anchors)
                    if not okay:break
                    proofs.append(proof)
                else:
                    okay = True
                if not okay:
                    failures['worker_front_access'] += 1;continue
                if not rules._army_route_ok(info, candidate, moving, army_walk, boxes, army_cache):
                    failures['army_route'] += 1;continue
                gas_state = rules._gas_state(candidate, anchors, worker_walk, boxes)
                if not known_gas <= set(gas_state):
                    failures['gas_return_route'] += 1;continue
                if any(i not in gas_state or tuple(gas_state[i]['anchor']['center']) != center for i in gases):
                    failures['gas_different_base'] += 1;continue
                for field,proof in zip(fields,proofs):field['front_access'] = proof
                for field in own_fields:
                    field.update(status='functional_ladder_arc', **shape)
                    field['changed'] = any(original[i][:2] != candidate[i][:2] for i in field['unit_indices'])
                info = candidate;known_gas = set(gas_state)
                report.update(status='joint_ladder_arc', mineral_positions=[list(info[i][:2]) for i in indices],
                              gas_positions=[list(info[i][:2]) for i in gases], **shape)
                accepted = True;break
            if accepted:break
        report['reasons'] = dict(failures)
        if not accepted:report['reason'] = 'terrain_occupancy_or_access_constraints'
    return info, reports


def apply_to_functional_map(chk, report, row=None):
    """Offline continuation of an exact existing functional map receipt."""
    import struct
    before = chk.getsection('UNIT')
    if rules._hash(before) != report['output_unit_sha256']:
        raise ValueError('Functional resource receipt does not match the input map')
    info = list(map(rules.geometry._info, rules.geometry._records(chk)))
    original = list(info)
    for move in report['moves']:
        i=move['unit_index'];original[i]=(*move['from'],*original[i][2:])
    walk,_=rules.geometry.load_terrain(chk);worker=rules._worker_terrain(walk);army=rules._worker_terrain(rules._worker_terrain(worker))
    boxes,_=rules.geometry.load_unit_geometry();buildable=rules.mining.load_buildable_grid(chk)
    explicit,locations=rules._critical_locations(chk,original)
    result=copy.deepcopy(report);fields=[f for f in result['clusters'] if f['status'].startswith('functional_')]
    by_center={tuple(f['anchor']['center']):f['anchor'] for f in fields}
    for gas in result['gas_fields']:
        if 'anchor' in gas:by_center.setdefault(tuple(gas['anchor']['center']),gas['anchor'])
    anchors=list(by_center.values())
    info,baselines=refine(chk,info,original,fields,anchors,result['reserved_resource_depot_centers'],worker,army,
        walk,boxes,buildable,explicit,locations,result['reserved_points'],{'baseline':original})
    raw=bytearray(before)
    for i,item in enumerate(info):struct.pack_into('<HH',raw,i*36+4,*item[:2])
    rules.verify_only_resource_coordinates(before,raw);chk.setsection('UNIT',raw)
    result['algorithm']=VERSION;result['ladder_bases']=baselines;result['output_unit_sha256']=rules._hash(raw)
    result['moves']=[dict(unit_index=i,unit_type=a[2],owner=a[3],**{'from':list(a[:2]),'to':list(b[:2])},displacement_pixels=round(math.dist(a[:2],b[:2]),6)) for i,(a,b) in enumerate(zip(original,info)) if a[:2]!=b[:2]]
    result['moved_indices']=[m['unit_index'] for m in result['moves']];result['moved_count']=len(result['moves']);result['changed']=bool(result['moves'])
    state=rules._gas_state(info,anchors,worker,boxes)
    for gas in result['gas_fields']:
        i=gas['unit_index'];gas.update(position=list(info[i][:2]),changed=info[i][:2]!=original[i][:2],**state.get(i,{}))
    return result
