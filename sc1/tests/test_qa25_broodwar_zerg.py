"""Built Vile Disruption actors/upgrades and the actual Reign of Fire rescue."""
from pathlib import Path
import json,struct,tempfile,unittest
from sc1.native_campaign import build_all_campaigns as maps,package_all_campaigns as package
from sc1.manager.store import CampaignStore,GrowthChoicesPending


class BroodWarZergOpeningTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.metadata={m['mission_id']:m for m in json.loads(maps.MISSION_JSON.read_text(encoding='utf8'))['missions']}
  cls.rows={m['mission_id']:m for m in json.loads(maps.RECEIPT.read_text(encoding='utf8'))['maps']}
 def scenario(self,identity):
  r=self.rows[identity]
  return maps.CHK(Path(r['source']).read_bytes()),maps.CHK(Path(r['output']).read_bytes()),r
 def test_exploration_gets_six_upgrades_and_no_extra_actors_or_waves(self):
  source,output,row=self.scenario(601)
  self.assertTrue(self.metadata[601]['no_production'])
  self.assertEqual(set(self.metadata[601]['available_unit_ids']),{37,38,45,46,53,101})
  self.assertEqual((row['difficulty']['static_added'],row['mission_balance']['garrison_added']),(0,0))
  before,after=maps.units(source),maps.units(output)
  self.assertEqual(len(after),len(before))
  for old,new in zip(before,after):
   if maps.unit_info(old)[2] not in (176,177,178,188):self.assertEqual(old,new)
  self.assertEqual(row['unlock']['no_production_combat_upgrade_level'],6)
  for tag,n in (('UPGR',46),('PUPx',61)):
   if tag.encode() not in output.sections:continue
   data=output.getsection(tag)
   for uid in maps.COMBAT_UPGRADES:
    self.assertEqual(data[(26+3)*n+uid],0)
    self.assertGreaterEqual(data[(12+3)*n+uid],6)
  profile=next(p for p in json.loads((maps.ROOT/'rework_wave_profiles.json').read_text(encoding='utf8'))['profiles'] if p['mission_id']==601)
  self.assertFalse(profile['enabled'])
 def test_final_unprotection_and_clear_condition_keep_original_actor_set(self):
  source,output,row=self.scenario(601)
  old,new=maps.triggers(source),maps.triggers(output)
  for index in (51,54,55,57,58):
   self.assertEqual(old[index],new[row['progression']['original_trigger_indices'][index]])
  ending=row['progression']['routes'][0]
  self.assertEqual(ending['source_trigger'],59)
  self.assertEqual(new[ending['ending_trigger_index']][320:],old[59][320:])
  package.verify_checkpoint_layout(source,output,self.metadata[601],row)
 def test_reign_of_fire_adds_eight_only_at_first_drone_rescue(self):
  source,output,row=self.scenario(602)
  self.assertFalse(self.metadata[602]['no_production'])
  original=maps.triggers(source)[67];gift=row['progression']['opening_workers']
  ts=maps.triggers(output);t=ts[gift['gift_trigger_index']]
  self.assertEqual([c for _,c in maps.conditions(t)],[c for _,c in maps.conditions(original)])
  self.assertEqual([i for i,v in enumerate(t[2372:2399]) if v],[3])
  actions=[struct.unpack('<IIIIIIHBBBBH',a) for _,a in maps.actions(t)]
  self.assertEqual(actions,[(105,0,0,0,3,0,41,44,8,20,0,0)])
  self.assertFalse(any(a[7]==3 for a in actions))
  self.assertEqual(ts[row['progression']['original_trigger_indices'][67]],original)
  workers=[r for r in maps.units(source) if maps.unit_info(r)[2]==41]
  self.assertEqual(len(workers),2)
  self.assertTrue(all(maps.unit_info(r)[3]==5 for r in workers))
  self.assertEqual(gift['total_drones'],10)
  package.verify_checkpoint_layout(source,output,self.metadata[602],row)
 def test_rescue_gift_tampering_is_rejected_by_package(self):
  source,output,row=self.scenario(602)
  raw=bytearray(output.getsection('TRIG'));ix=row['progression']['opening_workers']['gift_trigger_index']
  raw[ix*2400+320+27]=80;output.setsection('TRIG',bytes(raw))
  with self.assertRaises(ValueError):package.verify_checkpoint_layout(source,output,self.metadata[602],row)
 def test_current_catalog_opens_and_confirms_first_zerg_exploration_offer(self):
  with tempfile.TemporaryDirectory(prefix='sc1-qa25-disposable-') as tmp:
   store=CampaignStore(Path(tmp)/'synthetic.sqlite3',new_profile='original')
   with self.assertRaises(GrowthChoicesPending) as pending:
    store.restore_growth_phase(601,2,1,phase_version=2)
   state=pending.exception.state;offer=state['offer']
   self.assertEqual((state['mission'],offer['kind'],len(offer['candidates'])),(601,'talent',4))
   self.assertTrue(all(x.get('category')!='economy' for x in offer['candidates']))
   while state.get('state')=='choosing':
    offer=state['offer']
    state=store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],601,2,
     choice_kind=1 if offer['kind']=='talent' else 2,phase=1,phase_version=2)
   restored=store.restore_growth_phase(601,2,1,phase_version=2)
   self.assertEqual(restored['growth_words'],state['growth_words'])


if __name__=='__main__':unittest.main()
