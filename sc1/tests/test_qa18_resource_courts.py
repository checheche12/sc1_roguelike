"""Audit actual campaign outputs against the gas-behind-minerals regression."""
import json,struct,unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as maps,courtyard_resource_layout as joint

class ResourceCourtTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rows=json.loads(maps.RECEIPT.read_text(encoding='utf8'))['maps']
 def test_entire_roster_has_three_sides_and_unblocked_gas(self):
  self.assertEqual(len(self.rows),63);courts=0
  for row in self.rows:
   chk=maps.CHK(Path(row['output']).read_bytes());info=list(map(joint.rules.geometry._info,joint.rules.geometry._records(chk)))
   walk,_=joint.rules.geometry.load_terrain(chk);worker=joint.rules._worker_terrain(walk);boxes,_=joint.rules.geometry.load_unit_geometry()
   buildable=joint.rules.mining.load_buildable_grid(chk)
   for bank in row['courtyard_resource_layout']['bases']:
    if not bank['gas_indices']:continue
    center=bank['anchor']['center'];minerals=[info[i][:2] for i in bank['mineral_indices']];gases=[info[i][:2] for i in bank['gas_indices']]
    if len(minerals)>=3:
     self.assertEqual(bank['status'],'joint_u_court',(row['mission_id'],bank['anchor']));courts+=1
     self.assertEqual(joint.court(center,minerals,gases),tuple(bank['opening']))
    for index in bank['gas_indices']:
     self.assertTrue(joint.gas.direct_lane(bank['anchor'],info[index][:2],info,index,worker,boxes),(row['mission_id'],index))
     self.assertTrue(joint.rules._foundation(chk,info[index][:2],188,buildable))
    self.assertTrue(joint.corner.depot_sites(chk,info,bank['anchor'],buildable,boxes)[0])
    self.assertTrue(joint.worker_access(info,bank['mineral_indices'],bank['anchor'],worker,boxes)[0],(row['mission_id'],bank['anchor']))
  self.assertGreater(courts,250)
 def test_only_resource_xy_changes_and_exact_undo(self):
  boxes,_=joint.rules.geometry.load_unit_geometry()
  for row in self.rows:
   final=maps.CHK(Path(row['output']).read_bytes());raw=final.save();before=maps.CHK(raw);joint.undo(before,row['courtyard_resource_layout'])
   self.assertEqual(before.order,final.order)
   for tag,value in before.sections.items():
    if tag!=b'UNIT':self.assertEqual(value,final.sections[tag])
   old=joint.rules.geometry._records(before);new=joint.rules.geometry._records(final);self.assertEqual(len(old),len(new))
   for a,b in zip(old,new):
    if a==b:continue
    self.assertIn(struct.unpack_from('<H',a,8)[0],joint.rules.MINERALS|joint.gas.GAS_TYPES)
    self.assertEqual(a[:4],b[:4]);self.assertEqual(a[8:],b[8:])
   old_info=list(map(joint.rules.geometry._info,old));new_info=list(map(joint.rules.geometry._info,new))
   for point in old_info:
    if point[2] in joint.rules.HEADQUARTERS and joint.rules._resource_clear(point[:2],old_info):
     self.assertTrue(joint.rules._resource_clear(point[:2],new_info))
 def test_reported_402_regression_and_promised_amounts(self):
  row=next(r for r in self.rows if r['mission_id']==402);final=maps.CHK(Path(row['output']).read_bytes());old=maps.CHK(final.save());joint.undo(old,row['courtyard_resource_layout'])
  before=list(map(joint.rules.geometry._info,joint.rules.geometry._records(old)));after=list(map(joint.rules.geometry._info,joint.rules.geometry._records(final)))
  main=next(b for b in row['courtyard_resource_layout']['bases'] if 20 in b['gas_indices'])
  walk,_=joint.rules.geometry.load_terrain(final);worker=joint.rules._worker_terrain(walk);boxes,_=joint.rules.geometry.load_unit_geometry()
  self.assertFalse(joint.gas.direct_lane(main['anchor'],before[20][:2],before,20,worker,boxes))
  self.assertTrue(joint.gas.direct_lane(main['anchor'],after[20][:2],after,20,worker,boxes))
  raw=final.getsection('UNIT');self.assertEqual(struct.unpack_from('<I',raw,20*36+20)[0],7000)
  self.assertEqual(sum(struct.unpack_from('<I',raw,i*36+20)[0] for i in (7,8,9,10,11,12,13,14,15,16,19)),55000)
  self.assertEqual(sum(p[2:]==(61,1) for p in after),4)
 def test_tampering_cannot_be_undone_with_valid_receipt(self):
  row=next(r for r in self.rows if r['mission_id']==402);chk=maps.CHK(Path(row['output']).read_bytes());raw=bytearray(chk.getsection('UNIT'))
  struct.pack_into('<I',raw,20*36+20,6999);chk.setsection('UNIT',raw)
  with self.assertRaises(AssertionError):joint.undo(chk,row['courtyard_resource_layout'])
 def test_original_event_mineral_is_kept_at_exact_position(self):
  row=next(r for r in self.rows if r['mission_id']==608);final=maps.CHK(Path(row['output']).read_bytes());old=maps.CHK(final.save());joint.undo(old,row['courtyard_resource_layout'])
  self.assertEqual(joint.rules.geometry._records(final)[19],joint.rules.geometry._records(old)[19])
 def test_worker_can_harvest_another_edge_but_not_an_isolated_patch(self):
  boxes,_=joint.rules.geometry.load_unit_geometry();worker=joint.rules._worker_terrain([bytearray([1]*128) for _ in range(128)])
  anchor=dict(kind='existing_depot',center=[256,240],depot_type=106,owner=1)
  info=[(256,240,106,1),(448,240,176,11),(376,240,124,1)]
  bounds=joint.rules._bounds([p[:2] for p in info],worker,32);labels,_,_=joint.rules._components(worker,info,bounds,boxes)
  hq=joint.rules._perimeter_labels(info[0],labels,bounds,boxes)
  self.assertFalse(joint.rules._front_labels(info[1],(1,0),labels,bounds,boxes)&hq)
  ok,proof=joint.worker_access(info,[1],anchor,worker,boxes)
  self.assertTrue(ok);self.assertEqual(proof['other_reachable_edge_indices'],[1])
  isolated=[bytearray(128) for _ in range(128)]
  self.assertFalse(joint.worker_access(info,[1],anchor,isolated,boxes)[0])

if __name__=='__main__':unittest.main()
