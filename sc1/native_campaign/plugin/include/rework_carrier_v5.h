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
inline U32 capacity(const bw::Unit* u) noexcept {const auto base=original_capacity(u);return own(u) && rework_catalog::rank(g.growth,130)?std::min(24u,base+talent_power::v5(130,4)):base;}
struct CountMask {
 Identity who{};U8 inside=0,outside=0;bool masked=false;
 explicit CountMask(bw::Unit* u,bool native_already_eight) noexcept {
  if(!own(u) || !rework_catalog::rank(g.growth,130) || (!native_already_eight&&!talent_power::enabled))return;
  const auto actual=census(u);if(!actual.valid || actual.inside!=u->unit_specific.bytes[16] || actual.outside!=u->unit_specific.bytes[17])return;
  who=identity(u);inside=U8(actual.inside);outside=U8(actual.outside);U32 remove=talent_power::enabled?capacity(u)-8:4u;
  const auto a=std::min(remove,U32(inside));u->unit_specific.bytes[16]=U8(inside-a);remove-=a;u->unit_specific.bytes[17]=U8(outside-std::min(remove,U32(outside)));masked=true;
 }
 void restore() noexcept {if(!masked || !same(who))return;const auto actual=census(who.p);who.p->unit_specific.bytes[16]=actual.valid?U8(actual.inside):inside;who.p->unit_specific.bytes[17]=actual.valid?U8(actual.outside):outside;masked=false;}
};
inline U32 scope_depth=0;
struct TrainingScope {
 CountMask mask;rework_upgrade_storage::View upgrade;bool active=false;
 explicit TrainingScope(bw::Unit* u) noexcept :mask(u,own(u) && original_capacity(u)==8 && scope_depth==0 && u->secondary_order==63 && rework_upgrade_storage::slot(u->player,43)){
  if(!own(u) || !rework_catalog::rank(g.growth,130) || u->secondary_order!=63 || scope_depth)return;
  if(!upgrade.begin(u->player,43,1))return;active=true;++scope_depth;
 }
 ~TrainingScope(){mask.restore();if(active){upgrade.restore();--scope_depth;}}
};
struct CommandScope {
 std::vector<CountMask> masks;rework_upgrade_storage::View upgrade;bool active=false;
 CommandScope(U32 player,const void* data,U32 length){
  if(!g.active || !g.applied || player!=player_owner() || !rework_catalog::rank(g.growth,130) || scope_depth || !data || length!=1 || *static_cast<const U8*>(data)!=0x27)return;
  if(!rework_upgrade_storage::slot(player,43))return;const auto original=rework_upgrade_storage::level(player,43);
  // Native TrainFighter keeps its original five-entry queue, resource checks,
  // payment, construction time, child creation and hangar linkage. Only its
  // hardcoded4/8 capacity predicate receives this temporary count view.
  living_units([&](bw::Unit* u){if(own(u))masks.emplace_back(u,u->unit_id==82 || original!=0);});
  if(!upgrade.begin(player,43,1))return;active=true;++scope_depth;
 }
 ~CommandScope(){for(auto& mask:masks)mask.restore();if(active){upgrade.restore();--scope_depth;}}
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
inline void reset() noexcept {launches.clear();scope_depth=0;}
inline void forget(bw::Unit* u) noexcept {if(valid_unit(u) && launches.size()==g.units_count)launches[static_cast<std::size_t>(u-g.units)]={};}
}
