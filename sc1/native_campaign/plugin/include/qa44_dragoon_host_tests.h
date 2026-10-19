#pragma once
namespace host_test {
inline constexpr std::size_t qa44_group_count=1;
inline void qa44_dragoon_procs_on_third_hit_for450_percent(){
 using namespace rework_fixture;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 for(U32 id:{66u,78u}){
  qa9_fixture::begin({137});auto dragoon=unit(id,1,100,100),target=unit(37,6,120,100),other=unit(37,6,125,100);
  const auto weapon=qa39_fixture::weapon(id);const auto hp=target->flingy.hitpoints;
  for(U32 hit=1;hit<=6;hit++){
   game.frame_count=100+hit;qa39_fixture::primary(dragoon,target,weapon,1000,hit);
   CHECK(target->flingy.hitpoints==hp-int(hit*1750+(hit/3)*4500));
   CHECK(other->flingy.hitpoints==256000);CHECK(rework_combat_v5::pending_shots.empty());
  }
  qa9_fixture::end();
 }
 combat_effects::original_weapon_damage=saved;
}
inline void run_qa44_groups(){qa44_dragoon_procs_on_third_hit_for450_percent();}
}
