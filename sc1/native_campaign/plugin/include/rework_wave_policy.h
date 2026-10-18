#pragma once
#include <algorithm>
#include <array>
#include <cstdint>
namespace sc1_native { namespace rework_wave {
using U32=std::uint32_t;
struct Profile {U32 mission;bool enabled,starting_hq;U32 first,interval,base_grace,rare,epic,legendary,rare_grace,epic_grace,legendary_grace,blocked_heroes;};
enum Slot:U32 {Raid=15,Reinforcements=16,Attack=17,Health=18,Haste=19,DeathSupport=20,Elite=21,Barrier=22,Lifesteal=23,
 Reserve=24,Rear=25,Heavy=26,Flank=27,Ground=28,Air=29,Lurkers=30,Carriers=31,Siege=32,Fleet=33,Hunters=34,Vanguard=35,
 Alliance=36,Catastrophe=37,Raynor=38,Duke=39,Fenix=40,Kukulza=41,Magellan=42,Tassadar=43,Hyperion=44,Kerrigan=45,Zeratul=46,Twilight=47,Skies=48,ThreeHeroes=49};
enum Requirement:U32 {GroundPath=1,AntiAir=2,Detection=4};
struct Member {std::uint16_t unit;U32 count;bool hero=false;};
struct Roster {U32 slot,cadence,grade,requirements,hp_percent,attack_percent;std::array<Member,6> units;};
// grade0 common/uncommon,1 rare,2 epic,3 legendary. No hero count scaling.
inline constexpr Roster kRosters[]={
 {Reserve,1,0,GroundPath,100,100,{{{0,3},{0,0},{0,0},{0,0},{0,0},{0,0}}}},
 {Rear,1,0,GroundPath,100,100,{{{0,12}}}},
 {Heavy,1,0,GroundPath,100,100,{{{3,4}}}},
 {Flank,2,0,GroundPath,100,100,{{{2,8}}}},
 {Ground,2,1,GroundPath,100,100,{{{5,2},{38,6},{66,4}}}},
 {Air,2,1,AntiAir,100,100,{{{8,4},{43,6},{70,2}}}},
 {Lurkers,3,1,GroundPath|Detection,100,100,{{{103,4},{38,8}}}},
 {Carriers,3,1,AntiAir,100,100,{{{72,2},{60,4}}}},
 {Siege,2,2,GroundPath,100,100,{{{5,4},{83,2},{38,8}}}},
 {Fleet,3,2,AntiAir,100,100,{{{12,2},{71,2},{8,4}}}},
 {Hunters,2,2,GroundPath|AntiAir,130,130,{{{38,8},{62,2}}}},
 {Vanguard,2,2,GroundPath,200,100,{{{5,2},{0,8}}}},
 {Alliance,3,3,GroundPath|AntiAir,100,100,{{{5,4},{39,2},{66,6},{43,6}}}},
 {Catastrophe,3,3,GroundPath,400,150,{{{12,1},{0,12}}}},
 {Raynor,2,1,GroundPath,100,100,{{{20,2,true},{0,20},{34,4}}}},
 {Duke,3,1,GroundPath,100,100,{{{23,1,true},{5,2},{3,4}}}},
 {Fenix,2,1,GroundPath,100,100,{{{77,1,true},{65,6},{66,4}}}},
 {Kukulza,3,1,AntiAir,100,100,{{{55,1,true},{43,6},{47,4}}}},
 {Magellan,2,2,GroundPath|AntiAir,100,100,{{{22,1,true},{3,8},{12,2}}}},
 {Tassadar,3,2,GroundPath,100,100,{{{79,1,true},{67,3},{66,6}}}},
 {Hyperion,3,3,AntiAir,100,100,{{{28,1,true},{29,1,true},{8,6},{58,2}}}},
 {Kerrigan,3,3,GroundPath,100,100,{{{51,1,true},{53,4,true},{39,2},{37,12}}}},
 {Zeratul,3,3,GroundPath|AntiAir|Detection,100,100,{{{75,1,true},{61,4},{71,1},{70,4}}}},
 {Twilight,3,3,GroundPath|AntiAir|Detection,100,100,{{{79,1,true},{75,1,true},{66,6},{72,1}}}},
 {Skies,3,3,AntiAir,100,100,{{{80,1,true},{56,1,true},{70,4},{44,3}}}},
 {ThreeHeroes,3,3,GroundPath,100,100,{{{23,1,true},{48,1,true},{78,1,true},{3,4},{38,6},{66,4}}}},
};
// Apply once to the final army size, after curse stacking. Round to the nearest
// unit/half-supply so small groups remain usable and zero stays zero.
inline constexpr U32 reduced_amount(U32 amount) noexcept {return U32((std::uint64_t(amount)*85u+50u)/100u);}
inline constexpr U32 detector(U32 race) noexcept {return race==0?42u:race==2?84u:9u;}
inline U32 scaled_count(U32 amount,U32 stacks) noexcept {return amount*(100u+15u*std::min(stacks,3u))/100u;}
inline constexpr U32 normal_budget(U32 ordinal,U32 mission=0) noexcept {return mission==404?16u+4u*std::min(ordinal,4u):32u+8u*std::min(ordinal,12u);}
inline constexpr U32 live_supply_cap(U32 mission) noexcept {return mission==404?64u:480u;}
inline U32 raid_count(U32 stacks,U32 reinforcements=0) noexcept {stacks=std::min(stacks,255u);return scaled_count(stacks*(stacks+1u),reinforcements);}
inline U32 reserve_budget(U32 main_budget,U32 stacks) noexcept {return U32(std::min<std::uint64_t>(480u,std::uint64_t(main_budget)*stacks/2u));}
inline U32 stacked_count(U32 amount,U32 stacks) noexcept {return U32(std::min<std::uint64_t>(480u,std::uint64_t(amount)*stacks));}
struct Timeline {
 bool initialized=false,had_home=false,home=false;U32 frame=0,active_ticks=0,ready_at=0,next=0,ordinal=0,warning_at=0,departure_at=0;
 U32 cursor=0;std::array<U32,26> delivered{};
 void reset() noexcept {*this={};}
 U32 second() const noexcept {return active_ticks/24u;}
 void advance(const Profile& p,U32 now,bool ready,bool blocked,bool home_ready) noexcept {
   if(!p.enabled){reset();return;}
   if(!initialized){initialized=true;frame=now;}
   const auto delta=now>=frame ? std::min(now-frame,24u):0u;frame=now;
   if(ready && !blocked)active_ticks+=delta;
   if(home_ready && !home){ready_at=second();const auto grace=(!had_home && p.starting_hq && p.mission!=101)?0u:p.base_grace;next=std::max(p.first,ready_at+grace);warning_at=departure_at=0;had_home=true;}
   home=home_ready;
   if(!home){warning_at=departure_at=0;next=0;}
 }
 bool eligible(const Profile& p,const Roster& r,U32 capabilities) const noexcept {
   if(!p.enabled || !home || (r.requirements&capabilities)!=r.requirements || (p.blocked_heroes&(1u<<(r.slot-24))))return false;
   if(r.slot==Reserve && ordinal<1)return false;
   if(r.slot==Rear && ordinal<1)return false;
   U32 nominal=r.grade==1?p.rare:r.grade==2?p.epic:r.grade==3?p.legendary:0u;
   U32 grace=r.grade==1?p.rare_grace:r.grade==2?p.epic_grace:r.grade==3?p.legendary_grace:0u;
   const auto unlock=std::max(nominal,(!p.starting_hq || ready_at)?ready_at+grace:0u);
   // Selection occurs at the warning, but eligibility belongs to the actual
   // departure. An unlock exactly on that departure joins this first wave.
   if((departure_at?departure_at:second())<unlock)return false;
   const auto last=delivered[r.slot-24];return !last || ordinal+1>=last+r.cadence;
 }
 void mark_delivered(U32 slot) noexcept {if(slot>=24 && slot<=49)delivered[slot-24]=ordinal+1;}
 bool due(const Profile& p) const noexcept {return p.enabled && home && next && second()+24>=next && !departure_at;}
 void warn() noexcept {warning_at=second();departure_at=second()+24;}
 void finished(const Profile& p) noexcept {++ordinal;next=second()+p.interval;warning_at=departure_at=0;}
 U32 countdown(const Profile& p) const noexcept {if(!p.enabled || !home)return 0;const auto due=departure_at?departure_at:next;return due>second()?due-second():0;}
};
} }
