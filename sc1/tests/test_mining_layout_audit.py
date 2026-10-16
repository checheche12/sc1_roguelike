from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from sc1.native_campaign import mining_layout_audit as audit
from sc1.native_campaign.build_plain_chk import CHK

def fake_chk(width=16,height=16):
    fields=[(b'DIM ',struct.pack('<HH',width,height)),(b'ERA ',struct.pack('<H',0)),(b'MTXM',bytes(width*height*2))]
    return CHK(b''.join(struct.pack('<4sI',name,len(body))+body for name,body in fields))

def terrain(flags=0,walk=None):
    cv5=bytearray(52);struct.pack_into('<H',cv5,2,flags)
    return bytes(cv5),struct.pack('<16H',*([1]*16 if walk is None else walk))

class MiningLayoutAuditTests(unittest.TestCase):
    def test_buildable_requires_cv5_and_all_walk_minitiles(self):
        chk=fake_chk()
        with patch.object(audit,'_terrain_bytes',return_value=terrain()):
            self.assertTrue(audit.load_buildable_grid(chk)[2][2])
        with patch.object(audit,'_terrain_bytes',return_value=terrain(0x80)):
            self.assertFalse(audit.load_buildable_grid(chk)[2][2])
        partial=[1]*16;partial[7]=0
        with patch.object(audit,'_terrain_bytes',return_value=terrain(walk=partial)):
            self.assertFalse(audit.load_buildable_grid(chk)[2][2])

    def test_foundation_full_size_alignment_and_edges(self):
        chk=fake_chk(8,8)
        with patch.object(audit,'_terrain_bytes',return_value=terrain()):
            self.assertTrue(audit.foundation_buildable(chk,(128,80),106))
            self.assertFalse(audit.foundation_buildable(chk,(129,80),106))
            self.assertFalse(audit.foundation_buildable(chk,(32,80),106))
            self.assertFalse(audit.foundation_buildable(chk,(128,208),106))
            self.assertTrue(audit.foundation_buildable(chk,(128,96),188))

    def test_24px_worker_rejects_16px_corridor_accepts_32px(self):
        chk=fake_chk()
        def walk(gap):
            grid=[bytearray(b'\x01'*16) for _ in range(16)]
            for y in range(6,10):
                for x in range(16):grid[y][x]=int(5<=x<5+gap)
            return grid
        with patch.object(audit,'_raw_walk',return_value=walk(2)):
            labels,_=audit.worker_components(chk,[])
            self.assertNotEqual(labels[3][6],labels[12][6])
        with patch.object(audit,'_raw_walk',return_value=walk(4)):
            labels,_=audit.worker_components(chk,[])
            self.assertEqual(labels[3][6],labels[12][6])

    def test_front_blockage_is_distinct_from_any_side_access(self):
        chk=fake_chk(32,32);raw=[bytearray(b'\x01'*128) for _ in range(128)]
        before=[(192,208,106,1),(320,208,176,11),(384,208,177,11)]
        after=[before[0],(384,144,176,11),before[2]]
        anchor={'kind':'existing_depot','center':[192,208],'depot_type':106,'unit_index':0}
        with patch.object(audit,'_raw_walk',return_value=raw),patch.object(audit,'foundation_buildable',return_value=True):
            old=audit.audit_field(chk,before,[1,2],anchor,(1,0))
            new=audit.audit_field(chk,after,[1,2],anchor,(1,0))
        outer=next(r for r in old['minerals'] if r['unit_index']==2)
        self.assertTrue(outer['any_side_reachable'])
        self.assertFalse(outer['depot_facing_front_reachable'])
        self.assertEqual(new['front_reachable_count'],2)
        self.assertTrue(new['resource_depot_clear'])

    def test_full_front_corner_lane_remains_a_valid_24px_approach(self):
        chk=fake_chk(32,32);raw=[bytearray(b'\x01'*128) for _ in range(128)]
        rows=[(384,80,106,1),(384,304,176,11),(384,272,200,11)]
        anchor={'kind':'existing_depot','center':[384,80],'depot_type':106,'unit_index':0}
        original=audit._footprint
        def footprint(x,y,unit):
            # Narrow fixed obstruction blocks the middle of a 64px front;
            # workers still fit around it at both ends of that same front.
            return (x-4,y-12,x+4,y+12) if unit==200 else original(x,y,unit)
        with patch.object(audit,'_raw_walk',return_value=raw),patch.object(audit,'_footprint',side_effect=footprint),patch.object(audit,'foundation_buildable',return_value=True):
            result=audit.audit_field(chk,rows,[1],anchor,(0,1))
        self.assertEqual(result['front_reachable_count'],1)

    def test_hatchery_collision_allows_lane_inside_placement_foundation(self):
        # Actual Hatchery right edge242 to wall272 leaves30px for a worker.
        # Using its placement right edge256 would falsely reduce this to16px.
        self.assertEqual(audit._footprint(192,208,131),(143,176,242,241))
        raw=[bytearray(int(28<=x<36) for x in range(64)) for _ in range(64)]
        rows=[(192,208,131,0),(276,256,200,11)];original=audit._footprint
        def footprint(x,y,unit):
            return (272,0,280,512) if unit==200 else original(x,y,unit)
        with patch.object(audit,'_raw_walk',return_value=raw),patch.object(audit,'_footprint',side_effect=footprint):
            labels,_=audit.worker_components(fake_chk(),rows)
        self.assertGreaterEqual(labels[14][32],0)
        self.assertEqual(labels[14][32],labels[40][32])

if __name__=='__main__':unittest.main()
