"""Variable mission curses preserve old history and the three talent rewards."""
from pathlib import Path
import json,sqlite3,tempfile,unittest
from contextlib import closing
from unittest.mock import patch
from sc1.manager.store import open_campaign_store,GrowthChoicesPending
from sc1.manager.preferences import startup_curses_per_mission,remember_curses_per_mission
from sc1.campaign.runtime_catalog import GrowthError
from sc1.campaign import checkpoint_growth

def restore(store,phase,nonce=None,version=2,mission=101):
 try:return store.restore_growth_phase(mission,2,phase,nonce=nonce if phase>1 else None,phase_version=version)
 except GrowthChoicesPending as exc:return exc.state

def finish(store,phase,nonce=None,version=2,mission=101):
 state=restore(store,phase,nonce,version,mission);selected=[]
 while state.get('state')=='choosing':
  offer=state['offer'];selected.append(offer['kind'])
  state=store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],mission,2,
   choice_kind=1 if offer['kind']=='talent' else 2,phase=phase,nonce=nonce if phase>1 else None,phase_version=version)
 return restore(store,phase,nonce,version,mission),selected

class DifficultyTests(unittest.TestCase):
 def test_all_five_modes_keep_three_talents_and_complete(self):
  for count in range(5):
   with self.subTest(curses=count),tempfile.TemporaryDirectory() as folder:
    store=open_campaign_store(Path(folder)/'fixture.sqlite3',curses_per_mission=count);nonce=None;selected=[]
    for phase in range(1,5):
     result,choices=finish(store,phase,nonce);nonce=result['nonce'];selected+=choices
     self.assertEqual(result['completed_phase'],phase)
     if phase<4:
      with self.assertRaises(GrowthError):store.complete(101,nonce,0,result['gold'])
    self.assertEqual(selected.count('talent'),3);self.assertEqual(selected.count('curse'),count)
    self.assertEqual(store.growth_status(101)['curses_per_mission'],count)
    store.complete(101,nonce,0,result['gold'])
    again=restore(store,1);self.assertEqual(again['growth_words'],result['growth_words']);self.assertEqual(again['completed_phase'],4)
 def test_setting_pins_once_and_applies_to_next_unprepared_mission(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'fixture.sqlite3';store=open_campaign_store(path,curses_per_mission=0)
   result,_=finish(store,1);nonce=result['nonce'];store=open_campaign_store(path,curses_per_mission=4)
   for phase in (2,3,4):result,_=finish(store,phase,nonce)
   self.assertEqual(store.growth_status(101)['curses_per_mission'],0);store.complete(101,nonce,0,result['gold'])
   state=restore(store,1,mission=102);self.assertEqual(state['curses_per_mission'],4)
 def test_old_prepared_mission_import_preserves_uuids_and_frozen_payloads(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'fixture.sqlite3';store=open_campaign_store(path)
   old,_=finish(store,1,version=1);nonce=old['nonce'];pending=restore(store,2,nonce,version=1)
   with closing(sqlite3.connect(path)) as conn:
    before=conn.execute('SELECT * FROM growth_phase_snapshots').fetchall();offers=conn.execute('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL ORDER BY sequence').fetchall()
   store=open_campaign_store(path,curses_per_mission=0);current=restore(store,1)
   self.assertEqual(current['completed_phase'],1);self.assertEqual(current['growth_words'],old['growth_words'])
   empty=restore(store,2,nonce);self.assertEqual(empty['completed_phase'],2)
   next_offer=restore(store,3,nonce);self.assertEqual(next_offer['offer']['offer_id'],pending['offer']['offer_id'])
   self.assertEqual(next_offer['curses_per_mission'],3)
   with closing(sqlite3.connect(path)) as conn:
    self.assertEqual(conn.execute('SELECT * FROM growth_phase_snapshots').fetchall(),before)
    self.assertEqual(conn.execute('SELECT offer_id,candidates_json FROM growth_offers WHERE candidates_json IS NOT NULL ORDER BY sequence').fetchall(),offers)
   for phase in (3,4):result,_=finish(store,phase,nonce)
   store.complete(101,nonce,0,result['gold'])
 def test_out_of_order_wrong_nonce_and_old_protocol_cannot_add_rewards(self):
  with tempfile.TemporaryDirectory() as folder:
   store=open_campaign_store(Path(folder)/'fixture.sqlite3',curses_per_mission=4);result,_=finish(store,1);nonce=result['nonce']
   for phase,token,version in ((4,nonce,2),(2,'a'*32,2),(2,nonce,1)):
    with self.assertRaises(GrowthError):restore(store,phase,token,version)
   self.assertEqual(store.growth_status(101)['completed_phase'],1)
 def test_invalid_modes_are_rejected_before_database_creation(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'fixture.sqlite3'
   for value in (-1,5,True,1.0,'0'):
    with self.assertRaises(GrowthError):open_campaign_store(path,curses_per_mission=value)
    self.assertFalse(path.exists())
 def test_duplicate_confirmation_does_not_grant_another_reward(self):
  with tempfile.TemporaryDirectory() as folder:
   store=open_campaign_store(Path(folder)/'fixture.sqlite3',curses_per_mission=0);state=restore(store,1);offer=state['offer']
   args=(offer['offer_id'],1,offer['revision'],101,2)
   first=store.choose_growth_phase_slot(*args,choice_kind=1,phase=1,phase_version=2)
   again=store.choose_growth_phase_slot(*args,choice_kind=1,phase=1,phase_version=2)
   self.assertFalse(first['duplicate']);self.assertTrue(again['duplicate']);self.assertEqual(first['growth_words'],again['growth_words'])
 def test_retired_imported_pending_offer_keeps_valid_foreign_keys(self):
  from sc1.campaign.runtime_catalog import load_catalog
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'fixture.sqlite3';store=open_campaign_store(path)
   first,_=finish(store,1,version=1);nonce=first['nonce'];pending=restore(store,2,nonce,version=1);identity=pending['offer']['offer_id']
   retired=next(x for x in load_catalog(expected_version=2)['talents'] if x['id']=='bbf067dc-0ced-5875-a519-2c0443580c8d')
   with closing(sqlite3.connect(path)) as conn:
    conn.execute('UPDATE growth_offers SET candidates_json=? WHERE offer_id=?',(json.dumps([retired]),identity));conn.commit()
   restore(store,1);restore(store,2,nonce);replacement=restore(store,3,nonce)
   self.assertNotEqual(replacement['offer']['offer_id'],identity)
   with closing(sqlite3.connect(path)) as conn:self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])
 def test_preferences_preserve_zero_and_other_loader_settings(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'preferences.json';path.write_text(json.dumps(dict(version=1,last_database='kept.sqlite3',game_path='kept-game')),encoding='utf8')
   for count in range(5):
    remember_curses_per_mission(count,preferences_path=path);self.assertEqual(startup_curses_per_mission(preferences_path=path),count)
    self.assertEqual(json.loads(path.read_text(encoding='utf8'))['last_database'],'kept.sqlite3')
   for value in (True,5,-1,'0'):
    path.write_text(json.dumps(dict(curses_per_mission=value)),encoding='utf8');self.assertEqual(startup_curses_per_mission(preferences_path=path),3)

if __name__=='__main__':unittest.main()
