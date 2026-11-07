#pragma once
namespace host_test {
inline constexpr std::size_t omni_battleship_group_count=10;
namespace omni_fixture {
inline bw::Bullet* __cdecl without_yamato(U32 w,int x,int y,U32 owner,U32 direction,bw::Unit* source){
    return w==30?nullptr:rework_fixture::hooked(w,x,y,owner,direction,source);
}
inline bw::Bullet* __cdecl lethal_instant(U32 w,int x,int y,U32 owner,U32 direction,bw::Unit* source){
    auto b=multi_fixture::raw(w,x,y,owner,direction,source);
    observe_instant_launch(b);b->target.unit->flingy.hitpoints=0;return b;
}
inline void freeze_batteries(bw::Unit* ship){
    auto s=rework_combat_v5::state(ship);s->next_ground=s->next_air=10000;
}
inline void four(bw::Unit* ship,bw::Unit* target,bool hold_yamato=false){
    if(hold_yamato)multi_target::create_bullet=without_yamato;
    for(U32 i=0;i<4;++i){game.frame_count=100+i;rework_fixture::bullet(ship,target,rework_combat_v5::weapon(ship,false));}
    multi_target::create_bullet=rework_fixture::hooked;
    freeze_batteries(ship);
}
}
inline void omni_automatic_batteries_count_for_all_ship_variants(){
    using namespace rework_fixture;
    for(U32 id:{12u,27u,28u,29u,102u})for(U32 order:{3u,6u,107u}){
        qa9_fixture::begin({65});auto ship=unit(id,1,100,100,true);unit(37,6,150,100);ship->order=U8(order);ship->energy=0;
        const auto w=rework_combat_v5::weapon(ship,false);
        for(U32 i=0;i<4;++i){pulse(100+i*40);CHECK(multi_fixture::shot_count(w)==i+1);CHECK(multi_fixture::shot_count(30)==(i==3?1u:0u));}
        CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==4);
        CHECK(multi_fixture::shots.back().weapon==30&&multi_fixture::shots.back().frame==220);
        pulse(222);CHECK(multi_fixture::shot_count(30)==1&&ship->energy==0);
        pulse(223);CHECK(multi_fixture::shot_count(30)==1);qa9_fixture::end();
    }
}
inline void omni_both_layers_count_once_even_with_interleaved_callbacks(){
    using namespace rework_fixture;qa9_fixture::begin({65});
    auto ship=unit(12,1,100,100,true),ground=unit(37,6,150,100);unit(43,6,160,100,true);ship->order=10;
    for(U32 cycle=0;cycle<2;++cycle){
        game.frame_count=100+cycle*40;auto primary=bullet(ship,ground,19);pulse(game.frame_count);
        CHECK(multi_fixture::shot_count(19)==cycle+1&&multi_fixture::shot_count(20)==cycle+1);
        CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==(cycle+1)*2);
        rework_combat_v5::launched(19,ship,primary);
        CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==(cycle+1)*2);
    }
    CHECK(rework_combat_v5::pending_shots.empty()&&multi_fixture::shot_count(30)==1);
    CHECK(multi_fixture::shots.back().weapon==30&&multi_fixture::shots.back().frame==140);
    pulse(142);CHECK(multi_fixture::shot_count(30)==1);qa9_fixture::end();
}
inline void omni_moving_air_control_keeps_four_shot_interval(){
    using namespace rework_fixture;qa9_fixture::begin({47,65});auto ship=unit(12,1,100,100,true);unit(37,6,150,100);ship->order=6;
    for(U32 i=0;i<8;++i){ship->ground_cooldown=ship->air_cooldown=0;pulse(100+i*40);pulse(102+i*40);}
    CHECK(multi_fixture::shot_count(19)==8&&multi_fixture::shot_count(30)==2);
    CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==8);qa9_fixture::end();
}
inline void omni_spread_and_echo_do_not_count_as_new_attacks(){
    using namespace rework_fixture;
    for(bool scaled:{false,true}){
        qa9_fixture::begin({18,57,65});talent_power::enabled=scaled;
        auto ship=unit(12,1,100,100,true),target=unit(37,6,150,100);unit(37,6,170,100);unit(37,6,180,100);ship->order=10;
        omni_fixture::four(ship,target);pulse(105);pulse(106);
        // Legacy57 fans out; the current focus version replaces that effect.
        CHECK(multi_fixture::shot_count(19)==(scaled?8u:16u)&&multi_fixture::shot_count(30)==1);
        CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==4&&rework_combat_v5::pending_shots.empty());qa9_fixture::end();
    }
}
inline void omni_earned_yamato_retargets_only_attackable_nearby_enemies(){
    using namespace rework_fixture;qa9_fixture::begin({65});
    auto ship=unit(12,1,100,100,true),target=unit(37,6,150,100);ship->order=10;
    auto ally=unit(37,1,110,100),fog=unit(37,6,120,100),undetected=unit(37,6,125,100),protected_unit=unit(37,6,130,100);
    auto replacement=unit(43,6,160,100,true);unit(37,6,1000,100);
    static_cast<bw::SpriteScr*>(fog->flingy.sprite)->visibility_mask=0;undetected->detection_status=0;protected_unit->flags|=0x4000000u;
    omni_fixture::four(ship,target,true);target->flingy.hitpoints=0;pulse(111);
    CHECK(multi_fixture::shot_count(30)==1&&multi_fixture::shots.back().target==replacement);
    CHECK(ally->flingy.hitpoints==256000&&rework_combat_v5::pending_shots.empty());qa9_fixture::end();
}
inline void omni_earned_yamato_survives_no_target_disable_and_pool_failure(){
    using namespace rework_fixture;qa9_fixture::begin({65});auto ship=unit(12,1,100,100,true),target=unit(37,6,150,100);ship->order=10;
    omni_fixture::four(ship,target,true);target->flingy.hitpoints=0;pulse(111);pulse(119);
    CHECK(multi_fixture::shot_count(30)==0&&rework_combat_v5::pending_shots.size()==1);
    auto replacement=unit(37,6,160,100);ship->lockdown_timer=3;pulse(127);
    CHECK(multi_fixture::shot_count(30)==0&&rework_combat_v5::pending_shots.size()==1);
    ship->lockdown_timer=0;multi_fixture::fail_all=true;pulse(135);
    CHECK(multi_fixture::shot_count(30)==0&&rework_combat_v5::pending_shots.size()==1);
    multi_fixture::fail_all=false;pulse(143);pulse(151);
    CHECK(multi_fixture::shot_count(30)==1&&multi_fixture::shots.back().target==replacement&&rework_combat_v5::pending_shots.empty());qa9_fixture::end();
}
inline void omni_pending_yamato_cannot_survive_source_or_talent_loss(){
    using namespace rework_fixture;
    for(U32 mode=0;mode<4;++mode){qa9_fixture::begin({65});auto ship=unit(12,1,100,100,true),target=unit(37,6,150,100);ship->order=10;
        omni_fixture::four(ship,target,true);
        if(mode==0)ship->flingy.hitpoints=0;else if(mode==1)++ship->minor_unique_index;else if(mode==2)ship->player=6;else ranks[65]=0;
        pulse(111);CHECK(multi_fixture::shot_count(30)==0&&rework_combat_v5::pending_shots.empty());qa9_fixture::end();
    }
}
inline void omni_retargeted_free_triple_yamato_preserves_damage_and_energy(){
    using namespace rework_fixture;qa9_fixture::begin({64,65});auto ship=unit(12,1,100,100,true),target=unit(37,6,150,100);
    auto replacement=unit(37,6,170,100);replacement->flingy.hitpoints=10000*256;ship->order=10;ship->energy=0;
    omni_fixture::four(ship,target,true);target->flingy.hitpoints=0;pulse(111);
    CHECK(multi_fixture::shot_count(30)==1);auto root=&multi_fixture::bullets[multi_fixture::next_bullet-1];
    CHECK(root->weapon_id==30&&root->target.unit==replacement);yamato_targets.clear();
    {rework_combat_v5::MissileScope hit(root,qa26_yamato_dispatch);qa26_yamato_dispatch(root);}
    CHECK(yamato_targets.size()==3&&replacement->flingy.hitpoints==(10000-1560)*256);
    CHECK(ship->energy==0&&rework_combat_v5::state(ship)->bc_primary_attacks==4);qa9_fixture::end();
}
inline void omni_fourth_and_eighth_keep_normal_shot_and_launch_yamato_same_frame(){
    using namespace rework_fixture;
    for(U32 id:{12u,27u,28u,29u,102u})for(bool triple:{false,true}){
        qa9_fixture::begin({65});if(triple)ranks[64]=1;
        auto ship=unit(id,1,100,100,true),target=unit(37,6,150,100);ship->order=10;ship->energy=0;
        const auto w=rework_combat_v5::weapon(ship,false);
        for(U32 i=1;i<=8;++i){
            game.frame_count=100+i*40;const auto count_before=multi_fixture::shots.size();
            auto normal=bullet(ship,target,w);CHECK(normal&&normal->weapon_id==w);
            CHECK(multi_fixture::shot_count(w)==i&&multi_fixture::shot_count(30)==i/4);
            CHECK(multi_fixture::shots.size()==count_before+(i%4==0?2u:1u));
            if(i%4==0){
                const auto& pair=multi_fixture::shots;CHECK(pair[pair.size()-2].weapon==w&&pair.back().weapon==30);
                CHECK(pair[pair.size()-2].frame==pair.back().frame&&pair.back().frame==game.frame_count);
                auto root=&multi_fixture::bullets[multi_fixture::next_bullet-1];
                CHECK(rework_combat_v5::projectiles.at(root).percent==(triple?200u:100u));
            }
            CHECK(ship->energy==0&&ship->order==10&&ship->order_target.unit==target);
            CHECK(rework_combat_v5::pending_shots.empty());
        }
        CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==8);qa9_fixture::end();
    }
}
inline void omni_lethal_fourth_normal_retargets_after_native_create_returns(){
    using namespace rework_fixture;qa9_fixture::begin({65});
    auto ship=unit(12,1,100,100,true),target=unit(37,6,150,100),replacement=unit(37,6,170,100);ship->order=10;
    for(U32 i=0;i<3;++i){game.frame_count=100+i*40;bullet(ship,target,19);}
    game.frame_count=220;multi_fixture::target(ship,target);
    auto normal=owner_bullet_create_hook(19,100,100,1,0,ship,omni_fixture::lethal_instant);
    CHECK(normal&&target->flingy.hitpoints==0&&multi_fixture::shot_count(19)==4);
    CHECK(multi_fixture::shot_count(30)==1&&multi_fixture::shots.back().frame==220&&multi_fixture::shots.back().target==replacement);
    CHECK(rework_combat_v5::state(ship)->bc_primary_attacks==4&&rework_combat_v5::pending_shots.empty());qa9_fixture::end();
}
inline void run_omni_battleship_groups(){
    omni_automatic_batteries_count_for_all_ship_variants();omni_both_layers_count_once_even_with_interleaved_callbacks();
    omni_moving_air_control_keeps_four_shot_interval();omni_spread_and_echo_do_not_count_as_new_attacks();
    omni_earned_yamato_retargets_only_attackable_nearby_enemies();omni_earned_yamato_survives_no_target_disable_and_pool_failure();
    omni_pending_yamato_cannot_survive_source_or_talent_loss();omni_retargeted_free_triple_yamato_preserves_damage_and_energy();
    omni_fourth_and_eighth_keep_normal_shot_and_launch_yamato_same_frame();omni_lethal_fourth_normal_retargets_after_native_create_returns();
}
}
