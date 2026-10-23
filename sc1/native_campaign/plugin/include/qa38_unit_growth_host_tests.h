#pragma once
namespace host_test {
namespace qa38_units {
inline void set(GrowthSnapshot& s,U32 ordinal,U32 value){
 for(auto f:rework_catalog::kPackedFields)if(f.ordinal==ordinal){
  auto& word=f.word<=16?s.talent_bits[f.word-1]:s.talent_ranks[f.word-33];
  word=(word&~(((1u<<f.width)-1u)<<f.shift))|(value<<f.shift);return;
 }CHECK(false);
}
inline U32 first(const unit_growth::Rule& r){for(U32 id=0;id<228;++id)if(rework_combat_v5::unit_growth_matches(r,id))return id;return 228;}
}
inline void qa38_unit_health_native_caps_and_separation(){
 for(const auto& rule:unit_growth::rules)if(rule.kind==0)for(U32 rank:{1u,4u}){
  qa13_fixture::begin();GrowthSnapshot s{};s.wire_version=2;qa38_units::set(s,rule.ordinal,rank);
  const U32 id=qa38_units::first(rule);auto u=add(id,1,100,100,int(original_stat({0,8,id})));u->flags=1;
  CHECK(apply_snapshot(nullptr,s));const U32 expected=U32((std::uint64_t(original_stat({0,8,id}))*(100+28*rank)+50)/100);
  CHECK(owner_stat(1,{0,8,id})==expected&&effective_max_hp(u)==expected);
  CHECK(owner_stat(6,{0,8,id})==original_stat({0,8,id}));
  for(U32 other:{0u,37u,65u})if(!rework_combat_v5::unit_growth_matches(rule,other))CHECK(owner_stat(1,{0,8,other})==original_stat({0,8,other}));
  if(rework_combat_v5::race_type(id,2))CHECK(owner_stat(1,{0,7,id})==U32((std::uint64_t(original_stat({0,7,id}))*(100+28*rank)+50)/100));
  qa13_fixture::end();
 }
}
inline void qa38_unit_attack_profiles_cooldown_and_parent_aliases(){
 for(const auto& rule:unit_growth::rules)if(rule.kind==1){
  qa13_fixture::begin();GrowthSnapshot s{};s.wire_version=2;qa38_units::set(s,rule.ordinal,4);CHECK(apply_snapshot(nullptr,s));
  const U32 id=qa38_units::first(rule);auto source=add(id,1,100,100);source->flags=1;
  CHECK(rework_combat_v5::unit_attack_rank(g.growth,id)==4);
  CHECK(std::abs(rework_combat_v5::cooldown_ratio(source,0)-std::pow(0.955,4))<0.000001);
  for(U32 field:{17u,19u}){auto w=original_stat({0,field,id});if(id==72||id==82)w=79;if(id==81||id==83||id==85)w=82;if(w>=130)continue;
   if(rule.parent==29){CHECK(rework_combat_v5::infantry_damage_rank(source,w)==4);CHECK(rework_combat_v5::infantry_ui_value(source,w,100)==160);}
   else {const U32 bonus=id==58?4u:rework_combat_v5::in(id,{7,41,64})?12u:rework_combat_v5::manual_damage_bonus(rule.parent,(id==72||id==82)?73u:id,field,4);
    CHECK(owner_stat(1,{1,14,w})==original_stat({1,14,w})+bonus);CHECK(owner_stat(6,{1,14,w})==original_stat({1,14,w}));}
  }
  qa13_fixture::end();
 }
 // Independent parent/ammo rewards grant the strongest rank, not both bonuses.
 qa13_fixture::begin();GrowthSnapshot s{};s.wire_version=2;
 for(const auto& r:unit_growth::rules)if(r.kind==1&&rework_combat_v5::in(qa38_units::first(r),{72,73}))qa38_units::set(s,r.ordinal,2);
 CHECK(apply_snapshot(nullptr,s));CHECK(rework_combat_v5::unit_attack_rank(g.growth,73)==2);CHECK(owner_stat(1,{1,14,79})==original_stat({1,14,79})+2);
 qa13_fixture::end();
}
inline void qa38_every_unit_trait_native_stats_motion_and_damage(){
 for(const auto& r:unit_growth::rules)if(r.kind==2){
  qa13_fixture::begin();GrowthSnapshot s{};s.wire_version=2;qa38_units::set(s,r.ordinal,1);CHECK(apply_snapshot(nullptr,s));
  const U32 id=qa38_units::first(r);auto u=add(id,1,100,100);u->flags=1;
  CHECK(owner_stat(1,{0,27,id})==original_stat({0,27,id})+r.armor);
  CHECK(owner_stat(1,{0,8,id})==U32((std::uint64_t(original_stat({0,8,id}))*(100+r.hp)+50)/100));
  CHECK(std::abs(rework_combat_v5::speed_ratio(u)-(1.0+r.speed/100.0))<0.000001);
  auto weapon=qa38_fixture::weapon(id);if(id==72||id==82)weapon=79;if(id==81||id==83||id==85)weapon=82;
  if(weapon<130)CHECK(rework_combat_v5::infantry_ui_value(u,weapon,100)==100+r.damage);
  if(r.energy){const auto e=u->energy;CHECK(rework_combat_v5::energy_total_cap(u,*rework_combat_v5::state(u))==200*256+r.energy*256);CHECK(u->energy==e);}
  u->player=6;CHECK(rework_combat_v5::expansion_static_bonus(u,weapon)==0);qa13_fixture::end();
 }
}
inline void qa38_packed_wire_rank_increment_and_invalid_decrease(){
 const rework_catalog::Field* picked=nullptr;for(const auto& f:rework_catalog::kPackedFields)if(f.word<=16&&f.width==3){picked=&f;break;}CHECK(picked);
 reset();make_chk(nullptr,2);init_units(original);
 auto payload=reply(1);payload[4]=1;payload[5]=2;payload[6]=3;payload[7]=4;payload[10]=0x50480101;payload[11+picked->word]=3u<<picked->shift;
 publish(payload);protocol_pump(nullptr);CHECK(g.protocol.ready());CHECK(rework_catalog::rank(g.growth,picked->ordinal)==3);
 CHECK(g.protocol.request_phase(2));payload=reply(1);payload[4]=1;payload[5]=2;payload[6]=3;payload[7]=4;payload[10]=0x50480202;payload[11+picked->word]=4u<<picked->shift;
 publish(payload);protocol_pump(nullptr);CHECK(g.protocol.ready());CHECK(rework_catalog::rank(g.growth,picked->ordinal)==4);
 auto invalid=g.growth;qa38_units::set(invalid,picked->ordinal,5);CHECK(!apply_snapshot(nullptr,invalid));
}
inline void run_qa38_unit_growth_groups(){qa38_unit_health_native_caps_and_separation();qa38_unit_attack_profiles_cooldown_and_parent_aliases();qa38_every_unit_trait_native_stats_motion_and_damage();qa38_packed_wire_rank_increment_and_invalid_decrease();}
}
