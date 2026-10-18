"""Structural and ordinary-CHK execution tests; no StarCraft process is launched.

The independent interpreter below executes the bytes of all gated endings. It
models the trigger control flow (including waits, pauses and original next-map
operations), not combat, UI rendering, AI, pathfinding or the native game engine.
"""
from __future__ import annotations
from copy import deepcopy
import hashlib,json,struct,unittest
from pathlib import Path
from sc1.campaign.missions import load_missions
from sc1.native_campaign import build_all_campaigns as builder
ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'native_campaign/all_campaign_maps_evidence.json'

def sections(raw):
 result={};off=0
 while off<len(raw):
  name,n=struct.unpack_from('<4sI',raw,off);off+=8;result[name]=raw[off:off+n];off+=n
 assert off==len(raw)
 return result

def trigger_rows(raw):
 assert len(raw)%2400==0
 return [raw[i:i+2400] for i in range(0,len(raw),2400)]

def cs(t):return [t[i:i+20] for i in range(0,320,20) if t[i+15] and not t[i+17]&2]
def acts(t):return [t[i:i+32] for i in range(320,2368,32) if t[i+26] and not t[i+28]&2]
def effective(data,n,owner,i,current=True):
 default=data[(26+owner)*n+i]
 return data[((25 if current else 24) if default else (12+owner if current else owner))*n+i]

class OrdinaryTriggerMachine:
 """Independent interpreter for every condition used by the 71 original endings.

Source mission completion is provided as a numeric fixture. This deliberately
makes no claim to play through the mission or emulate native campaign behavior.
 """
 def __init__(self):
  self.values={};self.deaths={};self.switches={};self.events=[];self.victory=False;self.paused=False;self.clock_ms=0;self.next_scenario=None
 @staticmethod
 def unpack(c):return struct.unpack('<IIIHBBBBH',c)
 @staticmethod
 def compare(actual,expected,op):
  if op==0:return actual>=expected
  if op==1:return actual<=expected
  if op==10:return actual==expected
  raise AssertionError(f'Unsupported numeric comparator {op}')
 def satisfy(self,conditions):
  for c in conditions:
   loc,p,n,u,op,kind,extra,flags,mask=self.unpack(c)
   if kind==11:self.switches[extra]=(op==2)
   elif kind==15:self.deaths[p,u]=n if op!=1 else 0
   elif kind in (1,2,3,4,5,12):self.values[kind,p,u,loc,extra]=n if op!=1 else 0
   elif kind==22:pass
   else:raise AssertionError(f'Unsupported source condition {kind}')
  assert all(self.condition(c) for c in conditions),'Source fixture is internally inconsistent'
 def condition(self,c):
  loc,p,n,u,op,kind,extra,flags,mask=self.unpack(c)
  if kind==11:return self.switches.get(extra,False)==(op==2)
  if kind==15:return self.compare(self.deaths.get((p,u),0),n,op)
  if kind in (1,2,3,4,5,12):return self.compare(self.values.get((kind,p,u,loc,extra),0),n,op)
  if kind==22:return True
  if kind==23:return False
  raise AssertionError(f'Unsupported condition {kind}')
 def eligible(self,t):return all(self.condition(c) for c in cs(t))
 def run(self,t):
  if not self.eligible(t):return False
  for a in acts(t):
   loc,text,wav,time,p,value,u,kind,mod,flags,pad,mask=struct.unpack('<IIIIIIHBBBBH',a)
   if kind==45:
    before=self.deaths.get((p,u),0)
    self.deaths[p,u]=value if mod==7 else before+value if mod==8 else max(0,before-value)
   elif kind==4:self.events.append(('wait_begin',time));self.clock_ms+=time;self.events.append(('wait_resume',self.clock_ms))
   elif kind==5:self.paused=True;self.events.append(('pause',))
   elif kind==6:self.paused=False;self.events.append(('unpause',))
   elif kind==13:
    self.switches[value]=True if mod==4 else False if mod==5 else not self.switches.get(value,False)
    self.events.append(('switch',value,self.switches[value]))
   elif kind==41:self.next_scenario=text;self.events.append(('next_scenario',text))
   elif kind==1:self.victory=True;self.events.append(('victory',));break
   else:self.events.append(('original_action',kind,hashlib.sha256(a).hexdigest()))
  return True

class AllCampaignMapTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=json.loads(REPORT.read_text(encoding='utf-8'));cls.rows=load_missions();cls.byid={r['mission_id']:r for r in cls.rows};cls.execution=[]
 def test_all_63_assets_and_57_logical_missions(self):
  self.assertEqual(len(self.rows),63);self.assertEqual(len({r['completion_bit'] for r in self.rows}),57)
  self.assertEqual({r['mission_id'] for r in self.rows},{r['mission_id'] for r in self.receipt['maps']})
  self.assertEqual({r['mission_id'] for r in self.rows if r['no_production']},{104,205,306,401,405,502,507,601,611})
  self.assertEqual(self.byid[515]['completion_bit'],self.byid[505]['completion_bit'])
  self.assertEqual(self.byid[611]['campaign_id'],7)
  for id in range(614,619):self.assertEqual(self.byid[id]['shared_reward_mission_id'],604)
 def test_original_sections_units_dialogue_and_player_slots_preserved(self):
  for row in self.receipt['maps']:
   with self.subTest(mission=row['mission_id']):
    src=sections(Path(row['source']).read_bytes());dst=sections(Path(row['output']).read_bytes())
    self.assertEqual(list(src),list(dst));self.assertEqual(hashlib.sha256(Path(row['output']).read_bytes()).hexdigest(),row['sha256'])
    for tag in (b'VER ',b'IVER',b'IVE2',b'MRGN',b'MTXM',b'ERA ',b'DIM ',b'MBRF',b'WAV ',b'SPRP',b'UNIS',b'UNIx'):
     if tag in src:self.assertEqual(src[tag],dst[tag],tag)
    self.assertGreaterEqual(len(dst[b'UNIT']),len(src[b'UNIT']))
    for offset in range(0,len(src[b'UNIT']),36):
     a,b=src[b'UNIT'][offset:offset+36],dst[b'UNIT'][offset:offset+36]
     if a==b:continue
     self.assertIn(struct.unpack_from('<H',a,8)[0],(176,177,178,188))
     self.assertEqual(a[:4],b[:4]);self.assertEqual(a[8:],b[8:])
     ax,ay=struct.unpack_from('<HH',a,4);bx,by=struct.unpack_from('<HH',b,4)
     self.assertLessEqual((ax-bx)**2+(ay-by)**2,builder.resource_layout.MAX_DISPLACEMENT**2)
    source_strings=builder.strings(src[b'STR ']);self.assertEqual(builder.strings(dst[b'STR '])[:len(source_strings)],source_strings)
    for tag in (b'OWNR',b'SIDE',b'FORC'):
     if row['mission_id']!=101:self.assertEqual(src[tag],dst[tag])
     else:
      a,b=bytearray(src[tag]),bytearray(dst[tag]);a[6]=b[6];self.assertEqual(a,b)
 def test_goal_latches_keep_original_initialization_order(self):
  for row in self.receipt['maps']:
   p=row['progression'];indices=p['original_trigger_indices']
   self.assertEqual(indices,sorted(indices))
   for route in p['routes']:
    self.assertEqual(route['goal_trigger_index']+1,route['ending_trigger_index'])
    self.assertEqual(indices[route['source_trigger']],route['ending_trigger_index'])
    if route['source_trigger']>0:self.assertLess(indices[route['source_trigger']-1],route['goal_trigger_index'])
 def test_every_original_action_and_defeat_trigger_preserved(self):
  for row in self.receipt['maps']:
   src=trigger_rows(sections(Path(row['source']).read_bytes())[b'TRIG']);dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG']);p=row['progression'];routes={r['source_trigger']:r for r in p['routes']}
   for i,t in enumerate(src):
    with self.subTest(mission=row['mission_id'],trigger=i):
     new=dst[p['original_trigger_indices'][i]]
     if i not in routes:self.assertEqual(t,new)
     else:
      self.assertEqual(t[320:],new[320:]);latch=dst[routes[i]['goal_trigger_index']]
      self.assertEqual(cs(latch)[:-1],cs(t));self.assertEqual(latch[2372:2400],t[2372:2400])
 def test_all_71_original_endings_execute_only_after_phase3_and_ack(self):
  total=0;paused=0
  for row in self.receipt['maps']:
   source=trigger_rows(sections(Path(row['source']).read_bytes())[b'TRIG']);patched=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG']);p=row['progression']
   for route in p['routes']:
    total+=1
    with self.subTest(mission=row['mission_id'],route=route['route']):
     original=source[route['source_trigger']];latch=patched[route['goal_trigger_index']];ending=patched[route['ending_trigger_index']]
     engine=OrdinaryTriggerMachine();engine.satisfy(cs(original));self.assertFalse(engine.run(ending));self.assertFalse(engine.victory)
     self.assertTrue(engine.run(latch));self.assertEqual(engine.deaths[11,226],1);self.assertEqual(engine.deaths[11,223],route['route']);self.assertTrue(engine.switches[builder.SWITCHES['goal']]);self.assertTrue(engine.switches[route['route_switch']]);self.assertFalse(engine.paused)
     # First and second choice cycles cannot accidentally release the ending.
     for phase in (1,2):
      engine.switches[builder.SWITCHES['growth_ready']]=False;engine.switches[builder.SWITCHES['ack']]=True
      self.assertFalse(engine.run(ending),(phase,row['mission_id']))
     engine.switches[builder.SWITCHES['growth_ready']]=True;engine.switches[builder.SWITCHES['ack']]=False;self.assertFalse(engine.run(ending));self.assertFalse(engine.victory)
     # Original gameplay conditions may change while choosing; route remains latched.
     engine.values.clear();engine.switches={k:v for k,v in engine.switches.items() if k in range(240,250)};engine.switches[builder.SWITCHES['ack']]=True
     expected=OrdinaryTriggerMachine();expected.satisfy(cs(original));expected.run(original)
     engine.events.clear();self.assertTrue(engine.run(ending));self.assertTrue(engine.victory)
     self.assertEqual(engine.events,expected.events);self.assertEqual(engine.next_scenario,expected.next_scenario)
     self.assertFalse(engine.run(latch),'A winning route must not be replaced after it has latched')
     paused+=any(e[0]=='pause' for e in engine.events)
     self.execution.append({'mission_id':row['mission_id'],'route':route['route'],'source_trigger':route['source_trigger'],'save_ack_required':True,'switch_handshake':True,'original_action_trace_equal':True,'pause_events':sum(e[0]=='pause' for e in engine.events),'wait_events':sum(e[0]=='wait_begin' for e in engine.events),'next_scenario_string_id':engine.next_scenario,'victory_executed':engine.victory})
  self.assertEqual(total,71);self.assertEqual(paused,36)
 def test_middle_signals_use_real_player_progress_and_reserved_counter(self):
  allowed={'original_scripted_movement_checkpoint','half_original_countdown','half_original_production_goal','half_original_elimination_goal','original_hostile_force_combat_progress'}
  for row in self.receipt['maps']:
   with self.subTest(mission=row['mission_id']):
    p=row['progression'];self.assertIn(p['middle']['kind'],allowed)
    dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG']);mid=dst[p['middle_trigger_index']]
    self.assertEqual([i for i,v in enumerate(mid[2372:2400]) if v],[row['owner']])
    engine=OrdinaryTriggerMachine();engine.satisfy(cs(mid));self.assertTrue(engine.run(mid));self.assertEqual(engine.deaths[11,224],1);self.assertTrue(engine.switches[builder.SWITCHES['middle']]);self.assertFalse(engine.switches.get(builder.SWITCHES['goal'],False),'Middle choices must not wait for victory');self.assertFalse(engine.victory)
    self.assertFalse(row['death_counter_audit']['reserved_pair_collisions'])
 def test_reserved_switches_are_unused_in_every_original_and_no_death_gate_remains(self):
  reserved=builder.reserved_switch_ids()
  for row in self.receipt['maps']:
   src=trigger_rows(sections(Path(row['source']).read_bytes())[b'TRIG']);dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG']);used=set()
   for t in src:
    used.update(c[16] for c in cs(t) if c[15]==11)
    used.update(struct.unpack_from('<I',a,20)[0] for a in acts(t) if a[26]==13)
   with self.subTest(mission=row['mission_id']):
    self.assertFalse(used&reserved);self.assertEqual(used,set(row['switch_audit']['original_used_ids']));self.assertFalse(row['switch_audit']['collisions'])
    self.assertEqual(row['progression']['handshake']['kind'],'ordinary_switches_v1');self.assertIn('_V3_SW1_',row['fingerprint'])
    for route in row['progression']['routes']:
     latch=dst[route['goal_trigger_index']];ending=dst[route['ending_trigger_index']]
     gate=cs(latch)[-1];self.assertEqual((gate[15],gate[16],gate[14]),(11,240,3))
     self.assertEqual([(c[15],c[16],c[14]) for c in cs(ending)],[(11,route['route_switch'],2),(11,242,2),(11,243,2)])
 def test_stale_reserved_deaths_cannot_block_goal_or_release_ending(self):
  for row in self.receipt['maps']:
   src=trigger_rows(sections(Path(row['source']).read_bytes())[b'TRIG']);dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG'])
   for route in row['progression']['routes']:
    with self.subTest(mission=row['mission_id'],route=route['route']):
     m=OrdinaryTriggerMachine();m.satisfy(cs(src[route['source_trigger']]))
     m.deaths.update({(11,u):0xffffffff for u in range(223,228)})
     latch=dst[route['goal_trigger_index']];ending=dst[route['ending_trigger_index']]
     self.assertTrue(m.run(latch));self.assertTrue(m.switches[240]);self.assertFalse(m.run(ending))
     m.deaths.update({(11,u):0 for u in range(223,228)})
     m.switches[242]=True;m.switches[243]=True;self.assertTrue(m.run(ending));self.assertTrue(m.victory)
 def test_first_winning_branch_cannot_be_replaced_while_choices_are_pending(self):
  checked=0
  for row in self.receipt['maps']:
   routes=row['progression']['routes']
   if len(routes)<2:continue
   src=trigger_rows(sections(Path(row['source']).read_bytes())[b'TRIG']);dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG'])
   for first in routes:
    m=OrdinaryTriggerMachine();m.satisfy(cs(src[first['source_trigger']]));self.assertTrue(m.run(dst[first['goal_trigger_index']]))
    for other in routes:
     if other is first:continue
     m.satisfy(cs(src[other['source_trigger']]));self.assertFalse(m.run(dst[other['goal_trigger_index']]))
     self.assertFalse(m.switches.get(other['route_switch'],False))
    m.switches[242]=m.switches[243]=True
    self.assertTrue(m.run(dst[first['ending_trigger_index']]))
    checked+=1
  self.assertEqual(checked,12)
 def test_scripted_middle_latches_before_original_condition_is_consumed(self):
  count=0;switch_consumers=[]
  for row in self.receipt['maps']:
   p=row['progression']
   if p['middle']['kind']!='original_scripted_movement_checkpoint':continue
   count+=1;source=p['middle']['source_trigger'];dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG'])
   mid=dst[p['middle_trigger_index']];event=dst[p['original_trigger_indices'][source]]
   with self.subTest(mission=row['mission_id'],source=source):
    self.assertTrue(p['middle_evaluated_before_source_actions'])
    self.assertEqual(p['middle_trigger_index']+1,p['original_trigger_indices'][source])
    self.assertEqual(cs(mid),cs(event))
    fixed=OrdinaryTriggerMachine();fixed.satisfy(cs(event));self.assertTrue(fixed.run(mid));self.assertTrue(fixed.run(event));self.assertEqual(fixed.deaths[11,224],1)
    old=OrdinaryTriggerMachine();old.satisfy(cs(event));old.run(event)
    if not old.eligible(mid):
     switch_consumers.append(row['mission_id']);self.assertFalse(old.run(mid));self.assertEqual(old.deaths.get((11,224),0),0)
  self.assertGreater(count,0);self.assertIn(102,switch_consumers)
  # T02's original Switch0-cleared event sets Switch0 before its dialogue.
  # The previous append-at-end model demonstrably loses the checkpoint.
 def test_non_scripted_middle_conditions_still_match_evidence(self):
  for row in self.receipt['maps']:
   p=row['progression'];dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG'])
   self.assertEqual([builder.cf(c) for c in cs(dst[p['middle_trigger_index']])],p['middle']['conditions'])
 def test_countdown_midpoint_requires_real_timer_start_and_half_progress(self):
  checked=0
  for row in self.receipt['maps']:
   p=row['progression'];middle=p['middle']
   if middle['kind']!='half_original_countdown':continue
   checked+=1;dst=trigger_rows(sections(Path(row['output']).read_bytes())[b'TRIG']);mid=dst[p['middle_trigger_index']]
   m=OrdinaryTriggerMachine();m.values[12,0,0,0,0]=1
   if row['mission_id']==209:
    # Original timer remains0 before a Drone reaches the crystal mining area.
    # The old half-countdown-only predicate would fire at this point.
    self.assertFalse(m.run(mid));self.assertFalse(m.switches.get(241,False))
    self.assertEqual(middle['countdown_started_guard']['original_switch'],0)
    m.switches[0]=True
   else:self.assertTrue(middle['countdown_started_at_initialization'])
   half=middle['original_countdown_seconds']//2
   m.values[1,0,0,0,0]=half+1;self.assertFalse(m.run(mid))
   m.values[1,0,0,0,0]=half;self.assertTrue(m.run(mid));self.assertTrue(m.switches[241]);self.assertFalse(m.switches.get(240,False))
  self.assertEqual(checked,5)
 def test_original_start_upgrades_never_decrease_and_no_production_is_six(self):
  for row in self.receipt['maps']:
   src=sections(Path(row['source']).read_bytes());dst=sections(Path(row['output']).read_bytes());owner=row['owner']
   for tag,n in ((b'UPGR',46),(b'PUPx',61),(b'PTEC',24),(b'PTEx',44)):
    if tag not in src:continue
    for i in range(n):
     with self.subTest(mission=row['mission_id'],section=tag,upgrade=i):
      self.assertGreaterEqual(effective(dst[tag],n,owner,i),effective(src[tag],n,owner,i))
      if row['no_production'] and tag in (b'UPGR',b'PUPx') and i<16:self.assertGreaterEqual(effective(dst[tag],n,owner,i),6)
 def test_brood_war_regular_units_permitted_without_changing_original_format(self):
  for row in self.receipt['maps']:
   m=self.byid[row['mission_id']];dst=sections(Path(row['output']).read_bytes());puni=dst[b'PUNI'];owner=row['owner']
   for unit in builder.BW_UNITS[m['race']]:
    self.assertEqual(puni[owner*228+unit],1)
    self.assertEqual(puni[(13+owner)*228+unit],0)
   self.assertEqual(struct.unpack('<H',dst[b'VER '])[0],205 if m['expansion'] else 59)
 def test_every_map_has_checked_original_enemy_origin_and_static_additions(self):
  for row in self.receipt['maps']:
   with self.subTest(mission=row['mission_id']):
    d=row['difficulty'];self.assertGreater(d['static_added'],0);self.assertGreater(len(d['wave_origins']),0)
    for origin in d['wave_origins']:
     self.assertIn(origin['owner'],d['hostile_owners']);self.assertTrue(origin['source_is_original_hostile_position']);self.assertGreaterEqual(origin['cell_count'],4);self.assertLessEqual(origin['cell_count'],32)
     self.assertEqual(len(origin['cells']),origin['cell_count'])
     if not origin['ground_route_connected']:self.assertIn(origin['unit1'],(8,43,70));self.assertTrue(origin['flying_only'])
 @classmethod
 def tearDownClass(cls):
  target=ROOT/'campaign/all_map_trigger_execution.json'
  target.write_text(json.dumps({'schema_version':1,'scope':'Independent ordinary CHK byte interpreter with source-condition fixtures, not StarCraft engine or gameplay execution','source_receipt_sha256':hashlib.sha256(REPORT.read_bytes()).hexdigest(),'maps':63,'ending_routes_executed':len(cls.execution),'game_process_accessed':False,'native_gameplay_verified':False,'routes':cls.execution},indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':unittest.main()
