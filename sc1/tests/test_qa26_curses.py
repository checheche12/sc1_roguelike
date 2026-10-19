import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from contextlib import closing
from sc1.campaign import rework_growth,progression,talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import load_catalog,encode_growth,GrowthError
from sc1.campaign.curse_balance import REAR_ID
from sc1.manager.store import CampaignStore,GrowthChoicesPending

class QA26Curses(unittest.TestCase):
 def setUp(self):self.catalog=load_catalog(expected_version=2)

 def test_existing_pinned_catalog_gains_unlimited_caps_without_reindexing(self):
  old=copy.deepcopy(self.catalog)
  for item in old['curses'][15:]:
   item['effect']['qa_revision']=20261016
   if item['byte_index'] in (16,17,18):item['max_stacks']=3
   item.pop('choice_max_stacks',None)
  with tempfile.TemporaryDirectory(prefix='sc1-qa26-pin-') as tmp,closing(sqlite3.connect(':memory:')) as conn:
   path=Path(tmp)/'old.json';path.write_text(json.dumps(old,ensure_ascii=False),encoding='utf8')
   rework_growth.enable(conn,path);rework_growth.enable(conn)
   updated=rework_growth.overlay(conn,load_catalog())
   for slot in (16,17,18):
    item=next(x for x in updated['curses'] if x['byte_index']==slot)
    self.assertEqual(item['id'],old['curses'][slot]['id'])
    self.assertEqual(item['max_stacks'],0xffffffff)
   self.assertEqual(updated['curses'][15]['choice_max_stacks'],3)

 def test_extended_counts_do_not_corrupt_neighbouring_curses(self):
  ids={x['byte_index']:x['id'] for x in self.catalog['curses']}
  for count in (1,3,4,254,255,256,1000,0xffffffff):
   counts={ids[16]:count,ids[17]:count,ids[18]:count,ids[19]:2,REAR_ID:7}
   before=copy.deepcopy(counts);words=encode_growth(self.catalog,[],counts)
   self.assertEqual(counts,before)
   for slot in (16,17,18):
    self.assertEqual(words[80-slot],count)
    self.assertEqual((words[17+slot//4]>>(8*(slot%4)))&255,min(count,255))
   self.assertEqual((words[21]>>24)&255,2)
   self.assertEqual((words[23]>>8)&255,7)
  with self.assertRaises(GrowthError):encode_growth(self.catalog,[],{ids[16]:0x100000000})

 def test_old_raid_counts_remain_readable_but_new_selection_stops_at_three(self):
  raid=self.catalog['curses'][15];self.assertEqual(raid['choice_max_stacks'],3)
  self.assertEqual(raid['effect']['units_sequence'],[2,6,10])
  encode_growth(self.catalog,[],{raid['id']:4})
  self.assertFalse(rework_growth.curse_eligible(self.catalog['curses'][25],101))

 def test_legendary_unlocks_at_campaign_midpoint_for_every_branch(self):
  for first in (101,201,301,401,501,601):
   middle=(policy.logical_mission_count(first)+1)//2
   for mission in progression.campaign_missions(first):
    ordinal=progression.metadata(mission)['ordinal']
    self.assertEqual(rework_growth.curse_tier(mission,2)=='legendary',ordinal>=middle)
  self.assertEqual(rework_growth.curse_tier(105,2),'legendary')

 def test_pending_retired_curse_reissued_and_archived_in_both_protocols(self):
  for phase_version in (1,2):
   with self.subTest(phase_version=phase_version),tempfile.TemporaryDirectory(prefix='sc1-qa26-disposable-') as tmp:
    path=Path(tmp)/'synthetic.sqlite3';store=CampaignStore(path,new_profile='original')
    def load():
     try:return store.restore_growth_phase(101,2,1,phase_version=phase_version)
     except GrowthChoicesPending as pending:return pending.state
    state=load()
    while state['offer']['kind']!='curse':
     offer=state['offer'];state=store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],101,2,choice_kind=1,phase=1,phase_version=phase_version)
    offer=state['offer'];oldid=offer['offer_id'];saved=json.dumps([self.catalog['curses'][25]],ensure_ascii=False)
    with closing(sqlite3.connect(path)) as conn,conn:
     conn.execute('UPDATE growth_offers SET candidates_json=? WHERE offer_id=?',(saved,oldid))
    fresh=load();self.assertNotEqual(fresh['offer']['offer_id'],oldid)
    self.assertNotIn(REAR_ID,[x['id'] for x in fresh['offer']['candidates']])
    with closing(sqlite3.connect(path)) as conn:
     self.assertEqual(conn.execute('SELECT candidates_json FROM growth_offer_retirement_history WHERE offer_id=?',(oldid,)).fetchone()[0],saved)

if __name__=='__main__':unittest.main()
