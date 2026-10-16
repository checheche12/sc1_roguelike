"""Deterministic, inspected Terran01 additions; no game process access."""
from collections import deque
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'campaign_sources'))
from analyze_terran01_paths import load_grid, nearest, route
sys.path.insert(0, str(ROOT / 'native_campaign'))
from resource_depot_placement import resource_forbidden_tiles

TERRAN_UNITS = (0,1,2,3,5,7,8,9,11,12,13,14,30,32,34,58,
               106,107,108,109,110,111,112,113,114,115,116,117,118,120,122,123,124,125)
TERRAN_UPGRADES = {i: (3 if i in (0,1,2,7,8,9) else 1)
                   for i in (0,1,2,7,8,9,16,17,19,20,21,22,23,51,54)}
TERRAN_TECH = tuple(range(11)) + (24,30,34)
INNATE_TECH = (4,6,34)  # Scanner sweep, defensive matrix, medic healing: not research purchases.
ORIGINS = (('east', (1808,896)), ('west', (256,1504)),
           ('far_west', (224,1872)), ('northeast', (1744,544)))
WAVES = ((14,2),(20,4),(26,6),(32,8),(38,10),(44,12),(48,12))

def records(data):
    return [data[i:i+36] for i in range(0,len(data),36)]

def unit_info(record):
    x,y,unit = struct.unpack_from('<HHH',record,4)
    return x,y,unit,record[16]

def accessible(clear):
    start = nearest(clear,(1056,1600)); seen = {start}; pending = deque([start])
    while pending:
        x,y = pending.popleft()
        for a,b in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0 <= b < len(clear) and 0 <= a < len(clear[0]) and clear[b][a] and (a,b) not in seen:
                seen.add((a,b)); pending.append((a,b))
    return seen

def unlock(chk):
    puni = bytearray(chk.getsection('PUNI'))
    for unit in TERRAN_UNITS:
        puni[228+unit] = 1
        puni[14*228+unit] = 0
    chk.setsection('PUNI',puni)
    upgrades = bytearray(chk.getsection('PUPx'))
    for i,maximum in TERRAN_UPGRADES.items():
        upgrades[61+i] = maximum
        upgrades[13*61+i] = 0
        upgrades[27*61+i] = 0
    chk.setsection('PUPx',upgrades)
    tech = bytearray(chk.getsection('PTEx'))
    for i in TERRAN_TECH:
        tech[44+i] = 1
        tech[13*44+i] = int(i in INNATE_TECH)
        tech[27*44+i] = 0
    chk.setsection('PTEx',tech)

