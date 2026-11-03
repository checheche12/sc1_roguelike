"""Pinned playtest placement corrections after the general resource planner.

Keep every unit record except reviewed XY coordinates; the sole location edit
moves P10's scripted starting Command Center. These are offline checks.
"""
import copy
import math
import struct
from . import ladder_resource_banks as banks, addon_placement as addons
from .mission_placement_plan import PLAN

VERSION = 'campaign_playtest_20261103_v3'
MISSIONS = frozenset(map(int, PLAN))
BUILDINGS = {
    int(mid): {m['index']: (m['before'][2],m['before'][3],tuple(m['before'][:2]),tuple(m['after'][:2]))
               for m in plan['moves'] if m['before'][2] not in banks.rules.MINERALS | banks.gas.GAS_TYPES}
    for mid,plan in PLAN.items()
}
TERRAN9_MINERALS = {m['index']:tuple(m['after'][:2]) for m in PLAN['109']['moves']
                    if m['before'][2] in banks.rules.MINERALS}
LOCATION_310 = ((864,608,992,704),(384,768,512,864))

def units(chk):
    return list(map(banks.rules.geometry._info,banks.rules.geometry._records(chk)))


def parent_site(addon):
    x,y,unit,_=addon
    sizes,offsets=addons.geometry()
    left,top,_,_=addons.rect((x,y),unit)
    dx,dy=offsets[unit];parent=addons.ADDONS[unit]
    return (left-dx+sizes[parent][0]//2,top-dy+sizes[parent][1]//2),parent


def _spatial_selectors(chk,unit):
    from . import build_all_campaigns as maps
    locations=set()
    for trigger in maps.triggers(chk):
        for _,c in maps.conditions(trigger):
            if c[15] in (3,7,16,17) and struct.unpack_from('<H',c,12)[0] in (unit,229,231,232):
                locations.add(struct.unpack_from('<I',c)[0])
        for _,a in maps.actions(trigger):
            if a[26] in (23,25,38,39,43,44,46,48,49,50,51,52,53) and struct.unpack_from('<H',a,24)[0] in (unit,229,231,232):
                locations.add(struct.unpack_from('<I',a)[0])
    return {loc for loc in locations if 0<loc<=len(chk.getsection('MRGN'))//20}



def verify_locations(before,after,mission):
    raw=bytearray(before.getsection('MRGN'))
    if mission['mission_id']==310:
        assert struct.unpack_from('<4I',raw,60)==LOCATION_310[0]
        struct.pack_into('<4I',raw,60,*LOCATION_310[1])
    assert bytes(raw)==after.getsection('MRGN'),'Unreviewed location edit'



def verify_locations(before,after,mission):
    raw=bytearray(before.getsection('MRGN'))
    if mission['mission_id']==310:
        assert struct.unpack_from('<4I',raw,60)==LOCATION_310[0]
        struct.pack_into('<4I',raw,60,*LOCATION_310[1])
    assert bytes(raw)==after.getsection('MRGN'),'Unreviewed location edit'


def mineral_corridors(chk,info,groups):
    """48px army paths across each bank's local terrain, including small exits."""
    from collections import Counter,defaultdict
    walk,_=banks.rules.geometry.load_terrain(chk)
    for _ in range(3):walk=banks.rules._worker_terrain(walk)
    boxes=banks.rules.geometry.load_unit_geometry()[0];result=[]
    for group in groups:
        ids=set(group['mineral_indices']+group['gas_indices'])
        bounds=banks.rules._bounds([info[i][:2] for i in ids],walk,24)
        removed=[(*p[:2],214,p[3]) if i in ids else p for i,p in enumerate(info)]
        old,_,_=banks.rules._components(walk,removed,bounds,boxes,radius=24)
        new,sizes,boundary=banks.rules._components(walk,info,bounds,boxes,radius=24)
        overlap=defaultdict(Counter)
        for arow,brow in zip(old,new):
            for a,b in zip(arow,brow):
                if a and b and (b in boundary or sizes[b]>=128):overlap[a][b]+=1
        result.append(not any(sum(n>=64 for n in hits.values())>1 for hits in overlap.values()))
    return result


def verify(chk,mission,report):
    mid=mission['mission_id'];info=units(chk);boxes=banks.rules.geometry.load_unit_geometry()[0]
    heights=banks.terrain_heights(chk);grid=banks.mining.load_buildable_grid(chk)
    groups=report['bases'];model=banks.court._ground_model(info)
    for i,(unit,owner,old,dest) in BUILDINGS.get(mid,{}).items():
        assert info[i]==(*dest,unit,owner),(mid,i,'unexpected building')
        rect=addons.rect(dest,unit)
        assert banks.mining.foundation_buildable(chk,dest,unit,grid),(mid,i,'terrain')
        assert banks.flat_rect(heights,rect,heights[old[1]//8][old[0]//8]),(mid,i,'plateau')
        assert not banks.rules._fixed_collision(rect,model,{i},boxes,mobile=False),(mid,i,'collision')
        if mid!=108:
            assert all(banks.rect_gap(rect,addons.rect(p[:2],p[2]))>=64
                for p in info if p[2] in banks.rules.MINERALS|banks.gas.GAS_TYPES),(mid,i,'resource clearance')
        if unit==165:
            assert any(p[2:]==(156,owner) and abs(p[0]-dest[0])<=160 and abs(p[1]-dest[1])<=96 for p in info)
        if unit in banks.rules.HEADQUARTERS:assert banks.rules._resource_clear(dest,info),(mid,i,'HQ resource clearance')
    proof=dict(passed=True,moved_building_foundations_clear=True,live_gameplay_verified=False)
    if mid==108:
        landings=[];virtual=list(info);rects=[]
        for i in (239,241,250,256,259):
            addon=info[i];center,parent=parent_site(addon);rect=addons.rect(center,parent)
            assert banks.mining.foundation_buildable(chk,center,parent,grid),(i,'parent terrain')
            assert banks.mining.foundation_buildable(chk,addon[:2],addon[2],grid),(i,'addon terrain')
            assert not banks.rules._fixed_collision(rect,model,{i},boxes,mobile=False),(i,'parent collision')
            assert not any(banks.rules.geometry._overlap(rect,r) for r in rects),(i,'parent overlap')
            if parent==106:
                assert list(center) in [g['anchor']['center'] for g in groups]
                assert banks.rules._resource_clear(center,info),(i,'CC resource exclusion')
            virtual.append((*center,parent,0));rects.append(rect)
            landings.append(dict(addon_index=i,parent_type=parent,parent_center=list(center)))
        for g in groups:assert banks.audit_base(chk,virtual,g,heights,boxes)['passed']
        proof.update(addon_landings=landings,all_parents_can_coexist=True)
    if mid==310:
        from . import build_all_campaigns as maps
        assert struct.unpack_from('<4I',chk.getsection('MRGN'),60)==LOCATION_310[1]
        refs=[a for t in maps.triggers(chk) for _,a in maps.actions(t) if struct.unpack_from('<I',a)[0]==4]
        assert len(refs)==1 and refs[0][26]==11 and struct.unpack_from('<H',refs[0],24)[0]==106
        center=(448,816);assert banks.mining.foundation_buildable(chk,center,106,grid)
        assert not banks.rules._fixed_collision(addons.rect(center,106),model,set(),boxes,mobile=False)
        virtual=info+[(*center,106,1)]
        for g in groups:assert banks.audit_base(chk,virtual,g,heights,boxes)['passed']
        proof.update(starting_command_center=list(center),only_starting_cc_location_referenced=True)
    if mid==503:
        g=next(g for g in groups if g['parent_site_index']==6);anchor=g['anchor'];cx,cy=anchor['center']
        assert banks.flat_rect(heights,(cx-96,cy-80,cx+96,cy+80),heights[cy//8][cx//8])
        assert all(banks.rect_gap(addons.rect((cx,cy),106),addons.rect(p[:2],p[2]))>=32
                   for p in model if p[2]>=106 and p[2]!=214)
        labels,sizes=banks.mining.worker_components(chk,model,anchor)
        exits=banks.mining._perimeter_labels((cx,cy,106,12),labels)
        assert len(exits)==1,(mid,'CC edges disconnected',exits)
        access=banks.mining.audit_field(chk,model,g['mineral_indices'],anchor,labels=labels)
        assert access['front_reachable_count']==len(g['mineral_indices'])
        proof.update(expansion_cc=list(anchor['center']),clear_32px_foundation_ring=True,
                     all_worker_exit_edges_connected_to_minerals=True)
        assert (cx,cy)==(736,3856) and heights[cy//8][cx//8]==0
        proof['expansion_on_lower_plaza']=True
    if mid==506:
        rect=struct.unpack_from('<4I',chk.getsection('MRGN'),13*20)
        center=[(rect[0]+rect[2])//2,(rect[1]+rect[3])//2]
        group=next(g for g in groups if g['parent_site_index']==4)
        assert center==[1312,3504] and group['anchor']['center']==center
        assert group['anchor'].get('scripted_starting_depot_location')==14
        assert banks.mining.foundation_buildable(chk,center,106,grid)
        assert banks.rules._resource_clear(center,info)
        assert not banks.rules._fixed_collision(addons.rect(center,106),model,set(),boxes,mobile=False)
        proof['player_arrival_command_center_resource_site']=center
    if mid==603:
        corridors=mineral_corridors(chk,info,groups)
        assert all(corridors),(mid,'local mineral corridor blocked',corridors)
        proof.update(local_resource_corridors= len(corridors),army_diameter_pixels=48)
    return proof


def apply(chk,mission,report):
    mid=mission['mission_id']
    if mid not in MISSIONS:return report
    plan=PLAN[str(mid)];before=chk.getsection('UNIT');original=units(chk);info=list(original)
    assert banks.rules._hash(before)==plan['input_unit_sha256'],(mid,'planner input differs from reviewed plan')
    report=copy.deepcopy(report)
    assert 'playtest_placement' not in report
    for move in plan['moves']:
        i=move['index'];assert list(info[i])==move['before'],(mid,i)
        assert move['before'][2:]==move['after'][2:]
        info[i]=tuple(move['after'])
    changed=[m['index'] for m in plan['moves']]
    explicit,locations=banks.rules._critical_locations(chk,original)
    resources=[i for i in changed if info[i][2] in banks.rules.MINERALS|banks.gas.GAS_TYPES]
    boxes=banks.rules.geometry.load_unit_geometry()[0]
    model=banks.court._ground_model(info)
    assert all(not banks.rules._fixed_collision(addons.rect(info[i][:2],info[i][2]),model,{i},boxes,mobile=False)
               for i in resources),(mid,'overlapping resource foundations')
    assert not set(resources)&explicit,(mid,'scripted resource moved')
    assert banks.rules._critical_membership(chk,original,info,resources,locations),(mid,'resource trigger region')
    for i in set(changed)-set(resources):
        assert banks.rules._critical_membership(chk,original,info,[i],_spatial_selectors(chk,info[i][2])),(mid,i,'building trigger region')
    raw=bytearray(before)
    for i in changed:struct.pack_into('<HH',raw,i*36+4,*info[i][:2])
    chk.setsection('UNIT',raw)
    location_changes=[]
    if mid==310:
        regions=bytearray(chk.getsection('MRGN'))
        assert struct.unpack_from('<4I',regions,60)==LOCATION_310[0]
        struct.pack_into('<4I',regions,60,*LOCATION_310[1]);chk.setsection('MRGN',regions)
        location_changes=[dict(location=4,before=list(LOCATION_310[0]),after=list(LOCATION_310[1]))]
    report['bases']=copy.deepcopy(plan['groups'])
    prior={m['index']:m['before'] for m in report['moves']}
    report['moves']=[dict(index=i,before=prior.get(i,list(a[:2])),after=list(b[:2]))
                     for i,(a,b) in enumerate(zip(original,info)) if prior.get(i,list(a[:2]))!=list(b[:2])]
    report['output_unit_sha256']=banks.rules._hash(raw)
    groups=report['bases'];heights=banks.terrain_heights(chk);boxes=banks.rules.geometry.load_unit_geometry()[0]
    for g in groups:
        g['mineral_positions']=[list(info[i][:2]) for i in g['mineral_indices']]
        g['gas_positions']=[list(info[i][:2]) for i in g['gas_indices']]
        g['audit']=banks.audit_base(chk,info,g,heights,boxes)
        assert g['audit']['passed'],(mid,g['anchor'],g['audit'])
    report['additional_depot_sites']=[g['anchor'] for g in groups if g['anchor'].get('additional_group_depot')]
    report['maximum_minerals_per_depot']=max(12,max(len(g['mineral_indices']) for g in groups))
    report['adaptive_group_overrides']={str(parent):sum(g['parent_site_index']==parent for g in groups)
                                      for parent in {g['parent_site_index'] for g in groups}}
    report['small_split_group_policy']='Merge newly split groups of seven or fewer; preserve original small fields.'
    walk,_=banks.rules.geometry.load_terrain(chk)
    army=banks.rules._worker_terrain(banks.rules._worker_terrain(banks.rules._worker_terrain(walk)))
    assert not changed or banks.rules._army_route_ok(original,info,changed,army,boxes,{'baseline':original}),(mid,'army route')
    report['playtest_placement']=dict(version=VERSION,mission=mid,changes=copy.deepcopy(plan['moves']),
        location_changes=location_changes,only_reviewed_coordinates_changed=True,script_region_membership_preserved=True,
        army_routes_preserved=True,verification=verify(chk,mission,report))
    return report

def adjust_difficulty(chk,mission,difficulty):
    changes=PLAN.get(str(mission['mission_id']),{}).get('wave_cell_changes',[])
    if not changes:return difficulty
    result=copy.deepcopy(difficulty)
    result['resource_wave_origins']=copy.deepcopy(difficulty['wave_origins'])
    for change in changes:
        assert result['wave_origins'][change['index']]==change['before']
        result['wave_origins'][change['index']]=copy.deepcopy(change['after'])
    result['placement_wave_cells']=dict(reason='Keep the merged mineral banks and reinforcement cells separate.',
                                      changed_origins=[c['index'] for c in changes],same_owners_targets_counts=True)
    verify_wave_cells(chk,mission,result)
    return result


def verify_wave_cells(chk,mission,difficulty):
    changes=PLAN.get(str(mission['mission_id']),{}).get('wave_cell_changes',[])
    if not changes:return
    info=units(chk);walk,_=banks.rules.geometry.load_terrain(chk)
    army=banks.rules._worker_terrain(banks.rules._worker_terrain(banks.rules._worker_terrain(walk)))
    boxes=banks.rules.geometry.load_unit_geometry()[0]
    labels,sizes,_=banks.rules._components(army,info,(0,0,len(army[0]),len(army)),boxes,radius=24)
    owner=mission['owner'];own=chk.getsection('OWNR');friendly={owner}|{i for i,v in enumerate(own) if v==3}
    protected=[p[:2] for p in info[:difficulty['original_unit_records_preserved']] if p[3] in friendly and p[2]!=214]
    for change in changes:
        before,after=change['before'],change['after']
        assert {k:v for k,v in before.items() if k!='cells'}=={k:v for k,v in after.items() if k!='cells'}
        assert len(after['cells'])==after['cell_count'] and len(after['cells'])>=4
        for x,y in after['cells']:
            assert labels[y//8][x//8] and sizes[labels[y//8][x//8]]>=512
            assert all(math.dist((x,y),p)>=512 for p in protected+[after['target']])
            assert all(not(l-24<x<r+24 and t-24<y<b+24)
                for l,t,r,b in (addons.rect(p[:2],p[2]) for p in info if p[2] in banks.rules.MINERALS|banks.gas.GAS_TYPES))
        assert difficulty['wave_origins'][change['index']]==after
