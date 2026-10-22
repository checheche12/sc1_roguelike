import hashlib,json,struct,unittest
from pathlib import Path
from sc1.native_campaign.build_plain_chk import CHK,strings
from sc1.campaign.build_effect_lab import MARKER
from sc1.build_portable import runtime_sources

ROOT=Path(__file__).resolve().parents[2]
class EffectLab(unittest.TestCase):
 def test_large_ordinary_map_and_all_effect_checklist(self):
  base=ROOT/'sc1/effect_lab';c=CHK((base/'scenario.chk').read_bytes());proof=json.loads((base/'build_evidence.json').read_text())
  self.assertEqual(struct.unpack('<HH',c.getsection('DIM ')),(256,256));self.assertIn(MARKER,strings(c.getsection('STR ')))
  self.assertEqual(len(c.getsection('MTXM')),256*256*2);self.assertEqual(len(c.getsection('MASK')),256*256)
  self.assertEqual(c.getsection('OWNR')[0],6);self.assertEqual(c.getsection('OWNR')[6],5)
  self.assertGreater(len(c.getsection('UNIT'))//36,120);self.assertEqual(len(c.getsection('TRIG')),2400)
  self.assertEqual(proof['map_sha256'],hashlib.sha256((base/'SC1_Effect_Lab.scx').read_bytes()).hexdigest())
  self.assertTrue(proof['terrain_walkability_verified']);self.assertFalse(proof['live_gameplay_verified'])
  page=(base/'Effect_Checklist.html').read_text(encoding='utf8');self.assertEqual(page.count('<tr data-search='),611)
  for text in ('-t 343 1','-t 560 1','-c 49 1','-case','localStorage'):self.assertIn(text,page)
 def test_lab_assets_and_launcher_are_pinned_in_portable_closure(self):
  names={p.relative_to(ROOT).as_posix() for p in runtime_sources(ROOT)}
  for name in ('SC1_Effect_Lab.scx','Effect_Checklist.html','build_evidence.json'):self.assertIn('sc1/effect_lab/'+name,names)
  self.assertIn('sc1/manager/effect_lab_launch.py',names)

if __name__=='__main__':unittest.main()
