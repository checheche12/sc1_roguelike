"""Original mission preservation and completion protocol, without game access."""
import ast
from pathlib import Path
import struct
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

from sc1.bridge.protocol import Dispatcher, read_request
from sc1.manager.store import CampaignStore
from sc1.tests.test_official_probe_plugin import Runtime, Value, number, NONCE
from sc1.tests.test_bridge import BASE, FakeMemory

SC1=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(SC1/'tools'))
import build_original_campaign as builder
PLUGIN=SC1/'plugins/original_campaign.py'

class CampaignValue(Value):
    def __and__(self, other):
        return CampaignValue(self.value & number(other))

    def __add__(self, other):return type(self)(self.value + number(other))
    __radd__ = __add__
    def __sub__(self, other):return type(self)(self.value - number(other))
    def __isub__(self, other):self.value -= number(other);return self
    def __mul__(self, other):return type(self)(self.value * number(other))
    __rmul__ = __mul__
    def __floordiv__(self, other):return type(self)(self.value // number(other))
    def __mod__(self, other):return type(self)(self.value % number(other))
    def __rshift__(self, other):return type(self)(self.value >> number(other))
    def __le__(self, other):return self.value <= number(other)

class CampaignRuntime(Runtime):
    P2, Set, Clear = 1, 4, 5
    EUDVariable=CampaignValue

    def __init__(self, settings_override=None):
        types.ModuleType.__init__(self,'eudplib')
        self.memory=FakeMemory(); self.cp=7; self.minerals=40; self.gas=0
        self.texts=[];self.branches=[];self.map_writes=[];self.switch=False;self.victories=[]
        module=types.ModuleType('original_campaign_under_test');module.settings={'mission':'101'}
        if settings_override:module.settings.update(settings_override)
        with patch.dict(sys.modules,{'eudplib':self}):
            exec(compile(PLUGIN.read_text(encoding='utf-8'),str(PLUGIN),'exec'),module.__dict__)
        module.emit_build_info=lambda:None
        self.plugin=module;module.onPluginStart()
        assert self.cp==7 and not self.branches

    def f_dwread_epd(self,address):
        return CampaignValue(struct.unpack('<I',self.memory.read(address*4,4))[0])

    def SetSwitch(self,index,value):
        assert index==255 and value==self.Clear
        return lambda:setattr(self,'switch',False)

    def Switch(self,index,value):
        assert index==255 and value==self.Set
        return self.switch

    def DisplayText(self,text):
        if isinstance(text,bytes):text=text.decode('utf-8')
        return lambda:self.texts.append((self.cp,text))

    def SetResources(self,*args):
        raise AssertionError('Original campaign plugin must never modify battle resources')

    def Victory(self):
        return lambda:self.victories.append(self.cp)

    def response(self,*,completed=0,**kwargs):
        super().response(**kwargs);self.memory.set(41,completed)

    def EUDElse(self):
        def alternate():
            active = not self.branches[-1]
            self.branches[-1] = True
            return active
        return alternate

class OriginalCampaignPluginTests(unittest.TestCase):
    def test_initial_load101_keeps_resources_and_cp(self):
        r=CampaignRuntime();q=read_request(r.memory,BASE)
        self.assertEqual((q.mission,q.state,q.operation,q.sequence,q.gold_delta),(101,1,1,2,0))
        self.assertEqual((r.cp,r.minerals,r.gas,r.switch),(7,40,0,False))

    def test_completed_objective_waits_for_late_manager(self):
        r=CampaignRuntime();r.switch=True
        for _ in range(100):r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(8),len(r.texts),r.victories),(1,2,1,[]))
        r.response();r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(9),r.memory.get(14)),(3,2,0))

    def test_durable_ack_then_48_ticks_then_single_p2_victory(self):
        r=CampaignRuntime();r.restored();r.switch=True;r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(8)),(3,6))
        for _ in range(100):r.tick()
        self.assertEqual((r.memory.get(8),r.victories),(6,[]))
        r.response(seq=4,status=2,echo=6,gold=37,completed=1);r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(8),r.victories),(4,8,[]))
        for _ in range(46):r.tick()
        self.assertEqual(r.victories,[])
        r.tick();self.assertEqual(r.victories,[1])
        for _ in range(100):r.tick()
        self.assertEqual((r.victories,r.minerals,r.gas,r.cp),([1],40,0,7))

    def test_replay_requires_objective_and_never_commits(self):
        r=CampaignRuntime();r.response(completed=1);r.tick()
        for _ in range(60):r.tick()
        self.assertEqual((r.memory.get(7),r.victories),(2,[]))
        r.switch=True;r.tick()
        self.assertEqual((r.memory.get(7),r.memory.get(9)),(4,0))
        for _ in range(47):r.tick()
        self.assertEqual(r.victories,[1])
        self.assertFalse(any(i==9 and value==2 for i,value,_ in r.map_writes))

    def test_other_completion_bits_do_not_skip_commit(self):
        r=CampaignRuntime();r.response(completed=2);r.tick();r.switch=True;r.tick()
        self.assertEqual(r.memory.get(7),3)

    def test_load_rejects_incomplete_wrong_echo_and_bad_nonce(self):
        for kwargs in ({'seq':3},{'echo':4},{'status':2},{'nonce':(0,0,0,0)}):
            with self.subTest(kwargs=kwargs):
                r=CampaignRuntime();r.switch=True;r.response(**kwargs);r.tick()
                self.assertEqual((r.memory.get(7),r.victories),(1,[]))

    def test_torn_completed_mask_is_not_accepted(self):
        r=CampaignRuntime();r.switch=True;r.response(completed=1);reads=0
        def change(address,size):
            nonlocal reads
            if address==BASE+128:
                reads+=1
                if reads==2:r.memory.set(32,4)
        r.memory.on_read=change;r.tick()
        self.assertEqual((r.memory.get(7),r.victories),(1,[]))

    def test_wrong_nonce_ack_is_ignored_then_fresh_valid_ack_works(self):
        r=CampaignRuntime();r.restored();r.switch=True;r.tick()
        r.response(seq=4,status=2,echo=6,nonce=(1,*NONCE[1:]));r.tick()
        self.assertEqual((r.memory.get(7),r.victories),(3,[]))
        r.response(seq=6,status=2,echo=6);r.tick()
        self.assertEqual(r.memory.get(7),4)

    def test_error_holds_victory_and_does_not_repeat_text(self):
        for after_load in (False,True):
            with self.subTest(after_load=after_load):
                r=CampaignRuntime();r.switch=True
                if after_load:r.response();r.tick()
                r.response(seq=4 if after_load else 2,status=3,echo=6 if after_load else 2,nonce=(0,0,0,0));r.tick()
                texts=list(r.texts)
                for _ in range(100):r.tick()
                self.assertEqual((r.memory.get(7),r.victories,r.texts),(5,[],texts))

    def test_cp_and_seqlock_ownership_every_transition(self):
        r=CampaignRuntime();r.cp=5;r.restored();r.switch=True;r.tick();r.response(seq=4,status=2,echo=6);r.tick()
        self.assertEqual(r.cp,5)
        self.assertTrue(all(player==1 for player,_ in r.texts))
        self.assertTrue(all(index<32 for index,_,_ in r.map_writes))
        self.assertTrue(all(seq&1 for index,_,seq in r.map_writes if index in (7,9,10,11,12,13,14,15)))

    def test_real_store_save_restart_and_completed_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            db=Path(folder)/'original.sqlite3'
            r=CampaignRuntime();store=CampaignStore(db,new_profile='original');d=Dispatcher(r.memory,BASE,store)
            d.poll();r.tick();self.assertEqual(d.poll()['status'],'restored');r.tick()
            r.switch=True;r.tick();self.assertEqual(d.poll()['status'],'committed');r.tick()
            self.assertEqual((store.status()['gold'],store.status()['completed_mask'],store.status()['revision']),(0,1,1))
            replay=CampaignRuntime();reopened=CampaignStore(db,new_profile='original');d2=Dispatcher(replay.memory,BASE,reopened)
            d2.poll();replay.tick();self.assertEqual(d2.poll()['status'],'restored');replay.tick()
            replay.switch=True;replay.tick()
            for _ in range(47):replay.tick()
            self.assertEqual(replay.victories,[1]);self.assertEqual(reopened.status()['revision'],1)

    def test_disk_error_never_acknowledges_but_retry_same_request_succeeds(self):
        with tempfile.TemporaryDirectory() as folder:
            store=CampaignStore(Path(folder)/'original.sqlite3',new_profile='original')
            r=CampaignRuntime();d=Dispatcher(r.memory,BASE,store);d.poll();r.tick();d.poll();r.tick();r.switch=True;r.tick()
            before=bytes(r.memory.data[128:172]);request=read_request(r.memory,BASE)
            with patch.object(store,'complete',side_effect=OSError('disk unavailable')):
                with self.assertRaises(OSError):d.poll()
            self.assertEqual(bytes(r.memory.data[128:172]),before);r.tick()
            self.assertEqual((r.memory.get(7),r.victories,store.status()['completed_mask']),(3,[],0))
            self.assertEqual(read_request(r.memory,BASE).nonce,request.nonce)
            self.assertEqual(d.poll()['status'],'committed');r.tick();self.assertEqual(r.memory.get(7),4)

    def test_no_resource_actions_or_independent_loop_or_talent_effects(self):
        tree=ast.parse(PLUGIN.read_text(encoding='utf-8'))
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        self.assertFalse(calls & {'SetResources','ModifyUnitHitPoints','CreateUnit','SaveMap','LoadMap','EUDDoEvents','EUDInfLoop','RunTrigTrigger'})
        self.assertTrue({'f_getcurpl','f_setcurpl','Victory','Switch'}<=calls)

