#pragma once
// SC:R13515/SAMASE0.10.28: serialize native lighting readers against the
// complete SAMASE lighting loader, including its original native callback.
// All counters/hooks live for the process lifetime. No image, DAT, asset or
// lighting value is changed. A reader during a rebuild returns native false.
namespace rework_lighting_v5 {
using Reader=U32 (__cdecl*)(void*,void*,U32,U32);
using NativeWriter=U32 (__cdecl*)(void*,U32,U32,std::uintptr_t,U32,std::uintptr_t);
using Writer=U32 (__cdecl*)(void*,U32,U32,std::uintptr_t,U32,std::uintptr_t,NativeWriter);
inline Reader original_reader=nullptr;
inline Writer original_writer=nullptr;
inline std::atomic<U32> readers{0},writers{0};
inline std::atomic<bool> enabled{false};
inline thread_local U32 writer_depth=0;
struct ReadScope {
    bool entered=false;
    ReadScope() noexcept {
        // Cross-atomic Dekker handshake requires a single total order.
        if(!enabled.load(std::memory_order_seq_cst)||writers.load(std::memory_order_seq_cst))return;
        readers.fetch_add(1,std::memory_order_seq_cst);
        if(writers.load(std::memory_order_seq_cst)){readers.fetch_sub(1,std::memory_order_seq_cst);return;}
        entered=true;
    }
    ~ReadScope(){if(entered)readers.fetch_sub(1,std::memory_order_seq_cst);}
    ReadScope(const ReadScope&)=delete;ReadScope& operator=(const ReadScope&)=delete;
};
struct WriteScope {
    bool outer=false;
    WriteScope() noexcept {
        if(writer_depth){++writer_depth;return;}
        // Distinct native asset workers can wait on each other. Preserve their
        // parallelism; exclude readers while any complete writer is active.
        writers.fetch_add(1,std::memory_order_seq_cst);outer=true;
        U32 spins=0;while(readers.load(std::memory_order_seq_cst)){YieldProcessor();if((++spins&63u)==0)SwitchToThread();}
        writer_depth=1;
    }
    ~WriteScope(){if(writer_depth)--writer_depth;if(outer)writers.fetch_sub(1,std::memory_order_seq_cst);}
    WriteScope(const WriteScope&)=delete;WriteScope& operator=(const WriteScope&)=delete;
};
inline U32 __cdecl read(void* resource,void* output,U32 image,U32 frame) {
    ReadScope guard;if(!guard.entered||!original_reader)return 0;
    // The pinned native function is a leaf: no callback while counted.
    return original_reader(resource,output,image,frame);
}
inline U32 __cdecl write(void* resource,U32 first,U32 count,std::uintptr_t opaque,U32 fifth,std::uintptr_t sixth,NativeWriter callback) {
    WriteScope guard;return original_writer ? original_writer(resource,first,count,opaque,fifth,sixth,callback):0;
}
inline constexpr U32 reader_rva=0x151570,writer_rva=0xb1f3;
inline constexpr U8 reader_prefix[]={0x48,0x83,0xec,0x28,0x4c,0x8b,0x51,0x58,0x4d,0x85,0xd2,0x74,0x57,0x49,0x63,0xc0};
inline constexpr U8 reader_unwind[]={1,4,1,0,4,0x42,0,0};
inline constexpr U8 reader_tail[]={0x49,0x39,0x42,0x08,0x76,0x4e,0x4d,0x8b,0x02,0x48,0x8d,0x04,0x40,0x49,0x63,0xc9,0x49,0x3b,0x4c,0xc0,0x08,0x73,0x1f,0x49,0x8b,0x04,0xc0,0x48,0xc1,0xe1,0x05,0x0f,0x10,0x04,0x01};
inline constexpr U8 reader_false[]={0x32,0xc0,0x48,0x83,0xc4,0x28,0xc3};
inline constexpr U8 reader_middle[]={0x0f,0x11,0x02,0x0f,0x10,0x4c,0x01,0x10,0xb0,0x01,0x0f,0x11,0x4a,0x10,0x48,0x83,0xc4,0x28,0xc3,0x33,0xc0,0x0f,0x57,0xc9,0x48,0x89,0x04,0x24,0x48,0x89,0x44,0x24,0x08,0x0f,0x10,0x04,0x24,0x0f,0x11,0x02,0x0f,0x11,0x4a,0x10,0x48,0x83,0xc4,0x28,0xc3};
inline constexpr U8 writer_prefix[]={0x41,0x57,0x41,0x56,0x41,0x55,0x41,0x54,0x56,0x57,0x55,0x53,0x48,0x81,0xec,0xb8,0,0,0};
inline constexpr U8 writer_unwind[]={1,19,10,0,19,1,23,0,12,0x30,11,0x50,10,0x70,9,0x60,8,0xc0,6,0xd0,4,0xe0,2,0xf0};
inline constexpr U8 writer_args[]={0x49,0x89,0xcf,0x48,0x8b,0x84,0x24,0x30,0x01,0,0,0x44,0x89,0xc1,0x81,0xf1,0xe7,0x03,0,0,0x09,0xd1};
inline constexpr U8 writer_native_call[]={0x4c,0x89,0xf9,0x31,0xd2,0xff,0xd0,0x84,0xc0};
inline constexpr U8 writer_free[]={0x49,0x8b,0x77,0x58,0x48,0x85,0xf6,0x74,0x2e,0x48,0x8b,0x0e,0x48,0x8b,0x56,0x08,0xe8,0x25,0xee,0x1b,0};
inline constexpr U8 writer_publish[]={0x4d,0x85,0xf6,0x74,0x06,0x4d,0x89,0x77,0x58};
inline constexpr native_engine_hooks::Bytes writer_witnesses[]={
    {0xb21f,writer_args,sizeof(writer_args)}, {0xb267,writer_native_call,sizeof(writer_native_call)},
    {0xb278,writer_free,sizeof(writer_free)}, {0xb60d,writer_publish,sizeof(writer_publish)}
};
inline constexpr native_engine_hooks::Spec writer_spec={writer_rva,writer_prefix,sizeof(writer_prefix),writer_unwind,sizeof(writer_unwind),writer_witnesses,std::size(writer_witnesses)};
inline native_engine_hooks::Hook reader_hook{},writer_hook{};
inline U8* game_base=nullptr,*module_base=nullptr;
inline U8 reader_branch[16]{},reader_code[38]{};
inline const char* last_error="not_bound";
inline bool fail(const char* stage) noexcept {last_error=stage;return false;}
inline bool reader_original(U8* base) noexcept {
    return base&&native_engine_hooks::match(base+reader_rva,reader_prefix,sizeof(reader_prefix))&&native_engine_hooks::match(base+0x151580,reader_tail,sizeof(reader_tail))&&native_engine_hooks::match(base+0x1515a3,reader_middle,sizeof(reader_middle))&&native_engine_hooks::match(base+0x1515d4,reader_false,sizeof(reader_false));
}
inline bool make_reader(U8* base) noexcept {
    using namespace native_engine_hooks;
    if(reader_hook.allocation||!reader_original(base))return fail("reader_original_mismatch");
    auto code=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));if(!code)return fail("reader_allocate");
    std::memcpy(code,reader_prefix,16);code[12]=18; // JE to local false epilog at31.
    continuation_jump(code+16,base+reader_rva+16);
    const U8 epilog[]={0x33,0xc0,0x48,0x83,0xc4,0x28,0xc3};std::memcpy(code+31,epilog,7);std::memcpy(code+128,reader_unwind,sizeof(reader_unwind));
    reader_hook.runtime={0,38,128};DWORD old=0;
    if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),code,136)){VirtualFree(code,0,MEM_RELEASE);return fail("reader_protect");}
    if(!RtlAddFunctionTable(&reader_hook.runtime,1,reinterpret_cast<DWORD64>(code))){VirtualFree(code,0,MEM_RELEASE);return fail("reader_unwind_register");}
    std::memcpy(reader_code,code,38);reader_hook.allocation=code;reader_hook.trampoline=code;return true;
}
inline bool verify_ready() noexcept {
    using namespace native_engine_hooks;
    U8 branch[48]{},continuation[15]{};std::memset(branch,0x90,sizeof(branch));absolute_jump(branch,reinterpret_cast<void*>(write));
    continuation_jump(continuation,module_base ? module_base+writer_rva+19:nullptr);
    if(!(game_base&&module_base&&(reader_hook.installed||reader_hook.queued)&&writer_hook.installed&&
        match(game_base+reader_rva,reader_branch,16)&&match(module_base+writer_rva,branch,19)&&
        match(reader_hook.allocation,reader_code,38)&&match(reader_hook.allocation+128,reader_unwind,sizeof(reader_unwind))&&
        match(writer_hook.allocation,writer_prefix,19)&&match(writer_hook.allocation+19,continuation,15)&&match(writer_hook.allocation+128,writer_unwind,sizeof(writer_unwind)))){enabled.store(false,std::memory_order_seq_cst);return false;}
    if(!match(game_base+0x151580,reader_tail,sizeof(reader_tail))||!match(game_base+0x1515a3,reader_middle,sizeof(reader_middle))||!match(game_base+0x1515d4,reader_false,sizeof(reader_false))){enabled.store(false,std::memory_order_seq_cst);return false;}
    for(const auto& witness:writer_witnesses)if(!match(module_base+witness.rva,witness.expected,witness.length)){enabled.store(false,std::memory_order_seq_cst);return false;}
    reader_hook.installed=true;enabled.store(true,std::memory_order_seq_cst);last_error="ready";return true;
}
// Init-only, before native asset workers start. The reader is installed first
// with its gate closed; it cannot observe data before the complete writer hook.
inline bool install_at(U8* game,U8* module) noexcept {
    using namespace native_engine_hooks;
    if(enabled.load(std::memory_order_seq_cst))return game==game_base&&module==module_base&&verify_ready();
    if(reader_hook.allocation||writer_hook.allocation||!game||!module)return fail("partial_or_invalid_install");
    if(!reader_original(game)||!match(module+writer_rva,writer_prefix,19))return fail("original_bytes");
    for(const auto& witness:writer_witnesses)if(!match(module+witness.rva,witness.expected,witness.length))return fail("writer_witness");
    if(!make_reader(game))return false;
    original_reader=reinterpret_cast<Reader>(reader_hook.trampoline);
    std::memset(reader_branch,0x90,sizeof(reader_branch));absolute_jump(reader_branch,reinterpret_cast<void*>(read));
    DWORD old=0;if(!protect_code_for_write(game+reader_rva,16,&old))return fail("reader_original_protect");
    std::memcpy(game+reader_rva,reader_branch,16);DWORD ignored=0;
    const bool protection=VirtualProtect(game+reader_rva,16,old,&ignored)!=0;
    const bool flushed=FlushInstructionCache(GetCurrentProcess(),game+reader_rva,16)!=0;
    reader_hook.installed=true;game_base=game;module_base=module;
    if(!protection||!flushed||!match(game+reader_rva,reader_branch,16))return fail("reader_original_finalize");
    if(!native_engine_hooks::install_at(module,writer_spec,reinterpret_cast<void*>(write),writer_hook))return fail("writer_install");
    original_writer=reinterpret_cast<Writer>(writer_hook.trampoline);
    enabled.store(true,std::memory_order_seq_cst);
    if(!verify_ready()){enabled.store(false,std::memory_order_seq_cst);return fail("installed_verification");}
    last_error="ready";return true;
}
// The game is a read-only MEM_MAPPED view during plugin init. SAMASE queues
// absolute game addresses and applies them in its own executable image phase;
// VirtualProtect(WRITECOPY) is rejected there with ERROR_INVALID_PARAMETER.
// The SAMASE DLL is a normal MEM_IMAGE and its writer is patched immediately.
inline bool register_at(U8* game,U8* module,native_engine_hooks::WriteExeMemory patch) noexcept {
    using namespace native_engine_hooks;
    if(reader_hook.queued)return game==game_base&&module==module_base&&writer_hook.installed;
    if(reader_hook.allocation||writer_hook.allocation||!game||!module||!patch)return fail("partial_or_invalid_registration");
    if(!reader_original(game)||!match(module+writer_rva,writer_prefix,19))return fail("original_bytes");
    for(const auto& witness:writer_witnesses)if(!match(module+witness.rva,witness.expected,witness.length))return fail("writer_witness");
    if(!make_reader(game))return false;
    original_reader=reinterpret_cast<Reader>(reader_hook.trampoline);
    std::memset(reader_branch,0x90,sizeof(reader_branch));absolute_jump(reader_branch,reinterpret_cast<void*>(read));
    if(!patch(reinterpret_cast<std::size_t>(game+reader_rva),reader_branch,16))return fail("reader_registration_rejected");
    reader_hook.queued=true;game_base=game;module_base=module;
    if(!native_engine_hooks::install_at(module,writer_spec,reinterpret_cast<void*>(write),writer_hook))return fail("writer_install");
    original_writer=reinterpret_cast<Writer>(writer_hook.trampoline);
    last_error="registered_waiting_for_loader";return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {
    if(!api||api->version!=44||!api->write_exe_memory||!native_engine_hooks::verify_image()||!samase_status_ui::verify_module(api))return fail("api_or_module_pin");
    return register_at(native_engine_hooks::verified_base,samase_status_ui::module_base(),reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));
}
inline void reset() noexcept {} // Do not invalidate counts or detach live asset workers.
}
