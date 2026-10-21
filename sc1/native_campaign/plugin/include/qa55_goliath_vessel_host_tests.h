#pragma once
namespace host_test {
inline constexpr std::size_t qa55_group_count=3;
inline void qa55_goliath_primary_half_damage_and_three_target_cap(){
 using namespace rework_fixture;
 for(bool air:{false,true})for(U32 id:{3u,17u}){
  qa9_fixture::begin({56});auto body=unit(id,1,100,100),turret=unit(id==3?4:18,1,100,100);body->subunit=turret;turret->subunit=body;
  auto target=unit(air?43:37,6,150,100,air);const U32 w=air?8:7;
  for(U32 i=0;i<4;i++)unit(air?43:37,6,155+int(i)*5,100,air);
  auto original=bullet(turret,target,w);if(air)bullet(turret,target,w);
  CHECK(rework_combat_v5::projectiles.at(original).percent==100);
  CHECK(rework_combat_v5::focus_damage(body,target,w,1000,true)==1000);
  CHECK(rework_combat_v5::pending_shots.size()==3*multi_target::factor(w));
  for(auto shot:rework_combat_v5::pending_shots)CHECK(shot.percent==50&&shot.target.p!=target&&shot.weapon==w);
  pulse(101);CHECK(rework_combat_v5::pending_shots.empty());
  for(U32 i=air?2:1;i<multi_fixture::next_bullet;i++){
   auto b=&multi_fixture::bullets[i];CHECK(rework_combat_v5::projectiles.at(b).secondary);
   rework_combat_v5::MissileScope missile(b);g.normal_hit=true;std::int32_t amount=1000;
   {rework_combat_v5::DamageScope damage(b->target.unit,body,w,1,amount);CHECK(amount==500);}
  }
  qa9_fixture::end();
 }
}
inline void qa55_goliath_visibility_layer_range_owner_and_failure(){
 using namespace rework_fixture;qa9_fixture::begin({56});auto pair=multi_fixture::goliath();auto target=unit(37,6,150,100);
 auto invisible=unit(37,6,151,100);static_cast<bw::SpriteScr*>(invisible->flingy.sprite)->visibility_mask=0;
 unit(37,1,152,100);unit(43,6,153,100,true);auto invincible=unit(37,6,154,100);invincible->flags|=0x4000000u;
 unit(37,6,247,100);auto one=unit(37,6,155,100);bullet(pair.second,target,7);
 CHECK(rework_combat_v5::pending_shots.size()==1&&rework_combat_v5::pending_shots[0].target.p==one);
 ++one->minor_unique_index;pulse(101);CHECK(multi_fixture::shots.size()==1);qa9_fixture::end();
 qa9_fixture::begin({56});pair=multi_fixture::goliath();pair.first->player=pair.second->player=6;target=unit(37,1,150,100);unit(37,1,155,100);bullet(pair.second,target,7);CHECK(rework_combat_v5::pending_shots.empty());qa9_fixture::end();
}
namespace qa55_fixture {
inline U32 calls=0;
inline void __cdecl regenerate(bw::Unit* u){CHECK(u->energy==0);u->energy=200*256;++calls;}
}
inline void qa55_additional_vessels_zero_energy_originals_and_captures(){
 using namespace rework_wave_tests;begin(106);rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=8;
 auto original=add(9,6,1800,1600);original->energy=175*256;const auto untouched=*original;
 for(U32 slot:{0u,26u,38u}){
  auto u=rework_waves::create(9,slot);CHECK(u&&rework_curses::spell_disabled(u)&&u->energy==0);
  auto v=rework_curses::identity(u);CHECK(v&&!rework_waves::spell_due(u,*v));
  u->energy=200*256;rework_waves::release_and_orders();CHECK(u->energy==0);
  owner_unit_hook(u,qa55_fixture::regenerate);CHECK(u->energy==0);
  std::uint16_t error=0;CHECK(!rework_combat_v5::order_target_hook(u,141,original,0,0,&error,targeting_bridge_tests::order_original));
  u->player=U8(player_owner());u->energy=33*256;rework_waves::release_and_orders();CHECK(!rework_curses::spell_disabled(u)&&u->energy==33*256);
  u->flingy.position.x+=600;
 }
 CHECK(std::memcmp(original,&untouched,sizeof(untouched))==0);
}
inline void run_qa55_groups(){qa55_goliath_primary_half_damage_and_three_target_cap();qa55_goliath_visibility_layer_range_owner_and_failure();qa55_additional_vessels_zero_energy_originals_and_captures();}
}
