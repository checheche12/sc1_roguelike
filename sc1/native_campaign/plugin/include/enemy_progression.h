#pragma once
// Native upgrade/tech IDs and speed rules: pinned bw_dat Game and OpenBW
// references in analysis/runtime_rework_20261016/primary_sources. No DAT edits.
#include "rework_upgrade_storage.h"
namespace rework_waves {U32 upgrade_second(U32 elapsed) noexcept;}
namespace enemy_progression {
struct Unlock {U32 minute,id;};
inline constexpr Unlock upgrades[]={
 // Tier 1: infantry/early vehicles and basic ground movement/range.
 {6,16},{6,17},{6,27},{6,34},
 // Tier 2: Hydralisks, Dragoons and scouting/transport support.
 {8,29},{8,30},{8,33},{8,24},{8,25},{8,26},{8,37},{8,38},{8,39},
 // Specialist ground support and anti-air.
 {10,20},{10,54},{10,51},
 // Robotics and fleet mobility/capacity.
 {12,35},{12,36},{12,41},{12,42},{12,43},
 // Advanced casters and capital ships.
 {14,19},{14,21},{14,22},{14,23},{14,31},{14,40},{14,44},{14,47},{14,49},
 // Hive finishers.
 {16,28},{16,32},{16,52},{16,53},
};
inline constexpr Unlock technologies[]={
 {6,0},{6,3},{6,4},{6,11},{6,34},            // Stim, mines, scan, burrow, heal.
 {8,5},{8,6},{8,10},{8,12},{8,18},{8,23},{8,24},{8,28},{8,29},{8,30},{8,32},
 {10,1},{10,9},{10,17},{10,19},{10,20},      // Lockdown, Wraith, Queen, Templar.
 {12,2},{12,7},{12,13},{12,14},{12,25},       // Vessel, Queen, Swarm, Corsair.
 {14,8},{14,22},{14,31},                    // Yamato, Stasis, Maelstrom.
 {16,15},{16,16},{16,21},{16,27},           // Plague/Consume, Recall, Mind Control.
};
inline bool initialized=false;
inline U32 last_frame=0,active_ticks=0,last_second=0,announced=0;
inline void reset() noexcept {initialized=false;last_frame=active_ticks=last_second=announced=0;}
inline U32 second() noexcept {return active_ticks/24;}
inline U8* tech_slot(U32 owner,U32 id) noexcept {
 if(owner>=12||id>=44)return nullptr;
 if(g.extended||g.extended_count){
  if(!g.extended||g.extended_count<=2)return nullptr;
  const auto& a=g.extended[2];const auto begin=reinterpret_cast<std::uintptr_t>(a.pointer),end=reinterpret_cast<std::uintptr_t>(a.end);
  const auto offset=std::size_t(id)*12+owner;
  return begin && end>=begin && offset<end-begin?a.pointer+offset:nullptr;
 }
 auto game=g.game?g.game():nullptr;if(!game)return nullptr;
 return id<24?&game->tech_level_sc[owner][id]:&game->tech_level_bw[owner][id-24];
}
inline bool researched(U32 owner,U32 id) noexcept {const auto p=tech_slot(owner,id);return p&&*p;}
inline void upgrade(U32 owner,U32 id,U32 minimum) noexcept {
 auto p=rework_upgrade_storage::slot(owner,id);if(!p)return;
 *p=std::max(*p,U8(minimum));
 auto legacy=rework_upgrade_storage::legacy(owner,id);if(legacy)*legacy=std::max(*legacy,*p);
}
inline void research(U32 owner,U32 id) noexcept {
 auto p=tech_slot(owner,id);if(!p)return;*p=std::max(*p,U8(1));
 auto game=g.game?g.game():nullptr;if(game){auto& legacy=id<24?game->tech_level_sc[owner][id]:game->tech_level_bw[owner][id-24];legacy=std::max(legacy,*p);}
}
inline U32 speed_upgrade(U32 type) noexcept {
 switch(type){case 2:case 19:return 17;case 42:return 26;case 37:return 27;case 38:return 29;case 65:return 34;
 case 70:return 42;case 69:return 37;case 84:return 39;case 39:return 53;default:return 61;}
}
inline void refresh_motion(bw::Unit* u) noexcept {
 if(!valid_unit(u)||!is_enemy(u->player)||hallucination(u)||u->flingy.hitpoints<=0||!u->order)return;
 if(u->unit_id==37&&rework_upgrade_storage::level(u->player,28))u->flags|=0x20000000u;
 const auto id=speed_upgrade(u->unit_id);if(id>=61||!rework_upgrade_storage::level(u->player,id))return;
 u->flags|=0x10000000u;
 // Iscript-driven ground movement reads the speed flag in native Move.
 if(u->flingy.movement_type==2)return;
 const auto flingy=original_stat({0,0,u->unit_id});
 auto speed=table_for({2,1,flingy},false),accel=table_for({2,2,flingy},false),turn=table_for({2,4,flingy},false);
 if(!speed||!accel||!turn)return;
 U32 s=read_entry(speed,flingy),a=read_entry(accel,flingy),t=read_entry(turn,flingy);
 const int modifier=1+(u->stim_timer?1:0)-(u->ensnare_timer?1:0);
 if(modifier>0){s=u->unit_id==70?1707u:std::max(853u,s+s/2);a*=2;t*=2;}
 else if(modifier<0){s/=2;a-=a/4;t-=t/4;}
 u->flingy.top_speed=s;u->flingy.acceleration=std::uint16_t(std::min(65535u,a));u->flingy.turn_speed=U8(std::min(255u,t));
 if(auto tracked=existing_track(u)){tracked->base_speed=s;tracked->applied_speed=s;}
}
inline U32 escort_base(const bw::Unit*,U32 native_speed) noexcept {return native_speed;}
inline void step(bool ready,bool blocked,bool goal) {
 auto game=g.game?g.game():nullptr;if(!game||!g.active||!g.applied||!g.mission)return;
 const auto frame=game->frame_count;if(!initialized){initialized=true;last_frame=frame;}
 const auto delta=frame>=last_frame?std::min(24u,frame-last_frame):0;last_frame=frame;
 if(!ready||blocked||goal)return;
 active_ticks+=delta;
 const auto now=rework_waves::upgrade_second(second());
 if(now!=last_second){
  last_second=now;const U32 level=now>=840?3u:now>=600?2u:now>=360?1u:0u;
  bool combat_changed=false,special_changed=false;
  if(level)for(U32 owner=0;owner<8;owner++)if(is_enemy(owner)){
   for(U32 id=0;id<16;id++){combat_changed|=rework_upgrade_storage::level(owner,id)<level;upgrade(owner,id,level);}
   for(const auto& unlock:upgrades)if(now>=unlock.minute*60){special_changed|=rework_upgrade_storage::level(owner,unlock.id)<1;upgrade(owner,unlock.id,1);}
   for(const auto& unlock:technologies)if(now>=unlock.minute*60){special_changed|=!researched(owner,unlock.id);research(owner,unlock.id);}
  }
  const U32 stage=now<360?0:std::min(6u,(now-360)/120+1);
  if(stage>announced){announced=stage;log_event("Enemy technology stage=%u active_seconds=%u adjusted_seconds=%u",stage,second(),now);if(combat_changed)message("적의 공방 업그레이드가 완료되었습니다.");if(special_changed)message("적의 특수 기술 중 일부가 강화되었습니다.");}
 }
 living_units([](bw::Unit* u){refresh_motion(u);});
}
}
