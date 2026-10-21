#pragma once
namespace host_test { namespace qa50_air_tests {
namespace p=sc1_native::rework_wave;
inline std::vector<U32> plan(U32 race,bool air,U32 second,U32 ordinal,U32 budget){
 std::vector<U32> result;U32 used=0;
 for(U32 i=0;i<480&&used<budget;i++){
  const auto next=sc1_native::wave_progression::select(race,air,second,ordinal,i,budget-used,wave_supply,true);
  if(!next.valid)break;result.push_back(next.unit_id);used+=next.supply;
 }
 return result;
}
inline void dispatch_matches_reduced_air_and_exact_legacy_ground(){
 for(U32 race:{0u,1u,2u})for(bool air:{false,true})for(U32 second:{300u,600u,900u})for(U32 stacks:{0u,1u}){
  rework_wave_tests::begin(101);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
  auto primary=*origin;primary.race=race;
  const U32 seed=air?(race==0?43u:race==1?8u:70u):(race==0?37u:race==1?0u:65u);
  primary.unit1=primary.unit2=seed;rework_waves::primary=&primary;
  auto aa=add(0,player_owner(),origin->target.x,origin->target.y);aa->flags=1;
  auto original=add(37,primary.owner,origin->target.x+200,origin->target.y+200);const auto untouched=*original;
  rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=second*24;
  rework_waves::timeline.ordinal=second==900?12u:0u;g.current_wave_id=17;g.growth.curse_counts[16]=static_cast<U8>(stacks);
  const auto raw=p::scaled_count(38,stacks);
  const auto detector_cost=std::max(1u,original_stat({0,46,p::detector(race)}));
  const auto legacy_budget=p::normal_amount(p::reduced_amount(raw))-detector_cost;
  const auto combat_budget=air?U32((std::uint64_t(legacy_budget)*80u+50u)/100u):legacy_budget;
  const auto legacy=plan(race,air,second,rework_waves::timeline.ordinal,legacy_budget);
  const auto expected=plan(race,air,second,rework_waves::timeline.ordinal,combat_budget);
  const auto before=count;rework_waves::normal_units(raw);std::vector<U32> actual;U32 detectors=0,combat_supply=0;
  for(std::size_t i=before;i<count;i++){
   auto u=&units[i];CHECK(rework_curses::marked(u)&&rework_curses::appearing(u));
   if(wave_targeting::detector(u)){++detectors;CHECK(u->unit_id==p::detector(race));}
   else {actual.push_back(u->unit_id);combat_supply+=wave_supply(u->unit_id);if(air)CHECK(original_stat({0,22,u->unit_id})&4u);}
  }
  CHECK(actual==expected&&detectors==1&&combat_supply<=combat_budget);
  if(air)CHECK(actual.size()<legacy.size());else CHECK(actual==legacy);
  CHECK(std::memcmp(original,&untouched,sizeof(untouched))==0);
  rework_waves::timeline.active_ticks+=4*24;rework_waves::release_and_orders();
  for(std::size_t i=before;i<count;i++)CHECK(!rework_curses::appearing(&units[i])&&rework_wave_tests::marching(&units[i]));
  std::printf("QA50_BASIC race=%u air=%u second=%u stacks=%u legacy_units=%zu actual_units=%zu combat_half_supply=%u detector_count=%u\n",race,air?1u:0u,second,stacks,legacy.size(),actual.size(),combat_supply,detectors);
 }
}
inline void air_reduction_once_after_stacking_and_support_budget(){
 for(U32 raw:{18u,34u,128u}){
  rework_wave_tests::begin(101);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
  auto primary=*origin;primary.race=0;primary.unit1=primary.unit2=43;rework_waves::primary=&primary;
  add(0,player_owner(),origin->target.x,origin->target.y)->flags=1;
  rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=300*24;g.current_wave_id=18;
  const auto total=p::normal_amount(p::reduced_amount(raw));
  const auto cost=std::max(1u,original_stat({0,46,42}));
  const auto expected=plan(0,true,300,0,U32((std::uint64_t(total-cost)*80u+50u)/100u));
  const auto before=count;rework_waves::normal_units(raw);U32 combat=0,detectors=0;
  for(std::size_t i=before;i<count;i++){if(wave_targeting::detector(&units[i]))++detectors;else ++combat;}
  CHECK(combat==expected.size()&&detectors==1);
 }
 rework_wave_tests::begin(101);const auto origin=rework_waves::choose_origin(true);CHECK(origin);
 auto primary=*origin;primary.race=0;primary.unit1=primary.unit2=43;rework_waves::primary=&primary;
 auto aa=add(0,player_owner(),origin->target.x,origin->target.y);aa->flags=1;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=300*24;g.current_wave_id=19;g.growth.curse_counts[16]=3;
 rework_waves::main_wave();const auto raw=p::scaled_count(p::normal_budget(0,101),3);
 CHECK(rework_waves::last_main_budget==raw);
 const auto cost=std::max(1u,original_stat({0,46,42}));
 const auto total=p::normal_amount(p::reduced_amount(raw));
 const auto expected=plan(0,true,300,0,U32((std::uint64_t(total-cost)*80u+50u)/100u));
 U32 combat=0;living_units([&](bw::Unit* u){if(rework_curses::marked(u)&&!wave_targeting::detector(u))++combat;});
 CHECK(combat==expected.size());
 // Air-only armies still wait for real anti-air. Detection is not spawned
 // by a blocked dispatch, and a ground primary remains a ground primary.
 rework_wave_tests::begin(101);rework_waves::primary=&primary;g.current_wave_id=20;
 const auto before=count;rework_waves::normal_units(38);CHECK(count==before);
}
} // namespace qa50_air_tests
inline constexpr std::size_t qa50_group_count=2;
inline void run_qa50_groups(){qa50_air_tests::dispatch_matches_reduced_air_and_exact_legacy_ground();qa50_air_tests::air_reduction_once_after_stacking_and_support_budget();}
}
