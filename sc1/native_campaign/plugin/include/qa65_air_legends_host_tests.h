#pragma once
namespace host_test {
inline constexpr std::size_t qa65_group_count=13;
namespace qa65_fixture {
inline void __cdecl native_bounce(bw::Bullet* b){
 CHECK(b->bounces_remaining==2);CHECK(rework_combat_v5::DamageScope::current_primary==b->target.unit);
 // The stock dispatcher divides the final two hits by3/9. Its scoped count
 // must avoid that division while the real counter remains available to route.
 const U32 divisor=b->bounces_remaining==0?9:b->bounces_remaining==1?3:1;
 combat_effects::weapon_damage(b->target.unit,70*256/divisor,b->weapon_id,1,0,b->parent,b->player,qa9_fixture::damage);
}
inline void __cdecl native_bounce_63(bw::Bullet* b){
 CHECK(b->bounces_remaining<=2); // The native divisor table has only three entries.
 const U32 divisor=b->bounces_remaining==0?9:b->bounces_remaining==1?3:1;
 combat_effects::weapon_damage(b->target.unit,63*256/divisor,b->weapon_id,1,0,b->parent,b->player,qa9_fixture::damage);
}
inline U32 __cdecl native_weapon(bw::Unit* source,U32 w,bw::Unit* target){
 CHECK(valid_unit(source)&&valid_unit(target));CHECK(reinterpret_cast<std::uintptr_t>(target)>0xffffffffu);
 return w<130&&(raw_value(1,3,w)&((target->flags&4u)?1u:2u));
}
inline U32 __cdecl native_can(bw::Unit* source,bw::Unit* target,U32 detection){
 CHECK(detection==1);if(target->detection_status==0)return 0;
 const U32 field=(target->flags&4u)?19:17,w=raw_value(0,field,source->unit_id);
 return raw_value(0,field+1,source->unit_id)&&rework_combat_v5::weapon_target_hook(source,w,target,native_weapon);
}
inline U32 __cdecl native_order(bw::Unit* source,U32 order,bw::Unit* target,U32,U32,std::uint16_t*){
 CHECK(order==10);return rework_combat_v5::can_attack_hook(source,target,1,native_can);
}
inline void __cdecl native_splash(bw::Bullet* b){
 CHECK((raw_value(1,3,b->weapon_id)&3u)==1u);
 living_units([&](bw::Unit* target){if(target==b->parent||target->player==b->player||!rework_combat_v5::eligible(target))return;
  if(native_weapon(b->parent,b->weapon_id,target)&&rework_combat_v5::dist(target,b->target.unit)<=20u*20u)
   combat_effects::weapon_damage(target,20*256,b->weapon_id,1,0,b->parent,b->player,qa9_fixture::damage);
 });
}
inline void __cdecl victim_owned_splash(bw::Bullet* b){
 living_units([&](bw::Unit* victim){if(victim==b->parent||victim->player==b->player||!rework_combat_v5::eligible(victim))return;
  if(rework_combat_v5::weapon_target_hook(victim,b->weapon_id,victim,native_weapon))
   combat_effects::weapon_damage(victim,20*256,b->weapon_id,1,0,b->parent,b->player,qa9_fixture::damage);
 });
}
inline void __cdecl instant_damage(bw::Bullet* b){combat_effects::weapon_damage(b->target.unit,20*256,b->weapon_id,1,0,b->parent,b->player,qa9_fixture::damage);}
inline bw::Bullet* __cdecl instant_create(U32 w,int x,int y,U32 owner,U32 direction,bw::Unit* source){auto b=multi_fixture::raw(w,x,y,owner,direction,source);if(b)owner_missile_hook(b,instant_damage);return b;}
inline U32 chat_original_calls=0;
inline void __cdecl original_chat(const U8*,U32){++chat_original_calls;}
}
inline void qa65_mutal_single_talents_and_combined_native_damage(){
 using namespace rework_fixture;
 // Actual HP loss for base attack 63: neither talent, extra bounces only,
 // legendary only, then both. All expected values are exact fixed-point hits.
 constexpr U32 hits[4]={3,6,7,10};
 constexpr U32 expected[4][10]={{63,21,7},{63,21,7,7,7,7},
  {54,54,54,18,18,18,18},{54,54,54,18,18,18,18,18,18,18}};
 for(U32 id:{43u,55u})for(U32 mode=0;mode<4;mode++)for(U32 percent:{100u,50u}){
  qa9_fixture::begin({});const bool extra=(mode&1u)!=0,legend=(mode&2u)!=0;
  if(extra)ranks[93]=1;if(legend)ranks[105]=1;
  auto source=unit(id,1,100,100,true);std::array<bw::Unit*,10> targets{};
  for(U32 i=0;i<hits[mode];i++)targets[i]=unit(43,6,140+int(i)*10,100,true);
  rework_combat_v5::emission_percent=percent;rework_combat_v5::emission_secondary=percent==50;
  auto b=bullet(source,targets[0],48);
  rework_combat_v5::emission_percent=100;rework_combat_v5::emission_secondary=false;
  CHECK(rework_combat_v5::projectiles.at(b).legend_bounce==legend);
  if(legend){CHECK(b->bounces_remaining==hits[mode]);CHECK(rework_combat_v5::projectiles.at(b).initial_bounces==hits[mode]);}
  else b->bounces_remaining=3; // The raw fixture does not initialize native routing.
  for(U32 i=0;i<hits[mode];i++){
   b->target.unit=targets[i];b->target.x=targets[i]->flingy.position.x;--b->bounces_remaining;
   const U32 before=b->bounces_remaining;owner_missile_hook(b,qa65_fixture::native_bounce_63);
   CHECK(b->bounces_remaining==before+U32(extra&&!legend&&i==0?3:0));
   CHECK(targets[i]->flingy.hitpoints==256000-int(expected[mode][i]*256*percent/100));
   CHECK(rework_combat_v5::mutal_bounce_numerator==0&&rework_combat_v5::pending_shots.empty());
   CHECK(rework_combat_v5::DamageScope::current_bounce_divisor==1);
  }
  CHECK(!b->bounces_remaining);qa9_fixture::end();
 }
}
inline void qa65_mutal_snapshot_survives_source_loss_and_nested_scopes(){
 using namespace rework_fixture;
 for(bool extra:{false,true}){
  qa9_fixture::begin({105});if(extra)ranks[93]=1;
  auto source=unit(43,1,100,100,true),target=unit(43,6,150,100,true);
  const U8 remaining=U8(extra?6u:3u);
  auto b=bullet(source,target,48);b->bounces_remaining=remaining;ranks[93]=extra?0u:1u;source->flingy.hitpoints=0;source->order=0;
  const auto before=target->flingy.hitpoints;owner_missile_hook(b,qa65_fixture::native_bounce);
  CHECK(target->flingy.hitpoints==before-20*256&&b->bounces_remaining==remaining);
  source->order=2;source->flingy.hitpoints=256000;
  auto other=unit(0,1,100,200),enemy=unit(37,6,150,200);auto ordinary=bullet(other,enemy,0);
  {rework_combat_v5::MissileScope outer(b);CHECK(rework_combat_v5::mutal_bounce_numerator==1);
   {rework_combat_v5::MissileScope inner(ordinary);CHECK(!rework_combat_v5::mutal_bounce_numerator);}
   CHECK(rework_combat_v5::mutal_bounce_numerator==1&&b->bounces_remaining==2);
  }
  CHECK(!rework_combat_v5::mutal_bounce_numerator&&b->bounces_remaining==remaining);qa9_fixture::end();
 }
}
inline void qa65_mutal_without_legend_enemy_and_hallucination_keep_stock(){
 using namespace rework_fixture;
 for(U32 mode=0;mode<3;mode++){
  qa9_fixture::begin(mode?std::initializer_list<U32>{105}:std::initializer_list<U32>{});auto source=unit(43,mode==1?6:1,100,100,true),target=unit(43,6,150,100,true);
  if(mode==2)source->flags|=0x40000000u;
  auto b=bullet(source,target,48);CHECK(!rework_combat_v5::projectiles.at(b).legend_bounce&&b->bounces_remaining!=7);
  {rework_combat_v5::MissileScope scope(b);CHECK(!rework_combat_v5::mutal_bounce_numerator);}qa9_fixture::end();
 }
}
inline void qa65_manual_A_and_right_click_query_all_added_attack_layers(){
 using namespace rework_fixture;
 for(auto spec:{std::array<U32,3>{97,103,1},{59,10,1},{59,32,1},{138,61,1},{138,74,1},{138,75,1},{58,58,0},{106,62,0}}){
  qa9_fixture::begin({spec[0]});install();auto source=unit(spec[1],1,100,100),target=unit(43,6,150,100,spec[2]!=0);
  source->flags|=0x10u;std::uint16_t error=0;const U32 field=spec[2]?19:17;
  const auto original=raw_value(0,field,source->unit_id);
  const auto accepted=rework_combat_v5::order_target_hook(source,10,target,150,100,&error,qa65_fixture::native_order);
  if(!accepted)std::fprintf(stderr,"manual query ordinal%u unit%u ownerweapon%u hitcount%u flags%u\n",spec[0],spec[1],owner_stat(1,{0,field,spec[1]}),owner_stat(1,{0,field+1,spec[1]}),owner_stat(1,{1,3,original_stat({0,field==19?17u:19u,spec[1]})}));CHECK(accepted);
  CHECK(rework_combat_v5::can_attack_hook(source,target,1,qa65_fixture::native_can));
  CHECK(raw_value(0,field,source->unit_id)==original);target->detection_status=0;
  CHECK(!rework_combat_v5::can_attack_hook(source,target,1,qa65_fixture::native_can));target->detection_status=0xff;
  source->player=6;CHECK(!rework_combat_v5::can_attack_hook(source,target,1,qa65_fixture::native_can));source->player=1;
  source->flags|=0x40000000u;CHECK(!rework_combat_v5::can_attack_hook(source,target,1,qa65_fixture::native_can));qa9_fixture::end();
 }
 // A manually targeted Lurker attack may remain in native order9.
 auto source=qa64_fixture::begin();auto target=unit(43,6,200,100,true);source->order=9;multi_fixture::target(source,target);
 pulse(100);CHECK(multi_fixture::shots.size()==1&&multi_fixture::shots[0].target==target);qa64_fixture::end();
}
inline void qa65_manual_launch_without_initialized_bullet_target_preserves_air_splash(){
 using namespace rework_fixture;
 for(U32 id:{10u,32u,103u}){
  qa9_fixture::begin({id==103?97u:59u});install();auto source=unit(id,1,100,100),target=unit(43,6,150,100,true),other=unit(43,6,160,100,true),ground=unit(37,6,150,100);
  multi_fixture::target(source,target);bw::Bullet b{};b.parent=source;b.player=1;b.weapon_id=U8(original_stat({0,17,id}));b.target.x=150;b.target.y=100;
  rework_combat_v5::launched(b.weapon_id,source,&b);const auto& p=rework_combat_v5::projectiles.at(&b);
  CHECK(p.layer==1&&p.primary.p==target);b.target.unit=target;
  const auto flags=raw_value(1,3,b.weapon_id);owner_missile_hook(&b,qa65_fixture::native_splash);
  CHECK(target->flingy.hitpoints==256000-20*256&&other->flingy.hitpoints==256000-20*256&&ground->flingy.hitpoints==256000);
  CHECK(raw_value(1,3,b.weapon_id)==flags);qa9_fixture::end();
 }
}
inline void qa65_guardian_primary_and_six_secondary_hits_include_150_percent_once(){
 // The real splash callback queries each enemy using the enemy as the first
 // argument. A nested owner scope must retain this projectile's attack layer.
 for(auto spec:{std::array<U32,3>{58,58,0},{59,32,1}}){
  using namespace rework_fixture;qa9_fixture::begin({spec[0]});install();auto source=unit(spec[1],1,100,100),target=unit(43,6,150,100,spec[2]!=0),other=unit(37,6,155,100,spec[2]!=0),wrong=unit(43,6,150,100,spec[2]==0),ally=unit(43,1,150,100,spec[2]!=0);
  const U32 w=original_stat({0,spec[2]?17u:19u,spec[1]});auto b=bullet(source,target,w);const auto flags=raw_value(1,3,w);
  owner_missile_hook(b,qa65_fixture::victim_owned_splash);
  CHECK(target->flingy.hitpoints<256000&&other->flingy.hitpoints<256000);CHECK(wrong->flingy.hitpoints==256000&&ally->flingy.hitpoints==256000);
  CHECK(raw_value(1,3,w)==flags&&rework_combat_v5::impact_weapon==130&&rework_combat_v5::impact_owner==12&&rework_combat_v5::impact_layer==2);qa9_fixture::end();
 }
 using namespace rework_fixture;qa9_fixture::begin({191});auto source=unit(44,1,100,100),target=unit(37,6,150,100);
 std::array<bw::Unit*,7> others{};for(U32 i=0;i<7;i++)others[i]=unit(37,6,151+int(i),100);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;
 g.normal_hit=true;g.bullet_hit_context=true;g.hit_source=source;g.hit_identity={source,source->unit_id,source->player,source->minor_unique_index};g.hit_bonus=0;
 const U32 w=original_stat({0,17,44});qa39_fixture::primary(source,target,w,20*256,1);
 CHECK(target->flingy.hitpoints==256000-50*256);U32 n=0;for(auto u:others)if(u->flingy.hitpoints!=256000){CHECK(u->flingy.hitpoints==256000-50*256);++n;}CHECK(n==6);
 CHECK(rework_combat_v5::infantry_ui_value(source,w,100)==250);combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa65_transport_cards_keep_speed_without_capacity_expansion(){
 using namespace rework_fixture;
 for(U32 id:{11u,42u,57u,69u}){
  qa9_fixture::begin({33,74,115});install();auto source=unit(id,1,100,100,true);
  CHECK(rework_cargo_v5::capacity(source)==8);game.upgrade_level_sc[1][24]=1;CHECK(rework_cargo_v5::capacity(source)==8);
  CHECK(std::abs(rework_combat_v5::speed_ratio(source)-1.4)<0.00001);CHECK(owner_stat(1,{0,48,id})==8);
  qa9_fixture::end();
 }
}
inline void qa65_hydra_instant_creation_records_once_before_damage_and_extra_shot(){
 using namespace rework_fixture;qa9_fixture::begin({18,90});auto source=unit(38,1,100,100),target=unit(37,6,150,100);multi_fixture::target(source,target);const U32 w=original_stat({0,17,38});
 auto b=owner_bullet_create_hook(w,150,100,1,0,source,qa65_fixture::instant_create);
 CHECK(b&&target->flingy.hitpoints==256000-20*256);CHECK(rework_combat_v5::projectiles.at(b).impact);
 CHECK(rework_combat_v5::pending_shots.size()==1&&rework_combat_v5::state(source)->shot_count==1);
 pulse(101);CHECK(rework_combat_v5::pending_shots.empty()&&multi_fixture::shots.size()==2);
 CHECK(rework_combat_v5::projectiles.at(&multi_fixture::bullets[1]).percent==50);CHECK(!BulletCreation::current);qa9_fixture::end();
}
inline bw::Bullet* __cdecl qa66_instant_hooked(U32 w,int x,int y,U32 owner,U32 direction,bw::Unit* source){return owner_bullet_create_hook(w,x,y,owner,direction,source,qa65_fixture::instant_create);}
inline void qa66_instant_secondary_native_damage_is_exactly_half(){
 using namespace rework_fixture;qa9_fixture::begin({18});auto source=unit(38,1,100,100),target=unit(37,6,150,100);multi_fixture::target(source,target);const U32 w=original_stat({0,17,38});
 multi_target::create_bullet=qa66_instant_hooked;
 auto b=qa66_instant_hooked(w,150,100,1,0,source);CHECK(b&&target->flingy.hitpoints==256000-20*256);
 pulse(101);CHECK(rework_combat_v5::pending_shots.empty()&&multi_fixture::shots.size()==2);
 CHECK(target->flingy.hitpoints==256000-30*256);CHECK(rework_combat_v5::projectiles.at(&multi_fixture::bullets[1]).secondary);
 qa9_fixture::end();
}
inline void qa66_lurker_instant_air_primary_keeps_per_victim_extra_hit(){
 using namespace rework_fixture;auto source=qa64_fixture::begin();ranks[18]=1;auto target=unit(43,6,200,100,true);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;multi_target::create_bullet=qa66_instant_hooked;
 pulse(100);CHECK(multi_fixture::shots.size()==1&&target->flingy.hitpoints==256000-30*256);
 CHECK(rework_combat_v5::pending_shots.empty()&&source->air_cooldown&&source->ground_cooldown);
 combat_effects::original_weapon_damage=saved;qa64_fixture::end();
}
inline void qa65_lurker_extra_hit_per_pierced_victim_without_duplicate_spines(){
 using namespace rework_fixture;qa9_fixture::begin({18});auto source=unit(103,1,100,100),first=unit(37,6,150,100),second=unit(37,6,160,100);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;
 auto b=bullet(source,first,109);CHECK(rework_combat_v5::pending_shots.empty());
 {rework_combat_v5::MissileScope scope(b);g.normal_hit=true;g.bullet_hit_context=true;g.hit_identity={source,103,1,source->minor_unique_index};
  combat_effects::weapon_damage(first,20*256,109,1,0,source,1,qa9_fixture::damage);combat_effects::weapon_damage(second,20*256,109,1,0,source,1,qa9_fixture::damage);
 }
 CHECK(first->flingy.hitpoints==256000-30*256&&second->flingy.hitpoints==256000-30*256);CHECK(rework_combat_v5::pending_shots.empty());
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa65_lab_all_talent_rank_encodings_and_command_boundary(){
 using namespace rework_fixture;qa9_fixture::begin({});effect_lab::enabled=true;
 for(U32 i=0;i<std::size(effect_lab_data::talents);i++){
  GrowthSnapshot s{};s.wire_version=2;const auto maximum=effect_lab_data::talents[i].maximum;
  CHECK(effect_lab::set_talent(s,i,maximum));CHECK(rework_catalog::valid_packed(s));CHECK(effect_lab::set_talent(s,i,0));
  for(auto w:s.talent_bits)CHECK(!w);for(auto w:s.talent_ranks)CHECK(!w);CHECK(!effect_lab::set_talent(s,i,maximum+1));
 }
 effect_lab::enabled=false;CHECK(!effect_lab::command("-t 343 1"));std::array<U8,82> data{};data[0]=0x5c;std::memcpy(data.data()+2,"-t 343 1",8);
 qa65_fixture::chat_original_calls=0;effect_lab::chat(data.data(),82,0,0,qa65_fixture::original_chat);CHECK(qa65_fixture::chat_original_calls==1);qa9_fixture::end();
}
inline void qa65_lab_custom_map_activation_and_repeatable_effect_updates(){
 reset();make_chk(&effect_lab::mission,2);game.campaign_mission=0;game.map_width_tiles=game.map_height_tiles=256;
 CHECK(effect_lab::matches(chk.data(),chk.size()));init_units(original);CHECK(effect_lab::enabled&&g.active&&g.applied&&g.mission==&effect_lab::mission);
 CHECK(effect_lab::command("-t 343 1"));CHECK(rework_catalog::rank(g.growth,105)==1);
 CHECK(effect_lab::command("-t 560 2"));CHECK(rework_catalog::rank(g.growth,322)==2);
 CHECK(effect_lab::command("-c 49 1"));CHECK(g.growth.curse_counts[49]==1);
 CHECK(effect_lab::command("-clear"));CHECK(rework_catalog::rank(g.growth,105)==0&&g.growth.curse_counts[49]==0);
 abandon_session();CHECK(!effect_lab::enabled&&!g.active);
}
inline void run_qa65_groups(){qa66_instant_secondary_native_damage_is_exactly_half();qa66_lurker_instant_air_primary_keeps_per_victim_extra_hit();qa65_mutal_single_talents_and_combined_native_damage();qa65_mutal_snapshot_survives_source_loss_and_nested_scopes();qa65_mutal_without_legend_enemy_and_hallucination_keep_stock();qa65_manual_A_and_right_click_query_all_added_attack_layers();qa65_manual_launch_without_initialized_bullet_target_preserves_air_splash();qa65_guardian_primary_and_six_secondary_hits_include_150_percent_once();qa65_transport_cards_keep_speed_without_capacity_expansion();qa65_hydra_instant_creation_records_once_before_damage_and_extra_shot();qa65_lurker_extra_hit_per_pierced_victim_without_duplicate_spines();qa65_lab_all_talent_rank_encodings_and_command_boundary();qa65_lab_custom_map_activation_and_repeatable_effect_updates();}
}
