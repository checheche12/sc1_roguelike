#pragma once
namespace host_test {
inline constexpr std::size_t qa31_group_count=5;
inline void qa31_four_curse_totals_and_large_counts(){
 namespace p=sc1_native::rework_wave;namespace cs=sc1_native::curse_scaling;
 const U32 amount[]={0,20,44,72,104},stat[]={0,10,22,36,52},health[]={0,10,22,36,52},haste[]={0,15,31,48,66};
 for(U32 rank=0;rank<5;++rank){
  rework_wave_tests::begin(101);g.growth.curse_counts[16]=g.growth.curse_counts[17]=g.growth.curse_counts[18]=g.growth.curse_counts[19]=U8(rank);
  g.current_wave_id=1;auto u=rework_waves::create(0,0);CHECK(u);
  CHECK(p::scaled_count(100,rank)==100+amount[rank]);
  CHECK(rework_curses::attack_percent(u)==100+stat[rank]);
  CHECK(rework_curses::hp_percent(u)==100+health[rank]);
  CHECK(rework_curses::speed_percent(u)==100+haste[rank]);
 }
 CHECK(cs::bonus(40001,5,1)==800220005u);
 for(U32 rank:{256u,1000u,0xffffffffu}){
  g.growth.curse_counts[19]=255;g.growth.talent_ranks[28]=rank;
  CHECK(rework_curses::count(19)==rank);
  CHECK(rework_curses::speed_percent(&units[count-1])==cs::scale(100,cs::bonus(rank,15,1)));
 }
}
inline void qa31_attack_and_movement_speed_are_additive_and_owner_scoped(){
 for(U32 rank:{1u,2u,3u,256u}){
  rework_wave_tests::begin(101);g.growth.curse_counts[19]=U8(std::min(rank,255u));g.growth.talent_ranks[28]=rank;
  g.current_wave_id=1;auto enemy=rework_waves::create(0,0);CHECK(enemy);
  auto friendly=add(0,player_owner(),100,100),original=add(0,enemy->player,1800,1800);
  for(auto u:{enemy,friendly,original})u->flingy.top_speed=1000;
  refresh_units();U32 elapsed=0,air_elapsed=0;const double period=15.0*100.0/double(rework_curses::speed_percent(enemy));
  for(U32 shot=0;shot<100;++shot){
   // Replay the native timer reaching zero between attacks. Skipping this
   // observation would present a repeated15 as an unchanged running timer.
   game.frame_count=elapsed?elapsed-1:0;enemy->ground_cooldown=enemy->air_cooldown=0;apply_unit_motion();
   game.frame_count=elapsed;enemy->ground_cooldown=enemy->air_cooldown=15;
   friendly->ground_cooldown=original->ground_cooldown=15;
   note_attack_launch(enemy,0);note_attack_launch(friendly,0);note_attack_launch(original,0);apply_unit_motion();
   CHECK(friendly->ground_cooldown==15 && original->ground_cooldown==15);
   CHECK(enemy->flingy.top_speed==U32(1000ull*rework_curses::speed_percent(enemy)/100u));
   CHECK(friendly->flingy.top_speed==1000 && original->flingy.top_speed==1000);
   const auto applied=enemy->ground_cooldown;apply_unit_motion();CHECK(enemy->ground_cooldown==applied);
   elapsed+=enemy->ground_cooldown;air_elapsed+=enemy->air_cooldown;
  }
  std::printf("AUDIT haste rank=%u ground=%u air=%u ideal=%.4f marked=%u\n",rank,elapsed,air_elapsed,100.0*std::max(1.0,period),unsigned(rework_curses::marked(enemy)));
  CHECK(std::abs(double(elapsed)-100.0*std::max(1.0,period))<1.01);
  CHECK(elapsed==air_elapsed);
 }
}
inline void qa31_haste_wide_counter_cannot_decrease_across_checkpoint(){
 reset();make_chk(nullptr,2);init_units(original);
 auto payload=reply(1);payload[4]=1;payload[5]=2;payload[6]=3;payload[7]=4;payload[10]=0x50480101;payload[32]=255u<<24;payload[72]=1000;
 publish(payload);protocol_pump(nullptr);CHECK(g.protocol.ready() && rework_curses::count(19)==1000);
 CHECK(g.protocol.request_phase(2));payload=reply(1);payload[4]=1;payload[5]=2;payload[6]=3;payload[7]=4;payload[10]=0x50480202;payload[32]=255u<<24;payload[72]=999;
 publish(payload);protocol_pump(nullptr);CHECK(g.protocol.failed());
}
inline void qa31_arbiter_rejoins_own_wave_preserving_cast_and_cloak_orders(){
 for(U32 id:{71u,86u}){
  rework_wave_tests::begin(101);auto hq=add(106,player_owner(),1000,1000);hq->flags=1;
  auto arbiter=wave_target_tests::wave(id,4,200,200),leader=wave_target_tests::wave(0,4,600,600);
  rework_waves::finish_created(arbiter,0,100,100,200,200);auto tag=rework_curses::identity(arbiter);CHECK(tag);
  arbiter->flags=(arbiter->flags&~0x04009000u)|tag->saved_flags;tag->appearance_until=0;CHECK(wave_targeting::marked(arbiter));
  auto other_wave=wave_target_tests::wave(0,4,900,900);existing_track(other_wave)->wave_id=2;
  auto unmarked=add(id,4,220,220);unmarked->order=163;const auto saved=*unmarked;
  arbiter->secondary_order=131; // CloakNearbyUnits is independent of movement.
  for(U32 order:{49u,163u}){
   arbiter->order=U8(order);game.frame_count+=48;wave_targeting::issue(arbiter);
   CHECK(arbiter->order==14 && arbiter->order_target.x==600 && arbiter->order_target.y==600);
   CHECK(arbiter->secondary_order==131);
  }
  arbiter->order=147;game.frame_count+=48;const auto issued_count=wave_target_tests::issued.size();wave_targeting::issue(arbiter);
  CHECK(arbiter->order==147 && wave_target_tests::issued.size()==issued_count);
  arbiter->order=130;game.frame_count+=48;wave_targeting::issue(arbiter);CHECK(arbiter->order==130); // Do not cancel native aura initialization.
  arbiter->order=163;leader->flingy.hitpoints=0;game.frame_count+=48;wave_targeting::issue(arbiter);
  CHECK(arbiter->order==14 && arbiter->order_target.x==1000 && arbiter->order_target.y==1000);
  wave_targeting::issue(unmarked);CHECK(std::memcmp(unmarked,&saved,sizeof(saved))==0);
 }
}
inline void qa31_guardian_manual_matches_mutalisk_without_other_air_buff(){
 for(U32 rank:{1u,4u}){
  qa13_fixture::begin();GrowthSnapshot snapshot{};snapshot.wire_version=2;
  snapshot.talent_bits[(238+72)/32]|=1u<<((238+72)%32);snapshot.talent_ranks[rework_catalog::kRankSlots[72]]=rank;
  CHECK(apply_snapshot(nullptr,snapshot));
  for(U32 id:{43u,44u,55u,56u,47u,62u}){
   auto own=add(id,player_owner(),100,100);
   const U32 increase=(id==43||id==44||id==55||id==56)?6u:3u;
   U32 weapons=0;for(U32 field:{17u,19u}){const auto weapon=original_stat({0,field,id});if(weapon>=130)continue;++weapons;
   CHECK(owner_stat(player_owner(),{1,14,weapon})==original_stat({1,14,weapon})+rank*increase);
   CHECK(owner_stat(6,{1,14,weapon})==original_stat({1,14,weapon}));
   CHECK(std::abs(rework_combat_v5::cooldown_ratio(own,weapon)-std::pow(0.955,double(rank)))<0.00001);
   }CHECK(weapons>0);
  }
  qa13_fixture::end();
 }
}
inline void run_qa31_groups(){qa31_four_curse_totals_and_large_counts();qa31_attack_and_movement_speed_are_additive_and_owner_scoped();qa31_haste_wide_counter_cannot_decrease_across_checkpoint();qa31_arbiter_rejoins_own_wave_preserving_cast_and_cloak_orders();qa31_guardian_manual_matches_mutalisk_without_other_air_buff();}
}
