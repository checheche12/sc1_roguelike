"""Compact resources on one plateau, with gas outside the mineral bank.

Reference: installed ladder Fighting Spirit 1.3, Polypoid 1.65, Circuit Breaker
and Eclipse 1.2. Their mineral fronts occupy a short side arc, while the gas
has a separate depot-facing lane. Keep resource counts, amounts and scripts.
This is offline terrain/footprint validation, not native mining proof.
"""
from __future__ import annotations
from collections import defaultdict
from itertools import product
from pathlib import Path
import copy,math,struct
from functools import lru_cache

from . import resource_layout as rules,mining_layout_audit as mining
from . import courtyard_resource_layout as court,corner_resource_layout as corner
from . import main_base_gas as gas,ladder_resource_layout as ladder,addon_placement as addons

VERSION='ladder_curved_bank_separate_gas_v2'
REFERENCE_MAPS={
 'Fighting Spirit 1.3':'f39df27cea359b06f0775cdc34d427150d40e9eb33cc688bfb10b6b5a29ca34d',
 'Polypoid 1.65':'0071bea653a4c8572b228576c380af9f7e71f4928135b061d0db9f0db738b5a7',
 'Circuit Breaker':'ba956f73d18342f3f329741b684fd569e6bcf718b1fcebd86c2d965481260bc0',
 'Eclipse 1.2':'ca797ea09e9b4f82ca71d9ced7c958b575e774d49a47bd6bfc7cac666d21a8fa',
}
# Actual relative mineral coordinates of Fighting Spirit's northeast main.
REFERENCE_EAST=((192,96),(192,128),(160,160),(224,64),(224,0),(192,-32),(192,-96),(192,32),(224,-64))
MAX_DISPLACEMENT=1280
GAS_MINERAL_GAP=48

