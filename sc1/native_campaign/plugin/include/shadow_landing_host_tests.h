#pragma once
namespace host_test {
namespace shadow_landing_fixture {
inline bw::Point center{},origin{};
inline U32 mode=0,attempts=0;
inline U32 __cdecl place(bw::Unit*,const bw::Point* requested,bw::Point* result,const void*,U32,U32){
 ++attempts;*result=*requested;
 if(mode==1){
  // A wall blocks the line through the target, with open space to either side.
  const auto dx=int(center.x)-origin.x,dy=int(center.y)-origin.y;
  const auto cross=std::int64_t(requested->x-center.x)*dy-std::int64_t(requested->y-center.y)*dx;
  return std::abs(cross)>=24*std::max(std::abs(dx),std::abs(dy));
 }
 if(mode==2)return requested->x<=550; // The first target's entire far side is occupied.
 if(mode==3)return 0; // No legal landing anywhere.
 return 1;
}
inline void begin(){qa9_fixture::begin({321});rework_fixture::relocation();projectile_audit_fixture::load_dimensions();attempts=0;rework_relocation::native_place=place;qa75_fixture::victims.clear();qa75_fixture::shadow_damage.clear();}
inline void end(){rework_fixture::relocation_end();qa9_fixture::end();}
}
inline void shadow_landing_uses_clear_far_side_around_wall(){
 using namespace shadow_landing_fixture;
 for(U32 id:{61u,74u,75u})for(const auto direction:std::array<bw::Point,4>{{{-100,0},{100,0},{0,-100},{0,100}}}){
  begin();mode=1;center={500,500};origin={std::int16_t(500+direction.x),std::int16_t(500+direction.y)};
  auto u=rework_fixture::unit(id,1,origin.x,origin.y),target=rework_fixture::unit(37,6,center.x,center.y);
  CHECK(rework_combat_v5::shadow_cross_target(u,target));
  const auto p=u->flingy.position;
  CHECK(std::int64_t(origin.x-center.x)*(p.x-center.x)+std::int64_t(origin.y-center.y)*(p.y-center.y)<0);
  CHECK(attempts>3&&rework_fixture::moves==1);end();
 }
}
inline void shadow_landing_skips_unlandable_target_without_losing_strikes(){
 using namespace shadow_landing_fixture;begin();mode=2;
 auto u=rework_fixture::unit(61,1,500,500),blocked=rework_fixture::unit(37,6,600,500),clear=rework_fixture::unit(37,6,500,650);
 u->order=10;multi_fixture::target(u,blocked);clear->flingy.hitpoints=1000000;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa75_fixture::record_damage;
 rework_combat_v5::shadow_begin(u,blocked);auto s=rework_combat_v5::state(u);
 for(U32 i=0;i<5;i++){game.frame_count=100+i*4;rework_combat_v5::focus_tick(u,*s);CHECK(qa75_fixture::victims.size()==i+1&&qa75_fixture::victims.back()==clear);}
 CHECK(!s->shadow_active&&s->shadow_count==5&&s->shadow_step==5&&s->shadow_cooldown==388);
 CHECK(u->flingy.position.x==500&&u->flingy.position.y==500&&u->order_target.unit==blocked);
 combat_effects::original_weapon_damage=saved;end();
}
inline void shadow_landing_failed_cast_retries_and_restores_state(){
 using namespace shadow_landing_fixture;
 for(bool preexisting_invincibility:{false,true}){
  begin();mode=3;auto u=rework_fixture::unit(61,1,500,500),target=rework_fixture::unit(37,6,600,500);
  u->order=10;multi_fixture::target(u,target);u->flags|=preexisting_invincibility?0x4000000u:0u;
  int queued=0;u->order_queue_begin=u->order_queue_end=&queued;u->highlight_order_count=1;
  const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa75_fixture::record_damage;
  rework_combat_v5::shadow_begin(u,target);auto s=rework_combat_v5::state(u);rework_combat_v5::focus_tick(u,*s);
  CHECK(!s->shadow_active&&s->shadow_count==0&&s->shadow_step==0&&s->shadow_cooldown==108);
  CHECK(qa75_fixture::victims.empty()&&rework_fixture::moves==0&&bool(u->flags&0x4000000u)==preexisting_invincibility);
  CHECK(u->order==10&&u->order_target.unit==target&&u->order_queue_begin==&queued&&u->highlight_order_count==1);
  mode=0;game.frame_count=107;rework_combat_v5::shadow_prepare(u);CHECK(!s->shadow_active);
  game.frame_count=108;rework_combat_v5::shadow_prepare(u);CHECK(s->shadow_active);rework_combat_v5::focus_tick(u,*s);
  CHECK(qa75_fixture::victims.size()==1&&s->shadow_count==1&&s->shadow_cooldown==396);
  mode=3;game.frame_count=112;rework_combat_v5::focus_tick(u,*s);
  CHECK(!s->shadow_active&&s->shadow_count==1&&s->shadow_step==1&&s->shadow_cooldown==396);
  combat_effects::original_weapon_damage=saved;end();
 }
}
inline constexpr std::size_t shadow_landing_group_count=3;
inline void run_shadow_landing_groups(){shadow_landing_uses_clear_far_side_around_wall();shadow_landing_skips_unlandable_target_without_losing_strikes();shadow_landing_failed_cast_retries_and_restores_state();std::printf("SHADOW_LANDING lateral_clearance=1 alternate_target=1 five_actual_strikes=1 zero_hit_retry=8 partial_hit_cooldown=288 state_restored=1\n");}
}
