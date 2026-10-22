"""QA39 current offers, durable history and requested native metadata."""
import copy,json,random,sqlite3,tempfile,unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch
from sc1.campaign import rework_growth,legendary_bundles as bundles
from sc1.campaign.runtime_catalog import load_catalog,encode_growth
from sc1.campaign.talent_retirement import ORDINALS
from sc1.campaign.legend_focus import CONVERTED,DEMOTIONS
from sc1.manager.store import GrowthChoicesPending,open_campaign_store

class QA39Legends(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=load_catalog(expected_version=2)
  cls.by={x['effect_ordinal']:x for x in cls.catalog['talents'] if x.get('rework_revision')==5}

 def test_removed_main_or_partner_never_appears_in_new_choices(self):
  for mission in (101,201,301,401,501,601):
   for seed in range(50):
    for item in rework_growth.candidates(self.catalog,mission,1,[],random.Random(seed)):
     self.assertFalse(rework_growth.option_has_retired(item,self.catalog))
     for identity in bundles.member_ids(item,self.catalog):
      row=next(x for x in self.catalog['talents'] if x['id']==identity)
      self.assertNotIn(row.get('effect_ordinal'),ORDINALS|DEMOTIONS)

 def test_removed_and_demoted_historical_pairs_remain_readable(self):
  for ordinal in ORDINALS|DEMOTIONS:
   left=self.by[ordinal]
   right=next(x for x in self.by.values() if x['race']==left['race'] and x['rarity']=='legendary' and not x['effect'].get('retired') and not set(x['target_units'])&set(left['target_units']))
   old=dict(id=left['id'],bundled_talent_ids=[left['id'],right['id']])
   self.assertEqual(bundles.member_ids(old,self.catalog),(left['id'],right['id']))
   words=encode_growth(self.catalog,[left['id']],{})
   self.assertTrue(words[1+left['bit_index']//32]&(1<<(left['bit_index']%32)))

 def test_pending_retired_partner_archived_exactly_in_both_protocols(self):
  for version,removed in ((v,n) for v in (1,2) for n in (183,200,218,225,226,250,261,291,312)):
   with self.subTest(version=version,removed=removed),tempfile.TemporaryDirectory() as folder:
    db=Path(folder)/'disposable.sqlite3';store=open_campaign_store(db,curses_per_mission=0)
    right=self.by[removed]
    left=next(x for x in self.by.values() if not x['effect'].get('offer_retired') and not rework_growth.retired(x) and bundles.compatible(x,right,historical=True))
    option=copy.deepcopy(left);option['bundled_talent_ids']=[left['id'],right['id']]
    def load():
     try:return store.restore_growth_phase(101,2,1,phase_version=version)
     except GrowthChoicesPending as pending:return pending.state
    with patch.object(rework_growth,'candidates',return_value=[option]):old=copy.deepcopy(load()['offer'])
    with closing(sqlite3.connect(db)) as conn:
     conn.execute('CREATE TABLE sentinel (value BLOB)');conn.execute('INSERT INTO sentinel VALUES (?)',(b'accepted source and frozen input',));conn.commit()
     text=conn.execute('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(old['offer_id'],)).fetchone()[0]
    new=load()['offer'];self.assertNotEqual(new['offer_id'],old['offer_id'])
    self.assertTrue(all(not rework_growth.option_has_retired(x,self.catalog) for x in new['candidates']))
    with closing(sqlite3.connect(db)) as conn:
     self.assertEqual(conn.execute('SELECT candidates_json FROM growth_offer_retirement_history WHERE offer_id=?',(old['offer_id'],)).fetchone()[0],text)
     self.assertEqual(conn.execute('SELECT value FROM sentinel').fetchone()[0],b'accepted source and frozen input')

 def test_spell_cone_single_target_and_shadow_contracts(self):
  b=self.by
  for ordinal in DEMOTIONS:self.assertEqual(b[ordinal]['rarity'],'epic')
  self.assertEqual(b[140]['effect']['moving_attack_percent'],100)
  self.assertFalse(b[136]['effect']['ignore_health_armor'])
  self.assertEqual(b[82]['name'],'마비성 인스네어')
  for key in ('ensnare_attack_speed_reduction_percent','ensnare_movement_speed_reduction_percent'):self.assertEqual(b[82]['effect'][key],85)
  self.assertEqual(b[149]['effect']['stasis_radius_multiplier'],1.5)
  self.assertTrue(b[149]['effect']['stasis_friendly_full_health_shields'])
  self.assertEqual(b[106]['effect']['acid_spore_effect_multiplier'],2)
  self.assertEqual(b[92]['effect']['cleave_extra_targets'],3)
  self.assertEqual(b[92]['effect']['cleave_damage_percent'],70)
  self.assertEqual(b[92]['effect']['actual_hp_shield_lifesteal_percent'],100)
  self.assertEqual(b[97]['effect']['air_attack_percent'],100)
  self.assertEqual(b[96]['effect']['base_bonus_percent'],50)
  self.assertEqual((b[96]['effect']['blast_radius_pixels'],b[96]['effect']['blast_damage_percent']),(64,50))
  self.assertEqual(b[96]['effect']['blast_target_layer'],'air')
  self.assertFalse(b[96]['effect']['blast_friendly_fire'])
  self.assertNotIn(96,self.catalog['single_target_legend_ordinals'])
  self.assertEqual(b[185]['effect']['cone_radius_pixels'],96)
  self.assertEqual(b[185]['effect']['cone_angle_degrees'],120)
  self.assertNotIn('증식 브루들링',b[104]['description'])
  self.assertEqual(b[321]['name'],'그림자 격노');self.assertEqual(b[321]['rarity'],'legendary')
  self.assertEqual(len(CONVERTED),18)
  self.assertTrue(b[139]['effect']['reflection_only_releases_on_attack'])
  self.assertGreater(b[194]['effect']['base_bonus_percent'],b[184]['effect']['base_bonus_percent'])

if __name__=='__main__':unittest.main()
