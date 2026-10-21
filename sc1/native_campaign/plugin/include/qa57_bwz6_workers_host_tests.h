#pragma once
namespace host_test {
inline constexpr std::size_t qa57_group_count=3;
namespace qa57_fixture {
inline void __cdecl targeted_order(bw::Unit* u,U32 id,U32 x,U32 y,bw::Unit* target,U32){order(u,id,x,y,target,0);u->order_target.unit=target;}
inline void begin(){
    reset();for(const auto& m:campaign_config::kMissions)if(m.mission_id==606)g.mission=&m;
    CHECK(g.mission->mission_id==606&&player_owner()==3);CHECK(apply_snapshot(nullptr,economy_snapshot({})));g.create=economy_create_supply;g.order=targeted_order;game.frame_count=48;
}
inline bw::Unit* base(U32 id,int x,int y){
    auto u=economy_add(id,player_owner(),x,y);u->flags=1;
    auto mineral=economy_add(176,11,x+200,y);rework_economy_v5::amount(mineral,1500);return u;
}
inline void workers_at(int x,int y){
    U32 workers=0;living_units([&](bw::Unit* u){if(u->player==player_owner()&&u->unit_id==41){
        ++workers;CHECK(std::abs(int(u->flingy.position.x)-x)<=320&&std::abs(int(u->flingy.position.y)-y)<=320&&u->order==85);
        CHECK(u->order_target.unit&&std::abs(int(u->order_target.unit->flingy.position.y)-y)<=320);
    }});CHECK(workers==4&&rework_economy_v5::starting_workers==4);
    CHECK(game.minerals[player_owner()]==500&&game.gas[player_owner()]==500&&game.supplies[0].provided[player_owner()]==8&&game.supplies[0].used[player_owner()]==8);
}
}
inline void qa57_real_chk_hatcheries_choose_main_island_independent_of_order(){
    using namespace qa57_fixture;
    for(bool reversed:{false,true}){
        begin();
        if(reversed){base(131,4160,1680);base(131,4480,3632);base(131,5568,2768);base(131,5792,1744);base(132,4160,1424);base(131,4224,272);}
        else{base(131,4224,272);base(132,4160,1424);base(131,4160,1680);base(131,5792,1744);base(131,5568,2768);base(131,4480,3632);}
        rework_economy_v5::step();workers_at(4160,1424);
        const auto made=count;game.frame_count=240;rework_economy_v5::step();CHECK(count==made&&game.minerals[player_owner()]==500);
    }
}
inline void qa57_missing_island_depot_defers_without_crediting_wrong_base(){
    using namespace qa57_fixture;begin();base(131,4224,272);base(131,4480,3632);
    rework_economy_v5::step();CHECK(!rework_economy_v5::starting_bonus_credited&&rework_economy_v5::starting_workers==0&&game.minerals[player_owner()]==0&&game.gas[player_owner()]==0);
    base(132,4160,1424);game.frame_count=72;fail_spawn=true;rework_economy_v5::step();CHECK(rework_economy_v5::starting_bonus_credited&&rework_economy_v5::starting_workers==0);
    fail_spawn=false;game.frame_count=96;rework_economy_v5::step();workers_at(4160,1424);
}
inline void qa57_island_hatchery_fallback_retains_retry_and_supply_accounting(){
    using namespace qa57_fixture;begin();base(131,4224,272);base(131,4160,1680);
    rework_economy_v5::step();workers_at(4160,1680);
    CHECK(apply_snapshot(nullptr,economy_snapshot({},2)));game.frame_count=240;rework_economy_v5::step();workers_at(4160,1680);
}
inline void run_qa57_groups(){qa57_real_chk_hatcheries_choose_main_island_independent_of_order();qa57_missing_island_depot_defers_without_crediting_wrong_base();qa57_island_hatchery_fallback_retains_retry_and_supply_accounting();}
}
