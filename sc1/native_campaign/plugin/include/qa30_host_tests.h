#pragma once
namespace host_test {
inline constexpr std::size_t qa30_group_count=5;
inline GrowthSnapshot qa30_air_snapshot(U32 stacks){
 GrowthSnapshot s{};s.wire_version=2;
 for(U32 ord:{69u,72u,110u,112u,157u,160u}){const U32 bit=238+ord;s.talent_bits[bit/32]|=1u<<(bit%32);const int slot=rework_catalog::kRankSlots[ord];if(slot>=0)s.talent_ranks[slot]=stacks;}
 return s;
}
inline void qa30_air_matrix_preserves_layers_owners_and_stack_caps(){
 for(U32 stacks:{1u,4u}){
  qa13_fixture::begin();CHECK(apply_snapshot(nullptr,qa30_air_snapshot(stacks)));
  for(U32 id:{43u,44u,45u,47u,55u,56u,62u,60u,70u,71u,72u,73u,80u,82u,84u,86u,88u,98u}){
   auto u=add(id,1,100,100);u->flags=5;
   CHECK(owner_stat(1,{0,8,id})==(original_stat({0,8,id})*(100+stacks*28)+50)/100);
   CHECK(owner_stat(6,{0,8,id})==original_stat({0,8,id}));
   const bool mobile=rework_combat_v5::in(id,{44,56,62,70,71,72,80,82,86,88});
   CHECK(std::abs(rework_combat_v5::speed_ratio(u)-(mobile?1.2:1.0))<0.00001);
   if(rework_combat_v5::group(112,id))CHECK(std::abs(rework_combat_v5::cooldown_ratio(u,0)-std::pow(0.955,double(stacks)))<0.00001);
   for(U32 field:{17u,19u}){const auto w=original_stat({0,field,id});if(w>=130)continue;
    const U32 bonus=rework_combat_v5::air_control(g.growth,id)?32u:0u;
    CHECK(owner_stat(1,{1,5,w})==original_stat({1,5,w})+bonus);
    CHECK(owner_stat(6,{1,5,w})==original_stat({1,5,w}));
   }
  }
  for(U32 id:{43u,44u,47u,62u,60u,69u,70u,71u,72u,84u}){
   CHECK(owner_stat(1,{0,42,id})==(original_stat({0,42,id})*4+4)/5);
   CHECK(owner_stat(6,{0,42,id})==original_stat({0,42,id}));
  }
  qa13_fixture::end();
 }
}
inline U32 __cdecl qa30_acquisition(bw::Unit* u){return raw_value(0,23,u->unit_id);}
inline void qa30_carrier_range_uses_native_acquisition_tiles(){
 reset();CHECK(apply_snapshot(nullptr,qa30_air_snapshot(4)));
 for(U32 id:{72u,82u}){
  CHECK(original_stat({0,17,id})==130&&original_stat({0,19,id})==130);
  auto own=add(id,1,100,100),enemy=add(id,6,100,100),fake=add(id,1,100,100);fake->flags|=0x40000000u;
  CHECK(owner_acquire_hook(own,qa30_acquisition)==9&&owner_acquire_hook(enemy,qa30_acquisition)==8&&owner_acquire_hook(fake,qa30_acquisition)==8);
  {OwnerDatScope outer(1,1,own);CHECK(raw_value(0,23,id)==9);CHECK(owner_acquire_hook(enemy,qa30_acquisition)==8);CHECK(raw_value(0,23,id)==9);}
  CHECK(raw_value(0,23,id)==8);
 }
}
inline void qa30_corsair_range_keeps_legacy_hero_and_spell_rules(){
 reset();auto s=qa30_air_snapshot(4);s.talent_bits[102/32]|=1u<<(102%32);CHECK(apply_snapshot(nullptr,s));
 auto corsair=add(60,1,100,100),hero=add(98,1,100,100),enemy=add(60,6,100,100),fake=add(60,1,100,100);fake->flags|=0x40000000u;
 const auto base=original_stat({1,5,100}),spell=original_stat({1,5,101});
 CHECK(owner_attack_range_hook(corsair,100,audit_weapon_range_return)==base+64);
 CHECK(owner_attack_range_hook(hero,100,audit_weapon_range_return)==base+32);
 CHECK(owner_attack_range_hook(enemy,100,audit_weapon_range_return)==base);
 CHECK(owner_attack_range_hook(fake,100,audit_weapon_range_return)==base);
 CHECK(owner_attack_range_hook(corsair,101,audit_weapon_range_return)==spell);
 CHECK(raw_value(1,5,100)==base);
}
inline void __cdecl qa30_corsair_impact(bw::Bullet* b){
 std::int32_t amount=5*256;rework_combat_v5::DamageScope scope(b->target.unit,b->parent,100,1,amount);b->target.unit->flingy.hitpoints-=amount;
}
inline void qa30_corsair_fourth_launch_survives_spells_extras_and_late_impacts(){
 using namespace rework_fixture;qa9_fixture::begin({135});auto caster=unit(60,1,100,100,true);
 std::array<bw::Bullet*,5> shots{};std::array<bw::Unit*,5> victims{};
 for(U32 i=0;i<5;++i){game.frame_count=100+i*10;victims[i]=unit(43,6,130+int(i),100,true);shots[i]=bullet(caster,victims[i],100);
  CHECK(rework_combat_v5::projectiles.at(shots[i]).token==i+1);
  ++game.frame_count;bullet(caster,victims[i],101); // Web is not an ordinary attack.
  rework_combat_v5::emission_secondary=true;auto extra=bullet(caster,victims[i],100);rework_combat_v5::emission_secondary=false;
  owner_missile_hook(extra,qa30_corsair_impact);CHECK(!rework_combat_v5::state(victims[i])->slow_until);
 }
 CHECK(rework_combat_v5::state(caster)->corsair_primary_attacks==5);
 game.frame_count=200;
 for(U32 index:{0u,3u,4u,1u,2u}){owner_missile_hook(shots[index],qa30_corsair_impact);auto state=rework_combat_v5::state(victims[index]);CHECK(state->slow_until==(index==3?320u:0u));if(index==3)CHECK(state->slow_percent==50);}
 qa9_fixture::end();
}
inline void qa30_scout_dual_layer_respects_native_primary_clock(){
 using namespace rework_fixture;
 for(U32 type:{70u,80u,88u}){
  qa9_fixture::begin({142});auto scout=unit(type,1,100,100,true);auto ground=unit(37,6,130,100),air=unit(43,6,135,100,true);unit(43,1,132,100,true);
  scout->order=10;multi_fixture::target(scout,ground);pulse(100);
  CHECK(multi_fixture::shots.size()==multi_target::factor(original_stat({0,19,type})));
  for(auto& p:rework_combat_v5::projectiles)CHECK(p.second.primary.p==air&&p.second.percent==250);
  const auto stacks=multi_fixture::shots.size();pulse(101);CHECK(multi_fixture::shots.size()==stacks);qa9_fixture::end();
 }
}
inline void run_qa30_groups(){qa30_air_matrix_preserves_layers_owners_and_stack_caps();qa30_carrier_range_uses_native_acquisition_tiles();qa30_corsair_range_keeps_legacy_hero_and_spell_rules();qa30_corsair_fourth_launch_survives_spells_extras_and_late_impacts();qa30_scout_dual_layer_respects_native_primary_clock();}
}
