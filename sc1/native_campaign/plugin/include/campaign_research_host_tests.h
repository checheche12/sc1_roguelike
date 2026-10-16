#pragma once
#include "campaign_research_specs.generated.h"
namespace host_test {
inline constexpr std::size_t campaign_research_group_count=2;
namespace campaign_research_fixture {
inline U8* image=nullptr;
inline bool finish_job=true;
inline void __cdecl order(bw::Unit* u){
    CHECK(game.is_bw==1);
    if(!finish_job)return;
    const U32 job=u->unit_specific.bytes[u->order==75 ? 12:13];
    const auto setter=image+(u->order==75 ? 0x3d4b40:0x3d4bf0);
    reinterpret_cast<void (__cdecl*)(U32,U32,U32)>(setter)(u->player,job,1);
    u->order=3;u->unit_specific.bytes[12]=44;u->unit_specific.bytes[13]=61;
}
}
inline void campaign_research_native_completion_and_lurker_gate(){
    using namespace campaign_research_fixture;reset();
    image=static_cast<U8*>(VirtualAlloc(nullptr,native_engine_hooks::kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(image);
    std::memcpy(image+0x3d4b40,campaign_research_specs::tech_setter,sizeof(campaign_research_specs::tech_setter));
    std::memcpy(image+0x3d4ce0,campaign_research_specs::tech_getter,sizeof(campaign_research_specs::tech_getter));
    std::memcpy(image+0x3d4bf0,campaign_research_specs::upgrade_setter,sizeof(campaign_research_specs::upgrade_setter));
    const auto encoded=reinterpret_cast<std::uintptr_t>(&game)^0x3703db00831bdfe2ull;
    std::memcpy(image+0xdb00d8,&encoded,sizeof(encoded));DWORD old=0;
    CHECK(VirtualProtect(image+0x3d4000,4096,PAGE_EXECUTE_READ,&old));CHECK(FlushInstructionCache(GetCurrentProcess(),image+0x3d4000,4096));
    const auto set=reinterpret_cast<void (__cdecl*)(U32,U32,U32)>(image+0x3d4b40);
    const auto get=reinterpret_cast<U32 (__cdecl*)(U32,U32)>(image+0x3d4ce0);
    auto den=add(135,1,500,500);den->flags=1;refresh_units();
    // Reproduce the original bug with the real native setter: completed BW
    // technology is silently discarded in original campaign mode.
    game.is_bw=0;set(1,32,1);CHECK(get(1,32)==0);
    den->order=75;den->unit_specific.bytes[12]=32;finish_job=false;
    owner_order_hook(den,campaign_research_fixture::order);CHECK(!game.is_bw && get(1,32)==0 && den->order==75);
    finish_job=true;owner_order_hook(den,campaign_research_fixture::order);
    CHECK(!game.is_bw && get(1,32)==1 && den->order==3);
    CHECK(enemy_progression::researched(1,32) && !enemy_progression::researched(2,32));
    // Cover other BW technology and upgrade completion without changing the
    // campaign's persistent expansion flag or another owner's research.
    for(U32 id:{24u,25u,27u,29u,30u,31u,32u}){
        den->order=75;den->unit_specific.bytes[12]=U8(id);
        owner_order_hook(den,campaign_research_fixture::order);CHECK(!game.is_bw && get(1,id)==1 && get(2,id)==0);
    }
    for(U32 id:{47u,49u,51u,52u,53u,54u}){
        den->order=76;den->unit_specific.bytes[13]=U8(id);
        owner_order_hook(den,campaign_research_fixture::order);CHECK(!game.is_bw && rework_upgrade_storage::level(1,id)==1 && !rework_upgrade_storage::level(2,id));
    }
    CHECK(VirtualFree(image,0,MEM_RELEASE));image=nullptr;
}
inline void campaign_research_scope_boundaries(){
    reset();auto den=add(135,1,500,500);den->flags=1;den->order=75;den->unit_specific.bytes[12]=32;refresh_units();
    {campaign_research::Scope outer(den);CHECK(game.is_bw==1);{campaign_research::Scope inner(den);CHECK(game.is_bw==1);}CHECK(game.is_bw==1);}CHECK(!game.is_bw);
    game.is_bw=1;{campaign_research::Scope scope(den);CHECK(game.is_bw==1);}CHECK(game.is_bw==1);game.is_bw=0;
    for(U32 kind=0;kind<7;kind++){
        den->flags=1;den->order=75;den->unit_specific.bytes[12]=32;den->flingy.hitpoints=2560;g.active=true;g.mission=&campaign_config::kMissions[0];
        if(kind==0)g.active=false;if(kind==1)g.mission=nullptr;if(kind==2)den->flags|=0x40000000u;
        if(kind==3)den->flags=0;if(kind==4)den->flingy.hitpoints=0;if(kind==5)den->order=3;if(kind==6)den->unit_specific.bytes[12]=23;
        {campaign_research::Scope scope(den);CHECK(!game.is_bw);}CHECK(!game.is_bw && !game.tech_level_bw[1][8]);
    }
    g.active=true;g.mission=&campaign_config::kMissions[0];
}
inline void run_campaign_research_groups(){campaign_research_native_completion_and_lurker_gate();campaign_research_scope_boundaries();}
}
