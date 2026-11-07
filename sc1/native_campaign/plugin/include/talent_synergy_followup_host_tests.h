#pragma once
namespace host_test {
inline constexpr std::size_t talent_synergy_followup_group_count=13;
inline void synergy2_warmup_combines_and_resets(){
 using namespace rework_fixture;qa9_fixture::begin({16,162});auto u=unit(0,1,100,100);auto s=rework_combat_v5::state(u);
 s->last_launch=100;s->streak=3;CHECK(std::abs(rework_combat_v5::cooldown_ratio(u,0)-0.175)<0.000001);
 ranks[162]=0;CHECK(std::abs(rework_combat_v5::cooldown_ratio(u,0)-0.25)<0.000001);
 ranks[16]=0;ranks[162]=1;CHECK(std::abs(rework_combat_v5::cooldown_ratio(u,0)-0.7)<0.000001);
 ranks[16]=1;game.frame_count=173;CHECK(rework_combat_v5::cooldown_ratio(u,0)==1);qa9_fixture::end();
}
inline void synergy2_ensnare_area_and_strong_slow(){
 using namespace rework_fixture;
 for(bool extended:{false,true}){
  qa9_fixture::begin({82});if(extended)ranks[80]=1;
  auto queen=unit(45,1,500,500,true),target=unit(37,6,1000,1000),edge=unit(37,6,1127,1000),outside=unit(37,6,1129,1000);
  rework_combat_v5::get_sprite_position=sprite_get;rework_combat_v5::set_sprite_position=sprite_set;
  auto shot=bullet(queen,target,58);{rework_combat_v5::MissileScope hit(shot,area);area(shot);}
  CHECK(bool(edge->ensnare_timer)==extended&&!outside->ensnare_timer);
  CHECK(target->ensnare_timer==(extended?150:75));CHECK(rework_combat_v5::enhanced_ensnare(target));
  area_visuals::publish(true);CHECK(area_visuals::published->images[383].x==(extended?2.0:1.0));qa9_fixture::end();
 }
}
inline void synergy2_free_yamato_is_a_triple_cast_once(){
 using namespace rework_fixture;
 for(bool triple:{false,true}){
  qa9_fixture::begin({65});if(triple)ranks[64]=1;
  auto source=unit(12,1,100,100),target=unit(37,6,150,100);target->flingy.hitpoints=10000*256;source->energy=200*256;
  for(U32 i=0;i<4;++i){game.frame_count=100+i*2;bullet(source,target,19);}
  CHECK(rework_combat_v5::pending_shots.empty()&&multi_fixture::shot_count(19)==4&&multi_fixture::shot_count(30)==1);
  CHECK(multi_fixture::shots.back().frame==106&&multi_fixture::shots.back().weapon==30);
  const auto attacks=rework_combat_v5::state(source)->shot_count;const auto energy=source->energy;
  rework_combat_v5::state(source)->next_ground=rework_combat_v5::state(source)->next_air=1000;
  pulse(108);bw::Bullet* root=nullptr;
  for(auto& pair:rework_combat_v5::projectiles)if(pair.second.weapon==30){CHECK(!root);root=pair.first;CHECK(pair.second.secondary&&pair.second.spell_root&&pair.second.percent==(triple?200u:100u));}
  CHECK(root);CHECK(rework_combat_v5::state(source)->shot_count==attacks);yamato_targets.clear();
  {rework_combat_v5::MissileScope hit(root,qa26_yamato_dispatch);qa26_yamato_dispatch(root);}
  CHECK(yamato_targets.size()==(triple?3u:1u));CHECK(target->flingy.hitpoints==10000*256-(triple?1560:260)*256);
  CHECK(rework_combat_v5::pending_shots.empty()&&source->energy==energy);
  {rework_combat_v5::MissileScope repeated(root,qa26_yamato_dispatch);}
  CHECK(yamato_targets.size()==(triple?3u:1u));qa9_fixture::end();
 }
}
inline void synergy2_spread_spores_keep_amplification_and_duration(){
 using namespace rework_fixture;qa9_fixture::begin({86,100,106});auto source=unit(62,1,100,100,true),target=unit(43,6,150,100,true),spread=unit(43,6,180,100,true),ally=unit(43,1,180,110,true);
 auto shot=bullet(source,target,104);
 {rework_combat_v5::MissileScope hit(shot);target->acid_spore_count=1;target->acid_spore_timers[0]=150;}
 CHECK(target->acid_spore_count==1&&spread->acid_spore_count==1&&!ally->acid_spore_count);
 CHECK(rework_combat_v5::state(target)->double_acid&&rework_combat_v5::state(spread)->double_acid);
 CHECK(spread->acid_spore_timers[0]==255);qa9_fixture::end();
}
inline void synergy2_distinct_slows_expire_independently(){
 using namespace rework_fixture;qa9_fixture::begin({94,135,143,149});auto target=unit(37,6,100,100);
 rework_combat_v5::mark_slow(target,25,120,143);rework_combat_v5::mark_slow(target,50,48,94);
 CHECK(std::abs(rework_combat_v5::speed_ratio(target)-0.125)<0.000001);
 rework_combat_v5::mark_slow(target,50,48,94);CHECK(std::abs(rework_combat_v5::speed_ratio(target)-0.125)<0.000001);
 game.frame_count=148;CHECK(rework_combat_v5::speed_ratio(target)==0.25);
 game.frame_count=220;CHECK(rework_combat_v5::speed_ratio(target)==1);
 rework_combat_v5::mark_slow(target,50,10,149);++target->minor_unique_index;CHECK(rework_combat_v5::speed_ratio(target)==1);qa9_fixture::end();
}
inline void synergy2_added_air_range_retains_shared_and_bunker_bonuses(){
 using namespace rework_fixture;
 for(U32 id:{32u,10u,61u,74u,75u}){
  qa9_fixture::begin({10,34,59,138});auto source=unit(id,1,100,100),target=unit(43,6,260,100,true);source->order_target.unit=target;
  CHECK(rework_combat_v5::attack_range(source,32)==216);CHECK(rework_combat_v5::acquisition_range(source,3)==7);
  source->flags|=0x20u;CHECK(rework_combat_v5::attack_range(source,32)==280);CHECK(rework_combat_v5::acquisition_range(source,3)==9);
  source->player=6;CHECK(rework_combat_v5::attack_range(source,32)==32);qa9_fixture::end();
 }
}
inline void synergy2_fast_supply_retains_building_speed(){
 using namespace rework_fixture;qa9_fixture::begin({4,20,22});
 auto snapshot=economy_snapshot({4,20,22});std::vector<Edit> edits;CHECK(rework_economy_v5::plan_stats(snapshot,edits));
 for(U32 id:{109u,156u})CHECK(effect_value(edits,{0,42,id},original_stat({0,42,id}))==36);
 CHECK(effect_value(edits,{0,42,42},original_stat({0,42,42}))==72);qa9_fixture::end();
}
namespace synergy2_fixture {
inline U32 armor=~0u,shield_upgrade=~0u;inline std::int32_t damage=0;
inline void __cdecl split(bw::Unit* target,std::int32_t amount,U8 weapon,U32 divisor,U8 direction,bw::Unit* source,U32 owner){
 armor=raw_value(0,27,target->unit_id);shield_upgrade=rework_combat_v5::upgrade_level(target->player,15);damage=amount;
 combat_audit::native_split(target,amount,weapon,divisor,direction,source,owner);
}
}
inline void synergy2_generated_hits_share_shield_ignore_acid_and_restore(){
 using namespace rework_fixture;qa9_fixture::begin({19,106});auto source=unit(0,1,100,100),target=unit(66,6,130,100);
 auto level=rework_upgrade_storage::slot(6,15);CHECK(level);*level=3;target->shields=100*256;
 target->acid_spore_count=3;rework_combat_v5::state(target)->double_acid=true;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=synergy2_fixture::split;combat_audit::armor=0;
 rework_combat_v5::DamageScope::current_percent=200;rework_combat_v5::DamageScope::current_primary=source;
 rework_combat_v5::weapon_hurt(target,1000,0,source,1);
 CHECK(synergy2_fixture::armor==0&&synergy2_fixture::shield_upgrade==0&&synergy2_fixture::damage==1000+3*256);
 CHECK(*level==3&&rework_combat_v5::generated_depth==0&&rework_combat_v5::DamageScope::current==nullptr);
 rework_combat_v5::weapon_hurt(target,1000,55,nullptr,1);
 CHECK(synergy2_fixture::shield_upgrade==0&&*level==3);
 CHECK(rework_combat_v5::DamageScope::current_percent==200&&rework_combat_v5::pending_shots.empty());
 rework_combat_v5::DamageScope::current_percent=100;rework_combat_v5::DamageScope::current_primary=nullptr;
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy2_generated_erosion_uses_ghost_normal_type_and_no_reproc(){
 using namespace rework_fixture;qa9_fixture::begin({49,190});install();auto source=unit(1,1,100,100),target=unit(39,6,130,100);
 auto status=rework_combat_v5::state(target);status->erosion=33;status->erosion_owner=1;
 auto level=rework_upgrade_storage::slot(6,original_stat({0,25,39}));CHECK(level);*level=1;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=synergy2_fixture::split;combat_audit::armor=0;
 const auto hp=target->flingy.hitpoints;rework_combat_v5::weapon_hurt(target,1000,2,source,1);
 CHECK(target->flingy.hitpoints==hp-1000+172);CHECK(status->erosion==33);
 CHECK(rework_combat_v5::state(source)->focus_hits==0&&rework_combat_v5::pending_shots.empty());
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy2_generated_defense_and_lifesteal_follow_actual_loss(){
 using namespace rework_fixture;qa9_fixture::begin({150,92});auto source=unit(37,6,100,100),target=unit(65,1,130,100);
 rework_combat_v5::state(target)->protection=200;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=synergy2_fixture::split;combat_audit::armor=0;
 const auto hp=target->flingy.hitpoints;rework_combat_v5::weapon_hurt(target,1000,35,source,6);
 CHECK(target->flingy.hitpoints==hp-650);
 auto ultra=unit(39,1,160,100),victim=unit(37,6,180,100);ultra->flingy.hitpoints=256;victim->flingy.hitpoints=100;victim->shields=100;
 rework_combat_v5::weapon_hurt(victim,1000,40,ultra,1);CHECK(ultra->flingy.hitpoints==456);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy2_storm_multipliers_and_generated_matrix_reserve(){
 using namespace rework_fixture;qa9_fixture::begin({121,144});auto caster=unit(67,1,100,100),target=unit(37,6,130,100);
 auto shot=bullet(caster,target,84);CHECK(rework_combat_v5::projectiles.at(shot).percent==300);
 {rework_combat_v5::MissileScope missile(shot);g.normal_hit=false;std::int32_t amount=8*256;rework_combat_v5::DamageScope hit(target,caster,84,1,amount);CHECK(amount==24*256);}
 qa9_fixture::end();qa9_fixture::begin({42});auto source=unit(37,6,100,100);target=unit(0,1,130,100);
 target->defensive_matrix_dmg=1000;target->matrix_timer=100;rework_combat_v5::matrix_state(target)->reserve=2000;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=synergy2_fixture::split;combat_audit::armor=0;
 const auto hp=target->flingy.hitpoints;rework_combat_v5::weapon_hurt(target,1000,35,source,6);
 CHECK(rework_combat_v5::matrix_state(target)->reserve==1000&&target->defensive_matrix_dmg==1000&&target->flingy.hitpoints==hp);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void synergy2_unit_damage_pair_sweep_keeps_both_bonuses(){
 using namespace rework_fixture;using namespace rework_combat_v5;U32 pairs=0,covered_units=0,misses=0;
 for(U32 id=0;id<106;++id){
  qa9_fixture::begin({});auto source=unit(id,1,100,100);const auto w=qa38_fixture::weapon(id);
  if(w>=130||!ordinary_weapon(w)){qa9_fixture::end();continue;}
  std::vector<U32> candidates;
  for(const auto& r:unit_growth::rules)if((r.kind==1||(r.kind==2&&r.damage))&&unit_growth_matches(r,id,true)&&!unit_cleanup_retired(r.ordinal))candidates.push_back(r.ordinal);
  for(const auto& r:legend_focus::rules)if(r.base&&focus_match(r,source))candidates.push_back(r.ordinal);
  for(const auto& r:unit_legend_expansion::rules)if((r.mode==1||r.mode==11)&&r.bonus&&expansion_matches(r,id)&&!legend_focus::converted(r.ordinal)&&!unit_cleanup_retired(r.ordinal))candidates.push_back(r.ordinal);
  std::sort(candidates.begin(),candidates.end());candidates.erase(std::unique(candidates.begin(),candidates.end()),candidates.end());
  qa9_fixture::end();
  const auto value=[&](U32 first,U32 second){qa9_fixture::begin({});auto actor=unit(id,1,100,100);
   if(first<ranks.size())ranks[first]=1;if(second<ranks.size())ranks[second]=1;install();
   const auto v=weapon_ui_damage_q8(actor,w,std::int32_t(owner_stat(1,{1,14,w})*256));qa9_fixture::end();return v;};
  const auto base=value(~0u,~0u);std::vector<std::pair<U32,std::int32_t>> benefits;
  for(auto ordinal:candidates){const auto v=value(ordinal,~0u);if(v>base)benefits.emplace_back(ordinal,v);}
  if(benefits.size()>1)++covered_units;
  for(std::size_t a=0;a<benefits.size();++a)for(std::size_t b=a+1;b<benefits.size();++b){
   const auto v=value(benefits[a].first,benefits[b].first);
   if(!(v>benefits[a].second&&v>benefits[b].second)){++misses;std::printf("SYNERGY_MISS unit=%u weapon=%u a=%u b=%u base=%d first=%d second=%d combined=%d\n",id,w,benefits[a].first,benefits[b].first,base,benefits[a].second,benefits[b].second,v);}
   ++pairs;
  }
  qa9_fixture::end();
 }
 CHECK(!misses);CHECK(pairs>50&&covered_units>20);std::printf("SYNERGY_DAMAGE_PAIRS units=%u pairs=%u both_bonuses_retained=1\n",covered_units,pairs);
}
inline void synergy2_lockdown_duration_does_not_clip_the_second_talent(){
 using namespace rework_fixture;qa9_fixture::begin({45,63});auto source=unit(1,1,100,100),target=unit(37,6,130,100);
 auto shot=bullet(source,target,32);{rework_combat_v5::MissileScope hit(shot);target->lockdown_timer=131;}
 CHECK(target->lockdown_timer==255&&rework_combat_v5::state(target)->lockdown_reserve==269);
 for(U32 ticks=1;ticks<=524;++ticks){CHECK(target->lockdown_timer);--target->lockdown_timer;pulse(100+ticks*8);CHECK(bool(target->lockdown_timer)==(ticks<524));}
 CHECK(!rework_combat_v5::state(target)->lockdown_reserve);
 shot=bullet(source,target,32);{rework_combat_v5::MissileScope hit(shot);target->lockdown_timer=131;}
 target->lockdown_timer=0;pulse(5000);CHECK(!rework_combat_v5::state(target)->lockdown_reserve);qa9_fixture::end();
}
inline void run_talent_synergy_followup_groups(){
 synergy2_warmup_combines_and_resets();synergy2_ensnare_area_and_strong_slow();synergy2_free_yamato_is_a_triple_cast_once();
 synergy2_spread_spores_keep_amplification_and_duration();synergy2_distinct_slows_expire_independently();synergy2_added_air_range_retains_shared_and_bunker_bonuses();
 synergy2_fast_supply_retains_building_speed();synergy2_generated_hits_share_shield_ignore_acid_and_restore();synergy2_generated_erosion_uses_ghost_normal_type_and_no_reproc();synergy2_generated_defense_and_lifesteal_follow_actual_loss();
 synergy2_storm_multipliers_and_generated_matrix_reserve();synergy2_unit_damage_pair_sweep_keeps_both_bonuses();
 synergy2_lockdown_duration_does_not_clip_the_second_talent();
}
}
