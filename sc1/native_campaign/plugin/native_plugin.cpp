// Native campaign prototype. Public SAMASE API44 + pinned bw_dat x64 layout.
// Engine extensions are restricted to the byte-verified SC:R13515 executable.
// No EUD payload is used.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <algorithm>
#include <array>
#include <atomic>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#include <cmath>
#include <deque>
#include <limits>
#include <memory>
#include <numeric>
#include <vector>
#include <unordered_map>
#include "include/samase_api44.h"
#include "include/bw_dat_x64.h"
#include "include/sight_cargo_runtime.h"
#include "include/frozen_catalog.generated.h"
#include "include/rework_catalog.generated.h"
#include "include/rework_wave_profiles.generated.h"
#include "include/campaign_config.generated.h"
#include "include/campaign_waves.generated.h"
#include "mailbox_protocol.h"
#include "include/curse_scaling.h"
#include "wave_runtime.h"
#include "include/wave_timer.h"
#include "include/wave_progression.h"
#include "dialog_ui.h"

namespace {
namespace campaign_config = sc1_native::campaign_config;
using U32 = std::uint32_t;
using U8 = std::uint8_t;
#include "include/objective_guards.generated.h"
using samase::GenericFn;
using sc1_native::GrowthSnapshot;
using sc1_native::ChoiceOffer;
constexpr U32 kOwner = 1, kCounterOwner = 11; // kOwner is retained only for the T01 regression fixture.
constexpr U32 kRouteCounter = 223, kMiddleCounter = 224;
constexpr U32 kReadyCounter = 225, kGoalCounter = 226, kAckCounter = 227;
constexpr U32 kAttackMove = 14;
namespace rework_waves {inline void spell_launched(bw::Unit*,U32) noexcept;}
namespace enemy_detection {inline void note(bw::Unit*,bw::Unit*) noexcept;inline void reset() noexcept;inline void step(bool,bool,bool);}
struct Key { U32 table, field, id; };
struct Edit { Key key; bw::DatTable* table; U32 before, after; };
struct OwnerEdit {Key key;bw::DatTable* table;U32 original,friendly,enemy;};
struct CooldownTrack {U32 weapon=130,reset_frame=0,reset_value=0,fraction=0,denominator=0;bool launched=false,processed=false;};
struct UnitTrack {bool seen=false,spawned=false;U8 unique=0,owner=12,ground=0,air=0;std::uint16_t id=228;U32 base_speed=0,applied_speed=0,last_damage=0,spawn_second=0;std::int32_t hp=0,shields=0;bool elite=false,barrier=false;
    CooldownTrack cooldown[2]{};
    U32 wave_id=0,last_attack_frame=0,last_damage_frame=0,first_attack_end=0,first_attack_bonus=0,command_until=0;
    U32 healed_frame=0,bomb_hit_frame=0,pair_index=0xffffffffu,pair_due=0;U8 pair_unique=0;
    bool medic=false,commander=false,pair_used=false,death_processed=false;
    bool wave_ordered=false,wave_position_seen=false;U32 wave_order_frame=0,wave_position_frame=0;int wave_position_x=0,wave_position_y=0;
};
struct DeathBomb{int x,y;U32 created,due,damage,owner;};
using GetGame = bw::Game* (__cdecl*)();
using GetUnit = bw::Unit* (__cdecl*)();
using GetDat = bw::DatTable* (__cdecl*)(std::size_t*);
using MutateDat = void* (__cdecl*)(U32,U32);
using ReadVars = void (__cdecl*)(const std::uint16_t*,std::size_t*,std::size_t);
using FreeMemory = void (__cdecl*)(U8*);
using CreateUnit = bw::Unit* (__cdecl*)(U32,std::int32_t,std::int32_t,U32,const U8*);
using CreateLone=void* (__cdecl*)(U32,std::int32_t,std::int32_t,U32);
using DamageFn=void (__cdecl*)(bw::Unit*,std::int32_t,bw::Unit*,U32,U32);
using AddOverlay = void* (__cdecl*)(void*,U32,std::int32_t,std::int32_t,U32);
using UnitFn = void (__cdecl*)(bw::Unit*);
using SetHp = void (__cdecl*)(bw::Unit*,std::int32_t);
using IssueOrder = void (__cdecl*)(bw::Unit*,U32,U32,U32,bw::Unit*,U32);
using PrintText = void (__cdecl*)(const U8*);
using ReadMap = U8* (__cdecl*)(const U8*,std::size_t*);
using GetFlag = U32 (__cdecl*)();
using UnitArray = void (__cdecl*)(bw::Unit**,std::size_t*);
struct ProjectileSource {bw::Unit* unit=nullptr;U32 id=228,owner=12,unique=0;};
struct State {
    U32 api_version = 0;
    std::array<GetDat,5> dat_getters{};
    MutateDat mutate_dat = nullptr;
    ReadVars read_vars = nullptr;
    FreeMemory free_memory = nullptr;
    GetGame game = nullptr;
    GetUnit first_active = nullptr, first_hidden = nullptr;
    CreateUnit create = nullptr;
    AddOverlay add_overlay = nullptr;
    DamageFn damage = nullptr;
    CreateLone lone_sprite = nullptr;
    UnitFn finish_pre = nullptr, finish_post = nullptr;
    SetHp set_hp = nullptr;
    IssueOrder order = nullptr;
    PrintText text = nullptr;
    ReadMap read_map = nullptr;
    GetFlag multiplayer = nullptr, replay = nullptr;
    UnitArray unit_array = nullptr;
    samase::ExtendedArray* extended = nullptr;
    std::size_t extended_count = 0;
    bw::Unit* units = nullptr;
    std::size_t units_count = 0;
    sc1_native::MailboxProtocol protocol;
    sc1_native::WaveRuntime waves;
    sc1_native::DialogUi dialog;
    std::vector<Edit> baseline;
    const campaign_config::Mission* mission = nullptr;
    std::vector<Edit> friendly_edits, enemy_edits;
    std::vector<OwnerEdit> owner_edits;
    U32 campaign_index = 0;
    const sc1_native::campaign_wave_config::Origin* pending_origin=nullptr;
    U32 next_wave_second=0,pending_second=0,pending_supply=0,wave_stage=0,wave_spawn_number=0,pending_batch=0;
    U32 next_wave_id=0,current_wave_id=0,pending_wave_id=0,t01_wave_id=0;
    U32 kills_for_wave=0,last_death_wave=0,last_regen_second=0;
    bool death_wave_due=false,normal_hit=false,elite_hit=false;
    GrowthSnapshot growth{};
    std::vector<UnitTrack> tracks;
    std::vector<std::pair<bw::Unit*,U8>> objective_units;
    bw::Unit* tracked_base=nullptr;
    std::array<bool,130> ordinary_weapons{};bool weapon_cache=false;
    std::unordered_map<bw::Bullet*,bool> bullet_elites;
    std::unordered_map<bw::Bullet*,U32> bullet_bonuses;
    std::unordered_map<bw::Bullet*,ProjectileSource> bullet_sources;
    ProjectileSource hit_identity{};bool bullet_hit_context=false;
    std::vector<DeathBomb> bombs;U32 hit_bonus=0,last_diversity_frame=0;bw::Unit* hit_source=nullptr;
    bool active = false, applied = false, offer_active = false, hooks_ready = false;
    bool pumping = false;
    bool survival_hint_shown = false;
    bool campaign_clear_shown = false;
    std::atomic_bool wrong_thread_reported{false};
    std::atomic<DWORD> game_thread{0};
    U32 last_frame = std::numeric_limits<U32>::max(), logged_state = 0;
    U32 last_objectives = std::numeric_limits<U32>::max(), last_leaderboard = std::numeric_limits<U32>::max();
    U32 shown_objectives = std::numeric_limits<U32>::max();
    U32 spawn_attempts = 0;
    U32 applied_phase = 0, observed_phase = 0, phase_frame = 0;
    U32 milestone_barracks = std::numeric_limits<U32>::max();
    U32 milestone_flags = std::numeric_limits<U32>::max();
    std::array<U32,3> objective_counts{{0xffffffffu,0xffffffffu,0xffffffffu}};
    U8 wave_stacks = 0;
    ChoiceOffer offer{};
    const char* apply_failure = nullptr; // Static diagnostic text; no user record/nonce.
} g;
namespace rework_combat_v5 {bool plan_stats(const GrowthSnapshot&,std::vector<Edit>&);double speed_ratio(bw::Unit*);double cooldown_ratio(bw::Unit*,U32);U32 fractional_period(bw::Unit*,U32,U32,double);void growth_applied(const GrowthSnapshot&,const GrowthSnapshot&);bool enhanced_ensnare(bw::Unit*);void hold_ensnare_cooldown(bw::Unit*,U32,U8&,U32=0);}
namespace rework_economy_v5 {bool plan_stats(const GrowthSnapshot&,std::vector<Edit>&);void before_snapshot();void after_snapshot();double motion_ratio(bw::Unit*) noexcept;}
namespace campaign_visibility {void reset() noexcept;}
namespace yamato_cost_ui {void reset() noexcept;void publish() noexcept;}
namespace rework_energy_ui {void reset() noexcept;void publish() noexcept;}
namespace rework_economy_ui {void reset() noexcept;bool publish(bool) noexcept;}
namespace rework_shield_ui_v5 {void reset() noexcept;bool publish(bool) noexcept;}
bw::Unit* spawn(U32,int,int,U32) noexcept;
#include "include/rework_curse_decl.h"
bool verify_stat_engine_after_dat() noexcept;
void heal_enemy(bw::Unit*,U32) noexcept;
U32 charged_attack(bw::Unit*,U32) noexcept;
void note_attack_launch(bw::Unit*,U32) noexcept;
void curse_death(bw::Unit*,bool direct_combat=false);

void log_event(const char* format,...) noexcept {
    char line[2048]; va_list args;va_start(args,format);
    std::vsnprintf(line,sizeof(line),format,args);va_end(args);
    OutputDebugStringA(line);OutputDebugStringA("\n");
#ifndef SC1_NATIVE_HOST_TEST
    // Write beside this local mod DLL, never in the installed game directory.
    HMODULE module=nullptr;
    if (!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                           reinterpret_cast<LPCWSTR>(&log_event),&module)) return;
    wchar_t path[32768];DWORD n=GetModuleFileNameW(module,path,32768);
    if (!n || n>=32768) return;
    auto slash=wcsrchr(path,L'\\');if (!slash) return;
    if (wcscpy_s(slash+1,32768-static_cast<std::size_t>(slash+1-path),L"sc1_native.log")) return;
    HANDLE file=CreateFileW(path,FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if (file==INVALID_HANDLE_VALUE) return;
    SYSTEMTIME t{};GetLocalTime(&t);char prefix[80];
    std::snprintf(prefix,sizeof(prefix),"%04u-%02u-%02u %02u:%02u:%02u.%03u ",t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,t.wMilliseconds);
    DWORD written=0;WriteFile(file,prefix,static_cast<DWORD>(std::strlen(prefix)),&written,nullptr);
    WriteFile(file,line,static_cast<DWORD>(std::strlen(line)),&written,nullptr);WriteFile(file,"\r\n",2,&written,nullptr);CloseHandle(file);
#endif
}
void message(const char* s) noexcept {
    if (g.text) g.text(reinterpret_cast<const U8*>(s));
    log_event("%s",s);
}
void visible_failure(const wchar_t* text) noexcept {
    log_event("Initialization failed; visible Windows diagnostic displayed.");
#ifndef SC1_NATIVE_HOST_TEST
    MessageBoxW(nullptr,text,L"SC1 native campaign",MB_OK|MB_ICONERROR);
#else
    (void)text;
#endif
}
U32 u32(const U8* p) noexcept { U32 v; std::memcpy(&v,p,4); return v; }
std::uint16_t u16(const U8* p) noexcept { std::uint16_t v; std::memcpy(&v,p,2); return v; }
bool same(Key a,Key b) noexcept {return a.table==b.table && a.field==b.field && a.id==b.id;}
#include "include/stat_lookup.h"
#include "include/frame_profile.h"

U32 player_owner() noexcept { return g.mission ? g.mission->owner : kOwner; }
bool is_enemy(U32 owner) noexcept {
    auto game=g.game ? g.game() : nullptr;
    return game && owner<8 && owner!=player_owner() &&
        game->starting_player_types[owner]!=0 && game->starting_player_types[owner]!=3 && game->starting_player_types[owner]!=7 &&
        game->alliances[player_owner()][owner]==0 && game->alliances[owner][player_owner()]==0;
}
// An authenticated per-map marker is necessary but not sufficient: the original
// format, dimensions, human owner and race must agree with the frozen manifest.
std::array<char,80> legacy_mission_marker(const campaign_config::Mission& m) noexcept {
    std::array<char,80> result{};std::snprintf(result.data(),result.size(),"SC1_NATIVE_M%u_V3_SW1_R469",m.mission_id);return result;
}
const campaign_config::Mission* identify_chk(const U8* data,std::size_t size,U32* phase_capability=nullptr) noexcept {
    U32 ver=0; U32 width=0,height=0; const U8* owners=nullptr;const U8* sides=nullptr;
    const campaign_config::Mission* found=nullptr;U32 found_capability=0;
    if (!data || size>16*1024*1024) return nullptr;
    for (std::size_t pos=0;pos<size;) {
        if(size-pos<8)return nullptr;
        const U32 n=u32(data+pos+4);const U8* p=data+pos+8;
        if(n>size-pos-8)return nullptr;const char* tag=reinterpret_cast<const char*>(data+pos);
        if(!std::memcmp(tag,"VER ",4))ver=n==2 ? u16(p) : 0;
        if(!std::memcmp(tag,"DIM ",4) && n==4){width=u16(p);height=u16(p+2);}
        if(!std::memcmp(tag,"OWNR",4) && n==12)owners=p;
        if(!std::memcmp(tag,"SIDE",4) && n==12)sides=p;
        if(!std::memcmp(tag,"STR ",4)){
            if(n<2)return nullptr;U32 count=u16(p);if(2+count*2>n)return nullptr;
            for(U32 i=0;i<count;i++){
                U32 off=u16(p+2+i*2);if(off>=n)continue;
                for(const auto& m:campaign_config::kMissions){
                    const auto old=legacy_mission_marker(m);const auto len=std::strlen(m.marker)+1,old_len=std::strlen(old.data())+1;
                    const U32 capability=n-off>=len && !std::memcmp(p+off,m.marker,len) ? 2u :
                        n-off>=old_len && !std::memcmp(p+off,old.data(),old_len) ? 1u : 0u;
                    if(capability){
                        if(found && (found!=&m || found_capability!=capability))return nullptr;found=&m;found_capability=capability;
                    }
                }
            }
        }
        pos+=8+n;
    }
    if(phase_capability)*phase_capability=found_capability;
    return found && ver==found->chk_version && owners && sides && width==found->width && height==found->height &&
        found->owner<8 && owners[found->owner]==6 && sides[found->owner]==found->race ? found : nullptr;
}
[[maybe_unused]] bool is_our_chk(const U8* data,std::size_t size) noexcept {return identify_chk(data,size)!=nullptr;}

bool reject_growth(const char* reason) noexcept {
    g.apply_failure=reason;
    log_event("Growth apply rejected: reason=%s applied_phase=%u active=%u",reason,g.applied_phase,g.active ? 1u : 0u);
    return false;
}
bw::DatTable* reject_dat(Key k,const char* reason,std::size_t fields=0,const bw::DatTable* t=nullptr) noexcept {
    g.apply_failure=reason;
    log_event("DAT access rejected: reason=%s table=%u field=%u id=%u fields=%zu data_present=%u width=%u entries=%u",
        reason,k.table,k.field,k.id,fields,t && t->data ? 1u : 0u,t ? t->entry_size : 0,t ? t->entries : 0);
    return nullptr;
}
bw::DatTable* table_for(Key k,bool mutate) noexcept {
    // extended_dat is an init-only factory, not the runtime table getter.
    // SAMASE panics if that factory is called while applying a game snapshot.
    if (k.table>=g.dat_getters.size()) return reject_dat(k,"table_id");
    auto getter=g.dat_getters[k.table];
    if (!getter) return reject_dat(k,"missing_getter");
    std::size_t fields=0; auto tables=getter(&fields);
    if (!tables) return reject_dat(k,"getter_null",fields);
    if (k.field>=fields) return reject_dat(k,"field_bounds",fields);
    auto t=tables+k.field;
    if (mutate) {
        if (!g.mutate_dat) return reject_dat(k,"missing_mutate",fields,t);
        // Public AICE caches this direct callback and invokes it from iscript;
        // unlike extended_dat, mutate_dat is a runtime operation.
        // API44 explicitly returns one DatTable descriptor, not its raw data.
        auto changed=static_cast<bw::DatTable*>(g.mutate_dat(k.table,k.field));
        if (!changed) return reject_dat(k,"mutate_rejected",fields,t);
        t=changed;
    }
    if (!t->data) return reject_dat(k,"data_null",fields,t);
    if (k.id>=t->entries) return reject_dat(k,"entry_bounds",fields,t);
    if (t->entry_size!=1 && t->entry_size!=2 && t->entry_size!=4) return reject_dat(k,"entry_width",fields,t);
    return t;
}
U32 read_entry(const bw::DatTable* t,U32 id) noexcept {
    U32 value=0;
    std::memcpy(&value,static_cast<const U8*>(t->data)+std::size_t(id)*t->entry_size,t->entry_size);
    return value;
}
void write_entry(bw::DatTable* t,U32 id,U32 value) noexcept {
    std::memcpy(static_cast<U8*>(t->data)+std::size_t(id)*t->entry_size,&value,t->entry_size);
}
U32 maximum(const bw::DatTable* t) noexcept {
    return t->entry_size==1 ? 255u : t->entry_size==2 ? 65535u : 0xffffffffu;
}
bool plan_edit(std::vector<Edit>& edits,Key k,U32 op,U32 num,U32 den) {
    auto it=std::find_if(edits.begin(),edits.end(),[&](const Edit& e){return same(e.key,k);});
    if (it==edits.end()) {
        auto t=table_for(k,true); if (!t) return false;
        U32 v=read_entry(t,k.id); edits.push_back({k,t,v,v}); it=edits.end()-1;
    }
    std::uint64_t value=it->after;
    if (op==0) value=num;
    else if (op==1) value+=num;
    else if (op==2) { if (!den) return reject_growth("ratio_denominator"); value=std::max<std::uint64_t>(1,(value*num+den/2)/den); }
    else if (op==3) { if (!den) return reject_growth("ratio_denominator"); value=(value*num+den-1)/den; }
    else if (op==4) { if (!den) return reject_growth("ratio_denominator"); value=(value*num+den/2)/den; }
    else return reject_growth("patch_operation");
    if (value>maximum(it->table)) {
        log_event("DAT value rejected: table=%u field=%u id=%u op=%u before=%u value=%llu maximum=%u",
            k.table,k.field,k.id,op,it->before,static_cast<unsigned long long>(value),maximum(it->table));
        return reject_growth("value_overflow");
    }
    it->after=static_cast<U32>(value); return true;
}
void refresh_units() noexcept {
    g.units=nullptr;g.units_count=0;
    if (g.unit_array) g.unit_array(&g.units,&g.units_count);
    if (g.units_count>1000000) {g.units=nullptr;g.units_count=0;}
}
bool valid_unit(const bw::Unit* u) noexcept {
    auto p=reinterpret_cast<std::uintptr_t>(u),base=reinterpret_cast<std::uintptr_t>(g.units);
    return u && g.units && p>=base && (p-base)%sizeof(bw::Unit)==0 &&
           (p-base)/sizeof(bw::Unit)<g.units_count;
}
#ifdef SC1_NATIVE_HOST_TEST
std::uint64_t host_unit_scans=0,host_unit_visits=0;
#endif
// A scan may call native damage/creation and recursively scan again. Deque
// elements keep stable references when a deeper call acquires its own buffer.
namespace unit_scan_scratch {
inline std::deque<std::vector<U8>> buffers;inline std::size_t depth=0;
struct Lease {
    std::vector<U8>& seen;
    static std::vector<U8>& acquire(){if(depth==buffers.size())buffers.emplace_back();auto& result=buffers[depth];result.assign(g.units_count,0);++depth;return result;}
    Lease():seen(acquire()){}~Lease(){--depth;}
};
}
template<class F> void living_units(F fn) {
#ifdef SC1_NATIVE_HOST_TEST
    ++host_unit_scans;
#endif
    refresh_units();
    unit_scan_scratch::Lease scratch;auto& seen=scratch.seen;
    for (auto head:{g.first_active,g.first_hidden}) {
        auto u=head ? head() : nullptr;
        for (std::size_t i=0;valid_unit(u) && i<g.units_count;i++) {
            std::size_t index=static_cast<std::size_t>(u-g.units);
            if (seen[index]) break;
            seen[index]=1;
#ifdef SC1_NATIVE_HOST_TEST
            ++host_unit_visits;
#endif
            auto next=reinterpret_cast<bw::Unit*>(u->flingy.next);
            if (u->flingy.hitpoints>0 && u->order!=0) fn(u);
            u=next;
        }
    }
}
void capture_objective_units() {
    g.objective_units.clear();if(!g.mission)return;
    living_units([&](bw::Unit* u){for(const auto& origin:objective_guards::origins)
        if(origin.mission_id==g.mission->mission_id && origin.unit_id==u->unit_id && origin.owner==u->player &&
           origin.x==static_cast<U32>(u->flingy.position.x) && origin.y==static_cast<U32>(u->flingy.position.y))
            g.objective_units.emplace_back(u,u->minor_unique_index);
    });
}
bool protected_objective_unit(const bw::Unit* u) noexcept {
    if(!valid_unit(u))return false;
    for(const auto& identity:g.objective_units)if(identity.first==u && identity.second==u->minor_unique_index)return true;
    return false;
}
U32* deaths(U32 unit,U32 owner) noexcept {
    if (unit>=228 || owner>=12 || !g.game) return nullptr;
    if (g.extended || g.extended_count) {
        if (!g.extended || g.extended_count<=0xa) return nullptr;
        auto& a=g.extended[0xa];std::size_t off=(unit*12+owner)*4;
        if (a.pointer && a.end && a.end>=a.pointer && std::size_t(a.end-a.pointer)>=off+4)
            return reinterpret_cast<U32*>(a.pointer+off);
        // A declared but too-short extended table is not safely interchangeable
        // with the legacy game array. Fail closed instead of writing a different counter.
        return nullptr;
    }
    auto game=g.game(); return game ? &game->deaths[unit][owner] : nullptr;
}
// The V3_SW1 map contract uses native CHK switches as its only authority.
// Deaths 223..227 remain optional diagnostics; Dat+ table availability cannot
// grant or block a milestone. Access Game through the public API getter.
U32 handshake_switch(U32 unit) noexcept {
    switch(unit){
    case kMiddleCounter:return campaign_config::kMiddleSwitch;
    case kReadyCounter:return campaign_config::kReadySwitch;
    case kGoalCounter:return campaign_config::kGoalSwitch;
    case kAckCounter:return campaign_config::kAckSwitch;
    default:return 256;
    }
}
bool switch_set(const bw::Game* game,U32 index) noexcept {
    return game && index<256 && (game->switches[index/32]&(1u<<(index%32)))!=0;
}
void write_switch(bw::Game* game,U32 index,bool value) noexcept {
    if(!game || index>=256)return;
    const U32 mask=1u<<(index%32);
    if(value)game->switches[index/32]|=mask;else game->switches[index/32]&=~mask;
}
U32 counter_value(U32 unit) noexcept {
    const auto game=g.game ? g.game() : nullptr;if(!game)return 0;
    if(unit==kRouteCounter){
        for(U32 i=0;i<campaign_config::kRouteSwitchCount;i++)
            if(switch_set(game,campaign_config::kRouteSwitchBase+i))return i+1;
        return 0;
    }
    return switch_set(game,handshake_switch(unit)) ? 1u : 0u;
}
void mirror_counter(U32 unit,U32 value) noexcept {
    if(unit<kRouteCounter || unit>kAckCounter)return;
    auto game=g.game ? g.game() : nullptr;if(!game)return;
    game->deaths[unit][kCounterOwner]=value;
    if(auto p=deaths(unit,kCounterOwner))*p=value;
}
bool set_counter(U32 unit,U32 value) noexcept {
    auto game=g.game ? g.game() : nullptr;
    if(!game || unit<kRouteCounter || unit>kAckCounter)return false;
    if(unit==kRouteCounter){
        if(value>campaign_config::kRouteSwitchCount)return false;
        for(U32 i=0;i<campaign_config::kRouteSwitchCount;i++)
            write_switch(game,campaign_config::kRouteSwitchBase+i,value==i+1);
    }else{
        if(value>1)return false;
        write_switch(game,handshake_switch(unit),value!=0);
    }
    mirror_counter(unit,value);return true;
}
bool counter(U32 unit) noexcept {return counter_value(unit)!=0;}
void mirror_handshake() noexcept {
    for(U32 unit=kRouteCounter;unit<=kAckCounter;unit++)mirror_counter(unit,counter_value(unit));
}
struct ProgressDialogBarrier {bool open_seen=false,closed_frame_valid=false;U32 closed_frame=0;};
ProgressDialogBarrier progress_dialog{};
void observe_progress_dialog(bool open) noexcept {if(open)progress_dialog.open_seen=true;}
bool progress_frame_allowed(U32 frame,bool open) noexcept {
    observe_progress_dialog(open);if(open)return false;
    if(progress_dialog.open_seen){
        progress_dialog.open_seen=false;progress_dialog.closed_frame_valid=true;
        progress_dialog.closed_frame=frame;return false;
    }
    return !progress_dialog.closed_frame_valid || progress_dialog.closed_frame!=frame;
}
U32 completed_count(U32 unit,U32 owner) noexcept {
    if (unit>=228 || owner>=12 || !g.game) return 0;
    // Pinned bw_dat Game::completed_count uses extended array8 in Dat+ mode.
    // The legacy Game array can remain zero after a building is completed.
    if (g.extended || g.extended_count) {
        if (!g.extended || g.extended_count<=8) return 0;
        const auto& a=g.extended[8];const std::size_t off=(unit*12+owner)*4;
        if (a.pointer && a.end && a.end>=a.pointer && std::size_t(a.end-a.pointer)>=off+4)
            return u32(a.pointer+off);
        // A declared but invalid extended table cannot be substituted with a
        // stale legacy count, which could award a milestone before completion.
        return 0;
    }
    const auto game=g.game();return game ? game->completed_units_count[unit][owner] : 0;
}
void update_original_goal() noexcept {
    if (counter(kGoalCounter)) {set_counter(kGoalCounter,1);return;}
    if (!g.mission || g.mission->mission_id!=101) return;
    // Frozen T01 trigger1 is exactly three P2 Command AtLeast conditions.
    // AtLeast counts completed units. Read their current Dat+ counts directly,
    // so an unrefreshed trigger cache cannot hide an already satisfied goal.
    // This function runs only on simulation frames, never a paused UI pump.
    const std::array<U32,3> counts{{completed_count(0,kOwner),completed_count(111,kOwner),completed_count(19,kOwner)}};
    if (counts!=g.objective_counts) {
        log_event("Original goal check: completed_marines=%u completed_barracks=%u raynor=%u required=10/1/1",
            counts[0],counts[1],counts[2]);g.objective_counts=counts;
    }
    if(counts[1]>=1)set_counter(kMiddleCounter,1);
    if (counts[0]>=10 && counts[1]>=1 && counts[2]>=1 && set_counter(kRouteCounter,1) && set_counter(kGoalCounter,1))
        log_event("Original goal latched from completed units: marines=%u barracks=%u raynor=%u; final choice and durable ACK still required",
            counts[0],counts[1],counts[2]);
}
bool apply_no_production_upgrades() noexcept {
    if(!g.mission || !g.mission->no_production)return true;
    auto game=g.game ? g.game() : nullptr;if(!game)return false;
    // bw_dat Game::upgrade_level uses extended array0, upgrade-major/player-minor.
    // Validate every destination before changing any level; invalid extended
    // storage never falls through to a stale legacy Game array.
    std::array<U8*,16> fields{};
    for(U32 id=0;id<16;id++){
        if(g.extended || g.extended_count){
            if(!g.extended || !g.extended_count)return false;
            auto& a=g.extended[0];const auto off=id*12+player_owner();
            if(!a.pointer || !a.end || a.end<a.pointer || std::size_t(a.end-a.pointer)<=off)return false;
            fields[id]=a.pointer+off;
        }else fields[id]=&game->upgrade_level_sc[player_owner()][id];
    }
    for(U32 id=0;id<16;id++){
        *fields[id]=std::max<U8>(*fields[id],6);
        game->upgrade_level_sc[player_owner()][id]=std::max<U8>(game->upgrade_level_sc[player_owner()][id],6);
    }
    log_event("No-production mission: player=%u standard weapons/armor/shields minimum level6",player_owner());return true;
}
bool loaded_save() noexcept {
    const auto id=static_cast<std::uint16_t>(samase::VarId::LoadedSave);
    // read_vars returns the variable's VALUE, already dereferenced by SAMASE.
    // LoadedSave is an opaque file HANDLE, not a bool or pointer to a bool.
    // Public samase_scarf game_init/units analysis compares it to -1 (both
    // 32-bit and pointer-width forms). The older shim uses nullptr instead.
    // Never dereference this handle: INVALID_HANDLE_VALUE is not readable memory.
    std::size_t value=0;g.read_vars(&id,&value,1);
    const bool is_loaded=value!=0 && value!=std::numeric_limits<std::size_t>::max() && value!=0xffffffffu;
    log_event("LoadedSave handle=0x%016llx loaded=%u (0/-1 invalid-handle means fresh)",static_cast<unsigned long long>(value),is_loaded ? 1u : 0u);
    return is_loaded;
}

U32 effect_value(const std::vector<Edit>& edits,Key key,U32 original) noexcept {
    for(const auto& e:edits)if(same(e.key,key))return e.after;
    return original;
}
// DAT is normally unchanged. A bounded stack scope applies the unit owner and
// weapon owner independently and always restores exact prior values, including
// nested hit callbacks and callbacks belonging to the opposing same unit type.
UnitTrack* existing_track(const bw::Unit* u) noexcept {
    if(!valid_unit(u) || g.tracked_base!=g.units || g.tracks.size()!=g.units_count)return nullptr;
    auto& t=g.tracks[static_cast<std::size_t>(u-g.units)];
    return t.id==u->unit_id && t.owner==u->player && t.unique==u->minor_unique_index ? &t : nullptr;
}
// Turrets have their own weapon/cooldown state, while wave roles and health
// belong to the owning body. Require the native reciprocal owner link.
bw::Unit* effect_body(bw::Unit* u) noexcept {
    if(!valid_unit(u))return nullptr;
    U32 main_id=228;
    switch(u->unit_id){case 4:main_id=3;break;case 6:main_id=5;break;case 18:main_id=17;break;case 24:main_id=23;break;case 26:main_id=25;break;case 31:main_id=30;break;default:return u;}
    auto main=u->subunit;
    return valid_unit(main) && main->unit_id==main_id && main->subunit==u && main->player==u->player ? main : nullptr;
}
bool regular_combat_type(U32 id) noexcept {
    static constexpr auto allowed=[](){std::array<bool,228> value{};for(auto unit:frozen::kRegularCombatUnits)if(unit<value.size())value[unit]=true;return value;}();
    return id<allowed.size()&&allowed[id];
}
bool regular_enemy(const bw::Unit* u) noexcept {return u && is_enemy(u->player) && regular_combat_type(u->unit_id) && !(u->flags&0x40000000u);}
bool hallucination(const bw::Unit* u) noexcept {return u && (u->flags&0x40000000u)!=0;}
// The native spell creates the unit before setting its Hallucination flag.
// Scope the complete CastHallucination order (148), including nested creation.
U32 hallucination_creation_depth=0;
struct HallucinationCreationScope {
    bool enabled;
    explicit HallucinationCreationScope(bool value) noexcept:enabled(value){if(enabled)++hallucination_creation_depth;}
    ~HallucinationCreationScope(){if(enabled)--hallucination_creation_depth;}
};
#include "include/max_hp_runtime.h"
#include "include/owner_dat_query.h"
#include "include/native_tech_cost_view.h"
class OwnerDatScope {
    native_tech_cost_view::Scope native_tech_cost_;
    struct Saved {bw::DatTable* table;U32 id,value;};
    std::array<Saved,1024> saved_;std::size_t size_=0;
public:
    OwnerDatScope(U32 unit_owner,U32 weapon_owner,bw::Unit* subject=nullptr) noexcept
        :OwnerDatScope(unit_owner,weapon_owner,subject,subject){}
    OwnerDatScope(U32 unit_owner,U32 weapon_owner,bw::Unit* subject,bw::Unit* weapon_subject,bool query_only=false) noexcept {
        if(!g.active || !g.applied || GetCurrentThreadId()!=g.game_thread.load())return;
        if(hallucination(subject) || hallucination_creation_depth)unit_owner=12;
        if(hallucination(weapon_subject) || hallucination_creation_depth)weapon_owner=12;
        native_tech_cost_.begin(unit_owner);
        const auto& edits=query_only?owner_dat_query::values():g.owner_edits;
        ++frame_profile::dat_scopes;if(query_only)++frame_profile::query_scopes;frame_profile::dat_entries+=edits.size();
        for(const auto& e:edits){
            const U32 owner=e.key.table==1 ? weapon_owner : unit_owner;
            U32 next=owner==player_owner() ? e.friendly : is_enemy(owner) ? e.enemy : e.original;
            if(e.key.table==0 && e.key.field==48 && (e.key.id==11 || e.key.id==42 || e.key.id==57 || e.key.id==69))next=std::min(next,8u);
            // Corsairs and Raszagal share weapon 100. This talent excludes
            // heroes: an owner-only DAT view must not extend Raszagal's range.
            if(owner==player_owner() && weapon_subject && weapon_subject->unit_id==98 &&
               e.key.table==1 && e.key.field==5 && e.key.id==100)next=e.original;
            // Cooldowns are owner-adjusted after simulation, independent of the
            // engine's iscript execution pass (which is outside step_order).
            if(e.key.table==1 && e.key.field==16)continue;
            const U32 current=read_entry(e.table,e.key.id);
            if(current==next)continue;
            if(size_==saved_.size())break; // apply_snapshot enforces this bound.
            saved_[size_++]={e.table,e.key.id,current};write_entry(e.table,e.key.id,next);++frame_profile::dat_writes;
        }
        const auto t=existing_track(subject);
        if(!query_only && t && ((t->elite && regular_enemy(subject)) || (rework_curses::marked(subject) && rework_curses::hp_percent(subject)!=100)) && unit_owner==subject->player){
            const Key key{0,8,subject->unit_id};auto table=table_for(key,false);
            if(table && size_<saved_.size()){
                const U32 current=read_entry(table,key.id);saved_[size_++]={table,key.id,current};
                write_entry(table,key.id,effective_max_hp(subject));
            }
        }
        if(!query_only && valid_unit(subject) && unit_owner==subject->player){
            const Key key{0,7,subject->unit_id};auto table=table_for(key,false);
            if(table && size_<saved_.size()){
                const U32 current=read_entry(table,key.id),next=effective_max_shields(subject);
                if(current!=next){saved_[size_++]={table,key.id,current};write_entry(table,key.id,next);}
            }
        }
    }
    void include_transform_type(const bw::Unit* subject,U32 id) noexcept {
        // Native TransformUnit computes newMax / oldMax directly from DAT.
        // Expose the same instance multiplier for both types during that call.
        if(!g.active || !g.applied || GetCurrentThreadId()!=g.game_thread.load() ||
           !valid_unit(subject) || id>=228 || id==subject->unit_id ||
           (!(regular_combat_type(id) && regular_enemy(subject)) && !rework_curses::marked(subject)) || hallucination_creation_depth)return;
        const auto track=existing_track(subject);if(!track || (!track->elite && !rework_curses::marked(subject)))return;
        const Key key{0,8,id};auto table=table_for(key,false);
        if(!table || size_>=saved_.size())return;
        const U32 current=read_entry(table,id),base=owner_stat(subject->player,key);
        saved_[size_++]={table,id,current};
        const U32 percent=rework_curses::marked(subject) ? rework_curses::hp_percent(subject):150u;
        write_entry(table,id,static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(base)*percent/100)));
        const Key shield_key{0,7,id};auto shield_table=table_for(shield_key,false);
        if(shield_table && size_<saved_.size()){
            const U32 shield=read_entry(shield_table,id);saved_[size_++]={shield_table,id,shield};
            const U32 shield_base=owner_stat(subject->player,{0,6,id})?owner_stat(subject->player,shield_key):0u;
            write_entry(shield_table,id,static_cast<U32>(std::min<std::uint64_t>(65535u,std::uint64_t(shield_base)*rework_curses::shield_percent(subject)/100)));
        }
    }
    ~OwnerDatScope(){while(size_){const auto& e=saved_[--size_];write_entry(e.table,e.id,e.value);}}
    OwnerDatScope(const OwnerDatScope&)=delete;OwnerDatScope& operator=(const OwnerDatScope&)=delete;
};

