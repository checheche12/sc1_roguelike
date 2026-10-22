#pragma once
namespace host_test {
inline constexpr std::size_t qa61_group_count=7;
inline void qa61_tower_snapshot_health_shields_and_invalid_rank(){
 for(U32 rank:{0u,1u,2u}){
  qa13_fixture::begin();GrowthSnapshot s{};s.wire_version=2;qa38_units::set(s,322,rank);
  CHECK(apply_snapshot(nullptr,s));
  for(U32 id:{124u,144u,162u}){
   const auto hp=original_stat({0,8,id});CHECK(owner_stat(1,{0,8,id})==hp*(1+rank));
   CHECK(owner_stat(6,{0,8,id})==hp);
   if(id==162)CHECK(owner_stat(1,{0,7,id})==original_stat({0,7,id})*(1+rank));
  }
  auto invalid=s;qa38_units::set(invalid,322,3);CHECK(!apply_snapshot(nullptr,invalid));
  CHECK(rework_catalog::rank(g.growth,322)==rank);qa13_fixture::end();
 }
}
inline void qa61_tower_ground_upgrade_ids_and_native_upgrade_damage(){
 for(U32 rank:{0u,1u,2u}){
  qa9_fixture::begin({});rework_fixture::ranks[322]=rank;rework_fixture::install();
  for(U32 id:{124u,144u,162u})for(U32 field:{17u,19u}){
   const auto w=original_stat({0,field,id});if(w>=130)continue;
   const U32 upgrade=id==124?8u:id==144?11u:13u;
   CHECK(owner_stat(1,{1,6,w})==upgrade&&owner_stat(1,{1,15,w})==2);
   CHECK(owner_stat(6,{1,6,w})==original_stat({1,6,w}));
   CHECK(owner_stat(6,{1,15,w})==original_stat({1,15,w}));
   auto source=rework_fixture::unit(id,1,100,100),target=rework_fixture::unit(field==19?43:37,6,150,100,field==19);
   for(U32 level:{0u,1u,3u,9u}){
    auto p=rework_upgrade_storage::slot(1,upgrade);CHECK(p);*p=U8(level);
    const U32 raw=owner_stat(1,{1,14,w})+owner_stat(1,{1,15,w})*rework_combat_v5::upgrade_level(1,owner_stat(1,{1,6,w}));
    g.normal_hit=true;const U32 expected=(raw*(100+(field==19?50*rank:0))+50)/100;
    CHECK(rework_combat_v5::infantry_ui_value(source,w,raw)==expected);
    g.normal_hit=true;auto amount=int(raw*256);{rework_combat_v5::DamageScope scope(target,source,w,1,amount);}
    CHECK(amount==int(raw*256*(100+(field==19?50*rank:0))/100));
   }
  }
  qa9_fixture::end();
 }
}
inline void qa61_tower_native_projectile_fanout_filters_and_no_recursion(){
 using namespace rework_fixture;
 for(U32 id:{124u,144u,162u})for(U32 rank:{1u,2u}){
  qa9_fixture::begin({});ranks[322]=rank;install();auto source=unit(id,1,100,100),primary=unit(43,6,180,100,true);
  auto ground=unit(37,6,181,100),ally=unit(43,1,182,100,true),unseen=unit(43,6,183,100,true);
  static_cast<bw::SpriteScr*>(unseen->flingy.sprite)->visibility_mask=0;auto cloaked=unit(43,6,184,100,true);cloaked->detection_status=0;
  auto disabled=unit(43,6,185,100,true);disabled->stasis_timer=100;
  auto a=unit(43,6,190,100,true),b=unit(43,6,200,100,true);unit(43,6,210,100,true);
  const U32 w=original_stat({0,19,id});const auto range=owner_stat(1,{1,5,w});auto outside=unit(43,6,101+int(range),100,true);
  const auto order=source->order_target;bullet(source,primary,w);
  CHECK(rework_combat_v5::pending_shots.size()==rank);
  CHECK(rework_combat_v5::resolve(rework_combat_v5::pending_shots[0].target)==a);
  if(rank==2)CHECK(rework_combat_v5::resolve(rework_combat_v5::pending_shots[1].target)==b);
  for(const auto& shot:rework_combat_v5::pending_shots){CHECK(shot.percent==100&&shot.weapon==w);CHECK(shot.target.p!=outside&&shot.target.p!=ground&&shot.target.p!=ally&&shot.target.p!=unseen&&shot.target.p!=cloaked&&shot.target.p!=disabled);}
  const auto primary_order=source->order_target;pulse(101);
  CHECK(rework_combat_v5::pending_shots.empty()&&multi_fixture::shots.size()==1+rank);
  CHECK(source->order_target.unit==primary_order.unit&&primary_order.unit==primary&&order.unit==nullptr);
  for(U32 i=1;i<=rank;i++){
   auto extra=&multi_fixture::bullets[i];CHECK(rework_combat_v5::projectiles.at(extra).secondary);
   const auto raw=owner_stat(1,{1,14,w});g.normal_hit=true;auto amount=int(raw*256);
   {rework_combat_v5::MissileScope missile(extra);rework_combat_v5::DamageScope damage(extra->target.unit,source,w,1,amount);}
   CHECK(amount==int(raw*256*(100+50*rank)/100));
  }
  pulse(102);CHECK(multi_fixture::shots.size()==1+rank);qa9_fixture::end();
 }
}
inline void qa61_tower_ground_and_nonowner_attacks_do_not_fanout(){
 using namespace rework_fixture;
 for(U32 mode:{0u,1u,2u,3u}){
  qa9_fixture::begin({});ranks[322]=mode==3?0:2;install();
  auto source=unit(162,mode==1?6:1,100,100),target=unit(mode==0?37:43,6,150,100,mode!=0);
  if(mode==2)source->flags|=0x40000000u;
  unit(43,6,160,100,true);unit(43,6,170,100,true);
  const U32 w=original_stat({0,mode==0?17u:19u,162});bullet(source,target,w);
  CHECK(rework_combat_v5::pending_shots.empty());
  if(mode!=0)CHECK(rework_combat_v5::infantry_ui_value(source,w,20)==20);
  else CHECK(rework_combat_v5::infantry_ui_value(source,w,20)==20);
  qa9_fixture::end();
 }
}
inline void qa61_tower_sparse_targets_and_disabled_source(){
 using namespace rework_fixture;
 for(U32 mode:{0u,1u}){
  qa9_fixture::begin({322});ranks[322]=2;install();auto source=unit(124,1,100,100),target=unit(43,6,150,100,true);
  if(mode){source->lockdown_timer=100;unit(43,6,160,100,true);}
  bullet(source,target,original_stat({0,19,124}));CHECK(rework_combat_v5::pending_shots.empty());qa9_fixture::end();
 }
}
inline void qa61_vulture_legend_uses_normal_type_for_body_and_hero(){
 for(bool legendary:{false,true}){
  qa13_fixture::begin();auto s=qa13_fixture::snapshot(54);if(!legendary)s={};s.wire_version=2;
  CHECK(apply_snapshot(nullptr,s));
  for(U32 id:{2u,19u}){const auto w=original_stat({0,17,id});CHECK(w<130);
   CHECK(owner_stat(1,{1,7,w})==(legendary?3u:original_stat({1,7,w})));
   CHECK(owner_stat(6,{1,7,w})==original_stat({1,7,w}));
   {OwnerDatScope view(1,1);CHECK(raw_value(1,7,w)==(legendary?3u:original_stat({1,7,w})));}
   CHECK(raw_value(1,7,w)==original_stat({1,7,w}));
  }
  qa13_fixture::end();
 }
}
inline void qa61_reaver_legend_free_scarabs_with_discount_and_owner_cost_view(){
 for(bool legendary:{false,true})for(bool discount:{false,true}){
  qa13_fixture::begin();auto s=qa13_fixture::snapshot(141);if(!legendary)s={};s.wire_version=2;
  if(discount){const U32 bit=238+117;s.talent_bits[bit/32]|=1u<<(bit%32);}
  CHECK(apply_snapshot(nullptr,s));
  const auto original=original_stat({0,40,85});const auto expected=legendary?0u:discount?(original+1)/2:original;
  CHECK(owner_stat(1,{0,40,85})==expected&&rework_economy_v5::current_cost(85).mineral==expected);
  CHECK(owner_stat(6,{0,40,85})==original&&owner_stat(2,{0,40,85})==original);
  CHECK(owner_stat(1,{0,41,85})==original_stat({0,41,85}));
  CHECK(owner_stat(1,{0,40,73})==(discount?(original_stat({0,40,73})+1)/2:original_stat({0,40,73})));
  {OwnerDatScope view(1,1);CHECK(raw_value(0,40,85)==expected);}
  CHECK(raw_value(0,40,85)==original);qa13_fixture::end();
 }
}
inline void run_qa61_groups(){qa61_vulture_legend_uses_normal_type_for_body_and_hero();qa61_reaver_legend_free_scarabs_with_discount_and_owner_cost_view();qa61_tower_snapshot_health_shields_and_invalid_rank();qa61_tower_ground_upgrade_ids_and_native_upgrade_damage();qa61_tower_native_projectile_fanout_filters_and_no_recursion();qa61_tower_ground_and_nonowner_attacks_do_not_fanout();qa61_tower_sparse_targets_and_disabled_source();}
}
