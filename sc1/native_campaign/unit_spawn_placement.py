"""Repair ground troop collisions after every resource/building placement pass.

Only mobile XY can change. Existing actors move only if a new or relocated
obstacle now intersects their actual collision box. Unit counts, properties,
resources and scripts stay byte-identical. The final check uses
the whole units.dat collision box, including its corners, against terrain
and ground obstacles. Flying units and turret subunits are separate layers.
"""
from collections import deque
from functools import lru_cache
import hashlib
from pathlib import Path
import struct

from . import mineral_layout as geo
from . import scripted_openings, ladder_resource_banks as banks
from .build_managed_dat import legacy_fields, source_bytes

VERSION = 'added_ground_footprints_20261107'
MAX_MOVE = 256


@lru_cache(maxsize=1)
def unit_flags():
    data = legacy_fields('units', source_bytes('units'))[22][1]
    return struct.unpack('<228I', data)


def grounded(unit):
    return 0 <= unit < 214 and not unit_flags()[unit] & (4 | 16)


def original_count(mission):
    return len(original_points(mission))


def original_points(mission):
    from .build_plain_chk import CHK
    raw = Path(mission['source']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == mission['source_sha256']
    return list(map(geo._info,geo._records(CHK(raw))))


@lru_cache(maxsize=1)
def engine_boxes():
    data=legacy_fields('units',source_bytes('units'))[38][1]
    result={}
    for unit in range(228):
        l,t,r,b=struct.unpack_from('<4H',data,unit*8)
        result[unit]=(l,t,r+1,b+1)
    return result


def spatial_selectors(chk, unit, owner):
    from . import build_all_campaigns as maps
    result = set()
    # These repaired actors are mobile: Buildings/Factories do not select them.
    for trigger in maps.triggers(chk):
        executors = [p for p in range(8) if maps.trigger_has_player(chk,trigger,p)]
        def owned(selector):
            return any(owner in maps.players_for(chk,selector,p) for p in executors)
        for _, c in maps.conditions(trigger):
            if c[15] in (3,7,16,17) and struct.unpack_from('<H',c,12)[0] in (unit,229,230) and owned(struct.unpack_from('<I',c,4)[0]):
                result.add(struct.unpack_from('<I',c)[0])
        for _, a in maps.actions(trigger):
            if a[26] in (23,25,38,39,43,44,46,48,49,50,51,52,53) and struct.unpack_from('<H',a,24)[0] in (unit,229,230) and owned(struct.unpack_from('<I',a,16)[0]):
                result.add(struct.unpack_from('<I',a)[0])
                if a[26] in (39,46):
                    result.add(struct.unpack_from('<I',a,20)[0])
    return {loc for loc in result if 0 < loc <= len(chk.getsection('MRGN'))//20}


class Field:
    def __init__(self, chk):
        self.points = list(map(geo._info, geo._records(chk)))
        self.boxes = geo.load_unit_geometry()[0]
        self.walk = geo.load_terrain(chk)[0]
        self.heights = banks.terrain_heights(chk)
        self.buckets = {}
        for i, p in enumerate(self.points):
            if grounded(p[2]):
                self.insert(i)

    def rect(self, p):
        return geo._rect(*p[:3], self.boxes)

    def cells(self, rect):
        l, t, r, b = rect
        return [(x, y) for y in range(t // 128, (b-1) // 128+1)
                for x in range(l // 128, (r-1) // 128+1)]

    def insert(self, i):
        for cell in self.cells(self.rect(self.points[i])):
            self.buckets.setdefault(cell, set()).add(i)

    def move(self, i, p):
        for cell in self.cells(self.rect(self.points[i])):
            self.buckets[cell].remove(i)
        self.points[i] = p
        self.insert(i)

    def problems(self, i, p=None, gap=0):
        p = p or self.points[i]
        rect = self.rect(p)
        reasons = []
        if not geo._walkable_rect(self.walk, rect):
            reasons.append('terrain_or_map_edge')
        l, t, r, b = rect
        padded = l-gap, t-gap, r+gap, b+gap
        nearby = set().union(*(self.buckets.get(c, set()) for c in self.cells(padded)))
        hits = sorted(j for j in nearby if j != i and geo._overlap(padded, self.rect(self.points[j])))
        if hits:
            reasons.append('ground_overlap')
        return reasons, hits

    def original_conflicts(self, original):
        """Actual engine collisions newly introduced by edited obstacles."""
        boxes=engine_boxes();result={}
        for i,a in enumerate(self.points[:len(original)]):
            if a[2]>=106 or not grounded(a[2]):continue
            rect=geo._rect(*a[:3],boxes)
            nearby=set().union(*(self.buckets.get(c,set()) for c in self.cells(rect)))
            for j in sorted(nearby):
                b=self.points[j]
                if b[2]<106 or not geo._overlap(rect,geo._rect(*b[:3],boxes)):continue
                if j<len(original) and geo._overlap(geo._rect(*original[i][:3],boxes),geo._rect(*original[j][:3],boxes)):continue
                result.setdefault(i,[]).append(j)
        return result

    def reachable(self, p):
        """Keep the new centre in the same nearby terrain component/height."""
        sx, sy = p[0] // 8, p[1] // 8
        h, w = len(self.walk), len(self.walk[0])
        level = self.heights[sy][sx]
        seen = {(sx, sy)}
        queue = deque(seen)
        while queue:
            x, y = queue.popleft()
            for nx, ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if ((nx,ny) in seen or not 0 <= nx < w or not 0 <= ny < h
                        or abs(nx-sx) > MAX_MOVE//8 or abs(ny-sy) > MAX_MOVE//8
                        or not self.walk[ny][nx] or self.heights[ny][nx] != level):
                    continue
                seen.add((nx,ny)); queue.append((nx,ny))
        return seen


def apply(chk, mission, report, *, reserved_points=()):
    """Extend the reversible final placement report, leaving its input intact."""
    assert 'spawn_placement' not in report, 'Placement repair must run exactly once'
    before = chk.getsection('UNIT')
    assert geo._sha(before) == report['output_unit_sha256']
    field = Field(chk)
    original=original_points(mission);count=len(original)
    original_conflicts=field.original_conflicts(original)
    additions = [i for i, p in enumerate(field.points) if i >= count and p[2] < 106 and grounded(p[2])]
    selected = sorted(original_conflicts)+additions
    moves = []
    selectors = {}
    regions = chk.getsection('MRGN')
    protected = [p[:2] for p in field.points[:count] if p[3] == mission['owner'] and p[2] != 214]
    for i in selected:
        old = field.points[i]
        reasons, hits = field.problems(i)
        if not reasons:
            continue
        if old[2:] not in selectors:
            selectors[old[2:]] = [struct.unpack_from('<4I', regions, (loc-1)*20)
                                for loc in spatial_selectors(chk,*old[2:])]
        rects = selectors[old[2:]]
        membership = lambda p: tuple(l <= p[0] <= r and t <= p[1] <= b for l,t,r,b in rects)
        old_membership = membership(old)
        connected = field.reachable(old)
        minimum_friend = min([512**2] + [(old[0]-x)**2+(old[1]-y)**2 for x,y in protected])
        offsets = sorted(((x-old[0])**2+(y-old[1])**2,y-old[1],x-old[0])
                         for y in range((old[1]-MAX_MOVE)//4*4,old[1]+MAX_MOVE+1,4)
                         for x in range((old[0]-MAX_MOVE)//4*4,old[0]+MAX_MOVE+1,4)
                         if 0 < (x-old[0])**2+(y-old[1])**2 <= MAX_MOVE**2)
        for _, dy, dx in offsets:
            candidate = old[0]+dx, old[1]+dy, old[2], old[3]
            x, y = candidate[:2]
            if (x//8,y//8) not in connected or membership(candidate) != old_membership:
                continue
            if (not scripted_openings.additional_spawn_allowed(mission,x,y)
                    and (i>=count or scripted_openings.additional_spawn_allowed(mission,*old[:2]))):
                continue
            if any((x-a)**2+(y-b)**2 < minimum_friend for a,b in protected):
                continue
            if any((x-a)**2+(y-b)**2 < 40**2 for a,b in reserved_points):
                continue
            if field.problems(i,candidate,gap=4)[0]:
                continue
            field.move(i,candidate)
            moves.append(dict(index=i,unit=old[2],owner=old[3],before=list(old[:2]),after=[x,y],
                              reasons=reasons,blocked_by=hits,original_actor=i<count,
                              introduced_obstacles=original_conflicts.get(i,[])))
            break
        else:
            raise AssertionError(('No safe local position for ground unit',mission['mission_id'],i,old,reasons,hits))
    for i in selected:
        assert not field.problems(i)[0], (mission['mission_id'],i,field.problems(i))
    raw = bytearray(before)
    prior = {m['index']: m for m in report['moves']}
    for move in moves:
        i = move['index']
        struct.pack_into('<HH',raw,i*36+4,*move['after'])
        if i in prior:
            prior[i]['after'] = move['after']
        else:
            prior[i] = {k:move[k] for k in ('index','before','after')}
    for i in range(len(field.points)):
        assert raw[i*36:i*36+4]+raw[i*36+8:i*36+36] == before[i*36:i*36+4]+before[i*36+8:i*36+36]
        if i<count and i not in original_conflicts:assert raw[i*36:i*36+36]==before[i*36:i*36+36]
    assert not field.original_conflicts(original)
    chk.setsection('UNIT',bytes(raw))
    report['moves'] = [prior[i] for i in sorted(prior)]
    report['output_unit_sha256'] = geo._sha(raw)
    report['spawn_placement'] = dict(version=VERSION,original_unit_count=count,checked_added_ground_units=len(additions),
        checked_original_ground_units=sum(p[2]<106 and grounded(p[2]) for p in original),
        moved_original_units=sum(m['original_actor'] for m in moves),new_original_obstacle_collisions=0,
        moved_units=len(moves),moves=moves,input_unit_sha256=geo._sha(before),output_unit_sha256=geo._sha(raw),
        collision_free=True,full_footprints_walkable=True,original_actors_preserved=True,
        counts_and_properties_preserved=True,trigger_region_membership_preserved=True,
        same_local_terrain_component=True,maximum_move_pixels=MAX_MOVE,live_gameplay_verified=False)
    return report


def verify(chk, mission, report):
    field = Field(chk)
    count = original_count(mission)
    selected = [i for i,p in enumerate(field.points) if i >= count and p[2] < 106 and grounded(p[2])]
    for i in selected:
        assert not field.problems(i)[0], (mission['mission_id'],i,field.problems(i))
    proof = report['spawn_placement']
    assert not field.original_conflicts(original_points(mission)),mission['mission_id']
    for move in proof['moves']:
        if move['original_actor']:assert not field.problems(move['index'])[0]
    assert proof['version'] == VERSION and proof['checked_added_ground_units'] == len(selected)
    assert geo._sha(chk.getsection('UNIT')) == proof['output_unit_sha256'] == report['output_unit_sha256']
    return len(selected)
