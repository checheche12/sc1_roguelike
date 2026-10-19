#pragma once
namespace host_test {
inline constexpr std::size_t qa37_group_count=4;
namespace qa37_fixture {
inline GrowthSnapshot manuals(U32 stacks){auto s=economy_snapshot({31,112});for(U32 ord:{31u,112u})s.talent_ranks[rework_catalog::kRankSlots[ord]]=stacks;return s;}
inline U32 observed_damage=0;
inline void __cdecl stock_interceptor_impact(bw::Bullet* b){observed_damage=raw_value(1,14,79);b->target.unit->flingy.hitpoints-=int(observed_damage*256);}
inline void __cdecl die(bw::Unit* u){u->order=0;u->flingy.hitpoints=0;}
inline void __cdecl native_expiry(bw::Unit* u){if(u->death_timer&&!--u->death_timer)owner_kill_hook(u,die);}
inline void __cdecl timer_only_expiry(bw::Unit* u){if(u->death_timer&&!--u->death_timer)die(u);}
inline U32 __cdecl original_base(const bw::Unit*,U32 weapon){return raw_value(1,14,weapon&255u);}
inline U32 __cdecl original_bonus(const bw::Unit*,U32 weapon){return 3*raw_value(1,15,weapon&255u);}
inline U32 __cdecl write(std::size_t at,const U8* bytes,std::size_t size){std::memcpy(reinterpret_cast<void*>(at),bytes,size);return FlushInstructionCache(GetCurrentProcess(),reinterpret_cast<void*>(at),size)!=0;}
struct CarrierImage {
 U8* base=nullptr;
 CarrierImage(){
  using namespace carrier_weapon_ui;CHECK(!code&&!queued);
  base=static_cast<U8*>(VirtualAlloc(nullptr,native_engine_hooks::kImageSize,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
  for(U32 i=0;i<2;i++)std::memcpy(base+sites[i],calls[i],5);
  std::memcpy(base+sites[0]+5,base_result,sizeof(base_result));std::memcpy(base+sites[1]+5,bonus_result,sizeof(bonus_result));
  std::memcpy(base+getters[0],base_getter,sizeof(base_getter));std::memcpy(base+getters[1],bonus_getter,sizeof(bonus_getter));
 }
 ~CarrierImage(){carrier_weapon_ui::dispose();VirtualFree(base,0,MEM_RELEASE);}
 void install(){CHECK(carrier_weapon_ui::register_at(base,write));CHECK(carrier_weapon_ui::verify_at(base));carrier_weapon_ui::original_base=original_base;carrier_weapon_ui::original_bonus=original_bonus;}
 U32 query(const bw::Unit* unit,U32 weapon,bool bonus=false){
  using namespace carrier_weapon_ui;const auto site=sites[bonus?1:0];U8 saved[16];std::memcpy(saved,base+site+5,sizeof(saved));
  const U8 ret[]={0x0f,0xb7,0xc0,0x48,0x83,0xc4,0x28,0xc3};std::memcpy(base+site+5,ret,sizeof(ret));
  const U8 entry[]={0x48,0x83,0xec,0x28};std::memcpy(base+0x10000,entry,sizeof(entry));native_engine_hooks::absolute_jump(base+0x10004,base+site);
  FlushInstructionCache(GetCurrentProcess(),base,native_engine_hooks::kImageSize);
  using Query=U32 (__cdecl*)(const bw::Unit*,U32);const auto value=reinterpret_cast<Query>(base+0x10000)(unit,weapon);
  std::memcpy(base+site+5,saved,sizeof(saved));FlushInstructionCache(GetCurrentProcess(),base+site+5,sizeof(saved));return value;
 }
};
}
inline void qa37_manuals_separate_ground_air_and_interceptor_damage(){
 for(U32 stacks=1;stacks<=4;stacks++){
  qa13_fixture::begin();CHECK(apply_snapshot(nullptr,qa37_fixture::manuals(stacks)));
  for(U32 id:{8u,21u,70u,80u,88u,73u,12u,27u,28u,29u,102u,58u,60u,71u,86u,98u})for(U32 field:{17u,19u}){
   const auto weapon=original_stat({0,field,id});if(weapon>=130)continue;
   U32 per=3;if(id==73)per=1;else if(rework_combat_v5::in(id,{8,21}))per=field==19?12:6;
   else if(rework_combat_v5::in(id,{70,80,88,12,27,28,29,102}))per=6;
   CHECK(owner_stat(1,{1,14,weapon})==original_stat({1,14,weapon})+per*stacks);
   for(U32 owner:{2u,6u,11u})CHECK(owner_stat(owner,{1,14,weapon})==original_stat({1,14,weapon}));
   CHECK(owner_stat(1,{1,15,weapon})==original_stat({1,15,weapon}));
  }
  auto interceptor=rework_fixture::unit(73,1,100,100,true),victim=rework_fixture::unit(37,6,120,100);
  auto shot=rework_fixture::bullet(interceptor,victim,79);qa37_fixture::observed_damage=0;
  owner_missile_hook(shot,qa37_fixture::stock_interceptor_impact);
  CHECK(qa37_fixture::observed_damage==6+stacks);CHECK(raw_value(1,14,79)==6);
  auto own=add(72,1,100,100);own->flags=5;CHECK(std::abs(rework_combat_v5::cooldown_ratio(own,79)-std::pow(0.955,double(stacks)))<0.00001);
  qa13_fixture::end();
 }
}
inline void qa37_illusion_blast_half_hp_shields_cap_and_full_area(){
 using namespace rework_fixture;
 for(auto pair:{std::pair<U32,U32>{0,20},{65,80},{66,90},{68,150}}){
  qa9_fixture::begin({147});auto illusion=unit(pair.first,1,300,300);illusion->flags|=0x40000000u;illusion->flingy.hitpoints=0;illusion->shields=0;rework_combat_v5::state(illusion)->materialized=true;
  std::vector<bw::Unit*> enemies;for(int i=0;i<12;i++)enemies.push_back(unit(37,6,310+i*3,300));
  auto edge=unit(43,6,428,300,true),outside=unit(37,6,429,300),ally=unit(37,1,320,300),neutral=unit(37,11,320,300);
  CHECK(original_stat({1,13,84})<=128);rework_combat_v5::death(illusion);
  for(auto target:enemies)CHECK(target->flingy.hitpoints==256000-int(pair.second*256));
  CHECK(edge->flingy.hitpoints==256000-int(pair.second*256));CHECK(outside->flingy.hitpoints==256000&&ally->flingy.hitpoints==256000&&neutral->flingy.hitpoints==256000);
  const auto after=edge->flingy.hitpoints;rework_combat_v5::death(illusion);CHECK(edge->flingy.hitpoints==after);qa9_fixture::end();
 }
}
inline void qa37_illusion_expiry_and_native_kill_do_not_double_blast(){
 using namespace rework_fixture;
 for(auto timers:{qa37_fixture::native_expiry,qa37_fixture::timer_only_expiry}){
  qa9_fixture::begin({147});auto illusion=unit(65,1,100,100),enemy=unit(37,6,120,100);illusion->flags|=0x40000000u;illusion->death_timer=2;rework_combat_v5::state(illusion)->materialized=true;
  owner_timer_hook(illusion,timers);CHECK(enemy->flingy.hitpoints==256000&&illusion->death_timer==1);
  owner_timer_hook(illusion,timers);CHECK(enemy->flingy.hitpoints==256000-80*256);
  owner_timer_hook(illusion,timers);owner_kill_hook(illusion,qa37_fixture::die);CHECK(enemy->flingy.hitpoints==256000-80*256);qa9_fixture::end();
 }
 for(U32 mode=0;mode<3;mode++){
  qa9_fixture::begin({147});auto illusion=unit(65,mode==0?6:1,100,100),enemy=unit(37,6,120,100);if(mode!=1)illusion->flags|=0x40000000u;illusion->death_timer=1;if(mode!=2)rework_combat_v5::state(illusion)->materialized=true;
  owner_timer_hook(illusion,qa37_fixture::native_expiry);CHECK(enemy->flingy.hitpoints==256000);qa9_fixture::end();
 }
}
inline void qa37_native_carrier_tooltip_uses_interceptor_owner_cache(){
 using namespace qa37_fixture;
 for(U32 stacks=1;stacks<=4;stacks++){
  qa13_fixture::begin();auto own=add(72,1,100,100),hero=add(82,1,100,100),enemy=add(72,6,100,100),ally=add(72,2,100,100),neutral=add(72,11,100,100);CHECK(apply_snapshot(nullptr,manuals(stacks)));
  CarrierImage image;image.install();const auto storage_before=storage;
  for(auto unit:{own,hero,enemy,ally,neutral}){CHECK(image.query(unit,79)==(unit->player==1?6+stacks:6));CHECK(image.query(unit,79,true)==3);}
  CHECK(image.query(own,0x1004fu)==6+stacks);
  max_hp_cache::owner_weapon_values[1*260+130+79].store(2);CHECK(image.query(own,79,true)==6&&image.query(enemy,79,true)==3);max_hp_cache::publish(true);
  own->flags|=0x40000000u;CHECK(image.query(own,79)==6);own->flags&=~0x40000000u;
  max_hp_cache::sequence.fetch_add(1);CHECK(image.query(own,79)==6);max_hp_cache::sequence.fetch_add(1);
  bw::Unit external{};external.unit_id=72;external.player=1;CHECK(image.query(&external,79)==6);
  for(U32 i=0;i<2;i++){
   alignas(16) std::uint64_t stack[128]{};auto entry=stack+64;*entry=0x12345678;
   CONTEXT context{};context.Rip=reinterpret_cast<DWORD64>(carrier_weapon_ui::code+i*512+7);context.Rsp=reinterpret_cast<DWORD64>(entry)-0xc8;
   DWORD64 base=0;auto function=RtlLookupFunctionEntry(context.Rip,&base,nullptr);CHECK(function&&base==reinterpret_cast<DWORD64>(carrier_weapon_ui::code));
   PVOID handler=nullptr;DWORD64 frame=0;RtlVirtualUnwind(UNW_FLAG_NHANDLER,base,context.Rip,function,&context,&handler,&frame,nullptr);CHECK(context.Rip==*entry&&context.Rsp==reinterpret_cast<DWORD64>(entry+1));
  }
  const auto site=carrier_weapon_ui::sites[0];auto saved=image.base[site];image.base[site]^=1;CHECK(!carrier_weapon_ui::verify_at(image.base)&&!carrier_weapon_ui::activated.load());CHECK(carrier_weapon_ui::base_value(own,79)==6);image.base[site]=saved;CHECK(carrier_weapon_ui::verify_at(image.base));
  CHECK(storage==storage_before);qa13_fixture::end();
 }
}
inline void run_qa37_groups(){qa37_manuals_separate_ground_air_and_interceptor_damage();qa37_illusion_blast_half_hp_shields_cap_and_full_area();qa37_illusion_expiry_and_native_kill_do_not_double_blast();qa37_native_carrier_tooltip_uses_interceptor_owner_cache();}
}
