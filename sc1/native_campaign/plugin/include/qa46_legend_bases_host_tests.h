#pragma once
namespace host_test {
inline constexpr std::size_t qa46_group_count=2;
inline void qa46_zealot_execution_threshold_owner_and_manual_synergy(){
 using namespace rework_fixture;
 for(U32 id:{65u,77u}){
  qa9_fixture::begin({194});auto u=unit(id,1,100,100),target=unit(37,6,120,100);const U32 w=qa39_fixture::weapon(id);
  const auto max=effective_max_hp(target);
  target->flingy.hitpoints=int(max*51/100);CHECK(rework_combat_v5::focus_damage(u,target,w,1000,true)==1750);
  target->flingy.hitpoints=int(max/2);CHECK(rework_combat_v5::focus_damage(u,target,w,1000,true)==3750);
  CHECK(rework_combat_v5::focus_damage(u,target,w,1000,false)==1000);
  u->player=6;CHECK(rework_combat_v5::focus_damage(u,target,w,1000,true)==1000);u->player=1;
  u->flags|=0x40000000u;CHECK(rework_combat_v5::focus_damage(u,target,w,1000,true)==1000);u->flags&=~0x40000000u;
  ranks[111]=1;install();const auto upgraded=owner_stat(1,{1,14,w});CHECK(upgraded>original_stat({1,14,w}));
  target->flingy.hitpoints=int(max*51/100);CHECK(rework_combat_v5::focus_damage(u,target,w,int(upgraded*256),true)==int(upgraded*448));
  CHECK(owner_stat(6,{1,14,w})==original_stat({1,14,w}));qa9_fixture::end();
 }
}
inline void qa46_large_stat_bases_preserve_owner_scope(){
 using namespace rework_fixture;qa9_fixture::begin({96,144});install();
 CHECK(owner_stat(1,{0,8,47})==original_stat({0,8,47})*2);
 CHECK(owner_stat(6,{0,8,47})==original_stat({0,8,47}));
 for(U32 field:{11u,12u,13u}){
  CHECK(owner_stat(1,{1,field,84})==original_stat({1,field,84})*2);
  CHECK(owner_stat(6,{1,field,84})==original_stat({1,field,84}));
 }
 qa9_fixture::end();
}
inline void run_qa46_groups(){qa46_zealot_execution_threshold_owner_and_manual_synergy();qa46_large_stat_bases_preserve_owner_scope();}
}
