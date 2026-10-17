#pragma once
namespace host_test {
inline constexpr std::size_t qa12_group_count=7;
namespace qa12_fixture {
inline GrowthSnapshot talent(U32 ordinal){GrowthSnapshot s{};s.wire_version=2;const U32 bit=238+ordinal;s.talent_bits[bit/32]|=1u<<(bit%32);return s;}
inline void begin(U32 ordinal,bool held=true){
    rework_fixture::begin({});talent_power::enabled=true;
    rework_combat_v5::bind([](const GrowthSnapshot& s,U32 n) noexcept {return rework_catalog::rank(s,n);});
    g.growth=held?talent(ordinal):GrowthSnapshot{};g.growth.wire_version=2;
}
inline bw::Unit* __cdecl birth(U32 id,int x,int y,U32 owner,const U8*){auto u=add(id,owner,x,y);u->energy=0;return u;}
inline bw::Unit* produce(U32 id,U32 owner=1){const U8 skins[]={U8(owner),U8(owner)};return owner_create_hook(id,100,100,owner,skins,birth);}
inline void complete(bw::Unit* u,U32 energy=50){u->energy=std::uint16_t(energy*256);u->flags|=1;}
inline U32 total(bw::Unit* u){auto s=rework_combat_v5::state(u);return U32(u->energy)+(s?s->energy_reserve:0);}
inline void end(){rework_fixture::finish();talent_power::enabled=false;}
}
inline void qa12_energy_all_twenty_births_wait_for_completion(){
    using namespace qa12_fixture;U32 tested=0;
    for(U32 ordinal:{36u,76u,118u})for(U32 id=0;id<106;id++)if(rework_combat_v5::group(ordinal,id)){
        begin(ordinal);auto u=produce(id);CHECK(total(u)==0);
        rework_fixture::pulse(101);CHECK(total(u)==0&&!rework_combat_v5::state(u)->energy_granted);
        complete(u);rework_combat_v5::max_energy_hook(u,rework_fixture::max200);rework_fixture::pulse(102);
        CHECK(total(u)==250*256);CHECK(rework_combat_v5::state(u)->energy_granted);
        CHECK(rework_combat_v5::energy_total_cap(u,*rework_combat_v5::state(u))==400*256);
        rework_energy_ui::publish();CHECK(rework_energy_ui::current(u)==250);
        rework_fixture::pulse(103);CHECK(total(u)==250*256);
        std::printf("AUDIT energy_birth ordinal=%u unit=%u initial=50 completed=250 maximum=400 once=ok\n",ordinal,id);
        ++tested;end();
    }CHECK(tested==20);
}
inline void qa12_energy_acquisition_during_and_after_production(){
    using namespace qa12_fixture;
    for(U32 ordinal:{36u,76u,118u}){
        begin(ordinal,false);const U32 id=ordinal==36?1u:ordinal==76?45u:67u;
        auto existing=produce(id),building=produce(id);complete(existing);
        const auto previous=g.growth;g.growth=talent(ordinal);rework_combat_v5::growth_applied(previous,g.growth);
        CHECK(total(existing)==250*256&&total(building)==0);
        complete(building);rework_fixture::pulse(101);CHECK(total(building)==250*256);
        auto later=produce(id);complete(later);rework_fixture::pulse(102);CHECK(total(later)==250*256);
        rework_combat_v5::growth_applied(g.growth,g.growth);CHECK(total(existing)==250*256&&total(later)==250*256);end();
    }
}
inline void qa12_energy_never_refills_spent_or_rebound_units(){
    using namespace qa12_fixture;begin(36);auto u=produce(1);complete(u);rework_fixture::pulse(101);u->energy-=75*256;
    rework_fixture::pulse(102);CHECK(total(u)==175*256);
    u->energy+=8;rework_fixture::pulse(103);CHECK(total(u)==175*256+8);
    u->player=6;rework_fixture::pulse(104);u->player=1;rework_fixture::pulse(105);CHECK(total(u)==175*256+8);
    // A genuine birth, even with an identical wrapped generation byte, resets once.
    complete(u);rework_combat_v5::created(u);rework_fixture::pulse(106);CHECK(total(u)==250*256);end();
}
inline void qa12_energy_controls_exclude_enemies_hallucinations_and_non_targets(){
    using namespace qa12_fixture;
    begin(36,false);auto u=produce(1);complete(u);rework_fixture::pulse(101);CHECK(total(u)==50*256);end();
    begin(36);auto enemy=produce(1,6),fake=produce(1),marine=produce(0);complete(enemy);complete(fake);complete(marine);fake->flags|=0x40000000u;
    rework_fixture::pulse(101);CHECK(total(enemy)==50*256&&total(fake)==50*256&&total(marine)==50*256);end();
}
inline void qa12_energy_virtual_cap_and_spending(){
    using namespace qa12_fixture;begin(118,false);auto u=produce(67);complete(u,250);
    const auto previous=g.growth;g.growth=talent(118);
    rework_combat_v5::state(u)->energy_cap=250*256;rework_combat_v5::growth_applied(previous,g.growth);
    CHECK(total(u)==450*256&&u->energy==65535);rework_energy_ui::publish();CHECK(rework_energy_ui::current(u)==450);
    u->energy-=75*256;rework_fixture::pulse(101);CHECK(total(u)==375*256);rework_energy_ui::publish();CHECK(rework_energy_ui::current(u)==375);end();
}
inline void qa12_retired_reposition_cannot_move_old_owned_bits(){
    using namespace rework_fixture;begin({14});relocation();auto u=unit(0,1,100,100);auto s=rework_combat_v5::state(u);s->last_launch=100;
    u->order=6;u->order_target={300,100,nullptr};pulse(101);CHECK(u->flingy.position.x==100&&u->flingy.position.y==100);
    relocation_end();finish();
}
inline void __cdecl qa12_native_morph(bw::Unit* u,U32 id){u->unit_id=std::uint16_t(id);u->flags&=~1u;u->energy=0;}
inline void qa12_energy_morph_births_reuse_egg_and_merge_slots(){
    using namespace qa12_fixture;
    for(U32 id:{45u,46u,49u,52u,63u}){
        begin(id==63?118:76);auto u=produce(id==63?61:35);
        if(id!=63)owner_transform_hook(u,36,qa12_native_morph);
        owner_transform_hook(u,id,qa12_native_morph);rework_fixture::pulse(101);CHECK(total(u)==0);
        complete(u);rework_fixture::pulse(102);CHECK(total(u)==250*256);
        rework_fixture::pulse(103);CHECK(total(u)==250*256);end();
    }
}
inline void run_qa12_groups(){qa12_energy_all_twenty_births_wait_for_completion();qa12_energy_acquisition_during_and_after_production();qa12_energy_never_refills_spent_or_rebound_units();qa12_energy_controls_exclude_enemies_hallucinations_and_non_targets();qa12_energy_virtual_cap_and_spending();qa12_retired_reposition_cannot_move_old_owned_bits();qa12_energy_morph_births_reuse_egg_and_merge_slots();}
}