def terrain_heights(chk):
    width,height=struct.unpack('<HH',chk.getsection('DIM '))
    cv5,vf4=mining._terrain_bytes(int.from_bytes(chk.getsection('ERA '),'little')&7)
    tiles=struct.unpack('<'+'H'*(width*height),chk.getsection('MTXM'))
    result=[bytearray(width*4) for _ in range(height*4)];cache={}
    for i,tile in enumerate(tiles):
        if tile not in cache:
            mega=struct.unpack_from('<H',cv5,(tile>>4)*52+20+(tile&15)*2)[0]
            flags=struct.unpack_from('<16H',vf4,mega*32)
            cache[tile]=bytes(255 if not f&1 else 2 if f&4 else 1 if f&2 else 0 for f in flags)
        for dy in range(4):result[(i//width)*4+dy][(i%width)*4:(i%width)*4+4]=cache[tile][dy*4:dy*4+4]
    return result

def flat_rect(heights,rect,level):
    l,t,r,b=rect
    if l<0 or t<0 or r>len(heights[0])*8 or b>len(heights)*8:return False
    return all(heights[y][x]==level for y in range(t//8,(b+7)//8) for x in range(l//8,(r+7)//8))

def rect_gap(a,b):
    return math.hypot(max(0,a[0]-b[2],b[0]-a[2]),max(0,a[1]-b[3],b[1]-a[3]))

def native_rect_distance(a,b):
    """OpenBW units_distance/xy_length, using conservative placement boxes."""
    x=max(0,a[0]-b[2],b[0]-a[2]);y=max(0,a[1]-b[3],b[1]-a[3]);x,y=max(x,y),min(x,y)
    return x-x//16+y*3//8-x//64+y*3//256 if x//4<y else x


@lru_cache(maxsize=1)
def sunken_weapon():
    from .build_managed_dat import legacy_fields,source_bytes
    units=source_bytes('units');weapons=source_bytes('weapons')
    weapon=legacy_fields('units',units)[17][1][146]
    attack_range=struct.unpack_from('<I',legacy_fields('weapons',weapons)[5][1],weapon*4)[0]
    return dict(unit_id=146,weapon_id=weapon,range_pixels=attack_range,
                margin_pixels=32,worker_envelope_pixels=32,
                units_sha256=rules._hash(units),weapons_sha256=rules._hash(weapons))


def sunken_threats(info,owners,boxes):
    distance=sunken_weapon()['range_pixels']
    return [(rules.geometry._rect(x,y,u,boxes),distance) for x,y,u,p in info if u==146 and p in owners]


def sunken_clear(rect,threats,padding=32):
    l,t,r,b=rect;expanded=(l-padding,t-padding,r+padding,b+padding)
    return all(native_rect_distance(expanded,enemy)>distance+32 for enemy,distance in threats)


def sunken_safe_worker(worker,threats):
    safe=[bytearray(row) for row in worker];height,width=len(safe),len(safe[0])
    for rect,distance in threats:
        l,t,r,b=rect;pad=distance+48
        for y in range(max(0,(t-pad)//8),min(height,(b+pad)//8+1)):
            for x in range(max(0,(l-pad)//8),min(width,(r+pad)//8+1)):
                px,py=x*8+4,y*8+4
                if safe[y][x] and not sunken_clear((px-13,py-13,px+13,py+13),[(rect,distance)],padding=0):safe[y][x]=0
    return safe


def sunken_route_clear(center,point,threats):
    steps=max(1,math.ceil(math.dist(center,point)/8))
    return all(sunken_clear((x,y,x,y),threats) for x,y in (
        (round(center[0]+(point[0]-center[0])*t/steps),round(center[1]+(point[1]-center[1])*t/steps))
        for t in range(steps+1)))


def gas_separate(info,minerals,gases,boxes):
    rects=[rules.geometry._rect(*info[i][:2],info[i][2],boxes) for i in minerals]
    bounds=(min(r[0] for r in rects),min(r[1] for r in rects),max(r[2] for r in rects),max(r[3] for r in rects))
    return all(rect_gap(bounds,rules.geometry._rect(*info[j][:2],info[j][2],boxes))>=32 for j in gases) and all(rect_gap(rules.geometry._rect(*info[i][:2],info[i][2],boxes),
                        rules.geometry._rect(*info[j][:2],info[j][2],boxes))>=GAS_MINERAL_GAP
               for i in minerals for j in gases)

def curved_bank(points):
    """Reject straight or nearly straight fronts, including diagonal rows.

    The thinnest width of the convex hull must span three 8px terrain cells
    and at least 16% of the front's length. This prevents a long straight
    row with just one displaced end patch from being called a curved bank.
    The actual Fighting Spirit front exceeds this; a translated/rotated line
    cannot pass. One/two-patch scripted deposits cannot form a curve.
    """
    points=sorted(set(map(tuple,points)))
    if len(points)<3:return {'passed':True,'applicable':False,'minimum_width_pixels':0}
    cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    halves=[]
    for sequence in (points,list(reversed(points))):
        hull=[]
        for p in sequence:
            while len(hull)>1 and cross(hull[-2],hull[-1],p)<=0:hull.pop()
            hull.append(p)
        halves.extend(hull[:-1])
    width=min(max(abs(cross(a,b,p))/math.dist(a,b) for p in points)
              for a,b in zip(halves,halves[1:]+halves[:1]))
    length=max(math.dist(a,b) for a in points for b in points)
    return {'passed':width>=max(24,length*0.16),'applicable':True,
            'minimum_width_pixels':round(width,3),'width_length_ratio':round(width/length,4)}


def formations(count,center):
    ax,ay=center
    # Preserve the actual ladder arc first, including its 32px vertical pitch.
    if count<=9:
        ordered=sorted(REFERENCE_EAST,key=lambda p:p[1])
        chosen=[ordered[round(i*(len(ordered)-1)/(count-1))] for i in range(count)] if count>1 else [ordered[4]]
        for sign in (-1,1):
            for flip in (1,-1):
                for shift in (0,-32,32,-64,64):
                    points=tuple(rules._snap(ax+sign*x,ay+flip*y+shift) for x,y in chosen)
                    if curved_bank(points)['passed']:
                        yield points,(sign,0),{'formation':'fighting_spirit_side_arc','rows':1}
    # Extend the ladder's bowed front to campaign-sized banks. Every row
    # bends toward the depot at both ends; there is no straight-row fallback.
    rows_options=sorted({1,max(1,math.ceil(count/10)),max(1,math.ceil(count/7))})
    for rows in rows_options:
        lengths=[count//rows+(r<count%rows) for r in range(rows)]
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            vertical=bool(dx);pitch=32 if vertical else 64
            normal_min=192 if vertical else 160
            for distance in range(normal_min,normal_min+129,32):
                for shift in (0,-32,32,-64,64,-96,96,-128,128):
                    points=[]
                    for row,n in enumerate(lengths):
                        left=n//2
                        tangents=[-32-(left-1-i)*pitch-((left-1-i)//4)*32 for i in range(left)]
                        tangents += [32+i*pitch+(i//4)*32 for i in range(n-left)]
                        for tangent in tangents:
                            span=max(map(abs,tangents))
                            depth=max(2,math.ceil(span*0.4/32))
                            bow=round(depth*(1-(tangent/span)**2))*32 if span else 0
                            normal=distance+bow+row*(128 if vertical else 96)
                            points.append(rules._snap(ax+dx*normal if vertical else ax+tangent+shift,
                                                      ay+tangent+shift if vertical else ay+dy*normal))
                    if max(math.dist(center,p) for p in points)<=640 and curved_bank(points)['passed']:
                        yield tuple(points),(dx,dy),{'formation':'curved_ladder_bank','rows':rows}

def _plateau_worker(heights,level):
    flat=[bytearray(v==level for v in line) for line in heights]
    return rules._worker_terrain(flat)

def fitted_formations(info,indices,moving,anchor,walk,worker,boxes,reserved,occupied,heights,level,locked,threats=()):
    """Fit a short bent ladder bank around fixed campaign buildings/cliffs."""
    center=anchor['center'];ax,ay=center;pool=[]
    for y in range(ay-512,ay+513,32):
        for x in range(ax-512,ax+513,32):
            p=rules._snap(x,y)
            if not 160<=math.dist(center,p)<=600:continue
            rect=rules.geometry._rect(*p,176,boxes)
            if not sunken_clear(rect,threats):continue
            if not flat_rect(heights,rect,level):continue
            if not rules._geometry_ok(info,moving,[p],walk,boxes,reserved,occupied):continue
            if not rules._resource_clear(center,[(*p,176,11)]):continue
            pool.append(p)
    seen=set()
    for direction in ((0,-1),(0,1),(-1,0),(1,0)):
        dx,dy=direction
        for bias in (-160,-96,0,96,160):
            focus=(ax+dx*240+(bias if dy else 0),ay+dy*208+(bias if dx else 0))
            for spread in (0.3,0.7,1.2):
                # Prefer a curved depot-facing contour around obstructions.
                rx,ry=240+spread*80,208+spread*64
                contour=lambda p:abs(math.hypot((p[0]-ax)/rx,(p[1]-ay)/ry)-1)*320
                ordered=sorted(pool,key=lambda p:(contour(p)+0.4*math.dist(p,focus),p))
                chosen=list(locked.values());ordered_indices=list(locked)+[i for i in indices if i not in locked]
                for p in ordered:
                    rect=rules.geometry._rect(*p,176,boxes)
                    if chosen and min(rect_gap(rect,rules.geometry._rect(*q,176,boxes)) for q in chosen)>64:continue
                    if any(rules.geometry._overlap(rect,rules.geometry._rect(*q,176,boxes)) for q in chosen):continue
                    # A mineral behind another patch must have an open flank;
                    # do not silently replace front access with a remote detour.
                    model=list(info)
                    for i in moving:model[i]=(*model[i][:2],214,11)
                    for i,q in zip(ordered_indices,chosen+[p]):model[i]=(*q,176,11)
                    if not court.worker_access(model,ordered_indices[:len(chosen)+1],anchor,worker,boxes)[0]:continue
                    chosen.append(p)
                    if len(chosen)==len(indices):break
                signature=tuple(sorted(chosen))
                if len(chosen)==len(indices) and signature not in seen and curved_bank(chosen)['passed']:
                    seen.add(signature);yield tuple(chosen),direction,{'formation':'terrain_fitted_curved_bank','rows':0}

def _gas_access(info,index,anchor,worker,boxes):
    """Check the 32px lateral exit used by find_gas_exit_position as well as faces."""
    center=anchor['center'];point=info[index][:2]
    bounds=rules._bounds([center,point],worker,24);model=court._ground_model(info)
    if anchor['kind']=='expansion':model.append((*center,anchor['depot_type'],12))
    labels,_,_=rules._components(worker,model,bounds,boxes)
    depot=rules._perimeter_labels((*center,anchor['depot_type'],12),labels,bounds,boxes)
    sides=[]
    for direction in court.DIRECTIONS:
        if rules._front_labels(info[index],direction,labels,bounds,boxes)&depot:sides.append(direction)
    distance=math.dist(point,center);dx=(center[0]-point[0])/distance;dy=(center[1]-point[1])/distance
    # OpenBW's native-behavior reference offsets the return line 32px at
    # heading-90 degrees. A clear centerline alone can miss a trapped exit.
    offset=(dy*32,-dx*32);refinery=rules.geometry._rect(*point,info[index][2],boxes)
    depot_rect=rules.geometry._rect(*center,anchor['depot_type'],boxes)
    route=[]
    for step in range(math.ceil(distance/4)+1):
        t=min(1,step*4/distance);x=point[0]+(center[0]-point[0])*t+offset[0];y=point[1]+(center[1]-point[1])*t+offset[1]
        if any(l-13<=x<=r+13 and top-13<=y<=bottom+13 for l,top,r,bottom in (refinery,depot_rect)):continue
        xx=int(x)//8-bounds[0];yy=int(y)//8-bounds[1]
        route.append(0<=yy<len(labels) and 0<=xx<len(labels[0]) and labels[yy][xx] in depot)
    preferred=bool(route) and all(route)
    return len(sides)>=2 and preferred,{'reachable_exit_sides':[list(d) for d in sides],'preferred_32px_offset_exit_clear':preferred}

def compact_bank(info,indices,boxes):
    if not indices:return True
    seen={indices[0]};pending=set(indices[1:])
    while pending:
        joined={i for i in pending if any(rect_gap(rules.geometry._rect(*info[i][:2],info[i][2],boxes),
                            rules.geometry._rect(*info[j][:2],info[j][2],boxes))<=64 for j in seen)}
        if not joined:return False
        seen|=joined;pending-=joined
    return True

def audit_base(chk,info,bank,heights=None,boxes=None):
    heights=terrain_heights(chk) if heights is None else heights
    boxes=rules.geometry.load_unit_geometry()[0] if boxes is None else boxes
    anchor=bank['anchor'];cx,cy=anchor['center'];level=heights[cy//8][cx//8]
    indices=bank['mineral_indices'];gases=bank['gas_indices']
    flat=all(flat_rect(heights,rules.geometry._rect(*info[i][:2],info[i][2],boxes),level) for i in indices+gases)
    worker=_plateau_worker(heights,level)
    protection=bank.get('sunken_avoidance');threats=[]
    if protection:
        threats=sunken_threats(info,protection['hostile_owners'],boxes)
        worker=sunken_safe_worker(worker,threats)
    reachable,proof=court.worker_access(court._ground_model(info),indices,anchor,worker,boxes)
    exits={str(i):_gas_access(info,i,anchor,worker,boxes) for i in gases}
    direct=all(gas.direct_lane(anchor,info[i][:2],info,i,worker,boxes) for i in gases)
    separate=gas_separate(info,indices,gases,boxes)
    compact=compact_bank(info,indices,boxes)
    curve=curved_bank([info[i][:2] for i in indices])
    result={'same_plateau_footprints':flat,'same_plateau_worker_routes':reachable,
            'gas_outside_minerals':separate,'gas_direct_lane':direct,
            'gas_exits':{k:v[1] for k,v in exits.items()},'gas_exits_clear':all(v[0] for v in exits.values()),
            'compact_bank':compact,'curved_bank':curve,
            'passed':flat and reachable and direct and separate and compact and curve['passed'] and all(v[0] for v in exits.values()),
            'terrain_level':level,'worker_access':proof}
    if protection:
        clearance=all(sunken_clear(rules.geometry._rect(*info[i][:2],info[i][2],boxes),threats) for i in indices+gases)
        corridors=all(sunken_route_clear(anchor['center'],info[i][:2],threats) for i in indices+gases)
        result['sunken_safety']=dict(resources_and_worker_envelope_clear=clearance,safe_mining_routes=reachable and direct and corridors,
                                    threat_count=len(threats),**sunken_weapon())
        result['passed'] &= clearance and corridors
    return result

def apply(chk,mission,courtyard,*,reserved_points=()):
    from .build_plain_chk import CHK
    before=chk.getsection('UNIT');info=list(map(rules.geometry._info,rules.geometry._records(chk)));start=list(info)
    heights=terrain_heights(chk);walk,_=rules.geometry.load_terrain(chk)
    boxes,_=rules.geometry.load_unit_geometry();buildable=mining.load_buildable_grid(chk)
    original=list(map(rules.geometry._info,rules.geometry._records(CHK(Path(mission['source']).read_bytes()))))
    explicit,locations=rules._critical_locations(chk,original)
    refinery_locations=set();raw_triggers=chk.getsection('TRIG')
    for offset in range(0,len(raw_triggers),2400):
        trigger=raw_triggers[offset:offset+2400]
        for slot in range(16):
            c=trigger[slot*20:(slot+1)*20]
            if c[15] in (3,7,16,17) and struct.unpack_from('<H',c,12)[0] in gas.GAS_TYPES|{229,231}:refinery_locations.add(struct.unpack_from('<I',c)[0])
        for slot in range(64):
            a=trigger[320+slot*32:352+slot*32]
            if a[26] and struct.unpack_from('<H',a,24)[0] in gas.GAS_TYPES|{229,231}:refinery_locations.add(struct.unpack_from('<I',a)[0])
    landing=addons.reservations(info);reserved=tuple(map(tuple,reserved_points));reports=[]
    if mission['mission_id']==504:
        from . import terran4_repair
        for point in terran4_repair.destination_centers(chk):
            l,t,r,b=rules.geometry._rect(*point,108,boxes)
            reserved+=tuple((x,y) for y in range(t,b+1,16) for x in range(l,r+1,16))
    banks=copy.deepcopy(courtyard['bases'])
    # The prior fortification pass placed a turret inside this virtual site.
    # Reserve the adjacent legal foundation; no existing headquarters moves.
    for b in banks:
        if mission['mission_id']==515 and b['anchor']['center']==[5952,3632]:
            assert b['anchor']['kind']=='expansion';b['anchor']['center']=[5952,3696];b['anchor']['top_left_tile']=[184,114]
        if mission['mission_id']==508 and b['anchor']['kind']=='expansion' and b['anchor']['center']==[3168,5456]:
            b['sunken_avoidance']={'hostile_owners':[0,4,5],**sunken_weapon()}
    anchors=[b['anchor'] for b in banks]
    protected_centers=[tuple(a['center']) for a in anchors if rules._resource_clear(a['center'],info)]
    army=rules._worker_terrain(rules._worker_terrain(rules._worker_terrain(walk)));army_cache={'baseline':start}
    plateau_cache={}
    for bank in banks:
        anchor=bank['anchor'];center=tuple(anchor['center']);indices=bank['mineral_indices'];gases=bank['gas_indices'];moving=indices+gases
        if not indices:continue
        level=heights[center[1]//8][center[0]//8]
        worker=plateau_cache.setdefault(level,None)
        if worker is None:worker=_plateau_worker(heights,level);plateau_cache[level]=worker
        threats=[]
        if bank.get('sunken_avoidance'):
            threats=sunken_threats(info,bank['sunken_avoidance']['hostile_owners'],boxes)
            worker=sunken_safe_worker(worker,threats)
        failures=defaultdict(int);collision=court._ground_model(info);occupied=rules._collision_index(collision,moving,boxes)
        report={'anchor':copy.deepcopy(anchor),'mineral_indices':indices,'gas_indices':gases,'status':'pending','reasons':{}}
        if bank.get('sunken_avoidance'):report['sunken_avoidance']=copy.deepcopy(bank['sunken_avoidance'])
        reports.append(report)
        locked={i:info[i][:2] for i in indices if i in explicit}
        gas_options={}
        for i in gases:
            options=court._gas_options(chk,info,i,anchor,moving,walk,worker,boxes,reserved,buildable,original,landing,refinery_locations if info[i][2]!=188 else locations,protected_centers)
            gas_options[i]=[p for p in options if flat_rect(heights,rules.geometry._rect(*p,188,boxes),level) and sunken_clear(rules.geometry._rect(*p,188,boxes),threats)]
            if i in explicit:gas_options[i]=[info[i][:2]]
        choices=list(formations(len(indices),center))
        # Built-in float sum changed in Python 3.12; use the same accurate sum
        # in source builds and the portable Python 3.11 packaging verifier.
        choices.sort(key=lambda c:(c[2]['formation']!='fighting_spirit_side_arc',c[2]['rows'],max(math.dist(center,p) for p in c[0]),math.fsum(math.dist(center,p) for p in c[0])))
        from itertools import chain
        fitted=fitted_formations(collision,indices,moving,anchor,walk,worker,boxes,reserved,occupied,heights,level,locked,threats)
        for points,direction,shape in chain(choices,fitted):
            if any(p not in points for p in locked.values()):continue
            if any(not sunken_clear(rules.geometry._rect(*p,176,boxes),threats) for p in points):failures['sunken_range']+=1;continue
            if threats and any(not sunken_route_clear(center,p,threats) for p in points):failures['sunken_mining_route']+=1;continue
            if not all(flat_rect(heights,rules.geometry._rect(*p,176,boxes),level) for p in points):failures['plateau']+=1;continue
            if not rules._geometry_ok(collision,moving,points,walk,boxes,reserved,occupied):failures['geometry']+=1;continue
            free=[i for i in indices if i not in locked];targets=[p for p in points if p not in locked.values()]
            displacement=MAX_DISPLACEMENT
            assigned=rules._assignment([info[i][:2] for i in free],targets,limit=displacement)
            if assigned is None:failures['displacement']+=1;continue
            positions=dict(zip(free,assigned[0]));positions.update(locked)
            if any(i<len(original) and math.dist(original[i][:2],p)>displacement for i,p in positions.items()):failures['original_displacement']+=1;continue
            model=list(info)
            for i,p in positions.items():model[i]=(*p,*info[i][2:])
            # Remove old gas positions until a complete independent gas flank is selected.
            bare=list(model)
            for i in gases:bare[i]=(*info[i][:2],214,11)
            if not court.worker_access(court._ground_model(bare),indices,anchor,worker,boxes)[0]:failures['mineral_routes']+=1;continue
            options=[]
            for i in gases:
                legal=[p for p in gas_options[i] if court.side(center,p)!=direction and all(
                    rect_gap(rules.geometry._rect(*p,188,boxes),rules.geometry._rect(*m,176,boxes))>=GAS_MINERAL_GAP for m in points)]
                legal.sort(key=lambda p:(math.dist(center,p),math.dist(info[i][:2],p),p));options.append(legal[:12])
            for gas_points in product(*options):
                candidate=list(model)
                for i,p in zip(gases,gas_points):candidate[i]=(*p,*info[i][2:])
                if not gas_separate(candidate,indices,gases,boxes):failures['gas_inside_bank']+=1;continue
                if not ladder._geometry(court._ground_model(candidate),moving,[candidate[i][:2] for i in moving],walk,boxes,reserved,buildable,chk,failures):continue
                if any(not rules._resource_clear(c,candidate) for c in protected_centers):failures['depot_clearance']+=1;continue
                if not corner.depot_sites(chk,candidate,anchor,buildable,boxes)[0]:failures['depot_foundation']+=1;continue
                if not rules._critical_membership(chk,info,candidate,moving,locations):failures['trigger_region']+=1;continue
                if not rules._critical_membership(chk,info,candidate,[i for i in gases if info[i][2]!=188],refinery_locations):failures['refinery_trigger_region']+=1;continue
                if not all(gas.direct_lane(anchor,candidate[i][:2],candidate,i,worker,boxes) for i in gases):failures['gas_lane']+=1;continue
                if not all(_gas_access(candidate,i,anchor,worker,boxes)[0] for i in gases):failures['gas_exit']+=1;continue
                if not court.worker_access(court._ground_model(candidate),indices,anchor,worker,boxes)[0]:failures['joint_mineral_routes']+=1;continue
                if not compact_bank(candidate,indices,boxes):failures['mineral_bank_split']+=1;continue
                changed=[i for i in moving if candidate[i][:2]!=info[i][:2]]
                if not rules._army_route_ok(info,candidate,changed,army,boxes,army_cache):failures['army_route']+=1;continue
                info=candidate;report.update(status='ladder_separate_gas',direction=list(direction),**shape);break
            if report['status']!='pending':break
        if report['status']=='pending':
            report['status']='existing_compact_ladder_bank' if audit_base(chk,info,bank,heights,boxes)['passed'] else 'unresolved'
        report.update(reasons=dict(failures),mineral_positions=[list(info[i][:2]) for i in indices],gas_positions=[list(info[i][:2]) for i in gases])
        print('RESOURCE_BANK',mission['mission_id'],center,len(indices),report['status'],dict(failures),flush=True)
    raw=bytearray(before)
    for i,p in enumerate(info):struct.pack_into('<HH',raw,i*36+4,*p[:2])
    for i,(a,b) in enumerate(zip(start,info)):
        if a[:2]!=b[:2]:
            assert a[2] in rules.MINERALS|gas.GAS_TYPES
            assert before[i*36:i*36+4]==raw[i*36:i*36+4] and before[i*36+8:(i+1)*36]==raw[i*36+8:(i+1)*36]
    for report in reports:report['audit']=audit_base(chk,info,report,heights,boxes)
    unresolved=[(r['anchor']['center'],r['status'],r['audit']) for r in reports if r['status']=='unresolved' or not r['audit']['passed']]
    assert not unresolved,('Unsafe final mineral/gas layout',mission['mission_id'],unresolved)
    chk.setsection('UNIT',bytes(raw))
    return {'version':VERSION,'mission':mission['mission_id'],'bases':reports,
            'moves':[{'index':i,'before':list(a[:2]),'after':list(b[:2])} for i,(a,b) in enumerate(zip(start,info)) if a[:2]!=b[:2]],
            'input_unit_sha256':rules._hash(before),'output_unit_sha256':rules._hash(raw),
            'all_resource_amounts_and_counts_preserved':True,'native_mining_verified':False,'reference_map_sha256':REFERENCE_MAPS}

def undo(chk,report):
    court.undo(chk,report)