bool ordinary_weapon(U32 weapon) noexcept {
    if(weapon>=130)return false;if(g.weapon_cache)return g.ordinary_weapons[weapon];
    for(U32 id=0;id<228;id++)for(U32 field:{17u,19u}){auto t=table_for({0,field,id},false);if(t && read_entry(t,id)==weapon)return true;}
    return false;
}
U32 original_stat(Key key) noexcept;
#include "include/talent_power.h"
bool apply_snapshot(void*,const GrowthSnapshot& s) noexcept {
    const U32 phase=s.completed_phase ? s.completed_phase : 1;
    g.apply_failure=nullptr;
    if(!g.active)return reject_growth("session_inactive");
    if(phase>g.protocol.total_phases())return reject_growth("phase_bounds");
    if(g.applied && phase<=g.applied_phase)return reject_growth("phase_already_applied");
    if(s.wire_version!=1 && s.wire_version!=2)return reject_growth("growth_version");
    const U32 talent_limit=s.wire_version==1 ? frozen::kLegacyTalentCount:frozen::kTalentCount;
    const U32 curse_limit=s.wire_version==1 ? frozen::kLegacyCurseCount:frozen::kCurseCount;
    for(U32 i=0;i<16;i++){const U32 remaining=talent_limit>i*32 ? std::min(32u,talent_limit-i*32):0;const U32 allowed=remaining==32 ? 0xffffffffu:remaining ? (1u<<remaining)-1u:0u;if(s.talent_bits[i]&~(s.wire_version==2?frozen::kTalentMasks[i]:allowed))return reject_growth("talent_bits");}
    for(U32 i=curse_limit;i<64;i++)if(s.curse_counts[i])return reject_growth("curse_slots");
    for(U32 i=0;i<curse_limit;i++)if(s.curse_counts[i]>frozen::kCurseMaxStacks[i])return reject_growth("curse_stack_limit");
    if(!sc1_native::curse_scaling::valid_rank_storage<rework_catalog::kRankCount>(s)||!rework_catalog::valid_packed(s))return reject_growth("rank_slots");
    try {
        if(!g.weapon_cache){for(U32 id=0;id<228;id++)for(U32 field:{17u,19u}){auto table=table_for({0,field,id},false);if(!table)return false;const auto weapon=read_entry(table,id);if(weapon<130)g.ordinary_weapons[weapon]=true;}g.weapon_cache=true;}
        std::vector<Edit> friendly,enemy;
        // Starting every phase from the original map data prevents compounding.
        for(const auto& p:frozen::patches)if(s.talent_bits[p.bit/32]&(1u<<(p.bit%32)))
            if(!talent_power::legacy_patch(friendly,p))return false;
        if(talent_power::enabled)for(const auto& p:frozen::multi_target_patches)if(s.talent_bits[p.bit/32]&(1u<<(p.bit%32))){
            if(!plan_edit(friendly,{0,8,p.unit_id},4,5,4)||!plan_edit(friendly,{0,27,p.unit_id},1,1,1))return false;
        }
        if(!rework_combat_v5::plan_stats(s,friendly) || !rework_economy_v5::plan_stats(s,friendly))return false;
        if(s.curse_counts[1])for(U32 id=0;id<130;id++){
            if(!ordinary_weapon(id))continue;
            const Key key{1,14,id};auto t=table_for(key,true);if(!t)return false;
            if(read_entry(t,id) && !plan_edit(enemy,key,3,40+3*s.curse_counts[1],40))return false;
        }
        if(s.curse_counts[2] || s.curse_counts[7])for(U32 id=0;id<228;id++){
            if(!regular_combat_type(id))continue;
            const Key key{0,8,id};auto t=table_for(key,true);if(!t)return false;
            if(read_entry(t,id) && !plan_edit(enemy,key,4,10+s.curse_counts[2],10))return false;
        }
        // Pin originals before per-instance shield scopes can touch the DAT.
        // These owner edits are no-ops; only marked additional waves scale.
        if(s.wire_version==2 && sc1_native::curse_scaling::count(s,18))for(U32 id=0;id<228;id++){
            auto enabled=table_for({0,6,id},false);if(!enabled)return false;
            if(!read_entry(enabled,id))continue;
            const Key key{0,7,id};auto table=table_for(key,false);if(!table)return false;
            if(!plan_edit(enemy,key,0,read_entry(table,id),1))return false;
        }
        if(!verify_stat_engine_after_dat())return reject_growth("stat_engine_patch_changed");
        auto game=g.game();if(!game)return reject_growth("game_null");
        // Native switch handshake is independent of extended death-table storage.
        std::vector<bw::Unit*> units;living_units([&](bw::Unit* u){units.push_back(u);});
        auto baseline=g.baseline;
        for(const auto* edits:{&friendly,&enemy})for(const auto& e:*edits){
            if(e.key.table==0 && e.key.field==8 && !e.before)return reject_growth("hp_baseline_zero");
            if(std::none_of(baseline.begin(),baseline.end(),[&](const Edit& b){return same(b.key,e.key);}))baseline.push_back(e);
        }
        if(baseline.size()>1024)return reject_growth("scope_capacity");
        std::vector<OwnerEdit> owner_edits;owner_edits.reserve(baseline.size());
        for(const auto& b:baseline)owner_edits.push_back({b.key,b.table,b.before,
            effect_value(friendly,b.key,b.before),effect_value(enemy,b.key,b.before)});
        const auto previous_friendly=g.friendly_edits,previous_enemy=g.enemy_edits;
        rework_economy_v5::before_snapshot();
        g.baseline=std::move(baseline);g.friendly_edits=std::move(friendly);g.enemy_edits=std::move(enemy);
        stat_lookup::reset();
        g.owner_edits=std::move(owner_edits);owner_dat_query::reset();g.applied=true;
        max_hp_cache::publish(true);
        for(auto u:units){
            if(hallucination(u))continue;
            const bool own=u->player==player_owner(),foe=regular_enemy(u);
            if(!own && !foe)continue;
            const auto& previous=own ? previous_friendly : previous_enemy;
            const auto& current=own ? g.friendly_edits : g.enemy_edits;
            OwnerDatScope scope(u->player,u->player,u);
            for(const auto& e:current){
                if(e.key.table || u->unit_id!=e.key.id)continue;
                const U32 before=effect_value(previous,e.key,e.before);
                if(before==e.after)continue;
                if(e.key.field==8 && before){
                    const auto hp=std::max<std::uint64_t>(1,(std::uint64_t(static_cast<U32>(u->flingy.hitpoints))*e.after+before/2)/before);
                    g.set_hp(u,static_cast<std::int32_t>(std::min<std::uint64_t>(hp,0x7fffffff)));
                } else if(e.key.field==7 && before && u->shields>0){
                    u->shields=static_cast<std::int32_t>((std::uint64_t(u->shields)*e.after+before/2)/before);
                } else if(own && e.key.field==46 && before>=e.after){
                    // Captured/rescued units still consume their own race's
                    // supply, irrespective of the selected campaign race.
                    const U32 flags=original_stat({0,44,u->unit_id});
                    const U32 race=(flags&1u) ? 0u : (flags&4u) ? 2u : (flags&2u) ? 1u : 3u;
                    if(race>=3)continue;
                    auto& used=game->supplies[race].used[player_owner()];
                    used=used>=before-e.after ? used-(before-e.after) : 0;
                }
            }
        }
        const GrowthSnapshot previous_growth=g.growth;
        g.growth=s;g.wave_stacks=s.curse_counts[0];g.applied_phase=phase;
        rework_combat_v5::growth_applied(previous_growth,s);
        rework_economy_v5::after_snapshot();
        rework_economy_ui::publish(true);yamato_cost_ui::publish();
        rework_shield_ui_v5::publish(true);
        log_event("Owner-isolated cumulative growth: mission=%u phase=%u fields=%zu",g.mission ? g.mission->mission_id : 0,phase,g.owner_edits.size());
        return true;
    }catch(...){return reject_growth("cpp_exception");}
}

