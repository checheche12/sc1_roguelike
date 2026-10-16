#pragma once
// SAMASE's status screen otherwise reads only the native u16 energy high byte.
// Publish complete virtual energy on the simulation thread; render readers do
// not access mutable talent vectors or change a unit/DAT while drawing.
namespace rework_energy_ui {
constexpr std::size_t capacity=8191;
struct Entry {std::atomic<U32> sequence{0},identity{0},current{0},bonus{0};};
inline std::array<Entry,capacity> cache{};
inline std::atomic<std::uintptr_t> unit_base{0};
inline std::atomic<std::size_t> unit_count{0};
inline std::atomic<bool> active{false},passthrough{false};
inline U32 identity(const bw::Unit* u) noexcept {return U32(u->unit_id)|(U32(u->player)<<16)|(U32(u->minor_unique_index)<<24);}
inline void reset() noexcept {active.store(false,std::memory_order_release);unit_base.store(0);unit_count.store(0);}
inline void publish() noexcept {
    if(!g.active || !g.applied || !g.units || g.units_count>capacity){reset();return;}
    unit_base.store(reinterpret_cast<std::uintptr_t>(g.units),std::memory_order_relaxed);unit_count.store(g.units_count,std::memory_order_relaxed);
    for(std::size_t i=0;i<g.units_count;i++){
        auto u=g.units+i;U32 current=0,bonus=0,id=0;
        if(rework_combat_v5::own(u) && (bonus=rework_combat_v5::energy_bonus(u))!=0){
            auto state=rework_combat_v5::state(u);if(state){current=U32(u->energy)+state->energy_reserve;id=identity(u);}
        }
        auto& e=cache[i];e.sequence.fetch_add(1,std::memory_order_acq_rel);e.identity.store(id,std::memory_order_relaxed);
        e.current.store(current,std::memory_order_relaxed);e.bonus.store(bonus,std::memory_order_relaxed);e.sequence.fetch_add(1,std::memory_order_release);
    }
    active.store(true,std::memory_order_release);
}
inline bool read(const bw::Unit* u,U32& current,U32& bonus) noexcept {
    if(passthrough.load(std::memory_order_acquire) || !active.load(std::memory_order_acquire) || !u)return false;
    const auto base=unit_base.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(u),count=unit_count.load(std::memory_order_relaxed);
    if(address<base || (address-base)%sizeof(bw::Unit)!=0)return false;const auto index=(address-base)/sizeof(bw::Unit);if(index>=count || index>=capacity)return false;
    auto& e=cache[index];const auto before=e.sequence.load(std::memory_order_acquire);if(before&1)return false;
    const U32 id=e.identity.load(std::memory_order_relaxed);current=e.current.load(std::memory_order_relaxed);bonus=e.bonus.load(std::memory_order_relaxed);
    return id && id==identity(u) && e.sequence.load(std::memory_order_acquire)==before;
}
using Maximum=U32 (__cdecl*)(U8,std::uint16_t,void*);
inline Maximum original_maximum=nullptr;
inline U32 __cdecl maximum(U8 owner,std::uint16_t id,void* game,const bw::Unit* unit) noexcept {
    const U32 original=original_maximum ? original_maximum(owner,id,game):0;U32 current=0,bonus=0;
    return unit && unit->player==owner && unit->unit_id==id && read(unit,current,bonus) ? original+bonus:original;
}
inline U32 __cdecl current(const bw::Unit* unit) noexcept {U32 energy=0,bonus=0;return read(unit,energy,bonus) ? energy>>8:unit ? U32(unit->energy)>>8:0;}
inline constexpr U32 sites[2]={0x1b2f00,0x1b2f72};
inline constexpr U8 maximum_call[]={0xe8,0x62,0xb0,0x01,0x00};
inline constexpr U8 current_read[]={0x41,0x0f,0xb6,0x97,0xe7,0x00,0x00,0x00};
inline U8* module=nullptr,*relays=nullptr;
inline U8 branches[2][8]{};
inline U8 expected_relays[2][19]{};
inline bool ready=false;
inline bool verify_installation() noexcept {
    return ready && module && relays && native_engine_hooks::match(module+sites[0],branches[0],5) && native_engine_hooks::match(module+sites[1],branches[1],8) &&
        native_engine_hooks::match(relays,expected_relays[0],19) && native_engine_hooks::match(relays+64,expected_relays[1],17);
}
inline bool install_at(U8* base) noexcept {
    using namespace native_engine_hooks;
    if(ready)return base==module && verify_installation();
    if(relays || !base || !match(base+sites[0],maximum_call,5) || !match(base+sites[1],current_read,8))return false;
    auto code=nearby_code(base+sites[0]);if(!code)return false;
    const U8 max_args[]={0x4c,0x8b,0x4c,0x24,0x40};std::memcpy(code,max_args,sizeof(max_args));absolute_jump(code+5,reinterpret_cast<void*>(maximum));
    const U8 current_args[]={0x4c,0x89,0xf9};std::memcpy(code+64,current_args,sizeof(current_args));absolute_jump(code+67,reinterpret_cast<void*>(current));
    U8 next[2][8]{};for(U32 i=0;i<2;i++){
        const auto distance=reinterpret_cast<std::intptr_t>(code+i*64)-reinterpret_cast<std::intptr_t>(base+sites[i]+5);
        if(distance<INT32_MIN || distance>INT32_MAX){VirtualFree(code,0,MEM_RELEASE);return false;}
        next[i][0]=0xe8;const auto delta=std::int32_t(distance);std::memcpy(next[i]+1,&delta,4);
    }
    next[1][5]=0x89;next[1][6]=0xc2;next[1][7]=0x90; // EDX = returned current energy, no 8-bit truncation.
    DWORD old=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),code,128)){VirtualFree(code,0,MEM_RELEASE);return false;}
    const std::size_t span=sites[1]+8-sites[0];auto start=base+sites[0];
    if(!protect_code_for_write(start,span,&old)){VirtualFree(code,0,MEM_RELEASE);return false;}
    original_maximum=reinterpret_cast<Maximum>(base+0x1cdf67);
    std::memcpy(base+sites[0],next[0],5);std::memcpy(base+sites[1],next[1],8);
    bool okay=match(base+sites[0],next[0],5) && match(base+sites[1],next[1],8);
    DWORD ignored=0;okay=VirtualProtect(start,span,old,&ignored)!=0 && FlushInstructionCache(GetCurrentProcess(),start,span)!=0 && okay;
    if(!okay){
        DWORD recovery=0;bool restored=false;
        if(protect_code_for_write(start,span,&recovery)){
            std::memcpy(base+sites[0],maximum_call,5);std::memcpy(base+sites[1],current_read,8);
            VirtualProtect(start,span,old,&ignored);FlushInstructionCache(GetCurrentProcess(),start,span);
            restored=match(base+sites[0],maximum_call,5) && match(base+sites[1],current_read,8);
        }
        if(restored){original_maximum=nullptr;VirtualFree(code,0,MEM_RELEASE);}else {module=base;relays=code;passthrough.store(true,std::memory_order_release);}
        return false;
    }
    module=base;relays=code;std::memcpy(branches,next,sizeof(next));std::memcpy(expected_relays[0],code,19);std::memcpy(expected_relays[1],code+64,17);ready=true;return verify_installation();
}
inline bool bind(const samase::PluginApi* api) noexcept {return samase_status_ui::verify_module(api) && install_at(samase_status_ui::module_base());}
}
