#pragma once
namespace host_test {
inline constexpr std::size_t qa64_group_count=5;
namespace qa64_fixture {
inline U32 __cdecl no_native_attack(bw::Unit*,bw::Unit*,U32){return 0;}
inline U32 __cdecl outside(bw::Unit* source,bw::Unit* target){const U32 w=raw_value(0,19,103),range=raw_value(1,5,w);return rework_combat_v5::dist(source,target)>std::uint64_t(range)*range;}
inline U32 __cdecl weapon(bw::Unit* source,U32 w,bw::Unit* target){
 CHECK(source->unit_id==103&&w==109);CHECK(raw_value(0,19,103)==109&&raw_value(0,20,103)==1);CHECK(raw_value(1,3,w)&1u);
 return target->detection_status!=0;
}
inline rework_combat_v5::WeaponTargetFn saved_weapon=nullptr;
inline bw::Unit* begin(bool held=true){
 qa9_fixture::begin(held?std::initializer_list<U32>{97}:std::initializer_list<U32>{});rework_fixture::install();
 saved_weapon=rework_combat_v5::native_weapon_target;rework_combat_v5::native_weapon_target=weapon;multi_target::can_attack=no_native_attack;multi_target::outside_range=outside;
 auto source=rework_fixture::unit(103,1,100,100);source->flags|=0x10u;source->order=2;return source;
}
inline void end(){rework_combat_v5::native_weapon_target=saved_weapon;qa9_fixture::end();}
inline void __cdecl native_pierce(bw::Bullet* b){
 CHECK(raw_value(1,3,b->weapon_id)==1);CHECK(rework_combat_v5::DamageScope::current_percent==100);
 living_units([&](bw::Unit* target){if(target==b->parent||target->player==b->player||!rework_combat_v5::eligible(target))return;
  if((target->flags&4u)&&std::abs(target->flingy.position.x-b->target.x)<=20&&std::abs(target->flingy.position.y-b->target.y)<=20)
   combat_effects::weapon_damage(target,20*256,b->weapon_id,1,0,b->parent,b->player,qa9_fixture::damage);
 });
}
}
inline void qa64_burrowed_lurker_acquires_air_and_uses_shared_native_cooldown(){
 using namespace rework_fixture;auto source=qa64_fixture::begin();auto target=unit(43,6,200,100,true);unit(43,6,220,100,true);
 const auto saved=source->order_target;const auto flags=raw_value(1,3,109);CHECK(flags==2&&raw_value(0,19,103)==130&&raw_value(0,20,103)==0);
 pulse(100);CHECK(multi_fixture::shots.size()==1&&multi_fixture::shots[0].target==target&&multi_fixture::shots[0].weapon==109);
 const auto b=&multi_fixture::bullets[0];const auto& shot=rework_combat_v5::projectiles.at(b);CHECK(shot.layer==1&&shot.percent==100&&!shot.secondary);
 const auto period=multi_target::period(source,109);CHECK(source->ground_cooldown==period&&source->air_cooldown==period);
 CHECK(source->order==2&&source->order_target.unit==saved.unit&&raw_value(1,3,109)==flags&&raw_value(0,19,103)==130);
 pulse(100);pulse(101);CHECK(multi_fixture::shots.size()==1);
 source->ground_cooldown=source->air_cooldown=0;pulse(100+period-1);CHECK(multi_fixture::shots.size()==1);pulse(100+period);CHECK(multi_fixture::shots.size()==2);
 qa64_fixture::end();
}
inline void qa64_air_fire_respects_burrow_owner_detection_status_and_orders(){
 using namespace rework_fixture;
 for(U32 mode=0;mode<10;mode++){
  auto source=qa64_fixture::begin(mode!=0);auto target=unit(43,6,200,100,true);
  if(mode==1)source->flags&=~0x10u;if(mode==2)source->player=6;if(mode==3)source->flags|=0x40000000u;
  if(mode==4)source->stasis_timer=1;if(mode==5)source->lockdown_timer=1;if(mode==6)source->maelstrom_timer=1;
  if(mode==7)source->order=6;if(mode==8)source->flingy.current_speed=1;if(mode==9)source->flags|=0x40u;
  pulse(100);CHECK(multi_fixture::shots.empty()&&target->flingy.hitpoints==256000);qa64_fixture::end();
 }
 auto source=qa64_fixture::begin();auto target=unit(43,6,200,100,true);target->flags|=0x100u;target->detection_status=0;
 pulse(100);CHECK(multi_fixture::shots.empty());target->detection_status=0xff;static_cast<bw::SpriteScr*>(target->flingy.sprite)->visibility_mask=0;
 pulse(101);CHECK(multi_fixture::shots.empty());static_cast<bw::SpriteScr*>(target->flingy.sprite)->visibility_mask=0xff;target->flingy.position.x=500;
 pulse(102);CHECK(multi_fixture::shots.empty());target->flingy.position.x=200;target->stasis_timer=1;pulse(103);CHECK(multi_fixture::shots.empty());
 target->stasis_timer=0;pulse(104);CHECK(multi_fixture::shots.size()==1&&source->flags&0x10u);qa64_fixture::end();
}
inline void qa64_explicit_air_target_and_ground_attack_do_not_double_fire(){
 using namespace rework_fixture;auto source=qa64_fixture::begin();auto nearby_air=unit(43,6,150,100,true),chosen=unit(43,6,250,100,true);source->order=11;multi_fixture::target(source,chosen);
 pulse(100);CHECK(multi_fixture::shots.size()==1&&multi_fixture::shots[0].target==chosen&&source->order_target.unit==chosen);qa64_fixture::end();
 source=qa64_fixture::begin();auto ground=unit(37,6,180,100);nearby_air=unit(43,6,150,100,true);source->order=11;multi_fixture::target(source,ground);
 pulse(100);CHECK(multi_fixture::shots.empty()&&source->order_target.unit==ground);bullet(source,ground,109);source->order_target.unit=nullptr;
 pulse(100);CHECK(multi_fixture::shots.size()==1);source->ground_cooldown=10;pulse(101);CHECK(multi_fixture::shots.size()==1);
 CHECK(nearby_air->flingy.hitpoints==256000);qa64_fixture::end();
}
inline void qa64_native_air_impact_hits_only_air_at_one_hundred_percent(){
 using namespace rework_fixture;auto source=qa64_fixture::begin();auto target=unit(43,6,200,100,true),other=unit(43,6,210,100,true),ground=unit(37,6,200,100),ally=unit(43,1,205,100,true);
 pulse(100);CHECK(multi_fixture::shots.size()==1);auto b=&multi_fixture::bullets[0];const auto before=raw_value(1,3,109);
 owner_missile_hook(b,qa64_fixture::native_pierce);CHECK(target->flingy.hitpoints==256000-20*256&&other->flingy.hitpoints==256000-20*256);
 CHECK(ground->flingy.hitpoints==256000&&ally->flingy.hitpoints==256000&&raw_value(1,3,109)==before);CHECK(source->flags&0x10u);qa64_fixture::end();
}
inline void qa64_failed_native_allocation_does_not_consume_attack_clock(){
 using namespace rework_fixture;auto source=qa64_fixture::begin();unit(43,6,200,100,true);multi_fixture::fail_all=true;
 pulse(100);CHECK(multi_fixture::shots.empty()&&!source->ground_cooldown&&!source->air_cooldown&&rework_combat_v5::state(source)->next_air==0);
 multi_fixture::fail_all=false;pulse(101);CHECK(multi_fixture::shots.size()==1&&source->ground_cooldown&&source->air_cooldown);qa64_fixture::end();
}
inline void run_qa64_groups(){qa64_burrowed_lurker_acquires_air_and_uses_shared_native_cooldown();qa64_air_fire_respects_burrow_owner_detection_status_and_orders();qa64_explicit_air_target_and_ground_attack_do_not_double_fire();qa64_native_air_impact_hits_only_air_at_one_hundred_percent();qa64_failed_native_allocation_does_not_consume_attack_clock();}
}
