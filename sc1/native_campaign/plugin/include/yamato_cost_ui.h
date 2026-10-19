#pragma once
// Exact native energy-tooltip store. Read-only published owner/talent state;
// native techdata owner views perform the real precheck and energy deduction.
namespace yamato_cost_ui {
inline std::atomic<U32> owner{12};
inline std::atomic<std::uintptr_t> units{0};inline std::atomic<std::size_t> count{0};
inline U8* module=nullptr,*code=nullptr;inline U8 branch[8]{},expected[128]{};
inline std::size_t size=0;inline RUNTIME_FUNCTION unwind{};inline bool queued=false;
inline constexpr U32 site=0x3ee113,output=0x10a37b8;
inline constexpr U8 original[]={0x66,0x44,0x89,0x0d,0x9d,0x56,0xcb,0x00};
inline void reset() noexcept {owner.store(12,std::memory_order_release);units.store(0,std::memory_order_release);count.store(0,std::memory_order_release);}
inline void publish() noexcept {
 owner.store(12,std::memory_order_release);
 if(!g.active || !g.applied || !talent_power::enabled || !rework_catalog::rank(g.growth,64) || !g.units || g.units_count>65536)return;
 units.store(reinterpret_cast<std::uintptr_t>(g.units),std::memory_order_relaxed);count.store(g.units_count,std::memory_order_relaxed);owner.store(player_owner(),std::memory_order_release);
}
inline U32 value(const bw::Unit* u,U32 tech,U32 fallback) noexcept {
 const U32 own=owner.load(std::memory_order_acquire);const auto base=units.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(u);
 if(tech!=8 || own>=8 || !base || address<base || (address-base)%sizeof(bw::Unit) || (address-base)/sizeof(bw::Unit)>=count.load(std::memory_order_relaxed))return fallback;
 return u->player==own && !(u->flags&0x40000000u) ? 50u:150u;
}
inline void __cdecl store(U32 tech,U32 energy) noexcept {
 const bw::Unit* selected=nullptr;
 if(module){native_engine_hooks::read_exact(module+0x10a4458,&selected,sizeof(selected));const auto result=std::uint16_t(value(selected,tech,energy));std::memcpy(module+output,&result,2);}
}
inline bool verify_installation() noexcept {
 return queued && module && code && native_engine_hooks::match(module+site,branch,8) && native_engine_hooks::match(code,expected,size) && native_engine_hooks::match(code+1024,rework_economy_ui::relay_unwind,sizeof(rework_economy_ui::relay_unwind));
}
inline bool register_at(U8* base,native_engine_hooks::WriteExeMemory writer) noexcept {
 if(queued)return module==base;
 if(code || !base || !writer || !native_engine_hooks::match(base+site,original,8))return false;
 code=native_engine_hooks::nearby_code(base+site);if(!code)return false;module=base;std::size_t n=0;
 const auto put=[&](std::initializer_list<U8> bytes){for(auto b:bytes)code[n++]=b;};
 put({0x9c,0x50,0x51,0x52,0x41,0x50,0x41,0x51,0x41,0x52,0x41,0x53,0x48,0x83,0xec,0x28});
 // BX = native tech ID, R9W = original energy. Preserve every volatile GPR.
 put({0x0f,0xb7,0xcb,0x44,0x89,0xca,0x48,0xb8});const auto callback=reinterpret_cast<std::uintptr_t>(store);std::memcpy(code+n,&callback,8);n+=8;put({0xff,0xd0});
 put({0x48,0x83,0xc4,0x28,0x41,0x5b,0x41,0x5a,0x41,0x59,0x41,0x58,0x5a,0x59,0x58,0x9d,0xc3});size=n;std::memcpy(expected,code,n);
 std::memcpy(code+1024,rework_economy_ui::relay_unwind,sizeof(rework_economy_ui::relay_unwind));unwind={0,DWORD(n),1024};
 const auto delta=reinterpret_cast<std::intptr_t>(code)-reinterpret_cast<std::intptr_t>(base+site+5);
 if(delta<INT32_MIN || delta>INT32_MAX)return false;
 std::memset(branch,0x90,8);branch[0]=0xe8;const auto relative=std::int32_t(delta);std::memcpy(branch+1,&relative,4);
 DWORD old=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),code,4096) || !RtlAddFunctionTable(&unwind,1,reinterpret_cast<DWORD64>(code)))return false;
 queued=true;return writer(reinterpret_cast<std::size_t>(base+site),branch,8)!=0;
}
inline bool bind(const samase::PluginApi* api) noexcept {return api && api->write_exe_memory && native_engine_hooks::verify_image() && register_at(native_engine_hooks::verified_base,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));}
}
