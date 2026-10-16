#pragma once
// Ordinary weapon effects run before the native armor/shield/matrix split.
// Include after DamageObservationScope. Engine installation must separately
// verify the pinned DoWeaponDamage call ABI and all stolen instructions.
#include <new>
#include "native_engine_hooks.h"
namespace combat_effects {
using WeaponDamageFn=void (__cdecl*)(bw::Unit*,std::int32_t,U8,U32,U8,bw::Unit*,U32);
struct HitContext {
    bool normal,elite,bullet;U32 bonus;bw::Unit* source;ProjectileSource identity;
    HitContext() noexcept:normal(g.normal_hit),elite(g.elite_hit),bullet(g.bullet_hit_context),bonus(g.hit_bonus),source(g.hit_source),identity(g.hit_identity){}
    void restore() const noexcept {g.normal_hit=normal;g.elite_hit=elite;g.bullet_hit_context=bullet;g.hit_bonus=bonus;g.hit_source=source;g.hit_identity=identity;}
};
struct MeleeFrame {
    bw::Unit* unit=nullptr;ProjectileSource identity{};U32 weapon=130;bool engaged=false;
    HitContext context{};OwnerDatScope* dat=nullptr;
    alignas(OwnerDatScope) unsigned char storage[sizeof(OwnerDatScope)];
};
inline MeleeFrame melee_frames[32];
inline U32 melee_depth=0,overflow_depth=0,weapon_depth=0;
inline bool verified_engine_hook=false;
inline WeaponDamageFn original_weapon_damage=nullptr;
// Optional rework adapter brackets exactly one native armor/shield split.
// The null callbacks retain the legacy production path byte-for-byte.
using DamageEnter=void* (*)(bw::Unit*,bw::Unit*,U32,U32,std::int32_t&) noexcept;
using DamageLeave=void (*)(void*) noexcept;
inline DamageEnter damage_enter=nullptr;
inline DamageLeave damage_leave=nullptr;
using DamageFilter=bool (*)(bw::Unit*,bw::Unit*,U32,bool) noexcept;
inline DamageFilter damage_filter=nullptr;
using DamageSkip=bool (*)(void*) noexcept;
inline DamageSkip damage_skip=nullptr;
inline bool weapon_damage_active() noexcept {return weapon_depth!=0;}
inline bool active_session() noexcept {return g.active && g.applied && g.game && GetCurrentThreadId()==g.game_thread.load();}
inline ProjectileSource source_identity(bw::Unit* u) noexcept {
    return valid_unit(u) ? ProjectileSource{u,u->unit_id,u->player,u->minor_unique_index} : ProjectileSource{};
}
inline bw::Unit* melee_source() noexcept {
    if(!melee_depth || overflow_depth)return nullptr;
    const auto& frame=melee_frames[melee_depth-1];
    return frame.engaged ? verified_projectile_source(frame.identity) : nullptr;
}
inline void melee_enter(bw::Unit* u) noexcept {
    if(overflow_depth || melee_depth>=32){++overflow_depth;return;}
    auto& frame=melee_frames[melee_depth++];frame.unit=u;frame.identity={};frame.weapon=130;frame.engaged=false;frame.dat=nullptr;frame.context=HitContext{};
    if(!active_session() || !valid_unit(u) || (u->flags&0x40000000u))return;
    auto target=u->order_target.unit;auto source=effect_body(u);
    if(!source || hallucination(source) || !valid_unit(target))return;
    const auto weapon=original_stat({0,17,u->unit_id});
    if(weapon>=130 || !ordinary_weapon(weapon))return;
    frame.identity=source_identity(source);frame.weapon=weapon;frame.engaged=true;
    // Target armor and attacker's weapon data require different owner views.
    // Keep the original AttackMelee opcode, hit count, sound/RNG and targeting.
    frame.dat=new(frame.storage) OwnerDatScope(unit_owner(target),unit_owner(source),target,source);
    g.normal_hit=true;g.bullet_hit_context=false;g.hit_identity=frame.identity;g.hit_source=source;
    const auto track=existing_track(source);g.elite_hit=track && track->elite && regular_enemy(source);
    note_attack_launch(u,weapon);g.hit_bonus=charged_attack(u,weapon);
}
inline void close_melee_frame() noexcept {
    auto& frame=melee_frames[--melee_depth];
    if(frame.dat){frame.dat->~OwnerDatScope();frame.dat=nullptr;}
    frame.context.restore();frame.engaged=false;frame.unit=nullptr;frame.identity={};
}
inline void reset_melee() noexcept {overflow_depth=0;while(melee_depth)close_melee_frame();}
inline void melee_leave(bw::Unit* u) noexcept {
    if(overflow_depth){--overflow_depth;return;}
    if(!melee_depth)return;
    if(melee_frames[melee_depth-1].unit!=u){reset_melee();return;}
    close_melee_frame();
}
inline std::int32_t percentage(std::int32_t amount,U32 numerator,U32 denominator) noexcept {
    if(amount<=0 || !denominator)return amount;
    return static_cast<std::int32_t>(std::min<std::uint64_t>(0x7fffffffu,(std::uint64_t(amount)*numerator+denominator-1)/denominator));
}
inline void weapon_damage(bw::Unit* target,std::int32_t damage,U8 weapon,U32 divisor,U8 direction,bw::Unit* attacker,U32 player,WeaponDamageFn original) noexcept {
    if(!original)return;
    if(!active_session()){original(target,damage,weapon,divisor,direction,attacker,player);return;}
    const HitContext saved;
    auto source=g.bullet_hit_context ? verified_projectile_source(g.hit_identity) : melee_source();
    if(!source&&!g.bullet_hit_context&&!ordinary_weapon(weapon))source=effect_body(attacker);
    const bool melee=source && !g.bullet_hit_context && effect_body(attacker)==source;
    const bool normal=ordinary_weapon(weapon) && ((g.bullet_hit_context && g.normal_hit) || (melee && melee_frames[melee_depth-1].weapon==weapon));
    // Preserve the engine's original damage calculation. Only the incoming
    // ordinary attack amount changes, before the original armor/shield split.
    // The original divisor, direction, attacker and player are forwarded once.
    OwnerDatScope view(unit_owner(target),player,target,source);
    DamageObservationScope observed(target,player);
    g.normal_hit=normal;
    if(damage_filter&&!damage_filter(target,source,weapon,normal)){saved.restore();return;}
    if(normal){
        if(g.elite_hit)damage=percentage(damage,6,5);
        if(g.hit_bonus)damage=percentage(damage,100+g.hit_bonus,100);
        const auto track=existing_track(target);
        if(track && track->barrier && regular_enemy(target) && g.game()->elapsed_seconds-track->spawn_second<20)damage=percentage(damage,3,4);
        if(rework_curses::marked(source))damage=percentage(damage,rework_curses::attack_percent(source),100);
        if(rework_curses::barrier(target))damage=percentage(damage,3,4);
    }
    auto extension=damage_enter ? damage_enter(target,source,weapon,divisor,damage) : nullptr;
    if(!extension||!damage_skip||!damage_skip(extension)){++weapon_depth;original(target,damage,weapon,divisor,direction,attacker,player);--weapon_depth;}
    if(extension && damage_leave)damage_leave(extension);
    saved.restore();
}
inline void __cdecl engine_weapon_damage(bw::Unit* target,std::int32_t damage,U8 weapon,U32 divisor,U8 direction,bw::Unit* attacker,U32 player) noexcept {
    weapon_damage(target,damage,weapon,divisor,direction,attacker,player,original_weapon_damage);
}
// The integration layer may publish an original trampoline only after its
// executable hash, callsites, ABI and relocation instructions were verified.
inline void bind_verified_weapon_hook(WeaponDamageFn original) noexcept {original_weapon_damage=original;verified_engine_hook=original!=nullptr;}
inline native_engine_hooks::Hook weapon_hook;
inline constexpr U8 weapon_prologue[]={0x40,0x53,0x55,0x57,0x41,0x55,0x48,0x83,0xec,0x38,0x83,0x79,0x10,0x00};
inline constexpr U8 weapon_unwind[]={0x01,0x0a,0x05,0x00,0x0a,0x62,0x06,0xd0,0x04,0x70,0x03,0x50,0x02,0x30,0x00,0x00};
inline constexpr U8 witness_0[]={0xe8,0x82,0xf5,0xff,0xff};
inline constexpr U8 witness_1[]={0xe8,0x7f,0xc6,0xff,0xff};
inline constexpr U8 witness_2[]={0xe8,0xaf,0x4b,0x02,0x00};
inline constexpr native_engine_hooks::Bytes weapon_witnesses[]={
 {0x1b37a9,witness_0,sizeof(witness_0)},{0x1b66ac,witness_1,sizeof(witness_1)},{0x191a1c,witness_2,sizeof(witness_2)}};
inline constexpr native_engine_hooks::Spec weapon_spec{0x1b2d30,weapon_prologue,sizeof(weapon_prologue),weapon_unwind,sizeof(weapon_unwind),weapon_witnesses,std::size(weapon_witnesses)};
// This must precede register_owner_hooks so API pointers still identify the
// pinned native entry points observed by the read-only engine diagnostic.
inline bool bind(const samase::PluginApi* api) noexcept {
    if(verified_engine_hook)return true;
    if(!api || api->version<44 || !api->get_func || !api->write_exe_memory || !native_engine_hooks::verify_image())return false;
    const auto base=native_engine_hooks::verified_base;
    if(reinterpret_cast<void*>(api->get_func(static_cast<std::uint16_t>(samase::FuncId::HitUnit)))!=base+0x1b3720 ||
       reinterpret_cast<void*>(api->get_func(static_cast<std::uint16_t>(samase::FuncId::DamageUnit)))!=base+0x1b2f70)return false;
    if(!native_engine_hooks::register_hook(weapon_spec,reinterpret_cast<void*>(engine_weapon_damage),weapon_hook,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory)))return false;
    // Safe pass-through is available even if a later registration fails.
    // Growth remains inactive until first-file verifies the actual branch.
    original_weapon_damage=reinterpret_cast<WeaponDamageFn>(weapon_hook.trampoline);
    return true;
}
inline bool verify_installation() noexcept {
    if(!native_engine_hooks::verify_registered(weapon_spec,reinterpret_cast<void*>(engine_weapon_damage),weapon_hook))return false;
    verified_engine_hook=true;return true;
}

}
