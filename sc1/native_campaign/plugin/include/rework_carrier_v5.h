#pragma once
#include "rework_upgrade_storage.h"
// Native carrier capacity and launch progress. Linked lists stay engine-owned;
// unlike transports, a carrier hangar has no eight-element passenger array.
namespace rework_carrier_v5 {
struct Census {U32 inside=0,outside=0;bool valid=false;};
struct Identity {bw::Unit* p=nullptr;U8 unique=0,owner=12;std::uint16_t type=228;};
inline Identity identity(bw::Unit* u) noexcept {return valid_unit(u)?Identity{u,u->minor_unique_index,u->player,u->unit_id}:Identity{};}
inline bool same(const Identity& i) noexcept {return valid_unit(i.p) && i.p->minor_unique_index==i.unique && i.p->player==i.owner && i.p->unit_id==i.type;}
inline bool own(const bw::Unit* u) noexcept {return valid_unit(u) && g.active && g.applied && u->player==player_owner() && (u->unit_id==72 || u->unit_id==82) && !(u->flags&0x40000000u);}
inline bw::Unit* pointer(const U8* bytes,std::size_t offset) noexcept {bw::Unit* p=nullptr;std::memcpy(&p,bytes+offset,sizeof(p));return p;}
inline Census census(const bw::Unit* carrier) noexcept {
 if(!valid_unit(carrier) || (carrier->unit_id!=72 && carrier->unit_id!=82))return {};
 Census result{};std::array<const bw::Unit*,64> seen{};U32 n=0;
 for(U32 outside=0;outside<2;outside++){
  auto child=pointer(carrier->unit_specific.bytes,outside*8);const bw::Unit* previous=nullptr;
  while(child){
   if(!valid_unit(child) || n==seen.size() || child->unit_id!=73 || child->player!=carrier->player || pointer(child->unit_specific.bytes,0)!=carrier || pointer(child->unit_specific.bytes,16)!=previous || U32(child->unit_specific.bytes[24]!=0)!=outside)return {};
   for(U32 i=0;i<n;i++)if(seen[i]==child)return {};
   seen[n++]=child;if(outside)++result.outside;else ++result.inside;previous=child;child=pointer(child->unit_specific.bytes,8);
  }
 }
 result.valid=true;return result;
}
inline U32 original_capacity(const bw::Unit* u) noexcept {return u && (u->unit_id==82 || rework_upgrade_storage::level(u->player,43))?8u:4u;}
inline U32 capacity(const bw::Unit* u) noexcept {return original_capacity(u);}
struct BurstClock {Identity who{};U32 frame=~0u;};
inline std::vector<BurstClock> bursts;
inline U32 burst_depth=0;
struct BurstScope {
 Identity who{};Census before{};bool active=false;
 explicit BurstScope(bw::Unit* u) noexcept {
  if(burst_depth || !own(u) || !rework_catalog::rank(g.growth,130))return;
  before=census(u);if(!before.valid || !before.inside || before.inside!=u->unit_specific.bytes[16] || before.outside!=u->unit_specific.bytes[17])return;
  who=identity(u);active=true;
 }
 template<class Step> void finish(Step native_order) {
  if(!active || burst_depth || !same(who) || !own(who.p) || !rework_catalog::rank(g.growth,130))return;
  auto after=census(who.p);
  // The native order must first authorize and perform a real launch. Range,
  // target, disable, Stop and Recall checks remain in that native path.
  if(!after.valid || after.inside>=before.inside || after.outside<=before.outside)return;
  if(bursts.size()!=g.units_count)bursts.assign(g.units_count,{});
  auto& clock=bursts[static_cast<std::size_t>(who.p-g.units)];const auto frame=g.game()->frame_count;
  if(same(clock.who) && clock.who.p==who.p && clock.frame==frame)return;
  clock={who,frame};struct Guard {Guard(){++burst_depth;}~Guard(){--burst_depth;}} guard;
  U32 released=after.outside-before.outside;
  while(released<8 && after.inside){
   const auto timer=who.p->order_timer,wait=who.p->order_wait,order=who.p->order;
   // StepOrder has a separate dispatcher wait (native13515 unit+0xc9).
   // It resets to eight before CarrierAttack runs; clearing order_timer
   // alone leaves every additional call blocked at that dispatcher gate.
   who.p->order_timer=0;who.p->order_wait=0;native_order();
   if(!same(who) || !own(who.p))return;
   const auto next=census(who.p);if(!next.valid)return;
   if(next.inside>=after.inside || next.outside<=after.outside){if(who.p->order==order){who.p->order_timer=timer;who.p->order_wait=wait;}return;}
   released+=next.outside-after.outside;after=next;
  }
 }
};
struct LaunchClock {Identity who{};U32 carry=0,last_frame=0;bool sampled=false;};
inline std::vector<LaunchClock> launches;
struct LaunchScope {
 Identity who{};U32 outside=0;bool active=false;
 explicit LaunchScope(bw::Unit* u) noexcept {if(own(u) && rework_catalog::rank(g.growth,136)){who=identity(u);outside=u->unit_specific.bytes[17];active=true;}}
 ~LaunchScope(){
  if(!active || !same(who) || !own(who.p) || !rework_catalog::rank(g.growth,136) || who.p->unit_specific.bytes[17]<=outside || !who.p->order_timer)return;
  if(launches.size()!=g.units_count)launches.assign(g.units_count,{});auto& clock=launches[static_cast<std::size_t>(who.p-g.units)];const auto frame=g.game()->frame_count;
  if(!same(clock.who) || clock.who.p!=who.p)clock={who,0,0,false};if(clock.sampled && clock.last_frame==frame)return;
  const U32 denominator=8+talent_power::quarters(374);const U32 total=U32(who.p->order_timer)*8+clock.carry;who.p->order_timer=U8(std::max(1u,total/denominator));clock.carry=total%denominator;clock.last_frame=frame;clock.sampled=true;
 }
};
inline void reset() noexcept {launches.clear();bursts.clear();burst_depth=0;}
inline void forget(bw::Unit* u) noexcept {if(valid_unit(u)){const auto index=static_cast<std::size_t>(u-g.units);if(launches.size()==g.units_count)launches[index]={};if(bursts.size()==g.units_count)bursts[index]={};}}
}
