#pragma once
namespace host_test {
inline constexpr std::size_t qa16_group_count=3;
inline void qa16_fifty_percent_ranged_melee_and_no_recursion(){
    using namespace rework_fixture;qa9_fixture::begin({18});auto source=unit(0,1,100,100),target=unit(37,6,120,100);
    bullet(source,target,0);CHECK(rework_combat_v5::pending_shots.size()==1);
    CHECK(rework_combat_v5::pending_shots[0].percent==50);pulse(101);CHECK(rework_combat_v5::pending_shots.empty());
    CHECK(multi_fixture::shots.size()==2); // Primary and exactly one secondary.
    const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa9_fixture::damage;
    auto melee=unit(40,1,130,100);const auto hp=target->flingy.hitpoints;
    rework_combat_v5::ordinary_hit(melee,target,5*256,40,false);
    CHECK(target->flingy.hitpoints==hp-5*128);
    rework_combat_v5::ordinary_hit(melee,target,5*256,40,true);CHECK(target->flingy.hitpoints==hp-5*128);
    combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa16_broodlings_stack_melee_common_and_spawn_initialization(){
    using namespace rework_fixture;
    for(bool legendary:{false,true})for(U32 stacks=1;stacks<=4;stacks++){
        qa9_fixture::begin({8,11,67,70});ranks[67]=ranks[70]=ranks[11]=stacks;if(legendary)ranks[104]=1;install();CHECK(max_hp_cache::publish());
        auto queen=unit(45,1,100,100),victim=unit(37,6,120,100),old=unit(40,1,90,100);old->flingy.hitpoints=7*256;
        const U32 base=original_stat({0,8,40}),expected=owner_stat(1,{0,8,40});CHECK(expected>base);
        const auto weapon=original_stat({0,17,40});CHECK(owner_stat(1,{1,14,weapon})>original_stat({1,14,weapon}));
        auto b=bullet(queen,victim,57);bw::Unit* born=nullptr;
        {rework_combat_v5::MissileScope impact(b);born=rank_fixture::create_full(40,120,100,1,nullptr);born->death_timer=1800;born->flingy.hitpoints=base;}
        CHECK(U32(born->flingy.hitpoints)==expected&&old->flingy.hitpoints==7*256);
        U32 spawned=0;living_units([&](bw::Unit* u){if(u!=old&&u->player==1&&u->unit_id==40){CHECK(U32(u->flingy.hitpoints)==expected);++spawned;}});
        CHECK(spawned==(legendary?18u:1u));
        CHECK(owner_stat(6,{0,8,40})==base);CHECK(rework_combat_v5::frontline_rank(born)==stacks);
        CHECK(rework_combat_v5::speed_ratio(born)>1.0);CHECK(rework_combat_v5::cooldown_ratio(born,weapon)<1.0);
        U32 shown=0,shield=0;CHECK(max_hp_cache::read_display(born,shown,shield)&&shown==expected);
        qa9_fixture::end();
    }
}
inline void qa16_infest_controls_without_energy_and_restores_owner(){
    using namespace rework_fixture;qa9_fixture::begin({107});rework_combat_v5::native_give=give;
    auto queen=unit(45,1,100,100),target=unit(37,6,120,100),extra=unit(38,6,130,100);queen->energy=0;
    target->flingy.hitpoints=int(effective_max_hp(target)/2);extra->flingy.hitpoints=int(effective_max_hp(extra)/2);queen->order=27;multi_fixture::target(queen,target);
    {rework_combat_v5::OrderScope scope(queen);CHECK(scope.handled());}
    CHECK(target->player==1&&extra->player==1&&queen->energy==0);
    CHECK(rework_combat_v5::persistent.size()==2);pulse(100+120*24);
    CHECK(target->player==6&&extra->player==6&&queen->energy==0);qa9_fixture::end();
}
inline void run_qa16_groups(){qa16_fifty_percent_ranged_melee_and_no_recursion();qa16_broodlings_stack_melee_common_and_spawn_initialization();qa16_infest_controls_without_energy_and_restores_owner();}
}
