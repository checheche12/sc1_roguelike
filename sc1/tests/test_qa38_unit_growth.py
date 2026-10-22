import copy,random,sqlite3,unittest
from sc1.campaign.runtime_catalog import load_catalog,encode_growth,validate_catalog,GrowthError
from sc1.campaign.unit_growth import specifications,identity,OLD_MANUALS
from sc1.campaign import rework_growth
from sc1.campaign.legendary_bundles import member_ids,compatible

class UnitGrowth(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.catalog=load_catalog(expected_version=2)

 def test_all_fields_roundtrip_without_changing_historical_words(self):
  c=self.catalog;new=c['talents'][437:560]
  self.assertEqual(len(new),123)
  self.assertEqual(sum(x.get('repeatable',False) for x in new),78)
  ranks={x['id']:4 for x in new if x['repeatable']}
  old=c['talents'][246] # existing manual ordinal8
  curse=c['curses'][19]
  baseline=encode_growth(c,[old['id']],{curse['id']:1000},{old['id']:3})
  words=encode_growth(c,[old['id']]+[x['id'] for x in new],{curse['id']:1000},{old['id']:3,**ranks})
  self.assertEqual(len(words),65)
  for i in list(range(1,14))+list(range(17,54))+list(range(61,65)):
   self.assertEqual(words[i],baseline[i],i)
  for x in new:
   f=x['wire_storage'];self.assertEqual((words[f['word']]>>f['shift'])&((1<<f['width'])-1),4 if x['repeatable'] else 1)
  for x in new:
   for rank in (1,2,3,4):
    w=encode_growth(c,[x['id']],{}, {x['id']:rank} if x['repeatable'] else {})
    f=x['wire_storage'];self.assertEqual(w[f['word']]>>f['shift'],rank if x['repeatable'] else 1)

 def test_corrupt_storage_and_collisions_are_rejected(self):
  c=copy.deepcopy(self.catalog);c['talents'][437]['wire_storage']['word']=61
  with self.assertRaises(GrowthError):validate_catalog(c,2)

 def test_legacy_caps_and_ammo_aliases_prevent_empty_rewards(self):
  from sc1.campaign import rank_policy
  c=self.catalog;old=c['talents'][238+29]
  marine=next(x for x in c['talents'][437:] if x['target_units']==[0,20] and x['effect']['unit_growth']['kind']=='attack')
  self.assertTrue(rank_policy.exhausted(marine,[old['id']],{old['id']:4},c))
  conn=sqlite3.connect(':memory:');owned=[old['id']]
  rework_growth.save_ranks(conn,101,{old['id']:3});rework_growth.acquire(conn,101,c,owned,marine['id'])
  self.assertTrue(rank_policy.exhausted(marine,owned,rework_growth.ranks(conn,101),c))
  carrier=next(x for x in c['talents'][437:] if x['target_units']==[72,82] and x['effect']['unit_growth']['kind']=='attack')
  ammo=next(x for x in c['talents'][437:] if x['target_units']==[73] and x['effect']['unit_growth']['kind']=='attack')
  owned=[carrier['id']];rework_growth.save_ranks(conn,101,{carrier['id']:2})
  rework_growth.acquire(conn,101,c,owned,ammo['id'])
  self.assertEqual(rework_growth.ranks(conn,101)[ammo['id']],3)
  conn.close()

 def test_both_members_are_awarded_and_ranked_for_each_tier(self):
  conn=sqlite3.connect(':memory:');c=self.catalog
  for rarity in ('common','uncommon','rare','epic'):
   pool=[x for x in c['talents'][437:] if x['race']=='terran' and x['rarity']==rarity and not x['effect'].get('offer_retired')]
   a=pool[0];b=next(x for x in pool if compatible(a,x));owned=[]
   option=dict(a,bundled_talent_ids=[a['id'],b['id']])
   rework_growth.acquire_option(conn,101,c,owned,option)
   self.assertEqual(owned,[a['id'],b['id']])
   self.assertEqual(member_ids(option,c),(a['id'],b['id']))
   if rarity=='common':
    for _ in range(3):rework_growth.acquire_option(conn,101,c,owned,option)
    before=copy.deepcopy(owned);ranks=rework_growth.ranks(conn,101)
    with self.assertRaises(GrowthError):rework_growth.acquire_option(conn,101,c,owned,option)
    self.assertEqual(before,owned);self.assertEqual(ranks,rework_growth.ranks(conn,101))
  conn.close()

 def test_future_unit_rewards_pair_same_rarity_and_omit_broad_manuals(self):
  seen=set();c=self.catalog
  for seed in range(100):
   for item in rework_growth.candidates(c,109,2,[],random.Random(seed)):
    self.assertNotIn(item.get('effect_ordinal'),OLD_MANUALS)
    if item.get('bundle_family') is not None:
     members=member_ids(item,c);self.assertEqual(len(members),3 if item['rarity']=='common' else 2)
     rows=[next(x for x in c['talents'] if x['id']==m) for m in members]
     for i,a in enumerate(rows):
      for b in rows[i+1:]:
       self.assertEqual(a['rarity'],b['rarity']);self.assertTrue(compatible(a,b))
     seen.add(item['rarity'])
  self.assertTrue(seen&{'uncommon','rare','epic'})

 def test_curse_start_and_sequences_match_requested_values(self):
  rows=self.catalog['curses']
  for slot,first,step in ((16,20,4),(18,10,2),(17,10,2),(19,15,1)):
   self.assertEqual(rows[slot]['effect']['first_increment_percent'],first)
   self.assertEqual(rows[slot]['effect']['increment_step_percent'],step)
  self.assertIn('+10/+22/+36%',rows[18]['description'])
  self.assertIn('+10/+22/+36%',rows[17]['description'])
  self.assertIn('+15/+31/+48%',rows[19]['description'])

if __name__=='__main__':unittest.main()
