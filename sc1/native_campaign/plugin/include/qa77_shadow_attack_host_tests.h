#pragma once
// Native command/Order adapters with explicit host command predicates.
// These are production-code regressions, not a live engine or visual playtest.
namespace host_test {
namespace qa77_fixture {
inline std::array<bw::Unit*,2> selected{};
inline U32 requested_order=6;inline bool queued=false;
inline U32 accepted=0;
inline void native_command(){
 for(auto u:selected){
  // OrderAllowed/Stop reject incomplete, disabled, lockdown, stasis and
  // maelstrom units before replacing orders or allocating queued orders.
  if(!u || !(u->flags&1u) || (u->flags&0x400u) || u->lockdown_timer || u->stasis_timer || u->maelstrom_timer)continue;
  ++accepted;if(queued){++u->highlight_order_count;continue;}
  u->order=U8(requested_order);u->order_target={1200,1200,nullptr};
 }
}
inline void __cdecl packet(const U8*,U32){native_command();}
inline void __cdecl commands(const void*,U32,U32){native_command();}
inline void __cdecl click(void*){native_command();}
}
inline void qa77_shadow_starts_only_on_attack_intent(){
 using namespace rework_fixture;
 for(U32 id:{61u,74u,75u})for(U32 order:{1u,2u,3u,6u,49u,152u,137u})for(bool stale_target:{false,true}){
  qa9_fixture::begin({321});relocation();auto u=unit(id,1,500,500),enemy=unit(37,6,600,500);u->order=U8(order);u->flags|=0x08000000u;u->ground_cooldown=12;
  if(stale_target)multi_fixture::target(u,enemy);else u->order_target={700,500,nullptr};
  auto s=rework_combat_v5::state(u);s->last_launch=100;const auto hp=enemy->flingy.hitpoints;qa75_fixture::order_calls=0;
  for(U32 frame=100;frame<124;frame++){
   game.frame_count=frame;owner_order_hook(u,qa75_fixture::original_order);rework_combat_v5::focus_tick(u,*s);
  }
  rework_combat_v5::shadow_begin(u,enemy);
  rework_combat_v5::ordinary_hit(u,enemy,256,original_stat({0,17,id}),false);
  CHECK(!s->shadow_active&&s->shadow_cooldown==0&&s->shadow_count==0&&moves==0);
  CHECK(u->order==order&&u->flingy.position.x==500&&enemy->flingy.hitpoints==hp&&qa75_fixture::order_calls==24);
  relocation_end();qa9_fixture::end();
 }
 for(U32 order:{8u,9u,10u,11u,12u,14u,21u,22u,107u,157u,158u}){
  qa9_fixture::begin({321});relocation();auto u=unit(61,1,500,500),enemy=unit(37,6,692,500);u->order=U8(order);
  if(order!=14)multi_fixture::target(u,enemy);else u->order_target={1200,500,nullptr};
  const auto hp=enemy->flingy.hitpoints;qa75_fixture::order_calls=0;owner_order_hook(u,qa75_fixture::original_order);auto s=rework_combat_v5::state(u);
  CHECK(s->shadow_active&&qa75_fixture::order_calls==0&&enemy->flingy.hitpoints==hp);
  relocation_end();qa9_fixture::end();
 }
 qa9_fixture::begin({321});relocation();auto u=unit(61,1,500,500);unit(37,6,600,500);u->order=107;u->order_target={500,500,nullptr};owner_order_hook(u,qa75_fixture::original_order);CHECK(!rework_combat_v5::state(u)->shadow_active);relocation_end();qa9_fixture::end();
 std::printf("QA77_SHADOW_START move_follow_idle_patrol_blocked=1 stale_target_cooldown_blocked=1 attack_before_first_hit=1 attack_move=1 hold_requires_target=1\n");
}
inline void qa77_shadow_commands_ignored_until_cast_finishes(){
 using namespace rework_fixture;using namespace qa77_fixture;
 for(U32 path=0;path<3;path++){
  qa9_fixture::begin({321});relocation();projectile_audit_fixture::load_dimensions();
  auto u=unit(61,1,500,500),enemy=unit(37,6,692,500),other=unit(65,1,510,500);u->flags|=1;other->flags|=1;u->order=10;multi_fixture::target(u,enemy);
  int old_queue=0;u->order_queue_begin=u->order_queue_end=&old_queue;u->highlight_order_count=1;selected={u,other};
  const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa76_fixture::damage;qa75_fixture::victims.clear();qa76_fixture::strike_positions.clear();
  rework_combat_v5::shadow_begin(u,enemy);auto s=rework_combat_v5::state(u);CHECK(s->shadow_active);
  {rework_combat_v5::CommandScope outer(1);CHECK(u->lockdown_timer==1);{rework_combat_v5::CommandScope inner(1);CHECK(u->lockdown_timer==1);}CHECK(u->lockdown_timer==1);}CHECK(!u->lockdown_timer);
  const U8 data[11]={0x15,0,0,0,0,0,0,0,0,6,0};saved_handle=1;
  for(U32 i=0;i<5;i++){
   game.frame_count=100+i*4;requested_order=i%2?1u:6u;queued=i==2;accepted=0;
   if(path==0)owner_commands_hook(data,11,0,commands);
   else if(path==1)rework_combat_v5::motion_command(data,11,1,0,packet);
   else owner_rclick_hook(nullptr,click);
   CHECK(accepted==1&&s->shadow_active&&!u->lockdown_timer);
   CHECK(u->order==10&&u->order_target.unit==enemy&&u->order_queue_begin==&old_queue&&u->order_queue_end==&old_queue&&u->highlight_order_count==1);
   owner_order_hook(u,qa75_fixture::original_order);rework_combat_v5::focus_tick(u,*s);CHECK(qa75_fixture::victims.size()==i+1);
  }
  CHECK(!s->shadow_active&&u->flingy.position.x==500&&u->flingy.position.y==500&&!(u->flags&0x4000000u));
  requested_order=6;queued=false;accepted=0;owner_commands_hook(data,11,0,commands);CHECK(accepted==2&&u->order==6&&!u->lockdown_timer);
  combat_effects::original_weapon_damage=saved;relocation_end();qa9_fixture::end();
 }
 std::printf("QA77_SHADOW_COMMANDS process_commands=1 motion_packet=1 right_click=1 queued_orders_ignored=1 mixed_selection_preserved=1 all_five_hits=1 unlocked_after_return=1\n");
}
inline constexpr std::size_t qa77_group_count=2;
inline void run_qa77_groups(){qa77_shadow_starts_only_on_attack_intent();qa77_shadow_commands_ignored_until_cast_finishes();}
}
