"""Inspect actual built maps, including economic access and tamper rejection."""
from pathlib import Path
import copy,json,math,struct,unittest
from unittest.mock import patch
from sc1.native_campaign import build_all_campaigns as maps,mission_balance as balance
from sc1.native_campaign import package_all_campaigns as package,mining_layout_audit as mining
from sc1.campaign.missions import load_missions

def balance_map(row):
 chk=maps.CHK(Path(row['output']).read_bytes())
 if 'courtyard_resource_layout' in row:
  from sc1.native_campaign import courtyard_resource_layout
  courtyard_resource_layout.undo(chk,row['courtyard_resource_layout'])
 return chk

class MissionBalanceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.receipt=json.loads((maps.ROOT/'all_campaign_maps_evidence.json').read_text(encoding='utf8'))
  cls.rows=cls.receipt['maps'];cls.missions={r['mission_id']:r for r in load_missions()}
 def test_every_asset_has_reviewed_budget_and_no_production_exemptions(self):
  self.assertEqual(set(balance.GARRISONS),set(self.missions))
  self.assertGreater(len(set(balance.GARRISONS.values())),8)
  for row in self.rows:
   r=row['mission_balance'];self.assertEqual(r['garrison_added'],balance.GARRISONS[row['mission_id']])
   if self.missions[row['mission_id']]['no_production'] or row['mission_id'] in (201,501,602):self.assertEqual(r['garrison_added'],0)
 def test_original_units_preserved_and_only_hostile_armed_prototypes_copied(self):
  for row in self.rows:
   chk=balance_map(row);raw=balance.records(chk);r=row['mission_balance']
   baseline=maps.CHK(chk.save());balance.undo(baseline,r);old=balance.records(baseline)
   moved={m['index'] for m in (r.get('opening') or {}).get('mineral_moves',[])}
   for i,v in enumerate(old):
    if i not in moved:self.assertEqual(v,raw[i])
   for index,guard in enumerate(r['garrisons'],r['base_unit_count']):
    source=old[guard['source_record']];actual=raw[index]
    self.assertEqual(source[8:],actual[8:]);self.assertEqual(guard['unit'],balance.info(actual)[2])
    self.assertIn(guard['unit'],balance.ARMED);self.assertIn(guard['owner'],row['difficulty']['hostile_owners'])
    self.assertLessEqual(math.dist(guard['source'],guard['added']),math.hypot(320,320))
 def test_placements_do_not_overlap_fixed_objects_or_wave_cells(self):
  boxes,_=balance.geometry.load_unit_geometry()
  for row in self.rows:
   chk=balance_map(row);points=list(map(balance.info,balance.records(chk)));r=row['mission_balance']
   for i,p in enumerate(points[r['base_unit_count']:],r['base_unit_count']):
    x,y,u,owner=p;rect=balance.geometry._rect(x,y,u,boxes)
    for j,(xx,yy,unit,_) in enumerate(points):
     if i==j or unit==214:continue
     self.assertFalse(balance.geometry._overlap(rect,balance.geometry._rect(xx,yy,unit,boxes)),(row['mission_id'],i,j))
    if row['mission_id']!=201:
     for origin in row['difficulty']['wave_origins']:
      self.assertTrue(all(math.dist((x,y),cell)>=48 for cell in origin['cells']))
 def test_zerg01_ten_drones_and_all_eleven_mineral_fronts(self):
  row=next(r for r in self.rows if r['mission_id']==201);chk=balance_map(row)
  info=list(map(balance.info,balance.records(chk)));r=row['mission_balance']['opening']
  self.assertEqual(sum(u==41 and owner==row['owner'] for x,y,u,owner in info),10)
  self.assertEqual(row['mission_balance']['garrison_added'],0)
  audit=mining.audit_field(chk,info,balance.ZERG01_MINERALS,r['mining_audit']['anchor'],direction=(0,1))
  self.assertEqual(audit['front_reachable_count'],11);self.assertTrue(audit['resource_depot_clear'])
  self.assertTrue(audit['foundation_terrain_buildable']);self.assertLess(max(r['mineral_distance_after']),251)
  self.assertLess(sum(r['mineral_distance_after']),sum(r['mineral_distance_before'])*.83)
  self.assertTrue(r['army_routes_preserved']);self.assertTrue(r['resource_trigger_membership_preserved'])
 def test_new_pass_replays_exactly_after_undo(self):
  for row in self.rows:
   raw=balance_map(row).save();chk=maps.CHK(raw);balance.undo(chk,row['mission_balance'])
   report=balance.apply(chk,self.missions[row['mission_id']],row['difficulty'])
   self.assertEqual(report,row['mission_balance']);self.assertEqual(chk.save(),raw)
 def test_receipt_cannot_authorize_a_different_guard(self):
  row=copy.deepcopy(next(r for r in self.rows if r['mission_balance']['garrison_added']))
  output=maps.CHK(Path(row['output']).read_bytes());source=maps.CHK(Path(row['source']).read_bytes())
  raw=bytearray(output.getsection('UNIT'));offset=row['mission_balance']['base_unit_count']*36
  struct.pack_into('<H',raw,offset+8,41);output.setsection('UNIT',bytes(raw));report=row['mission_balance']
  report['appended_records'][0]=bytes(raw[offset:offset+36]).hex();report['after_unit_sha256']=balance.sha(bytes(raw))
  with patch.object(package,'_verify_base_resource_layout'):
   with self.assertRaises(ValueError):package.verify_mineral_layout(source,output,self.missions[row['mission_id']],row)
 def test_rear_catalog_matches_actual_default_counts(self):
  catalog=json.loads((maps.SC1/'campaign/runtime_talents_v5.json').read_text(encoding='utf8'))
  rear=next(c for c in catalog['curses'] if c['id']=='09224f2f-b115-5c53-adb3-883bb36075cd')
  self.assertTrue(rear['effect']['retired']);self.assertTrue(rear['effect']['runtime_disabled'])
  self.assertEqual(rear['effect']['shared_special_roster_limit'],2)

if __name__=='__main__':unittest.main()
