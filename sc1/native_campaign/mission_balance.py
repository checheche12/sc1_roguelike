"""Reviewed mission-specific garrisons and the original Zerg01 opening.

This final UNIT-only pass follows the generic mining repair. New garrisons are
ordinary preplaced enemies, never registered as native reinforcement waves.
The explicit per-map budget is additional to the earlier static additions.
"""
from __future__ import annotations
import hashlib
import math
import struct
from . import mineral_layout as geometry
from . import mining_layout_audit as mining
from . import resource_depot_placement as depots
from . import resource_layout

REVISION = 2026101714
# Fixed-army/infiltration maps and the two fragile Zerg openings are exempt.
# Values are counts, not a global percentage or a time-dependent wave multiplier.
GARRISONS = {
    101:6,102:10,103:12,104:0,105:18,106:20,107:24,108:24,109:28,110:36,
    201:0,202:8,203:14,204:10,205:0,206:22,207:20,208:18,209:28,210:32,
    301:6,302:12,303:16,304:12,305:20,306:0,307:28,308:22,309:28,310:32,
    401:0,402:12,403:16,404:0,405:0,406:28,407:18,408:24,
    501:0,502:0,503:20,504:28,505:28,515:28,506:24,507:0,508:32,
    601:0,602:0,603:20,604:28,614:28,615:28,616:28,617:28,618:28,
    605:24,606:24,607:16,608:18,609:24,610:32,611:0,
}
# Armed stock units only; no heroes, workers, spellcasters, ammunition or
# carriers/reavers that would require separate hangar initialization.
ARMED = frozenset((0,1,2,3,5,8,12,30,32,37,38,39,43,44,47,50,
                   58,60,61,62,65,66,68,70,103))
AIR = frozenset((8,12,43,44,47,58,60,62,70))
ZERG01_MINERALS = (87,88,89,90,91,92,93,95,96,97,98)
# Two compact rows with a 32px gap; the north exit stays open.
ZERG01_ARC = ((192,1840),(256,1840),(320,1840),(384,1840),(448,1840),
              (512,1840),(576,1840),(288,1904),(352,1904),(416,1904),(480,1904))

def sha(raw):return hashlib.sha256(raw).hexdigest()
def records(chk):return geometry._records(chk)
def info(raw):return geometry._info(raw)

