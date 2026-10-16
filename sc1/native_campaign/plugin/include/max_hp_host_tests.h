#pragma once
// Production HP arithmetic and lifecycle tests. No engine, UI or game process.
namespace host_test {
void hp_maximum_all_regular_units() {
    reset();std::vector<bw::Unit*> enemies,own,neutral;
    for(auto id:frozen::kRegularCombatUnits){const auto base=original_stat({0,8,id});if(!base)continue;
        enemies.push_back(add(id,6,100,100,static_cast<int>(base)));own.push_back(add(id,1,200,100,static_cast<int>(base)));neutral.push_back(add(id,11,300,100,static_cast<int>(base)));}
    GrowthSnapshot s{};s.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,s));
    for(std::size_t i=0;i<enemies.size();i++){auto enemy=enemies[i];const auto base=original_stat({0,8,enemy->unit_id});const U32 max=static_cast<U32>((std::uint64_t(base)*11+5)/10);
        CHECK(effective_max_hp(enemy)==max);CHECK(enemy->flingy.hitpoints==static_cast<int>(max));
        CHECK(effective_max_hp(own[i])==base && effective_max_hp(neutral[i])==base);
        CHECK(raw_value(0,8,enemy->unit_id)==base);
    }
}
void hp_maximum_eligibility_and_session() {
    reset();auto own=add(0,1,100,100),enemy=add(0,6,200,100),neutral=add(0,11,300,100),hero=add(20,6,400,100),building=add(106,6,500,100);
    const auto base=original_stat({0,8,0});GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    CHECK(effective_max_hp(own)==base+2560);CHECK(effective_max_hp(enemy)==(base*11+5)/10);CHECK(effective_max_hp(neutral)==base);
    CHECK(effective_max_hp(hero)==original_stat({0,8,20}));CHECK(effective_max_hp(building)==original_stat({0,8,106}));
    own->flags|=0x40000000u;enemy->flags|=0x40000000u;
    CHECK(effective_max_hp(own)==base);CHECK(effective_max_hp(enemy)==base);
    own->flags=enemy->flags=0;g.active=false;CHECK(effective_max_hp(own)==base && effective_max_hp(enemy)==base);
    g.active=true;g.applied=false;CHECK(effective_max_hp(own)==base && effective_max_hp(enemy)==base);
}
void hp_maximum_elite_scope_nesting() {
    reset();GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    auto own=add(0,1,100,100),elite=add(0,6,200,100),normal=add(0,6,300,100);refresh_units();g.wave_spawn_number=0;mark_wave_unit(elite);
    const auto base=original_stat({0,8,0}),foe=(base*11+5)/10,maximum=foe*3/2;
    CHECK(effective_max_hp(elite)==maximum && effective_max_hp(normal)==foe);
    {OwnerDatScope first(6,6,elite);CHECK(raw_value(0,8,0)==maximum);
        {OwnerDatScope second(6,6,elite);CHECK(raw_value(0,8,0)==maximum);CHECK(effective_max_hp(elite)==maximum);}
        {OwnerDatScope normal_scope(6,6,normal);CHECK(raw_value(0,8,0)==foe);CHECK(effective_max_hp(elite)==maximum);}
        CHECK(raw_value(0,8,0)==maximum);
        {OwnerDatScope own_scope(1,1,own);CHECK(raw_value(0,8,0)==base+2560);CHECK(effective_max_hp(normal)==foe);}
        CHECK(raw_value(0,8,0)==maximum);
    }
    CHECK(raw_value(0,8,0)==base);
    elite->minor_unique_index++;CHECK(effective_max_hp(elite)==foe);
    elite->minor_unique_index--;elite->player=11;CHECK(effective_max_hp(elite)==base);
    elite->player=6;elite->unit_id=37;CHECK(effective_max_hp(elite)==owner_stat(6,{0,8,37}));
}
void hp_maximum_native_heal_cap() {
    reset();GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[5]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    auto unit=add(0,6,100,100);refresh_units();g.wave_spawn_number=0;mark_wave_unit(unit);const auto maximum=effective_max_hp(unit);
    unit->flingy.hitpoints=static_cast<int>(maximum-100);heal_enemy(unit,999999);CHECK(unit->flingy.hitpoints==static_cast<int>(maximum));
    unit->flingy.hitpoints=static_cast<int>(maximum-100);auto t=existing_track(unit);t->hp=unit->flingy.hitpoints;t->last_damage=0;regenerate_waves(game.elapsed_seconds);
    CHECK(unit->flingy.hitpoints==static_cast<int>(maximum));CHECK(raw_value(0,8,0)==original_stat({0,8,0}));
}
void __cdecl hp_maximum_give(bw::Unit* unit,U32 owner){unit->player=static_cast<U8>(owner);}
void hp_maximum_owner_transfer_ratio() {
    reset();GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    auto unit=add(0,6,100,100);refresh_units();g.wave_spawn_number=0;mark_wave_unit(unit);
    const auto before=effective_max_hp(unit);unit->flingy.hitpoints=static_cast<int>(before/4);const auto current=unit->flingy.hitpoints;
    owner_give_hook(unit,1,hp_maximum_give);const auto after=effective_max_hp(unit);
    CHECK(unit->flingy.hitpoints==static_cast<int>((std::uint64_t(current)*after+before/2)/before));
    CHECK(after==original_stat({0,8,0})+2560);CHECK(!existing_track(unit) || !existing_track(unit)->elite);
    const auto own_hp=unit->flingy.hitpoints;owner_give_hook(unit,6,hp_maximum_give);
    CHECK(effective_max_hp(unit)==owner_stat(6,{0,8,0}));CHECK(unit->flingy.hitpoints==static_cast<int>((std::uint64_t(own_hp)*effective_max_hp(unit)+after/2)/after));
}
void hp_maximum_cumulative_ratio_no_double_apply() {
    reset();auto unit=add(0,6,100,100,5120);GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[7]=1;s.completed_phase=1;CHECK(apply_snapshot(nullptr,s));
    refresh_units();g.wave_spawn_number=0;mark_wave_unit(unit);const auto first=unit->flingy.hitpoints;
    s.completed_phase=2;s.curse_counts[2]=2;CHECK(apply_snapshot(nullptr,s));
    CHECK(effective_max_hp(unit)==static_cast<U32>(original_stat({0,8,0})*12/10*3/2));
    CHECK(unit->flingy.hitpoints==static_cast<int>((std::uint64_t(first)*12+5)/11));
    const auto second=unit->flingy.hitpoints;CHECK(!apply_snapshot(nullptr,s));CHECK(unit->flingy.hitpoints==second);
}

