#pragma once
namespace host_test {
namespace targeting_bridge_tests {
inline std::uintptr_t observed_target=0;
inline U32 __cdecl original_tech(bw::Unit*,U32,bw::Unit* target,U32,U32,U32,std::uint16_t*){return valid_unit(target)?1u:0u;}
inline U32 __cdecl observe(bw::Unit* u,U32 tech,bw::Unit* target,U32 fow,U32 x,U32 y,std::uint16_t* error,rework_combat_v5::TechTargetFn original){observed_target=reinterpret_cast<std::uintptr_t>(target);return original(u,tech,target,fow,x,y,error);}
inline void actual_loader_dispatch_reproduces_pointer_loss(){
 reset();auto caster=add(9,6,100,100),target=add(0,6,120,100);const auto pointer=reinterpret_cast<std::uintptr_t>(target);CHECK(pointer>0xffffffffu);
 // Exact SAMASE 0.10.28 x64 dispatch7 bytes, RVA BD37..BD7F. The dump's
 // Func24 descriptor uses FFFF for target; Func25 uses full pointer width.
 const U8 code[]={0x48,0x83,0xec,0x48,0x0f,0x28,0x84,0x24,0x80,0,0,0,0x48,0x8b,0x84,0x24,0x90,0,0,0,0x48,0x23,0x50,0x08,0x4c,0x23,0x40,0x10,0x4c,0x23,0x48,0x18,0x4c,0x8b,0x50,0x20,0x4c,0x8b,0x58,0x28,0x4c,0x23,0x54,0x24,0x70,0x4c,0x23,0x5c,0x24,0x78,0x0f,0x11,0x44,0x24,0x30,0x4c,0x89,0x5c,0x24,0x28,0x4c,0x89,0x54,0x24,0x20,0xff,0x10,0x90,0x48,0x83,0xc4,0x48,0xc3};
 auto executable=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(executable);std::memcpy(executable,code,sizeof(code));CHECK(FlushInstructionCache(GetCurrentProcess(),executable,sizeof(code)));
 struct Descriptor {std::uintptr_t function;std::uint64_t masks[5];};
 Descriptor descriptor{reinterpret_cast<std::uintptr_t>(observe),{0xffff,0xffff,0xffff,0xffff,0xffff}};
 using Dispatch=U32 (__cdecl*)(bw::Unit*,U32,bw::Unit*,U32,U32,U32,std::uint16_t*,rework_combat_v5::TechTargetFn,const Descriptor*);
 auto invoke=reinterpret_cast<Dispatch>(executable);std::uint16_t error=0;
 CHECK(!invoke(caster,6,target,228,100,100,&error,original_tech,&descriptor));CHECK(observed_target==(pointer&0xffffu)&&observed_target!=pointer);
 descriptor.masks[1]=0xffffffffffffffffull;
 CHECK(invoke(caster,6,target,228,100,100,&error,original_tech,&descriptor));CHECK(observed_target==pointer);
 CHECK(VirtualFree(executable,0,MEM_RELEASE));
}
inline std::vector<U32> registered;
inline U32 __cdecl hook(std::uint16_t id,std::uintptr_t callback){registered.push_back(id);if(id==25)CHECK(callback==reinterpret_cast<std::uintptr_t>(rework_combat_v5::order_target_hook));CHECK(id!=24);return 1;}
inline GenericFn __cdecl get(std::uint16_t){return reinterpret_cast<GenericFn>(original_tech);}
inline void __cdecl load(const std::uint16_t*,U8* values,std::size_t length){for(std::size_t i=0;i<length;i++)values[i]=3;}
inline void __cdecl read_vars(const std::uint16_t*,std::size_t*,std::size_t){}
inline void __cdecl write_vars(const std::uint16_t*,const std::size_t*,std::size_t){}
inline void registration_avoids_broken_func24_entirely(){
 reset();registered.clear();samase::PluginApi provider{};provider.hook_func=reinterpret_cast<GenericFn>(hook);provider.get_func=get;
 provider.load_vars=load;provider.read_vars=read_vars;provider.write_vars=reinterpret_cast<GenericFn>(write_vars);
 auto saved_kill=rework_combat_v5::native_kill;auto saved_give=rework_combat_v5::native_give;auto saved_read=rework_combat_v5::script_context_read;auto saved_write=rework_combat_v5::script_context_write;
 CHECK(rework_combat_v5::bind_engine(&provider));CHECK(registered.size()==6&&std::count(registered.begin(),registered.end(),25u)==1&&std::count(registered.begin(),registered.end(),24u)==0);
 rework_combat_v5::native_kill=saved_kill;rework_combat_v5::native_give=saved_give;rework_combat_v5::script_context_read=saved_read;rework_combat_v5::script_context_write=saved_write;
}
inline bw::Unit* expected_target=nullptr;
inline U32 __cdecl order_original(bw::Unit*,U32,bw::Unit* target,U32,U32,std::uint16_t*){CHECK(target==expected_target);return valid_unit(target)?1u:0u;}
inline void ordinary_enemy_matrix_keeps_target_pointer(){
 rework_wave_tests::begin(105);auto vessel=add(9,6,100,100),marine=add(0,6,120,100);expected_target=marine;std::uint16_t error=0;
 const auto before=*marine;CHECK(rework_combat_v5::order_target_hook(vessel,141,marine,120,100,&error,order_original));CHECK(std::memcmp(marine,&before,sizeof(before))==0);
}
}
inline constexpr std::size_t targeting_bridge_group_count=3;
inline void run_targeting_bridge_groups(){targeting_bridge_tests::actual_loader_dispatch_reproduces_pointer_loss();targeting_bridge_tests::registration_avoids_broken_func24_entirely();targeting_bridge_tests::ordinary_enemy_matrix_keeps_target_pointer();}
}
