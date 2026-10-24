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
 for(U32 n=0;n<14;++n){game.frame_count=100+n%3;shots[n]=bullet(caster,target,84);shots[n]->flingy.position={120,100};shots[n]->flingy.sprite=&multi_fixture::sprites[0];shots[n]->state=4;shots[n]->death_timer=63;
  CHECK(admit_storm(target,shots[n],projectiles.at(shots[n]))==(n<13));
  if(n<13)CHECK(!admit_storm(target,shots[n],projectiles.at(shots[n])));
 }
 game.frame_count=107;for(U32 n=0;n<14;++n){shots[n]->death_timer=0;CHECK(admit_storm(target,shots[n],projectiles.at(shots[n]))==(n<13));}
 shots[0]->state=5;game.frame_count=108;CHECK(admit_storm(target,shots[13],projectiles.at(shots[13])));
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
  const bool expected=scenario==0||scenario>=4;CHECK(observed_calls==(expected?1u:0u));if(expected)CHECK(observed_amount==50*256);
  raw=100*256;{DamageScope scope(other,source,w,1,raw);}CHECK(observed_calls==(expected?1u:0u));
  combat_effects::original_weapon_damage=saved;g.bullet_hit_context=false;g.hit_identity={};g.normal_hit=false;DamageScope::current_primary=nullptr;qa9_fixture::end();
 }
}
inline constexpr std::size_t qa92_special_group_count=4;
inline void run_qa92_special_groups(){qa92_suicide_fragments_exact_generation_once();qa92_storm_staggered_lifetime_limit();qa92_shadow_return_ignores_only_self();qa92_hallucination_native_divisors_and_dead_suicide();}
}
