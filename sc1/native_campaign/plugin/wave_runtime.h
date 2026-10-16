#pragma once

// Portable T01 wave scheduler. The native plugin owns all game/API pointers.
#include <cstdint>

namespace sc1_native {

struct WavePoint {
    std::int32_t x;
    std::int32_t y;
};

struct WaveRect {
    std::int32_t left;
    std::int32_t top;
    std::int32_t right;
    std::int32_t bottom;
};

constexpr int kWaveAllPlayers = -1;
constexpr int kWaveAnyUnit = -1;
constexpr int kWaveMen = -2;

struct WaveHost {
    void* context = nullptr;
    // nullptr area means the whole map. Count actual living, active units.
    // Men queries are used only for the dedicated P7 Zerg wave pool.
    std::uint32_t (*count)(void*, int owner, int unit, const WaveRect* area) = nullptr;
    // nullptr means creation failed; failure is discarded, never queued.
    void* (*spawn)(void*, std::uint16_t unit, std::int32_t x, std::int32_t y,
                   std::uint8_t owner) = nullptr;
    // Reorder only P7 combat units currently inside this entry's bounds.
    void (*attack_area)(void*, std::uint8_t owner, const WaveRect* area,
                        std::int32_t target_x, std::int32_t target_y) = nullptr;
    // Optional one-time text warning for a scheduled attempt. No invented
    // minimap-ping API is required by this component.
    void (*warning)(void*, std::uint32_t origin_index, const WavePoint* point) = nullptr;
    // Original units.dat half-supply; canonical pinned values are the fallback.
    std::uint32_t (*supply)(std::uint16_t unit) = nullptr;
};

struct WaveState {
    bool home_seen = false;
    std::uint32_t home_ticks = 0;
    bool active = false;
    std::uint32_t interval_ticks = 0;
    bool due = false;
    std::uint32_t pending = 0; // 0 none; 1..4 origin index+1.
    std::uint32_t warning_ticks = 0;
    std::uint32_t preference = 0;
    std::uint32_t stage = 0;
    std::uint32_t retry_ticks = 0;
    std::uint32_t ling_remainder = 0;
    std::uint32_t hydra_remainder = 0;
    bool has_frame = false;
    std::uint32_t last_frame = 0;
};

class WaveRuntime {
public:
    void reset() noexcept { state_ = WaveState{}; }
    const WaveState& state() const noexcept { return state_; }
    void tick(std::uint32_t frame, bool growth_ready, std::uint32_t elapsed_seconds,
              std::uint8_t wave_curse_stacks, bool goal_reached, const WaveHost& host,
              std::uint8_t interval_curse_stacks=0);

private:
    std::uint32_t used_supply(const WaveHost& host) const;
    bool capacity(const WaveHost& host) const;
    bool safe(std::uint32_t origin_index, const WaveHost& host) const;
    void choose(const WaveHost& host);
    void spawn(std::uint8_t stacks,std::uint32_t elapsed_seconds,const WaveHost& host);
    WaveState state_{};
};

} // namespace sc1_native
