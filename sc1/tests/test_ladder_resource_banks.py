"""Campaign-wide resource geometry and regression checks; no native game use."""
import json,struct,unittest
from pathlib import Path
from sc1.native_campaign import ladder_resource_banks as banks,build_all_campaigns as maps

class LadderResourceBanksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(maps.RECEIPT.read_text('utf8'))['maps']
        cls.boxes=banks.rules.geometry.load_unit_geometry()[0]

    def test_gas_cannot_be_inserted_in_a_wide_mineral_gap(self):
        info=[(128,240,176,11),(512,240,176,11),(320,240,188,11)]
        self.assertFalse(banks.gas_separate(info,[0,1],[2],self.boxes))
        info[2]=(320,48,188,11)
        self.assertTrue(banks.gas_separate(info,[0,1],[2],self.boxes))

    def test_separated_resource_pockets_are_not_a_compact_bank(self):
        self.assertFalse(banks.compact_bank([(128,240,176,11),(512,240,176,11)],[0,1],self.boxes))
        self.assertTrue(banks.compact_bank([(128,240,176,11),(192,240,176,11)],[0,1],self.boxes))

    def test_straight_rows_cannot_pass_as_ladder_curves(self):
        for points in ([(x,160) for x in range(0,384,64)],
                       [(192,y) for y in range(0,192,32)],
                       [(x,x) for x in range(0,384,64)],
                       [(x,160) for x in range(0,768,64)]+[(800,192)]):
            self.assertFalse(banks.curved_bank(points)['passed'])
        self.assertTrue(banks.curved_bank(banks.REFERENCE_EAST)['passed'])

    def test_campaign_size_templates_have_no_straight_fallback(self):
        for count in range(3,34):
            candidates=list(banks.formations(count,(1024,1024)))
            self.assertTrue(candidates,count)
            for points,_,_ in candidates:
                self.assertEqual(len(points),count)
                self.assertTrue(banks.curved_bank(points)['passed'],(count,points))

    def test_sunken_guard_includes_gas_and_worker_envelope(self):
        threats=[((-32,-32,32,32),224)]
        near=banks.rules.geometry._rect(352,0,188,self.boxes)
        far=banks.rules.geometry._rect(448,0,188,self.boxes)
        self.assertGreater(banks.native_rect_distance(near,threats[0][0]),224)
        self.assertFalse(banks.sunken_clear(near,threats))
        self.assertTrue(banks.sunken_clear(far,threats))
        self.assertFalse(banks.sunken_route_clear((-400,0),(400,0),threats))

    def test_bw_terran8_six_oclock_minerals_and_gas_avoid_sunkens(self):
        row=next(r for r in self.rows if r['mission_id']==508)
        protected=[b for b in row['ladder_resource_banks']['bases'] if b.get('sunken_avoidance')]
        self.assertEqual(len(protected),1)
        base=protected[0];self.assertEqual(base['anchor']['center'],[3168,5456])
        self.assertEqual((len(base['mineral_indices']),len(base['gas_indices'])),(12,1))
        chk=maps.CHK(Path(row['output']).read_bytes());info=list(map(banks.rules.geometry._info,banks.rules.geometry._records(chk)))
        threats=banks.sunken_threats(info,[0,4,5],self.boxes)
        self.assertEqual(len(threats),91)
        for index in base['mineral_indices']+base['gas_indices']:
            self.assertTrue(banks.sunken_clear(banks.rules.geometry._rect(*info[index][:2],info[index][2],self.boxes),threats))
            self.assertTrue(banks.sunken_route_clear(base['anchor']['center'],info[index][:2],threats))
        self.assertTrue(base['audit']['sunken_safety']['safe_mining_routes'])

    def test_mixed_height_and_cliff_footprints_are_rejected(self):
        heights=[bytearray([1]*16) for _ in range(16)]
        self.assertTrue(banks.flat_rect(heights,(32,32,64,64),1))
        heights[5][5]=0;self.assertFalse(banks.flat_rect(heights,(32,32,64,64),1))
        heights[5][5]=255;self.assertFalse(banks.flat_rect(heights,(32,32,64,64),1))

    def test_all_main_and_expansion_sites(self):
        self.assertEqual(len(self.rows),63);sites=0;expansions=0
        for row in self.rows:
            chk=maps.CHK(Path(row['output']).read_bytes());report=row['ladder_resource_banks']
            info=list(map(banks.rules.geometry._info,banks.rules.geometry._records(chk)))
            heights=banks.terrain_heights(chk)
            self.assertEqual(len(report['bases']),len(row['courtyard_resource_layout']['bases']))
            covered=[i for base in report['bases'] for i in base['mineral_indices']]
            self.assertEqual(len(covered),len(set(covered)))
            self.assertEqual(set(covered),{i for i,p in enumerate(info) if p[2] in banks.rules.MINERALS})
            for base in report['bases']:
                sites+=1;expansions+=base['anchor']['kind']=='expansion'
                with self.subTest(mission=row['mission_id'],center=base['anchor']['center']):
                    self.assertNotEqual(base['status'],'unresolved')
                    proof=banks.audit_base(chk,info,base,heights,self.boxes)
                    self.assertTrue(proof['passed'],proof);self.assertEqual(base['audit'],proof)
                    self.assertEqual(proof['curved_bank']['applicable'],len(base['mineral_indices'])>=3)
                    for gas in proof['gas_exits'].values():self.assertTrue(gas['preferred_32px_offset_exit_clear'])
        self.assertEqual(sites,345);self.assertGreater(expansions,100)

    def test_only_resource_coordinates_change_and_undo_is_exact(self):
        for row in self.rows:
            final=maps.CHK(Path(row['output']).read_bytes());old=maps.CHK(final.save())
            banks.undo(old,row['ladder_resource_banks'])
            a=old.getsection('UNIT');b=final.getsection('UNIT');self.assertEqual(len(a),len(b))
            for at in range(0,len(a),36):
                self.assertEqual(a[at:at+4],b[at:at+4]);self.assertEqual(a[at+8:at+36],b[at+8:at+36])
                if a[at:at+36]!=b[at:at+36]:self.assertIn(struct.unpack_from('<H',a,at+8)[0],banks.rules.MINERALS|banks.gas.GAS_TYPES)
            for tag in final.sections:
                if tag!=b'UNIT':self.assertEqual(old.sections[tag],final.sections[tag])

    def test_reported_maps_and_scripted_mineral(self):
        for mid in (108,503):
            row=next(r for r in self.rows if r['mission_id']==mid)
            self.assertTrue(row['ladder_resource_banks']['moves'])
            self.assertTrue(all(b['audit']['passed'] for b in row['ladder_resource_banks']['bases']))
        row=next(r for r in self.rows if r['mission_id']==608)
        final=maps.CHK(Path(row['output']).read_bytes());old=maps.CHK(final.save());banks.undo(old,row['ladder_resource_banks'])
        self.assertEqual(old.getsection('UNIT')[19*36:20*36],final.getsection('UNIT')[19*36:20*36])

    def test_occupied_virtual_expansion_gets_a_legal_adjacent_site(self):
        row=next(r for r in self.rows if r['mission_id']==515)
        base=next(b for b in row['ladder_resource_banks']['bases'] if b['anchor']['center']==[5952,3696])
        chk=maps.CHK(Path(row['output']).read_bytes());info=list(map(banks.rules.geometry._info,banks.rules.geometry._records(chk)))
        self.assertTrue(banks.corner.depot_sites(chk,info,base['anchor'],banks.mining.load_buildable_grid(chk),self.boxes)[0])

    def test_bw_terran4_scripted_silo_destinations_remain_clear(self):
        from sc1.native_campaign import terran4_repair
        row=next(r for r in self.rows if r['mission_id']==504)
        terran4_repair.verify_silo_destinations(maps.CHK(Path(row['output']).read_bytes()))

    def test_final_wave_relocation_preserves_resource_reservations(self):
        # These missions select a new wave route after placing resources.
        # Replaying a layout must use its initial reservation points.
        for mid in (308,504):
            difficulty=next(r for r in self.rows if r['mission_id']==mid)['difficulty']
            initial=[point for origin in difficulty['resource_wave_origins'] for point in origin['cells']]
            final=[point for origin in difficulty['wave_origins'] for point in origin['cells']]
            self.assertNotEqual(initial,final)
            self.assertEqual(maps.mineral_reserved_points(difficulty),initial)

    def test_reference_is_a_real_side_arc_with_separate_gas(self):
        # Original NE main coordinates of the pinned installed Fighting Spirit.
        info=[(x+3808,y+272,176,11) for x,y in banks.REFERENCE_EAST]+[(3808,96,188,11)]
        self.assertEqual(len(banks.REFERENCE_EAST),9)
        self.assertTrue(banks.gas_separate(info,list(range(9)),[9],self.boxes))
        self.assertEqual(len(banks.REFERENCE_MAPS),4)

if __name__=='__main__':unittest.main()
