#pragma once
// Include inside the native plugin namespace after bw::Unit/U32 are declared.
namespace rework_curses {
bool marked(const bw::Unit*) noexcept;
bool spell_disabled(const bw::Unit*) noexcept;
U32 hp_percent(const bw::Unit*) noexcept;
U32 shield_percent(const bw::Unit*) noexcept;
U32 attack_percent(const bw::Unit*) noexcept;
U32 speed_percent(const bw::Unit*) noexcept;
U32 lifesteal_percent(const bw::Unit*) noexcept;
bool barrier(const bw::Unit*) noexcept;
bool appearing(const bw::Unit*) noexcept;
bool transport_hold(const bw::Unit*) noexcept;
bw::Unit* raid_target(const bw::Unit*) noexcept;
void transformed(bw::Unit*,U32 old_id) noexcept;
void before_give(bw::Unit*,U32 new_owner) noexcept;
void forget(bw::Unit*) noexcept;
}
namespace rework_waves {
void reset() noexcept;
void note_death(bw::Unit*,bool) noexcept;
}