U32 original_stat(Key key) noexcept {
    if(const auto edit=stat_lookup::baseline.find(g.baseline,key))return edit->before;
    auto t=table_for(key,false);return t ? read_entry(t,key.id) : 0;
}
U32 owner_stat(U32 owner,Key key) noexcept {
    const U32 original=original_stat(key);
    const auto edit=owner==player_owner() ? stat_lookup::friendly.find(g.friendly_edits,key) :
        is_enemy(owner) ? stat_lookup::enemy.find(g.enemy_edits,key) : nullptr;
    return edit ? edit->after:original;
}
UnitTrack* track_unit(bw::Unit* u) {
    if(!valid_unit(u))return nullptr;
    if(g.tracked_base!=g.units || g.tracks.size()!=g.units_count){g.tracks.assign(g.units_count,{});g.tracked_base=g.units;}
    auto& t=g.tracks[static_cast<std::size_t>(u-g.units)];
    if(t.id!=u->unit_id || t.unique!=u->minor_unique_index || t.owner!=u->player){
        t={};t.id=u->unit_id;t.unique=u->minor_unique_index;t.owner=u->player;t.hp=u->flingy.hitpoints;t.shields=u->shields;
        t.last_damage=g.game ? g.game()->elapsed_seconds : 0;t.last_damage_frame=g.game ? g.game()->frame_count : 0;
    }
    return &t;
}
void note_attack_launch(bw::Unit* u,U32 weapon) noexcept {
    if(hallucination(u))return;
    auto t=track_unit(u);if(!t)return;
    if(original_stat({0,17,u->unit_id})==weapon)t->cooldown[0].launched=true;
    if(original_stat({0,19,u->unit_id})==weapon)t->cooldown[1].launched=true;
}
#include "include/enemy_progression.h"
void apply_unit_motion() {
    if(!g.applied)return;
    const auto step=[&](bw::Unit* u){
        auto t=track_unit(u);if(!t || t->seen)return;t->seen=true;
        if(hallucination(u)){
            if(t->base_speed && u->flingy.top_speed==t->applied_speed)u->flingy.top_speed=t->base_speed;
            t->base_speed=t->applied_speed=0;t->cooldown[0]={};t->cooldown[1]={};return;
        }
        std::uint64_t speed_num=1,speed_den=1;
        if(u->player==player_owner())for(const auto& p:frozen::movement_patches)
            if(u->unit_id==p.unit_id && (g.growth.talent_bits[p.bit/32]&(1u<<(p.bit%32)))){talent_power::multiply(speed_num,speed_den,p.bit,p.numerator,p.denominator);}
        if(regular_enemy(u) && g.growth.curse_counts[3]){speed_num*=40+3*g.growth.curse_counts[3];speed_den*=40;}
        if(regular_enemy(u) && t->command_until>g.game()->frame_count){speed_num*=6;speed_den*=5;}
        const auto speed_divisor=std::gcd(speed_num,speed_den);speed_num/=speed_divisor;speed_den/=speed_divisor;
        if(u->flingy.top_speed!=t->applied_speed || !t->base_speed)t->base_speed=u->flingy.top_speed;
        t->applied_speed=static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,(std::uint64_t(enemy_progression::escort_base(u,t->base_speed))*speed_num+speed_den/2)/speed_den));
        u->flingy.top_speed=t->applied_speed;
        const double rework_speed=rework_combat_v5::speed_ratio(u)*rework_economy_v5::motion_ratio(u)*double(rework_curses::speed_percent(u))/100.0;
        if(rework_speed!=1.0){t->applied_speed=static_cast<U32>(std::min<double>(0xffffffffu,double(t->applied_speed)*rework_speed));u->flingy.top_speed=t->applied_speed;}
        const auto cooldown=[&](U8& current,U8& old,U32 unit_field,CooldownTrack& clock){
            const U32 weapon=original_stat({0,unit_field,u->unit_id});const U32 frame=g.game()->frame_count;
            if(clock.weapon!=weapon && clock.weapon<130){clock={};clock.weapon=weapon;old=current;return;}
            clock.weapon=weapon;if(current>old){clock.reset_frame=frame;clock.reset_value=current;clock.processed=false;}
            // A reset from an order change alone is not an attack. Only a real
            // primary projectile launch consumes a fractional cooldown share.
            if(clock.launched && !clock.processed && current && weapon<130){
                std::uint64_t numerator=1,denominator=1;
                if(u->player==player_owner())for(const auto& patch:frozen::patches)
                    if(patch.table==1 && patch.field==16 && patch.id==weapon && (g.growth.talent_bits[patch.bit/32]&(1u<<(patch.bit%32)))){talent_power::multiply(numerator,denominator,patch.bit,patch.numerator,patch.denominator);}
                if(is_enemy(u->player) && g.growth.curse_counts[3]){numerator*=40;denominator*=40+3*g.growth.curse_counts[3];}
                // Rank and legacy ratios can share large common factors.
                // Reduce before storing the carry denominator in its U32 field.
                const auto divisor=std::gcd(numerator,denominator);numerator/=divisor;denominator/=divisor;
                if(numerator!=denominator){
                    if(clock.denominator!=denominator){clock.fraction=static_cast<U32>(denominator/2);clock.denominator=static_cast<U32>(denominator);}
                    U32 base=clock.reset_value,elapsed=frame-clock.reset_frame;if(!base || elapsed>=base){base=current;elapsed=0;}
                    const auto scaled=std::uint64_t(base)*numerator+clock.fraction;
                    const auto total=std::max<std::uint64_t>(1,scaled/denominator);
                    current=static_cast<U8>(std::min<std::uint64_t>(255,total>elapsed ? total-elapsed : 1));
                    clock.fraction=static_cast<U32>(scaled%denominator);
                }else{clock.fraction=clock.denominator=0;}
                const double ratio=rework_combat_v5::cooldown_ratio(u,weapon)*100.0/double(rework_curses::speed_percent(u));
                if(ratio!=1.0){const auto period=rework_combat_v5::fractional_period(u,unit_field==19?1u:0u,current,ratio);current=static_cast<U8>(std::min(255u,period));if(rework_combat_v5::enhanced_ensnare(u))rework_combat_v5::hold_ensnare_cooldown(u,unit_field==19?1u:0u,current,period);}
                clock.reset_value=0;clock.processed=true;
                auto body=existing_track(effect_body(u));
                if(body && body->first_attack_bonus)body->first_attack_end=frame+current;
            }
            rework_combat_v5::hold_ensnare_cooldown(u,unit_field==19?1u:0u,current);clock.launched=false;old=current;
        };
        cooldown(u->ground_cooldown,t->ground,17,t->cooldown[0]);
        cooldown(u->air_cooldown,t->air,19,t->cooldown[1]);
    };
    living_units([&](bw::Unit* u){
        step(u);auto turret=u->subunit;
        if(turret && turret!=u && effect_body(turret)==u && turret->flingy.hitpoints>0 && turret->order)step(turret);
    });
    for(auto& t:g.tracks){if(!t.seen)t={};else t.seen=false;}
}