class Placement:
    def __init__(self,chk):
        self.boxes,_=geometry.load_unit_geometry()
        self.walk,_=geometry.load_terrain(chk)
        self.width,self.height=struct.unpack('<HH',chk.getsection('DIM '))
        self.buckets={}
        for r in records(chk):
            x,y,u,p=info(r)
            if u!=214:self.add(x,y,u)
    def rect(self,x,y,u):return geometry._rect(x,y,u,self.boxes)
    def add(self,x,y,u):
        rect=self.rect(x,y,u)
        l,t,r,b=rect
        for yy in range(t//128,b//128+1):
            for xx in range(l//128,r//128+1):self.buckets.setdefault((xx,yy),[]).append(rect)
    def safe(self,x,y,u):
        rect=self.rect(x,y,u);l,t,r,b=rect
        if l<24 or t<24 or r>self.width*32-24 or b>self.height*32-24:return False
        if u not in AIR and not geometry._walkable_rect(self.walk,rect):return False
        # Reserve an eight-pixel gap instead of packing touching collision boxes.
        padded=(l-8,t-8,r+8,b+8)
        for yy in range((t-8)//128,(b+8)//128+1):
            for xx in range((l-8)//128,(r+8)//128+1):
                if any(geometry._overlap(padded,other) for other in self.buckets.get((xx,yy),())):return False
        return True

def add_record(source,x,y,serial):
    r=bytearray(source);struct.pack_into('<IHH',r,0,serial,x,y);return bytes(r)

def _garrisons(chk,row,difficulty):
    from . import scripted_openings
    target=GARRISONS[row['mission_id']]
    if row['no_production']:assert target==0
    if not target:return []
    raw=records(chk);original_count=difficulty['original_unit_records_preserved']
    hostile=set(difficulty['hostile_owners']);original=[info(r) for r in raw[:original_count]]
    # Only original hostile prototypes authorize a race, tech and placement area.
    sources=[(i,p) for i,p in enumerate(original) if p[3] in hostile and p[2] in ARMED]
    assert sources,('No armed source',row['mission_id'])
    bases=[p for p in original if p[3] in hostile and 106<=p[2]<176]
    def home(p):
        nearby=[b for b in bases if b[3]==p[3] and math.dist(b[:2],p[:2])<=768]
        return min(nearby,key=lambda b:math.dist(b[:2],p[:2]))[:2] if nearby else p[:2]
    # Interleave base clusters, retaining the original ground/air composition.
    groups={}
    for i,p in sources:groups.setdefault((p[3],*home(p)),[]).append((i,p))
    sources=[]
    for n in range(max(map(len,groups.values()))):
        sources.extend(group[n] for group in groups.values() if n<len(group))
    placement=Placement(chk)
    friendly=[p[:2] for p in original if p[3] not in hostile and p[3]<8 and p[2]!=214]
    reserved=[p for origin in difficulty['wave_origins'] for p in origin['cells']]
    serial=max(struct.unpack_from('<I',r)[0] for r in raw)+1;added=[];reports=[]
    offsets=sorted(((dx*dx+dy*dy,dy,dx) for dy in range(-320,321,32) for dx in range(-320,321,32)))
    # Revisit prototypes if a small original garrison needs several defenders.
    for source_index,p in sources*max(1,(target+len(sources)-1)//len(sources)+1):
        if len(added)==target:break
        sx,sy,u,owner=p
        for _,dy,dx in offsets:
            x,y=sx+dx,sy+dy
            if not scripted_openings.additional_spawn_allowed(row,x,y):continue
            if any((x-a)**2+(y-b)**2<512**2 for a,b in friendly):continue
            if any((x-a)**2+(y-b)**2<48**2 for a,b in reserved):continue
            if not placement.safe(x,y,u):continue
            new=add_record(raw[source_index],x,y,serial);serial+=1
            reports.append(dict(source_record=source_index,unit=u,owner=owner,source=[sx,sy],added=[x,y],role='ordinary_preplaced_garrison'))
            added.append(new);placement.add(x,y,u);break
    assert len(added)==target,('Garrison budget unresolved',row['mission_id'],target,len(added))
    chk.setsection('UNIT',b''.join(raw+added));return reports

def _zerg01(chk,row):
    raw=records(chk);before=list(map(info,raw));owner=row['owner']
    drones=[i for i,p in enumerate(before) if p[2:]==(41,owner)]
    assert len(drones)==2 and before[100]==(384,1680,131,owner)
    moved=[]
    # Match the new rows to the old minerals by nearest distance, preserving IDs,
    # amounts and all properties except XY. Keep every mineral within 256px.
    remaining=list(ZERG01_ARC)
    for i in sorted(ZERG01_MINERALS,key=lambda i:(before[i][0],before[i][1])):
        x,y,u,p=before[i];assert u in mining.MINERALS
        dest=min(remaining,key=lambda xy:(math.dist((x,y),xy),xy));remaining.remove(dest)
        r=bytearray(raw[i]);struct.pack_into('<HH',r,4,*dest);raw[i]=bytes(r)
        if (x,y)!=dest:moved.append(dict(index=i,before=[x,y],after=list(dest)))
    chk.setsection('UNIT',b''.join(raw));after=list(map(info,raw))
    # Validate the moved resource footprint independently of the old generic
    # layout policy, which deliberately prevented any newly restricted depot tile.
    boxes,_=geometry.load_unit_geometry();walk,_=geometry.load_terrain(chk)
    for i in ZERG01_MINERALS:
        x,y,u,p=after[i];rect=geometry._rect(x,y,u,boxes)
        assert geometry._walkable_rect(walk,rect),('Mineral terrain',i)
        for j,(xx,yy,unit,_) in enumerate(after):
            if j==i or unit==214:continue
            assert not geometry._overlap(rect,geometry._rect(xx,yy,unit,boxes)),('Mineral collision',i,j)
        assert math.dist((384,1680),(x,y))<=256
        assert math.dist(before[i][:2],(x,y))<=768
    anchor=dict(kind='player_base',center=[384,1680],depot_type=131,owner=owner)
    audit=mining.audit_field(chk,after,ZERG01_MINERALS,anchor,direction=(0,1))
    assert audit['foundation_terrain_buildable'] and audit['resource_depot_clear'] and audit['front_reachable_count']==11,audit
    _,locations=resource_layout._critical_locations(chk,before)
    assert resource_layout._critical_membership(chk,before,after,ZERG01_MINERALS,locations)
    army_walk=resource_layout._worker_terrain(mining._raw_walk(chk))
    assert resource_layout._army_route_ok(before,after,ZERG01_MINERALS,army_walk,boxes,{})
    # Explicitly account for the relaxed depot-grid invariant in this one map.
    map_size=struct.unpack('<HH',chk.getsection('DIM '))
    newly=depots.newly_blocked_depot_tiles(before,after,106,map_size)
    assert all(abs(x-10)<=16 and abs(y-51)<=16 for x,y in newly)
    for x,y,u,p in before:
        if u in mining.DEPOTS:
            w,h=mining.stock_geometry()[0][u];tile=((x-w//2)//32,(y-h//2)//32)
            assert tile not in newly,('Existing base rebuild blocked',tile)
    placement=Placement(chk);serial=max(struct.unpack_from('<I',r)[0] for r in raw)+1;workers=[]
    candidates=sorted(((x-384)**2+(y-1552)**2,y,x) for y in range(1456,1649,32) for x in range(224,577,32))
    for _,y,x in candidates:
        if len(workers)==8:break
        if not placement.safe(x,y,41):continue
        raw.append(add_record(raw[drones[0]],x,y,serial));serial+=1;placement.add(x,y,41);workers.append([x,y])
    assert len(workers)==8
    chk.setsection('UNIT',b''.join(raw))
    return dict(initial_drones_before=2,initial_drones_after=10,added_drones=workers,
        mineral_moves=moved,main_mineral_indices=list(ZERG01_MINERALS),
        mineral_distance_before=sorted(round(math.dist((384,1680),before[i][:2]),1) for i in ZERG01_MINERALS),
        mineral_distance_after=sorted(round(math.dist((384,1680),after[i][:2]),1) for i in ZERG01_MINERALS),
        mining_audit=audit,army_routes_preserved=True,resource_trigger_membership_preserved=True,
        newly_restricted_depot_tiles=[list(p) for p in newly],
        depot_grid_policy='Zerg01 main field only: closer minerals may restrict nearby hypothetical depot sites; existing depot rebuilds preserved',
        native_mining_verified=False)

def _terran03_gas(chk,row):
    """Raise only the original third mission's starting-base geyser reserve."""
    raw=records(chk);points=list(map(info,raw))
    assert (320,2704,106,row['owner']) in points, 'Terran03 starting command center changed'
    gases=[i for i,(x,y,u,p) in enumerate(points)
           if u==188 and math.dist((320,2704),(x,y))<=512]
    assert len(gases)==1, ('Terran03 starting geyser is ambiguous',gases)
    i=gases[0];before=struct.unpack_from('<I',raw[i],20)[0]
    assert before==1000, ('Unexpected Terran03 starting reserve',before)
    r=bytearray(raw[i]);struct.pack_into('<I',r,20,5000);raw[i]=bytes(r)
    chk.setsection('UNIT',b''.join(raw))
    return [dict(index=i,unit=188,position=list(points[i][:2]),before=before,after=5000)]


def _protoss08_main_resources(chk,row):
    """Add reserves to the sixteen minerals and two geysers of the starting base."""
    raw=records(chk);points=list(map(info,raw));center=(736,432)
    assert (*center,154,row['owner']) in points, 'Protoss08 starting nexus changed'
    selected=[i for i,(x,y,u,p) in enumerate(points)
              if u in (176,177,178,188) and math.dist(center,(x,y))<=512]
    assert sum(points[i][2]==188 for i in selected)==2 and len(selected)==18
    changes=[]
    for i in selected:
        r=bytearray(raw[i]);before=struct.unpack_from('<I',r,20)[0]
        assert struct.unpack_from('<H',r,14)[0]&16, 'Resource reserve must be explicit'
        bonus=2000 if points[i][2]==188 else 500
        struct.pack_into('<I',r,20,before+bonus);raw[i]=bytes(r)
        changes.append(dict(index=i,unit=points[i][2],position=list(points[i][:2]),before=before,after=before+bonus))
    chk.setsection('UNIT',b''.join(raw));return changes


def apply(chk,row,difficulty):
    before=chk.getsection('UNIT');before_records=records(chk)
    guards=_garrisons(chk,row,difficulty)
    opening=_zerg01(chk,row) if row['mission_id']==201 else None
    amounts=_terran03_gas(chk,row) if row['mission_id']==103 else []
    if row['mission_id']==308:amounts=_protoss08_main_resources(chk,row)
    after=chk.getsection('UNIT')
    report=dict(revision=REVISION,mission_id=row['mission_id'],
        requested_garrison=GARRISONS[row['mission_id']],garrison_added=len(guards),garrisons=guards,
        opening=opening,before_unit_sha256=sha(before),after_unit_sha256=sha(after),
        base_unit_count=len(before_records),appended_records=[r.hex() for r in records(chk)[len(before_records):]],
        ordinary_enemies=True,registered_as_added_wave=False,live_gameplay_verified=False)
    if amounts:report.update(revision=2026102378 if row['mission_id']==308 else 2026102201,resource_amount_changes=amounts)
    return report

def undo(chk,report):
    """Recover the exact generic-layout input, then let the caller replay both passes."""
    assert sha(chk.getsection('UNIT'))==report['after_unit_sha256']
    raw=records(chk);count=report['base_unit_count']
    assert [r.hex() for r in raw[count:]]==report['appended_records']
    raw=raw[:count]
    for change in report.get('resource_amount_changes',[]):
        r=bytearray(raw[change['index']]);assert struct.unpack_from('<I',r,20)[0]==change['after']
        struct.pack_into('<I',r,20,change['before']);raw[change['index']]=bytes(r)
    for move in (report.get('opening') or {}).get('mineral_moves',[]):
        r=bytearray(raw[move['index']]);assert list(struct.unpack_from('<HH',r,4))==move['after']
        struct.pack_into('<HH',r,4,*move['before']);raw[move['index']]=bytes(r)
    unit=b''.join(raw);assert sha(unit)==report['before_unit_sha256']
    chk.setsection('UNIT',unit)
