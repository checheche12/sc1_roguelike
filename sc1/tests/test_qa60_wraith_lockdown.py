import copy,json,sqlite3,unittest
from pathlib import Path
from sc1.campaign import rework_growth,legendary_expansion,generate_native_catalog
from sc1.campaign.runtime_catalog import load_catalog

class QA60WraithLockdown(unittest.TestCase):
 def test_release_copy_and_native_rules_agree(self):
  c=load_catalog(expected_version=2);by={r.get('effect_ordinal'):r for r in c['talents'] if r.get('rework_revision')==5}
  row=by[186];spec=next(r for r in legendary_expansion.entries(c) if r['ordinal']==186)
  for key,value in dict(bonus=100,percent=200,count=3,radius=128).items():
   self.assertEqual(row['effect'][key],value);self.assertEqual(spec[key],value)
  self.assertIn('+100%',row['description']);self.assertIn('200%',row['description']);self.assertIn('3기',row['description'])
  self.assertEqual(row['target_units'],[8,21]);self.assertEqual(row['id'],legendary_expansion.identity(186))
  self.assertTrue(by[63]['effect']['prefer_unlocked_unclaimed_targets']);self.assertIn('우선',by[63]['description'])
  root=Path(__file__).resolve().parents[2]
  self.assertEqual((root/'sc1/native_campaign/plugin/include/frozen_catalog.generated.h').read_text(encoding='utf8'),generate_native_catalog.render(c))
 def test_existing_catalog_upgrade_preserves_issued_offers_and_identity(self):
  current=load_catalog(expected_version=2);old=copy.deepcopy(current)
  for ordinal in (63,186):old['talents'][238+ordinal]['effect']['qa_revision']=2026102038
  old['talents'][424]['effect'].update(bonus=0,percent=100,count=2)
  old['talents'][424]['description']='old issued text'
  with sqlite3.connect(':memory:') as conn:
   conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT)')
   conn.execute('INSERT INTO growth_rework_catalog VALUES (1,?)',(json.dumps(old),))
   conn.execute('CREATE TABLE issued (text TEXT)');conn.execute('INSERT INTO issued VALUES (?)',('old issued text',))
   rework_growth.enable(conn);pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
   self.assertEqual(pinned['talents'][424]['effect']['bonus'],100)
   self.assertEqual(pinned['talents'][424]['effect']['count'],3)
   self.assertTrue(pinned['talents'][301]['effect']['prefer_unlocked_unclaimed_targets'])
   self.assertEqual([r['id'] for r in old['talents']],[r['id'] for r in pinned['talents']])
   self.assertEqual(conn.execute('SELECT text FROM issued').fetchone()[0],'old issued text')

if __name__=='__main__':unittest.main()
