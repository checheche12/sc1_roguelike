#pragma once
namespace host_test {
namespace rework_wave_tests {
namespace p=sc1_native::rework_wave;
inline void qa_stack_counts_and_wave_budgets(){
 CHECK(p::reduced_amount(0)==0&&p::reduced_amount(1)==1&&p::reduced_amount(20)==17&&p::reduced_amount(32)==27&&p::reduced_amount(40)==34&&p::reduced_amount(128)==109);
 CHECK(p::normal_budget(0)==38&&p::normal_budget(1)==48&&p::normal_budget(12)==153&&p::normal_budget(100)==153);
 const U32 wanted[]={0,2,6,10,10,10,10,10};for(U32 i=0;i<std::size(wanted);i++)CHECK(p::raid_count(i)==wanted[i]);
 CHECK(p::raid_count(4,3)==17);
}
inline void begin(U32 mission=106){wave_target_tests::begin(mission);g.applied=true;g.growth={};g.growth.wire_version=2;rework_waves::reset();CHECK(rework_waves::enabled());}
inline void advance_second(U32 second){game.frame_count=second*24;game.elapsed_seconds=second;rework_waves::tick(true,false,false);wave_targeting::step(true,false);}
inline bool marching(bw::Unit* u){return u->order==(wave_targeting::detector(u)?6u:14u);}
inline U32 expected_normal_budget(U32 raw,const sc1_native::campaign_wave_config::Origin* origin){
 const U32 total=p::normal_amount(p::reduced_amount(raw));
 CHECK(origin);
 const bool air=sc1_native::wave_progression::air_only_unit(std::uint16_t(origin->unit1))&&sc1_native::wave_progression::air_only_unit(std::uint16_t(origin->unit2));
 if(!air)return total;
 const U32 detector=std::max(1u,original_stat({0,46,p::detector(origin->race)}));
 CHECK(total>detector);
 return detector+U32((std::uint64_t(total-detector)*80u+50u)/100u);
}
inline void all_missions_actual_adapter_departures(){
 U32 audited=0;
 for(const auto& profile:p::kProfiles){if(!profile.enabled)continue;begin(profile.mission);
  const sc1_native::campaign_wave_config::Origin* origin=nullptr;
  for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==profile.mission){origin=&o;break;}CHECK(origin);
  const U32 hq_id=g.mission->race==0?131u:g.mission->race==2?154u:106u,worker_id=g.mission->race==0?41u:g.mission->race==2?64u:7u;
  auto hq=add(hq_id,player_owner(),origin->target.x,origin->target.y);hq->flags=1;
  auto worker=add(worker_id,player_owner(),origin->target.x+32,origin->target.y);worker->flags=1;
  auto aa=add(0,player_owner(),origin->target.x+64,origin->target.y);aa->flags=1;
  const auto baseline=count;const auto first=std::max(profile.first,profile.base_grace);
  for(U32 second=0;second<first-4;second++){advance_second(second);CHECK(count==baseline);}
  advance_second(first-4);CHECK(count>baseline);const auto first_count=count-baseline;
  const auto first_budget=expected_normal_budget(p::normal_budget(0,profile.mission),rework_waves::primary);
  CHECK(rework_waves::live_supply()<=first_budget&&rework_waves::live_supply()>=first_budget-5);
  for(std::size_t i=baseline;i<count;i++){CHECK(rework_curses::appearing(&units[i]));CHECK(units[i].order==23);}
  for(U32 second=first-3;second<=first;second++)advance_second(second);
  CHECK(rework_waves::timeline.ordinal==1&&rework_waves::timeline.next==first+profile.interval);
  for(std::size_t i=baseline;i<count;i++){CHECK(!rework_curses::appearing(&units[i]));CHECK(marching(&units[i]));if(!wave_targeting::detector(&units[i]))CHECK(units[i].order_target.x==hq->flingy.position.x&&units[i].order_target.y==hq->flingy.position.y);
   // A real engine moves the departed army. Free its origin cells before the
   // second warning, keeping that army alive for shared supply accounting.
   units[i].flingy.position={std::int16_t(origin->target.x+64),std::int16_t(origin->target.y+64)};}
  const auto after_first=count;
  U32 second_budget=0;
  for(U32 second=first+1;second<=first+profile.interval;second++){
   advance_second(second);
   if(second==first+profile.interval-4)second_budget=expected_normal_budget(p::normal_budget(1,profile.mission),rework_waves::primary);
  }
  CHECK(rework_waves::timeline.ordinal==2&&count>after_first);
  const auto both_budgets=first_budget+second_budget;
  CHECK(second_budget&&rework_waves::live_supply()<=both_budgets&&rework_waves::live_supply()>=both_budgets-10);
  for(std::size_t i=after_first;i<count;i++)CHECK(!rework_curses::appearing(&units[i])&&marching(&units[i]));
  std::printf("AUDIT mission=%u first=%u interval=%u first_units=%zu repeat_units=%zu half_supply=%u attack_orders=ok\n",profile.mission,first,profile.interval,first_count,count-after_first,rework_waves::live_supply());++audited;
 }
 CHECK(audited>0);
}
inline void occupied_cells_and_original_assault_clock(){
 begin();auto enemy=add(37,4,2000,2000);CHECK(rework_waves::clear_cell(2032,2032));CHECK(!rework_waves::clear_cell(2039,2000));CHECK(rework_waves::clear_cell(2040,2000));
 auto hq=add(106,player_owner(),500,500);hq->flags=1;CHECK(!rework_waves::clear_cell(900,500));
 enemy->flingy.hitpoints=0;
 for(U32 i=0;i<12;i++){auto u=add(37,4,700+int(i)*20,500);u->order=14;u->order_target.unit=nullptr;}
 CHECK(!rework_waves::major_original_assault());
 for(std::size_t i=count-12;i<count;i++)units[i].ground_cooldown=1;CHECK(rework_waves::major_original_assault());
 units[count-1].flingy.hitpoints=0;CHECK(!rework_waves::major_original_assault());
 for(std::size_t i=count-12;i<count;i++){units[i].ground_cooldown=0;units[i].order=10;units[i].order_target.unit=hq;}
 units[count-1].flingy.hitpoints=2560;CHECK(rework_waves::major_original_assault());
}
inline void resource_and_neutral_origin_guards(){
 begin(108);const auto origin=rework_waves::choose_origin(false);CHECK(origin&&origin_safe(*origin));
 for(U32 id:{176u,177u,178u,188u}){auto resource=add(id,11,origin->center.x,origin->center.y);CHECK(!wave_protected_unit(resource));CHECK(origin_safe(*origin));CHECK(!rework_waves::clear_cell(origin->center.x,origin->center.y));resource->flingy.hitpoints=0;}
 auto passive=add(38,7,origin->center.x,origin->center.y);game.starting_player_types[7]=7;CHECK(!wave_protected_unit(passive)&&origin_safe(*origin));
 g.objective_units.emplace_back(passive,passive->minor_unique_index);CHECK(wave_protected_unit(passive)&&!origin_safe(*origin));g.objective_units.clear();
 game.alliances[player_owner()][7]=1;CHECK(wave_protected_unit(passive)&&!origin_safe(*origin));game.alliances[player_owner()][7]=0;
 game.starting_player_types[7]=3;CHECK(wave_protected_unit(passive)&&!origin_safe(*origin));
 passive->player=static_cast<U8>(player_owner());CHECK(wave_protected_unit(passive)&&!origin_safe(*origin));
}
inline void larger_raids_reserves_and_uncommon_stacks(){
 begin(101);rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=10;
 auto worker=add(7,player_owner(),1000,1700);worker->flags=1;add(176,11,960,1700);
 CHECK(rework_waves::count_spawn(43,p::raid_count(4),15)==10);CHECK(rework_waves::live_supply()==40);
 U32 mutas=0;living_units([&](bw::Unit* u){if(u->unit_id==43&&rework_curses::marked(u)){++mutas;CHECK(wave_targeting::distance(u->flingy.position.x,u->flingy.position.y,1000,1700)<384ll*384);CHECK(rework_curses::raid_target(u)==worker);}});CHECK(mutas==10);
 living_units([&](bw::Unit* u){if(u->unit_id==43&&rework_curses::marked(u)){wave_targeting::issue(u);CHECK(u->order==23);}});
 rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();
 living_units([&](bw::Unit* u){if(u->unit_id==43&&rework_curses::marked(u))CHECK(u->order==14&&u->order_target.x==1000&&u->order_target.y==1700);});
 for(U32 slot:{26u,27u})for(U32 stacks:{1u,2u,3u}){
  begin(101);g.growth.curse_counts[slot]=static_cast<U8>(stacks);g.growth.curse_counts[16]=2;g.current_wave_id=10;
  rework_waves::primary=rework_waves::choose_origin(true);CHECK(rework_waves::primary);rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=300*24;
  const auto& roster=p::kRosters[slot-24];CHECK(rework_waves::timeline.eligible(*rework_waves::current,roster,rework_waves::capabilities()));
  const auto initial=count;rework_waves::roster(roster);CHECK(count-initial==p::graded_amount(p::reduced_amount(p::scaled_count(roster.units[0].count*stacks,2)),roster.grade));
 }
 begin(101);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
 auto hq=add(106,player_owner(),origin->target.x,origin->target.y);hq->flags=1;add(7,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
 add(0,player_owner(),origin->target.x+64,origin->target.y)->flags=1;g.growth.curse_counts[24]=2;
 const auto second_departure=rework_waves::current->first+rework_waves::current->interval;
 for(U32 second=0;second<=second_departure;second++){
  advance_second(second);
  if(second==rework_waves::current->first){living_units([&](bw::Unit* u){if(rework_curses::marked(u))u->flingy.position={std::int16_t(origin->target.x+96),std::int16_t(origin->target.y+96)};});}
 }
 CHECK(rework_waves::timeline.ordinal==2);
 CHECK(rework_waves::reserve_at==0&&rework_waves::reserve_supply==0);
 for(U32 second=second_departure+1;second<=second_departure+15;second++)advance_second(second);
 CHECK(!rework_waves::pending_kind&&rework_waves::reserve_at==0);
 living_units([&](bw::Unit* u){const auto v=rework_curses::identity(u);CHECK(!v || v->slot!=24);});
 CHECK(!rework_waves::create(0,24)&&rework_curses::count(24)==0);

}
inline void profile_binding_and_readiness(){
 static_assert(std::size(p::kProfiles)==std::size(campaign_config::kMissions),"all original profiles are bound");
 for(const auto& m:campaign_config::kMissions){const auto profile=p::profile(m.mission_id);CHECK(profile && profile->enabled==!m.no_production);
  if(m.mission_id==404){CHECK(profile->first==360&&profile->interval==120&&profile->base_grace==360);CHECK(profile->rare==540&&profile->epic==660&&profile->legendary==780);}
  else {CHECK(profile->first>=240 && profile->first<=360);CHECK(profile->rare>=480 && profile->rare<=600);CHECK(profile->epic>=600 && profile->epic<=720);CHECK(profile->legendary>=720 && profile->legendary<=840);}}
 const p::Profile profile{1,true,false,300,120,240,480,600,720,360,480,600,0};p::Timeline t;
 for(U32 f=0;f<=1200*24;f+=24)t.advance(profile,f,true,false,false);
 CHECK(t.second()==1200 && !t.home && !t.next);
 t.advance(profile,1201*24,true,false,true);CHECK(t.next==1441 && t.ready_at==1201);
 for(U32 f=1202*24;f<=1416*24;f+=24)t.advance(profile,f,true,false,true);CHECK(!t.due(profile));
 t.advance(profile,1417*24,true,false,true);CHECK(t.due(profile));t.warn();CHECK(t.countdown(profile)==24);
 for(U32 f=1418*24;f<=1500*24;f+=24)t.advance(profile,f,true,true,true);CHECK(t.second()==1417 && t.countdown(profile)==24);
 const auto scheduled=t.next,departure=t.departure_at,ready_at=t.ready_at;
 t.advance(profile,1501*24,true,false,false);CHECK(t.home && t.next==scheduled && t.departure_at==departure);
 t.advance(profile,1502*24,true,false,true);CHECK(t.next==scheduled && t.ready_at==ready_at && t.departure_at==departure);
}
inline void reduced_auxiliary_dispatch(){
 for(U32 kind:{2u,3u}){
  begin(101);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
  add(106,player_owner(),origin->target.x,origin->target.y)->flags=1;
  add(7,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
  add(0,player_owner(),origin->target.x+64,origin->target.y)->flags=1;
  g.growth.curse_counts[20]=3;g.growth.curse_counts[15]=4;g.current_wave_id=10;
  rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;
  rework_waves::timeline.next=900;rework_waves::timeline.departure_at=604;
  rework_waves::pending_kind=kind;rework_waves::pending_spawn_at=600;
  rework_waves::primary=kind==3?rework_waves::raid_owner():rework_waves::choose_origin(true);
  const auto before=count;advance_second(0);CHECK(count>before&&rework_waves::spawned_pending);
  const auto supply=rework_waves::live_supply();
  if(kind==2){const auto budget=p::normal_amount(p::reduced_amount(34));CHECK(supply>=budget-3&&supply<=budget);}
  else {CHECK(count-before==11&&supply==41);U32 mutas=0,detectors=0;for(std::size_t i=before;i<count;i++){if(units[i].unit_id==43)++mutas;if(wave_targeting::detector(&units[i]))++detectors;}CHECK(mutas==10&&detectors==1);}
 }
}
inline void detectors_cover_their_own_army(){
 for(U32 race:{0u,1u,2u}){
  begin(101);const auto origin=rework_waves::choose_origin(true);CHECK(origin);auto own_origin=*origin;own_origin.race=race;rework_waves::primary=&own_origin;
  add(106,player_owner(),origin->target.x,origin->target.y)->flags=1;
  auto original=add(37,origin->owner,origin->target.x-96,origin->target.y);const auto untouched=*original;
  rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=55;
  const auto before=count;rework_waves::normal_units(40);bw::Unit* detector=nullptr;U32 detectors=0;
  for(std::size_t i=before;i<count;i++)if(wave_targeting::detector(&units[i])){detector=&units[i];++detectors;}
  CHECK(detectors==1&&detector->unit_id==p::detector(race));CHECK(original_stat({0,22,detector->unit_id})&0x8000u);
  CHECK(rework_waves::live_supply()<=p::normal_amount(34));CHECK(rework_waves::add_detector()==detector);
  rework_waves::timeline.active_ticks=604*24;game.frame_count=96;rework_waves::release_and_orders();CHECK(detector->order==6);
  bool follows_army=false;for(std::size_t i=before;i<count;i++)if(!wave_targeting::detector(&units[i])){auto p=units[i].flingy.position;if(detector->order_target.x==p.x&&detector->order_target.y==p.y)follows_army=true;units[i].flingy.hitpoints=0;}
  CHECK(follows_army&&std::memcmp(original,&untouched,sizeof(untouched))==0);
  const auto issued_before=wave_target_tests::issued.size();game.frame_count=192;detector->order=3;wave_targeting::issue(detector);CHECK(wave_target_tests::issued.size()==issued_before+1&&detector->order==6);
  CHECK(detector->order_target.x==origin->target.x&&detector->order_target.y==origin->target.y);
 }
}
inline void first_eligible_then_relative_cadence(){
 const p::Profile profile{1,true,true,300,120,180,480,600,720,360,480,600,0};
 for(const auto& r:p::kRosters){
  p::Timeline t;t.home=true;t.ordinal=2;t.active_ticks=900*24;if(r.slot==p::Rear || r.slot==p::Reserve){CHECK(!t.eligible(profile,r,7));continue;}CHECK(t.eligible(profile,r,7));t.mark_delivered(r.slot);CHECK(!t.eligible(profile,r,0));
  if(r.cadence>1){t.ordinal=3;CHECK(!t.eligible(profile,r,7));}
  t.ordinal=2+r.cadence;CHECK(t.eligible(profile,r,7));
  auto disabled=profile;disabled.enabled=false;CHECK(!t.eligible(disabled,r,7));
 }
 const auto& ground=p::kRosters[4];p::Timeline t;t.home=true;t.active_ticks=480*24;CHECK(t.eligible(profile,ground,7));
 t.ready_at=400;CHECK(!t.eligible(profile,ground,7));t.active_ticks=760*24;CHECK(t.eligible(profile,ground,7));
 const auto& hyperion=p::kRosters[20];t.ready_at=0;t.active_ticks=720*24;CHECK(t.eligible(profile,hyperion,7)); // first unlock wave, not 20min
 auto block=profile;block.blocked_heroes=1u<<(hyperion.slot-24);CHECK(!t.eligible(block,hyperion,7));
}
inline void no_production_never_adds_or_counts_down(){
 for(const auto& m:campaign_config::kMissions){if(!m.no_production)continue;
  wave_target_tests::begin(m.mission_id);g.applied=true;g.growth.wire_version=2;for(auto& c:g.growth.curse_counts)c=1;
  auto hq=add(106,player_owner(),500,500);hq->flags=1;auto worker=add(7,player_owner(),550,500);worker->flags=1;
  auto original=add(37,4,1600,800);const auto before=*original;const auto initial=count;
  for(U32 f=0;f<=3600*24;f+=24){game.frame_count=f;game.elapsed_seconds=f/24;rework_waves::tick(true,false,false);}
  CHECK(count==initial && rework_waves::pending_kind==0 && rework_waves::timeline.ordinal==0);
  CHECK(rework_waves::countdown(true,false).kind==sc1_native::WaveCountdown::Kind::Hidden);
  CHECK(std::memcmp(original,&before,sizeof(before))==0);
 }
}
inline void marked_passives_mirror_identity_and_preservation(){
 begin();auto original=add(0,4,1900,1700),friendly=add(0,player_owner(),200,200);const auto before=*original;const auto friendly_before=*friendly;
 for(U32 slot:{17u,18u,19u,21u,22u})g.growth.curse_counts[slot]=3;g.growth.curse_counts[23]=2;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=7;rework_waves::unit_ordinal=0;
 auto enemy=rework_waves::create(0,0);CHECK(enemy && enemy->player!=player_owner());CHECK(rework_curses::marked(enemy));
 CHECK(rework_curses::hp_percent(enemy)==217);CHECK(rework_curses::attack_percent(enemy)==170);CHECK(rework_curses::speed_percent(enemy)==148);CHECK(rework_curses::lifesteal_percent(enemy)==24);CHECK(rework_curses::barrier(enemy));
 CHECK(rework_curses::hp_percent(original)==100 && rework_curses::attack_percent(friendly)==100);CHECK(!rework_curses::marked(original) && !rework_curses::marked(friendly));
 CHECK(std::memcmp(original,&before,sizeof(before))==0 && std::memcmp(friendly,&friendly_before,sizeof(friendly_before))==0);
 const auto old_owner=enemy->player;enemy->player=static_cast<U8>(player_owner());CHECK(!rework_curses::marked(enemy));enemy->player=old_owner;++enemy->minor_unique_index;CHECK(!rework_curses::marked(enemy));
}
inline void exact_rare_and_hero_rosters(){
 CHECK(p::kRosters[14].slot==p::Raynor&&p::kRosters[14].units[0].count==2&&p::kRosters[14].units[1].count==20&&p::kRosters[14].units[2].count==4);
 CHECK(p::kRosters[4].units[0].count==2 && p::kRosters[4].units[1].count==6 && p::kRosters[4].units[2].count==4);
 CHECK(p::kRosters[5].units[0].count==4 && p::kRosters[5].units[1].count==6 && p::kRosters[5].units[2].count==2);
 CHECK(p::kRosters[6].units[0].count==4 && p::kRosters[6].units[1].count==8);CHECK(p::kRosters[7].units[0].count==2 && p::kRosters[7].units[1].count==4);
 for(const auto& r:p::kRosters){if(r.slot<38)continue;
  const p::Profile* chosen=nullptr;for(const auto& q:p::kProfiles)if(q.enabled && !(q.blocked_heroes&(1u<<(r.slot-24)))){chosen=&q;break;}CHECK(chosen);
  begin(chosen->mission);auto detector=add(9,player_owner(),500,500);detector->flags=1;auto aa=add(0,player_owner(),550,500);aa->flags=1;
  rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=900*24;rework_waves::timeline.ordinal=6;g.current_wave_id=55;
  rework_waves::primary=rework_waves::choose_origin(true);CHECK(rework_waves::primary);g.growth.curse_counts[r.slot]=1;
  const auto before=count;rework_waves::roster(r);CHECK(count>before);U32 expected=0;for(auto member:r.units)expected+=p::graded_amount(member.hero?member.count:p::reduced_amount(member.count),r.grade);
  CHECK(count-before==expected);for(std::size_t i=before;i<count;i++)CHECK(is_enemy(units[i].player) && rework_curses::marked(&units[i]));
  const auto once=count;rework_waves::roster(r);CHECK(count==once); // live hero forbids duplicate roster
 }
}
inline void death_recursion_and_stock_ammunition(){
 begin();g.growth.curse_counts[20]=1;rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;
 auto original=add(37,4,1900,1700);for(U32 i=0;i<19;i++)rework_waves::note_death(original,true);CHECK(!rework_waves::support_due);
 g.current_wave_id=9;auto added=rework_waves::create(37,0);CHECK(added);for(U32 i=0;i<30;i++)rework_waves::note_death(added,true);CHECK(!rework_waves::support_due);
 rework_waves::note_death(original,false);CHECK(!rework_waves::support_due);rework_waves::note_death(original,true);CHECK(rework_waves::support_due);
 auto carrier=add(72,4,1800,1600);carrier->secondary_order=23;carrier->current_build_slot=0;rework_waves::ammunition(carrier);CHECK(carrier->secondary_order==63 && carrier->build_queue[0]==73);
 auto child=add(73,4,1800,1600);child->remaining_build_time=30;carrier->secondary_order_target.unit=child;rework_waves::ammunition(carrier);CHECK(child->remaining_build_time==1);
 auto reaver=add(83,4,1800,1600);rework_waves::ammunition(reaver);CHECK(reaver->secondary_order==63 && reaver->build_queue[0]==85);
}
inline void arrival_transform_give_death_lifecycle(){
 begin();rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=5;
 auto duke=rework_waves::create(23,39,200,130);CHECK(duke && rework_curses::marked(duke) && rework_curses::appearing(duke));
 const auto flags=rework_curses::identity(duke)->saved_flags;auto turret=add(24,duke->player,duke->flingy.position.x,duke->flingy.position.y);duke->subunit=turret;turret->subunit=duke;
 CHECK(rework_curses::marked(turret) && rework_curses::hp_percent(turret)==200);
 auto t=existing_track(duke);CHECK(t);duke->unit_id=25;t->id=25;turret->unit_id=26;rework_curses::transformed(duke,23);
 CHECK(rework_curses::marked(duke) && rework_curses::marked(turret) && rework_curses::hp_percent(duke)==200);
 rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();CHECK(!rework_curses::appearing(duke));CHECK((duke->flags&0x04009000u)==flags);
 rework_curses::before_give(duke,duke->player);CHECK(rework_curses::marked(duke));
 rework_curses::before_give(duke,player_owner());CHECK(!rework_curses::marked(duke) && rework_curses::hp_percent(duke)==100);
 g.current_wave_id=6;auto tank=rework_waves::create(5,0,150,100);CHECK(tank);auto tank_track=existing_track(tank);tank->unit_id=30;tank_track->id=30;rework_curses::transformed(tank,5);CHECK(rework_curses::marked(tank));
 const auto arrival_flags=rework_curses::identity(tank)->saved_flags;rework_curses::forget(tank);CHECK(!rework_curses::marked(tank));CHECK((tank->flags&0x04009000u)==arrival_flags);
}
inline void special_max_two_and_counterplay_gate(){
 begin();g.current_wave_id=9;rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=900*24;rework_waves::timeline.ordinal=6;
 for(U32 slot=24;slot<50;slot++)g.growth.curse_counts[slot]=1;
 auto hq=add(106,player_owner(),500,500);hq->flags=1;auto aa=add(0,player_owner(),600,500);aa->flags=1;
 rework_waves::select_specials();CHECK(rework_waves::selected[0] && rework_waves::selected[1] && rework_waves::selected[0]!=rework_waves::selected[1]);
 // No detector means burrow/permanent-cloak rosters cannot depart even when
 // held and otherwise fully unlocked. Air requires a current anti-air unit.
 const auto& lurkers=p::kRosters[6];CHECK(!rework_waves::timeline.eligible(*rework_waves::current,lurkers,rework_waves::capabilities()));
 aa->flingy.hitpoints=0;const auto& air=p::kRosters[5];CHECK(!rework_waves::timeline.eligible(*rework_waves::current,air,rework_waves::capabilities()));
}
inline void actual_stat_damage_heal_and_renderer_scopes(){
 begin();for(U32 slot:{17u,18u,21u,22u})g.growth.curse_counts[slot]=3;g.growth.curse_counts[23]=2;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=8;
 const auto baseline=raw_value(0,8,0);auto enemy=rework_waves::create(0,0);CHECK(enemy);const auto maximum=baseline*217/100;
 CHECK(effective_max_hp(enemy)==maximum);{OwnerDatScope scoped(enemy->player,enemy->player,enemy);CHECK(raw_value(0,8,0)==maximum);}CHECK(raw_value(0,8,0)==baseline);
 max_hp_cache::publish(true);U32 rendered=0;CHECK(max_hp_cache::read_values(enemy,rendered,nullptr,nullptr) && rendered==maximum);
 auto player=add(0,player_owner(),700,700,50000);enemy->flingy.hitpoints=5000;g.normal_hit=true;g.hit_bonus=0;g.elite_hit=false;g.bullet_hit_context=false;
 owner_damage_hook(player,1000,enemy,enemy->player,1,direct_damage);CHECK(player->flingy.hitpoints==50000-1700);CHECK(enemy->flingy.hitpoints==5000+408);
 const auto enemy_before=enemy->flingy.hitpoints;owner_damage_hook(enemy,1000,player,player_owner(),1,direct_damage);CHECK(enemy->flingy.hitpoints==enemy_before-720);
 const auto original_enemy=add(0,enemy->player,1800,1700,5000);const auto untouched=original_enemy->flingy.hitpoints;
 owner_damage_hook(player,1000,original_enemy,original_enemy->player,1,direct_damage);CHECK(player->flingy.hitpoints==50000-1700-1000);CHECK(original_enemy->flingy.hitpoints==untouched);
 CHECK(effective_max_hp(original_enemy)==baseline && effective_max_hp(player)==baseline);CHECK(raw_value(0,8,0)==baseline);
}
inline void uraj_owned_air_and_kukulza_are_delivered(){
 const auto prepare=[](){
  begin(404);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
  add(154,player_owner(),origin->target.x,origin->target.y)->flags=1;
  add(64,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
  add(0,player_owner(),origin->target.x+64,origin->target.y)->flags=1;
  rework_waves::timeline.home=true;rework_waves::timeline.ready_at=134;
  rework_waves::timeline.active_ticks=610*24;rework_waves::timeline.departure_at=614;rework_waves::timeline.ordinal=2;
  rework_waves::primary=origin;g.current_wave_id=10;
  for(U32 i=0;i<233;i++){auto u=rework_waves::create(0,0);CHECK(u);u->flingy.position={1900,1552};}
  CHECK(rework_waves::live_supply()==466);
  g.current_wave_id=11;rework_waves::unit_ordinal=0;
  g.growth.curse_counts[p::Air]=g.growth.curse_counts[p::Kukulza]=1;g.growth.curse_counts[16]=3;
  rework_waves::select_specials();CHECK(rework_waves::selected[0]==p::Air&&rework_waves::selected[1]==p::Kukulza);
 };
 // Reproduce the previous dispatch order: filler fills the cap and neither
 // selected composition gets its representative unit.
 prepare();rework_waves::normal_units(p::scaled_count(p::normal_budget(2,404),3));rework_waves::selected_units();
 CHECK(!rework_waves::timeline.delivered[p::Air-24]&&!rework_waves::timeline.delivered[p::Kukulza-24]);
 prepare();const auto baseline=count;rework_waves::main_wave();U32 wraiths=0,kukulzas=0,detectors=0;
 for(std::size_t i=baseline;i<count;i++){
  const auto v=rework_curses::identity(&units[i]);CHECK(v);
  if(v->slot==p::Air&&units[i].unit_id==8)++wraiths;
  if(v->slot==p::Kukulza&&units[i].unit_id==55)++kukulzas;
  if(wave_targeting::detector(&units[i]))++detectors;
 }
 CHECK(wraiths>0&&kukulzas==2&&detectors==1&&rework_waves::live_supply()<=480);
 CHECK(rework_waves::timeline.delivered[p::Air-24]==3&&rework_waves::timeline.delivered[p::Kukulza-24]==3);
 rework_waves::timeline.active_ticks=614*24;rework_waves::release_and_orders();
 for(std::size_t i=baseline;i<count;i++)CHECK(!rework_curses::appearing(&units[i])&&marching(&units[i]));
}
inline void newly_unlocked_curses_precede_delivered_repeats(){
 begin(404);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
 add(154,player_owner(),origin->target.x,origin->target.y)->flags=1;
 add(64,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
 add(0,player_owner(),origin->target.x+64,origin->target.y)->flags=1;
 rework_waves::timeline.home=true;rework_waves::timeline.ready_at=134;rework_waves::timeline.active_ticks=610*24;
 rework_waves::timeline.departure_at=614;rework_waves::timeline.ordinal=2;rework_waves::timeline.cursor=1;
 for(U32 slot:{p::Rear,p::Heavy,p::Air,p::Kukulza})g.growth.curse_counts[slot]=1;
 rework_waves::timeline.delivered[p::Rear-24]=rework_waves::timeline.delivered[p::Heavy-24]=1;
 rework_waves::select_specials();CHECK(rework_waves::selected[0]==p::Air&&rework_waves::selected[1]==p::Kukulza);
 CHECK(rework_waves::timeline.unlock_second(*rework_waves::current,p::kRosters[p::Air-24])==540);
 CHECK(rework_waves::timeline.unlock_second(*rework_waves::current,p::kRosters[p::Kukulza-24])==540);
}
inline void uraj_completed_nexus_clock_and_auxiliary_grace(){
 for(U32 completed:{120u,900u}){
  begin(404);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
  auto nexus=add(154,player_owner(),origin->target.x,origin->target.y);nexus->flags=0;
  add(64,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
  add(0,player_owner(),origin->target.x+64,origin->target.y)->flags=1;
  auto original=add(0,origin->owner,origin->target.x+800,origin->target.y+800);
  const auto baseline=count;g.growth.curse_counts[15]=1;g.growth.curse_counts[20]=1;
  for(U32 second=0;second<completed;second++){advance_second(second);CHECK(count==baseline&&!rework_waves::timeline.home);}
  nexus->flags=1;advance_second(completed);const auto first=completed+360;
  CHECK(rework_waves::timeline.ready_at==completed&&rework_waves::timeline.next==first&&rework_waves::opening_second()==first);
  for(U32 second=completed+1;second<first-24;second++){
   rework_waves::support_due=true;advance_second(second);CHECK(count==baseline&&!rework_waves::pending_kind);
  }
  rework_waves::support_due=false;
  for(U32 i=0;i<20;i++)rework_waves::note_death(original,true);
  CHECK(!rework_waves::support_due&&rework_waves::support_kills==0);
  advance_second(first-24);CHECK(rework_waves::pending_kind==1&&rework_waves::timeline.departure_at==first);
  for(U32 second=first-23;second<first-4;second++){advance_second(second);CHECK(count==baseline);}
  advance_second(first-4);CHECK(count>baseline);
  for(std::size_t i=baseline;i<count;i++)CHECK(rework_curses::appearing(&units[i]));
  for(U32 second=first-3;second<=first;second++)advance_second(second);
  CHECK(rework_waves::timeline.ordinal==1&&rework_waves::timeline.next==first+120);
  for(std::size_t i=baseline;i<count;i++){CHECK(!rework_curses::appearing(&units[i]));units[i].flingy.position={std::int16_t(origin->target.x+96),std::int16_t(origin->target.y+96)};}
  g.growth.curse_counts[15]=g.growth.curse_counts[20]=0;const auto after_first=count;
  for(U32 second=first+1;second<first+116;second++){advance_second(second);CHECK(count==after_first);}
  for(U32 second=first+116;second<=first+120;second++)advance_second(second);
  CHECK(count>after_first&&rework_waves::timeline.ordinal==2&&rework_waves::timeline.next==first+240);
 }
}
inline void uraj_shared_cap_and_capped_growth(){
 CHECK(p::normal_budget(0,404)==19&&p::normal_budget(1,404)==24&&p::normal_budget(4,404)==38&&p::normal_budget(100,404)==38);
 CHECK(p::live_supply_cap(404)==480&&p::live_supply_cap(403)==480);
 begin(404);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
 add(154,player_owner(),origin->target.x,origin->target.y)->flags=1;
 add(64,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
 auto original=add(0,origin->owner,origin->target.x+700,origin->target.y+700);const auto untouched=*original;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=1200*24;g.current_wave_id=9;
 for(U32 i=0;i<240;i++){auto u=rework_waves::create(0,26);CHECK(u);u->flingy.position={1900,1552};}
 CHECK(rework_waves::live_supply()==480);
 for(U32 slot:{0u,15u,20u,24u,25u,38u})CHECK(!rework_waves::create(0,slot));
 CHECK(std::memcmp(original,&untouched,sizeof(untouched))==0);
 living_units([&](bw::Unit* u){if(rework_curses::marked(u))u->flingy.hitpoints=0;});
 CHECK(rework_waves::live_supply()==0&&!rework_waves::create(0,24)&&rework_waves::create(0,26));
}
inline void native_caster_orders_and_original_hero_exclusion(){
 begin(101);rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;g.current_wave_id=8;
 auto original=add(79,4,1800,1600);original->energy=200*256;const auto before=*original;
 auto caster=rework_waves::create(79,43);CHECK(caster);const auto pos=caster->flingy.position;
 auto a=add(0,player_owner(),pos.x+120,pos.y);a->flags=1;auto b=add(0,player_owner(),pos.x+140,pos.y+20);b->flags=1;
 bw::SpriteScr visible{};visible.visibility_mask=U8(1u<<caster->player);a->flingy.sprite=b->flingy.sprite=&visible;enemy_progression::research(caster->player,19);
 game.frame_count=96;rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();CHECK(caster->order==142 && rework_curses::identity(caster)->last_spell==96);
 CHECK(std::memcmp(original,&before,sizeof(before))==0);const auto previous=orders;game.frame_count=120;rework_waves::release_and_orders();CHECK(orders==previous);
 // A type reference owned by anybody in the original CHK conservatively
 // removes its hero composition. It cannot be made safe by a tag alone.
 const p::Profile* blocked=nullptr;const auto& hyperion=p::kRosters[20];for(const auto& q:p::kProfiles)if(q.enabled && (q.blocked_heroes&(1u<<(hyperion.slot-24)))){blocked=&q;break;}CHECK(blocked);
 begin(blocked->mission);rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=900*24;rework_waves::timeline.ordinal=6;rework_waves::primary=rework_waves::choose_origin(true);CHECK(rework_waves::primary);
 const auto initial=count;rework_waves::roster(hyperion);CHECK(count==initial);
}
}
inline void economy_loss_never_cancels_scheduled_waves(){
 using namespace rework_wave_tests;
 U32 missions=0;
 for(const auto& profile:p::kProfiles){if(!profile.enabled)continue;++missions;
  for(U32 loss_before:{25u,12u,2u}){
   begin(profile.mission);const auto origin=rework_waves::choose_origin(false);CHECK(origin);
   const U32 hq_id=g.mission->race==0?131u:g.mission->race==2?154u:106u,worker_id=g.mission->race==0?41u:g.mission->race==2?64u:7u;
   auto hq=add(hq_id,player_owner(),origin->target.x,origin->target.y);hq->flags=1;
   auto worker=add(worker_id,player_owner(),origin->target.x+32,origin->target.y);worker->flags=1;
   add(0,player_owner(),origin->target.x+64,origin->target.y)->flags=1;
   const auto first=std::max(profile.first,profile.base_grace);U32 first_units=0;
   for(U32 second=0;second<=first+profile.interval;second++){
    if(second==first-loss_before){hq->flingy.hitpoints=0;worker->flingy.hitpoints=0;CHECK(!rework_waves::usable_home());}
    if(second==first+30){add(hq_id,player_owner(),origin->target.x,origin->target.y)->flags=1;add(worker_id,player_owner(),origin->target.x+32,origin->target.y)->flags=1;}
    advance_second(second);CHECK(rework_waves::timeline.home&&rework_waves::timeline.ready_at==0);
    CHECK(rework_waves::countdown(true,false).kind==sc1_native::WaveCountdown::Kind::Scheduled);
    if(second<first)CHECK(rework_waves::timeline.next==first);
    if(second==first-24)CHECK(rework_waves::pending_kind==1&&rework_waves::timeline.departure_at==first);
    if(second==first){
     CHECK(rework_waves::timeline.ordinal==1&&rework_waves::timeline.next==first+profile.interval);
     living_units([&](bw::Unit* u){if(!rework_curses::marked(u))return;++first_units;CHECK(!rework_curses::appearing(u)&&marching(u));u->flingy.position={std::int16_t(origin->target.x+96),std::int16_t(origin->target.y+96)};});
     CHECK(first_units>0);
    }
    if(second>first&&second<first+profile.interval)CHECK(rework_waves::timeline.next==first+profile.interval);
   }
   CHECK(rework_waves::timeline.ordinal==2&&rework_waves::timeline.next==first+2*profile.interval);
   U32 total=0;living_units([&](bw::Unit* u){if(rework_curses::marked(u))++total;});CHECK(total>first_units);
  }
 }
 CHECK(missions>0);
}
inline void qa78_dispatch_preserves_blocked_units_and_special_priority(){
 using namespace rework_wave_tests;
 begin(308);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
 add(154,player_owner(),origin->target.x,origin->target.y)->flags=1;
 add(64,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
 add(66,player_owner(),origin->target.x+64,origin->target.y)->flags=1;
 add(84,player_owner(),origin->target.x+96,origin->target.y)->flags=1;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=1200*24;rework_waves::timeline.ordinal=8;
 rework_waves::primary=origin;g.current_wave_id=41;rework_waves::selected={p::Lurkers,p::Alliance};
 g.growth.curse_counts[p::Lurkers]=g.growth.curse_counts[p::Alliance]=1;
 const auto baseline=count;fail_spawn=true;rework_waves::main_wave();CHECK(count==baseline&&!rework_waves::deferred.empty());
 CHECK(rework_waves::timeline.delivered[p::Lurkers-24]==0&&rework_waves::timeline.delivered[p::Alliance-24]==0);
 const auto requested=rework_waves::deferred.size();CHECK(requested>20);fail_spawn=false;
 g.current_wave_id=99;rework_waves::primary=nullptr;rework_waves::timeline.ordinal=9;
 for(U32 sec=1201;sec<1230&&!rework_waves::deferred.empty();sec++){
  rework_waves::timeline.active_ticks=sec*24;rework_waves::retry_dispatch();
  CHECK(g.current_wave_id==99&&rework_waves::primary==nullptr&&rework_waves::live_supply()<=480);
  for(std::size_t i=baseline;i<count;i++){const auto v=rework_curses::identity(&units[i]);CHECK(v&&v->wave==41);units[i].flingy.position={std::int16_t(origin->target.x+128),std::int16_t(origin->target.y+128)};}
 }
 CHECK(rework_waves::deferred.empty()&&count-baseline==requested);
 CHECK(wave_targeting::detector(&units[baseline])&&rework_curses::identity(&units[baseline+1])->slot==p::Lurkers);
 CHECK(rework_waves::timeline.delivered[p::Lurkers-24]==9&&rework_waves::timeline.delivered[p::Alliance-24]==9);
 const auto once=count;rework_waves::retry_dispatch();CHECK(count==once);
 rework_waves::collecting=true;fail_spawn=true;CHECK(rework_waves::request_spawn(65,0));rework_waves::collecting=false;
 rework_waves::timeline.active_ticks=1231*24;rework_waves::retry_dispatch();CHECK(rework_waves::deferred.empty());fail_spawn=false;
 std::printf("QA78_DISPATCH mission=308 preserved=%zu duplicated=0 expiry=bounded\n",requested);
}
inline constexpr std::size_t rework_wave_group_count=24;
inline void run_rework_wave_groups(){
 qa78_dispatch_preserves_blocked_units_and_special_priority();
 economy_loss_never_cancels_scheduled_waves();
 CHECK(std::strcmp(rework_waves::warning_text(1),rework_waves::warning_text(2))==0);
 CHECK(std::strstr(rework_waves::warning_text(1),"공세"));
 CHECK(std::strstr(rework_waves::warning_text(3),"일꾼 기습"));
 CHECK(std::strcmp(rework_waves::warning_text(1),rework_waves::warning_text(3))!=0);
 rework_wave_tests::qa_stack_counts_and_wave_budgets();
 rework_wave_tests::reduced_auxiliary_dispatch();
 rework_wave_tests::detectors_cover_their_own_army();
 rework_wave_tests::resource_and_neutral_origin_guards();
 rework_wave_tests::all_missions_actual_adapter_departures();rework_wave_tests::occupied_cells_and_original_assault_clock();rework_wave_tests::larger_raids_reserves_and_uncommon_stacks();
 rework_wave_tests::profile_binding_and_readiness();rework_wave_tests::first_eligible_then_relative_cadence();
 rework_wave_tests::no_production_never_adds_or_counts_down();rework_wave_tests::marked_passives_mirror_identity_and_preservation();
 rework_wave_tests::exact_rare_and_hero_rosters();rework_wave_tests::death_recursion_and_stock_ammunition();
 rework_wave_tests::arrival_transform_give_death_lifecycle();rework_wave_tests::special_max_two_and_counterplay_gate();
 rework_wave_tests::actual_stat_damage_heal_and_renderer_scopes();
 rework_wave_tests::native_caster_orders_and_original_hero_exclusion();
 rework_wave_tests::uraj_shared_cap_and_capped_growth();
 rework_wave_tests::uraj_completed_nexus_clock_and_auxiliary_grace();
 rework_wave_tests::uraj_owned_air_and_kukulza_are_delivered();
 rework_wave_tests::newly_unlocked_curses_precede_delivered_repeats();
}
}
