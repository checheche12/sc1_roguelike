#pragma once
// Included inside host_test after the production combat adapter and fixture.
inline void phase_echo_cast(bw::Unit* caster,U32 order,bool success=true){
    caster->order=U8(order);caster->energy=200*256;
    rework_combat_v5::OrderScope cast(caster);
    if(success)caster->energy=150*256;
}
inline void phase_echo_native_casts_and_recipient_scope(){
    using namespace rework_fixture;
    for(const auto spec:{std::pair<U32,U32>{67,142},{67,148},{71,137},{71,147},{60,181},{63,182},{63,184},{63,186}}){
        begin({323,108,110});talent_power::enabled=true;install();
        auto caster=unit(spec.first,1,300,300,spec.first==71||spec.first==60);
        auto ground=unit(65,1,310,300),air_unit=unit(70,1,320,300,true),hero=unit(77,1,330,300),edge=unit(65,1,460,300);
        auto outside=unit(65,1,461,300),enemy=unit(65,6,310,310),worker=unit(64,1,320,310),building_=unit(162,1,330,310);
        auto foreign=unit(37,1,310,320),illusion=unit(65,1,320,320),frozen=unit(65,1,330,320),dead=unit(65,1,340,320);
        for(auto u:{ground,air_unit,hero,edge,outside,enemy,worker,building_,foreign,illusion,frozen,dead})u->shields=0;
        illusion->flags|=0x40000000u;frozen->stasis_timer=1;dead->flingy.hitpoints=0;
        CHECK(effective_max_shields(ground)>original_stat({0,7,65}));
        phase_echo_cast(caster,spec.second,false);
        CHECK(ground->shields==0); // Entering or canceling an order is not a cast.
        phase_echo_cast(caster,spec.second);
        for(auto u:{ground,air_unit,hero,edge})CHECK(u->shields==std::int32_t(std::uint64_t(effective_max_shields(u))*256/5));
        for(auto u:{outside,enemy,worker,building_,foreign,illusion,frozen,dead})CHECK(u->shields==0);
        finish();talent_power::enabled=false;
    }
}
inline void phase_echo_shared_cooldown_caps_and_lifecycle(){
    using namespace rework_fixture;begin({323,120,126});talent_power::enabled=true;
    auto first=unit(67,1,300,300),second=unit(71,1,320,300,true),patient=unit(65,1,310,300);
    const auto cap=std::int32_t(effective_max_shields(patient)*256);patient->shields=0;
    phase_echo_cast(first,142);CHECK(patient->shields==cap/5&&first->energy==175*256);
    phase_echo_cast(second,137);CHECK(patient->shields==cap/5&&second->energy==200*256);
    game.frame_count=219;phase_echo_cast(first,142);CHECK(patient->shields==cap/5);
    game.frame_count=220;phase_echo_cast(second,137);CHECK(patient->shields==cap*2/5); // Fully refunded successful Recall still triggers.
    game.frame_count=340;patient->shields=cap-1;phase_echo_cast(first,142);CHECK(patient->shields==cap);
    game.frame_count=460;phase_echo_cast(first,142);patient->shields=0;phase_echo_cast(second,147);CHECK(patient->shields==cap/5); // Full shields do not consume the recovery interval.
    patient->shields=0;rework_combat_v5::created(patient);phase_echo_cast(first,142);CHECK(patient->shields==cap/5);
    patient->shields=0;patient->player=6;phase_echo_cast(first,142);CHECK(patient->shields==0);
    finish();talent_power::enabled=false;
}
inline void phase_echo_ownership_and_wire_isolation(){
    using namespace rework_fixture;
    for(U32 mode:{0u,1u,2u,3u,4u}){
        begin({323});talent_power::enabled=true;
        auto caster=unit(mode==2?46u:67u,mode==1?6u:1u,300,300),patient=unit(65,1,310,300);patient->shields=0;
        if(mode==0)ranks[323]=0;
        if(mode==4)caster->flags|=0x40000000u;
        phase_echo_cast(caster,mode==3?3u:142u);CHECK(patient->shields==0);
        finish();talent_power::enabled=false;
    }
    reset();GrowthSnapshot snapshot{};snapshot.wire_version=2;snapshot.talent_bits[15]=1u<<30;
    CHECK(rework_catalog::rank(snapshot,323)==1&&rework_catalog::rank(snapshot,322)==0);
    CHECK(apply_snapshot(nullptr,snapshot));CHECK(rework_combat_v5::rank(323)==1);
    snapshot.talent_bits[15]|=2u<<28;
    CHECK(rework_catalog::rank(snapshot,323)==1&&rework_catalog::rank(snapshot,322)==2);
}
