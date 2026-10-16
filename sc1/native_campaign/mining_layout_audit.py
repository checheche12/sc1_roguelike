"""Independent offline resource-field audit helpers; no native game queries.

Terrain buildability follows the pinned OpenBW CV5 unbuildable bit (0x80)
and rejects partially walkable footprint tiles. Worker reachability is a
conservative 24-pixel square on an eight-pixel lattice, including stationary
unit DAT collision obstacles. Mobile units, runtime creep, fog and
mining orders are outside this model.
"""
from __future__ import annotations
from collections import deque
from functools import lru_cache
import hashlib
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
SOURCE_ROOT=HERE.parent/'campaign_sources/raw'
TILESETS=('badlands','platform','install','ashworld','jungle','desert','ice','twilight')
DEPOTS=frozenset((106,131,132,133,154))
MINERALS=frozenset((176,177,178))

@lru_cache(maxsize=8)
def _terrain_bytes(era):
    name=TILESETS[era]
    return ((SOURCE_ROOT/'TileSet'/f'{name}.cv5').read_bytes(),
            (SOURCE_ROOT/'TileSet'/f'{name}.vf4').read_bytes())

def load_buildable_grid(chk):
    """Return 32px tiles allowing a full foundation (no creep/fog/unit test)."""
    width,height=struct.unpack('<HH',chk.getsection('DIM '))
    era=struct.unpack('<H',chk.getsection('ERA '))[0]&7
    cv5,vf4=_terrain_bytes(era)
    tiles=struct.unpack('<'+'H'*(width*height),chk.getsection('MTXM'))
    result=[bytearray(width) for _ in range(height)];cache={}
    for i,tile in enumerate(tiles):
        if tile not in cache:
            group,member=tile>>4,tile&15
            flags=struct.unpack_from('<H',cv5,group*52+2)[0]
            mega=struct.unpack_from('<H',cv5,group*52+20+member*2)[0]
            walk=struct.unpack_from('<16H',vf4,mega*32)
            cache[tile]=int(not(flags&0x80) and all(v&1 for v in walk))
        result[i//width][i%width]=cache[tile]
    # OpenBW applies these map-edge unbuildable tiles after terrain loading.
    if height>=2:
        result[-1][:]=bytes(width)
        for x in list(range(min(5,width)))+list(range(max(0,width-5),width)):
            result[-2][x]=0
    return result

@lru_cache(maxsize=1)
def stock_geometry():
    try:from .build_managed_dat import legacy_fields,source_bytes
    except ImportError:from build_managed_dat import legacy_fields,source_bytes
    fields=legacy_fields('units',source_bytes('units'))
    sizes={i:struct.unpack_from('<2H',fields[36][1],4*i) for i in range(228)}
    boxes={i:struct.unpack_from('<4H',fields[38][1],8*i) for i in range(228)}
    return sizes,boxes

def foundation_buildable(chk,center,depot_type,buildable=None):
    grid=load_buildable_grid(chk) if buildable is None else buildable
    width,height=stock_geometry()[0][depot_type];x,y=center
    left,top=x-width//2,y-height//2
    if left%32 or top%32:return False
    tx,ty=left//32,top//32;tw,th=width//32,height//32
    if tx<0 or ty<0 or ty+th>len(grid) or tx+tw>len(grid[0]):return False
    return all(all(grid[yy][tx:tx+tw]) for yy in range(ty,ty+th))

def _raw_walk(chk):
    width,height=struct.unpack('<HH',chk.getsection('DIM '))
    cv5,vf4=_terrain_bytes(struct.unpack('<H',chk.getsection('ERA '))[0]&7)
    tiles=struct.unpack('<'+'H'*(width*height),chk.getsection('MTXM'))
    result=[bytearray(width*4) for _ in range(height*4)];cache={}
    for i,tile in enumerate(tiles):
        if tile not in cache:
            mega=struct.unpack_from('<H',cv5,(tile>>4)*52+20+(tile&15)*2)[0]
            cache[tile]=bytes(bool(v&1) for v in struct.unpack_from('<16H',vf4,mega*32))
        for dy in range(4):
            result[(i//width)*4+dy][(i%width)*4:(i%width)*4+4]=cache[tile][dy*4:dy*4+4]
    return result

def _footprint(x,y,unit):
    # Placement foundations reserve construction tiles. Existing units block
    # movement with field38 collision extents instead; e.g. a Hatchery's
    # 128x96 placement footprint has a 99x65 collision rectangle.
    _,boxes=stock_geometry();l,t,r,b=boxes[unit]
    return x-l,y-t,x+r+1,y+b+1

def worker_components(chk,info,extra_anchor=None):
    raw=_raw_walk(chk);height,width=len(raw),len(raw[0])
    free=[bytearray(width) for _ in range(height)]
    # Samples represent a worker CENTER at (8*x+4,8*y+4). A radius12 worker
    # covers exactly the 3x3 terrain minitiles around that center.
    for y in range(1,height-1):
        for x in range(1,width-1):
            free[y][x]=int(all(raw[yy][x-1:x+2]==b'\x01\x01\x01' for yy in (y-1,y,y+1)))
    obstacles=[p for p in info if p[2]>=106 and p[2]!=214]
    if extra_anchor is not None:obstacles.append((*extra_anchor['center'],extra_anchor['depot_type'],12))
    for x,y,unit,_ in obstacles:
        l,t,r,b=_footprint(x,y,unit)
        # Exclude all sample centers whose 24px box overlaps the footprint.
        x1=max(0,(l-12-4)//8+1);x2=min(width-1,(r+12-4-1)//8)
        y1=max(0,(t-12-4)//8+1);y2=min(height-1,(b+12-4-1)//8)
        for yy in range(y1,y2+1):free[yy][x1:x2+1]=bytes(x2-x1+1)
    labels=[[-1]*width for _ in range(height)];sizes=[]
    for y in range(height):
        for x in range(width):
            if not free[y][x] or labels[y][x]>=0:continue
            tag=len(sizes);q=deque(((x,y),));labels[y][x]=tag;n=0
            while q:
                xx,yy=q.popleft();n+=1
                for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                    if 0<=nx<width and 0<=ny<height and free[ny][nx] and labels[ny][nx]<0:
                        labels[ny][nx]=tag;q.append((nx,ny))
            sizes.append(n)
    return labels,sizes

def _perimeter_labels(item,labels):
    x,y,unit,_=item;l,t,r,b=_footprint(x,y,unit)
    # First valid worker center along each unobstructed foundation edge.
    x1=(l-12-4)//8;x2=(r+12-4+7)//8
    y1=(t-12-4)//8;y2=(b+12-4+7)//8
    points=[(xx,y1) for xx in range(x1,x2+1)]+[(xx,y2) for xx in range(x1,x2+1)]
    points += [(x1,yy) for yy in range(y1,y2+1)]+[(x2,yy) for yy in range(y1,y2+1)]
    return {labels[yy][xx] for xx,yy in points if 0<=yy<len(labels) and 0<=xx<len(labels[0]) and labels[yy][xx]>=0}

def audit_field(chk,info,mineral_indices,anchor,direction=None,labels=None):
    """Check each assigned mineral's depot-facing access against HQ perimeter."""
    try:from .resource_depot_placement import resource_forbidden_tiles
    except ImportError:from resource_depot_placement import resource_forbidden_tiles
    if labels is None:labels,_=worker_components(chk,info,anchor if anchor.get('kind')=='expansion' else None)
    hq=(*anchor['center'],anchor['depot_type'],12);hq_labels=_perimeter_labels(hq,labels)
    cx,cy=anchor['center'];mineral_results=[]
    for index in mineral_indices:
        x,y,unit,_=info[index]
        if direction is None:
            dx,dy=x-cx,y-cy
            face=(1 if dx>=0 else -1,0) if abs(dx)>=abs(dy) else (0,1 if dy>=0 else -1)
        else:face=tuple(direction)
        # Direction points from HQ towards the minerals. Sample just outside
        # each mineral's HQ-facing edge, plus three lateral offsets.
        l,t,r,b=_footprint(x,y,unit);points=[]
        # Horizontal mineral faces are 64px wide. Samples near their corners
        # are legitimate worker approach positions; restricting them to the
        # central 16px would report a blocked front despite a usable lane.
        offsets=(-8,0,8) if face[0] else (-24,-16,-8,0,8,16,24)
        for offset in offsets:
            if face[0]>0:points.append((((l-12-4)//8)*8+4,y+offset))
            elif face[0]<0:points.append((((r+12-4+7)//8)*8+4,y+offset))
            elif face[1]>0:points.append((x+offset,((t-12-4)//8)*8+4))
            else:points.append((x+offset,((b+12-4+7)//8)*8+4))
        fronts={labels[py//8][px//8] for px,py in points if 0<=py//8<len(labels) and 0<=px//8<len(labels[0]) and labels[py//8][px//8]>=0}
        mineral_results.append({'unit_index':index,'position':[x,y],
             'any_side_reachable':bool(_perimeter_labels(info[index],labels)&hq_labels),
             'depot_facing_front_reachable':bool(fronts&hq_labels)})
    w,h=stock_geometry()[0][anchor['depot_type']];tile=((cx-w//2)//32,(cy-h//2)//32)
    map_size=struct.unpack('<HH',chk.getsection('DIM '))
    return {'anchor':anchor,'foundation_terrain_buildable':foundation_buildable(chk,anchor['center'],anchor['depot_type']),
        'resource_depot_clear':tile not in resource_forbidden_tiles(info,106,map_size),
        'mineral_count':len(mineral_results),'front_reachable_count':sum(m['depot_facing_front_reachable'] for m in mineral_results),
        'any_side_reachable_count':sum(m['any_side_reachable'] for m in mineral_results),
        'minerals':mineral_results,'worker_clearance_pixels':24,'native_mining_verified':False}
