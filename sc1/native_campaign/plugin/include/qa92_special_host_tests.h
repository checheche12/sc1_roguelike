#pragma once
namespace host_test {
namespace qa92_fixture {
inline std::array<U32,32*32> tiles{};
inline U32* __cdecl get_tiles(){return tiles.data();}
inline void __cdecl place(U32 x,U32 y,U32 w,U32 h,U32 round){CHECK(w==1&&h==1&&!round);tiles[y*32+x]|=0x00400000u;}
inline U32 observed_divisor=0,observed_amount=0,observed_calls=0;
inline void __cdecl hallucination(bw::Unit*,U32,U32,bw::Unit*){}
inline void __cdecl damage(bw::Unit*,std::int32_t amount,U8,U32 divisor,U8,bw::Unit*,U32){++observed_calls;observed_amount=U32(amount);observed_divisor=divisor;}
inline void __cdecl hit(bw::Unit* target,bw::Bullet* shot,U32){rework_combat_v5::hallucination_hit_hook(target,shot->weapon_id,0,shot->parent,hallucination);}
}
inline void qa92_creep_drone_exclusion_and_frontier(){
 using namespace rework_fixture;using namespace qa92_fixture;
 qa9_fixture::begin({75});game.map_width_tiles=game.map_height_tiles=32;tiles.fill(0);
 const auto saved_tiles=rework_combat_v5::get_tiles;const auto saved_place=rework_combat_v5::creep_march::place;
 rework_combat_v5::get_tiles=get_tiles;rework_combat_v5::creep_march::place=place;
 auto hatch=unit(131,1,336,336);hatch->flags|=1;
 tiles[10*32+10]=0x00400000u;
 for(U32 id:{37u,38u,39u,41u,43u})for(U32 owner:{1u,6u}){
  auto u=unit(id,owner,336,336,id==43);write_entry(&dat[0][44],id,1);
  const bool expected=owner==1&&id!=41&&id!=43;
  CHECK(rework_combat_v5::creep_march::boosted(u)==expected);
  CHECK(std::abs(rework_combat_v5::speed_ratio(u)-(expected?1.5:1.0))<0.00001);
  CHECK(std::abs(rework_combat_v5::cooldown_ratio(u,35)-(expected?0.8:1.0))<0.00001);
 }
 auto enemy=unit(131,6,720,720);enemy->flags|=1;tiles[22*32+22]=0x00400000u;
 auto ultra=unit(39,1,336,336),drone=unit(41,1,336,336);movement_effects::Image attack_image{};attack_image.script.animation=5;
 static_cast<bw::SpriteScr*>(ultra->flingy.sprite)->main_image=&attack_image;static_cast<bw::SpriteScr*>(drone->flingy.sprite)->main_image=&attack_image;
 auto us=rework_combat_v5::state(ultra),ds=rework_combat_v5::state(drone);U32 attack_frames=0;
 for(U32 n=0;n<5;++n){attack_image.script.pos=std::uint16_t(100+n);attack_image.script.wait=1;rework_combat_v5::creep_attack_animation(ultra,*us);attack_frames+=attack_image.script.wait+1;const auto once=attack_image.script.wait;rework_combat_v5::creep_attack_animation(ultra,*us);CHECK(attack_image.script.wait==once);attack_image.script.wait=1;rework_combat_v5::creep_attack_animation(drone,*ds);CHECK(attack_image.script.wait==1);}
 CHECK(attack_frames==8);
 tiles[9*32+9]=0x00800000u;tiles[9*32+10]=0x20000000u;tiles[9*32+11]=0x08000000u;
 game.frame_count=100;rework_combat_v5::creep_march::reset();rework_combat_v5::creep_march::step();
 game.frame_count=171;rework_combat_v5::creep_march::step();CHECK(rework_combat_v5::creep_march::placed_tiles==0);
 game.frame_count=172;rework_combat_v5::creep_march::step();CHECK(rework_combat_v5::creep_march::expansions==1);
 CHECK(!(tiles[9*32+9]&0x00400000u)&&!(tiles[9*32+10]&0x00400000u)&&!(tiles[9*32+11]&0x00400000u));
 CHECK(tiles[11*32+10]&0x00400000u);CHECK(!(tiles[12*32+10]&0x00400000u));CHECK(!(tiles[23*32+22]&0x00400000u));
 game.frame_count=244;rework_combat_v5::creep_march::step();CHECK(tiles[12*32+10]&0x00400000u);
 ranks[75]=0;const auto placed_count=rework_combat_v5::creep_march::placed_tiles;game.frame_count=316;rework_combat_v5::creep_march::step();CHECK(rework_combat_v5::creep_march::placed_tiles==placed_count);
 rework_combat_v5::get_tiles=saved_tiles;rework_combat_v5::creep_march::place=saved_place;qa9_fixture::end();
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
inline constexpr std::size_t qa92_special_group_count=5;
inline void run_qa92_special_groups(){qa92_suicide_fragments_exact_generation_once();qa92_creep_drone_exclusion_and_frontier();qa92_storm_staggered_lifetime_limit();qa92_shadow_return_ignores_only_self();qa92_hallucination_native_divisors_and_dead_suicide();}
}
