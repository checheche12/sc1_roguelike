#pragma once
#include <thread>
// Synthetic concurrency/ABI proof only. Actual SC:R reload proof is separate.
namespace host_test {
namespace lighting_fixture {
using namespace rework_lighting_v5;
template<class Predicate> inline bool until(const Predicate& predicate) {
    const auto end=GetTickCount64()+5000;while(!predicate()){if(GetTickCount64()>=end)return false;SwitchToThread();}return true;
}
inline std::atomic<bool> entered{false},release{false},writer_entered{false},valid{true};
inline U32 __cdecl blocking_reader(void*,void* output,U32,U32){entered=true;if(!until([]{return release.load();}))valid=false;*static_cast<U32*>(output)=0x51ce;return 1;}
inline U32 __cdecl counting_writer(void*,U32,U32,std::uintptr_t,U32,std::uintptr_t,NativeWriter){writer_entered=true;return 0x44;}
inline U32 __cdecl throwing_reader(void*,void*,U32,U32){throw std::runtime_error("reader_fixture");}
inline U32 __cdecl throwing_writer(void*,U32,U32,std::uintptr_t,U32,std::uintptr_t,NativeWriter){throw std::runtime_error("writer_fixture");}
inline std::atomic<U32> bodies{0},completed{0};
inline U32 __cdecl parallel_writer(void*,U32,U32,std::uintptr_t,U32,std::uintptr_t,NativeWriter){
    bodies.fetch_add(1);if(!until([]{return bodies.load()==2;}))valid=false;
    U32 output=0x1234;if(read(nullptr,&output,0,0)||output!=0x1234)valid=false;
    if(!until([]{return release.load();}))valid=false;completed.fetch_add(1);return 1;
}
inline U32 __cdecl nested_writer(void* resource,U32 first,U32 total,std::uintptr_t opaque,U32 fifth,std::uintptr_t sixth,NativeWriter callback){
    if(writers.load()!=1||writer_depth!=first+1)valid=false;
    U32 out=0x77;if(read(nullptr,&out,0,0)||out!=0x77)valid=false;
    return first ? 0xabc:write(resource,1,total,opaque,fifth,sixth,callback);
}
struct GateFixture {
    Reader old_reader=original_reader;Writer old_writer=original_writer;bool old_enabled=enabled.load();
    GateFixture(){CHECK(readers.load()==0&&writers.load()==0&&writer_depth==0);enabled=true;entered=false;release=false;writer_entered=false;valid=true;bodies=0;completed=0;}
    ~GateFixture(){original_reader=old_reader;original_writer=old_writer;enabled=old_enabled;}
};
inline U32 __cdecl marker_callback(void*,U32,U32,std::uintptr_t,U32,std::uintptr_t){return 0x51cee12;}
inline std::array<std::uintptr_t,7> observed{};
inline U8* queued_address=nullptr;inline std::array<U8,16> queued_bytes{};inline bool accept_queue=true,init_open=false;inline U32 queue_calls=0;
inline U32 __cdecl queue_patch(std::size_t address,const U8* bytes,std::size_t length){
    ++queue_calls;if(!init_open||!accept_queue||length!=16)return 0;queued_address=reinterpret_cast<U8*>(address);std::memcpy(queued_bytes.data(),bytes,16);return 1;
}
inline U32 __cdecl abi_writer(void* a,U32 b,U32 c,std::uintptr_t d,U32 e,std::uintptr_t f,NativeWriter callback){
    observed={reinterpret_cast<std::uintptr_t>(a),b,c,d,e,f,reinterpret_cast<std::uintptr_t>(callback)};
    if(writers.load()!=1||writer_depth!=1)valid=false;return 0xa53c0de;
}
struct ExecutableFixture {
    U8* game=nullptr;U8* module=nullptr;
    Reader old_reader=original_reader;Writer old_writer=original_writer;bool old_enabled=enabled.load();
    ExecutableFixture(){
        CHECK(!reader_hook.allocation&&!writer_hook.allocation);CHECK(readers.load()==0&&writers.load()==0);
        game=static_cast<U8*>(VirtualAlloc(nullptr,0x152000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
        module=static_cast<U8*>(VirtualAlloc(nullptr,0xc000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(game&&module);
        std::memcpy(game+reader_rva,reader_prefix,sizeof(reader_prefix));std::memcpy(game+0x151580,reader_tail,sizeof(reader_tail));
        std::memcpy(game+0x1515a3,reader_middle,sizeof(reader_middle));std::memcpy(game+0x1515d4,reader_false,sizeof(reader_false));
        std::memcpy(module+writer_rva,writer_prefix,sizeof(writer_prefix));for(const auto& w:writer_witnesses)std::memcpy(module+w.rva,w.expected,w.length);
        // After the witnessed copied prologue, a synthetic epilogue restores
        // exactly that frame then tail-calls the C++ seven-argument observer.
        module[writer_rva+19]=0xe9;const std::int32_t offset=0xb700-(writer_rva+24);std::memcpy(module+writer_rva+20,&offset,4);
        const U8 unwind_frame[]={0x48,0x81,0xc4,0xb8,0,0,0,0x5b,0x5d,0x5f,0x5e,0x41,0x5c,0x41,0x5d,0x41,0x5e,0x41,0x5f};
        std::memcpy(module+0xb700,unwind_frame,sizeof(unwind_frame));native_engine_hooks::absolute_jump(module+0xb700+sizeof(unwind_frame),reinterpret_cast<void*>(abi_writer));
    }
    ~ExecutableFixture(){
        enabled=false;
        if(reader_hook.allocation){RtlDeleteFunctionTable(&reader_hook.runtime);VirtualFree(reader_hook.allocation,0,MEM_RELEASE);}
        if(writer_hook.allocation){RtlDeleteFunctionTable(&writer_hook.runtime);VirtualFree(writer_hook.allocation,0,MEM_RELEASE);}
        reader_hook={};writer_hook={};game_base=module_base=nullptr;original_reader=old_reader;original_writer=old_writer;
        if(game)VirtualFree(game,0,MEM_RELEASE);if(module)VirtualFree(module,0,MEM_RELEASE);enabled=old_enabled;last_error="host_fixture_clean";
    }
};
inline void unwind(const native_engine_hooks::Hook& hook,U32 offset,bool writer){
    alignas(16) DWORD64 stack[128]{};auto entry=&stack[96];*entry=0x123456789abcull;
    for(U32 i=1;i<=8;i++)entry[-static_cast<int>(i)]=0x1000+i;
    CONTEXT context{};context.ContextFlags=CONTEXT_FULL;context.Rip=reinterpret_cast<DWORD64>(hook.allocation+offset);
    context.Rsp=reinterpret_cast<DWORD64>(entry)-(writer ? 248:40);DWORD64 image=0;
    auto function=RtlLookupFunctionEntry(context.Rip,&image,nullptr);CHECK(function&&function->UnwindData==128&&image==reinterpret_cast<DWORD64>(hook.allocation));
    void* handler_data=nullptr;DWORD64 establisher=0;RtlVirtualUnwind(UNW_FLAG_NHANDLER,image,context.Rip,function,&context,&handler_data,&establisher,nullptr);
    CHECK(context.Rip==*entry&&context.Rsp==reinterpret_cast<DWORD64>(entry+1));
    if(writer){CHECK(context.R15==0x1001&&context.R14==0x1002&&context.R13==0x1003&&context.R12==0x1004);CHECK(context.Rsi==0x1005&&context.Rdi==0x1006&&context.Rbp==0x1007&&context.Rbx==0x1008);}
}
}
inline void lighting_drains_old_reader_and_skips_new(){
    using namespace lighting_fixture;GateFixture fixture;original_reader=blocking_reader;original_writer=counting_writer;
    U32 output=0;std::thread old([&]{if(read(nullptr,&output,0,0)!=1)valid=false;});
    const bool old_started=until([]{return entered.load();});
    std::thread loader([]{if(write(nullptr,0,0,0,0,0,nullptr)!=0x44)valid=false;});
    const bool loader_waiting=until([]{return writers.load()==1;});U32 untouched=0x3344;
    const auto skipped=read(nullptr,&untouched,1,2);const bool blocked=!writer_entered.load();
    reset();const bool reset_kept_gate=readers.load()==1&&writers.load()==1;
    release=true;old.join();loader.join();
    CHECK(old_started&&loader_waiting&&blocked&&reset_kept_gate);CHECK(!skipped&&untouched==0x3344);CHECK(valid&&output==0x51ce&&writer_entered);CHECK(readers.load()==0&&writers.load()==0);
}
inline void lighting_parallel_workers_nested_and_cpp_unwind(){
    using namespace lighting_fixture;GateFixture fixture;original_reader=blocking_reader;original_writer=parallel_writer;
    std::thread a([]{write(reinterpret_cast<void*>(1),0,0,0,0,0,nullptr);});std::thread b([]{write(reinterpret_cast<void*>(2),0,0,0,0,0,nullptr);});
    const bool parallel=until([]{return bodies.load()==2;});const auto active_writers=writers.load();release=true;a.join();b.join();
    CHECK(parallel&&active_writers==2&&completed==2&&valid);CHECK(!writers.load()&&!readers.load());
    original_writer=nested_writer;CHECK(write(nullptr,0,0,0,0,0,nullptr)==0xabc&&valid);CHECK(!writers.load()&&!writer_depth);
    original_writer=throwing_writer;bool threw=false;try{write(nullptr,0,0,0,0,0,nullptr);}catch(const std::runtime_error&){threw=true;}CHECK(threw&&!writers.load()&&!writer_depth);
    original_reader=throwing_reader;threw=false;try{read(nullptr,nullptr,0,0);}catch(const std::runtime_error&){threw=true;}CHECK(threw&&!readers.load());
}
inline void lighting_handshake_stress(){
    using namespace lighting_fixture;GateFixture fixture;std::atomic<U32> payload{7},inside{0},violations{0};std::atomic<bool> start{false};
    std::thread reader([&]{while(!start.load())SwitchToThread();for(U32 i=0;i<20000;i++){ReadScope guard;if(guard.entered){inside.fetch_add(1);const auto a=payload.load();YieldProcessor();const auto b=payload.load();if(a!=b)violations++;inside.fetch_sub(1);}}});
    std::thread writer([&]{start=true;for(U32 i=0;i<10000;i++){WriteScope guard;if(inside.load())violations++;payload.fetch_add(1);}});
    reader.join();writer.join();CHECK(!violations.load()&&!readers.load()&&!writers.load());CHECK(payload==10007);
}
inline void lighting_native_trampoline_abi_witness_and_unwind(){
    using namespace lighting_fixture;ExecutableFixture fixture;
    fixture.game[0x1515ab]^=1;CHECK(!install_at(fixture.game,fixture.module)&&!reader_hook.allocation&&!enabled.load());fixture.game[0x1515ab]^=1;
    fixture.module[0xb278]^=1;CHECK(!install_at(fixture.game,fixture.module)&&!writer_hook.allocation&&!enabled.load());fixture.module[0xb278]^=1;
    CHECK(install_at(fixture.game,fixture.module)&&verify_ready());CHECK(install_at(fixture.game,fixture.module));
    const auto writer=reinterpret_cast<Writer>(fixture.module+writer_rva);observed={};valid=true;
    CHECK(writer(reinterpret_cast<void*>(0x12345678),0x89abcdef,0xfedcba98,0x1122334455667788ull,0x76543210,0x8877665544332211ull,marker_callback)==0xa53c0de);
    CHECK(observed[0]==0x12345678&&observed[1]==0x89abcdef&&observed[2]==0xfedcba98&&observed[3]==0x1122334455667788ull);
    CHECK(observed[4]==0x76543210&&observed[5]==0x8877665544332211ull&&observed[6]==reinterpret_cast<std::uintptr_t>(marker_callback)&&valid);CHECK(!writers.load()&&!writer_depth);
    struct Vector{void* data;std::size_t length,capacity;};struct Resource{U8 prefix[0x58]{};Vector* root=nullptr;};
    std::array<U8,64> frames{};for(U32 i=0;i<frames.size();i++)frames[i]=U8(i+1);Vector per_image{frames.data(),2,2},root{&per_image,1,1};Resource resource;resource.root=&root;
    std::array<U8,32> out{};const auto reader=reinterpret_cast<Reader>(fixture.game+reader_rva);
    CHECK((reader(&resource,out.data(),0,1)&255)==1&&std::memcmp(out.data(),frames.data()+32,32)==0);
    out.fill(0xab);CHECK(!(reader(&resource,out.data(),0,2)&255));for(auto value:out)CHECK(!value);
    out.fill(0xab);resource.root=nullptr;CHECK(!(reader(&resource,out.data(),0,0)&255));for(auto value:out)CHECK(value==0xab);
    resource.root=&root;{WriteScope guard;CHECK(!reader(&resource,out.data(),0,0));}for(auto value:out)CHECK(value==0xab);
    unwind(reader_hook,16,false);unwind(reader_hook,31,false);unwind(writer_hook,19,true);
    auto continuation=writer_hook.allocation+19;DWORD old=0;CHECK(VirtualProtect(continuation,15,PAGE_EXECUTE_READWRITE,&old)!=0);continuation[0]^=1;CHECK(!verify_ready());continuation[0]^=1;DWORD ignored=0;CHECK(VirtualProtect(continuation,15,old,&ignored)!=0);CHECK(verify_ready());
    fixture.module[0xb60d]^=1;CHECK(!verify_ready());fixture.module[0xb60d]^=1;CHECK(verify_ready());
    CHECK(!bind(nullptr));samase::PluginApi wrong_api{};wrong_api.version=43;CHECK(!bind(&wrong_api));
}
inline void lighting_queued_game_patch_and_first_file_gate(){
    using namespace lighting_fixture;
    {ExecutableFixture fixture;accept_queue=false;init_open=true;queue_calls=0;queued_address=nullptr;
        CHECK(!register_at(fixture.game,fixture.module,queue_patch));init_open=false;CHECK(queue_calls==1&&!enabled.load()&&!reader_hook.queued&&!writer_hook.allocation);CHECK(reader_original(fixture.game));CHECK(!verify_ready());
    }
    {ExecutableFixture fixture;accept_queue=true;init_open=true;queue_calls=0;queued_address=nullptr;
        CHECK(register_at(fixture.game,fixture.module,queue_patch));CHECK(register_at(fixture.game,fixture.module,queue_patch));init_open=false;
        CHECK(queue_calls==1&&reader_hook.queued&&!reader_hook.installed&&writer_hook.installed&&!enabled.load());CHECK(reader_original(fixture.game));CHECK(!verify_ready()&&!enabled.load());
        U32 untouched=0x1234;CHECK(!read(nullptr,&untouched,0,0)&&untouched==0x1234);CHECK(queued_address==fixture.game+reader_rva);
        valid=true;observed={};const auto writer=reinterpret_cast<Writer>(fixture.module+writer_rva);
        CHECK(writer(reinterpret_cast<void*>(0x42),1,2,3,4,5,marker_callback)==0xa53c0de&&valid);CHECK(!writers.load()&&!enabled.load());
        // Simulate the loader's own post-init image patch phase. No API call is
        // permitted when first-file verification subsequently opens the gate.
        std::memcpy(queued_address,queued_bytes.data(),16);FlushInstructionCache(GetCurrentProcess(),queued_address,16);
        CHECK(verify_ready()&&reader_hook.installed&&enabled.load()&&queue_calls==1);
        std::array<U8,0x60> resource{};CHECK(!(reinterpret_cast<Reader>(fixture.game+reader_rva)(resource.data(),&untouched,0,0)&255)&&untouched==0x1234);
    }
}
inline constexpr std::size_t rework_lighting_v5_group_count=5;
inline void run_rework_lighting_v5_groups(){lighting_drains_old_reader_and_skips_new();lighting_parallel_workers_nested_and_cpp_unwind();lighting_handshake_stress();lighting_native_trampoline_abi_witness_and_unwind();lighting_queued_game_patch_and_first_file_gate();}
}
