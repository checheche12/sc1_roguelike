#pragma once
namespace host_test {
inline constexpr std::size_t qa10_group_count=6;
inline void qa10_burrow_regeneration(){
    using namespace rework_fixture;qa9_fixture::begin({89});
    auto lurker=unit(103,1,100,100),enemy=unit(103,6,150,100),standing=unit(103,1,200,100);
    lurker->flags|=0x10u;enemy->flags|=0x10u;
    lurker->flingy.hitpoints=enemy->flingy.hitpoints=standing->flingy.hitpoints=60*256;
    CHECK(effective_max_hp(lurker)==125*256);pulse(120);
    CHECK(lurker->flingy.hitpoints==60*256+1920);CHECK(enemy->flingy.hitpoints==60*256&&standing->flingy.hitpoints==60*256);
    auto s=rework_combat_v5::state(lurker);s->last_damage=121;pulse(144);pulse(192);CHECK(lurker->flingy.hitpoints==60*256+1920);
    pulse(216);CHECK(lurker->flingy.hitpoints==60*256+3840);s->last_launch=217;pulse(240);CHECK(lurker->flingy.hitpoints==60*256+3840);
    s->last_launch=s->last_damage=0;lurker->flingy.hitpoints=124*256;pulse(264);CHECK(lurker->flingy.hitpoints==125*256);
    qa9_fixture::end();
}

namespace qa10_fixture {
inline bw::Unit* lurker=nullptr;inline U32 queued=0;
inline void __cdecl click(void*){queued=(lurker->flags&0x10u)?0u:6u;}
inline void __cdecl packet(const U8* data,U32 length){
    CHECK(length==2);if(!(lurker->flags&0x10u)){lurker->order=data[1];lurker->order_target={500,400,nullptr};}
}
}
inline void qa10_lurker_click_attack_move_and_unburrow_boundaries(){
    using namespace rework_fixture;qa9_fixture::begin({91});
    auto u=unit(103,1,100,100),enemy=unit(103,6,160,100);qa10_fixture::lurker=u;
    u->flags|=0x10u;enemy->flags|=0x10u;u->movement_state=2;pulse(100);
    const auto flags=u->flags;owner_rclick_hook(nullptr,qa10_fixture::click);
    CHECK(qa10_fixture::queued==6&&u->flags==flags&&enemy->flags&0x10u);
    for(U8 order:{U8(6),U8(14)}){
        const U8 data[2]={0x15,order};rework_combat_v5::motion_command(data,2,1,0,qa10_fixture::packet);
        CHECK(u->order==order&&u->flags==flags&&u->movement_state==9&&u->flingy.top_speed==640);
        u->flingy.current_speed=128;CHECK(!rework_combat_v5::allow_primary(u));
        u->flingy.current_speed=0;u->order=11;CHECK(rework_combat_v5::allow_primary(u));
    }
    // Unburrow and other packets pass through the outer command hook with the
    // real burrow flag, so the native toggle is not rejected as already up.
    {rework_combat_v5::CommandScope outer(1,false);CHECK(u->flags&0x10u);u->flags&=~0x10u;}
    CHECK(!(u->flags&0x10u));pulse(101);CHECK(!(u->flags&0x20000u));
    u->flags|=0x10u;ranks[91]=0;owner_rclick_hook(nullptr,qa10_fixture::click);CHECK(!qa10_fixture::queued);
    ranks[91]=1;const U8 data[2]={0x15,14};u->order=3;
    rework_combat_v5::motion_command(data,2,6,0,qa10_fixture::packet);CHECK(u->order==3);
    qa9_fixture::end();
}
inline void qa10_mobility_damage_ui_and_dead_projectile_snapshot(){
    using namespace rework_fixture;qa9_fixture::begin({8,9,29});ranks[8]=2;
    auto marine=unit(0,1,100,100),air_unit=unit(8,1,100,150,true),enemy=unit(0,6,200,100),worker=unit(7,1,150,150);
    CHECK(rework_combat_v5::mobility_damage_bonus(marine,0)==30);
    CHECK(rework_combat_v5::mobility_damage_bonus(air_unit,15)==15);
    CHECK(!rework_combat_v5::mobility_damage_bonus(worker,0)&&!rework_combat_v5::mobility_damage_bonus(enemy,0));
    CHECK(!rework_combat_v5::mobility_damage_bonus(marine,30));
    CHECK(rework_combat_v5::infantry_ui_value(marine,0,20)==30);
    g.normal_hit=true;std::int32_t amount=100*256;
    {rework_combat_v5::DamageScope hit(enemy,marine,0,1,amount);}CHECK(amount==149*256+128);
    auto b=bullet(marine,enemy,0);CHECK(rework_combat_v5::projectiles.at(b).mobility_bonus==30);
    ranks[8]=ranks[29]=0;marine->flingy.hitpoints=0;
    {rework_combat_v5::MissileScope missile(b);amount=100*256;{rework_combat_v5::DamageScope hit(enemy,nullptr,0,1,amount);}CHECK(amount==149*256+128);}
    CHECK(!rework_combat_v5::DamageScope::current_mobility_bonus);qa9_fixture::end();
}
inline void qa10_ground_roles_and_four_health_ranks(){
    using namespace rework_fixture;qa9_fixture::begin({26,27,28,67,68,69,108,109,110,29,30,31,70,111});
    for(U32 ordinal:{26u,27u,28u,67u,68u,69u,108u,109u,110u})ranks[ordinal]=4;
    install();
    for(U32 id:{0u,3u,8u,37u,38u,43u,65u,66u,70u}){
        CHECK(owner_stat(1,{0,8,id})==(original_stat({0,8,id})*212+50)/100);
        CHECK(owner_stat(6,{0,8,id})==original_stat({0,8,id}));
        if(id>=65)CHECK(owner_stat(1,{0,7,id})==(original_stat({0,7,id})*212+50)/100);
    }
    for(auto pair:{std::pair<U32,U32>{6,6},{31,12},{2,5},{12,6},{39,6},{50,60},{66,3},{61,6},{68,6}}){
        const auto w=original_stat({0,17,pair.first});CHECK(w<130);
        CHECK(owner_stat(1,{1,14,w})==original_stat({1,14,w})+pair.second);
    }
    CHECK(owner_stat(1,{1,14,82})==original_stat({1,14,82})+15);
    auto source=unit(0,6,100,100);g.normal_hit=true;
    for(U32 id:{32u,37u,39u,50u,65u,61u}){
        auto target=unit(id,1,200,100);std::int32_t amount=100*256;
        {rework_combat_v5::DamageScope hit(target,source,0,6,amount);}CHECK(amount==90*256);
        ranks[29]=ranks[70]=ranks[111]=4;amount=100*256;
        {rework_combat_v5::DamageScope hit(target,source,0,6,amount);}CHECK(amount==60*256);
        amount=100*256;{rework_combat_v5::DamageScope hit(target,source,30,6,amount);}CHECK(amount==100*256);
        ranks[29]=ranks[70]=ranks[111]=1;
    }
    auto hydra=unit(38,1,200,200);std::int32_t amount=100*256;{rework_combat_v5::DamageScope hit(hydra,source,0,6,amount);}CHECK(amount==100*256);
    qa9_fixture::end();
}
inline void qa10_old_snapshots_fallback_and_native_cap(){
    GrowthSnapshot snapshot{};
    for(U32 ordinal:{8u,26u,110u}){
        const auto bit=238+ordinal;snapshot.talent_bits[bit/32]|=1u<<(bit%32);
        CHECK(rework_catalog::rank(snapshot,ordinal)==1);
        snapshot.talent_ranks[rework_catalog::kRankSlots[ordinal]]=100000;
        CHECK(rework_catalog::rank(snapshot,ordinal)==4);
    }
    CHECK(rework_catalog::kRankSlots[29]==4&&rework_catalog::kRankSlots[111]==10&&rework_catalog::kRankSlots[26]==12);
}
namespace qa10_fixture {
inline std::array<U32,256*256> tiles{};
inline U32* __cdecl get_tiles(){return tiles.data();}
}
inline void qa10_explored_map_preserves_current_fog(){
    using namespace rework_fixture;qa9_fixture::begin({});
    auto old_tiles=rework_combat_v5::get_tiles;rework_combat_v5::get_tiles=qa10_fixture::get_tiles;
    const auto old_mission=g.mission;auto mission=*old_mission;mission.mission_id=206;g.mission=&mission;
    constexpr U32 samples[]={0xa55affffu,0xa55a0000u,0xa55a55aau,0xa55aaa55u,0xffffffffu,0u,0x12345678u,0x87654321u};
    for(auto id:campaign_visibility::missions)for(U32 owner=0;owner<8;owner++){
        mission.mission_id=id;mission.owner=static_cast<U8>(owner);
        qa10_fixture::tiles.fill(0xa55affffu);
        for(U32 i=0;i<4096;i++)qa10_fixture::tiles[i]=samples[i%8];
        campaign_visibility::step();
        const U32 mask=~(1u<<(owner+8));
        for(U32 i=0;i<4096;i++)CHECK(qa10_fixture::tiles[i]==(samples[i%8]&mask));
        CHECK(qa10_fixture::tiles[4096]==0xa55affffu);
        // A native sight change on a later frame must survive exploration.
        qa10_fixture::tiles[0]^=1u<<owner;const U32 refreshed=qa10_fixture::tiles[0];
        campaign_visibility::step();CHECK(qa10_fixture::tiles[0]==refreshed);
    }
    mission.mission_id=104;qa10_fixture::tiles.fill(0xa55affffu);campaign_visibility::step();CHECK(qa10_fixture::tiles[0]==0xa55affffu);
    mission.mission_id=206;mission.width=128;campaign_visibility::step();CHECK(qa10_fixture::tiles[0]==0xa55affffu);
    g.mission=old_mission;rework_combat_v5::get_tiles=old_tiles;qa9_fixture::end();
}
inline void run_qa10_groups(){qa10_explored_map_preserves_current_fog();qa10_burrow_regeneration();qa10_lurker_click_attack_move_and_unburrow_boundaries();qa10_mobility_damage_ui_and_dead_projectile_snapshot();qa10_ground_roles_and_four_health_ranks();qa10_old_snapshots_fallback_and_native_cap();}
}
