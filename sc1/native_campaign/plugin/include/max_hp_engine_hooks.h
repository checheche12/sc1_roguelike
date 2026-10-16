#pragma once
// 13515 native maximum-health queries, including both UI and simulation.
// All patches are queued through SAMASE during initialization. Readers use
// published atomic values and never change process-global DAT for drawing.
#include "native_engine_hooks.h"
namespace max_hp_engine {
using Query=std::int32_t (__cdecl*)(const bw::Unit*);
inline Query originals[5]{};
inline native_engine_hooks::Hook hooks[5];
inline bool ready=false;
inline std::int32_t display(U32 maximum,const bw::Unit* u,bool modified=false) noexcept {
    // Native current HP is rounded up. Fractional growth (35 -> 38.5) must
    // display 39/39 at full health while retaining exactly 38.5 simulation HP.
    if(modified && maximum)return static_cast<std::int32_t>((std::uint64_t(maximum)+255u)/256u);
    const auto points=static_cast<std::int32_t>(maximum)>>8;
    if(points)return points;
    const auto current=static_cast<std::int32_t>(static_cast<U32>(u->flingy.hitpoints)+255u)>>8;
    return current ? current:1;
}
inline std::int32_t __cdecl q8(const bw::Unit* u) noexcept {
    U32 value=0;return max_hp_cache::read(u,value) ? static_cast<std::int32_t>(value):originals[0](u);
}
inline std::int32_t __cdecl points(const bw::Unit* u) noexcept {
    U32 value=0,original=0;return max_hp_cache::read(u,value,&original) ? display(value,u,value!=original):originals[1](u);
}
inline std::int32_t __cdecl third(const bw::Unit* u) noexcept {
    U32 value=0;return max_hp_cache::read(u,value) ? static_cast<std::int32_t>(value)/3:originals[2](u);
}
inline std::int32_t __cdecl damaged(const bw::Unit* u) noexcept {
    U32 value=0;return max_hp_cache::read(u,value) ? (u->flingy.hitpoints<static_cast<std::int32_t>(value) ? 1:0):originals[3](u);
}
inline std::int32_t __cdecl hp_shields(const bw::Unit* u) noexcept {
    U32 value=0,shields=0,original=0;
    if(!max_hp_cache::read_display(u,value,shields,&original))return originals[4](u);
    return display(value,u,value!=original)+static_cast<std::int32_t>(shields);
}
inline constexpr U8 leaf_unwind[]={1,0,0,0};
inline constexpr U8 stack40_unwind[]={1,4,1,0,4,0x42,0,0};
inline constexpr U8 rbx_stack32_unwind[]={1,6,2,0,6,0x32,2,0x30};
struct Entry {
    native_engine_hooks::Spec spec;
    std::size_t displacement;
    Query callback;
};
// Exact bytes and callers come from the preserved, hash-pinned engine dump.
#include "max_hp_engine_specs.generated.h"
#include "max_hp_dat_relocation.h"
using AddHp=void (__cdecl*)(bw::Unit*,std::int32_t);
inline AddHp original_add=nullptr;
inline native_engine_hooks::Hook add_hook;
inline void __cdecl add_hp(bw::Unit* unit,std::int32_t amount) noexcept {
    // Medic, repair and Zerg regeneration share this helper, which reads DAT
    // directly. Its target's owner and elite instance must determine the cap.
    OwnerDatScope scope(unit_owner(unit),unit_owner(unit),unit);
    original_add(unit,amount);
}
inline bool register_at(U8* base,const Entry& entry,native_engine_hooks::Hook& hook,native_engine_hooks::WriteExeMemory writer) noexcept {
    using namespace native_engine_hooks;
    const auto& spec=entry.spec;
    if(hook.queued || hook.installed)return true;
    if(!base || !writer || !entry.callback || !valid_spec(spec) || entry.displacement<3 ||
       entry.displacement>spec.stolen-4 || entry.displacement+4!=spec.stolen ||
       (spec.prologue[entry.displacement-3]!=0x48 && spec.prologue[entry.displacement-3]!=0x4c) ||
       spec.prologue[entry.displacement-2]!=0x8d || (spec.prologue[entry.displacement-1]&0xc7)!=5)
        return install_failed("hp_invalid_arguments");
    if(!match(base+spec.rva,spec.prologue,spec.stolen)){
        for(std::size_t n=0;n<spec.stolen;n++)if(base[spec.rva+n]!=spec.prologue[n])
            log_event("Maximum-health prologue mismatch: rva=%zx offset=%zu expected=%02x actual=%02x",static_cast<std::size_t>(spec.rva),n,spec.prologue[n],base[spec.rva+n]);
        return install_failed("hp_prologue_mismatch");
    }
    for(std::size_t n=0;n<spec.witness_count;n++){
        const auto& witness=spec.witnesses[n];
        if(witness.rva>=kImageSize || witness.length>kImageSize-witness.rva || !match(base+witness.rva,witness.expected,witness.length)){
            log_event("Maximum-health witness mismatch: function=%zx witness=%zx bytes=%zu",static_cast<std::size_t>(spec.rva),static_cast<std::size_t>(witness.rva),witness.length);
            return install_failed("hp_witness_mismatch");
        }
    }
    // Each stolen prefix has exactly one verified RIP-relative LEA. Allocate
    // within rel32 reach, then relocate its displacement before making RX.
    auto code=nearby_code(base+spec.rva);
    if(!code)return install_failed("hp_allocate_trampoline",true);
    std::memcpy(code,spec.prologue,spec.stolen);
    std::int32_t previous=0;std::memcpy(&previous,code+entry.displacement,4);
    const auto target=reinterpret_cast<std::intptr_t>(base+spec.rva+entry.displacement+4)+previous;
    const auto delta=target-reinterpret_cast<std::intptr_t>(code+entry.displacement+4);
    if(delta<INT32_MIN || delta>INT32_MAX){VirtualFree(code,0,MEM_RELEASE);return install_failed("hp_relocation_out_of_range");}
    const auto relocated=static_cast<std::int32_t>(delta);std::memcpy(code+entry.displacement,&relocated,4);
    continuation_jump(code+spec.stolen,base+spec.rva+spec.stolen);
    std::memcpy(code+128,spec.unwind,spec.unwind_size);
    hook.runtime={0,static_cast<DWORD>(spec.stolen+continuation_jump_size),128};DWORD old=0;
    if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old)){install_failed("hp_protect_trampoline",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    if(!FlushInstructionCache(GetCurrentProcess(),code,spec.stolen+continuation_jump_size)){install_failed("hp_flush_trampoline",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    if(!RtlAddFunctionTable(&hook.runtime,1,reinterpret_cast<DWORD64>(code))){install_failed("hp_register_unwind");VirtualFree(code,0,MEM_RELEASE);return false;}
    U8 branch[48];std::memset(branch,0x90,sizeof(branch));absolute_jump(branch,reinterpret_cast<void*>(entry.callback));
    if(!writer(reinterpret_cast<std::size_t>(base+spec.rva),branch,spec.stolen)){
        install_failed("hp_registration_rejected");RtlDeleteFunctionTable(&hook.runtime);VirtualFree(code,0,MEM_RELEASE);return false;
    }
    hook.allocation=code;hook.trampoline=code;hook.queued=true;last_install={"hp_registered_waiting_for_loader",0,false};return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {
    if(!api || !api->write_exe_memory || !native_engine_hooks::verify_image())return false;
    if(!hooks[0].queued){
        image_dat_getter=api->extended_dat ? reinterpret_cast<GetDat>(api->extended_dat(6)):nullptr;
        if(!prepare_runtime_specs(native_engine_hooks::verified_base))return false;
    }
    for(std::size_t i=0;i<std::size(runtime_entries);i++){
        if(!register_at(native_engine_hooks::verified_base,runtime_entries[i],hooks[i],reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory)))return false;
        originals[i]=reinterpret_cast<Query>(hooks[i].trampoline);
    }
    if(!native_engine_hooks::register_hook(runtime_add_spec,reinterpret_cast<void*>(add_hp),add_hook,
        reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory)))return false;
    original_add=reinterpret_cast<AddHp>(add_hook.trampoline);return true;
}
inline bool verify_installation() noexcept {
    ready=false;
    for(std::size_t i=0;i<std::size(runtime_entries);i++){
        const auto& spec=runtime_entries[i].spec;
        if(!native_engine_hooks::verify_registered(spec,reinterpret_cast<void*>(runtime_entries[i].callback),hooks[i]))return false;
        for(std::size_t n=0;n<spec.witness_count;n++){
            const auto& w=spec.witnesses[n];
            if(!native_engine_hooks::match(native_engine_hooks::verified_base+w.rva,w.expected,w.length))
                return native_engine_hooks::install_failed("hp_registered_remainder_changed");
        }
    }
    if(!native_engine_hooks::verify_registered(runtime_add_spec,reinterpret_cast<void*>(add_hp),add_hook))return false;
    for(const auto& w:runtime_add_witnesses)
        if(!native_engine_hooks::match(native_engine_hooks::verified_base+w.rva,w.expected,w.length))
            return native_engine_hooks::install_failed("hp_add_remainder_changed");
    ready=true;return true;
}
}
