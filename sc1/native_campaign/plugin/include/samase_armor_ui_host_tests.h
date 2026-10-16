#pragma once
namespace host_test {
namespace armor_ui_fixture {
inline bw::DatTable* __cdecl tables(std::size_t* field_count){*field_count=dat_counts[0];return dat[0];}
struct Write {std::size_t address;std::vector<U8> bytes;};
inline std::vector<Write> writes;inline unsigned calls=0,reject_at=0;inline bool init_open=false;
inline U32 __cdecl writer(std::size_t address,const U8* bytes,std::size_t length){
    ++calls;if(!init_open || calls==reject_at)return 0;writes.push_back({address,std::vector<U8>(bytes,bytes+length)});return 1;
}
struct Image {
    U8* base=nullptr;bw::DatTable saved{};
    explicit Image(U32 armor_offset=0x1453568){
        using namespace samase_armor_ui;CHECK(!code && !queued);
        base=static_cast<U8*>(VirtualAlloc(nullptr,0x1460000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
        std::memcpy(base+call_rva,call_original,sizeof(call_original));std::memcpy(base+raw_rva,raw_stock,sizeof(raw_stock));
        std::memcpy(base+raw_rva+5,&armor_offset,4);
        std::memcpy(base+0x3f33a7,before_original,sizeof(before_original));std::memcpy(base+0x3f33c2,between_original,sizeof(between_original));
        std::memcpy(base+0x3f33d5,after_original,sizeof(after_original));std::memcpy(base+0x1c6280,id_original,sizeof(id_original));
        saved=dat[0][27];for(U32 id=0;id<228;id++)base[armor_offset+id]=static_cast<U8>(raw_value(0,27,id));
        dat[0][27]={base+armor_offset,1,228};
        const U8 harness[]={0x56,0x57,0x41,0x54,0x48,0x83,0xec,0x30,0x89,0xd6};
        std::memcpy(base+0x10000,harness,sizeof(harness));native_engine_hooks::absolute_jump(base+0x10000+sizeof(harness),base+call_rva);
        writes.clear();calls=reject_at=0;init_open=false;
        CHECK(FlushInstructionCache(GetCurrentProcess(),base,0x1460000));
    }
    ~Image(){abandon_session();dat[0][27]=saved;samase_armor_ui::dispose();writes.clear();if(base)VirtualFree(base,0,MEM_RELEASE);}
    bool queue(){init_open=true;const bool result=samase_armor_ui::register_at(base,tables,writer);init_open=false;return result;}
    void apply(){for(const auto& w:writes)std::memcpy(reinterpret_cast<void*>(w.address),w.bytes.data(),w.bytes.size());CHECK(FlushInstructionCache(GetCurrentProcess(),base,0x1460000));}
    void install(){CHECK(queue());CHECK(calls==2 && writes.size()==2);apply();CHECK(samase_armor_ui::verify_at(base));}
    std::array<U8,160> registers(bw::Unit* unit){
        std::vector<U8> entry={0x56,0x57,0x41,0x54,0x48,0x83,0xec,0x40,0x4c,0x89,0x44,0x24,0x20};
        const auto imm=[&](U8 prefix,U8 op,std::uint64_t value){entry.push_back(prefix);entry.push_back(op);const auto p=reinterpret_cast<const U8*>(&value);entry.insert(entry.end(),p,p+8);};
        imm(0x48,0xba,0x1122334455667788ull);imm(0x49,0xb8,0x8877665544332211ull);
        imm(0x49,0xb9,0x2233445566778899ull);imm(0x49,0xba,0x33445566778899aaull);imm(0x49,0xbb,0x445566778899aabbull);
        for(U32 i=0;i<96;i++)base[0x30000+i]=static_cast<U8>(i*7+3);imm(0x48,0xb8,reinterpret_cast<std::uintptr_t>(base+0x30000));
        for(U8 i=0;i<6;i++){const U8 op[]={0xf3,0x0f,0x6f,static_cast<U8>(0x40+(i<<3)),static_cast<U8>(16*i)};entry.insert(entry.end(),op,op+5);}
        std::memcpy(base+0x20000,entry.data(),entry.size());native_engine_hooks::absolute_jump(base+0x20000+entry.size(),base+samase_armor_ui::call_rva);
        std::vector<U8> finish={0x48,0x8b,0x44,0x24,0x20,0x48,0x89,0x50,0,0x4c,0x89,0x40,8,0x4c,0x89,0x48,16,
            0x4c,0x89,0x50,24,0x4c,0x89,0x58,32,0x48,0x89,0x88,0x90,0,0,0,0x4c,0x89,0xa0,0x98,0,0,0,0x48,0x83,0xc0,0x30};
        for(U8 i=0;i<6;i++){const U8 op[]={0xf3,0x0f,0x7f,static_cast<U8>(0x40+(i<<3)),static_cast<U8>(16*i)};finish.insert(finish.end(),op,op+5);}
        const U8 end[]={0x48,0x83,0xc4,0x40,0x41,0x5c,0x5f,0x5e,0xc3};finish.insert(finish.end(),end,end+sizeof(end));
        std::vector<U8> saved_tail(finish.size());std::memcpy(saved_tail.data(),base+0x3f33d5,finish.size());std::memcpy(base+0x3f33d5,finish.data(),finish.size());
        FlushInstructionCache(GetCurrentProcess(),base,0x1460000);
        std::array<U8,160> output{};using Observe=void (__cdecl*)(bw::Unit*,U32,U8*);reinterpret_cast<Observe>(base+0x20000)(unit,3,output.data());
        std::memcpy(base+0x3f33d5,saved_tail.data(),saved_tail.size());FlushInstructionCache(GetCurrentProcess(),base,0x1460000);return output;
    }
    std::uint64_t query(bw::Unit* unit,U32 upgrade){
        U8 saved_tail[32];std::memcpy(saved_tail,base+0x3f33d5,sizeof(saved_tail));
        // Return the unchanged upgrade value and UnitId alongside base armor.
        const U8 finish[]={0x89,0xf8,0x89,0xf2,0x48,0xc1,0xe2,0x20,0x48,0x09,0xd0,0x48,0xc1,0xe1,0x30,0x48,0x09,0xc8,
            0x48,0x83,0xc4,0x30,0x41,0x5c,0x5f,0x5e,0xc3};
        std::memcpy(base+0x3f33d5,finish,sizeof(finish));FlushInstructionCache(GetCurrentProcess(),base+0x3f33d5,sizeof(finish));
        using Query=std::uint64_t (__cdecl*)(bw::Unit*,U32);const auto result=reinterpret_cast<Query>(base+0x10000)(unit,upgrade);
        std::memcpy(base+0x3f33d5,saved_tail,sizeof(saved_tail));FlushInstructionCache(GetCurrentProcess(),base+0x3f33d5,sizeof(saved_tail));return result;
    }
};
inline void check_unwind(){
    using namespace samase_armor_ui;
    CHECK(code && queued && ready);const auto length=runtime.EndAddress;
    const U8 epilogue[]={0x48,0x81,0xc4,0xc8,0,0,0,0xc3};
    CHECK(length>sizeof(epilogue) && std::memcmp(code+length-sizeof(epilogue),epilogue,sizeof(epilogue))==0);
    DWORD body=7;for(DWORD i=7;i+10<length;i++)if(code[i]==0x48 && code[i+1]==0xb8){body=i;break;}
    // RtlVirtualUnwind consumes the actual registered x64 code/unwind metadata.
    // Contexts represent entry, allocated prologue, body, ADD epilogue and RET.
    struct Point{DWORD offset;bool allocated;};
    const Point points[]={{0,false},{7,true},{body,true},{length-8,true},{length-1,false}};
    alignas(16) std::uint64_t stack[128]{};auto entry=stack+64;
    constexpr std::uint64_t target=0x123456789abull;*entry=target;
    for(const auto point:points){
        CONTEXT context{};context.ContextFlags=CONTEXT_FULL;
        context.Rip=reinterpret_cast<DWORD64>(code+point.offset);
        context.Rsp=reinterpret_cast<DWORD64>(entry)-(point.allocated?0xc8:0);
        context.Rbx=0x1234;context.Rsi=0x2345;context.Rdi=0x3456;context.R12=0x4567;
        DWORD64 found_base=0;auto function=RtlLookupFunctionEntry(context.Rip,&found_base,nullptr);
        CHECK(function && found_base==reinterpret_cast<DWORD64>(code));
        PVOID handler_data=nullptr;DWORD64 establisher=0;
        RtlVirtualUnwind(UNW_FLAG_NHANDLER,found_base,context.Rip,function,&context,&handler_data,&establisher,nullptr);
        CHECK(context.Rip==target);CHECK(context.Rsp==reinterpret_cast<DWORD64>(entry+1));
        CHECK(context.Rbx==0x1234 && context.Rsi==0x2345 && context.Rdi==0x3456 && context.R12==0x4567);
    }
}
inline void expect(Image& image,bw::Unit* unit,U32 armor,U32 upgrade){CHECK(image.query(unit,upgrade)==((std::uint64_t(unit->unit_id)<<48)|(std::uint64_t(upgrade)<<32)|armor));}
inline GrowthSnapshot armor_snapshot(){GrowthSnapshot s{};for(U32 bit:{21u,26u,40u,50u,57u,61u,86u,95u,98u})s.talent_bits[bit/32]|=1u<<(bit%32);return s;}
}
void armor_ui_original_and_relocated_x64(){
    using namespace armor_ui_fixture;
    for(U32 offset:{0xe5ab30u,0x1453568u}){
        reset();for(U32 id=0;id<228;id++)write_entry(&dat[0][27],id,id%7);Image image(offset);
        for(U32 id:{0u,3u,4u,32u,37u,39u,43u,62u,65u,70u,83u,98u,227u}){
            auto unit=add(id,1,0,0);for(U32 level:{0u,1u,3u,6u})expect(image,unit,id%7,level);
        }
        const auto native_registers=image.registers(units.data());
        image.install();check_unwind();const auto patched_registers=image.registers(units.data());
        CHECK(native_registers==patched_registers);
        const std::uint64_t expected_regs[]={0x1122334455667788ull,0x8877665544332211ull,0x2233445566778899ull,0x33445566778899aaull,0x445566778899aabbull};
        for(U32 i=0;i<5;i++){std::uint64_t got=0;std::memcpy(&got,patched_registers.data()+i*8,8);CHECK(got==expected_regs[i]);}
        for(U32 i=0;i<96;i++)CHECK(patched_registers[48+i]==static_cast<U8>(i*7+3));
        std::uint64_t id=0,image_register=0;std::memcpy(&id,patched_registers.data()+144,8);std::memcpy(&image_register,patched_registers.data()+152,8);
        CHECK(id==units[0].unit_id && image_register==reinterpret_cast<std::uintptr_t>(image.base));
        for(U32 i=0;i<count;i++)expect(image,units.data()+i,units[i].unit_id%7,3);
        CHECK(samase_armor_ui::verify_at(image.base));
        // A later SAMASE allocation changes its typed operand; this untouched
        // raw instruction remains writable without damaging our call/JMP.
        const U32 moved=offset+1024;std::memcpy(image.base+moved,dat[0][27].data,228);
        dat[0][27].data=image.base+moved;std::memcpy(image.base+samase_armor_ui::raw_rva+5,&moved,4);
        CHECK(samase_armor_ui::verify_at(image.base));
        for(U32 i=0;i<count;i++)expect(image,units.data()+i,units[i].unit_id%7,3);
    }
}
void armor_ui_all_talents_owner_cache(){
    using namespace armor_ui_fixture;reset();Image image;
    for(U32 id:{32u,3u,4u,39u,37u,43u,62u,65u,83u,60u})for(U32 owner:{1u,6u,11u})add(id,owner,0,0);
    CHECK(apply_snapshot(nullptr,armor_snapshot()));image.install();
    for(U32 i=0;i<count;i++){
        auto unit=units.data()+i;const auto expected=owner_stat(unit->player,{0,27,unit->unit_id});
        for(U32 level:{0u,1u,3u,6u})expect(image,unit,expected,level);
        U32 cached=0;CHECK(max_hp_cache::read_armor(unit,cached) && cached==expected);
        if(unit->player!=1)CHECK(cached==original_stat({0,27,unit->unit_id}));
    }
    for(auto bit:{21u,26u,40u,50u,57u,61u,86u,95u,98u})for(const auto& patch:frozen::patches)if(patch.bit==bit && patch.table==0 && patch.field==27){
        auto own=add(patch.id,1,0,0);CHECK(max_hp_cache::publish());CHECK(owner_stat(1,{0,27,patch.id})==original_stat({0,27,patch.id})+patch.numerator);
        expect(image,own,owner_stat(1,{0,27,patch.id}),2);
    }
    CHECK(samase_armor_ui::verify_at(image.base));
}
void armor_ui_isolation_lifecycle_and_fallback(){
    using namespace armor_ui_fixture;reset();Image image;auto unit=add(32,1,0,0),enemy=add(32,6,0,0);
    const auto original=original_stat({0,27,32});CHECK(apply_snapshot(nullptr,armor_snapshot()));image.install();expect(image,unit,original+1,3);
    {OwnerDatScope scope(1,1,unit);expect(image,enemy,original,3);expect(image,unit,original+1,3);}
    CHECK(raw_value(0,27,32)==original);
    unit->flags|=0x40000000u;expect(image,unit,original,3);unit->flags&=~0x40000000u;
    unit->player=6;expect(image,unit,original,3);unit->player=11;expect(image,unit,original,3);unit->player=1;unit->minor_unique_index++;expect(image,unit,original+1,3);
    max_hp_cache::sequence.fetch_add(1);expect(image,unit,original,3);max_hp_cache::sequence.fetch_add(1);expect(image,unit,original+1,3);
    U32 value=999;CHECK(!max_hp_cache::read_armor(nullptr,value) && value==999);
    bw::Unit external{};external.unit_id=32;external.player=1;expect(image,&external,original,3);
    CHECK(!max_hp_cache::read_armor(reinterpret_cast<const bw::Unit*>(reinterpret_cast<const U8*>(unit)+1),value));
    max_hp_cache::reset();expect(image,unit,original,3);CHECK(max_hp_cache::publish(true));expect(image,unit,original+1,3);
    // Descriptor/data relocation after bind must be respected by fallback.
    std::array<U8,228> replaced{};replaced[32]=5;auto saved=dat[0][27];dat[0][27].data=replaced.data();
    max_hp_cache::reset();expect(image,unit,5,3);dat[0][27]=saved;
    abandon_session();expect(image,unit,original,3);
}
void armor_ui_registration_and_integrity(){
    using namespace armor_ui_fixture;using namespace samase_armor_ui;
    {reset();Image image;CHECK(!bind(nullptr));CHECK(!register_at(image.base,nullptr,writer));CHECK(!register_at(image.base,tables,nullptr));
        for(U32 rva:{call_rva,skip_rva,raw_rva,0x3f33a7u,0x3f33c2u,0x3f33d5u,0x1c6280u}){auto saved=image.base[rva];image.base[rva]^=1;CHECK(!image.queue());CHECK(!code && writes.empty());image.base[rva]=saved;}
        auto descriptor=dat[0][27];dat[0][27].data=static_cast<U8*>(dat[0][27].data)+1;CHECK(!image.queue());dat[0][27]=descriptor;
        dat[0][27].entry_size=2;CHECK(!image.queue());dat[0][27]=descriptor;
        dat[0][27].entries=227;CHECK(!image.queue());dat[0][27]=descriptor;
        reject_at=1;CHECK(!image.queue());CHECK(!code && writes.empty());reject_at=0;calls=0;
        CHECK(image.queue());CHECK(!verify_at(image.base));image.apply();CHECK(verify_at(image.base));
        for(U32 rva:{call_rva,skip_rva,raw_rva,0x3f33a7u,0x3f33c2u,0x3f33d5u,0x1c6280u}){auto saved=image.base[rva];image.base[rva]^=1;CHECK(!verify_at(image.base));CHECK(!activated.load());image.base[rva]=saved;CHECK(verify_at(image.base));}
    }
    {reset();Image image;auto unit=add(32,1,0,0);CHECK(apply_snapshot(nullptr,armor_snapshot()));const auto original=original_stat({0,27,32});
        reject_at=2;CHECK(!image.queue());CHECK(code && writes.size()==1 && !activated.load());image.apply();
        // A partial init registration keeps the call executable; the retained
        // native raw load overwrites EDI and produces the original value.
        expect(image,unit,original,3);CHECK(!verify_at(image.base));
    }
}
inline constexpr std::size_t samase_armor_ui_group_count=4;
void run_samase_armor_ui_groups(){armor_ui_original_and_relocated_x64();armor_ui_all_talents_owner_cache();armor_ui_isolation_lifecycle_and_fallback();armor_ui_registration_and_integrity();}
}
