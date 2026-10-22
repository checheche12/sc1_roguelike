import copy,json,sqlite3,tempfile,unittest
from pathlib import Path
from sc1.campaign import rework_growth,air_legend_balance,legendary_expansion
from sc1.campaign.runtime_catalog import load_catalog

class AirLegendBalance(unittest.TestCase):
 def test_mutal_linear_six_bounces_and_guardian_preserves_splash(self):
  c=load_catalog(expected_version=2);m=c['talents'][343];g=c['talents'][429]
  self.assertEqual(m['effect']['projectile_damage_percent'],200)
  self.assertEqual(m['effect']['legendary_bounces'],6)
  self.assertEqual(m['effect']['bounce_damage_numerators'],[7,6,5,4,3,2,1]);self.assertEqual(m['effect']['bounce_damage_denominator'],7)
  self.assertNotIn(105,c['single_target_legend_ordinals'])
  self.assertEqual((g['effect']['bonus'],g['effect']['percent'],g['effect']['count'],g['effect']['radius']),(150,100,6,96))
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);(root/'sc1/native_campaign/plugin/include').mkdir(parents=True)
   text=legendary_expansion.generate_header(c,root).read_text()
   self.assertIn('{191u,1u,150u,100u,6u,1u,96u,',text)
 def test_transport_speed_only_and_decorator_preserves_frozen_copy(self):
  c=load_catalog(expected_version=2);before=copy.deepcopy(c);air_legend_balance.decorate(c)
  for index in (271,312,353):
   t=c['talents'][index];self.assertNotIn('16',t['description']);self.assertNotIn('수송 공간',t['description'])
   self.assertEqual(t['effect']['transport_capacity_bonus'],0);self.assertEqual(t['effect']['movement_speed_bonus_percent'],40)
   self.assertEqual(t['source_description'],before['talents'][index]['source_description'])
  self.assertEqual(c,before)
 def test_all_old_pinned_cards_refresh_and_owned_ranks_survive(self):
  current=load_catalog(expected_version=2);old=copy.deepcopy(current);indices=(271,284,312,341,343,353,429,560)
  nuclear=current['talents'][284]
  self.assertEqual((nuclear['effect']['nuclear_warning_frames'],nuclear['effect']['nuclear_build_time_frames'],nuclear['effect']['nuclear_supply_required']),(36,720,2))
  self.assertIn('1.5초',nuclear['description']);self.assertIn('30초',nuclear['description'])
  for i in indices:old['talents'][i]['effect']['qa_revision']=2026102264;old['talents'][i]['description']='Previous card'
  old['talents'][560]['candidate_weight_percent']=200
  with sqlite3.connect(':memory:') as conn:
   conn.execute('CREATE TABLE growth_rework_catalog (id INTEGER PRIMARY KEY,catalog_json TEXT NOT NULL)')
   conn.execute('INSERT INTO growth_rework_catalog VALUES(1,?)',(json.dumps(old),))
   rework_growth.save_ranks(conn,201,{current['talents'][343]['id']:1,current['talents'][341]['id']:1})
   rework_growth.enable(conn);updated=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
   for i in indices:
    for key in ('description','effect','id','bit_index','source_description'):self.assertEqual(updated['talents'][i][key],current['talents'][i][key])
   self.assertEqual(updated['talents'][560]['candidate_weight_percent'],300)
   self.assertEqual(rework_growth.ranks(conn,201),{current['talents'][343]['id']:1,current['talents'][341]['id']:1})
   self.assertEqual(updated['curses'],current['curses'])

if __name__=='__main__':unittest.main()
