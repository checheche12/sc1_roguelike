#pragma once
// Included inside rework_waves, after the shared spell spatial index.
// Stock native orders98/99 own the animation, turret and morph. OpenBW's
// order_Sieging/order_Unsieging are the reference; no unit-ID/HP/DAT writes.
inline std::int64_t tank_target_distance(bw::Unit* u,bw::Unit* target) noexcept {
 const auto a=multi_target::dimensions(u->unit_id),b=multi_target::dimensions(target->unit_id);
 const auto p=u->flingy.position,q=target->flingy.position;
 const auto dx=std::max<std::int64_t>(0,std::max(std::int64_t(p.x)-a.left-q.x-b.right,std::int64_t(q.x)-b.left-p.x-a.right));
 const auto dy=std::max<std::int64_t>(0,std::max(std::int64_t(p.y)-a.top-q.y-b.bottom,std::int64_t(q.y)-b.top-p.y-a.bottom));
 return dx*dx+dy*dy;
}
inline void tank_tactics(bw::Unit* u,rework_curses::Identity& v) {
 const bool mobile=u->unit_id==5||u->unit_id==23,deployed=u->unit_id==30||u->unit_id==25;
 if((!mobile&&!deployed)||!g.order||!g.game||!multi_target::can_attack||!rework_curses::marked(u)||counter(kGoalCounter)||
    rework_curses::appearing(u)||v.transport_hold||!(u->flags&1u)||(u->flags&(0x20u|0x40u|0x1000u|0x40000000u))||
    u->lockdown_timer||u->stasis_timer||u->maelstrom_timer||u->order==98||u->order==99)return;
 if(!wave_targeting::reorderable(u->order)&&u->order!=100&&u->order!=152)return;
 auto turret=u->subunit;const bool hero=u->unit_id==23||u->unit_id==25;
 if(!valid_unit(turret)||turret->subunit!=u||turret->player!=u->player||
    turret->unit_id!=(hero?(deployed?26u:24u):(deployed?31u:6u)))return;
 const U32 frame=g.game()->frame_count;
 if(v.siege_scan!=~0u&&frame-v.siege_scan<24)return;v.siege_scan=frame;
 const U32 weapon=original_stat({0,17,hero?26u:31u});if(weapon>=130)return;
 const U32 minimum=original_stat({1,4,weapon}),maximum=original_stat({1,5,weapon});
 if(!maximum||maximum>1024||minimum>=maximum)return;
 bw::Unit* choice=nullptr;std::int64_t nearest=std::numeric_limits<std::int64_t>::max();bool close=false,keep_current=false;
 const auto origin=u->flingy.position;
 spell_search::nearby(origin.x,origin.y,int(maximum)+128,[&](bw::Unit* target){
  if(target->player!=player_owner()||target->unit_id>=228||(target->flags&(4u|0x40u|0x4000000u))||target->stasis_timer)return true;
  auto sprite=static_cast<bw::SpriteScr*>(target->flingy.sprite);
  if(!sprite||!(sprite->visibility_mask&(1u<<u->player))||((target->flags&0x300u)&&!(target->detection_status&(1u<<u->player))))return true;
  {OwnerDatScope scope(u->player,u->player,turret);if(!multi_target::can_attack(turret,target,1))return true;}
  const auto distance=tank_target_distance(u,target);if(distance>std::int64_t(maximum)*maximum)return true;
  if(distance<std::int64_t(minimum)*minimum){close=true;return true;}
  const bool active_target=target==u->order_target.unit||target==turret->order_target.unit;
  if(!choice||(!keep_current&&(active_target||distance<nearest))){choice=target;nearest=distance;keep_current=active_target;}
  return true;
 });
 const bool settled=!v.siege_changed||frame-v.siege_change_frame>=72;
 if(choice){
  v.siege_contact=true;v.siege_contact_frame=frame;
  if(mobile){
   if(settled){v.siege_changed=true;v.siege_change_frame=frame;g.order(u,98,origin.x,origin.y,nullptr,228);}
  }else if(u->order_target.unit!=choice||(u->order!=100&&!multi_target::attack_order(u->order))){
   const auto p=choice->flingy.position;g.order(u,10,p.x,p.y,choice,choice->unit_id);
  }
 }else if(deployed){
  if(!v.siege_contact){v.siege_contact=true;v.siege_contact_frame=frame;}
  if(settled&&frame-v.siege_contact_frame>=(close?24u:72u)){
   v.siege_changed=true;v.siege_change_frame=frame;g.order(u,99,origin.x,origin.y,nullptr,228);
  }
 }
}
