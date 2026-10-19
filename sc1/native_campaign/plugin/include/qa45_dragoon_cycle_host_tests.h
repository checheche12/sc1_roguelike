#pragma once
namespace host_test {
inline constexpr std::size_t qa45_group_count=3;
inline void qa45_targets_pauses_and_dragoon_instances_keep_independent_cycles(){
 using namespace rework_fixture;const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 for(U32 id:{66u,78u}){
  qa9_fixture::begin({137});auto u=unit(id,1,100,100),other=unit(id,1,100,120);
  auto a=unit(37,6,120,100),b=unit(37,6,125,100),c=unit(43,6,130,100,true);auto targets=std::array<bw::Unit*,3>{a,b,c};
  const U32 weapon=qa39_fixture::weapon(id);
  for(U32 hit=1;hit<=6;hit++){
   auto target=targets[(hit-1)%3];const auto hp=target->flingy.hitpoints;game.frame_count=hit*100;
   qa39_fixture::primary(u,target,weapon,1000,hit);
   CHECK(target->flingy.hitpoints==hp-int(hit%3?1750:4250));
   CHECK(rework_combat_v5::state(u)->dragoon_hits==hit%3);
   if(hit==2){const auto before=a->flingy.hitpoints;qa39_fixture::primary(other,a,weapon,1000,100);CHECK(a->flingy.hitpoints==before-1750);CHECK(rework_combat_v5::state(other)->dragoon_hits==1);}
  }
  qa9_fixture::end();
 }
 combat_effects::original_weapon_damage=saved;
}
inline void qa45_killing_hits_advance_cycle_and_duplicate_or_generated_hits_do_not(){
 using namespace rework_fixture;qa9_fixture::begin({137});const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 auto u=unit(66,1,100,100),a=unit(37,6,120,100),b=unit(37,6,125,100),c=unit(37,6,130,100);const U32 w=qa39_fixture::weapon(66);
 a->flingy.hitpoints=b->flingy.hitpoints=100;qa39_fixture::primary(u,a,w,1000,1);CHECK(a->flingy.hitpoints==0&&rework_combat_v5::state(u)->dragoon_hits==1);
 g.bullet_hit_context=true;rework_combat_v5::ordinary_hit(u,a,1000,w,false,1);g.bullet_hit_context=false;CHECK(rework_combat_v5::state(u)->dragoon_hits==1);
 rework_combat_v5::ordinary_hit(u,c,1000,w,true,2);++rework_combat_v5::generated_depth;rework_combat_v5::ordinary_hit(u,c,1000,w,false,2);--rework_combat_v5::generated_depth;CHECK(rework_combat_v5::state(u)->dragoon_hits==1);
 qa39_fixture::primary(u,b,w,1000,2);CHECK(b->flingy.hitpoints==0&&rework_combat_v5::state(u)->dragoon_hits==2);
 const auto hp=c->flingy.hitpoints;qa39_fixture::primary(u,c,w,1000,3);CHECK(c->flingy.hitpoints==hp-4250&&rework_combat_v5::state(u)->dragoon_hits==0);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa45_new_generation_or_owner_cannot_inherit_a_charged_cycle(){
 using namespace rework_fixture;qa9_fixture::begin({137});auto u=unit(66,1,100,100),target=unit(37,6,120,100);const U32 w=qa39_fixture::weapon(66);
 rework_combat_v5::ordinary_hit(u,target,1000,w,false);rework_combat_v5::ordinary_hit(u,target,1000,w,false);CHECK(rework_combat_v5::state(u)->dragoon_hits==2);
 u->player=2;CHECK(rework_combat_v5::state(u)->dragoon_hits==0);u->player=1;CHECK(rework_combat_v5::state(u)->dragoon_hits==0);
 rework_combat_v5::ordinary_hit(u,target,1000,w,false);CHECK(rework_combat_v5::state(u)->dragoon_hits==1);++u->minor_unique_index;CHECK(rework_combat_v5::state(u)->dragoon_hits==0);qa9_fixture::end();
}
inline void run_qa45_groups(){qa45_targets_pauses_and_dragoon_instances_keep_independent_cycles();qa45_killing_hits_advance_cycle_and_duplicate_or_generated_hits_do_not();qa45_new_generation_or_owner_cannot_inherit_a_charged_cycle();}
}
