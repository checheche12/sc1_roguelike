#pragma once
// Scheduler/facing regression model, complemented by the actual-game demo.
namespace host_test {
inline constexpr std::size_t mind_control_group_count=3;
namespace mind_control_fixture {
inline bw::Unit* rejected=nullptr;
inline U32 successes=0;
inline void __cdecl cast(bw::Unit* u){
    // Native order dispatch skips a waiting unit. A failed facing/target check
    // retains the eight-tick wait; successful order completion clears it.
    if(u->order_wait){--u->order_wait;return;}
    u->order_wait=8;
    auto target=u->order_target.unit;if(u->order!=182||!target)return;
    const U32 delta=(U32(u->flingy.facing_direction)+256-multi_target::direction_to(u,target))&255u;
    if(std::min(delta,256-delta)>5||target==rejected)return;
    rework_fixture::native_cast(u);u->order_wait=0;++successes;
}
inline void begin(bool talent=true){qa9_fixture::begin(talent?std::initializer_list<U32>{146}:std::initializer_list<U32>{});rejected=nullptr;successes=0;}
inline void primary(bw::Unit* caster,bw::Unit* target){
    caster->energy=200*256;caster->shields=180*256;caster->order=182;caster->order_wait=0;
    caster->flingy.facing_direction=U8(multi_target::direction_to(caster,target));multi_fixture::target(caster,target);
    {rework_combat_v5::OrderScope scope(caster,cast);cast(caster);}
}
}
inline void mind_control_spread_targets_obey_cap_and_single_cost(){
    using namespace rework_fixture;using namespace mind_control_fixture;
    for(bool talent:{false,true})for(U32 enemies:{3u,7u}){
        mind_control_fixture::begin(talent);auto caster=unit(63,1,100,100),target=unit(37,6,140,100);
        std::vector<bw::Unit*> targets{target};
        for(U32 i=1;i<enemies;++i)targets.push_back(unit(12,6,145+int(i)*5,120+int(i)*3,true));
        primary(caster,target);U32 controlled_count=0;for(auto u:targets)controlled_count+=u->player==1;
        CHECK(controlled_count==(talent?std::min(enemies,5u):1u));CHECK(successes==controlled_count);
        CHECK(caster->energy==50*256&&caster->shields==0);
        CHECK(caster->order_wait==0&&caster->flingy.facing_direction==64);
        CHECK(caster->order==3&&caster->order_target.unit==target);qa9_fixture::end();
    }
}
inline void mind_control_rejection_loaded_and_allied_targets(){
    using namespace rework_fixture;using namespace mind_control_fixture;
    mind_control_fixture::begin();auto caster=unit(63,1,100,100),target=unit(37,6,140,100);
    rejected=unit(37,6,142,100);auto loaded=unit(37,6,144,100),ally=unit(37,1,146,100);
    loaded->flags|=0x40u;
    std::vector<bw::Unit*> targets;
    for(U32 i=0;i<5;++i)targets.push_back(unit(12,6,155+int(i)*5,125+int(i)*3,true));
    primary(caster,target);U32 controlled_count=1;for(auto u:targets)controlled_count+=u->player==1;
    CHECK(controlled_count==5&&successes==5);CHECK(rejected->player==6&&loaded->player==6&&ally->player==1);
    CHECK(caster->energy==50*256&&caster->shields==0&&caster->order_wait==0);qa9_fixture::end();
}
inline void mind_control_borrowed_cast_restores_pending_order(){
    using namespace rework_fixture;using namespace mind_control_fixture;
    for(bool reject:{false,true}){
        mind_control_fixture::begin();auto caster=unit(63,1,100,100),target=unit(37,6,140,130);
        if(reject)rejected=target;
        caster->order=6;caster->order_state=3;caster->order_signal=5;caster->order_timer=9;
        caster->order_wait=7;caster->flingy.facing_direction=222;caster->energy=50*256;caster->shields=90*256;
        caster->order_target={600,700,nullptr};caster->flingy.move_target={650,750,nullptr};
        caster->order_queue_begin=reinterpret_cast<decltype(caster->order_queue_begin)>(std::uintptr_t(0x1234));
        caster->order_queue_end=reinterpret_cast<decltype(caster->order_queue_end)>(std::uintptr_t(0x5678));
        const auto before=*caster;
        rework_combat_v5::borrowed_order(caster,cast,182,target,140,130);
        CHECK(target->player==(reject?6u:1u));CHECK(successes==(reject?0u:1u));
        CHECK(caster->order==6&&caster->order_state==3&&caster->order_signal==5&&caster->order_timer==9);
        CHECK(caster->order_wait==7&&caster->flingy.facing_direction==222);
        CHECK(caster->energy==50*256&&caster->shields==90*256&&caster->flags==before.flags);
        CHECK(caster->order_target.x==600&&caster->order_target.y==700&&!caster->order_target.unit);
        CHECK(caster->order_queue_begin==before.order_queue_begin&&caster->order_queue_end==before.order_queue_end);
        CHECK(caster->flingy.move_target.x==650&&caster->flingy.move_target.y==750);
        qa9_fixture::end();
    }
}
inline void run_mind_control_groups(){mind_control_spread_targets_obey_cap_and_single_cost();mind_control_rejection_loaded_and_allied_targets();mind_control_borrowed_cast_restores_pending_order();}
}
