#pragma once
#include "qa29_armor_native.generated.h"
namespace host_test {
inline constexpr std::size_t qa29_group_count=8;
inline void qa29_stat_indexes_match_linear_values_and_reset(){
 reset();GrowthSnapshot snapshot{};snapshot.wire_version=2;
 for(U32 ordinal:{26u,31u,32u})snapshot.talent_bits[(238+ordinal)/32]|=1u<<((238+ordinal)%32);
 snapshot.talent_ranks[rework_catalog::kRankSlots[26]]=1;snapshot.talent_ranks[rework_catalog::kRankSlots[31]]=1;CHECK(apply_snapshot(nullptr,snapshot));
 for(U32 table=0;table<2;++table)for(U32 field:table?std::initializer_list<U32>{5,14,16}:std::initializer_list<U32>{8,27,42})for(U32 id=0;id<(table?130u:228u);++id){
  const Key key{table,field,id};auto raw=table_for(key,false);const auto baseline=effect_value(g.baseline,key,raw?read_entry(raw,id):0);
  U32 original=raw?read_entry(raw,id):0;for(const auto& e:g.baseline)if(same(e.key,key)){original=e.before;break;}
  (void)baseline;CHECK(original_stat(key)==original);
  for(U32 owner:{1u,4u,11u})CHECK(owner_stat(owner,key)==(owner==1?effect_value(g.friendly_edits,key,original):owner==4?effect_value(g.enemy_edits,key,original):original));
 }
 snapshot.completed_phase=2;snapshot.talent_ranks[rework_catalog::kRankSlots[31]]=2;CHECK(apply_snapshot(nullptr,snapshot));
 const auto weapon=original_stat({0,17,12});CHECK(owner_stat(1,{1,14,weapon})>original_stat({1,14,weapon}));
 init_game();CHECK(owner_stat(1,{1,14,weapon})==original_stat({1,14,weapon}));
}
inline void qa29_marine_burst_keeps_primary_and_two_small_extras(){
 using namespace rework_fixture;
 for(U32 type:{0u,20u}){qa9_fixture::begin({53});auto marine=unit(type,1,100,100),victim=unit(37,6,120,100);auto primary=bullet(marine,victim,0);
  CHECK(rework_combat_v5::projectiles.at(primary).percent==100);
  CHECK(rework_combat_v5::pending_shots.size()==2);for(const auto& shot:rework_combat_v5::pending_shots)CHECK(shot.percent==35);
  pulse(102);pulse(104);CHECK(multi_fixture::shots.size()==3&&rework_combat_v5::pending_shots.empty());
  U32 total=0;for(const auto& item:rework_combat_v5::projectiles)total+=item.second.percent;CHECK(total==170);
  qa9_fixture::end();
 }
}
inline void qa29_bc_auto_yamato_counts_primary_attacks_only(){
 using namespace rework_fixture;qa9_fixture::begin({65});auto bc=unit(12,1,100,100),victim=unit(37,6,130,100);bc->order=10;const U32 w=original_stat({0,17,12});
 for(U32 i=0;i<4;i++){game.frame_count=100+i;bullet(bc,victim,w);if(i<3)CHECK(rework_combat_v5::pending_shots.empty());}
 CHECK(rework_combat_v5::pending_shots.size()==1&&rework_combat_v5::pending_shots[0].weapon==30&&rework_combat_v5::pending_shots[0].percent==100);
 pulse(105);CHECK(rework_combat_v5::pending_shots.empty()&&rework_combat_v5::state(bc)->bc_primary_attacks==4);
 U32 yamatos=0;for(const auto& p:rework_combat_v5::projectiles)if(p.second.weapon==30){++yamatos;CHECK(p.second.secondary&&p.second.percent==100);}CHECK(yamatos==1);
 qa9_fixture::end();
}
inline void qa29_air_control_and_procurement_are_bounded(){
 reset();GrowthSnapshot snapshot{};snapshot.wire_version=2;for(U32 ordinal:{47u,69u,110u,112u,153u,157u,160u})snapshot.talent_bits[(238+ordinal)/32]|=1u<<((238+ordinal)%32);
 for(U32 ordinal:{69u,110u,112u})snapshot.talent_ranks[rework_catalog::kRankSlots[ordinal]]=1;
 CHECK(apply_snapshot(nullptr,snapshot));
 for(U32 id:{8u,12u,44u,62u,70u,71u,72u}){
  const auto w=original_stat({0,17,id});if(w<130)CHECK(owner_stat(1,{1,5,w})==original_stat({1,5,w})+32);
  CHECK(owner_stat(1,{0,42,id})==(original_stat({0,42,id})*4+4)/5);
  CHECK(owner_stat(1,{0,40,id})==(original_stat({0,40,id})*4+4)/5);
  CHECK(owner_stat(4,{0,42,id})==original_stat({0,42,id}));
 }
 CHECK(!rework_combat_v5::air_control(snapshot,43)&&!rework_combat_v5::air_control(snapshot,98));
}
inline void qa29_bc_moving_fire_keeps_destination_and_native_disable_guards(){
 using namespace rework_fixture;qa9_fixture::begin({47});auto bc=unit(12,1,100,100,true);unit(37,6,130,100);
 bc->order=6;bc->order_target={600,700,nullptr};pulse(100);
 CHECK(multi_fixture::shots.size()==1&&bc->order==6&&bc->order_target.x==600&&bc->order_target.y==700&&bc->order_target.unit==nullptr);
 pulse(101);CHECK(multi_fixture::shots.size()==1);
 bc->ground_cooldown=bc->air_cooldown=0;bc->lockdown_timer=1;pulse(500);CHECK(multi_fixture::shots.size()==1);
 bc->lockdown_timer=0;bc->player=6;pulse(501);CHECK(multi_fixture::shots.size()==1);qa9_fixture::end();
}
namespace qa29_armor_fixture {
inline U8* allocated=nullptr;inline bool reject=false;
inline U32 __cdecl write(std::size_t address,const U8* bytes,std::size_t length){if(reject||address!=reinterpret_cast<std::size_t>(allocated+campaign_ultra_armor::gate_rva)||length!=2)return 0;std::memcpy(reinterpret_cast<void*>(address),bytes,length);return 1;}
inline U32 __cdecl id(bw::Unit* u){return u->unit_id;}
inline U32 __cdecl ultra(bw::Unit* u){return u->unit_id==39||u->unit_id==48;}
inline U32 __cdecl hero(bw::Unit* u){return u->unit_id==48;}
inline U32 __cdecl upgrade(U32 owner,U32 number){return rework_upgrade_storage::level(owner,number);}
struct Image {
 Image(){allocated=static_cast<U8*>(VirtualAlloc(nullptr,0x1460000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(allocated);
  std::memcpy(allocated+0x1e7db0,qa29_armor_native::body,sizeof(qa29_armor_native::body));
  const auto encoded=reinterpret_cast<std::uintptr_t>(&game)^qa29_armor_native::key;std::memcpy(allocated+qa29_armor_native::pointer_rva,&encoded,8);
  auto table=reinterpret_cast<U32*>(allocated+qa29_armor_native::table_rva);table[0]=table[39]=table[48]=3;
  native_engine_hooks::absolute_jump(allocated+0x1c6280,reinterpret_cast<void*>(id));native_engine_hooks::absolute_jump(allocated+0x1c7bf0,reinterpret_cast<void*>(ultra));
  native_engine_hooks::absolute_jump(allocated+0x1c74f0,reinterpret_cast<void*>(hero));native_engine_hooks::absolute_jump(allocated+0x3d4d40,reinterpret_cast<void*>(upgrade));
  campaign_ultra_armor::queued=false;campaign_ultra_armor::image=nullptr;reject=false;
 }
 ~Image(){campaign_ultra_armor::queued=false;campaign_ultra_armor::image=nullptr;VirtualFree(allocated,0,MEM_RELEASE);allocated=nullptr;}
 U32 bonus(bw::Unit* unit){FlushInstructionCache(GetCurrentProcess(),allocated,0x1460000);return reinterpret_cast<U32 (__cdecl*)(bw::Unit*)>(allocated+0x1e7db0)(unit)&255u;}
};
}
inline void qa29_native_ultra_armor_gate_honors_research_in_both_modes(){
 using namespace qa29_armor_fixture;reset();Image image;auto unit=add(39,4,100,100);game.upgrade_level_sc[4][3]=3;game.upgrade_level_bw[4][6]=1;
 game.is_bw=0;CHECK(image.bonus(unit)==3); // Reproduce the missing Chitinous+2.
 CHECK(campaign_ultra_armor::register_at(allocated,write)&&campaign_ultra_armor::verify_installation());
 CHECK(image.bonus(unit)==5&&game.is_bw==0);game.is_bw=1;CHECK(image.bonus(unit)==5);
 game.upgrade_level_bw[4][6]=0;CHECK(image.bonus(unit)==3);game.is_bw=0;CHECK(image.bonus(unit)==3);
 unit->unit_id=0;CHECK(image.bonus(unit)==3);unit->unit_id=48;CHECK(image.bonus(unit)==5);
 unit->unit_id=39;unit->player=1;CHECK(image.bonus(unit)==0);
}
inline void qa29_native_ultra_registration_rejects_changed_code(){
 using namespace qa29_armor_fixture;reset();Image image;reject=true;CHECK(!campaign_ultra_armor::register_at(allocated,write));reject=false;
 allocated[campaign_ultra_armor::gate_rva]=0x74;CHECK(!campaign_ultra_armor::register_at(allocated,write));allocated[campaign_ultra_armor::gate_rva]=0x75;
 CHECK(campaign_ultra_armor::register_at(allocated,write));allocated[campaign_ultra_armor::gate_rva]=0x75;CHECK(!campaign_ultra_armor::verify_installation());
}
inline void qa29_yamato_preparation_preserves_native_launch_and_cost(){
 using namespace rework_fixture;
 const auto& code=movement_effects::data::kIscript;
 CHECK(std::memcmp(code+4512,"SCPE",4)==0&&code[4520]==0xac&&code[4521]==0x11);
 for(auto ordinal:{64u,65u}){
  begin({ordinal});auto bc=unit(12,1,100,100,true);bc->order=113;bc->order_state=2;bc->energy=75*256;
  movement_effects::Image image{};auto sprite=static_cast<bw::SpriteScr*>(bc->flingy.sprite);sprite->first_image=&image;
  image.parent=sprite;image.image_id=543;image.script.header=4512;image.script.animation=0;
  U32 native_frames=0,fast_frames=0,waits=0,casts=0;
  for(U32 pos=4524;pos<=4641;){
   const auto opcode=code[pos];if(opcode==39){++casts;break;}
   if(opcode==5){image.script.pos=std::uint16_t(pos+2);image.script.wait=code[pos+1];native_frames+=image.script.wait+1;
    pulse(100+waits);fast_frames+=image.script.wait+1;++waits;CHECK(image.script.pos==pos+2);
    rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==0);pos+=2;
   }else if(opcode==0||opcode==24)pos+=3;else {CHECK(opcode==46);++pos;}
  }
  CHECK(waits==22&&casts==1&&native_frames==66&&fast_frames==22);
  CHECK(bc->energy==75*256&&bc->order==113&&bc->order_state==2&&bc->order_signal==0);
  image.script.pos=4644;image.script.wait=2;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2); // post-launch retained
  image.script.pos=4533;
  for(U32 id:{12u,27u,28u,29u,102u}){bc->unit_id=std::uint16_t(id);image.script.wait=2;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==0);}
  bc->unit_id=12;bc->player=6;image.script.wait=2;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2);bc->player=1;
  bc->lockdown_timer=1;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2);bc->lockdown_timer=0;
  bc->order=6;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2);bc->order=113;
  image.image_id=542;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2);image.image_id=543;
  image.script.header=4513;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2);image.script.header=4512;
  rework_fixture::ranks[ordinal]=0;rework_combat_v5::accelerate_yamato(bc);CHECK(image.script.wait==2);
  finish();
 }
}
inline void run_qa29_groups(){qa29_yamato_preparation_preserves_native_launch_and_cost();qa29_stat_indexes_match_linear_values_and_reset();qa29_marine_burst_keeps_primary_and_two_small_extras();qa29_bc_auto_yamato_counts_primary_attacks_only();qa29_air_control_and_procurement_are_bounded();qa29_bc_moving_fire_keeps_destination_and_native_disable_guards();qa29_native_ultra_armor_gate_honors_research_in_both_modes();qa29_native_ultra_registration_rejects_changed_code();}
}
