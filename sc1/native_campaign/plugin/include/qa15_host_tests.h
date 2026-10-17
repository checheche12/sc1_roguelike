#pragma once
namespace host_test {
inline constexpr std::size_t qa15_group_count=2;
inline void qa15_current_maps_use_four_checkpoints_and_final_ack(){
 for(const auto& mission:campaign_config::kMissions){
  reset();make_chk(&mission,2);U32 capability=0;CHECK(identify_chk(chk.data(),chk.size(),&capability)==&mission&&capability==2);
  game.map_width_tiles=static_cast<std::uint16_t>(mission.width);game.map_height_tiles=static_cast<std::uint16_t>(mission.height);
  game.campaign_mission=static_cast<std::uint16_t>(mission.campaign_index?mission.campaign_index:17u);
  init_units(original);CHECK(g.active&&g.protocol.phase_version()==2&&g.protocol.total_phases()==4);
  CHECK(!switch_set(&game,campaign_config::kQuarterSwitch));
  const auto next=[&](U32 phase){for(U32 n=0;n<12 && g.protocol.requested_phase()!=phase;n++)tick();CHECK(g.protocol.requested_phase()==phase&&g.protocol.state()==1);};
  for(U32 phase=1;phase<=4;phase++){
   if(phase==2)write_switch(&game,campaign_config::kQuarterSwitch,true);
   if(phase==3)set_counter(kMiddleCounter,1);
   if(phase==4){set_counter(kRouteCounter,1);set_counter(kGoalCounter,1);}
   next(phase);CHECK(!counter(kReadyCounter)&&!counter(kAckCounter));
   auto snapshot=load_reply(phase);snapshot[12]=snapshot[28]=0;publish(snapshot);tick();
   CHECK(g.protocol.completed_phase()==phase&&!g.protocol.failed());
   if(phase<4)CHECK(g.protocol.ready()&&!counter(kReadyCounter));
  }
  CHECK(g.protocol.state()==3&&!counter(kAckCounter));
  auto ack=reply(2);for(U32 i=0;i<4;i++)ack[4+i]=g.protocol.mailbox_words()[10+i];ack[8]=1;ack[9]=1;
  publish(ack);protocol_pump(nullptr);CHECK(g.protocol.victory_ack_ready());tick();tick();CHECK(counter(kReadyCounter)&&counter(kAckCounter));
 }
}
inline void qa15_legacy_markers_and_future_phase_are_rejected(){
 reset();make_chk();U32 capability=0;CHECK(identify_chk(chk.data(),chk.size(),&capability)&&capability==1);init_units(original);
 CHECK(g.protocol.phase_version()==1&&g.protocol.total_phases()==3);CHECK(!g.protocol.request_phase(4));
 reset();make_chk(nullptr,2);init_units(original);CHECK(g.protocol.phase_version()==2);
 auto first=load_reply(1);first[12]=first[28]=0;publish(first);tick();CHECK(!g.protocol.request_phase(4));
 CHECK(!counter(kReadyCounter)&&!counter(kAckCounter));
}
inline void run_qa15_groups(){qa15_current_maps_use_four_checkpoints_and_final_ack();qa15_legacy_markers_and_future_phase_are_rejected();}
}
