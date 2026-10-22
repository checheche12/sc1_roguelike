import copy,json,sqlite3,unittest
from fractions import Fraction
from pathlib import Path
from sc1.campaign import rework_growth
from sc1.campaign.runtime_catalog import load_catalog

class ZerglingErosion(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.catalog=load_catalog(expected_version=2);cls.item=cls.catalog['talents'][428]

 def test_exact_point33_metadata_native_rule_and_description(self):
  x=self.item;self.assertEqual(x['effect_ordinal'],190)
  self.assertEqual(x['effect']['armor_erosion_per_hit'],0.33)
  self.assertEqual((x['effect']['armor_erosion_numerator'],x['effect']['armor_erosion_denominator']),(33,100))
  self.assertEqual(x['effect']['focus_step_percent'],33)
  self.assertEqual(3*Fraction(33,100),Fraction(99,100));self.assertEqual(100*Fraction(33,100),33)
  self.assertIn('0.33',x['description']);self.assertNotIn('1씩',x['description'])
  root=Path(__file__).resolve().parents[2]
  text=(root/'sc1/native_campaign/plugin/include/legend_focus.generated.h').read_text(encoding='utf8')
  self.assertIn('armor_erosion_denominator=100u',text);self.assertIn('{190u,6u,0u,1u,0u,33u,0u,',text)

 def test_old_pin_refreshes_effect_and_text_without_rewriting_issued_copy(self):
  prior=copy.deepcopy(self.catalog);old=prior['talents'][428]
  old['description']='저글링의 공격마다 체력 방어력을 1씩 감소.';old['description_revision']=2026102039
  old['effect']['qa_revision']=2026102039;old['effect']['focus_step_percent']=1
  for k in ('armor_erosion_per_hit','armor_erosion_numerator','armor_erosion_denominator'):old['effect'].pop(k,None)
  saved=json.dumps(old,ensure_ascii=False)
  with sqlite3.connect(':memory:') as conn:
   conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
   conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(prior),))
   conn.execute('CREATE TABLE issued (text TEXT)');conn.execute('INSERT INTO issued VALUES(?)',(saved,))
   rework_growth.enable(conn)
   new=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
   self.assertEqual(new['talents'][428]['effect'],self.item['effect']);self.assertEqual(new['talents'][428]['description'],self.item['description'])
   self.assertEqual(new['talents'][428]['source_description'],old['source_description'])
   self.assertEqual(new['talents'][:428],prior['talents'][:428]);self.assertEqual(new['talents'][429:],prior['talents'][429:])
   self.assertEqual(new['curses'],prior['curses']);self.assertEqual(conn.execute('SELECT text FROM issued').fetchone()[0],saved)

if __name__=='__main__':unittest.main()
