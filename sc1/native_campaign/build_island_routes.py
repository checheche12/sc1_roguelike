"""Generate transport staging/landing cells from the already pinned map terrain."""
from pathlib import Path
import hashlib, json, sys

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import build_all_campaigns as maps

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def generate():
 receipt=json.loads((ROOT/'all_campaign_maps_evidence.json').read_text(encoding='utf8'))
 missions={r['mission_id']:r for r in json.loads((ROOT.parent/'campaign/missions.json').read_text(encoding='utf8'))['missions']}
 routes=[];evidence=[]
 for row in receipt['maps']:
  origins=row['difficulty']['wave_origins'];mission=missions[row['mission_id']]
  if mission['no_production'] or any(o['ground_route_connected'] for o in origins):continue
  path=Path(row['output']);assert digest(path)==row['sha256']
  chk=maps.CHK(path.read_bytes());clear,terrain=maps.load_terrain(chk)
  connected,target=maps.connected_cells(clear,origins[0]['target']);w,h=len(clear[0])*8,len(clear)*8
  info=[maps.unit_info(r) for r in maps.units(chk)];friendly={mission['owner']}|{i for i,t in enumerate(chk.getsection('OWNR')) if t==3}
  protected=[(x,y) for x,y,u,p in info if p in friendly and u!=214]+[target]
  occupied=[(x,y,80 if 106<=u<176 else 40) for x,y,u,p in info if u!=214]
  def cells(center,region,radius,clearance,limit):
   choices=[]
   for y in range(28,h-24,32):
    for x in range(28,w-24,32):
     distance=(x-center[0])**2+(y-center[1])**2
     if distance>radius**2 or not clear[y//8][x//8] or not region[y//8][x//8]:continue
     if any((x-a)**2+(y-b)**2<clearance**2 for a,b in protected):continue
     if any((x-a)**2+(y-b)**2<r*r for a,b,r in occupied):continue
     choices.append((distance,y,x))
   result=[]
   for _,y,x in sorted(choices):
    if all((x-a)**2+(y-b)**2>=48**2 for a,b in result):result.append((x,y))
    if len(result)>=limit:break
   return result
  # Passengers physically fly here and use native unloading/placement. Unlike
  # creating a new army, a landing can approach a defended small island.
  landing=cells(target,connected,max(w,h),0,64)
  assert landing,('No player-island landing cell',row['mission_id'])
  for origin in origins:
   region,center=maps.connected_cells(clear,origin['center'])
   if connected[center[1]//8][center[0]//8]:continue
   loading=cells(center,region,640,512,128)
   if len(loading)<8:continue
   routes.append(dict(mission=row['mission_id'],owner=origin['owner'],race=origin['race'],center=origin['center'],loading=loading,landing=landing))
  assert any(r['mission']==row['mission_id'] for r in routes),('No hostile-island staging',row['mission_id'])
  evidence.append(dict(mission=row['mission_id'],map=str(path),map_sha256=row['sha256'],terrain=terrain,landing_cells=len(landing),routes=sum(r['mission']==row['mission_id'] for r in routes)))
 lines=['#pragma once','#include <cstdint>','namespace sc1_native::island_routes {',
  'struct Point{int x,y;};','struct Route{unsigned mission,owner,race,loading_count,landing_count;Point center,loading[128],landing[64];};','inline constexpr Route routes[]={']
 for r in routes:
  points=lambda values:'{'+','.join('{%d,%d}'%p for p in values)+'}'
  lines.append('{%d,%d,%d,%d,%d,{%d,%d},%s,%s},'%(r['mission'],r['owner'],r['race'],len(r['loading']),len(r['landing']),*r['center'],points(r['loading']),points(r['landing'])))
 lines+=['};','}']
 header=ROOT/'plugin/include/island_routes.generated.h';header.write_text('\n'.join(lines)+'\n',encoding='utf8')
 result=dict(passed=True,routes=len(routes),missions=evidence,header=str(header),header_sha256=digest(header),source_sha256=digest(__file__),game_accessed=False,scope='Offline pinned terrain and map occupancy. Runtime must recheck owner, occupancy and native path regions.')
 (ROOT/'island_routes_evidence.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 return result

if __name__=='__main__':print(json.dumps(generate(),ensure_ascii=False))