void __cdecl owner_kill_hook(bw::Unit*,UnitFn) noexcept;
U32 unit_owner(const bw::Unit* u) noexcept {return u ? u->player : 12u;}
using UnitHookRegister=U32 (__cdecl*)(void (__cdecl*)(bw::Unit*,UnitFn));
using FuncHookRegister=U32 (__cdecl*)(std::uint16_t,std::uintptr_t);
using RangeFn=U32 (__cdecl*)(bw::Unit*,U32);
using UnitValueFn=U32 (__cdecl*)(bw::Unit*);
using HitFn=void (__cdecl*)(bw::Unit*,bw::Bullet*,U32);
using BulletFn=void (__cdecl*)(bw::Bullet*);
using CommandFn=void (__cdecl*)(const void*,U32,U32);
using CreateBulletFn=bw::Bullet* (__cdecl*)(U32,int,int,U32,U32,bw::Unit*);
bw::Bullet* __cdecl owner_bullet_create_hook(U32,int,int,U32,U32,bw::Unit*,CreateBulletFn) noexcept;
// Owns only additional ordinary attacks; engine damage/range/detection rules remain native.
#include "include/multi_target_runtime.h"
void __cdecl owner_unit_hook(bw::Unit* u,UnitFn original) noexcept;
void __cdecl owner_order_hook(bw::Unit* u,UnitFn original) noexcept;
void __cdecl owner_hp_hook(bw::Unit* u,std::int32_t hp,SetHp original) noexcept {OwnerDatScope scope(unit_owner(u),unit_owner(u),u);original(u,hp);}
U32 __cdecl owner_range_hook(bw::Unit* u,U32 id,RangeFn original) noexcept {OwnerDatScope scope(unit_owner(u),unit_owner(u),u,u,true);return original(u,id);}
U32 __cdecl owner_acquire_hook(bw::Unit* u,UnitValueFn original) noexcept {OwnerDatScope scope(unit_owner(u),unit_owner(u),u,u,true);return original(u);}
bw::Unit* verified_projectile_source(const ProjectileSource& source) noexcept {
    auto u=source.unit;
    return valid_unit(u) && u->unit_id==source.id && u->player==source.owner &&
        u->minor_unique_index==source.unique ? u : nullptr;
}
ProjectileSource projectile_identity(bw::Bullet* bullet) noexcept {
    const auto found=g.bullet_sources.find(bullet);
    if(!bullet || found==g.bullet_sources.end())return {};
    const auto source=found->second;
    // The engine may clear a dead parent. Never infer a source from a reused
    // unit-array slot, a changed owner, or an unobserved projectile launch.
    return bullet->parent==source.unit && bullet->player==source.owner ? source : ProjectileSource{};
}
struct DamageObservation {
    bw::Unit* unit=nullptr;DamageObservation* previous=nullptr;
    std::int32_t hp=0,shields=0;U32 id=228,owner=12,unique=0,attacking_player=12;bool deferred_death=false;
};
DamageObservation* active_damage_observation=nullptr;
bool same_observed_unit(const DamageObservation& o) noexcept {
    return valid_unit(o.unit) && o.unit->unit_id==o.id && o.unit->player==o.owner && o.unit->minor_unique_index==o.unique;
}
bool record_actual_damage(const DamageObservation& o) noexcept {
    if(!g.active || !g.applied || !same_observed_unit(o))return false;
    const bool damaged=o.unit->flingy.hitpoints<o.hp || o.unit->shields<o.shields;
    if(damaged)if(auto t=existing_track(o.unit)){
        t->last_damage=g.game()->elapsed_seconds;t->last_damage_frame=g.game()->frame_count;
    }
    return damaged;
}
struct DamageObservationScope {
    DamageObservation observation;
    explicit DamageObservationScope(bw::Unit* unit,U32 attacking_player=12) noexcept {
        observation.previous=active_damage_observation;
        observation.attacking_player=attacking_player;
        if(valid_unit(unit)){
            observation.unit=unit;observation.hp=unit->flingy.hitpoints;observation.shields=unit->shields;
            observation.id=unit->unit_id;observation.owner=unit->player;observation.unique=unit->minor_unique_index;
        }
        active_damage_observation=&observation;
    }
    ~DamageObservationScope(){
        active_damage_observation=observation.previous;
        const bool damaged=record_actual_damage(observation);
        // KillUnit may run inside the engine DamageUnit callback before HP is
        // changed. Evaluate its curse roles after observing the actual result.
        if(observation.deferred_death && same_observed_unit(observation) && g.active && g.applied)
            curse_death(observation.unit,damaged && observation.unit->flingy.hitpoints<=0 && observation.attacking_player==player_owner());
    }
};
#include "include/combat_effects_runtime.h"
#include "include/movement_effects_runtime.h"
#include "include/rework_relocation_v5.h"
#include "include/rework_combat_v5.h"
#include "include/area_visuals.h"
#include "include/rework_economy_v5.h"
#include "include/rework_cargo_v5.h"
#include "include/rework_carrier_v5.h"
#include "include/campaign_research.h"
U32 __cdecl owner_attack_range_hook(bw::Unit* u,U32 id,RangeFn original) noexcept {return rework_combat_v5::attack_range(u,owner_range_hook(u,id,original),id);}
U32 __cdecl owner_sight_range_hook(bw::Unit* u,U32 ignore_blind,RangeFn original) noexcept {return rework_combat_v5::sight_range(u,owner_range_hook(u,ignore_blind,original),ignore_blind);}
void __cdecl owner_unit_hook(bw::Unit* u,UnitFn original) noexcept {
    OwnerDatScope scope(unit_owner(u),unit_owner(u),u);rework_cargo_v5::OrderScope cargo(u);if(!cargo.allow_original())return;rework_economy_v5::UnitScope economy(u);original(u);
}
void __cdecl owner_timer_hook(bw::Unit* u,UnitFn original) noexcept {
    rework_combat_v5::ExpiryScope expiry(u);owner_unit_hook(u,original);
}
void __cdecl owner_order_hook(bw::Unit* u,UnitFn original) noexcept {
    campaign_research::Scope research(u);HallucinationCreationScope creation(u && u->order==148);rework_carrier_v5::LaunchScope launch(u);rework_carrier_v5::BurstScope burst(u);rework_combat_v5::OrderScope rework(u,original);if(!rework.handled()){owner_unit_hook(u,original);burst.finish([&]{owner_unit_hook(u,original);});}
}
void __cdecl owner_secondary_hook(bw::Unit* u,UnitFn original) noexcept {owner_unit_hook(u,original);}
void __cdecl owner_damage_hook(bw::Unit* u,std::int32_t amount,bw::Unit* attacker,U32 player,U32 show,DamageFn original) noexcept {
    OwnerDatScope scope(unit_owner(u),player,u,attacker);
    DamageObservationScope observed(u,player);
    auto t=existing_track(u);auto attacking_body=g.bullet_hit_context ? verified_projectile_source(g.hit_identity) : effect_body(attacker);const auto attack=existing_track(attacking_body);
    if(g.normal_hit && !combat_effects::weapon_damage_active()){
        if(g.elite_hit || (!g.bullet_hit_context && attack && attack->elite && regular_enemy(attacking_body)))amount=static_cast<std::int32_t>(std::min<std::int64_t>(0x7fffffff,(std::int64_t(amount)*6+4)/5));
        if(g.hit_bonus)amount=static_cast<std::int32_t>(std::min<std::int64_t>(0x7fffffff,(std::int64_t(amount)*(100+g.hit_bonus)+99)/100));
        if(t && t->barrier && regular_enemy(u) && g.game()->elapsed_seconds-t->spawn_second<20)amount=static_cast<std::int32_t>((std::int64_t(amount)*3+3)/4);
        if(rework_curses::marked(attacking_body))amount=static_cast<std::int32_t>(std::min<std::int64_t>(0x7fffffff,(std::int64_t(amount)*rework_curses::attack_percent(attacking_body)+99)/100));
        if(rework_curses::barrier(u))amount=static_cast<std::int32_t>((std::int64_t(amount)*72+99)/100);
    }
    amount=rework_combat_v5::post_armor_damage(u,amount);
    const auto hp=u ? u->flingy.hitpoints : 0;original(u,amount,attacker,player,show);
    if(u&&u->flingy.hitpoints<hp)enemy_detection::note(u,attacking_body);
    auto source=g.bullet_hit_context ? verified_projectile_source(g.hit_identity) : effect_body(attacker ? attacker : g.hit_source);
    if(g.normal_hit && g.growth.curse_counts[11] && regular_enemy(source) && u && u!=source && u->player==player_owner() && hp>0){
        const auto actual=std::max(0,hp-std::max(0,u->flingy.hitpoints));
        if(actual)heal_enemy(source,static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(actual)*g.growth.curse_counts[11]/10)));
    }
    if(g.normal_hit && rework_curses::marked(source) && u && u!=source && u->player==player_owner() && hp>0){const auto actual=std::max(0,hp-std::max(0,u->flingy.hitpoints));const auto percent=rework_curses::lifesteal_percent(source);if(actual && percent)heal_enemy(source,static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(actual)*percent/100)));}
}
void __cdecl owner_hit_hook(bw::Unit* u,bw::Bullet* bullet,U32 divisor,HitFn original) noexcept {
    OwnerDatScope scope(unit_owner(u),bullet ? bullet->player : 12u,u,verified_projectile_source(projectile_identity(bullet)));
    DamageObservationScope observed(u,bullet ? bullet->player : 12u);
    const bool previous=g.normal_hit;g.normal_hit=false;
    if(bullet)g.normal_hit=ordinary_weapon(bullet->weapon_id);
    const bool previous_elite=g.elite_hit;
    const auto it=g.bullet_elites.find(bullet);g.elite_hit=it!=g.bullet_elites.end() && it->second;
    const auto bonus=g.hit_bonus;auto source=g.hit_source;const auto found=g.bullet_bonuses.find(bullet);
    const bool previous_context=g.bullet_hit_context;const auto previous_identity=g.hit_identity;
    g.bullet_hit_context=true;g.hit_identity=projectile_identity(bullet);
    g.hit_bonus=found==g.bullet_bonuses.end() ? 0 : found->second;g.hit_source=verified_projectile_source(g.hit_identity);
    original(u,bullet,divisor);g.normal_hit=previous;g.elite_hit=previous_elite;g.hit_bonus=bonus;g.hit_source=source;g.bullet_hit_context=previous_context;g.hit_identity=previous_identity;
}
void __cdecl owner_missile_hook(bw::Bullet* bullet,BulletFn original) noexcept {
    OwnerDatScope scope(12u,bullet ? bullet->player : 12u,nullptr,verified_projectile_source(projectile_identity(bullet)));
    const bool previous=g.normal_hit,previous_elite=g.elite_hit;g.normal_hit=bullet && ordinary_weapon(bullet->weapon_id);
    const auto it=g.bullet_elites.find(bullet);g.elite_hit=it!=g.bullet_elites.end() && it->second;
    const auto bonus=g.hit_bonus;auto source=g.hit_source;const auto found=g.bullet_bonuses.find(bullet);
    const bool previous_context=g.bullet_hit_context;const auto previous_identity=g.hit_identity;
    g.bullet_hit_context=true;g.hit_identity=projectile_identity(bullet);
    g.hit_bonus=found==g.bullet_bonuses.end() ? 0 : found->second;g.hit_source=verified_projectile_source(g.hit_identity);
    {rework_combat_v5::MissileScope rework(bullet,original);original(bullet);}g.normal_hit=previous;g.elite_hit=previous_elite;g.hit_bonus=bonus;g.hit_source=source;g.bullet_hit_context=previous_context;g.hit_identity=previous_identity;
}
bw::Unit* __cdecl owner_create_hook(U32 id,int x,int y,U32 player,const U8* skins,CreateUnit original) noexcept {
    OwnerDatScope scope(player,player);auto unit=original(id,x,y,player,skins);
    if(g.active && g.applied){refresh_units();max_hp_cache::forget(unit);if(auto track=existing_track(unit))*track={};max_hp_cache::publish_unit(unit);rework_economy_v5::created(unit);rework_combat_v5::created(unit);}
    return unit;
}
bw::Bullet* __cdecl owner_bullet_create_hook(U32 id,int x,int y,U32 player,U32 direction,bw::Unit* parent,CreateBulletFn original) noexcept {
    if(!rework_combat_v5::allow_primary(parent))return nullptr;
    try{if(!multi_target::allow_primary(id,parent))return nullptr;}
    catch(...){multi_target::reset();log_event("Multi-target allocation failed before primary; retaining original attack.");}
    auto body=effect_body(parent);OwnerDatScope scope(player,player,body);rework_combat_v5::ScriptSourceScope script_source(parent);auto bullet=original(id,x,y,player,direction,parent);
    if(bullet && g.active){
        if(!multi_target::secondary())note_attack_launch(parent,id);const auto t=existing_track(body);
        // Bullet storage is reused. Clear all previous launch metadata first;
        // an allocation failure must not retain the old projectile's effects.
        g.bullet_elites.erase(bullet);g.bullet_bonuses.erase(bullet);g.bullet_sources.erase(bullet);
        try{
            g.bullet_elites[bullet]=t && t->elite && regular_enemy(body);g.bullet_bonuses[bullet]=charged_attack(parent,id);
            auto source=effect_body(bullet->parent);
            if(source && source==bullet->parent && source->player==bullet->player)
                g.bullet_sources[bullet]={source,source->unit_id,source->player,source->minor_unique_index};
        }catch(...){g.bullet_elites.erase(bullet);g.bullet_bonuses.erase(bullet);g.bullet_sources.erase(bullet);}
    }
    if(bullet)rework_waves::spell_launched(parent,id);
    try{multi_target::launched(id,parent,bullet);}
    catch(...){multi_target::reset();log_event("Multi-target allocation failed after primary; additional attacks skipped.");}
    try{rework_combat_v5::launched(id,parent,bullet);}catch(...){rework_combat_v5::reset();log_event("Revision5 projectile allocation failed; primary retained.");}
    return bullet;
}
using UnitIdFn=void (__cdecl*)(bw::Unit*,U32);
void __cdecl owner_transform_hook(bw::Unit* u,U32 id,UnitIdFn original) noexcept {
    const U32 old_type=valid_unit(u) ? u->unit_id:228u;
    auto game=g.game ? g.game():nullptr;
    const U32 supply_before=game && unit_owner(u)<12 ? game->supplies[0].used[unit_owner(u)]:0u;
    rework_combat_v5::invalidate(u);
    multi_target::invalidate(u);
    const auto old=existing_track(u);const UnitTrack saved=old ? *old : UnitTrack{};
    if(old && old->base_speed && u->flingy.top_speed==old->applied_speed)u->flingy.top_speed=old->base_speed;
    max_hp_cache::begin_transform(u);
    OwnerDatScope scope(unit_owner(u),unit_owner(u),u);scope.include_transform_type(u,id);original(u,id);
    if(old && valid_unit(u)){*old=saved;old->id=u->unit_id;old->unique=u->minor_unique_index;old->base_speed=0;old->applied_speed=0;}
    rework_curses::transformed(u,old_type);
    rework_combat_v5::transformed(u,old_type);
    max_hp_cache::publish_unit(u);
    rework_economy_v5::transformed(u,old_type,supply_before);
}
void __cdecl owner_give_hook(bw::Unit* u,U32 player,UnitIdFn original) noexcept {
    // Engine callers may redundantly give a unit to its current owner. Such a
    // call must not strip wave roles, elite HP or an in-flight attack clock.
    if(!u || unit_owner(u)==player || hallucination(u)){OwnerDatScope scope(player,player,u);original(u,player);return;}
    multi_target::invalidate(u);rework_combat_v5::invalidate(u);
    rework_carrier_v5::forget(u);
    const auto track=existing_track(u);
    if(track && track->base_speed && u->flingy.top_speed==track->applied_speed)u->flingy.top_speed=track->base_speed;
    const U32 old_owner=unit_owner(u),id=u->unit_id;
    const U32 before=effective_max_hp(u),after=owner_stat(player,{0,8,id});
    const U32 shield_before=effective_max_shields(u),shield_after=owner_stat(player,{0,6,id})?owner_stat(player,{0,7,id}):0u;
    const U32 mule_expiry=rework_economy_v5::expiry(u);
    const U32 old_supply=old_owner==player_owner() && mule_expiry ? 0u:owner_stat(old_owner,{0,46,id}),new_supply=owner_stat(player,{0,46,id});
    const U32 old_provided=owner_stat(old_owner,{0,45,id}),new_provided=owner_stat(player,{0,45,id});
    const auto hp=u->flingy.hitpoints,shields=u->shields;
    auto game=g.game ? g.game() : nullptr;std::array<U32,3> used{},provided{};
    if(game && old_owner<12)for(U32 race=0;race<3;race++){used[race]=game->supplies[race].used[old_owner];provided[race]=game->supplies[race].provided[old_owner];}
    rework_curses::before_give(u,player);
    rework_cargo_v5::before_give(u,player,[&](bw::Unit* p,U32 owner){owner_give_hook(p,owner,original);});
    max_hp_cache::forget(u);
    {OwnerDatScope scope(player,player);original(u,player);}
    rework_cargo_v5::step();
    if(!g.active || unit_owner(u)!=player)return;
    if(mule_expiry)rework_economy_v5::transferred(u,mule_expiry);
    if(track)*track={};
    max_hp_cache::publish_unit(u);
    if(before && hp>0){OwnerDatScope scope(player,player);g.set_hp(u,static_cast<std::int32_t>(std::min<std::uint64_t>(0x7fffffffu,(std::uint64_t(hp)*after+before/2)/before)));}
    if(shield_before && shields>0)u->shields=static_cast<std::int32_t>(std::min<std::uint64_t>(std::uint64_t(shield_after)*256,(std::uint64_t(shields)*shield_after+shield_before/2)/shield_before));
    // GiveUnit observes the destination view for its add/subtract. Correct only
    // its changed source-race ledger to the source owner's original unit cost.
    if(game && old_owner<12 && old_owner!=player && old_supply!=new_supply)for(U32 race=0;race<3;race++){
        auto& current=game->supplies[race].used[old_owner];
        if(current!=used[race])current=used[race]>=old_supply ? used[race]-old_supply : 0;
    }
    if(game && old_owner<12 && old_owner!=player && old_provided!=new_provided)for(U32 race=0;race<3;race++){
        auto& current=game->supplies[race].provided[old_owner];
        if(current!=provided[race])current=provided[race]>=old_provided ? provided[race]-old_provided:0;
    }
}
void __cdecl owner_commands_hook(const void* data,U32 len,U32 replay,CommandFn original) noexcept {
    // CommandUser is a scalar read_vars value; never dereference it. This covers
    // resource and supply checks before a training/morph order reaches a unit.
    const auto id=static_cast<std::uint16_t>(samase::VarId::CommandUser);std::size_t player=12;
    if(g.active)g.read_vars(&id,&player,1);OwnerDatScope scope(static_cast<U32>(player),static_cast<U32>(player));rework_economy_v5::CommandScope economy(static_cast<U32>(player),data,len);rework_combat_v5::CommandScope combat(static_cast<U32>(player),false);rework_cargo_v5::CommandScope cargo(data,len);original(data,len,replay);
}
using GuiFn=void (__cdecl*)(void*);
void __cdecl owner_rclick_hook(void* event,GuiFn original) noexcept {
    // Right-click chooses the default order BEFORE ProcessCommands. Native
    // burrowed-Lurker predicates reject movement at both boundaries.
    if(g.active&&g.applied){rework_combat_v5::CommandScope combat(player_owner(),true,false);original(event);}
    else original(event);
}
bool register_owner_hooks(const samase::PluginApi* api) noexcept {
    if(!api->hook_func || !api->hook_step_order || !api->hook_step_order_hidden ||
       !api->hook_step_secondary_order || !api->hook_create_unit || !api->hook_create_bullet || !api->hook_process_commands || !api->hook_game_screen_rclick)return false;
    const auto command=static_cast<std::uint16_t>(samase::VarId::CommandUser);U8 support=0;api->load_vars(&command,&support,1);if(support<2)return false;
    auto hook=reinterpret_cast<FuncHookRegister>(api->hook_func);
    const auto bind=[&](samase::FuncId id,auto callback){return hook(static_cast<std::uint16_t>(id),reinterpret_cast<std::uintptr_t>(callback))!=0;};
    if(!reinterpret_cast<UnitHookRegister>(api->hook_step_order)(owner_order_hook) ||
       !reinterpret_cast<UnitHookRegister>(api->hook_step_order_hidden)(owner_order_hook) ||
       !reinterpret_cast<UnitHookRegister>(api->hook_step_secondary_order)(owner_secondary_hook))return false;
    using CreateRegister=U32 (__cdecl*)(bw::Unit* (__cdecl*)(U32,int,int,U32,const U8*,CreateUnit));
    using BulletRegister=U32 (__cdecl*)(bw::Bullet* (__cdecl*)(U32,int,int,U32,U32,bw::Unit*,CreateBulletFn));
    using RclickRegister=U32 (__cdecl*)(void (__cdecl*)(void*,GuiFn));
    using CommandRegister=U32 (__cdecl*)(void (__cdecl*)(const void*,U32,U32,CommandFn));
    return reinterpret_cast<CreateRegister>(api->hook_create_unit)(owner_create_hook) &&
        reinterpret_cast<BulletRegister>(api->hook_create_bullet)(owner_bullet_create_hook) &&
        reinterpret_cast<CommandRegister>(api->hook_process_commands)(owner_commands_hook) &&
        reinterpret_cast<RclickRegister>(api->hook_game_screen_rclick)(owner_rclick_hook) &&
        bind(samase::FuncId::UnitSetHp,owner_hp_hook) &&
        bind(samase::FuncId::KillUnit,owner_kill_hook) &&
        bind(samase::FuncId::TransformUnit,owner_transform_hook) &&
        bind(samase::FuncId::GiveUnit,owner_give_hook) &&
        bind(samase::FuncId::StepUnitTimers,owner_timer_hook) &&
        bind(samase::FuncId::FinishUnitPre,owner_unit_hook) &&
        bind(samase::FuncId::FinishUnitPost,owner_unit_hook) &&
        bind(samase::FuncId::UnitAttackRange,owner_attack_range_hook) &&
        bind(samase::FuncId::UnitSightRange,owner_sight_range_hook) &&
        bind(samase::FuncId::UnitTargetAcquisitionRange,owner_acquire_hook) &&
        bind(samase::FuncId::DamageUnit,owner_damage_hook) &&
        bind(samase::FuncId::HitUnit,owner_hit_hook) &&
        bind(samase::FuncId::DoMissileDamage,owner_missile_hook);
}

