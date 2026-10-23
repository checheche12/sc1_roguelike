#pragma once
namespace host_test {
inline constexpr std::size_t qa82_group_count=3;
namespace qa82_fixture {
inline U32 remaining=0;
inline bw::Unit* __cdecl limited_create(U32 id,int x,int y,U32 owner,const U8* skins){
    if(!remaining)return nullptr;--remaining;return economy_create_supply(id,x,y,owner,skins);
}
inline void begin(U32 mission){
    reset();for(const auto& m:campaign_config::kMissions)if(m.mission_id==mission)g.mission=&m;
    CHECK(g.mission->mission_id==mission);CHECK(apply_snapshot(nullptr,economy_snapshot({})));
    g.create=economy_create_supply;g.order=qa57_fixture::targeted_order;game.frame_count=48;
}
inline void base(U32 mission){
    const U32 id=mission/100==1?106u:mission/100==3?154u:131u;
    auto u=economy_add(id,player_owner(),1024,1024);u->flags=1;
    auto mineral=economy_add(176,11,1224,1024);rework_economy_v5::amount(mineral,1500);
}
inline void check_support(U32 mission,U32 amount,U32 workers){
    const U32 race=mission/100==1?1u:mission/100==3?2u:0u,id=race==1?7u:race==2?64u:41u;
    U32 actual=0;living_units([&](bw::Unit* u){if(u->player==player_owner()&&u->unit_id==id){++actual;CHECK(u->order==85&&u->order_target.unit);}});
    CHECK(actual==workers&&rework_economy_v5::starting_workers==workers);
    CHECK(game.minerals[player_owner()]==amount&&game.gas[player_owner()]==amount);
    CHECK(game.supplies[race].provided[player_owner()]==workers*2&&game.supplies[race].used[player_owner()]==workers*2);
    for(U32 owner=0;owner<8;++owner)if(owner!=player_owner())CHECK(game.minerals[owner]==0&&game.gas[owner]==0);
}
}
inline void qa82_late_support_scope_and_one_time_delivery(){
    using namespace qa82_fixture;
    for(const auto& m:campaign_config::kMissions){
        const U32 campaign=m.mission_id/100,ordinal=m.mission_id%100;
        const bool expected=(campaign==1||campaign==2||campaign==3||campaign==6)&&(ordinal==9||ordinal==10);
        CHECK(rework_economy_v5::late_campaign_support(m.mission_id)==expected);
    }
    for(U32 mission:{109u,110u,209u,210u,309u,310u,609u,610u,108u,208u,308u,608u}){
        begin(mission);base(mission);rework_economy_v5::step();
        const bool late=mission%100>=9;check_support(mission,late?750:500,late?6:4);
        CHECK(apply_snapshot(nullptr,economy_snapshot({},2)));game.frame_count=480;rework_economy_v5::step();
        check_support(mission,late?750:500,late?6:4);
        std::printf("QA82_STARTING_SUPPORT mission=%u resources=%u workers=%u once=1\n",mission,late?750u:500u,late?6u:4u);
    }
}
inline void qa82_support_waits_for_settlement_and_retries_partial_spawn(){
    using namespace qa82_fixture;begin(309);rework_economy_v5::step();
    CHECK(!rework_economy_v5::starting_bonus_credited&&game.minerals[player_owner()]==0);
    base(309);remaining=2;g.create=limited_create;rework_economy_v5::step();
    CHECK(rework_economy_v5::starting_bonus_credited&&rework_economy_v5::starting_workers==2);
    CHECK(game.minerals[player_owner()]==750&&game.supplies[2].provided[player_owner()]==12);
    game.frame_count=60;rework_economy_v5::step();CHECK(rework_economy_v5::starting_workers==2);
    remaining=20;game.frame_count=72;rework_economy_v5::step();check_support(309,750,6);
    game.frame_count=240;rework_economy_v5::step();check_support(309,750,6);
}
inline void qa82_nonproduction_and_unfinished_bases_never_credit(){
    using namespace qa82_fixture;begin(309);base(309);
    living_units([&](bw::Unit* u){if(u->unit_id==154)u->flags=0;});
    rework_economy_v5::step();CHECK(!rework_economy_v5::starting_bonus_credited);
    auto mission=*g.mission;mission.no_production=true;g.mission=&mission;
    living_units([&](bw::Unit* u){if(u->unit_id==154)u->flags=1;});
    rework_economy_v5::step();CHECK(!rework_economy_v5::starting_bonus_credited&&rework_economy_v5::starting_workers==0);
}
inline void run_qa82_groups(){qa82_late_support_scope_and_one_time_delivery();qa82_support_waits_for_settlement_and_retries_partial_spawn();qa82_nonproduction_and_unfinished_bases_never_credit();}
}
