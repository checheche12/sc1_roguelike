#pragma once
// Real x64 execution of the pinned five getters in private synthetic memory.
// No game executable/process, installation, database or GUI is accessed.
namespace host_test {
namespace hp_engine_fixture {
struct Queued {std::size_t address;std::vector<U8> bytes;};
inline std::vector<Queued> writes;
inline bool init_open=false,reject=false;
inline unsigned writer_calls=0,unsafe_original_reads=0;
inline bw::DatTable image_dat[14]{};
inline bw::DatTable* __cdecl get_images(std::size_t* field_count){*field_count=std::size(image_dat);return image_dat;}
inline samase::GenericFn __cdecl dat_factory(U32 id){return id==6 ? reinterpret_cast<samase::GenericFn>(get_images):nullptr;}
inline int __cdecl changing_original_composite(const bw::Unit*){++unsafe_original_reads;return 63;}
inline int __cdecl changing_original_points(const bw::Unit*){++unsafe_original_reads;return 50;}
inline U32 __cdecl writer(std::size_t address,const U8* bytes,std::size_t length){
    ++writer_calls;if(!init_open || reject)return 0;
    writes.push_back({address,std::vector<U8>(bytes,bytes+length)});return 1;
}
struct Image {
    U8* base=nullptr;U8* saved_base=nullptr;bw::DatTable saved_tables[3]{};
    Image(){
        using namespace max_hp_engine;
        for(auto& h:hooks)CHECK(!h.allocation && !h.queued && !h.installed);
        CHECK(!add_hook.allocation && !add_hook.queued && !add_hook.installed);
        saved_base=native_engine_hooks::verified_base;
        base=static_cast<U8*>(VirtualAlloc(nullptr,native_engine_hooks::kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base!=nullptr);
        for(const auto& entry:entries){
            std::memcpy(base+entry.spec.rva,entry.spec.prologue,entry.spec.stolen);
            for(std::size_t i=0;i<entry.spec.witness_count;i++){const auto& w=entry.spec.witnesses[i];std::memcpy(base+w.rva,w.expected,w.length);}
        }
        std::memcpy(base+add_spec.rva,add_original_bytes,sizeof(add_original_bytes));
        for(const auto& w:add_witnesses)std::memcpy(base+w.rva,w.expected,w.length);
        constexpr U8 unit_id[]={0x0f,0xb7,0x81,0x8c,0,0,0,0xc3},false_query[]={0x33,0xc0,0xc3};
        std::memcpy(base+0x1c6280,unit_id,sizeof(unit_id));std::memcpy(base+0x1c7a90,false_query,sizeof(false_query));std::memcpy(base+0x1c70e0,false_query,sizeof(false_query));
        constexpr U8 current_q8[]={0x8b,0x41,0x10,0xc3};
        constexpr U8 current_points[]={0x8b,0x41,0x10,0x05,0xff,0,0,0,0xc1,0xf8,0x08,0xc3};
        std::memcpy(base+0x1a05e0,current_q8,sizeof(current_q8));std::memcpy(base+0x1a0650,current_points,sizeof(current_points));
        for(U32 id=0;id<228;id++){hp(id,original_stat({0,8,id}));shields(id,static_cast<U8>(original_stat({0,6,id})),static_cast<std::uint16_t>(original_stat({0,7,id})));}
        for(U32 i=0;i<3;i++)saved_tables[i]=dat[0][i+6];
        dat[0][6].data=base+0xe59160;dat[0][7].data=base+0xe59250;dat[0][8].data=base+0xe59420;
        native_engine_hooks::verified_base=base;ready=false;writes.clear();writer_calls=0;init_open=false;reject=false;
        std::memset(image_dat,0,sizeof(image_dat));
        image_dat[10].data=base+0xe4bea0;image_dat[10].entry_size=8;image_dat[10].entries=999;
        CHECK(FlushInstructionCache(GetCurrentProcess(),base,native_engine_hooks::kImageSize)!=0);
    }
    ~Image(){
        abandon_session();for(U32 i=0;i<3;i++)dat[0][i+6]=saved_tables[i];
        init_open=false;writes.clear();
        for(auto& h:max_hp_engine::hooks){if(h.allocation){RtlDeleteFunctionTable(&h.runtime);VirtualFree(h.allocation,0,MEM_RELEASE);}h={};}
        auto& add=max_hp_engine::add_hook;if(add.allocation){RtlDeleteFunctionTable(&add.runtime);VirtualFree(add.allocation,0,MEM_RELEASE);}add={};max_hp_engine::original_add=nullptr;
        for(auto& f:max_hp_engine::originals)f=nullptr;
        max_hp_engine::ready=false;max_hp_engine::image_dat_getter=nullptr;native_engine_hooks::verified_base=saved_base;
        if(base)VirtualFree(base,0,MEM_RELEASE);
    }
    void hp(U32 id,U32 value){std::memcpy(base+0xe59420+id*4,&value,4);}
    void shields(U32 id,U8 enabled,std::uint16_t value){base[0xe59160+id]=enabled;std::memcpy(base+0xe59250+id*2,&value,2);}
    max_hp_engine::Query query(std::size_t n)const{return reinterpret_cast<max_hp_engine::Query>(base+max_hp_engine::entries[n].spec.rva);}
    bool queue(){samase::PluginApi local{};local.write_exe_memory=reinterpret_cast<samase::GenericFn>(writer);local.extended_dat=dat_factory;init_open=true;const bool result=max_hp_engine::bind(&local);init_open=false;return result;}
    void apply(){for(const auto& w:writes)std::memcpy(reinterpret_cast<void*>(w.address),w.bytes.data(),w.bytes.size());CHECK(FlushInstructionCache(GetCurrentProcess(),base,native_engine_hooks::kImageSize)!=0);}
    void install(){CHECK(queue());CHECK(writes.size()==6 && writer_calls==6);apply();CHECK(max_hp_engine::verify_installation());CHECK(max_hp_engine::ready);}
};
inline int displayed(U32 hp,int current){const int points=static_cast<int>(hp)>>8;if(points)return points;const int value=static_cast<int>(static_cast<U32>(current)+255u)>>8;return value?value:1;}
inline void expect(Image& image,bw::Unit* unit,U32 hp,int shield=0,int point_override=-1){
    const auto current=unit->flingy.hitpoints;const int points=point_override<0 ? displayed(hp,current):point_override;
    CHECK(image.query(0)(unit)==static_cast<int>(hp));
    CHECK(image.query(1)(unit)==points);
    CHECK(image.query(2)(unit)==static_cast<int>(hp)/3);
    CHECK(image.query(3)(unit)==(current<static_cast<int>(hp)?1:0));
    CHECK(image.query(4)(unit)==points+shield);
    CHECK(unit->flingy.hitpoints==current);
}
}
void hp_engine_original_x64(){
    using namespace hp_engine_fixture;reset();Image image;auto unit=add(0,1,0,0,40*256);
    expect(image,unit,40*256);unit->flingy.hitpoints=39*256;expect(image,unit,40*256);
    image.shields(0,1,23);expect(image,unit,40*256,23);image.shields(0,0,23);expect(image,unit,40*256);
    for(U32 value:{0u,1u,255u,256u,10241u})for(int current:{0,1,255,256,257,10240}){image.hp(0,value);unit->flingy.hitpoints=current;expect(image,unit,value);}
}
void hp_engine_owner_and_elite_x64(){
    using namespace hp_engine_fixture;reset();Image image;
    auto own=add(0,1,0,0,40*256),enemy=add(0,6,0,0,40*256),elite=add(0,6,0,0,40*256),neutral=add(0,11,0,0,40*256);
    GrowthSnapshot snapshot{};snapshot.talent_bits[0]=1u<<1;snapshot.curse_counts[2]=snapshot.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,snapshot));
    refresh_units();g.wave_spawn_number=0;mark_wave_unit(elite);CHECK(max_hp_cache::publish(true));
    image.install();expect(image,own,50*256);expect(image,enemy,44*256);expect(image,elite,66*256);expect(image,neutral,40*256);
    for(auto unit:{own,enemy,elite}){unit->flingy.hitpoints=40*256;CHECK(image.query(3)(unit)==1);unit->flingy.hitpoints=image.query(0)(unit);CHECK(image.query(3)(unit)==0);}
    write_entry(&dat[0][6],0,1);write_entry(&dat[0][7],0,23);CHECK(max_hp_cache::publish(true));
    image.shields(0,1,23);expect(image,own,50*256,23);expect(image,enemy,44*256,23);expect(image,elite,66*256,23);expect(image,neutral,40*256,23);
    for(std::size_t i=0;i<5;i++)CHECK(max_hp_engine::originals[i](enemy)==(i==0?10240:i==1?40:i==2?3413:i==3?0:63));
    const auto old_points=max_hp_engine::originals[1],old_composite=max_hp_engine::originals[4];
    max_hp_engine::originals[1]=changing_original_points;max_hp_engine::originals[4]=changing_original_composite;unsafe_original_reads=0;
    CHECK(image.query(4)(own)==73);CHECK(unsafe_original_reads==0);
    max_hp_engine::originals[1]=old_points;max_hp_engine::originals[4]=old_composite;
    CHECK(raw_value(0,8,0)==40*256);U32 hp=0;std::memcpy(&hp,image.base+0xe59420,4);CHECK(hp==40*256);
    DWORD64 unwind_base=0;CHECK(RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(max_hp_engine::originals[1])+4,&unwind_base,nullptr)!=nullptr);CHECK(unwind_base==reinterpret_cast<DWORD64>(max_hp_engine::hooks[1].allocation));
}
void hp_engine_fallbacks_x64(){
    using namespace hp_engine_fixture;reset();Image image;auto own=add(0,1,0,0,10240),enemy=add(0,6,0,0,10240);
    GrowthSnapshot snapshot{};snapshot.talent_bits[0]=1u<<1;snapshot.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,snapshot));image.install();
    own->flags|=0x40000000u;enemy->flags|=0x40000000u;expect(image,own,10240);expect(image,enemy,10240);
    own->flags=enemy->flags=0;max_hp_cache::sequence.fetch_add(1);expect(image,own,10240);max_hp_cache::sequence.fetch_add(1);expect(image,own,12800);
    bw::Unit outside{};outside.unit_id=0;outside.flingy.hitpoints=10240;expect(image,&outside,10240);
    max_hp_cache::reset();expect(image,own,10240);expect(image,enemy,10240);
    CHECK(max_hp_cache::publish(true));expect(image,own,12800);abandon_session();expect(image,own,10240);
}
void hp_engine_zero_and_fractional_x64(){
    using namespace hp_engine_fixture;
    for(U32 maximum:{0u,1u,255u,256u,10241u}){
        reset();write_entry(&dat[0][8],15,maximum);write_entry(&dat[0][6],15,1);write_entry(&dat[0][7],15,60);Image image;auto unit=add(15,11,0,0,256);
        GrowthSnapshot snapshot{};CHECK(apply_snapshot(nullptr,snapshot));CHECK(max_hp_cache::publish(true));image.install();image.shields(15,1,60);
        for(int current:{0,1,128,255,256,257,10240}){unit->flingy.hitpoints=current;expect(image,unit,maximum,60);}
    }
    {
        reset();Image image;auto ling=add(37,6,0,0,35*256);GrowthSnapshot snapshot{};snapshot.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,snapshot));image.install();
        CHECK(original_stat({0,8,37})==35*256);expect(image,ling,9856,0,39);CHECK(image.query(2)(ling)==3285);
        ling->flingy.hitpoints=9856;CHECK(image.query(3)(ling)==0);CHECK(image.query(1)(ling)==39);
    }
}
void hp_engine_registration_guards(){
    using namespace hp_engine_fixture;using namespace max_hp_engine;reset();Image image;
    CHECK(!bind(nullptr));samase::PluginApi missing{};CHECK(!bind(&missing));
    const auto check_bad=[&](Entry entry){native_engine_hooks::Hook hook{};const auto calls=writer_calls;CHECK(!register_at(image.base,entry,hook,writer));CHECK(!hook.queued && !hook.allocation);CHECK(writer_calls==calls);};
    Entry invalid=entries[0];invalid.callback=nullptr;check_bad(invalid);
    invalid=entries[0];invalid.displacement=std::numeric_limits<std::size_t>::max();check_bad(invalid);
    invalid=entries[0];invalid.displacement=0;check_bad(invalid);
    invalid=entries[0];invalid.displacement=9;check_bad(invalid);
    invalid=entries[0];invalid.spec.stolen=13;check_bad(invalid);
    for(std::size_t i=0;i<5;i++){
        const auto& entry=entries[i];auto site=image.base+entry.spec.rva;const auto before=*site;*site^=1;check_bad(entry);*site=before;
        for(std::size_t j=0;j<entry.spec.witness_count;j++){auto w=image.base+entry.spec.witnesses[j].rva;const auto b=*w;*w^=1;check_bad(entry);*w=b;}
    }
    native_engine_hooks::Hook hook{};init_open=true;reject=true;CHECK(!register_at(image.base,entries[0],hook,writer));init_open=false;reject=false;
    CHECK(!hook.queued && !hook.installed && !hook.allocation && !hook.trampoline);CHECK(writes.empty());
    CHECK(std::string(native_engine_hooks::last_install.stage)=="hp_registration_rejected");
    CHECK(!register_at(image.base,entries[0],hook,writer));CHECK(writes.empty());
    CHECK(image.query(0)(add(0,1,0,0))==10240);
}
void hp_engine_loader_queue_and_branch_guards(){
    using namespace hp_engine_fixture;using namespace max_hp_engine;reset();Image image;auto unit=add(0,6,0,0,10240);
    GrowthSnapshot snapshot{};snapshot.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,snapshot));
    CHECK(!verify_installation());CHECK(!ready);CHECK(image.queue());CHECK(writes.size()==6);
    CHECK(!verify_installation());CHECK(!ready);expect(image,unit,10240);
    const auto calls=writer_calls;CHECK(image.queue());CHECK(writer_calls==calls && writes.size()==6);
    image.apply();CHECK(verify_installation());expect(image,unit,11264);
    for(std::size_t i=0;i<5;i++){
        auto address=image.base+entries[i].spec.rva+6;const auto saved=*address;*address^=1;
        CHECK(!verify_installation());CHECK(!ready);CHECK(std::string(native_engine_hooks::last_install.stage)=="registered_branch_mismatch");
        *address=saved;CHECK(verify_installation());CHECK(ready);
        for(std::size_t n=0;n<entries[i].spec.witness_count;n++){
            auto witness=image.base+entries[i].spec.witnesses[n].rva;const auto expected=*witness;*witness^=1;
            CHECK(!verify_installation());CHECK(!ready);CHECK(std::string(native_engine_hooks::last_install.stage)=="hp_registered_remainder_changed");
            *witness=expected;CHECK(verify_installation());CHECK(ready);
        }
    }
    auto add_branch=image.base+add_spec.rva+6;const auto old_add_branch=*add_branch;*add_branch^=1;
    CHECK(!verify_installation());CHECK(!ready);*add_branch=old_add_branch;CHECK(verify_installation());
    for(const auto& w:add_witnesses){auto target=image.base+w.rva;const auto old=*target;*target^=1;CHECK(!verify_installation());CHECK(!ready);CHECK(std::string(native_engine_hooks::last_install.stage)=="hp_add_remainder_changed");*target=old;CHECK(verify_installation());}
    CHECK(!init_open);CHECK(writer_calls==calls);
}
void hp_engine_shield_talent_isolation_x64(){
    using namespace hp_engine_fixture;reset();Image image;
    auto own=add(65,1,0,0),enemy=add(65,6,0,0),neutral=add(65,11,0,0),illusion=add(65,1,0,0),interceptor=add(73,1,0,0);
    const U32 base_hp=original_stat({0,8,65}),shield=original_stat({0,7,65});
    const U32 interceptor_hp=original_stat({0,8,73}),interceptor_shield=original_stat({0,7,73});
    GrowthSnapshot snapshot{};snapshot.talent_bits[69/32]|=1u<<(69%32);snapshot.talent_bits[103/32]|=1u<<(103%32);snapshot.curse_counts[2]=1;
    CHECK(apply_snapshot(nullptr,snapshot));illusion->flags|=0x40000000u;image.install();
    expect(image,own,base_hp,static_cast<int>(shield+20));expect(image,enemy,static_cast<U32>((std::uint64_t(base_hp)*11+5)/10),static_cast<int>(shield));
    expect(image,neutral,base_hp,static_cast<int>(shield));expect(image,illusion,base_hp,static_cast<int>(shield));
    expect(image,interceptor,interceptor_hp+20*256,static_cast<int>(interceptor_shield+20));
    CHECK(raw_value(0,7,65)==shield && raw_value(0,7,73)==interceptor_shield);
    // A disabled shield field must stay disabled even if a nonzero maximum is stored.
    max_hp_cache::reset();image.shields(65,0,static_cast<std::uint16_t>(shield));write_entry(&dat[0][6],65,0);CHECK(max_hp_cache::publish(true));
    expect(image,own,base_hp,0);expect(image,illusion,base_hp,0);
}
void hp_engine_add_native_clamp_x64(){
    using namespace hp_engine_fixture;reset();Image image;
    struct Alias {bw::DatTable before;Alias(U8* bytes):before(dat[0][8]){dat[0][8].data=bytes;}~Alias(){abandon_session();dat[0][8]=before;}} alias(image.base+0xe59420);
    auto own=add(0,1,0,0,10240),enemy=add(0,6,0,0,10240),elite=add(0,6,0,0,10240),neutral=add(0,11,0,0,10240);
    GrowthSnapshot snapshot{};snapshot.talent_bits[0]=1u<<1;snapshot.curse_counts[2]=snapshot.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,snapshot));refresh_units();g.wave_spawn_number=0;mark_wave_unit(elite);
    const auto native_add=reinterpret_cast<max_hp_engine::AddHp>(image.base+max_hp_engine::add_spec.rva);
    elite->flingy.hitpoints=50*256;native_add(elite,256);CHECK(elite->flingy.hitpoints==40*256); // Original direct DAT clamp reproduces the defect.
    image.install();elite->flingy.hitpoints=50*256;native_add(elite,256);CHECK(elite->flingy.hitpoints==51*256);
    native_add(elite,999999);CHECK(elite->flingy.hitpoints==66*256);
    own->flingy.hitpoints=49*256;native_add(own,5*256);CHECK(own->flingy.hitpoints==50*256);
    enemy->flingy.hitpoints=43*256;native_add(enemy,5*256);CHECK(enemy->flingy.hitpoints==44*256);
    neutral->flingy.hitpoints=39*256;native_add(neutral,5*256);CHECK(neutral->flingy.hitpoints==40*256);
    elite->flags|=0x40000000u;elite->flingy.hitpoints=39*256;native_add(elite,5*256);CHECK(elite->flingy.hitpoints==40*256);elite->flags=0;
    {OwnerDatScope outer(1,1,own);CHECK(raw_value(0,8,0)==50*256);elite->flingy.hitpoints=60*256;native_add(elite,999999);CHECK(elite->flingy.hitpoints==66*256);CHECK(raw_value(0,8,0)==50*256);}
    CHECK(raw_value(0,8,0)==40*256);max_hp_engine::original_add(elite,0);CHECK(elite->flingy.hitpoints==40*256);
    abandon_session();own->flingy.hitpoints=39*256;native_add(own,5*256);CHECK(own->flingy.hitpoints==40*256);
}
void hp_engine_extended_dat_relocations_x64(){
    using namespace hp_engine_fixture;using namespace max_hp_engine;reset();Image image;
    struct Aliases {
        bw::DatTable saved[3];
        Aliases(U8* base){for(U32 i=0;i<3;i++){saved[i]=dat[0][i+6];auto target=base+0x1100000+i*0x1000;std::memcpy(target,saved[i].data,saved[i].entry_size*saved[i].entries);dat[0][i+6].data=target;}}
        ~Aliases(){abandon_session();for(U32 i=0;i<3;i++)dat[0][i+6]=saved[i];}
    } aliases(image.base);
    const auto operand=[&](U32 rva,std::size_t offset,std::size_t origin,const void* target){
        const auto delta=reinterpret_cast<std::intptr_t>(target)-reinterpret_cast<std::intptr_t>(image.base)-static_cast<std::intptr_t>(origin);
        CHECK(delta>=INT32_MIN && delta<=INT32_MAX);const auto value=static_cast<std::int32_t>(delta);std::memcpy(image.base+rva+offset,&value,4);
    };
    for(std::size_t i=0;i<4;i++)operand(entries[i].spec.rva,entries[i].displacement,entries[i].spec.rva+entries[i].spec.stolen,dat[0][8].data);
    operand(entries[4].spec.rva,23,0,dat[0][6].data);operand(entries[4].spec.rva,34,0,dat[0][7].data);operand(entries[4].spec.rva,45,0,dat[0][8].data);
    operand(add_spec.rva,34,0,dat[0][8].data);operand(add_spec.rva,57,0,dat[0][8].data);
    image_dat[10].data=image.base+0x1103000;image_dat[10].entry_size=8;image_dat[10].entries=999;
    operand(add_spec.rva,132,0,image_dat[10].data);
    auto own=add(0,1,0,0,10240),enemy=add(0,6,0,0,10240),neutral=add(0,11,0,0,10240);
    expect(image,own,10240);expect(image,enemy,10240);
    GrowthSnapshot snapshot{};snapshot.talent_bits[0]=1u<<1;snapshot.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,snapshot));
    // Reproduce the exact old failure with a relocated, otherwise stock getter.
    CHECK(!native_engine_hooks::match(image.base+entries[0].spec.rva,entries[0].spec.prologue,entries[0].spec.stolen));
    // A readable but unrelated address must never be accepted as a DAT array.
    operand(entries[0].spec.rva,entries[0].displacement,entries[0].spec.rva+entries[0].spec.stolen,static_cast<U8*>(dat[0][8].data)+4);
    CHECK(!image.queue());CHECK(writes.empty());CHECK(std::string(native_engine_hooks::last_install.stage)=="hp_dat_operand_target_mismatch");
    operand(entries[0].spec.rva,entries[0].displacement,entries[0].spec.rva+entries[0].spec.stolen,dat[0][8].data);
    const auto saved_width=dat[0][8].entry_size;dat[0][8].entry_size=2;CHECK(!image.queue());CHECK(writes.empty());dat[0][8].entry_size=saved_width;
    image_dat[10].entry_size=4;CHECK(!image.queue());CHECK(writes.empty());image_dat[10].entry_size=8;
    const auto overlay=image_dat[10].data;image_dat[10].data=nullptr;CHECK(!image.queue());CHECK(writes.empty());image_dat[10].data=overlay;
    image.install();expect(image,own,50*256);expect(image,enemy,44*256);expect(image,neutral,40*256);
    const auto native_add=reinterpret_cast<AddHp>(image.base+add_spec.rva);
    enemy->flingy.hitpoints=43*256;native_add(enemy,5*256);CHECK(enemy->flingy.hitpoints==44*256);
    CHECK(raw_value(0,8,0)==40*256);CHECK(verify_installation());
    max_hp_cache::reset();expect(image,own,40*256);expect(image,enemy,40*256);
    U32 value=42*256;std::memcpy(static_cast<U8*>(dat[0][8].data),&value,4);expect(image,own,value);
}
inline constexpr unsigned max_hp_engine_group_count=9;
void run_max_hp_engine_groups(){hp_engine_original_x64();hp_engine_owner_and_elite_x64();hp_engine_fallbacks_x64();hp_engine_zero_and_fractional_x64();hp_engine_shield_talent_isolation_x64();hp_engine_add_native_clamp_x64();hp_engine_registration_guards();hp_engine_loader_queue_and_branch_guards();hp_engine_extended_dat_relocations_x64();}
}
