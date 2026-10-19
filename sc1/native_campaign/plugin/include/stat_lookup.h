#pragma once
// Simulation-thread indexes for immutable phase edits. Unedited fields still
// read the current native table; temporary owner scopes never become baselines.
namespace stat_lookup {
inline constexpr U32 fields=64,entries=228,tables=5;
struct Index {
 const Edit* data=nullptr;std::size_t count=~std::size_t(0);
 std::array<std::int16_t,tables*fields*entries> positions{};
 void reset() noexcept {data=nullptr;count=~std::size_t(0);}
 const Edit* find(const std::vector<Edit>& edits,Key key) noexcept {
  if(edits.empty())return nullptr;
  if(key.table>=tables||key.field>=fields||key.id>=entries||edits.size()>1024){
   for(const auto& edit:edits)if(same(edit.key,key))return &edit;return nullptr;
  }
  if(data!=edits.data()||count!=edits.size()){
   positions.fill(-1);data=edits.data();count=edits.size();
   for(std::size_t i=0;i<count;++i){const auto k=data[i].key;if(k.table>=tables||k.field>=fields||k.id>=entries)continue;
    auto& at=positions[(k.table*fields+k.field)*entries+k.id];if(at<0)at=std::int16_t(i);
   }
  }
  const auto position=positions[(key.table*fields+key.field)*entries+key.id];
  return position>=0?data+position:nullptr;
 }
};
inline Index baseline,friendly,enemy;
inline void reset() noexcept {baseline.reset();friendly.reset();enemy.reset();}
}
