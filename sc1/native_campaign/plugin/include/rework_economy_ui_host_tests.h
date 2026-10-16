#pragma once
#include <thread>
#include "rework_economy_ui_specs.generated.h"
// Production publication and the exact executable x64 relays in an owned host.
namespace host_test {
inline constexpr std::size_t rework_economy_ui_group_count=4;
namespace economy_ui_fixture {
inline U8* image=nullptr;inline U32 writes=0,reject_write=0;
inline U32 __cdecl writer(std::size_t address,const U8* bytes,std::size_t length){
    ++writes;if(writes==reject_write)return 0;
    CHECK(image && (address==reinterpret_cast<std::size_t>(image+rework_economy_ui::cost_site) ||
        std::any_of(std::begin(rework_economy_ui::supply_sites),std::end(rework_economy_ui::supply_sites),[&](U32 site){return address==reinterpret_cast<std::size_t>(image+site);})));
    std::memcpy(reinterpret_cast<void*>(address),bytes,length);return 1;
}
inline void cleanup(){
    using namespace rework_economy_ui;
    rework_economy_ui::reset();if(code){CHECK(RtlDeleteFunctionTable(unwind.data())!=0);CHECK(VirtualFree(code,0,MEM_RELEASE)!=0);}
    code=nullptr;module=nullptr;native_supply=nullptr;queued=false;ready=false;passthrough=false;
    if(image){CHECK(VirtualFree(image,0,MEM_RELEASE)!=0);image=nullptr;}writes=0;reject_write=0;
}
inline void prepare(U32 relocation=0){
    using namespace rework_economy_ui;
    cleanup();image=static_cast<U8*>(VirtualAlloc(nullptr,native_engine_hooks::kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(image);
    std::memcpy(image+0x3ee1f3,rework_economy_ui_specs::production_branch,sizeof(rework_economy_ui_specs::production_branch));
    std::memcpy(image+cost_site,cost_original,sizeof(cost_original));std::memcpy(image+0x3ee1f3,unit_id_witness,sizeof(unit_id_witness));
    std::memcpy(image+cost_site+sizeof(cost_original),final_witness,sizeof(final_witness));
    for(U32 i=0;i<3;i++){std::memcpy(image+supply_sites[i],supply_original[i],9);const std::int32_t offset=0xe5cc30+relocation;std::memcpy(image+supply_sites[i]+5,&offset,4);}
    for(U32 i=0;i<4;i++){std::memcpy(image+cost_reads[i],cost_read_original[i],9);const std::int32_t offset=(i%2 ? 0xe5c310:0xe5c4e0)+relocation;std::memcpy(image+cost_reads[i]+5,&offset,4);}
    for(U32 id=0;id<228;id++){auto mineral=std::uint16_t(original_stat({0,40,id})),gas=std::uint16_t(original_stat({0,41,id}));
        std::memcpy(image+0xe5c310+relocation+id*2,&mineral,2);std::memcpy(image+0xe5c4e0+relocation+id*2,&gas,2);image[0xe5cc30+relocation+id]=U8(original_stat({0,46,id}));
        const U32 flags=original_stat({0,22,id});std::memcpy(image+0xe5a3e0+id*4,&flags,4);image[0xe5ca50+id]=U8(original_stat({0,44,id}));}
}
inline bool install(U32 relocation=0){using namespace rework_economy_ui;return register_at(image,image+0xe5c310+relocation,image+0xe5c4e0+relocation,image+0xe5cc30+relocation,writer);}
inline bool verified(U32 relocation=0){using namespace rework_economy_ui;return verify_at(image+0xe5c310+relocation,image+0xe5c4e0+relocation,image+0xe5cc30+relocation);}
inline void selection(bw::Unit* unit){std::memcpy(image+rework_economy_ui::selected_rva,&unit,sizeof(unit));}
inline U8* executable(const std::vector<U8>& bytes){auto p=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(p);std::memcpy(p,bytes.data(),bytes.size());DWORD old=0;CHECK(VirtualProtect(p,4096,PAGE_EXECUTE_READ,&old));CHECK(FlushInstructionCache(GetCurrentProcess(),p,bytes.size()));return p;}
inline void append64(std::vector<U8>& out,std::uintptr_t value){for(U32 i=0;i<8;i++)out.push_back(U8(value>>(i*8)));}
inline void invoke_cost(U32 id,U32 mineral,U32 gas){
    // Win64(button*,mineral,gas) -> R14=button,EAX=mineral,ECX=gas.
    std::vector<U8> bytes={0x41,0x56,0x48,0x83,0xec,0x20,0x49,0x89,0xce,0x89,0xd0,0x44,0x89,0xc1,0x49,0xbb};
    append64(bytes,reinterpret_cast<std::uintptr_t>(rework_economy_ui::code));
    for(int b:{0x41,0xff,0xd3,0x48,0x83,0xc4,0x20,0x41,0x5e,0xc3})bytes.push_back(U8(b));
    auto helper=executable(bytes);U8 button[32]{};const auto type=std::uint16_t(id);std::memcpy(button+0x1a,&type,2);
    reinterpret_cast<void (__cdecl*)(const void*,U32,U32)>(helper)(button,mineral,gas);CHECK(VirtualFree(helper,0,MEM_RELEASE));
}
inline void invoke_native_cost(U32 id,bool with_supply){
    namespace ui=rework_economy_ui;
    // Execute the production formatter's actual global-array read bytes,
    // followed by the installed relay's real stores. No assumed total unit
    // price is fed to the adapter: morph components come from native DAT.
    std::vector<U8> bytes={0x41,0x56,0x48,0x83,0xec,0x20,0x49,0x89,0xce,0x49,0xb8};append64(bytes,reinterpret_cast<std::uintptr_t>(image));
    if(with_supply)bytes.insert(bytes.end(),std::begin(ui::unit_id_witness),std::end(ui::unit_id_witness));
    else for(int b:{0x41,0x0f,0xb7,0x46,0x1a})bytes.push_back(U8(b));
    for(U32 i=with_supply ? 2u:0u;i<(with_supply ? 4u:2u);i++)bytes.insert(bytes.end(),ui::read_witnesses[i],ui::read_witnesses[i]+9);
    bytes.push_back(0x49);bytes.push_back(0xbb);append64(bytes,reinterpret_cast<std::uintptr_t>(ui::code));
    for(int b:{0x41,0xff,0xd3,0x48,0x83,0xc4,0x20,0x41,0x5e,0xc3})bytes.push_back(U8(b));
    auto helper=executable(bytes);U8 button[32]{};const auto type=std::uint16_t(id);std::memcpy(button+0x1a,&type,2);
    reinterpret_cast<void (__cdecl*)(const void*)>(helper)(button);CHECK(VirtualFree(helper,0,MEM_RELEASE));
}
inline std::array<std::uint16_t,8> invoke_native_production(U32 id){
    namespace ui=rework_economy_ui;
    // Call the complete219-byte native unit-production calculation at its
    // original RVA, including original race/two-per-egg arithmetic and the
    // four installed adapter branches. Only its later text-formatting
    // continuation is replaced with RET in this owned synthetic procedure.
    auto continuation=image+ui::cost_site+14;continuation[0]=0xc3;
    DWORD old=0;CHECK(VirtualProtect(image+0x3ee000,4096,PAGE_EXECUTE_READ,&old));CHECK(FlushInstructionCache(GetCurrentProcess(),image+0x3ee000,4096));
    std::vector<U8> bytes={0x57,0x41,0x56,0x48,0x83,0xec,0x28,0x49,0x89,0xce,0x49,0xbb};append64(bytes,reinterpret_cast<std::uintptr_t>(image+0x3ee1f3));
    for(int b:{0x41,0xff,0xd3,0x48,0x83,0xc4,0x28,0x41,0x5e,0x5f,0xc3})bytes.push_back(U8(b));
    auto helper=executable(bytes);U8 button[32]{};const auto type=std::uint16_t(id);std::memcpy(button+0x1a,&type,2);
    reinterpret_cast<void (__cdecl*)(const void*)>(helper)(button);CHECK(VirtualFree(helper,0,MEM_RELEASE));
    DWORD ignored=0;CHECK(VirtualProtect(image+0x3ee000,4096,old,&ignored));std::memcpy(continuation,ui::final_witness,sizeof(ui::final_witness));
    std::array<std::uint16_t,8> result{};std::memcpy(result.data(),image+ui::output_rva,sizeof(result));return result;
}
struct Registers {std::uint64_t rax,r8,r9,r10,flags,rcx,r11;};
inline Registers invoke_supply(U32 relay,U32 id){
    std::vector<U8> bytes={0x48,0x83,0xec,0x28,0x41,0x89,0xc9,0x48,0xb8};append64(bytes,0x123456789abcdef0ull);
    for(int b:{0x41,0xb8,0x67,0x45,0x23,0x01,0x41,0xba,0x98,0x76,0x54,0x32,0x49,0xbb})bytes.push_back(U8(b));
    append64(bytes,reinterpret_cast<std::uintptr_t>(rework_economy_ui::code+relay*128));
    for(int b:{0xf9,0x41,0xff,0xd3,0x48,0x89,0x02,0x4c,0x89,0x42,0x08,0x4c,0x89,0x4a,0x10,0x4c,0x89,0x52,0x18,
        0x9c,0x58,0x48,0x89,0x42,0x20,0x48,0x89,0x4a,0x28,0x4c,0x89,0x5a,0x30,0x48,0x83,0xc4,0x28,0xc3})bytes.push_back(U8(b));
    auto helper=executable(bytes);Registers result{};reinterpret_cast<void (__cdecl*)(U32,Registers*)>(helper)(id,&result);CHECK(VirtualFree(helper,0,MEM_RELEASE));return result;
}
}
inline void rework_economy_ui_prices_and_snapshot_epochs(){
    namespace ui=rework_economy_ui;
    reset();ui::reset();auto own=add(35,1,500,500);auto enemy=add(35,6,600,600);refresh_units();
    GrowthSnapshot s{};s.wire_version=2;
    for(U32 ordinal:{7u,24u,117u,151u,152u,153u,154u,155u,156u,157u,158u,159u,160u}){const U32 bit=238+ordinal;s.talent_bits[bit/32]|=1u<<(bit%32);}
    CHECK(apply_snapshot(nullptr,s));CHECK(ui::publish(true));
    struct Price{U32 id,mineral,gas;};const Price cases[]={{0,40,0},{5,120,80},{12,320,240},{37,40,0},{103,40,80},{45,80,80},{44,40,80},{65,80,0},{66,100,40},{72,280,200},
        {106,280,0},{131,210,0},{154,280,0},{73,13,0},{85,8,0},{41,100,0},{132,150,100}};
    for(const auto& row:cases){const auto value=ui::costs(own,row.id,999,888);CHECK(U32(value&65535u)==row.mineral && U32(value>>16)==row.gas);
        CHECK(ui::costs(enemy,row.id,999,888)==ui::pack(original_stat({0,40,row.id}),original_stat({0,41,row.id}),0));}
    std::uint64_t value=0;CHECK(ui::read(own,41,value) && (value>>32)==4);
    auto copied=*own;CHECK(!ui::read(&copied,41,value));CHECK(!ui::read(reinterpret_cast<bw::Unit*>(reinterpret_cast<U8*>(own)+1),41,value));
    own->flags|=0x40000000u;CHECK(ui::costs(own,0,91,23)==ui::pack(91,23,0));own->flags&=~0x40000000u;
    ui::sequence.fetch_add(1);CHECK(ui::costs(own,0,91,23)==ui::pack(91,23,0));ui::sequence.fetch_add(1);
    ui::reset();CHECK(ui::costs(own,41,50,0)==ui::pack(50,0,0));
    reset();ui::reset();own=add(7,1,500,500);refresh_units();GrowthSnapshot earlier{};earlier.wire_version=2;earlier.completed_phase=1;
    CHECK(apply_snapshot(nullptr,earlier));CHECK(ui::publish(true));CHECK(ui::costs(own,0,91,23)==ui::pack(50,0,0));
    earlier.completed_phase=2;earlier.talent_bits[(238+151)/32]|=1u<<((238+151)%32);CHECK(apply_snapshot(nullptr,earlier));CHECK(ui::publish(true));CHECK(ui::costs(own,0,91,23)==ui::pack(40,0,0));
}
inline void rework_economy_ui_real_relays_and_unwind(){
    namespace ui=rework_economy_ui;using namespace economy_ui_fixture;
    reset();ui::reset();auto own=add(35,1,500,500);refresh_units();GrowthSnapshot s{};s.wire_version=2;
    for(U32 ordinal:{7u,24u,117u,151u,155u,157u}){const U32 bit=238+ordinal;s.talent_bits[bit/32]|=1u<<(bit%32);}CHECK(apply_snapshot(nullptr,s));CHECK(ui::publish(true));
    prepare();CHECK(ui::publish(true));selection(own);CHECK(install());CHECK(writes==4 && !ui::ready && ui::queued);CHECK(verified());
    std::vector<U8> before(image+0xe5c310,image+0xe5cc30+228);
    for(const auto& row:std::array<std::array<U32,5>,4>{{{{41,50,0,100,0}},{{85,15,0,8,0}},{{44,50,100,40,80}},{{0,50,0,40,0}}}}){
        invoke_cost(row[0],row[1],row[2]);std::uint16_t result[2]{};std::memcpy(result,image+ui::output_rva,4);CHECK(result[0]==row[3] && result[1]==row[4]);}
    const std::array<U32,3> morphs[]={{{44,40,80}},{{62,120,40}},{{103,40,80}},{{132,150,100}}};
    for(bool branch:{false,true})for(const auto& row:morphs){invoke_native_cost(row[0],branch);std::uint16_t result[2]{};std::memcpy(result,image+ui::output_rva,4);CHECK(result[0]==row[1] && result[1]==row[2]);}
    const auto twin=invoke_native_production(41);CHECK(twin[0]==100 && twin[1]==0 && twin[5]==0 && twin[6]==0 && twin[7]==2);
    const auto pair=invoke_native_production(37);CHECK(pair[0]==50 && pair[7]==1); // both native two-units-per-egg and /2 execute.
    const auto marine=invoke_native_production(0);CHECK(marine[0]==40 && marine[6]==1 && marine[7]==0);
    const auto carrier=invoke_native_production(72);CHECK(carrier[0]==350 && carrier[1]==250 && carrier[5]==6);
    for(const auto& row:morphs){const auto result=invoke_native_production(row[0]);CHECK(result[0]==row[1] && result[1]==row[2]);}
    CHECK(verified());
    // A second call with already discounted register values still shows the
    // same owner price: discounts are planned once, never applied to UI input.
    invoke_cost(44,40,80);std::uint16_t once[2]{};std::memcpy(once,image+ui::output_rva,4);CHECK(once[0]==40 && once[1]==80);
    auto foreign=add(35,6,600,600);refresh_units();CHECK(ui::publish(true));selection(foreign);
    for(const auto& row:morphs){invoke_native_cost(row[0],true);std::uint16_t result[2]{};std::memcpy(result,image+ui::output_rva,4);CHECK(result[0]==original_stat({0,40,row[0]}) && result[1]==original_stat({0,41,row[0]}));}
    selection(own);
    for(U32 relay=1;relay<=3;relay++){
        const auto r=invoke_supply(relay,41);CHECK((relay==3 ? r.rax:r.r10)==4);CHECK((relay==3 ? r.r10:r.rax)==(relay==3 ? 0x32547698ull:0x123456789abcdef0ull));
        CHECK(r.r8==0x1234567 && r.r9==41 && r.rcx==41 && (r.flags&1));CHECK(r.r11==reinterpret_cast<std::uintptr_t>(ui::code+relay*128));
        const auto zergling=invoke_supply(relay,37);CHECK((relay==3 ? zergling.rax:zergling.r10)==1); // unchanged native2-per-egg then /2 gives1.
    }
    CHECK(std::equal(before.begin(),before.end(),image+0xe5c310));
    for(U32 i=0;i<4;i++){
        DWORD64 image_base=0;const auto address=reinterpret_cast<DWORD64>(ui::code+i*128+16);const auto entry=RtlLookupFunctionEntry(address,&image_base,nullptr);CHECK(entry==&ui::unwind[i]);
        std::uint64_t stack[20]{};stack[13]=0x1122334455667788ull;CONTEXT context{};context.Rip=address;context.Rsp=reinterpret_cast<DWORD64>(stack);void* handler=nullptr;DWORD64 frame=0;
        RtlVirtualUnwind(UNW_FLAG_NHANDLER,image_base,address,entry,&context,&handler,&frame,nullptr);
        if(context.Rip!=stack[13] || context.Rsp!=reinterpret_cast<DWORD64>(stack)+112)throw std::runtime_error("economy unwind relay"+std::to_string(i)+" rip "+std::to_string(context.Rip)+" rsp delta "+std::to_string(context.Rsp-reinterpret_cast<DWORD64>(stack)));
        CHECK(context.Rip==stack[13] && context.Rsp==reinterpret_cast<DWORD64>(stack)+112);
    }
    image[ui::cost_reads[0]]^=1;CHECK(!verified());invoke_cost(41,50,0);std::uint16_t fallback=0;std::memcpy(&fallback,image+ui::output_rva,2);CHECK(fallback==50);
    CHECK(invoke_supply(1,41).r10==2);image[ui::cost_reads[0]]^=1;CHECK(verified());cleanup();
}
inline void rework_economy_ui_relocations_and_rejected_witnesses(){
    using namespace economy_ui_fixture;namespace ui=rework_economy_ui;
    reset();prepare(0x20000);CHECK(install(0x20000));CHECK(verified(0x20000));
    // A subsequent legitimate DAT reallocation updates only the witnessed
    // displacement, and baseline supply fallback follows the new public array.
    for(U32 i=0;i<4;i++){const std::int32_t target=(i%2 ? 0xe5c310:0xe5c4e0)+0x30000;std::memcpy(image+ui::cost_reads[i]+5,&target,4);}
    image[0xe5cc30+0x30000+41]=6;CHECK(verified(0x30000));selection(nullptr);CHECK(invoke_supply(1,41).r10==6);cleanup();
    prepare();image[ui::cost_reads[1]+5]^=1;CHECK(!install());CHECK(writes==0 && !ui::queued);cleanup();
    prepare();image[ui::supply_sites[1]]^=1;CHECK(!install());CHECK(writes==0 && !ui::queued);cleanup();
    prepare();image[0x3ee1f3]^=1;CHECK(!install());CHECK(writes==0 && !ui::queued);cleanup();
    prepare();reject_write=3;CHECK(!install());CHECK(writes==3 && ui::queued && ui::code && ui::passthrough);CHECK(!verified());cleanup();
}
inline void rework_economy_ui_concurrent_publication_and_fallback(){
    namespace ui=rework_economy_ui;
    reset();ui::reset();auto own=add(7,1,500,500);refresh_units();GrowthSnapshot baseline{};baseline.wire_version=2;CHECK(apply_snapshot(nullptr,baseline));CHECK(ui::publish(true));
    std::atomic<bool> stop{false},bad{false};std::thread renderer([&]{while(!stop.load()){
        const auto pair=ui::costs(own,5,777,888);if(pair!=ui::pack(150,100,0) && pair!=ui::pack(120,80,0) && pair!=ui::pack(777,888,0))bad=true;
    }});
    try {for(U32 i=0;i<40;i++){if(i==20){auto s=baseline;s.completed_phase=2;const U32 bit=238+152;s.talent_bits[bit/32]|=1u<<(bit%32);CHECK(apply_snapshot(nullptr,s));}CHECK(ui::publish(true));}}
    catch(...){stop=true;renderer.join();throw;}
    stop=true;renderer.join();CHECK(!bad);ui::reset();
}
inline void run_rework_economy_ui_groups(){
    rework_economy_ui_prices_and_snapshot_epochs();rework_economy_ui_real_relays_and_unwind();
    rework_economy_ui_relocations_and_rejected_witnesses();rework_economy_ui_concurrent_publication_and_fallback();
}
}