bw::Unit* spawn(U32 id,int x,int y,U32 owner) noexcept {
    if (!g.create || id>=228 || owner>=12 || x<0 || y<0 || !g.mission || x>=static_cast<int>(g.mission->width*32) || y>=static_cast<int>(g.mission->height*32)) return nullptr;
    // Public maintainer example: neivv/aice cd7bc760f29007febc70eca44ef156a5c179bae6,
    // src/bw/mod.rs create_unit supplies exactly [player, player] as u8 skins.
    // SC:R reads both bytes. The older 1.16 shim ignores this argument, which
    // does NOT make nullptr valid in SC:R (our previous candidate crashed here).
    const U8 skins[2]={static_cast<U8>(owner),static_cast<U8>(owner)};
    const bool first=g.spawn_attempts++==0;
    if (first) log_event("CreateUnit first call: id=%u x=%d y=%d owner=%u skins=%u/%u",id,x,y,owner,skins[0],skins[1]);
    auto u=g.create(id,x,y,owner,skins);
    if (!u) {if(first)log_event("CreateUnit first call returned null.");return nullptr;}
    g.finish_pre(u);g.finish_post(u);rework_economy_v5::created(u);return u;
}
#include "include/curse_runtime.h"
void wave_marker(bw::Unit* u,const UnitTrack& t,U32 second) noexcept {
    if(!g.add_overlay || !regular_enemy(u) || !u->flingy.sprite)return;
    const auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);if(!sprite->main_image)return;
    // Original images377..379 use finite script301 (four frames then End).
    // A pulse cannot outlive the unit/session; unlike image371 it never loops.
    const U32 image=377u+(sprite->width>64 ? 2u : sprite->width>32 ? 1u : 0u);
    if(t.elite)g.add_overlay(sprite->main_image,image,0,-16,1);
    if(t.barrier && second-t.spawn_second<20)g.add_overlay(sprite->main_image,image,0,0,1);
}
void mark_wave_unit(bw::Unit* u) {
    refresh_units();auto t=track_unit(u);if(!t)return;
    t->spawned=true;t->wave_id=g.current_wave_id;t->spawn_second=g.game()->elapsed_seconds;t->last_damage=t->spawn_second;
    t->elite=g.growth.curse_counts[7] && g.wave_spawn_number<g.growth.curse_counts[7];
    t->barrier=g.growth.curse_counts[8] && g.wave_spawn_number<4u+2u*(g.growth.curse_counts[8]-1u);
    max_hp_cache::publish_unit(u);
    if(t->elite){OwnerDatScope scope(u->player,u->player,u);g.set_hp(u,static_cast<std::int32_t>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(u->flingy.hitpoints)*3/2)));}
    assign_wave_roles(u,*t);wave_marker(u,*t,t->spawn_second);
    ++g.wave_spawn_number;
}
#include "include/wave_targeting_runtime.h"
U32 wave_supply(std::uint16_t id) {return original_stat({0,46,id});}
U32 added_supply() {
    U32 supply=0;living_units([&](bw::Unit* u){auto t=existing_track(u);if(t && t->spawned && is_enemy(u->player) && !hallucination(u))supply+=std::max(1u,original_stat({0,46,u->unit_id}));});return supply;
}
bool wave_protected_unit(const bw::Unit* u) noexcept {
    // Raw resources and passive neutral staging troops block their footprint,
    // not an allied safety zone around every enemy mining base.
    if(!u || is_enemy(u->player))return false;
    if(u->unit_id==176 || u->unit_id==177 || u->unit_id==178 || u->unit_id==188)return false;
    if(u->player==player_owner() || protected_objective_unit(u))return true;
    if(u->player>=8 || !g.game)return false;const auto game=g.game();
    return game->starting_player_types[u->player]==3 || game->alliances[player_owner()][u->player] || game->alliances[u->player][player_owner()];
}
bool origin_safe(const sc1_native::campaign_wave_config::Origin& origin) {
    if(!g.mission || origin.mission_id!=g.mission->mission_id || !is_enemy(origin.owner) || !origin.cell_count)return false;
    bool safe=true;living_units([&](bw::Unit* u){
        if(!wave_protected_unit(u))return;
        // Human, allies, rescue units and neutral objectives protect an entry.
        const auto p=u->flingy.position;const auto dx=std::int64_t(p.x)-origin.center.x,dy=std::int64_t(p.y)-origin.center.y;
        if(dx*dx+dy*dy<512ll*512)safe=false;
    });return safe;
}
bool origin_has_live_base(const sc1_native::campaign_wave_config::Origin& origin) {
    bool found=false;living_units([&](bw::Unit* u){
        if(u->player!=origin.owner || !(original_stat({0,22,u->unit_id})&1u))return;
        const auto p=u->flingy.position;const auto dx=std::int64_t(p.x)-origin.center.x,dy=std::int64_t(p.y)-origin.center.y;
        if(dx*dx+dy*dy<512ll*512)found=true;
    });return found;
}
void announce_wave(U32 warning) noexcept {
    log_event("Additional wave scheduled: departure_in_seconds=%u",warning);
}
void choose_campaign_wave(U32 second,U32 supply,U32 warning) {
    if(g.pending_origin)return;const U32 current=added_supply(),cap=sc1_native::wave_progression::live_supply_cap(g.mission->no_production);
    if(current>=cap)return;supply=std::min(supply,cap-current);
    for(U32 pass=0;pass<2;pass++)for(const auto& origin:sc1_native::campaign_wave_config::kOrigins){
        if(origin_safe(origin) && (pass || origin_has_live_base(origin))){
            g.pending_origin=&origin;g.pending_supply=supply;g.pending_second=second+warning;g.pending_batch=0;g.pending_wave_id=++g.next_wave_id;
            announce_wave(warning);return;
        }
    }
}
void campaign_waves(U32 second,bool ready,bool goal) {
    if(!ready || goal || !g.mission)return;
    const U32 first=sc1_native::wave_progression::first_elapsed_seconds(g.mission->no_production);
    const U32 interval=sc1_native::wave_progression::interval_seconds(g.mission->no_production,g.growth.curse_counts[4]);
    if(!g.next_wave_second)g.next_wave_second=first;
    if(second<first || (g.mission->mission_id==101 && !g.waves.state().active)){
        // Opening grace also discards death reinforcements and partial kill
        // credits; early kills cannot create a banked wave at the boundary.
        g.death_wave_due=false;g.kills_for_wave=0;g.pending_origin=nullptr;g.pending_supply=0;g.pending_second=0;g.pending_batch=0;return;
    }
    if(g.mission->mission_id!=101 && second>=g.next_wave_second){
        g.next_wave_second=second+interval;
        choose_campaign_wave(second,sc1_native::wave_progression::budget(g.mission->no_production,g.wave_stage,g.wave_stacks),4);
    }
    if(g.death_wave_due){
        g.death_wave_due=false;
        if(g.growth.curse_counts[6] && (!g.last_death_wave || second-g.last_death_wave>=60)){
            g.last_death_wave=second;
            choose_campaign_wave(second,16u+8u*(g.growth.curse_counts[6]-1u),10);
        }
    }
    if(g.pending_origin && second>=g.pending_second){
        const auto primary=g.pending_origin;const auto current=added_supply(),cap=sc1_native::wave_progression::live_supply_cap(g.mission->no_production);
        const auto budget=current<cap ? std::min(g.pending_supply,cap-current) : 0u;
        g.pending_origin=nullptr;g.pending_supply=0;if(!budget)return;
        if(!g.pending_batch)g.wave_spawn_number=0;g.current_wave_id=g.pending_wave_id;
        U32 used=0,created=0;
        for(U32 pass=0;pass<2;pass++)for(const auto& candidate:sc1_native::campaign_wave_config::kOrigins){
            const auto origin=&candidate;if((pass==0)!=(origin==primary) || !origin_safe(*origin))continue;
            for(U32 i=0;i<origin->cell_count && i<32;i++){
                const bool air_only=sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(origin->unit1)) && sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(origin->unit2));
                const auto pick=sc1_native::wave_progression::select(origin->race,air_only,second,g.pending_wave_id-1,g.wave_spawn_number,budget-used,wave_supply);
                if(!pick.valid)break;const U32 id=pick.unit_id,supply=pick.supply;
                const auto p=origin->cells[i];bool clear=true;U32 alive=0;
                living_units([&](bw::Unit* u){++alive;const auto q=u->flingy.position;const auto dx=std::int64_t(q.x)-p.x,dy=std::int64_t(q.y)-p.y;
                    if(std::abs(dx)<40 && std::abs(dy)<40)clear=false;
                    if(wave_protected_unit(u) && dx*dx+dy*dy<512ll*512)clear=false;
                });
                if(alive>=1600)break;if(!clear)continue;
                OwnerDatScope scope(origin->owner,origin->owner);auto u=spawn(id,p.x,p.y,origin->owner);if(!u)continue;
                mark_wave_unit(u);used+=supply;++created;
                wave_targeting::issue(u);
            }
        }
        if(created){
            if(!g.pending_batch)++g.wave_stage;
            // Deliver the rest only after a successful first group has moved.
            // Blocked/empty attempts are discarded, never accumulated.
            if(used<budget && ++g.pending_batch<8){g.pending_origin=primary;g.pending_supply=budget-used;g.pending_second=second+12;}
        }
    }
}
#include "include/rework_wave_native.h"
#include "include/enemy_detection.h"
void regenerate_waves(U32 second) {
    if(g.applied)update_diversity();
    if(!g.applied || second==g.last_regen_second)return;g.last_regen_second=second;
    living_units([&](bw::Unit* u){auto t=track_unit(u);if(!t)return;
        if(u->flingy.hitpoints<t->hp || u->shields<t->shields)t->last_damage=second;
        if(t->spawned)wave_marker(u,*t,second);
        if(t->spawned && regular_enemy(u) && g.growth.curse_counts[5] && second-t->last_damage>=6){
            const U32 maximum=effective_max_hp(u);
            const U32 gain=static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(maximum)*g.growth.curse_counts[5]/100));
            if(u->flingy.hitpoints<static_cast<std::int32_t>(maximum)){OwnerDatScope scope(u->player,u->player,u);g.set_hp(u,static_cast<std::int32_t>(std::min<std::uint64_t>(maximum,std::uint64_t(u->flingy.hitpoints)+gain)));}
        }
        t->hp=u->flingy.hitpoints;t->shields=u->shields;
    });
}
void __cdecl owner_kill_hook(bw::Unit* u,UnitFn original) noexcept {
    rework_economy_v5::before_kill(u);
    rework_combat_v5::death(u);rework_combat_v5::invalidate(u);
    rework_carrier_v5::forget(u);
    multi_target::invalidate(u);
    g.objective_units.erase(std::remove_if(g.objective_units.begin(),g.objective_units.end(),[&](const auto& identity){return identity.first==u;}),g.objective_units.end());
    if(g.active && g.applied){
        if(regular_enemy(u))track_unit(u);
        auto observed=active_damage_observation;
        while(observed && observed->unit!=u)observed=observed->previous;
        if(observed)observed->deferred_death=true;
        else curse_death(u);
    }
    max_hp_cache::forget(u);
    rework_curses::forget(u);
    rework_cargo_v5::before_death(u,[&](bw::Unit* passenger){owner_kill_hook(passenger,original);});
    OwnerDatScope scope(unit_owner(u),unit_owner(u),u);original(u);
}
// Dialog adapter definitions follow the game/protocol callbacks below.
void dialog_clear_offer() noexcept;
void dialog_show_offer(const ChoiceOffer&) noexcept;
void clear_offer(void*) noexcept {
    g.offer_active=false;
    dialog_clear_offer();
}
void original_objectives_status(bw::Game* game,bool ready) noexcept {
    // Observe the original engine objective/leaderboard fields only. Native
    // TRIGs retain ownership of string IDs9/19/21 and Marine leaderboard24.
    const U32 objectives=game->player_objectives_string[player_owner()];
    const U32 leaderboard=game->leaderboard_type;
    if (objectives!=g.last_objectives || leaderboard!=g.last_leaderboard) {
        log_event("Original objectives: string=%u leaderboard_type=%u parameter=%u string=%u",objectives,leaderboard,game->leaderboard_parameter,game->leaderboard_string);
        g.last_objectives=objectives;g.last_leaderboard=leaderboard;
    }
    // One compact reminder when the stock objective changes or choices finish.
    // No guessed draw hook, fixed-address HUD write, or repeated objective spam.
    if (!g.mission || g.mission->mission_id!=101 || !ready || g.offer_active || objectives==g.shown_objectives) return;
    if (objectives==9) message("임무 목표: 배럭스 건설 · 마린 10기 훈련 · 레이너 생존");
    else if (objectives==19 || objectives==21) message("임무 목표: 레이너 찾기 · 배럭스 건설 · 마린 10기 훈련");
    else return;
    g.shown_objectives=objectives;
}
void show_offer(void*,const ChoiceOffer& offer) noexcept {
    g.offer=offer;g.offer_active=true;
    log_event("Dialog offer accepted: kind=%u count=%u revision=%u remaining=%u/%u phase=%u completed=%u",offer.kind,offer.count,offer.revision,offer.pending_talents,offer.pending_curses,g.protocol.requested_phase(),g.protocol.completed_phase());
    dialog_show_offer(offer);
}
void dialog_clear_offer() noexcept {g.dialog.clear();}
void dialog_show_offer(const ChoiceOffer& offer) noexcept {
    const bool already_open=g.dialog.open();
    g.dialog.show(offer);
    if (!already_open) message(offer.kind==1 ? "재능을 선택하세요." : "저주를 선택하세요.");
}
bool submit_dialog_choice(void*,U32 slot) noexcept {
    if (GetCurrentThreadId()!=g.game_thread.load() || !g.active || g.pumping || !g.offer_active) return false;
    if (!g.protocol.submit_choice(slot)) return false;
    g.offer_active=false;
    log_event("Dialog choice submitted: kind=%u slot=%u revision=%u; waiting for durable response",g.offer.kind,slot,g.offer.revision);
    return true;
}
bool dialog_session_active(void*) noexcept {
    return GetCurrentThreadId()==g.game_thread.load() && g.active;
}
bool dialog_can_resume(void*) noexcept {
    // This callback runs only after the guarded protocol pump returns. DAT
    // application alone is insufficient: word19/state publication must finish.
    return dialog_session_active(nullptr) && !g.pumping && g.applied &&
           g.protocol.growth_applied() && g.protocol.state()!=1 && !g.protocol.failed() &&
           (!g.protocol.phased() || g.protocol.completed_phase()>=g.protocol.requested_phase());
}
void dialog_report(void*,const char* text) noexcept {log_event("Dialog: %s",text ? text : "");}
void protocol_pump(void*) noexcept;
sc1_native::DialogUiCallbacks dialog_callbacks() noexcept {
    sc1_native::DialogUiCallbacks callbacks{nullptr,submit_dialog_choice,protocol_pump,dialog_session_active,dialog_can_resume,dialog_report};
    callbacks.cargo_toggle=rework_cargo_v5::toggle;callbacks.cargo_state_v2=rework_cargo_v5::status;
    return callbacks;
}
void on_error(void*,U32 code) noexcept {
    set_counter(kReadyCounter,0);set_counter(kAckCounter,0);
    // Error dismissal is a UI escape, never a successful growth/Victory ACK.
    // Deferred until the protocol callback returns; no modal or API reentry.
    g.dialog.dismiss_error();
    if(code==10) {
        log_event("Native effect application failed: reason=%s; persistence data not changed by plugin",
            g.apply_failure ? g.apply_failure : "unspecified");
        message("성장 효과 적용 오류 10. sc1_native.log의 적용 오류를 확인하세요. 승리는 대기합니다.");
    } else {
        char line[256];std::snprintf(line,sizeof(line),"캠페인 기록 연결 오류 %u. 관리자 상태를 확인하세요. 승리는 대기합니다.",code);message(line);
    }
}

