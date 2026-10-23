#pragma once
#include "base_defenses.generated.h"
namespace base_defenses {
struct Guard {bw::Unit* unit;U8 unique,owner;U32 type,x,y;};
inline std::vector<Guard> guards;
inline bool bound=false;
inline U32 last_frame=~0u;
inline void reset() noexcept {guards.clear();bound=false;last_frame=~0u;}
inline std::uint64_t distance(int x,int y,int a,int b) noexcept {
 const auto dx=std::int64_t(x)-a,dy=std::int64_t(y)-b;return dx*dx+dy*dy;
}
inline void bind(const base_defense_data::Post* posts,std::size_t count){
 bound=true;if(!g.mission)return;
 for(std::size_t i=0;i<count;i++){
  const auto& p=posts[i];if(p.mission!=g.mission->mission_id)continue;
  bw::Unit* found=nullptr;
  living_units([&](bw::Unit* u){
   if(u->unit_id!=p.type||u->player!=p.owner||!is_enemy(u->player)||rework_curses::marked(u))return;
   if(distance(u->flingy.position.x,u->flingy.position.y,p.x,p.y)>8u*8u)return;
   if(std::any_of(guards.begin(),guards.end(),[&](const Guard& q){return q.unit==u;}))return;
   found=u;
  });
  if(found)guards.push_back({found,found->minor_unique_index,found->player,found->unit_id,p.x,p.y});
 }
}
inline void step(bool ready,bool paused,bool goal){
 if(!g.active||!g.mission)return;
 if(!bound)bind(base_defense_data::posts,std::size(base_defense_data::posts));
 const auto game=g.game?g.game():nullptr;
 if(!ready||paused||goal||!game||!g.order||last_frame==game->frame_count)return;
 if(last_frame!=~0u&&game->frame_count-last_frame<8)return;last_frame=game->frame_count;
 for(auto& post:guards){
  auto u=post.unit;
  if(!valid_unit(u)||u->flingy.hitpoints<=0||u->order==0||u->minor_unique_index!=post.unique||u->player!=post.owner||u->unit_id!=post.type||!is_enemy(u->player)){
   post.unit=nullptr;continue;
  }
  if(u->stasis_timer||u->lockdown_timer||u->maelstrom_timer||(u->flags&0x40u))continue;
  auto target=u->order_target.unit;
  const bool outside=distance(u->flingy.position.x,u->flingy.position.y,post.x,post.y)>320u*320u;
  const bool chasing=valid_unit(target)&&distance(target->flingy.position.x,target->flingy.position.y,post.x,post.y)>384u*384u;
  const bool marching=!valid_unit(target)&&(u->order==6||u->order==14)&&distance(u->order_target.x,u->order_target.y,post.x,post.y)>320u*320u;
  if(outside||chasing||marching)g.order(u,kAttackMove,post.x,post.y,nullptr,228);
 }
}
}
