"""Actual 63-map outputs, original DT event prerequisites and expansion safety."""
import copy,json,math,struct,unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as maps,corner_resource_layout as corner
from sc1.native_campaign import mission_balance,scripted_openings
from sc1.campaign.missions import load_missions

class OpeningResourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=json.loads(maps.RECEIPT.read_text(encoding='utf8'))['maps']
  cls.missions={r['mission_id']:r for r in load_missions()}
 def test_complete_roster_and_original_unit_properties(self):
  self.assertEqual({r['mission_id'] for r in self.rows},set(self.missions))
  self.assertEqual(len(self.rows),63)
  for row in self.rows:
   output=maps.CHK(Path(row['output']).read_bytes());original=maps.CHK(Path(row['source']).read_bytes())
   baseline=maps.CHK(output.save());mission_balance.undo(baseline,row['mission_balance'])
   corner.undo(baseline,row['corner_resource_layout'])
   maps.assert_original_units_preserved(original.getsection('UNIT'),baseline.getsection('UNIT'),mineral_bonus=500)
   # Final pass has an exact, separately reversible record for each amount edit.
   self.assertEqual(row['corner_resource_layout']['mission'],row['mission_id'])
 def test_dt_holding_boxes_empty_after_four_original_moves(self):
  row=next(r for r in self.rows if r['mission_id']==402)
  output=maps.CHK(Path(row['output']).read_bytes());source=maps.CHK(Path(row['source']).read_bytes())
  points=list(map(mission_balance.info,mission_balance.records(output)))
  templars=[p for p in points if p[2:]==(61,1)]
  self.assertEqual(len(templars),4)
  locations=source.getsection('MRGN')
  for loc in (9,25,26,27):
   left,top,right,bottom=struct.unpack_from('<4I',locations,(loc-1)*20)
   held=[p for p in templars if left<=p[0]<=right and top<=p[1]<=bottom]
   self.assertEqual(len(held),1)
   templars.remove(held[0])
  self.assertEqual(templars,[])
  # Exact event code that moves DTs, gates the attack AI, and gives control back.
  final=maps.triggers(output);original=maps.triggers(source)
  for index in (14,17,18,27,28,29):self.assertIn(original[index],final)
  self.assertFalse({1,3}&set(row['difficulty']['hostile_owners']))
 def test_southwest_expansion_has_no_added_spawn_cells(self):
  row=next(r for r in self.rows if r['mission_id']==402);mission=self.missions[402]
  for origin in row['difficulty']['wave_origins']:
   self.assertEqual(origin['owner'],4)
   for x,y in origin['cells']:self.assertTrue(scripted_openings.additional_spawn_allowed(mission,x,y))
  for guard in row['mission_balance']['garrisons']+row['difficulty']['static_reinforcements']:
   self.assertTrue(scripted_openings.additional_spawn_allowed(mission,*guard['added']))
 def test_main_402_gas_and_eleven_minerals(self):
  row=next(r for r in self.rows if r['mission_id']==402)
  raw=maps.CHK(Path(row['output']).read_bytes()).getsection('UNIT')
  self.assertEqual(struct.unpack_from('<I',raw,20*36+20)[0],7000)
  indices=(7,8,9,10,11,12,13,14,15,16,19)
  self.assertEqual([struct.unpack_from('<I',raw,i*36+20)[0] for i in indices],[5000]*11)
  self.assertEqual(len(row['corner_resource_layout']['mineral_amount_changes']),11)
 def test_changed_banks_have_paths_foundations_and_shorter_trips(self):
  changed=0
  for row in self.rows:
   for bank in row['corner_resource_layout']['bases']:
    if bank['status']!='compact_corner':continue
    changed+=1
    self.assertTrue(bank['worker_access']['all_mineral_fronts_reachable'])
    self.assertEqual({r['unit'] for r in bank['depot_sites']},{106,131,154})
    self.assertTrue(all(r['terrain_buildable'] and r['resource_clear'] and r['fixed_occupancy_clear'] for r in bank['depot_sites']))
    self.assertLessEqual(max(bank['distance_after']),max(bank['distance_before'])+16.01)
    self.assertTrue(sum(bank['distance_after'])<=sum(bank['distance_before'])+.1 or max(bank['distance_after'])<=max(bank['distance_before'])*.85+.01)
  self.assertGreater(changed,250)
 def test_amount_and_coordinate_tampering_is_rejected(self):
  row=next(r for r in self.rows if r['mission_id']==402)
  output=maps.CHK(Path(row['output']).read_bytes());mission_balance.undo(output,row['mission_balance'])
  raw=bytearray(output.getsection('UNIT'));struct.pack_into('<I',raw,20*36+20,7001);output.setsection('UNIT',raw)
  with self.assertRaises(AssertionError):corner.undo(output,row['corner_resource_layout'])

if __name__=='__main__':unittest.main()