U32 wave_count(void*,int owner,int id,const sc1_native::WaveRect* area) {
    U32 count=0;
    living_units([&](bw::Unit* u){
        if (owner>=0 && u->player!=owner) return;
        if (id>=0 && u->unit_id!=id) return;
        if (id==-2 && u->unit_id>=106) return; // T01 P7 Men are exclusively37/38.
        auto p=u->flingy.position;
        if (area && (p.x<area->left || p.x>area->right || p.y<area->top || p.y>area->bottom)) return;
        ++count;
    });return count;
}
void* wave_spawn(void*,std::uint16_t id,std::int32_t x,std::int32_t y,U8 owner) noexcept {
    if(!is_enemy(owner))return nullptr;bool safe=true;
    living_units([&](bw::Unit* u){if(!wave_protected_unit(u))return;const auto p=u->flingy.position;
        const auto dx=std::int64_t(p.x)-x,dy=std::int64_t(p.y)-y;if(dx*dx+dy*dy<512ll*512)safe=false;});
    if(!safe)return nullptr;OwnerDatScope scope(owner,owner);auto u=spawn(id,x,y,owner);if(u)mark_wave_unit(u);return u;
}
void wave_attack(void*,U8 owner,const sc1_native::WaveRect* area,std::int32_t,std::int32_t) {
    living_units([&](bw::Unit* u){
        if(u->player!=owner || !wave_targeting::marked(u))return;
        const auto p=u->flingy.position;
        if(area && (p.x<area->left || p.x>area->right || p.y<area->top || p.y>area->bottom))return;
        wave_targeting::issue(u);
    });
}
void wave_warning(void*,U32,const sc1_native::WavePoint*) noexcept {g.wave_spawn_number=0;g.current_wave_id=g.t01_wave_id=++g.next_wave_id;announce_wave(4);}

