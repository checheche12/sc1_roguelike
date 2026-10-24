#pragma once
namespace host_test {
namespace qa75_fixture {
inline std::int32_t projectile_amount=0;
inline bw::Unit* splash=nullptr;
inline U32 order_calls=0;
inline std::vector<bw::Unit*> victims;
inline std::vector<std::int32_t> shadow_damage;
inline bw::Unit* building_blocker=nullptr;
inline U32 __cdecl building_edge_place(bw::Unit* u,const bw::Point* desired,bw::Point* result,const void*,U32 a,U32 b){
 CHECK(!a&&!b);*result=*desired;
 if(building_blocker){
  const auto target=multi_target::dimensions(building_blocker->unit_id),caster=multi_target::dimensions(u->unit_id);
  const int x=desired->x-building_blocker->flingy.position.x,y=desired->y-building_blocker->flingy.position.y;
  CHECK(x>target.right+caster.left || -x>target.left+caster.right || y>target.bottom+caster.top || -y>target.top+caster.bottom);
 }return 1;
}
inline void __cdecl split(bw::Unit* u,std::int32_t damage,U8 weapon,U32 divisor,U8 direction,bw::Unit* source,U32 owner){
 victims.push_back(u);combat_audit::native_split(u,damage,weapon,divisor,direction,source,owner);
}
inline void __cdecl hit(bw::Unit* u,bw::Bullet* b,U32 divisor){combat_effects::weapon_damage(u,projectile_amount,b->weapon_id,divisor,0,b->parent,b->player,split);}
inline void __cdecl missile(bw::Bullet* b){owner_hit_hook(b->target.unit,b,1,hit);if(splash)owner_hit_hook(splash,b,1,hit);}
inline void projectile(bw::Unit* source,bw::Unit* target,U32 weapon,U32 amount){
 projectile_amount=std::int32_t(amount);auto b=rework_fixture::bullet(source,target,weapon);CHECK(b);owner_missile_hook(b,missile);
}
inline void __cdecl record_damage(bw::Unit* u,std::int32_t damage,U8 weapon,U32 divisor,U8 direction,bw::Unit* source,U32 owner){victims.push_back(u);shadow_damage.push_back(damage);qa39_fixture::hp_shield_damage(u,damage,weapon,divisor,direction,source,owner);}
inline void __cdecl native_regeneration(bw::Unit* u){u->shields=std::int32_t(std::min(std::uint64_t(effective_max_shields(u))*256u,std::uint64_t(std::max(0,u->shields))+7u));}
inline void __cdecl no_regeneration(bw::Unit*){}
inline void __cdecl instant_regeneration(bw::Unit* u){u->shields+=100*256;}
inline void __cdecl shield_damage(bw::Unit* u){u->shields-=50;}
inline void __cdecl transfer_regeneration(bw::Unit* u){u->shields+=7;u->player=6;}
inline void __cdecl original_order(bw::Unit*){++order_calls;}
}
inline void qa75_retaliation_real_melee_and_projectile_callback_chain(){
 using namespace rework_fixture;using namespace qa75_fixture;
 for(U32 id:{68u,76u}){
  qa9_fixture::begin({139});combat_audit::armor=0;victims.clear();splash=nullptr;
  const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=split;
  auto archon=unit(id,1,100,100),ling=unit(37,6,120,100),hydra=unit(38,6,140,100),target=unit(39,6,160,100),neighbor=unit(39,6,170,100);
  archon->shields=2000*256;archon->flingy.hitpoints=10000*256;target->flingy.hitpoints=10000*256;
  auto state=rework_combat_v5::state(archon);const auto enemy_hp=ling->flingy.hitpoints;
  combat_audit::melee(ling,archon,100*256);CHECK(state->retaliation==30*256&&ling->flingy.hitpoints==enemy_hp);
  projectile(hydra,archon,38,100*256);CHECK(state->retaliation==60*256);
  combat_effects::weapon_damage(archon,100*256,30,1,0,hydra,6,split);CHECK(state->retaliation==60*256);
  combat_audit::melee(ling,archon,1000*256);CHECK(state->retaliation==200*256);
  const auto target_hp=target->flingy.hitpoints,neighbor_hp=neighbor->flingy.hitpoints;
  splash=neighbor;projectile(archon,target,70,20*256);splash=nullptr;
  CHECK(state->retaliation==0&&target->flingy.hitpoints==target_hp-240*256&&neighbor->flingy.hitpoints==neighbor_hp);
  projectile(archon,target,70,20*256);CHECK(target->flingy.hitpoints==target_hp-280*256);
  combat_audit::melee(ling,archon,10*256);CHECK(state->retaliation==3*256);
  archon->player=6;CHECK(rework_combat_v5::state(archon)->retaliation==0);
  std::printf("QA75_RETALIATION unit=%u melee=30 projectile=30 spell=0 cap=200 first_attack=240 next_attack=40 splash=0\n",id);
  combat_effects::original_weapon_damage=saved;qa9_fixture::end();
 }
}
inline void qa75_archon_natural_shield_regeneration_eleven_times(){
 using namespace rework_fixture;using namespace qa75_fixture;
 for(U32 id:{68u,76u}){
  qa9_fixture::begin({139});auto u=unit(id,1,100,100);u->flags|=1;u->shields=0;
  for(U32 frame=0;frame<24;frame++){game.frame_count=100+frame;owner_timer_hook(u,native_regeneration);}
  CHECK(u->shields==24*7*11&&rework_combat_v5::state(u)->retaliation==0);
  const auto before=u->shields;owner_timer_hook(u,no_regeneration);CHECK(u->shields==before);
  owner_timer_hook(u,instant_regeneration);CHECK(u->shields==before+100*256);
  owner_timer_hook(u,shield_damage);CHECK(u->shields==before+100*256-50);
  const auto maximum=std::int32_t(effective_max_shields(u)*256u);u->shields=maximum-3;owner_timer_hook(u,native_regeneration);CHECK(u->shields==maximum);
  u->shields=0;owner_timer_hook(u,transfer_regeneration);CHECK(u->shields==7);
  qa9_fixture::end();
 }
 for(U32 id:{63u,61u,64u,154u}){
  qa9_fixture::begin({139});auto u=unit(id,1,100,100);u->flags|=1;u->shields=0;owner_timer_hook(u,native_regeneration);CHECK(u->shields==7);qa9_fixture::end();
 }
 qa9_fixture::begin({});auto u=unit(68,1,100,100);u->flags|=1;u->shields=0;owner_timer_hook(u,native_regeneration);CHECK(u->shields==7);qa9_fixture::end();
 qa9_fixture::begin({139});u=unit(68,6,100,100);u->flags|=1;u->shields=0;owner_timer_hook(u,native_regeneration);CHECK(u->shields==7);qa9_fixture::end();
 qa9_fixture::begin({139});u=unit(68,1,100,100);u->flags|=1|0x40000000u;u->shields=0;owner_timer_hook(u,native_regeneration);CHECK(u->shields==7);qa9_fixture::end();
}
inline void qa75_shadow_pre_hit_six_tiles_chain_five_buildings_ground_and_return(){
 using namespace rework_fixture;using namespace qa75_fixture;
 qa9_fixture::begin({321});relocation();auto u=unit(61,1,500,500),a=unit(37,6,693,500),b=unit(106,6,852,500),c=unit(37,6,1012,500),air=unit(43,6,700,500,true);
 projectile_audit_fixture::load_dimensions();building_blocker=b;rework_relocation::native_place=building_edge_place;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=record_damage;victims.clear();shadow_damage.clear();order_calls=0;
 u->order=10;multi_fixture::target(u,a);const auto hp=a->flingy.hitpoints;
 owner_order_hook(u,original_order);CHECK(order_calls==1&&!rework_combat_v5::state(u)->shadow_active);
 a->flingy.position.x=692;owner_order_hook(u,original_order);auto s=rework_combat_v5::state(u);
 CHECK(s->shadow_active&&order_calls==1&&a->flingy.hitpoints==hp);
 for(U32 i=0;i<5;i++){game.frame_count=100+i*4;rework_combat_v5::focus_tick(u,*s);}
 CHECK(victims.size()==5&&victims[0]==a&&victims[1]==b&&victims[2]==c);
 const auto weapon=original_stat({0,17,u->unit_id});
 const auto normal_damage=owner_stat(u->player,{1,14,weapon})+owner_stat(u->player,{1,15,weapon})*rework_combat_v5::upgrade_level(u->player,original_stat({1,6,weapon}));
 CHECK(normal_damage>0&&shadow_damage.size()==5);
 for(const auto amount:shadow_damage)CHECK(amount==std::int32_t(normal_damage*512));
 CHECK(std::find(victims.begin(),victims.end(),air)==victims.end());
 CHECK(!s->shadow_active&&u->flingy.position.x==500&&u->flingy.position.y==500&&!(u->flags&0x4000000u));
 CHECK(s->shadow_cooldown==388);rework_combat_v5::shadow_prepare(u);CHECK(!s->shadow_active);
 combat_effects::original_weapon_damage=saved;building_blocker=nullptr;relocation_end();qa9_fixture::end();
 // A unit161px from the first victim is outside the chain. Killing the only
 // valid victim must return immediately to the cast origin.
 qa9_fixture::begin({321});relocation();u=unit(61,1,500,500);a=unit(37,6,692,500);b=unit(37,6,853,500);a->flingy.hitpoints=1;
 combat_effects::original_weapon_damage=record_damage;victims.clear();u->order=10;multi_fixture::target(u,a);owner_order_hook(u,original_order);s=rework_combat_v5::state(u);
 rework_combat_v5::focus_tick(u,*s);CHECK(a->flingy.hitpoints==0);game.frame_count+=4;rework_combat_v5::focus_tick(u,*s);
 CHECK(!s->shadow_active&&victims.size()==1&&u->flingy.position.x==500&&u->flingy.position.y==500);
 combat_effects::original_weapon_damage=saved;relocation_end();qa9_fixture::end();
 // Even an air weapon on the DT cannot enable Shadow Fury against air.
 qa9_fixture::begin({321});relocation();u=unit(61,1,500,500);air=unit(43,6,600,500,true);u->order=10;multi_fixture::target(u,air);
 const auto old_air=raw_value(0,19,61);auto air_table=table_for({0,19,61},false);CHECK(air_table);write_entry(air_table,61,0);owner_order_hook(u,original_order);CHECK(!rework_combat_v5::state(u)->shadow_active);write_entry(air_table,61,old_air);
 relocation_end();qa9_fixture::end();
}
inline void qa75_reaver_speed_is_double_for_parent_and_hero_only(){
 using namespace rework_fixture;qa9_fixture::begin({141});
 for(U32 id:{81u,83u}){auto u=unit(id,1,100,100);CHECK(std::abs(rework_combat_v5::speed_ratio(u)-2.0)<0.000001);u->player=6;CHECK(std::abs(rework_combat_v5::speed_ratio(u)-1.0)<0.000001);}
 for(U32 id:{85u,69u,65u}){auto u=unit(id,1,100,100);CHECK(std::abs(rework_combat_v5::speed_ratio(u)-1.0)<0.000001);}
 auto target=unit(39,6,120,100),neighbor=unit(39,6,130,100);
 for(U32 id:{81u,83u,85u}){
  auto source=unit(id,1,100,100);CHECK(rework_combat_v5::focus_damage(source,target,82,1000,true)==2500);
  CHECK(rework_combat_v5::focus_damage(source,neighbor,82,1000,false)==2500);
  const auto before=target->flingy.hitpoints,near_before=neighbor->flingy.hitpoints;
  qa75_fixture::splash=neighbor;qa75_fixture::projectile(source,target,82,1000);qa75_fixture::splash=nullptr;
  CHECK(target->flingy.hitpoints==before-2500&&neighbor->flingy.hitpoints==near_before-2500);
  source->player=6;CHECK(rework_combat_v5::focus_damage(source,target,82,1000,true)==1000);
 }
 qa9_fixture::end();
}
inline constexpr std::size_t qa75_group_count=4;
inline void run_qa75_groups(){qa75_retaliation_real_melee_and_projectile_callback_chain();qa75_archon_natural_shield_regeneration_eleven_times();qa75_shadow_pre_hit_six_tiles_chain_five_buildings_ground_and_return();qa75_reaver_speed_is_double_for_parent_and_hero_only();}
}
