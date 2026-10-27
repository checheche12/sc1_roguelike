"""Protect Korhal's scripted silos and use building-aware reinforcement routes.

Offline CHK and collision checks only; this does not emulate the live pathfinder.
"""
import struct
from collections import deque
from . import mineral_layout as geo, mining_layout_audit as mining

SILO_SEEN_SWITCH=252
SILO_DESTINATIONS=(32,33,34,37,36,35)
ROUTE_RADIUS=20


def destination_centers(chk):
    for loc in SILO_DESTINATIONS:
        left,top,right,bottom=struct.unpack_from('<4I',chk.getsection('MRGN'),(loc-1)*20)
        yield (left+right)//2,(top+bottom)//2


def correct_objective(chk,mission):
    from . import build_all_campaigns as b
    ts=b.triggers(chk)
    silos=[p for p in map(b.unit_info,b.units(chk)) if p[2]==108]
    assert len(silos)==6 and all(p[3]==1 for p in silos)
    # Reserve one audited-unused switch without changing original event indices.
    for t in ts:
        assert not any(c[15]==11 and c[16]==SILO_SEEN_SWITCH for _,c in b.conditions(t))
        assert not any(a[26]==13 and struct.unpack_from('<I',a,20)[0]==SILO_SEEN_SWITCH for _,a in b.actions(t))
    original=ts[22]
    assert [c[16] for _,c in b.conditions(original)]==[0,2,3,4,5,6,7]
    assert any(a[26]==1 for _,a in b.actions(original))
    cs=[b.switch_condition(0,False),b.switch_condition(SILO_SEEN_SWITCH),b.cond(2,1,0,108,10)]
    patched=bytearray(original);patched[:320]=bytes(320)
    for i,c in enumerate(cs):patched[i*20:(i+1)*20]=c
    ts[22]=bytes(patched)
    # Do not mistake an uninitialized/empty world for destruction. Observe an
    # actual enemy silo first. Capture/transfer also removes enemy ownership,
    # matching the stock mission's alternative to destroying each target.
    ts.append(b.new_trigger([b.cond(2,1,1,108)],
                           [b.setswitch(SILO_SEEN_SWITCH)],b.owner_bytes(mission['owner'])))
    chk.setsection('TRIG',b''.join(ts))
    return dict(mission=504,kind='enemy_nuclear_silos_after_seen',target_owner=1,
                initial_silos=6,seen_switch=SILO_SEEN_SWITCH,seen_trigger=len(ts)-1,
                victory_trigger=22,original_success_actions_preserved=True,
                original_physics_lab_route_preserved=True,
                scripted_silo_relocation_preserved=True,
                location_initialization_required=False,live_game_verified=False)


def verify_silo_destinations(chk):
    boxes,_=geo.load_unit_geometry()
    info=list(map(geo._info,geo._records(chk)))
    for dest in destination_centers(chk):
        rect=geo._rect(*dest,108,boxes)
        blockers=[(i,u,x,y) for i,(x,y,u,_) in enumerate(info)
                  if u!=214 and geo._overlap(rect,geo._rect(x,y,u,boxes))]
        assert not blockers,('Silo relocation destination obstructed',dest,blockers)


