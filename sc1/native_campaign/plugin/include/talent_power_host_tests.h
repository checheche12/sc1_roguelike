#pragma once
namespace host_test {
inline constexpr std::size_t talent_power_group_count=6;
inline void power_all_400_and_combined_owner_isolation(){
    for(U32 bit=0;bit<400;bit++){
        reset();GrowthSnapshot s{};s.wire_version=2;s.talent_bits[bit/32]|=1u<<(bit%32);
        if(bit>=238){const int slot=rework_catalog::kRankSlots[bit-238];if(slot>=0)s.talent_ranks[slot]=1;}
        CHECK(apply_snapshot(nullptr,s));
        for(const auto& e:g.friendly_edits){CHECK(owner_stat(1,e.key)==e.after);CHECK(owner_stat(6,e.key)==e.before);CHECK(read_entry(e.table,e.key.id)==e.before);}
    }
    reset();GrowthSnapshot all{};all.wire_version=2;
    for(U32 bit=0;bit<400;bit++)all.talent_bits[bit/32]|=1u<<(bit%32);
    for(U32 i=0;i<12;i++)all.talent_ranks[i]=10;
    CHECK(apply_snapshot(nullptr,all));
    for(const auto& e:g.friendly_edits)CHECK(e.after<=maximum(e.table));
}
inline void power_common_precision_and_caps(){
    using namespace rework_fixture;begin({29,11});ranks[29]=10;install();auto marine=unit(0,1,100,100),enemy=unit(37,6,120,100);
    std::int32_t damage=6*256;g.normal_hit=true;
    {rework_combat_v5::DamageScope hit(enemy,marine,0,1,damage);CHECK(damage==15*256);}
    damage=6*256;{rework_combat_v5::DamageScope hit(marine,enemy,35,1,damage);CHECK(hit.half_armor_reduction==128);}
    CHECK(std::abs(rework_combat_v5::cooldown_ratio(marine,0)-std::pow(.955,10))<1e-9);
    CHECK(rework_combat_v5::infantry_damage(0x7fffffff,0xffffffffu)==0x7fffffff);
    CHECK(rework_combat_v5::infantry_ui_value(marine,0,0xffffffffu)==0xffffffffu);
    ranks[11]=2;std::vector<Edit> edits;CHECK(rework_combat_v5::plan_stats(g.growth,edits));CHECK(effect_value(edits,{0,27,0},0)==1);
    finish();
}
inline void power_economy_actual_native_ledgers(){
    CHECK(talent_power::quarters(264)==7&&talent_power::quarters(238)==4&&talent_power::quarters(15)==4);
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({26})));CHECK(owner_stat(1,{0,8,0})==(40*256*128+50)/100);
    reset();auto s=economy_snapshot({0,1,3,7,24,151,117});CHECK(apply_snapshot(nullptr,s));
    CHECK(owner_stat(1,{0,40,0})==40);CHECK(owner_stat(1,{0,40,106})==280);
    CHECK(owner_stat(1,{0,40,41})==100);CHECK(owner_stat(1,{0,42,41})==150);
    CHECK(owner_stat(1,{0,40,73})==13);CHECK(owner_stat(1,{0,41,0})==0);
    auto worker_=economy_add(7);worker_->order=90;worker_->unit_specific.bytes[27]=8;worker_->carried_powerup_flags=2;
    game.minerals[1]=0;{rework_economy_v5::UnitScope scope(worker_);economy_return_original(worker_);}CHECK(game.minerals[1]==10);
    worker_->order=84;worker_->unit_specific.bytes[27]=8;worker_->carried_powerup_flags=1;
    game.gas[1]=0;{rework_economy_v5::UnitScope scope(worker_);economy_return_original(worker_);}CHECK(game.gas[1]==10);
    CHECK(talent_power::discount(3,1,1,2)==1&&talent_power::discount(3,0,1,2)==0);
}
inline void power_epic_legendary_projectiles_and_qualitative(){
    using namespace rework_fixture;begin({18,53});auto marine=unit(0,1,100,100),target=unit(37,6,120,100);
    auto b=bullet(marine,target,0);CHECK(rework_combat_v5::projectiles.at(b).percent==100);
    CHECK(rework_combat_v5::pending_shots.size()==3);CHECK(rework_combat_v5::pending_shots[0].percent==50);
    CHECK(rework_combat_v5::pending_shots[1].percent==35&&rework_combat_v5::pending_shots[2].percent==35);finish();
    begin({19,46});auto ghost=unit(1,1,100,100),enemy=unit(66,6,120,100);enemy->shields=80*256;game.upgrade_level_sc[6][15]=3;
    g.normal_hit=true;std::int32_t amount=100*256;
    {rework_combat_v5::DamageScope hit(enemy,ghost,2,1,amount);CHECK(rework_upgrade_storage::level(6,15)==0);}
    CHECK(rework_upgrade_storage::level(6,15)==3);g.normal_hit=false;amount=100*256;
    {rework_combat_v5::DamageScope hit(enemy,ghost,31,1,amount);CHECK(amount==150*256);}
    finish();
    for(bool learned:{false,true}){
        begin();if(learned)ranks[148]=1;
        auto carrier=unit(72,1,100,100,true),interceptor=unit(73,1,100,100,true);
        std::memcpy(interceptor->unit_specific.bytes,&carrier,sizeof(carrier));
        auto primary=unit(37,6,120,100),extra=unit(37,6,130,100);
        unit(37,6,140,100);unit(43,6,150,100,true);unit(37,6,160,100);unit(37,1,125,100);
        const auto w=rework_combat_v5::weapon(interceptor,false);CHECK(w<130);
        bullet(interceptor,primary,w);pulse(100);
        CHECK(multi_fixture::shots.size()==1&&extra);
        if(learned){rework_combat_v5::focus_hit(interceptor,primary,256,w);CHECK(rework_combat_v5::focus_damage(interceptor,primary,w,1000,true)==1200);}
        pulse(101);CHECK(multi_fixture::shots.size()==1);
        CHECK(rework_combat_v5::pending_shots.empty());finish();
    }
}
inline void power_carrier_cargo_and_legacy_conversion(){
    using namespace rework_carrier_tests;begin();talent(130);auto c=carrier(8);CHECK(rework_carrier_v5::capacity(c)==4);
    game.upgrade_level_sc[1][43]=1;CHECK(rework_carrier_v5::capacity(c)==8);
    talent(115);auto shuttle=fresh(69);CHECK(rework_cargo_v5::capacity(shuttle)==16);
    reset();GrowthSnapshot s{};s.talent_bits[0]=1u<<5;CHECK(apply_snapshot(nullptr,s));CHECK(owner_stat(1,{1,7,2})==3);CHECK(owner_stat(1,{1,14,2})==13);
}
inline void power_acid_fifteen_and_enemy_curses_unchanged(){
    using namespace rework_fixture;begin({86});auto target=unit(43,6,120,100,true);target->acid_spore_count=9;
    for(U32 i=0;i<12;i++)rework_combat_v5::add_spore(target,255,true);
    CHECK(target->acid_spore_count==15);CHECK(rework_combat_v5::extra_acid(*rework_combat_v5::acid_state(target))==6);finish();
    begin({102});auto caster=unit(46,1,100,100),victim=unit(37,6,120,100);
    victim->flingy.hitpoints=30*256;victim->plague_timer=75;
    rework_combat_v5::attach(102,victim,caster,600,0,75);
    const U32 tick=original_stat({1,14,60})*256/76;
    victim->flingy.hitpoints-=int(tick);--victim->plague_timer;pulse(101);
    CHECK(victim->flingy.hitpoints==30*256-int(tick*2));
    const auto hp=victim->flingy.hitpoints;pulse(102);CHECK(victim->flingy.hitpoints==hp);finish();
    reset();GrowthSnapshot s{};s.curse_counts[1]=1;s.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,s));
    CHECK(owner_stat(6,{1,14,35})==6&&owner_stat(6,{0,8,37})==9856);
}
inline void run_talent_power_groups(){
    talent_power::enabled=true;
    power_all_400_and_combined_owner_isolation();power_common_precision_and_caps();
    power_economy_actual_native_ledgers();power_epic_legendary_projectiles_and_qualitative();
    power_carrier_cargo_and_legacy_conversion();power_acid_fifteen_and_enemy_curses_unchanged();
    talent_power::enabled=false;
}
}
