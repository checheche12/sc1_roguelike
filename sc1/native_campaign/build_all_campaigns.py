"""Build every shipped base-game/Brood War campaign CHK without game access.

Original scenario sections and ending actions are preserved. Ending conditions
are latched before their cinematic, then the exact original ending runs after
native phase-three growth has been durably acknowledged. Ordinary switches carry
the handshake; ordinary death counters remain diagnostic mirrors only.
"""
from __future__ import annotations
from collections import deque
from datetime import datetime,timezone
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SC1=ROOT.parent
sys.path.insert(0,str(ROOT))
from build_plain_chk import CHK,strings,digest,make_plain_chk
import mineral_layout
import resource_layout
import ladder_resource_layout
import main_base_gas
import addon_placement
import mining_layout_audit
import resource_depot_placement
SOURCE_ROOT=SC1/'campaign_sources/raw'
OUT=ROOT/'build/all_campaigns'
RECEIPT=ROOT/'all_campaign_maps_evidence.json'
MISSION_JSON=SC1/'campaign/missions.json'
HEADER=ROOT/'plugin/include/campaign_config.generated.h'
WAVE_HEADER=ROOT/'plugin/include/campaign_waves.generated.h'
COUNTERS={'route':223,'middle':224,'growth_ready':225,'goal':226,'ack':227}
# Zero-based engine switch IDs, audited unused across all 63 original assets.
SWITCHES={'goal':240,'middle':241,'growth_ready':242,'ack':243,'route_base':244,'route_count':6,'enemy_base_seen':250}
TILESETS=('badlands','platform','install','ashworld','jungle','desert','ice','twilight')
RACES={'terran':1,'zerg':0,'protoss':2}
BASE_UNITS={
 'terran':(0,1,2,3,5,7,8,9,11,12,13,14,30,32,106,107,108,109,110,111,112,113,114,115,116,117,118,120,122,123,124,125),
 'zerg':(35,36,37,38,39,40,41,42,43,44,45,46,47,50,59,131,132,133,134,135,136,137,138,139,140,141,142,143,144,146,149),
 'protoss':(64,65,66,67,68,69,70,71,72,73,83,84,85,154,155,156,157,159,160,162,163,164,165,166,167,169,170,171,172),
}
BW_UNITS={'terran':(34,58),'zerg':(62,97,103),'protoss':(60,61,63)}
COMBAT=set((0,1,2,3,5,8,9,12,30,32,34,37,38,39,43,44,45,46,47,50,58,60,61,62,63,65,66,67,68,70,71,72,73,83,84,85,103))
GROUND_COMBAT=set((0,1,2,3,5,30,32,34,37,38,39,46,50,61,63,65,66,67,68,83,103))
UPGRADES={'terran':{i:3 if i in (0,1,2,7,8,9) else 1 for i in (0,1,2,7,8,9,16,17,19,20,21,22,23,51,54)},
 'zerg':{i:3 if i in (3,4,10,11,12) else 1 for i in (3,4,10,11,12,24,25,26,27,28,29,30,31,52,53)},
 'protoss':{i:3 if i in (5,6,13,14,15) else 1 for i in (5,6,13,14,15,33,34,35,36,37,38,39,40,41,42,43,44,47,49)}}
TECH={'terran':(0,1,2,3,4,5,6,7,8,9,10,24,30,34),'zerg':(11,12,13,14,15,16,17,18,31,32),'protoss':(19,20,21,22,23,25,27,28,29)}
INNATE={4,6,18,23,28,29,34}
COMBAT_UPGRADES={0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15}
# Reviewed terminal defense objectives only. A countdown alone is not enough:
# Z04/P02 lead into assault, Z09 into crystal delivery, and BW T07 is an escape.
# Owners are zero-based, and refer only to the original hostile base factions.
TIMED_SURVIVAL={
 103:{'name':'Desperate Alliance','ending_trigger':6,'timer_trigger':0,'timer_action':2,'seconds':1800,'enemy_owners':(4,),'active_switch':0,'failure_switch':None,'objectives':((0,1,False),)},
 408:{'name':'Countdown','ending_trigger':11,'timer_trigger':10,'timer_action':13,'seconds':900,'enemy_owners':(0,4,5),'active_switch':2,'failure_switch':4,'objectives':((0,0,False),(10,12,True))},
}

