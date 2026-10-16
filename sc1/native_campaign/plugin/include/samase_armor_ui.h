#pragma once
// SAMASE delegates armor tooltips to the original game's retained body.
// Its original trampoline returns to RVA3F2D10 (observed in the live loader).
// Only the base armor read is replaced; armor upgrade helper/formatting remain.
namespace samase_armor_ui {
#include "samase_armor_specs.generated.h"
using Getter=bw::DatTable* (__cdecl*)(std::size_t*);
inline constexpr U32 call_rva=0x3f33bd,skip_rva=0x3f33c5,raw_rva=0x3f33cc;
inline Getter units_getter=nullptr;inline U8* base=nullptr;inline U8* code=nullptr;
inline bool queued=false,ready=false;inline std::atomic<bool> activated{false};
inline RUNTIME_FUNCTION runtime{};
inline U8 call_branch[5]{},raw_before[9]{};
inline constexpr U8 skip_branch[]={0xe9,0x0b,0,0,0,0x90,0x90};
inline const char* last_error="not_bound";
inline bool fail(const char* reason) noexcept {ready=false;activated.store(false,std::memory_order_release);last_error=reason;return false;}
inline bool armor_table(bw::DatTable& table) noexcept {
    if(!units_getter)return false;std::size_t count=0;auto all=units_getter(&count);
    if(!all || count<=27 || !native_engine_hooks::read_exact(all+27,&table,sizeof(table)))return false;
    return table.data && table.entry_size==1 && table.entries>=228;
}
inline U32 fallback(U32 id) noexcept {
    bw::DatTable table{};if(!armor_table(table) || id>=table.entries)return 0;
    U8 value=0;return native_engine_hooks::read_exact(static_cast<const U8*>(table.data)+id,&value,1)?value:0;
}
inline std::uint64_t __cdecl armor_value(const bw::Unit* unit) noexcept {
    if(!unit)return 0;const U32 id=unit->unit_id;U32 value=0;
    if(!activated.load(std::memory_order_acquire) || !max_hp_cache::read_armor(unit,value))value=fallback(id);
    return (std::uint64_t(id)<<32)|(value&255u);
}
inline bool witnesses(U8* image) noexcept {
    using native_engine_hooks::match;
    return image && match(image+0x3f33a7,before_original,sizeof(before_original)) &&
        match(image+0x3f33c2,between_original,3) &&
        match(image+0x3f33d5,after_original,sizeof(after_original)) &&
        match(image+0x1c6280,id_original,sizeof(id_original));
}
inline bool normalized_raw(U8* image,U8* captured) noexcept {
    bw::DatTable table{};if(!armor_table(table) || !native_engine_hooks::read_exact(image+raw_rva,captured,9))return false;
    if(std::memcmp(captured,raw_stock,5)!=0)return false;
    std::int32_t displacement=0;std::memcpy(&displacement,captured+5,4);
    const auto expected=reinterpret_cast<std::uintptr_t>(table.data);
    const auto actual=reinterpret_cast<std::intptr_t>(image)+displacement;
    return actual>=0 && static_cast<std::uintptr_t>(actual)==expected;
}
inline void dispose() noexcept {
    if(code){RtlDeleteFunctionTable(&runtime);VirtualFree(code,0,MEM_RELEASE);}
    code=nullptr;base=nullptr;queued=false;ready=false;activated.store(false,std::memory_order_release);units_getter=nullptr;
}
inline bool register_at(U8* image,Getter getter,native_engine_hooks::WriteExeMemory writer) noexcept {
    if(queued)return image==base;
    if(code)return fail("registration_incomplete");
    if(!image || !getter || !writer)return fail("missing_api");
    units_getter=getter;
    if(!witnesses(image) || !native_engine_hooks::match(image+call_rva,call_original,5) || !native_engine_hooks::match(image+skip_rva,between_original+3,7) || !normalized_raw(image,raw_before))return fail("original_or_dat_mismatch");
    code=native_engine_hooks::nearby_code(image+call_rva);if(!code)return fail("allocate");
    // Return UnitId in AX and armor in EDI. The following original movzx
    // ECX,AX stays intact. The replacement JMP skips the raw armor read, while
    // R12 is set to the exact value of its displaced image-base LEA.
    // Leave the raw DAT instruction untouched so SAMASE may relocate it later.
    // Preserve volatile registers/XMM: the tiny original getter changed AX
    // only, and this shim must not introduce additional visible clobbers.
    const U8 stub[]={
        0x48,0x81,0xec,0xc8,0,0,0,
        0x48,0x89,0x54,0x24,0x20,0x4c,0x89,0x44,0x24,0x28,
        0x4c,0x89,0x4c,0x24,0x30,0x4c,0x89,0x54,0x24,0x38,0x4c,0x89,0x5c,0x24,0x40,
        0xf3,0x0f,0x7f,0x44,0x24,0x50,0xf3,0x0f,0x7f,0x4c,0x24,0x60,
        0xf3,0x0f,0x7f,0x54,0x24,0x70,0xf3,0x0f,0x7f,0x9c,0x24,0x80,0,0,0,
        0xf3,0x0f,0x7f,0xa4,0x24,0x90,0,0,0,0xf3,0x0f,0x7f,0xac,0x24,0xa0,0,0,0,
        0x48,0xb8,0,0,0,0,0,0,0,0,0xff,0xd0,
        0x89,0xc7,0x48,0xc1,0xe8,0x20,0x49,0xbc,0,0,0,0,0,0,0,0,
        0xf3,0x0f,0x6f,0x44,0x24,0x50,0xf3,0x0f,0x6f,0x4c,0x24,0x60,
        0xf3,0x0f,0x6f,0x54,0x24,0x70,0xf3,0x0f,0x6f,0x9c,0x24,0x80,0,0,0,
        0xf3,0x0f,0x6f,0xa4,0x24,0x90,0,0,0,0xf3,0x0f,0x6f,0xac,0x24,0xa0,0,0,0,
        0x48,0x8b,0x54,0x24,0x20,0x4c,0x8b,0x44,0x24,0x28,
        0x4c,0x8b,0x4c,0x24,0x30,0x4c,0x8b,0x54,0x24,0x38,0x4c,0x8b,0x5c,0x24,0x40,
        0x48,0x81,0xc4,0xc8,0,0,0,0xc3};
    std::memcpy(code,stub,sizeof(stub));
    const auto callback=reinterpret_cast<std::uintptr_t>(&armor_value),image_address=reinterpret_cast<std::uintptr_t>(image);
    for(std::size_t i=0;i+10<=sizeof(stub);i++){
        if(stub[i]==0x48 && stub[i+1]==0xb8)std::memcpy(code+i+2,&callback,8);
        if(stub[i]==0x49 && stub[i+1]==0xbc)std::memcpy(code+i+2,&image_address,8);
    }
    const U8 unwind[]={1,7,2,0,7,1,0x19,0};std::memcpy(code+512,unwind,sizeof(unwind));runtime={0,static_cast<DWORD>(sizeof(stub)),512};
    DWORD previous=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&previous) || !FlushInstructionCache(GetCurrentProcess(),code,4096)){
        VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("executable_code");}
    if(!RtlAddFunctionTable(&runtime,1,reinterpret_cast<DWORD64>(code))){VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("unwind");}
    if(!samase_weapon_ui::branch(call_branch,sizeof(call_branch),image+call_rva,code)){dispose();return fail("out_of_range");}
    // Register the call before its paired JMP. On a second-write rejection the
    // retained raw read overwrites EDI, yielding the original safe display.
    if(!writer(reinterpret_cast<std::size_t>(image+call_rva),call_branch,5)){dispose();return fail("call_registration_rejected");}
    base=image;
    if(!writer(reinterpret_cast<std::size_t>(image+skip_rva),skip_branch,7))return fail("skip_registration_rejected");
    queued=true;last_error="registered_waiting_for_loader";return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {
    if(!api || !api->extended_dat || !api->write_exe_memory || !native_engine_hooks::verify_image())return fail("missing_api_or_image");
    const auto getter=reinterpret_cast<Getter>(api->extended_dat(0));
    return register_at(native_engine_hooks::verified_base,getter,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));
}
inline bool verify_at(U8* image) noexcept {
    using native_engine_hooks::match;
    if(!queued || !base || image!=base || !code || !units_getter)return fail("not_registered");
    if(!witnesses(image) || !match(image+call_rva,call_branch,5) || !match(image+skip_rva,skip_branch,7))return fail("registered_site_changed");
    U8 relocated_raw[9]{};if(!normalized_raw(image,relocated_raw))return fail("armor_table_or_relocation_unavailable");
    ready=true;activated.store(true,std::memory_order_release);last_error="verified";return true;
}
inline bool verify_installation() noexcept {return verify_at(native_engine_hooks::verified_base);}
}
