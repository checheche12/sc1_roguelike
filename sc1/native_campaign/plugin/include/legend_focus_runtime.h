#pragma once
// Included inside rework_combat_v5 after weapon_hurt and before ordinary_hit.
inline bool focus_match(const legend_focus::Rule& r,const bw::Unit* u) noexcept {return valid_unit(u)&&u->unit_id<256&&(r.units[u->unit_id/32]&(1u<<(u->unit_id%32)));}
inline bool erosion_source(bw::Unit* u) noexcept {
 if(!talent_power::enabled||!valid_unit(u)||u->player!=player_owner()||hallucination(u)||!raw_rank(190))return false;
 for(const auto& r:legend_focus::rules)if(r.ordinal==190)return focus_match(r,u);return false;
}
inline bool flame_cone(bw::Unit* u,bw::Unit* target,bw::Unit* other) noexcept {
 if(!eligible(other)||air(other)!=air(target)||!is_enemy(other->player)||other==target||dist(u,other)>96u*96u)return false;
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
  if(!(r.ordinal==105&&mutal_bounce_numerator))bonus+=r.base;
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
  if(r.mode==10&&s->dragoon_hits==0)weapon_hurt(target,U32(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(amount)*r.proc/100)),weapon,u,u->player);
  if(r.mode==5&&s->retaliation){const U32 stored=s->retaliation;s->retaliation=0;weapon_hurt(target,stored,weapon,u,u->player);}
  if(r.mode==6){if(t->erosion_owner!=u->player){t->erosion=0;t->erosion_owner=u->player;}t->erosion=U32(std::min<std::uint64_t>(0xfffffffeu,std::uint64_t(t->erosion)+r.step));}
 }
}
inline void focus_received(bw::Unit* u,bw::Unit* attacker,U32 hp_loss,U32 shield_loss) {
 if(!focus_source(u)||!is_enemy(attacker?attacker->player:12))return;auto s=state(u);if(!s)return;
 for(auto r:legend_focus::rules)if(raw_rank(r.ordinal)&&focus_match(r,u)){
  if(r.mode==5)s->retaliation=U32(std::min<std::uint64_t>(r.limit*256u,std::uint64_t(s->retaliation)+(std::uint64_t(hp_loss)+shield_loss)*r.proc/100));
 }
}
// StepUnitTimers owns native natural shield regeneration. Multiply only its
// observed small recovery, leaving batteries, instant recovery and damage alone.
struct RetaliationShieldRegenScope {
 Identity who{};U32 before=0;bool watched=false;
 explicit RetaliationShieldRegenScope(bw::Unit* u) noexcept {
  if(!talent_power::enabled||!own(u)||!raw_rank(139)||!in(u->unit_id,{68,76})||!(u->flags&1u))return;
  who=identity(u);before=U32(std::max(0,u->shields));watched=true;
 }
 ~RetaliationShieldRegenScope() noexcept {
  if(!watched)return;auto u=resolve(who);if(!own(u)||!raw_rank(139)||u->shields<=std::int32_t(before))return;
  const auto gain=U32(u->shields)-before;if(gain>legend_focus::native_shield_regen_q8)return;
  const auto maximum=std::uint64_t(effective_max_shields(u))*256u;
  u->shields=std::int32_t(std::min(maximum,std::uint64_t(u->shields)+std::uint64_t(gain)*(legend_focus::retaliation_shield_regen_multiplier-1u)));
 }
};
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
 if(live(u)){const auto order=u->order,stage=u->order_state,signal=u->order_signal,timer=u->order_timer,wait=u->order_wait;const auto target=u->order_target;
  rework_relocation::move(u,s.shadow_x,s.shadow_y,96,false);u->order=order;u->order_state=stage;u->order_signal=signal;u->order_timer=timer;u->order_wait=wait;u->order_target=target;
  if(!live(target.unit)&&multi_target::attack_order(order))rework_relocation::stop_preserving_queue(u);}
}
inline bool shadow_candidate(bw::Unit* u,bw::Unit* target) {
 return eligible(target)&&!air(target)&&is_enemy(target->player)&&visible(target,u->player)&&!protected_objective_unit(target);
}
inline bw::Unit* shadow_pick(bw::Unit* u,UnitState& s,int x,int y,U32 radius) {
 bw::Unit* best=nullptr;U32 priority=3;std::uint64_t nearest=~std::uint64_t(0);
 for(auto candidate:around(x,y,radius,nullptr,65536,true,0)){
  if(!shadow_candidate(u,candidate))continue;U32 rank=0;
  for(U32 i=0;i<s.shadow_count;i++)if(generation(s.shadow_targets[i])==candidate)rank=1;
  // The previous victim is eligible only when no other candidate exists.
  if(s.shadow_count&&generation(s.shadow_targets[s.shadow_count-1])==candidate)rank=2;
  const auto distance=dist(x,y,candidate->flingy.position.x,candidate->flingy.position.y);
  if(rank<priority||(rank==priority&&distance<nearest)){best=candidate;priority=rank;nearest=distance;}
 }return best;
}
inline void shadow_begin(bw::Unit* u,bw::Unit* target) {
 if(!talent_power::enabled||!own(u)||!raw_rank(321)||!in(u->unit_id,{61,74,75})||(u->flags&0x40u)||u->stasis_timer||u->lockdown_timer||u->maelstrom_timer)return;
 auto s=state(u);if(!s||s->shadow_active||now()<s->shadow_cooldown)return;
 s->shadow_count=0;
 const auto radius=legend_focus::shadow_trigger_radius_pixels;
 if(!shadow_candidate(u,target)||dist(u,target)>std::uint64_t(radius)*radius)target=shadow_pick(u,*s,u->flingy.position.x,u->flingy.position.y,radius);
 if(!target||!rework_relocation::native_move)return;
 s->shadow_first=identity(target);s->shadow_anchor_x=target->flingy.position.x;s->shadow_anchor_y=target->flingy.position.y;
 s->shadow_active=true;s->shadow_step=0;s->shadow_due=now();s->shadow_cooldown=now()+288;s->shadow_x=u->flingy.position.x;s->shadow_y=u->flingy.position.y;s->shadow_invincible=u->flags&0x4000000u;u->flags|=0x4000000u;
}
inline void shadow_prepare(bw::Unit* u) {
 if(!talent_power::enabled||!own(u)||!in(u->unit_id,{61,74,75})||!raw_rank(321))return;
 auto s=state(u);if(!s||s->shadow_active||now()<s->shadow_cooldown)return;
 auto target=u->order_target.unit;const auto radius=legend_focus::shadow_trigger_radius_pixels;
 if(shadow_candidate(u,target)&&dist(u,target)<=std::uint64_t(radius)*radius){shadow_begin(u,target);return;}
 if(s->shadow_scan!=~0u&&now()-s->shadow_scan<8)return;s->shadow_scan=now();shadow_begin(u,nullptr);
}
inline bool shadow_cross_target(bw::Unit* u,bw::Unit* target) {
 const auto center=target->flingy.position;
 const auto a=multi_target::dimensions(target->unit_id),b=multi_target::dimensions(u->unit_id);
 int dx=int(center.x)-u->flingy.position.x,dy=int(center.y)-u->flingy.position.y;
 if(!dx&&!dy)dx=1;
 const int edge_x=(dx>=0?a.right+b.left:a.left+b.right)+8;
 const int edge_y=(dy>=0?a.bottom+b.top:a.top+b.bottom)+8;
 int offset_x=0,offset_y=0;
 // Extend the incoming direction through the target to the opposite edge,
 // accounting for both footprints so large buildings remain valid targets.
 if(std::int64_t(std::abs(dx))*edge_y>=std::int64_t(std::abs(dy))*edge_x){
  offset_x=dx>=0?edge_x:-edge_x;offset_y=int(std::int64_t(dy)*edge_x/std::abs(dx));
 }else{
  offset_y=dy>=0?edge_y:-edge_y;offset_x=int(std::int64_t(dx)*edge_y/std::abs(dy));
 }
 return rework_relocation::move(u,int(center.x)+offset_x,int(center.y)+offset_y,48,false,&center);
}
inline void focus_tick(bw::Unit* u,UnitState& s) {
 if(s.strong_ensnare&&!u->ensnare_timer)s.strong_ensnare=false;
 if(s.double_acid&&!u->acid_spore_count)s.double_acid=false;
 if(!s.shadow_active)shadow_prepare(u);
 if(s.shadow_active){
  if(!own(u)||!in(u->unit_id,{61,74,75})||u->stasis_timer||u->lockdown_timer||u->maelstrom_timer){shadow_restore(u,s);return;}
  if(now()<s.shadow_due)return;
  auto target=s.shadow_step==0?resolve(s.shadow_first):nullptr;
  if(!shadow_candidate(u,target))target=nullptr;
  if(!target)target=shadow_pick(u,s,s.shadow_anchor_x,s.shadow_anchor_y,legend_focus::shadow_chain_radius_pixels);
  if(!target){shadow_restore(u,s);return;}
  const auto old_order=u->order,old_stage=u->order_state,old_signal=u->order_signal,old_timer=u->order_timer,old_wait=u->order_wait;const auto old_target=u->order_target;
  if(shadow_cross_target(u,target)){
   s.shadow_anchor_x=target->flingy.position.x;s.shadow_anchor_y=target->flingy.position.y;
   if(s.shadow_count<5)s.shadow_targets[s.shadow_count++]=identity(target);
   const U32 w=original_stat({0,17,u->unit_id}),base=owner_stat(u->player,{1,14,w})+owner_stat(u->player,{1,15,w})*upgrade_level(u->player,original_stat({1,6,w}));
   if(g.lone_sprite)g.lone_sprite(361,u->flingy.position.x,u->flingy.position.y,u->player);
   weapon_hurt(target,U32(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(base)*256*legend_focus::shadow_damage_percent/100)),w,u,u->player);
  }
  u->order=old_order;u->order_state=old_stage;u->order_signal=old_signal;u->order_timer=old_timer;u->order_wait=old_wait;u->order_target=old_target;s.shadow_due=now()+4;
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
