#pragma once
namespace host_test {
namespace temple_wave_tests {
inline bw::Unit* setup(bool capture=true){
 rework_wave_tests::begin(408);add(154,player_owner(),800,1200)->flags=1;
 auto temple=add(175,capture?player_owner():6,3728,2304);temple->flags=1;
 if(capture)write_switch(&game,2,true);return temple;
}
inline void aimed(bw::Unit* u){CHECK(u->order_target.x==3728 && u->order_target.y==2304);}
inline void capture_and_cached_transition(){
 auto temple=setup(false);auto u=wave_target_tests::wave();
 wave_targeting::issue(u);CHECK(u->order_target.x==800 && !wave_targeting::target.temple);
 write_switch(&game,0,true);write_switch(&game,1,true);game.frame_count=1;
 wave_targeting::refresh();CHECK(wave_targeting::target.base->unit_id==154);
 // Ownership alone is not the mission's activation signal.
 temple->player=U8(player_owner());wave_targeting::refresh(true);CHECK(!wave_targeting::target.temple);
 temple->player=6;write_switch(&game,2,true);wave_targeting::refresh();CHECK(!wave_targeting::target.valid);
 temple->player=U8(player_owner());wave_targeting::issue(u);aimed(u);
 CHECK(wave_targeting::target.temple && existing_track(u)->temple_ordered);
 CHECK(wave_target_tests::issued.size()==2); // Old 48-frame throttle cannot delay capture.
 wave_targeting::issue(u);CHECK(wave_target_tests::issued.size()==2);
}
inline void original_assaults_and_identity_guards(){
 setup();
 for(U32 owner:{0u,4u,5u}){
  auto moving=add(37,owner,2000,2000);moving->order=14;const auto hp=moving->flingy.hitpoints;
  wave_targeting::issue(moving);aimed(moving);auto t=existing_track(moving);
  CHECK(t && t->temple_assault && !t->spawned && !t->wave_id && moving->flingy.hitpoints==hp);
  moving->order=3;game.frame_count+=48;wave_targeting::issue(moving);aimed(moving);CHECK(moving->order==14);
  auto guard=add(38,owner,2000,2100);const auto before=*guard;wave_targeting::issue(guard);
  CHECK(std::memcmp(guard,&before,sizeof(before))==0);
  auto worker=add(41,owner,2000,2200);worker->order=14;wave_targeting::issue(worker);CHECK(worker->order_target.x!=3728);
  auto building=add(131,owner,2000,2300);building->order=14;wave_targeting::issue(building);CHECK(building->order_target.x!=3728);
  auto attack=add(38,owner,2000,2400);attack->order=10;attack->order_target.unit=&units[0];attack->ground_cooldown=5;
  wave_targeting::issue(attack);aimed(attack);CHECK(attack->order==14);
  moving->player=U8(player_owner());moving->order=3;game.frame_count+=48;wave_targeting::issue(moving);CHECK(moving->order==3);
  guard->order=14;game.alliances[player_owner()][owner]=game.alliances[owner][player_owner()]=1;
  wave_targeting::issue(guard);CHECK(guard->order_target.x!=3728);
 }
}
inline void added_rosters_and_detector_destinations(){
 for(U32 slot:{0u,15u,20u,24u,25u,26u,27u,28u,29u,30u,31u,32u,33u,34u,35u,36u,37u,38u,39u,40u,41u,42u,43u,44u,45u,46u,47u,48u,49u}){
  setup();g.current_wave_id=7;
  for(U32 id:{37u,43u,9u,42u,84u,71u,86u,75u,12u}){
   auto u=wave_target_tests::wave(id);rework_curses::identities.resize(g.units_count);
   auto& v=rework_curses::identities[std::size_t(u-g.units)];v.wave=7;v.unique=u->minor_unique_index;v.owner=u->player;v.type=u->unit_id;v.slot=slot;
   wave_targeting::issue(u);aimed(u);CHECK(u->order==(wave_targeting::detector(u)?6u:14u));
   CHECK(!rework_curses::raid_target(u));
  }
 }
}
inline void raids_spawn_at_enemy_origins(){
 auto temple=setup(false);auto worker=add(64,player_owner(),900,1200);worker->flags=1;add(176,11,900,1160);
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=10;
 auto raid=rework_waves::create(43,sc1_native::rework_wave::Raid);CHECK(raid);
 CHECK(wave_targeting::distance(raid->flingy.position.x,raid->flingy.position.y,900,1200)<384ll*384);
 CHECK(rework_curses::raid_target(raid)==worker);
 rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();CHECK(raid->order_target.x==900);
 temple->player=U8(player_owner());write_switch(&game,2,true);wave_targeting::issue(raid);aimed(raid);
 auto next=rework_waves::create(43,sc1_native::rework_wave::Raid);CHECK(next);
 CHECK(wave_targeting::distance(next->flingy.position.x,next->flingy.position.y,900,1200)>768ll*768);
 CHECK(rework_curses::appearing(next) && next->order==23);
 rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();aimed(next);
 CHECK(next->order==14 && !rework_curses::raid_target(next));
}
inline void protected_orders_and_release(){
 setup();auto u=wave_target_tests::wave(43);
 for(U32 order:{114u,147u,116u,117u,98u,99u}){
  u->order=U8(order);wave_targeting::issue(u);CHECK(u->order==order && !existing_track(u)->temple_ordered);
 }
 u->order=3;u->stasis_timer=1;wave_targeting::issue(u);CHECK(u->order==3);u->stasis_timer=0;
 u->lockdown_timer=1;wave_targeting::issue(u);CHECK(u->order==3);u->lockdown_timer=0;
 u->maelstrom_timer=1;wave_targeting::issue(u);CHECK(u->order==3);u->maelstrom_timer=0;
 u->flags|=0x40u;wave_targeting::issue(u);CHECK(u->order==3);u->flags&=~0x40u;
 rework_curses::identities.resize(g.units_count);auto& v=rework_curses::identities[std::size_t(u-g.units)];
 v.wave=1;v.unique=u->minor_unique_index;v.owner=u->player;v.type=u->unit_id;v.appearance_until=4;
 wave_targeting::issue(u);CHECK(u->order==3);v.appearance_until=0;v.transport_hold=true;
 wave_targeting::issue(u);CHECK(u->order==3);v.transport_hold=false;wave_targeting::issue(u);aimed(u);
 auto victim=add(64,player_owner(),1400,800);u->order=10;u->order_target.unit=victim;
 game.frame_count=96;wave_targeting::issue(u);CHECK(u->order==10); // Normal combat resumes after initial redirection.
}
inline void lost_objective_endings_and_other_maps(){
 for(U32 mode=0;mode<5;mode++){
  auto temple=setup();auto u=wave_target_tests::wave();wave_targeting::issue(u);aimed(u);u->order=3;
  if(mode==0)temple->flingy.hitpoints=0;
  if(mode==1)temple->player=6;
  if(mode==2)write_switch(&game,4,true);
  if(mode==3)write_switch(&game,9,true);
  if(mode==4)CHECK(set_counter(kGoalCounter,1));
  game.frame_count=96;wave_targeting::step(true,false);CHECK(u->order==3 && wave_target_tests::issued.size()==1);
 }
 rework_wave_tests::begin(407);add(154,player_owner(),800,1200);add(175,player_owner(),3728,2304);write_switch(&game,2,true);
 auto u=wave_target_tests::wave();wave_targeting::issue(u);CHECK(!wave_targeting::target.temple && u->order_target.x==800);
 auto original=add(37,4,2000,2000);original->order=14;wave_targeting::issue(original);CHECK(original->order_target.x!=800);
 abandon_session();CHECK(!wave_targeting::target.temple && !wave_targeting::target.valid);
}
}
inline constexpr std::size_t temple_wave_group_count=6;
inline void run_temple_wave_groups(){
 temple_wave_tests::capture_and_cached_transition();temple_wave_tests::original_assaults_and_identity_guards();
 temple_wave_tests::added_rosters_and_detector_destinations();temple_wave_tests::raids_spawn_at_enemy_origins();
 temple_wave_tests::protected_orders_and_release();temple_wave_tests::lost_objective_endings_and_other_maps();
 std::puts("BWP8_TEMPLE mission=408 capture_switch=2 owned_objective=175 original_owners=3 added_slots=29 raids=enemy_origin protected_orders=ok endings=ok other_missions=unchanged");
}
}
