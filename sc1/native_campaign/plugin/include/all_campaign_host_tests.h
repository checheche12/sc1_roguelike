// Production callbacks with real stock DAT and synthetic owners only.
namespace host_test {
void all_mission_identity_and_phase_gates() {
    static_assert(std::size(campaign_config::kMissions)>=59,"complete campaigns");
    for(const auto& mission:campaign_config::kMissions){
        if(mission.mission_id==601)CHECK(mission.no_production && mission.owner==3);
        reset();make_chk(&mission);CHECK(identify_chk(chk.data(),chk.size())==&mission);
        game.campaign_mission=static_cast<std::uint16_t>(mission.campaign_index ? mission.campaign_index : mission.mission_id);
        game.map_width_tiles=static_cast<std::uint16_t>(mission.width);game.map_height_tiles=static_cast<std::uint16_t>(mission.height);
        init_units(original);CHECK(g.active && g.mission==&mission);CHECK(g.protocol.mailbox_words()[5]==mission.mission_id);
        CHECK(!counter(kRouteCounter) && !counter(kMiddleCounter) && !counter(kReadyCounter) && !counter(kAckCounter));
        for(U32 i=0;i<16;i++)CHECK(game.upgrade_level_sc[mission.owner][i]==(mission.no_production ? 6 : 0));
        if(mission.mission_id==601){
            std::array<U8,61*12> levels{};levels.fill(1);
            std::array<samase::ExtendedArray,1> arrays{};arrays[0].pointer=levels.data();arrays[0].end=levels.data()+levels.size();
            g.extended=arrays.data();g.extended_count=arrays.size();CHECK(apply_no_production_upgrades());
            for(U32 id=0;id<61;id++)for(U32 owner=0;owner<12;owner++)CHECK(levels[id*12+owner]==(id<16 && owner==3 ? 6 : 1));
            g.extended=nullptr;g.extended_count=0;
        }
        auto snapshot=load_reply(1);snapshot[12]=snapshot[28]=0;publish(snapshot);protocol_pump(nullptr);CHECK(g.protocol.completed_phase()==1);
        game.switches[campaign_config::kMiddleSwitch/32]|=1u<<(campaign_config::kMiddleSwitch%32);
        CHECK(!counter(kGoalCounter));
        observe_progress_dialog(true); // Production modal observation, without opening a game window.
        for(int n=0;n<4;n++)protocol_pump(nullptr);CHECK(g.protocol.requested_phase()==1);
        tick();CHECK(g.protocol.requested_phase()==1);
        tick();CHECK(g.protocol.requested_phase()==2 && g.protocol.state()==1);
        snapshot=load_reply(2);snapshot[12]=snapshot[28]=0;publish(snapshot);tick();CHECK(g.protocol.completed_phase()==2);
        game.switches[campaign_config::kRouteSwitchBase/32]|=1u<<(campaign_config::kRouteSwitchBase%32);
        game.switches[campaign_config::kGoalSwitch/32]|=1u<<(campaign_config::kGoalSwitch%32);tick();CHECK(g.protocol.requested_phase()==3 && !counter(kReadyCounter));
        observe_progress_dialog(true);snapshot=load_reply(3);snapshot[12]=snapshot[28]=0;publish(snapshot);tick();
        CHECK(g.protocol.state()==3 && !counter(kReadyCounter) && !counter(kAckCounter));
        auto ack=reply(2);for(int i=0;i<4;i++)ack[4+i]=g.protocol.mailbox_words()[10+i];ack[8]=1;ack[9]=1;
        publish(ack);protocol_pump(nullptr);CHECK(!counter(kReadyCounter) && !counter(kAckCounter));
        tick();CHECK(counter(kReadyCounter) && counter(kAckCounter));
        const auto old=g.protocol.mailbox_words();init_game();CHECK(!g.active && !g.protocol.mailbox_words());
        MEMORY_BASIC_INFORMATION info{};CHECK(VirtualQuery(const_cast<U32*>(old),&info,sizeof(info))==sizeof(info));CHECK(info.Protect==PAGE_NOACCESS);
        make_chk(&mission);init_units(original);CHECK(g.active && g.protocol.mailbox_words()!=old);
        chk[8]^=1;CHECK(!identify_chk(chk.data(),chk.size()));
    }
}
void switch_initialization_and_route_isolation() {
    reset();make_chk();for(auto& word:game.switches)word=0xa55aa55au;
    const auto before=game;init_units(original);CHECK(g.active);
    for(U32 i=0;i<256;i++) {
        const bool reserved=(i>=campaign_config::kGoalSwitch && i<campaign_config::kRouteSwitchBase+campaign_config::kRouteSwitchCount) || i==campaign_config::kEnemyBaseSeenSwitch;
        CHECK(switch_set(&game,i)==(!reserved && switch_set(&before,i)));
    }
    for(U32 route=0;route<=campaign_config::kRouteSwitchCount;route++) {
        const auto previous=game;CHECK(set_counter(kRouteCounter,route));CHECK(counter_value(kRouteCounter)==route);
        for(U32 i=0;i<256;i++) {
            if(i>=campaign_config::kRouteSwitchBase && i<campaign_config::kRouteSwitchBase+campaign_config::kRouteSwitchCount)
                CHECK(switch_set(&game,i)==(route==i-campaign_config::kRouteSwitchBase+1));
            else CHECK(switch_set(&game,i)==switch_set(&previous,i));
        }
    }
    const auto previous=game;CHECK(!set_counter(kRouteCounter,7));
    CHECK(std::memcmp(game.switches,previous.switches,sizeof(game.switches))==0);
    // Only newly authenticated V3_SW1 assets may use this native handshake.
    const std::string old_marker="SC1_NATIVE_M101_V2_R469";
    const std::string current=legacy_mission_marker(campaign_config::kMissions[0]).data();
    auto marker=std::search(chk.begin(),chk.end(),current.begin(),current.end());CHECK(marker!=chk.end());
    std::fill(marker,marker+current.size(),U8(0));std::copy(old_marker.begin(),old_marker.end(),marker);
    CHECK(!identify_chk(chk.data(),chk.size()));
}
void all_mission_early_goal_and_dialog_barriers() {
    U32 mission_number=0;
    for(const auto& mission:campaign_config::kMissions) {
        reset();make_chk(&mission);
        game.campaign_mission=static_cast<std::uint16_t>(mission.campaign_index ? mission.campaign_index : mission.mission_id);
        game.map_width_tiles=static_cast<std::uint16_t>(mission.width);game.map_height_tiles=static_cast<std::uint16_t>(mission.height);
        init_units(original);CHECK(g.active);
        const U32 route=1+mission_number++%campaign_config::kRouteSwitchCount;
        game.switches[campaign_config::kRouteSwitchBase/32]|=1u<<((campaign_config::kRouteSwitchBase+route-1)%32);
        game.switches[campaign_config::kGoalSwitch/32]|=1u<<(campaign_config::kGoalSwitch%32);
        // A short/unavailable diagnostic death array must not block CHK switches.
        std::array<samase::ExtendedArray,11> arrays{};std::array<U8,4> diagnostic{};
        arrays[10].pointer=diagnostic.data();arrays[10].end=diagnostic.data()+diagnostic.size();
        g.extended=arrays.data();g.extended_count=arrays.size();
        const auto ending=[&] {
            return switch_set(&game,campaign_config::kRouteSwitchBase+route-1) &&
                switch_set(&game,campaign_config::kReadySwitch) && switch_set(&game,campaign_config::kAckSwitch);
        };
        for(U32 phase=1;phase<=3;phase++) {
            auto snapshot=load_reply(phase);snapshot[12]=snapshot[28]=0;
            observe_progress_dialog(true);publish(snapshot);protocol_pump(nullptr);
            CHECK(g.protocol.completed_phase()==phase);CHECK(!ending());
            for(int n=0;n<6;n++)protocol_pump(nullptr);
            CHECK(g.protocol.requested_phase()==phase);CHECK(!counter(kReadyCounter) && !counter(kAckCounter));
            if(phase==3) {
                CHECK(g.protocol.state()==3);
                auto ack=reply(2);for(int i=0;i<4;i++)ack[4+i]=g.protocol.mailbox_words()[10+i];ack[8]=1;ack[9]=1;
                publish(ack);protocol_pump(nullptr);CHECK(g.protocol.state()==4 && !ending());
            }
            tick(); // First simulation frame sees the modal has returned.
            CHECK(g.protocol.requested_phase()==phase && !ending());
            frame();CHECK(g.protocol.requested_phase()==phase && !ending()); // Same frame cannot advance.
            tick(); // Next simulation frame may request the following stage / release Victory.
            if(phase<3)CHECK(g.protocol.requested_phase()==phase+1 && g.protocol.state()==1 && !ending());
            else CHECK(ending() && counter_value(kRouteCounter)==route);
        }
        // Diagnostic poisoning cannot select another ending or release the gate.
        CHECK(set_counter(kAckCounter,0));game.deaths[kAckCounter][kCounterOwner]=1;CHECK(!ending());
        g.extended=nullptr;g.extended_count=0;init_game();
    }
}
U32 inspected_hp=0,inspected_weapon=0;
void __cdecl inspect_owner(bw::Unit* u){inspected_hp=raw_value(0,8,u->unit_id);inspected_weapon=raw_value(1,14,raw_value(0,17,u->unit_id));}
void owner_views_all_races() {
    const U32 ids[]={0,37,66};
    for(U32 id:ids){
        reset();U32 bit=0xffffffffu;
        for(const auto& p:frozen::patches)if(p.table==0 && p.field==8 && p.id==id && p.op==1){bit=p.bit;break;}
        CHECK(bit!=0xffffffffu);GrowthSnapshot snapshot{};snapshot.talent_bits[bit/32]=1u<<(bit%32);snapshot.curse_counts[1]=snapshot.curse_counts[2]=1;
        const auto base=raw_value(0,8,id);auto own=add(id,1,100,100,static_cast<int>(base/2));auto foe=add(id,6,900,900,static_cast<int>(base/2));
        auto ally=add(id,2,200,200,static_cast<int>(base/2));auto neutral=add(id,11,300,300,static_cast<int>(base/2));
        game.starting_player_types[2]=3; // Rescue remains protected even before alliance initialization.
        CHECK(apply_snapshot(nullptr,snapshot));CHECK(raw_value(0,8,id)==base);
        const auto own_max=owner_stat(1,{0,8,id}),enemy_max=owner_stat(6,{0,8,id});CHECK(own_max>base && enemy_max>base);
        owner_unit_hook(own,inspect_owner);CHECK(inspected_hp==own_max);CHECK(raw_value(0,8,id)==base);
        owner_unit_hook(foe,inspect_owner);CHECK(inspected_hp==enemy_max);CHECK(raw_value(0,8,id)==base);
        owner_unit_hook(ally,inspect_owner);CHECK(inspected_hp==base);owner_unit_hook(neutral,inspect_owner);CHECK(inspected_hp==base);
        CHECK(own->flingy.hitpoints==static_cast<int>(own_max/2));CHECK(foe->flingy.hitpoints==static_cast<int>(enemy_max/2));
        CHECK(ally->flingy.hitpoints==static_cast<int>(base/2) && neutral->flingy.hitpoints==static_cast<int>(base/2));
        {OwnerDatScope friendly(1,1,own);CHECK(raw_value(0,8,id)==own_max);{OwnerDatScope enemy(6,6,foe);CHECK(raw_value(0,8,id)==enemy_max);}CHECK(raw_value(0,8,id)==own_max);}
        CHECK(raw_value(0,8,id)==base);
        const auto thread=g.game_thread.load();g.game_thread=thread+1;{OwnerDatScope foreign(1,1,own);CHECK(raw_value(0,8,id)==base);}g.game_thread=thread;
        init_game();CHECK(raw_value(0,8,id)==base);
    }
}
void __cdecl fake_damage(bw::Unit* u,std::int32_t amount,bw::Unit*,U32,U32){u->flingy.hitpoints-=amount;}
void __cdecl fake_hit(bw::Unit* u,bw::Bullet* bullet,U32){owner_damage_hook(u,static_cast<int>(raw_value(1,14,bullet->weapon_id)*256),nullptr,bullet->player,1,fake_damage);}
void projectile_owner_and_barrier() {
    reset();GrowthSnapshot s{};s.talent_bits[0]=1;s.curse_counts[1]=1;s.curse_counts[7]=1;s.curse_counts[8]=1;CHECK(apply_snapshot(nullptr,s));
    auto target=add(0,1,100,100,50000);auto enemy=add(0,6,1000,1000,50000);refresh_units();g.wave_spawn_number=0;mark_wave_unit(enemy);CHECK(existing_track(enemy)->elite && existing_track(enemy)->barrier);
    bw::Bullet bullet{};bullet.player=6;bullet.weapon_id=0;g.bullet_elites[&bullet]=true;
    const auto weapon=owner_stat(6,{1,14,0});const auto hp=target->flingy.hitpoints;
    owner_hit_hook(target,&bullet,1,fake_hit);CHECK(target->flingy.hitpoints==hp-static_cast<int>((weapon*256*6+4)/5));
    const auto elite_max=owner_stat(6,{0,8,0})*3/2;
    {OwnerDatScope first(6,6,enemy);CHECK(raw_value(0,8,0)==elite_max);{OwnerDatScope nested(6,6,enemy);CHECK(raw_value(0,8,0)==elite_max);}CHECK(raw_value(0,8,0)==elite_max);}
    CHECK(raw_value(0,8,0)==original_stat({0,8,0}));
    CHECK(raw_value(1,14,0)==6);
    U32 spells=0;for(U32 w=0;w<130;w++)if(!ordinary_weapon(w) && raw_value(1,14,w)){
        ++spells;const U32 base=raw_value(1,14,w);CHECK(owner_stat(6,{1,14,w})==base);
        bullet.weapon_id=static_cast<U8>(w);const auto health=target->flingy.hitpoints;owner_hit_hook(target,&bullet,1,fake_hit);CHECK(target->flingy.hitpoints==health-static_cast<int>(base*256));
    }CHECK(spells>0);bullet.weapon_id=0; // No permanent weapon modification.
    // A projectile keeps the original owner/elite identity even after source removal.
    enemy->player=11;target->flingy.hitpoints=hp;owner_hit_hook(target,&bullet,1,fake_hit);CHECK(target->flingy.hitpoints==hp-static_cast<int>((weapon*256*6+4)/5));
    enemy->player=6;existing_track(enemy)->spawn_second=game.elapsed_seconds;
    bullet.player=1;g.bullet_elites[&bullet]=false;const auto before=enemy->flingy.hitpoints;
    owner_hit_hook(enemy,&bullet,1,fake_hit);CHECK(enemy->flingy.hitpoints==before-static_cast<int>((6*256*3+3)/4));
    game.elapsed_seconds+=20;const auto later=enemy->flingy.hitpoints;owner_hit_hook(enemy,&bullet,1,fake_hit);CHECK(enemy->flingy.hitpoints==later-6*256);
}
void __cdecl fake_timers(bw::Unit* u){u->flingy.hitpoints=std::min(u->flingy.hitpoints+256,static_cast<int>(raw_value(0,8,u->unit_id)));}
bw::Unit* __cdecl stat_create(U32 id,int x,int y,U32 owner,const U8*){return add(id,owner,x,y,static_cast<int>(raw_value(0,8,id)));}
void __cdecl fake_give(bw::Unit* u,U32 player){
    auto& old=game.supplies[2].used[u->player];const U32 cost=raw_value(0,46,u->unit_id);old=old>=cost ? old-cost : 0;
    game.supplies[2].used[player]+=cost;u->player=static_cast<U8>(player);
}
void __cdecl fake_transform(bw::Unit* u,U32 id){u->unit_id=static_cast<std::uint16_t>(id);}
void birth_healing_owner_change_and_modes() {
    reset();GrowthSnapshot s{};s.talent_bits[0]=1u<<1;s.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,s));const U8 skin[]={1,1};
    auto own=owner_create_hook(0,100,100,1,skin,stat_create);auto foe=owner_create_hook(0,900,900,6,skin,stat_create);auto rescue=owner_create_hook(0,500,500,2,skin,stat_create);
    CHECK(own->flingy.hitpoints==12800 && foe->flingy.hitpoints==11264 && rescue->flingy.hitpoints==10240);
    own->flingy.hitpoints-=128;foe->flingy.hitpoints-=128;owner_unit_hook(own,fake_timers);owner_unit_hook(foe,fake_timers);CHECK(own->flingy.hitpoints==12800 && foe->flingy.hitpoints==11264);
    owner_give_hook(own,6,fake_give);CHECK(own->player==6 && own->flingy.hitpoints==11264);owner_give_hook(own,2,fake_give);CHECK(own->flingy.hitpoints==10240);
    auto tank=add(5,6,1000,1000,10000);refresh_units();g.wave_spawn_number=0;mark_wave_unit(tank);CHECK(existing_track(tank)->spawned);
    owner_transform_hook(tank,30,fake_transform);CHECK(existing_track(tank)->spawned && existing_track(tank)->id==30);
    reset();s={};U32 shield_bit=0xffffffffu;
    for(const auto& p:frozen::patches)if(p.table==0 && p.field==7 && p.id==66){shield_bit=p.bit;break;}CHECK(shield_bit!=0xffffffffu);
    s.talent_bits[shield_bit/32]|=1u<<(shield_bit%32);s.talent_bits[0]|=1u<<7;CHECK(apply_snapshot(nullptr,s));
    auto dragoon=add(66,1,100,100);dragoon->shields=static_cast<int>(owner_stat(1,{0,7,66})*128);
    owner_give_hook(dragoon,6,fake_give);CHECK(dragoon->shields==static_cast<int>(original_stat({0,7,66})*128));
    owner_give_hook(dragoon,1,fake_give);CHECK(dragoon->shields==static_cast<int>(owner_stat(1,{0,7,66})*128));
    auto probe=add(2,1,200,200);const U32 cheap=owner_stat(1,{0,46,2}),stock=original_stat({0,46,2});CHECK(cheap<stock);
    game.supplies[2].used[1]=10+cheap;game.supplies[2].used[6]=20;
    owner_give_hook(probe,6,fake_give);CHECK(game.supplies[2].used[1]==10 && game.supplies[2].used[6]==20+stock);
    owner_give_hook(probe,1,fake_give);CHECK(game.supplies[2].used[1]==10+cheap && game.supplies[2].used[6]==20);

}
void motion_and_regeneration_are_owner_only() {
    reset();const auto& p=frozen::movement_patches[0];GrowthSnapshot s{};s.talent_bits[p.bit/32]=1u<<(p.bit%32);s.curse_counts[3]=1;s.curse_counts[5]=1;
    CHECK(apply_snapshot(nullptr,s));auto own=add(p.unit_id,1,100,100,10000);auto foe=add(p.unit_id,6,1000,1000,10000);auto neutral=add(p.unit_id,11,1500,1500,10000);
    own->flingy.top_speed=foe->flingy.top_speed=neutral->flingy.top_speed=1000;
    apply_unit_motion();CHECK(own->flingy.top_speed==(1000*p.numerator+p.denominator/2)/p.denominator);CHECK(foe->flingy.top_speed==1075 && neutral->flingy.top_speed==1000);
    apply_unit_motion();CHECK(foe->flingy.top_speed==1075);foe->flingy.top_speed=2000;apply_unit_motion();CHECK(foe->flingy.top_speed==2150);
    auto ling=add(37,6,1600,1600,5000);refresh_units();g.wave_spawn_number=0;mark_wave_unit(ling);const auto maxhp=owner_stat(6,{0,8,37});const auto before=ling->flingy.hitpoints;
    regenerate_waves(game.elapsed_seconds+5);CHECK(ling->flingy.hitpoints==before);regenerate_waves(game.elapsed_seconds+6);CHECK(ling->flingy.hitpoints==before+static_cast<int>(maxhp/100));
    auto ally=add(37,1,500,500,5000);regenerate_waves(game.elapsed_seconds+7);CHECK(ally->flingy.hitpoints==5000);
    bw::SpriteScr sprite{};sprite.width=40;sprite.main_image=&sprite;ling->flingy.sprite=&sprite;
    auto tracked=track_unit(ling);tracked->elite=tracked->barrier=true;tracked->spawn_second=game.elapsed_seconds;
    wave_marker(ling,*tracked,game.elapsed_seconds);CHECK(markers.size()==2 && markers[0].image==378 && markers[0].y==-16 && markers[1].y==0);
    wave_marker(ling,*tracked,game.elapsed_seconds+20);CHECK(markers.size()==3 && markers.back().y==-16);
    ling->player=1;wave_marker(ling,*tracked,game.elapsed_seconds+21);CHECK(markers.size()==3);

}
void __cdecl campaign_lethal_damage(bw::Unit* u,std::int32_t,bw::Unit*,U32 player,U32) {
    u->last_attacking_player=static_cast<U8>(player);owner_kill_hook(u,kill);
}
void campaign_wave_safety_and_no_production_caps() {
    for(const auto& mission:campaign_config::kMissions){
        if(mission.mission_id==101)continue;
        reset();g.mission=&mission;g.campaign_index=mission.mission_id;game.campaign_mission=static_cast<std::uint16_t>(g.campaign_index);
        game.map_width_tiles=static_cast<std::uint16_t>(mission.width);game.map_height_tiles=static_cast<std::uint16_t>(mission.height);
        for(U32 p=0;p<8;p++)game.starting_player_types[p]=p==mission.owner ? 2 : 1;
        GrowthSnapshot s{};CHECK(apply_snapshot(nullptr,s));
        const sc1_native::campaign_wave_config::Origin* origin=nullptr;for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==mission.mission_id){origin=&o;break;}CHECK(origin);
        const U32 first=sc1_native::wave_progression::first_elapsed_seconds(mission.no_production);campaign_waves(first-1,true,false);CHECK(!g.pending_origin && count==0);
        campaign_waves(first,true,false);CHECK(g.pending_origin);CHECK(g.pending_origin);
        for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==mission.mission_id)add(0,mission.owner,o.center.x,o.center.y);
        const auto blockers=count;campaign_waves(first+4,true,false);CHECK(count==blockers && !g.pending_origin && orders==0);
        for(std::size_t i=0;i<blockers;i++)units[i].flingy.hitpoints=0;add(0,mission.owner,origin->target.x,origin->target.y);const auto spawn_begin=count;game.frame_count+=48;const auto next=g.next_wave_second;campaign_waves(next,true,false);CHECK(g.pending_origin);campaign_waves(next+4,true,false);
        CHECK(count>spawn_begin && orders>0);CHECK(added_supply()<=(mission.no_production ? 24u : 480u));
        for(std::size_t i=spawn_begin;i<count;i++){CHECK(units[i].player!=mission.owner);CHECK(existing_track(&units[i]) && existing_track(&units[i])->spawned);}
        const auto created=count;campaign_waves(g.next_wave_second+10000,true,true);CHECK(count==created);
    }
    reset();g.mission=&campaign_config::kMissions[1];for(U32 p=0;p<8;p++)game.starting_player_types[p]=p==player_owner() ? 2 : 1;
    GrowthSnapshot deaths{};deaths.curse_counts[6]=1;CHECK(apply_snapshot(nullptr,deaths));
    U32 enemy_owner=0;for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==g.mission->mission_id){enemy_owner=o.owner;break;}
    for(int i=0;i<20;i++){auto unit=add(0,enemy_owner,10,10);owner_damage_hook(unit,99999,nullptr,player_owner(),1,campaign_lethal_damage);}
    CHECK(g.death_wave_due && g.kills_for_wave==0);campaign_waves(100,true,false);CHECK(!g.pending_origin && !g.death_wave_due);
    g.kills_for_wave=19;campaign_waves(299,true,false);CHECK(g.kills_for_wave==0 && !g.pending_origin);
    g.next_wave_second=10000;
    for(int i=0;i<20;i++){auto unit=add(0,enemy_owner,10,10);owner_damage_hook(unit,99999,nullptr,player_owner(),1,campaign_lethal_damage);}
    CHECK(g.death_wave_due);campaign_waves(300,true,false);CHECK(g.pending_origin && g.pending_second==310 && !g.death_wave_due);
    campaign_waves(310,true,false);CHECK(!g.pending_origin && added_supply()>0 && added_supply()<=16);
    for(std::size_t i=20;i<count;i++){units[i].last_attacking_player=static_cast<U8>(player_owner());owner_kill_hook(&units[i],kill);}CHECK(g.kills_for_wave==0 && !g.death_wave_due);
    for(int i=0;i<20;i++){auto unit=add(0,enemy_owner,10,10);owner_damage_hook(unit,99999,nullptr,player_owner(),1,campaign_lethal_damage);}
    CHECK(g.death_wave_due);campaign_waves(330,true,false);CHECK(!g.pending_origin && !g.death_wave_due);

}
void run_all_campaign_groups(){all_mission_identity_and_phase_gates();switch_initialization_and_route_isolation();all_mission_early_goal_and_dialog_barriers();owner_views_all_races();projectile_owner_and_barrier();birth_healing_owner_change_and_modes();motion_and_regeneration_are_owner_only();campaign_wave_safety_and_no_production_caps();}
}
