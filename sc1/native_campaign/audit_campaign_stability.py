"""Offline campaign/bridge/native-parser audit; only disposable record copies.

This exercises actual catalog draws, SQLite transactions and the production
mailbox parser. It does not launch StarCraft or simulate mission combat.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from sc1.bridge.protocol import Dispatcher, read_request
from sc1.campaign.missions import load_missions
from sc1.manager.store import CampaignStore

BASE = 0x10000
WORDS = struct.Struct('<128I')


class Host:
    def __init__(self, executable, mission):
        self.process = subprocess.Popen(
            [str(executable), '--checkpoint-wire', str(mission)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8', creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.receive()

    def receive(self):
        line = self.process.stdout.readline()
        if not line.startswith('DUMP '):
            raise AssertionError('Native fixture stopped: ' + line)
        values = list(map(int, line.split()[1:]))
        assert len(values) == 134
        self.data = bytearray(WORDS.pack(*values[:128]))
        self.counters = values[128:]

    def read(self, address, size):
        return bytes(self.data[address-BASE:address-BASE+size])

    def write(self, address, data):
        offset = address-BASE
        assert 128 <= offset < offset+len(data) <= 512
        self.data[offset:offset+len(data)] = data

    def command(self, text):
        self.process.stdin.write(text+'\n')
        self.process.stdin.flush()
        self.receive()

    def deliver(self):
        self.command('RESPONSE '+' '.join(map(str, WORDS.unpack(self.data)[32:])))

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write('QUIT\n')
            self.process.stdin.flush()
        code = self.process.wait(timeout=5)
        error = self.process.stderr.read()
        for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
            stream.close()
        assert code == 0, error


def connect(host, store):
    dispatcher = Dispatcher(host, BASE, store, clock=lambda: 0)
    assert dispatcher.poll()['status'] == 'waiting_for_heartbeat'
    host.command('TICK')
    return dispatcher


def run_mission(executable, store, mission, *, finish=True, reconnect=True):
    host = Host(executable, mission)
    trace = []
    offers = []
    reconnects = 0
    try:
        dispatch = connect(host, store)

        def poll():
            event = dispatch.poll()
            if event['status'] in ('choice_offered', 'restored', 'committed'):
                before = WORDS.unpack(host.data)
                if event['status'] == 'choice_offered':
                    offers.append(dict(phase=before[31], kind=before[44],
                        candidates=list(before[47:47+before[46]]),
                        partners=list(before[64:68]), thirds=list(before[69:73])))
                host.deliver()
            words = WORDS.unpack(host.data)
            trace.append(dict(event=event['status'], phase=words[31], state=words[7], error=host.counters[4]))
            if host.counters[4]:
                raise AssertionError(f'native error {host.counters[4]} in mission {mission}')
            return event

        event = poll()
        if not finish:
            return dict(mission=mission, passed=True, offers=offers, trace=trace)
        # A goal reached before the first choice must still wait for all phases
        # and the durable completion acknowledgement.
        host.command('GOAL')
        while True:
            if event['status'] == 'choice_offered':
                # Restart the native session and reopen the store while an
                # issued offer is pending. Its UUID and candidates must survive.
                if reconnect and reconnects == 0:
                    previous = WORDS.unpack(host.data)
                    host.command('RESET')
                    dispatch = connect(host, CampaignStore(store.path, curses_per_mission=store.curses_per_mission))
                    event = poll()
                    current = WORDS.unpack(host.data)
                    assert previous[44:64] == current[44:64]
                    assert previous[64:73] == current[64:73]
                    reconnects += 1
                    host.command('GOAL')
                words = WORDS.unpack(host.data)
                assert not host.counters[5]
                # Vary chosen slots across missions and checkpoints.
                slot = 1+(mission+words[31]+words[44]) % words[46]
                host.command(f'CHOOSE {slot}')
                event = poll()
            elif event['status'] == 'restored':
                request = read_request(host, BASE)
                applies = host.counters[0]
                host.deliver()  # Duplicate response must not apply twice.
                assert host.counters[0] == applies
                if request.state == 3:
                    event = poll()
                elif host.counters[5]:
                    break  # Already-completed alternate map/replay.
                elif request.phase < 4:
                    assert not host.counters[5]
                    host.command(f'PHASE {request.phase+1}')
                    event = poll()
                else:
                    host.command('GOAL')
                    if host.counters[5]:
                        break
                    event = poll()
            elif event['status'] == 'committed':
                assert host.counters[5] == 1
                break
            else:
                raise AssertionError(f'unexpected event {event}')
        # A fresh native session replays without issuing or granting rewards.
        before_status = store.status()
        host.command('RESET')
        dispatch = connect(host, CampaignStore(store.path, curses_per_mission=store.curses_per_mission))
        event = poll()
        assert event['status'] == 'restored'
        host.command('GOAL')
        assert host.counters[5] == 1
        assert store.status() == before_status
        return dict(mission=mission, passed=True, offers=offers, trace=trace,
                    pending_offer_reconnects=reconnects, replay=True, early_goal=True)
    except Exception as exc:
        return dict(mission=mission, passed=False, error=str(exc), offers=offers, trace=trace)
    finally:
        host.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--mission', type=int, default=105)
    parser.add_argument('--finish-snapshot', action='store_true')
    parser.add_argument('--curses', type=int, nargs='+', default=list(range(5)))
    parser.add_argument('--campaigns', type=int, nargs='+')
    args = parser.parse_args()
    result = dict(executable=str(args.executable.resolve()),
        executable_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        game_started=False, source_player_record_modified=False, scenarios=[])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='sc1-stability-') as tmp:
        tmp = Path(tmp)
        if args.snapshot:
            snapshot_hash = hashlib.sha256(args.snapshot.read_bytes()).hexdigest()
            path = tmp/'snapshot.sqlite3'
            shutil.copy2(args.snapshot, path)
            row = run_mission(args.executable, CampaignStore(path), args.mission, finish=args.finish_snapshot)
            result['snapshot_sha256'] = snapshot_hash
            result['scenarios'].append(row)
            assert hashlib.sha256(args.snapshot.read_bytes()).hexdigest() == snapshot_hash
        else:
            missions = sorted(load_missions(), key=lambda row: (row['campaign_id'], row['ordinal'], row['mission_id']))
            if args.campaigns:
                missions = [row for row in missions if row['campaign_id'] in args.campaigns]
            for difficulty in args.curses:
                store = CampaignStore(tmp/f'mode_{difficulty}.sqlite3', new_profile='original', curses_per_mission=difficulty)
                rng = random.Random(20261107+difficulty)
                failed_campaigns = set()
                with patch('sc1.campaign.checkpoint_growth.secrets.SystemRandom', return_value=rng):
                    for mission in missions:
                        if mission['campaign_id'] in failed_campaigns:
                            continue
                        row = run_mission(args.executable, store, mission['mission_id'])
                        row.update(curses=difficulty, campaign=mission['campaign_id'])
                        result['scenarios'].append(row)
                        if not row['passed']:
                            failed_campaigns.add(mission['campaign_id'])
                        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
                        print(json.dumps({k:row[k] for k in ('mission','curses','passed')}), flush=True)
    result['passed'] = all(row['passed'] for row in result['scenarios'])
    result['scenario_count'] = len(result['scenarios'])
    result['failures'] = [{k:v for k,v in row.items() if k not in ('offers','trace')}
                          for row in result['scenarios'] if not row['passed']]
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='scenarios'}, ensure_ascii=False), flush=True)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
