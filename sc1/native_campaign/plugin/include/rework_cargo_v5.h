#pragma once
#include "rework_upgrade_storage.h"
// Include sight_cargo_runtime.h globally; this native adapter belongs inside
// native_plugin.cpp after owner_stat/OwnerDatScope and before order hooks.
namespace rework_cargo_v5 {
using Adapter=::sc1::sight_cargo::CargoAdapter;
using Selection=void* (__cdecl*)();
inline Adapter cargo;
inline bw::Unit* bound_units=nullptr;inline std::size_t bound_count=0;
inline Selection selection_source=nullptr;
inline U32 lifecycle_depth=0;
using UnloadAll=void (__cdecl*)(bw::Unit*);
using Detach=void (__cdecl*)(bw::Unit*,U32);
inline UnloadAll native_unload_all=nullptr;
inline Detach native_detach=nullptr;
inline constexpr U8 unload_bytes[]={0x41,0x56,0x48,0x83,0xec,0x60,0x4c,0x8b,0xf1,0xe8,0x02,0x51,0xfe,0xff,0x85,0xc0};
inline constexpr U8 detach_bytes[]={0x40,0x57,0x41,0x54,0x48,0x83,0xec,0x38,0x44,0x8b,0xe2,0x48,0x8b,0xf9,0xe8,0x8d,0x5b,0xfe,0xff};
inline constexpr U8 detach_call[]={0x33,0xd2,0x48,0x8b,0xcb,0xe8,0x5d,0xf2,0xff,0xff};
inline bool native_bytes(U8* base) noexcept {
 return base && native_engine_hooks::match(base+0x1e1e60,unload_bytes,sizeof(unload_bytes)) &&
 native_engine_hooks::match(base+0x1e1250,detach_bytes,sizeof(detach_bytes)) && native_engine_hooks::match(base+0x1e1fe9,detach_call,sizeof(detach_call));
}
inline bool bind_native() noexcept {
 if(!native_engine_hooks::verify_image() || !native_bytes(native_engine_hooks::verified_base))return false;
 native_unload_all=reinterpret_cast<UnloadAll>(native_engine_hooks::verified_base+0x1e1e60);
 native_detach=reinterpret_cast<Detach>(native_engine_hooks::verified_base+0x1e1250);return true;
}
inline unsigned space(const bw::Unit* u) {return valid_unit(u) && u->unit_id<228?std::min(8u,original_stat({0,47,u->unit_id})):0u;}
inline unsigned capacity(const bw::Unit* u) {
 if(!valid_unit(u) || u->unit_id>=228 || (u->flags&0x40000000u))return 8;
 // Current transport cards grant speed only. Legacy overflow can still unload.
 if(talent_power::enabled&&(u->unit_id==11||u->unit_id==42||u->unit_id==57||u->unit_id==69))return 8;
 U32 value=std::max(8u,std::min(talent_power::enabled?16u:12u,owner_stat(u->player,{0,48,u->unit_id})));
 if(!g.active || !g.applied || u->player!=player_owner())return value;
 if(u->unit_id==11 && rework_catalog::rank(g.growth,33))return 16;
 if((u->unit_id==42 || u->unit_id==57) && rework_catalog::rank(g.growth,74)){
  // The talent adds room, never the original transport research. The original
  // native boarding path retains its own race/tech/order checks as well.
  return rework_upgrade_storage::level(u->player,24)?(talent_power::enabled?16u:12u):8u;
 }
 if(u->unit_id==69 && rework_catalog::rank(g.growth,115))return talent_power::enabled?16u:12u;
 return value;
}
inline bool bind() noexcept {
 if(!g.units || !g.units_count)refresh_units();
 if(!g.units || !g.units_count || g.units_count>8191)return false;
 if(bound_units==g.units && bound_count==g.units_count)return true;
 if(!cargo.bind(g.units,g.units_count,capacity,space))return false;
 bound_units=g.units;bound_count=g.units_count;return true;
}
inline void reset() noexcept {cargo.reset();bound_units=nullptr;bound_count=0;lifecycle_depth=0;}
struct OrderScope {
 Adapter::Token token{};
 explicit OrderScope(bw::Unit* u) noexcept {if(g.active && bind())token=cargo.before_order(u);}
 bool allow_original() const noexcept {return !token.boarding_denied;}
 ~OrderScope(){cargo.after_order(token);}
};
struct CommandScope {
 bool active=false;
 CommandScope(const void* data,U32 length) noexcept {
  if(!g.active || !bind())return;active=true;cargo.before_commands();
  if(!data || (length!=3 && length!=5))return;
  const auto bytes=static_cast<const U8*>(data);if(bytes[0]!=0x29)return;
  // Native UnloadUnit contains a generation-tagged lookup handle. Support the
  // documented legacy16-bit and SCR extended32-bit command representations.
  U32 handle=0;std::memcpy(&handle,bytes+1,length-1);if(handle && handle<=0x3ffffu)cargo.present_passenger(handle);
 }
 ~CommandScope(){if(active)cargo.after_commands();}
};
inline bool transport_lifecycle(const bw::Unit* carrier) noexcept {
 // Only these transports use paged windows. Bunkers are explicitly ejected.
 // Do not require positive HP: lethal damage may already have set it to zero.
 return valid_unit(carrier) && (carrier->unit_id==11 || carrier->unit_id==42 || carrier->unit_id==57 || carrier->unit_id==69);
}
template<class Callback> inline void before_death(bw::Unit* carrier,Callback callback) {
 if(g.active && valid_unit(carrier) && carrier->unit_id==125 && !lifecycle_depth && bind() && native_unload_all && native_detach){
  const auto before=cargo.count(carrier);U32 forced=0;
  ++lifecycle_depth;native_unload_all(carrier);
  // Timers, disables and blocked terrain can reject stock UnloadAll. Only
  // detach passengers resolved from the physical, generation-tagged slots.
  ::sc1::sight_cargo::PackedWindow window{};
  std::memcpy(window.low.data(),carrier->loaded_units,sizeof(carrier->loaded_units));window.high=carrier->scr_carried_unit_high_bits;
  const U32 slots=std::min(8u,original_stat({0,48,125}));
  for(U32 i=0;i<slots;i++)if(auto p=cargo.resolve(::sc1::sight_cargo::unpack_slot(window,i))){
   if(p->related!=carrier || !(p->flags&0x40u))continue;
   const auto center=carrier->flingy.position;bw::Point placed=center;
   if(rework_relocation::native_move && rework_relocation::native_place){
    rework_relocation::native_move(p,U32(center.x),U32(center.y));
    bw::Point candidate{};if(rework_relocation::native_place(p,&center,&candidate,nullptr,0,0))placed=candidate;
    rework_relocation::native_move(p,U32(placed.x),U32(placed.y));
   }
   // Native ShowUnit/list/collision/packed-handle cleanup preserves the same
   // unit, HP and energy. It never spawns replacement occupants.
   native_detach(p,0);
   if(!p->related)++forced;
   if(g.order && !p->related)g.order(p,1,U32(placed.x),U32(placed.y),nullptr,228);
  }
  log_event("Bunker ejection: owner=%u unit=%u generation=%u occupants=%zu forced=%u remaining=%zu hp_q8=%d",U32(carrier->player),U32(carrier-g.units),U32(carrier->minor_unique_index),before,forced,cargo.count(carrier),carrier->flingy.hitpoints);
  --lifecycle_depth;return;
 }
 if(!g.active || !transport_lifecycle(carrier) || !bind() || lifecycle_depth || !cargo.count(carrier))return;
 ++lifecycle_depth;cargo.for_each_passenger(carrier,[&](bw::Unit* p){callback(p);});cargo.hide_window(carrier);--lifecycle_depth;
}
template<class Callback> inline void before_give(bw::Unit* carrier,U32 next_owner,Callback callback) {
 if(!g.active || !transport_lifecycle(carrier) || next_owner==carrier->player || !bind() || lifecycle_depth || !cargo.count(carrier))return;
 ++lifecycle_depth;cargo.for_each_passenger(carrier,[&](bw::Unit* p){callback(p,next_owner);});cargo.hide_window(carrier);--lifecycle_depth;
}
inline void step() noexcept {if(g.active && bind())cargo.refresh();}
inline bw::Unit* selected() noexcept {
 if(!g.active || !selection_source || !bind() || GetCurrentThreadId()!=g.game_thread.load())return nullptr;
 auto source=selection_source();if(!source)return nullptr;
 std::array<bw::Unit*,12> list{};SIZE_T got=0;if(!ReadProcessMemory(GetCurrentProcess(),source,list.data(),sizeof(list),&got) || got!=sizeof(list))return nullptr;
 bw::Unit* result=nullptr;for(auto u:list){if(!u)continue;if(!valid_unit(u) || u->player!=player_owner() || !u->order || u->flingy.hitpoints<=0 || (u->flags&0x40000000u) || result)return nullptr;result=u;}
 return result;
}
inline bool status(void*,std::uint64_t* token,U32* page,U32* pages,U32* passengers) noexcept {
 if(!token || !page || !pages || !passengers)return false;*token=0;*page=0;*pages=1;*passengers=0;
 auto carrier=selected();if(!carrier)return false;const auto info=cargo.page_info(carrier);if(info.pages<2)return false;
 *token=(std::uint64_t(carrier->player)<<32)|cargo.identity(carrier);*page=info.page;*pages=info.pages;*passengers=info.passengers;return true;
}
inline bool toggle(void*,std::uint64_t token) noexcept {
 auto carrier=selected();if(!carrier || token!=((std::uint64_t(carrier->player)<<32)|cargo.identity(carrier)))return false;return cargo.toggle_page(carrier);
}
}
