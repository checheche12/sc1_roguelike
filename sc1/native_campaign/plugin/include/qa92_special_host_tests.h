#pragma once
namespace host_test {
namespace qa92_fixture {
inline U32 observed_divisor=0,observed_amount=0,observed_calls=0;
inline void __cdecl hallucination(bw::Unit*,U32,U32,bw::Unit*){}
inline void __cdecl damage(bw::Unit*,std::int32_t amount,U8,U32 divisor,U8,bw::Unit*,U32){++observed_calls;observed_amount=U32(amount);observed_divisor=divisor;}
inline void __cdecl hit(bw::Unit* target,bw::Bullet* shot,U32){rework_combat_v5::hallucination_hit_hook(target,shot->weapon_id,0,shot->parent,hallucination);}
}
inline void qa92_storm_staggered_lifetime_limit(){
 using namespace rework_fixture;using namespace rework_combat_v5;
 qa9_fixture::begin({144});auto caster=unit(67,1,100,100),target=unit(37,6,120,100);std::array<bw::Bullet*,14> shots{};
 const auto admitted=[&](bw::Bullet* shot){MissileScope impact(shot);return !target->is_under_storm;};
 for(U32 n=0;n<14;++n){game.frame_count=100+n%3;shots[n]=bullet(caster,target,84);shots[n]->flingy.position={120,100};shots[n]->flingy.sprite=&multi_fixture::sprites[0];shots[n]->state=4;shots[n]->death_timer=63;
  CHECK(admitted(shots[n])==(n<13));
  if(n<13)CHECK(!admitted(shots[n]));
 }
 game.frame_count=107;for(U32 n=0;n<14;++n){shots[n]->death_timer=0;CHECK(admitted(shots[n])==(n<13));}
 shots[0]->state=5;game.frame_count=108;CHECK(admitted(shots[13]));
 target->flingy.position={2000,2000};
 {MissileScope elsewhere(shots[1]);} // The caster remains in range and witnesses the exit.
 target->flingy.position={120,100};CHECK(admitted(shots[13]));CHECK(!admitted(shots[13]));
 ++target->minor_unique_index;CHECK(admitted(shots[13]));
 ++projectiles.at(shots[13]).created;CHECK(admitted(shots[13]));
 rework_combat_v5::reset();CHECK(storm_admissions.empty());qa9_fixture::end();
}
inline void qa92_shadow_return_ignores_only_self(){
 using namespace rework_fixture;qa9_fixture::begin({321});relocation();projectile_audit_fixture::load_dimensions();
 auto u=unit(61,1,518,520);auto s=rework_combat_v5::state(u);s->shadow_active=true;s->shadow_x=500;s->shadow_y=500;s->shadow_invincible=0;u->flags|=0x4000000u;
 rework_relocation::native_place=qa76_fixture::wrong_side_place;qa76_fixture::incoming={490,528};
 rework_combat_v5::shadow_restore(u,*s);CHECK(u->flingy.position.x==500&&u->flingy.position.y==500&&!(u->flags&0x4000000u));
 auto blocker=unit(37,6,500,500);blocker->flingy.sprite=&multi_fixture::sprites[0];u->flingy.position={518,520};s->shadow_active=true;rework_combat_v5::shadow_restore(u,*s);CHECK(u->flingy.position.x==490&&u->flingy.position.y==528);
 relocation_end();qa9_fixture::end();
}
inline void qa92_hallucination_native_divisors_and_dead_suicide(){
 using namespace rework_fixture;using namespace qa92_fixture;
 for(U32 id:{43u,47u,50u,13u}){qa9_fixture::begin({147});auto source=unit(id,1,100,100,id!=50),target=unit(37,6,120,100);source->flags|=0x40000000u;rework_combat_v5::state(source)->materialized=true;
  const U32 weapon=id==43?48u:id==47?55u:id==50?54u:6u;auto shot=bullet(source,target,weapon);const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=damage;
  for(U32 divisor:{1u,2u,3u,4u,9u}){observed_divisor=observed_amount=0;owner_hit_hook(target,shot,divisor,hit);CHECK(observed_divisor==divisor&&observed_amount==original_stat({1,14,weapon})*256&&g.hit_divisor==1);}
  if(id!=43){rework_combat_v5::invalidate(source);source->order=0;source->flingy.hitpoints=0;shot->parent=nullptr;observed_amount=0;owner_hit_hook(target,shot,1,hit);CHECK(observed_amount==original_stat({1,14,weapon})*256);++source->minor_unique_index;observed_amount=0;owner_hit_hook(target,shot,1,hit);CHECK(observed_amount==0);}
  combat_effects::original_weapon_damage=saved;qa9_fixture::end();
 }
}
inline void qa92_suicide_fragments_exact_generation_once(){
 using namespace rework_fixture;using namespace qa92_fixture;using namespace rework_combat_v5;
 for(U32 id:{13u,47u,50u})for(U32 scenario=0;scenario<7;++scenario){
  const U32 ordinal=id==13?170u:id==47?174u:173u,w=id==13?6u:id==47?55u:54u;
  qa9_fixture::begin({ordinal});auto source=unit(id,1,100,100,id==47),target=unit(37,6,120,100,id==47),other=unit(38,6,140,100,id==47);
  source->order=0;source->flingy.hitpoints=0;g.normal_hit=true;g.bullet_hit_context=true;g.hit_identity={source,id,1,source->minor_unique_index};
  if(scenario==1)++source->minor_unique_index;
  if(scenario==2)source->flags|=0x40000000u;
  if(scenario==3)ranks[ordinal]=0;
  const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=damage;observed_calls=observed_amount=0;
  DamageScope::current_primary=scenario>=5?source:target;DamageScope::current_token=1;
  if(scenario==6){auto ally=unit(37,1,120,150,id==47);std::int32_t friendly=100*256;{DamageScope scope(ally,source,w,1,friendly);}CHECK(observed_calls==0);}
  std::int32_t raw=100*256;{DamageScope scope(target,source,w,1,raw);if(scenario==4){target->order=0;target->flingy.hitpoints=0;}}
  const bool expected=id!=50&&(scenario==0||scenario>=4);CHECK(observed_calls==(expected?1u:0u));if(expected)CHECK(observed_amount==50*256);
  raw=100*256;{DamageScope scope(other,source,w,1,raw);}CHECK(observed_calls==(expected?1u:0u));
  combat_effects::original_weapon_damage=saved;g.bullet_hit_context=false;g.hit_identity={};g.normal_hit=false;DamageScope::current_primary=nullptr;qa9_fixture::end();
 }
}
// Time the production impact adapter, including unit snapshots and storm bookkeeping.
// The fixture supplies projectile coordinates and does not simulate native spell damage.
inline void qa92_crowded_storm_pulses(){
 using namespace rework_fixture;
 for(bool player_cast:{true,false}){
  qa9_fixture::begin({144});
  auto caster=unit(67,player_cast?1u:6u,600,600);
  constexpr int nearby=128;
  for(int i=0;i<999;++i)unit(37,6,i<nearby?100+i%12:600+i%20,i<nearby?100+i%9:600+i%30);
  refresh_units();
  std::array<bw::Bullet*,4> storms{};
  for(auto& storm:storms){
   storm=bullet(caster,&units[1],84);storm->flingy.position={100,100};
   storm->flingy.sprite=&multi_fixture::sprites[0];storm->state=4;
  }
  LARGE_INTEGER frequency{};QueryPerformanceFrequency(&frequency);
  std::array<double,7> samples{};
  for(int pulse=0;pulse<=int(samples.size());++pulse){
   game.frame_count+=7;
   const auto scans_before=host_unit_scans;
   LARGE_INTEGER start{},end{};QueryPerformanceCounter(&start);
   for(auto storm:storms){rework_combat_v5::MissileScope impact(storm);}
   QueryPerformanceCounter(&end);
   if(!player_cast)CHECK(host_unit_scans==scans_before);
   if(pulse)samples[pulse-1]=1000.0*double(end.QuadPart-start.QuadPart)/double(frequency.QuadPart);
   for(int i=1;i<=nearby;++i)CHECK(!units[i].is_under_storm);
  }
  // A second hit from the same player storm in this frame must be suppressed
  // on every unit inside the circle. A unit outside retains its native flag.
  for(int i=1;i<=nearby;++i)units[i].is_under_storm=0;
  units[nearby+1].is_under_storm=1;
  {rework_combat_v5::MissileScope impact(storms[0]);}
  for(int i=1;i<=nearby;++i)CHECK(bool(units[i].is_under_storm)==player_cast);
  CHECK(units[nearby+1].is_under_storm==1);
  std::sort(samples.begin(),samples.end());
  std::printf("PERF storm_pulse {\"player_cast\":%s,\"units\":1000,\"nearby\":128,\"storms\":4,\"samples\":7,\"median_ms\":%.4f}\n",
      player_cast?"true":"false",samples[samples.size()/2]);
  qa9_fixture::end();
 }
}
inline void qa92_foreign_energy_spells_clear_only_drained_reserves(){
 using namespace rework_fixture;
 for(U32 weapon_id:{33u,106u}){
  qa9_fixture::begin({});
  auto caster=unit(weapon_id==33?9u:63u,6,100,100);
  auto drained=unit(67,1,110,100),untouched=unit(67,1,400,400);
  drained->energy=untouched->energy=200;
  auto shot=bullet(caster,drained,weapon_id);
  for(auto u:{drained,untouched})rework_combat_v5::state(u)->energy_reserve=1000;
  {rework_combat_v5::MissileScope impact(shot);drained->energy=0;}
  CHECK(rework_combat_v5::state(drained)->energy_reserve==0);
  CHECK(rework_combat_v5::state(untouched)->energy_reserve==1000);
  qa9_fixture::end();
 }
}
inline constexpr std::size_t qa92_special_group_count=6;
inline void run_qa92_special_groups(){qa92_suicide_fragments_exact_generation_once();qa92_storm_staggered_lifetime_limit();qa92_crowded_storm_pulses();qa92_foreign_energy_spells_clear_only_drained_reserves();qa92_shadow_return_ignores_only_self();qa92_hallucination_native_divisors_and_dead_suicide();}
}
