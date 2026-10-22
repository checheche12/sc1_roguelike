#pragma once
// Isolated marker-only single-player sandbox. No mailbox or campaign database.
#include "effect_lab.generated.h"
namespace effect_lab {
inline campaign_config::Mission mission{101,0,0,1,256,256,"SC1_EFFECT_LAB_V1_QA65",false,205};
inline std::vector<rework_combat_v5::Identity> test_units;
inline bool matches(const U8* data,std::size_t size) noexcept {
 if(!data||size<8)return false;bool marker=false,dimensions=false,version=false;std::size_t at=0;
 while(at+8<=size){const U32 n=u32(data+at+4);if(n>size-at-8)return false;const auto value=data+at+8;
  if(!std::memcmp(data+at,"DIM ",4)&&n==4)dimensions=u16(value)==256&&u16(value+2)==256;
  if(!std::memcmp(data+at,"VER ",4)&&n==2)version=u16(value)==205;
  if(!std::memcmp(data+at,"STR ",4)&&n>=2){const U32 count=u16(value);if(2u+count*2u>n)return false;
   for(U32 i=0;i<count;i++){const U32 offset=u16(value+2+i*2),len=U32(std::strlen(mission.marker));
    if(offset>=2+count*2&&offset+len<n&&!std::memcmp(value+offset,mission.marker,len)&&!value[offset+len])marker=true;
   }
  }at+=8+n;
 }return at==size&&marker&&dimensions&&version;
}
inline bool set_talent(GrowthSnapshot& snapshot,U32 index,U32 value) noexcept {
 if(index>=std::size(effect_lab_data::talents))return false;const auto& r=effect_lab_data::talents[index];if(value>r.maximum)return false;
 auto& word=r.word<=16?snapshot.talent_bits[r.word-1]:snapshot.talent_ranks[r.word-33];
 const U32 mask=((1u<<r.width)-1u)<<r.shift;word=(word&~mask)|((r.width==1?(value?1u:0u):value)<<r.shift);
 if(r.slot<32)snapshot.talent_ranks[r.slot]=value;return true;
}
inline void help(){message("EFFECT LAB: -t INDEX RANK | -c INDEX STACKS | -clear | -reset | -case 1..8 | -spawn UNIT COUNT OWNER(0/6) | -heal | -hurt | -up ID LEVEL | -wave. See Effect_Checklist.html.");}
inline void heal(bool);
inline bool apply(const GrowthSnapshot& snapshot){if(!apply_snapshot(nullptr,snapshot)){message("LAB: effect update rejected; previous effects retained.");return false;}heal(false);return true;}
inline bw::Unit* add(U32 id,U32 owner,int x,int y){auto u=spawn(id,x,y,owner);if(u){refresh_units();rework_combat_v5::created(u);test_units.push_back(rework_combat_v5::identity(u));}return u;}
inline void clear_units(){auto previous=std::move(test_units);test_units.clear();for(const auto& who:previous)if(auto u=rework_combat_v5::resolve(who))if(rework_combat_v5::native_kill)rework_combat_v5::native_kill(u);}
inline void make_case(U32 kind){
 clear_units();std::vector<U32> ids;
 switch(kind){case 1:ids={38,53};break;case 2:ids={103};break;case 3:ids={43};break;case 4:ids={44};break;case 5:ids={45,9,1,46,67,63,71};break;case 6:ids={124,144,162};break;case 7:ids={11,42,69};break;case 8:ids={10,32,39,65,68};break;default:message("LAB: choose -case 1..8");return;}
 for(U32 i=0;i<ids.size();i++)add(ids[i],0,2400+int(i%4)*128,2400+int(i/4)*128);
 if(kind==7){for(U32 i=0;i<24;i++)add(0,0,2400+int(i%8)*48,2800+int(i/8)*48);}
 else for(U32 i=0;i<12;i++)add(i<6?7u:42u,6,2528+int(i%4)*56,2400+int(i/4)*56);
 message("LAB: test squad at tile75,75. Lurker must burrow. Select enemies with A+click or right-click. -heal refills.");
}
inline void heal(bool hurt){living_units([&](bw::Unit* u){if(u->player!=0&&u->player!=6)return;
 const auto hp=effective_max_hp(u);if(!hp)return;if(g.set_hp)g.set_hp(u,int(hurt&&u->player==0?hp/2:hp));
 u->shields=int(effective_max_shields(u)*256/(hurt&&u->player==0?2:1));if(!hurt)u->energy=65535;
 });}
inline void wave(){
 // Use the production curse roster construction with the selected curse slots.
 rework_waves::enabled();if(!rework_waves::current){message("LAB: no wave profile");return;}
 static sc1_native::campaign_wave_config::Origin origin{};
 for(const auto& r:sc1_native::campaign_wave_config::kOrigins)if(r.mission_id==mission.mission_id){origin=r;break;}
 origin.owner=6;origin.center={6800,6800};origin.target={2400,2400};origin.cell_count=32;
 for(U32 i=0;i<32;i++)origin.cells[i]={6600+int(i%8)*64,6600+int(i/8)*64};
 rework_waves::primary=&origin;rework_waves::timeline.ordinal++;rework_waves::unit_ordinal=0;g.current_wave_id=++g.next_wave_id;
 rework_waves::selected={0,0};rework_waves::main_wave();
 for(const auto& r:rework_waves::policy::kRosters)if(rework_curses::count(r.slot))rework_waves::roster(r);
 rework_waves::primary=nullptr;message("LAB: production added-wave roster spawned with current curses.");
}
inline bool command(const char* input) {
 if(!enabled||!g.active||!g.applied||!input||input[0]!='-')return false;
 char op[24]{};unsigned a=0,b=1,c=0;const int count=sscanf_s(input,"%23s %u %u %u",op,unsigned(sizeof(op)),&a,&b,&c);
 auto snapshot=g.growth;
 if(!std::strcmp(op,"-help")){help();return true;}
 if(!std::strcmp(op,"-race")&&count==2){if(a<1||a>3){message("LAB: -race 1 Terran /2 Zerg /3 Protoss");return true;}mission.race=a;mission.mission_id=a==1?101:a==2?201:301;message("LAB: campaign race context changed; -clear then reapply start effects.");return true;}
 if(!std::strcmp(op,"-t")&&count>=2){if(!set_talent(snapshot,a,b)){message("LAB: invalid talent index/rank");return true;}apply(snapshot);return true;}
 if(!std::strcmp(op,"-c")&&count>=2){if(a>=frozen::kCurseCount||b>std::min(255u,frozen::kCurseMaxStacks[a])){message("LAB: invalid curse index/stacks");return true;}snapshot.curse_counts[a]=U8(b);apply(snapshot);return true;}
 if(!std::strcmp(op,"-clear")||!std::strcmp(op,"-reset")){snapshot={};snapshot.wire_version=2;snapshot.completed_phase=1;apply(snapshot);if(!std::strcmp(op,"-reset")){
  std::vector<rework_combat_v5::Identity> removed;living_units([&](bw::Unit* u){if((u->player==0||u->player==6)&&u->unit_id<106&&u->unit_id!=101)removed.push_back(rework_combat_v5::identity(u));});
  for(const auto& who:removed)if(auto u=rework_combat_v5::resolve(who))if(rework_combat_v5::native_kill)owner_kill_hook(u,rework_combat_v5::native_kill);
  test_units.clear();rework_combat_v5::reset();rework_combat_v5::bind();
  for(U32 i=0;i<std::size(effect_lab_data::roster);i++)spawn(effect_lab_data::roster[i],512+int(i%10)*128,512+int(i/10)*128,0);
  make_case(1);
 }message("LAB: all effects cleared");return true;}
 if(!std::strcmp(op,"-case")&&count==2){make_case(a);return true;}
 if(!std::strcmp(op,"-spawn")&&count>=2){if(a>=189||b>50||(c!=0&&c!=6)){message("LAB: invalid unit/count/owner");return true;}for(U32 i=0;i<b;i++)add(a,c,2400+int(i%8)*96,3200+int(i/8)*96);return true;}
 if(!std::strcmp(op,"-heal")||!std::strcmp(op,"-hurt")){heal(!std::strcmp(op,"-hurt"));return true;}
 if(!std::strcmp(op,"-up")&&count>=3){if(a>=61||b>255){message("LAB: invalid upgrade");return true;}auto slot=rework_upgrade_storage::slot(0,a);if(slot)*slot=U8(b);return true;}
 if(!std::strcmp(op,"-wave")){wave();return true;}
 return false;
}
using ChatOriginal=void (__cdecl*)(const U8*,U32);
inline void __cdecl chat(const U8* data,U32 length,U32 player,U32,ChatOriginal original) noexcept {
 // Standard chat command5c: one-byte target followed by 80-byte text.
 if(enabled&&player==0&&data&&length==82&&data[0]==0x5c){char text[81]{};std::memcpy(text,data+2,80);text[80]=0;try{if(command(text))return;}catch(...){message("LAB: command failed; use -reset");return;}}
 original(data,length);
}
inline void start(){
 enabled=true;mission.mission_id=101;mission.race=1;test_units.clear();g.mission=&mission;g.campaign_index=g.game()->campaign_mission;g.game_thread=GetCurrentThreadId();g.active=true;refresh_units();
 GrowthSnapshot snapshot{};snapshot.wire_version=2;snapshot.completed_phase=1;if(!apply(snapshot)){enabled=false;g.active=false;return;}help();
}
inline void step(){
 if(rework_waves::enabled())rework_waves::timeline.advance(*rework_waves::current,g.game()->frame_count,true,false,true);
 apply_unit_motion();max_hp_cache::publish();multi_target::step();rework_combat_v5::step();rework_economy_v5::step();rework_cargo_v5::step();
 rework_energy_ui::publish();yamato_cost_ui::publish();spell_energy_check::publish();siege_move_ui::publish();rework_economy_ui::publish(false);rework_shield_ui_v5::publish(false);rework_waves::release_and_orders();wave_targeting::step(true,false);area_visuals::publish();
}
}
