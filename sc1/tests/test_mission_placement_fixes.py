"""Playtest placement regressions across the original and Brood War campaigns."""
import json
import struct
import unittest
from pathlib import Path
from sc1.native_campaign import build_all_campaigns as maps,ladder_resource_banks as banks
from sc1.native_campaign import mission_placement_fixes as fixes,settlement_terrain as terrain


class MissionPlacementFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows={r['mission_id']:r for r in json.loads(maps.RECEIPT.read_text('utf8'))['maps']}
        cls.boxes=banks.rules.geometry.load_unit_geometry()[0]

    def current(self,mid):
        row=self.rows[mid];chk=maps.CHK(Path(row['output']).read_bytes())
        return row,chk,fixes.units(chk)

    def before(self,mid):
        row,chk,_=self.current(mid);raw=bytearray(chk.getsection('UNIT'))
        for move in row['ladder_resource_banks']['playtest_placement']['changes']:
            struct.pack_into('<2H',raw,move['index']*36+4,*move['before'][:2])
        chk.setsection('UNIT',raw)
        return chk,fixes.units(chk)

    def test_terran8_neutral_addons_have_all_five_clear_parent_foundations(self):
        row,chk,info=self.current(108)
        proof=fixes.verify(chk,{'mission_id':108},row['ladder_resource_banks'])
        self.assertEqual(len(proof['addon_landings']),5)
        expected={239:(2592,3280),256:(1824,3536)}
        for i,center in expected.items():
            self.assertEqual(info[i][2:],(108,11))
            self.assertEqual(info[i][:2],(center[0]+96,center[1]+16))
            self.assertTrue(banks.rules._resource_clear(center,info))
        old,before=self.before(108)
        old_parent,_=fixes.parent_site(before[241])
        self.assertTrue(banks.rules._fixed_collision(fixes.addons.rect(old_parent,114),before,{241},self.boxes,mobile=False))
        # UNIT serialization/link fields stay intact; auto-attachment is provided
        # by the game's normal parent/addon placement rule, not a new trigger.
        self.assertEqual(chk.getsection('TRIG'),old.getsection('TRIG'))

    def test_terran9_mining_avoids_enemy_range_without_closing_army_paths(self):
        row,chk,info=self.current(109);old,before=self.before(109)
        threats=banks.sunken_threats(info,[3],self.boxes)
        self.assertTrue(any(not banks.sunken_clear(fixes.addons.rect(before[i][:2],before[i][2]),threats)
                            for i in fixes.TERRAN9_MINERALS))
        self.assertTrue(fixes.verify(chk,{'mission_id':109},row['ladder_resource_banks'])['passed'])
        walk,_=banks.rules.geometry.load_terrain(chk)
        army=banks.rules._worker_terrain(banks.rules._worker_terrain(banks.rules._worker_terrain(walk)))
        self.assertTrue(banks.rules._army_route_ok(before,info,list(fixes.TERRAN9_MINERALS),army,self.boxes,{'baseline':before}))

    def test_terran10_three_supply_depots_leave_resource_corridors(self):
        row,chk,info=self.current(110);old,before=self.before(110)
        minerals=[p for p in before if p[2] in banks.rules.MINERALS]
        old_gaps=[min(banks.rect_gap(fixes.addons.rect(before[i][:2],109),fixes.addons.rect(p[:2],p[2])) for p in minerals)
                  for i in fixes.BUILDINGS[110]]
        self.assertTrue(all(g<32 for g in old_gaps))
        self.assertTrue(fixes.verify(chk,{'mission_id':110},row['ladder_resource_banks'])['passed'])
        self.assertEqual(sum(p[2:]==(109,1) for p in before),sum(p[2:]==(109,1) for p in info))

    def test_zerg2_second_hatchery_serves_the_other_bank(self):
        row,chk,info=self.current(202);_,before=self.before(202)
        self.assertFalse(banks.rules._resource_clear(before[145][:2],before))
        self.assertTrue(banks.rules._resource_clear(info[145][:2],info))
        self.assertEqual(info[143],before[143])
        self.assertEqual(info[145],(512,720,131,3))
        group=next(g for g in row['ladder_resource_banks']['bases'] if g['anchor'].get('unit_index')==145)
        self.assertEqual(len(group['mineral_indices']),8)
        self.assertEqual(group['audit']['worker_access']['front_reachable_count'],8)

    def test_zerg4_rock_sprite_and_blocking_terrain_are_both_removed(self):
        row,chk,_=self.current(204);original=maps.CHK(Path(row['source']).read_bytes())
        self.assertFalse(banks.mining.foundation_buildable(original,(1856,1840),131))
        self.assertTrue(banks.mining.foundation_buildable(chk,(1856,1840),131))
        proof=terrain.verify(original,chk,{'mission_id':204},row['settlement_terrain'])
        self.assertEqual(len(proof['changed_tiles']),8)
        for tag,stride,kind in (('DD2 ',8,40),('THG2',10,2)):
            raw=chk.getsection(tag)
            self.assertNotIn((kind,1856,1856),[struct.unpack_from('<3H',raw,i) for i in range(0,len(raw),stride)])
            self.assertEqual(len(original.getsection(tag))-len(raw),stride)
        self.assertEqual(chk.getsection('ISOM'),original.getsection('ISOM'))

    def test_user_corrected_nydus_report_is_zerg8_not_zerg6(self):
        row,chk,info=self.current(208)
        self.assertEqual(info[197],(3552,3744,134,3))
        self.assertTrue(fixes.verify(chk,{'mission_id':208},row['ladder_resource_banks'])['passed'])
        self.assertNotIn(206,fixes.MISSIONS)
        self.assertNotIn('playtest_placement',self.rows[206]['ladder_resource_banks'])

    def test_all_reported_blocking_buildings_keep_clear_resource_corridors(self):
        for mid in fixes.BUILDINGS:
            row,chk,_=self.current(mid)
            self.assertTrue(fixes.verify(chk,{'mission_id':mid},row['ladder_resource_banks'])['passed'])

    def test_scripted_starting_cc_has_its_own_resource_location(self):
        row,chk,_=self.current(310)
        self.assertEqual(struct.unpack_from('<4I',chk.getsection('MRGN'),60),(384,768,512,864))
        self.assertTrue(fixes.verify(chk,{'mission_id':310},row['ladder_resource_banks'])['only_starting_cc_location_referenced'])

    def test_narrow_hill_has_connected_scv_exit_and_resource_fronts(self):
        row,chk,_=self.current(503)
        self.assertTrue(fixes.verify(chk,{'mission_id':503},row['ladder_resource_banks'])['all_worker_exit_edges_connected_to_minerals'])

    def test_merged_banks_and_wave_cells_do_not_overlap(self):
        from sc1.campaign.missions import load_missions
        missions={m['mission_id']:m for m in load_missions()}
        for mid in (110,606,609):
            row,chk,_=self.current(mid)
            fixes.verify_wave_cells(chk,missions[mid],row['difficulty'])

    def test_every_relocated_resource_has_a_distinct_clear_foundation(self):
        for mid in fixes.MISSIONS:
            row,chk,info=self.current(mid);model=banks.court._ground_model(info)
            for move in row['ladder_resource_banks']['playtest_placement']['changes']:
                i=move['index'];p=info[i]
                if p[2] not in banks.rules.MINERALS|banks.gas.GAS_TYPES:continue
                self.assertFalse(banks.rules._fixed_collision(fixes.addons.rect(p[:2],p[2]),model,{i},self.boxes,mobile=False),(mid,i))

    def test_bw_terran6_starting_ground_army_has_an_open_exit(self):
        row,chk,info=self.current(506)
        labels,sizes=banks.mining.worker_components(chk,banks.court._ground_model(info))
        largest=max(range(len(sizes)),key=sizes.__getitem__)
        starters=[p for p in info if p[3]==0 and p[2] in (37,41)]
        self.assertTrue(starters)
        for x,y,unit,owner in starters:
            nearby={labels[yy][xx] for yy in range(y//8-2,y//8+3) for xx in range(x//8-2,x//8+3)}
            self.assertIn(largest,nearby,(x,y,unit))
        self.assertEqual(labels[2800//8][1248//8],largest)

    def test_coordinate_repairs_are_exactly_reversible_and_replayable(self):
        for mid in fixes.MISSIONS:
            row,chk,_=self.current(mid);before,_=self.before(mid)
            # Full layout undo also restores the approved non-resource buildings.
            restored=maps.CHK(chk.save());banks.undo(restored,row['ladder_resource_banks'])
            self.assertEqual(banks.rules._hash(restored.getsection('UNIT')),row['ladder_resource_banks']['input_unit_sha256'])
            a,b=before.getsection('UNIT'),chk.getsection('UNIT')
            self.assertEqual(len(a),len(b))
            for at in range(0,len(a),36):
                self.assertEqual(a[at:at+4]+a[at+8:at+36],b[at:at+4]+b[at+8:at+36])


if __name__=='__main__':unittest.main()
