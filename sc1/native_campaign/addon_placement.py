"""Keep full Terran parent/addon landing rectangles clear of moved resources.

DAT placement sizes and addon top-left offsets match OpenBW's
find_connecting_addon calculation. This is an offline footprint guard.
"""
from functools import lru_cache
import struct

PARENTS = {106:107,113:120,114:115,116:117}
ADDONS = {107:106,108:106,115:114,117:116,118:116,120:113}

@lru_cache(maxsize=1)
def geometry():
    try:from .build_managed_dat import legacy_fields,source_bytes
    except ImportError:from build_managed_dat import legacy_fields,source_bytes
    fields=legacy_fields('units',source_bytes('units'))
    sizes=[struct.unpack_from('<2H',fields[36][1],4*i) for i in range(228)]
    offsets=[struct.unpack_from('<2h',fields[37][1],4*i) for i in range(228)]
    return sizes,offsets

def rect(center,unit):
    width,height=geometry()[0][unit];x,y=center
    return x-width//2,y-height//2,x+width//2,y+height//2

def reservations(info):
    sizes,offsets=geometry();result=set()
    for x,y,unit,owner in info:
        if unit in PARENTS:
            parent=rect((x,y),unit);addon=PARENTS[unit];dx,dy=offsets[addon]
            result.add(parent);result.add((parent[0]+dx,parent[1]+dy,parent[0]+dx+sizes[addon][0],parent[1]+dy+sizes[addon][1]))
        elif unit in ADDONS:
            addon=rect((x,y),unit);parent=ADDONS[unit];dx,dy=offsets[unit]
            result.add(addon);result.add((addon[0]-dx,addon[1]-dy,addon[0]-dx+sizes[parent][0],addon[1]-dy+sizes[parent][1]))
    return result

def resource_clear(point,unit,reserved):
    l,t,r,b=rect(point,unit)
    return not any(l<rr and r>ll and t<bb and b>tt for ll,tt,rr,bb in reserved)
