#pragma once
namespace host_test {
inline constexpr std::size_t qa35_carrier_group_count=5;
namespace qa35_carrier {
inline U32 native_calls=0,allow_calls=100;
inline void __cdecl launch(bw::Unit* c){++native_calls;if(native_calls<=allow_calls)rework_carrier_tests::stock_launch(c);}
inline void begin(){rework_carrier_tests::begin();native_calls=0;allow_calls=100;}
}
inline void qa35_burst_releases_existing_children_up_to_eight(){
 using namespace rework_carrier_tests;
 for(U32 ammo=0;ammo<=8;++ammo){
  qa35_carrier::begin();talent(130);game.upgrade_level_sc[1][43]=1;game.frame_count=10;auto c=carrier(ammo);c->order=50;
  const auto allocated=count;owner_order_hook(c,qa35_carrier::launch);const auto actual=rework_carrier_v5::census(c);
  CHECK(actual.valid&&actual.inside==0&&actual.outside==ammo);CHECK(count==allocated);CHECK(c->order_timer==(ammo?7:0));
  CHECK(qa35_carrier::native_calls==(ammo?ammo:1));CHECK(game.upgrade_level_sc[1][43]==1);
 }
 qa35_carrier::begin();talent(130);auto c=carrier(5,3);c->order=50;owner_order_hook(c,qa35_carrier::launch);
 CHECK(rework_carrier_v5::census(c).inside==0&&rework_carrier_v5::census(c).outside==8&&qa35_carrier::native_calls==5);
 // An older in-progress mission may already have more children. Preserve them;
 // one burst launches at most eight and never deletes or duplicates a child.
 qa35_carrier::begin();talent(130);c=carrier(12);c->order=50;const auto before_count=count;owner_order_hook(c,qa35_carrier::launch);
 CHECK(rework_carrier_v5::census(c).inside==4&&rework_carrier_v5::census(c).outside==8&&count==before_count);
}
inline void qa35_burst_respects_native_denial_and_partial_progress(){
 using namespace rework_carrier_tests;
 qa35_carrier::begin();talent(130);auto c=carrier(8);c->order=50;c->order_timer=5;owner_order_hook(c,qa35_carrier::launch);
 CHECK(qa35_carrier::native_calls==1&&c->unit_specific.bytes[16]==8&&c->unit_specific.bytes[17]==0&&c->order_timer==5);
 qa35_carrier::begin();talent(130);qa35_carrier::allow_calls=0;c=carrier(8);c->order=52;owner_order_hook(c,qa35_carrier::launch);
 CHECK(qa35_carrier::native_calls==1&&c->unit_specific.bytes[16]==8&&c->order==52&&c->order_timer==0);
 qa35_carrier::begin();talent(130);qa35_carrier::allow_calls=3;c=carrier(8);c->order=50;owner_order_hook(c,qa35_carrier::launch);
 CHECK(qa35_carrier::native_calls==4&&c->unit_specific.bytes[16]==5&&c->unit_specific.bytes[17]==3&&c->order_timer==7);
}
inline void qa35_burst_owner_isolation_hero_and_launch_talent(){
 using namespace rework_carrier_tests;
 for(U32 owner:{1u,2u,6u,11u})for(bool learned:{false,true}){
  qa35_carrier::begin();if(learned)talent(130);auto c=carrier(8,0,owner);c->order=50;owner_order_hook(c,qa35_carrier::launch);
  CHECK(c->unit_specific.bytes[17]==(owner==1&&learned?8:1));
 }
 qa35_carrier::begin();talent(130);auto c=carrier(8);c->flags|=0x40000000u;c->order=50;owner_order_hook(c,qa35_carrier::launch);CHECK(c->unit_specific.bytes[17]==1);
 qa35_carrier::begin();talent(130);c=carrier(8);c->unit_id=82;c->order=50;owner_order_hook(c,qa35_carrier::launch);CHECK(c->unit_specific.bytes[17]==8);
 qa35_carrier::begin();talent(130);talent(136);c=carrier(8);c->order=50;owner_order_hook(c,qa35_carrier::launch);CHECK(c->unit_specific.bytes[17]==8&&c->order_timer==4);
}
inline void qa35_interceptor_exact_double_stats_existing_birth_and_display(){
 using namespace qa13_fixture;
 begin();auto own=add(73,1,100,100,int(original_stat({0,8,73})));own->flags=1;own->shields=int(original_stat({0,7,73})*256);
 auto enemy=add(73,6,200,100),ally=add(73,2,220,100),neutral=add(73,11,240,100);
 const auto hp=original_stat({0,8,73}),shield=original_stat({0,7,73});CHECK(apply_snapshot(nullptr,snapshot(130)));
 CHECK(owner_stat(1,{0,8,73})==hp*2&&owner_stat(1,{0,7,73})==shield*2);
 CHECK(U32(own->flingy.hitpoints)==hp*2&&U32(own->shields)==shield*2*256);
 U32 shown_hp=0,shown_shield=0;CHECK(max_hp_cache::read_display(own,shown_hp,shown_shield)&&shown_hp==hp*2&&shown_shield==shield*2);
 for(auto u:{enemy,ally,neutral})CHECK(owner_stat(u->player,{0,8,73})==hp&&owner_stat(u->player,{0,7,73})==shield);
 const U8 skins[]={1,1};auto born=owner_create_hook(73,200,200,1,skins,rank_fixture::create_full);CHECK(born&&U32(born->flingy.hitpoints)==hp*2&&U32(born->shields)==shield*2*256);
 CHECK(original_stat({0,8,73})==hp&&original_stat({0,7,73})==shield);end();
 // The new x2 is applied after other live talent bonuses, not to their text.
 begin();auto base=economy_snapshot({});base.talent_bits[103/32]|=1u<<(103%32);CHECK(apply_snapshot(nullptr,base));
 const auto with_health=owner_stat(1,{0,8,73}),with_shields=owner_stat(1,{0,7,73});CHECK(with_health>original_stat({0,8,73})&&with_shields>original_stat({0,7,73}));
 auto combined=base;combined.talent_bits[368/32]|=1u<<(368%32);combined.completed_phase=2;CHECK(apply_snapshot(nullptr,combined));CHECK(owner_stat(1,{0,8,73})==with_health*2&&owner_stat(1,{0,7,73})==with_shields*2);end();
}
inline void qa35_native_counts_and_research_never_receive_temporary_views(){
 using namespace rework_carrier_tests;
 qa35_carrier::begin();talent(130);game.upgrade_level_sc[1][43]=1;auto c=carrier(8);const auto before=c->unit_specific;
 game.minerals[1]=1000;command(c);CHECK(game.minerals[1]==1000&&std::memcmp(&before,&c->unit_specific,sizeof(before))==0);
 const auto observe=[](bw::Unit* u){CHECK(u->unit_specific.bytes[16]==8&&u->unit_specific.bytes[17]==0&&game.upgrade_level_sc[1][43]==1);};
 owner_secondary_hook(c,observe);CHECK(std::memcmp(&before,&c->unit_specific,sizeof(before))==0);
}
inline void run_qa35_carrier_groups(){qa35_burst_releases_existing_children_up_to_eight();qa35_burst_respects_native_denial_and_partial_progress();qa35_burst_owner_isolation_hero_and_launch_talent();qa35_interceptor_exact_double_stats_existing_birth_and_display();qa35_native_counts_and_research_never_receive_temporary_views();}
}
