#pragma once
// Windows' real unwinder and executable private memory, with the production
// installer and exact pinned prologues. No game process or user data access.
namespace host_test {
namespace trampoline_unwind_test {
using native_engine_hooks::Hook;
enum class Frame {Leaf,Stack40,Rbx32,AddHp,Weapon};
inline void unwind_boundary(const Hook& hook,std::size_t offset,Frame kind){
    alignas(16) DWORD64 memory[128]{};
    for(auto& word:memory)word=0xdeadbeef;
    auto caller=memory+80;
    constexpr DWORD64 expected_return=0x123456789abc,rbx=0x123401,rbp=0x123402,rdi=0x123403,r13=0x123404;
    *caller=expected_return;
    CONTEXT c{};c.ContextFlags=CONTEXT_ALL;c.Rip=reinterpret_cast<DWORD64>(hook.allocation+offset);
    c.Rbx=rbx;c.Rbp=rbp;c.Rdi=rdi;c.R13=r13;std::size_t depth=0;
    // Stack effects follow the actual instruction boundaries, independently
    // of the copied UNWIND_INFO being tested.
    if(kind==Frame::Stack40){if(offset>=4)depth=5;}
    if(kind==Frame::Rbx32){if(offset>=2){caller[-1]=rbx;depth=1;}if(offset>=6)depth=5;}
    if(kind==Frame::AddHp){
        if(offset>=5)caller[1]=rbx;
        if(offset>=6){caller[-1]=rdi;depth=1;}
        if(offset>=10)depth=5;
        if(offset>=16)c.Rbx=0x987654; // mov rbx,rcx is in the copied prefix.
    }
    if(kind==Frame::Weapon){
        if(offset>=2){caller[-1]=rbx;depth=1;}
        if(offset>=3){caller[-2]=rbp;depth=2;}
        if(offset>=4){caller[-3]=rdi;depth=3;}
        if(offset>=6){caller[-4]=r13;depth=4;}
        if(offset>=10)depth=11;
    }
    c.Rsp=reinterpret_cast<DWORD64>(caller-depth);
    PVOID handler=nullptr;DWORD64 establisher=0,image=0;
    const auto function=RtlLookupFunctionEntry(c.Rip,&image,nullptr);
    CHECK(function==&hook.runtime);CHECK(image==reinterpret_cast<DWORD64>(hook.allocation));
    RtlVirtualUnwind(UNW_FLAG_NHANDLER,image,c.Rip,function,&c,&handler,&establisher,nullptr);
    CHECK(c.Rip==expected_return);CHECK(c.Rsp==reinterpret_cast<DWORD64>(caller+1));
    CHECK(c.Rbx==rbx && c.Rbp==rbp && c.Rdi==rdi && c.R13==r13);
}
inline void verify(const Hook& hook,const native_engine_hooks::Spec& spec,Frame frame,std::initializer_list<std::size_t> boundaries){
    CHECK(hook.allocation[spec.stolen]==0x2e && hook.allocation[spec.stolen+1]==0xff && hook.allocation[spec.stolen+2]==0x25);
    CHECK(hook.runtime.EndAddress==spec.stolen+native_engine_hooks::continuation_jump_size);
    CHECK(std::memcmp(hook.allocation+128,spec.unwind,spec.unwind_size)==0); // No altered prolog size or unwind actions.
    for(const auto offset:boundaries)unwind_boundary(hook,offset,frame);
    unwind_boundary(hook,spec.stolen,frame); // The continuation instruction's actual RIP.
}
inline U32 __cdecl accept(std::size_t,const U8*,std::size_t){return 1;}
inline int __cdecl unused_detour(){return 99;}
inline void native_paths(bool queued){
    using namespace native_engine_hooks;
    const Spec* sources[]={&combat_effects::weapon_spec,&max_hp_engine::add_spec};
    for(std::size_t n=0;n<std::size(sources);n++){
        auto base=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
        auto spec=*sources[n];spec.rva=128;spec.witnesses=nullptr;spec.witness_count=0;
        std::memcpy(base+spec.rva,spec.prologue,spec.stolen);Hook hook{};
        if(queued)CHECK(register_at(base,spec,reinterpret_cast<void*>(unused_detour),hook,accept));
        else CHECK(install_at(base,spec,reinterpret_cast<void*>(unused_detour),hook));
        if(n==0)verify(hook,spec,Frame::Weapon,{0,2,3,4,6,10});
        else verify(hook,spec,Frame::AddHp,{0,5,6,10,13});
        // Only the continuation gets a prefix; the actual entry patch remains
        // the original 14-byte FF25 form and retains the original overwrite size.
        if(!queued)CHECK(base[128]==0xff && base[129]==0x25);
        CHECK(RtlDeleteFunctionTable(&hook.runtime)!=0);CHECK(VirtualFree(hook.allocation,0,MEM_RELEASE)!=0);CHECK(VirtualFree(base,0,MEM_RELEASE)!=0);
    }
}
inline void direct_path(){native_paths(false);}
inline void loader_path(){native_paths(true);}
inline void maximum_hp_paths(){
    reset();hp_engine_fixture::Image image;image.install();
    for(std::size_t i=0;i<5;i++){
        const auto& hook=max_hp_engine::hooks[i];const auto& spec=max_hp_engine::runtime_entries[i].spec;
        if(i==0 || i==2)verify(hook,spec,Frame::Leaf,{0,7});
        else if(i==1)verify(hook,spec,Frame::Stack40,{0,4,11});
        else verify(hook,spec,Frame::Rbx32,{0,2,6,13});
    }
    verify(max_hp_engine::add_hook,max_hp_engine::runtime_add_spec,Frame::AddHp,{0,5,6,10,13});
    // Original x64 getter bodies execute after the new continuation; both
    // stack-bearing and leaf fallbacks must still return actual original DAT.
    auto unit=add(0,11,0,0,10240);hp_engine_fixture::expect(image,unit,10240);
}
inline void cpu_register_and_flag_preservation(){
    using namespace native_engine_hooks;
    // mov rax,imm64; cmp ecx,edx; nop; nop -> continuation. The target records
    // RAX and ZF before any arithmetic; it uses no nonvolatile registers.
    const U8 prologue[]={0x48,0xb8,0x88,0x77,0x66,0x55,0x44,0x33,0x22,0x11,0x39,0xd1,0x90,0x90};
    const U8 tail[]={0x49,0x89,0x00,0x41,0x0f,0x94,0x40,0x08,0xc3};
    const U8 unwind[]={1,0,0,0};
    auto base=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
    std::memcpy(base+128,prologue,sizeof(prologue));std::memcpy(base+128+sizeof(prologue),tail,sizeof(tail));
    Spec spec{128,prologue,sizeof(prologue),unwind,sizeof(unwind),nullptr,0};Hook hook{};
    CHECK(install_at(base,spec,reinterpret_cast<void*>(unused_detour),hook));
    using Run=DWORD64 (__cdecl*)(U32,U32,DWORD64*);
    const auto run=reinterpret_cast<Run>(hook.trampoline);
    DWORD64 observed[2]{};
    CHECK(run(7,7,observed)==0x1122334455667788);CHECK(observed[0]==0x1122334455667788 && observed[1]==1);
    CHECK(run(7,8,observed)==0x1122334455667788);CHECK(observed[0]==0x1122334455667788 && observed[1]==0);
    CHECK(reinterpret_cast<int (__cdecl*)()>(base+128)()==99);
    verify(hook,spec,Frame::Leaf,{0,10,12,13});
    CHECK(RtlDeleteFunctionTable(&hook.runtime)!=0);CHECK(VirtualFree(hook.allocation,0,MEM_RELEASE)!=0);CHECK(VirtualFree(base,0,MEM_RELEASE)!=0);
}
}
inline constexpr std::size_t trampoline_unwind_group_count=4;
inline void run_trampoline_unwind_groups(){
    trampoline_unwind_test::direct_path();trampoline_unwind_test::loader_path();
    trampoline_unwind_test::maximum_hp_paths();trampoline_unwind_test::cpu_register_and_flag_preservation();
}
}
