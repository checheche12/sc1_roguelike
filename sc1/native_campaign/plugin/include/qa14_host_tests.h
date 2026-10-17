#pragma once
namespace host_test {
inline constexpr std::size_t qa14_group_count=2;
inline void qa14_rear_real_counts_and_departure_boundary(){
 namespace p=sc1_native::rework_wave;
 const auto& roster=p::kRosters[p::Rear-24];CHECK(roster.cadence==1);
 for(U32 race:{0u,1u,2u})for(U32 departure:{1199u,1200u}){
  rework_wave_tests::begin(101);auto source=rework_waves::choose_origin(true);CHECK(source);
  auto primary=*source;primary.race=race;rework_waves::primary=&primary;
  rework_waves::timeline.home=true;rework_waves::timeline.ordinal=1;
  rework_waves::timeline.active_ticks=(departure-4)*24;rework_waves::timeline.departure_at=departure;
  g.growth.curse_counts[p::Rear]=1;g.current_wave_id=10;
  const auto before=count;rework_waves::roster(roster);CHECK(count-before==(departure==1200?15u:10u));
  for(std::size_t i=before;i<count;i++){CHECK(units[i].unit_id==(race==0?37u:race==2?65u:0u));CHECK(rework_curses::marked(&units[i]));CHECK(rework_curses::identity(&units[i])->slot==p::Rear);}
 }
 const p::Profile profile{1,true,true,300,120,180,480,600,720,360,480,600,0};
 p::Timeline t;t.home=true;t.active_ticks=600*24;CHECK(!t.eligible(profile,roster,7));
 for(U32 ordinal=1;ordinal<=5;ordinal++){t.ordinal=ordinal;CHECK(t.eligible(profile,roster,7));t.mark_delivered(p::Rear);}
 CHECK(p::reduced_amount(p::scaled_count(p::stacked_count(12,3),3))==44);
 CHECK(p::reduced_amount(p::scaled_count(p::stacked_count(18,3),3))==66);
}
inline void qa14_garrisons_do_not_become_plugin_wave_members(){
 namespace p=sc1_native::rework_wave;
 rework_wave_tests::begin(101);auto source=rework_waves::choose_origin(true);CHECK(source);rework_waves::primary=source;
 auto guard=add(37,source->owner,source->center.x+320,source->center.y);guard->flags=1;guard->order=2;
 const auto saved=*guard;g.current_wave_id=44;g.growth.curse_counts[p::Rear]=1;
 g.growth.curse_counts[p::Attack]=3;g.growth.curse_counts[p::Health]=3;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;rework_waves::timeline.ordinal=1;
 CHECK(!rework_curses::marked(guard));CHECK(rework_waves::live_supply()==0);
 rework_waves::roster(p::kRosters[p::Rear-24]);CHECK(count>1);CHECK(rework_curses::hp_percent(guard)==100&&rework_curses::attack_percent(guard)==100);
 CHECK(!existing_track(guard)||!existing_track(guard)->spawned);
 game.frame_count=96;rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();
 CHECK(std::memcmp(guard,&saved,sizeof(saved))==0);CHECK(!rework_curses::identity(guard));
 for(U32 slot=25;slot<=49;slot++)g.growth.curse_counts[slot]=1;
 rework_waves::timeline.ordinal=8;rework_waves::timeline.active_ticks=1800*24;rework_waves::select_specials();
 static_assert(std::size(rework_waves::selected)==2,"retain two-special limit");
 CHECK(rework_waves::selected[0]&&rework_waves::selected[1]&&rework_waves::selected[0]!=rework_waves::selected[1]);
}
inline void run_qa14_groups(){qa14_rear_real_counts_and_departure_boundary();qa14_garrisons_do_not_become_plugin_wave_members();}
}
