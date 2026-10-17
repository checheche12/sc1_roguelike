from pathlib import Path
import hashlib,json,struct,unittest
from sc1.native_campaign import build_all_campaigns as maps
from sc1.native_campaign import package_all_campaigns as package
from sc1.campaign.missions import load_missions

class CheckpointMapTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.receipt=json.loads((maps.ROOT/'all_campaign_maps_evidence.json').read_text(encoding='utf8'))
 def test_all_assets_reserve_an_unused_quarter_switch_and_keep_ending_gates(self):
  self.assertEqual(len(self.receipt['maps']),63)
  for row in self.receipt['maps']:
   raw=Path(row['output']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
   chk=maps.CHK(raw);original=maps.CHK(Path(row['source']).read_bytes());audit=maps.audit_switches(original)
   self.assertNotIn(251,audit['original_used_ids']);self.assertIn(251,audit['reserved_ids'])
   ts=maps.triggers(chk);progress=row['progression'];quarter=ts[progress['quarter_trigger_index']]
   self.assertEqual([maps.cf(c) for _,c in maps.conditions(quarter)],progress['quarter']['conditions'])
   self.assertEqual([a for _,a in maps.actions(quarter)],[maps.setswitch(251)])
   for route in progress['routes']:
    ending=ts[route['ending_trigger_index']]
    self.assertIn(maps.switch_condition(242),[c for _,c in maps.conditions(ending)])
    self.assertIn(maps.switch_condition(243),[c for _,c in maps.conditions(ending)])
   self.assertIn('_V4_PH2_',row['fingerprint'])
 def test_gated_countdown_does_not_award_a_quarter_before_mining_starts(self):
  row=next(r for r in self.receipt['maps'] if r['mission_id']==209)
  chk=maps.CHK(Path(row['output']).read_bytes());quarter=maps.triggers(chk)[row['progression']['quarter_trigger_index']]
  self.assertIn(maps.switch_condition(0),[c for _,c in maps.conditions(quarter)])
  countdown=next(maps.cf(c)['amount'] for _,c in maps.conditions(quarter) if c[15]==1)
  self.assertEqual(countdown,450)
 def test_exact_trigger_replay_rejects_a_forged_quarter_action(self):
  missions={m['mission_id']:m for m in load_missions()}
  for row in self.receipt['maps']:
   source=maps.CHK(Path(row['source']).read_bytes());output=maps.CHK(Path(row['output']).read_bytes())
   package.verify_checkpoint_layout(source,output,missions[row['mission_id']],row)
  row=self.receipt['maps'][0];source=maps.CHK(Path(row['source']).read_bytes());output=maps.CHK(Path(row['output']).read_bytes())
  raw=bytearray(output.getsection('TRIG'));offset=row['progression']['quarter_trigger_index']*2400+320+20
  raw[offset]^=1;output.setsection('TRIG',bytes(raw))
  with self.assertRaises(ValueError):package.verify_checkpoint_layout(source,output,missions[row['mission_id']],row)

if __name__=='__main__':unittest.main()
