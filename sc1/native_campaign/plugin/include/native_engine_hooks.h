#pragma once
// Pinned x64 engine extension. No offsets are inferred at run time.
// Call install only from samase_plugin_init, before game simulation begins.
#include <bcrypt.h>
namespace native_engine_hooks {
inline constexpr char kGameSha256[]="ce3ab05dc9a6aa35418947e5d95e19651ad6fbcd5e2c1856cd729c5b7c31281c";
inline constexpr DWORD kTimestamp=0x6747c80c,kImageSize=0x1450000;
struct Bytes {U32 rva;const U8* expected;std::size_t length;};
struct Spec {
    U32 rva;const U8* prologue;std::size_t stolen;
    const U8* unwind;std::size_t unwind_size;
    const Bytes* witnesses;std::size_t witness_count;
};
struct Hook {U8* allocation=nullptr;void* trampoline=nullptr;RUNTIME_FUNCTION runtime{};bool installed=false,queued=false;};
inline U8* verified_base=nullptr;
// Capture the first failing native install operation for a user-visible startup
// diagnostic. GetLastError is meaningful only for the documented Win32 calls;
// RtlAddFunctionTable's BOOLEAN failure has no documented last-error contract.
struct InstallDiagnostic {const char* stage="not_started";DWORD win32_error=0;bool error_valid=false;};
inline InstallDiagnostic last_install{};
inline bool install_failed(const char* stage,bool win32=false) noexcept {
    const auto error=win32 ? GetLastError():0;last_install={stage,error,win32};return false;
}
inline bool read_exact(const void* address,void* out,std::size_t n) noexcept {SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),address,out,n,&got)!=0 && got==n;}
inline bool match(const void* address,const U8* expected,std::size_t n) noexcept {
    if(!expected || !n || n>512)return false;U8 buffer[512];return read_exact(address,buffer,n) && std::memcmp(buffer,expected,n)==0;
}
inline bool pinned_file() noexcept {
    wchar_t path[32768];const auto length=GetModuleFileNameW(nullptr,path,32768);if(!length || length>=32768)return false;
    HANDLE file=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,nullptr);if(file==INVALID_HANDLE_VALUE)return false;
    HMODULE library=LoadLibraryExW(L"bcrypt.dll",nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32);if(!library){CloseHandle(file);return false;}
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
        U8 result[32];if(complete && finish(digest,result,sizeof(result),0)>=0){char hex[65]{};const char digits[]="0123456789abcdef";for(unsigned i=0;i<32;i++){hex[i*2]=digits[result[i]>>4];hex[i*2+1]=digits[result[i]&15];}okay=std::strcmp(hex,kGameSha256)==0;}
    }
    if(digest && destroy)destroy(digest);if(algorithm && close)close(algorithm,0);FreeLibrary(library);CloseHandle(file);return okay;
}
inline bool verify_image() noexcept {
    if(verified_base)return true;
    auto base=reinterpret_cast<U8*>(GetModuleHandleW(nullptr));IMAGE_DOS_HEADER dos{};IMAGE_NT_HEADERS64 nt{};
    if(!read_exact(base,&dos,sizeof(dos)) || dos.e_magic!=IMAGE_DOS_SIGNATURE || dos.e_lfanew<0 || dos.e_lfanew>0x1000)return false;
    if(!read_exact(base+dos.e_lfanew,&nt,sizeof(nt)) || nt.Signature!=IMAGE_NT_SIGNATURE || nt.FileHeader.Machine!=IMAGE_FILE_MACHINE_AMD64 || nt.FileHeader.TimeDateStamp!=kTimestamp || nt.OptionalHeader.SizeOfImage!=kImageSize || !pinned_file())return false;
    verified_base=base;return true;
}
inline void absolute_jump(U8* out,const void* target) noexcept {
    out[0]=0xff;out[1]=0x25;std::memset(out+2,0,4);const auto address=reinterpret_cast<std::uint64_t>(target);std::memcpy(out+6,&address,8);
}
// A trampoline continues with its copied frame still allocated. Bare FF /4
// with mod=00 is a Windows x64 epilog suffix; at that RIP RtlVirtualUnwind
// would pop a return address before undoing the copied prologue. An ignored
// CS prefix makes this a body instruction, so the original unwind codes apply.
// Intel SDM Vol.1 3.3.7.1 (64-bit mode ignores CS/DS/ES/SS overrides), and
// Microsoft Learn x64 prolog-and-epilog (restricted epilog instruction forms).
// This one instruction preserves every register/flag. Its valid RIP is the
// prefix byte, never the internal FF byte. Entry patches/leaf relays stay FF25.
inline constexpr std::size_t continuation_jump_size=15;
inline void continuation_jump(U8* out,const void* target) noexcept {
    out[0]=0x2e;absolute_jump(out+1,target);
}
inline bool valid_spec(const Spec& spec) noexcept {
    // Only manually disassembled, relocation-free instruction sequences may
    // be listed. A full instruction-boundary byte match is mandatory.
    return spec.stolen>=14 && spec.stolen<=48 && spec.prologue && spec.unwind && spec.unwind_size>=4 && spec.unwind_size<=128 &&
        (spec.unwind[0]&0xf8)==0 && (spec.unwind[0]&7)==1 && spec.unwind[1]<=spec.stolen && spec.rva<kImageSize && spec.stolen<kImageSize-spec.rva;
}
// StarCraft 13515 is remapped as MEM_MAPPED/PAGE_EXECUTE_READ by its
// loader. A mapped read/execute view cannot become shared READWRITE (87).
// WRITECOPY creates process-private pages and preserves the backing EXE.
// See VirtualProtect / MapViewOfFile's documented compatible-protection rule.
inline bool protect_code_for_write(void* address,std::size_t length,DWORD* previous) noexcept {
    MEMORY_BASIC_INFORMATION region{};
    if(!address || !length || !previous || VirtualQuery(address,&region,sizeof(region))!=sizeof(region) || region.State!=MEM_COMMIT){SetLastError(ERROR_INVALID_ADDRESS);return false;}
    const auto begin=reinterpret_cast<std::uintptr_t>(address),region_begin=reinterpret_cast<std::uintptr_t>(region.BaseAddress);
    if(begin<region_begin || length>region.RegionSize || begin-region_begin>region.RegionSize-length){SetLastError(ERROR_INVALID_PARAMETER);return false;}
    const DWORD protection=(region.Type==MEM_MAPPED || region.Type==MEM_IMAGE) ? PAGE_EXECUTE_WRITECOPY:PAGE_EXECUTE_READWRITE;
    return VirtualProtect(address,length,protection,previous)!=0;
}
inline bool install_at(U8* base,const Spec& spec,void* destination,Hook& hook) noexcept {
    last_install={"begin",0,false};
    if(hook.installed){last_install={"already_installed",0,false};return true;}
    if(!base || !destination)return install_failed("invalid_arguments");
    if(!valid_spec(spec))return install_failed("invalid_spec");
    if(!match(base+spec.rva,spec.prologue,spec.stolen))return install_failed("prologue_mismatch");
    for(std::size_t i=0;i<spec.witness_count;i++){const auto& w=spec.witnesses[i];
        if(w.rva>=kImageSize || w.length>kImageSize-w.rva || !match(base+w.rva,w.expected,w.length))return install_failed("witness_mismatch");}
    auto code=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));if(!code)return install_failed("allocate_trampoline",true);
    std::memcpy(code,spec.prologue,spec.stolen);continuation_jump(code+spec.stolen,base+spec.rva+spec.stolen);std::memcpy(code+128,spec.unwind,spec.unwind_size);
    hook.runtime={0,static_cast<DWORD>(spec.stolen+continuation_jump_size),128};
    DWORD old=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old)){install_failed("protect_trampoline",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    if(!RtlAddFunctionTable(&hook.runtime,1,reinterpret_cast<DWORD64>(code))){install_failed("register_unwind");VirtualFree(code,0,MEM_RELEASE);return false;}
    U8 branch[48];std::memset(branch,0x90,sizeof(branch));absolute_jump(branch,destination);
    if(!protect_code_for_write(base+spec.rva,spec.stolen,&old)){install_failed("protect_original",true);RtlDeleteFunctionTable(&hook.runtime);VirtualFree(code,0,MEM_RELEASE);return false;}
    // Initialization only: no concurrent game simulation can enter this site.
    std::memcpy(base+spec.rva,branch,spec.stolen);DWORD ignored=0;VirtualProtect(base+spec.rva,spec.stolen,old,&ignored);FlushInstructionCache(GetCurrentProcess(),base+spec.rva,spec.stolen);FlushInstructionCache(GetCurrentProcess(),code,spec.stolen+continuation_jump_size);
    hook.allocation=code;hook.trampoline=code;hook.installed=true;last_install={"installed",0,false};return true;
}
inline bool install(const Spec& spec,void* destination,Hook& hook) noexcept {return verify_image() && install_at(verified_base,spec,destination,hook);}
using WriteExeMemory=U32 (__cdecl*)(std::size_t,const U8*,std::size_t);
// Only call while SAMASE's plugin-init context is active. The callback is not
// retained. Return means accepted by the loader, not that code is installed.
inline bool register_at(U8* base,const Spec& spec,void* destination,Hook& hook,WriteExeMemory writer) noexcept {
    last_install={"register_begin",0,false};
    if(hook.installed || hook.queued)return true;
    if(!base || !destination || !writer)return install_failed("registration_api_missing");
    if(!valid_spec(spec))return install_failed("invalid_spec");
    if(!match(base+spec.rva,spec.prologue,spec.stolen))return install_failed("prologue_mismatch");
    for(std::size_t i=0;i<spec.witness_count;i++){const auto& w=spec.witnesses[i];if(w.rva>=kImageSize || w.length>kImageSize-w.rva || !match(base+w.rva,w.expected,w.length))return install_failed("witness_mismatch");}
    auto code=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));if(!code)return install_failed("allocate_trampoline",true);
    std::memcpy(code,spec.prologue,spec.stolen);continuation_jump(code+spec.stolen,base+spec.rva+spec.stolen);std::memcpy(code+128,spec.unwind,spec.unwind_size);
    hook.runtime={0,static_cast<DWORD>(spec.stolen+continuation_jump_size),128};DWORD old=0;
    if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old)){install_failed("protect_trampoline",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    if(!FlushInstructionCache(GetCurrentProcess(),code,spec.stolen+continuation_jump_size)){install_failed("flush_trampoline",true);VirtualFree(code,0,MEM_RELEASE);return false;}
    if(!RtlAddFunctionTable(&hook.runtime,1,reinterpret_cast<DWORD64>(code))){install_failed("register_unwind");VirtualFree(code,0,MEM_RELEASE);return false;}
    U8 branch[48];std::memset(branch,0x90,sizeof(branch));absolute_jump(branch,destination);
    if(!writer(reinterpret_cast<std::size_t>(base+spec.rva),branch,spec.stolen)){install_failed("registration_api_rejected");RtlDeleteFunctionTable(&hook.runtime);VirtualFree(code,0,MEM_RELEASE);return false;}
    hook.allocation=code;hook.trampoline=code;hook.queued=true;last_install={"registered_waiting_for_loader",0,false};return true;
}
inline bool register_hook(const Spec& spec,void* destination,Hook& hook,WriteExeMemory writer) noexcept {
    return verify_image() && register_at(verified_base,spec,destination,hook,writer);
}
// First-file phase: read-only validation. Never call init-only APIs here.
inline bool verify_registered_at(U8* base,const Spec& spec,void* destination,Hook& hook) noexcept {
    if(!base || !destination || !hook.queued || !hook.trampoline || !valid_spec(spec))return install_failed("registration_missing");
    U8 branch[48];std::memset(branch,0x90,sizeof(branch));absolute_jump(branch,destination);
    if(!match(base+spec.rva,branch,spec.stolen))return install_failed("registered_branch_mismatch");
    hook.installed=true;last_install={"installed_verified_after_loader",0,false};return true;
}
inline bool verify_registered(const Spec& spec,void* destination,Hook& hook) noexcept {
    return verified_base && verify_registered_at(verified_base,spec,destination,hook);
}

struct CallSpec {Bytes site;U32 original_rva;};
inline U8* nearby_code(U8* site) noexcept {
    SYSTEM_INFO info{};GetSystemInfo(&info);const std::uintptr_t granularity=info.dwAllocationGranularity;
    const auto center=reinterpret_cast<std::uintptr_t>(site);const auto lower=center>0x70000000 ? center-0x70000000 : granularity;const auto upper=center+0x70000000;
    auto cursor=(lower+granularity-1)&~(granularity-1);
    while(cursor<upper){MEMORY_BASIC_INFORMATION region{};if(!VirtualQuery(reinterpret_cast<void*>(cursor),&region,sizeof(region)))break;
        const auto end=reinterpret_cast<std::uintptr_t>(region.BaseAddress)+region.RegionSize;
        if(region.State==MEM_FREE){const auto start=(cursor+granularity-1)&~(granularity-1);if(start+4096<=end && start+4096<upper){auto memory=static_cast<U8*>(VirtualAlloc(reinterpret_cast<void*>(start),4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));if(memory)return memory;}}
        if(end<=cursor)break;cursor=(end+granularity-1)&~(granularity-1);
    }return nullptr;
}
inline bool install_call_at(U8* base,const CallSpec& spec,void* destination,Hook& hook) noexcept {
    if(hook.installed)return true;
    if(!base || !destination || spec.site.length!=5 || !spec.site.expected || spec.site.expected[0]!=0xe8 || spec.site.rva>=kImageSize-5 || spec.original_rva>=kImageSize || !match(base+spec.site.rva,spec.site.expected,5))return false;
    std::int32_t expected=0;std::memcpy(&expected,spec.site.expected+1,4);if(std::int64_t(spec.site.rva)+5+expected!=spec.original_rva)return false;
    auto site=base+spec.site.rva;auto relay=nearby_code(site);if(!relay)return false;absolute_jump(relay,destination);
    const auto relative=reinterpret_cast<std::intptr_t>(relay)-reinterpret_cast<std::intptr_t>(site+5);if(relative<INT32_MIN || relative>INT32_MAX){VirtualFree(relay,0,MEM_RELEASE);return false;}
    DWORD old=0;if(!VirtualProtect(relay,4096,PAGE_EXECUTE_READ,&old)){VirtualFree(relay,0,MEM_RELEASE);return false;}
    U8 replacement[5]={0xe8};const auto offset=static_cast<std::int32_t>(relative);std::memcpy(replacement+1,&offset,4);
    if(!protect_code_for_write(site,5,&old)){VirtualFree(relay,0,MEM_RELEASE);return false;}
    std::memcpy(site,replacement,5);DWORD ignored=0;VirtualProtect(site,5,old,&ignored);FlushInstructionCache(GetCurrentProcess(),site,5);FlushInstructionCache(GetCurrentProcess(),relay,14);
    hook.allocation=relay;hook.trampoline=base+spec.original_rva;hook.installed=true;return true;
}
inline bool install_call(const CallSpec& spec,void* destination,Hook& hook) noexcept {return verify_image() && install_call_at(verified_base,spec,destination,hook);}

inline bool uninstall_call_at(U8* base,const CallSpec& spec,Hook& hook) noexcept {
    if(!hook.installed)return true;if(!base || !hook.allocation || spec.site.length!=5 || !spec.site.expected)return false;
    auto site=base+spec.site.rva;const auto relative=reinterpret_cast<std::intptr_t>(hook.allocation)-reinterpret_cast<std::intptr_t>(site+5);
    if(relative<INT32_MIN || relative>INT32_MAX)return false;U8 branch[5]={0xe8};const auto offset=static_cast<std::int32_t>(relative);std::memcpy(branch+1,&offset,4);if(!match(site,branch,5))return false;
    DWORD old=0;if(!protect_code_for_write(site,5,&old))return false;std::memcpy(site,spec.site.expected,5);DWORD ignored=0;VirtualProtect(site,5,old,&ignored);FlushInstructionCache(GetCurrentProcess(),site,5);
    VirtualFree(hook.allocation,0,MEM_RELEASE);hook={};return true;
}
inline bool uninstall_call(const CallSpec& spec,Hook& hook) noexcept {return verified_base && uninstall_call_at(verified_base,spec,hook);}

struct Patch {U32 rva=0;std::size_t length=0;U8 before[64]{},after[64]{};bool installed=false;};
inline bool install_patch(const Bytes& original,const U8* replacement,Patch& patch) noexcept {
    if(patch.installed)return true;if(!replacement || original.length>64 || !verify_image() || original.rva>=kImageSize || original.length>kImageSize-original.rva || !match(verified_base+original.rva,original.expected,original.length))return false;
    auto site=verified_base+original.rva;DWORD old=0;if(!protect_code_for_write(site,original.length,&old))return false;
    patch.rva=original.rva;patch.length=original.length;std::memcpy(patch.before,original.expected,original.length);std::memcpy(patch.after,replacement,original.length);
    std::memcpy(site,replacement,original.length);DWORD ignored=0;VirtualProtect(site,original.length,old,&ignored);FlushInstructionCache(GetCurrentProcess(),site,original.length);patch.installed=true;return true;
}
inline bool uninstall_patch(Patch& patch) noexcept {
    if(!patch.installed)return true;if(!verified_base || !match(verified_base+patch.rva,patch.after,patch.length))return false;
    auto site=verified_base+patch.rva;DWORD old=0;if(!protect_code_for_write(site,patch.length,&old))return false;
    std::memcpy(site,patch.before,patch.length);DWORD ignored=0;VirtualProtect(site,patch.length,old,&ignored);FlushInstructionCache(GetCurrentProcess(),site,patch.length);patch={};return true;
}

}
