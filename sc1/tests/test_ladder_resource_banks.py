"""Campaign-wide resource geometry and regression checks; no native game use."""
import json,math,struct,unittest
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

    def test_balanced_groups_preserve_count_and_limit_each_depot_to_twelve(self):
        for count,expected in ((1,[1]),(12,[12]),(13,[6,7]),(19,[9,10]),(25,[8,8,9]),(33,[11,11,11]),(34,[11,11,12])):
            self.assertEqual(banks.balanced_group_sizes(count),expected)

    def test_second_rows_and_alternating_staggered_rows_are_rejected(self):
        center=(1024,1040)
        for relative in (
            [(192,0),(256,0),(192,32),(256,32)],
            [(-64,-160),(0,-160),(64,-160),(-64,-192),(0,-192),(64,-192)],
            [(-128,-160),(-64,-192),(0,-160),(64,-192),(128,-160)]):
            self.assertFalse(banks.single_layer([(center[0]+x,center[1]+y) for x,y in relative],center))
        self.assertTrue(banks.single_layer([(960,880),(1024,880),(1088,880),(1216,912),(1216,944)],center))

    def test_army_aisles_keep_every_patch_on_one_nearest_landing_front(self):
        center=(1024,1040);candidates=list(banks.aisled_minimum_arcs(9,center))
        self.assertTrue(candidates)
        for points,direction,shape in candidates:
            self.assertEqual(len(set(points)),9)
            self.assertTrue(banks.single_layer(points,center))
            self.assertTrue(banks.rules._resource_clear(center,[(*p,176,11) for p in points]))
            self.assertTrue(all(abs(x-center[0])==192 or abs(y-center[1])==160 for x,y in points))

    def test_grouped_bw_protoss3_preserves_army_routes(self):
        row=next(r for r in self.rows if r['mission_id']==603)
        final=maps.CHK(Path(row['output']).read_bytes());before=maps.CHK(final.save())
        banks.undo(before,row['ladder_resource_banks'])
        info=lambda chk:list(map(banks.rules.geometry._info,banks.rules.geometry._records(chk)))
        virtual=[(*a['center'],a['depot_type'],12) for a in row['ladder_resource_banks']['bases'][0]['planned_depot_sites']]
        old,new=info(before)+virtual,info(final)+virtual
        walk,_=banks.rules.geometry.load_terrain(final)
        army=banks.rules._worker_terrain(banks.rules._worker_terrain(banks.rules._worker_terrain(walk)))
        indices=[r['index'] for r in row['ladder_resource_banks']['moves']]
        self.assertTrue(banks.rules._army_route_ok(old,new,indices,army,self.boxes,{'baseline':old}))

    def test_separated_resource_pockets_are_not_a_compact_bank(self):
        self.assertFalse(banks.compact_bank([(128,240,176,11),(512,240,176,11)],[0,1],self.boxes))
        self.assertTrue(banks.compact_bank([(128,240,176,11),(192,240,176,11)],[0,1],self.boxes))

    def test_minimum_arc_touches_the_landing_exclusion_boundary(self):
        center=(1024,1040)
        candidates=[c for c in banks.formations(9,center) if c[2]['formation']=='minimum_landing_arc']
        self.assertTrue(candidates)
        for points,_,_ in candidates:
            for x,y in points:
                self.assertTrue(banks.rules._resource_clear(center,[(x,y,176,11)]))
                dx,dy=x-center[0],y-center[1]
                # The normal inward grid step crosses the native resource
                # exclusion rectangle; the diagonal corner is legal exactly.
                p=(x-(32 if dx>0 else -32),y) if abs(dx)==192 else (x,y-(32 if dy>0 else -32))
                self.assertFalse(banks.rules._resource_clear(center,[(*p,176,11)]))

    def test_remote_legal_mineral_is_pulled_to_minimum_landing_distance(self):
        center=(1024,1040)
        info=[(1408,1040,176,11)]
        self.assertTrue(banks.rules._resource_clear(center,info))
        def accept(candidate,changed):
            return None if banks.rules._resource_clear(center,candidate) else 'landing_resource_exclusion'
        tightened,proof=banks.tighten_bank(info,[0],center,accept)
        self.assertEqual(tightened,[(1216,1040,176,11)])
        self.assertEqual(proof['accepted_steps'],6)
        self.assertTrue(proof['no_legal_closer_grid_step'])
        self.assertEqual(set(proof['blocked_steps']),{'landing_resource_exclusion'})

    def test_minimum_search_preserves_script_locks_and_obstacles(self):
        center=(1024,1040);info=[(1408,1040,176,11)]
        result,proof=banks.tighten_bank(info,[0],center,lambda *_:'fixed_building')
        self.assertEqual(result,info);self.assertGreater(proof['blocked_steps']['fixed_building'],0)
        result,proof=banks.tighten_bank(info,[0],center,lambda *_:None,locked=[0])
        self.assertEqual(result,info);self.assertEqual(proof['locked_indices'],[0])

    def test_two_patch_edge_pocket_includes_both_horizontal_grid_phases(self):
        center=(96,1552)
        candidates=[set(points) for points,_,_ in banks.formations(2,center)]
        self.assertIn({(32,1392),(96,1392)},candidates)
        row=next(r for r in self.rows if r['mission_id']==603)
        base=next(b for b in row['ladder_resource_banks']['bases'] if b['anchor']['center']==list(center))
        self.assertLessEqual(sum(math.dist(center,p) for p in base['mineral_positions'])/2,166.164)

    def test_crowded_banks_do_not_prefer_remote_rows_or_a_farther_orientation(self):
        # These published banks exposed the two regressions: a 25-patch
        # expansion averaged 492px, and choosing only the first nearest-fit
        # orientation made BW Terran4's 220px bank worse (249px).
        # BW T4's former six-patch site is now part of a twelve-patch merged
        # field. Its old six-patch distance bound no longer describes that bank.
        for mid,center,limit in ((108,[192,592],320),):
            row=next(r for r in self.rows if r['mission_id']==mid)
            base=next(b for b in row['ladder_resource_banks']['bases'] if b['anchor']['center']==center)
            distances=[math.dist(center,p) for p in base['mineral_positions']]
            self.assertLess(sum(distances)/len(distances),limit,(mid,distances))

    def test_straight_rows_cannot_pass_as_ladder_curves(self):
        for points in ([(x,160) for x in range(0,384,64)],
                       [(192,y) for y in range(0,192,32)],
                       [(x,x) for x in range(0,384,64)],
                       [(x,160) for x in range(0,768,64)]+[(800,192)]):
            self.assertFalse(banks.curved_bank(points)['passed'])
        self.assertTrue(banks.curved_bank(banks.REFERENCE_EAST)['passed'])

    def test_campaign_size_templates_have_no_straight_fallback(self):
        for count in range(3,13):
            candidates=list(banks.formations(count,(1024,1024)))
            self.assertTrue(candidates,count)
            for points,direction,shape in candidates:
                self.assertEqual(len(points),count)
                self.assertTrue(banks.curved_bank(points)['passed'],(count,points))
                self.assertTrue(banks.single_layer(points,(1024,1024)),(count,points))
                self.assertEqual(shape['rows'],1)

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
        self.assertEqual(len(self.rows),63);sites=0;expansions=0;parents=0
        for row in self.rows:
            chk=maps.CHK(Path(row['output']).read_bytes());report=row['ladder_resource_banks']
            info=list(map(banks.rules.geometry._info,banks.rules.geometry._records(chk)))
            heights=banks.terrain_heights(chk)
            parents+=len(row['courtyard_resource_layout']['bases'])
            self.assertEqual(report['parent_resource_sites'],len(row['courtyard_resource_layout']['bases']))
            self.assertLessEqual(report['maximum_minerals_per_depot'],15)
            for parent,original in enumerate(row['courtyard_resource_layout']['bases']):
                groups=[b for b in report['bases'] if b['parent_site_index']==parent]
                sizes=[len(b['mineral_indices']) for b in groups]
                self.assertLessEqual(max(sizes),report['maximum_minerals_per_depot'])
                if len(groups)>1:self.assertGreater(min(sizes),7)
                self.assertLessEqual(max(sizes)-min(sizes),1)
                self.assertEqual(sum(sizes),len(original['mineral_indices']))
                self.assertEqual({i for b in groups for i in b['mineral_indices']},set(original['mineral_indices']))
                self.assertEqual(sum(bool(b['anchor'].get('additional_group_depot')) for b in groups),len(groups)-1)
            covered=[i for base in report['bases'] for i in base['mineral_indices']]
            self.assertEqual(len(covered),len(set(covered)))
            self.assertEqual(set(covered),{i for i,p in enumerate(info) if p[2] in banks.rules.MINERALS})
            for base in report['bases']:
                sites+=1;expansions+=base['anchor']['kind']=='expansion'
                with self.subTest(mission=row['mission_id'],center=base['anchor']['center']):
                    self.assertNotEqual(base['status'],'unresolved')
                    proof=banks.audit_base(chk,info,base,heights,self.boxes)
                    self.assertTrue(proof['passed'],proof);self.assertEqual(base['audit'],proof)
                    self.assertTrue(proof['depot_landing_resource_clear'])
                    self.assertTrue(proof['single_layer'])
                    self.assertTrue(proof['depot_foundation_clear'])
                    if base.get('placement_policy')!='reviewed_playtest_layout':
                        minimum=base['minimum_spacing']
                        self.assertTrue(minimum['no_legal_closer_grid_step'])
                        self.assertLessEqual(minimum['after_mean_center_distance_pixels'],minimum['before_mean_center_distance_pixels'])
                    self.assertEqual(proof['curved_bank']['applicable'],len(base['mineral_indices'])>=3)
                    for gas in proof['gas_exits'].values():self.assertTrue(gas['preferred_32px_offset_exit_clear'])
        self.assertEqual(parents,345);self.assertGreaterEqual(sites,345);self.assertLess(sites,413);self.assertGreater(expansions,100)

    def test_only_resources_reviewed_buildings_and_repaired_mobile_units_move(self):
        from sc1.native_campaign import mission_placement_fixes as fixes
        for row in self.rows:
            final=maps.CHK(Path(row['output']).read_bytes());old=maps.CHK(final.save())
            banks.undo(old,row['ladder_resource_banks'])
            repair=row['ladder_resource_banks'].get('spawn_placement',{})
            corrected={m['index']:m for m in repair.get('moves',[])}
            a=old.getsection('UNIT');b=final.getsection('UNIT');self.assertEqual(len(a),len(b))
            for at in range(0,len(a),36):
                self.assertEqual(a[at:at+4],b[at:at+4]);self.assertEqual(a[at+8:at+36],b[at+8:at+36])
                if a[at:at+36]!=b[at:at+36]:
                    unit=struct.unpack_from('<H',a,at+8)[0]
                    if unit not in banks.rules.MINERALS|banks.gas.GAS_TYPES:
                        if at//36 in corrected:
                            move=corrected[at//36]
                            self.assertEqual(move['original_actor'],at//36<repair['original_unit_count'])
                            if move['original_actor']:self.assertTrue(move['introduced_obstacles'])
                            self.assertLess(unit,106)
                            self.assertEqual(list(struct.unpack_from('<2H',a,at+4)),move['before'])
                            self.assertEqual(list(struct.unpack_from('<2H',b,at+4)),move['after'])
                            continue
                        expected=fixes.BUILDINGS.get(row['mission_id'],{}).get(at//36)
                        self.assertIsNotNone(expected)
                        kind,owner,old_position,dest=expected
                        self.assertEqual((unit,a[at+16],struct.unpack_from('<2H',a,at+4)),(kind,owner,old_position))
                        self.assertEqual(struct.unpack_from('<2H',b,at+4),dest)
            for tag in final.sections:
                if tag not in (b'UNIT',b'MRGN'):self.assertEqual(old.sections[tag],final.sections[tag])
            fixes.verify_locations(old,final,{'mission_id':row['mission_id']})

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

    def test_narrow_cliff_pockets_keep_single_layers_and_gas_exits(self):
        for mid,center,sizes in ((606,[480,3760],[8]),(609,[3072,1392],[12])):
            row=next(r for r in self.rows if r['mission_id']==mid)
            groups=[b for b in row['ladder_resource_banks']['bases'] if b['source_anchor']==center]
            self.assertEqual([len(b['mineral_indices']) for b in groups],sizes)
            self.assertTrue(all(b['audit']['single_layer'] and b['audit']['depot_foundation_clear'] for b in groups))
        row=next(r for r in self.rows if r['mission_id']==610)
        base=next(b for b in row['ladder_resource_banks']['bases'] if b['parent_site_index']==10)
        self.assertEqual(base['anchor']['center'],[3072,1328])
        self.assertEqual(base['anchor']['kind'],'expansion')
        self.assertEqual(len(base['mineral_indices']),6)
        self.assertTrue(base['audit']['gas_exits_clear'])

    def test_bw_terran4_scripted_silo_destinations_remain_clear(self):
        from sc1.native_campaign import terran4_repair
        row=next(r for r in self.rows if r['mission_id']==504)
        terran4_repair.verify_silo_destinations(maps.CHK(Path(row['output']).read_bytes()))

    def test_final_wave_relocation_preserves_resource_reservations(self):
        # These missions select a new wave route after placing resources.
        # Replaying a layout must use its initial reservation points.
        for mid in (110,308,504,606,609):
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