void restore_baseline() noexcept {
    for (auto& e:g.baseline) if (auto t=table_for(e.key,false)) write_entry(t,e.key.id,e.before);
    if (!g.baseline.empty()) log_event("Previous mission DAT restored: entries=%zu",g.baseline.size());
    g.baseline.clear();
}
void abandon_session() noexcept {
    owner_dat_query::reset();
    stat_lookup::reset();
    frame_profile::reset();
    g.survival_hint_shown=false;
    g.campaign_clear_shown=false;
    area_visuals::reset();campaign_visibility::reset();yamato_cost_ui::reset();rework_energy_ui::reset();rework_economy_ui::reset();rework_shield_ui_v5::reset();enemy_progression::reset();rework_waves::reset();rework_combat_v5::reset();rework_economy_v5::reset();rework_cargo_v5::reset();rework_carrier_v5::reset();
    max_hp_cache::reset();
    wave_targeting::reset();enemy_detection::reset();
    movement_effects::reset();combat_effects::reset_melee();g.objective_units.clear();
    multi_target::reset();progress_dialog={};
    // Clear only our dialog state; choice UI owns no game units.
    g.active=false;
    g.mission=nullptr;g.friendly_edits.clear();g.enemy_edits.clear();g.owner_edits.clear();g.campaign_index=0;g.growth={};g.tracks.clear();g.weapon_cache=false;g.ordinary_weapons.fill(false);g.bullet_elites.clear();g.bullet_bonuses.clear();g.bullet_sources.clear();g.hit_identity={};g.bullet_hit_context=false;g.bombs.clear();g.hit_bonus=g.last_diversity_frame=0;g.hit_source=nullptr;g.tracked_base=nullptr;g.pending_origin=nullptr;g.next_wave_second=g.pending_second=g.pending_supply=g.wave_stage=g.wave_spawn_number=0;g.pending_batch=g.next_wave_id=g.current_wave_id=g.pending_wave_id=g.t01_wave_id=0;g.kills_for_wave=g.last_death_wave=g.last_regen_second=0;g.death_wave_due=g.normal_hit=g.elite_hit=false;
    g.protocol.shutdown();
    g.dialog.reset_session();
    g.applied=false;g.wave_stacks=0;
    g.applied_phase=g.observed_phase=g.phase_frame=0;
    g.milestone_barracks=g.milestone_flags=std::numeric_limits<U32>::max();
    g.objective_counts.fill(std::numeric_limits<U32>::max());
    g.last_frame=std::numeric_limits<U32>::max();g.logged_state=0;g.waves.reset();
    g.last_objectives=g.last_leaderboard=g.shown_objectives=std::numeric_limits<U32>::max();
    g.spawn_attempts=0;
    g.game_thread=0;g.wrong_thread_reported=false;
}
void __cdecl init_game() noexcept {
    // MTL uses extend_save's init callback as the game pre-init boundary.
    // Restore before the next map's UNIS/data initialization, not at init_units.
    abandon_session();restore_baseline();
    log_event("Game pre-init: previous private mailbox invalidated.");
}
void __cdecl save_extension(samase::SetSaveData set) noexcept {
    // Combat saves are deliberately outside the user-approved prototype scope.
    // Tag only our map; original campaigns retain their usual save behavior.
    if (g.active) {const U8 marker[4]={'S','C','1',2};set(marker,4);}
}
U32 __cdecl load_extension(const U8* data,std::size_t size) noexcept {
    if (size==4 && data && ((data[0]=='T' && data[1]=='0' && data[2]=='1' && data[3]==1) ||
        (data[0]=='S' && data[1]=='C' && data[2]=='1' && data[3]==2))) {
        abandon_session();
        log_event("Rejected native T01 combat save extension; growth persistence remains external.");return 0;
    }
    return 1;
}
void __cdecl init_units(GenericFn original) noexcept {
    abandon_session();
    original();
    if (!g.hooks_ready) return;
    try {
        auto game=g.game();
        if (!game || !game->campaign_mission || g.multiplayer() || g.replay() ||
            false) return;
        std::size_t size=0;auto data=g.read_map(reinterpret_cast<const U8*>("staredit\\scenario.chk"),&size);
        U32 phase_capability=0;const auto mission=identify_chk(data,size,&phase_capability);if(data)g.free_memory(data);
        if(!mission || (mission->campaign_index && game->campaign_mission!=mission->campaign_index) ||
           game->map_width_tiles!=mission->width || game->map_height_tiles!=mission->height)return;
        g.mission=mission;g.campaign_index=game->campaign_mission;
        capture_objective_units();
        log_event("Campaign marker accepted: mission=%u index=%u owner=%u race=%u",mission->mission_id,mission->campaign_index,mission->owner,mission->race);
        if(phase_capability==2)write_switch(game,campaign_config::kQuarterSwitch,false);
        if (!set_counter(kRouteCounter,0) || !set_counter(kMiddleCounter,0) || !set_counter(kReadyCounter,0) || !set_counter(kGoalCounter,0) || !set_counter(kAckCounter,0)) return;
        // The map must observe actual hostile bases in this mission before an
        // empty-building alternate win is eligible. Never inherit an old latch.
        write_switch(game,campaign_config::kEnemyBaseSeenSwitch,false);
        if (loaded_save()) {
            log_event("LoadedSave handle rejected for marker-matched T01; mailbox not published (no popup).");return;
        }
        if(!apply_no_production_upgrades()){message("비생산 임무의 업그레이드 배열을 확인하지 못했습니다. 성장을 연결하지 않습니다.");return;}
        g.game_thread=GetCurrentThreadId();g.active=true;
        g.dialog.set_callbacks(dialog_callbacks());
        sc1_native::MailboxCallbacks callbacks{nullptr,apply_snapshot,show_offer,clear_offer,on_error};
        if (!g.protocol.initialize(callbacks,g.mission->mission_id,true,2,phase_capability)) {g.active=false;return;}
        refresh_units();log_event("Native T01 initialized: API=%u Game=%zu Unit=%zu unit_array_len=%zu mailbox=%p",g.api_version,sizeof(bw::Game),sizeof(bw::Unit),g.units_count,static_cast<const void*>(const_cast<const U32*>(g.protocol.mailbox_words())));
        message("성장 기록을 연결합니다.");
    } catch (...) {g.active=false;message("본편 플러그인 초기화 오류. 캠페인 기록 연결을 중단했습니다.");}
}
void protocol_pump(void*) noexcept {
    const auto owner_thread=g.game_thread.load();
    if (!owner_thread || GetCurrentThreadId()!=owner_thread) {
        if (owner_thread && !g.wrong_thread_reported.exchange(true)) log_event("Protocol pump ignored on non-game thread.");
        return;
    }
    if (!g.active || g.pumping) return;
    struct Guard {Guard(){g.pumping=true;}~Guard(){g.pumping=false;}} guard;
    try {
        auto game=g.game();if (!game || !game->campaign_mission || g.multiplayer() || g.replay()) {abandon_session();return;}
        g.protocol.tick();
        const bool playable=g.protocol.growth_applied() && g.applied && !g.protocol.failed();
        if (g.observed_phase!=g.protocol.completed_phase()) {
            g.observed_phase=g.protocol.completed_phase();g.phase_frame=game->frame_count;
            log_event("Phase snapshot published: completed=%u requested=%u frame=%u",g.observed_phase,g.protocol.requested_phase(),g.phase_frame);
        }
        // Paused UI pumps may receive durable ACK, but never open Victory.
        // Only frame() publishes the ready/ACK switches after modal closure
        // and a subsequent simulation frame. Optional deaths are diagnostics.
        const bool dialog_open=g.dialog.open();observe_progress_dialog(dialog_open);
        const bool final_phase=playable && (!g.protocol.phased() || g.protocol.completed_phase()==g.protocol.total_phases());
        if(!final_phase || dialog_open){set_counter(kReadyCounter,0);set_counter(kAckCounter,0);}
        if (counter(kGoalCounter)) g.protocol.on_goal_reached();
        mirror_handshake();
        if (g.logged_state!=g.protocol.state()) {
            g.logged_state=g.protocol.state();
            log_event("Frame hook: frame=%u protocol_state=%u ready225=%u goal226=%u ack227=%u",game->frame_count,g.logged_state,counter(kReadyCounter) ? 1u : 0u,counter(kGoalCounter) ? 1u : 0u,counter(kAckCounter) ? 1u : 0u);
        }
        original_objectives_status(game,playable);
    } catch (...) {set_counter(kReadyCounter,0);set_counter(kAckCounter,0);abandon_session();message("본편 플러그인 기록 오류. 캠페인 기록 연결을 중단했습니다.");}
}
#include "include/campaign_visibility.h"
void __cdecl frame() noexcept {
    if (GetCurrentThreadId()!=g.game_thread.load() || !g.active || g.pumping) return;
    try {
        auto game=g.game();if (!game) return;
        if (g.last_frame==game->frame_count) return;
        g.last_frame=game->frame_count;
        if (!g.mission || game->campaign_mission!=g.campaign_index || g.multiplayer() || g.replay()) {abandon_session();return;}
        frame_profile::begin();
        campaign_visibility::step();
        update_original_goal();protocol_pump(nullptr);
        if (!g.active) return;
        g.dialog.pump(GetTickCount64());
        if (!g.active) return;
        // Trigger new stages only on a later simulation frame, after the prior
        // modal has returned. Paused ProcessEvents pumps never advance stages
        // or the wave clock. An early goal drains stage2 then stage3 in order.
        const bool after_dialog=progress_frame_allowed(game->frame_count,g.dialog.open());
        if (after_dialog && g.protocol.phased() && g.protocol.ready() && game->frame_count!=g.phase_frame) {
            const auto phase=g.protocol.completed_phase();
            const bool goal=counter(kGoalCounter);
            const U32 barracks=counter(kMiddleCounter) ? 1u : 0u;
            const bool dialog_open=g.dialog.open();
            const U32 flags=phase | (goal ? 0x100u : 0u) | (dialog_open ? 0x200u : 0u);
            if(g.milestone_barracks!=barracks || g.milestone_flags!=flags) {
                log_event("Growth milestone check: phase=%u completed_barracks=%u original_goal=%u dialog_open=%u extended_arrays=%zu legacy_barracks=%u",
                    phase,barracks,goal ? 1u : 0u,dialog_open ? 1u : 0u,g.extended_count,game->completed_units_count[111][kOwner]);
                g.milestone_barracks=barracks;g.milestone_flags=flags;
            }
            const bool quarter=switch_set(game,campaign_config::kQuarterSwitch);
            const bool due=g.protocol.phase_version()==2 ?
                ((phase==1 && (quarter || barracks>0 || goal)) || (phase==2 && (barracks>0 || goal)) || (phase==3 && goal)) :
                ((phase==1 && (barracks>0 || goal)) || (phase==2 && goal));
            if(!dialog_open && due && g.protocol.request_phase(phase+1))
                log_event("Growth phase requested: phase=%u completed_barracks=%u original_goal=%u",phase+1,barracks,goal ? 1u : 0u);
        }
        const bool final_phase=g.protocol.growth_applied() && g.applied && !g.protocol.failed() &&
            (!g.protocol.phased() || g.protocol.completed_phase()==g.protocol.total_phases());
        const bool victory_ready=final_phase && after_dialog && game->frame_count!=g.phase_frame;
        set_counter(kReadyCounter,victory_ready ? 1u : 0u);
        set_counter(kAckCounter,victory_ready && g.protocol.victory_ack_ready() ? 1u : 0u);
        if(counter(kAckCounter) && campaign_config::final_mission(g.mission->mission_id) && !g.campaign_clear_shown){
            g.campaign_clear_shown=true;message("축하합니다. 캠페인을 클리어하셨습니다!");
        }
        mirror_handshake();
        enemy_progression::step(g.protocol.growth_applied() && g.applied && !g.protocol.failed(),!after_dialog,counter(kGoalCounter));
        enemy_detection::step(g.protocol.growth_applied()&&g.applied&&!g.protocol.failed(),!after_dialog,counter(kGoalCounter));
        frame_profile::mark(0);
        apply_unit_motion();
        frame_profile::mark(1);
        max_hp_cache::publish();
        frame_profile::mark(2);
        multi_target::step();
        rework_combat_v5::step();frame_profile::mark(3);rework_economy_v5::step();rework_cargo_v5::step();rework_energy_ui::publish();yamato_cost_ui::publish();rework_economy_ui::publish(false);rework_shield_ui_v5::publish(false);frame_profile::mark(4);
        bool ready=g.protocol.growth_applied() && g.applied && !g.protocol.failed();
        if(ready && after_dialog && !g.survival_hint_shown){
            if(g.mission->mission_id==103)message("추가 승리 조건: 적 기지의 모든 건물을 파괴하면 남은 시간과 관계없이 승리합니다.");
            else if(g.mission->mission_id==408)message("추가 승리 조건: 사원 활성화 후 적 기지의 모든 건물을 파괴하면 남은 시간과 관계없이 승리합니다.");
            g.survival_hint_shown=true;
        }
        rework_waves::tick(ready,!after_dialog,counter(kGoalCounter));regenerate_waves(game->elapsed_seconds);
        frame_profile::mark(5);
        wave_targeting::step(ready,counter(kGoalCounter));area_visuals::publish();
        g.dialog.set_wave_timer(sc1_native::wave_countdown_text(rework_waves::countdown(ready,counter(kGoalCounter))));
        frame_profile::mark(6);frame_profile::finish(ready&&after_dialog,game->frame_count,g.units_count,rework_combat_v5::projectiles.size(),rework_combat_v5::pending_shots.size());
    } catch (...) {set_counter(kReadyCounter,0);set_counter(kAckCounter,0);abandon_session();message("본편 플러그인 실행 오류. 추가 공세와 승리 기록을 중단했습니다.");}
}

