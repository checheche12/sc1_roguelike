#pragma once
namespace host_test {
inline constexpr std::size_t qa33_group_count=3;
namespace qa33_fixture {
inline void begin(U32 rank){
 rework_wave_tests::begin(106);g.applied=false;GrowthSnapshot snapshot{};snapshot.wire_version=2;
 snapshot.curse_counts[18]=static_cast<U8>(std::min(rank,255u));if(rank>255)snapshot.talent_ranks[29]=rank;
 CHECK(apply_snapshot(nullptr,snapshot));g.current_wave_id=7;
}
inline bw::Unit* wave(U32 id=65){
 auto u=add(id,4,1800,1000);return rework_waves::finish_created(u,0,100,100,1800,1000);
}
inline void __cdecl regen(bw::Unit* u){
 const U32 cap=raw_value(0,7,u->unit_id)*256;
 u->shields=std::int32_t(std::min(cap,U32(std::max(0,u->shields))+7u));
}
inline void __cdecl give(bw::Unit* u,U32 player){u->player=static_cast<U8>(player);}
}
inline void qa33_health_curse_scales_spawned_shields_and_display(){
 for(U32 rank=0;rank<4;++rank)for(U32 id:{65u,66u,70u,72u}){
  qa33_fixture::begin(rank);const U32 base=original_stat({0,7,id}),percent=100+sc1_native::curse_scaling::bonus(rank,20,4);
  auto enemy=qa33_fixture::wave(id);const U32 expected=base*percent/100;
  CHECK(rework_curses::marked(enemy)&&rework_curses::shield_percent(enemy)==percent);
  CHECK(effective_max_shields(enemy)==expected&&enemy->shields==std::int32_t(expected*256));
  CHECK(max_hp_cache::publish(true));U32 hp=0,shields=0;
  CHECK(max_hp_cache::read_display(enemy,hp,shields)&&shields==expected);
  CHECK(samase_status_ui::shield_q8(enemy,id)==expected*256);
  auto normal=add(id,4,2000,1000),friendly=add(id,player_owner(),200,200),neutral=add(id,11,300,200);
  for(auto other:{normal,friendly,neutral})CHECK(effective_max_shields(other)==base);
  CHECK(max_hp_cache::publish(true));
  {OwnerDatScope view(4,4,enemy);CHECK(raw_value(0,7,id)==expected);
   {OwnerDatScope nested(4,4,normal);CHECK(raw_value(0,7,id)==base);}
   CHECK(raw_value(0,7,id)==expected);
   CHECK(max_hp_cache::read_display(normal,hp,shields)&&shields==base);
  }
  CHECK(raw_value(0,7,id)==base);
 }
}
inline void qa33_shield_regen_capture_and_slot_reuse(){
 qa33_fixture::begin(3);auto enemy=qa33_fixture::wave();const U32 base=original_stat({0,7,65}),maximum=effective_max_shields(enemy);
 enemy->shields=std::int32_t(maximum*256-4);owner_unit_hook(enemy,qa33_fixture::regen);
 CHECK(enemy->shields==std::int32_t(maximum*256)&&raw_value(0,7,65)==base);
 enemy->shields=0;owner_unit_hook(enemy,qa33_fixture::regen);CHECK(enemy->shields==7);
 enemy->shields=std::int32_t(maximum*128);owner_give_hook(enemy,player_owner(),qa33_fixture::give);
 CHECK(!rework_curses::marked(enemy)&&effective_max_shields(enemy)==base&&enemy->shields==std::int32_t(base*128));
 CHECK(max_hp_cache::publish(true));U32 hp=0,shields=0;CHECK(max_hp_cache::read_display(enemy,hp,shields)&&shields==base);
 auto recycled=qa33_fixture::wave();CHECK(max_hp_cache::read_display(recycled,hp,shields)&&shields==maximum);
 ++recycled->minor_unique_index;CHECK(!rework_curses::marked(recycled));
 CHECK(max_hp_cache::read_display(recycled,hp,shields)&&shields==base);
 auto illusion=qa33_fixture::wave();illusion->flags|=0x40000000u;
 CHECK(effective_max_shields(illusion)==base);CHECK(max_hp_cache::publish(true));
 CHECK(max_hp_cache::read_display(illusion,hp,shields)&&shields==base);
}
inline void qa33_shield_overflow_disabled_and_roster_isolation(){
 for(U32 rank:{256u,1000u,0xffffffffu}){
  qa33_fixture::begin(rank);auto enemy=qa33_fixture::wave();const U32 base=original_stat({0,7,65});
  const U32 expected=U32(std::min<std::uint64_t>(65535u,std::uint64_t(base)*sc1_native::curse_scaling::scale(100,sc1_native::curse_scaling::bonus(rank,20,4))/100));
  CHECK(effective_max_shields(enemy)==expected&&enemy->shields==std::int32_t(expected*256));
 }
 qa33_fixture::begin(0);g.growth.curse_counts[21]=3;rework_waves::unit_ordinal=0;
 auto elite=add(65,4,1800,1000);rework_waves::finish_created(elite,31,200,100,1800,1000);
 CHECK(rework_curses::hp_percent(elite)==320&&rework_curses::shield_percent(elite)==100);
 CHECK(effective_max_shields(elite)==original_stat({0,7,65}));
 auto marine=qa33_fixture::wave(0);CHECK(effective_max_shields(marine)==0&&marine->shields==0);
 qa33_fixture::begin(3);write_entry(&dat[0][6],65,0);auto disabled=qa33_fixture::wave();
 CHECK(effective_max_shields(disabled)==0&&disabled->shields==0);CHECK(max_hp_cache::publish(true));
 U32 hp=0,shields=1;CHECK(max_hp_cache::read_display(disabled,hp,shields)&&shields==0);
}
inline void run_qa33_groups(){qa33_health_curse_scales_spawned_shields_and_display();qa33_shield_regen_capture_and_slot_reuse();qa33_shield_overflow_disabled_and_roster_isolation();}
}
