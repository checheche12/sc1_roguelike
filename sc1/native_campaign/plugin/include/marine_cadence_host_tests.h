#pragma once
namespace host_test {
inline constexpr std::size_t marine_cadence_group_count=3;
inline void marine_cadence_recoil_and_order_follow_actual_cooldown(){
 using namespace rework_fixture;qa9_fixture::begin({16,162});
 auto u=unit(0,1,100,100),target=unit(7,6,150,100);auto s=rework_combat_v5::state(u);
 bw::SpriteScr sprite{};movement_effects::Image image{};sprite.main_image=&image;image.parent=&sprite;u->flingy.sprite=&sprite;
 image.script={28872,29207,0,5,1};u->order=10;u->order_wait=8;u->order_target.unit=target;u->ground_cooldown=3;
 s->streak=3;s->last_launch=100;s->weapon=0;s->target=rework_combat_v5::identity(target);
 rework_combat_v5::accelerate_marine_recovery(u,*s);
 CHECK(image.script.pos==29227&&image.script.wait==0&&u->order_wait==3);
 CHECK(u->ground_cooldown==3&&s->shot_count==0&&rework_combat_v5::pending_shots.empty());
 image.script.pos=29229;u->ground_cooldown=0;u->order_wait=8;
 rework_combat_v5::accelerate_marine_recovery(u,*s);CHECK(u->order_wait==0);
 qa9_fixture::end();
}
inline void marine_cadence_preserves_native_and_unrelated_states(){
 using namespace rework_fixture;
 for(U32 variant=0;variant<11;++variant){
  qa9_fixture::begin({16});auto u=unit(0,1,100,100),target=unit(7,6,150,100);auto s=rework_combat_v5::state(u);
  bw::SpriteScr sprite{};movement_effects::Image image{};sprite.main_image=&image;image.parent=&sprite;u->flingy.sprite=&sprite;
  image.script={28872,29207,0,5,1};u->order=10;u->order_wait=8;u->order_target.unit=target;u->ground_cooldown=3;
  s->streak=3;s->last_launch=100;s->weapon=0;s->target=rework_combat_v5::identity(target);
  switch(variant){
   case 0:ranks[16]=0;break;
   case 1:u->player=6;break;
   case 2:u->unit_id=1;break;
   case 3:u->order=6;break;
   case 4:u->stasis_timer=10;break;
   case 5:image.script.pos=29189;break; // Pre-fire wait must not be skipped.
   case 6:image.script.animation=1;break; // Death/other animation.
   case 7:image.script.header=0;break;
   case 8:u->order_target.unit=nullptr;break;
   case 9:game.frame_count=173;break;
   case 10:s->streak=1;u->ground_cooldown=11;break; // Native recoil already fits.
  }
  const auto before=image.script;const auto cd=u->ground_cooldown;
  rework_combat_v5::accelerate_marine_recovery(u,*s);
  CHECK(image.script.pos==before.pos&&image.script.wait==before.wait&&u->order_wait==8&&u->ground_cooldown==cd);
  qa9_fixture::end();
 }
}
inline void marine_cadence_hero_and_air_layer(){
 using namespace rework_fixture;
 for(U32 id:{0u,20u}){
  qa9_fixture::begin({16,162});auto u=unit(id,1,100,100),target=unit(11,6,150,100,true);auto s=rework_combat_v5::state(u);
  bw::SpriteScr sprite{};movement_effects::Image image{};sprite.main_image=&image;image.parent=&sprite;u->flingy.sprite=&sprite;
  image.script={28872,29202,0,6,0};u->order=10;u->order_wait=8;u->order_target.unit=target;u->ground_cooldown=0;u->air_cooldown=2;
  s->streak=3;s->last_launch=100;s->weapon=id==0?0u:1u;s->target=rework_combat_v5::identity(target);
  rework_combat_v5::accelerate_marine_recovery(u,*s);
  CHECK(image.script.pos==29227&&u->order_wait==2&&u->air_cooldown==2);
  qa9_fixture::end();
 }
}
inline void run_marine_cadence_groups(){marine_cadence_recoil_and_order_follow_actual_cooldown();marine_cadence_preserves_native_and_unrelated_states();marine_cadence_hero_and_air_layer();}
}
