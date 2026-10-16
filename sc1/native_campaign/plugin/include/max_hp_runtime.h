#pragma once
// Single Q8 maximum-health calculation shared by scoped native calls,
// restoration/healing and the verified native max-health query adapter.
// Reading this value never changes global DAT or the unit's current HP.
U32 original_stat(Key key) noexcept;
U32 owner_stat(U32 owner,Key key) noexcept;
U32 effective_max_hp(const bw::Unit* unit) noexcept {
    if(!valid_unit(unit) || unit->unit_id>=228)return 0;
    const Key key{0,8,unit->unit_id};
    const U32 original=original_stat(key);
    if(!g.active || !g.applied || hallucination(unit) || hallucination_creation_depth)return original;
    const U32 base=owner_stat(unit->player,key);
    if(rework_curses::marked(unit))return static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(base)*rework_curses::hp_percent(unit)/100));
    const auto track=existing_track(unit);
    const bool elite=regular_enemy(unit) && track && track->elite;
    return static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,
        std::uint64_t(base)*(elite ? 3u:2u)/2u));
}

// Render callbacks must not traverse vectors or read mutable growth state.
// A single simulation-thread writer publishes atomic values. A reader retries
// no locks and falls back to the engine value during a concurrent publication.
namespace max_hp_cache {
constexpr std::size_t capacity=65536;
static_assert(std::atomic<std::uint64_t>::is_always_lock_free,"x64 HP cache requires lock-free QWORD reads");
std::atomic<std::uint64_t> sequence{0};
std::atomic<bool> enabled{false};
std::atomic<std::uintptr_t> array_base{0};
std::atomic<std::size_t> array_count{0};
std::array<std::atomic<U32>,228> original_values{};
std::array<std::atomic<U32>,12*228> owner_values{};
std::array<std::atomic<U32>,228> original_shields{};
std::array<std::atomic<U32>,12*228> owner_shields{};
std::array<std::atomic<U32>,228> original_armor{};
std::array<std::atomic<U32>,12*228> owner_armor{};
// Published in the same epoch as HP/shields; renderer never reads owner_edits.
std::array<std::atomic<U32>,2*130> original_weapon_values{};
std::array<std::atomic<U32>,12*2*130> owner_weapon_values{};
std::array<std::atomic<bool>,228> regular_values{};
std::array<std::atomic<std::uint64_t>,capacity> elite_values{};
std::uintptr_t writer_base=0;std::size_t writer_count=0;U32 writer_signature=0xffffffffu;
U32 identity(const bw::Unit* unit) noexcept {
    return U32(unit->unit_id)|(U32(unit->player)<<16)|(U32(unit->minor_unique_index)<<24);
}
void reset() noexcept {
    enabled.store(false,std::memory_order_release);sequence.fetch_add(1,std::memory_order_acq_rel);
    array_base.store(0,std::memory_order_relaxed);array_count.store(0,std::memory_order_relaxed);
    for(auto& value:elite_values)value.store(0,std::memory_order_relaxed);
    writer_base=0;writer_count=0;writer_signature=0xffffffffu;
    sequence.fetch_add(1,std::memory_order_release);
}
void forget(const bw::Unit* unit) noexcept {
    if(!valid_unit(unit))return;const auto index=static_cast<std::size_t>(unit-g.units);
    if(index<capacity)elite_values[index].store(0,std::memory_order_release);
}
void publish_unit(const bw::Unit* unit) noexcept {
    if(!valid_unit(unit))return;const auto index=static_cast<std::size_t>(unit-g.units);if(index>=capacity)return;
    const auto track=existing_track(unit);std::uint64_t value=0;
    if(g.active && g.applied && track && ((track->elite && regular_enemy(unit)) || (rework_curses::marked(unit) && rework_curses::hp_percent(unit)!=100)))
        value=(std::uint64_t(identity(unit))<<32)|effective_max_hp(unit);
    elite_values[index].store(value,std::memory_order_release);
}
void begin_transform(const bw::Unit* unit) noexcept {
    if(!valid_unit(unit))return;const auto index=static_cast<std::size_t>(unit-g.units);if(index>=capacity)return;
    const auto track=existing_track(unit);
    // Native TransformUnit may query both old and new IDs before returning.
    // Preserve this same instance's elite role; recompute the current type from
    // the published owner table. Noncombat forms never inherit that role.
    if(g.active && g.applied && track && ((track->elite && regular_enemy(unit)) || (rework_curses::marked(unit) && rework_curses::hp_percent(unit)!=100)))
        elite_values[index].store(std::uint64_t((identity(unit)&0xffff0000u)|0xffffu)<<32,std::memory_order_release);
}
bool publish(bool force=false) noexcept {
    if(!g.active || !g.applied || !g.units || g.units_count>capacity){reset();return false;}
    const auto base=reinterpret_cast<std::uintptr_t>(g.units);U32 signature=player_owner()<<16;
    for(U32 owner=0;owner<12;owner++)if(is_enemy(owner))signature|=1u<<owner;
    const bool bulk=force || writer_signature!=signature || writer_base!=base || writer_count!=g.units_count;
    if(bulk)sequence.fetch_add(1,std::memory_order_acq_rel);
    if(writer_base!=base || writer_count!=g.units_count){
        for(auto& value:elite_values)value.store(0,std::memory_order_relaxed);
        writer_base=base;writer_count=g.units_count;force=true;
    }
    array_base.store(base,std::memory_order_relaxed);array_count.store(g.units_count,std::memory_order_relaxed);
    if(force || writer_signature!=signature){
        for(U32 id=0;id<228;id++){
            original_values[id].store(original_stat({0,8,id}),std::memory_order_relaxed);
            original_shields[id].store(original_stat({0,6,id})?original_stat({0,7,id}):0,std::memory_order_relaxed);
            original_armor[id].store(original_stat({0,27,id}),std::memory_order_relaxed);
            regular_values[id].store(regular_combat_type(id),std::memory_order_relaxed);
            for(U32 owner=0;owner<12;owner++){
                owner_values[owner*228+id].store(owner_stat(owner,{0,8,id}),std::memory_order_relaxed);
                owner_armor[owner*228+id].store(owner_stat(owner,{0,27,id}),std::memory_order_relaxed);
                owner_shields[owner*228+id].store(owner_stat(owner,{0,6,id})?owner_stat(owner,{0,7,id}):0,std::memory_order_relaxed);
            }
        }
        for(U32 field=14;field<=15;field++)for(U32 weapon=0;weapon<130;weapon++){
            const U32 offset=(field-14)*130+weapon;
            original_weapon_values[offset].store(original_stat({1,field,weapon}),std::memory_order_relaxed);
            for(U32 owner=0;owner<12;owner++)
                owner_weapon_values[owner*260+offset].store(owner_stat(owner,{1,field,weapon}),std::memory_order_relaxed);
        }
        writer_signature=signature;
    }
    for(std::size_t i=0;i<g.units_count;i++)publish_unit(g.units+i);
    if(bulk)sequence.fetch_add(1,std::memory_order_release);
    enabled.store(true,std::memory_order_release);return true;
}
bool read_values(const bw::Unit* unit,U32& maximum_q8,U32* shields_whole,U32* original_q8) noexcept {
    if(!unit || !enabled.load(std::memory_order_acquire))return false;
    const auto start=sequence.load(std::memory_order_acquire);if(start&1u)return false;
    const auto base=array_base.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(unit);
    const auto count=array_count.load(std::memory_order_relaxed);
    if(address<base || (address-base)%sizeof(bw::Unit))return false;
    const auto index=(address-base)/sizeof(bw::Unit);if(index>=count || index>=capacity)return false;
    const U32 key=identity(unit),id=key&0xffffu,owner=(key>>16)&255u;
    if(id>=228 || owner>=12)return false;
    const bool illusion=(unit->flags&0x40000000u)!=0;
    const U32 original=original_values[id].load(std::memory_order_relaxed);
    U32 result=illusion?original:owner_values[owner*228+id].load(std::memory_order_relaxed);
    const U32 shield=illusion?original_shields[id].load(std::memory_order_relaxed):owner_shields[owner*228+id].load(std::memory_order_relaxed);
    const auto elite=elite_values[index].load(std::memory_order_acquire);const U32 elite_key=static_cast<U32>(elite>>32);
    if(!illusion && elite && elite_key==key)result=static_cast<U32>(elite);
    else if(!illusion && elite && elite_key==((key&0xffff0000u)|0xffffu) && regular_values[id].load(std::memory_order_relaxed))
        result=static_cast<U32>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(result)*3/2));
    if(sequence.load(std::memory_order_acquire)!=start || !enabled.load(std::memory_order_acquire) || identity(unit)!=key)return false;
    maximum_q8=result;if(shields_whole)*shields_whole=shield;if(original_q8)*original_q8=original;return true;
}
bool read_armor(const bw::Unit* unit,U32& value) noexcept {
    if(!unit || !enabled.load(std::memory_order_acquire))return false;
    const auto start=sequence.load(std::memory_order_acquire);if(start&1u)return false;
    const auto base=array_base.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(unit);
    const auto count=array_count.load(std::memory_order_relaxed);
    if(address<base || (address-base)%sizeof(bw::Unit))return false;
    const auto index=(address-base)/sizeof(bw::Unit);if(index>=count || index>=capacity)return false;
    const U32 key=identity(unit),id=key&0xffffu,owner=(key>>16)&255u;
    if(id>=228 || owner>=12)return false;
    const bool illusion=(unit->flags&0x40000000u)!=0;
    const U32 result=illusion?original_armor[id].load(std::memory_order_relaxed):owner_armor[owner*228+id].load(std::memory_order_relaxed);
    if(sequence.load(std::memory_order_acquire)!=start || !enabled.load(std::memory_order_acquire) || identity(unit)!=key)return false;
    value=result;return true;
}
bool read_weapon(const bw::Unit* unit,U32 field,U32 weapon,U32& value) noexcept {
    if(!unit || field<14 || field>15 || weapon>=130 || !enabled.load(std::memory_order_acquire))return false;
    const auto start=sequence.load(std::memory_order_acquire);if(start&1u)return false;
    const auto base=array_base.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(unit);
    const auto count=array_count.load(std::memory_order_relaxed);
    if(address<base || (address-base)%sizeof(bw::Unit))return false;
    const auto index=(address-base)/sizeof(bw::Unit);if(index>=count || index>=capacity)return false;
    const U32 key=identity(unit),id=key&0xffffu,owner=(key>>16)&255u;
    if(id>=228 || owner>=12)return false;
    const U32 offset=(field-14)*130+weapon;const bool illusion=(unit->flags&0x40000000u)!=0;
    const U32 result=illusion?original_weapon_values[offset].load(std::memory_order_relaxed):
        owner_weapon_values[owner*260+offset].load(std::memory_order_relaxed);
    if(sequence.load(std::memory_order_acquire)!=start || !enabled.load(std::memory_order_acquire) || identity(unit)!=key)return false;
    value=result;return true;
}
bool read(const bw::Unit* unit,U32& maximum_q8,U32* original_q8=nullptr) noexcept {return read_values(unit,maximum_q8,nullptr,original_q8);}
bool read_display(const bw::Unit* unit,U32& maximum_q8,U32& shields_whole,U32* original_q8=nullptr) noexcept {
    return read_values(unit,maximum_q8,&shields_whole,original_q8);
}
}
