#pragma once
namespace host_test {
inline constexpr std::size_t qa36_carrier_group_count=2;
namespace qa36_carrier {
inline U32 calls=0,handler_calls=0,allow_launches=8;
inline bool target=true,in_range=true,disabled=false;
// Native13515 StepOrder: unit+0xc9 is decremented; nonzero OLD wait
// skips dispatch. A zero old wait sets eight before CarrierAttack.
// The separate unit+0x70 launch timer is checked by CarrierAttack.
inline void __cdecl native_dispatch(bw::Unit* c){
 ++calls;const auto old=c->order_wait;c->order_wait=U8(old-1);if(old)return;c->order_wait=8;++handler_calls;
 if(!target||!in_range||disabled||c->order==52||handler_calls>allow_launches)return;
 rework_carrier_tests::stock_launch(c);
}
inline void begin(){rework_carrier_tests::begin();calls=handler_calls=0;allow_launches=8;target=in_range=true;disabled=false;}
}
inline void qa36_burst_crosses_real_dispatch_wait_without_advancing_frames(){
 using namespace rework_carrier_tests;
 for(U32 ammo=1;ammo<=8;++ammo){
  qa36_carrier::begin();talent(130);auto c=carrier(ammo);c->order=56;game.frame_count=91;
  const auto allocated=count;owner_order_hook(c,qa36_carrier::native_dispatch);auto actual=rework_carrier_v5::census(c);
  CHECK(actual.valid&&actual.inside==0&&actual.outside==ammo);CHECK(qa36_carrier::calls==ammo&&qa36_carrier::handler_calls==ammo);
  CHECK(game.frame_count==91&&count==allocated&&c->order_wait==8&&c->order_timer==7);
 }
 qa36_carrier::begin();talent(130);auto c=carrier(5,3);c->order=56;owner_order_hook(c,qa36_carrier::native_dispatch);
 CHECK(c->unit_specific.bytes[16]==0&&c->unit_specific.bytes[17]==8&&c->order_wait==8);
 qa36_carrier::begin();talent(130);talent(136);c=carrier(8);c->order=56;owner_order_hook(c,qa36_carrier::native_dispatch);
 CHECK(c->unit_specific.bytes[17]==8&&c->order_wait==8&&c->order_timer==4);
}
inline void qa36_native_gate_and_failed_extra_attempt_keep_native_wait(){
 using namespace rework_carrier_tests;
 qa36_carrier::begin();talent(130);auto c=carrier(8);c->order=56;c->order_wait=5;owner_order_hook(c,qa36_carrier::native_dispatch);
 CHECK(qa36_carrier::calls==1&&qa36_carrier::handler_calls==0&&c->unit_specific.bytes[16]==8&&c->order_wait==4);
 for(U32 denial=0;denial<4;++denial){
  qa36_carrier::begin();talent(130);c=carrier(8);c->order=denial==3?52:56;
  qa36_carrier::target=denial!=0;qa36_carrier::in_range=denial!=1;qa36_carrier::disabled=denial==2;
  owner_order_hook(c,qa36_carrier::native_dispatch);CHECK(c->unit_specific.bytes[16]==8&&qa36_carrier::calls==1&&c->order_wait==8);
 }
 qa36_carrier::begin();talent(130);qa36_carrier::allow_launches=3;c=carrier(8);c->order=56;owner_order_hook(c,qa36_carrier::native_dispatch);
 CHECK(c->unit_specific.bytes[16]==5&&c->unit_specific.bytes[17]==3&&qa36_carrier::calls==4&&c->order_timer==7&&c->order_wait==8);
 for(U32 owner:{1u,2u,7u,11u})for(bool learned:{false,true}){
  qa36_carrier::begin();if(learned)talent(130);c=carrier(8,0,owner);c->order=56;owner_order_hook(c,qa36_carrier::native_dispatch);
  CHECK(c->unit_specific.bytes[17]==(owner==1&&learned?8:1)&&c->order_wait==8);
 }
}
inline void run_qa36_carrier_groups(){qa36_burst_crosses_real_dispatch_wait_without_advancing_frames();qa36_native_gate_and_failed_extra_attempt_keep_native_wait();}
}
