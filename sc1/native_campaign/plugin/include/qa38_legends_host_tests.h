#pragma once
namespace host_test {
inline constexpr std::size_t qa38_group_count=14;
namespace qa38_fixture {
inline void __cdecl timer(bw::Unit* u){if(u->death_timer)--u->death_timer;}
inline void __cdecl recall(bw::Unit* u){
 living_units([&](bw::Unit* friend_unit){if(friend_unit!=u&&friend_unit->player==u->player&&friend_unit->unit_id==65)friend_unit->flingy.position={u->flingy.position.x,u->flingy.position.y};});u->order=3;
}
inline bool paid=false;
inline void __cdecl native_cost(bw::Unit* u){const U32 cost=U32(*native_tech_cost_view::yamato)*256;paid=u->energy>=cost;if(paid)u->energy=std::uint16_t(u->energy-cost);}
inline U32 first(const unit_legend_expansion::Rule& r){for(U32 id=0;id<228;id++)if(rework_combat_v5::expansion_matches(r,id))return id;return 228;}
inline U32 weapon(U32 id){auto w=original_stat({0,17,id});return w<130?w:original_stat({0,19,id});}
}
inline void qa38_every_new_primary_bonus_uses_real_damage_and_ui(){
 using namespace rework_fixture;
 for(const auto& r:unit_legend_expansion::rules)if(r.mode==1&&r.bonus&&!legend_focus::converted(r.ordinal)){
  for(U32 id=0;id<106;id++)if(rework_combat_v5::expansion_matches(r,id)){
   qa9_fixture::begin({r.ordinal});auto source=unit(id,1,100,100),enemy=unit(37,6,120,100);auto w=qa38_fixture::weapon(id);if(w>=130)w=79;
   g.normal_hit=true;g.bullet_hit_context=true;g.hit_source=source;g.hit_identity={source,source->unit_id,source->player,source->minor_unique_index};g.hit_bonus=0;const auto hp=enemy->flingy.hitpoints;
   combat_effects::weapon_damage(enemy,1000,U8(w),1,0,source,1,qa9_fixture::damage);
   CHECK(enemy->flingy.hitpoints==hp-int(1000*(100+r.bonus)/100));
   CHECK(rework_combat_v5::infantry_ui_value(source,w,100)==100+r.bonus);
   source->player=6;CHECK(rework_combat_v5::expansion_static_bonus(source,w)==0);source->player=1;source->flags|=0x40000000u;
   CHECK(rework_combat_v5::expansion_static_bonus(source,w)==0);qa9_fixture::end();
  }
 }
}
inline void qa38_every_secondary_rule_has_cadence_limit_and_no_recursion(){
 using namespace rework_fixture;
 for(const auto& r:unit_legend_expansion::rules)if(r.mode==1&&r.count&&r.ordinal!=185&&!legend_focus::converted(r.ordinal)){
  qa9_fixture::begin({r.ordinal});const U32 id=qa38_fixture::first(r);auto source=unit(id,1,100,100),target=unit(37,6,200,100);
  auto w=qa38_fixture::weapon(id);if(w>=130)w=79;
  std::vector<bw::Unit*> victims;for(U32 i=0;i<r.count+2;i++)victims.push_back(unit(37,6,202+int(i),100));
  auto outside=unit(37,6,201+int(r.radius),100),ally=unit(37,1,202,100),airborne=unit(43,6,202,100,true);
  const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;
  const auto target_hp=target->flingy.hitpoints,out_hp=outside->flingy.hitpoints,ally_hp=ally->flingy.hitpoints,air_hp=airborne->flingy.hitpoints;
  for(U32 n=1;n<=r.cadence;n++){game.frame_count=100+n*8;rework_combat_v5::ordinary_hit(source,target,10*256,w,false);}
  U32 hit=0;for(auto u:victims){if(u->flingy.hitpoints!=256000){++hit;CHECK(u->flingy.hitpoints==256000-int(10*256*r.percent*(r.ordinal==191?250:100)/10000));}}
  CHECK(hit==r.count&&outside->flingy.hitpoints==out_hp&&ally->flingy.hitpoints==ally_hp&&airborne->flingy.hitpoints==air_hp);
  CHECK(target->flingy.hitpoints==target_hp-(r.cadence==3?20*256:0));
  const auto hp=victims[0]->flingy.hitpoints;rework_combat_v5::ordinary_hit(source,target,10*256,w,true);CHECK(victims[0]->flingy.hitpoints==hp);
  combat_effects::original_weapon_damage=saved;qa9_fixture::end();
 }
}
inline void qa38_worker_and_overlord_auras_heal_once_without_stacking(){
 using namespace rework_fixture;
 for(auto pair:{std::pair<U32,U32>{183,7},{188,41},{189,42},{193,64}}){
  qa9_fixture::begin({pair.first});unit(pair.second,1,100,100,true);unit(pair.second,1,101,100,true);
  auto target=unit(pair.second==7?3:pair.second==64?65:38,1,120,100);target->flingy.hitpoints=10*256;target->shields=0;
  auto enemy=unit(target->unit_id,6,120,100);enemy->flingy.hitpoints=10*256;enemy->shields=0;
  game.frame_count=120;const auto hp=target->flingy.hitpoints;rework_combat_v5::expansion_support();
  CHECK(target->shields==0&&target->flingy.hitpoints==hp);
  CHECK(enemy->flingy.hitpoints==10*256&&enemy->shields==0);
  const auto after_hp=target->flingy.hitpoints,after_shield=target->shields;rework_combat_v5::expansion_support();CHECK(target->flingy.hitpoints==after_hp&&target->shields==after_shield);
  qa9_fixture::end();
 }
 qa9_fixture::begin({188,189});unit(41,1,100,100);unit(42,1,100,100,true);auto target=unit(38,1,120,100);target->flingy.hitpoints=10*256;
 game.frame_count=120;rework_combat_v5::expansion_support();CHECK(target->flingy.hitpoints==10*256);qa9_fixture::end();
}
inline void qa38_transport_and_observer_buffs_apply_to_actual_hits_and_expire(){
 using namespace rework_fixture;
 for(U32 ordinal:{187u,195u,196u}){
  qa9_fixture::begin({ordinal});const U32 id=ordinal==187?11:ordinal==195?69:84;unit(id,1,100,100,true);
  auto source=unit(ordinal==187?0:65,1,120,100),enemy=unit(37,6,130,100);game.frame_count=120;
  rework_combat_v5::expansion_support();std::int32_t amount=1000;
  g.normal_hit=true;{rework_combat_v5::DamageScope damage(ordinal==195?source:enemy,ordinal==195?enemy:source,ordinal==195?35:0,1,amount);}
  CHECK(amount==1000);
  game.frame_count=168;amount=1000;g.normal_hit=true;{rework_combat_v5::DamageScope damage(ordinal==195?source:enemy,ordinal==195?enemy:source,0,1,amount);}CHECK(amount==1000);
  qa9_fixture::end();
 }
}
inline void qa38_broodling_death_expiry_once_and_birth_resets_token(){
 using namespace rework_fixture;
 for(bool expiry:{false,true}){
  qa9_fixture::begin({192});auto brood=unit(40,1,100,100),target=unit(37,6,120,100),ally=unit(37,1,120,100),air=unit(43,6,120,100,true);
  const auto hp=target->flingy.hitpoints;brood->death_timer=1;
  if(expiry)owner_timer_hook(brood,qa38_fixture::timer);else rework_combat_v5::death(brood);
  CHECK(target->flingy.hitpoints==hp&&ally->flingy.hitpoints==256000&&air->flingy.hitpoints==256000);
  rework_combat_v5::death(brood);CHECK(target->flingy.hitpoints==hp);
  rework_combat_v5::created(brood);rework_combat_v5::death(brood);CHECK(target->flingy.hitpoints==hp);qa9_fixture::end();
 }
}
inline void qa38_recall_buff_first_cast_refreshes_and_expires(){
 using namespace rework_fixture;qa9_fixture::begin({145});auto arbiter=unit(71,1,500,500,true),zealot=unit(65,1,100,100),enemy=unit(37,6,100,100);
 arbiter->order=137;arbiter->order_state=1;arbiter->order_timer=0;arbiter->order_target={100,100,nullptr};
 {rework_combat_v5::OrderScope scope(arbiter,qa38_fixture::recall);qa38_fixture::recall(arbiter);}
 CHECK(rework_combat_v5::state(zealot)->portal_buff_until==820&&rework_combat_v5::expansion_outgoing_bonus(zealot,64)==20);
 CHECK(!rework_combat_v5::state(enemy)->portal_buff_until);
 game.frame_count=200;rework_combat_v5::portal_buff(zealot);CHECK(rework_combat_v5::state(zealot)->portal_buff_until==920&&rework_combat_v5::expansion_outgoing_bonus(zealot,64)==20);
 game.frame_count=920;CHECK(rework_combat_v5::expansion_outgoing_bonus(zealot,64)==0);qa9_fixture::end();
}
inline void qa38_lockdown_six_tile_six_extras(){
 using namespace rework_fixture;qa9_fixture::begin({63});auto ghost=unit(1,1,100,100),target=unit(3,6,200,100);
 for(U32 n=0;n<8;n++)unit(3,6,350+int(n),100);auto outside=unit(3,6,393,100);unit(3,1,350,100);
 bullet(ghost,target,32);CHECK(rework_combat_v5::pending_shots.size()==6);
 for(const auto& shot:rework_combat_v5::pending_shots)CHECK(shot.target.p!=outside&&shot.target.owner==6);qa9_fixture::end();
}
inline void qa38_broodling_cast_has_three_extra_native_targets(){
 using namespace rework_fixture;qa9_fixture::begin({104});auto queen=unit(45,1,100,100,true),target=unit(37,6,200,100);
 for(U32 n=0;n<5;n++)unit(37,6,210+int(n),100);auto outside=unit(37,6,329,100);
 auto robot=unit(83,6,201,100),air=unit(43,6,201,100,true),building=unit(106,6,201,100);
 multi_target::can_attack=nullptr; // Native Queens cannot make ordinary attacks.
 auto shot=bullet(queen,target,57);CHECK(rework_combat_v5::pending_shots.size()==3);
 for(const auto& extra:rework_combat_v5::pending_shots)CHECK(extra.weapon==57&&extra.target.p!=outside&&extra.target.p!=robot&&extra.target.p!=air&&extra.target.p!=building);
 bw::Unit* born=nullptr;{rework_combat_v5::MissileScope impact(shot);born=rank_fixture::create_full(40,200,100,1,nullptr);born->death_timer=1800;}
 U32 babies=0;living_units([&](bw::Unit* u){if(u->unit_id==40&&u->player==1)++babies;});CHECK(babies==6);
 pulse(101);CHECK(multi_fixture::shots.size()==4&&rework_combat_v5::pending_shots.empty());qa9_fixture::end();
}
inline void qa38_mind_control_five_ignores_supply_and_infest_is_retired(){
 using namespace rework_fixture;qa9_fixture::begin({146});auto caster=unit(63,1,100,100),target=unit(37,6,120,100);caster->energy=200*256;
 for(U32 n=0;n<6;n++)unit(12,6,125+int(n),100,true);caster->order=182;multi_fixture::target(caster,target);
 {rework_combat_v5::OrderScope scope(caster,native_cast);native_cast(caster);}
 U32 controlled=0;living_units([&](bw::Unit* u){if(u!=caster&&u->player==1)++controlled;});CHECK(controlled==5&&caster->energy==50*256);qa9_fixture::end();
 qa9_fixture::begin({107});auto queen=unit(45,1,100,100,true);target=unit(37,6,120,100);target->flingy.hitpoints=1;queen->order=27;multi_fixture::target(queen,target);
 {rework_combat_v5::OrderScope scope(queen);CHECK(!scope.handled());}CHECK(target->player==6&&!rework_combat_v5::rank(107));qa9_fixture::end();
}
inline void qa38_irradiation_mechanical_damage_and_six_tile_infection(){
 using namespace rework_fixture;qa9_fixture::begin({61,198});auto vessel=unit(9,1,500,500,true),host=unit(37,6,1000,1000),machine=unit(3,6,1100,1000),friend_machine=unit(3,1,1100,1000),organic=unit(38,6,1100,1000),distant_machine=unit(3,6,1300,1000);
 host->irradiate_timer=75;host->irradiate_player=1;host->irradiated_by=vessel;
 const auto hp=machine->flingy.hitpoints,organic_hp=organic->flingy.hitpoints,far_hp=distant_machine->flingy.hitpoints;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;
 rework_combat_v5::expansion_radiation();--host->irradiate_timer;game.frame_count=108;rework_combat_v5::expansion_radiation();
 const U32 damage=original_stat({1,14,34})*256/std::max(1u,original_stat({1,16,34}))*3;
 CHECK(machine->flingy.hitpoints==hp-int(damage)&&friend_machine->flingy.hitpoints==hp-int(damage));
 CHECK(organic->flingy.hitpoints==organic_hp&&distant_machine->flingy.hitpoints==far_hp);rework_combat_v5::expansion_radiation();CHECK(machine->flingy.hitpoints==hp-int(damage));
 auto ring=unit(37,6,1180,1000),outside=unit(37,6,1300,1000);rework_combat_v5::irradiation::attach(host,vessel,1);rework_combat_v5::death(host);CHECK(ring->irradiate_timer&& !outside->irradiate_timer);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa38_native_original_energy_cell_precheck_deduction_and_nested_owners(){
 using namespace qa12_fixture;begin(64,false);g.applied=false;CHECK(apply_snapshot(nullptr,talent(64)));
 auto memory=static_cast<U8*>(VirtualAlloc(nullptr,0x1000000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(memory);
 const std::uint16_t original=150;std::memcpy(memory+native_tech_cost_view::energy_array+16,&original,2);auto previous=native_tech_cost_view::yamato;auto previous_image=native_tech_cost_view::image;
 for(U32 i=0;i<3;i++){std::memcpy(memory+native_tech_cost_view::sites[i],native_tech_cost_view::prefixes[i],5);std::memcpy(memory+native_tech_cost_view::sites[i]+5,&native_tech_cost_view::energy_array,4);}
 CHECK(native_tech_cost_view::bind(memory)&&native_tech_cost_view::verify_after_dat());auto caster=produce(12),enemy=produce(12,6);complete(caster,50);complete(enemy,149);
 owner_unit_hook(caster,qa38_fixture::native_cost);CHECK(qa38_fixture::paid&&caster->energy==0&&*native_tech_cost_view::yamato==150);
 complete(caster,49);owner_order_hook(caster,qa38_fixture::native_cost);CHECK(!qa38_fixture::paid&&caster->energy==49*256);
 owner_unit_hook(enemy,qa38_fixture::native_cost);CHECK(!qa38_fixture::paid&&enemy->energy==149*256);
 complete(enemy,150);owner_unit_hook(enemy,qa38_fixture::native_cost);CHECK(qa38_fixture::paid&&enemy->energy==0);
 {OwnerDatScope own(1,1,caster);CHECK(*native_tech_cost_view::yamato==50&&raw_value(4,3,8)==50);{OwnerDatScope foe(6,6,enemy);CHECK(*native_tech_cost_view::yamato==150);}CHECK(*native_tech_cost_view::yamato==50);}
 CHECK(*native_tech_cost_view::yamato==150);native_tech_cost_view::yamato=previous;native_tech_cost_view::image=previous_image;CHECK(VirtualFree(memory,0,MEM_RELEASE));end();
}
inline void qa38_wave_strength_and_global_limits(){
 namespace p=sc1_native::rework_wave;
 CHECK(p::normal_amount(100)==115&&p::graded_amount(100,1)==150&&p::graded_amount(100,2)==175&&p::graded_amount(100,3)==200);
 CHECK(!p::normal_amount(0)&&!p::graded_amount(0,3));
 rework_wave_tests::begin(101);g.growth.curse_counts[p::Fenix]=1;g.current_wave_id=10;
 rework_waves::primary=rework_waves::choose_origin(true);CHECK(rework_waves::primary);rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=5000*24;
 const auto& roster=*std::find_if(std::begin(p::kRosters),std::end(p::kRosters),[](const p::Roster& r){return r.slot==p::Fenix;});rework_waves::roster(roster);
 U32 heroes=0;living_units([&](bw::Unit* u){if(u->unit_id==77&&rework_curses::marked(u))++heroes;});CHECK(heroes==2);CHECK(rework_waves::live_supply()<=p::live_supply_cap(101)&&p::live_supply_cap(101)==480);
}
inline void qa38_plague_native_outer_area_is_doubled(){
 using namespace rework_fixture;qa9_fixture::begin({102});auto defiler=unit(46,1,500,500),center=unit(37,6,1000,1000),ring=unit(38,6,1120,1000),ally=unit(0,1,1120,1000),outside=unit(37,6,1129,1000);
 rework_combat_v5::get_sprite_position=sprite_get;rework_combat_v5::set_sprite_position=sprite_set;
 auto native=[](bw::Bullet* b){living_units([&](bw::Unit* u){if(rework_combat_v5::eligible(u)&&!(u->flags&0x10u)&&std::abs(int(u->flingy.position.x)-b->target.x)<=64&&std::abs(int(u->flingy.position.y)-b->target.y)<=64)u->plague_timer=75;});};
 auto shot=bullet(defiler,center,60);{rework_combat_v5::MissileScope scope(shot,native);native(shot);}
 CHECK(center->plague_timer&&ring->plague_timer&&ally->plague_timer&&!outside->plague_timer);qa9_fixture::end();
}
inline void qa38_promoted_battlecruiser_legend_reaches_all_hero_variants(){
 using namespace rework_fixture;
 for(U32 id:{12u,27u,28u,29u,102u}){
  qa9_fixture::begin({57});auto ship=unit(id,1,100,100,true),target=unit(37,6,120,100);
  for(U32 n=0;n<8;n++)unit(37,6,130+int(n)*5,100);
  bullet(ship,target,original_stat({0,17,id}));CHECK(rework_combat_v5::pending_shots.empty());CHECK(rework_combat_v5::focus_base(ship)==100);qa9_fixture::end();
 }
}
inline void run_qa38_groups(){
 qa38_every_new_primary_bonus_uses_real_damage_and_ui();qa38_every_secondary_rule_has_cadence_limit_and_no_recursion();
 qa38_worker_and_overlord_auras_heal_once_without_stacking();qa38_transport_and_observer_buffs_apply_to_actual_hits_and_expire();
 qa38_broodling_death_expiry_once_and_birth_resets_token();qa38_recall_buff_first_cast_refreshes_and_expires();
 qa38_lockdown_six_tile_six_extras();qa38_broodling_cast_has_three_extra_native_targets();
 qa38_mind_control_five_ignores_supply_and_infest_is_retired();qa38_irradiation_mechanical_damage_and_six_tile_infection();
 qa38_native_original_energy_cell_precheck_deduction_and_nested_owners();qa38_wave_strength_and_global_limits();qa38_plague_native_outer_area_is_doubled();qa38_promoted_battlecruiser_legend_reaches_all_hero_variants();
}
}
