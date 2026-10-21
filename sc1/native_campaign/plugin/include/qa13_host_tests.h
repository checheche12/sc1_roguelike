#pragma once
namespace host_test {
inline constexpr std::size_t qa13_group_count=3;
namespace qa13_fixture {
inline void begin(){reset();talent_power::enabled=true;rework_combat_v5::bind([](const GrowthSnapshot& s,U32 n) noexcept {return rework_catalog::rank(s,n);});}
inline void end(){rework_fixture::finish();talent_power::enabled=false;}
inline GrowthSnapshot snapshot(U32 ordinal,U32 stacks=1){auto s=economy_snapshot({ordinal});const auto slot=rework_catalog::kRankSlots[ordinal];if(slot>=0)s.talent_ranks[slot]=stacks;return s;}
}
inline void qa13_health_all_groups_ranks_native_caps_and_display(){
 using namespace qa13_fixture;U32 targets=0;
 for(U32 ordinal:{26u,27u,28u,67u,68u,69u,108u,109u,110u})for(U32 stacks=1;stacks<=4;stacks++){
  begin();std::vector<bw::Unit*> own;
  for(U32 id=0;id<228;id++)if(rework_combat_v5::group(ordinal,id)){
   auto u=add(id,1,100,100,int(original_stat({0,8,id})));u->flags=1;u->shields=int(original_stat({0,7,id})*256);own.push_back(u);
  }
  CHECK(!own.empty());auto enemy=add(own[0]->unit_id,6,200,100),ally=add(own[0]->unit_id,2,220,100),neutral=add(own[0]->unit_id,11,240,100);
  CHECK(apply_snapshot(nullptr,snapshot(ordinal,stacks)));
  for(auto u:own){const U32 id=u->unit_id,original=original_stat({0,8,id});const U32 expected=U32((std::uint64_t(original)*(100+28*stacks)+50)/100);
   CHECK(owner_stat(1,{0,8,id})==expected && U32(u->flingy.hitpoints)==expected);CHECK(original_stat({0,8,id})==original);
   U32 shown=0,shields=0;CHECK(max_hp_cache::read_display(u,shown,shields)&&shown==expected);
   if(ordinal>=108){const U32 shield=(original_stat({0,7,id})*(100+28*stacks)+50)/100;CHECK(owner_stat(1,{0,7,id})==shield && shields==shield && U32(u->shields)==shield*256);}
   ++targets;
  }
  for(auto u:{enemy,ally,neutral})CHECK(owner_stat(u->player,{0,8,u->unit_id})==original_stat({0,8,u->unit_id}));
  auto first=own[0];const U32 expected=owner_stat(1,{0,8,first->unit_id});first->flingy.hitpoints=1;first->shields=0;
  owner_unit_hook(first,rank_fixture::native_regeneration);CHECK(U32(first->flingy.hitpoints)==expected);
  const U8 skins[]={1,1};auto born=owner_create_hook(first->unit_id,200,200,1,skins,rank_fixture::create_full);CHECK(born && U32(born->flingy.hitpoints)==expected);
  end();
 }
 CHECK(targets>300);
}
inline void qa13_half_armor_integer_fraction_and_owner_isolation(){
 using namespace qa13_fixture;
 for(U32 ordinal:{11u,12u})for(U32 stacks=1;stacks<=4;stacks++){
  begin();const U32 id=ordinal==11?0u:8u;auto target=rework_fixture::unit(id,1,100,100,ordinal==12),enemy=rework_fixture::unit(0,6,200,100);
  CHECK(apply_snapshot(nullptr,snapshot(ordinal,stacks)));CHECK(owner_stat(1,{0,27,id})==original_stat({0,27,id})+stacks/2);
  CHECK(owner_stat(6,{0,27,id})==original_stat({0,27,id}));U32 shown=0;CHECK(max_hp_cache::read_armor(target,shown)&&shown==owner_stat(1,{0,27,id}));
  g.normal_hit=true;std::int32_t damage=10*256;{
   rework_combat_v5::DamageScope hit(target,enemy,0,6,damage);CHECK(hit.half_armor_reduction==(stacks%2)*128);
   CHECK(rework_combat_v5::post_armor_damage(target,damage-int(stacks/2)*256)==damage-int(stacks)*128);
  }
  target->player=6;{rework_combat_v5::DamageScope hit(target,enemy,0,6,damage);CHECK(hit.half_armor_reduction==0);}end();
 }
}
inline void qa13_supply_box_reduction_total_rounding_and_once(){
 using namespace qa13_fixture;
 for(U32 total:{0u,1u,2u,3u,4u,17u,80u}){
  begin();auto s=snapshot(5);U32 remaining=total;
  for(U32 i=0;i<50&&remaining;i++){const U32 n=std::min(remaining,U32(frozen::kCurseMaxStacks[i]));s.curse_counts[i]=U8(n);remaining-=n;}
  CHECK(!remaining);game.minerals[1]=1000;game.gas[1]=500;game.minerals[6]=700;game.gas[6]=800;
  CHECK(apply_snapshot(nullptr,s));const U32 bonus=total*25;CHECK(game.minerals[1]==1000+bonus && game.gas[1]==500+bonus);CHECK(game.minerals[6]==700&&game.gas[6]==800);
  rework_economy_v5::after_snapshot();CHECK(game.minerals[1]==1000+bonus);s.completed_phase=2;CHECK(apply_snapshot(nullptr,s));CHECK(game.minerals[1]==1000+bonus&&game.gas[1]==500+bonus);end();
 }
 begin();auto s=economy_snapshot({});s.curse_counts[0]=2;CHECK(apply_snapshot(nullptr,s));s=snapshot(5);s.completed_phase=2;s.curse_counts[0]=2;CHECK(apply_snapshot(nullptr,s));CHECK(game.minerals[1]==0&&game.gas[1]==0);end();
 begin();s=snapshot(5);s.curse_counts[0]=2;game.minerals[1]=game.gas[1]=0xfffffff0;CHECK(apply_snapshot(nullptr,s));CHECK(game.minerals[1]==0xffffffff&&game.gas[1]==0xffffffff);end();
}
inline void run_qa13_groups(){qa13_health_all_groups_ranks_native_caps_and_display();qa13_half_armor_integer_fraction_and_owner_isolation();qa13_supply_box_reduction_total_rounding_and_once();}
}