class OriginalFormatTests(unittest.TestCase):
    def test_row_conversion_preserves_each_player_not_just_flat_prefix(self):
        for old,new in ((46,61),(24,44)):
            raw=bytes((row*7+index)%256 for row in range(38) for index in range(old))
            output=builder.extend_rows(raw,old,new)
            for row in range(38):
                self.assertEqual(output[row*new:row*new+old],raw[row*old:(row+1)*old])
                self.assertEqual(output[row*new+old:(row+1)*new],bytes(new-old))

    def test_each_cost_array_preserves_values_and_padding(self):
        for old,new,fields,pad in ((46,61,6,1),(24,44,4,0)):
            values=[(field*500+index) for field in range(fields) for index in range(old)]
            raw=bytes((i%2 for i in range(old)))+struct.pack('<'+'H'*len(values),*values)
            output=builder.extend_costs(raw,old,new,fields,bool(pad))
            self.assertEqual(output[:old],raw[:old]);self.assertEqual(output[old:new],b'\x01'*(new-old))
            for field in range(fields):
                restored=struct.unpack_from('<'+'H'*new,output,new+pad+field*new*2)
                self.assertEqual(restored[:old],tuple(values[field*old:(field+1)*old]))
                self.assertEqual(restored[old:],(0,)*(new-old))

    def test_actual_source_only_bw_production_units_are_blocked(self):
        chk=builder.make_chk(builder.SOURCE.read_bytes());original=dict(chk.sections)
        builder.legacy_to_expansion(chk)
        for unit in range(228):
            for row in range(25):
                actual=chk.getsection('PUNI')[row*228+unit]
                self.assertEqual(actual,0 if unit in builder.BW_UNITS else original[b'PUNI'][row*228+unit])

    def test_patch_only_original_victory_32_bytes(self):
        chk=builder.make_chk(builder.SOURCE.read_bytes());original=chk.getsection('TRIG');builder.patch_victory(chk);modified=chk.getsection('TRIG')
        self.assertEqual(modified[:2720],original[:2720]);self.assertEqual(modified[2752:],original[2752:])
        self.assertEqual(modified[2720+26:2720+29],bytes([13,4,4]))
        self.assertEqual(struct.unpack_from('<I',modified,2720+20)[0],255)

    def test_final_official_artifact_preserves_source_and_assets(self):
        evidence=builder.inspect_output()
        self.assertEqual((evidence['mission_id'],evidence['human_player'],evidence['audio_files_verified']),(101,'P2',8))
        self.assertTrue(evidence['all_9_original_trigger_bodies_and_order_verified'])
        self.assertFalse(evidence['native_verified'])

if __name__=='__main__':unittest.main()
