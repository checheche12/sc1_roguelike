#pragma once
namespace host_test {
inline constexpr std::size_t qa60_group_count=5;
inline void qa60_wraith_ground_air_hero_damage_and_three_extras(){
 using namespace rework_fixture;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;
 for(U32 id:{8u,21u})for(bool air:{false,true})for(bool manual:{false,true}){
  qa9_fixture::begin({186});if(manual){ranks[31]=1;install();}
  auto source=unit(id,1,100,100,true),target=unit(air?43:37,6,200,100,air);
  const auto w=original_stat({0,air?19u:17u,id});CHECK(w<130);
  const auto base=owner_stat(1,{1,14,w});CHECK(rework_combat_v5::infantry_ui_value(source,w,base)==base*2);
  std::vector<bw::Unit*> victims;for(U32 n=0;n<5;n++)victims.push_back(unit(air?43:37,6,210+int(n),100,air));
  auto other_layer=unit(air?37:43,6,205,100,!air),ally=unit(air?43:37,1,205,100,air),outside=unit(air?43:37,6,329,100,air);
  auto b=bullet(source,target,w);const auto hp=target->flingy.hitpoints;
  g.normal_hit=true;g.bullet_hit_context=true;g.hit_source=source;g.hit_identity={source,source->unit_id,source->player,source->minor_unique_index};g.hit_bonus=0;
  {rework_combat_v5::MissileScope missile(b);combat_effects::weapon_damage(target,int(base*256),U8(w),1,0,source,1,qa9_fixture::damage);}
  CHECK(target->flingy.hitpoints==hp-int(base*512));U32 hit=0;
  for(auto u:victims)if(u->flingy.hitpoints!=256000){++hit;CHECK(u->flingy.hitpoints==256000-int(base*512));}
  CHECK(hit==3&&other_layer->flingy.hitpoints==256000&&ally->flingy.hitpoints==256000&&outside->flingy.hitpoints==256000);
  source->player=6;CHECK(rework_combat_v5::infantry_ui_value(source,w,base)==base);source->player=1;source->flags|=0x40000000u;
  CHECK(rework_combat_v5::infantry_ui_value(source,w,base)==base);qa9_fixture::end();
 }
 combat_effects::original_weapon_damage=saved;
}
inline void qa60_lockdown_skips_dense_locked_targets_and_prefers_fresh(){
 using namespace rework_fixture;namespace combat=rework_combat_v5;
 for(U32 mode:{0u,1u,2u,3u}){
  qa9_fixture::begin({63});auto ghost=unit(1,1,100,100),primary=unit(3,6,200,100);
  for(U32 n=0;n<80;n++){auto locked=unit(3,6,201+int(n%20),100);locked->lockdown_timer=100;}
  std::vector<bw::Unit*> reserved;
  for(U32 n=0;n<6;n++)reserved.push_back(unit(3,6,225+int(n),100));
  if(mode==0)for(auto u:reserved)combat::queue(ghost,u,32,100);
  if(mode==1)for(auto u:reserved){combat::Projectile p{};p.source=combat::identity(ghost);p.primary=combat::identity(u);p.weapon=32;p.created=game.frame_count;combat::projectiles[reinterpret_cast<bw::Bullet*>(u)]=p;}
  if(mode==2){for(auto u:reserved)combat::queue(ghost,u,32,100);combat::pending_work.swap(combat::pending_shots);}
  // Already impacted metadata must not reserve an unlocked target forever.
  if(mode==3)for(auto u:reserved){combat::Projectile p{};p.source=combat::identity(ghost);p.primary=combat::identity(u);p.weapon=32;p.created=game.frame_count;p.impact=true;combat::projectiles[reinterpret_cast<bw::Bullet*>(u)]=p;}
  std::vector<bw::Unit*> fresh;for(U32 n=0;n<6;n++)fresh.push_back(unit(3,6,300+int(n),100));
  const auto prior=combat::pending_shots.size();bullet(ghost,primary,32);CHECK(combat::pending_shots.size()==prior+6);
  for(U32 n=0;n<6;n++)CHECK(combat::resolve(combat::pending_shots[prior+n].target)==(mode==3?reserved[n]:fresh[n]));
  CHECK(primary->lockdown_timer==0);qa9_fixture::end();
 }
}
inline void qa60_lockdown_sparse_fallback_and_existing_lock_exclusion(){
 using namespace rework_fixture;namespace combat=rework_combat_v5;
 qa9_fixture::begin({63});auto ghost=unit(1,1,100,100),primary=unit(3,6,200,100),busy=unit(3,6,210,100),locked=unit(3,6,220,100);
 locked->lockdown_timer=10;combat::queue(ghost,busy,32,100);bullet(ghost,primary,32);
 CHECK(combat::pending_shots.size()==2&&combat::resolve(combat::pending_shots.back().target)==busy);
 combat::pending_shots.clear();busy->lockdown_timer=10;bullet(ghost,primary,32);CHECK(combat::pending_shots.empty());qa9_fixture::end();
}
namespace qa60_motion_fixture {
inline bw::Unit* selected=nullptr;inline U32 order=6,calls=0;
inline void __cdecl rclick(void*){
 ++calls;CHECK(raw_value(0,28,selected->unit_id)==1);
 {OwnerDatScope enemy(6,6);CHECK(raw_value(0,28,selected->unit_id)==3);}
 CHECK(raw_value(0,28,selected->unit_id)==1);
 selected->order=U8(order);selected->order_target={400,300,nullptr};
}
inline void __cdecl packet(const U8*,U32){rclick(nullptr);}
inline void __cdecl unchanged(void*){++calls;CHECK(raw_value(0,28,selected->unit_id)==3);}
}
inline void qa60_mobile_siege_rightclick_ground_attack_and_packet_owner_view(){
 using namespace rework_fixture;namespace motion=qa60_motion_fixture;
 for(U32 id:{25u,30u}){
  qa9_fixture::begin({55});install();auto tank=unit(id,1,100,100);motion::selected=tank;motion::calls=0;
  CHECK(raw_value(0,28,id)==3&&owner_stat(1,{0,28,id})==1&&owner_stat(6,{0,28,id})==3);
  for(U32 order:{6u,21u,14u}){motion::order=order;owner_rclick_hook(nullptr,motion::rclick);
   CHECK(tank->order==order&&tank->order_target.x==400&&raw_value(0,28,id)==3);
  }
  U8 command[11]{};for(U32 packet:{0x14u,0x15u}){command[0]=U8(packet);motion::order=packet==0x14?6:14;
   rework_combat_v5::motion_command(command,11,1,0,motion::packet);CHECK(tank->order==motion::order&&raw_value(0,28,id)==3);
  }
  CHECK(motion::calls==5);qa9_fixture::end();
 }
}
inline void qa60_siege_rightclick_without_talent_keeps_stock_behavior(){
 using namespace rework_fixture;namespace motion=qa60_motion_fixture;
 qa9_fixture::begin({});motion::selected=unit(30,1,100,100);motion::calls=0;
 owner_rclick_hook(nullptr,motion::unchanged);CHECK(motion::calls==1&&raw_value(0,28,30)==3);
 qa9_fixture::end();
}
inline void run_qa60_groups(){qa60_wraith_ground_air_hero_damage_and_three_extras();qa60_lockdown_skips_dense_locked_targets_and_prefers_fresh();qa60_lockdown_sparse_fallback_and_existing_lock_exclusion();qa60_mobile_siege_rightclick_ground_attack_and_packet_owner_view();qa60_siege_rightclick_without_talent_keeps_stock_behavior();}
}
