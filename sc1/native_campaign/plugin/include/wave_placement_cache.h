#pragma once
// A synchronous placement batch cannot advance native movement. Snapshot once,
// and discard the snapshot after every successful native creation (including
// its turret/children). No cached positions survive the outermost batch call.
namespace placement {
inline constexpr int width=64,pixels=128;
struct Entry {int x,y,next;U8 owner;bool protected_unit,building;};
inline std::array<int,width*width> heads{};
inline std::vector<Entry> entries;
inline U32 depth=0,alive=0,supply=0;inline bool ready=false;
inline void invalidate() noexcept {ready=false;}
struct Batch {
 Batch() noexcept {if(!depth++)invalidate();}
 ~Batch(){if(!--depth)invalidate();}
 Batch(const Batch&)=delete;Batch& operator=(const Batch&)=delete;
};
inline int cell(int p) noexcept {return std::clamp(p/pixels,0,width-1);}
inline void refresh(){
 if(ready)return;
 heads.fill(-1);entries.clear();alive=supply=0;
 living_units([](bw::Unit* u){
  ++alive;const auto t=existing_track(u);
  if(t&&t->spawned&&is_enemy(u->player))supply+=std::max(1u,original_stat({0,46,u->unit_id}));
  const auto p=u->flingy.position;const int bucket=cell(p.y)*width+cell(p.x),index=int(entries.size());
  entries.push_back({p.x,p.y,heads[bucket],u->player,wave_protected_unit(u),(original_stat({0,22,u->unit_id})&1u)!=0});heads[bucket]=index;
 });ready=true;++frame_profile::placement_snapshots;
}
template<class F>inline bool any(int x,int y,int radius,F matches){
 refresh();const auto limit=std::int64_t(radius)*radius;
 for(int cy=cell(y-radius);cy<=cell(y+radius);++cy)for(int cx=cell(x-radius);cx<=cell(x+radius);++cx)
  for(int i=heads[cy*width+cx];i>=0;i=entries[std::size_t(i)].next){
   ++frame_profile::placement_visits;const auto& e=entries[std::size_t(i)];
   const auto dx=std::int64_t(x)-e.x,dy=std::int64_t(y)-e.y;
   if(dx*dx+dy*dy<limit&&matches(e))return true;
  }
 return false;
}
inline bool clear(int x,int y,bool raid){
 ++frame_profile::placement_checks;refresh();
 if(alive>=1550||any(x,y,40,[](const Entry&){return true;}))return false;
 return raid||!any(x,y,512,[](const Entry& e){return e.protected_unit;});
}
inline bool safe(const sc1_native::campaign_wave_config::Origin& origin){
 if(!depth)return origin_safe(origin);
 return g.mission&&origin.mission_id==g.mission->mission_id&&is_enemy(origin.owner)&&origin.cell_count&&
  !any(origin.center.x,origin.center.y,512,[](const Entry& e){return e.protected_unit;});
}
inline bool base(const sc1_native::campaign_wave_config::Origin& origin){
 if(!depth)return origin_has_live_base(origin);
 return any(origin.center.x,origin.center.y,512,[&](const Entry& e){return e.owner==origin.owner&&e.building;});
}
}
