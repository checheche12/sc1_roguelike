"""PHC1 v2 native parser/bridge/SQLite interop in owned disposable fixtures."""
from pathlib import Path
import argparse,json,struct,subprocess,sys,tempfile
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from sc1.bridge.protocol import Dispatcher,read_request
from sc1.manager.store import CampaignStore
from sc1.campaign.runtime_catalog import load_catalog
BASE=0x10000;WORDS=struct.Struct('<128I')

def verify(executable):
 checks=0;results=[]
 def check(value):
  nonlocal checks
  checks+=1
  if not value:raise AssertionError(f'PHC1 v2 interop check {checks} failed')
 for difficulty in range(5):
  process=subprocess.Popen([str(executable),'--checkpoint-wire'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8')
  class Memory:
   def refresh(self):
    line=process.stdout.readline()
    if not line.startswith('DUMP '):raise AssertionError('Native fixture stopped: '+line+process.stderr.read())
    values=list(map(int,line.split()[1:]));check(len(values)==134)
    self.data=bytearray(WORDS.pack(*values[:128]));self.counters=values[128:]
   def read(self,address,size):return bytes(self.data[address-BASE:address-BASE+size])
   def write(self,address,value):
    offset=address-BASE;check(128<=offset<offset+len(value)<=512);self.data[offset:offset+len(value)]=value
   def command(self,text):process.stdin.write(text+'\n');process.stdin.flush();self.refresh()
   def deliver(self):self.command('RESPONSE '+' '.join(map(str,WORDS.unpack(self.data)[32:])))
  memory=Memory();memory.refresh()
  try:
   with tempfile.TemporaryDirectory(prefix='sc1-checkpoint-owned-') as folder:
    folder=Path(folder);catalog=load_catalog(expected_version=2);path=folder/'fixture_catalog.json';path.write_text(json.dumps(catalog),encoding='utf8')
    store=CampaignStore(folder/'fixture.sqlite3',new_profile='original',runtime_catalog_path=path,curses_per_mission=difficulty)
    dispatcher=Dispatcher(memory,BASE,store,clock=lambda:0);manual=next(x for x in catalog['talents'] if x.get('repeatable'))
    def poll():
     result=dispatcher.poll()
     if result['status'] in ('choice_offered','restored','committed'):memory.deliver()
     check(memory.counters[3]==0)
     return result
    check(poll()['status']=='waiting_for_heartbeat');memory.command('TICK');chosen={'talent':0,'curse':0}
    with patch('sc1.campaign.rework_growth.candidates',return_value=[manual]):
     for phase in range(1,5):
      if phase>1:memory.command(f'PHASE {phase}')
      state=poll()
      while state['status']=='choice_offered':
       request=read_request(memory,BASE);check(request.phase_version==2 and request.phase==phase)
       kind=WORDS.unpack(memory.data)[44];chosen['talent' if kind==1 else 'curse']+=1
       memory.command('CHOOSE 1');state=poll()
      check(state['status']=='restored');words=WORDS.unpack(memory.data)
      check(words[7]==(3 if phase==4 else 2) and words[19]==2 and words[76+manual['rank_slot']]==chosen['talent'])
      check(memory.counters[0]==phase)
      before=memory.counters[0];memory.deliver();check(memory.counters[0]==before)
      memory.command('GOAL')
      if phase<4:check(read_request(memory,BASE).operation!=2 and memory.counters[5]==0)
    check(chosen=={'talent':3,'curse':difficulty});check(read_request(memory,BASE).operation==2)
    check(poll()['status']=='committed' and memory.counters[5]==1)
    store.curses_per_mission=4-difficulty;memory.command('RESET');dispatcher=Dispatcher(memory,BASE,store,clock=lambda:0)
    check(poll()['status']=='waiting_for_heartbeat');memory.command('TICK');check(poll()['status']=='restored')
    check(WORDS.unpack(memory.data)[76+manual['rank_slot']]==3);memory.command('GOAL');check(memory.counters[5]==1)
    results.append(dict(curses=difficulty,talents=3,all_four_checkpoints=True,commit_and_replay=True))
  finally:
   if process.poll() is None:process.stdin.write('QUIT\n');process.stdin.flush()
   code=process.wait(timeout=5);error=process.stderr.read()
   for stream in (process.stdin,process.stdout,process.stderr):stream.close()
   if code:raise RuntimeError(error)
 return dict(passed=True,checks=checks,phase_version=2,phases=4,modes=results,game_accessed=False,player_database_accessed=False)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('executable',type=Path);args=parser.parse_args();print(json.dumps(verify(args.executable)))
