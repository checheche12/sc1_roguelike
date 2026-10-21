#pragma once
// Move/Patrol/Hold already exist in the stock tank button set. Condition32
// calls IsSiegedTank for every selected unit and hides them even with CanMove.
// Replace only that UI call, preserving every engine use of IsSiegedTank.
namespace siege_move_ui {
inline std::atomic<U32> owner{12};
inline std::atomic<std::uintptr_t> units{0};inline std::atomic<std::size_t> count{0};
using Predicate=U32 (__cdecl*)(const bw::Unit*);
inline Predicate original_predicate=nullptr;
inline U8* module=nullptr,*code=nullptr;inline U8 branch[5]{},expected[14]{};inline bool queued=false;
inline constexpr U32 site=0x3e4d5b,predicate_rva=0x1c7ac0;
inline constexpr U8 original[]={0xe8,0x60,0x2d,0xde,0xff};
inline constexpr U8 predicate_bytes[]={0x0f,0xb7,0x81,0x8c,0x00,0x00,0x00,0x66,0x83,0xf8,0x1e,0x74,0x09,0x66,0x83,0xf8,0x19,0x74,0x03,0x33,0xc0,0xc3,0xb8,0x01,0x00,0x00,0x00,0xc3};
inline void reset() noexcept {owner.store(12,std::memory_order_release);units.store(0,std::memory_order_release);count.store(0,std::memory_order_release);}
inline void publish() noexcept {
 owner.store(12,std::memory_order_release);
 if(!g.active||!g.applied||!talent_power::enabled||!rework_catalog::rank(g.growth,55)||!g.units||g.units_count>65536)return;
 units.store(reinterpret_cast<std::uintptr_t>(g.units),std::memory_order_relaxed);count.store(g.units_count,std::memory_order_relaxed);owner.store(player_owner(),std::memory_order_release);
}
inline U32 __cdecl blocked(const bw::Unit* u) noexcept {
 const U32 own=owner.load(std::memory_order_acquire);const auto base=units.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(u);
 if(own<8&&base&&address>=base&&(address-base)%sizeof(bw::Unit)==0&&(address-base)/sizeof(bw::Unit)<count.load(std::memory_order_relaxed)){
  if(u->player==own&&!(u->flags&0x40000000u)&&(u->flags&0x20001u)==0x20001u&&u->flingy.hitpoints>0&&(u->unit_id==25||u->unit_id==30))return 0;
 }
 return original_predicate?original_predicate(u):1u;
}
inline bool verify_installation() noexcept {
 return queued&&module&&code&&native_engine_hooks::match(module+site,branch,5)&&native_engine_hooks::match(code,expected,14)&&native_engine_hooks::match(module+predicate_rva,predicate_bytes,sizeof(predicate_bytes));
}
inline bool register_at(U8* base,native_engine_hooks::WriteExeMemory writer) noexcept {
 if(queued)return module==base;
 if(code||!base||!writer||!native_engine_hooks::match(base+site,original,5)||!native_engine_hooks::match(base+predicate_rva,predicate_bytes,sizeof(predicate_bytes)))return false;
 auto relay=native_engine_hooks::nearby_code(base+site);if(!relay)return false;
 native_engine_hooks::absolute_jump(relay,reinterpret_cast<void*>(blocked));
 const auto delta=reinterpret_cast<std::intptr_t>(relay)-reinterpret_cast<std::intptr_t>(base+site+5);
 DWORD old=0;
 if(delta<INT32_MIN||delta>INT32_MAX||!VirtualProtect(relay,4096,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),relay,4096)){VirtualFree(relay,0,MEM_RELEASE);return false;}
 branch[0]=0xe8;const auto relative=std::int32_t(delta);std::memcpy(branch+1,&relative,4);
 if(!writer(reinterpret_cast<std::size_t>(base+site),branch,5)){VirtualFree(relay,0,MEM_RELEASE);return false;}
 module=base;code=relay;std::memcpy(expected,relay,14);original_predicate=reinterpret_cast<Predicate>(base+predicate_rva);queued=true;return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {return api&&api->write_exe_memory&&native_engine_hooks::verify_image()&&register_at(native_engine_hooks::verified_base,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));}
}
