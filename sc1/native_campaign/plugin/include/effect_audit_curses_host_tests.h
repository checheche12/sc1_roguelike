// Regression expectations for production curse callbacks. No game process is used.
// Include after native_host_tests.h; the standalone audit runner renames its main.
#pragma once
namespace host_test {
namespace curse_audit {
inline bw::Bullet shot{};
inline bw::Bullet* __cdecl bullet(U32 weapon,int,int,U32 player,U32,bw::Unit* spawner){
    shot={};shot.weapon_id=static_cast<U8>(weapon);shot.player=static_cast<U8>(player);
    shot.parent=(spawner->unit_id==4 || spawner->unit_id==6 || spawner->unit_id==31) ? spawner->subunit : spawner;return &shot;
}
inline void __cdecl blocked(bw::Unit*,std::int32_t,bw::Unit*,U32,U32){}
inline void __cdecl modeled_weapon_split(bw::Unit* target,std::int32_t amount,U8,U32 divisor,U8,bw::Unit* attacker,U32 player){
    // Synthetic native armor/shield boundary; calls the actual lower hook.
    amount/=static_cast<int>(std::max(1u,divisor));
    const auto absorbed=std::min(amount,std::max(0,target->shields));target->shields-=absorbed;
    owner_damage_hook(target,amount-absorbed,attacker,player,1,fake_damage);
}
inline void __cdecl shields_then_hp(bw::Unit* target,bw::Bullet* b,U32 divisor){
    combat_effects::weapon_damage(target,static_cast<std::int32_t>(raw_value(1,14,b->weapon_id)*256),b->weapon_id,divisor,0,b->parent,b->player,modeled_weapon_split);
}
inline void modeled_native_melee(bw::Unit* source,bw::Unit* target,std::int32_t amount){
    source->order_target.unit=target;combat_effects::melee_enter(source);
    const auto weapon=static_cast<U8>(original_stat({0,17,source->unit_id}));
    combat_effects::weapon_damage(target,amount,weapon,1,0,source,source->player,modeled_weapon_split);
    combat_effects::melee_leave(source);
}
inline bw::Unit* wave(U32 id,U32 owner,int x=500,int y=500){
    auto unit=add(id,owner,x,y,static_cast<int>(owner_stat(owner,{0,8,id})));refresh_units();mark_wave_unit(unit);return unit;
}
inline void audit_zero_actual_damage_does_not_reset_charge(){
    reset();GrowthSnapshot s{};s.curse_counts[9]=1;CHECK(apply_snapshot(nullptr,s));
    game.frame_count=10;game.elapsed_seconds=1;auto enemy=add(0,6,500,500);refresh_units();auto track=track_unit(enemy);
    const auto prior=track->last_damage_frame;game.frame_count=250;game.elapsed_seconds=10;
    owner_damage_hook(enemy,1000,nullptr,1,1,blocked);
    std::printf("OBS zero_actual_hp_loss last_damage_frame=%u expected=%u\n",track->last_damage_frame,prior);
    CHECK(track->last_damage_frame==prior);
}
inline void audit_goliath_commander_bonus_follows_main(){
    reset();GrowthSnapshot s{};s.curse_counts[13]=1;CHECK(apply_snapshot(nullptr,s));game.frame_count=200;
    auto main=add(3,6,500,500),turret=add(4,6,500,500);main->subunit=turret;turret->subunit=main;refresh_units();
    track_unit(main)->command_until=400;turret->ground_cooldown=22;
    auto b=owner_bullet_create_hook(7,500,500,6,0,turret,bullet);
    std::printf("OBS goliath_commander projectile_bonus=%u expected=25\n",g.bullet_bonuses[b]);
    CHECK(g.bullet_bonuses[b]==25);
}
inline void audit_turret_track_survives_root_unit_enumeration(){
    reset();GrowthSnapshot s{};s.curse_counts[9]=1;CHECK(apply_snapshot(nullptr,s));game.frame_count=20;
    auto main=add(3,6,500,500),turret=add(4,6,500,500);main->subunit=turret;turret->subunit=main;
    // Native subunits are reached recursively from main, not independent roots.
    active=main;main->flingy.next=nullptr;refresh_units();auto old=track_unit(turret);old->last_attack_frame=17;
    apply_unit_motion();auto current=existing_track(turret);
    std::printf("OBS goliath_turret_track retained=%u expected=1\n",current!=nullptr);
    CHECK(current && current->last_attack_frame==17);
}
inline void audit_barrier_reduces_shield_damage(){
    reset();GrowthSnapshot s{};s.curse_counts[8]=1;CHECK(apply_snapshot(nullptr,s));
    auto target=wave(65,6);target->shields=20*256;auto source=add(0,1,100,100);refresh_units();
    auto b=owner_bullet_create_hook(0,100,100,1,0,source,bullet);const auto before=target->shields;
    owner_hit_hook(target,b,1,shields_then_hp);const auto actual=before-target->shields;const auto expected=(6*256*3+3)/4;
    std::printf("OBS barrier_shield_damage actual=%d expected=%d\n",actual,expected);
    CHECK(actual==expected);
}
inline void audit_melee_elite_uses_damage_entry(){
    reset();GrowthSnapshot s{};s.curse_counts[7]=1;CHECK(apply_snapshot(nullptr,s));auto source=wave(37,6);auto target=add(0,1,100,100,10000);refresh_units();
    const auto before=target->flingy.hitpoints;modeled_native_melee(source,target,5*256);
    const auto actual=before-target->flingy.hitpoints;std::printf("OBS melee_elite_damage actual=%d expected=%d\n",actual,6*256);
    CHECK(actual==6*256);
}
inline void audit_melee_lifesteal_uses_actual_hp_loss(){
    reset();GrowthSnapshot s{};s.curse_counts[11]=1;CHECK(apply_snapshot(nullptr,s));auto source=add(37,6,500,500,1000);auto target=add(0,1,100,100,10000);refresh_units();track_unit(source);
    const auto before=source->flingy.hitpoints;modeled_native_melee(source,target,1000);
    std::printf("OBS melee_lifesteal actual=%d expected=100\n",source->flingy.hitpoints-before);CHECK(source->flingy.hitpoints==before+100);
}
inline void audit_melee_charge_consumes_on_real_attack(){
    reset();GrowthSnapshot s{};s.curse_counts[9]=1;CHECK(apply_snapshot(nullptr,s));game.frame_count=1;
    auto source=add(37,6,500,500,1000);auto target=add(0,1,100,100,10000);refresh_units();track_unit(source);game.frame_count=200;
    const auto before=target->flingy.hitpoints;modeled_native_melee(source,target,5*256);
    std::printf("OBS melee_charge_damage actual=%d expected=%d\n",before-target->flingy.hitpoints,6*256);CHECK(target->flingy.hitpoints==before-6*256);
}
inline void audit_spell_damage_must_not_become_normal(){
    reset();GrowthSnapshot s{};s.curse_counts[7]=s.curse_counts[9]=s.curse_counts[11]=1;CHECK(apply_snapshot(nullptr,s));
    auto source=wave(37,6);source->flingy.hitpoints=1000;auto target=add(0,1,100,100,10000);refresh_units();
    bw::Bullet spell{};spell.player=6;spell.weapon_id=84;spell.parent=source;CHECK(!ordinary_weapon(84));
    const auto hp=target->flingy.hitpoints;owner_hit_hook(target,&spell,1,fake_hit);CHECK(source->flingy.hitpoints==1000);
    CHECK(target->flingy.hitpoints==hp-static_cast<int>(original_stat({1,14,84})*256));
}
inline void audit_pair_once_and_no_revive(){
    reset();GrowthSnapshot s{};s.curse_counts[14]=3;CHECK(apply_snapshot(nullptr,s));game.frame_count=100;g.current_wave_id=71;
    auto a=wave(0,6),b=wave(0,6,520,500);CHECK(existing_track(a)->pair_index==static_cast<U32>(b-g.units));
    b->flingy.hitpoints=1000;owner_kill_hook(a,kill);CHECK(existing_track(b)->pair_due==148);
    game.frame_count=147;update_diversity();CHECK(b->flingy.hitpoints==1000);
    game.frame_count=148;update_diversity();const auto healed=b->flingy.hitpoints;CHECK(healed==1000+static_cast<int>(effective_max_hp(b)*35/100));
    game.frame_count=196;update_diversity();CHECK(b->flingy.hitpoints==healed);
    reset();CHECK(apply_snapshot(nullptr,s));game.frame_count=100;g.current_wave_id=72;a=wave(0,6);b=wave(0,6,520,500);
    owner_kill_hook(a,kill);owner_kill_hook(b,kill);game.frame_count=148;update_diversity();CHECK(b->flingy.hitpoints==0);
}
inline void audit_give_and_transform_role_identity(){
    reset();GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[7]=s.curse_counts[8]=1;CHECK(apply_snapshot(nullptr,s));
    auto tank=wave(5,6);CHECK(existing_track(tank)->elite && existing_track(tank)->barrier);
    owner_transform_hook(tank,30,fake_transform);CHECK(existing_track(tank)->spawned && existing_track(tank)->elite && existing_track(tank)->barrier);
    owner_give_hook(tank,1,fake_give);CHECK(!existing_track(tank));CHECK(!regular_enemy(tank));
}
inline void __cdecl kill_before_hp_change(bw::Unit* u,std::int32_t,bw::Unit*,U32 player,U32){u->last_attacking_player=static_cast<U8>(player);owner_kill_hook(u,kill);}
inline void __cdecl hp_change_before_kill(bw::Unit* u,std::int32_t,bw::Unit*,U32 player,U32){u->last_attacking_player=static_cast<U8>(player);u->flingy.hitpoints=0;owner_kill_hook(u,kill);}
inline void audit_actual_lethal_damage_preserves_death_roles(){
    for(auto original:{kill_before_hp_change,hp_change_before_kill}){
        reset();GrowthSnapshot s{};s.curse_counts[10]=s.curse_counts[13]=s.curse_counts[14]=1;CHECK(apply_snapshot(nullptr,s));
        game.frame_count=1;g.current_wave_id=81;auto first=wave(0,6),second=wave(0,6,520,500);game.frame_count=250;
        auto human=add(0,1,500,500);refresh_units();owner_damage_hook(first,first->flingy.hitpoints,human,1,1,original);
        CHECK(first->flingy.hitpoints==0);CHECK(g.bombs.size()==1);CHECK(existing_track(second)->command_until==442);CHECK(existing_track(second)->pair_due==298);
    }
}
inline void audit_shield_only_hit_records_actual_damage(){
    reset();GrowthSnapshot s{};s.curse_counts[9]=1;CHECK(apply_snapshot(nullptr,s));game.frame_count=10;
    auto enemy=add(65,6,500,500,1000);enemy->shields=20*256;auto source=add(0,1,100,100);refresh_units();track_unit(enemy);game.frame_count=250;
    auto b=owner_bullet_create_hook(0,100,100,1,0,source,bullet);owner_hit_hook(enemy,b,1,shields_then_hp);
    CHECK(enemy->flingy.hitpoints==1000);CHECK(enemy->shields==14*256);CHECK(existing_track(enemy)->last_damage_frame==250);
}
inline void audit_turret_charge_and_elite_projectile_identity(){
    reset();GrowthSnapshot s{};s.curse_counts[7]=s.curse_counts[9]=1;CHECK(apply_snapshot(nullptr,s));game.frame_count=1;
    auto main=wave(3,6);auto turret=add(4,6,500,500);main->subunit=turret;turret->subunit=main;refresh_units();turret->ground_cooldown=22;game.frame_count=200;
    auto b=owner_bullet_create_hook(7,500,500,6,0,turret,bullet);CHECK(g.bullet_elites[b]);CHECK(g.bullet_bonuses[b]==20);CHECK(existing_track(main)->last_attack_frame==200);
    CHECK(!existing_track(turret)->elite);game.frame_count=201;owner_bullet_create_hook(7,500,500,6,0,turret,bullet);CHECK(g.bullet_bonuses[b]==20);
}
inline void audit_regular_broodling_and_infested_hp_speed(){
    for(U32 id:{40u,50u}){
        reset();GrowthSnapshot s{};s.curse_counts[2]=s.curse_counts[3]=1;auto unit=add(id,6,500,500,static_cast<int>(raw_value(0,8,id)));const auto hp=unit->flingy.hitpoints;unit->flingy.top_speed=1000;CHECK(apply_snapshot(nullptr,s));apply_unit_motion();
        std::printf("OBS regular_unit_%u hp=%d expected=%d speed=%u expected=1075\n",id,unit->flingy.hitpoints,(hp*11+5)/10,unit->flingy.top_speed);
        CHECK(unit->flingy.hitpoints==(hp*11+5)/10);CHECK(unit->flingy.top_speed==1075);
    }
}
inline void __cdecl hit_with_attacker(bw::Unit* u,bw::Bullet* b,U32){
    owner_damage_hook(u,static_cast<int>(raw_value(1,14,b->weapon_id)*256),b->parent,b->player,1,fake_damage);
}
inline bw::Unit* missile_target=nullptr;
inline HitFn missile_hit=nullptr;
inline void __cdecl missile_damage(bw::Bullet* b){missile_hit(missile_target,b,1);}
inline void invoke_projectile_hit(bw::Unit* target,bw::Bullet* b,HitFn callback,bool missile){
    if(missile){missile_target=target;missile_hit=callback;owner_missile_hook(b,missile_damage);}
    else owner_hit_hook(target,b,1,callback);
}
inline void audit_projectile_reused_parent_does_not_heal_replacement(){
    for(auto callback:{fake_hit,hit_with_attacker})for(bool missile:{false,true})for(bool launch_elite:{false,true}){
        reset();GrowthSnapshot s{};s.curse_counts[11]=1;CHECK(apply_snapshot(nullptr,s));
        auto enemy=add(0,6,500,500,1000);auto target=add(0,1,100,100,10000);refresh_units();track_unit(enemy)->elite=launch_elite;
        auto b=owner_bullet_create_hook(0,500,500,6,0,enemy,bullet);
        const int damage=launch_elite ? (6*256*6+4)/5 : 6*256;
        // Positive control: the launch owner can heal from either engine entry.
        invoke_projectile_hit(target,b,callback,missile);CHECK(enemy->flingy.hitpoints==1000+damage/10);
        ++enemy->minor_unique_index;enemy->flingy.hitpoints=1000;track_unit(enemy)->elite=!launch_elite;
        const auto before=target->flingy.hitpoints;invoke_projectile_hit(target,b,callback,missile);
        std::printf("OBS reused_parent_heal=%d expected=0 missile=%u attacker=%u launch_elite=%u\n",enemy->flingy.hitpoints-1000,missile,callback==hit_with_attacker,launch_elite);
        CHECK(enemy->flingy.hitpoints==1000);CHECK(before-target->flingy.hitpoints==damage);
    }
}
inline void audit_projectile_given_parent_does_not_heal_new_owner(){
    for(auto callback:{fake_hit,hit_with_attacker})for(bool missile:{false,true}){
        reset();GrowthSnapshot s{};s.curse_counts[11]=1;CHECK(apply_snapshot(nullptr,s));
        auto enemy=add(0,6,500,500,1000);auto target=add(0,1,100,100,10000);refresh_units();track_unit(enemy);
        auto b=owner_bullet_create_hook(0,500,500,6,0,enemy,bullet);owner_give_hook(enemy,4,fake_give);const auto before=enemy->flingy.hitpoints;
        invoke_projectile_hit(target,b,callback,missile);std::printf("OBS changed_owner_heal=%d expected=0 missile=%u attacker=%u\n",enemy->flingy.hitpoints-before,missile,callback==hit_with_attacker);CHECK(enemy->flingy.hitpoints==before);
    }
}
struct Case {const char* name;void(*fn)();bool unresolved=false;};
inline const Case cases[]={
 {"projectile_reused_parent",audit_projectile_reused_parent_does_not_heal_replacement},
 {"projectile_changed_owner",audit_projectile_given_parent_does_not_heal_new_owner},
 {"actual_lethal_roles",audit_actual_lethal_damage_preserves_death_roles},
 {"shield_damage_record",audit_shield_only_hit_records_actual_damage},
 {"turret_charge_elite",audit_turret_charge_and_elite_projectile_identity},
 {"broodling_infested",audit_regular_broodling_and_infested_hp_speed},
 {"zero_actual_damage",audit_zero_actual_damage_does_not_reset_charge},
 {"goliath_commander",audit_goliath_commander_bonus_follows_main},
 {"turret_track",audit_turret_track_survives_root_unit_enumeration},
 {"barrier_shields",audit_barrier_reduces_shield_damage},
 {"melee_elite",audit_melee_elite_uses_damage_entry},
 {"melee_lifesteal",audit_melee_lifesteal_uses_actual_hp_loss},
 {"melee_charge",audit_melee_charge_consumes_on_real_attack},
 {"spell_exclusion",audit_spell_damage_must_not_become_normal},
 {"pair_once_no_revive",audit_pair_once_and_no_revive},
 {"give_transform_identity",audit_give_and_transform_role_identity},
};
}
// All sixteen expectations now use the production upstream/prefix adapters.
// Host success is distinct from actual engine callback execution.
inline void run_effect_audit_curses_groups(){for(const auto& test:curse_audit::cases)test.fn();}
// Historical pre-fix failures are preserved in the audit snapshot artifacts.
inline void run_effect_audit_curses_regression_groups(){for(const auto& test:curse_audit::cases)if(!test.unresolved)test.fn();}
}
