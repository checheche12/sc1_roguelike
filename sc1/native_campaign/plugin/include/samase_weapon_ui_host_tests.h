#pragma once
// Executes exact pinned SAMASE tooltip read/multiply instructions in private
// x64 memory. No StarCraft process, user DB, UI or installation is accessed.
namespace host_test {
namespace weapon_ui_fixture {
struct Image {
    U8* base=nullptr;
    Image(){
        using namespace samase_weapon_ui;CHECK(code==nullptr && !bound_base);
        base=static_cast<U8*>(VirtualAlloc(nullptr,0x2bf000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
        const auto copy=[&](U32 rva,const auto& bytes){std::memcpy(base+rva,bytes,sizeof(bytes));};
        copy(base_rva,base_original);copy(bonus_rva,bonus_original);copy(raw_rva,raw_original);copy(factor_rva,factor_original);
        copy(0x4374,bonus_setup_original);copy(0x4480,base_continuation);copy(0x43ca,bonus_math_original);
        const auto tables=reinterpret_cast<std::uintptr_t>(dat[1]);const std::size_t fields=dat_counts[1];
        std::memcpy(base+descriptor_rva,&tables,8);std::memcpy(base+descriptor_rva+8,&fields,8);
        // Win64 entry adapters reproduce the original frame alignment and
        // nonvolatile state, then run the unchanged pinned instruction block.
        const U8 hbase[]={0x53,0x57,0x55,0x41,0x56,0x48,0x83,0xec,0x38,0x48,0x89,0xcb,0x89,0xd7,0x0f,0xb7,0xea};
        std::memcpy(base+0x10000,hbase,sizeof(hbase));native_engine_hooks::absolute_jump(base+0x10000+sizeof(hbase),base+base_rva);
        const U8 hbonus[]={0x53,0x57,0x55,0x41,0x56,0x41,0x57,0x48,0x83,0xec,0x30,0x48,0x89,0xcb,0x89,0xd7,0x45,0x89,0xc6,0x41,0xbf,0xff,0xff,0xff,0xff};
        std::memcpy(base+0x10100,hbonus,sizeof(hbonus));native_engine_hooks::absolute_jump(base+0x10100+sizeof(hbonus),base+0x43b3);
        CHECK(FlushInstructionCache(GetCurrentProcess(),base,0x2bf000)!=0);
    }
    ~Image(){
        if(samase_weapon_ui::code){
            std::memcpy(base+samase_weapon_ui::base_rva,samase_weapon_ui::base_original,sizeof(samase_weapon_ui::base_original));
            std::memcpy(base+samase_weapon_ui::bonus_rva,samase_weapon_ui::bonus_original,sizeof(samase_weapon_ui::bonus_original));
            samase_weapon_ui::dispose_code();
        }
        if(base)VirtualFree(base,0,MEM_RELEASE);
    }
    U32 damage(bw::Unit* unit,U32 weapon){
        // Stop immediately before formatting the number into a localized
        // string; formatting consumes this exact output without recalculation.
        U8 saved[24];std::memcpy(saved,base+0x4480,sizeof(saved));
        const U8 ret[]={0x89,0xd0,0x48,0x83,0xc4,0x38,0x41,0x5e,0x5d,0x5f,0x5b,0xc3};std::memcpy(base+0x4480,ret,sizeof(ret));
        FlushInstructionCache(GetCurrentProcess(),base+0x4480,sizeof(ret));
        using Query=U32 (__cdecl*)(bw::Unit*,U32);const auto result=reinterpret_cast<Query>(base+0x10000)(unit,weapon);
        std::memcpy(base+0x4480,saved,sizeof(saved));FlushInstructionCache(GetCurrentProcess(),base+0x4480,sizeof(saved));return result;
    }
    U32 bonus(bw::Unit* unit,U32 weapon,U32 level_times_factor){
        U8 saved[24];std::memcpy(saved,base+0x43df,sizeof(saved));
        const U8 ret[]={0x44,0x89,0xf8,0x48,0x83,0xc4,0x30,0x41,0x5f,0x41,0x5e,0x5d,0x5f,0x5b,0xc3};std::memcpy(base+0x43df,ret,sizeof(ret));
        FlushInstructionCache(GetCurrentProcess(),base+0x43df,sizeof(ret));
        using Query=U32 (__cdecl*)(bw::Unit*,U32,U32);const auto result=reinterpret_cast<Query>(base+0x10100)(unit,weapon,level_times_factor);
        std::memcpy(base+0x43df,saved,sizeof(saved));FlushInstructionCache(GetCurrentProcess(),base+0x43df,sizeof(saved));return result;
    }
    void install(){CHECK(samase_weapon_ui::install_at(base));CHECK(samase_weapon_ui::verify_at(base));CHECK(samase_weapon_ui::ready);}
};
inline void check_unwind(){
    using namespace samase_weapon_ui;CHECK(code && ready);
    const U8 epilogue[]={0x48,0x83,0xc4,0x28,0xc3};const DWORD bodies[]={19,9,7};
    for(std::size_t shim=0;shim<unwind.size();shim++){
        const auto entry_info=unwind[shim];CHECK(std::memcmp(code+entry_info.EndAddress-sizeof(epilogue),epilogue,sizeof(epilogue))==0);
        struct Point{DWORD offset;bool allocated;};const Point points[]={{entry_info.BeginAddress,false},{entry_info.BeginAddress+4,true},
            {entry_info.BeginAddress+bodies[shim],true},{entry_info.EndAddress-5,true},{entry_info.EndAddress-1,false}};
        alignas(16) std::uint64_t stack[128]{};auto entry=stack+64;constexpr std::uint64_t target=0x123456789abull;*entry=target;
        for(const auto point:points){
            CONTEXT context{};context.ContextFlags=CONTEXT_FULL;context.Rip=reinterpret_cast<DWORD64>(code+point.offset);
            context.Rsp=reinterpret_cast<DWORD64>(entry)-(point.allocated?0x28:0);
            context.Rbx=0x1234;context.Rsi=0x2345;context.Rdi=0x3456;context.R12=0x4567;
            DWORD64 found_base=0;auto function=RtlLookupFunctionEntry(context.Rip,&found_base,nullptr);
            CHECK(function && found_base==reinterpret_cast<DWORD64>(code));
            PVOID handler_data=nullptr;DWORD64 establisher=0;
            RtlVirtualUnwind(UNW_FLAG_NHANDLER,found_base,context.Rip,function,&context,&handler_data,&establisher,nullptr);
            CHECK(context.Rip==target);CHECK(context.Rsp==reinterpret_cast<DWORD64>(entry+1));
            CHECK(context.Rbx==0x1234 && context.Rsi==0x2345 && context.Rdi==0x3456 && context.R12==0x4567);
        }
    }
}
inline void stats(){for(U32 weapon=0;weapon<130;weapon++){write_entry(&dat[1][14],weapon,7+weapon);write_entry(&dat[1][15],weapon,1+weapon%4);write_entry(&dat[1][17],weapon,1+(weapon%3));}}
inline GrowthSnapshot damage_snapshot(){GrowthSnapshot s{};for(U32 bit:{22u,25u,46u,49u,51u,54u,58u,82u,88u})s.talent_bits[bit/32]|=1u<<(bit%32);s.curse_counts[1]=1;return s;}
inline U32 multiplier(U32 id,U32 weapon){if(id==10 || id==32 || id==65 || id==77)return 2;if(id==58)return 1;return raw_value(1,17,weapon);}
}
void weapon_ui_original_x64(){
    using namespace weapon_ui_fixture;reset();stats();Image image;
    for(U32 id:{0u,3u,4u,10u,32u,37u,38u,43u,47u,58u,65u,70u,77u,103u}){
        auto unit=add(id,1,0,0);
        for(U32 weapon:{0u,7u,8u,25u,35u,38u,48u,55u,66u,73u,103u,109u,129u}){
            CHECK(image.damage(unit,weapon)==raw_value(1,14,weapon)*multiplier(id,weapon));
            for(U32 level:{0u,1u,3u})CHECK(image.bonus(unit,weapon,level*multiplier(id,weapon))==raw_value(1,15,weapon)*level*multiplier(id,weapon));
        }
    }
}
void weapon_ui_owner_cache_and_x64(){
    using namespace weapon_ui_fixture;reset();stats();Image image;
    auto own=add(32,1,0,0),enemy=add(32,6,0,0),neutral=add(32,11,0,0);
    const auto snapshot=damage_snapshot();CHECK(apply_snapshot(nullptr,snapshot));image.install();check_unwind();
    for(auto unit:{own,enemy,neutral})for(U32 weapon=0;weapon<130;weapon++)for(U32 field:{14u,15u}){
        U32 value=0;CHECK(max_hp_cache::read_weapon(unit,field,weapon,value));CHECK(value==owner_stat(unit->player,{1,field,weapon}));
        if(field==14)CHECK(image.damage(unit,weapon)==value*2);
        else for(U32 level:{0u,1u,3u})CHECK(image.bonus(unit,weapon,level*2)==value*level*2);
    }
    CHECK(image.damage(own,25)==(7+25+2)*2);CHECK(image.damage(neutral,25)==(7+25)*2);
    CHECK(raw_value(1,14,25)==7+25);CHECK(samase_weapon_ui::verify_at(image.base));
    const auto before=image.damage(own,25);
    {OwnerDatScope other(6,6,enemy);CHECK(image.damage(own,25)==before);CHECK(image.damage(neutral,25)==(7+25)*2);}
    own->player=6;CHECK(image.damage(own,25)==owner_stat(6,{1,14,25})*2);
    own->player=11;CHECK(image.damage(own,25)==(7+25)*2);
    own->player=1;own->minor_unique_index++;CHECK(image.damage(own,25)==before);
    own->flags|=0x40000000u;CHECK(image.damage(own,25)==(7+25)*2);own->flags&=~0x40000000u;
    CHECK(raw_value(1,14,25)==7+25 && raw_value(1,15,25)==2);
}
void weapon_ui_fallbacks_and_guards(){
    using namespace weapon_ui_fixture;using namespace samase_weapon_ui;reset();stats();Image image;
    auto unit=add(32,1,0,0);CHECK(apply_snapshot(nullptr,damage_snapshot()));
    CHECK(!bind(nullptr));CHECK(!install_at(nullptr));CHECK(!code);
    for(auto rva:{base_rva,bonus_rva,raw_rva,factor_rva,0x4374u,0x4480u,0x43cau}){
        auto saved=image.base[rva];image.base[rva]^=1;CHECK(!install_at(image.base));CHECK(!code);image.base[rva]=saved;
    }
    image.install();const U32 original=(7+25)*2;CHECK(image.damage(unit,25)==original+4);
    CHECK(image.damage(unit,0x10019u)==original+4); // Original EBP/DI truncation.
    CHECK(image.damage(unit,0xffffu)==0); // Invalid Rust Option retains zero.
    CHECK(image.damage(unit,200)==raw_value(1,14,200)*2); // Expanded ID fallback.
    const auto untouched=storage;image.damage(unit,25);image.bonus(unit,25,6);CHECK(storage==untouched);
    max_hp_cache::sequence.fetch_add(1);CHECK(image.damage(unit,25)==original);max_hp_cache::sequence.fetch_add(1);
    CHECK(image.damage(unit,25)==original+4);U32 value=12345;
    CHECK(!max_hp_cache::read_weapon(nullptr,14,25,value));CHECK(value==12345);
    CHECK(!max_hp_cache::read_weapon(unit,13,25,value));CHECK(!max_hp_cache::read_weapon(unit,16,25,value));CHECK(!max_hp_cache::read_weapon(unit,14,130,value));
    bw::Unit external{};external.unit_id=32;external.player=1;CHECK(image.damage(&external,25)==original);
    auto wrong=reinterpret_cast<const bw::Unit*>(reinterpret_cast<const U8*>(unit)+1);CHECK(!max_hp_cache::read_weapon(wrong,14,25,value));
    unit->player=12;CHECK(image.damage(unit,25)==original);unit->player=1;
    unit->flags|=0x40000000u;CHECK(image.damage(unit,25)==original);unit->flags&=~0x40000000u;
    max_hp_cache::reset();CHECK(image.damage(unit,25)==original);CHECK(max_hp_cache::publish(true));CHECK(image.damage(unit,25)==original+4);
    for(auto rva:{base_rva,bonus_rva,raw_rva,factor_rva,0x4374u,0x4480u,0x43cau}){
        auto saved=image.base[rva];DWORD old=0;CHECK(native_engine_hooks::protect_code_for_write(image.base+rva,1,&old));image.base[rva]^=1;
        CHECK(!verify_at(image.base));CHECK(!activated.load());image.base[rva]=saved;DWORD ignored=0;VirtualProtect(image.base+rva,1,old,&ignored);CHECK(verify_at(image.base));
    }
    // An unrelated witness failure must disable cache substitution, even while
    // the safe remaining adapter branch is still reachable.
    image.base[0x4374]^=1;CHECK(!verify_at(image.base));CHECK(image.damage(unit,25)==original);
    image.base[0x4374]^=1;CHECK(verify_at(image.base));CHECK(image.damage(unit,25)==original+4);
    abandon_session();CHECK(image.damage(unit,25)==original);CHECK(image.bonus(unit,25,6)==12);
}
void weapon_ui_factor_upgrade_and_overflow(){
    using namespace weapon_ui_fixture;reset();stats();Image image;
    auto firebat=add(32,1,0,0),goliath=add(3,1,0,0),turret=add(4,1,0,0),valk=add(58,1,0,0),zealot=add(65,1,0,0);
    CHECK(apply_snapshot(nullptr,damage_snapshot()));image.install();
    for(auto unit:{firebat,goliath,turret,valk,zealot})for(U32 weapon:{7u,8u,25u,73u,103u}){
        const U32 factor=multiplier(unit->unit_id,weapon);
        CHECK(image.damage(unit,weapon)==owner_stat(1,{1,14,weapon})*factor);
        for(U32 level:{0u,1u,2u,3u})CHECK(image.bonus(unit,weapon,level*factor)==owner_stat(1,{1,15,weapon})*level*factor);
    }
    // Exercise both exact machine-code saturation paths; production DAT uses
    // U16 damage, but a malformed/custom table must retain legacy saturation.
    max_hp_cache::owner_weapon_values[1*260+25].store(0xffffffffu);CHECK(image.damage(firebat,25)==0xffffffffu);
    max_hp_cache::owner_weapon_values[1*260+130+25].store(0xffffffffu);CHECK(image.bonus(firebat,25,6)==0xffffffffu);
    max_hp_cache::publish(true);CHECK(image.damage(firebat,25)==68);
    CHECK(samase_weapon_ui::verify_at(image.base));
    DWORD64 found_base=0;CHECK(RtlLookupFunctionEntry(reinterpret_cast<DWORD64>(samase_weapon_ui::code)+132,&found_base,nullptr));CHECK(found_base==reinterpret_cast<DWORD64>(samase_weapon_ui::code));
}
inline constexpr std::size_t samase_weapon_ui_group_count=4;
void run_samase_weapon_ui_groups(){weapon_ui_original_x64();weapon_ui_owner_cache_and_x64();weapon_ui_fallbacks_and_guards();weapon_ui_factor_upgrade_and_overflow();}
}
