#pragma once
// Included inside rework_combat_v5 after native damage/emission helpers.
inline bool expansion_matches(const unit_legend_expansion::Rule& r,U32 id) noexcept {
 return id<256&&(r.units[id/32]&(1u<<(id%32)));
}
inline U32 expansion_static_bonus(const bw::Unit* unit,U32 weapon) noexcept {
 if(!talent_power::enabled||!valid_unit(unit)||unit->player!=player_owner()||hallucination(unit)||!ordinary_weapon(weapon))return 0;
 U32 value=unit_trait_value(g.growth,unit->unit_id,2,true);for(const auto& r:unit_legend_expansion::rules)if((r.mode==1||r.mode==11)&&rank(r.ordinal)&&expansion_matches(r,unit->unit_id))value+=r.bonus;
 return value;
}
inline U32 expansion_outgoing_bonus(bw::Unit* unit,U32 weapon) {
 U32 value=expansion_static_bonus(unit,weapon);
 if(!own(unit)||!ordinary_weapon(weapon))return value;
 if(auto s=state(unit)){if(s->portal_buff_until>now())value+=20;if(s->fleet_buff_until>now())value+=30;}
 return value;
}
inline void portal_buff(bw::Unit* unit) {
 if(own(unit)&&!building(unit)&&!(unit->flags&(0x10u|0x20u|0x40u)))if(auto s=state(unit))s->portal_buff_until=now()+720;
}
inline void expansion_hit(bw::Unit* source,bw::Unit* target,U32 amount,U32 weapon) {
 if(!talent_power::enabled||(!own(source)&&!witnessed_suicide_source(source,weapon))||!valid_unit(target)||(live(target)&&!eligible(target))||!is_enemy(target->player))return;
 auto s=state(source);if(!s)return;
 for(const auto& r:unit_legend_expansion::rules){
  if(r.ordinal==185||legend_focus::converted(r.ordinal)||r.mode!=1||!r.count||!rank(r.ordinal)||!expansion_matches(r,source->unit_id)||s->shot_count%std::max(1u,r.cadence))continue;
  if(r.cadence==3)weapon_hurt(target,U32(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(amount)*2)),weapon,source,source->player);
  const auto secondary_amount=r.ordinal==191?std::uint64_t(amount)*(100+r.bonus)/100:std::uint64_t(amount);
  std::vector<Identity> victims;for(auto other:around(target->flingy.position.x,target->flingy.position.y,r.radius,target,r.count,true,air(target)))victims.push_back(identity(other));
  for(const auto& id:victims)if(auto other=resolve(id))weapon_hurt(other,U32(std::min<std::uint64_t>(0x7fffffffu,secondary_amount*r.percent/100)),weapon,source,source->player);
 }
}
inline void expansion_death(bw::Unit* dead) {
 if(!talent_power::enabled||!valid_unit(dead)||dead->player!=player_owner()||hallucination(dead))return;
 auto s=state(dead);if(!s||s->legendary_death_done)return;
 for(const auto& r:unit_legend_expansion::rules)if(r.mode==5&&rank(r.ordinal)&&expansion_matches(r,dead->unit_id)){
  s->legendary_death_done=true;std::vector<Identity> victims;
  for(auto other:around(dead->flingy.position.x,dead->flingy.position.y,r.radius,nullptr,r.count,true,0))victims.push_back(identity(other));
  for(const auto& id:victims)if(auto other=resolve(id))hurt(other,60*256,dead,dead->player);
  break;
 }
}
inline bool expansion_expiring(bw::Unit* unit) {
 if(!talent_power::enabled||!valid_unit(unit)||unit->player!=player_owner()||hallucination(unit))return false;
 for(const auto& r:unit_legend_expansion::rules)if(r.mode==5&&rank(r.ordinal)&&expansion_matches(r,unit->unit_id))return true;
 return false;
}
inline U32 expansion_support_frame=~0u;
inline void expansion_support() {
 if(!talent_power::enabled||now()%24||expansion_support_frame==now())return;
 expansion_support_frame=now();
 const U32 frame=now();std::vector<Identity> sources;
 living_units([&](bw::Unit* u){if(own(u)&&eligible(u)&&!u->lockdown_timer&&!u->maelstrom_timer&&!(u->flags&(0x10u|0x20u|0x40u)))sources.push_back(identity(u));});
 for(const auto& id:sources){auto source=resolve(id);if(!source)continue;
  for(const auto& r:unit_legend_expansion::rules){
   if(r.mode<2||r.mode>8||r.mode==5||!rank(r.ordinal)||!expansion_matches(r,source->unit_id))continue;
   for(auto target:around(source->flingy.position.x,source->flingy.position.y,r.radius,nullptr,65536,r.mode==8)){
    if(hallucination(target)||!eligible(target))continue;
    auto s=state(target);if(!s)continue;
    if(r.mode==8){if(visible(target,source->player))s->observer_mark_until=frame+48;continue;}
    const bool terran=race_type(target->unit_id,0),zerg=race_type(target->unit_id,1),protoss=race_type(target->unit_id,2);
    if(s->support_frame!=frame){s->support_frame=frame;s->support_hp=s->support_shields=0;}
    if(r.mode==2&&terran&&(original_stat({0,22,target->unit_id})&0x40000000u))s->support_hp=std::max(s->support_hp,12u*256);
    if(building(target)||!soldier(target->unit_id))continue;
    if(r.mode==3&&terran)s->fleet_buff_until=frame+48;
    if(r.mode==4&&zerg)s->support_hp=std::max(s->support_hp,U32(std::uint64_t(effective_max_hp(target))*(r.radius==128?3u:2u)/100));
    if(r.mode==6&&protoss)s->support_shields=std::max(s->support_shields,12u*256);
    if(r.mode==7&&protoss)s->shuttle_guard_until=frame+48;
   }
  }
 }
 living_units([&](bw::Unit* u){auto s=state(u);if(!s||s->support_frame!=frame)return;
  if(s->support_hp)heal(u,s->support_hp);
  if(s->support_shields){const auto cap=std::uint64_t(effective_max_shields(u))*256;u->shields=std::int32_t(std::min<std::uint64_t>(cap,std::uint64_t(std::max(0,u->shields))+s->support_shields));}
 });
}
inline void expansion_radiation() {
 if(!talent_power::enabled||!rank(unit_legend_expansion::kRadiationOrdinal))return;
 const U32 tick=original_stat({1,14,34})*256/std::max(1u,original_stat({1,16,34}));
 living_units([&](bw::Unit* host){auto s=state(host);if(!s)return;
  const U32 timer=host->irradiate_timer,previous=s->mechanical_irradiate_timer;s->mechanical_irradiate_timer=timer;
  if(!timer||previous!=timer+1||host->irradiate_player!=player_owner()||(host->flags&(0x10u|0x40u)))return;
  const U32 radius=rank(61)?128u:32u;auto source=valid_unit(host->irradiated_by)?host->irradiated_by:nullptr;
  for(const auto& id:irradiation::nearby(host->flingy.position.x,host->flingy.position.y,radius))if(auto target=resolve(id)){
   if(organic(target)||building(target)||!(original_stat({0,22,target->unit_id})&0x40000000u)||(target->flags&(0x10u|0x40u))||irradiation::box_distance(host,target)>std::uint64_t(radius)*radius)continue;
   weapon_hurt(target,tick*(rank(61)?3u:1u),34,source,player_owner());
  }
 });
}
