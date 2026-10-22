import copy,json,random,sqlite3,unittest
from unittest.mock import patch
from sc1.campaign.runtime_catalog import load_catalog,encode_growth,validate_catalog,GrowthError
from sc1.campaign.unit_growth import specifications,identity,OLD_MANUALS
from sc1.campaign import rework_growth
from sc1.campaign.legendary_bundles import member_ids,compatible,pair_options,paired_unit

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
   for item in rework_growth.candidates(c,109,3,[],random.Random(seed)):
    self.assertNotEqual(item['category'],'economy')
    self.assertNotIn(item.get('effect_ordinal'),OLD_MANUALS)
    if paired_unit(item):
     members=member_ids(item,c);self.assertEqual(len(members),3 if item['rarity']=='common' else 2)
     rows=[next(x for x in c['talents'] if x['id']==m) for m in members]
     for i,a in enumerate(rows):
      for b in rows[i+1:]:
       self.assertEqual(a['rarity'],b['rarity']);self.assertTrue(compatible(a,b))
     seen.add(item['rarity'])
  self.assertTrue(seen&{'uncommon','rare','epic'})

 def test_every_economic_reward_is_single_and_never_a_new_combat_partner(self):
  from sc1.campaign.rework_growth import retired,unit_offer_removed
  c=self.catalog
  pool=[x for x in c['talents'] if x.get('rework_revision')==5 and not retired(x)
        and not unit_offer_removed(x) and not x['effect'].get('offer_retired')]
  economic=[x for x in pool if x['category']=='economy']
  self.assertEqual(len(economic),24)
  for item in economic:
   self.assertFalse(paired_unit(item),item['name'])
   option=pair_options([item],pool,random.Random(73))[0]
   self.assertEqual(member_ids(option,c),(item['id'],))
   self.assertNotIn('bundled_talent_ids',option)
   for other in pool:
    self.assertFalse(compatible(item,other),(item['name'],other['name']))
    self.assertFalse(compatible(other,item),(other['name'],item['name']))

 def test_all_campaign_economic_payouts_and_combat_rewards_keep_their_category(self):
  from sc1.campaign import progression,talent_campaign_policy as policy
  c=self.catalog;by={x['id']:x for x in c['talents']};seen=set()
  with patch.object(policy,'rolled_rarity',return_value='rare'):
   for first in (101,201,301,401,501,601):
    for mission in progression.campaign_missions(first):
     economic=policy.reward_policy(mission,2).category=='economy'
     for seed in range(3):
      for option in rework_growth.candidates(c,mission,2,[],random.Random(seed)):
       ids=member_ids(option,c)
       self.assertTrue(all((by[x]['category']=='economy')==economic for x in ids))
       if economic:
        self.assertEqual(len(ids),1);self.assertNotIn('bundled_talent_ids',option)
        seen.add(progression.metadata(mission)['campaign_id'])
  self.assertEqual(seen,{1,2,3,4,5,6})

 def test_previously_issued_economic_pairs_remain_readable_but_cannot_be_redrawn(self):
  c=self.catalog
  for index in (258,260):
   item=c['talents'][index]
   other=next(x for x in c['talents'] if x['rarity']==item['rarity'] and compatible(item,x,historical=True))
   saved=dict(item,bundled_talent_ids=[item['id'],other['id']])
   self.assertEqual(member_ids(saved,c),(item['id'],other['id']))
   self.assertFalse(compatible(item,other))
   self.assertNotIn('bundled_talent_ids',pair_options([item],[item,other],random.Random(0))[0])
   with sqlite3.connect(':memory:') as conn:
    owned=[];rework_growth.acquire_option(conn,301,c,owned,saved)
    self.assertEqual(owned,[item['id'],other['id']])

 def test_auxiliary_unit_combat_rewards_pair_with_a_different_combat_family(self):
  c=self.catalog;expected={284:1,355:72,374:72,414:72,419:81}
  for index,family in expected.items():
   item=c['talents'][index]
   self.assertNotEqual(item['category'],'economy');self.assertTrue(paired_unit(item))
   if index==355:
    from sc1.campaign.talent_balance import power_quarters
    self.assertEqual(power_quarters(item),4)
   self.assertEqual(item['bundle_family'],family)
   pool=[x for x in c['talents'] if x['race']==item['race'] and x['rarity']==item['rarity']
         and paired_unit(x) and not x['effect'].get('offer_retired')]
   for other in pool:
    if other.get('bundle_family') in ({72,81} if index==355 else {family}):self.assertFalse(compatible(item,other))
   for seed in range(5):
    option=pair_options([item],pool,random.Random(seed))[0]
    ids=member_ids(option,c);self.assertEqual(len(ids),2)
    with sqlite3.connect(':memory:') as conn:
     owned=[];rework_growth.acquire_option(conn,301,c,owned,option)
     self.assertEqual(owned,list(ids))
     self.assertTrue(encode_growth(c,owned,{})[1+index//32]&(1<<(index%32)))

 def test_ammunition_pin_upgrade_preserves_previously_issued_single(self):
  c=self.catalog;old=copy.deepcopy(c);ammo=old['talents'][355]
  ammo['category']='economy'
  for field in ('bundle_family','bundle_families'):ammo.pop(field,None)
  ammo['effect']['qa_revision']=2026101610
  issued=copy.deepcopy(ammo)
  with sqlite3.connect(':memory:') as conn:
   conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
   conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old,ensure_ascii=False),))
   rework_growth.enable(conn)
   refreshed=rework_growth.overlay(conn,old)
   future=refreshed['talents'][355]
   self.assertEqual(future['category'],'combat')
   self.assertTrue(paired_unit(future));self.assertEqual(set(future['bundle_families']),{72,81})
   self.assertEqual(future['source_description'],issued['source_description'])
   self.assertEqual(member_ids(issued,refreshed),(issued['id'],))
   owned=[];rework_growth.acquire_option(conn,301,refreshed,owned,issued)
   self.assertEqual(owned,[issued['id']])

 def test_shared_melee_mastery_pairs_with_each_faction_and_awards_both(self):
  c=self.catalog;melee=c['talents'][388]
  self.assertTrue(paired_unit(melee));self.assertEqual(melee['rarity'],'uncommon')
  self.assertEqual(set(melee['bundle_families']),{10,37,39,40,61,65})
  faction_partners=[]
  for race in ('terran','zerg','protoss'):
   pool=[x for x in c['talents'] if x['race'] in (race,'shared') and x['rarity']=='uncommon'
         and paired_unit(x) and not x['effect'].get('offer_retired')]
   for other in pool:
    if other.get('bundle_family') in melee['bundle_families']:
     self.assertFalse(compatible(melee,other));self.assertFalse(compatible(other,melee))
   for seed in range(10):
    option=pair_options([melee],pool,random.Random(seed))[0]
    ids=member_ids(option,c);self.assertEqual(len(ids),2)
    other=next(x for x in pool if x['id']==ids[1])
    self.assertEqual(other['race'],race);self.assertNotEqual(other['category'],'economy')
    self.assertFalse(set(other['target_units'])&set(melee['target_units']))
    self.assertTrue(compatible(other,melee));faction_partners.append(other)
    with sqlite3.connect(':memory:') as conn:
     owned=[];rework_growth.acquire_option(conn,301,c,owned,option)
     self.assertEqual(owned,list(ids));self.assertTrue(encode_growth(c,owned,{})[1+388//32]&(1<<(388%32)))
  self.assertFalse(compatible(faction_partners[0],faction_partners[10]))

 def test_shared_melee_mastery_draws_in_all_six_campaigns(self):
  from sc1.campaign import progression,talent_campaign_policy as policy
  c=self.catalog;melee=c['talents'][388];by={x['id']:x for x in c['talents']}
  with patch.object(policy,'rolled_rarity',return_value='uncommon'):
   for mission in (109,209,309,407,507,609):
    found=False;race=progression.metadata(mission)['race']
    for seed in range(30):
     for option in rework_growth.candidates(c,mission,3,[],random.Random(seed)):
      ids=member_ids(option,c)
      if melee['id'] in ids:
       found=True;self.assertEqual(len(ids),2)
       partner=next(by[x] for x in ids if x!=melee['id'])
       self.assertEqual(partner['race'],race);self.assertEqual(partner['rarity'],'uncommon')
    self.assertTrue(found,mission)

 def test_shared_melee_mastery_pin_upgrade_preserves_issued_single(self):
  c=self.catalog;old=copy.deepcopy(c);item=old['talents'][388]
  for field in ('bundle_family','bundle_families'):item.pop(field,None)
  item['effect']['qa_revision']=2026101610;issued=copy.deepcopy(item)
  with sqlite3.connect(':memory:') as conn:
   conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
   conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old,ensure_ascii=False),))
   rework_growth.enable(conn);refreshed=rework_growth.overlay(conn,old)
   self.assertTrue(paired_unit(refreshed['talents'][388]))
   self.assertEqual(set(refreshed['talents'][388]['bundle_families']),{10,37,39,40,61,65})
   self.assertEqual(member_ids(issued,refreshed),(issued['id'],))
   self.assertEqual(refreshed['talents'][388]['description'],issued['description'])

 def test_curse_start_and_sequences_match_requested_values(self):
  rows=self.catalog['curses']
  for slot,first,step in ((16,20,4),(18,10,2),(17,10,2),(19,15,1)):
   self.assertEqual(rows[slot]['effect']['first_increment_percent'],first)
   self.assertEqual(rows[slot]['effect']['increment_step_percent'],step)
  self.assertIn('+10/+22/+36%',rows[18]['description'])
  self.assertIn('+10/+22/+36%',rows[17]['description'])
  self.assertIn('+15/+31/+48%',rows[19]['description'])

if __name__=='__main__':unittest.main()
