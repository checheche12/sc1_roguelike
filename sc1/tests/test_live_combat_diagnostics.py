import unittest
import struct
import tempfile
from pathlib import Path

from sc1.diagnostics.live_combat import analyze_rows, dump_summary


class LiveCombatEvidenceTests(unittest.TestCase):
    def result(self, rows=(), **run):
        return analyze_rows(list(rows), dict(game_exit_code=0, timed_out=False, crash_dumps=[], **run))

    def test_empty_log_is_not_success(self):
        result = self.result()
        self.assertFalse(result['passed'])
        self.assertFalse(result['actual_engine_executed'])
        self.assertFalse(next(c for c in result['checks'] if c['name']=='complete_evidence')['passed'])

    def test_survival_and_terminal_do_not_prove_damage(self):
        rows = [dict(event='phase_complete', phase=i) for i in range(4)]
        rows += [dict(event='entry',pid=123),dict(event='terminal', status='complete',pid=123)]
        result = self.result(rows,owned_game_pid=123)
        self.assertTrue(next(c for c in result['checks'] if c['name']=='complete_evidence')['passed'])
        self.assertFalse(result['passed'])

    def test_old_log_from_another_process_is_rejected(self):
        rows = [dict(event='phase_complete',phase=i) for i in range(4)]
        rows += [dict(event='entry',pid=123),dict(event='terminal',status='complete',pid=123)]
        result=self.result(rows,owned_game_pid=456)
        self.assertFalse(next(c for c in result['checks'] if c['name']=='complete_evidence')['passed'])

    def test_crash_dump_process_and_exception_are_read(self):
        data=bytearray(256);data[:4]=b'MDMP'
        struct.pack_into('<II',data,8,2,32)
        struct.pack_into('<III',data,32,15,12,56)
        struct.pack_into('<III',data,44,6,168,80)
        struct.pack_into('<III',data,56,12,1,123)
        struct.pack_into('<I',data,88,0xC0000005)
        struct.pack_into('<Q',data,104,0x12345678)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'test.dmp';path.write_bytes(data)
            result=dump_summary(path)
        self.assertEqual(result['pid'],123)
        self.assertEqual(result['exception_code'],'0xc0000005')
        self.assertEqual(result['exception_address'],'0x12345678')

    def test_nonzero_exit_and_dump_each_fail(self):
        for run in [dict(game_exit_code=0xC0000005),dict(game_exit_code=0,crash_dumps=[dict(pid=123)]),dict(game_exit_code=0,timed_out=True)]:
            result=analyze_rows([],run)
            self.assertFalse(next(c for c in result['checks'] if c['name']=='process_exit')['passed'])

    def test_full_damage_contract_rejects_one_wrong_hit(self):
        rows=[dict(event='hit',phase=3,case=1,victim=0,frame=i,weapon=2,
                   generated=0,hp_before=100000,hp_after=100000-5120,
                   shields_before=0,shields_after=0,target_identity_retained=True) for i in range(5)]
        check=lambda result:next(c for c in result['checks'] if c['name']=='ghost_normal_type_3')['passed']
        self.assertTrue(check(self.result(rows)))
        rows[-1]['hp_after']+=1
        self.assertFalse(check(self.result(rows)))

    def test_impact_on_reused_slot_is_not_valid_evidence(self):
        rows=[dict(event='hit',phase=0,case=2,victim=0,frame=i,weapon=55,
                   generated=0,hp_before=100000,hp_after=72096,
                   shields_before=0,shields_after=0,target_identity_retained=False) for i in range(3)]
        result=self.result(rows)
        self.assertFalse(next(c for c in result['checks'] if c['name']=='scourge_rank4_0')['passed'])

    def test_equal_attack_interval_medians_are_not_synergy(self):
        rows=[]
        for phase,period in enumerate((15,9,11,9)):
            rows.append(dict(event='phase_start',phase=phase,frame=phase*2000))
            for i in range(65):
                frame=phase*2000+240+i*period+(1 if phase==1 and i>30 else 0)
                rows.append(dict(event='hit',phase=phase,case=0,victim=0,frame=frame,
                                 weapon=0,generated=0,hp_before=10000,hp_after=8464,
                                 shields_before=0,shields_after=0,target_identity_retained=True))
        result=self.result(rows)
        self.assertFalse(next(c for c in result['checks'] if c['name']=='both_warmups_change_actual_cadence')['passed'])


if __name__=='__main__':unittest.main()
