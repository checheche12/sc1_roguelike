#pragma once
// Included inside rework_waves, after finish_created. Native orders92/112/111
// perform boarding, flight and unloading; no packed cargo or passenger
// coordinates are fabricated. Only newly created special-wave units enter.
using IslandRoute=sc1_native::island_routes::Route;
using IslandToken=rework_combat_v5::Identity;
struct IslandConvoy {IslandToken ship{};std::vector<IslandToken> passengers;const IslandRoute* route=nullptr;U32 wave=0,space=0,phase=0,started=0,last_order=0;int land_x=0,land_y=0;};
inline std::vector<IslandConvoy> island_convoys;
inline const IslandRoute* island_cached=nullptr;
inline U32 island_cache_frame=~0u,island_cache_owner=12;
inline int island_load_x=0,island_load_y=0,island_land_x=0,island_land_y=0;
inline bw::Unit* island_unit(const IslandToken& id) noexcept {return rework_combat_v5::resolve(id);}
inline void island_hold(bw::Unit* u,bool value) noexcept {if(auto v=rework_curses::identity(u))v->transport_hold=value;}
inline void reset_islands() noexcept {island_convoys.clear();island_cached=nullptr;island_cache_frame=~0u;island_cache_owner=12;}
inline bool island_slot(U32 slot) noexcept {for(const auto& r:policy::kRosters)if(r.slot==slot)return r.grade>0;return false;}
inline bool island_landing_clear(int x,int y) {
 bool clear=true;living_units([&](bw::Unit* u){if(original_stat({0,22,u->unit_id})&4u)return;const auto p=u->flingy.position;if(!(u->flags&0x40u)&&wave_targeting::distance(x,y,p.x,p.y)<40ll*40)clear=false;});return clear;
}
inline bool island_landing(const IslandRoute& route,int& x,int& y) {
 wave_targeting::refresh();if(!wave_targeting::target.valid||!rework_relocation::pathing_source)return false;
 const auto& goal=wave_targeting::target;std::int64_t best=std::numeric_limits<std::int64_t>::max();bool found=false;
 for(U32 i=0;i<route.landing_count;i++){
  const auto p=route.landing[i];const bw::Point from{std::int16_t(p.x),std::int16_t(p.y)},to{std::int16_t(goal.x),std::int16_t(goal.y)};
  if(!rework_relocation::connected(from,to)||!island_landing_clear(p.x,p.y))continue;
  const auto distance=wave_targeting::distance(p.x,p.y,goal.x,goal.y);const auto score=std::abs(distance-640ll*640);
  if(!found||score<best){found=true;best=score;x=p.x;y=p.y;}
 }return found;
}
inline const IslandRoute* island_plan(U32 owner=12) {
 if(!g.mission||!g.game||!rework_relocation::pathing_source)return nullptr;
 const U32 frame=g.game()->frame_count;
 if(island_cache_frame==frame&&island_cache_owner==owner)return island_cached;
 island_cache_frame=frame;island_cache_owner=owner;island_cached=nullptr;
 for(const auto& route:sc1_native::island_routes::routes){
  if(route.mission!=g.mission->mission_id||!is_enemy(route.owner)||(owner<12&&route.owner!=owner))continue;
  bool safe=false;for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==route.mission&&o.owner==route.owner&&o.center.x==route.center.x&&o.center.y==route.center.y&&origin_safe(o)){safe=true;break;}
  if(!safe||!island_landing(route,island_land_x,island_land_y))continue;
  const bw::Point landing{std::int16_t(island_land_x),std::int16_t(island_land_y)};
  for(U32 i=0;i<route.loading_count;i++){
   const auto p=route.loading[i];const bw::Point loading{std::int16_t(p.x),std::int16_t(p.y)};
   if(clear_cell(p.x,p.y)&&!rework_relocation::connected(loading,landing)){
    island_load_x=p.x;island_load_y=p.y;island_cached=&route;return island_cached;
   }
  }
 }return nullptr;
}
inline bool island_available(){return island_plan()!=nullptr;}
inline void island_discard(bw::Unit* u) {if(u&&rework_curses::marked(u)&&rework_combat_v5::native_kill)owner_kill_hook(u,rework_combat_v5::native_kill);}
inline void island_release_ground(bw::Unit* u,U32 reason) {
 if(!u || !rework_curses::marked(u) || (u->flags&0x40u))return;
 island_hold(u,false);wave_targeting::issue(u);
 log_event("Island convoy released grounded passenger: unit=%u owner=%u reason=%u frame=%u",U32(u->unit_id),U32(u->player),reason,g.game()->frame_count);
}
inline bw::Unit* island_create(U32 id,U32 slot,U32 hp,U32 attack,U32 required_owner) {
 const auto route=island_plan(required_owner<12?required_owner:primary?primary->owner:12u);
 if(!route||!g.order||!island_slot(slot))return nullptr;
 const U32 space=original_stat({0,47,id});if(!space||space>8)return nullptr;
 IslandConvoy* convoy=nullptr;
 for(auto& c:island_convoys)if(!c.phase&&c.wave==g.current_wave_id&&c.route==route&&c.space+space<=8&&island_unit(c.ship)){convoy=&c;break;}
 const U32 carrier_id=route->race==0?42u:route->race==2?69u:11u;
 const U32 budget=std::max(1u,original_stat({0,46,id}))+(convoy?0u:std::max(1u,original_stat({0,46,carrier_id})));
 if(live_supply()+budget>supply_cap()||(!convoy&&island_convoys.size()>=64))return nullptr;
 bw::Unit* ship=convoy?island_unit(convoy->ship):nullptr;
 if(!ship){
  for(U32 i=0;i<route->loading_count&&!ship;i++){const auto p=route->loading[i];if(!clear_cell(p.x,p.y))continue;OwnerDatScope scope(route->owner,route->owner);ship=spawn(carrier_id,p.x,p.y,route->owner);if(ship)finish_created(ship,0,100,100,p.x,p.y);}
  if(!ship)return nullptr;
  island_hold(ship,true);
  // Ventral Sacs is needed by the native Overlord boarding path. This changes
  // only the hostile transport owner's research, never the human's levels.
  if(carrier_id==42)enemy_progression::upgrade(route->owner,24,1);
 }
 bw::Unit* passenger=nullptr;
 for(U32 i=0;i<route->loading_count&&!passenger;i++){const auto p=route->loading[i];if(!clear_cell(p.x,p.y))continue;OwnerDatScope scope(route->owner,route->owner);passenger=spawn(id,p.x,p.y,route->owner);if(passenger)finish_created(passenger,slot,hp,attack,p.x,p.y);}
 if(!passenger){if(!convoy)island_discard(ship);return nullptr;}
 island_hold(passenger,true);
 if(!convoy){const bool announced=std::any_of(island_convoys.begin(),island_convoys.end(),[](const auto& c){return c.wave==g.current_wave_id;});IslandConvoy c{};c.ship=rework_combat_v5::identity(ship);c.route=route;c.wave=g.current_wave_id;c.started=g.game()->frame_count;c.land_x=island_land_x;c.land_y=island_land_y;island_convoys.push_back(std::move(c));convoy=&island_convoys.back();
  if(!announced)message("섬 지형: 지상 특수 공세가 수송선에 탑승해 상륙합니다.");
 }
 convoy->passengers.push_back(rework_combat_v5::identity(passenger));convoy->space+=space;return passenger;
}
inline void island_step() {
 if(!g.game||!g.order)return;const U32 frame=g.game()->frame_count;
 for(auto it=island_convoys.begin();it!=island_convoys.end();){
  auto& c=*it;auto ship=island_unit(c.ship);
  if(!ship||!is_enemy(ship->player)){
   // The native cargo hook owns passengers still aboard. Grounded units may
   // already be fighting after a partial/full unload; losing or capturing
   // their former transport must never kill them.
   for(const auto& token:c.passengers)if(auto p=island_unit(token))island_release_ground(p,1);
   it=island_convoys.erase(it);continue;
  }
  if(rework_curses::appearing(ship)){++it;continue;}
  U32 waiting=0,aboard=0;
  for(const auto& token:c.passengers)if(auto p=island_unit(token)){
   if((p->flags&0x40u)&&p->related==ship){++aboard;continue;}
   if(!c.phase){
    if(frame-c.started>=45u*24u){island_release_ground(p,2);continue;}
    ++waiting;if(!rework_curses::appearing(p)&&!(p->flags&0x40u)&&(p->order!=92||p->order_target.unit!=ship))g.order(p,92,ship->flingy.position.x,ship->flingy.position.y,ship,ship->unit_id);
   }else {island_hold(p,false);wave_targeting::issue(p);}
  }
  if(!c.phase&&!waiting){
   if(!aboard){island_discard(ship);it=island_convoys.erase(it);continue;}
   c.phase=1;c.last_order=0;
  }
  if(c.phase==1||c.phase==2){
   if(!aboard){c.phase=3;c.last_order=frame;g.order(ship,6,c.route->center.x,c.route->center.y,nullptr,228);}
   else if(!c.last_order||frame-c.last_order>=48){
    int x=c.land_x,y=c.land_y;
    if(island_landing(*c.route,x,y)){
     const bool changed=x!=c.land_x||y!=c.land_y;c.land_x=x;c.land_y=y;
     if(!c.last_order||changed||(ship->order!=111&&ship->order!=112))g.order(ship,112,x,y,nullptr,228);
     c.last_order=frame;c.phase=2;
    }
   }
  }else if(c.phase==3){
   const auto p=ship->flingy.position;
   if(wave_targeting::distance(p.x,p.y,c.route->center.x,c.route->center.y)<=192ll*192){island_discard(ship);it=island_convoys.erase(it);continue;}
   if(frame-c.last_order>=120&&ship->order!=6){g.order(ship,6,c.route->center.x,c.route->center.y,nullptr,228);c.last_order=frame;}
  }
  ++it;
 }
}
