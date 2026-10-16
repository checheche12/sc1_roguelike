#pragma once
namespace host_test {
inline void enemy_spell_dense_battle_performance(){
 using namespace enemy_progression_tests;
 begin();ep::research(4,19);
 for(U32 i=0;i<32;i++)CHECK(caster(67));
 for(U32 i=0;i<784;i++)CHECK(target(0,1940+int(i%8)*8,1544+int(i%15)*8));
 for(U32 i=0;i<784;i++){auto u=add(37,4,1950+int(i%4)*4,1580+int(i%8)*4);CHECK(u);u->flags=1;}
 CHECK(count==1600);host_unit_scans=host_unit_visits=0;
 LARGE_INTEGER frequency{},start{},end{};QueryPerformanceFrequency(&frequency);QueryPerformanceCounter(&start);
 rework_waves::release_and_orders();
 QueryPerformanceCounter(&end);
 const double milliseconds=double(end.QuadPart-start.QuadPart)*1000.0/double(frequency.QuadPart);
 std::printf("PERF enemy_spell {\"units\":1600,\"casters\":32,\"global_scans\":%llu,\"unit_visits\":%llu,\"milliseconds\":%.3f}\n",
  static_cast<unsigned long long>(host_unit_scans),static_cast<unsigned long long>(host_unit_visits),milliseconds);
 for(std::size_t i=0;i<32;i++)CHECK(units[i].order==14); // Mixed armies: no friendly-fire storm.
 CHECK(host_unit_scans<=2&&host_unit_visits<200000);
}
inline void enemy_spell_budget_has_no_caster_starvation(){
 using namespace enemy_progression_tests;
 begin();ep::research(4,19);
 for(U32 i=0;i<128;i++)CHECK(caster(67));
 target();target(0,1960,1620);auto friend_unit=add(37,4,1940,1600);friend_unit->flags=1;
 for(U32 frame=96;frame<128;frame++){
  game.frame_count=frame;rework_waves::release_and_orders();U32 scanned=0;
  for(U32 i=0;i<128;i++)if(rework_curses::identity(&units[i])->last_scan==frame)++scanned;
  CHECK(scanned==rework_waves::spell_search::casters_per_frame);
 }
 for(U32 i=0;i<128;i++)CHECK(rework_curses::identity(&units[i])->last_scan>=96);
}
inline void enemy_spell_spatial_cache_revalidates_identity_and_frame(){
 using namespace enemy_progression_tests;
 begin();auto a=target(),b=target(0,1960,1620);
 const auto count_near=[](){U32 found=0;rework_waves::spell_search::nearby(1950,1600,128,[&](bw::Unit*){++found;return true;});return found;};
 CHECK(count_near()==2);a->flingy.hitpoints=0;CHECK(count_near()==1);
 ++b->minor_unique_index;CHECK(count_near()==0);++game.frame_count;CHECK(count_near()==1);
 b->flingy.position={3000,3000};CHECK(count_near()==0);++game.frame_count;CHECK(count_near()==0);
 rework_waves::reset_spells();CHECK(!rework_waves::spell_search::initialized);
}
inline constexpr std::size_t enemy_performance_group_count=3;
inline void run_enemy_performance_groups(){enemy_spell_dense_battle_performance();enemy_spell_budget_has_no_caster_starvation();enemy_spell_spatial_cache_revalidates_identity_and_frame();}
}
