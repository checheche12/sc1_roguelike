#pragma once
// Presentation-only correction for the pinned SAMASE weapon tooltip.
// The simulation's DAT arrays are never written by these callbacks.
namespace samase_weapon_ui {
#include "samase_weapon_specs.generated.h"
inline constexpr U32 base_rva=0x4443,bonus_rva=0x43c5,raw_rva=0xb2f23,factor_rva=0x1881bc,descriptor_rva=0x2aa570;
using RawRead=std::uint64_t (__cdecl*)(U32,U32);
using Factor=U32 (__cdecl*)(U32,U32);
inline U8* bound_base=nullptr;inline U8* code=nullptr;inline bool ready=false;
inline std::atomic<bool> activated{false};
inline RawRead raw_read=nullptr;inline Factor factor=nullptr;
inline std::array<RUNTIME_FUNCTION,3> unwind{};
inline std::array<U8,sizeof(base_original)> base_branch{};
inline std::array<U8,sizeof(bonus_original)> bonus_branch{};
inline const char* last_error="not_bound";
inline std::uint64_t __cdecl field_value(const bw::Unit* unit,U32 weapon,U32 field) noexcept {
    U32 value=0;
    if(activated.load(std::memory_order_acquire) && max_hp_cache::read_weapon(unit,field,weapon,value)){
        if(field==15)value=rework_combat_v5::infantry_ui_value(unit,weapon,value);
        return (std::uint64_t(value)<<32)|1u;
    }
    return raw_read ? raw_read(weapon,field):0;
}
inline U32 __cdecl base_value(const bw::Unit* unit,U32 weapon) noexcept {
    if(!unit || !factor)return 0;weapon&=0xffffu;
    // Preserve SAMASE's exact type-specific factor (Firebat/Zealot=2,
    // Valkyrie=1, otherwise weapons.dat factor), including its fallback.
    const U32 multiplier=factor(unit->unit_id,weapon);
    const auto raw=field_value(unit,weapon,14);if(!(raw&1u))return 0;
    const std::uint64_t product=(raw>>32)*multiplier;
    return rework_combat_v5::infantry_ui_value(unit,weapon,static_cast<U32>(std::min<std::uint64_t>(product,0xffffffffu)));
}
inline bool fail(const char* reason) noexcept {ready=false;activated.store(false,std::memory_order_release);last_error=reason;return false;}
inline bool witnesses(U8* base) noexcept {
    using native_engine_hooks::match;
    return base && match(base+raw_rva,raw_original,sizeof(raw_original)) &&
        match(base+factor_rva,factor_original,sizeof(factor_original)) &&
        match(base+0x4374,bonus_setup_original,sizeof(bonus_setup_original)) &&
        match(base+0x4480,base_continuation,sizeof(base_continuation)) &&
        match(base+0x43ca,bonus_math_original,sizeof(bonus_math_original));
}
inline bool write_code(U8* location,const U8* expected,const U8* replacement,std::size_t length) noexcept {
    using namespace native_engine_hooks;
    if(!match(location,expected,length))return false;
    DWORD previous=0;if(!protect_code_for_write(location,length,&previous))return false;
    std::memcpy(location,replacement,length);DWORD ignored=0;
    const bool restored=VirtualProtect(location,length,previous,&ignored)!=0;
    const bool flushed=FlushInstructionCache(GetCurrentProcess(),location,length)!=0;
    return restored && flushed;
}
inline bool branch(U8* output,std::size_t length,U8* site,U8* destination) noexcept {
    const auto delta=reinterpret_cast<std::intptr_t>(destination)-reinterpret_cast<std::intptr_t>(site+5);
    if(length<5 || delta<INT32_MIN || delta>INT32_MAX)return false;
    std::memset(output,0x90,length);output[0]=0xe8;const auto displacement=static_cast<std::int32_t>(delta);std::memcpy(output+1,&displacement,4);return true;
}
inline void dispose_code() noexcept {
    if(code){RtlDeleteFunctionTable(unwind.data());VirtualFree(code,0,MEM_RELEASE);}
    code=nullptr;raw_read=nullptr;factor=nullptr;bound_base=nullptr;ready=false;activated.store(false,std::memory_order_release);
}
inline bool make_code(U8* base) noexcept {
    code=native_engine_hooks::nearby_code(base+base_rva);if(!code)return fail("allocate");
    const auto put64=[](U8* out,std::uintptr_t value){std::memcpy(out,&value,8);};
    // Rust's Option<U32> is returned in EAX(valid), EDX(value). Pack it into
    // an ordinary Win64 U64 so C++ never relies on an unsupported Rust ABI.
    const U8 raw[]={0x48,0x83,0xec,0x28,0x41,0x89,0xd0,0x89,0xca,0x48,0xb9,0,0,0,0,0,0,0,0,
        0x48,0xb8,0,0,0,0,0,0,0,0,0xff,0xd0,0x48,0xc1,0xe2,0x20,0x89,0xc0,0x48,0x09,0xd0,0x48,0x83,0xc4,0x28,0xc3};
    std::memcpy(code,raw,sizeof(raw));put64(code+11,reinterpret_cast<std::uintptr_t>(base+descriptor_rva));put64(code+21,reinterpret_cast<std::uintptr_t>(base+raw_rva));
    // Replace exactly 4443..447f, ending before the original output store.
    // RBX is still the actual selected Unit here; original code afterwards
    // expects RBX=0 and R14=&weapons descriptor. Both are reproduced.
    const U8 base_stub[]={0x48,0x83,0xec,0x28,0x48,0x89,0xd9,0x89,0xfa,0x48,0xb8,0,0,0,0,0,0,0,0,
        0xff,0xd0,0x49,0xbe,0,0,0,0,0,0,0,0,0x89,0xc2,0x31,0xdb,0x48,0x83,0xc4,0x28,0xc3};
    std::memcpy(code+128,base_stub,sizeof(base_stub));put64(code+139,reinterpret_cast<std::uintptr_t>(&base_value));put64(code+151,reinterpret_cast<std::uintptr_t>(base+descriptor_rva));
    // Upgrade factor and level were already computed by SAMASE. Only replace
    // field15's read, restoring its exact EAX/EDX Option return convention.
    const U8 bonus_stub[]={0x48,0x83,0xec,0x28,0x48,0x89,0xd9,0x48,0xb8,0,0,0,0,0,0,0,0,
        0xff,0xd0,0x48,0x89,0xc2,0x48,0xc1,0xea,0x20,0x48,0x83,0xc4,0x28,0xc3};
    std::memcpy(code+256,bonus_stub,sizeof(bonus_stub));put64(code+265,reinterpret_cast<std::uintptr_t>(&field_value));
    const U8 unwind_bytes[]={1,4,1,0,4,0x42,0,0};std::memcpy(code+512,unwind_bytes,sizeof(unwind_bytes));
    unwind={RUNTIME_FUNCTION{0,static_cast<DWORD>(sizeof(raw)),512},RUNTIME_FUNCTION{128,128+static_cast<DWORD>(sizeof(base_stub)),512},RUNTIME_FUNCTION{256,256+static_cast<DWORD>(sizeof(bonus_stub)),512}};
    DWORD old=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),code,4096)){
        VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("executable_code");}
    if(!RtlAddFunctionTable(unwind.data(),static_cast<DWORD>(unwind.size()),reinterpret_cast<DWORD64>(code))){VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("unwind");}
    raw_read=reinterpret_cast<RawRead>(code);factor=reinterpret_cast<Factor>(base+factor_rva);return true;
}
inline bool verify_at(U8* base) noexcept {
    using native_engine_hooks::match;
    if(!base || base!=bound_base || !code || !raw_read || !factor)return fail("not_bound");
    if(!witnesses(base))return fail("witness_changed");
    if(!match(base+base_rva,base_branch.data(),base_branch.size()) || !match(base+bonus_rva,bonus_branch.data(),bonus_branch.size()))return fail("branch_changed");
    ready=true;activated.store(true,std::memory_order_release);last_error="verified";return true;
}
inline bool install_at(U8* base) noexcept {
    using native_engine_hooks::match;
    if(bound_base)return verify_at(base);
    if(!witnesses(base) || !match(base+base_rva,base_original,sizeof(base_original)) || !match(base+bonus_rva,bonus_original,sizeof(bonus_original)))return fail("original_mismatch");
    if(!make_code(base))return false;
    if(!branch(base_branch.data(),base_branch.size(),base+base_rva,code+128) || !branch(bonus_branch.data(),bonus_branch.size(),base+bonus_rva,code+256)){dispose_code();return fail("out_of_range");}
    const auto rollback=[&](const char* reason){
        activated.store(false,std::memory_order_release);
        if(match(base+bonus_rva,bonus_branch.data(),bonus_branch.size()))write_code(base+bonus_rva,bonus_branch.data(),bonus_original,bonus_branch.size());
        if(match(base+base_rva,base_branch.data(),base_branch.size()))write_code(base+base_rva,base_branch.data(),base_original,base_branch.size());
        // If restoring protection/flushing failed, free only after both sites
        // are demonstrably original. Otherwise keep executable passthroughs.
        if(match(base+base_rva,base_original,sizeof(base_original)) && match(base+bonus_rva,bonus_original,sizeof(bonus_original)))dispose_code();
        else bound_base=base;
        return fail(reason);
    };
    if(!write_code(base+base_rva,base_original,base_branch.data(),base_branch.size()))return rollback("base_write");
    if(!write_code(base+bonus_rva,bonus_original,bonus_branch.data(),bonus_branch.size()))return rollback("bonus_write");
    bound_base=base;if(!verify_at(base))return rollback("post_write_verification");return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {
    if(!samase_status_ui::verify_module(api))return fail("module_verification");
    return install_at(samase_status_ui::module_base());
}
inline bool verify_installation() noexcept {return verify_at(samase_status_ui::module_base());}
}
