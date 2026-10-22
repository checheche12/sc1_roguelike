import copy,json,sqlite3,unittest
from sc1.campaign import rework_growth
from sc1.campaign.runtime_catalog import load_catalog

class LurkerAir(unittest.TestCase):
 def test_metadata_preserves_original_damage_and_requires_burrow(self):
  x=load_catalog(expected_version=2)['talents'][335]
  self.assertEqual(x['effect_ordinal'],97);self.assertEqual(x['effect']['air_attack_percent'],100)
  self.assertTrue(x['effect']['burrow_required']);self.assertTrue(x['effect']['air_target_acquisition']);self.assertTrue(x['effect']['shared_ground_air_cooldown'])
  self.assertIn('잠복',x['description']);self.assertIn('공중 적만 관통',x['description']);self.assertEqual(x['target_units'],[103])
 def test_old_pin_updates_air_fire_and_weight_without_changing_issued_copy(self):
  c=load_catalog(expected_version=2);prior=copy.deepcopy(c);x=prior['talents'][335]
  x['description']='러커가 공중 적에게도 가시를 쏩니다.';x['effect']['qa_revision']=2026102039
  for key in ('burrow_required','air_target_acquisition','shared_ground_air_cooldown'):x['effect'].pop(key,None)
  saved=json.dumps(x,ensure_ascii=False)
  with sqlite3.connect(':memory:') as conn:
   conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)');conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(prior),))
   conn.execute('CREATE TABLE issued (text TEXT)');conn.execute('INSERT INTO issued VALUES(?)',(saved,))
   rework_growth.enable(conn);current=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
   self.assertEqual(current['talents'][335]['effect'],c['talents'][335]['effect']);self.assertEqual(current['talents'][335]['source_description'],x['source_description'])
   self.assertEqual(conn.execute('SELECT text FROM issued').fetchone()[0],saved);self.assertEqual(current['curses'],prior['curses'])
if __name__=='__main__':unittest.main()
