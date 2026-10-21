"""QA52 midpoint guarantee, issued-offer preservation and random pairing."""
import copy,json,random,sqlite3,tempfile,unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from sc1.campaign import rework_growth,talent_campaign_policy as policy
from sc1.campaign.runtime_catalog import load_catalog,encode_growth
from sc1.campaign.legendary_bundles import member_ids,compatible
from sc1.manager.store import open_campaign_store,GrowthChoicesPending

class QA52Rewards(unittest.TestCase):
 def test_box_refresh_preserves_issued_rows_and_wire(self):
  catalog=load_catalog(expected_version=2);box=catalog['talents'][243]
  self.assertEqual(box['effect']['resources_per_curse'],25);self.assertEqual(box['effect']['qa_revision'],2026102052)
  prior=copy.deepcopy(catalog);prior['talents'][243]['effect'].update(qa_revision=2026101713,resources_per_curse=37.5)
  prior['talents'][243]['description']='Prior supply box37.5'
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'temporary.sqlite3';store=open_campaign_store(path)
   try:state=store.restore_growth_phase(101,2,1,phase_version=2)
   except GrowthChoicesPending as pending:state=pending.state
   while state['state']=='choosing':
    offer=state['offer'];state=store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],101,2,choice_kind=1 if offer['kind']=='talent' else 2,phase=1,phase_version=2)
   with closing(sqlite3.connect(path)) as conn:
    conn.execute('UPDATE growth_rework_catalog SET catalog_json=?',(json.dumps(prior),));conn.commit();before=list(conn.iterdump())
    rework_growth.enable(conn);refreshed=rework_growth.overlay(conn,load_catalog());after=list(conn.iterdump())
    without_catalog=lambda rows:[x for x in rows if not x.startswith('INSERT INTO "growth_rework_catalog"')]
    self.assertEqual(without_catalog(before),without_catalog(after));self.assertEqual(refreshed['talents'][243],box)
    for stacks in (0,1,55,255,256,1000):
     curses={catalog['curses'][16]['id']:stacks}
     self.assertEqual(encode_growth(prior,[box['id']],curses),encode_growth(catalog,[box['id']],curses))

 def test_six_campaigns_get_opening_and_midpoint_without_late_compensation(self):
  catalog=load_catalog(expected_version=2)
  for mission in (101,201,301,401,501,601):
   schedule=policy.campaign_schedule(mission);guarantees=[x for x in schedule if x.guaranteed_legendary]
   self.assertEqual([(x.ordinal,x.phase) for x in guarantees],[(1,1),(policy.logical_mission_count(mission)//2+1,1)])
   self.assertEqual(sum(x.category=='economy' for x in schedule),5)
  for mission in (306,405,505,515,606):
   choices=rework_growth.candidates(catalog,mission,1,[],random.Random(7))
   self.assertTrue(choices and all(x['rarity']=='legendary' for x in choices))
  for mission in (307,407):self.assertFalse(policy.reward_policy(mission,1).guaranteed_legendary)
  self.assertFalse(any(x.guaranteed_legendary for x in policy.campaign_schedule(611)))

 def test_previously_issued_midpoint_offer_is_preserved_without_late_compensation(self):
  catalog=load_catalog(expected_version=2)
  ordinary=next(x for x in catalog['talents'] if x.get('rework_revision')==5 and x['rarity']=='common' and x['race']=='terran' and x.get('repeatable') and not x.get('wire_storage'))
  for version in (1,2):
   with tempfile.TemporaryDirectory() as folder:
    path=Path(folder)/'temporary.sqlite3';store=open_campaign_store(path,curses_per_mission=0)
    with closing(sqlite3.connect(path)) as conn:
     conn.execute('UPDATE campaign SET completed_mask=?',((1<<5)-1,));conn.commit()
    def load():
     try:return store.restore_growth_phase(106,2,1,phase_version=version)
     except GrowthChoicesPending as pending:return pending.state
    with patch.object(rework_growth,'candidates',return_value=[ordinary]):old=copy.deepcopy(load()['offer'])
    store=open_campaign_store(path)
    with patch.object(rework_growth,'candidates',side_effect=AssertionError('No redraw')):
     self.assertEqual(load()['offer'],old)
    result=store.choose_growth_phase_slot(old['offer_id'],1,old['revision'],106,2,choice_kind=1,phase=1,phase_version=version)
    while result.get('offer'):
     curse=result['offer'];self.assertEqual(curse['kind'],'curse')
     result=store.choose_growth_phase_slot(curse['offer_id'],1,curse['revision'],106,2,choice_kind=2,phase=1,phase_version=version)
    words=result['growth_words'];store=open_campaign_store(path)
    with patch.object(rework_growth,'candidates',side_effect=AssertionError('No late grant')):
     self.assertEqual(load()['growth_words'],words)
    self.assertTrue(words[1+ordinary['bit_index']//32] & (1<<(ordinary['bit_index']%32)))
    for item in catalog['talents']:
     if item['rarity']=='legendary' and not item.get('wire_storage'):
      bit=item['bit_index'];self.assertFalse(words[1+bit//32] & (1<<(bit%32)))

 def test_dragoons_pair_with_multiple_manual_families(self):
  catalog=load_catalog(expected_version=2);by_id={x['id']:x for x in catalog['talents']};partners=set();pairs=set()
  for seed in range(160):
   for option in rework_growth.candidates(catalog,301,3,[],random.Random(seed)):
    ids=option.get('bundled_talent_ids')
    if not ids:continue
    members=[by_id[i] for i in member_ids(option,catalog)]
    for index,left in enumerate(members):
     for right in members[index+1:]:self.assertTrue(compatible(left,right))
    pairs.add(tuple(sorted(ids)))
    if any(x['name']=='드라군 화력 교범' for x in members):partners.update(x['name'] for x in members if x['name']!='드라군 화력 교범')
  self.assertGreater(len(partners),1);self.assertGreater(len(pairs),20)
