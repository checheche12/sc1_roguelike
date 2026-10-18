"""Execute shipped landing resource actions using independently decoded CHK semantics.

ChkDraft's Chk::Trigger::ValueModifier and eudplib's TrgModifier both define
SetTo=7, Add=8 and Subtract=9. The interpreter does not import the patch's
operation value, so a subtraction accidentally labelled 'Add' fails here.
"""
import json,struct,unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as maps

def execute_resources(trigger,resources,owner=1):
 result=list(resources)
 for _,action in maps.actions(trigger):
  if action[26]!=26:continue
  player=struct.unpack_from('<I',action,16)[0]
  if player not in (owner,13):continue
  resource=struct.unpack_from('<H',action,24)[0]
  amount=struct.unpack_from('<I',action,20)[0]
  for index in ([0,1] if resource==2 else [resource]):
   if action[27]==7:result[index]=amount
   elif action[27]==8:result[index]+=amount
   elif action[27]==9:result[index]=max(0,result[index]-amount)
   else:raise ValueError('Unknown CHK resource operation')
 return tuple(result)

class LandingResourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  row=next(r for r in json.loads(maps.RECEIPT.read_text(encoding='utf8'))['maps'] if r['mission_id']==404)
  cls.triggers=maps.triggers(maps.CHK(Path(row['output']).read_bytes()))
 def test_shipped_landing_adds_to_zero_and_retains_existing_resources(self):
  for initial in ((0,0),(200,0),(2600,700)):
   self.assertEqual(execute_resources(self.triggers[15],initial),(initial[0]+1500,initial[1]+500))
 def test_initialization_then_landing_funds_a_nexus_and_keeps_gas(self):
  resources=execute_resources(self.triggers[5],(0,0))
  self.assertEqual(resources,(200,0))
  resources=execute_resources(self.triggers[15],resources)
  self.assertEqual(resources,(1700,500))
  self.assertEqual((resources[0]-400,resources[1]),(1300,500))
 def test_recreates_qa19_zero_resource_failure(self):
  bad=bytearray(self.triggers[15])
  for action in (15,16):bad[320+action*32+27]=9
  self.assertEqual(execute_resources(bytes(bad),(200,0)),(0,0))
  self.assertNotEqual(execute_resources(self.triggers[15],(200,0)),(0,0))

if __name__=='__main__':unittest.main()
