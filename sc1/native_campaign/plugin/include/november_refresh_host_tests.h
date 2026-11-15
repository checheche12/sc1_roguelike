namespace host_test {
inline constexpr std::size_t november_refresh_group_count=8;
inline void __cdecl november_native_try_mine(bw::Unit* u){
    auto p=u->order_target.unit;if(!p||p->unit_specific2.bytes[3]||!rework_economy_v5::amount(p))return;
    p->unit_specific2.bytes[3]=1;u->unit_specific.bytes[26]=1;
    std::memcpy(u->unit_specific2.bytes,&p,sizeof(p));u->order=87;
}
inline void __cdecl november_native_finish_mine(bw::Unit* u){
    auto p=rework_economy_v5::harvest_target(u);CHECK(p);
    const auto n=std::min(8u,rework_economy_v5::amount(p));rework_economy_v5::amount(p,rework_economy_v5::amount(p)-n);
    u->unit_specific.bytes[27]=U8(n);u->carried_powerup_flags=n?2:0;u->unit_specific.bytes[26]=0;
    std::memset(u->unit_specific2.bytes,0,sizeof(void*));p->unit_specific2.bytes[3]=0;u->order=90;
}
inline void november_two_mineral_slots_preserve_native_cargo_and_owner_limits(){
    for(U32 id:{7u,41u,64u}){
        reset();auto p=economy_add(176,11,550,550);rework_economy_v5::amount(p,100);
        CHECK(apply_snapshot(nullptr,economy_snapshot({2})));CHECK(rework_economy_v5::amount(p)==300);
        auto a=economy_add(id),b=economy_add(id),c=economy_add(id),enemy=economy_add(id,6);
        for(auto u:{a,b,c,enemy}){u->order=86;u->order_target.unit=p;}
        owner_unit_hook(a,november_native_try_mine);owner_unit_hook(b,november_native_try_mine);
        CHECK(a->order==87&&b->order==87&&p->unit_specific2.bytes[3]==1);
        owner_unit_hook(c,november_native_try_mine);owner_unit_hook(enemy,november_native_try_mine);
        CHECK(c->order==86&&enemy->order==86);
        owner_unit_hook(a,november_native_finish_mine);CHECK(p->unit_specific2.bytes[3]==1&&b->order==87);
        owner_unit_hook(enemy,november_native_try_mine);CHECK(enemy->order==86);
        owner_unit_hook(c,november_native_try_mine);CHECK(c->order==87);
        owner_unit_hook(a,economy_return_original);CHECK(game.minerals[1]==8&&rework_economy_v5::amount(p)==292);
        owner_unit_hook(b,november_native_finish_mine);owner_unit_hook(c,november_native_finish_mine);
        CHECK(p->unit_specific2.bytes[3]==0&&rework_economy_v5::amount(p)==276);
        owner_unit_hook(enemy,november_native_try_mine);CHECK(enemy->order==87);
        a->order=86;owner_unit_hook(a,november_native_try_mine);CHECK(a->order==86); // No extra slot beside an enemy.
    }
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({2})));auto gas=economy_add(110);gas->unit_specific2.bytes[3]=1;rework_economy_v5::amount(gas,100);
    auto worker=economy_add(7);worker->order=82;worker->order_target.unit=gas;
    {rework_economy_v5::UnitScope scope(worker);CHECK(gas->unit_specific2.bytes[3]==1);}
}
inline void november_new_expansions_grant_once_after_completion_and_retry(){
    for(U32 id:{106u,131u,154u}){
        reset();auto map=*g.mission;map.width=map.height=256;g.mission=&map;game.map_width_tiles=game.map_height_tiles=256;
        auto initial=economy_add(id);initial->flags=1;CHECK(apply_snapshot(nullptr,economy_snapshot({7})));g.create=economy_create_supply;
        rework_economy_v5::expansion_bonus({initial});CHECK(count==1);
        auto base=economy_add(id,1,1500,1500);base->flags=0;
        rework_economy_v5::created(base);rework_economy_v5::expansion_bonus({base});CHECK(count==2);
        base->flags=1;fail_spawn=true;rework_economy_v5::expansion_bonus({base});CHECK(count==2);
        fail_spawn=false;game.frame_count=24;rework_economy_v5::expansion_bonus({base});CHECK(count==6);
        const U32 worker=id==106?7u:id==154?64u:41u;for(U32 n=2;n<6;++n)CHECK(units[n].unit_id==worker);
        for(U32 n=0;n<5;++n){game.frame_count+=24;rework_economy_v5::expansion_bonus({base});}CHECK(count==6);
        for(U32 n=0;n<3;++n){auto extra=economy_add(id,1,2500+int(n)*800,1500);extra->flags=0;rework_economy_v5::created(extra);extra->flags=1;game.frame_count+=24;rework_economy_v5::expansion_bonus({extra});}
        if(count!=17||rework_economy_v5::expansion_grants!=3)throw std::runtime_error("Expansion fixture id="+std::to_string(id)+" units="+std::to_string(count)+" grants="+std::to_string(rework_economy_v5::expansion_grants));
        CHECK(count==17&&rework_economy_v5::expansion_grants==3);
        g.mission=&campaign_config::kMissions[0];
    }
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({7})));auto hatch=economy_add(131);hatch->flags=1;
    hatch->unit_id=132;rework_economy_v5::transformed(hatch,131);rework_economy_v5::expansion_bonus({hatch});CHECK(count==1);
    auto drone=economy_add(41);drone->unit_id=131;drone->flags=0;rework_economy_v5::transformed(drone,41);
    CHECK(rework_economy_v5::state(drone)->expansion_pending);drone->unit_id=41;rework_economy_v5::transformed(drone,131);
    CHECK(!rework_economy_v5::state(drone)->expansion_pending);
}
inline void november_resource_returns_stack_and_fail_closed(){
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({0,1,2})));
    auto worker=economy_add(7),enemy=economy_add(7,6);
    for(auto u:{worker,enemy})for(U32 flags:{1u,2u}){
        u->order=flags==1?84:90;u->unit_specific.bytes[27]=8;u->carried_powerup_flags=U8(flags);
        owner_unit_hook(u,economy_return_original);
    }
    CHECK(game.minerals[1]==10&&game.gas[1]==10);
    CHECK(game.minerals[6]==8&&game.gas[6]==8);
    worker->order=90;worker->unit_specific.bytes[27]=8;worker->carried_powerup_flags=2;
    {rework_economy_v5::UnitScope aborted(worker);worker->unit_specific.bytes[27]=0;worker->carried_powerup_flags=0;}
    CHECK(game.minerals[1]==10);
}
inline void november_wasteland_thresholds_preserve_all_three_conditions(){
    for(U32 marines:{9u,10u,11u,50u})for(U32 barracks:{0u,1u})for(U32 raynor:{0u,1u}){
        reset();make_chk();init_units(original);
        game.completed_units_count[0][kOwner]=marines;
        game.completed_units_count[111][kOwner]=barracks;
        game.completed_units_count[19][kOwner]=raynor;
        update_original_goal();CHECK(counter(kGoalCounter)==(marines>=10&&barracks&&raynor));
        CHECK(!counter(kReadyCounter)&&!counter(kAckCounter));
    }
}
inline void november_fire_visual_has_bounded_cadence_and_lifetime(){
    reset();make_chk();init_units(original);using namespace rework_combat_v5;
    Persist fire{};fire.kind=52;fire.x=500;fire.y=500;fire.owner=1;fire.until=120;
    U32 budget=64;const auto before=ground_pulses;
    for(U32 frame=0;frame<144;++frame){budget=64;residual_fire_visual(fire,frame,budget);residual_fire_visual(fire,frame,budget);}
    CHECK(ground_pulses-before==10);
    fire.visual_due=0;fire.until=100;budget=0;residual_fire_visual(fire,1,budget);CHECK(ground_pulses-before==10);
    budget=64;fire.x=-1;residual_fire_visual(fire,1,budget);CHECK(budget==64);
    fire.x=500;g.lone_sprite=nullptr;residual_fire_visual(fire,1,budget);CHECK(budget==64);
}
inline void november_fire_direction_matches_attack_and_survives_turning(){
    using namespace rework_combat_v5;
    bw::SpriteScr sprite{};sprite.sprite_id=378;
    movement_effects::Image image{};image.image_id=421;image.parent=&sprite;
    sprite.main_image=&image;bw::LoneSprite lone{};lone.sprite=&sprite;
    const U8 expected[]={0,4,8,12,16,12,8,4};
    for(U32 direction=0;direction<8;++direction){
        image.flags=8;image.frameset=51;image.frame=51;
        orient_flame_visual(&lone,U8(direction*32));
        CHECK(image.direction==expected[direction]&&image.frame==51+expected[direction]);
        CHECK(bool(image.flags&2u)==(direction>4)&&bool(image.flags&1u));
    }
    orient_flame_visual(&lone,255);CHECK(image.direction==0&&image.frame==51);
    orient_flame_visual(&lone,0);CHECK(!(image.flags&2u));
    using namespace rework_fixture;qa9_fixture::begin({52});
    auto source=unit(32,1,100,100),target=unit(37,6,150,100);source->flingy.facing_direction=64;
    ordinary_hit(source,target,256,25,false);CHECK(persistent.size()==1&&persistent[0].visual_direction==64);
    source->flingy.facing_direction=192;CHECK(persistent[0].visual_direction==64);
    ordinary_hit(source,target,256,25,false);CHECK(persistent.size()==1&&persistent[0].visual_direction==192);
    qa9_fixture::end();
}
inline void november_fan_visual_is_bounded_and_does_not_generate_damage(){
    using namespace rework_combat_v5;using namespace rework_fixture;qa9_fixture::begin({52,185});
    auto source=unit(32,1,100,100),target=unit(37,6,150,100);source->flingy.facing_direction=64;
    const auto before=ground_pulses;flame_visual_frame=~0u;
    ordinary_hit(source,target,256,25,false);CHECK(ground_pulses-before==4);
    ordinary_hit(source,target,256,25,false);CHECK(ground_pulses-before==4);
    CHECK(persistent.size()==1&&persistent[0].visual_direction==64);
    auto state=rework_combat_v5::state(source);game.frame_count+=12;
    auto& budget=flame_budget(game.frame_count);budget=3;fan_flame_visual(source,*state,game.frame_count);CHECK(ground_pulses-before==4&&budget==3);
    budget=4;fan_flame_visual(source,*state,game.frame_count);CHECK(ground_pulses-before==8&&budget==0);
    CHECK(target->flingy.hitpoints>0);qa9_fixture::end();
}
inline void november_residual_fan_covers_cone_and_stays_at_firing_origin(){
    using namespace rework_combat_v5;using namespace rework_fixture;qa9_fixture::begin({52,185});
    auto source=unit(32,1,100,100),target=unit(37,6,164,100),edge=unit(37,6,148,155),back=unit(37,6,40,100),side=unit(37,6,100,190),outside=unit(37,6,197,100);
    ordinary_hit(source,target,256,25,false);CHECK(persistent.size()==1);auto& fire=persistent[0];
    CHECK(fire.fire_cone&&fire.x==100&&fire.y==100&&fire.fire_aim_x==164&&fire.fire_aim_y==100);
    CHECK(residual_fire_contains(fire,target)&&residual_fire_contains(fire,edge));
    CHECK(!residual_fire_contains(fire,back)&&!residual_fire_contains(fire,side)&&!residual_fire_contains(fire,outside));
    source->flingy.position={500,500};source->flingy.facing_direction=192;
    CHECK(residual_fire_contains(fire,edge)&&fire.x==100&&fire.y==100);
    fire.until=120;fire.visual_due=0;const auto before=ground_pulses;U32 budget=4;
    residual_fire_visual(fire,1,budget);CHECK(ground_pulses==before&&budget==4);
    budget=64;residual_fire_visual(fire,1,budget);CHECK(ground_pulses-before==5&&budget==59);
    residual_fire_visual(fire,2,budget);CHECK(ground_pulses-before==5);
    fire.fire_cone=false;fire.x=164;fire.y=100;CHECK(!residual_fire_contains(fire,edge));qa9_fixture::end();
}
inline void run_november_refresh_groups(){
    november_two_mineral_slots_preserve_native_cargo_and_owner_limits();november_new_expansions_grant_once_after_completion_and_retry();
    november_resource_returns_stack_and_fail_closed();
    november_wasteland_thresholds_preserve_all_three_conditions();november_fire_visual_has_bounded_cadence_and_lifetime();november_fire_direction_matches_attack_and_survives_turning();november_fan_visual_is_bounded_and_does_not_generate_damage();november_residual_fan_covers_cone_and_stays_at_firing_origin();
}
}
