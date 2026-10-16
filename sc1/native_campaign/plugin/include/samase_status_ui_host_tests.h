#pragma once
namespace host_test {
namespace samase_ui_fixture {
struct Image {
    U8* base=nullptr;
    Image(){
        using namespace samase_status_ui;
        CHECK(!relay_page && !ready);base=static_cast<U8*>(VirtualAlloc(nullptr,kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
        for(std::size_t i=0;i<kSiteCount;i++)std::memcpy(base+kSites[i],kCalls[i],5);
        std::memcpy(base+0x1b2c93,kSavedUnit,sizeof(kSavedUnit));std::memcpy(base+0x1b2d40,kFirstArgs,sizeof(kFirstArgs));
        std::memcpy(base+0x1b2da9,kSecondArgs,sizeof(kSecondArgs));std::memcpy(base+0x1b2dc2,kFormatter,sizeof(kFormatter));std::memcpy(base+kGetterRva,kGetter,sizeof(kGetter));
        std::memcpy(base+0x1b2cf2,kSecondArgs,sizeof(kSecondArgs));std::memcpy(base+0x1b2d0b,kShieldFormatter,sizeof(kShieldFormatter));
        // Keep the exact pinned getter body and point its descriptor at a
        // private table. No real game or loader module is loaded or changed.
        constexpr U8 remaining[]={0x74,0x0e,0x31,0xc0,0x39,0x4a,0x0c,0x76,0x06,0x48,0x8b,0x02,0x8b,0x04,0x88,0xc3};
        std::memcpy(base+kGetterRva+13,remaining,sizeof(remaining));
        auto descriptor=base+0x2a0000;auto values=base+0x2a1000;auto desc_pointer=reinterpret_cast<std::uintptr_t>(descriptor),values_pointer=reinterpret_cast<std::uintptr_t>(values);
        std::memcpy(base+0x2aa610,&desc_pointer,8);std::memcpy(descriptor,&values_pointer,8);U32 width=4,entries=228;std::memcpy(descriptor+8,&width,4);std::memcpy(descriptor+12,&entries,4);
        for(U32 id=0;id<228;id++){const U32 original=original_stat({0,8,id});std::memcpy(values+id*4,&original,4);}
        constexpr U8 shield_getter[]={0x56,0x48,0x83,0xec,0x20,0x89,0xce,0xe8,0x5f,0xfe,0xff,0xff,0x89,0xc1,0x31,0xc0,0x84,0xc9,0x74,0x3a,0x0f,0xb7,0xce,0x48,0x8b,0x15,0x46,0x74,0x1f,0x00,0x48,0x85,0xd2,0x74,0x10,0x31,0xc0,0x39,0x4a,0x0c,0x76,0x21,0x48,0x8b,0x02,0x0f,0xb7,0x04,0x48,0xeb,0x0a,0xba,0x07,0x00,0x00,0x00,0xe8,0xd8,0xfd,0xff,0xff,0x8d,0x88,0x00,0x00,0x80,0xff,0x81,0xf9,0x00,0x00,0x00,0xff,0x72,0x09,0xc1,0xe0,0x08,0x48,0x83,0xc4,0x20,0x5e,0xc3,0xc1,0xe8,0x1f,0x05,0xff,0xff,0xff,0x7f,0xeb,0xf0};
        constexpr U8 enabled_getter[]={0x48,0x83,0xec,0x28,0x0f,0xb7,0xc9,0x48,0x8b,0x15,0x13,0x76,0x1f,0x00,0x48,0x85,0xd2,0x74,0x10,0x31,0xc0,0x39,0x4a,0x0c,0x76,0x13,0x48,0x8b,0x02,0x0f,0xb6,0x04,0x08,0xeb,0x0a,0xba,0x06,0x00,0x00,0x00,0xe8,0x7d,0xff,0xff,0xff,0x85,0xc0,0x0f,0x95,0xc0,0x48,0x83,0xc4,0x28,0xc3};
        std::memcpy(base+kShieldGetterRva,shield_getter,sizeof(shield_getter));std::memcpy(base+0xb302f,enabled_getter,sizeof(enabled_getter));
        auto shield_descriptor=base+0x2a2000,shield_values=base+0x2a3000,enabled_descriptor=base+0x2a4000,enabled_values=base+0x2a5000;
        auto shield_pointer=reinterpret_cast<std::uintptr_t>(shield_descriptor),enabled_pointer=reinterpret_cast<std::uintptr_t>(enabled_descriptor);
        auto shield_data=reinterpret_cast<std::uintptr_t>(shield_values),enabled_data=reinterpret_cast<std::uintptr_t>(enabled_values);
        std::memcpy(base+0x2aa628,&shield_pointer,8);std::memcpy(base+0x2aa650,&enabled_pointer,8);
        std::memcpy(shield_descriptor,&shield_data,8);std::memcpy(enabled_descriptor,&enabled_data,8);
        U32 shield_width=2,enabled_width=1;std::memcpy(shield_descriptor+8,&shield_width,4);std::memcpy(enabled_descriptor+8,&enabled_width,4);
        std::memcpy(shield_descriptor+12,&entries,4);std::memcpy(enabled_descriptor+12,&entries,4);
        for(U32 id=0;id<228;id++){const std::uint16_t shield=static_cast<std::uint16_t>(original_stat({0,7,id}));const U8 enabled=static_cast<U8>(original_stat({0,6,id}));std::memcpy(shield_values+id*2,&shield,2);enabled_values[id]=enabled;}
        CHECK(FlushInstructionCache(GetCurrentProcess(),base,kImageSize));
    }
    ~Image(){using namespace samase_status_ui;ready=false;passthrough_only.store(false);original_maximum=nullptr;original_shields=nullptr;verified_module=nullptr;if(relay_page)VirtualFree(relay_page,0,MEM_RELEASE);relay_page=nullptr;logged_queries.store(0);if(base)VirtualFree(base,0,MEM_RELEASE);}
    void install(){CHECK(samase_status_ui::install_at(base));CHECK(samase_status_ui::verify_installation());}
    // Real x64 caller preserves Unit* at the same [rsp+38] as SAMASE. The call
    // targets the installed relay extracted from the actual patched site.
    U32 invoke(std::size_t which,bw::Unit* unit,U32 requested=0xffffffffu){
        using namespace samase_status_ui;
        std::int32_t delta=0;std::memcpy(&delta,base+kSites[which]+1,4);auto relay=base+kSites[which]+5+delta;
        auto code=static_cast<U8*>(VirtualAlloc(nullptr,4096,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(code);
        // sub rsp,48; save unit at+38; ecx=edx(requested id); call relay; restore
        constexpr U8 prefix[]={0x48,0x83,0xec,0x48,0x48,0x89,0x4c,0x24,0x38,0x89,0xd1,0x48,0xb8};
        std::memcpy(code,prefix,sizeof(prefix));const auto address=reinterpret_cast<std::uintptr_t>(relay);std::memcpy(code+sizeof(prefix),&address,8);
        constexpr U8 suffix[]={0xff,0xd0,0x48,0x83,0xc4,0x48,0xc3};std::memcpy(code+sizeof(prefix)+8,suffix,sizeof(suffix));
        DWORD old=0;CHECK(VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old));CHECK(FlushInstructionCache(GetCurrentProcess(),code,64));
        using Fn=U32 (__cdecl*)(bw::Unit*,U32);const auto value=reinterpret_cast<Fn>(code)(unit,requested==0xffffffffu ? U32(unit->unit_id):requested);VirtualFree(code,0,MEM_RELEASE);return value;
    }
};
}
void samase_hp_ui_owner_queries(){
    reset();auto own=add(0,1,100,100,40*256),enemy=add(0,6,200,100,40*256),neutral=add(0,11,300,100,40*256);GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,s));
    samase_ui_fixture::Image image;image.install();for(std::size_t i=0;i<2;i++){CHECK(image.invoke(i,own)==50*256);CHECK(image.invoke(i,enemy)==44*256);CHECK(image.invoke(i,neutral)==40*256);}
    CHECK(raw_value(0,8,0)==40*256);CHECK(own->flingy.hitpoints==50*256);CHECK(enemy->flingy.hitpoints==44*256);
}
void samase_hp_ui_fractional_and_elite(){
    reset();auto enemy=add(37,6,100,100,35*256);GrowthSnapshot s{};s.curse_counts[2]=1;s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));samase_ui_fixture::Image image;image.install();
    CHECK(image.invoke(0,enemy)==9856);CHECK(image.invoke(1,enemy)==39*256);g.wave_spawn_number=0;mark_wave_unit(enemy);
    CHECK(image.invoke(0,enemy)==14784);CHECK(image.invoke(1,enemy)==58*256);CHECK(raw_value(0,8,37)==35*256);
}
void samase_hp_ui_fallbacks_and_reuse(){
    reset();auto own=add(0,1,100,100,40*256);GrowthSnapshot s{};s.talent_bits[0]=1u<<1;CHECK(apply_snapshot(nullptr,s));samase_ui_fixture::Image image;image.install();
    bw::Unit external{};external.unit_id=0;external.player=1;external.flingy.hitpoints=50*256;
    for(std::size_t i=0;i<2;i++){CHECK(image.invoke(i,&external)==40*256);CHECK(image.invoke(i,own,37)==35*256);}
    own->flags|=0x40000000u;CHECK(image.invoke(1,own)==40*256);own->flags&=~0x40000000u;
    own->player=11;CHECK(image.invoke(1,own)==40*256);own->player=1;CHECK(image.invoke(1,own)==50*256);
    max_hp_cache::reset();CHECK(image.invoke(1,own)==40*256);CHECK(max_hp_cache::publish(true));CHECK(image.invoke(1,own)==50*256);
}
void samase_hp_ui_original_mismatch_atomic(){
    reset();samase_ui_fixture::Image image;using namespace samase_status_ui;
    image.base[kSites[2]+1]^=1;CHECK(!install_at(image.base));CHECK(!relay_page && !ready);CHECK(native_engine_hooks::match(image.base+kSites[0],kCalls[0],5));CHECK(native_engine_hooks::match(image.base+kSites[1],kCalls[1],5));image.base[kSites[2]+1]^=1;
    image.base[kSites[1]+1]^=1;CHECK(!install_at(image.base));CHECK(!relay_page && !ready);CHECK(native_engine_hooks::match(image.base+kSites[0],kCalls[0],5));
    image.base[kSites[1]+1]^=1;image.base[0x1b2c93]^=1;CHECK(!install_at(image.base));CHECK(!relay_page);CHECK(native_engine_hooks::match(image.base+kSites[1],kCalls[1],5));
    image.base[0x1b2c93]^=1;image.install();CHECK(install_at(image.base));image.base[kSites[0]]^=1;CHECK(!verify_installation());image.base[kSites[0]]^=1;CHECK(verify_installation());image.base[kSites[2]]^=1;CHECK(!verify_installation());image.base[kSites[2]]^=1;CHECK(verify_installation());
}
void samase_hp_ui_firebat_and_display_no_heal(){
    reset();auto own=add(32,1,100,100,50*256),enemy=add(32,6,200,100,50*256);GrowthSnapshot s{};s.talent_bits[0]=1u<<3;CHECK(apply_snapshot(nullptr,s));samase_ui_fixture::Image image;image.install();
    own->flingy.hitpoints=90*256;for(unsigned i=0;i<20;i++){CHECK(image.invoke(1,own)==100*256);CHECK(image.invoke(1,enemy)==50*256);CHECK(own->flingy.hitpoints==90*256);}
    CHECK(samase_status_ui::logged_queries.load()==8);CHECK(raw_value(0,8,32)==50*256);
}
void samase_shield_ui_owner_fallback_and_no_heal(){
    reset();auto own=add(65,1,100,100),enemy=add(65,6,200,100),neutral=add(65,11,300,100),marine=add(0,1,400,100);
    write_entry(&dat[0][6],65,1);write_entry(&dat[0][7],65,60);GrowthSnapshot s{};s.talent_bits[69/32]=1u<<(69%32);CHECK(apply_snapshot(nullptr,s));
    samase_ui_fixture::Image image;image.install();
    CHECK(image.invoke(2,own)==80*256);CHECK(image.invoke(2,enemy)==60*256);CHECK(image.invoke(2,neutral)==60*256);CHECK(image.invoke(2,marine)==0);
    own->shields=45*256;CHECK(image.invoke(2,own)==80*256);CHECK(own->shields==45*256);CHECK(raw_value(0,7,65)==60);
    own->flags|=0x40000000u;CHECK(image.invoke(2,own)==60*256);own->flags&=~0x40000000u;
    own->player=6;CHECK(image.invoke(2,own)==60*256);own->player=1;CHECK(image.invoke(2,own)==80*256);
    bw::Unit external{};external.unit_id=65;external.player=1;CHECK(image.invoke(2,&external)==60*256);CHECK(image.invoke(2,own,0)==0);
    max_hp_cache::reset();CHECK(image.invoke(2,own)==60*256);CHECK(max_hp_cache::publish(true));CHECK(image.invoke(2,own)==80*256);
    samase_status_ui::passthrough_only.store(true);CHECK(image.invoke(2,own)==60*256);samase_status_ui::passthrough_only.store(false);CHECK(samase_status_ui::verify_installation());
}
void run_samase_status_ui_groups(){samase_hp_ui_owner_queries();samase_hp_ui_fractional_and_elite();samase_hp_ui_fallbacks_and_reuse();samase_hp_ui_original_mismatch_atomic();samase_hp_ui_firebat_and_display_no_heal();samase_shield_ui_owner_fallback_and_no_heal();}
inline constexpr std::size_t samase_status_ui_group_count=6;
}