template<class T> T function(const samase::PluginApi* api,samase::FuncId id) noexcept {
    return api->get_func && static_cast<U32>(id)<api->max_func_id ?
        reinterpret_cast<T>(api->get_func(static_cast<std::uint16_t>(id))) : nullptr;
}
bool bind_api(const samase::PluginApi* api) noexcept {
    if (!api || api->version<44) return false;
    if (!api->game || !api->first_active_unit || !api->first_hidden_unit || !api->unit_array_len ||
        !api->create_unit || !api->finish_unit_pre || !api->finish_unit_post || !api->issue_order ||
        !api->print_text || !api->read_map_file || !api->is_multiplayer || !api->is_replay ||
        !api->hook_on_first_file_access || !api->hook_init_units || !api->hook_step_objects || !api->extend_save || !api->load_vars || !api->read_vars ||
        !api->extended_dat || !api->create_lone_sprite || !api->add_overlay_iscript || !api->mutate_dat || !api->extended_arrays || !api->free_memory || !api->create_bullet) return false;
    const auto loaded_id=static_cast<std::uint16_t>(samase::VarId::LoadedSave);
    U8 loaded_support=0;api->load_vars(&loaded_id,&loaded_support,1);
    if (loaded_support<2) return false;
    // Resolve every init-only factory here. Store only runtime callbacks/data;
    // no runtime path retains or invokes the PluginApi registration object.
    g.api_version=api->version;
    g.dat_getters={reinterpret_cast<GetDat>(api->extended_dat(0)),reinterpret_cast<GetDat>(api->extended_dat(1)),reinterpret_cast<GetDat>(api->extended_dat(2)),nullptr,reinterpret_cast<GetDat>(api->extended_dat(4))};
    g.mutate_dat=api->mutate_dat;g.read_vars=api->read_vars;g.free_memory=api->free_memory;
    g.extended_count=api->extended_arrays(&g.extended);
    g.game=reinterpret_cast<GetGame>(api->game());
    g.first_active=reinterpret_cast<GetUnit>(api->first_active_unit());
    g.first_hidden=reinterpret_cast<GetUnit>(api->first_hidden_unit());
    g.unit_array=reinterpret_cast<UnitArray>(api->unit_array_len());
    g.create=reinterpret_cast<CreateUnit>(api->create_unit());
    g.lone_sprite=reinterpret_cast<CreateLone>(reinterpret_cast<GenericFn (__cdecl*)()>(api->create_lone_sprite)());
    g.add_overlay=reinterpret_cast<AddOverlay>(reinterpret_cast<GenericFn (__cdecl*)()>(api->add_overlay_iscript)());
    g.finish_pre=reinterpret_cast<UnitFn>(api->finish_unit_pre());
    g.finish_post=reinterpret_cast<UnitFn>(api->finish_unit_post());
    g.order=reinterpret_cast<IssueOrder>(api->issue_order());
    g.text=reinterpret_cast<PrintText>(api->print_text());
    g.read_map=reinterpret_cast<ReadMap>(api->read_map_file());
    g.multiplayer=reinterpret_cast<GetFlag>(api->is_multiplayer());
    g.replay=reinterpret_cast<GetFlag>(api->is_replay());
    g.set_hp=function<SetHp>(api,samase::FuncId::UnitSetHp);
    g.damage=function<DamageFn>(api,samase::FuncId::DamageUnit);
    rework_waves::native_tech_target=function<rework_waves::TechTargetFn>(api,samase::FuncId::CheckTechTargeting);
    rework_combat_v5::native_tech_target=rework_waves::native_tech_target;
    const auto can_attack=function<multi_target::CanAttackFn>(api,samase::FuncId::CanAttackUnit);
    const auto outside_range=function<multi_target::OutsideRangeFn>(api,samase::FuncId::IsOutsideAttackRange);
    const auto create_bullet=reinterpret_cast<CreateBulletFn>(reinterpret_cast<GenericFn (__cdecl*)()>(api->create_bullet)());
    multi_target::bind(can_attack,outside_range,create_bullet);
    log_event("Area visual renderer: registered=%u",area_visuals::bind(api)?1u:0u);
    return g.game && g.first_active && g.first_hidden && g.unit_array && g.create && g.finish_pre &&
           g.finish_post && g.order && g.text && g.read_map && g.multiplayer && g.replay &&
            g.set_hp && g.damage && rework_waves::native_tech_target && can_attack && outside_range && create_bullet && g.lone_sprite && g.add_overlay && g.dat_getters[0] && g.dat_getters[1] && g.dat_getters[2] && g.dat_getters[4] && (!g.extended_count || g.extended);
}
}

#include "include/max_hp_engine_hooks.h"
#include "include/samase_status_ui.h"
#include "include/samase_weapon_ui.h"
#include "include/samase_armor_ui.h"
#include "include/campaign_ultra_armor.h"
namespace {
#include "include/rework_lighting_v5.h"
#include "include/rework_energy_ui_v5.h"
#include "include/rework_economy_ui_v5.h"
#include "include/yamato_cost_ui.h"
#include "include/rework_shield_ui_v5.h"
#include "include/carrier_weapon_ui.h"
bool verify_stat_engine_after_dat() noexcept {
    if(native_tech_cost_view::yamato&&!native_tech_cost_view::verify_after_dat()){
        log_event("Native energy array changed after DAT mutation: stage=%s",native_tech_cost_view::last_error);return false;
    }
    if(carrier_weapon_ui::queued&&!carrier_weapon_ui::verify_installation()){
        log_event("Carrier weapon display changed after DAT mutation: stage=%s",carrier_weapon_ui::last_error);return false;
    }
    if(campaign_ultra_armor::queued&&!campaign_ultra_armor::verify_installation()){
        log_event("Ultra armor patch changed after DAT mutation.");return false;
    }
    if(yamato_cost_ui::queued && !yamato_cost_ui::verify_installation()){
        log_event("Yamato tooltip patch changed after DAT mutation.");return false;
    }
    if(max_hp_engine::hooks[0].queued && !max_hp_engine::verify_installation()){
        log_event("Maximum-health patch changed after DAT mutation: stage=%s",native_engine_hooks::last_install.stage);return false;
    }
    if(samase_armor_ui::queued && !samase_armor_ui::verify_installation()){
        log_event("Armor display changed after DAT mutation: stage=%s",samase_armor_ui::last_error);
        return false;
    }
    if(rework_economy_ui::queued && !rework_economy_ui::verify_installation()){
        log_event("Production tooltip changed after DAT mutation: stage=%s",rework_economy_ui::last_error);
        return false;
    }
    if(rework_shield_ui_v5::queued && !rework_shield_ui_v5::verify_installation()){
        log_event("Shield armor display changed after DAT mutation: stage=%s",rework_shield_ui_v5::last_error);
        return false;
    }
    return true;
}
}
void __cdecl verify_registered_engine_hooks() noexcept {
    g.hooks_ready=false;
    if(!rework_lighting_v5::verify_ready()){log_event("Lighting synchronization verification failed: stage=%s",rework_lighting_v5::last_error);visible_failure(L"그래픽 보호 기능을 확인하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!combat_effects::verify_installation() || !max_hp_engine::verify_installation() || !samase_status_ui::verify_installation() || !samase_weapon_ui::verify_installation() || !carrier_weapon_ui::verify_installation() || !samase_armor_ui::verify_installation() || !campaign_ultra_armor::verify_installation()){
        log_event("Engine patch verification failed: stage=%s error=%lu weapon_ui=%s armor_ui=%s",native_engine_hooks::last_install.stage,native_engine_hooks::last_install.win32_error,samase_weapon_ui::last_error,samase_armor_ui::last_error);
        visible_failure(L"게임 패치의 실제 적용을 확인하지 못했습니다. 플러그인을 활성화하지 않습니다. sc1_native.log를 확인하세요.");return;
    }
    if(!yamato_cost_ui::verify_installation() || !rework_relocation::bind() || !rework_cargo_v5::bind_native() || !campaign_visibility::bind_native() || !rework_energy_ui::verify_installation()){visible_failure(L"이동·에너지 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!rework_economy_ui::verify_installation()){log_event("Production tooltip verification failed: stage=%s",rework_economy_ui::last_error);visible_failure(L"생산 비용 표시를 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!rework_shield_ui_v5::verify_installation()){log_event("Shield armor display verification failed: stage=%s",rework_shield_ui_v5::last_error);visible_failure(L"보호막 방어력 표시를 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    g.hooks_ready=true;log_event("Required engine patch verified after loader; init_units/step_objects hooks ready.");
}
extern "C" __declspec(dllexport) void __cdecl samase_plugin_init(const samase::PluginApi* api) noexcept {
    log_event("Plugin entry: API=%u required=44",api ? api->version : 0);
    if (!bind_api(api)) {visible_failure(L"SC1 본편 플러그인을 시작하지 못했습니다. SAMASE API 44 또는 필수 기능을 사용할 수 없습니다. sc1_native.log를 확인하세요.");return;}
    if(!rework_lighting_v5::bind(api)){log_event("Lighting synchronization registration failed: stage=%s",rework_lighting_v5::last_error);visible_failure(L"그래픽 보호 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    log_event("Lighting synchronization guard registered: native13515, SAMASE0.10.28, awaiting loader verification.");
    if (!combat_effects::bind(api)) {
        visible_failure(L"전투 효과 엔진 연결을 확인하지 못했습니다. 지원되는 스타크래프트 버전은 1.23.10.13515입니다. 플러그인을 활성화하지 않습니다.");return;
    }
    rework_combat_v5::bind([](const GrowthSnapshot& snapshot,U32 ordinal) noexcept {return rework_catalog::rank(snapshot,ordinal);});
    if(!campaign_visibility::bind_api(api) || !rework_combat_v5::bind_engine(api)) {visible_failure(L"새 재능 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!api->client_selection || !(rework_cargo_v5::selection_source=reinterpret_cast<rework_cargo_v5::Selection>(reinterpret_cast<GenericFn (__cdecl*)()>(api->client_selection)()))) {visible_failure(L"수송 목록 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!api->pathing || !(rework_relocation::pathing_source=reinterpret_cast<rework_relocation::GetPathing>(reinterpret_cast<GenericFn (__cdecl*)()>(api->pathing)()))) {visible_failure(L"이동 경로 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if (!max_hp_engine::bind(api)) {
        log_event("Maximum-health engine registration failed: stage=%s error=%lu",native_engine_hooks::last_install.stage,native_engine_hooks::last_install.win32_error);
        visible_failure(L"최대 체력 기능을 연결하지 못했습니다. 플러그인을 활성화하지 않습니다. sc1_native.log를 확인하세요.");return;
    }
    if (!samase_status_ui::bind(api)) {
        log_event("SAMASE status display registration failed: stage=%s error=%lu",native_engine_hooks::last_install.stage,native_engine_hooks::last_install.win32_error);
        visible_failure(L"유닛 능력치 표시 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;
    }
    if(!rework_energy_ui::bind(api)){visible_failure(L"에너지 표시 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!yamato_cost_ui::bind(api)||!native_tech_cost_view::bind(native_engine_hooks::verified_base)){visible_failure(L"야마토 에너지 표시와 실제 비용을 연결하지 못했습니다.");return;}
    if(!rework_economy_ui::bind(api)){log_event("Production tooltip registration failed: stage=%s",rework_economy_ui::last_error);visible_failure(L"생산 비용 표시를 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if (!samase_weapon_ui::bind(api)) {
        log_event("SAMASE weapon display registration failed: stage=%s",samase_weapon_ui::last_error);
        visible_failure(L"유닛 공격력 표시 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;
    }
    if(!carrier_weapon_ui::bind(api)){log_event("Carrier attack tooltip registration failed: stage=%s",carrier_weapon_ui::last_error);visible_failure(L"캐리어 공격력 표시를 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if (!samase_armor_ui::bind(api)) {
        log_event("Armor display registration failed: stage=%s",samase_armor_ui::last_error);
        visible_failure(L"유닛 방어력 표시 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;
    }
    if(!rework_shield_ui_v5::bind(api)){log_event("Shield armor display registration failed: stage=%s",rework_shield_ui_v5::last_error);visible_failure(L"보호막 방어력 표시를 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!campaign_ultra_armor::bind(api)){visible_failure(L"울트라리스크 방어력 업그레이드를 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if (!register_owner_hooks(api)) {visible_failure(L"성장 효과의 소유자 분리 기능을 등록하지 못했습니다. 플러그인을 활성화하지 않습니다.");return;}
    if(!rework_combat_v5::bind_motion_commands(api)){visible_failure(L"잠복 이동 명령을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if(!rework_economy_v5::bind_commands(api)){visible_failure(L"생산 비용 기능을 연결하지 못했습니다. sc1_native.log를 확인하세요.");return;}
    if (!movement_effects::bind(api,combat_effects::melee_enter,combat_effects::melee_leave)) {
        visible_failure(L"이동·근접 공격 효과 연결에 실패했습니다. 플러그인을 활성화하지 않습니다.");return;
    }
    if (!g.dialog.initialize(api,dialog_callbacks())) {
        visible_failure(L"SC1 성장 선택 대화창에 필요한 기능을 등록하지 못했습니다. sc1_native.log를 확인하세요.");return;
    }
    log_event("Native choice UI registered: scoped native GameMenu text-panel templates; RunDialog, SpawnDialog and ProcessEvents; Stat_F10 automatic activation.");
    if (!api->extend_save(reinterpret_cast<const U8*>("sc1_native_v1"),save_extension,load_extension,init_game) ||
        !api->hook_init_units(init_units) || !api->hook_step_objects(frame,1)) {
        visible_failure(L"SC1 본편 플러그인의 초기화/프레임 훅을 등록하지 못했습니다. sc1_native.log를 확인하세요.");return;
    }
    reinterpret_cast<void (__cdecl*)(void (__cdecl*)())>(api->hook_on_first_file_access)(verify_registered_engine_hooks);
    log_event("Required hooks registered; awaiting loader engine-patch verification.");
}

#ifdef SC1_NATIVE_HOST_TEST
#include "include/native_host_tests.h"
#endif
