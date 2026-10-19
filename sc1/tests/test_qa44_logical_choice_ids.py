"""Logical choice IDs beyond the512 physical ownership bits stay selectable."""
import copy,random,struct,unittest,uuid
from sc1.bridge.protocol import Request,BridgeError,choice_payload
from sc1.campaign.runtime_catalog import load_catalog
from sc1.campaign.rework_growth import candidates
from sc1.campaign.legendary_bundles import compatible,pair_options

class LogicalChoiceIds(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.catalog=load_catalog(expected_version=2)
 def request(self):return Request(301,1,1,2,4,'01'*16,0,0,growth_version=2,growth_applied=2,choice_version=1,phase_version=2,phase=3)
 def state(self,rows):
  return dict(state='choosing',requested_phase=3,completed_phase=2,total_phases=4,
   phase_pending={'talent':1,'curse':1},curses=[],offer=dict(offer_id=str(uuid.uuid4()),kind='talent',revision=1,candidates=rows))
 def test_protoss_midpoint_real_draw_reaches_wire(self):
  rows=candidates(self.catalog,301,2,[],random.Random(0))
  self.assertTrue(any(x['bit_index']>=512 for x in rows))
  words=struct.unpack('<95I',choice_payload(self.request(),self.state(rows)))
  self.assertEqual(list(words[14:18]),[x['bit_index']+1 for x in rows])
  self.assertEqual(words[35],0x424e4431)
 def test_every_new_logical_id_is_valid_and_overflow_is_rejected(self):
  for index in range(511,len(self.catalog['talents'])):
   row=self.catalog['talents'][index]
   words=struct.unpack('<95I',choice_payload(self.request(),self.state([row])))
   self.assertEqual(words[14],index+1)
  row=copy.deepcopy(self.catalog['talents'][-1]);row['bit_index']=len(self.catalog['talents'])
  with self.assertRaisesRegex(BridgeError,'not supported'):choice_payload(self.request(),self.state([row]))
 def test_bundle_partner_above512_keeps_numeric_identity(self):
  pool=[x for x in self.catalog['talents'] if x.get('rework_revision')==5 and x.get('bundle_family') is not None]
  high=next(x for x in pool if x['bit_index']>=512 and not x['effect'].get('offer_retired'))
  low=next(x for x in pool if x['bit_index']<512 and compatible(x,high))
  row=pair_options([low],[high],random.Random(0))[0]
  words=struct.unpack('<95I',choice_payload(self.request(),self.state([row])))
  self.assertEqual(words[14],low['bit_index']+1);self.assertEqual(words[31],high['bit_index']+1)

if __name__=='__main__':unittest.main()
