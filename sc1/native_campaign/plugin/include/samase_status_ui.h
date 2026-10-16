#pragma once
// SAMASE 0.10.28 replaces the status screen with its own Rust implementation.
// Patch its two HP reads and one maximum-shield read. No DAT value or selection is changed by drawing.
#include "native_engine_hooks.h"
namespace samase_status_ui {
inline constexpr char kSha256[]="6b0d6c1016e637ef433f962b9c4b06c091fef81c515ec9bf747158ffab599c3c";
inline constexpr DWORD kTimestamp=0x6a54152e,kImageSize=0x2bf000;
inline constexpr U32 kGetterRva=0xb3283;
inline constexpr std::size_t kSiteCount=3;
inline constexpr U32 kShieldGetterRva=0xb31c4;
inline constexpr U32 kSites[kSiteCount]={0x1b2d4c,0x1b2dac,0x1b2cf5};
inline constexpr U8 kCalls[kSiteCount][5]={{0xe8,0x32,0x05,0xf0,0xff},{0xe8,0xd2,0x04,0xf0,0xff},{0xe8,0xca,0x04,0xf0,0xff}};
inline constexpr U8 kShieldGetter[]={0x56,0x48,0x83,0xec,0x20,0x89,0xce,0xe8,0x5f,0xfe,0xff,0xff,0x89,0xc1,0x31,0xc0,0x84,0xc9};
inline constexpr U8 kShieldFormatter[]={0x4c,0x89,0xe9,0x89,0xda,0xe8,0xc2,0x2b,0,0};
inline constexpr U8 kSavedUnit[]={0x4c,0x89,0x7c,0x24,0x38};
inline constexpr U8 kFirstArgs[]={0x48,0x8b,0x44,0x24,0x38,0x0f,0xb7,0x88,0x8c,0,0,0};
inline constexpr U8 kSecondArgs[]={0x44,0x89,0xe1};
inline constexpr U8 kFormatter[]={0x4c,0x89,0xe9,0x89,0xea,0xe8,0x0b,0x2b,0,0};
inline constexpr U8 kGetter[]={0x0f,0xb7,0xc9,0x48,0x8b,0x15,0x83,0x73,0x1f,0,0x48,0x85,0xd2};
inline U8* verified_module=nullptr;
inline U8* relay_page=nullptr;
inline U8 installed_calls[kSiteCount][5]{};
inline U8 expected_relays[kSiteCount][21]{};
inline bool ready=false;
inline std::atomic<bool> passthrough_only{false};
inline std::atomic<U32> logged_queries{0};
using OriginalMaximum=U32 (__cdecl*)(U32);
inline OriginalMaximum original_maximum=nullptr;
inline OriginalMaximum original_shields=nullptr;
inline U8* module_base() noexcept {return verified_module;}
inline bool hash_module(HMODULE module) noexcept {
    wchar_t path[32768];const auto length=GetModuleFileNameW(module,path,32768);if(!length || length>=32768)return false;
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);if(file==INVALID_HANDLE_VALUE)return false;
    auto library=LoadLibraryExW(L"bcrypt.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!library){CloseHandle(file);return false;}
    auto open=reinterpret_cast<decltype(&BCryptOpenAlgorithmProvider)>(GetProcAddress(library,"BCryptOpenAlgorithmProvider"));
    auto create=reinterpret_cast<decltype(&BCryptCreateHash)>(GetProcAddress(library,"BCryptCreateHash"));
    auto update=reinterpret_cast<decltype(&BCryptHashData)>(GetProcAddress(library,"BCryptHashData"));
    auto finish=reinterpret_cast<decltype(&BCryptFinishHash)>(GetProcAddress(library,"BCryptFinishHash"));
    auto destroy=reinterpret_cast<decltype(&BCryptDestroyHash)>(GetProcAddress(library,"BCryptDestroyHash"));
    auto close=reinterpret_cast<decltype(&BCryptCloseAlgorithmProvider)>(GetProcAddress(library,"BCryptCloseAlgorithmProvider"));
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE digest=nullptr;bool okay=false;
    if(open && create && update && finish && destroy && close && open(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)>=0 && create(algorithm,&digest,nullptr,0,nullptr,0,0)>=0){
        U8 bytes[65536];DWORD got=0;bool complete=true;
        for(;;){if(!ReadFile(file,bytes,sizeof(bytes),&got,nullptr)){complete=false;break;}if(!got)break;if(update(digest,bytes,got,0)<0){complete=false;break;}}
        U8 result[32];if(complete && finish(digest,result,sizeof(result),0)>=0){char hex[65]{};constexpr char digits[]="0123456789abcdef";for(unsigned i=0;i<32;i++){hex[i*2]=digits[result[i]>>4];hex[i*2+1]=digits[result[i]&15];}okay=std::strcmp(hex,kSha256)==0;}
    }
    if(digest && destroy)destroy(digest);if(algorithm && close)close(algorithm,0);FreeLibrary(library);CloseHandle(file);return okay;
}
inline bool verify_module(const samase::PluginApi* api) noexcept {
    if(verified_module)return true;
    if(!api || !api->extended_dat)return false;
    MEMORY_BASIC_INFORMATION memory{};if(VirtualQuery(reinterpret_cast<const void*>(api->extended_dat),&memory,sizeof(memory))!=sizeof(memory) || memory.Type!=MEM_IMAGE)return false;
    auto base=static_cast<U8*>(memory.AllocationBase);IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};
    if(!native_engine_hooks::read_exact(base,&dos,sizeof(dos)) || dos.e_magic!=IMAGE_DOS_SIGNATURE || dos.e_lfanew<0 || dos.e_lfanew>0x1000)return false;
    if(!native_engine_hooks::read_exact(base+dos.e_lfanew,&nt,sizeof(nt)) || nt.Signature!=IMAGE_NT_SIGNATURE || nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64 || nt.FileHeader.TimeDateStamp!=kTimestamp || nt.OptionalHeader.SizeOfImage!=kImageSize || !hash_module(reinterpret_cast<HMODULE>(base)))return false;
    verified_module=base;return true;
}
inline U32 fallback(U32 id) noexcept {return original_maximum ? original_maximum(id):0;}
inline U32 __cdecl health_q8(const bw::Unit* unit,U32 id) noexcept {
    if(passthrough_only.load(std::memory_order_acquire))return fallback(id);
    U32 maximum=0;
    if(max_hp_cache::read(unit,maximum) && unit->unit_id==id)return maximum;
    return fallback(id);
}
inline U32 __cdecl health_display_q8(const bw::Unit* unit,U32 id) noexcept {
    if(passthrough_only.load(std::memory_order_acquire))return fallback(id);
    U32 maximum=0,original=0;
    if(!max_hp_cache::read(unit,maximum,&original) || unit->unit_id!=id)return fallback(id);
    if(maximum!=original){
        U32 count=logged_queries.load(std::memory_order_relaxed);
        while(count<8 && !logged_queries.compare_exchange_weak(count,count+1,std::memory_order_relaxed)){}
        if(count<8)log_event("SAMASE HP UI owner query: unit=%p id=%u owner=%u hp_q8=%d maximum_q8=%u original_q8=%u thread=%lu",static_cast<const void*>(unit),id,U32(unit->player),unit->flingy.hitpoints,maximum,original,GetCurrentThreadId());
        // SAMASE shifts signed Q8 down after this call. Round modified maxima
        // up solely for that text read; the percent/color call keeps exact Q8.
        if(maximum)return static_cast<U32>(std::min<std::uint64_t>(0x7fffff00u,(std::uint64_t(maximum)+255u)&~std::uint64_t(255)));
    }
    return maximum;
}
inline U32 __cdecl shield_q8(const bw::Unit* unit,U32 id) noexcept {
    U32 hp=0,shields=0;
    if(!passthrough_only.load(std::memory_order_acquire) && max_hp_cache::read_display(unit,hp,shields) && unit->unit_id==id)
        return static_cast<U32>(std::min<std::uint64_t>(0x7fffff00u,std::uint64_t(shields)<<8));
    return original_shields ? original_shields(id):0;
}
inline void build_relay(U8* code,const void* callback) noexcept {
    // Original call sees caller [rsp+38] = Unit*. The return address adds8.
    // Preserve requested type ID in EDX; RCX receives the actual Unit pointer.
    constexpr U8 args[]={0x89,0xca,0x48,0x8b,0x4c,0x24,0x40};
    std::memcpy(code,args,sizeof(args));native_engine_hooks::absolute_jump(code+sizeof(args),callback);
}
inline bool original_bytes(U8* base) noexcept {
    using native_engine_hooks::match;
    return base && match(base+kSites[0],kCalls[0],5) && match(base+kSites[1],kCalls[1],5) && match(base+kSites[2],kCalls[2],5) &&
        match(base+0x1b2cf2,kSecondArgs,sizeof(kSecondArgs)) && match(base+0x1b2d0b,kShieldFormatter,sizeof(kShieldFormatter)) && match(base+kShieldGetterRva,kShieldGetter,sizeof(kShieldGetter)) &&
        match(base+0x1b2c93,kSavedUnit,sizeof(kSavedUnit)) && match(base+0x1b2d40,kFirstArgs,sizeof(kFirstArgs)) &&
        match(base+0x1b2da9,kSecondArgs,sizeof(kSecondArgs)) && match(base+0x1b2dc2,kFormatter,sizeof(kFormatter)) && match(base+kGetterRva,kGetter,sizeof(kGetter));
}
inline bool verify_installation() noexcept {
    using native_engine_hooks::match;
    ready=!passthrough_only.load(std::memory_order_acquire) && verified_module && relay_page && match(verified_module+kSites[0],installed_calls[0],5) && match(verified_module+kSites[1],installed_calls[1],5) && match(verified_module+kSites[2],installed_calls[2],5) &&
        match(verified_module+0x1b2cf2,kSecondArgs,sizeof(kSecondArgs)) && match(verified_module+0x1b2d0b,kShieldFormatter,sizeof(kShieldFormatter)) && match(verified_module+kShieldGetterRva,kShieldGetter,sizeof(kShieldGetter)) &&
        match(relay_page,expected_relays[0],21) && match(relay_page+64,expected_relays[1],21) && match(relay_page+128,expected_relays[2],21) &&
        match(verified_module+0x1b2c93,kSavedUnit,sizeof(kSavedUnit)) && match(verified_module+0x1b2d40,kFirstArgs,sizeof(kFirstArgs)) &&
        match(verified_module+0x1b2da9,kSecondArgs,sizeof(kSecondArgs)) && match(verified_module+0x1b2dc2,kFormatter,sizeof(kFormatter)) && match(verified_module+kGetterRva,kGetter,sizeof(kGetter));
    return ready;
}
// Initialization only. Also exposed to an isolated synthetic-image host test;
// production callers must reach this only after verify_module(api).
inline bool install_at(U8* base) noexcept {
    using namespace native_engine_hooks;
    if(ready)return base==verified_module && verify_installation();
    if(relay_page || !original_bytes(base))return install_failed("samase_hp_original_mismatch");
    auto code=nearby_code(base+kSites[0]);if(!code)return install_failed("samase_hp_relay_allocate",true);
    U8 branches[kSiteCount][5]{};U8 relays[kSiteCount][21]{};
    build_relay(relays[0],reinterpret_cast<const void*>(health_q8));build_relay(relays[1],reinterpret_cast<const void*>(health_display_q8));build_relay(relays[2],reinterpret_cast<const void*>(shield_q8));
    for(std::size_t i=0;i<kSiteCount;i++){
        std::memcpy(code+i*64,relays[i],21);const auto delta=reinterpret_cast<std::intptr_t>(code+i*64)-reinterpret_cast<std::intptr_t>(base+kSites[i]+5);
        if(delta<INT32_MIN || delta>INT32_MAX){VirtualFree(code,0,MEM_RELEASE);return install_failed("samase_hp_relay_range");}
        branches[i][0]=0xe8;const auto relative=static_cast<std::int32_t>(delta);std::memcpy(branches[i]+1,&relative,4);
    }
    DWORD old=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),code,192)){install_failed("samase_hp_relay_protect",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    // All three call instructions are on one page. No writes occur until all
    // checks and relay preparation pass; this interval covers all three.
    auto begin=base+kSites[2];const std::size_t span=kSites[1]+5-kSites[2];
    if(!protect_code_for_write(begin,span,&old)){install_failed("samase_hp_calls_protect",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    original_maximum=reinterpret_cast<OriginalMaximum>(base+kGetterRva);original_shields=reinterpret_cast<OriginalMaximum>(base+kShieldGetterRva);
    for(std::size_t i=0;i<kSiteCount;i++)std::memcpy(base+kSites[i],branches[i],5);
    bool okay=true;for(std::size_t i=0;i<kSiteCount;i++)okay=okay && match(base+kSites[i],branches[i],5);
    if(!okay)for(std::size_t i=0;i<kSiteCount;i++)std::memcpy(base+kSites[i],kCalls[i],5);
    DWORD ignored=0;
    if(!VirtualProtect(begin,span,old,&ignored) || !FlushInstructionCache(GetCurrentProcess(),begin,span)){
        const auto saved_error=GetLastError();DWORD recovery=0;
        if(protect_code_for_write(begin,span,&recovery)){for(std::size_t i=0;i<kSiteCount;i++)std::memcpy(base+kSites[i],kCalls[i],5);VirtualProtect(begin,span,old,&ignored);FlushInstructionCache(GetCurrentProcess(),begin,span);}
        bool restored=true;for(std::size_t i=0;i<kSiteCount;i++)restored=restored && match(base+kSites[i],kCalls[i],5);
        if(restored){VirtualFree(code,0,MEM_RELEASE);original_maximum=nullptr;original_shields=nullptr;}
        else {
            // A failed OS rollback must never leave calls targeting freed
            // executable memory. Preserve the relays for process lifetime,
            // disable cache use, and fail activation with native fallbacks.
            verified_module=base;relay_page=code;passthrough_only.store(true,std::memory_order_release);
            std::memcpy(installed_calls,branches,sizeof(branches));std::memcpy(expected_relays,relays,sizeof(relays));
        }
        SetLastError(saved_error);return install_failed(restored ? "samase_hp_calls_finalize_rolled_back":"samase_hp_rollback_failed_passthrough",true);
    }
    if(!okay){VirtualFree(code,0,MEM_RELEASE);return install_failed("samase_hp_calls_verify");}
    original_maximum=reinterpret_cast<OriginalMaximum>(base+kGetterRva);verified_module=base;relay_page=code;
    std::memcpy(installed_calls,branches,sizeof(branches));std::memcpy(expected_relays,relays,sizeof(relays));
    passthrough_only.store(false,std::memory_order_release);return verify_installation();
}
inline bool bind(const samase::PluginApi* api) noexcept {
    if(!verify_module(api))return native_engine_hooks::install_failed("samase_hp_module_pin");
    return install_at(verified_module);
}
}
