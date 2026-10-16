#pragma once
// Lifecycle regressions use production callbacks and real managed DAT.
// These tests do not execute the game engine or prove gameplay speed/DPS.
namespace host_test {
void audit_supply_uses_unit_race() {
    reset();g.mission=&campaign_config::kMissions[0];
    for(const auto& mission:campaign_config::kMissions)if(mission.race==2){g.mission=&mission;break;}
    CHECK(g.mission->race==2);const auto owner=player_owner();
    auto vulture=add(2,owner,100,100);(void)vulture;
    game.supplies[0].used[owner]=18;game.supplies[1].used[owner]=20;game.supplies[2].used[owner]=24;
    GrowthSnapshot s{};s.talent_bits[0]=1u<<7;CHECK(apply_snapshot(nullptr,s));
    CHECK(game.supplies[0].used[owner]==18);
    CHECK(game.supplies[1].used[owner]==18);
    CHECK(game.supplies[2].used[owner]==24);
}
void __cdecl audit_same_owner_engine_noop(bw::Unit*,U32) {}
void audit_same_owner_give_preserves_effects() {
    reset();GrowthSnapshot s{};s.curse_counts[3]=s.curse_counts[7]=s.curse_counts[8]=1;
    CHECK(apply_snapshot(nullptr,s));auto u=add(3,6,100,100,10000);refresh_units();
    g.wave_spawn_number=0;mark_wave_unit(u);u->flingy.top_speed=1000;apply_unit_motion();
    auto t=existing_track(u);CHECK(t && t->elite && t->barrier && t->spawned);
    const auto hp=u->flingy.hitpoints;const auto speed=u->flingy.top_speed;
    owner_give_hook(u,6,audit_same_owner_engine_noop);
    CHECK(u->flingy.hitpoints==hp && u->flingy.top_speed==speed);
    t=existing_track(u);CHECK(t && t->elite && t->barrier && t->spawned);
}
void audit_transform_does_not_compound_speed() {
    reset();GrowthSnapshot s{};s.curse_counts[3]=1;CHECK(apply_snapshot(nullptr,s));
    auto tank=add(5,6,100,100,10000);tank->flingy.top_speed=1000;apply_unit_motion();
    CHECK(tank->flingy.top_speed==1075);
    // A native mode transition is allowed to retain movement fields. Restore
    // our multiplier before it runs so retained fields cannot become the base.
    owner_transform_hook(tank,30,fake_transform);apply_unit_motion();
    CHECK(tank->flingy.top_speed==1075);
    owner_transform_hook(tank,5,fake_transform);apply_unit_motion();
    CHECK(tank->flingy.top_speed==1075);
}
U32 __cdecl audit_weapon_range_return(bw::Unit*,U32 weapon) {return raw_value(1,5,weapon);}
void audit_shared_weapon_excludes_raszagal() {
    reset();GrowthSnapshot s{};s.talent_bits[102/32]=1u<<(102%32);CHECK(apply_snapshot(nullptr,s));
    auto corsair=add(60,1,100,100),hero=add(98,1,200,100),enemy=add(60,6,300,100);
    const auto base=original_stat({1,5,100});
    CHECK(owner_range_hook(corsair,100,audit_weapon_range_return)==base+32);
    CHECK(owner_range_hook(hero,100,audit_weapon_range_return)==base);
    CHECK(owner_range_hook(enemy,100,audit_weapon_range_return)==base);
    {OwnerDatScope outer(1,1,corsair);
        CHECK(owner_range_hook(hero,100,audit_weapon_range_return)==base);
        CHECK(raw_value(1,5,100)==base+32);
    }
    CHECK(raw_value(1,5,100)==base);
}
void audit_base_curses_include_broodling_and_infested_terran() {
    reset();auto broodling=add(40,6,100,100),infested=add(50,6,200,100);
    for(auto u:{broodling,infested}){u->flingy.hitpoints=static_cast<int>(original_stat({0,8,u->unit_id}));u->flingy.top_speed=1000;}
    GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[3]=1;CHECK(apply_snapshot(nullptr,s));
    for(auto u:{broodling,infested}) {
        CHECK(regular_enemy(u));
        CHECK(u->flingy.hitpoints==static_cast<int>((std::uint64_t(original_stat({0,8,u->unit_id}))*11+5)/10));
    }
    // This asserts the speed field, not iscript displacement (separately open).
    apply_unit_motion();CHECK(broodling->flingy.top_speed==1075 && infested->flingy.top_speed==1075);
    CHECK(!regular_combat_type(7) && !regular_combat_type(20));
}
void audit_hallucinations_keep_original_stats() {
    reset();auto marine=add(0,1,100,100,5120),zealot=add(65,1,200,100,10000),dt=add(61,1,300,100,10000);
    for(auto u:{marine,zealot,dt})u->flags|=0x40000000u;
    zealot->shields=30*256;dt->flingy.top_speed=1000;marine->ground_cooldown=15;
    GrowthSnapshot s{};for(U32 bit:{0u,2u,69u,73u,86u})s.talent_bits[bit/32]|=1u<<(bit%32);
    CHECK(apply_snapshot(nullptr,s));CHECK(marine->flingy.hitpoints==5120 && zealot->shields==30*256);
    note_attack_launch(marine,0);apply_unit_motion();
    CHECK(dt->flingy.top_speed==1000 && marine->ground_cooldown==15);
    {OwnerDatScope scope(1,1,zealot);CHECK(raw_value(0,27,65)==original_stat({0,27,65}));CHECK(raw_value(0,7,65)==original_stat({0,7,65}));}
    {OwnerDatScope scope(1,1,marine);CHECK(raw_value(0,8,0)==original_stat({0,8,0}));}
}
bw::Unit* audit_created_clone=nullptr;
bw::Unit* __cdecl audit_create_clone(U32 id,int x,int y,U32 owner,const U8*) {
    auto result=add(id,owner,x,y,static_cast<int>(raw_value(0,8,id)));
    result->shields=static_cast<int>(raw_value(0,7,id)*256);return result;
}
void __cdecl audit_cast_clone(bw::Unit* caster) {
    // Mirrors native ordering: create/finish first; mark hallucination after.
    audit_created_clone=owner_create_hook(65,100,100,caster->player,nullptr,audit_create_clone);
    CHECK(audit_created_clone && !hallucination(audit_created_clone));
    audit_created_clone->flags|=0x40000000u;
}
void audit_hallucination_birth_is_unmodified() {
    reset();GrowthSnapshot s{};for(U32 bit:{69u,85u})s.talent_bits[bit/32]|=1u<<(bit%32);CHECK(apply_snapshot(nullptr,s));
    auto caster=add(67,1,100,100);caster->order=148;
    owner_order_hook(caster,audit_cast_clone);
    CHECK(audit_created_clone->flingy.hitpoints==static_cast<int>(original_stat({0,8,65})));
    CHECK(audit_created_clone->shields==static_cast<int>(original_stat({0,7,65})*256));
    CHECK(hallucination_creation_depth==0);
    auto real=owner_create_hook(65,100,100,1,nullptr,audit_create_clone);
    CHECK(real->flingy.hitpoints==static_cast<int>(owner_stat(1,{0,8,65})));
    CHECK(real->shields==static_cast<int>(owner_stat(1,{0,7,65})*256));
}
void audit_damage_subjects_are_independent() {
    reset();GrowthSnapshot s{};s.talent_bits[86/32]=1u<<(86%32);s.curse_counts[1]=1;CHECK(apply_snapshot(nullptr,s));
    auto target=add(65,1,100,100),source=add(37,6,200,100);target->flags|=0x40000000u;
    {OwnerDatScope outer(1,1);OwnerDatScope hit(1,6,target,source);
        CHECK(raw_value(0,27,65)==original_stat({0,27,65}));CHECK(raw_value(1,14,35)==owner_stat(6,{1,14,35}));
    }
    target->flags&=~0x40000000u;source->flags|=0x40000000u;
    {OwnerDatScope hit(1,6,target,source);
        CHECK(raw_value(0,27,65)==owner_stat(1,{0,27,65}));CHECK(raw_value(1,14,35)==original_stat({1,14,35}));
    }
}
void __cdecl audit_lethal_damage(bw::Unit* u,std::int32_t,bw::Unit*,U32 player,U32) {
    u->last_attacking_player=static_cast<U8>(player);owner_kill_hook(u,kill);
}
void audit_death_count_needs_lethal_damage_once() {
    reset();GrowthSnapshot s{};s.curse_counts[6]=1;CHECK(apply_snapshot(nullptr,s));
    auto scripted=add(0,6,100,100);scripted->last_attacking_player=1;
    owner_kill_hook(scripted,kill);CHECK(g.kills_for_wave==0);
    auto fought=add(0,6,100,100);owner_damage_hook(fought,99999,nullptr,1,1,audit_lethal_damage);
    CHECK(g.kills_for_wave==1);owner_kill_hook(fought,kill);CHECK(g.kills_for_wave==1);
    auto allied=add(0,6,100,100);owner_damage_hook(allied,99999,nullptr,4,1,audit_lethal_damage);CHECK(g.kills_for_wave==1);
    fought->minor_unique_index++;fought->flingy.hitpoints=100;fought->order=3;
    owner_damage_hook(fought,99999,nullptr,1,1,audit_lethal_damage);CHECK(g.kills_for_wave==2);
}
void audit_mission_unit_bomb_exclusion_retains_identity() {
    reset();for(const auto& m:campaign_config::kMissions)if(m.mission_id==608)g.mission=&m;
    CHECK(g.mission->mission_id==608);auto required=add(61,1,976,1949,10000);
    auto ordinary=add(61,player_owner(),976,1949,10000);capture_objective_units();
    CHECK(protected_objective_unit(required) && !protected_objective_unit(ordinary));
    required->player=static_cast<U8>(player_owner());CHECK(protected_objective_unit(required));
    GrowthSnapshot s{};CHECK(apply_snapshot(nullptr,s));
    g.bombs.push_back({976,1949,1,25,8,6});game.frame_count=25;update_diversity();
    CHECK(required->flingy.hitpoints==10000 && ordinary->flingy.hitpoints==10000-8*256);
    owner_kill_hook(required,kill);required->flingy.hitpoints=10000;required->order=3;
    CHECK(!protected_objective_unit(required));
}
void run_effect_audit_lifecycle_groups() {
    audit_supply_uses_unit_race();audit_same_owner_give_preserves_effects();audit_transform_does_not_compound_speed();
    audit_shared_weapon_excludes_raszagal();audit_base_curses_include_broodling_and_infested_terran();
    audit_hallucinations_keep_original_stats();audit_hallucination_birth_is_unmodified();audit_damage_subjects_are_independent();audit_death_count_needs_lethal_damage_once();
    audit_mission_unit_bomb_exclusion_retains_identity();
}
}