def apply(chk):
    """Mutate only authorized settings and additions; return runtime config/evidence."""
    unlock(chk)
    grid,clear = load_grid(); connected = accessible(clear)
    old = records(chk.getsection('UNIT')); assert len(old) == 49
    old_info = [unit_info(r) for r in old]
    occupied = [(x,y) for x,y,u,p in old_info if u != 214]
    next_serial = max(struct.unpack_from('<I',r)[0] for r in old) + 1
    additions = []; reinforcement_evidence = []
    protected = [(x,y,384 if u < 100 and p == 1 else (256 if p == 2 else 320))
                 for x,y,u,p in old_info if p in (1,2) and u != 214]
    for source in old:
        x,y,unit,owner = unit_info(source)
        if (unit,owner) != (37,4): continue
        candidates = []
        for yy in range(max(12,y-112),min(2036,y+113),8):
            for xx in range(max(12,x-112),min(2036,x+113),8):
                px,py = (xx//8)*8+4,(yy//8)*8+4
                if (px//8,py//8) not in connected: continue
                if any((px-a)**2+(py-b)**2 < 32**2 for a,b in occupied): continue
                if any((px-a)**2+(py-b)**2 < radius**2 for a,b,radius in protected): continue
                candidates.append(((px-x)**2+(py-y)**2,py,px))
        chosen = []
        for _,py,px in sorted(candidates):
            if any((px-a)**2+(py-b)**2 < 32**2 for a,b in occupied): continue
            record=bytearray(source);struct.pack_into('<IHH',record,0,next_serial,px,py)
            next_serial+=1;additions.append(bytes(record));occupied.append((px,py));chosen.append([px,py])
            if len(chosen)==2: break
        assert len(chosen)==2,('no static reinforcement space',x,y)
        reinforcement_evidence.append({'original':[x,y],'added':chosen})
    assert len(additions)==46

    # A 4x2-tile geyser, near the command center and clear of existing resources.
    # Foundation clearance alone is insufficient: depot placement rejects
    # resources within three tiles of its entire 4x3 footprint. Preserve every
    # original placed depot position that was resource-clear before this addition.
    originally_forbidden=resource_forbidden_tiles(old_info,map_size=(64,64))
    rebuild_positions=[((x-64)//32,(y-48)//32) for x,y,u,p in old_info
                       if u in (106,131,132,133,154) and ((x-64)//32,(y-48)//32) not in originally_forbidden]
    tiles=struct.unpack('<4096H',chk.getsection('MTXM'))
    cv5=(ROOT/'campaign_sources/raw/TileSet/badlands.cv5').read_bytes()
    candidates=[]
    for y in range(1568,1921,32):
        for x in range(800,1569,32):
            # Leave the original north entrance and command-center addon side open.
            if 920 <= x <= 1200 and y <= 1680:continue
            gas_forbidden=resource_forbidden_tiles([(x,y,188,11)],map_size=(64,64))
            if any(position in gas_forbidden for position in rebuild_positions):continue
            if any(not grid[b][a] for b in range((y-32)//8,(y+32)//8) for a in range((x-64)//8,(x+64)//8)):continue
            if any(struct.unpack_from('<H',cv5,(tiles[ty*64+tx]>>4)*52+2)[0]&0x80
                   for ty in range((y-32)//32,(y+32)//32) for tx in range((x-64)//32,(x+64)//32)):continue
            blocked=False
            for ux,uy,u,p in old_info:
                if u==214:continue
                hx,hy=(64,48) if u==106 else ((48,32) if u==109 else ((32,16) if u in (176,177,178) else (16,16)))
                if abs(x-ux)<64+hx+32 and abs(y-uy)<32+hy+32:blocked=True;break
            if blocked or (x//8,y//8) not in connected:continue
            candidates.append(((x-1056)**2+(y-1744)**2,y,x))
    assert candidates,'no verified geyser footprint'
    _,gy,gx=min(candidates)
    template=next(r for r in old if unit_info(r)[2] in (176,177,178))
    geyser=bytearray(template);struct.pack_into('<IHHH',geyser,0,next_serial,gx,gy,188)
    geyser[16]=11;struct.pack_into('<I',geyser,20,5000);additions.append(bytes(geyser))
    chk.setsection('UNIT',b''.join(old+additions))
    owner=bytearray(chk.getsection('OWNR')); assert owner[6]==0;owner[6]=5;chk.setsection('OWNR',owner)
    side=bytearray(chk.getsection('SIDE'));side[6]=0;chk.setsection('SIDE',side)
    force=bytearray(chk.getsection('FORC'));force[6]=force[4];chk.setsection('FORC',force)

    origin_evidence=[]
    for name,(x,y) in ORIGINS:
        choices=[]
        for py in range(max(20,y-320)//32*32+20,min(2028,y+321),32):
            for px in range(max(20,x-320)//32*32+20,min(2028,x+321),32):
                if (px//8,py//8) not in connected:continue
                if any((px-a)**2+(py-b)**2 < 32**2 for a,b in occupied):continue
                choices.append(((px-x)**2+(py-y)**2,py,px))
        cells=[[px,py] for _,py,px in sorted(choices)[:90]];assert len(cells)==90,(name,len(cells))
        bounds=[min(p[0] for p in cells)-20,min(p[1] for p in cells)-20,
                max(p[0] for p in cells)+20,max(p[1] for p in cells)+20]
        guard=[max(0,bounds[0]-512),max(0,bounds[1]-512),min(2048,bounds[2]+512),min(2048,bounds[3]+512)]
        path=route(clear,(x,y),(1056,1600));assert path
        origin_evidence.append({'name':name,'center':[x,y],'cells':cells,'bounds':bounds,'guard':guard,
            'terrain_route_pixels':(len(path)-1)*8,'terrain_waypoints':path[::16]+[path[-1]]})
    # Reserve only previously zero extended locations; originals1..64 untouched.
    locations=bytearray(chk.getsection('MRGN'))
    for loc,rect in ((65,[0,0,1,1]),(66,[0,0,1,1]),(67,[0,0,1,1]),(68,[0,0,1,1]),
                     (69,[896,1504,1408,1952]),(70,[1056,1600,1056,1600])):
        assert locations[(loc-1)*20:loc*20]==bytes(20)
        struct.pack_into('<4IHH',locations,(loc-1)*20,*rect,0,0)
    chk.setsection('MRGN',locations)
    return {'schema_version':1,'mission':101,'revision':'hard-t01-growth-v1','enabled':True,
        'original_units_preserved':49,'original_zerglings':23,'static_zerglings_added':46,'static_zerglings_total':69,
        'new_static_minimum_clearance_pixels':{'starting_p2_mobile_units':384,'raynor':256,'original_p2_buildings':320},
        'static_reinforcements':reinforcement_evidence,'static_owner_zero_based':4,'wave_owner_zero_based':6,
        'wave_compositions':[list(w) for w in WAVES],'base_wave_unit_cap':60,'wave_unit_cap':90,
        'wave_zergling_cap':72,'wave_hydralisk_cap':18,
        'wave_growth':{'per_stack_numerator':1,'denominator':4,'fraction_carry':True,
                       'rounding':'carry quarters by unit type only on successful wave attempts',
                       'cap_note':'2 stacks reach 72 zerglings +18 hydralisks; further stacks are capped per wave'},
        'active_wave_unit_cap':160,'active_wave_hydralisk_cap':40,
        'max_wave_supply':54,'active_wave_supply_cap':100,
        'first_elapsed_seconds':180,'base_arrival_grace_ticks':1440,'interval_ticks':2880,
        'warning_ticks':96,'stuck_order_interval_ticks':720,'ticks_per_fastest_second':24,
        'time_note':'ElapsedTime180 is the game trigger clock; hook ticks are about24/sec atFastest and slower at slower speeds.',
        'origins':origin_evidence,'locations':{'spawn':65,'guard':66,'point':67,'point_clearance':68,'home':69,'target':70},
        'geyser':{'unit_id':188,'owner_zero_based':11,'position':[gx,gy],'resources':5000,
                  'footprint_pixels':[128,64],'cv5_buildable_and_vf4_walkable':True,
                  'original_depot_rebuild_tiles_preserved':[list(p) for p in rebuild_positions],
                  'resource_exclusion_checked':True,'native_can_build_verified':False},
        'unlock':{'player':'P2','unit_ids':list(TERRAN_UNITS),'upgrade_maximums':{str(k):v for k,v in TERRAN_UPGRADES.items()},
                  'available_technology_ids':list(TERRAN_TECH),'innate_researched_ids':list(INNATE_TECH),
                  'researched_purchasable_techs':False,'initial_upgrade_levels':0,'normal_costs_and_prerequisites':True},
        'source_urls':['https://github.com/bwapi/bwapi/blob/main/bwapi/include/BWAPI/UnitType.h',
                       'https://github.com/bwapi/bwapi/blob/main/bwapi/include/BWAPI/TechType.h',
                       'https://github.com/bwapi/bwapi/blob/main/bwapi/include/BWAPI/UpgradeType.h',
                       'https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/sc.h'],
        'limits':['Terrain connectivity is static, not native pathfinder verification.',
                  'Only Terran01 has configured placements; other original missions are not yet strengthened.',
                  'No live-game difficulty, refinery placement or combat balance verification.']}
