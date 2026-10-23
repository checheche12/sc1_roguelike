#pragma once
namespace host_test {
namespace shield_ui_fixture {
inline std::vector<std::pair<std::size_t,std::vector<U8>>> writes;
inline bool reject=false;inline U32 formatted=~0u,native_calls=0;
inline std::atomic<bool> synthetic_transient{false};inline std::atomic<U32> synthetic_level{0};
inline U32 __cdecl writer(std::size_t at,const U8* data,std::size_t n){if(reject)return 0;writes.push_back({at,std::vector<U8>(data,data+n)});return 1;}
inline U32 __cdecl level(U32 owner,U32 upgrade){++native_calls;CHECK(upgrade==15);return synthetic_transient.load()?synthetic_level.load():rework_upgrade_storage::level(owner,upgrade);}
inline void* __cdecl text(void* out,U32){static const char name[]="native localized shield label";*static_cast<const char**>(out)=name;return out;}
inline U32 __cdecl format(void*,U32 length,const char*,const char*,const char*,std::uintptr_t zero,U32 number){CHECK(length==128&&zero==0);formatted=number;return 0;}
inline GrowthSnapshot snapshot(){GrowthSnapshot s{};s.wire_version=2;s.completed_phase=1;const U32 bit=238+113;s.talent_bits[bit/32]|=1u<<(bit%32);return s;}
struct Image {
 U8* base=nullptr;U8* previous_verified_base=nullptr;
 Image(){using namespace rework_shield_ui_v5;CHECK(!code);writes.clear();reject=false;native_calls=0;synthetic_transient=false;
  base=static_cast<U8*>(VirtualAlloc(nullptr,0x1460000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
  previous_verified_base=native_engine_hooks::verified_base;native_engine_hooks::verified_base=base;
  std::memcpy(base+0x3f3237,selected_original,sizeof(selected_original));std::memcpy(base+call_rva,call_original,5);
  std::memcpy(base+0x3f3243,result_original,sizeof(result_original));std::memcpy(base+getter_rva,getter_original,sizeof(getter_original));std::memcpy(base+0x3f328a,formatter_original,sizeof(formatter_original));
  // Exact retained native shield tooltip branch, including its AL→EDI read,
  // localization lookups and seventh formatter argument at caller[RSP+30].
  const U8 middle[]={0x48,0x8d,0x4c,0x24,0x48,0xe8,0x9b,0xc2,0,0,0x90,0x48,0x8b,0x18,0x41,0x0f,0xb7,0x4f,0x0c,0x4c,0x8d,0x25,0x9b,0xcd,0xc0,0xff,0x41,0x0f,0xb7,0x94,0x4c,0x20,0xdc,0xe5,0,0x48,0x8d,0x4c,0x24,0x70,0xe8,0x78,0xc2,0,0,0x90,0x4c,0x8b,0x08,0x48,0x8d,0x0d,0xb5,0x87,0x6f,0,0x4c,0x8d,0x05,0xae,0x83,0x6f,0};
  std::memcpy(base+0x3f324b,middle,sizeof(middle));
  native_engine_hooks::absolute_jump(base+0x3d4d40,reinterpret_cast<void*>(level)); // SAMASE's native authoritative upgrade provider.
  native_engine_hooks::absolute_jump(base+0x3ff4f0,reinterpret_cast<void*>(text));
  native_engine_hooks::absolute_jump(base+0x5e1cb0,reinterpret_cast<void*>(format));
  const U8 start[]={0x55,0x53,0x56,0x57,0x41,0x54,0x41,0x57,0x48,0x81,0xec,0x08,0x01,0,0,0x48,0x8d,0xac,0x24,0xc0,0,0,0,0x49,0x89,0xd7};
  std::memcpy(base+0x10000,start,sizeof(start));native_engine_hooks::absolute_jump(base+0x10000+sizeof(start),base+0x3f3237);
  const U8 finish[]={0x89,0xf8,0x48,0x81,0xc4,0x08,0x01,0,0,0x41,0x5f,0x41,0x5c,0x5f,0x5e,0x5b,0x5d,0xc3};std::memcpy(base+0x3f32af,finish,sizeof(finish));
  CHECK(FlushInstructionCache(GetCurrentProcess(),base,0x1460000));
 }
 ~Image(){rework_shield_ui_v5::dispose();abandon_session();native_engine_hooks::verified_base=previous_verified_base;if(base)VirtualFree(base,0,MEM_RELEASE);}
 void install(){CHECK(rework_shield_ui_v5::register_at(base,writer));CHECK(writes.size()==1);for(auto& w:writes)std::memcpy(reinterpret_cast<void*>(w.first),w.second.data(),w.second.size());FlushInstructionCache(GetCurrentProcess(),base,0x1460000);CHECK(rework_shield_ui_v5::verify_at(base));}
 U32 query(bw::Unit* u){std::memcpy(base+0x10a4458,&u,sizeof(u));alignas(16) U8 icon[32]{};formatted=~0u;using Query=U32 (__cdecl*)(bw::Unit*,void*);const auto number=reinterpret_cast<Query>(base+0x10000)(u,icon);CHECK(formatted==number);return number;}
};
inline void set_level(U32 player,U8 value){auto slot=rework_upgrade_storage::slot(player,15);CHECK(slot);*slot=value;}
inline void publish(){CHECK(max_hp_cache::publish(true));CHECK(rework_shield_ui_v5::publish(true));}
}
void rework_shield_ui_native_branch_and_eligibility(){
 using namespace shield_ui_fixture;reset();Image image;image.install();
 auto soldier=add(65,1,0,0),hero=add(77,1,0,0),probe=add(64,1,0,0),building=add(154,1,0,0),enemy=add(65,6,0,0),terran=add(0,1,0,0),illusion=add(65,1,0,0);illusion->flags|=0x40000000u;
 set_level(1,3);set_level(6,6);
 for(auto u:{soldier,hero,probe,building,terran,illusion})CHECK(image.query(u)==3);CHECK(image.query(enemy)==6);
 CHECK(apply_snapshot(nullptr,snapshot()));publish();
 CHECK(image.query(soldier)==4);CHECK(image.query(hero)==4);CHECK(image.query(probe)==3);CHECK(image.query(building)==3);CHECK(image.query(terran)==3);CHECK(image.query(illusion)==3);CHECK(image.query(enemy)==6);
 const auto baseline=native_calls;for(auto u:{soldier,hero,probe,building,terran,illusion})image.query(u);CHECK(native_calls==baseline);
 set_level(1,0);publish();CHECK(image.query(soldier)==1);CHECK(image.query(probe)==0);
 set_level(1,255);publish();CHECK(image.query(soldier)==255);CHECK(image.query(probe)==255);
 GrowthSnapshot none{};none.wire_version=2;none.completed_phase=2;CHECK(apply_snapshot(nullptr,none));CHECK(!rework_shield_ui_v5::publish());set_level(1,7);CHECK(image.query(soldier)==7);
}
void rework_shield_ui_scoped_research_and_lifecycle(){
 using namespace shield_ui_fixture;reset();Image image;image.install();auto soldier=add(65,1,0,0),probe=add(64,1,0,0),building=add(154,1,0,0),enemy=add(65,6,0,0);CHECK(apply_snapshot(nullptr,snapshot()));
 std::array<U8,61*12> levels{};samase::ExtendedArray arrays[1]{};arrays[0].pointer=levels.data();arrays[0].end=levels.data()+levels.size();auto old=g.extended;const auto old_count=g.extended_count;g.extended=arrays;g.extended_count=1;
 levels[15*12+1]=5;levels[15*12+6]=8;game.upgrade_level_sc[1][15]=1;publish();
 {rework_upgrade_storage::View scope;CHECK(scope.begin(1,15,6));CHECK(rework_upgrade_storage::level(1,15)==6);CHECK(image.query(soldier)==6);CHECK(image.query(probe)==5);CHECK(image.query(building)==5);CHECK(image.query(enemy)==8);}
 CHECK(levels[15*12+1]==5&&game.upgrade_level_sc[1][15]==1);
 U32 result=99;CHECK(!rework_shield_ui_v5::cached(nullptr,result)&&result==99);bw::Unit outside{};outside.player=1;outside.unit_id=65;CHECK(!rework_shield_ui_v5::cached(&outside,result));
 CHECK(!rework_shield_ui_v5::cached(reinterpret_cast<bw::Unit*>(reinterpret_cast<U8*>(soldier)+1),result));
 rework_shield_ui_v5::sequence.fetch_add(1);CHECK(!rework_shield_ui_v5::cached(soldier,result));rework_shield_ui_v5::sequence.fetch_add(1);
 soldier->player=6;CHECK(image.query(soldier)==8);soldier->player=1;soldier->minor_unique_index++;CHECK(image.query(soldier)==6);
 soldier->flags|=0x40000000u;CHECK(image.query(soldier)==5);soldier->flags&=~0x40000000u;
 levels[15*12+1]=7;publish();CHECK(image.query(soldier)==8);rework_shield_ui_v5::reset();CHECK(image.query(soldier)==7);
 g.extended=old;g.extended_count=old_count;
}
void rework_shield_ui_unwind_and_integrity(){
 using namespace shield_ui_fixture;using namespace rework_shield_ui_v5;reset();Image fixture;
 for(U32 rva:{call_rva,0x3f3237u,0x3f3243u,getter_rva,0x3f328au}){const auto saved=fixture.base[rva];fixture.base[rva]^=1;CHECK(!register_at(fixture.base,writer));CHECK(!code&&writes.empty());fixture.base[rva]=saved;}
 reject=true;CHECK(!register_at(fixture.base,writer));CHECK(!code);reject=false;fixture.install();
 alignas(16) std::uint64_t stack[128]{};auto entry=stack+64;constexpr std::uint64_t ret=0x123456789abull;*entry=ret;
 struct Point{DWORD offset;bool allocated;};const Point points[]={{0,false},{7,true},{48,true},{runtime.EndAddress-8,true},{runtime.EndAddress-1,false}};
 for(const auto p:points){CONTEXT context{};context.ContextFlags=CONTEXT_FULL;context.Rip=reinterpret_cast<DWORD64>(code+p.offset);context.Rsp=reinterpret_cast<DWORD64>(entry)-(p.allocated?0xc8:0);context.Rbx=11;context.Rbp=12;context.Rsi=13;context.Rdi=14;context.R12=15;context.R15=16;
  DWORD64 found=0;auto function=RtlLookupFunctionEntry(context.Rip,&found,nullptr);CHECK(function&&found==reinterpret_cast<DWORD64>(code));PVOID data=nullptr;DWORD64 establisher=0;RtlVirtualUnwind(UNW_FLAG_NHANDLER,found,context.Rip,function,&context,&data,&establisher,nullptr);CHECK(context.Rip==ret&&context.Rsp==reinterpret_cast<DWORD64>(entry+1));CHECK(context.Rbx==11&&context.Rbp==12&&context.Rsi==13&&context.Rdi==14&&context.R12==15&&context.R15==16);
 }
 for(U32 rva:{call_rva,0x3f3237u,0x3f3243u,getter_rva,0x3f328au}){const auto saved=fixture.base[rva];fixture.base[rva]^=1;CHECK(!verify_at(fixture.base));CHECK(!activated.load());fixture.base[rva]=saved;CHECK(verify_at(fixture.base));}
 const auto saved=code[20];DWORD old=0;CHECK(VirtualProtect(code,4096,PAGE_EXECUTE_READWRITE,&old));code[20]^=1;CHECK(!verify_at(fixture.base));code[20]=saved;DWORD ignored=0;VirtualProtect(code,4096,old,&ignored);CHECK(verify_at(fixture.base));
}
void rework_shield_ui_concurrent_transient_research(){
 using namespace shield_ui_fixture;reset();Image image;image.install();auto soldier=add(65,1,0,0),probe=add(64,1,0,0),building=add(154,1,0,0);CHECK(apply_snapshot(nullptr,snapshot()));set_level(1,5);publish();
 synthetic_transient=true;synthetic_level=6;const auto before=native_calls;std::atomic<bool> done{false},bad{false};std::atomic<U32> samples{0};
 std::thread render([&](){while(!done.load()){if(rework_shield_ui_v5::value(soldier)!=6||rework_shield_ui_v5::value(probe)!=5||rework_shield_ui_v5::value(building)!=5)bad=true;++samples;}});
 for(U32 i=0;i<20000;i++){synthetic_level=6;YieldProcessor();synthetic_level=5;CHECK(rework_shield_ui_v5::publish());}
 done=true;render.join();CHECK(samples.load()>0);CHECK(!bad.load());CHECK(native_calls==before);synthetic_transient=false;
}
void qa74_shield_refraction_three_matches_native_damage_and_display(){
 using namespace shield_ui_fixture;reset();Image image;image.install();
 auto soldier=add(65,1,0,0),hero=add(77,1,0,0),probe=add(64,1,0,0),building=add(154,1,0,0),enemy=add(65,6,0,0),attacker=add(0,6,0,0);
 soldier->shields=10*256;CHECK(apply_snapshot(nullptr,snapshot()));talent_power::enabled=true;
 for(U32 level:{0u,2u,250u}){
  set_level(1,U8(level));set_level(6,6);publish();
  CHECK(image.query(soldier)==level+3&&image.query(hero)==level+3);
  CHECK(image.query(probe)==level&&image.query(building)==level&&image.query(enemy)==6);
  g.normal_hit=true;std::int32_t damage=10*256;
  {rework_combat_v5::DamageScope scope(soldier,attacker,0,6,damage);CHECK(rework_combat_v5::upgrade_level(1,15)==level+3);CHECK(image.query(soldier)==level+3);}
  CHECK(rework_combat_v5::upgrade_level(1,15)==level);
 }
 talent_power::enabled=false;
}
inline constexpr std::size_t rework_shield_ui_v5_group_count=5;
inline void run_rework_shield_ui_v5_groups(){qa74_shield_refraction_three_matches_native_damage_and_display();rework_shield_ui_native_branch_and_eligibility();rework_shield_ui_scoped_research_and_lifecycle();rework_shield_ui_unwind_and_integrity();rework_shield_ui_concurrent_transient_research();}
}
