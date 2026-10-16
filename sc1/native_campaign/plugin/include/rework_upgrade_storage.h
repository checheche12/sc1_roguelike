#pragma once
// SAMASE relocates upgrade levels to extended array0, upgrade-major/player-minor.
// Legacy Game bytes remain a compatibility view and are not the native source
// of truth when the extended array is present.
namespace rework_upgrade_storage {
inline U8* legacy(U32 owner,U32 id) noexcept {
 auto game=g.game?g.game():nullptr;if(!game||owner>=12||id>=61)return nullptr;
 return id<46?&game->upgrade_level_sc[owner][id]:&game->upgrade_level_bw[owner][id-46];
}
inline U8* slot(U32 owner,U32 id) noexcept {
 if(owner>=12||id>=61)return nullptr;
 if(g.extended||g.extended_count){
  if(!g.extended||!g.extended_count)return nullptr;
  const auto& array=g.extended[0];const auto begin=reinterpret_cast<std::uintptr_t>(array.pointer),end=reinterpret_cast<std::uintptr_t>(array.end);const auto offset=std::size_t(id)*12+owner;
  if(!begin||end<begin||offset>=end-begin)return nullptr;
  return array.pointer+offset;
 }
 return legacy(owner,id);
}
inline U32 level(U32 owner,U32 id) noexcept {const auto p=slot(owner,id);return p?*p:0;}
struct View {
 U8* native=nullptr;U8* compatibility=nullptr;U8 prior=0,prior_compatibility=0;
 View()=default;View(const View&)=delete;View& operator=(const View&)=delete;
 bool begin(U32 owner,U32 id,U8 value) noexcept {
  if(native)return false;auto target=slot(owner,id);if(!target)return false;
  native=target;compatibility=legacy(owner,id);prior=*native;
  if(compatibility&&compatibility!=native){prior_compatibility=*compatibility;*compatibility=value;}
  *native=value;return true;
 }
 void restore() noexcept {if(!native)return;*native=prior;if(compatibility&&compatibility!=native)*compatibility=prior_compatibility;native=compatibility=nullptr;}
 ~View(){restore();}
};
}
