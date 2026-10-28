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

from . import resource_layout as rules,mining_layout_audit as mining
from . import courtyard_resource_layout as court,corner_resource_layout as corner
from . import main_base_gas as gas,ladder_resource_layout as ladder,addon_placement as addons

VERSION='ladder_separate_gas_single_plateau_v1'
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

def gas_separate(info,minerals,gases,boxes):
    rects=[rules.geometry._rect(*info[i][:2],info[i][2],boxes) for i in minerals]
    bounds=(min(r[0] for r in rects),min(r[1] for r in rects),max(r[2] for r in rects),max(r[3] for r in rects))
    return all(rect_gap(bounds,rules.geometry._rect(*info[j][:2],info[j][2],boxes))>=32 for j in gases) and all(rect_gap(rules.geometry._rect(*info[i][:2],info[i][2],boxes),
                        rules.geometry._rect(*info[j][:2],info[j][2],boxes))>=GAS_MINERAL_GAP
               for i in minerals for j in gases)

def formations(count,center):
    ax,ay=center
    # Preserve the actual ladder arc first, including its 32px vertical pitch.
    if count<=9:
        chosen=sorted(REFERENCE_EAST,key=lambda p:(abs(p[1]-32),p))[:count]
        for sign in (-1,1):
            for shift in (0,-32,32,-64,64):
                points=tuple(rules._snap(ax+sign*x,ay+y+shift) for x,y in chosen)
                yield points,(sign,0),{'formation':'fighting_spirit_side_arc','rows':1}
    # Larger campaign banks retain their original patch count. Aligned gaps
    # through successive rows allow outer workers to reach the same depot face.
    rows_options=sorted({1,max(1,math.ceil(count/10)),max(1,math.ceil(count/7))})
    for rows in rows_options:
        lengths=[count//rows+(r<count%rows) for r in range(rows)]
        for dx,dy in ((0,-1),(0,1),(-1,0),(1,0)):
            vertical=bool(dx);pitch=32 if vertical else 64
            normal_min=192 if vertical else 160
            for distance in range(normal_min,normal_min+161,32):
                for shift in (0,-32,32,-64,64,-96,96,-128,128):
                    points=[]
                    for row,n in enumerate(lengths):
                        left=n//2
                        tangents=[-32-(left-1-i)*pitch-((left-1-i)//4)*32 for i in range(left)]
                        tangents += [32+i*pitch+(i//4)*32 for i in range(n-left)]
                        for tangent in tangents:
                            normal=distance+row*(128 if vertical else 96)
                            points.append(rules._snap(ax+dx*normal if vertical else ax+tangent+shift,
                                                      ay+tangent+shift if vertical else ay+dy*normal))
                    if max(math.dist(center,p) for p in points)<=640:
                        yield tuple(points),(dx,dy),{'formation':'ladder_side_bank','rows':rows}

def _plateau_worker(heights,level):
    flat=[bytearray(v==level for v in line) for line in heights]
    return rules._worker_terrain(flat)

def fitted_formations(info,indices,moving,anchor,walk,worker,boxes,reserved,occupied,heights,level,locked):
    """Fit a short bent ladder bank around fixed campaign buildings/cliffs."""
    center=anchor['center'];ax,ay=center;pool=[]
    for y in range(ay-512,ay+513,32):
        for x in range(ax-512,ax+513,32):
            p=rules._snap(x,y)
            if not 160<=math.dist(center,p)<=600:continue
            rect=rules.geometry._rect(*p,176,boxes)
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
                ordered=sorted(pool,key=lambda p:(math.dist(p,focus)+spread*math.dist(p,center),p))
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
                if len(chosen)==len(indices) and signature not in seen:
                    seen.add(signature);yield tuple(chosen),direction,{'formation':'terrain_fitted_ladder_bank','rows':0}

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
    reachable,proof=court.worker_access(court._ground_model(info),indices,anchor,worker,boxes)
    exits={str(i):_gas_access(info,i,anchor,worker,boxes) for i in gases}
    direct=all(gas.direct_lane(anchor,info[i][:2],info,i,worker,boxes) for i in gases)
    separate=gas_separate(info,indices,gases,boxes)
    compact=compact_bank(info,indices,boxes)
    return {'same_plateau_footprints':flat,'same_plateau_worker_routes':reachable,
            'gas_outside_minerals':separate,'gas_direct_lane':direct,
            'gas_exits':{k:v[1] for k,v in exits.items()},'gas_exits_clear':all(v[0] for v in exits.values()),
            'compact_bank':compact,
            'passed':flat and reachable and direct and separate and compact and all(v[0] for v in exits.values()),
            'terrain_level':level,'worker_access':proof}

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
        failures=defaultdict(int);collision=court._ground_model(info);occupied=rules._collision_index(collision,moving,boxes)
        report={'anchor':copy.deepcopy(anchor),'mineral_indices':indices,'gas_indices':gases,'status':'pending','reasons':{}}
        reports.append(report)
        locked={i:info[i][:2] for i in indices if i in explicit}
        gas_options={}
        for i in gases:
            options=court._gas_options(chk,info,i,anchor,moving,walk,worker,boxes,reserved,buildable,original,landing,refinery_locations if info[i][2]!=188 else locations,protected_centers)
            gas_options[i]=[p for p in options if flat_rect(heights,rules.geometry._rect(*p,188,boxes),level)]
            if i in explicit:gas_options[i]=[info[i][:2]]
        choices=list(formations(len(indices),center))
        # Built-in float sum changed in Python 3.12; use the same accurate sum
        # in source builds and the portable Python 3.11 packaging verifier.
        choices.sort(key=lambda c:(c[2]['rows'],max(math.dist(center,p) for p in c[0]),math.fsum(math.dist(center,p) for p in c[0])))
        from itertools import chain
        fitted=fitted_formations(collision,indices,moving,anchor,walk,worker,boxes,reserved,occupied,heights,level,locked)
        for points,direction,shape in chain(choices,fitted):
            if any(p not in points for p in locked.values()):continue
            if not all(flat_rect(heights,rules.geometry._rect(*p,176,boxes),level) for p in points):failures['plateau']+=1;continue
            if not rules._geometry_ok(collision,moving,points,walk,boxes,reserved,occupied):failures['geometry']+=1;continue
            free=[i for i in indices if i not in locked];targets=[p for p in points if p not in locked.values()]
            assigned=rules._assignment([info[i][:2] for i in free],targets,limit=MAX_DISPLACEMENT)
            if assigned is None:failures['displacement']+=1;continue
            positions=dict(zip(free,assigned[0]));positions.update(locked)
            if any(i<len(original) and math.dist(original[i][:2],p)>MAX_DISPLACEMENT for i,p in positions.items()):failures['original_displacement']+=1;continue
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
