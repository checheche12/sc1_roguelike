#pragma once
// Included inside rework_waves. Native orders own energy, damage and effects.
using TechTargetFn=U32 (__cdecl*)(bw::Unit*,U32,bw::Unit*,U32,U32,U32,std::uint16_t*);
inline TechTargetFn native_tech_target=nullptr;
struct SpellReservation {U32 tech=44,until=0,owner=12;int x=0,y=0;bw::Unit* target=nullptr;U8 unique=0;};
inline std::array<SpellReservation,64> spell_reservations{};
inline U32 spell_cursor=0;
#include "enemy_spell_search.h"
inline void reset_spells() noexcept {spell_reservations={};spell_cursor=0;spell_search::reset();}
inline bool spell_candidate(bw::Unit* caster,bw::Unit* target,bool friendly) noexcept {
 if(!valid_unit(target)||target==caster||target->flingy.hitpoints<=0||!target->order||!(target->flags&1u)||
    (target->flags&(0x40000040u|0x1000u))||target->stasis_timer||protected_objective_unit(target)||!regular_combat_type(target->unit_id))return false;
 if(friendly){if(target->player!=caster->player)return false;}
 else {
  if(target->player!=player_owner())return false;
  auto sprite=static_cast<bw::SpriteScr*>(target->flingy.sprite);
  if(!sprite||!(sprite->visibility_mask&(1u<<caster->player)))return false;
  if((target->flags&0x300u)&&!(target->detection_status&(1u<<caster->player)))return false;
 }
 const auto a=caster->flingy.position,b=target->flingy.position;
 return wave_targeting::distance(a.x,a.y,b.x,b.y)<=288ll*288;
}
inline bool spell_reserved(U32 tech,U32 owner,bw::Unit* target,bool area,U32 frame) noexcept {
 const auto p=target->flingy.position;
 for(const auto& r:spell_reservations)if(r.tech==tech&&r.owner==owner&&r.until>frame){
  if(area&&wave_targeting::distance(r.x,r.y,p.x,p.y)<=128ll*128)return true;
  if(!area&&r.target==target&&r.unique==target->minor_unique_index)return true;
 }
 return false;
}
inline bool spell_due(bw::Unit* u,const rework_curses::Identity& v) noexcept {
 if(!native_tech_target||!g.order||!rework_curses::marked(u)||u->flingy.hitpoints<=0||!u->order||
    u->lockdown_timer||u->stasis_timer||u->maelstrom_timer||u->spell_cooldown||(u->flags&(0x1000u|0x40u)))return false;
 const U32 frame=g.game()->frame_count;
 if(v.last_spell&&frame-v.last_spell<72)return false;
 if(v.last_scan&&frame-v.last_scan<24)return false;
 if(!wave_targeting::reorderable(u->order)&&u->order!=50&&u->order!=58)return false;
 const auto ready=[&](U32 tech,U32 energy){return u->energy>=energy*256&&enemy_progression::researched(u->player,tech);};
 switch(u->unit_id){
 case 67:case 79:case 51:return ready(19,75);
 case 9:case 22:return ready(2,100)||ready(7,75)||ready(6,100);
 case 71:return ready(22,100);
 case 12:case 28:case 29:return ready(8,150);
 case 1:case 16:case 99:case 100:return ready(1,100);
 case 45:case 49:return ready(13,150)||ready(17,75)||ready(18,75);
 case 46:case 50:return ready(15,150)||ready(14,100)||(u->energy<100*256&&ready(16,0));
 case 63:return ready(29,50)||ready(31,100)||ready(27,150);
 case 60:return ready(25,125);
 case 34:return ready(24,50)||ready(30,75);
 default:return false;
 }
}
inline void auto_spell(bw::Unit* u,rework_curses::Identity& v) {
 if(!spell_due(u,v))return;
 const U32 frame=g.game()->frame_count;v.last_scan=frame?frame:1;
 bw::Unit* choice=nullptr;U32 chosen_tech=44,chosen_order=0;bool chosen_area=false;
 auto pick=[&](U32 tech,U32 order,U32 energy,bool friendly,bool area,U32 minimum,auto useful,bool costly=false){
  if(choice||u->energy<energy*256||!enemy_progression::researched(u->player,tech))return;
  struct Candidate {bw::Unit* unit=nullptr;U32 priority=0;};
  std::array<Candidate,spell_search::candidate_limit> candidates{};std::size_t count=0;
  const auto origin=u->flingy.position;
  spell_search::nearby(origin.x,origin.y,288,[&](bw::Unit* target){
   if(!spell_candidate(u,target,friendly)||spell_reserved(tech,u->player,target,area,frame)||(!costly&&!useful(target)))return true;
   Candidate next{target,spell_search::priority(target,tech,frame)};
   if(count<candidates.size())candidates[count++]=next;
   else {auto worst=std::max_element(candidates.begin(),candidates.end(),[](const auto& a,const auto& b){return a.priority<b.priority;});if(next.priority<worst->priority)*worst=next;}
   return true;
  });
  std::int64_t best=-1;
  for(std::size_t index=0;index<count;index++){
   auto target=candidates[index].unit;if(costly&&!useful(target))continue;
   const auto p=target->flingy.position;U32 enemies=0,friends=0;
   if(area)spell_search::nearby(p.x,p.y,96,[&](bw::Unit* other){
    if(spell_candidate(u,other,false))++enemies;
    if(valid_unit(other)&&other->flingy.hitpoints>0&&other->order&&other->player<8&&
       (other->player==u->player||(!is_enemy(other->player)&&other->player!=player_owner())||
        g.game()->alliances[u->player][other->player]||g.game()->alliances[other->player][u->player])&&
       other->player!=player_owner()&&!(other->flags&0x40u)){
      // Web affects ground units; the other offensive areas affect both.
      if(tech!=25||!(original_stat({0,22,other->unit_id})&4u))++friends;
    }
    return friends==0;
   });
   if(area&&(enemies<minimum||friends))continue;
   std::uint16_t error=0;if(!native_tech_target(u,tech,target,target->unit_id,U32(p.x),U32(p.y),&error))continue;
   const auto score=std::int64_t(enemies)*1000000+target->flingy.hitpoints+target->shields;
   if(score>best){best=score;choice=target;chosen_tech=tech;chosen_order=order;chosen_area=area;}
  }
 };
 const auto any=[](bw::Unit*){return true;};
 const auto organic=[](bw::Unit* t){return (original_stat({0,22,t->unit_id})&0x10000u)!=0;};
 const auto ground=[](bw::Unit* t){return !(original_stat({0,22,t->unit_id})&4u);};
 switch(u->unit_id){
 case 67:case 79:case 51:
  pick(19,142,75,false,true,2,[](bw::Unit* t){return !t->is_under_storm;});break;
 case 9:case 22:
  pick(2,122,100,false,false,1,[](bw::Unit* t){return t->shields>=100*256||t->energy>=100*256;});
  pick(7,143,75,false,false,1,[&](bw::Unit* t){return organic(t)&&!t->irradiate_timer&&t->flingy.hitpoints>=80*256;});
  pick(6,141,100,true,false,1,[&](bw::Unit* t){
   if(t->matrix_timer)return false;bool fighting=false;const auto p=t->flingy.position;spell_search::nearby(p.x,p.y,192,[&](bw::Unit* e){
    if(spell_candidate(u,e,false))fighting=true;return !fighting;});return fighting;},true);break;
 case 71:pick(22,147,100,false,true,3,any);break;
 case 12:case 28:case 29:
  pick(8,113,150,false,false,1,[](bw::Unit* t){return t->flingy.hitpoints>=150*256;});break;
 case 1:case 16:case 99:case 100:
  pick(1,115,100,false,false,1,[](bw::Unit* t){return !t->lockdown_timer&&(original_stat({0,22,t->unit_id})&0x40000000u)&&t->flingy.hitpoints>=80*256;});break;
 case 45:case 49:
  pick(13,121,150,false,false,1,[](bw::Unit* t){return t->flingy.hitpoints>=100*256;});
  pick(17,146,75,false,true,3,[](bw::Unit* t){return !t->ensnare_timer;});
  pick(18,120,75,false,false,1,[&](bw::Unit* t){return t->flingy.hitpoints>=150*256&&!(t->parasited_by_players&(1u<<u->player));});break;
 case 46:case 50:
  pick(15,144,150,false,true,3,[](bw::Unit* t){return !t->plague_timer&&t->flingy.hitpoints>=40*256;});
  // Protect a marked melee front line; never consume original/script units.
  pick(14,119,100,true,false,1,[&](bw::Unit* t){
   if(!ground(t)||!rework_curses::marked(t)||original_stat({0,17,t->unit_id})>=130)return false;
   bool ranged_enemy=false;const auto p=t->flingy.position;spell_search::nearby(p.x,p.y,192,[&](bw::Unit* e){if(spell_candidate(u,e,false)&&ground(e)&&original_stat({0,17,e->unit_id})<130)ranged_enemy=true;return !ranged_enemy;});return ranged_enemy;},true);
  if(u->energy<100*256)pick(16,145,0,true,false,1,[](bw::Unit* t){auto tag=rework_curses::identity(t);return t->unit_id==37&&rework_curses::marked(t)&&tag&&!tag->elite;});break;
 case 63:
  pick(29,180,50,false,false,1,[](bw::Unit* t){return t->energy>=75*256;});
  pick(31,182,100,false,true,3,[&](bw::Unit* t){return organic(t)&&!t->maelstrom_timer;});
  pick(27,178,150,false,false,1,[](bw::Unit* t){return t->flingy.hitpoints>=200*256;});break;
 case 60:pick(25,177,125,false,true,3,ground);break;
 case 34:
  pick(24,176,50,true,false,1,[](bw::Unit* t){return t->lockdown_timer||t->irradiate_timer||t->plague_timer||t->ensnare_timer||t->is_blind;});
  pick(30,181,75,false,false,1,[](bw::Unit* t){return !t->is_blind&&((original_stat({0,22,t->unit_id})&0x8000u)||t->energy>=75*256);});break;
 default:return;
 }
 if(!choice)return;
 const auto p=choice->flingy.position;v.last_spell=frame?frame:1;
 auto& reservation=spell_reservations[spell_cursor++%spell_reservations.size()];
 reservation={chosen_tech,frame+(chosen_area||chosen_tech==14?144u:72u),u->player,p.x,p.y,choice,choice->minor_unique_index};
 g.order(u,chosen_order,U32(p.x),U32(p.y),choice,choice->unit_id);
}
