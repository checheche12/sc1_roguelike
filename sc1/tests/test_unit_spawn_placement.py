"""Actual map footprint, preservation and deterministic repair regressions."""
import copy
import hashlib
import json
from pathlib import Path
import struct
import unittest
from unittest.mock import patch

from sc1.campaign.missions import load_missions
from sc1.native_campaign import build_all_campaigns as maps, unit_spawn_placement as placement


class UnitSpawnPlacementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = json.loads(maps.RECEIPT.read_text('utf-8'))['maps']
        cls.missions = {r['mission_id']:r for r in load_missions()}

    def current(self, row):
        return maps.CHK(Path(row['output']).read_bytes())

    def test_diagonal_tank_and_non_tank_intersections_are_rejected(self):
        chk = self.current(self.rows[0])
        from sc1.native_campaign.base_defenses import record
        walk = [bytearray([1])*512 for _ in range(512)]
        for unit in (3,5,30,66,83):
            chk.setsection('UNIT',record(unit,6,1000,1000,1)+record(unit,6,1029,1029,2))
            with patch.object(placement.geo,'load_terrain',return_value=(walk,{})), patch.object(placement.banks,'terrain_heights',return_value=walk):
                field=placement.Field(chk)
            self.assertGreater(29*29*2,40*40)
            self.assertIn('ground_overlap',field.problems(1)[0],unit)
            self.assertFalse(field.problems(1,(1080,1000,unit,6))[0],unit)

    def test_every_final_ground_addition_has_a_clear_full_footprint(self):
        checked=0;changed=0
        for row in self.rows:
            chk=self.current(row);mission=self.missions[row['mission_id']]
            checked+=placement.verify(chk,mission,row['ladder_resource_banks'])
            changed+=row['ladder_resource_banks']['spawn_placement']['moved_units']
        self.assertGreater(checked,4000)
        self.assertGreater(changed,79)

    def test_repair_only_changes_affected_mobile_xy_and_is_exactly_replayable(self):
        for row in self.rows:
            chk=self.current(row);final=chk.save();report=copy.deepcopy(row['ladder_resource_banks'])
            proof=report.pop('spawn_placement');before=bytearray(chk.getsection('UNIT'));after=bytes(before)
            moved={m['index'] for m in proof['moves']}
            for m in proof['moves']:
                i=m['index']
                self.assertEqual(m['original_actor'],i<proof['original_unit_count'])
                if m['original_actor']:self.assertTrue(m['introduced_obstacles'])
                self.assertLess(m['unit'],106);self.assertTrue(placement.grounded(m['unit']))
                self.assertEqual(list(struct.unpack_from('<HH',before,i*36+4)),m['after'])
                self.assertLessEqual(sum((a-b)**2 for a,b in zip(m['before'],m['after'])),placement.MAX_MOVE**2)
                struct.pack_into('<HH',before,i*36+4,*m['before'])
                self.assertEqual(before[i*36:i*36+4],after[i*36:i*36+4])
                self.assertEqual(before[i*36+8:i*36+36],after[i*36+8:i*36+36])
            self.assertEqual(hashlib.sha256(before).hexdigest(),proof['input_unit_sha256'])
            for i in range(proof['original_unit_count']):
                if i not in moved:self.assertEqual(before[i*36:i*36+36],after[i*36:i*36+36])
            report['moves']=[m for m in report['moves'] if m['index'] not in moved]
            report['output_unit_sha256']=proof['input_unit_sha256'];chk.setsection('UNIT',bytes(before))
            placement.apply(chk,self.missions[row['mission_id']],report,reserved_points=maps.mineral_reserved_points(row['difficulty']))
            self.assertEqual(report,row['ladder_resource_banks']);self.assertEqual(chk.save(),final)

    def test_original_troops_move_only_for_new_obstacle_collisions(self):
        checked=moved=0
        for row in self.rows:
            chk=self.current(row);mission=self.missions[row['mission_id']]
            proof=row['ladder_resource_banks']['spawn_placement'];raw=bytearray(chk.getsection('UNIT'))
            for move in proof['moves']:struct.pack_into('<HH',raw,move['index']*36+4,*move['before'])
            chk.setsection('UNIT',raw)
            conflicts=placement.Field(chk).original_conflicts(placement.original_points(mission))
            original_moves={m['index']:m['introduced_obstacles'] for m in proof['moves'] if m['original_actor']}
            self.assertEqual(conflicts,original_moves)
            self.assertEqual(len(conflicts),proof['moved_original_units'])
            checked+=proof['checked_original_ground_units'];moved+=len(conflicts)
        self.assertGreater(checked,1000);self.assertEqual(moved,42)

    def test_building_only_objectives_do_not_select_enemy_mobile_troops(self):
        row=next(r for r in self.rows if r['mission_id']==405)
        self.assertNotIn(38,placement.spatial_selectors(self.current(row),3,6))

    def test_forged_report_cannot_hide_a_new_collision(self):
        row=next(r for r in self.rows if r['mission_id']==108);chk=self.current(row)
        report=copy.deepcopy(row['ladder_resource_banks']);proof=report['spawn_placement']
        move=next(m for m in proof['moves'] if 'ground_overlap' in m['reasons'])
        raw=bytearray(chk.getsection('UNIT'));struct.pack_into('<HH',raw,move['index']*36+4,*move['before'])
        chk.setsection('UNIT',raw);report['output_unit_sha256']=proof['output_unit_sha256']=hashlib.sha256(raw).hexdigest()
        with self.assertRaises(AssertionError):placement.verify(chk,self.missions[108],report)

    def test_runtime_guard_posts_follow_corrected_additions(self):
        from sc1.native_campaign import base_defenses
        header=(maps.ROOT/'plugin/include/base_defenses.generated.h').read_text('utf-8')
        for row in self.rows:
            points=list(map(placement.geo._info,placement.geo._records(self.current(row))))
            for offset,item in enumerate(row['base_defenses']['added']):
                if item['role']!='defender':continue
                x,y,unit,owner=points[row['base_defenses']['base_unit_count']+offset]
                self.assertIn('{'+','.join(map(str,(row['mission_id'],unit,owner,x,y)))+'},',header)


if __name__ == '__main__':
    unittest.main()
