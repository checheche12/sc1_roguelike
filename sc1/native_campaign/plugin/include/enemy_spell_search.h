#pragma once
// Shared, frame-local spatial index. Orders still use live native validation.
namespace spell_search {
inline constexpr U32 cells=64,cell_pixels=128,candidate_limit=24,casters_per_frame=4;
struct Entry {bw::Unit* unit;int next;U8 unique,owner;std::uint16_t type;};
inline std::array<int,cells*cells> heads{};
inline std::vector<Entry> entries;
inline bw::Unit* base=nullptr;inline std::size_t capacity=0;
inline U32 frame=0;inline bool initialized=false;
inline void reset() noexcept {initialized=false;entries.clear();base=nullptr;capacity=0;}
inline int cell(int p) noexcept {return std::clamp(p/int(cell_pixels),0,int(cells)-1);}
inline void refresh(){
 const auto now=g.game()->frame_count;
 if(initialized&&frame==now&&base==g.units&&capacity==g.units_count)return;
 heads.fill(-1);entries.clear();
 living_units([](bw::Unit* u){
  const auto p=u->flingy.position;const auto bucket=cell(p.y)*cells+cell(p.x);
  const int index=int(entries.size());entries.push_back({u,heads[bucket],u->minor_unique_index,u->player,u->unit_id});heads[bucket]=index;
 });
 base=g.units;capacity=g.units_count;frame=now;initialized=true;
}
template<class F> void nearby(int x,int y,int radius,F fn){
 refresh();const auto limit=std::int64_t(radius)*radius;
 for(int cy=cell(y-radius);cy<=cell(y+radius);cy++)for(int cx=cell(x-radius);cx<=cell(x+radius);cx++){
  for(int i=heads[cy*cells+cx];i>=0;i=entries[std::size_t(i)].next){
#ifdef SC1_NATIVE_HOST_TEST
   ++host_unit_visits;
#endif
   const auto& entry=entries[std::size_t(i)];auto u=entry.unit;
   if(!valid_unit(u)||u->minor_unique_index!=entry.unique||u->player!=entry.owner||u->unit_id!=entry.type||u->flingy.hitpoints<=0||!u->order)continue;
   const auto p=u->flingy.position;
   if(wave_targeting::distance(x,y,p.x,p.y)<=limit&&!fn(u))return;
  }
 }
}
inline U32 priority(const bw::Unit* u,U32 tech,U32 now) noexcept {
 U32 value=U32(u-g.units)*0x9e3779b9u+tech*0x85ebca6bu+(now/24)*0xc2b2ae35u;
 value^=value>>16;value*=0x7feb352du;value^=value>>15;return value;
}
}
