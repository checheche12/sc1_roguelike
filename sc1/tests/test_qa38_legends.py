import copy,json,random,sqlite3,tempfile,unittest
from pathlib import Path
from sc1.campaign import rework_growth
from sc1.campaign.runtime_catalog import load_catalog,encode_growth
from sc1.campaign.legendary_expansion import UNIT_FAMILIES,PROMOTIONS,REVISION,identity,RADIATION_ORDINAL
from sc1.campaign.legendary_bundles import unit_legendary,compatible,member_ids
from sc1.campaign.talent_balance import power_quarters

class QA38Legends(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=load_catalog(expected_version=2)
  cls.by_ord={x['effect_ordinal']:x for x in cls.catalog['talents'] if x.get('rework_revision')==5}

 def test_every_playable_family_has_a_nonshared_legend(self):
  legends=[x for x in self.catalog['talents'] if unit_legendary(x)]
  self.assertEqual(len(legends),38)
  self.assertEqual(sum(len(x) for x in UNIT_FAMILIES.values()),44)
  for race,rows in UNIT_FAMILIES.items():
   for name,ids in rows:
    from sc1.campaign.talent_retirement import NONCOMBAT_FAMILIES
    if ids[0] in NONCOMBAT_FAMILIES:continue
    self.assertTrue(any(x['race']==race and set(ids)&set(x['target_units']) for x in legends),name)

 def test_promotions_have_weaker_replacements_without_implicit_power_jump(self):
  for ordinal in PROMOTIONS:
   parent=self.by_ord[ordinal];self.assertEqual(parent['rarity'],'epic' if ordinal in (136,138,140) else 'legendary')
   self.assertEqual(power_quarters(parent),10)
   replacements=[x for x in self.catalog['talents'] if x['effect'].get('replaces_epic_id')==parent['id']]
   self.assertEqual(len(replacements),1);child=replacements[0]
   self.assertEqual(child['rarity'],'epic');self.assertEqual(power_quarters(child),4)
  self.assertEqual(self.by_ord[145]['rarity'],'epic')
  self.assertTrue(rework_growth.retired(self.by_ord[107]))

 def test_requested_spell_contracts(self):
  expected={61:{'infection_radius_pixels':192},63:{'chain_radius_pixels':192,'chain_total_targets':7},
   64:{'energy_cost':50},102:{'radius_multiplier':2},103:{'swarm_max_hp_regen_percent_per_second':3},
   104:{'broodlings_per_target':6,'additional_cast_targets':3,'additional_cast_radius_pixels':128},
   145:{'recall_attack_bonus_percent':20,'recall_buff_frames':720,'recall_buff_stacks':False},
   146:{'chain_total_targets':5,'additional_target_supply_limit':False}}
  for ordinal,fields in expected.items():
   for key,value in fields.items():self.assertEqual(self.by_ord[ordinal]['effect'][key],value)
  self.assertEqual(self.by_ord[RADIATION_ORDINAL]['rarity'],'epic')

 def test_wave_metadata_reports_the_actual_integer_rosters(self):
  self.assertEqual(self.catalog['wave_count_multiplier_percent'],dict(normal=115,rare=150,epic=175,legendary=200))
  raynor=self.catalog['curses'][38]
  self.assertEqual(raynor['effect']['wave_count_multiplier_percent'],150)
  self.assertEqual([x['count'] for x in raynor['effect']['base_delivered_roster']],[3,26,5])
  self.assertEqual(self.catalog['curses'][40]['effect']['base_delivered_roster'][0]['count'],2)

 def test_pin_upgrade_appends_only_new_ids_and_keeps_issued_data(self):
  old=copy.deepcopy(self.catalog);old['talents']=old['talents'][:400]
  for item in old['talents'][238:]:
   item['effect']['qa_revision']=2026102037
   if item['effect_ordinal'] in PROMOTIONS:item['rarity']='epic'
  issued=json.dumps([{'id':self.by_ord[145]['id'],'name':'old offered text','bundled_talent_ids':[self.by_ord[145]['id'],self.by_ord[144]['id']]}])
  conn=sqlite3.connect(':memory:')
  conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT)')
  conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
  conn.execute('CREATE TABLE issued (text TEXT)');conn.execute('INSERT INTO issued VALUES (?)',(issued,))
  conn.execute('CREATE TABLE frozen (bytes BLOB)');conn.execute('INSERT INTO frozen VALUES (?)',(b'unchanged accepted input and checkpoint',))
  rework_growth.enable(conn)
  pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
  self.assertEqual(len(pinned['talents']),560)
  self.assertEqual(conn.execute('SELECT text FROM issued').fetchone()[0],issued)
  self.assertEqual(conn.execute('SELECT bytes FROM frozen').fetchone()[0],b'unchanged accepted input and checkpoint')
  self.assertEqual([x['id'] for x in pinned['talents'][:400]],[x['id'] for x in old['talents']])
  again=conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0];rework_growth.enable(conn)
  self.assertEqual(again,conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
  words=encode_growth(self.catalog,[identity(RADIATION_ORDINAL)],{})
  bit=238+RADIATION_ORDINAL;self.assertTrue(words[1+bit//32]&(1<<(bit%32)))
  conn.close()

 def test_historical_recall_bundle_remains_valid_after_demotion(self):
  left,right=self.by_ord[145],self.by_ord[144]
  self.assertFalse(unit_legendary(left));self.assertFalse(compatible(left,right))
  self.assertEqual(member_ids(dict(id=left['id'],bundled_talent_ids=[left['id'],right['id']]),self.catalog),(left['id'],right['id']))

 def test_opening_has_one_third_common_independent_of_unit_pool_size(self):
  for mission in (101,201,301,401,501,601):
   common=0
   for seed in range(300):
    options=rework_growth.candidates(self.catalog,mission,1,[],random.Random(seed))
    self.assertEqual(len(options),4)
    shared=[x for x in options if x['race']=='shared']
    self.assertLessEqual(len(shared),1);common+=bool(shared)
    self.assertTrue(all(x['rarity']=='legendary' for x in options))
    self.assertTrue(all(x.get('bundled_talent_ids') for x in options if x['race']!='shared'))
   self.assertLess(abs(common/300-1/3),.08)

 def test_common_exhaustion_does_not_force_duplicates(self):
  owned=[x['id'] for x in self.catalog['talents'] if x['race']=='shared' and x['rarity']=='legendary']
  for seed in range(40):
   options=rework_growth.candidates(self.catalog,101,1,owned,random.Random(seed))
   self.assertEqual(len(options),4);self.assertTrue(all(x['race']=='terran' for x in options))
   self.assertFalse(any(x['id'] in owned for x in options))

if __name__=='__main__':unittest.main()
