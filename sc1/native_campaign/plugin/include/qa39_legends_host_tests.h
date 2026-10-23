#pragma once
namespace host_test {
inline constexpr std::size_t qa39_group_count=13;
namespace qa39_fixture {
inline void __cdecl targeted_order(bw::Unit* u,U32 id,U32 x,U32 y,bw::Unit* target,U32){u->order=U8(id);u->order_target={std::int16_t(x),std::int16_t(y),target};}
inline U32 first(const legend_focus::Rule& r){for(U32 id=0;id<228;id++)if(r.units[id/32]&(1u<<(id%32)))return id;return 228;}
inline U32 weapon(U32 id){const auto w=qa38_fixture::weapon(id);return w<130?w:79u;}
inline void __cdecl hp_shield_damage(bw::Unit* u,std::int32_t amount,U8,U32,U8,bw::Unit*,U32){const auto shield=std::min(std::max(0,u->shields),amount);u->shields-=shield;u->flingy.hitpoints=std::max(0,u->flingy.hitpoints-(amount-shield));}
inline void primary(bw::Unit* u,bw::Unit* target,U32 weapon,std::int32_t amount,U32 token){
 g.normal_hit=true;g.bullet_hit_context=true;g.hit_source=u;g.hit_identity={u,u->unit_id,u->player,u->minor_unique_index};g.hit_bonus=0;
 rework_combat_v5::DamageScope::current_primary=target;rework_combat_v5::DamageScope::current_token=token;
 combat_effects::weapon_damage(target,amount,U8(weapon),1,0,u,u->player,hp_shield_damage);
 rework_combat_v5::DamageScope::current_primary=nullptr;g.bullet_hit_context=false;
}
}
inline void qa39_focus_damage_ui_owner_and_primary_boundary(){
 using namespace rework_fixture;
 for(auto r:legend_focus::rules){qa9_fixture::begin({r.ordinal});auto u=unit(qa39_fixture::first(r),1,100,100),target=unit(37,6,120,100),other=unit(37,6,125,100);const auto w=u->unit_id==85?82u:qa39_fixture::weapon(u->unit_id);
  CHECK(rework_combat_v5::infantry_ui_value(u,w,100)==100+r.base);
  CHECK(rework_combat_v5::focus_damage(u,target,w,1000,true)==int(1000*(100+r.base)/100));
  auto hp=other->flingy.hitpoints;g.normal_hit=true;rework_combat_v5::DamageScope::current_primary=target;
  {std::int32_t amount=1000;rework_combat_v5::DamageScope scope(other,u,w,1,amount);if(r.ordinal==197)CHECK(amount==1000);else {if(amount)std::fprintf(stderr,"FOCUS ordinal=%u weapon=%u normal=%d active=%d applied=%d source=%d amount=%d\n",r.ordinal,w,scope.normal,g.active,g.applied,rework_combat_v5::focus_source(u),amount);CHECK(amount==0);}other->flingy.hitpoints-=amount;}
  CHECK(other->flingy.hitpoints==hp-(r.ordinal==197?1000:0));rework_combat_v5::DamageScope::current_primary=nullptr;
  u->player=6;CHECK(rework_combat_v5::focus_damage(u,target,w,1000,true)==1000);qa9_fixture::end();
 }
}
inline void qa88_retired_mine_keeps_native_damage_splash_and_old_wire_identity(){
 using namespace rework_fixture;qa9_fixture::begin({60});
 g.growth.talent_bits[298/32]|=1u<<(298%32);
 CHECK(rework_catalog::rank(g.growth,60)==1&&rework_combat_v5::rank(60)==0);
 CHECK(!legend_focus::converted(60));install();
 auto mine=unit(13,1,100,100),target=unit(37,6,120,100),other=unit(37,6,125,100);
 CHECK(!rework_combat_v5::focus_source(mine)&&rework_combat_v5::focus_base(mine)==0);
 CHECK(rework_combat_v5::infantry_ui_value(mine,6,125)==125);
 CHECK(rework_combat_v5::focus_damage(mine,target,6,1000,true)==1000);
 CHECK(owner_stat(1,{0,19,13})==original_stat({0,19,13}));
 g.normal_hit=true;rework_combat_v5::DamageScope::current_primary=target;
 {std::int32_t amount=1000;rework_combat_v5::DamageScope hit(other,mine,6,1,amount);CHECK(amount==1000);}
 rework_combat_v5::DamageScope::current_primary=nullptr;
 auto flyer=unit(8,6,140,100,true);mine->order=20;mine->order_state=3;mine->order_target={0,0,nullptr};
 pulse(104);CHECK(mine->order_state==3&&!mine->order_target.unit&&multi_fixture::shots.empty());
 CHECK(flyer->flingy.hitpoints==256000&&rework_catalog::rank(g.growth,60)==1);
 qa9_fixture::end();
}
inline void qa39_periodic_hits_use_unamplified_base_and_no_splash(){
 using namespace rework_fixture;const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 for(auto r:legend_focus::rules)if(r.mode==2){qa9_fixture::begin({r.ordinal});auto u=unit(qa39_fixture::first(r),1,100,100),target=unit(37,6,120,100),other=unit(37,6,125,100);const U32 w=qa39_fixture::weapon(u->unit_id);const auto hp=target->flingy.hitpoints;
  for(U32 n=1;n<=r.cadence;n++){game.frame_count=100+n;qa39_fixture::primary(u,target,w,1000,n);}
  CHECK(target->flingy.hitpoints==hp-int(r.cadence*1000*(100+r.base)/100+1000*r.proc/100));CHECK(other->flingy.hitpoints==256000);CHECK(rework_combat_v5::pending_shots.empty());qa9_fixture::end();
 }combat_effects::original_weapon_damage=saved;
}
inline void qa78_carrier_shared_focus_and_auxiliary_damage(){
 using namespace rework_fixture;
 for(U32 parent_id:{72u,82u}){
  qa9_fixture::begin({148});auto parent=unit(parent_id,1,100,100,true),second=unit(parent_id,1,120,100,true);
  auto a=unit(73,1,100,100,true),b=unit(73,1,100,100,true),c=unit(73,1,120,100,true),target=unit(39,6,150,100),other=unit(39,6,160,100);
  std::memcpy(a->unit_specific.bytes,&parent,sizeof(parent));std::memcpy(b->unit_specific.bytes,&parent,sizeof(parent));std::memcpy(c->unit_specific.bytes,&second,sizeof(second));
  const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
  for(U32 n=0;n<16;n++){
   game.frame_count=100+n;auto u=n%2?a:b;const auto before=target->flingy.hitpoints;
   qa39_fixture::primary(u,target,79,1000,100+n);
   CHECK(before-target->flingy.hitpoints==1000+int(std::min(240u,n*20u)*10));
  }
  CHECK(rework_combat_v5::focus_damage(a,target,79,1000,true)==3400);
  CHECK(rework_combat_v5::focus_damage(c,target,79,1000,true)==1000);
  qa39_fixture::primary(b,other,79,1000,200);CHECK(rework_combat_v5::focus_damage(a,target,79,1000,true)==1000);
  CHECK(rework_combat_v5::focus_damage(a,other,79,1000,true)==1200);
  game.frame_count+=73;CHECK(rework_combat_v5::focus_damage(a,other,79,1000,true)==1000);
  ++parent->minor_unique_index;CHECK(rework_combat_v5::focus_damage(a,other,79,1000,true)==1000);
  combat_effects::original_weapon_damage=saved;qa9_fixture::end();
 }
 bool found=false;for(const auto& r:unit_legend_expansion::rules)if(r.ordinal==176){CHECK(r.percent==50&&r.count==1);found=true;}CHECK(found);
 std::puts("QA78_CARRIER shared_parent=1 parents=2 cap=240 target_reset=1 timeout=1 auxiliary_percent=50");
}
inline void qa39_ramps_reset_and_armor_erosion_exceeds_zero(){
 qa78_carrier_shared_focus_and_auxiliary_damage();
 using namespace rework_fixture;qa9_fixture::begin({190});auto u=unit(37,1,100,100),target=unit(39,6,120,100);const U32 armor=original_stat({0,27,39});
 for(U32 n=0;n<100;n++)rework_combat_v5::focus_hit(u,target,256,35);
 auto s=rework_combat_v5::state(target);CHECK(s->erosion==3300);g.normal_hit=true;
 {std::int32_t amount=256;rework_combat_v5::DamageScope scope(target,u,35,1,amount);CHECK(amount==int((34-armor)*256));CHECK(raw_value(0,27,39)==0);}CHECK(raw_value(0,27,39)==armor);
 ranks[19]=1;{std::int32_t amount=256;rework_combat_v5::DamageScope scope(target,u,35,1,amount);CHECK(amount>=int((34-armor)*256));}target->player=2;CHECK(rework_combat_v5::state(target)->erosion==0);qa9_fixture::end();
 qa9_fixture::begin({90});u=unit(38,1,100,100);target=unit(39,6,120,100);auto other=unit(39,6,130,100);
 for(U32 n=0;n<20;n++)rework_combat_v5::focus_hit(u,target,256,38);
 CHECK(rework_combat_v5::focus_damage(u,target,38,1000,true)==2800);CHECK(rework_combat_v5::focus_damage(u,other,38,1000,true)==1000);game.frame_count+=73;CHECK(rework_combat_v5::focus_damage(u,target,38,1000,true)==1000);qa9_fixture::end();
}
inline void qa39_retaliation_needs_attack_and_has_storage_cap(){
 using namespace rework_fixture;qa9_fixture::begin({139});auto archon=unit(68,1,100,100),enemy=unit(37,6,120,100);auto s=rework_combat_v5::state(archon);const auto hp=enemy->flingy.hitpoints;
 rework_combat_v5::focus_received(archon,enemy,1000*256,1000*256);CHECK(s->retaliation==200*256&&enemy->flingy.hitpoints==hp);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 rework_combat_v5::ordinary_hit(archon,enemy,256,70,true);CHECK(s->retaliation==200*256);rework_combat_v5::ordinary_hit(archon,enemy,256,70,false);CHECK(s->retaliation==0&&enemy->flingy.hitpoints==hp-200*256);combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa39_firebat_real_projectiles_form_front_cone_and_stop_recursion(){
 using namespace rework_fixture;qa9_fixture::begin({185});auto u=unit(32,1,100,100),target=unit(37,6,125,100),front=unit(37,6,190,100),edge=unit(37,6,140,169),back=unit(37,6,80,100),side=unit(37,6,120,180),outside=unit(37,6,197,100),ally=unit(37,1,130,100),air=unit(43,6,130,100,true);
 rework_combat_v5::ordinary_hit(u,target,256,25,false);CHECK(multi_fixture::shots.size()==2);for(auto shot:multi_fixture::shots)CHECK(shot.secondary&&(shot.target==front||shot.target==edge));
 CHECK(!rework_combat_v5::flame_cone(u,target,back)&&!rework_combat_v5::flame_cone(u,target,side)&&!rework_combat_v5::flame_cone(u,target,outside)&&!rework_combat_v5::flame_cone(u,target,ally)&&!rework_combat_v5::flame_cone(u,target,air));
 rework_combat_v5::ordinary_hit(u,front,256,25,true);CHECK(multi_fixture::shots.size()==2);
 auto shot=&multi_fixture::bullets[0];{rework_combat_v5::MissileScope scope(shot);g.normal_hit=true;std::int32_t amount=1000;{rework_combat_v5::DamageScope damage(shot->target.unit,u,25,1,amount);CHECK(amount==1000);}}
 qa9_fixture::end();
}
inline void qa39_ensnare_native_duration_final_speed_and_long_cooldown(){
 using namespace rework_fixture;qa9_fixture::begin({82});auto queen=unit(45,1,100,100,true),enemy=unit(37,6,130,100),ally=unit(37,1,140,100);auto shot=bullet(queen,enemy,58);
 {rework_combat_v5::MissileScope scope(shot,area);area(shot);}CHECK(rework_combat_v5::enhanced_ensnare(enemy)&&!rework_combat_v5::enhanced_ensnare(ally));
 CHECK(std::abs(rework_combat_v5::speed_ratio(enemy)*0.5-0.15)<0.00001);
 const U32 w=original_stat({0,17,37}),base=original_stat({1,16,w}),native=std::min(250u,std::max(5u,base+base/4));CHECK(std::abs(rework_combat_v5::cooldown_ratio(enemy,w)*native-double(std::max(5u,base))/0.15)<0.00001);
 U8 timer=200;rework_combat_v5::hold_ensnare_cooldown(enemy,0,timer,400);CHECK(timer==255);game.frame_count=499;rework_combat_v5::hold_ensnare_cooldown(enemy,0,timer);CHECK(timer==1);enemy->ensnare_timer=0;CHECK(rework_combat_v5::speed_ratio(enemy)==1);qa9_fixture::end();
}
inline void qa39_stasis_area_allies_heal_and_visual_scale(){
 using namespace rework_fixture;qa9_fixture::begin({149});rework_combat_v5::get_sprite_position=sprite_get;rework_combat_v5::set_sprite_position=sprite_set;
 auto arbiter=unit(71,1,500,500,true),target=unit(37,6,1000,1000),friend_unit=unit(65,1,1070,1000),outside=unit(65,1,1073,1000);friend_unit->flingy.hitpoints=256;friend_unit->shields=0;friend_unit->energy=0;
 auto shot=bullet(arbiter,target,83);{rework_combat_v5::MissileScope scope(shot,area);area(shot);}CHECK(friend_unit->stasis_timer&&!outside->stasis_timer);friend_unit->stasis_timer=0;pulse(101);CHECK(friend_unit->flingy.hitpoints==int(effective_max_hp(friend_unit))&&friend_unit->shields==int(effective_max_shields(friend_unit)*256)&&friend_unit->energy==0);
 area_visuals::publish(true);CHECK(area_visuals::published->images[364].x==1.5);qa9_fixture::end();
}
inline void qa39_ultralisk_three_cleaves_actual_leech_and_overkill_cap(){
 using namespace rework_fixture;qa9_fixture::begin({92});auto u=unit(39,1,100,100),target=unit(37,6,120,100);u->flingy.hitpoints=256;
 auto a=unit(37,6,125,100),b=unit(37,6,130,100),c=unit(37,6,135,100),d=unit(37,6,140,100);for(auto v:{a,b,c}){v->flingy.hitpoints=100;v->shields=100;}
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 qa39_fixture::primary(u,target,40,1000,1);CHECK(target->flingy.hitpoints==255000);CHECK(a->flingy.hitpoints==0&&b->flingy.hitpoints==0&&c->flingy.hitpoints==0&&d->flingy.hitpoints==256000);CHECK(u->flingy.hitpoints==256+1000+600);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa39_acid_spore_damage_and_slow_are_doubled(){
 using namespace rework_fixture;qa9_fixture::begin({106});auto u=unit(62,1,100,100,true),enemy=unit(43,6,140,100,true);auto shot=bullet(u,enemy,104);
 {rework_combat_v5::MissileScope scope(shot);enemy->acid_spore_count=3;enemy->acid_spore_timers[0]=75;}
 CHECK(rework_combat_v5::state(enemy)->double_acid);const U32 w=original_stat({0,19,43}),base=original_stat({1,16,w}),step=std::max(3u,base/8);CHECK(std::abs(rework_combat_v5::cooldown_ratio(enemy,w)-double(base+6*step)/(base+3*step))<0.00001);
 auto marine=unit(0,1,120,100);g.normal_hit=true;{std::int32_t amount=1000;rework_combat_v5::DamageScope scope(enemy,marine,0,1,amount);CHECK(amount==1000+3*256);}qa9_fixture::end();
}
inline void qa39_scourge_damage_health_survival_and_smart_target(){
 using namespace rework_fixture;qa9_fixture::begin({96});install();CHECK(owner_stat(1,{0,8,47})==original_stat({0,8,47})*2);CHECK(owner_stat(1,{0,17,47})>=130);
 auto u=unit(47,1,100,100,true),other=unit(47,1,101,100,true),a=unit(43,6,160,100,true),b=unit(43,6,180,100,true),enemy=unit(0,6,130,100);a->flingy.hitpoints=10*256;multi_fixture::target(u,a);multi_fixture::target(other,a);
 g.normal_hit=true;{std::int32_t amount=1000;rework_combat_v5::DamageScope scope(u,enemy,0,1,amount);CHECK(amount==250);}game.frame_count=104;auto s=rework_combat_v5::state(u);auto saved_order=g.order;g.order=qa39_fixture::targeted_order;rework_combat_v5::focus_tick(u,*s);CHECK(u->order_target.unit==b);g.order=saved_order;
 auto shot=bullet(u,a,55);CHECK(projectile_identity(shot).unit==u);u->order=0;shot->parent=nullptr;CHECK(projectile_identity(shot).unit==u);
 const auto unique=u->minor_unique_index;u->minor_unique_index++;CHECK(!projectile_identity(shot).unit);u->minor_unique_index=unique;
 u->player=6;CHECK(!projectile_identity(shot).unit);u->player=1;shot->player=6;CHECK(!projectile_identity(shot).unit);shot->player=1;
 shot->weapon_id=0;CHECK(!projectile_identity(shot).unit);shot->weapon_id=55;
 auto edge=unit(43,6,224,100,true),outside=unit(43,6,225,100,true),ally=unit(43,1,170,110,true),stasis=unit(43,6,160,110,true);stasis->stasis_timer=10;
 const auto hp=b->flingy.hitpoints,edge_hp=edge->flingy.hitpoints,out_hp=outside->flingy.hitpoints,ally_hp=ally->flingy.hitpoints,ground_hp=enemy->flingy.hitpoints,stasis_hp=stasis->flingy.hitpoints;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 qa39_fixture::primary(u,a,55,110*256,77);CHECK(a->flingy.hitpoints==0);CHECK(b->flingy.hitpoints==hp-165*128&&edge->flingy.hitpoints==edge_hp-165*128);
 CHECK(outside->flingy.hitpoints==out_hp&&ally->flingy.hitpoints==ally_hp&&enemy->flingy.hitpoints==ground_hp&&stasis->flingy.hitpoints==stasis_hp);
 combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa39_shadow_fury_five_strikes_return_and_restore_invulnerability(){
 using namespace rework_fixture;qa9_fixture::begin({321});relocation();auto u=unit(61,1,100,100),target=unit(37,6,140,100);u->order=10;multi_fixture::target(u,target);const auto flags=u->flags;const auto hp=target->flingy.hitpoints;
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa39_fixture::hp_shield_damage;
 rework_combat_v5::shadow_begin(u,target);auto s=rework_combat_v5::state(u);CHECK(s->shadow_active&&(u->flags&0x4000000u));
 for(U32 n=0;n<5;n++){game.frame_count=100+4*n;rework_combat_v5::focus_tick(u,*s);}CHECK(!s->shadow_active&&(u->flags&0x4000000u)==(flags&0x4000000u)&&u->flingy.position.x==100&&u->flingy.position.y==100&&u->order==10&&u->order_target.unit==target);CHECK(target->flingy.hitpoints<hp);rework_combat_v5::shadow_begin(u,target);CHECK(!s->shadow_active);
 combat_effects::original_weapon_damage=saved;relocation_end();qa9_fixture::end();
}
inline void run_qa39_groups(){qa88_retired_mine_keeps_native_damage_splash_and_old_wire_identity();qa39_focus_damage_ui_owner_and_primary_boundary();qa39_periodic_hits_use_unamplified_base_and_no_splash();qa39_ramps_reset_and_armor_erosion_exceeds_zero();qa39_retaliation_needs_attack_and_has_storage_cap();qa39_firebat_real_projectiles_form_front_cone_and_stop_recursion();qa39_ensnare_native_duration_final_speed_and_long_cooldown();qa39_stasis_area_allies_heal_and_visual_scale();qa39_ultralisk_three_cleaves_actual_leech_and_overkill_cap();qa39_acid_spore_damage_and_slow_are_doubled();qa39_scourge_damage_health_survival_and_smart_target();qa39_shadow_fury_five_strikes_return_and_restore_invulnerability();}
}
