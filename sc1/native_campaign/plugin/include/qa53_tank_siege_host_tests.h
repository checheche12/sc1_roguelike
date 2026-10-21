#pragma once
namespace host_test { namespace qa53_fixture {
struct Command {bw::Unit* unit;U32 order;bw::Unit* target;};
inline std::vector<Command> commands;
inline bw::Unit* denied=nullptr;
inline U32 validations=0;
inline U32 __cdecl can_attack(bw::Unit*,bw::Unit* target,U32 check){CHECK(check==1);++validations;return target!=denied;}
inline void __cdecl record(bw::Unit* u,U32 id,U32 x,U32 y,bw::Unit* target,U32){commands.push_back({u,id,target});u->order=U8(id);u->order_state=0;u->order_target={std::int16_t(x),std::int16_t(y),target};}
inline bw::Unit* turret(bw::Unit* tank){
 const U32 id=tank->unit_id==5?6u:tank->unit_id==23?24u:tank->unit_id==30?31u:26u;
 auto gun=multi_fixture::unit(id,tank->player,tank->flingy.position.x,tank->flingy.position.y);
 tank->subunit=gun;gun->subunit=tank;return gun;
}
inline void __cdecl native_morph(bw::Unit* tank,U32 id){
 tank->unit_id=std::uint16_t(id);tank->order=2;tank->order_target.unit=nullptr;
 tank->subunit->unit_id=std::uint16_t(id==30?31u:id==25?26u:id==5?6u:24u);tank->subunit->order=22;
}
inline void complete(bw::Unit* tank){const U32 next=tank->order==98?(tank->unit_id==23?25u:30u):(tank->unit_id==25?23u:5u);owner_transform_hook(tank,next,native_morph);}
inline bw::Unit* begin(U32 id=5){
 rework_wave_tests::begin(106);g.create=qa52_fixture::create;g.order=record;multi_target::can_attack=can_attack;
 commands.clear();denied=nullptr;validations=0;g.current_wave_id=91;
 rework_waves::timeline.home=true;rework_waves::timeline.active_ticks=900*24;
 auto tank=rework_waves::create(id,id==23?39u:32u,150,130);CHECK(tank);tank->flingy.position={1000,1000};turret(tank);
 rework_waves::timeline.active_ticks+=4*24;game.frame_count=96;rework_waves::release_and_orders();
 CHECK(!rework_curses::appearing(tank));commands.clear();return tank;
}
inline bw::Unit* target(int x=1380,int y=1000,U32 id=0,bool flying=false){return multi_fixture::unit(id,player_owner(),x,y,flying);}
inline void tick(U32 frame){game.frame_count=frame;rework_waves::release_and_orders();wave_targeting::step(true,false);}
} // namespace qa53_fixture
inline void qa53_normal_and_duke_siege_fire_unsiege_and_resume(){
 using namespace qa53_fixture;
 for(U32 id:{5u,23u}){
  auto tank=begin(id);auto victim=target();const auto hp=tank->flingy.hitpoints;
  auto original=multi_fixture::unit(id,tank->player,1000,1100);turret(original);const auto untouched=*original;
  tick(120);CHECK(tank->order==98&&commands.size()==1&&commands[0].unit==tank);
  CHECK(tank->unit_id==id&&tank->flingy.hitpoints==hp); // Controller did not fake a morph or shot.
  tick(144);CHECK(tank->order==98&&commands.size()==1);
  complete(tank);CHECK(rework_curses::marked(tank)&&rework_curses::hp_percent(tank)==150&&rework_curses::attack_percent(tank)==130);
  tick(168);CHECK(tank->order==10&&tank->order_target.unit==victim);const auto issued=commands.size();
  tank->order=100;wave_targeting::issue(tank);tick(192);CHECK(commands.size()==issued&&tank->order==100);
  victim->flingy.hitpoints=0;tick(216);tick(240);CHECK(tank->order==100);
  tick(264);CHECK(tank->order==99);complete(tank);CHECK(tank->unit_id==id&&rework_curses::marked(tank));
  auto distant=target(2200,1000,106);distant->flags=1;tick(288);CHECK(tank->order==14&&tank->order_target.x==2200);
  CHECK(std::memcmp(original,&untouched,sizeof(untouched))==0);
  std::printf("QA53_TANK unit=%u siege=98 fire=10 unsiege=99 march=14 lifecycle=ok\n",id);
 }
}
inline void qa53_tank_visibility_range_and_native_target_validation(){
 using namespace qa53_fixture;
 auto tank=begin();auto victim=target();auto sprite=static_cast<bw::SpriteScr*>(victim->flingy.sprite);
 sprite->visibility_mask=0;tick(120);CHECK(tank->order!=98);
 sprite->visibility_mask=0xff;victim->flags|=4;tick(144);CHECK(tank->order!=98);victim->flags&=~4u;
 victim->flags|=0x40;tick(168);CHECK(tank->order!=98);victim->flags&=~0x40u;
 victim->flags|=0x4000000;tick(192);CHECK(tank->order!=98);victim->flags&=~0x4000000u;
 victim->flags|=0x100;victim->detection_status=0;tick(216);CHECK(tank->order!=98);victim->flags&=~0x100u;
 victim->flingy.position={1024,1000};tick(240);CHECK(tank->order!=98);
 victim->flingy.position={1800,1000};tick(264);CHECK(tank->order!=98);
 victim->flingy.position={1380,1000};denied=victim;tick(288);CHECK(tank->order!=98);
 denied=nullptr;victim->player=tank->player;tick(312);CHECK(tank->order!=98);victim->player=U8(player_owner());
 tick(336);CHECK(tank->order==98&&validations>0);
  complete(tank);tick(360);CHECK(tank->order==10);auto nearby_victim=target(1024);victim->flingy.hitpoints=0;
 tick(384);CHECK(tank->order==10);tick(408);CHECK(tank->order==99);complete(tank);
  tick(432);CHECK(tank->order!=98);nearby_victim->flingy.position={1380,1000};tick(456);CHECK(tank->order!=98);tick(480);CHECK(tank->order==98);
}
inline void qa53_tank_disables_appearance_orders_identity_and_scan_budget(){
 using namespace qa53_fixture;
 auto tank=begin();target();auto v=rework_curses::identity(tank);CHECK(v);
 v->transport_hold=true;tick(120);CHECK(tank->order!=98);v->transport_hold=false;
 tank->flags|=0x40;tick(144);CHECK(tank->order!=98);tank->flags&=~0x40u;
 tank->lockdown_timer=1;tick(168);CHECK(tank->order!=98);tank->lockdown_timer=0;
 tank->stasis_timer=1;tick(192);CHECK(tank->order!=98);tank->stasis_timer=0;
 tank->maelstrom_timer=1;tick(216);CHECK(tank->order!=98);tank->maelstrom_timer=0;
 tank->order=92;tick(240);CHECK(tank->order==92);tank->order=99;tick(264);CHECK(tank->order==99);
 tank->order=14;tick(288);CHECK(tank->order==98);complete(tank);tick(312);CHECK(tank->order==10);
 auto count_before=validations;for(U32 f=313;f<336;f++)tick(f);CHECK(validations==count_before);
 const auto command_count=commands.size();++tank->minor_unique_index;tick(360);CHECK(commands.size()==command_count&&!rework_curses::marked(tank));
 tank=begin();auto victim=target();rework_curses::before_give(tank,player_owner());tank->player=U8(player_owner());tick(120);CHECK(tank->order!=98);
 tank=begin();victim=target();(void)victim;v=rework_curses::identity(tank);v->appearance_until=rework_waves::timeline.second()+4;tick(120);CHECK(tank->order!=98);
}
inline void qa53_island_tanks_siege_only_after_native_unload(){
 using namespace qa53_fixture;
 qa52_fixture::island_begin(108);multi_target::can_attack=can_attack;denied=nullptr;commands.clear();
 g.growth.curse_counts[28]=1;rework_waves::roster(sc1_native::rework_wave::kRosters[4]);
 bw::Unit* tank=nullptr;rework_waves::IslandConvoy* convoy=nullptr;
 for(auto& c:rework_waves::island_convoys)for(const auto& token:c.passengers)if(auto u=rework_waves::island_unit(token))if(u->unit_id==5&&!tank){tank=u;convoy=&c;}
 CHECK(tank&&convoy);turret(tank);qa52_fixture::board_all();auto ship=rework_waves::island_unit(convoy->ship);CHECK(ship);
 g.order=record;auto victim=target(tank->flingy.position.x+200,tank->flingy.position.y);tick(game.frame_count+24);
 CHECK(std::none_of(commands.begin(),commands.end(),[](const auto& c){return c.order==98;}));
 ship->flingy.position={std::int16_t(convoy->land_x),std::int16_t(convoy->land_y)};ship->order=111;
 for(std::size_t i=0;i<convoy->passengers.size();i++)owner_unit_hook(ship,qa52_fixture::unload);
 victim->flingy.position={std::int16_t(convoy->land_x+200),std::int16_t(convoy->land_y)};
 game.frame_count+=48;rework_waves::island_step();CHECK(!(tank->flags&0x40u)&&!rework_curses::transport_hold(tank));
 tick(game.frame_count+24);CHECK(tank->order==98);
 rework_fixture::relocation_end();rework_fixture::finish();
}
inline constexpr std::size_t qa53_group_count=4;
inline void run_qa53_groups(){qa53_normal_and_duke_siege_fire_unsiege_and_resume();qa53_tank_visibility_range_and_native_target_validation();qa53_tank_disables_appearance_orders_identity_and_scan_budget();qa53_island_tanks_siege_only_after_native_unload();}
}