def dump(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def units(chk):
 raw=chk.getsection('UNIT');assert len(raw)%36==0
 return [raw[i:i+36] for i in range(0,len(raw),36)]
def unit_info(r):return (*struct.unpack_from('<HHH',r,4),r[16])
def triggers(chk):
 raw=chk.getsection('TRIG');assert len(raw)%2400==0
 return [raw[i:i+2400] for i in range(0,len(raw),2400)]
def conditions(t):return [(i,t[i*20:(i+1)*20]) for i in range(16) if t[i*20+15] and not t[i*20+17]&2]
def actions(t):return [(i,t[320+i*32:352+i*32]) for i in range(64) if t[320+i*32+26] and not t[320+i*32+28]&2]
def cf(c):
 loc,player,count,unit,comparison,kind,*_=struct.unpack('<IIIHBBBBH',c)
 return {'location':loc,'player':player,'amount':count,'unit':unit,'comparison':comparison,'type':kind}
def cond(kind,player=0,count=0,unit=0,comparison=0,location=0):return struct.pack('<IIIHBBBBH',location,player,count,unit,comparison,kind,0,0,0)
def death(unit,count=1,comparison=0):return cond(15,11,count,unit,comparison)
def switch_condition(index,is_set=True):
 c=bytearray(cond(11,comparison=2 if is_set else 3));c[16]=index;return bytes(c)
def setswitch(index,is_set=True):return struct.pack('<IIIIIIHBBBBH',0,0,0,0,0,index,0,13,4 if is_set else 5,4,0,0)
def setdeath(unit,count=1):return struct.pack('<IIIIIIHBBBBH',0,0,0,0,11,count,unit,45,7,20,0,0)
def new_trigger(cs,acts,owners):
 assert len(cs)<=16 and len(acts)<=64
 t=bytearray(2400)
 for i,c in enumerate(cs):t[i*20:(i+1)*20]=c
 for i,a in enumerate(acts):t[320+i*32:352+i*32]=a
 t[2372:2400]=owners
 return bytes(t)
def owner_bytes(owner):
 b=bytearray(28);b[owner]=1;return bytes(b)
def players_for(chk,encoded,owner):
 if encoded<12:return {encoded}
 if encoded==13:return {owner}
 if encoded in (17,26):return set(range(8))
 if 18<=encoded<=21:return {i for i,v in enumerate(chk.getsection('FORC')[:8]) if v==encoded-18}
 if encoded==14:return {i for i,v in enumerate(chk.getsection('OWNR')[:8]) if v==5 and i!=owner}
 if encoded==15:return {owner}|{i for i,v in enumerate(chk.getsection('OWNR')[:8]) if v==3}
 return set()
def trigger_has_player(chk,t,owner):
 return any(v and owner in players_for(chk,i,owner) for i,v in enumerate(t[2372:2399]))
def count_matches(rows,owners,unit):
 return sum(p in owners and (u==unit or unit==229 and u<228 and u!=214 or unit==230 and u<106 or unit==231 and 106<=u<176) for x,y,u,p in map(unit_info,rows))
def append_marker(data,marker):
 ss=strings(data);assert marker not in ss
 n=len(ss);offsets=struct.unpack_from('<'+'H'*n,data,2)
 assert len(data)+2+len(marker)+1<65536
 result=struct.pack('<H',n+1)+struct.pack('<'+'H'*(n+1),*[i+2 for i in offsets],len(data)+2)+data[2+2*n:]+marker+b'\0'
 assert strings(result)==ss+[marker]
 return result

def reserved_switch_ids():
 return set(range(SWITCHES['goal'],SWITCHES['route_base']+SWITCHES['route_count']))|{SWITCHES['enemy_base_seen']}

def roster_specs():
 rows=[]
 for campaign,folder,race,n,start in ((1,'Terran','terran',10,0),(2,'Zerg','zerg',10,10),(3,'Protoss','protoss',10,20),(4,'EXPProtoss','protoss',8,30),(5,'EXPTerran','terran',8,38),(6,'EXPZerg','zerg',10,46)):
  prefix=race.title()
  for ordinal in range(1,n+1):
   number=(1,2,3,4,5,6,8,9,11,12)[ordinal-1] if campaign==1 else ordinal
   suffix='a' if (campaign,ordinal) in ((5,5),(6,4)) else ''
   rows.append({'mission_id':campaign*100+ordinal,'campaign_id':campaign,'race':race,'ordinal':ordinal,'completion_bit':start+ordinal-1,'required_mask':sum(1<<(start+i) for i in range(ordinal-1)),
     'final':ordinal==n,'next_mission_ids':[] if ordinal==n else [campaign*100+ordinal+1], 'asset_path':f'campaign/{folder}/{prefix}{number:02d}{suffix}/staredit/scenario.chk','shared_reward_mission_id':campaign*100+ordinal,'secret':False})
   if suffix:
    for j,ch in enumerate('b' if campaign==5 else 'bcdef'):
     r=dict(rows[-1]);r.update(mission_id=515 if campaign==5 else 614+j,asset_path=f'campaign/{folder}/{prefix}{number:02d}{ch}/staredit/scenario.chk',variant=ch);rows.append(r)
  # Variants are alternative assets for one logical mission, not extra progression.
 rows.append({'mission_id':611,'campaign_id':7,'race':'protoss','ordinal':1,'completion_bit':56,'required_mask':0,'final':True,'next_mission_ids':[610],'asset_path':'campaign/EXPZerg/Bonus/staredit/scenario.chk','shared_reward_mission_id':611,'secret':True})
 return sorted(rows,key=lambda r:(r['campaign_id'],r['ordinal'],r['mission_id']))

def metadata(spec,chk,source):
 row=dict(spec);own=chk.getsection('OWNR');owner=[i for i,v in enumerate(own) if v==6]
 assert len(owner)==1,(spec,owner)
 owner=owner[0];rows=units(chk);friendly={owner}|{i for i,v in enumerate(own) if v==3}
 available={u for x,y,u,p in map(unit_info,rows) if p in friendly and u!=214}
 starting={u for x,y,u,p in map(unit_info,rows) if p==owner and u!=214}
 for t in triggers(chk):
  for _,a in actions(t):
   if a[26] in (11,44):
    dest=struct.unpack_from('<I',a,16)[0]
    # CurrentPlayer means this trigger's players, not always the human.
    if owner in players_for(chk,dest,owner) and (dest!=13 or trigger_has_player(chk,t,owner)):
     available.add(struct.unpack_from('<H',a,24)[0])
 no_production=not bool(available&{7,41,64})
 # These missions transfer neutral bases through original campaign AI scripts.
 if spec['mission_id'] in (105,301,503,601,605,606):no_production=False
 version=struct.unpack('<H',chk.getsection('VER '))[0]
 marker=f'SC1_NATIVE_M{spec["mission_id"]}_V3_SW1_R469'
 objectives=[];ss=strings(chk.getsection('STR '))
 for t in triggers(chk):
  for _,a in actions(t):
   if a[26]==12:
    ix=struct.unpack_from('<I',a,4)[0]
    if 0<ix<=len(ss):objectives.append(ss[ix-1].decode('utf-8','replace'))
 row.update(player_slot=owner,owner=owner,chk_version=version,campaign_index=2 if spec['mission_id']==101 else 0,
  width=struct.unpack_from('<H',chk.getsection('DIM '))[0],height=struct.unpack_from('<H',chk.getsection('DIM '),2)[0],
  no_production=no_production,starting_unit_ids=sorted(starting),available_unit_ids=sorted(available),fingerprint=marker,source=str(source),source_sha256=digest(source.read_bytes()),
  expansion=spec['campaign_id']>=4,label=f'{"Brood War " if spec["campaign_id"]>=4 else ""}{spec["race"].title()} {spec["ordinal"]}'+(' Secret' if spec['secret'] else ''),original_objectives=objectives,
  campaign_index_authentication='T01 live value; other missions use unique marker plus original dimensions, human owner, race and CHK version')
 # All regular units are producible on maps with economy; preserve mission heroes.
 if not no_production:row['available_unit_ids']=sorted(available|set(BASE_UNITS[row['race']])|set(BW_UNITS[row['race']]))
 return row

def audit_counters(chk):
 operations=[];collisions=[]
 for ti,t in enumerate(triggers(chk)):
  for ci,c in conditions(t):
   if c[15]==15:
    f=cf(c);operations.append({'trigger':ti,'condition':ci,**f})
    if f['unit'] in COUNTERS.values():collisions.append(operations[-1])
  for ai,a in actions(t):
   if a[26]==45:
    f={'trigger':ti,'action':ai,'unit':struct.unpack_from('<H',a,24)[0],'player':struct.unpack_from('<I',a,16)[0]};operations.append(f)
    if f['unit'] in COUNTERS.values():collisions.append(f)
 physical=[unit_info(r) for r in units(chk) if unit_info(r)[2] in COUNTERS.values()]
 assert not collisions and not physical,('Reserved ordinary counter collision',collisions,physical)
 return {'owner':11,'counters':COUNTERS,'original_death_operations':operations,'reserved_pair_collisions':[],'physical_reserved_types':[],'eud_memory_addressing':False}

def audit_switches(chk):
 operations=[];used=set()
 reserved=reserved_switch_ids()
 for ti,t in enumerate(triggers(chk)):
  for ci,c in conditions(t):
   if c[15]==11:
    used.add(c[16]);operations.append({'trigger':ti,'condition':ci,'switch':c[16]})
  for ai,a in actions(t):
   if a[26]==13:
    index=struct.unpack_from('<I',a,20)[0];used.add(index);operations.append({'trigger':ti,'action':ai,'switch':index})
 assert not (reserved&used),('Reserved campaign switch collision',sorted(reserved&used))
 return {'zero_based':True,'handshake':SWITCHES,'reserved_ids':sorted(reserved),'original_used_ids':sorted(used),'original_switch_operations':operations,'collisions':[]}

def timed_survival_plan(chk,row):
 """Fail-closed review of the two true terminal countdown defenses.

 Ordinary Command Buildings tests include airborne structures and rebuilt bases.
 The reviewed factions contain only destructible standard Zerg buildings; special
 campaign objects and the neutral temple therefore cannot block this condition.
 """
 config=TIMED_SURVIVAL.get(row['mission_id'])
 if config is None:return None
 ts=triggers(chk);owner=row['owner'];enemy=set(config['enemy_owners']);own=chk.getsection('OWNR')
 assert enemy=={i for i,v in enumerate(own[:8]) if v==5},('Survival hostile owners changed',row['mission_id'])
 timer=ts[config['timer_trigger']][320+config['timer_action']*32:352+config['timer_action']*32]
 assert (timer[26],timer[27],struct.unpack_from('<I',timer,12)[0])==(14,7,config['seconds'])
 ending=ts[config['ending_trigger']];source_cs=[c for _,c in conditions(ending)]
 assert any(a[26]==1 for _,a in actions(ending))
 assert cond(1,count=0,comparison=1) in source_cs
 assert switch_condition(config['active_switch']) in source_cs
 rows=units(chk);counts={};types={}
 standard_buildings=set(BASE_UNITS['zerg'])&set(range(106,176))
 for p in sorted(enemy):
  buildings=[r for r in rows if unit_info(r)[3]==p and 106<=unit_info(r)[2]<176]
  assert buildings and any(unit_info(r)[2] in (131,132,133) for r in buildings),('No real original enemy base',row['mission_id'],p)
  assert all(unit_info(r)[2] in standard_buildings and not(struct.unpack_from('<H',r,12)[0]&16 and struct.unpack_from('<H',r,26)[0]&16) for r in buildings),('Special/invincible hostile building needs review',row['mission_id'],p)
  counts[p]=len(buildings);types[p]=sorted({unit_info(r)[2] for r in buildings})
 # Fail closed if a future source adds invincibility or transfers involving the
 # target buildings, or changes a target faction into an ally during gameplay.
 for ti,t in enumerate(ts):
  if ti==config['ending_trigger']:continue
  for _,a in actions(t):
   kind=a[26];p=struct.unpack_from('<I',a,16)[0];u=struct.unpack_from('<H',a,24)[0]
   involved=players_for(chk,p,owner)&enemy
   if kind==43 and involved and a[27]!=5:assert u<106 or u>=176 and u not in (229,231),('Enemy building invincibility needs review',row['mission_id'],ti)
   if kind==48:assert not involved and struct.unpack_from('<I',a,20)[0] not in enemy,('Enemy ownership transfer needs review',row['mission_id'],ti)
   if kind==57 and u!=0:
    source_owners={i for i,v in enumerate(t[2372:2400]) if v and i<12}
    if owner in players_for(chk,p,owner) and source_owners&enemy:
     # Countdown allies its defeated enemies only after its success cinematic
     # begins (Switch9); that action cannot invalidate the pre-victory targets.
     assert row['mission_id']==408 and switch_condition(9) in [c for _,c in conditions(t)]
    else:assert not(owner in source_owners and involved),('Enemy alliance change needs review',row['mission_id'],ti)
 cs=[c for c in source_cs if c[15]!=1]
 cs.extend([cond(12,count=1),cond(2,owner,1,231)])
 if row['mission_id']==408:
  # The original delivery removes the heroes, so use original hero death
  # counters, not a requirement that removed heroes still exist on the map.
  cs.extend([cond(15,owner,0,75,comparison=1),cond(15,owner,0,88,comparison=1),cond(2,17,1,175),switch_condition(9,False)])
 cs.extend([switch_condition(SWITCHES['enemy_base_seen'])]+[cond(2,p,0,231,comparison=1) for p in sorted(enemy)])
 assert len(cs)<16
 return {'config':config,'conditions':cs,'initial_enemy_building_counts':counts,'initial_enemy_building_types':types}

def append_survival_objectives(chk,row,plan,result):
 updates=[];ts=triggers(chk);config=plan['config']
 for source_ti,source_ai,active in config['objectives']:
  source=ts[source_ti][320+source_ai*32:352+source_ai*32];assert source[26]==12
  index=struct.unpack_from('<I',source,4)[0];ss=strings(chk.getsection('STR '));assert 0<index<=len(ss)
  extra='\n- 또는 적 기지의 모든 건물 파괴' if row['mission_id']==103 or active else '\n- 사원 활성화 후 적 기지의 모든 건물 파괴로 조기 승리 가능'
  text=ss[index-1]+extra.encode('utf-8');chk.setsection('STR ',append_marker(chk.getsection('STR '),text))
  action=bytearray(source);struct.pack_into('<I',action,4,len(ss)+1)
  cs=[cond(12,count=1)]
  if row['mission_id']==408:cs.append(switch_condition(config['active_switch'],active))
  else:cs.append(switch_condition(config['active_switch']))
  updates.append({'trigger_index':len(result),'source_trigger':source_ti,'source_action':source_ai,'string_id':len(ss)+1,'conditions':[cf(c) for c in cs],'text_utf8':text.decode('utf-8')})
  result.append(new_trigger(cs,[bytes(action)],owner_bytes(row['owner'])))
 return updates

def milestone(chk,row):
 ts=triggers(chk);owner=row['owner'];unit_rows=units(chk)
 # Existing scripted objective transitions are preferable to generic timers.
 scripted=[]
 for ti,t in enumerate(ts):
  aa=actions(t);cs=conditions(t)
  if any(a[26] in (1,2) for _,a in aa) or not trigger_has_player(chk,t,owner):continue
  if any(a[26] in (7,12,13,48) for _,a in aa) and any(c[15] in (2,3,11,15) for _,c in cs):
   if any(c[15]==3 and cf(c)['player'] not in (17,26) and cf(c)['comparison'] in (0,10) and cf(c)['amount']>0 and owner in players_for(chk,cf(c)['player'],owner) for _,c in cs):
    scripted.append((ti,t,cs))
 if scripted:
  ti,t,cs=scripted[len(scripted)//2]
  return [c for _,c in cs],owner_bytes(owner),{'kind':'original_scripted_movement_checkpoint','source_trigger':ti,'conditions':[cf(c) for _,c in cs]}
 # Half of an original timed survival objective is itself genuine progress.
 timer=max((struct.unpack_from('<I',a,12)[0] for t in ts for _,a in actions(t) if a[26]==14 and a[27]==7),default=0)
 if timer and any(c[15]==1 for t in ts for _,c in conditions(t)):
  cs=[cond(1,count=max(1,timer//2),comparison=1),cond(12,count=1)]
  timer_sources=[{'trigger':ti,'action':ai,'conditions':[cf(c) for _,c in conditions(t)]} for ti,t in enumerate(ts) for ai,a in actions(t) if a[26]==14 and a[27]==7 and struct.unpack_from('<I',a,12)[0]==timer]
  timing={'source_countdown_starts':timer_sources}
  if row['mission_id']==209:
   # Zerg09 has no initial timer. Original trigger3 starts mining, sets600s,
   # then sets Switch0; its completion event also requires that same switch.
   # Never interpret the initial zero countdown as five minutes of progress.
   writes=[(ti,ai,a[27]) for ti,t in enumerate(ts) for ai,a in actions(t) if a[26]==13 and struct.unpack_from('<I',a,20)[0]==0]
   assert writes==[(3,15,4)] and timer_sources[0]['trigger']==3 and timer_sources[0]['action']==9
   cs.append(switch_condition(0))
   timing['countdown_started_guard']={'original_switch':0,'required_state':'set','source_trigger':3,'source_action':15,'timer_action':9,'original_switch_never_cleared':True}
  else:
   # All other selected countdowns are initialized by their original startup
   # event; fail the build if a source change makes that initialization gated.
   assert timer_sources and all(c['type']==22 or c['type'] in (1,12) and c['comparison']==0 and c['amount']==0 for item in timer_sources for c in item['conditions'])
   timing['countdown_started_at_initialization']=True
  return cs,owner_bytes(owner),{'kind':'half_original_countdown','original_countdown_seconds':timer,'conditions':[cf(c) for c in cs],**timing}
 # Build-up missions: reach an explicit partial production objective.
 for ti,t in enumerate(ts):
  if not any(a[26]==1 for _,a in actions(t)):continue
  for ci,c in conditions(t):
   f=cf(c)
   if f['type']==2 and owner in players_for(chk,f['player'],owner) and f['comparison']==0 and f['amount']>1:
    r=bytearray(c);struct.pack_into('<I',r,8,max(1,f['amount']//2));cs=[bytes(r)]
    return cs,owner_bytes(owner),{'kind':'half_original_production_goal','source_trigger':ti,'source_condition':ci,'conditions':[cf(c) for c in cs]}
 # Base-clearing missions: remove half of the actual objective's initial force.
 for ti,t in enumerate(ts):
  if not any(a[26]==1 for _,a in actions(t)):continue
  for ci,c in conditions(t):
   f=cf(c);owners=players_for(chk,f['player'],owner)
   if f['type']==2 and f['comparison']==1 and f['amount']==0 and owner not in owners:
    n=count_matches(unit_rows,owners,f['unit'])
    if n>=2:
     r=bytearray(c);struct.pack_into('<I',r,8,n//2);cs=[bytes(r)]
     return cs,owner_bytes(owner),{'kind':'half_original_elimination_goal','source_trigger':ti,'source_condition':ci,'initial_target_count':n,'conditions':[cf(c) for c in cs]}
 # Single-target/escort maps without intermediate script: combat against the
 # original hostile force is measurable progress; final goal catches up if bypassed.
 hostile=[r for r in unit_rows if chk.getsection('OWNR')[unit_info(r)[3]]==5 and unit_info(r)[2] in COMBAT]
 threshold=max(1,min(30,len(hostile)//3))
 cs=[cond(5,owner,threshold,229)]
 return cs,owner_bytes(owner),{'kind':'original_hostile_force_combat_progress','original_hostile_combatants':len(hostile),'kills_required':threshold,'conditions':[cf(c) for c in cs],'goal_catches_up_if_bypassed':True}

def patch_progression(chk,row):
 original=triggers(chk);result=[];receipt=[];original_indices=[]
 survival=timed_survival_plan(chk,row)
 middle_cs,owners,mid=milestone(chk,row)
 # A scripted checkpoint can consume its own switch, move units, or start a
 # blocking cinematic. Capture its condition before that exact source event.
 middle_source=mid.get('source_trigger') if mid['kind']=='original_scripted_movement_checkpoint' else None
 middle_index=None
 for ti,t in enumerate(original):
  if ti==middle_source:
   middle_index=len(result);result.append(new_trigger(middle_cs,[setswitch(SWITCHES['middle']),setdeath(224)],owners))
  victory=[ai for ai,a in actions(t) if a[26]==1]
  if not victory:original_indices.append(len(result));result.append(t);continue
  assert trigger_has_player(chk,t,row['owner']),('Non-human original victory',row['mission_id'],ti)
  route=len(receipt)+1;cs=[c for _,c in conditions(t)]
  assert len(cs)<16,('No condition slot for first-route latch',row['mission_id'],ti)
  # Evaluate the goal in its original relative position: original initialization
  # and scripted target creation must run before a zero-target victory check.
  latch_index=len(result)
  assert route<=SWITCHES['route_count'],('Too many ending routes',row['mission_id'])
  route_switch=SWITCHES['route_base']+route-1
  result.append(new_trigger(cs+[switch_condition(SWITCHES['goal'],False)],[setswitch(route_switch),setswitch(SWITCHES['goal']),setdeath(223,route),setdeath(226)],t[2372:2400]))
  patched=bytearray(t);patched[:320]=bytes(320)
  for i,c in enumerate((switch_condition(route_switch),switch_condition(SWITCHES['growth_ready']),switch_condition(SWITCHES['ack']))):patched[i*20:(i+1)*20]=c
  assert patched[320:]==t[320:]
  original_indices.append(len(result));result.append(bytes(patched))
  receipt.append({'source_trigger':ti,'route':route,'route_switch':route_switch,'goal_trigger_index':latch_index,'ending_trigger_index':len(result)-1,'victory_action_indices':victory,'original_conditions_hex':t[:320].hex(),'original_actions_sha256':digest(t[320:2368]),'owners_hex':t[2372:2400].hex(),'cinematic_and_transition_actions_byte_identical':True})
 assert receipt,('No original Victory',row['mission_id'])
 if middle_index is None:
  middle_index=len(result);result.append(new_trigger(middle_cs,[setswitch(SWITCHES['middle']),setdeath(224)],owners))
 alternate=None
 if survival is not None:
  config=survival['config'];ending_route=next(r for r in receipt if r['source_trigger']==config['ending_trigger'])
  # Observe every actual enemy base before accepting a zero-building result.
  # This event is independent of the defense's activation, allowing a player
  # to clear Countdown's bases before delivering both crystals to the temple.
  seen_cs=[cond(12,count=1)]+[cond(2,p,1,231) for p in config['enemy_owners']]
  seen_index=len(result);result.append(new_trigger(seen_cs,[setswitch(SWITCHES['enemy_base_seen'])],owner_bytes(row['owner'])))
  latch_index=len(result)
  result.append(new_trigger(survival['conditions']+[switch_condition(SWITCHES['goal'],False)],[setswitch(ending_route['route_switch']),setswitch(SWITCHES['goal']),setdeath(223,ending_route['route']),setdeath(226)],owner_bytes(row['owner'])))
  objective_updates=append_survival_objectives(chk,row,survival,result)
  alternate={'kind':'reviewed_timed_survival_all_hostile_buildings','name':config['name'],'goal_trigger_index':latch_index,'enemy_seen_trigger_index':seen_index,'enemy_seen_switch':SWITCHES['enemy_base_seen'],'enemy_owners':list(config['enemy_owners']),'initial_enemy_building_counts':survival['initial_enemy_building_counts'],'initial_enemy_building_types':survival['initial_enemy_building_types'],'conditions':[cf(c) for c in survival['conditions']],'conditions_hex':[c.hex() for c in survival['conditions']],'original_ending_trigger':config['ending_trigger'],'ending_trigger_index':ending_route['ending_trigger_index'],'route':ending_route['route'],'route_switch':ending_route['route_switch'],'original_timer_seconds':config['seconds'],'original_timer_victory_preserved':True,'timer_expiration_required':False,'base_clear_semantics':'Command Buildings equals zero for every reviewed original hostile base owner, anywhere; all standard structures including defense, supply, technology, resource buildings, add-ons and lifted or rebuilt buildings count. Enemy mobile units do not block. Neutral, rescuable, player and decorative campaign-object owners are excluded.','startup_guard':'Each reviewed hostile owner must first be observed with at least one building at elapsed time >=1s; original countdown activation switch and player survival guards are required.','objective_updates':objective_updates,'same_original_success_actions_after_growth_and_ack':True}
 chk.setsection('TRIG',b''.join(result))
 return {'routes':receipt,'goal_latches_inserted_before_original_endings':len(receipt),'middle_trigger_index':middle_index,'middle':mid,'middle_evaluated_before_source_actions':middle_source is not None,'original_trigger_indices':original_indices,'preserves_all_original_actions':True,'preserves_all_original_trigger_owners':True,'original_initialization_and_goal_evaluation_order_preserved':True,'defeat_triggers_byte_identical':True,'victory_requires':'latched original route switch + phase3 readiness switch242 + durable save ACK switch243','handshake':{'kind':'ordinary_switches_v1',**SWITCHES},'death_counters_are_diagnostic_mirrors_only':True,'cinematic_begins_after_save_ack':True,'alternate_survival_victory':alternate}

def unlock(chk,row):
 owner=row['owner'];race=row['race'];selected=set(BASE_UNITS[race])|set(BW_UNITS[race])
 puni=bytearray(chk.getsection('PUNI'))
 for unit in selected:puni[owner*228+unit]=1;puni[(13+owner)*228+unit]=0
 chk.setsection('PUNI',puni)
 changed=[]
 for tag,n in (('UPGR',46),('PUPx',61)):
  if tag.encode() not in chk.sections:continue
  data=bytearray(chk.getsection(tag));assert len(data)==38*n
  for i,maxlevel in UPGRADES[race].items():
   if i>=n:continue
   default=bool(data[(26+owner)*n+i]);existing_level=data[(25 if default else 12+owner)*n+i];existing_max=data[(24 if default else owner)*n+i]
   level=max(existing_level,6 if row['no_production'] and i in COMBAT_UPGRADES else 0)
   data[owner*n+i]=max(maxlevel,level,existing_max);data[(12+owner)*n+i]=level;data[(26+owner)*n+i]=0
  # Rescue heroes/units may be another race; give their attack/armor the same 6/6.
  if row['no_production']:
   for i in COMBAT_UPGRADES:
    default=bool(data[(26+owner)*n+i]);level=max(6,data[(25 if default else 12+owner)*n+i]);maximum=data[(24 if default else owner)*n+i]
    data[owner*n+i]=max(level,maximum);data[(12+owner)*n+i]=level;data[(26+owner)*n+i]=0
  chk.setsection(tag,data);changed.append(tag)
 for tag,n in (('PTEC',24),('PTEx',44)):
  if tag.encode() not in chk.sections:continue
  data=bytearray(chk.getsection(tag));assert len(data)==38*n
  for i in TECH[race]:
   if i>=n:continue
   default=bool(data[(26+owner)*n+i]);existing=data[(25 if default else 12+owner)*n+i]
   data[owner*n+i]=1;data[(12+owner)*n+i]=max(existing,int(i in INNATE or row['no_production']));data[(26+owner)*n+i]=0
  chk.setsection(tag,data);changed.append(tag)
 return {'unit_ids':sorted(selected),'setting_sections':changed,'no_production_combat_upgrade_level':6 if row['no_production'] else 0,'normal_research_costs_and_prerequisites':not row['no_production'],'original_owner_side_force_preserved':True,'brood_war_regular_units_permitted_in_all_puni':True,'legacy_missing_bw_research_fields_require_native_runtime':not row['expansion'],'actual_bw_unit_production_in_original_mode_verified':False}


def generate_metadata():
 rows=[]
 for spec in roster_specs():
  source=SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path']
  row=metadata(spec,CHK(source.read_bytes()),source);rows.append(row)
 dump(MISSION_JSON,{'schema_version':2,'scope':'30 original +33 Brood War scenario assets; 57 logical missions','missions':rows,'excluded_assets':['Terran/Terran07 (deleted mission)','Terran/Terran10 (deleted mission)','all three tutorials'],'variant_rewards_shared':True,'bonus_campaign_id':7})
 h=['// Generated from original CHK metadata; do not hand edit.','#pragma once','#include <cstdint>','namespace sc1_native { namespace campaign_config {','struct Mission { std::uint32_t mission_id,campaign_index,owner,race,width,height; const char* marker; bool no_production; std::uint32_t chk_version; };','inline constexpr std::uint32_t kGoalSwitch=240,kMiddleSwitch=241,kReadySwitch=242,kAckSwitch=243,kRouteSwitchBase=244,kRouteSwitchCount=6,kEnemyBaseSeenSwitch=250;', 'inline constexpr Mission kMissions[] = {']
 for row in rows:h.append('    {'+', '.join(map(str,(row['mission_id'],row['campaign_index'],row['owner'],RACES[row['race']],row['width'],row['height'])))+', "'+row['fingerprint']+'", '+str(row['no_production']).lower()+', '+str(row['chk_version'])+'},')
 h+=['};','inline constexpr bool final_mission(std::uint32_t id) noexcept {return '+' || '.join('id=='+str(r['mission_id']) for r in rows if r['final'])+';}','} } // namespace sc1_native::campaign_config']
 HEADER.write_text('\n'.join(h)+'\n',encoding='utf-8')
 return rows


def load_terrain(chk):
 width,height=struct.unpack('<HH',chk.getsection('DIM '));era=struct.unpack('<H',chk.getsection('ERA '))[0]&7
 name=TILESETS[era];cv5=(SOURCE_ROOT/'TileSet'/f'{name}.cv5').read_bytes();vf4=(SOURCE_ROOT/'TileSet'/f'{name}.vf4').read_bytes()
 tiles=struct.unpack('<'+'H'*(width*height),chk.getsection('MTXM'));w,h=width*4,height*4
 raw=[bytearray(w) for _ in range(h)]
 cache={}
 for y in range(height):
  for x in range(width):
   tile=tiles[y*width+x]
   if tile not in cache:
    mega=struct.unpack_from('<H',cv5,(tile>>4)*52+20+(tile&15)*2)[0]
    cache[tile]=tuple(int(bool(f&1)) for f in struct.unpack_from('<16H',vf4,mega*32))
   flags=cache[tile]
   for sy in range(4):raw[y*4+sy][x*4:x*4+4]=bytes(flags[sy*4:sy*4+4])
 clear=[bytearray(w) for _ in range(h)]
 for y in range(1,h-1):
  a,b,c=raw[y-1:y+2];out=clear[y]
  for x in range(1,w-1):out[x]=int(a[x-1] and a[x] and a[x+1] and b[x-1] and b[x] and b[x+1] and c[x-1] and c[x] and c[x+1])
 return clear,{'tileset':name,'cv5_sha256':digest(cv5),'vf4_sha256':digest(vf4),'center_terrain_clearance_pixels':24,'native_pathfinder_verified':False}

def nearest(clear,xy):
 x,y=xy[0]//8,xy[1]//8;w,h=len(clear[0]),len(clear)
 for radius in (8,24,64):
  options=[((xx-x)**2+(yy-y)**2,xx,yy) for yy in range(max(1,y-radius),min(h-1,y+radius+1)) for xx in range(max(1,x-radius),min(w-1,x+radius+1)) if clear[yy][xx]]
  if options:return min(options)[1:]
 raise ValueError(('No walkable target',xy))

def connected_cells(clear,target):
 w,h=len(clear[0]),len(clear);start=nearest(clear,target);seen=[bytearray(w) for _ in range(h)];seen[start[1]][start[0]]=1;q=deque([start])
 while q:
  x,y=q.popleft()
  for xx,yy in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
   if 0<yy<h-1 and 0<xx<w-1 and clear[yy][xx] and not seen[yy][xx]:seen[yy][xx]=1;q.append((xx,yy))
 return seen,[start[0]*8+4,start[1]*8+4]

def strengthen(chk,row):
 records=units(chk);info=list(map(unit_info,records));own=chk.getsection('OWNR');force=chk.getsection('FORC');owner=row['owner'];friendly={owner}|{i for i,v in enumerate(own) if v==3}
 # An owner that is ever explicitly allied to the human is not a reinforcement
 # source: source scripts may change allegiance as part of the original mission.
 allied=set()
 for t in triggers(chk):
  for _,a in actions(t):
   if a[26]==57 and struct.unpack_from('<H',a,24)[0] in (0,2) and trigger_has_player(chk,t,owner):allied|=players_for(chk,struct.unpack_from('<I',a,16)[0],owner)
 friendly|=allied
 if force[16+force[owner]]&1:friendly|={i for i in range(8) if force[i]==force[owner]}
 hostile={i for i,v in enumerate(own[:8]) if v==5 and i not in friendly}
 human=[r for r in info if r[3]==owner and r[2]!=214]
 bases=[r for r in human if r[2] in (106,131,132,133,154)]
 mobile=[r for r in human if r[2]<106]
 start=next((r[:2] for r in info if r[3]==owner and r[2]==214),None)
 candidates=bases or mobile or human
 if not candidates and start:candidates=[(*start,214,owner)]
 if not candidates:
  for t in triggers(chk):
   for _,a in actions(t):
    if a[26] in (11,44) and owner in players_for(chk,struct.unpack_from('<I',a,16)[0],owner):
     loc=struct.unpack_from('<I',a,0)[0]
     if 0<loc<=len(chk.getsection('MRGN'))//20:
      l,top,r,b=struct.unpack_from('<4I',chk.getsection('MRGN'),(loc-1)*20);candidates=[((l+r)//2,(top+b)//2,214,owner)];break
   if candidates:break
 assert candidates,('No player target',row['mission_id'])
 target=min(candidates,key=lambda r:(r[0]-(start or r)[0])**2+(r[1]-(start or r)[1])**2)[:2]
 clear,terrain=load_terrain(chk);connected,target=connected_cells(clear,target);w,h=len(clear[0])*8,len(clear)*8
 protected=[(x,y) for x,y,u,p in info if p in friendly and u!=214]+[tuple(target)]
 occupied=[(x,y,80 if 106<=u<176 else 40) for x,y,u,p in info if u!=214]
 def safe(x,y,ground=True,extra=()):
  if not(24<x<w-24 and 24<y<h-24):return False
  if ground and not clear[y//8][x//8]:return False
  if any((x-a)**2+(y-b)**2<512**2 for a,b in protected):return False
  if any((x-a)**2+(y-b)**2<r*r for a,b,r in occupied):return False
  if any((x-a)**2+(y-b)**2<40**2 for a,b in extra):return False
  return True
 next_serial=max(struct.unpack_from('<I',r)[0] for r in records)+1
 added=[];static=[]
 enemy_ground=[(i,r,unit_info(r)) for i,r in enumerate(records) if unit_info(r)[3] in hostile and unit_info(r)[2] in GROUND_COMBAT]
 cap=24 if row['no_production'] else 80
 for index,source,(sx,sy,unit,p) in enemy_ground[::2]:
  if len(added)>=cap:break
  choices=[]
  for y in range(max(28,sy-128)//16*16+4,min(h-24,sy+129),16):
   for x in range(max(28,sx-128)//16*16+4,min(w-24,sx+129),16):
    if safe(x,y):choices.append(((x-sx)**2+(y-sy)**2,y,x))
  if not choices:continue
  _,y,x=min(choices);r=bytearray(source);struct.pack_into('<IHH',r,0,next_serial,x,y);next_serial+=1
  added.append(bytes(r));occupied.append((x,y,40));static.append({'source_record':index,'unit':unit,'owner':p,'source':[sx,sy],'added':[x,y]})
 chk.setsection('UNIT',b''.join(records+added))
 # Candidate origins stay at actual enemy positions, never arbitrary rings around
 # the human. Prefer a ground route; island-only fronts use flying native units.
 origins=[];sources=[(x,y,u,p) for x,y,u,p in info if p in hostile and (u in COMBAT or 106<=u<176)]
 sources.sort(key=lambda r:(not(106<=r[2]<176),-((r[0]-target[0])**2+(r[1]-target[1])**2)))
 for ground in (True,False):
  if origins:break
  for sx,sy,su,p in sources:
   if any((sx-o['center'][0])**2+(sy-o['center'][1])**2<640**2 for o in origins):continue
   choices=[]
   for y in range(max(28,sy-192)//32*32+20,min(h-24,sy+193),32):
    for x in range(max(28,sx-192)//32*32+20,min(w-24,sx+193),32):
     if safe(x,y,ground) and (not ground or connected[y//8][x//8]):choices.append(((x-sx)**2+(y-sy)**2,y,x))
   cells=[]
   for _,y,x in sorted(choices):
    if any((x-a)**2+(y-b)**2<40**2 for a,b in cells):continue
    cells.append([x,y])
    if len(cells)==32:break
   if len(cells)<4:continue
   race=chk.getsection('SIDE')[p];race=race if race in (0,1,2) else 0
   unit1,unit2=({0:(37,38),1:(0,32),2:(65,66)} if ground else {0:(43,44),1:(8,12),2:(70,72)})[race]
   origins.append({'mission_id':row['mission_id'],'owner':p,'race':race,'unit1':unit1,'unit2':unit2,'cell_count':len(cells),'center':[sx,sy],'target':target,'cells':cells,'source_unit':su,'ground_route_connected':ground,'flying_only':not ground,'source_is_original_hostile_position':True,'friendly_clearance_pixels':512,'original_occupancy_clearance_pixels':[40,80]})
   if len(origins)==4:break
 assert origins,('No safe original enemy reinforcement origin',row['mission_id'],len(hostile),len(sources))
 return {'static_added':len(added),'static_reinforcements':static,'wave_origins':origins,'terrain':terrain,'hostile_owners':sorted(hostile),'original_unit_records_preserved':len(records),'first_elapsed_seconds':360 if row['no_production'] else 300,'interval_seconds':180 if row['no_production'] else 120,'wave_progression_seconds':[300,600,900],'wave_policy':'plugin/include/wave_progression.h','wave_composition':'deterministic race/elapsed-time variants; live DAT half-supply budget; flying-only origin restriction preserved','limits':['Offline terrain connectivity and placement checks, not native pathfinder or combat playtest.','Native runtime rechecks current allies, occupancy and hostile ownership immediately before each spawn.']}

def mineral_reserved_points(difficulty):
 return [point for origin in difficulty['wave_origins'] for point in origin['cells']]

def assert_original_units_preserved(before,after,mineral_bonus=0):
 """Only mineral/geyser coordinates may change during the mining repair."""
 assert len(before)%36==0 and len(after)%36==0 and len(after)>=len(before)
 moved=[]
 for index in range(len(before)//36):
  a,b=before[index*36:(index+1)*36],after[index*36:(index+1)*36]
  if mineral_bonus and struct.unpack_from('<H',a,8)[0] in (176,177,178):
   expected=bytearray(a);valid=struct.unpack_from('<H',a,14)[0];amount=struct.unpack_from('<I',a,20)[0] if valid&16 else 1500
   struct.pack_into('<H',expected,14,valid|16);struct.pack_into('<I',expected,20,amount+mineral_bonus)
   a=bytes(expected)
  if a==b:continue
  assert struct.unpack_from('<H',a,8)[0] in (176,177,178,188),('Non-resource moved',index)
  assert a[:4]==b[:4] and a[8:]==b[8:],('Mineral properties changed',index)
  ax,ay=struct.unpack_from('<HH',a,4);bx,by=struct.unpack_from('<HH',b,4)
  assert (ax-bx)**2+(ay-by)**2<=resource_layout.MAX_DISPLACEMENT**2,('Resource moved too far',index)
  moved.append(index)
 return moved

def make_map(raw,row):
 chk=CHK(raw);original=dict(chk.sections);original_order=list(chk.order)
 assert digest(raw)==row['source_sha256']
 counter_audit=audit_counters(chk);switch_audit=audit_switches(chk)
 settings=unlock(chk,row)
 # Keep the proven T01 static additions/terrain targets, while the all-map ending
 # pipeline handles its original Victory before cinematic just like other maps.
 if row['mission_id']==101:
  t01,t01_report,t01_config=make_plain_chk(raw);t01=CHK(t01)
  for tag in ('UNIT','OWNR','SIDE','FORC'):chk.setsection(tag,t01.getsection(tag))
  # Preserve the existing T01 wave owner's dedicated unused P7 slot exactly as
  # the validated standalone patch; all original human/enemy slots stay unchanged.
  temp=CHK(raw);difficulty=strengthen(temp,row);difficulty['static_added']=len(chk.getsection('UNIT'))//36-len(original[b'UNIT'])//36;difficulty['t01_static_source']='Existing inspected build_plain_chk.apply_difficulty (46 zerglings + 1 geyser)';difficulty['static_reinforcements']=t01_config['static_reinforcements']
 else:difficulty=strengthen(chk,row)
 minerals=resource_layout.apply_layout(chk,row,reserved_points=mineral_reserved_points(difficulty))
 gas=main_base_gas.apply(chk,row,minerals,reserved_points=mineral_reserved_points(difficulty))
 from sc1.native_campaign import mineral_amount_bonus
 mineral_amounts=mineral_amount_bonus.apply(chk)
 progression=patch_progression(chk,row)
 chk.setsection('STR ',append_marker(chk.getsection('STR '),row['fingerprint'].encode('ascii')))
 permitted={b'UNIT',b'PUNI',b'UPGR',b'PUPx',b'PTEC',b'PTEx',b'TRIG',b'STR '}
 if row['mission_id']==101:permitted|={b'OWNR',b'SIDE',b'FORC'}
 assert chk.order==original_order
 assert all(chk.sections[k]==v for k,v in original.items() if k not in permitted)
 assert_original_units_preserved(original[b'UNIT'],chk.getsection('UNIT'),mineral_bonus=500)
 assert strings(chk.getsection('STR '))[:len(strings(original[b'STR ']))]==strings(original[b'STR '])
 rawout=chk.save();assert CHK(rawout).save()==rawout
 report={'mission_id':row['mission_id'],'asset_path':row['asset_path'],'source':row['source'],'source_sha256':row['source_sha256'],'sha256':digest(rawout),'bytes':len(rawout),'chk_version':row['chk_version'],'fingerprint':row['fingerprint'],'owner':row['owner'],'no_production':row['no_production'],'original_section_order_preserved':True,'unchanged_sections':[k.decode('ascii') for k in original if k not in permitted],'original_briefing_wav_locations_terrain_heroes_preserved':True,'original_player_ownership_and_races_preserved':row['mission_id']!=101,'ownership_exception':'T01 existing dedicated P7 wave slot only' if row['mission_id']==101 else None,'progression':progression,'death_counter_audit':counter_audit,'switch_audit':switch_audit,'unlock':settings,'difficulty':difficulty,'native_load_verified':False,'mission_completion_verified':False}
 report['mineral_layout']=minerals
 report['resource_layout']=minerals
 report['main_base_gas']=gas
 report['mineral_amount_bonus']=mineral_amounts
 return rawout,report

def wave_header(rows):
 h=['// Generated from offline original terrain/occupancy analysis.','#pragma once','#include <cstdint>','namespace sc1_native { namespace campaign_wave_config {','struct Point { std::int32_t x,y; };','struct Origin { std::uint32_t mission_id,owner,race,unit1,unit2,cell_count; Point center,target; Point cells[32]; };','inline constexpr Origin kOrigins[] = {']
 for r in rows:
  for o in r['difficulty']['wave_origins']:
   values=', '.join(str(o[k]) for k in ('mission_id','owner','race','unit1','unit2','cell_count'))
   point=lambda xy:'{'+', '.join(map(str,xy))+'}'
   cells=o['cells']+[[0,0]]*(32-len(o['cells']))
   h.append('    {'+values+', '+point(o['center'])+', '+point(o['target'])+', {'+', '.join(point(c) for c in cells)+'}},')
 h+=['};','} } // namespace sc1_native::campaign_wave_config']
 return '\n'.join(h)+'\n'

def build(output=OUT,receipt=RECEIPT):
 output,receipt=Path(output),Path(receipt)
 assert output.resolve().is_relative_to(SC1.resolve()) and receipt.resolve().is_relative_to(SC1.resolve())
 rows=generate_metadata();reports=[]
 for row in rows:
  source=Path(row['source']);raw,report=make_map(source.read_bytes(),row)
  dest=output/str(row['mission_id'])/'scenario.chk';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
  report['output']=str(dest.resolve());dump(dest.with_name('evidence.json'),report);reports.append(report)
  print(json.dumps({'mission_id':row['mission_id'],'built':True,'added_units':report['difficulty']['static_added'],'origins':len(report['difficulty']['wave_origins']),'midpoint':report['progression']['middle']['kind']}),flush=True)
 WAVE_HEADER.write_text(wave_header(reports),encoding='utf-8')
 report={'schema_version':3,'handshake':{'kind':'ordinary_switches_v1',**SWITCHES},'built_at_utc':datetime.now(timezone.utc).isoformat(),'status':'63 original and Brood War campaign assets built; live playtest pending','map_count':len(reports),'logical_mission_count':len({r['completion_bit'] for r in rows}),'maps':reports,'generated_header':str(HEADER.resolve()),'generated_header_sha256':digest(HEADER.read_bytes()),'wave_generated_header':str(WAVE_HEADER.resolve()),'wave_generated_header_sha256':digest(WAVE_HEADER.read_bytes()),'mission_metadata':str(MISSION_JSON.resolve()),'mission_metadata_sha256':digest(MISSION_JSON.read_bytes()),'game_files_modified':False,'game_process_accessed':False,'user_database_accessed':False,'live_gameplay_verified':False,'scope_exclusions':['Original developer-cut Terran07 and Terran10','tutorial scenarios'],'limits':['All 63 assets have structural progression, original-ending and offline placement verification only.','Actual campaign menu loading, final reward/ACK/ending, transitions and combat balance require live playtests.']}
 report['mineral_layout_source']=str(Path(mineral_layout.__file__).resolve())
 report['mineral_layout_source_sha256']=digest(Path(mineral_layout.__file__).read_bytes())
 report['resource_layout_source']=str(Path(resource_layout.__file__).resolve())
 report['resource_layout_source_sha256']=digest(Path(resource_layout.__file__).read_bytes())
 report['ladder_resource_layout_source']=str(Path(ladder_resource_layout.__file__).resolve())
 report['ladder_resource_layout_source_sha256']=digest(Path(ladder_resource_layout.__file__).read_bytes())
 report['addon_placement_source']=str(Path(addon_placement.__file__).resolve())
 report['addon_placement_source_sha256']=digest(Path(addon_placement.__file__).read_bytes())
 report['main_base_gas_source']=str(Path(main_base_gas.__file__).resolve())
 report['main_base_gas_source_sha256']=digest(Path(main_base_gas.__file__).read_bytes())
 report['mining_layout_audit_source']=str(Path(mining_layout_audit.__file__).resolve())
 report['mining_layout_audit_source_sha256']=digest(Path(mining_layout_audit.__file__).read_bytes())
 report['resource_depot_guard_source']=str(Path(resource_depot_placement.__file__).resolve())
 report['resource_depot_guard_source_sha256']=digest(Path(resource_depot_placement.__file__).read_bytes())
 from sc1.native_campaign import mineral_amount_bonus
 report['mineral_amount_bonus_source']=str(Path(mineral_amount_bonus.__file__).resolve())
 report['mineral_amount_bonus_source_sha256']=digest(Path(mineral_amount_bonus.__file__).read_bytes())
 report['map_builder_sha256']=digest(Path(__file__).read_bytes())
 dump(receipt,report);return report

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=OUT);parser.add_argument('--receipt',type=Path,default=RECEIPT);parser.add_argument('--metadata-only',action='store_true');args=parser.parse_args()
 if args.metadata_only:print(json.dumps({'missions':len(generate_metadata())}));return
 result=build(args.output,args.receipt);print(json.dumps({'maps':result['map_count'],'receipt':str(args.receipt)}))
if __name__=='__main__':main()
