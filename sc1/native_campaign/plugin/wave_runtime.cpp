#include "wave_runtime.h"
#include "include/wave_config.generated.h"
#include "include/wave_progression.h"

#include <algorithm>

namespace sc1_native {
namespace {
constexpr int kPlayer = 1;
constexpr int kRescue = 2;
constexpr int kEnemy = 6;
constexpr int kScv = 7;

}

std::uint32_t WaveRuntime::used_supply(const WaveHost& host) const {
    std::uint32_t used=0;for(const auto id:wave_progression::kUnits){
        const auto cost=host.supply?host.supply(id):wave_progression::standard_supply(id);
        const auto count=host.count(host.context,kEnemy,id,nullptr);
        used+=static_cast<std::uint32_t>(std::min<std::uint64_t>(std::uint64_t(count)*cost,480u));
    }return used;
}
bool WaveRuntime::capacity(const WaveHost& host) const {
    return used_supply(host)<wave_progression::live_supply_cap(false)
        && host.count(host.context,kWaveAllPlayers,kWaveAnyUnit,nullptr)<1600u;
}

bool WaveRuntime::safe(std::uint32_t index, const WaveHost& host) const {
    const auto& origin = wave_config::kOrigins[index];
    return host.count(host.context, kPlayer, kWaveAnyUnit, &origin.guard) == 0
        && host.count(host.context, kRescue, kWaveAnyUnit, &origin.guard) == 0
        && host.count(host.context, kEnemy, kWaveMen, &origin.bounds) == 0;
}

void WaveRuntime::choose(const WaveHost& host) {
    const std::uint32_t orders[2][4] = {{0, 1, 2, 3}, {1, 0, 2, 3}};
    for (const auto index : orders[state_.preference]) {
        if (!safe(index, host)) {
            continue;
        }
        state_.pending = index + 1;
        state_.warning_ticks = 0;
        if (host.warning) {
            host.warning(host.context, index, &wave_config::kOrigins[index].center);
        }
        break;
    }
}

void WaveRuntime::spawn(std::uint8_t stacks,std::uint32_t elapsed_seconds,const WaveHost& host) {
    const auto cap=wave_progression::live_supply_cap(false),current=used_supply(host);
    const auto budget=std::min(wave_progression::budget(false,state_.stage,stacks),current<cap?cap-current:0u);
    std::uint32_t used=0,made=0;
    for(std::uint32_t offset=0;offset<4;offset++){
        const auto index=(state_.pending-1+offset)%4;if(!safe(index,host))continue;
        const auto& origin=wave_config::kOrigins[index];std::uint32_t created=0;
        for(const auto point:origin.cells){
            if(used>=budget || !capacity(host))break;
            const auto unit=wave_progression::select(wave_progression::Zerg,false,elapsed_seconds,state_.stage,made,budget-used,host.supply);
            if(!unit.valid)break;
            const WaveRect clearance{point.x-40,point.y-40,point.x+40,point.y+40};
            if(host.count(host.context,kWaveAllPlayers,kWaveAnyUnit,&clearance))continue;
            if(host.spawn(host.context,unit.unit_id,point.x,point.y,static_cast<std::uint8_t>(kEnemy))){used+=unit.supply;++made;++created;}
        }
        if(created)host.attack_area(host.context,static_cast<std::uint8_t>(kEnemy),&origin.bounds,wave_config::kTarget.x,wave_config::kTarget.y);
    }
    if(made && state_.stage<0xffffffffu)++state_.stage;
}

void WaveRuntime::tick(std::uint32_t frame, bool ready, std::uint32_t elapsed_seconds,
                       std::uint8_t stacks, bool goal_reached, const WaveHost& host, std::uint8_t interval_stacks) {
    if (state_.has_frame && state_.last_frame == frame) {
        return;
    }
    state_.has_frame = true;
    state_.last_frame = frame;
    if (!ready || goal_reached || !host.count || !host.spawn || !host.attack_area) {
        return;
    }
    if (!state_.home_seen && host.count(host.context, kPlayer, kScv, &wave_config::kHome) >= 1) {
        state_.home_seen = true;
    }
    if (state_.home_seen && state_.home_ticks < wave_config::kHomeGraceTicks) {
        ++state_.home_ticks;
    }
    if (!state_.active && elapsed_seconds >= std::max(wave_config::kFirstElapsedSeconds,wave_progression::first_elapsed_seconds(false))
        && state_.home_ticks >= wave_config::kHomeGraceTicks) {
        state_.active = true;
        state_.due = true;
        state_.interval_ticks = 0;
    }
    const auto interval=wave_progression::interval_seconds(false,interval_stacks)*24u;
    if (state_.active && ++state_.interval_ticks >= interval) {
        state_.interval_ticks = 0;
        state_.due = true;
    }
    if (state_.due && state_.pending == 0) {
        state_.due = false; // A blocked/capped attempt is never queued.
        if (capacity(host)) {
            choose(host);
        }
        state_.preference = (state_.preference + 1) % 2;
    }
    if (state_.pending != 0 && ++state_.warning_ticks >= wave_config::kWarningTicks) {
        spawn(stacks,elapsed_seconds,host);
        state_.pending = 0;
    }
    if (++state_.retry_ticks >= wave_config::kRetryTicks) {
        state_.retry_ticks = 0;
        // Reissue orders only at entries and only for dedicated P7 combat units.
        for (const auto& origin : wave_config::kOrigins) {
            host.attack_area(host.context, static_cast<std::uint8_t>(kEnemy), &origin.bounds,
                             wave_config::kTarget.x, wave_config::kTarget.y);
        }
    }
}

} // namespace sc1_native
