#pragma once
namespace host_test {
inline constexpr std::size_t qa62_group_count=5;
inline void qa62_exact_hundredth_stacks_multiple_sources_and_saturation(){
 using namespace rework_fixture;qa9_fixture::begin({190});auto ling=unit(37,1,100,100),hero=unit(54,1,110,100),target=unit(39,6,120,100);
 for(U32 n=1;n<=100;n++){
  rework_combat_v5::focus_hit(n%2?ling:hero,target,256,35);
  CHECK(rework_combat_v5::state(target)->erosion==33*n);
 }
 auto status=rework_combat_v5::state(target);CHECK(status->erosion==3300);
 status->erosion=0xfffffff0u;rework_combat_v5::focus_hit(ling,target,256,35);CHECK(status->erosion==0xfffffffeu);
 rework_combat_v5::focus_hit(hero,target,256,35);CHECK(status->erosion==0xfffffffeu);qa9_fixture::end();
}
inline void qa62_fractional_armor_health_callback_size_rules_and_restore(){
 using namespace rework_fixture;
 for(U32 id:{37u,38u,39u})for(U32 w:{0u,8u,2u}){
  qa9_fixture::begin({190});auto source=unit(0,1,100,100),target=unit(id,6,150,100);g.normal_hit=true;
  auto level=rework_upgrade_storage::slot(6,original_stat({0,25,id}));CHECK(level);*level=1;
  auto status=rework_combat_v5::state(target);status->erosion=33;status->erosion_owner=1;
  const U32 size=original_stat({0,26,id}),before=raw_value(0,27,id),upgrade_before=raw_value(0,25,id);
  const U32 expected=w==0?172u:w==8?(size==1?86u:size==2?129u:172u):(size==1?172u:size==2?86u:43u);
  std::int32_t amount=10*256;
  {rework_combat_v5::DamageScope scope(target,source,w,1,amount);
   CHECK(scope.erosion_armor_reduction==expected);
   CHECK(raw_value(0,27,id)==original_stat({0,27,id}));CHECK(raw_value(0,25,id)==61);
   CHECK(rework_combat_v5::post_armor_damage(target,1000)==1000-int(expected));
   CHECK(rework_combat_v5::post_armor_damage(target,128)==128);
   const auto hp=target->flingy.hitpoints;
   owner_damage_hook(target,1000,source,1,1,direct_damage);CHECK(target->flingy.hitpoints==hp-1000+int(expected));
  }
  CHECK(raw_value(0,27,id)==before&&raw_value(0,25,id)==upgrade_before);qa9_fixture::end();
 }
}
inline void qa62_shields_spill_and_armor_ignore_keep_native_boundaries(){
 using namespace rework_fixture;qa9_fixture::begin({190});auto source=unit(0,1,100,100),target=unit(66,6,150,100);g.normal_hit=true;
 auto status=rework_combat_v5::state(target);status->erosion=33;status->erosion_owner=1;target->shields=5*256;
 std::int32_t damage=10*256;const auto shields=target->shields;
 {rework_combat_v5::DamageScope scope(target,source,0,1,damage);
  CHECK(scope.erosion_armor_reduction==172);CHECK(target->shields==shields&&damage==10*256);
  CHECK(rework_combat_v5::post_armor_damage(target,64)==0);CHECK(target->shields==shields);
 }
 ranks[19]=1;
 {rework_combat_v5::DamageScope scope(target,source,0,1,damage);CHECK(scope.erosion_armor_reduction==0);CHECK(rework_combat_v5::post_armor_damage(target,1000)==1000);}
 ranks[19]=0;g.normal_hit=false;
 {rework_combat_v5::DamageScope scope(target,source,84,1,damage);CHECK(scope.erosion_armor_reduction==0);CHECK(rework_combat_v5::post_armor_damage(target,1000)==1000);}
 qa9_fixture::end();
}
inline void qa62_negative_armor_bonus_scales_by_point33_for_zerglings_only(){
 using namespace rework_fixture;
 for(U32 source_id:{37u,54u,0u})for(auto sample:{std::pair<U32,U32>{33,340},{99,509},{100,512},{132,593}}){
  qa9_fixture::begin({190});auto source=unit(source_id,1,100,100),target=unit(37,6,150,100);g.normal_hit=true;
  auto status=rework_combat_v5::state(target);status->erosion=sample.first;status->erosion_owner=1;
  const U32 w=original_stat({0,17,source_id});std::int32_t amount=256;
  {rework_combat_v5::DamageScope scope(target,source,w,1,amount);CHECK(amount==int(source_id==0?256:sample.second));CHECK(raw_value(0,27,37)==0);CHECK(scope.erosion_armor_reduction==0);}
  qa9_fixture::end();
 }
}
inline void qa62_target_lifecycle_and_primary_only_stacks(){
 using namespace rework_fixture;qa9_fixture::begin({190});auto source=unit(37,1,100,100),target=unit(39,6,150,100);
 rework_combat_v5::ordinary_hit(source,target,256,35,true);CHECK(rework_combat_v5::state(target)->erosion==0);
 rework_combat_v5::ordinary_hit(source,target,256,35,false);CHECK(rework_combat_v5::state(target)->erosion==33);
 source->flags|=0x40000000u;rework_combat_v5::focus_hit(source,target,256,35);CHECK(rework_combat_v5::state(target)->erosion==33);
 source->flags&=~0x40000000u;source->player=6;rework_combat_v5::focus_hit(source,target,256,35);CHECK(rework_combat_v5::state(target)->erosion==33);
 source->player=1;game.frame_count+=10000;rework_combat_v5::focus_hit(source,target,256,35);CHECK(rework_combat_v5::state(target)->erosion==66);
 target->player=2;CHECK(rework_combat_v5::state(target)->erosion==0);target->player=6;
 rework_combat_v5::focus_hit(source,target,256,35);CHECK(rework_combat_v5::state(target)->erosion==33);
 rework_combat_v5::created(target);CHECK(rework_combat_v5::state(target)->erosion==0);qa9_fixture::end();
}
inline void run_qa62_groups(){qa62_exact_hundredth_stacks_multiple_sources_and_saturation();qa62_fractional_armor_health_callback_size_rules_and_restore();qa62_shields_spill_and_armor_ignore_keep_native_boundaries();qa62_negative_armor_bonus_scales_by_point33_for_zerglings_only();qa62_target_lifecycle_and_primary_only_stacks();}
}
