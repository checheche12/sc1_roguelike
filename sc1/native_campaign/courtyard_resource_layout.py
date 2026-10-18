"""Joint three-sided resource courts with a straight depot-to-gas worker lane."""
from __future__ import annotations
from collections import Counter,defaultdict
from itertools import product
from pathlib import Path
import copy,math,struct
from functools import lru_cache
from . import resource_layout as rules,corner_resource_layout as corner
from . import main_base_gas as gas,ladder_resource_layout as ladder,addon_placement as addons

VERSION='joint_u_court_direct_gas_v1'
DIRECTIONS=((-1,0),(1,0),(0,-1),(0,1))
MAX_RESOURCE_DISPLACEMENT=1280

@lru_cache(maxsize=1)
def _flying_types():
    from .build_managed_dat import legacy_fields,source_bytes
    flags=legacy_fields('units',source_bytes('units'))[22][1]
    return frozenset(i for i in range(106) if struct.unpack_from('<I',flags,i*4)[0]&4)

def _ground_model(info):
    # Air units can fly over minerals/geysers; they do not occupy ground cells.
    flying=_flying_types()
    return [(*p[:2],214,p[3]) if p[2] in flying else p for p in info]

def _groups(mission,corner_report):
    # Empty sites beside a cliff need a different depot foundation to leave
    # three usable resource walls. Original placed HQs are never moved.
    reviewed={(108,(192,720)):(192,592),(408,(5600,3856)):(5600,4240)}
    groups={}
    for bank in corner_report['bases']:
        anchor=copy.deepcopy(bank['anchor']);old=tuple(anchor['center'])
        center=reviewed.get((mission['mission_id'],old),old)
        if center!=old:
            assert anchor['kind']=='expansion'
            anchor.update(center=list(center),top_left_tile=[(center[0]-64)//32,(center[1]-48)//32])
        groups[center]=dict(anchor=anchor,indices=bank['indices'],source_anchor=list(old))
    return groups

def side(center,point):
    return rules._direction(center,point)

def court(center,minerals,gases):
    occupied={side(center,p) for p in minerals+gases}
    return next((d for d in DIRECTIONS if d not in occupied),None) if len(occupied)==3 else None

def worker_access(info,indices,anchor,walk,boxes):
    """Each patch must reach a depot face; separate faces may serve separate banks."""
    center=anchor['center'];bounds=rules._bounds([info[i][:2] for i in indices]+[center],walk,32)
    model=list(info)
    if anchor['kind']=='expansion':model.append((*center,anchor['depot_type'],12))
    labels,_,_=rules._components(walk,model,bounds,boxes)
    depot=rules._perimeter_labels((*center,anchor['depot_type'],12),labels,bounds,boxes)
    blocked=[];faces={};front_count=0;other_edges=[]
    for i in indices:
        available=rules._front_labels(info[i],rules._direction(center,info[i][:2]),labels,bounds,boxes)&depot
        if available:front_count+=1
        else:
            # Workers can harvest from any reachable edge of the patch. Cliff
            # and city banks need not all dock on the same compass-facing edge.
            available=rules._perimeter_labels(info[i],labels,bounds,boxes)&depot
            if available:other_edges.append(i)
        if not available:blocked.append(i)
        faces[str(i)]=sorted(available)
    return not blocked,dict(all_mineral_patches_reach_a_depot_face=not blocked,front_reachable_count=front_count,
        other_reachable_edge_indices=other_edges,blocked_indices=blocked,depot_face_components=faces)

def _gas_options(chk,info,index,anchor,moving,walk,worker,boxes,reserved,buildable,original,landing,critical_locations=(),protected_centers=()):
    current=info[index][:2]
    points=list(dict.fromkeys([current]+gas.candidates(anchor,info,index)))
    candidates=[];failures=defaultdict(int)
    model=_ground_model(info)
    for other in moving:
        if other!=index:model[other]=(*info[other][:2],214,11)
    for point in points:
        if math.dist(point,anchor['center'])>512:continue
        if index<len(original) and math.dist(point,original[index][:2])>MAX_RESOURCE_DISPLACEMENT:continue
        if not addons.resource_clear(point,188,landing):continue
        # Reserve against fixed objects now; the complete joint geometry is
        # checked again after both mineral and gas positions have been chosen.
        if not rules._foundation(chk,point,188,buildable):continue
        if not ladder._geometry(model,[index],[point],walk,boxes,reserved,buildable,chk,failures):continue
        if not rules._resource_clear(anchor['center'],[(*point,188,11)]):continue
        if any(not rules._resource_clear(c,[(*point,188,11)]) for c in protected_centers):continue
        if not gas.direct_lane(anchor,point,model,index,worker,boxes):continue
        proposed=list(info);proposed[index]=(*point,*info[index][2:])
        if not rules._critical_membership(chk,info,proposed,[index],critical_locations):continue
        candidates.append(point)
    return candidates

def _segment_hits(start,end,rect):
    low,high=0.,1.
    for a,b,left,right in ((start[0],end[0],rect[0]-12,rect[2]+12),(start[1],end[1],rect[1]-12,rect[3]+12)):
        delta=b-a
        if not delta:
            if a<=left or a>=right:return False
            continue
        t0,t1=sorted(((left-a)/delta,(right-a)/delta));low=max(low,t0);high=min(high,t1)
        if low>=high:return False
    return True

def _gas_choices(info,indices,options,anchor,worker,boxes,mineral_points):
    center=anchor['center'];mineral_sides={side(center,p) for p in mineral_points}
    for opening in DIRECTIONS:
        if opening in mineral_sides:continue
        needed=set(DIRECTIONS)-{opening}-mineral_sides
        if len(needed)>len(indices):continue
        choices=[]
        for index in indices:
            candidates=[p for p in options[index] if side(center,p)!=opening and
                        not any(_segment_hits(center,p,rules.geometry._rect(*m,176,boxes)) for m in mineral_points)]
            candidates.sort(key=lambda p:(side(center,p) not in needed,math.dist(p,center),math.dist(p,info[index][:2]),p))
            # Preserve at least two representatives for every available side.
            chosen=[];counts=Counter()
            for p in candidates:
                key=side(center,p)
                if counts[key]>=3:continue
                chosen.append(p);counts[key]+=1
            if not chosen:break
            choices.append(chosen)
        if len(choices)!=len(indices):continue
        for points in product(*choices):
            if court(center,mineral_points,list(points))==opening:yield list(points),opening

def _u_candidates(info,mineral_indices,gases,options,anchor,walk,boxes,reserved,buildable,chk,*,fine=False,protected_centers=()):
    """Choose gas lanes first, then pack minerals on all three court walls."""
    center=anchor['center'];ax,ay=center;moving=mineral_indices+gases
    collision=_ground_model(info);occupied=rules._collision_index(collision,moving,boxes)
    preferred=court(center,[info[i][:2] for i in mineral_indices],[])
    openings=sorted(DIRECTIONS,key=lambda d:(d!=preferred,d));seen_layouts=set()
    static=list(collision)
    for i in moving:static[i]=(*info[i][:2],214,11)
    if anchor['kind']=='expansion':static.append((*center,anchor['depot_type'],12))
    bounds=rules._bounds([(ax-800,ay-800),(ax+800,ay+800)],walk,4)
    worker=rules._worker_terrain(walk)
    labels,_,_=rules._components(worker,static,bounds,boxes)
    hq_labels=rules._perimeter_labels((*center,anchor['depot_type'],12),labels,bounds,boxes)
    ports={}
    def worker_ports(point):
        if point in ports:return ports[point]
        x,y=point;dx,dy=side(center,point);l,t,r,b=rules._worker_boxes()[176]
        cx,cy=x-dx*(max(l,r)+12),y-dy*(max(t,b)+12)
        values=[]
        for off in ((-8,0,8) if dx else (-24,-16,-8,0,8,16,24)):
            xx=int(cx+(0 if dx else off))//8;yy=int(cy+(off if dx else 0))//8
            if 0<=yy-bounds[1]<len(labels) and 0<=xx-bounds[0]<len(labels[0]) and labels[yy-bounds[1]][xx-bounds[0]] in hq_labels:
                values.append((xx*8+4,yy*8+4))
        if fine:
            left,right,top,bottom=int(x-l-16)//8,int(x+r+15)//8,int(y-t-16)//8,int(y+b+15)//8
            cells=[(xx,top) for xx in range(left,right+1)]+[(xx,bottom) for xx in range(left,right+1)]
            cells += [(left,yy) for yy in range(top,bottom+1)]+[(right,yy) for yy in range(top,bottom+1)]
            for xx,yy in cells:
                if 0<=yy-bounds[1]<len(labels) and 0<=xx-bounds[0]<len(labels[0]) and labels[yy-bounds[1]][xx-bounds[0]] in hq_labels:
                    point_on_edge=(xx*8+4,yy*8+4)
                    if point_on_edge not in values:values.append(point_on_edge)
        ports[point]=values;return values
    def blocked(port,rect):
        x,y=port;l,t,r,b=rect;return l-12<x<r+12 and t-12<y<b+12
    for gap_x,gap_y in ((96,64),(64,64),(96,32),(64,32)):
        pool=set()
        for sign in (-1,1):
            for row in range(20 if fine else 4):
                for k in range(-8,9):
                    for p in ((ax+k*gap_x,ay+sign*(160+row*(32 if fine else 64))),
                              (ax+sign*(192+row*(32 if fine else 64)),ay+k*gap_y)):
                        p=rules._snap(*p)
                        # Keep a worker/army gate through every layer of a wall.
                        # Merely leaving gaps inside each row can still seal the
                        # outer mineral fronts when another row plugs those gaps.
                        dx,dy=side(center,p)
                        if abs((p[1]-ay) if dx else (p[0]-ax))<(48 if dx else 64):continue
                        if worker_ports(p) and rules._geometry_ok(collision,moving,[p],walk,boxes,reserved,occupied) and rules._resource_clear(center,[(*p,176,11)]) and all(rules._resource_clear(c,[(*p,176,11)]) for c in protected_centers):pool.add(p)
        for opening in openings:
            choices=[]
            for index in gases:
                candidates=sorted((p for p in options[index] if side(center,p)!=opening),
                    key=lambda p:(math.dist(center,p),math.dist(info[index][:2],p),p))
                selected=[];seen=Counter()
                for p in candidates:
                    key=(side(center,p),round(math.dist(center,p)/64))
                    if seen[key]>=2:continue
                    selected.append(p);seen[key]+=1
                choices.append(selected[:24])
            if any(not c for c in choices):continue
            combinations=[()]
            for choice in choices:
                combinations=sorted((previous+(p,) for previous in combinations for p in choice),
                    key=lambda points:(sum(math.dist(center,p) for p in points),points))[:192]
            for gas_points in combinations:
                candidate=list(collision)
                for i in mineral_indices:candidate[i]=(*info[i][:2],214,11)
                for i,p in zip(gases,gas_points):candidate[i]=(*p,*info[i][2:])
                if not ladder._geometry(candidate,gases,list(gas_points),walk,boxes,reserved,buildable,chk,defaultdict(int)):continue
                available=[p for p in pool if side(center,p)!=opening and
                    not any(rules.geometry._overlap(rules.geometry._rect(*p,176,boxes),rules.geometry._rect(*g,188,boxes)) or
                            _segment_hits(center,g,rules.geometry._rect(*p,176,boxes)) for g in gas_points)]
                for mode in range(20 if fine else 4):
                    bias=mode%4;minimum_radius=(0,256,320,384,448)[mode//4] if fine else 0
                    chosen=[];counts=Counter();remaining_ports={};gas_rects=[rules.geometry._rect(*g,188,boxes) for g in gas_points]
                    access_model=list(candidate)
                    for p in sorted(available,key=lambda p:(math.dist(center,p)+(32 if bias and side(center,p)==DIRECTIONS[bias-1] else 0),p)):
                        if math.dist(center,p)<minimum_radius:continue
                        rect=rules.geometry._rect(*p,176,boxes)
                        if any(rules.geometry._overlap(rect,rules.geometry._rect(*q,176,boxes)) for q in chosen):continue
                        if bias>=2 and (any(_segment_hits(center,p,rules.geometry._rect(*q,176,boxes)) or _segment_hits(center,q,rect) for q in chosen) or
                                        any(_segment_hits(center,p,r) for r in gas_rects)):continue
                        front=[port for port in worker_ports(p) if not any(blocked(port,r) for r in gas_rects+[rules.geometry._rect(*q,176,boxes) for q in chosen])]
                        if not front or any(all(blocked(port,rect) for port in remaining_ports[q]) for q in chosen):continue
                        if fine:
                            index=mineral_indices[len(chosen)];access_model[index]=(*p,*info[index][2:])
                            if not worker_access(access_model,mineral_indices[:len(chosen)+1],anchor,worker,boxes)[0]:
                                access_model[index]=(*info[index][:2],214,11);continue
                        for q in chosen:remaining_ports[q]=[port for port in remaining_ports[q] if not blocked(port,rect)]
                        remaining_ports[p]=front
                        chosen.append(p);counts[side(center,p)]+=1
                        if len(chosen)==len(mineral_indices):break
                    if len(chosen)==len(mineral_indices) and court(center,chosen,list(gas_points))==opening:
                        signature=(tuple(sorted(chosen)),tuple(gas_points),opening)
                        if signature in seen_layouts:continue
                        seen_layouts.add(signature)
                        if len(seen_layouts)>(512 if fine else 128):return
                        yield chosen,list(gas_points),opening,dict(formation='joint_three_wall_court',mineral_grid=[gap_x,gap_y])

def apply(chk,mission,layout,gas_report,corner_report,*,reserved_points=()):
    before=chk.getsection('UNIT');records=rules.geometry._records(chk)
    info=list(map(rules.geometry._info,records));start=list(info)
    from .build_plain_chk import CHK
    original=list(map(rules.geometry._info,rules.geometry._records(CHK(Path(mission['source']).read_bytes()))))
    walk,_=rules.geometry.load_terrain(chk);worker=rules._worker_terrain(walk)
    army=rules._worker_terrain(rules._worker_terrain(worker));boxes,_=rules.geometry.load_unit_geometry()
    buildable=rules.mining.load_buildable_grid(chk);explicit,locations=rules._critical_locations(chk,original)
    # Gas buildings are resources too. Preserve any original trigger region that
    # can select them when relocating their complete, otherwise unchanged record.
    raw_triggers=chk.getsection('TRIG');refinery_locations=set()
    for offset in range(0,len(raw_triggers),2400):
        trigger=raw_triggers[offset:offset+2400]
        for slot in range(16):
            condition=trigger[slot*20:(slot+1)*20]
            if condition[15] in (3,7,16,17) and struct.unpack_from('<H',condition,12)[0] in gas.GAS_TYPES|{229,231}:
                refinery_locations.add(struct.unpack_from('<I',condition)[0])
        for slot in range(64):
            action=trigger[320+slot*32:352+slot*32]
            if action[26] and struct.unpack_from('<H',action,24)[0] in gas.GAS_TYPES|{229,231}:
                refinery_locations.add(struct.unpack_from('<I',action)[0])
    groups=_groups(mission,corner_report)
    anchors=[g['anchor'] for g in groups.values()];centers=list(groups);assigned={}
    redirects={tuple(g['source_anchor']):c for c,g in groups.items()}
    for field in layout['gas_fields']:
        if 'anchor' in field and tuple(field['anchor']['center']) in redirects:
            assigned[field['unit_index']]=redirects[tuple(field['anchor']['center'])]
    for index in gas_report.get('gas_indices',[]):
        if tuple(gas_report['anchor']['center']) in redirects:assigned[index]=redirects[tuple(gas_report['anchor']['center'])]
    for index,item in enumerate(info):
        if item[2] in gas.GAS_TYPES and index not in assigned and centers:
            center=min(centers,key=lambda c:(math.dist(c,item[:2]),c))
            if math.dist(center,item[:2])<=768:assigned[index]=center
    landing=addons.reservations(info);reserved=tuple(map(tuple,reserved_points));reports=[]
    for center,group in groups.items():
        indices=group['indices'];anchor=group['anchor']
        gases=sorted(i for i,c in assigned.items() if c==center)
        mineral_points=[info[i][:2] for i in indices]
        proof=dict(anchor=copy.deepcopy(anchor),source_anchor=group['source_anchor'],mineral_indices=indices,gas_indices=gases,status='pending',reasons={})
        reports.append(proof)
        if not gases:
            proof['status']='no_gas_mineral_corner_preserved';continue
        direct={i:gas.direct_lane(anchor,info[i][:2],info,i,worker,boxes) for i in gases}
        opening=court(center,mineral_points,[info[i][:2] for i in gases])
        if opening and all(direct.values()) and corner.depot_sites(chk,info,anchor,buildable,boxes)[0]:
            proof.update(status='joint_u_court',opening=list(opening),changed=False,
                gas_direct_lanes={str(i):True for i in gases},mineral_positions=[list(p) for p in mineral_points],
                gas_positions=[list(info[i][:2]) for i in gases]);continue
        if len(indices)<3:
            proof.update(status='scripted_or_small_field_preserved',gas_direct_lanes={str(i):v for i,v in direct.items()});continue
        moving=indices+gases
        protected_centers=sorted({tuple(p[:2]) for p in start if p[2] in rules.HEADQUARTERS and rules._resource_clear(p[:2],start)}|
                                 {tuple(a['center']) for a in anchors if rules._resource_clear(a['center'],info)})
        options={i:_gas_options(chk,info,i,anchor,moving,walk,worker,boxes,reserved,buildable,original,landing,
                               refinery_locations if info[i][2]!=188 else locations,protected_centers) for i in gases}
        for i in gases:
            if i in explicit:options[i]=[info[i][:2]]
        proof['gas_option_counts']={str(i):len(points) for i,points in options.items()}
        collision_info=_ground_model(info)
        occupied=rules._collision_index(collision_info,moving,boxes)
        first=(tuple(mineral_points),dict(formation='existing_minerals_gas_repaired'),None,None)
        # terrain_fitted_formations needs the mineral count, while occupancy must
        # ignore movable geysers. Pass the already prepared collision index.
        alternatives=list(corner.terrain_fitted_formations(collision_info,indices,center,walk,boxes,reserved,occupied))
        alternatives+=list(corner.formations(len(indices),center))
        alternatives.sort(key=lambda item:(max(math.dist(center,p) for p in item[0]),sum(math.dist(center,p) for p in item[0]),item[0]))
        def candidates():
            yield first
            for points,gas_points,opening,shape in _u_candidates(info,indices,gases,options,anchor,walk,boxes,reserved,buildable,chk,fine=mission['mission_id']==603 and tuple(center)==(800,2320),protected_centers=protected_centers):
                yield points,shape,gas_points,opening
            for points,shape in alternatives:yield points,shape,None,None
        failures=defaultdict(int);army_cache={'baseline':list(info)}
        old_distances=[math.dist(center,p) for p in mineral_points]
        for points,shape,planned_gases,planned_opening in candidates():
            locked={i:info[i][:2] for i in indices if i in explicit}
            points=list(points)
            for fixed in locked.values():
                if fixed not in points:
                    replace=min((n for n,p in enumerate(points) if p not in locked.values()),key=lambda n:(math.dist(points[n],fixed),points[n]))
                    points[replace]=fixed
            distances=[math.dist(center,p) for p in points]
            if max(distances)>max(old_distances)+128 or sum(distances)>sum(old_distances)*1.5:
                failures['mineral_mining_distance']+=1;continue
            new_mineral_points=[p for p in points if p not in mineral_points]
            if not rules._geometry_ok(collision_info,moving,new_mineral_points,walk,boxes,reserved,occupied):
                failures['mineral_geometry']+=1;continue
            free_indices=[i for i in indices if i not in locked]
            free_points=[p for p in points if p not in locked.values()]
            assignment=rules._assignment([info[i][:2] for i in free_indices],free_points,limit=MAX_RESOURCE_DISPLACEMENT)
            if assignment is None:failures['assignment']+=1;continue
            by_index=dict(zip(free_indices,assignment[0]));by_index.update(locked)
            points=[by_index[i] for i in indices]
            if any(i in explicit and p!=info[i][:2] for i,p in zip(indices,points)):continue
            if any(i<len(original) and math.dist(original[i][:2],p)>MAX_RESOURCE_DISPLACEMENT for i,p in zip(indices,points)):
                failures['original_displacement']+=1;continue
            model=list(info)
            for i,p in zip(indices,points):model[i]=(*p,*info[i][2:])
            gas_choices=[(planned_gases,planned_opening)] if planned_gases is not None else _gas_choices(model,gases,options,anchor,worker,boxes,points)
            for gas_points,opening in gas_choices:
                if court(center,points,gas_points)!=opening:continue
                candidate=list(model)
                for i,p in zip(gases,gas_points):candidate[i]=(*p,*info[i][2:])
                changed=[i for i in moving if info[i][:2]!=candidate[i][:2]]
                # Original scripted resources can occupy stock cliff-edge tiles.
                # Preserve those records; validate every newly placed footprint
                # against all unchanged objects rather than relocating the event.
                if not ladder._geometry(_ground_model(candidate),changed,[candidate[i][:2] for i in changed],walk,boxes,reserved,buildable,chk,failures):continue
                if not all(gas.direct_lane(anchor,candidate[i][:2],candidate,i,worker,boxes) for i in gases):
                    failures['gas_behind_resource']+=1;continue
                if any(not rules._resource_clear(c,candidate) for c in protected_centers):
                    failures['other_depot']+=1;continue
                legal,sites=corner.depot_sites(chk,candidate,anchor,buildable,boxes)
                if not legal:failures['depot_foundation']+=1;continue
                if not rules._critical_membership(chk,info,candidate,changed,locations):
                    failures['trigger_region']+=1;continue
                if not rules._critical_membership(chk,info,candidate,[i for i in gases if info[i][2]!=188],refinery_locations):
                    failures['refinery_trigger_region']+=1;continue
                if not worker_access(candidate,indices,anchor,worker,boxes)[0]:
                    failures['mineral_access']+=1;continue
                if any(worker_access(info,g['indices'],g['anchor'],worker,boxes)[0] and not worker_access(candidate,g['indices'],g['anchor'],worker,boxes)[0]
                       for c,g in groups.items() if c!=center and math.dist(c,center)<768):
                    failures['neighbor_mineral_access']+=1;continue
                if any(gas.direct_lane(groups[c]['anchor'],info[i][:2],info,i,worker,boxes) and
                       not gas.direct_lane(groups[c]['anchor'],candidate[i][:2],candidate,i,worker,boxes)
                       for i,c in assigned.items() if c!=center and math.dist(c,center)<768):
                    failures['neighbor_gas_lane']+=1;continue
                if not rules._army_route_ok(info,candidate,changed,army,boxes,army_cache):
                    failures['army_route']+=1;continue
                info=candidate
                proof.update(status='joint_u_court',changed=bool(changed),opening=list(opening),
                    mineral_positions=[list(info[i][:2]) for i in indices],gas_positions=[list(info[i][:2]) for i in gases],
                    gas_direct_lanes={str(i):True for i in gases},depot_sites=sites,**shape)
                break
            if proof['status']=='joint_u_court':break
        if proof['status']=='pending':proof.update(status='terrain_constrained',gas_direct_lanes={str(i):v for i,v in direct.items()})
        proof['reasons']=dict(failures)
    raw=bytearray(before)
    unresolved=[(b['anchor']['center'],b['reasons']) for b in reports if b['gas_indices'] and len(b['mineral_indices'])>=3 and b['status']!='joint_u_court']
    assert not unresolved, ('Unresolved joint mineral/gas court',unresolved)
    assert all(gas.direct_lane(groups[c]['anchor'],info[i][:2],info,i,worker,boxes) for i,c in assigned.items()), 'A final gas worker lane is blocked'
    assert all(worker_access(info,b['mineral_indices'],b['anchor'],worker,boxes)[0] for b in reports if b['gas_indices']), 'A final mineral cannot return cargo to its depot'
    assert all(not rules._resource_clear(p[:2],start) or rules._resource_clear(p[:2],info)
               for p in start if p[2] in rules.HEADQUARTERS), 'Existing HQ resource exclusion changed'
    for i,p in enumerate(info):struct.pack_into('<HH',raw,i*36+4,*p[:2])
    for i in range(len(info)):
        a,b=before[i*36:(i+1)*36],raw[i*36:(i+1)*36]
        if a==b:continue
        assert struct.unpack_from('<H',a,8)[0] in rules.MINERALS|gas.GAS_TYPES
        assert a[:4]==b[:4] and a[8:]==b[8:]
    moves=[dict(index=i,before=list(a[:2]),after=list(b[:2])) for i,(a,b) in enumerate(zip(start,info)) if a[:2]!=b[:2]]
    chk.setsection('UNIT',raw)
    return dict(version=VERSION,mission=mission['mission_id'],bases=reports,moves=moves,
        input_unit_sha256=rules._hash(before),output_unit_sha256=rules._hash(raw),
        all_resource_amounts_and_counts_preserved=True,native_mining_verified=False)

def undo(chk,report):
    raw=bytearray(chk.getsection('UNIT'));assert rules._hash(raw)==report['output_unit_sha256']
    for move in report['moves']:
        offset=move['index']*36+4;assert list(struct.unpack_from('<HH',raw,offset))==move['after']
        struct.pack_into('<HH',raw,offset,*move['before'])
    assert rules._hash(raw)==report['input_unit_sha256'];chk.setsection('UNIT',raw)
