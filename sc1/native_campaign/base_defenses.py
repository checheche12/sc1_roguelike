"""Deterministic, append-only fortifications sized from each original enemy base.

No resources, scripts, original actors or wave budgets are changed. Foundations
require a clear 64px bypass ring; resource lines and human openings are reserved.
The native companion keeps only these added defenders near their assigned post.
"""
from __future__ import annotations
import hashlib
import struct
from pathlib import Path
from . import mineral_layout as geo, mining_layout_audit as mining
from . import mission_balance, scripted_openings, addon_placement

HQ={106,131,132,133,154}
PRODUCTION={111,113,114,131,132,133,155,160,167}
BUILDINGS=HQ|{107,108,109,110,111,112,113,114,115,116,117,118,120,122,123,124,125,
    134,135,136,137,138,139,140,141,142,143,144,146,149,155,156,157,159,160,162,163,164,165,166,167,169,170,171,172}
TOWERS={124,144,146,162}
GROUND=mission_balance.ARMED-mission_balance.AIR-{50,103,30}
REVISION=2026102385
sha=lambda raw:hashlib.sha256(raw).hexdigest()
dist=lambda a,b:(a[0]-b[0])**2+(a[1]-b[1])**2

def budget(score,army):
    tier=0 if score<12 else 1 if score<28 else 2 if score<55 else 3
    return tier,min(40,max((6,12,20,28)[tier],(army*35+99)//100)),(2,4,6,8)[tier]

def clusters(original,hostile):
    remaining={i for i,p in enumerate(original) if p[3] in hostile and p[2] in BUILDINGS}
    result=[]
    while remaining:
        first=min(remaining);remaining.remove(first);group=[first]
        for i in group:
            nearby=sorted(j for j in remaining if original[j][3]==original[i][3] and dist(original[i],original[j])<=384**2)
            remaining.difference_update(nearby);group.extend(nearby)
        # Isolated turrets are not separate bases. Count actual infrastructure.
        if len(group)>=3 or any(original[i][2] in HQ|PRODUCTION for i in group):result.append(sorted(group))
    return result

def record(unit,owner,x,y,serial):
    r=bytearray(36);struct.pack_into('<IHHH',r,0,serial,x,y,unit)
    # Default unit properties: no inherited invincibility, links or resources.
    r[16:20]=bytes((owner,100,100,100));return bytes(r)

def apply(chk,mission,difficulty):
    raw=geo._records(chk);before=chk.getsection('UNIT');info=list(map(geo._info,raw))
    original=info[:difficulty['original_unit_records_preserved']]
    hostile=set(difficulty['hostile_owners'])-set(scripted_openings.excluded_factions(mission))
    result=dict(revision=REVISION,mission_id=mission['mission_id'],base_unit_count=len(raw),
        before_unit_sha256=sha(before),bases=[],added=[],skipped_reason=None,
        original_units_preserved=True,registered_as_wave=False,live_gameplay_verified=False)
    if mission['no_production']:
        result['skipped_reason']='fixed_army_or_infiltration'
    else:
        placement=mission_balance.Placement(chk);grid=mining.load_buildable_grid(chk)
        friendly=[p for p in original if p[3]<8 and p[3] not in hostile and p[2]!=214]
        resources=[p for p in info if p[2] in {176,177,178,188,110,149,157}]
        reserved=[p for o in difficulty['wave_origins'] for p in o['cells']]
        addon_rects=addon_placement.reservations(info)
        serial=max(struct.unpack_from('<I',r)[0] for r in raw)+1
        groups=clusters(original,hostile)
        assigned={n:[] for n in range(len(groups))}
        for i,p in enumerate(original):
            if p[2] not in GROUND or p[3] not in hostile:continue
            near=[(min(dist(p,original[j]) for j in group),n) for n,group in enumerate(groups) if original[group[0]][3]==p[3]]
            if near and min(near)[0]<=512**2:assigned[min(near)[1]].append(i)
        def safe(x,y,u,owner,building=False):
            if not scripted_openings.additional_spawn_allowed(mission,x,y):return False
            if any(dist((x,y),p)<640**2 for p in friendly):return False
            if any(dist((x,y),p)<192**2 for p in resources):return False
            if any(dist((x,y),p)<96**2 for p in reserved):return False
            if not placement.safe(x,y,u):return False
            rect=placement.rect(x,y,u)
            if any(geo._overlap(rect,r) for r in addon_rects):return False
            if not building:return True
            if not mining.foundation_buildable(chk,(x,y),u,grid):return False
            # A full open ring gives ground units a route around the new tower.
            ring=(rect[0]-64,rect[1]-64,rect[2]+64,rect[3]+64)
            if not geo._walkable_rect(placement.walk,ring):return False
            for xx,yy,unit,_ in info:
                if unit>=106 and unit!=214 and geo._overlap(ring,placement.rect(xx,yy,unit)):return False
            # Stay conservatively inside existing power/creep sources. Never
            # manufacture an unsupported cannon or a remote Zerg outpost.
            if u==162 and not any(p[2]==156 and p[3]==owner and abs(x-p[0])<=160 and abs(y-p[1])<=64 for p in info):return False
            if u in (144,146) and not any(p[2] in {131,132,133,143,144,146} and p[3]==owner and dist((x,y),p)<=192**2 for p in info):return False
            return True
        def append(u,owner,x,y,base,role):
            nonlocal serial
            r=record(u,owner,x,y,serial);serial+=1;raw.append(r);info.append((x,y,u,owner));placement.add(x,y,u)
            result['added'].append(dict(unit=u,owner=owner,position=[x,y],base=base,role=role,record=r.hex()))
        for number,group in enumerate(groups):
            owner=original[group[0]][3];points=[original[i] for i in group]
            score=sum(4 if p[2] in HQ else 2 if p[2] in PRODUCTION else 1 for p in points)
            army=assigned[number];tier,wanted,towers=budget(score,len(army))
            # Reuse the original faction's grounded combat tech; never invent
            # a hero, caster, transport, ammunition unit or siege transformation.
            sources=army or [i for i,p in enumerate(original) if p[3]==owner and p[2] in GROUND]
            if not sources:continue
            base=dict(owner=owner,buildings=len(group),headquarters=sum(p[2] in HQ for p in points),
                production=sum(p[2] in PRODUCTION for p in points),score=score,tier=tier,
                original_defenders=len(army),requested_units=wanted,requested_towers=towers,
                unit_count=0,tower_count=0,center=[sum(p[0] for p in points)//len(points),sum(p[1] for p in points)//len(points)])
            result['bases'].append(base);base_index=len(result['bases'])-1
            race=chk.getsection('SIDE')[owner]
            types=(146,144) if race==0 else (162,) if race==2 else (124,)
            # Grid foundations distributed among original structures, not a
            # solid wall at the entrance. Stop when safe local spaces run out.
            candidates=set()
            for sx,sy,_,_ in points:
                for dy in range(-256,257,32):
                    for dx in range(-256,257,32):
                        if 128**2<=dx*dx+dy*dy<=256**2:candidates.add(((sx+dx)//32*32,(sy+dy)//32*32))
            candidates=sorted(candidates,key=lambda p:(min(dist(p,q) for q in points),p[1],p[0]))
            for x,y in candidates:
                if base['tower_count']>=towers:break
                u=types[base['tower_count']%len(types)]
                if safe(x,y,u,owner,True):append(u,owner,x,y,base_index,'tower');base['tower_count']+=1
            offsets=sorted((dx*dx+dy*dy,dy,dx) for dy in range(-256,257,32) for dx in range(-256,257,32))
            for n in range(wanted):
                u=original[sources[n%len(sources)]][2]
                anchor=points[n%len(points)]
                for _,dy,dx in offsets:
                    x,y=anchor[0]+dx,anchor[1]+dy
                    if safe(x,y,u,owner):append(u,owner,x,y,base_index,'defender');base['unit_count']+=1;break
            base['space_limited']=base['unit_count']<wanted or base['tower_count']<towers
        if not result['bases']:result['skipped_reason']='no_eligible_enemy_base'
    chk.setsection('UNIT',b''.join(raw));result['after_unit_sha256']=sha(chk.getsection('UNIT'))
    result['added_units']=sum(x['role']=='defender' for x in result['added'])
    result['added_towers']=sum(x['role']=='tower' for x in result['added'])
    return result

def undo(chk,report):
    raw=geo._records(chk);assert sha(chk.getsection('UNIT'))==report['after_unit_sha256']
    assert [r.hex() for r in raw[report['base_unit_count']:]]==[x['record'] for x in report['added']]
    before=b''.join(raw[:report['base_unit_count']]);assert sha(before)==report['before_unit_sha256']
    chk.setsection('UNIT',before)

def generate_header(rows,root):
    lines=['#pragma once','namespace base_defense_data {','struct Post {unsigned mission,type,owner,x,y;};','inline constexpr Post posts[]={']
    for row in rows:
        for item in row['base_defenses']['added']:
            if item['role']=='defender':lines.append('{'+','.join(map(str,(row['mission_id'],item['unit'],item['owner'],*item['position'])))+'},')
    lines+=['};','}']
    path=Path(root)/'sc1/native_campaign/plugin/include/base_defenses.generated.h'
    path.write_text('\n'.join(lines)+'\n',encoding='utf8');return path
