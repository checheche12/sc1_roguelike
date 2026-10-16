"""Read-only terrain connectivity analysis; this does not emulate SC pathing."""
from collections import deque
import hashlib
import json
from pathlib import Path
import struct
from analyze_terran01 import parse_sections

ROOT=Path(__file__).resolve().parent
DEST=ROOT.parent/'campaign/analysis'

def load_grid():
    chk,_=parse_sections((ROOT/'raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk').read_bytes())
    cv5=(ROOT/'raw/TileSet/badlands.cv5').read_bytes()
    vf4=(ROOT/'raw/TileSet/badlands.vf4').read_bytes()
    width,height=struct.unpack('<HH',chk['DIM ']); tiles=struct.unpack('<'+'H'*(width*height),chk['MTXM'])
    grid=[[False]*(width*4) for _ in range(height*4)]
    for y in range(height):
        for x in range(width):
            tile=tiles[y*width+x]; group,member=tile>>4,tile&15
            mega=struct.unpack_from('<H',cv5,group*52+20+member*2)[0]
            flags=struct.unpack_from('<16H',vf4,mega*32)
            for sy in range(4):
                for sx in range(4):grid[y*4+sy][x*4+sx]=bool(flags[sy*4+sx]&1)
    # Conservative terrain-only center clearance: 3x3 mini tiles (24x24px).
    cleared=[[False]*(width*4) for _ in range(height*4)]
    for y in range(1,height*4-1):
        for x in range(1,width*4-1):
            cleared[y][x]=all(grid[yy][xx] for yy in range(y-1,y+2) for xx in range(x-1,x+2))
    return grid,cleared

def nearest(grid,xy):
    x,y=xy[0]//8,xy[1]//8
    options=[(abs(xx-x)+abs(yy-y),xx,yy) for yy in range(max(0,y-8),min(len(grid),y+9))
             for xx in range(max(0,x-8),min(len(grid[0]),x+9)) if grid[yy][xx]]
    _,x,y=min(options);return (x,y)

def route(grid,origin,destination):
    start,goal=nearest(grid,origin),nearest(grid,destination)
    queue=deque([start]);previous={start:None}
    while queue:
        x,y=queue.popleft()
        if (x,y)==goal:
            result=[];at=goal
            while at is not None:result.append([at[0]*8+4,at[1]*8+4]);at=previous[at]
            return result[::-1]
        for xx,yy in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
            if 0<=yy<len(grid) and 0<=xx<len(grid[0]) and grid[yy][xx] and (xx,yy) not in previous:
                previous[xx,yy]=(x,y);queue.append((xx,yy))
    return None

def main():
    grid,clear=load_grid()
    points={'start':[128,128],'raynor':[1014,1031],'base_approach':[1056,1600],
            'east_garrison':[1888,1296],'southwest_garrison':[256,1504],
            'far_southwest_garrison':[224,1872],'northeast_garrison':[1744,544]}
    pairs=[('start','raynor'),('raynor','base_approach')]+[(name,'base_approach') for name in points if name.endswith('garrison')]
    routes=[]
    for a,b in pairs:
        path=route(clear,points[a],points[b]);assert path
        routes.append({'from':a,'to':b,'requested_origin':points[a],'requested_destination':points[b],
                       'snapped_origin':path[0],'snapped_destination':path[-1],
                       'four_way_terrain_path_pixels':(len(path)-1)*8,'waypoints_every_128px':path[::16]+[path[-1]]})
    result={'schema_version':1,'scope':'Offline CV5/VF4 terrain connectivity only, with24px clearance. No live units/buildings or native pathfinder simulation.',
            'source':'https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/sc.h',
            'assets':{name:hashlib.sha256((ROOT/'raw/TileSet'/name).read_bytes()).hexdigest() for name in ('badlands.cv5','badlands.vf4')},
            'grid_size_minitiles':[len(grid[0]),len(grid)],'points':points,'routes':routes,
            'no_game_access':True,'map_files_changed':False}
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/'terran01_terrain_routes.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    # Small vector plot: generated analytical data visualization, not a game screenshot.
    shapes=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 2048 2048">','<rect width="2048" height="2048" fill="#121820"/>']
    for y,row in enumerate(grid):
        start=None
        for x,walk in enumerate(row+[False]):
            if walk and start is None:start=x
            if not walk and start is not None:
                shapes.append(f'<rect x="{start*8}" y="{y*8}" width="{(x-start)*8}" height="8" fill="#424e55"/>');start=None
    for r in routes:
        path=route(clear,points[r['from']],points[r['to']]);shapes.append('<polyline fill="none" stroke="#facc15" stroke-width="4" points="'+' '.join(f'{x},{y}' for x,y in path)+'"/>')
    for name,(x,y) in points.items():
        shapes.append(f'<circle cx="{x}" cy="{y}" r="15" fill="#fa694d"/><text x="{x-100}" y="{y-28}" font-size="28" fill="white">{name}</text>')
    shapes.append('</svg>');(DEST/'terran01_terrain_routes.svg').write_text('\n'.join(shapes),encoding='utf-8')
    print(json.dumps({'routes':[{k:v for k,v in row.items() if k!='waypoints_every_128px'} for row in routes]}))

if __name__=='__main__':main()
