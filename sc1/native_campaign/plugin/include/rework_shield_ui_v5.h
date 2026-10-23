#pragma once
// Presentation-only shield armor113. The simulation publishes stable research
// outside DamageScope; rendering never sees temporary damage-scope research.
namespace rework_shield_ui_v5 {
using Native=U32 (__cdecl*)(const bw::Unit*);
inline Native original=nullptr;
inline std::atomic<std::uint64_t> sequence{0};
inline std::atomic<bool> enabled{false},activated{false};
inline std::atomic<std::uintptr_t> array_base{0};
inline std::atomic<std::size_t> array_count{0};
inline std::atomic<U32> owner{12},base_level{0};
inline std::atomic<U32> bonus_level{0};
inline std::array<std::atomic<bool>,228> beneficiary{};
inline void reset() noexcept {
 enabled.store(false,std::memory_order_release);sequence.fetch_add(1,std::memory_order_acq_rel);
 array_base.store(0,std::memory_order_relaxed);array_count.store(0,std::memory_order_relaxed);owner.store(12,std::memory_order_relaxed);bonus_level.store(0,std::memory_order_relaxed);
 sequence.fetch_add(1,std::memory_order_release);
}
inline bool publish(bool=false) noexcept {
 if(!g.active||!g.applied||!g.units||g.units_count>max_hp_cache::capacity||!rework_catalog::rank(g.growth,113)){reset();return false;}
 auto native=rework_upgrade_storage::slot(player_owner(),15);if(!native){reset();return false;}
 // Research refresh is one atomic store, not a temporarily invalid cache. A
 // render fallback during a per-frame odd epoch could otherwise race the next
 // DamageScope and observe its transient bonus. Rebind at a map/array boundary.
 if(enabled.load(std::memory_order_acquire)&&array_base.load(std::memory_order_relaxed)==reinterpret_cast<std::uintptr_t>(g.units)&&array_count.load(std::memory_order_relaxed)==g.units_count&&owner.load(std::memory_order_relaxed)==player_owner()){
  base_level.store(*native,std::memory_order_release);bonus_level.store(rework_combat_v5::shield_armor_bonus(),std::memory_order_release);return true;
 }
 sequence.fetch_add(1,std::memory_order_acq_rel);
 array_base.store(reinterpret_cast<std::uintptr_t>(g.units),std::memory_order_relaxed);array_count.store(g.units_count,std::memory_order_relaxed);
 owner.store(player_owner(),std::memory_order_relaxed);base_level.store(*native,std::memory_order_relaxed);
 bonus_level.store(rework_combat_v5::shield_armor_bonus(),std::memory_order_relaxed);
 for(U32 id=0;id<228;id++)beneficiary[id].store(rework_combat_v5::soldier(id)&&rework_combat_v5::race_type(id,2),std::memory_order_relaxed);
 sequence.fetch_add(1,std::memory_order_release);enabled.store(true,std::memory_order_release);return true;
}
inline bool cached(const bw::Unit* unit,U32& value) noexcept {
 if(!unit||!enabled.load(std::memory_order_acquire))return false;
 const auto before=sequence.load(std::memory_order_acquire);if(before&1)return false;
 const auto base=array_base.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(unit),count=array_count.load(std::memory_order_relaxed);
 if(address<base||(address-base)%sizeof(bw::Unit)||(address-base)/sizeof(bw::Unit)>=count)return false;
 const U32 key=max_hp_cache::identity(unit),id=key&0xffffu,player=(key>>16)&255u;
 if(id>=228||player!=owner.load(std::memory_order_relaxed))return false;
 const auto illusion=unit->flags&0x40000000u;
 const U32 bonus=!illusion&&beneficiary[id].load(std::memory_order_relaxed)?bonus_level.load(std::memory_order_acquire):0u;
 const U32 result=std::min(255u,base_level.load(std::memory_order_acquire)+bonus);
 if(sequence.load(std::memory_order_acquire)!=before||!enabled.load(std::memory_order_acquire)||max_hp_cache::identity(unit)!=key||(unit->flags&0x40000000u)!=illusion)return false;
 value=result;return true;
}
inline U32 __cdecl value(const bw::Unit* unit) noexcept {
 U32 result=0;
 if(activated.load(std::memory_order_acquire)&&cached(unit,result))return result;
 return unit&&original ? original(unit)&255u:0;
}
inline constexpr U32 call_rva=0x3f323e,getter_rva=0x1c80b0;
inline constexpr U8 call_original[]={0xe8,0x6d,0x4e,0xdd,0xff};
inline constexpr U8 selected_original[]={0x48,0x8b,0x0d,0x1a,0x12,0xcb,0x00};
inline constexpr U8 result_original[]={0x0f,0xb6,0xf8,0xba,0x0b,0x03,0x00,0x00};
inline constexpr U8 getter_original[]={0x0f,0xb6,0x49,0x68,0xba,0x0f,0,0,0,0xe9,0x82,0xcc,0x20,0};
inline constexpr U8 formatter_original[]={0x40,0x84,0xff,0x4c,0x0f,0x45,0xc1,0x89,0x7c,0x24,0x30,0x33,0xf6,0x48,0x89,0x74,0x24,0x28,0x48,0x89,0x5c,0x24,0x20,0xba,0x80,0,0,0,0x48,0x8d,0x4d,0xc0,0xe8,0x01,0xea,0x1e,0x00};
inline constexpr U8 unwind_bytes[]={1,7,2,0,7,1,0x19,0};
inline U8* image=nullptr,*code=nullptr;
inline U8 branch[5]{};inline std::vector<U8> expected_code;
inline RUNTIME_FUNCTION runtime{};
inline bool queued=false;inline const char* last_error="not_bound";
inline bool fail(const char* reason) noexcept {activated.store(false,std::memory_order_release);last_error=reason;return false;}
inline bool witnesses(U8* base) noexcept {
 using native_engine_hooks::match;
 return base&&match(base+0x3f3237,selected_original,sizeof(selected_original))&&match(base+0x3f3243,result_original,sizeof(result_original))&&match(base+getter_rva,getter_original,sizeof(getter_original))&&match(base+0x3f328a,formatter_original,sizeof(formatter_original));
}
inline void dispose() noexcept { // Synthetic host teardown only; production hooks live for the process.
 reset();activated.store(false,std::memory_order_release);
 if(code){RtlDeleteFunctionTable(&runtime);VirtualFree(code,0,MEM_RELEASE);}
 code=image=nullptr;original=nullptr;queued=false;expected_code.clear();
}
inline bool register_at(U8* base,native_engine_hooks::WriteExeMemory writer) noexcept {
 if(queued)return base==image;
 if(code||!base||!writer||!witnesses(base)||!native_engine_hooks::match(base+call_rva,call_original,5))return fail("original_or_api_mismatch");
 auto allocation=native_engine_hooks::nearby_code(base+call_rva);if(!allocation)return fail("allocate");
 std::vector<U8> stub={0x48,0x81,0xec,0xc8,0,0,0};
 const U8 save[]={0x48,0x89,0x4c,0x24,0x20,0x48,0x89,0x54,0x24,0x28,0x4c,0x89,0x44,0x24,0x30,0x4c,0x89,0x4c,0x24,0x38,0x4c,0x89,0x54,0x24,0x40,0x4c,0x89,0x5c,0x24,0x48};
 stub.insert(stub.end(),save,save+sizeof(save));
 const auto xmm=[&](bool load){for(U8 n=0;n<6;n++){const U32 offset=0x50+16*n;stub.insert(stub.end(),{0xf3,0x0f,U8(load?0x6f:0x7f),U8((offset<128?0x44:0x84)+(n<<3)),0x24,U8(offset)});if(offset>=128)stub.insert(stub.end(),{0,0,0});}};
 xmm(false);stub.insert(stub.end(),{0x48,0xb8});const auto callback=reinterpret_cast<std::uintptr_t>(value);const auto bytes=reinterpret_cast<const U8*>(&callback);stub.insert(stub.end(),bytes,bytes+8);stub.insert(stub.end(),{0xff,0xd0});xmm(true);
 const U8 restore[]={0x48,0x8b,0x4c,0x24,0x20,0x48,0x8b,0x54,0x24,0x28,0x4c,0x8b,0x44,0x24,0x30,0x4c,0x8b,0x4c,0x24,0x38,0x4c,0x8b,0x54,0x24,0x40,0x4c,0x8b,0x5c,0x24,0x48,0x48,0x81,0xc4,0xc8,0,0,0,0xc3};stub.insert(stub.end(),restore,restore+sizeof(restore));
 std::memcpy(allocation,stub.data(),stub.size());std::memcpy(allocation+512,unwind_bytes,sizeof(unwind_bytes));
 runtime={0,static_cast<DWORD>(stub.size()),512};DWORD old=0;
 if(!VirtualProtect(allocation,4096,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),allocation,4096)){VirtualFree(allocation,0,MEM_RELEASE);return fail("executable_code");}
 if(!RtlAddFunctionTable(&runtime,1,reinterpret_cast<DWORD64>(allocation))){VirtualFree(allocation,0,MEM_RELEASE);return fail("unwind");}
 if(!samase_weapon_ui::branch(branch,5,base+call_rva,allocation)){RtlDeleteFunctionTable(&runtime);VirtualFree(allocation,0,MEM_RELEASE);return fail("out_of_range");}
 original=reinterpret_cast<Native>(base+getter_rva);code=allocation;expected_code=stub;
 if(!writer(reinterpret_cast<std::size_t>(base+call_rva),branch,5)){dispose();return fail("registration_rejected");}
 image=base;queued=true;last_error="registered_waiting_for_loader";return true;
}
inline bool verify_at(U8* base) noexcept {
 using native_engine_hooks::match;
 if(!queued||base!=image||!code||!original||!witnesses(base)||!match(base+call_rva,branch,5)||!match(code,expected_code.data(),expected_code.size())||!match(code+512,unwind_bytes,sizeof(unwind_bytes)))return fail("registered_site_changed");
 activated.store(true,std::memory_order_release);last_error="verified";return true;
}
inline bool verify_installation() noexcept {return verify_at(native_engine_hooks::verified_base);}
inline bool bind(const samase::PluginApi* api) noexcept {
 if(!api||!api->write_exe_memory||!native_engine_hooks::verify_image())return fail("api_or_image_pin");
 return register_at(native_engine_hooks::verified_base,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));
}
}