void hp_cache_isolated_from_scoped_dat() {
    reset();auto own=add(0,1,100,100),enemy=add(0,6,200,100),neutral=add(0,11,300,100);
    auto protoss=add(65,1,100,200),foe=add(65,6,200,200),passive=add(65,11,300,200);
    GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.talent_bits[69/32]=1u<<(69%32);s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    U32 shield=0,maximum=0;const U32 stock_shield=original_stat({0,7,65});
    CHECK(max_hp_cache::read_display(protoss,maximum,shield) && maximum==owner_stat(1,{0,8,65}) && shield==stock_shield+20);
    CHECK(max_hp_cache::read_display(foe,maximum,shield) && maximum==owner_stat(6,{0,8,65}) && shield==stock_shield);
    CHECK(max_hp_cache::read_display(passive,maximum,shield) && maximum==original_stat({0,8,65}) && shield==stock_shield);
    {OwnerDatScope scope(1,1,protoss);CHECK(raw_value(0,7,65)==stock_shield+20);CHECK(max_hp_cache::read_display(foe,maximum,shield) && shield==stock_shield);}
    protoss->flags|=0x40000000u;CHECK(max_hp_cache::read_display(protoss,maximum,shield) && maximum==original_stat({0,8,65}) && shield==stock_shield);protoss->flags&=~0x40000000u;
    CHECK(max_hp_cache::read_display(own,maximum,shield) && shield==0);CHECK(max_hp_cache::read(own,maximum) && maximum==50*256);
    CHECK(max_hp_cache::read(enemy,maximum) && maximum==44*256);
    {OwnerDatScope scope(6,6,enemy);CHECK(raw_value(0,8,0)==44*256);CHECK(max_hp_cache::read(own,maximum)&&maximum==50*256);}
    g.wave_spawn_number=0;mark_wave_unit(enemy);CHECK(max_hp_cache::read(enemy,maximum)&&maximum==66*256);
    {OwnerDatScope scope(6,6,enemy);CHECK(raw_value(0,8,0)==66*256);CHECK(max_hp_cache::read(neutral,maximum)&&maximum==40*256);}
    enemy->flags|=0x40000000u;CHECK(max_hp_cache::read(enemy,maximum)&&maximum==40*256);
    bw::Unit external{};CHECK(!max_hp_cache::read(&external,maximum));CHECK(!max_hp_cache::read(nullptr,maximum));
    abandon_session();CHECK(!max_hp_cache::read(own,maximum));
}
bw::Unit* hp_cache_recycled=nullptr;
bw::Unit* __cdecl hp_cache_reuse_create(U32 id,int,int,U32 owner,const U8*) {hp_cache_recycled->unit_id=static_cast<std::uint16_t>(id);hp_cache_recycled->player=static_cast<U8>(owner);return hp_cache_recycled;}
void hp_cache_lifecycle_reuse_and_transfer() {
    reset();GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    auto unit=add(0,6,100,100);refresh_units();g.wave_spawn_number=0;mark_wave_unit(unit);U32 maximum=0;
    CHECK(max_hp_cache::read(unit,maximum)&&maximum==66*256);
    unit->minor_unique_index++;CHECK(max_hp_cache::read(unit,maximum)&&maximum==44*256);
    unit->minor_unique_index--;hp_cache_recycled=unit;
    // Simulate the native 8-bit identity wrapping. Creation clears a stale slot
    // before it can be reused as another elite with the same key.
    CHECK(owner_create_hook(0,0,0,6,nullptr,hp_cache_reuse_create)==unit);
    CHECK(max_hp_cache::read(unit,maximum)&&maximum==44*256);
    track_unit(unit)->elite=true;max_hp_cache::publish_unit(unit);CHECK(max_hp_cache::read(unit,maximum)&&maximum==66*256);
    owner_give_hook(unit,1,hp_maximum_give);CHECK(max_hp_cache::read(unit,maximum)&&maximum==50*256);
}
U32 hp_cache_transform_observed=0;
void __cdecl hp_cache_transform_native(bw::Unit* unit,U32 id) {
    // Exact integer ratio ordering observed at native RVA1c3420, including its
    // whole-HP truncation. A getter-only mock missed the two direct DAT reads.
    const U32 old_max=raw_value(0,8,unit->unit_id)>>8,current=static_cast<U32>(unit->flingy.hitpoints)>>8;
    unit->unit_id=static_cast<std::uint16_t>(id);const U32 new_max=raw_value(0,8,id)>>8;
    unit->flingy.hitpoints=static_cast<int>((old_max ? new_max*current/old_max:1u)<<8);
    CHECK(max_hp_cache::read(unit,hp_cache_transform_observed));
}
void hp_cache_transform_native_queries() {
    reset();GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));
    auto unit=add(5,6,100,100);refresh_units();g.wave_spawn_number=0;mark_wave_unit(unit);
    const auto expected=owner_stat(6,{0,8,30})*3/2;const auto hp=unit->flingy.hitpoints;const auto old_max=effective_max_hp(unit);
    const U32 native_expected=((expected>>8)*(static_cast<U32>(hp)>>8)/(old_max>>8))<<8;
    owner_transform_hook(unit,30,hp_cache_transform_native);
    CHECK(unit->flingy.hitpoints==static_cast<int>(native_expected));
    CHECK(raw_value(0,8,5)==original_stat({0,8,5}) && raw_value(0,8,30)==original_stat({0,8,30}));
    CHECK(hp_cache_transform_observed==expected);U32 maximum=0;CHECK(max_hp_cache::read(unit,maximum)&&maximum==expected);
}
void hp_cache_publication_guard_and_alliance() {
    reset();auto unit=add(0,6,100,100);GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));g.wave_spawn_number=0;mark_wave_unit(unit);
    U32 maximum=0;CHECK(max_hp_cache::read(unit,maximum)&&maximum==66*256);
    max_hp_cache::sequence.fetch_add(1);CHECK(!max_hp_cache::read(unit,maximum));max_hp_cache::sequence.fetch_add(1);
    game.alliances[1][6]=1;CHECK(max_hp_cache::publish());CHECK(max_hp_cache::read(unit,maximum)&&maximum==40*256);
    game.alliances[1][6]=0;CHECK(max_hp_cache::publish());CHECK(max_hp_cache::read(unit,maximum)&&maximum==66*256);
    max_hp_cache::reset();CHECK(!max_hp_cache::read(unit,maximum));CHECK(max_hp_cache::publish(true));CHECK(max_hp_cache::read(unit,maximum)&&maximum==66*256);
}
void run_max_hp_groups(){hp_maximum_all_regular_units();hp_maximum_eligibility_and_session();hp_maximum_elite_scope_nesting();hp_maximum_native_heal_cap();hp_maximum_owner_transfer_ratio();hp_maximum_cumulative_ratio_no_double_apply();hp_cache_isolated_from_scoped_dat();hp_cache_lifecycle_reuse_and_transfer();hp_cache_transform_native_queries();hp_cache_publication_guard_and_alliance();}
}
