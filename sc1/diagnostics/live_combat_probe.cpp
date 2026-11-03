// Compiled only into a private diagnostic overlay. Production source is copied
// byte-for-byte; the wrapper drives fixtures and observes the real engine.
#include "paths.generated.h"
#define samase_plugin_init production_entry
#include "snapshot/plugin/native_plugin.cpp"
#undef samase_plugin_init
#include <share.h>
#include <mutex>
namespace live_audit {
using namespace rework_combat_v5;
using Send=void (__cdecl*)(const void*,U32);
struct Subject {Identity actor{};std::vector<Identity> targets;};
std::array<Subject,9> subjects{};
std::vector<Identity> entities,hold;
FILE* output=nullptr;std::mutex output_mutex;std::atomic<bool> done{false};
U32 phase=0,start=0,last=~0u;bool begun=false;Send send=nullptr;
combat_effects::WeaponDamageFn stock_weapon=nullptr;
void log(const char* fmt,...) noexcept {
 if(!output)return;std::lock_guard<std::mutex> guard(output_mutex);
 va_list args;va_start(args,fmt);std::vfprintf(output,fmt,args);va_end(args);
 std::fputc('\n',output);std::fflush(output);
}
void finish(const char* reason,U32 code) noexcept {
 if(done.exchange(true))return;
 log("{\"event\":\"terminal\",\"status\":\"%s\",\"pid\":%lu,\"phase\":%u,\"controlled_exit\":true}",reason,GetCurrentProcessId(),phase);
 ExitProcess(code);
}
DWORD WINAPI watchdog(void*) noexcept {Sleep(900000);finish("watchdog_timeout",73);return 0;}
bw::Unit* add(U32 id,U32 owner,int x,int y,bool fixed=false) {
 auto u=effect_lab::add(id,owner,x,y);if(!u){finish("create_failed",73);return nullptr;}
 const auto who=identity(u);entities.push_back(who);
 u->flingy.hitpoints=300000*256;u->shields=0;u->energy=200*256;
 if(fixed)hold.push_back(who);
 return u;
}
void target(U32 i,U32 id,U32 owner,int x,int y) {subjects[i].targets.push_back(identity(add(id,owner,x,y,true)));}
void select_send(bw::Unit* u,const U8* data,U32 length) {
 if(!u||!send)return;
 const U32 handle=U32(u-g.units+1)|(U32(u->minor_unique_index)<<(g.units_count>1700?13u:11u));
 U8 selection[]={0x63,1,0,0,0,0};std::memcpy(selection+2,&handle,4);send(selection,6);send(data,length);
}
void targeted_order(bw::Unit* u,bw::Unit* t,U8 order) {
 if(!u||!t)return;
 const U32 handle=U32(t-g.units+1)|(U32(t->minor_unique_index)<<(g.units_count>1700?13u:11u));
 const auto x=t->flingy.position.x,y=t->flingy.position.y;
 U8 data[]={0x61,U8(x),U8(x>>8),U8(y),U8(y>>8),U8(handle),U8(handle>>8),U8(handle>>16),U8(handle>>24),0xe4,0,order,0};
 select_send(u,data,13);
}
void attack(bw::Unit* u,bw::Unit* t) {targeted_order(u,t,8);}
void __cdecl weapon(bw::Unit* t,std::int32_t amount,U8 w,U32 divisor,U8 direction,bw::Unit* source,U32 owner) noexcept {
 if(!begun){stock_weapon(t,amount,w,divisor,direction,source,owner);return;}
 int subject=-1,victim=-1;
 for(U32 i=0;i<subjects.size();i++)for(U32 n=0;n<subjects[i].targets.size();n++)if(generation(subjects[i].targets[n])==t){subject=int(i);victim=int(n);}
 const auto hp=t?t->flingy.hitpoints:0,shield=t?t->shields:0;
 const auto target_id=t?t->unit_id:228u,unique=t?t->minor_unique_index:0u;
 const auto generated=generated_depth;
 stock_weapon(t,amount,w,divisor,direction,source,owner);
 if(subject>=0)log("{\"event\":\"hit\",\"phase\":%u,\"case\":%d,\"victim\":%d,\"frame\":%u,\"weapon\":%u,\"input_q8\":%d,\"divisor\":%u,\"hp_before\":%d,\"hp_after\":%d,\"shields_before\":%d,\"shields_after\":%d,\"generated\":%u,\"target_identity_retained\":%s}",phase,subject,victim,now(),w,amount,divisor,hp,t?t->flingy.hitpoints:0,shield,t?t->shields:0,generated,t&&t->unit_id==target_id&&t->minor_unique_index==unique?"true":"false");
}
void clean() {
 std::vector<Identity> remove;
 living_units([&](bw::Unit* u){if((u->player==0||u->player==6)&&u->unit_id<106&&u->unit_id!=101)remove.push_back(identity(u));});
 for(const auto& who:remove)if(auto u=resolve(who))native_kill(u);
 entities.clear();hold.clear();subjects={};effect_lab::test_units.clear();effect_lab::stationary_targets.clear();
}
void begin() {
 clean();GrowthSnapshot growth{};growth.wire_version=2;growth.completed_phase=1;
 // Four controls: empty, A only, B only, A+B. Other test lanes are spatially
 // isolated. Universal armor-ignore also affects the explicitly listed lane3.
 if(phase&1u)for(U32 ordinal:{16u,48u,49u,65u,83u,80u,45u,100u})effect_lab::set_talent(growth,238u+ordinal,1);
 if(phase&1u)effect_lab::set_talent(growth,238u+244u,4);
 if(phase&2u)for(U32 ordinal:{162u,19u,64u,103u,82u,63u,106u})effect_lab::set_talent(growth,238u+ordinal,1);
 if(!apply_snapshot(nullptr,growth)){finish("apply_failed",73);return;}
 // Ordinary damage and attack-interval controls.
 subjects[0].actor=identity(add(0,0,800,3000));target(0,7,6,960,3000);
 subjects[1].actor=identity(add(1,0,2400,3000));target(1,3,6,2496,3000);target(1,3,6,2540,3000);
 subjects[2].actor=identity(add(47,0,4000,3000));target(2,11,6,4160,3000);
 subjects[3].actor=identity(add(12,0,5600,3000));target(3,7,6,5760,3000);
 // Actual spell casts and boundary targets.
 subjects[4].actor=identity(add(46,0,700,4800));
 target(4,7,0,1000,4800);target(4,7,0,1070,4800);
 subjects[5].actor=identity(add(45,0,2400,4800));
 target(5,7,6,2600,4800);target(5,7,6,2696,4800);target(5,7,6,2744,4800);
 subjects[6].actor=identity(add(1,0,4200,4800));
 target(6,3,6,4360,4800);target(6,0,6,4360,4896);
 subjects[7].actor=identity(add(62,0,5900,4800));
 target(7,8,6,6080,4800);target(7,8,6,6116,4800);
 subjects[8].actor=identity(add(2,0,2400,6500));
 target(8,32,6,2560,6500);target(8,32,6,2584,6500);
 // Remove the two enemy attackers from the lab's stationary-target list.
 for(U32 n=0;n<2;n++) {
  auto u=add(0,6,1000+int(n)*70,4920);auto who=identity(u);
  effect_lab::stationary_targets.erase(std::remove_if(effect_lab::stationary_targets.begin(),effect_lab::stationary_targets.end(),[&](const Identity& v){return v.p==who.p&&v.unique==who.unique;}),effect_lab::stationary_targets.end());
  auto t=resolve(subjects[4].targets[n]);g.order(u,10,t->flingy.position.x,t->flingy.position.y,t,0);
 }
 for(U32 i=0;i<subjects.size();i++)if(auto u=resolve(subjects[i].actor)) {
  if(i==3)u->energy=0;
  log("{\"event\":\"fixture\",\"phase\":%u,\"case\":%u,\"unit\":%u,\"x\":%d,\"y\":%d}",phase,i,u->unit_id,u->flingy.position.x,u->flingy.position.y);
 }
 start=now();begun=true;
 log("{\"event\":\"phase_start\",\"phase\":%u,\"frame\":%u,\"duration\":%u}",phase,start,phase==3?4600u:1440u);
}
void issue() {
 for(U32 i:{0u,1u,2u,3u,7u,8u})attack(resolve(subjects[i].actor),resolve(subjects[i].targets[0]));
 if(auto u=resolve(subjects[4].actor))g.order(u,119,800,4800,nullptr,0);
 if(auto u=resolve(subjects[5].actor))g.order(u,146,2600,4800,nullptr,0);
 // Queue through the native player-command path, including an in-progress
 // no-break firing animation. A direct g.order can silently discard this cast.
 targeted_order(resolve(subjects[6].actor),resolve(subjects[6].targets[0]),115);
 log("{\"event\":\"commands_issued\",\"phase\":%u,\"frame\":%u}",phase,now());
}
void sample(U32 elapsed) {
 for(U32 i=0;i<subjects.size();i++) {
  if(auto u=resolve(subjects[i].actor)) {
   auto s=state(u);
   log("{\"event\":\"actor\",\"phase\":%u,\"case\":%u,\"elapsed\":%u,\"frame\":%u,\"energy\":%u,\"order\":%u,\"shots\":%u,\"primary_attacks\":%u,\"ground_cd\":%u,\"air_cd\":%u}",phase,i,elapsed,now(),u->energy,u->order,s?s->shot_count:0,s?s->bc_primary_attacks:0,u->ground_cooldown,u->air_cooldown);
  }
  for(U32 n=0;n<subjects[i].targets.size();n++)if(auto u=resolve(subjects[i].targets[n])) {
   auto s=state(u);
   log("{\"event\":\"target\",\"phase\":%u,\"case\":%u,\"victim\":%u,\"elapsed\":%u,\"frame\":%u,\"hp_q8\":%d,\"shields_q8\":%d,\"ensnare\":%u,\"strong_ensnare\":%u,\"lockdown\":%u,\"lockdown_reserve\":%u,\"acid\":%u,\"double_acid\":%u,\"x\":%d,\"y\":%d}",phase,i,n,elapsed,now(),u->flingy.hitpoints,u->shields,u->ensnare_timer,s&&s->strong_ensnare?1u:0u,u->lockdown_timer,s?s->lockdown_reserve:0,u->acid_spore_count,s&&s->double_acid?1u:0u,u->flingy.position.x,u->flingy.position.y);
  }
 }
}
void __cdecl tick() noexcept {
 if(done||!effect_lab::enabled||!g.active)return;
 try {
  const U32 frame=now();if(frame==last)return;last=frame;
  if(!begun){begin();return;}const U32 elapsed=frame-start;
  for(const auto& who:hold)if(auto u=resolve(who))if(u->order!=107)g.order(u,107,u->flingy.position.x,u->flingy.position.y,nullptr,0);
  if(elapsed==48)issue();
  if(elapsed==240||elapsed==432)if(!resolve(subjects[2].actor)) {
   subjects[2].actor=identity(add(47,0,4000,3000));attack(resolve(subjects[2].actor),resolve(subjects[2].targets[0]));
  }
  if(elapsed%12==0)sample(elapsed);
  if(elapsed%240==0)log("{\"event\":\"heartbeat\",\"phase\":%u,\"frame\":%u}",phase,frame);
  if(elapsed>=(phase==3?4600u:1440u)) {
   log("{\"event\":\"phase_complete\",\"phase\":%u,\"frame\":%u}",phase,frame);
   if(++phase==4){finish("complete",0);return;}begun=false;
  }
 }catch(...){finish("observer_exception",73);}
}
}
extern "C" __declspec(dllexport) void __cdecl samase_plugin_init(const samase::PluginApi* api) noexcept {
 using namespace live_audit;
 output=_wfsopen(AUDIT_LOG,L"wb",_SH_DENYNO);
 log("{\"event\":\"entry\",\"pid\":%lu,\"schema\":1}",GetCurrentProcessId());
 auto thread=CreateThread(nullptr,0,watchdog,nullptr,0,nullptr);if(thread)CloseHandle(thread);
 production_entry(api);
 stock_weapon=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=weapon;
 send=api->send_command?reinterpret_cast<Send>(reinterpret_cast<GenericFn (__cdecl*)()>(api->send_command)()):nullptr;
 if(!send||!stock_weapon||!api->hook_step_objects(tick,1))finish("registration_failed",73);
 log("{\"event\":\"registered\",\"hooks_ready\":%s}",g.hooks_ready?"true":"false");
}
