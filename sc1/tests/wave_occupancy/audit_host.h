#pragma once
#include "fixtures.generated.h"
namespace host_test { namespace installed_spawn_audit {
inline U32 normalized_homes=0;
inline void prepare(const original_spawn_fixture::Scenario& source) {
 wave_target_tests::begin(source.mission);g.applied=true;g.growth={};g.growth.wire_version=2;rework_waves::reset();
 for(U32 owner=0;owner<8;owner++){
  const U32 type=source.owners[owner];game.starting_player_types[owner]=type==5?1u:type==6?2u:type==3?3u:type==7?7u:0u;
  for(U32 other=0;other<8;other++)if(source.forces[owner]<4&&source.forces[owner]==source.forces[other]&&(source.force_flags[source.forces[owner]]&1u))game.alliances[owner][other]=1;
 }
 for(U32 index=source.offset;index<source.offset+source.count;index++){
  const auto& placed=original_spawn_fixture::units[index];auto u=add(placed.id,placed.owner,placed.x,placed.y,int(std::max(256u,original_stat({0,8,placed.id}))));CHECK(u);
  u->flags=1u|((original_stat({0,22,placed.id})&4u)?4u:0u);
  if(placed.state&2u)u->flags|=0x10u;if(placed.state&4u)u->flags|=4u;if(placed.state&8u)u->flags|=0x40000000u;if(placed.state&16u)u->flags|=0x04000000u;
 }
 refresh_units();capture_objective_units();
}
inline bool working_home() {
 if(rework_waves::usable_home())return false;
 const sc1_native::campaign_wave_config::Origin* origin=nullptr;
 for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==g.mission->mission_id){origin=&o;break;}CHECK(origin);
 bool hq=false,worker=false;living_units([&](bw::Unit* u){if(u->player!=player_owner()||!(u->flags&1u)||(u->flags&4u))return;if(wave_targeting::headquarters(u->unit_id))hq=true;if(wave_targeting::worker(u->unit_id))worker=true;});
 const U32 race=g.mission->race;
 if(!hq)add(race==0?131:race==2?154:106,player_owner(),origin->target.x,origin->target.y)->flags=1;
 if(!worker)add(race==0?41:race==2?64:7,player_owner(),origin->target.x+32,origin->target.y)->flags=1;
 CHECK(rework_waves::usable_home());return true;
}
inline void simulate_second(U32 second){game.frame_count=second*24;game.elapsed_seconds=second;rework_waves::tick(true,false,false);wave_targeting::step(true,false);}
inline void audit_all_installed_scenarios() {
 U32 pass=0,disabled=0,air_only=0;
 for(const auto& fixture:original_spawn_fixture::scenarios){
  prepare(fixture);const auto profile=sc1_native::rework_wave::profile(fixture.mission);CHECK(profile);
  if(!profile->enabled){const auto before=count;for(U32 t=0;t<100;t++)simulate_second(t);CHECK(count==before&&!rework_waves::pending_kind);++disabled;std::printf("MAP_AUDIT mission=%u disabled=1 placed=%u\n",fixture.mission,fixture.count);continue;}
  CHECK(rework_waves::enabled());const bool normalized=working_home();if(normalized)++normalized_homes;
  auto primary=rework_waves::choose_origin(true);if(!primary)primary=rework_waves::choose_origin(false);
  if(!primary){std::printf("MAP_FAIL mission=%u reason=no_safe_origin placed=%u\n",fixture.mission,fixture.count);continue;}
  const bool air=sc1_native::wave_progression::air_only_unit(std::uint16_t(primary->unit1))&&sc1_native::wave_progression::air_only_unit(std::uint16_t(primary->unit2));
  // Reproduce the installed selector's ground-only first pick against the
  // exact same origin/occupancy rules. The production fix must create an air
  // army instead on each of the five eligible air-only maps.
  if(air){++air_only;g.current_wave_id=1;
   auto legacy=sc1_native::wave_progression::select(primary->race,false,profile->first,0,0,16,wave_supply);CHECK(legacy.valid);
   const auto before=count;auto unit=rework_waves::create(legacy.unit_id,0);CHECK(!unit&&count==before);
   std::printf("LEGACY_REPRO mission=%u ground_pick=%u created=0 air_only=1\n",fixture.mission,legacy.unit_id);
  }
  simulate_second(0);const U32 first=rework_waves::timeline.next;CHECK(first);
  rework_waves::timeline.active_ticks=(first-25)*24;
  U32 now=1;const auto original_count=count;
  for(U32 t=first-24;t<=first;t++,now++)simulate_second(now);
  const auto first_units=count-original_count;
  if(!first_units){std::printf("MAP_FAIL mission=%u reason=zero_first units=%zu ordinal=%u\n",fixture.mission,first_units,rework_waves::timeline.ordinal);continue;}
  CHECK(rework_waves::timeline.ordinal==1);U32 first_supply=0;
  for(std::size_t i=original_count;i<count;i++){
   auto u=&units[i];CHECK(is_enemy(u->player)&&rework_curses::marked(u)&&!rework_curses::appearing(u)&&u->order==(wave_targeting::detector(u)?6u:14u));
   if(air)CHECK(original_stat({0,22,u->unit_id})&4u);first_supply+=wave_supply(u->unit_id);
   // Engine movement is outside a host test. Remove departed fixture units
   // from origin occupancy by moving to the actual current player target.
   u->flingy.position={std::int16_t(wave_targeting::target.x+64),std::int16_t(wave_targeting::target.y+64)};
  }
  const auto after_first=count;
  for(U32 t=0;t<profile->interval;t++,now++)simulate_second(now);
  const auto repeat_units=count-after_first;
  if(!repeat_units){std::printf("MAP_FAIL mission=%u reason=zero_repeat\n",fixture.mission);continue;}
  CHECK(rework_waves::timeline.ordinal==2);for(std::size_t i=after_first;i<count;i++)CHECK(is_enemy(units[i].player)&&rework_curses::marked(&units[i])&&!rework_curses::appearing(&units[i])&&units[i].order==(wave_targeting::detector(&units[i])?6u:14u));
  std::printf("MAP_AUDIT mission=%u disabled=0 placed=%u normalized_home=%u air=%u first_units=%zu repeat_units=%zu first_half_supply=%u\n",fixture.mission,fixture.count,normalized?1:0,air?1:0,first_units,repeat_units,first_supply);++pass;
 }
 CHECK(pass==55&&disabled==8&&air_only==5);
 std::printf("PASS installed-map spawn audit:55 enabled,8 disabled,5 air-only, normalized_homes=%u; synthetic engine callbacks only\n",normalized_homes);
}
} }
