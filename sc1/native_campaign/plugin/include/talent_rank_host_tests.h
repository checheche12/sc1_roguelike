#pragma once
// Offline synthetic host only. Production application, owner scopes, published
// display cache, native creation/healing adapters and projectile callbacks are
// exercised here. This is not an actual StarCraft/UI or campaign playtest.
namespace host_test {
namespace rank_fixture {
inline constexpr U32 first_bit=106,last_bit=237;
inline void acquire(GrowthSnapshot& snapshot,U32 bit){CHECK(bit>=first_bit && bit<=last_bit);snapshot.talent_bits[bit/32]|=1u<<(bit%32);}
inline void isolation(){
    game.starting_player_types[2]=1;game.alliances[1][2]=game.alliances[2][1]=1;
    game.starting_player_types[5]=3;
}
inline void unchanged_owners(Key key,U32 stock){for(U32 owner:{2u,5u,6u,11u})CHECK(owner_stat(owner,key)==stock);}
inline void display(bw::Unit* unit,U32 hp,U32 shield){
    U32 shown_hp=0,shown_shield=0;const auto current_hp=unit->flingy.hitpoints,current_shield=unit->shields;
    CHECK(max_hp_cache::read_display(unit,shown_hp,shown_shield));CHECK(shown_hp==hp && shown_shield==shield);
    CHECK(unit->flingy.hitpoints==current_hp && unit->shields==current_shield);
}
inline void move_result(bw::Unit* unit){
    unit->flingy.movement_type=2;unit->flingy.current_speed=unit->flingy.next_speed=1000;
    unit->flingy.current_speed_x=600;unit->flingy.current_speed_y=-800;
}
inline bw::Unit* __cdecl create_full(U32 id,int x,int y,U32 owner,const U8*){
    auto unit=add(id,owner,x,y,static_cast<int>(raw_value(0,8,id)));
    unit->shields=raw_value(0,6,id) ? static_cast<int>(raw_value(0,7,id)*256):0;return unit;
}
inline void __cdecl native_regeneration(bw::Unit* unit){
    // The original engine callback obtains its cap through the scoped native
    // DAT reads. Deliberately request more than the remaining HP/shields.
    unit->flingy.hitpoints=std::min(unit->flingy.hitpoints+999*256,static_cast<int>(raw_value(0,8,unit->unit_id)));
    if(raw_value(0,6,unit->unit_id))unit->shields=std::min(unit->shields+999*256,static_cast<int>(raw_value(0,7,unit->unit_id)*256));
}
}

void rank_every_new_bit_owner_cache_and_dat_isolation(){
    using namespace rank_fixture;U32 applied_bits=0,stat_keys=0,movement_entries=0,multi_entries=0;
    for(U32 bit=first_bit;bit<=last_bit;bit++){
        reset();isolation();const auto before=storage;GrowthSnapshot snapshot{};acquire(snapshot,bit);
        auto own=add(0,1,100,100),enemy=add(0,6,200,100),ally=add(0,2,300,100),neutral=add(0,11,400,100),rescue=add(0,5,500,100);
        CHECK(apply_snapshot(nullptr,snapshot));CHECK(g.applied && g.applied_phase==1);++applied_bits;
        bool implemented=false;
        for(const auto& patch:frozen::patches)if(patch.bit==bit){
            implemented=true;++stat_keys;const Key key{patch.table,patch.field,patch.id};
            const U32 stock=raw_value(key.table,key.field,key.id),effective=owner_stat(1,key);
            // A small cooldown ratio can round to the same DAT integer. Its
            // fractional launch clock is checked below across twenty shots.
            if(key.table==1 && key.field==16)CHECK(effective<=stock && effective>0);
            else CHECK(effective!=stock);
            unchanged_owners(key,stock);
            const U32 engine_effective=key.table==0 && key.field==48 && (key.id==11 || key.id==42 || key.id==57 || key.id==69) ? std::min(effective,8u):effective;
            {OwnerDatScope scope(1,1);CHECK(raw_value(key.table,key.field,key.id)==(key.table==1 && key.field==16 ? stock:engine_effective));}
            CHECK(raw_value(key.table,key.field,key.id)==stock);
            for(U32 owner:{2u,5u,6u,11u}){OwnerDatScope scope(owner,owner);CHECK(raw_value(key.table,key.field,key.id)==stock);}
            if(key.table==0 && key.field==8){
                auto subject=add(key.id,1,100,200);U32 shown=0;CHECK(max_hp_cache::read(subject,shown));CHECK(shown==effective && effective_max_hp(subject)==effective);
            }
            if(key.table==0 && key.field==7){
                auto subject=add(key.id,1,100,300);U32 shown_hp=0,shown_shield=0;CHECK(max_hp_cache::read_display(subject,shown_hp,shown_shield));CHECK(shown_shield==effective);
            }
            if(key.table==0 && key.field==27){
                auto subject=add(key.id,1,100,400);U32 shown=0;CHECK(max_hp_cache::read_armor(subject,shown));CHECK(shown==effective);
            }
            if(key.table==1 && (key.field==14 || key.field==15)){
                U32 shown=0;CHECK(max_hp_cache::read_weapon(own,key.field,key.id,shown));CHECK(shown==effective);
                for(auto subject:{enemy,ally,neutral,rescue}){CHECK(max_hp_cache::read_weapon(subject,key.field,key.id,shown));CHECK(shown==stock);}
            }
        }
        for(const auto& patch:frozen::movement_patches)if(patch.bit==bit){
            implemented=true;++movement_entries;
            for(U32 owner:{1u,2u,5u,6u,11u}){
                auto subject=add(patch.unit_id,owner,100,500);move_result(subject);movement_effects::after_move(subject,0,nullptr);
                if(owner==1){CHECK(subject->flingy.next_speed>1000);CHECK(subject->flingy.current_speed_x>600 && subject->flingy.current_speed_y<-800);}
                else CHECK(subject->flingy.next_speed==1000 && subject->flingy.current_speed_x==600 && subject->flingy.current_speed_y==-800);
            }
        }
        for(const auto& patch:frozen::multi_target_patches)if(patch.bit==bit){
            implemented=true;++multi_entries;multi_target::bind(multi_fixture::can,multi_fixture::outside,multi_fixture::hooked);
            for(U32 owner:{1u,2u,5u,6u,11u}){
                auto subject=add(patch.unit_id,owner,100,600);CHECK(multi_target::enabled(subject)==(owner==1));
            }
        }
        CHECK(implemented);CHECK(storage==before);init_game();CHECK(storage==before);
    }
    CHECK(applied_bits==132 && stat_keys>132 && movement_entries>0 && multi_entries>0);
}

void rank_marine_firepower_cumulative_weapon_and_cooldown(){
    using namespace rank_fixture;reset();isolation();const auto before=storage;
    auto marine=add(0,1,100,100,20*256),enemy=add(0,6,200,100,40*256);
    CHECK(raw_value(0,8,0)==40*256 && raw_value(1,14,0)==6 && raw_value(1,16,0)==15 && raw_value(1,5,0)==128);
    samase_ui_fixture::Image hp_ui;weapon_ui_fixture::Image weapon_ui;GrowthSnapshot snapshot{};
    const U32 expected_hp[]={40,40,50},expected_damage[]={6,7,8},expected_dat_cooldown[]={14,13,13},expected_live_cooldown[]={14,12,12};
    for(U32 rank=0;rank<3;rank++){
        acquire(snapshot,106+rank);snapshot.completed_phase=rank+1;CHECK(apply_snapshot(nullptr,snapshot));
        if(!rank){hp_ui.install();weapon_ui.install();}
        CHECK(owner_stat(1,{0,8,0})==expected_hp[rank]*256);CHECK(marine->flingy.hitpoints==static_cast<int>(expected_hp[rank]*128));
        CHECK(owner_stat(1,{1,14,0})==expected_damage[rank] && owner_stat(1,{1,16,0})==expected_dat_cooldown[rank]);
        CHECK(owner_stat(1,{1,5,0})==160 && owner_stat(6,{1,5,0})==128);
        display(marine,expected_hp[rank]*256,0);CHECK(hp_ui.invoke(1,marine)==expected_hp[rank]*256 && hp_ui.invoke(1,enemy)==40*256);
        CHECK(weapon_ui.damage(marine,0)==expected_damage[rank] && weapon_ui.damage(enemy,0)==6);
        // A real launch notification adjusts the native cooldown once. The
        // precise cumulative .9*.9 clock differs from sequential DAT rounding.
        marine->ground_cooldown=0;apply_unit_motion();game.frame_count+=100;
        marine->ground_cooldown=15;note_attack_launch(marine,0);apply_unit_motion();CHECK(marine->ground_cooldown==expected_live_cooldown[rank]);
        const auto live_cooldown=marine->ground_cooldown;apply_unit_motion();CHECK(marine->ground_cooldown==live_cooldown);
        bw::Bullet bullet{};bullet.player=1;bullet.weapon_id=0;const auto hp=enemy->flingy.hitpoints;
        owner_hit_hook(enemy,&bullet,1,fake_hit);CHECK(enemy->flingy.hitpoints==hp-static_cast<int>(expected_damage[rank]*256));
        CHECK(storage==before);
    }
    const auto hp=marine->flingy.hitpoints;CHECK(!apply_snapshot(nullptr,snapshot));CHECK(marine->flingy.hitpoints==hp);
}

void rank_marine_guard_three_phase_hp_ui_healing_and_late_birth(){
    using namespace rank_fixture;reset();isolation();const auto before=storage;
    auto own=add(0,1,100,100,20*256),enemy=add(0,6,200,100,20*256),ally=add(0,2,300,100,20*256),neutral=add(0,11,400,100,20*256);
    samase_ui_fixture::Image ui;GrowthSnapshot snapshot{};const U32 hp[]={50,60,70},armor[]={1,1,2},speed[]={1000,1100,1100};
    for(U32 rank=0;rank<3;rank++){
        acquire(snapshot,109+rank);snapshot.completed_phase=rank+1;CHECK(apply_snapshot(nullptr,snapshot));if(!rank)ui.install();
        CHECK(owner_stat(1,{0,8,0})==hp[rank]*256 && owner_stat(1,{0,27,0})==armor[rank]);
        CHECK(own->flingy.hitpoints==static_cast<int>(hp[rank]*128));display(own,hp[rank]*256,0);
        CHECK(ui.invoke(0,own)==hp[rank]*256 && ui.invoke(1,own)==hp[rank]*256);
        for(auto subject:{enemy,ally,neutral}){display(subject,40*256,0);CHECK(subject->flingy.hitpoints==20*256 && ui.invoke(1,subject)==40*256);}
        auto late=owner_create_hook(0,100,200,1,nullptr,create_full),late_enemy=owner_create_hook(0,200,200,6,nullptr,create_full);
        CHECK(late->flingy.hitpoints==static_cast<int>(hp[rank]*256) && late_enemy->flingy.hitpoints==40*256);display(late,hp[rank]*256,0);
        own->flingy.hitpoints=static_cast<int>(hp[rank]*256-1);owner_unit_hook(own,native_regeneration);CHECK(own->flingy.hitpoints==static_cast<int>(hp[rank]*256));
        owner_unit_hook(own,native_regeneration);CHECK(own->flingy.hitpoints==static_cast<int>(hp[rank]*256));own->flingy.hitpoints=static_cast<int>(hp[rank]*128);
        move_result(own);movement_effects::after_move(own,0,nullptr);CHECK(own->flingy.next_speed==static_cast<int>(speed[rank]));
        move_result(enemy);movement_effects::after_move(enemy,0,nullptr);CHECK(enemy->flingy.next_speed==1000);CHECK(storage==before);
    }
}

void rank_dragoon_three_phase_hp_shield_ui_and_late_birth(){
    using namespace rank_fixture;reset();isolation();const auto before=storage;
    CHECK(raw_value(0,8,66)==100*256 && raw_value(0,7,66)==80 && raw_value(1,14,66)==20);
    auto own=add(66,1,100,100,50*256),enemy=add(66,6,200,100,50*256),neutral=add(66,11,300,100,50*256);
    own->shields=enemy->shields=neutral->shields=40*256;
    samase_ui_fixture::Image ui;weapon_ui_fixture::Image weapon_ui;GrowthSnapshot snapshot{};const U32 hp[]={100,115,115},damage[]={20,22,22};
    for(U32 rank=0;rank<3;rank++){
        acquire(snapshot,187+rank);snapshot.completed_phase=rank+1;CHECK(apply_snapshot(nullptr,snapshot));if(!rank){ui.install();weapon_ui.install();}
        CHECK(owner_stat(1,{0,8,66})==hp[rank]*256 && owner_stat(1,{0,7,66})==100);
        CHECK(own->flingy.hitpoints==static_cast<int>(hp[rank]*128) && own->shields==50*256);display(own,hp[rank]*256,100);
        CHECK(ui.invoke(1,own)==hp[rank]*256 && ui.invoke(2,own)==100*256);CHECK(weapon_ui.damage(own,66)==damage[rank]);
        for(auto subject:{enemy,neutral}){display(subject,100*256,80);CHECK(ui.invoke(2,subject)==80*256 && subject->shields==40*256);CHECK(weapon_ui.damage(subject,66)==20);}
        auto late=owner_create_hook(66,100,200,1,nullptr,create_full),late_enemy=owner_create_hook(66,200,200,6,nullptr,create_full);
        CHECK(late->flingy.hitpoints==static_cast<int>(hp[rank]*256) && late->shields==100*256);display(late,hp[rank]*256,100);
        CHECK(late_enemy->flingy.hitpoints==100*256 && late_enemy->shields==80*256);
        own->flingy.hitpoints=static_cast<int>(hp[rank]*256-1);own->shields=100*256-1;owner_unit_hook(own,native_regeneration);
        CHECK(own->flingy.hitpoints==static_cast<int>(hp[rank]*256) && own->shields==100*256);CHECK(ui.invoke(2,own)==100*256);
        own->flingy.hitpoints=static_cast<int>(hp[rank]*128);own->shields=50*256;CHECK(storage==before);
    }
}

void rank_shared_squad_cumulative_heroes_and_exclusions(){
    using namespace rank_fixture;reset();isolation();const auto before=storage;
    const U32 hero_max=raw_value(0,8,19),hero_armor=raw_value(0,27,19),hero_weapon=raw_value(0,17,19),hero_damage=raw_value(1,14,hero_weapon);
    auto own=add(0,1,100,100,20*256),hero=add(19,1,100,200,static_cast<int>(hero_max/2)),enemy=add(19,6,200,200,static_cast<int>(hero_max/2));
    auto worker=add(7,1,100,300),building=add(106,1,100,400),revealer=add(101,1,100,500);
    GrowthSnapshot snapshot{};const U32 hp[]={45,50,55},motion[]={1050,1103,1158};
    for(U32 rank=0;rank<3;rank++){
        for(U32 first:{223u,226u,229u,232u})acquire(snapshot,first+rank);snapshot.completed_phase=rank+1;CHECK(apply_snapshot(nullptr,snapshot));
        CHECK(owner_stat(1,{0,8,0})==hp[rank]*256 && owner_stat(1,{1,14,0})==7+rank && owner_stat(1,{0,27,0})==rank+1);
        CHECK(owner_stat(1,{0,8,19})==hero_max+(rank+1)*5*256 && owner_stat(1,{0,27,19})==hero_armor+rank+1);
        CHECK(owner_stat(1,{1,14,hero_weapon})==hero_damage+rank+1);CHECK(enemy->flingy.hitpoints==static_cast<int>(hero_max/2));
        display(own,hp[rank]*256,0);display(hero,hero_max+(rank+1)*5*256,0);display(enemy,hero_max,0);
        for(auto subject:{own,hero,enemy,worker,building,revealer}){
            move_result(subject);movement_effects::after_move(subject,0,nullptr);
            CHECK(subject->flingy.next_speed==static_cast<int>((subject==own || subject==hero) ? motion[rank]:1000u));
        }
        for(U32 id:{7u,106u,101u})for(U32 field:{8u,27u})CHECK(owner_stat(1,{0,field,id})==raw_value(0,field,id));
        CHECK(storage==before);
    }
}

void rank_legacy_and_new_multi_target_never_duplicate(){
    using namespace rank_fixture;using namespace multi_fixture;
    for(U32 mode=0;mode<3;mode++){
        // New rank alone, historical bit alone, and both together use the same
        // production boolean ability. The combined snapshot must not fire twice.
        const U32 bc_bit=mode==1 ? 105:135;begin(bc_bit);
        if(mode==2){GrowthSnapshot s{};s.completed_phase=2;acquire(s,135);s.talent_bits[105/32]|=1u<<(105%32);CHECK(apply_snapshot(nullptr,s));}
        auto source=bc(),a=unit(37,6,130,100);unit(37,6,140,100);unit(43,6,150,100,true);unit(43,6,160,100,true);target(source,a);
        auto bullet=primary(source,19);CHECK(bullet && shots.size()==3);CHECK(shot_count(19,true)==1 && shot_count(20,true)==1);
        multi_target::launched(19,source,bullet);multi_target::step();CHECK(shots.size()==3 && !multi_target::secondary());
        game.frame_count+=30;primary(source,19);CHECK(shots.size()==6);for(const auto& shot:shots)CHECK(shot.damage==25);
        const U32 goliath_bit=mode==1 ? 104:126;begin(goliath_bit);
        if(mode==2){GrowthSnapshot s{};s.completed_phase=2;acquire(s,126);s.talent_bits[104/32]|=1u<<(104%32);CHECK(apply_snapshot(nullptr,s));}
        auto pair=goliath();auto main=pair.first,turret=pair.second;auto ground=unit(37,6,130,100);unit(43,6,140,100,true);target(main,ground);target(turret,ground);
        primary(turret,7);multi_target::step();CHECK(shots.size()==3 && shot_count(7)==1 && shot_count(8,true)==2);
        multi_target::step();CHECK(shots.size()==3);game.frame_count+=22;multi_target::step();CHECK(shots.size()==5 && shot_count(8,true)==4);
        CHECK(raw_value(1,14,7)==12 && raw_value(1,14,8)==10);
    }
}

void rank_shared_cooldown_three_phase_fractional_launch_totals(){
    using namespace rank_fixture;reset();isolation();const auto before=storage;
    auto own=add(0,1,100,100),enemy=add(0,6,200,100);GrowthSnapshot snapshot{};
    // 20 unmodified 15-frame shots total300. Three cumulative 5% stages
    // independently give285,271,257 after carrying the fractional remainder.
    const U32 totals[]={285,271,257};
    for(U32 rank=0;rank<3;rank++){
        acquire(snapshot,235+rank);snapshot.completed_phase=rank+1;CHECK(apply_snapshot(nullptr,snapshot));U32 total=0;
        for(U32 shot=0;shot<20;shot++){
            own->ground_cooldown=enemy->ground_cooldown=0;apply_unit_motion();game.frame_count+=100;
            own->ground_cooldown=enemy->ground_cooldown=15;note_attack_launch(own,0);note_attack_launch(enemy,0);apply_unit_motion();
            CHECK(own->ground_cooldown>0 && own->ground_cooldown<=15);CHECK(enemy->ground_cooldown==15);total+=own->ground_cooldown;
            const auto remaining=own->ground_cooldown;apply_unit_motion();CHECK(own->ground_cooldown==remaining);
        }
        CHECK(total==totals[rank]);CHECK(raw_value(1,16,0)==15 && storage==before);
    }
}

void rank_legacy_new_and_shared_cooldown_carry_survives_reapply(){
    using namespace rank_fixture;reset();isolation();const auto before=storage;
    auto own=add(0,1,100,100,20*256),enemy=add(0,6,200,100,20*256);GrowthSnapshot snapshot{};
    snapshot.talent_bits[0]|=1u<<2; // Historical Marine 100/130 attack period.
    for(U32 bit:{106u,107u,108u,235u,236u,237u})acquire(snapshot,bit);
    snapshot.completed_phase=1;CHECK(apply_snapshot(nullptr,snapshot));
    // Independent rational oracle: (100/130)*(.9^2)*(.95^3)
    // =555579/1040000. The unreduced denominator13,000,000,000 cannot
    // be stored in CooldownTrack::denominator, whereas the reduced one fits.
    constexpr std::uint64_t unreduced_denominator=13000000000ull;
    CHECK(unreduced_denominator>std::numeric_limits<U32>::max());U32 total=0;
    for(U32 shot=0;shot<130;shot++){
        own->ground_cooldown=enemy->ground_cooldown=0;apply_unit_motion();game.frame_count+=100;
        own->ground_cooldown=enemy->ground_cooldown=15;note_attack_launch(own,0);note_attack_launch(enemy,0);apply_unit_motion();
        CHECK(own->ground_cooldown==8 || own->ground_cooldown==9);CHECK(enemy->ground_cooldown==15);total+=own->ground_cooldown;
        auto track=existing_track(own);CHECK(track && track->cooldown[0].denominator==1040000u);
        CHECK(track->cooldown[0].fraction<track->cooldown[0].denominator);
        if(shot==19){
            CHECK(total==160);const auto carry=track->cooldown[0];const auto hp=own->flingy.hitpoints;const auto live=own->ground_cooldown;
            CHECK(!apply_snapshot(nullptr,snapshot)); // Duplicate publication is rejected without touching the live clock.
            CHECK(track->cooldown[0].fraction==carry.fraction && track->cooldown[0].denominator==carry.denominator);
            snapshot.completed_phase=2;CHECK(apply_snapshot(nullptr,snapshot)); // New phase, identical acquired effects.
            CHECK(track->cooldown[0].fraction==carry.fraction && track->cooldown[0].denominator==carry.denominator);
            CHECK(track->cooldown[0].reset_frame==carry.reset_frame && track->cooldown[0].reset_value==carry.reset_value);
            CHECK(track->cooldown[0].processed==carry.processed && track->cooldown[0].launched==carry.launched && track->cooldown[0].weapon==carry.weapon);
            CHECK(own->flingy.hitpoints==hp && own->ground_cooldown==live);
        }
    }
    CHECK(total==1042);CHECK(raw_value(1,16,0)==15 && storage==before);
}

inline constexpr std::size_t talent_rank_group_count=8;
void run_talent_rank_groups(){
    rank_every_new_bit_owner_cache_and_dat_isolation();rank_marine_firepower_cumulative_weapon_and_cooldown();
    rank_marine_guard_three_phase_hp_ui_healing_and_late_birth();rank_dragoon_three_phase_hp_shield_ui_and_late_birth();
    rank_shared_squad_cumulative_heroes_and_exclusions();rank_legacy_and_new_multi_target_never_duplicate();
    rank_shared_cooldown_three_phase_fractional_launch_totals();
    rank_legacy_new_and_shared_cooldown_carry_survives_reapply();
}
} // namespace host_test
