#pragma once
// Carrier's native Interceptor tooltip bypasses the generic SAMASE weapon
// tooltip: native13515 formatter3f2d00 calls weapon79's original getters.
// Replace only those two presentation calls; never write simulation DAT.
namespace carrier_weapon_ui {
using Native=U32 (__cdecl*)(const bw::Unit*,U32);
inline Native original_base=nullptr,original_bonus=nullptr;
inline std::atomic<bool> activated{false};
inline U8* image=nullptr,*code=nullptr;inline bool queued=false;
inline const char* last_error="not_bound";
inline constexpr U32 sites[]={0x3f2f21,0x3f2f10},getters[]={0x1b8770,0x1b86d0};
inline constexpr U8 calls[][5]={{0xe8,0x4a,0x58,0xdc,0xff},{0xe8,0xbb,0x57,0xdc,0xff}};
inline constexpr U8 base_result[]={0x0f,0xb7,0xf8,0xba,0x09,0x03,0,0},bonus_result[]={0x0f,0xb7,0xf0};
inline constexpr U8 base_getter[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20};
inline constexpr U8 bonus_getter[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x48,0x89,0x7c,0x24,0x20};
inline constexpr U8 unwind_bytes[]={1,7,2,0,7,1,0x19,0};
inline std::array<RUNTIME_FUNCTION,2> unwind{};
inline std::array<std::array<U8,5>,2> branches{};
inline std::array<std::vector<U8>,2> expected_code;
inline bool subject(const bw::Unit* unit,U32 weapon) noexcept {
 return unit&&(unit->unit_id==72||unit->unit_id==82)&&(weapon&255u)==79;
}
inline U32 __cdecl base_value(const bw::Unit* unit,U32 weapon) noexcept {
 weapon&=255u;U32 value=0;
 if(activated.load(std::memory_order_acquire)&&subject(unit,weapon)&&max_hp_cache::read_weapon(unit,14,weapon,value))
  return rework_combat_v5::infantry_ui_value(unit,weapon,value);
 return unit&&original_base?original_base(unit,weapon):0;
}
inline U32 __cdecl bonus_value(const bw::Unit* unit,U32 weapon) noexcept {
 weapon&=255u;const U32 native=unit&&original_bonus?original_bonus(unit,weapon):0;U32 value=0;
 if(!activated.load(std::memory_order_acquire)||!subject(unit,weapon)||!max_hp_cache::read_weapon(unit,15,weapon,value))return native;
 const U32 baseline=max_hp_cache::original_weapon_values[130+79].load(std::memory_order_relaxed);
 // Preserve the original native research level and display factor, including
 // extended upgrade storage. Weapon79's pinned baseline bonus is one.
 if(!baseline)return native;
 value=rework_combat_v5::infantry_ui_value(unit,weapon,value);
 return U32(std::min<std::uint64_t>(65535u,std::uint64_t(native)*value/baseline));
}
inline bool fail(const char* reason) noexcept {activated.store(false,std::memory_order_release);last_error=reason;return false;}
inline bool witnesses(U8* base) noexcept {
 using native_engine_hooks::match;
 return base&&match(base+sites[0]+5,base_result,sizeof(base_result))&&match(base+sites[1]+5,bonus_result,sizeof(bonus_result))&&
  match(base+getters[0],base_getter,sizeof(base_getter))&&match(base+getters[1],bonus_getter,sizeof(bonus_getter));
}
inline std::vector<U8> relay(Native callback){
 std::vector<U8> stub={0x48,0x81,0xec,0xc8,0,0,0};
 const U8 save[]={0x48,0x89,0x4c,0x24,0x20,0x48,0x89,0x54,0x24,0x28,0x4c,0x89,0x44,0x24,0x30,0x4c,0x89,0x4c,0x24,0x38,0x4c,0x89,0x54,0x24,0x40,0x4c,0x89,0x5c,0x24,0x48};
 stub.insert(stub.end(),save,save+sizeof(save));
 const auto xmm=[&](bool load){for(U8 n=0;n<6;n++){const U32 offset=0x50+16*n;stub.insert(stub.end(),{0xf3,0x0f,U8(load?0x6f:0x7f),U8((offset<128?0x44:0x84)+(n<<3)),0x24,U8(offset)});if(offset>=128)stub.insert(stub.end(),{0,0,0});}};
 xmm(false);stub.insert(stub.end(),{0x48,0xb8});const auto address=reinterpret_cast<std::uintptr_t>(callback);const auto bytes=reinterpret_cast<const U8*>(&address);stub.insert(stub.end(),bytes,bytes+8);stub.insert(stub.end(),{0xff,0xd0});xmm(true);
 const U8 restore[]={0x48,0x8b,0x4c,0x24,0x20,0x48,0x8b,0x54,0x24,0x28,0x4c,0x8b,0x44,0x24,0x30,0x4c,0x8b,0x4c,0x24,0x38,0x4c,0x8b,0x54,0x24,0x40,0x4c,0x8b,0x5c,0x24,0x48,0x48,0x81,0xc4,0xc8,0,0,0,0xc3};
 stub.insert(stub.end(),restore,restore+sizeof(restore));return stub;
}
inline void dispose() noexcept { // Isolated host teardown; production lives with the process.
 activated.store(false,std::memory_order_release);
 if(code){RtlDeleteFunctionTable(unwind.data());VirtualFree(code,0,MEM_RELEASE);}
 code=image=nullptr;original_base=original_bonus=nullptr;queued=false;for(auto& s:expected_code)s.clear();
}
inline bool register_at(U8* base,native_engine_hooks::WriteExeMemory writer) noexcept {
 using native_engine_hooks::match;
 if(queued)return image==base;
 if(code||!base||!writer||!witnesses(base)||!match(base+sites[0],calls[0],5)||!match(base+sites[1],calls[1],5))return fail("original_or_api_mismatch");
 auto allocation=native_engine_hooks::nearby_code(base+sites[0]);if(!allocation)return fail("allocate");
 const Native callbacks[]={base_value,bonus_value};
 for(U32 i=0;i<2;i++){
  auto bytes=relay(callbacks[i]);std::memcpy(allocation+i*512,bytes.data(),bytes.size());expected_code[i]=bytes;
  std::memcpy(allocation+1024+i*16,unwind_bytes,sizeof(unwind_bytes));unwind[i]={i*512,DWORD(i*512+bytes.size()),1024+i*16};
  if(!samase_weapon_ui::branch(branches[i].data(),5,base+sites[i],allocation+i*512)){VirtualFree(allocation,0,MEM_RELEASE);return fail("out_of_range");}
 }
 DWORD old=0;if(!VirtualProtect(allocation,4096,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),allocation,4096)){VirtualFree(allocation,0,MEM_RELEASE);return fail("executable_code");}
 if(!RtlAddFunctionTable(unwind.data(),2,reinterpret_cast<DWORD64>(allocation))){VirtualFree(allocation,0,MEM_RELEASE);return fail("unwind");}
 code=allocation;image=base;original_base=reinterpret_cast<Native>(base+getters[0]);original_bonus=reinterpret_cast<Native>(base+getters[1]);
 // Keep both executable passthroughs if a loader rejects the second request:
 // it may have already accepted the first branch. Activation remains false.
 queued=true;
 for(U32 i=0;i<2;i++)if(!writer(reinterpret_cast<std::size_t>(base+sites[i]),branches[i].data(),5))return fail("registration_rejected");
 last_error="registered_waiting_for_loader";return true;
}
inline bool verify_at(U8* base) noexcept {
 using native_engine_hooks::match;
 if(!queued||base!=image||!code||!witnesses(base))return fail("registered_witness_changed");
 for(U32 i=0;i<2;i++)if(!match(base+sites[i],branches[i].data(),5)||!match(code+i*512,expected_code[i].data(),expected_code[i].size())||!match(code+1024+i*16,unwind_bytes,sizeof(unwind_bytes)))return fail("registered_site_changed");
 activated.store(true,std::memory_order_release);last_error="verified";return true;
}
inline bool verify_installation() noexcept {return verify_at(native_engine_hooks::verified_base);}
inline bool bind(const samase::PluginApi* api) noexcept {
 return api&&api->write_exe_memory&&native_engine_hooks::verify_image()&&register_at(native_engine_hooks::verified_base,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));
}
}
