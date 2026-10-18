"""Offline v5 map profile and production-native adapter verification."""
from __future__ import annotations
import hashlib,json,os,pathlib,subprocess,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sc1.native_campaign.build_rework_wave_profiles import derive,HEROES

class Profiles(unittest.TestCase):
 def test_all63_are_bound_and_original_sources_retained(self):
  rows=derive();missions=json.loads((ROOT/'sc1/campaign/missions.json').read_text(encoding='utf8'))['missions']
  self.assertEqual(len(rows),63);self.assertEqual({r['mission_id'] for r in rows},{m['mission_id'] for m in missions})
  for r,m in zip(rows,missions):self.assertEqual(r['original_chk_sha256'],hashlib.sha256(pathlib.Path(m['source']).read_bytes()).hexdigest())
 def test_no_production_fails_closed_and_timings_fit(self):
  rows=derive();self.assertEqual(sum(not p['enabled'] for p in rows),8)
  for p in rows:
   if p['mission_id']==404:
    self.assertEqual((p['normal_first_seconds'],p['normal_interval_seconds'],p['new_base_grace_seconds']),(240,120,240))
    self.assertEqual((p['rare_unlock_seconds'],p['epic_unlock_seconds'],p['legendary_unlock_seconds']),(1200,1500,1800))
    self.assertEqual((p['warning_seconds'],p['appearance_seconds']),(20,4))
    continue
   self.assertEqual(p['normal_first_seconds'],240 if p['enabled'] else 360);self.assertIn(p['rare_unlock_seconds'],range(480,601));self.assertIn(p['epic_unlock_seconds'],range(600,721));self.assertIn(p['legendary_unlock_seconds'],range(720,841))
   self.assertEqual((p['warning_seconds'],p['appearance_seconds']),(20,4))
   self.assertEqual(p['normal_interval_seconds'],120)
   if p['mode']=='disabled':self.assertFalse(p['enabled'])
 def test_hero_collision_guards_are_per_map_and_owner_independent(self):
  rows=derive();self.assertGreater(sum(len(p['blocked_hero_curse_slots']) for p in rows),0)
  for p in rows:
   refs=set(p['hero_referenced_types'])
   for slot,ids in HEROES.items():self.assertEqual(slot in p['blocked_hero_curse_slots'],bool(refs.intersection(ids)))
   self.assertFalse(p['original_triggers_changed'])
 def test_coverage_binds_exact_frozen35_and_excludes_deleted_torasque(self):
  c=json.loads((ROOT/'analysis/runtime_rework_20261016/wave_curse_coverage.json').read_text(encoding='utf8'))
  b=json.loads((ROOT/'analysis/runtime_rework_20261016/input_board_r42.json').read_text(encoding='utf8'))
  expected={x['id'] for x in b['items'] if x.get('kind')=='curse'}
  self.assertEqual(set(c['items']),expected);self.assertEqual(len(expected),35);self.assertNotIn('rework-rule-special-wave',c['items'])

def native_probe(cargo=False,carrier=False):
 """Compile a private copy; shared native_plugin.cpp is never rewritten here."""
 plugin=ROOT/'sc1/native_campaign/plugin';kind='carrier' if carrier else 'cargo' if cargo else 'wave';out=ROOT/('analysis/runtime_rework_20261016/'+kind+'_native_probe');out.mkdir(parents=True,exist_ok=True)
 s=(plugin/'native_plugin.cpp').read_text(encoding='utf8')
 if '#include "include/rework_wave_profiles.generated.h"' not in s:s=s.replace('#include "include/wave_progression.h"','#include "include/wave_progression.h"\n#include "include/rework_wave_profiles.generated.h"',1)
 if '#include "include/rework_curse_decl.h"' not in s:s=s.replace('void log_event(const char* format,...) noexcept {','#include "include/rework_curse_decl.h"\nvoid log_event(const char* format,...) noexcept {',1)
 if '#include "include/rework_wave_native.h"' not in s:s=s.replace('void regenerate_waves(U32 second) {','#include "include/rework_wave_native.h"\nvoid regenerate_waves(U32 second) {',1)
 test_header='rework_'+kind+'_v5_host_tests.h' if cargo or carrier else 'rework_wave_host_tests.h'
 entry='#define main existing_host_main\n#include "include/native_host_tests.h"\n#undef main\n#include "include/'+test_header+'"\nint main(){try{host_test::run_rework_'+kind+'_groups();std::printf("PASS v5 '+kind+' native adapter: %zu groups %d checks\\n",host_test::rework_'+kind+'_group_count,host_test::checks);return 0;}catch(const std::exception& e){std::fprintf(stderr,"FAIL %s\\n",e.what());return 1;}}'
 s=s.replace('#include "include/native_host_tests.h"',entry,1)
 fixture=plugin/('rework_'+kind+'_probe.private.cpp');fixture.write_text(s,encoding='utf8');(out/'production_source.cpp').write_text(s,encoding='utf8')
 boot=json.loads((ROOT/'analysis/all_campaign_20261015/previous_native_build_evidence.json').read_text(encoding='utf8'));compiler=pathlib.Path(boot['compiler']['path']);env=dict(os.environ);env.update(boot['compiler']['environment']);env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
 argv=[str(compiler),'/nologo','/std:c++17','/EHsc','/MT','/utf-8','/W4','/WX','/DSC1_NATIVE_HOST_TEST',fixture.name,'mailbox_protocol.cpp','wave_runtime.cpp','dialog_ui.cpp','/Fo:'+str(out)+'/', '/Fe:'+str(out/'waves.exe'),'/link','/MACHINE:X64','user32.lib']
 result=subprocess.run(argv,cwd=plugin,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/'compile.log').write_bytes(result.stdout)
 fixture.unlink(missing_ok=True)
 if result.returncode:raise RuntimeError(result.stdout.decode('utf8','replace'))
 result=subprocess.run([str(out/'waves.exe')],cwd=plugin,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/'tests.log').write_bytes(result.stdout);print(result.stdout.decode('utf8','replace'))
 if result.returncode:raise RuntimeError('native probe failed')
 return result.stdout.decode('utf8','replace')

if __name__=='__main__':
 if any(a in sys.argv for a in ('--native','--cargo','--carrier')):native_probe(cargo='--cargo' in sys.argv,carrier='--carrier' in sys.argv)
 else:unittest.main()
