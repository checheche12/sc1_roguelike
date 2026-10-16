"""Source-CHK progression regression tests; no map files or game are changed.

The interpreter checks ordinary trigger conditions and action bytes, not the
StarCraft engine, UI appearance, pathfinding, combat or an actual mission win.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import struct,unittest
from sc1.native_campaign import build_all_campaigns as b
from sc1.tests.test_all_campaign_maps import OrdinaryTriggerMachine,cs,acts

class TimedSurvivalVictoryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.maps={}
  for spec in b.roster_specs():
   src=b.SOURCE_ROOT/'locales/koKR/Assets'/spec['asset_path'];raw=src.read_bytes();source=b.CHK(raw);row=b.metadata(spec,source,src);patched=b.CHK(raw)
   progression=b.patch_progression(patched,row)
   cls.maps[row['mission_id']]=(row,source,patched,progression)
 def fixture(self,mission):
  row,src,dst,p=self.maps[mission];alt=p['alternate_survival_victory'];ts=b.triggers(dst);m=OrdinaryTriggerMachine()
  m.satisfy(cs(ts[alt['goal_trigger_index']]))
  return row,src,dst,p,alt,ts,m
 def test_only_reviewed_terminal_holdouts_receive_alternate_victory(self):
  self.assertEqual(len(self.maps),63)
  self.assertEqual({i for i,(_,_,_,p) in self.maps.items() if p['alternate_survival_victory']},{103,408})
  # These use timers but still require assault, escort, mining/delivery, escape,
  # a duel, a ceasefire, an ending animation, or the timed bonus branch.
  for mission in (202,204,209,302,502,507,605,607,609):
   self.assertIsNone(self.maps[mission][3]['alternate_survival_victory'])
 def test_observation_switch_is_unused_in_all_original_assets(self):
  for row,src,_,_ in self.maps.values():
   with self.subTest(mission=row['mission_id']):
    audit=b.audit_switches(src);self.assertIn(250,audit['reserved_ids']);self.assertNotIn(250,audit['original_used_ids'])
 def test_every_original_action_owner_and_failure_trigger_stays_identical(self):
  count=0
  for row,src,dst,p in self.maps.values():
   before=b.triggers(src);after=b.triggers(dst);routes={x['source_trigger']:x for x in p['routes']}
   for i,t in enumerate(before):
    new=after[p['original_trigger_indices'][i]]
    with self.subTest(mission=row['mission_id'],trigger=i):
     self.assertEqual(new[320:],t[320:])
     if i not in routes:self.assertEqual(new,t)
     else:
      count+=1;self.assertEqual(cs(after[routes[i]['goal_trigger_index']])[:-1],cs(t))
  self.assertEqual(count,71)
 def test_empty_start_and_unobserved_factions_cannot_win(self):
  for mission in (103,408):
   row,src,dst,p,alt,ts,m=self.fixture(mission);latch=ts[alt['goal_trigger_index']];seen=ts[alt['enemy_seen_trigger_index']]
   cold=OrdinaryTriggerMachine();self.assertFalse(cold.run(seen));self.assertFalse(cold.run(latch))
   m.switches[250]=False;self.assertFalse(m.run(latch))
   # Even elapsed time and active original switches do not invent a base.
   self.assertFalse(m.run(seen));self.assertFalse(m.run(latch))
   for enemy in alt['enemy_owners']:m.values[2,enemy,231,0,0]=1
   m.values[12,0,0,0,0]=0;self.assertFalse(m.run(seen))
   m.values[12,0,0,0,0]=1
   if len(alt['enemy_owners'])>1:
    enemy=alt['enemy_owners'][-1];m.values[2,enemy,231,0,0]=0;self.assertFalse(m.run(seen));m.values[2,enemy,231,0,0]=1
   self.assertTrue(m.run(seen));self.assertTrue(m.switches[250]);self.assertFalse(m.run(latch))
   for enemy in alt['enemy_owners']:m.values[2,enemy,231,0,0]=0
   self.assertTrue(m.run(latch));self.assertTrue(m.switches[240]);self.assertFalse(m.victory)
 def test_every_hostile_building_owner_blocks_until_completely_clear(self):
  for mission in (103,408):
   row,src,dst,p,alt,ts,m=self.fixture(mission);latch=ts[alt['goal_trigger_index']]
   enemies=alt['enemy_owners'];self.assertEqual(enemies,[4] if mission==103 else [0,4,5])
   targets=[b.cf(c) for c in cs(latch) if c[15]==2 and b.cf(c)['player'] in enemies]
   self.assertEqual(targets,[{'location':0,'player':x,'amount':0,'unit':231,'comparison':1,'type':2} for x in enemies])
   # Command Buildings uses no location/ground-only filter. A remaining supply,
   # defense, extractor, add-on or lifted building is still a building count.
   for enemy in enemies:
    m.values[2,enemy,231,0,0]=1;self.assertFalse(m.run(latch));m.values[2,enemy,231,0,0]=0
   self.assertTrue(m.run(latch))
 def test_original_activation_and_survival_failures_block_the_alternate(self):
  for mission in (103,408):
   row,src,dst,p,alt,ts,m=self.fixture(mission);latch=ts[alt['goal_trigger_index']]
   active=b.TIMED_SURVIVAL[mission]['active_switch'];m.switches[active]=False;self.assertFalse(m.run(latch));m.switches[active]=True
   m.values[2,row['owner'],231,0,0]=0;self.assertFalse(m.run(latch));m.values[2,row['owner'],231,0,0]=1
   if mission==408:
    for hero in (75,88):
     m.deaths[row['owner'],hero]=1;self.assertFalse(m.run(latch));m.deaths[row['owner'],hero]=0
    m.values[2,17,175,0,0]=0;self.assertFalse(m.run(latch));m.values[2,17,175,0,0]=1
    for failure_switch in (4,9):
     m.switches[failure_switch]=True;self.assertFalse(m.run(latch));m.switches[failure_switch]=False
    self.assertFalse(any(c[15]==2 and b.cf(c)['unit'] in (75,88) for c in cs(latch)),'Delivered heroes are removed by the original map')
   self.assertTrue(m.run(latch))
 def test_alternate_uses_unexpired_timer_and_exact_success_after_ready_and_ack(self):
  for mission in (103,408):
   row,src,dst,p,alt,ts,m=self.fixture(mission);latch=ts[alt['goal_trigger_index']];ending=ts[alt['ending_trigger_index']]
   m.values[1,0,0,0,0]=alt['original_timer_seconds']-1
   self.assertFalse(any(c[15]==1 for c in cs(latch)));self.assertTrue(m.run(latch));self.assertFalse(m.paused);self.assertFalse(m.victory)
   for ready,ack in ((False,False),(False,True),(True,False)):
    m.switches[242]=ready;m.switches[243]=ack;self.assertFalse(m.run(ending));self.assertFalse(m.victory)
   # Finishing growth does not wait for the original countdown, and does not
   # substitute a defeat/cinematic sequence for the original success sequence.
   m.switches[242]=m.switches[243]=True;m.events.clear();self.assertTrue(m.run(ending));self.assertTrue(m.victory)
   original=b.triggers(src)[alt['original_ending_trigger']];expected=OrdinaryTriggerMachine();expected.satisfy(cs(original));expected.run(original)
   self.assertEqual(m.events,expected.events);self.assertEqual(m.next_scenario,expected.next_scenario)
   self.assertEqual(ending[320:],original[320:]);self.assertNotIn(2,[a[26] for a in acts(ending)])
 def test_first_original_or_alternate_route_cannot_be_replaced(self):
  for mission in (103,408):
   row,src,dst,p,alt,ts,m=self.fixture(mission);alternate=ts[alt['goal_trigger_index']]
   self.assertTrue(m.run(alternate))
   for route in p['routes']:
    m.satisfy(cs(b.triggers(src)[route['source_trigger']]))
    self.assertFalse(m.run(ts[route['goal_trigger_index']]))
   for route in p['routes']:
    original_first=OrdinaryTriggerMachine();original_first.satisfy(cs(b.triggers(src)[route['source_trigger']]))
    self.assertTrue(original_first.run(ts[route['goal_trigger_index']]))
    original_first.satisfy(cs(alternate)[:-1]);self.assertFalse(original_first.run(alternate))
 def test_objective_updates_preserve_existing_strings_and_source_actions(self):
  for mission,(row,src,dst,p) in self.maps.items():
   before=b.strings(src.getsection('STR '));after=b.strings(dst.getsection('STR '));self.assertEqual(after[:len(before)],before)
   alt=p['alternate_survival_victory']
   if alt is None:self.assertEqual(before,after);continue
   self.assertEqual(len(after)-len(before),1 if mission==103 else 2)
   for update in alt['objective_updates']:
    event=b.triggers(dst)[update['trigger_index']];self.assertEqual([a[26] for a in acts(event)],[12]);self.assertIn('모든 건물 파괴',update['text_utf8'])
    self.assertEqual(after[update['string_id']-1].decode('utf-8'),update['text_utf8'])
 def test_changed_or_empty_sources_fail_closed_for_review(self):
  for mission in (103,408):
   row,src,_,_=self.maps[mission];enemy=b.TIMED_SURVIVAL[mission]['enemy_owners'][0]
   empty=b.CHK(src.save());empty.setsection('UNIT',b''.join(r for r in b.units(src) if not(b.unit_info(r)[3]==enemy and 106<=b.unit_info(r)[2]<176)))
   with self.assertRaises(AssertionError):b.timed_survival_plan(empty,row)
   invincible=b.CHK(src.save());records=b.units(src);i=next(i for i,r in enumerate(records) if b.unit_info(r)[3]==enemy and 106<=b.unit_info(r)[2]<176);r=bytearray(records[i]);struct.pack_into('<H',r,12,16);struct.pack_into('<H',r,26,16);records[i]=bytes(r);invincible.setsection('UNIT',b''.join(records))
   with self.assertRaises(AssertionError):b.timed_survival_plan(invincible,row)

if __name__=='__main__':unittest.main()