def route_grid(chk):
    """40px terrain clearance plus complete final building/resource footprints."""
    raw=mining._raw_walk(chk);height,width=len(raw),len(raw[0])
    free=[bytearray(width) for _ in range(height)]
    for y in range(2,height-2):
        for x in range(2,width-2):
            free[y][x]=int(all(raw[yy][x-2:x+3]==b'\x01'*5 for yy in range(y-2,y+3)))
    boxes,_=geo.load_unit_geometry()
    fixed=[(x,y,u) for x,y,u,_ in map(geo._info,geo._records(chk)) if u>=106 and u!=214]
    # Moving the original silos must not close a route that looked open in UNIT.
    fixed.extend((x,y,108) for x,y in destination_centers(chk))
    for x,y,u in fixed:
        left,top,right,bottom=geo._rect(x,y,u,boxes)
        x1=max(0,(left-ROUTE_RADIUS-4)//8+1);x2=min(width-1,(right+ROUTE_RADIUS-5)//8)
        y1=max(0,(top-ROUTE_RADIUS-4)//8+1);y2=min(height-1,(bottom+ROUTE_RADIUS-5)//8)
        for yy in range(y1,y2+1):free[yy][x1:x2+1]=bytes(x2-x1+1)
    return free


def reachable_origins(chk,mission,difficulty):
    from . import build_all_campaigns as b,scripted_openings
    free=route_grid(chk);height,width=len(free),len(free[0])
    base_target=difficulty['wave_origins'][0]['target']
    # A command center occupies its own target point. Its closest free cell
    # can be an enclosed courtyard. Choose an approach in the largest terrain
    # component reaching within 256px of the actual player base instead.
    visited=[bytearray(width) for _ in range(height)];approaches=[]
    for yy in range(height):
        for xx in range(width):
            if not free[yy][xx] or visited[yy][xx]:continue
            q=deque([(xx,yy)]);visited[yy][xx]=1;count=0;nearest=None
            while q:
                x,y=q.popleft();count+=1
                distance=(x*8+4-base_target[0])**2+(y*8+4-base_target[1])**2
                candidate=(distance,x*8+4,y*8+4)
                if distance<=256**2 and (nearest is None or candidate<nearest):nearest=candidate
                for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                    if 0<=nx<width and 0<=ny<height and free[ny][nx] and not visited[ny][nx]:
                        visited[ny][nx]=1;q.append((nx,ny))
            if nearest:approaches.append((count,nearest))
    assert approaches,'No reachable approach to player base'
    _,nearest=max(approaches,key=lambda p:(p[0],-p[1][0]))
    target=list(nearest[1:]);connected,goal=b.connected_cells(free,target)
    info=list(map(b.unit_info,b.units(chk)))
    original=info[:difficulty['original_unit_records_preserved']]
    hostile=set(difficulty['hostile_owners'])
    friendly=[p[:2] for p in original if p[3] not in hostile and p[3]<8 and p[2]!=214]+[base_target]
    occupied=[(x,y,80 if u>=106 else 40) for x,y,u,_ in info if u!=214]
    sources=[p for p in original if p[3] in hostile and (p[2] in b.COMBAT or 106<=p[2]<176)]
    sources.sort(key=lambda p:(not(106<=p[2]<176),-((p[0]-target[0])**2+(p[1]-target[1])**2)))
    origins=[]
    boxes,_=geo.load_unit_geometry()
    north_front=max(geo._rect(x,y,u,boxes)[3] for x,y,u,p in original if u==111 and p==0)+40
    for owner in sorted(hostile):
        for sx,sy,su,p in sources:
            if p!=owner:continue
            if any((sx-o['center'][0])**2+(sy-o['center'][1])**2<640**2 for o in origins):continue
            choices=[]
            for y in range(max(28,sy-384)//32*32+20,min(height*8-24,sy+385),32):
                for x in range(max(28,sx-384)//32*32+20,min(width*8-24,sx+385),32):
                    # Enter on the south/front side of the northern Barracks
                    # line, rather than making the wave traverse its rear yard.
                    if owner==0 and y<north_front:continue
                    if not connected[y//8][x//8] or not scripted_openings.additional_spawn_allowed(mission,x,y):continue
                    if any((x-a)**2+(y-bb)**2<512**2 for a,bb in friendly):continue
                    if any((x-a)**2+(y-bb)**2<radius**2 for a,bb,radius in occupied):continue
                    choices.append(((x-sx)**2+(y-sy)**2,y,x))
            cells=[]
            for _,y,x in sorted(choices):
                if all((x-a)**2+(y-bb)**2>=48**2 for a,bb in cells):cells.append([x,y])
                if len(cells)==32:break
            if len(cells)<4:continue
            assert chk.getsection('SIDE')[owner]==1
            origins.append(dict(mission_id=504,owner=owner,race=1,unit1=0,unit2=32,
                cell_count=len(cells),center=[sx,sy],target=target,cells=cells,source_unit=su,
                ground_route_connected=True,flying_only=False,source_is_original_hostile_position=True,
                friendly_clearance_pixels=512,original_occupancy_clearance_pixels=[40,80],
                route_clearance_pixels=40,final_building_collision_checked=True,
                scripted_silo_destinations_reserved=True,route_goal=goal,
                player_base_target=base_target,north_barracks_front_y=north_front))
            if sum(o['owner']==owner for o in origins)==2:break
        assert sum(o['owner']==owner for o in origins)==2,('Two reachable origins required',owner,goal)
    return origins
