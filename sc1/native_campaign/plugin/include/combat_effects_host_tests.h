#pragma once
// Synthetic callback-contract regressions, not an installed-engine execution.
// A modeled native shield split calls the real lower production damage hook.
namespace host_test { namespace combat_audit {
inline U32 calls=0,seen_weapon=0,seen_divisor=0,seen_direction=0,seen_player=0;
inline std::int32_t seen_amount=0;inline bw::Unit* seen_attacker=nullptr;
inline bool seen_wrapped=false;inline U32 armor=0;
inline void __cdecl native_split(bw::Unit* target,std::int32_t amount,U8 weapon,U32 divisor,U8 direction,bw::Unit* attacker,U32 player){
    ++calls;seen_amount=amount;seen_weapon=weapon;seen_divisor=divisor;seen_direction=direction;seen_attacker=attacker;seen_player=player;seen_wrapped=combat_effects::weapon_damage_active();
    // Test fixture's split preserves shielding and subtracts fixture armor;
    // it deliberately does not claim to reimplement all StarCraft damage rules.
    auto remaining=std::max(0,amount/static_cast<int>(std::max(1u,divisor))-static_cast<int>(armor));
    const auto shield=std::min(remaining,std::max(0,target->shields));target->shields-=shield;remaining-=shield;
    owner_damage_hook(target,remaining,attacker,player,1,fake_damage);
}
inline void __cdecl hit_to_weapon(bw::Unit* target,bw::Bullet* bullet,U32 divisor){
    combat_effects::weapon_damage(target,static_cast<int>(raw_value(1,14,bullet->weapon_id)*256),bullet->weapon_id,divisor,91,bullet->parent,bullet->player,native_split);
}
inline void start(const GrowthSnapshot& s){reset();calls=armor=0;seen_wrapped=false;CHECK(apply_snapshot(nullptr,s));}
inline void melee(bw::Unit* source,bw::Unit* target,std::int32_t amount,U32 divisor=1){
    source->order_target.unit=target;combat_effects::melee_enter(source);
    const auto weapon=original_stat({0,17,source->unit_id});
    combat_effects::weapon_damage(target,amount,static_cast<U8>(weapon),divisor,37,source,source->player,native_split);
    combat_effects::melee_leave(source);
}
inline void barrier_before_shield_and_hp(){
    for(int shield:{20*256,2*256,0}){
        GrowthSnapshot s{};s.curse_counts[8]=1;start(s);auto target=curse_audit::wave(65,6);auto source=add(0,1,100,100);refresh_units();target->shields=shield;const auto hp=target->flingy.hitpoints;
        bw::SpriteScr sprite{};source->flingy.sprite=&sprite;
        auto bullet=owner_bullet_create_hook(0,100,100,1,0,source,curse_audit::bullet);owner_hit_hook(target,bullet,1,hit_to_weapon);
        CHECK(calls==1 && seen_wrapped);CHECK(seen_amount==1152);CHECK(hp-target->flingy.hitpoints+shield-target->shields==1152);CHECK(seen_direction==91 && seen_weapon==0 && seen_divisor==1 && seen_attacker==source && seen_player==1);
        CHECK(!combat_effects::weapon_damage_active());CHECK(!g.normal_hit);
    }
}
inline void melee_elite_and_lifesteal(){
    GrowthSnapshot s{};s.curse_counts[7]=s.curse_counts[11]=1;start(s);auto source=curse_audit::wave(37,6);auto target=add(0,1,100,100,10000);refresh_units();source->flingy.hitpoints=1000;const auto hp=target->flingy.hitpoints;
    melee(source,target,5*256);CHECK(calls==1 && seen_wrapped);CHECK(seen_amount==6*256);CHECK(hp-target->flingy.hitpoints==6*256);CHECK(source->flingy.hitpoints==1153);CHECK(!g.normal_hit && !g.elite_hit && !g.hit_source);CHECK(combat_effects::melee_depth==0);
}
inline void charge_and_multihit_bundle(){
    GrowthSnapshot s{};s.curse_counts[9]=1;start(s);game.frame_count=1;auto source=add(37,6,500,500,1000);auto target=add(0,1,100,100,10000);refresh_units();track_unit(source);source->ground_cooldown=8;game.frame_count=200;
    melee(source,target,5*256);CHECK(seen_amount==1536);CHECK(existing_track(source)->cooldown[0].launched);game.frame_count=201;melee(source,target,5*256);CHECK(seen_amount==1536);game.frame_count=209;melee(source,target,5*256);CHECK(seen_amount==1280);CHECK(calls==3);
}
inline void armor_and_lifesteal_actual_hp(){
    GrowthSnapshot s{};s.curse_counts[7]=s.curse_counts[11]=1;start(s);auto source=curse_audit::wave(37,6);auto target=add(0,1,100,100,10000);refresh_units();source->flingy.hitpoints=1000;target->shields=400;armor=200;
    melee(source,target,2000,2);CHECK(seen_amount==2400 && seen_divisor==2 && seen_direction==37);CHECK(target->shields==0);CHECK(target->flingy.hitpoints==9400);CHECK(source->flingy.hitpoints==1060);CHECK(calls==1);
}
inline void melee_owner_dat_and_restore(){
    GrowthSnapshot s{};s.talent_bits[49/32]|=1u<<(49%32);start(s);auto source=add(37,1,500,500,1000);auto target=add(0,6,100,100,10000);refresh_units();source->order_target.unit=target;const auto stock=raw_value(1,14,35);
    combat_effects::melee_enter(source);CHECK(raw_value(1,14,35)==stock+1);CHECK(g.hit_source==source && g.normal_hit);combat_effects::melee_leave(source);CHECK(raw_value(1,14,35)==stock);CHECK(!g.normal_hit);
    source->player=6;target->player=1;combat_effects::melee_enter(source);CHECK(raw_value(1,14,35)==stock);combat_effects::melee_leave(source);CHECK(raw_value(1,14,35)==stock);
}
inline void spell_hallucination_and_direct_exclusion(){
    GrowthSnapshot s{};s.curse_counts[7]=s.curse_counts[9]=s.curse_counts[11]=1;start(s);auto source=curse_audit::wave(37,6);auto target=add(0,1,100,100,10000);refresh_units();source->flingy.hitpoints=1000;
    combat_effects::weapon_damage(target,1000,35,1,37,source,6,native_split);CHECK(seen_amount==1000 && source->flingy.hitpoints==1000);
    source->flags|=0x40000000u;melee(source,target,1000);CHECK(seen_amount==1000 && source->flingy.hitpoints==1000);CHECK(!g.normal_hit);source->flags&=~0x40000000u;
    source->order_target.unit=target;combat_effects::melee_enter(source);combat_effects::weapon_damage(target,1000,84,1,37,source,6,native_split);combat_effects::melee_leave(source);CHECK(seen_amount==1000 && source->flingy.hitpoints==1000);CHECK(calls==3);
}
inline void nested_scope_reset_and_invalid_target(){
    GrowthSnapshot s{};s.curse_counts[9]=1;start(s);auto source=add(37,6,500,500,1000);auto target=add(0,1,100,100,10000);refresh_units();combat_effects::melee_enter(source);CHECK(!g.normal_hit && !combat_effects::melee_source());combat_effects::melee_leave(source);
    source->order_target.unit=target;combat_effects::melee_enter(source);CHECK(g.normal_hit && combat_effects::melee_source()==source);combat_effects::melee_enter(nullptr);CHECK(!combat_effects::melee_source());combat_effects::melee_leave(nullptr);CHECK(combat_effects::melee_source()==source);combat_effects::melee_leave(target);CHECK(!g.normal_hit && combat_effects::melee_depth==0);
    for(int i=0;i<35;i++)combat_effects::melee_enter(source);CHECK(combat_effects::melee_depth==32 && combat_effects::overflow_depth==3);combat_effects::reset_melee();CHECK(!g.normal_hit && combat_effects::melee_depth==0 && combat_effects::overflow_depth==0);
}

inline native_engine_hooks::Hook* executing_hook=nullptr;inline U32 detour_calls=0;
inline int __cdecl synthetic_detour(bw::Unit* unit){++detour_calls;return reinterpret_cast<int (__cdecl*)(bw::Unit*)>(executing_hook->trampoline)(unit)+1;}
inline int __cdecl synthetic_call_detour(){++detour_calls;return reinterpret_cast<int (__cdecl*)()>(executing_hook->trampoline)()+5;}
inline void trampoline_real_execution_and_guards(){
    using namespace native_engine_hooks;
    CHECK(!verify_image()); // host EXE must never pass the game's file pin.
    auto base=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(base);
    std::memcpy(base+128,combat_effects::weapon_prologue,14);
    const U8 tail[]={0xb8,42,0,0,0,0x48,0x83,0xc4,0x38,0x41,0x5d,0x5f,0x5d,0x5b,0xc3};std::memcpy(base+142,tail,sizeof(tail));
    DWORD old=0;CHECK(VirtualProtect(base,4096,PAGE_EXECUTE_READ,&old)!=0);
    Spec spec{128,combat_effects::weapon_prologue,14,combat_effects::weapon_unwind,16,nullptr,0};Hook hook{};
    U8 wrong[14];std::memcpy(wrong,combat_effects::weapon_prologue,14);wrong[0]^=1;auto bad=spec;bad.prologue=wrong;CHECK(!install_at(base,bad,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(!hook.installed && !hook.allocation);
    CHECK(install_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook));executing_hook=&hook;detour_calls=0;bw::Unit target{};
    CHECK(reinterpret_cast<int (__cdecl*)(bw::Unit*)>(base+128)(&target)==43);CHECK(detour_calls==1);
    DWORD64 image=0;CHECK(RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(hook.trampoline),&image,nullptr)==&hook.runtime);CHECK(image==reinterpret_cast<DWORD64>(hook.trampoline));
    CHECK(RtlDeleteFunctionTable(&hook.runtime)!=0);VirtualFree(hook.allocation,0,MEM_RELEASE);VirtualFree(base,0,MEM_RELEASE);executing_hook=nullptr;
}
inline void near_call_relay_real_execution_and_guards(){
    using namespace native_engine_hooks;
    auto base=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(base);
    const U8 code[]={0x48,0x83,0xec,0x28,0xe8,0x77,0,0,0,0x48,0x83,0xc4,0x28,0xc3};std::memcpy(base+128,code,sizeof(code));const U8 target[]={0xb8,37,0,0,0,0xc3};std::memcpy(base+256,target,sizeof(target));
    DWORD old=0;CHECK(VirtualProtect(base,4096,PAGE_EXECUTE_READ,&old)!=0);CHECK(reinterpret_cast<int (__cdecl*)()>(base+128)()==37);
    const U8 call[]={0xe8,0x77,0,0,0};CallSpec spec{{132,call,5},256};Hook hook{};auto wrong=spec;wrong.original_rva=257;CHECK(!install_call_at(base,wrong,reinterpret_cast<void*>(synthetic_call_detour),hook));CHECK(!hook.installed);
    CHECK(install_call_at(base,spec,reinterpret_cast<void*>(synthetic_call_detour),hook));executing_hook=&hook;detour_calls=0;CHECK(reinterpret_cast<int (__cdecl*)()>(base+128)()==42);CHECK(detour_calls==1);CHECK(hook.trampoline==base+256);
    CHECK(uninstall_call_at(base,spec,hook));CHECK(!hook.installed && !hook.allocation);CHECK(reinterpret_cast<int (__cdecl*)()>(base+128)()==37);VirtualFree(base,0,MEM_RELEASE);executing_hook=nullptr;
}
inline void exact_game_spec_installation(){
    using namespace native_engine_hooks;
    CHECK(valid_spec(combat_effects::weapon_spec));
    auto base=static_cast<U8*>(VirtualAlloc(nullptr,kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(base);
    const auto& spec=combat_effects::weapon_spec;
    std::memcpy(base+spec.rva,spec.prologue,spec.stolen);
    const U8 tail[]={0xb8,42,0,0,0,0x48,0x83,0xc4,0x38,0x41,0x5d,0x5f,0x5d,0x5b,0xc3};std::memcpy(base+spec.rva+spec.stolen,tail,sizeof(tail));
    for(std::size_t i=0;i<spec.witness_count;i++){const auto& w=spec.witnesses[i];std::memcpy(base+w.rva,w.expected,w.length);}
    Hook hook{};auto invalid=spec;invalid.stolen=13;CHECK(!install_at(base,invalid,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(std::strcmp(last_install.stage,"invalid_spec")==0);
    base[spec.witnesses[1].rva]^=1;CHECK(!install_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(std::strcmp(last_install.stage,"witness_mismatch")==0);base[spec.witnesses[1].rva]^=1;
    DWORD old=0;CHECK(VirtualProtect(base,kImageSize,PAGE_EXECUTE_READ,&old)!=0);
    CHECK(install_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(std::strcmp(last_install.stage,"installed")==0 && !last_install.error_valid);
    executing_hook=&hook;detour_calls=0;bw::Unit target{};CHECK(reinterpret_cast<int (__cdecl*)(bw::Unit*)>(base+spec.rva)(&target)==43);CHECK(detour_calls==1);
    DWORD64 image=0;CHECK(RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(hook.trampoline),&image,nullptr)==&hook.runtime);
    CHECK(RtlDeleteFunctionTable(&hook.runtime)!=0);VirtualFree(hook.allocation,0,MEM_RELEASE);VirtualFree(base,0,MEM_RELEASE);executing_hook=nullptr;
}
inline void mapped_read_execute_install_and_file_preservation(){
    using namespace native_engine_hooks;
    wchar_t directory[MAX_PATH]{},filename[MAX_PATH]{};CHECK(GetTempPathW(MAX_PATH,directory)!=0);CHECK(GetTempFileNameW(directory,L"sc1",0,filename)!=0);
    HANDLE file=CreateFileW(filename,GENERIC_READ|GENERIC_WRITE|GENERIC_EXECUTE,FILE_SHARE_READ,nullptr,CREATE_ALWAYS,FILE_ATTRIBUTE_TEMPORARY,nullptr);CHECK(file!=INVALID_HANDLE_VALUE);
    const auto& spec=combat_effects::weapon_spec;std::vector<U8> original(kImageSize);std::memcpy(original.data()+spec.rva,spec.prologue,spec.stolen);
    const U8 tail[]={0xb8,42,0,0,0,0x48,0x83,0xc4,0x38,0x41,0x5d,0x5f,0x5d,0x5b,0xc3};std::memcpy(original.data()+spec.rva+spec.stolen,tail,sizeof(tail));
    for(std::size_t i=0;i<spec.witness_count;i++){const auto& w=spec.witnesses[i];std::memcpy(original.data()+w.rva,w.expected,w.length);}
    // Also exercise the shared relative call and byte-patch paths in this map.
    const U8 caller[]={0x48,0x83,0xec,0x28,0xe8,0x77,0,0,0,0x48,0x83,0xc4,0x28,0xc3},callee[]={0xb8,37,0,0,0,0xc3};std::memcpy(original.data()+128,caller,sizeof(caller));std::memcpy(original.data()+256,callee,sizeof(callee));
    DWORD done=0;CHECK(WriteFile(file,original.data(),kImageSize,&done,nullptr)!=0 && done==kImageSize);
    HANDLE mapping=CreateFileMappingW(file,nullptr,PAGE_EXECUTE_READ,0,0,nullptr);CHECK(mapping);auto base=static_cast<U8*>(MapViewOfFile(mapping,FILE_MAP_READ|FILE_MAP_EXECUTE,0,0,0));CHECK(base);
    MEMORY_BASIC_INFORMATION region{};CHECK(VirtualQuery(base+spec.rva,&region,sizeof(region))==sizeof(region));CHECK(region.Type==MEM_MAPPED && region.Protect==PAGE_EXECUTE_READ);
    DWORD old=0;CHECK(VirtualProtect(base+spec.rva,spec.stolen,PAGE_EXECUTE_READWRITE,&old)==0);CHECK(GetLastError()==ERROR_INVALID_PARAMETER);
    Hook hook{};CHECK(install_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(std::strcmp(last_install.stage,"installed")==0);executing_hook=&hook;bw::Unit target{};CHECK(reinterpret_cast<int (__cdecl*)(bw::Unit*)>(base+spec.rva)(&target)==43);
    CHECK(VirtualQuery(base+spec.rva,&region,sizeof(region))==sizeof(region));CHECK(region.Protect==PAGE_EXECUTE_READ);CHECK(RtlDeleteFunctionTable(&hook.runtime)!=0);VirtualFree(hook.allocation,0,MEM_RELEASE);executing_hook=nullptr;
    const U8 call[]={0xe8,0x77,0,0,0};CallSpec call_spec{{132,call,5},256};Hook relay{};CHECK(install_call_at(base,call_spec,reinterpret_cast<void*>(synthetic_call_detour),relay));executing_hook=&relay;CHECK(reinterpret_cast<int (__cdecl*)()>(base+128)()==42);CHECK(uninstall_call_at(base,call_spec,relay));CHECK(reinterpret_cast<int (__cdecl*)()>(base+128)()==37);executing_hook=nullptr;
    const auto saved_base=verified_base;verified_base=base;const U8 changed[]={0xb8,39,0,0,0,0xc3};Patch patch{};CHECK(install_patch({256,callee,sizeof(callee)},changed,patch));CHECK(reinterpret_cast<int (__cdecl*)()>(base+256)()==39);CHECK(uninstall_patch(patch));CHECK(reinterpret_cast<int (__cdecl*)()>(base+256)()==37);verified_base=saved_base;
    CHECK(SetFilePointer(file,static_cast<LONG>(spec.rva),nullptr,FILE_BEGIN)==spec.rva);U8 disk[14]{};CHECK(ReadFile(file,disk,14,&done,nullptr)!=0 && done==14);CHECK(std::memcmp(disk,spec.prologue,14)==0);
    CHECK(SetFilePointer(file,128,nullptr,FILE_BEGIN)==128);U8 disk_call[sizeof(caller)]{};CHECK(ReadFile(file,disk_call,sizeof(caller),&done,nullptr)!=0 && done==sizeof(caller));CHECK(std::memcmp(disk_call,caller,sizeof(caller))==0);
    UnmapViewOfFile(base);CloseHandle(mapping);CloseHandle(file);CHECK(DeleteFileW(filename)!=0);
}
inline std::size_t registered_address=0,registered_size=0;inline U8 registered_bytes[48]{};inline bool reject_registration=false;
inline U32 __cdecl loader_register(std::size_t at,const U8* bytes,std::size_t size){
    if(reject_registration)return 0;registered_address=at;registered_size=size;std::memcpy(registered_bytes,bytes,size);return 1;
}
inline void registered_loader_write_requires_actual_branch(){
    using namespace native_engine_hooks;
    auto base=static_cast<U8*>(VirtualAlloc(nullptr,kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(base);const auto& spec=combat_effects::weapon_spec;
    std::memcpy(base+spec.rva,spec.prologue,spec.stolen);const U8 tail[]={0xb8,42,0,0,0,0x48,0x83,0xc4,0x38,0x41,0x5d,0x5f,0x5d,0x5b,0xc3};std::memcpy(base+spec.rva+spec.stolen,tail,sizeof(tail));
    for(std::size_t i=0;i<spec.witness_count;i++){const auto& w=spec.witnesses[i];std::memcpy(base+w.rva,w.expected,w.length);}DWORD old=0;CHECK(VirtualProtect(base,kImageSize,PAGE_EXECUTE_READ,&old)!=0);
    Hook hook{};registered_address=registered_size=0;reject_registration=true;CHECK(!register_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook,loader_register));CHECK(!hook.installed && !hook.queued && !hook.allocation);CHECK(std::strcmp(last_install.stage,"registration_api_rejected")==0);
    reject_registration=false;CHECK(register_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook,loader_register));CHECK(hook.queued && !hook.installed);CHECK(registered_address==reinterpret_cast<std::size_t>(base+spec.rva) && registered_size==spec.stolen);CHECK(match(base+spec.rva,spec.prologue,spec.stolen));
    CHECK(!verify_registered_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(!hook.installed);CHECK(std::strcmp(last_install.stage,"registered_branch_mismatch")==0);
    // Model only the loader's eventual byte application, using the registered
    // absolute address. The production first-file operation only reads it.
    CHECK(protect_code_for_write(base+spec.rva,spec.stolen,&old));std::memcpy(reinterpret_cast<void*>(registered_address),registered_bytes,registered_size);DWORD ignored=0;CHECK(VirtualProtect(base+spec.rva,spec.stolen,old,&ignored)!=0);CHECK(FlushInstructionCache(GetCurrentProcess(),base+spec.rva,spec.stolen)!=0);
    CHECK(!verify_registered_at(base,spec,reinterpret_cast<void*>(synthetic_call_detour),hook));CHECK(!hook.installed);CHECK(verify_registered_at(base,spec,reinterpret_cast<void*>(synthetic_detour),hook));CHECK(hook.installed && std::strcmp(last_install.stage,"installed_verified_after_loader")==0);
    executing_hook=&hook;bw::Unit unit{};CHECK(reinterpret_cast<int (__cdecl*)(bw::Unit*)>(base+spec.rva)(&unit)==43);executing_hook=nullptr;CHECK(RtlDeleteFunctionTable(&hook.runtime)!=0);VirtualFree(hook.allocation,0,MEM_RELEASE);VirtualFree(base,0,MEM_RELEASE);
}
struct Case {const char* name;void(*fn)();};inline const Case cases[]={
 {"barrier_before_shield_hp",barrier_before_shield_and_hp},{"melee_elite_lifesteal",melee_elite_and_lifesteal},{"charge_multihit",charge_and_multihit_bundle},{"armor_actual_hp",armor_and_lifesteal_actual_hp},{"owner_dat",melee_owner_dat_and_restore},{"spell_hallucination_direct",spell_hallucination_and_direct_exclusion},{"nested_reset_invalid",nested_scope_reset_and_invalid_target},{"trampoline_execution_guards",trampoline_real_execution_and_guards},{"near_call_execution_guards",near_call_relay_real_execution_and_guards},{"exact_game_spec_installation",exact_game_spec_installation},{"mapped_rx_execution_file_preservation",mapped_read_execute_install_and_file_preservation},{"registered_loader_write_actual_branch",registered_loader_write_requires_actual_branch}};
} inline void run_combat_effects_groups(){for(const auto& test:combat_audit::cases)test.fn();} }
