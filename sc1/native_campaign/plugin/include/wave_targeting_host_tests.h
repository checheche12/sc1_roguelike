#pragma once
namespace host_test {
namespace wave_target_tests {
struct Issued {bw::Unit* unit;U32 x,y;};inline std::vector<Issued> issued;
inline void __cdecl record(bw::Unit* u,U32 id,U32 x,U32 y,bw::Unit* target,U32 fow){
    issued.push_back({u,x,y});order(u,id,x,y,target,fow);u->order_target.unit=target;
}
inline void begin(U32 mission=106){
    reset();for(const auto& m:campaign_config::kMissions)if(m.mission_id==mission){g.mission=&m;break;}
    CHECK(g.mission->mission_id==mission);g.campaign_index=g.mission->campaign_index;game.campaign_mission=static_cast<std::uint16_t>(g.campaign_index);
    game.map_width_tiles=static_cast<std::uint16_t>(g.mission->width);game.map_height_tiles=static_cast<std::uint16_t>(g.mission->height);
    for(U32 i=0;i<8;i++)game.starting_player_types[i]=i==player_owner()?2:1;
    game.frame_count=0;g.order=record;g.current_wave_id=1;issued.clear();
}
inline bw::Unit* wave(U32 id=37,U32 owner=4,int x=1500,int y=800){
    auto u=add(id,owner,x,y);mark_wave_unit(u);return u;
}
inline void advance(U32 frame){game.frame_count=frame;wave_targeting::step(true,false);}
inline void t06_rescue_move_destroy(){
    begin();CHECK(player_owner()==0);auto army=add(0,0,1340,2860);auto cc=add(106,6,320,2544);cc->flags=1;
    auto u=wave();advance(0);CHECK(issued.size()==1 && issued.back().x==1340 && issued.back().y==2860);
    // Rescue transfers the original CC into player0, away from the static start.
    cc->player=0;advance(48);CHECK(issued.size()==2 && issued.back().x==320 && issued.back().y==2544);
    cc->flags|=4;cc->flingy.position={900,2000};advance(96);CHECK(issued.size()==3 && issued.back().x==900 && issued.back().y==2000);
    cc->flags&=~4u;cc->flingy.position={1200,1600};advance(144);CHECK(issued.size()==4 && issued.back().x==1200 && issued.back().y==1600);
    cc->flingy.hitpoints=0;army->flingy.position={1300,1500};advance(192);CHECK(issued.size()==5 && issued.back().x==1300 && issued.back().y==1500);
    CHECK(issued.back().unit==u);
}
inline void only_marked_hostile_identities(){
    begin();add(106,0,400,2200)->flags=1;
    auto original=add(37,4,1500,800);track_unit(original);const auto untouched=*original;
    auto zero_id=wave();existing_track(zero_id)->wave_id=0;
    auto ally=wave(37,2);game.alliances[0][2]=game.alliances[2][0]=1;
    auto neutral=wave(37,11);auto converted=wave();converted->player=0;
    auto recycled=wave();++recycled->minor_unique_index;
    auto morphed=wave();morphed->unit_id=38;
    auto good=wave();advance(0);CHECK(issued.size()==1 && issued[0].unit==good);
    CHECK(std::memcmp(original,&untouched,sizeof(untouched))==0);
    CHECK(zero_id->order==3 && ally->order==3 && neutral->order==3 && converted->order==3 && recycled->order==3 && morphed->order==3);
    const sc1_native::WaveRect area{0,0,3000,3000};wave_attack(nullptr,4,&area,1,1);CHECK(issued.size()==1);
    good->player=0;advance(48);CHECK(issued.size()==1);CHECK(std::memcmp(original,&untouched,sizeof(untouched))==0);
}
inline void combat_and_order_throttle(){
    begin();auto cc=add(106,0,400,2200);auto victim=add(0,0,1400,800);auto u=wave();advance(0);CHECK(issued.size()==1);
    advance(24);advance(48);advance(72);CHECK(issued.size()==1);
    cc->flingy.position={800,1800};u->order=10;u->order_target.unit=victim;advance(96);CHECK(issued.size()==1);
    victim->flingy.hitpoints=0;u->ground_cooldown=1;advance(120);CHECK(issued.size()==1);
    u->ground_cooldown=0;existing_track(u)->last_attack_frame=120;advance(144);CHECK(issued.size()==1);
    advance(168);CHECK(issued.size()==2 && issued.back().x==800);
    u->order=3;advance(192);CHECK(issued.size()==2);advance(216);CHECK(issued.size()==3);
    u->order=114;cc->flingy.position={1200,1400};advance(264);CHECK(issued.size()==3); // CastLockdown must finish.
    u->order=3;u->stasis_timer=1;advance(288);CHECK(issued.size()==3);u->stasis_timer=0;u->flags|=0x40;advance(312);CHECK(issued.size()==3);
    u->flags&=~0x40u;advance(336);CHECK(issued.size()==4);
    // Small position changes do not repeatedly tear down the current path.
    cc->flingy.position.x+=20;advance(384);CHECK(issued.size()==4);cc->flingy.position.x+=60;advance(408);CHECK(issued.size()==5);
    // A genuine stalled move gets a sparse retry even if the destination did
    // not move. Ordinary path progress prevents that retry.
    advance(576);CHECK(issued.size()==5);advance(600);CHECK(issued.size()==6);
    u->flingy.position.x+=32;advance(768);advance(792);CHECK(issued.size()==6);
}
inline void turret_combat_and_target_fallback(){
    begin();auto cc=add(106,0,400,2200);auto victim=add(0,0,1400,800);auto u=wave(3);auto turret=add(4,4,1500,800);u->subunit=turret;turret->subunit=u;
    turret->ground_cooldown=3;advance(0);CHECK(issued.empty());turret->ground_cooldown=0;turret->order_target.unit=victim;advance(24);CHECK(issued.empty());
    victim->flingy.hitpoints=0;advance(48);CHECK(issued.size()==1 && issued[0].unit==u);
    // Losing the only owned base falls back to a current surviving army member.
    auto a=add(0,0,1000,1200),b=add(0,0,1100,1250),c=add(0,0,1400,1500);cc->player=6;
    advance(96);CHECK(issued.size()==2);CHECK((issued.back().x==static_cast<U32>(a->flingy.position.x)) || (issued.back().x==static_cast<U32>(b->flingy.position.x)) || (issued.back().x==static_cast<U32>(c->flingy.position.x)));
    a->flingy.hitpoints=b->flingy.hitpoints=c->flingy.hitpoints=0;advance(144);CHECK(issued.size()==2);CHECK(!wave_targeting::target.valid);
}
inline void stable_primary_base_and_session_goal(){
    begin();auto old=add(106,0,400,2200);old->flags=1;auto newer=add(106,0,1800,800);newer->flags=1;
    add(7,0,400,2200);auto u=wave();advance(0);CHECK(issued.back().x==400);
    add(7,0,1800,800);advance(48);CHECK(issued.size()==1); // Equal economies retain selected base.
    add(7,0,1810,810);add(7,0,1820,820);advance(96);CHECK(issued.size()==2 && issued.back().x==1800);
    newer->flags|=4;advance(144);CHECK(issued.size()==3 && issued.back().x==400);
    old->flingy.hitpoints=0;newer->flags&=~4u;++newer->minor_unique_index;advance(192);CHECK(issued.size()==4 && issued.back().x==1800);
    u->order=3;CHECK(set_counter(kGoalCounter,1));advance(240);CHECK(issued.size()==4);
    CHECK(set_counter(kGoalCounter,0));game.frame_count=288;wave_targeting::step(false,false);CHECK(issued.size()==4);
    abandon_session();CHECK(!wave_targeting::target.valid && !wave_targeting::sampled);CHECK(g.tracks.empty());
}
inline void all_campaign_headquarters_and_t01_callback(){
    for(const auto& m:campaign_config::kMissions){
        begin(m.mission_id);const U32 enemy=player_owner()==4 ? 6u:4u;
        for(U32 id:{106u,131u,132u,133u,154u}){
            auto hq=add(id,player_owner(),500,500);hq->flags=1;
            auto u=wave(37,enemy,1200,1000);wave_targeting::refresh(true);wave_targeting::issue(u);
            CHECK(!issued.empty() && issued.back().unit==u && issued.back().x==500 && issued.back().y==500);
            hq->flingy.hitpoints=0;u->flingy.hitpoints=0;
        }
    }
    begin(101);auto hq=add(106,player_owner(),700,900);auto added=wave(3,6,300,300);auto original=add(37,6,310,300);const auto before=*original;
    const sc1_native::WaveRect area{200,200,400,400};wave_attack(nullptr,6,&area,100,100);
    CHECK(issued.size()==1 && issued.back().unit==added && issued.back().x==700 && issued.back().y==900);
    CHECK(std::memcmp(original,&before,sizeof(before))==0);hq->flingy.position={1100,1200};game.frame_count=48;wave_attack(nullptr,6,&area,100,100);
    CHECK(issued.size()==2 && issued.back().x==1100 && issued.back().y==1200);
}
}
inline void qa78_arbiters_and_orphan_detectors_march(){
 using namespace wave_target_tests;
 for(U32 id:{71u,86u,9u,42u,84u}){
  begin();g.applied=true;auto hq=add(106,player_owner(),400,2200);hq->flags=1;
  auto u=wave(id,4,1500,800);u->ai=reinterpret_cast<void*>(1);
  rework_curses::identities.resize(g.units_count);auto& v=rework_curses::identities[std::size_t(u-g.units)];v.wave=1;v.unique=u->minor_unique_index;v.owner=u->player;v.type=u->unit_id;
  const bool arbiter=id==71||id==86;
  auto leader=wave(37,4,1200,1000);advance(0);CHECK(u->order==(arbiter?14u:6u)&&u->order_target.x==(arbiter?400:1200));
  // An acquired but stale remote enemy must not pin an Arbiter at its origin.
  if(arbiter){u->order=10;u->order_target.unit=hq;advance(48);CHECK(u->order==10);advance(192);CHECK(u->order==6);}
  leader->flingy.hitpoints=0;advance(240);CHECK(u->order==6&&u->order_target.x==400&&u->order_target.y==2200);
  g.current_wave_id=2;auto next=wave(37,4,700,1400);advance(288);CHECK(u->order==6&&u->order_target.x==(arbiter?400:700));
  u->order=147;next->flingy.position.x=600;advance(336);CHECK(u->order==147); // Preserve Stasis casting.
  u->order=3;u->stasis_timer=1;advance(384);CHECK(u->order==3);u->stasis_timer=0;
  u->player=U8(player_owner());advance(432);CHECK(u->order==3); // Never take over captured units.
 }
 std::puts("QA78_ESCORT arbiters=2 direct_base_attack=1 detector_types=3 orphan_join=1 stale_target=1 spells_preserved=1");
}
inline constexpr std::size_t wave_targeting_group_count=7;
inline void run_wave_targeting_groups(){
    qa78_arbiters_and_orphan_detectors_march();
    wave_target_tests::t06_rescue_move_destroy();wave_target_tests::only_marked_hostile_identities();
    wave_target_tests::combat_and_order_throttle();wave_target_tests::turret_combat_and_target_fallback();
    wave_target_tests::stable_primary_base_and_session_goal();wave_target_tests::all_campaign_headquarters_and_t01_callback();
}
}
