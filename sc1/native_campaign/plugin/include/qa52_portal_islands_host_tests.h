#pragma once
namespace host_test { namespace qa52_fixture {
struct Visual {U32 id,owner;int x,y;};inline std::vector<Visual> visuals;
inline void* __cdecl visual(U32 id,int x,int y,U32 owner){visuals.push_back({id,owner,x,y});return nullptr;}
inline void __cdecl order(bw::Unit* u,U32 id,U32 x,U32 y,bw::Unit* target,U32){u->order=U8(id);u->order_target={std::int16_t(x),std::int16_t(y),target};}
inline bw::Unit* __cdecl create(U32 id,int x,int y,U32 owner,const U8* skins){auto u=host_test::create(id,x,y,owner,skins);if(u){u->flags=1u|((original_stat({0,22,id})&4u)?4u:0u);auto& sprite=multi_fixture::sprites[static_cast<std::size_t>(u-units.data())];sprite={};sprite.visibility_mask=0xff;u->flingy.sprite=&sprite;u->minor_unique_index&=31;}return u;}
inline void __cdecl unload(bw::Unit* carrier){
 auto window=rework_cargo_tests::packed(carrier);
 for(U32 i=0;i<8;i++)if(auto p=rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(window,i))){
  if(p->related!=carrier||!(p->flags&0x40u))continue;
  p->related=nullptr;p->flags&=~0x40u;p->order=1;p->flingy.position=carrier->flingy.position;
  carrier->loaded_units[i]=0;carrier->scr_carried_unit_high_bits=std::uint16_t(carrier->scr_carried_unit_high_bits&~(3u<<(i*2)));break;
 }
}
inline void island_begin(U32 mission){
 rework_wave_tests::begin(mission);rework_fixture::relocation();g.order=order;g.create=create;
 rework_combat_v5::native_kill=rework_cargo_tests::native_kill;rework_cargo_tests::death_calls={};rework_cargo_tests::give_calls={};
 rework_fixture::pathing.count=2;rework_fixture::pathing.regions[0].group=1;rework_fixture::pathing.regions[1].group=2;
 std::fill(std::begin(rework_fixture::pathing.tiles),std::end(rework_fixture::pathing.tiles),std::uint16_t(1));
 const sc1_native::island_routes::Route* first=nullptr;
 for(const auto& route:sc1_native::island_routes::routes)if(route.mission==mission){if(!first)first=&route;for(U32 i=0;i<route.landing_count;i++){const auto p=route.landing[i];rework_fixture::pathing.tiles[(p.y/32)*256+p.x/32]=0;}}
 CHECK(first);const auto origin=rework_waves::choose_origin(false);CHECK(origin);const auto target=origin->target;
 rework_fixture::pathing.tiles[(target.y/32)*256+target.x/32]=0;
 add(106,player_owner(),target.x,target.y)->flags=1;add(7,player_owner(),target.x+32,target.y)->flags=1;
 add(0,player_owner(),target.x+64,target.y)->flags=1;add(9,player_owner(),target.x+96,target.y)->flags=5;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=900*24;rework_waves::timeline.ordinal=6;
 rework_waves::primary=origin;g.current_wave_id=91;CHECK((rework_waves::capabilities()&8u)!=0);CHECK(!(rework_waves::capabilities()&1u));
}
inline void board_all(){
 rework_waves::timeline.active_ticks+=4*24;game.frame_count+=96;rework_waves::release_and_orders();rework_waves::island_step();
 for(auto& c:rework_waves::island_convoys)for(const auto& token:c.passengers)if(auto p=rework_waves::island_unit(token)){
  CHECK(p->order==92&&p->order_target.unit==rework_waves::island_unit(c.ship));owner_unit_hook(p,rework_cargo_tests::board);CHECK((p->flags&0x40u)&&p->related==rework_waves::island_unit(c.ship));
 }
 ++game.frame_count;rework_waves::island_step();
 for(auto& c:rework_waves::island_convoys){auto ship=rework_waves::island_unit(c.ship);CHECK(ship&&ship->order==112&&c.phase==2);const auto before=ship->order;wave_targeting::issue(ship);CHECK(ship->order==before);}
}
} // namespace qa52_fixture
inline void qa52_portal_repeat_visuals_follow_fixed_endpoints_and_expire(){
 using namespace rework_fixture;qa9_fixture::begin({145});relocation();qa52_fixture::visuals.clear();g.lone_sprite=qa52_fixture::visual;
 auto arbiter=unit(71,player_owner(),500,500,true),first=unit(65,player_owner(),100,100);
 arbiter->order=137;arbiter->order_state=1;arbiter->order_timer=0;arbiter->order_target={100,100,nullptr};
 {rework_combat_v5::OrderScope scope(arbiter,qa38_fixture::recall);qa38_fixture::recall(arbiter);}
 CHECK(first->flingy.position.x==500&&qa52_fixture::visuals.empty());
 auto later=unit(37,player_owner(),100,100);pulse(147);CHECK(qa52_fixture::visuals.empty());pulse(148);
 CHECK(later->flingy.position.x==500&&later->flingy.position.y==500&&qa52_fixture::visuals.size()==2);
 const auto& a=qa52_fixture::visuals[0];const auto& b=qa52_fixture::visuals[1];CHECK(a.id==379&&a.owner==player_owner()&&a.x==100&&a.y==100);CHECK(b.id==379&&b.x==500&&b.y==500);
 pulse(149);CHECK(qa52_fixture::visuals.size()==2);arbiter->flingy.position={1000,1000};auto next=unit(37,player_owner(),100,100);pulse(196);
 CHECK(next->flingy.position.x==500&&next->flingy.position.y==500&&qa52_fixture::visuals.size()==4);
 pulse(1253);const auto visual_count=qa52_fixture::visuals.size();pulse(1301);CHECK(qa52_fixture::visuals.size()==visual_count&&rework_combat_v5::persistent.empty());
 relocation_end();qa9_fixture::end();
}
inline void qa52_island_all_grades_board_fly_unload_and_attack(){
 U32 audited=0;
 for(U32 mission:{108u,204u,305u,503u,606u})for(const auto& roster:sc1_native::rework_wave::kRosters){
  if(!roster.grade||!(roster.requirements&sc1_native::rework_wave::GroundPath))continue;const U32 slot=roster.slot;
  qa52_fixture::island_begin(mission);auto original=add(37,4,800,800);const auto untouched=*original;
  if(rework_waves::current->blocked_heroes&(1u<<(slot-24))){CHECK(!rework_waves::timeline.eligible(*rework_waves::current,roster,rework_waves::capabilities()));rework_fixture::relocation_end();rework_fixture::finish();continue;}
  g.growth.curse_counts[slot]=1;
  CHECK(rework_waves::timeline.eligible(*rework_waves::current,roster,rework_waves::capabilities()));
  const auto baseline=count;rework_waves::roster(roster);CHECK(count>baseline&&!rework_waves::island_convoys.empty());
  U32 passengers=0;for(const auto& c:rework_waves::island_convoys){CHECK(c.space<=8);passengers+=U32(c.passengers.size());auto ship=rework_waves::island_unit(c.ship);CHECK(ship&&(ship->unit_id==11||ship->unit_id==42||ship->unit_id==69));}
  CHECK(passengers&&rework_waves::live_supply()<=480);qa52_fixture::board_all();
  for(auto& c:rework_waves::island_convoys){auto ship=rework_waves::island_unit(c.ship);ship->flingy.position={std::int16_t(c.land_x),std::int16_t(c.land_y)};ship->order=111;
   for(std::size_t i=0;i<c.passengers.size();i++)owner_unit_hook(ship,qa52_fixture::unload);
  }
  game.frame_count+=48;rework_waves::island_step();U32 unloaded=0;
  for(const auto& c:rework_waves::island_convoys)for(const auto& token:c.passengers)if(auto p=rework_waves::island_unit(token)){
   if((p->flags&0x40u)||p->related||rework_curses::transport_hold(p)||p->order!=14)std::printf("QA52_UNLOAD_DEBUG mission=%u slot=%u unit=%u flags=%u related=%u hold=%u order=%u x=%d y=%d\n",mission,slot,p->unit_id,p->flags,p->related?1u:0u,rework_curses::transport_hold(p)?1u:0u,p->order,p->flingy.position.x,p->flingy.position.y);
   CHECK(!(p->flags&0x40u)&&!p->related&&!rework_curses::transport_hold(p)&&p->order==14);++unloaded;
  }
  CHECK(unloaded==passengers&&std::memcmp(original,&untouched,sizeof(untouched))==0);
  std::printf("QA52_ISLAND mission=%u slot=%u passengers=%u transports=%zu native_orders=92,112,111 attack=ok\n",mission,slot,passengers,rework_waves::island_convoys.size());
  rework_fixture::relocation_end();rework_fixture::finish();++audited;
 }
 CHECK(audited>=60);
}
inline void qa52_island_transport_death_and_capture_preserve_identity(){
 for(bool capture:{false,true}){
  qa52_fixture::island_begin(108);g.growth.curse_counts[28]=1;rework_waves::roster(sc1_native::rework_wave::kRosters[4]);qa52_fixture::board_all();
  const auto c=rework_waves::island_convoys.front();auto ship=rework_waves::island_unit(c.ship);CHECK(ship);std::vector<bw::Unit*> passengers;
  for(const auto& token:c.passengers)passengers.push_back(rework_waves::island_unit(token));
  if(capture)owner_give_hook(ship,player_owner(),rework_cargo_tests::native_give);else owner_kill_hook(ship,rework_cargo_tests::native_kill);
  rework_waves::island_step();
  for(auto p:passengers)if(capture)CHECK(p->player==player_owner()&&p->flingy.hitpoints>0&&!rework_curses::transport_hold(p));else CHECK(p->flingy.hitpoints<=0);
  rework_fixture::relocation_end();rework_fixture::finish();
 }
}
inline constexpr std::size_t qa52_group_count=3;
inline void run_qa52_groups(){qa52_portal_repeat_visuals_follow_fixed_endpoints_and_expire();qa52_island_all_grades_board_fly_unload_and_attack();qa52_island_transport_death_and_capture_preserve_identity();}
}
