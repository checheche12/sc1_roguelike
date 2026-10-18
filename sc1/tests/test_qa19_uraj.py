"""Uraj's original landing executes once with a viable opening economy."""
import json,struct,unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as maps,scripted_openings as opening
from sc1.native_campaign import package_all_campaigns as package,mission_balance
from sc1.campaign.missions import load_missions

class UrajTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mission=next(m for m in load_missions() if m['mission_id']==404)
  cls.source=Path(cls.mission['source']).read_bytes()
  cls.receipt=json.loads(maps.RECEIPT.read_text(encoding='utf8'))
  cls.row=next(r for r in cls.receipt['maps'] if r['mission_id']==404)
 def test_landing_ten_probes_and_one_time_additive_resources(self):
  chk=maps.CHK(self.source);before=chk.getsection('TRIG');report=opening.apply(chk,self.mission)
  after=chk.getsection('TRIG');expected=bytearray(before)
  for c in report['changes']:
   pos=c['trigger']*2400+320+c['action']*32
   self.assertEqual(before[pos:pos+32],bytes.fromhex(c['before']))
   expected[pos:pos+32]=bytes.fromhex(c['after'])
  self.assertEqual(after,bytes(expected))
  trigger=maps.triggers(chk)[15]
  self.assertEqual(sum(a[27] for _,a in maps.actions(trigger) if a[26]==44 and struct.unpack_from('<H',a,24)[0]==64),10)
  resources=[(struct.unpack_from('<H',a,24)[0],struct.unpack_from('<I',a,20)[0],a[27]) for _,a in maps.actions(trigger) if a[26]==26]
  self.assertEqual(resources,[(0,1500,8),(1,500,8)])
  self.assertFalse(any(a[26]==3 for _,a in maps.actions(trigger))) # No Preserve Trigger/repeated gifts.
  for tag,data in maps.CHK(self.source).sections.items():
   if tag!=b'TRIG':self.assertEqual(chk.sections[tag],data)
 def test_unexpected_landing_is_rejected_and_other_maps_unchanged(self):
  chk=maps.CHK(self.source);raw=bytearray(chk.getsection('TRIG'));raw[15*2400+320+4*32+27]=2;chk.setsection('TRIG',bytes(raw))
  with self.assertRaises(AssertionError):opening.apply(chk,self.mission)
  control=maps.CHK(self.source);self.assertIsNone(opening.apply(control,dict(mission_id=403)))
  self.assertEqual(control.save(),self.source)
 def test_shipped_map_has_no_added_garrison_and_keeps_landing_patch(self):
  self.assertEqual(self.row['difficulty']['static_added'],0)
  self.assertEqual(self.row['mission_balance']['garrison_added'],0)
  self.assertEqual(mission_balance.GARRISONS[404],0)
  self.assertNotIn(5,self.row['difficulty']['hostile_owners'])
  output=maps.CHK(Path(self.row['output']).read_bytes())
  package.verify_checkpoint_layout(maps.CHK(self.source),output,self.mission,self.row)
  probes=[a for _,a in maps.actions(maps.triggers(output)[15]) if a[26]==44 and struct.unpack_from('<H',a,24)[0]==64]
  self.assertEqual(sum(a[27] for a in probes),10)
 def test_receipt_cannot_hide_a_changed_gift(self):
  output=maps.CHK(Path(self.row['output']).read_bytes());raw=bytearray(output.getsection('TRIG'))
  struct.pack_into('<I',raw,15*2400+320+15*32+20,999999);output.setsection('TRIG',bytes(raw))
  with self.assertRaises(ValueError):package.verify_checkpoint_layout(maps.CHK(self.source),output,self.mission,self.row)

if __name__=='__main__':unittest.main()
