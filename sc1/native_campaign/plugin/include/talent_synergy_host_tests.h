#pragma once
namespace host_test {
inline constexpr std::size_t talent_synergy_group_count=7;
inline void synergy_ghost_normal_type_is_owner_scoped(){
 qa9_fixture::begin({49});rework_fixture::install();
 for(U32 id:{1u,16u,99u,100u,104u})for(U32 field:{17u,19u}){
  auto w=original_stat({0,field,id});if(w>=130)continue;
  CHECK(owner_stat(1,{1,7,w})==3);CHECK(owner_stat(6,{1,7,w})==original_stat({1,7,w}));
  {OwnerDatScope view(1,1);CHECK(read_entry(table_for({1,7,w},false),w)==3);}
  CHECK(read_entry(table_for({1,7,w},false),w)==original_stat({1,7,w}));
 }qa9_fixture::end();
 qa9_fixture::begin({63});rework_fixture::install();
 const auto w=original_stat({0,17,1});CHECK(owner_stat(1,{1,7,w})==original_stat({1,7,w}));qa9_fixture::end();
}
inline void synergy_emp_stasis_independent_radii_and_visuals(){
 using namespace rework_fixture;qa9_fixture::begin({44,62,127,149});install();
 for(U32 f:{11u,12u,13u})CHECK(owner_stat(1,{1,f,33})==original_stat({1,f,33})*3);
 CHECK(rework_combat_v5::stasis_radius()==120);
 rework_combat_v5::get_sprite_position=sprite_get;rework_combat_v5::set_sprite_position=sprite_set;
 auto caster=unit(71,1,500,500,true),target=unit(37,6,1000,1000),inside=unit(65,1,1119,1000),outside=unit(65,1,1121,1000);
 inside->flingy.hitpoints=256;inside->shields=0;
 auto shot=bullet(caster,target,83);{rework_combat_v5::MissileScope scope(shot,area);area(shot);}
 CHECK(inside->stasis_timer&&!outside->stasis_timer);
 inside->stasis_timer=0;pulse(101);CHECK(inside->flingy.hitpoints==int(effective_max_hp(inside)));
 area_visuals::publish(true);CHECK(area_visuals::published->images[364].x==2.5);qa9_fixture::end();
}
inline void synergy_archon_legend_does_not_erase_native_area(){
 using namespace rework_fixture;qa9_fixture::begin({129,139});install();
 auto source=unit(68,1,100,100),target=unit(37,6,130,100),other=unit(37,6,135,100);
 const auto w=original_stat({0,17,68});CHECK(owner_stat(1,{1,13,w})==(original_stat({1,13,w})*150+50)/100);
 g.normal_hit=true;rework_combat_v5::DamageScope::current_primary=target;
 {std::int32_t amount=1000;rework_combat_v5::DamageScope hit(other,source,w,1,amount);CHECK(amount==1000);}
 rework_combat_v5::DamageScope::current_primary=nullptr;qa9_fixture::end();
}
inline void synergy_ghost_fragments_inherit_legend_and_manual_once(){
 using namespace rework_fixture;qa9_fixture::begin({49,163,164,206});
 auto source=unit(1,1,100,100),target=unit(37,6,130,100),other=unit(37,6,135,100);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 qa39_fixture::primary(source,target,2,1000,1);
 CHECK(target->flingy.hitpoints==256000-3105);CHECK(other->flingy.hitpoints==256000-1150);
 CHECK(rework_combat_v5::rank(164)==0&&rework_combat_v5::raw_rank(164)==1);
 CHECK(rework_combat_v5::generated_depth==0&&rework_combat_v5::pending_shots.empty());
 CHECK(rework_combat_v5::state(source)->focus_hits==1);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy_periodic_hit_keeps_manual_without_self_multiplication(){
 using namespace rework_fixture;qa9_fixture::begin({184,202});auto source=unit(0,1,100,100),target=unit(37,6,130,100);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 for(U32 n=1;n<=3;++n){game.frame_count=100+n;qa39_fixture::primary(source,target,0,1000,n);}
 CHECK(target->flingy.hitpoints==256000-3*1437-3450);
 CHECK(rework_combat_v5::state(source)->focus_hits==3&&rework_combat_v5::generated_depth==0);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy_melee_extra_attack_inherits_legend_without_recursion(){
 using namespace rework_fixture;qa9_fixture::begin({18,194});auto source=unit(65,1,100,100),target=unit(37,6,130,100);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 rework_combat_v5::ordinary_hit(source,target,1000,64,false);
 CHECK(target->flingy.hitpoints==256000-875);CHECK(rework_combat_v5::state(source)->focus_hits==1);
 CHECK(rework_combat_v5::pending_shots.empty()&&rework_combat_v5::generated_depth==0);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy_parent_ammo_traits_and_independent_manual_caps(){
 qa13_fixture::begin();GrowthSnapshot s{};s.wire_version=2;
 for(const auto& r:unit_growth::rules)if(rework_combat_v5::in(qa38_units::first(r),{72,73}))qa38_units::set(s,r.ordinal,r.kind==1?4u:r.kind==2?1u:0u);
 CHECK(apply_snapshot(nullptr,s));CHECK(rework_combat_v5::unit_attack_rank(g.growth,73)==8);
 CHECK(owner_stat(1,{1,14,79})==original_stat({1,14,79})+8);
 U32 expected=0;for(const auto& r:unit_growth::rules)if(r.kind==2&&rework_combat_v5::in(qa38_units::first(r),{72,73}))expected+=r.damage;
 CHECK(expected==20&&rework_combat_v5::unit_trait_value(g.growth,73,2,true)==expected);
 qa13_fixture::end();
 for(U32 n:{164u,210u,211u,283u}){qa9_fixture::begin({n});CHECK(rework_combat_v5::raw_rank(n)==1&&rework_combat_v5::rank(n)==0);qa9_fixture::end();}
}
inline void run_talent_synergy_groups(){
 synergy_ghost_normal_type_is_owner_scoped();synergy_emp_stasis_independent_radii_and_visuals();
 synergy_archon_legend_does_not_erase_native_area();synergy_ghost_fragments_inherit_legend_and_manual_once();
 synergy_periodic_hit_keeps_manual_without_self_multiplication();synergy_melee_extra_attack_inherits_legend_without_recursion();
 synergy_parent_ammo_traits_and_independent_manual_caps();
}
}
