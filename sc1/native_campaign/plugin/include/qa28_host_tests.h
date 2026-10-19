#pragma once
namespace host_test {
inline constexpr std::size_t qa28_group_count=3;
inline void qa28_extended_curses_reach_native_apply_through_mailbox(){
 for(U32 slot=16;slot<=19;++slot)for(U32 stacks:{1u,2u,3u,255u,256u,1000u,0xffffffffu}){
  reset();make_chk(nullptr,2);init_units(original);
  CHECK(g.protocol.phase_version()==2 && g.protocol.state()==1);
  auto response=reply(1);response[4]=1;response[5]=2;response[6]=3;response[7]=4;
  response[10]=0x50480101;response[28+slot/4]=std::min(stacks,255u)<<((slot%4)*8);
  response[91-slot]=stacks;publish(response);protocol_pump(nullptr);
  CHECK(g.protocol.ready() && g.applied && g.applied_phase==1 && !g.apply_failure);
  CHECK(sc1_native::curse_scaling::count(g.growth,slot)==stacks);
  CHECK(g.growth.curse_counts[20]==0);
  CHECK(g.protocol.request_phase(2));response=reply(1);response[4]=1;response[5]=2;response[6]=3;response[7]=4;
  response[10]=0x50480202;response[28+slot/4]=std::min(stacks,255u)<<((slot%4)*8);response[91-slot]=stacks;
  publish(response);protocol_pump(nullptr);CHECK(g.protocol.ready() && g.applied_phase==2);
 }
}
inline void qa28_rank_storage_rejects_invalid_native_application_atomically(){
 for(U32 index=rework_catalog::kRankCount;index<28;++index){
  reset();const auto before=storage;GrowthSnapshot snapshot{};snapshot.wire_version=2;snapshot.talent_ranks[index]=1;
  CHECK(!apply_snapshot(nullptr,snapshot) && !g.applied && g.baseline.empty() && storage==before);
 }
 for(U32 slot=16;slot<=19;++slot){
  for(U32 extended:{1u,256u}){
   reset();const auto before=storage;GrowthSnapshot snapshot{};snapshot.wire_version=2;snapshot.talent_ranks[47-slot]=extended;
   CHECK(!apply_snapshot(nullptr,snapshot) && !g.applied && g.baseline.empty() && storage==before);
  }
  reset();GrowthSnapshot legacy{};legacy.talent_ranks[47-slot]=1;
  CHECK(!apply_snapshot(nullptr,legacy) && !g.applied);
 }
}
inline void qa28_byte_only_legacy_and_v2_snapshots_still_apply(){
 for(U32 version:{1u,2u}){
  reset();GrowthSnapshot snapshot{};snapshot.wire_version=version;snapshot.curse_counts[version==1?1:16]=3;
  CHECK(apply_snapshot(nullptr,snapshot) && g.applied && !g.apply_failure);
 }
}
inline void run_qa28_groups(){qa28_extended_curses_reach_native_apply_through_mailbox();qa28_rank_storage_rejects_invalid_native_application_atomically();qa28_byte_only_legacy_and_v2_snapshots_still_apply();}
}
