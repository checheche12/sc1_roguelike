#pragma once
// Included inside rework_combat_v5 after weapon_hurt and before ordinary_hit.
inline bool focus_match(const legend_focus::Rule& r,const bw::Unit* u) noexcept {return valid_unit(u)&&u->unit_id<256&&(r.units[u->unit_id/32]&(1u<<(u->unit_id%32)));}
inline bool flame_cone(bw::Unit* u,bw::Unit* target,bw::Unit* other) noexcept {
 if(!eligible(other)||air(other)||!is_enemy(other->player)||other==target||dist(u,other)>96u*96u)return false;
 const auto dx=std::int64_t(target->flingy.position.x)-u->flingy.position.x,dy=std::int64_t(target->flingy.position.y)-u->flingy.position.y;
 const auto ox=std::int64_t(other->flingy.position.x)-u->flingy.position.x,oy=std::int64_t(other->flingy.position.y)-u->flingy.position.y;
 const auto dot=dx*ox+dy*oy,cross=dx*oy-dy*ox;return dot>0&&cross*cross<=3*dot*dot;
}
inline U32 focus_base(const bw::Unit* u) noexcept {
 U32 result=0;if(!talent_power::enabled||!valid_unit(u)||u->player!=player_owner()||hallucination(u))return 0;
 for(auto r:legend_focus::rules)if(raw_rank(r.ordinal)&&focus_match(r,u))result+=r.base;
 return result;
}
inline bool focus_source(bw::Unit* u) noexcept {
 if(!talent_power::enabled||!valid_unit(u)||u->player!=player_owner()||hallucination(u))return false;
 for(auto r:legend_focus::rules)if(raw_rank(r.ordinal)&&focus_match(r,u))return true;return false;
}
inline std::int32_t focus_damage(bw::Unit* u,bw::Unit* target,U32 weapon,std::int32_t amount,bool primary) {
 if(!focus_source(u)||!ordinary_weapon(weapon)||amount<=0||!primary)return amount;
 auto s=state(u);U32 bonus=0;
 for(auto r:legend_focus::rules)if(raw_rank(r.ordinal)&&focus_match(r,u)){
  bonus+=r.base;
  if(r.mode==1&&live(target)&&std::uint64_t(std::max(0,target->flingy.hitpoints))*100<=std::uint64_t(effective_max_hp(target))*r.limit)bonus+=r.proc;
  if(r.mode==3&&s&&generation(s->focus_target)==target&&now()-s->focus_last<=72)bonus+=std::min(r.limit,s->focus_hits*r.step);
  if(r.mode==7&&u->order==6)bonus+=r.proc;
  if(r.mode==8&&valid_unit(target)&&(original_stat({0,26,target->unit_id})==3||building(target)))bonus+=r.proc;
 }
 return std::int32_t(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(amount)*(100ull+bonus)/100));
}
inline void focus_hit(bw::Unit* u,bw::Unit* target,U32 amount,U32 weapon) {
 if(!focus_source(u)||!eligible(target)||!is_enemy(target->player))return;auto s=state(u),t=state(target);if(!s||!t)return;
 const bool same=generation(s->focus_target)==target&&now()-s->focus_last<=72;
 s->focus_hits=same?std::min(0xfffffffeu,s->focus_hits)+1:1;s->focus_last=now();s->focus_target=identity(target);
 for(auto r:legend_focus::rules)if(raw_rank(r.ordinal)&&focus_match(r,u)){
  if(r.mode==2&&s->focus_hits%r.cadence==0)weapon_hurt(target,U32(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(amount)*r.proc/100)),weapon,u,u->player);
  if(r.mode==5&&s->retaliation){const U32 stored=s->retaliation;s->retaliation=0;weapon_hurt(target,stored,weapon,u,u->player);}
  if(r.mode==6){if(t->erosion_owner!=u->player){t->erosion=0;t->erosion_owner=u->player;}if(t->erosion<0xfffffffeu)++t->erosion;}
 }
}
inline void focus_received(bw::Unit* u,bw::Unit* attacker,U32 hp_loss,U32 shield_loss) {
 if(!focus_source(u)||!is_enemy(attacker?attacker->player:12))return;auto s=state(u);if(!s)return;
 for(auto r:legend_focus::rules)if(raw_rank(r.ordinal)&&focus_match(r,u)){
  if(r.mode==5)s->retaliation=U32(std::min<std::uint64_t>(r.limit*256u,std::uint64_t(s->retaliation)+(std::uint64_t(hp_loss)+shield_loss)*r.proc/100));
 }
}
inline bool enhanced_ensnare(bw::Unit* u) {
 auto body=effect_body(u);if(!valid_unit(body))return false;auto s=state(body);
 return talent_power::enabled&&raw_rank(82)&&s&&s->strong_ensnare&&body->ensnare_timer&&is_enemy(body->player);
}
inline double ensnare_move_ratio(bw::Unit* u) {
 if(!enhanced_ensnare(u))return 1;
 const auto body=effect_body(u);const int boosts=(body->stim_timer?1:0)+((body->flags&0x10000000u)?1:0);
 auto table=table_for({2,1,original_stat({0,0,body->unit_id})},false);const double base=table?read_entry(table,original_stat({0,0,body->unit_id})):256;
 const double fast=in(body->unit_id,{70,80,88})?1707.0:std::max(853.0,base*1.5);
 const double before=boosts?fast:base,after=boosts>1?fast:boosts==1?base:base/2;
 return after>0?before*0.15/after:0.15;
}
inline double ensnare_attack_ratio(bw::Unit* u,U32 weapon) {
 if(!enhanced_ensnare(u)||weapon>=130)return 1;
 U32 value=original_stat({1,16,weapon});if(u->acid_spore_count)value+=std::max(3u,value/8)*u->acid_spore_count;
 const int boosts=(u->stim_timer?1:0)+((u->flags&0x20000000u)?1:0);
 const auto without=std::max(5u,std::min(250u,boosts?value/2:value));
 const auto with=std::max(5u,std::min(250u,boosts>1?value/2:boosts==1?value:value+value/4));
 return double(without)*100/(double(with)*15);
}
inline double acid_attack_ratio(bw::Unit* u,U32 weapon) {
 auto s=state(u);if(!talent_power::enabled||!s||!s->double_acid||!u->acid_spore_count||weapon>=130)return 1;
 const U32 base=original_stat({1,16,weapon}),step=std::max(3u,base/8),count=u->acid_spore_count;
 const int boosts=(u->stim_timer?1:0)+((u->flags&0x20000000u)?1:0)-(u->ensnare_timer?1:0);
 auto period=[&](U32 n){U32 v=base+step*n;if(boosts>0)v/=2;else if(boosts<0)v+=v/4;return std::max(5u,std::min(250u,v));};
 return double(period(count*2))/period(count);
}
inline void hold_ensnare_cooldown(bw::Unit* u,U32 layer,U8& timer,U32 scaled) {
 auto s=state(u);if(!s)return;const bool active=enhanced_ensnare(u);const U32 frame=now();auto& due=s->ensnare_due[layer];
 if(active){
  if(scaled){due=frame+scaled;s->ensnare_factor[layer]=ensnare_attack_ratio(u,original_stat({0,layer?19u:17u,u->unit_id}));}
  else if(!due&&timer){const double factor=ensnare_attack_ratio(u,original_stat({0,layer?19u:17u,u->unit_id}));due=frame+U32(std::ceil(timer*factor));s->ensnare_factor[layer]=factor;}
  if(due>frame)timer=U8(std::min(255u,due-frame));else due=0;
 }else if(due){const U32 left=due>frame?due-frame:0;timer=U8(std::min(255u,U32(std::ceil(left/std::max(1.0,s->ensnare_factor[layer])))));due=0;}
}
inline void shadow_restore(bw::Unit* u,UnitState& s) {
 if(!s.shadow_active)return;u->flags=(u->flags&~0x4000000u)|s.shadow_invincible;s.shadow_active=false;
 if(live(u)){const auto order=u->order;const auto target=u->order_target;rework_relocation::move(u,s.shadow_x,s.shadow_y,96,false);u->order=order;u->order_target=target;}
}
inline void shadow_begin(bw::Unit* u,bw::Unit* target) {
 if(!talent_power::enabled||!own(u)||!raw_rank(321)||!in(u->unit_id,{61,74,75})||!eligible(target)||air(target))return;
 auto s=state(u);if(!s||s->shadow_active||now()<s->shadow_cooldown)return;
 auto targets=around(u->flingy.position.x,u->flingy.position.y,192,nullptr,65536,true,0);
 targets.erase(std::remove_if(targets.begin(),targets.end(),[&](bw::Unit* v){return building(v)||!visible(v,u->player)||protected_objective_unit(v);}),targets.end());
 if(targets.empty()||!rework_relocation::native_move)return;
 s->shadow_count=U32(std::min<std::size_t>(5,targets.size()));for(U32 i=0;i<s->shadow_count;i++)s->shadow_targets[i]=identity(targets[i]);
 s->shadow_active=true;s->shadow_step=0;s->shadow_due=now();s->shadow_cooldown=now()+288;s->shadow_x=u->flingy.position.x;s->shadow_y=u->flingy.position.y;s->shadow_invincible=u->flags&0x4000000u;u->flags|=0x4000000u;
}
inline void focus_tick(bw::Unit* u,UnitState& s) {
 if(s.strong_ensnare&&!u->ensnare_timer)s.strong_ensnare=false;
 if(s.double_acid&&!u->acid_spore_count)s.double_acid=false;
 if(s.shadow_active){
  if(!own(u)||!in(u->unit_id,{61,74,75})||u->stasis_timer||u->lockdown_timer||u->maelstrom_timer){shadow_restore(u,s);return;}
  if(now()<s.shadow_due)return;
  bw::Unit* target=nullptr;for(U32 n=0;n<s.shadow_count;n++){auto candidate=resolve(s.shadow_targets[(s.shadow_step+n)%s.shadow_count]);if(eligible(candidate)&&is_enemy(candidate->player)){target=candidate;break;}}
  if(!target){shadow_restore(u,s);return;}
  const auto old_order=u->order;const auto old_target=u->order_target;
  if(rework_relocation::move(u,target->flingy.position.x,target->flingy.position.y,48,false)){
   const U32 w=original_stat({0,17,u->unit_id}),base=owner_stat(u->player,{1,14,w})+owner_stat(u->player,{1,15,w})*upgrade_level(u->player,original_stat({1,6,w}));
   if(g.lone_sprite)g.lone_sprite(361,u->flingy.position.x,u->flingy.position.y,u->player);
   weapon_hurt(target,U32(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(base)*512)),w,u,u->player);
  }
  u->order=old_order;u->order_target=old_target;s.shadow_due=now()+4;
  if(++s.shadow_step>=5)shadow_restore(u,s);return;
 }
 if(talent_power::enabled&&raw_rank(96)&&own(u)&&u->unit_id==47&&now()%8==0){
  auto target=u->order_target.unit;if(!eligible(target)||!air(target))return;
  const U32 w=original_stat({0,19,47}),hit=(owner_stat(u->player,{1,14,w})*3/2)*256;
  auto reserved=[&](bw::Unit* enemy){std::uint64_t amount=0;living_units([&](bw::Unit* other){if(other!=u&&own(other)&&other->unit_id==47&&other->order_target.unit==enemy)amount+=hit;});return amount;};
  if(reserved(target)<std::uint64_t(std::max(0,target->flingy.hitpoints))+std::max(0,target->shields))return;
  for(auto candidate:around(u->flingy.position.x,u->flingy.position.y,192,target,65536,true,1))if(visible(candidate,u->player)&&reserved(candidate)<std::uint64_t(std::max(0,candidate->flingy.hitpoints))+std::max(0,candidate->shields)){
   if(g.order)g.order(u,10,candidate->flingy.position.x,candidate->flingy.position.y,candidate,0);break;
  }
 }
}
