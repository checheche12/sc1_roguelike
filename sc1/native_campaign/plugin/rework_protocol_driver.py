"""Real v2 native parser <-> Dispatcher/store; owned process + disposable DB only."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from sc1.bridge.protocol import Dispatcher,read_request
from sc1.manager.store import CampaignStore
from sc1.campaign.runtime_catalog import load_catalog

BASE=0x10000
WORDS=struct.Struct('<128I')


def verify(executable):
    process=subprocess.Popen([str(executable),'--rework-wire'],stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf8')
    checks=0
    def check(condition):
        nonlocal checks
        checks+=1
        if not condition:raise AssertionError(f'Extended wire check {checks} failed')
    class Memory:
        def refresh(self):
            line=process.stdout.readline()
            if not line.startswith('DUMP '):raise AssertionError('Native host stopped: '+line)
            values=list(map(int,line.split()[1:]))
            check(len(values)==134)
            self.data=bytearray(WORDS.pack(*values[:128]));self.counters=values[128:]
        def read(self,address,size):return bytes(self.data[address-BASE:address-BASE+size])
        def write(self,address,value):
            offset=address-BASE
            check(128<=offset<offset+len(value)<=512)
            self.data[offset:offset+len(value)]=value
        def command(self,text):
            process.stdin.write(text+'\n');process.stdin.flush();self.refresh()
        def deliver(self):self.command('RESPONSE '+' '.join(map(str,WORDS.unpack(self.data)[32:])))
    memory=Memory();memory.refresh()
    try:
        with tempfile.TemporaryDirectory(prefix='sc1-rework-native-owned-') as folder:
            folder=Path(folder);catalog=load_catalog(expected_version=2)
            for kind in ('talents','curses'):
                for item in catalog[kind]:item['implemented']=True
            catalog_path=folder/'synthetic_coverage.json';catalog_path.write_text(json.dumps(catalog),encoding='utf8')
            store=CampaignStore(folder/'synthetic.sqlite3',new_profile='original',runtime_catalog_path=catalog_path)
            dispatcher=Dispatcher(memory,BASE,store,clock=lambda:0)
            manual=next(x for x in catalog['talents'] if x.get('repeatable'))
            def poll():
                result=dispatcher.poll()
                if result['status'] in ('choice_offered','restored','committed'):memory.deliver()
                return result
            check(poll()['status']=='waiting_for_heartbeat');memory.command('TICK')
            with patch('sc1.campaign.rework_growth.candidates',return_value=[manual]):
                for phase in (1,2,3):
                    if phase>1:memory.command(f'PHASE {phase}')
                    check(poll()['status']=='choice_offered')
                    check(WORDS.unpack(memory.data)[46]==1)
                    memory.command('CHOOSE 1');check(poll()['status']=='choice_offered')
                    memory.command('CHOOSE 3');check(poll()['status']=='restored')
                    words=WORDS.unpack(memory.data)
                    check(words[7]==2 and words[19]==2 and words[76+manual['rank_slot']]==phase)
                    check(memory.counters[0]==phase)
                memory.command('GOAL');check(read_request(memory,BASE).operation==2)
                check(poll()['status']=='committed');check(memory.counters[5]==1)
                memory.command('RESET');dispatcher=Dispatcher(memory,BASE,store,clock=lambda:0)
                check(poll()['status']=='waiting_for_heartbeat');memory.command('TICK')
                check(poll()['status']=='restored')
                check(WORDS.unpack(memory.data)[76+manual['rank_slot']]==3)
                memory.command('GOAL');check(memory.counters[5]==1)
        return dict(passed=True,checks=checks,wire_version=2,mailbox_words=128,
                    persistent_manual_rank=3,standalone_confirmation=True,phases=3,
                    victory_and_replay=True,game_accessed=False,player_database_accessed=False)
    finally:
        if process.poll() is None:process.stdin.write('QUIT\n');process.stdin.flush()
        code=process.wait(timeout=5);error=process.stderr.read()
        for pipe in (process.stdin,process.stdout,process.stderr):pipe.close()
        if code:raise RuntimeError(error)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('executable',type=Path);args=parser.parse_args()
    print(json.dumps(verify(args.executable),ensure_ascii=False))
