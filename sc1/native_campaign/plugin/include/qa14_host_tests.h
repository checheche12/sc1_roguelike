#pragma once
namespace host_test {
inline constexpr std::size_t qa14_group_count=2;
inline void qa14_rear_real_counts_and_departure_boundary(){
 namespace p=sc1_native::rework_wave;
 const auto& roster=p::kRosters[p::Rear-24];
 for(U32 stacks:{1u,2u,255u})for(U32 departure:{1199u,1200u}){
  rework_wave_tests::begin(101);auto source=rework_waves::choose_origin(true);CHECK(source);
  rework_waves::primary=source;rework_waves::timeline.home=true;rework_waves::timeline.ordinal=5;
  rework_waves::timeline.active_ticks=departure*24;g.growth.curse_counts[p::Rear]=static_cast<U8>(stacks);
  const auto before=count;rework_waves::roster(roster);CHECK(count==before);
  CHECK(!rework_waves::create(0,p::Rear));CHECK(rework_curses::count(p::Rear)==0);
  CHECK(!rework_waves::timeline.eligible(*rework_waves::current,roster,7));
  rework_waves::select_specials();CHECK(rework_waves::selected[0]!=p::Rear&&rework_waves::selected[1]!=p::Rear);
 }
 using namespace sc1_native::curse_scaling;
 CHECK(bonus(1,25)==25&&bonus(2,25)==55&&bonus(3,25)==90&&bonus(4,25)==130);
 CHECK(bonus(1,10)==10&&bonus(2,10)==25&&bonus(3,10)==45&&bonus(4,10)==70);
 CHECK(bonus(0xffffffffu,25)==0xffffffffu&&scale(480,0xffffffffu)==0xffffffffu);
 rework_wave_tests::begin(101);g.growth.curse_counts[16]=255;g.growth.talent_ranks[31]=256;
 CHECK(rework_curses::count(16)==256);
 g.growth.curse_counts[17]=255;g.growth.talent_ranks[30]=1000;CHECK(rework_curses::count(17)==1000);
 CHECK(p::raid_count(1)==2&&p::raid_count(2)==6&&p::raid_count(3)==10&&p::raid_count(255)==10);
 CHECK(p::raid_count(3,1)==12&&p::raid_count(3,2)==15);
}
inline void qa14_garrisons_do_not_become_plugin_wave_members(){
 namespace p=sc1_native::rework_wave;
 rework_wave_tests::begin(101);auto source=rework_waves::choose_origin(true);CHECK(source);rework_waves::primary=source;
 auto guard=add(37,source->owner,source->center.x+320,source->center.y);guard->flags=1;guard->order=2;
 const auto saved=*guard;g.current_wave_id=44;g.growth.curse_counts[p::Heavy]=1;
 g.growth.curse_counts[p::Attack]=3;g.growth.curse_counts[p::Health]=3;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=600*24;rework_waves::timeline.ordinal=1;
 CHECK(!rework_curses::marked(guard));CHECK(rework_waves::live_supply()==0);
 rework_waves::roster(p::kRosters[p::Heavy-24]);CHECK(count>1);CHECK(rework_curses::hp_percent(guard)==100&&rework_curses::attack_percent(guard)==100);
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
