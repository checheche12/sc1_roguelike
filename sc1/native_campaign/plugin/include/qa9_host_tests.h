#pragma once
namespace host_test {
inline constexpr std::size_t qa9_group_count=11;
namespace qa9_fixture {
inline void begin(std::initializer_list<U32> talents){talent_power::enabled=true;rework_fixture::begin(talents);}
inline void end(){rework_fixture::finish();talent_power::enabled=false;}
inline void __cdecl damage(bw::Unit* u,std::int32_t amount,U8,U32,U8,bw::Unit*,U32){u->flingy.hitpoints-=amount;}
}
inline void qa9_irradiate_five_branches_five_generations(){
    using namespace rework_fixture;qa9_fixture::begin({61});auto vessel=unit(9,1,600,900),root=unit(37,6,1000,1000);
    std::array<std::array<bw::Unit*,5>,6> levels{};
    for(U32 generation=0;generation<6;generation++)for(U32 i=0;i<5;i++)levels[generation][i]=unit(37,6,1100+int(generation)*120,1000+int(i)*3);
    auto b=bullet(vessel,root,34);{rework_combat_v5::MissileScope scope(b);root->irradiate_timer=75;}
    CHECK(rework_combat_v5::irradiation::roots.size()==1);root->irradiate_timer=50;
    rework_combat_v5::death(root);kill(root);
    for(U32 generation=0;generation<5;generation++){
        for(auto u:levels[generation]){CHECK(u->irradiate_timer==75);const auto& node=rework_combat_v5::irradiation::nodes[std::size_t(u-g.units)];CHECK(node.active&&node.generation==generation+1);}
        auto next=levels[generation][0];next->irradiate_timer=20;rework_combat_v5::death(next);kill(next);
    }
    for(auto u:levels[5])CHECK(!u->irradiate_timer);
    auto cured=levels[0][1];cured->irradiate_timer=0;rework_combat_v5::irradiation::forget(cured);
    rework_combat_v5::death(levels[0][2]);kill(levels[0][2]);CHECK(!cured->irradiate_timer);
    qa9_fixture::end();
}
inline void qa9_irradiate_native_damage_outer_ring_and_cure(){
    using namespace rework_fixture;qa9_fixture::begin({61});auto vessel=unit(9,1,600,900),root=unit(37,6,1000,1000),ring=unit(37,6,1110,1000),distant=unit(37,6,1300,1000);
    const U32 tick=original_stat({1,14,34})*256/std::max(1u,original_stat({1,16,34}));
    const auto hp=root->flingy.hitpoints;
    combat_effects::weapon_damage(root,int(tick),34,1,0,vessel,1,qa9_fixture::damage);CHECK(root->flingy.hitpoints==hp-int(tick*2));CHECK(combat_effects::damage_player==12);
    auto b=bullet(vessel,root,34);{rework_combat_v5::MissileScope scope(b);root->irradiate_timer=75;}
    const auto ring_hp=ring->flingy.hitpoints,far_hp=distant->flingy.hitpoints;
    const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=nullptr;
    --root->irradiate_timer;pulse(108);CHECK(ring->flingy.hitpoints==ring_hp-int(tick*2));CHECK(distant->flingy.hitpoints==far_hp);
    pulse(109);CHECK(ring->flingy.hitpoints==ring_hp-int(tick*2));
    root->irradiate_timer=0;rework_combat_v5::death(root);CHECK(!ring->irradiate_timer);
    combat_effects::original_weapon_damage=saved;qa9_fixture::end();
}
inline void qa9_goliath_three_targets_infinite_fire_bundle(){
    using namespace rework_fixture;qa9_fixture::begin({56,18});auto body=unit(3,1,100,100),turret=unit(4,1,100,100);body->subunit=turret;turret->subunit=body;
    auto target=unit(43,6,150,100,true);for(U32 i=0;i<5;i++)unit(43,6,160+int(i)*10,100,true);
    bullet(turret,target,8);bullet(turret,target,8);
    const auto& shots=rework_combat_v5::pending_shots;CHECK(shots.size()==7);
    CHECK(shots[0].percent==50&&shots[0].target.p==target);
    CHECK(rework_combat_v5::focus_base(body)==0);
    pulse(101);CHECK(rework_combat_v5::pending_shots.empty());CHECK(multi_fixture::shots.size()==9);qa9_fixture::end();
}
inline void qa9_emp_hits_energyless_enemies_only(){
    using namespace rework_fixture;qa9_fixture::begin({62});install();auto vessel=unit(9,1,100,100),primary=unit(37,6,150,100),other=unit(37,6,200,100),ally=unit(37,1,150,120),distant=unit(37,6,500,500);
    const auto hp=primary->flingy.hitpoints;auto b=bullet(vessel,primary,33);{rework_combat_v5::MissileScope scope(b);}
    CHECK(primary->flingy.hitpoints==hp-200*256&&other->flingy.hitpoints==hp-200*256);CHECK(ally->flingy.hitpoints==hp&&distant->flingy.hitpoints==hp);
    qa9_fixture::end();
}
inline void qa9_all_unit_legendaries_and_native_damage(){
    using namespace rework_fixture;qa9_fixture::begin({105,106,144});
    for(U32 ordinal:{61u,62u,63u,64u,65u,66u,102u,103u,104u,105u,106u,107u,144u,145u,146u,147u,148u,149u})CHECK(talent_power::quarters(238+ordinal)==(ordinal==148?4u:16u));
    CHECK(talent_power::quarters(256)==4&&talent_power::quarters(257)==10&&talent_power::quarters(389)==4);
    auto muta=unit(43,1,100,100),target=unit(43,6,150,100,true);auto b=bullet(muta,target,48);CHECK(rework_combat_v5::projectiles.at(b).percent==100);CHECK(rework_combat_v5::pending_shots.empty()&&b->bounces_remaining==7);
    auto devourer=unit(62,1,100,200);b=bullet(devourer,target,104);CHECK(rework_combat_v5::projectiles.at(b).percent==200);auto ground=unit(37,6,150,200);b=bullet(devourer,ground,104);CHECK(rework_combat_v5::projectiles.at(b).percent==200);
    auto templar=unit(67,1,100,300);b=bullet(templar,ground,84);CHECK(rework_combat_v5::projectiles.at(b).percent==200);qa9_fixture::end();
}
inline void qa9_air_wave_requires_real_counter(){
    using namespace rework_wave_tests;begin(101);auto marine=add(0,player_owner(),500,500);marine->flags=1;CHECK(rework_waves::capabilities()&p::AntiAir);
    marine->flingy.hitpoints=0;CHECK(!(rework_waves::capabilities()&p::AntiAir));
    auto body=add(3,player_owner(),500,500),turret=add(4,player_owner(),500,500);body->flags=1;turret->flags=1;body->subunit=turret;turret->subunit=body;CHECK(rework_waves::capabilities()&p::AntiAir);
    for(U32 race=0;race<3;race++)for(U32 second:{300u,600u,900u,1800u})for(U32 ordinal=0;ordinal<4;ordinal++)for(U32 unit=0;unit<20;unit++){
        auto pick=sc1_native::wave_progression::select(race,false,second,ordinal,unit,128,nullptr,false);CHECK(pick.valid&&!sc1_native::wave_progression::air_only_unit(pick.unit_id));
        CHECK(!sc1_native::wave_progression::select(race,true,second,ordinal,unit,128,nullptr,false).valid);
    }
}
inline void qa9_enemy_detector_reacts_to_burrowed_fire(){
    using namespace rework_wave_tests;begin(201);enemy_detection::reset();const auto origin=rework_waves::choose_origin(false);CHECK(origin);
    auto lurker=add(103,player_owner(),origin->target.x,origin->target.y);lurker->flags=1u|0x10u;
    auto victim=add(38,origin->owner,origin->target.x+100,origin->target.y);victim->flags=1;
    const auto before=count;enemy_detection::step(true,false,false);CHECK(count==before);
    enemy_detection::note(victim,lurker);game.frame_count+=24;enemy_detection::step(true,false,false);CHECK(count==before+1);
    auto detector=&units[count-1];CHECK(detector->unit_id==p::detector(origin->race)&&detector->player==victim->player);CHECK(detector->detection_status==0&&lurker->detection_status==0);
    rework_waves::timeline.active_ticks+=4*24;game.frame_count+=4*24;rework_waves::release_and_orders();enemy_detection::step(true,false,false);
    CHECK(detector->order==6&&detector->order_target.x==lurker->flingy.position.x&&detector->order_target.y==lurker->flingy.position.y);
    for(U32 i=0;i<20;i++){game.frame_count+=24;enemy_detection::note(victim,lurker);enemy_detection::step(true,false,false);}CHECK(count==before+1);
    enemy_detection::reset();
}
inline void qa9_upgrade_announcements_are_separate(){
    using namespace enemy_progression_tests;begin();printed.clear();to(360);
    const auto combat=[](){return std::count(printed.begin(),printed.end(),std::string("적의 공방 업그레이드가 완료되었습니다."));};
    const auto special=[](){return std::count(printed.begin(),printed.end(),std::string("적의 특수 기술 중 일부가 강화되었습니다."));};
    CHECK(combat()==1&&special()==1);to(480);CHECK(combat()==1&&special()==2);to(600);CHECK(combat()==2&&special()==3);to(960);CHECK(combat()==3&&special()==6);
    const auto size=printed.size();to(1200);CHECK(printed.size()==size);
}
inline void qa9_yamato_returns_to_attack_after_witnessed_launch(){
    using namespace enemy_progression_tests;begin();ep::research(4,8);auto ship=caster(12);auto enemy=target(12,1940,1600,500);auto hq=add(106,player_owner(),1800,1500);hq->flags=1;
    auto v=rework_curses::identity(ship);rework_waves::auto_spell(ship,*v);CHECK(ship->order==113&&v->cast_order==113);
    game.frame_count+=120;rework_waves::resume_yamato(ship,*v);CHECK(ship->order==113); // Charging has no timeout cancellation.
    rework_waves::spell_launched(ship,30);ship->energy=50*256;ship->order_state=2;game.frame_count+=47;
    rework_waves::resume_yamato(ship,*v);CHECK(ship->order==113);++game.frame_count;rework_waves::resume_yamato(ship,*v);
    CHECK(ship->order==14&&!v->cast_order&&ship->energy==50*256);CHECK(ship->order_target.x==hq->flingy.position.x);
    const auto before=orders;rework_waves::resume_yamato(ship,*v);CHECK(orders==before&&enemy->flingy.hitpoints==500*256);
}
inline void qa9_lockdown_extra_projectiles_follow_real_launch(){
    using namespace rework_fixture;qa9_fixture::begin({63});auto ghost=unit(1,1,100,100),primary=unit(37,6,160,100);
    for(U32 i=0;i<5;i++)unit(37,6,170+int(i)*10,100);
    ghost->energy=100*256;auto shot=bullet(ghost,primary,32);
    CHECK(rework_combat_v5::pending_shots.size()==5);
    {rework_combat_v5::MissileScope impact(shot);primary->lockdown_timer=30;}CHECK(primary->lockdown_timer==60);
    pulse(101);CHECK(rework_combat_v5::pending_shots.empty());CHECK(multi_fixture::shots.size()==6&&ghost->energy==100*256);
    for(std::size_t i=1;i<6;i++){auto b=&multi_fixture::bullets[i];CHECK(b->weapon_id==32);auto target=b->target.unit;
        {rework_combat_v5::MissileScope impact(b);target->lockdown_timer=30;}CHECK(target->lockdown_timer==60);
    }
    CHECK(rework_combat_v5::pending_shots.empty());qa9_fixture::end();
}
inline void qa9_mutalisk_manual_compensates_slower_attack(){
    using namespace rework_fixture;qa9_fixture::begin({70,71,72});install();
    const U32 hydra=original_stat({0,17,38}),muta=original_stat({0,17,43}),guardian=original_stat({0,17,44});
    CHECK(owner_stat(1,{1,14,hydra})==original_stat({1,14,hydra})+3);
    CHECK(owner_stat(1,{1,14,muta})==original_stat({1,14,muta})+4);
    CHECK(owner_stat(1,{1,14,guardian})==original_stat({1,14,guardian})+6);
    auto h=unit(38,1,100,100),m=unit(43,1,200,100,true);
    CHECK(std::abs(rework_combat_v5::cooldown_ratio(h,hydra)-0.955)<0.00001);
    CHECK(std::abs(rework_combat_v5::cooldown_ratio(m,muta)-0.955)<0.00001);
    const U32 ling=original_stat({0,17,37}),ultra=original_stat({0,17,39});
    CHECK(owner_stat(1,{1,14,ling})==original_stat({1,14,ling})+2);
    CHECK(owner_stat(1,{1,14,ultra})==original_stat({1,14,ultra})+6);
    ranks[70]=ranks[71]=ranks[72]=2;install();
    CHECK(owner_stat(1,{1,14,ling})==original_stat({1,14,ling})+3);
    CHECK(owner_stat(1,{1,14,ultra})==original_stat({1,14,ultra})+12);CHECK(owner_stat(1,{1,14,muta})==original_stat({1,14,muta})+8);
    qa9_fixture::end();
}
inline void run_qa9_groups(){qa9_mutalisk_manual_compensates_slower_attack();qa9_lockdown_extra_projectiles_follow_real_launch();qa9_yamato_returns_to_attack_after_witnessed_launch();qa9_irradiate_five_branches_five_generations();qa9_irradiate_native_damage_outer_ring_and_cure();qa9_goliath_three_targets_infinite_fire_bundle();qa9_emp_hits_energyless_enemies_only();qa9_all_unit_legendaries_and_native_damage();qa9_air_wave_requires_real_counter();qa9_enemy_detector_reacts_to_burrowed_fire();qa9_upgrade_announcements_are_separate();}
}
