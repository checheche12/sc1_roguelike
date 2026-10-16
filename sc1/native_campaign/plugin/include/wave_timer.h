#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <string>
#include "../wave_runtime.h"
#include "wave_config.generated.h"
#include "wave_progression.h"
namespace sc1_native {
struct WaveCountdown {
    enum class Kind { Hidden, WaitingForHome, Scheduled } kind=Kind::Hidden;
    std::uint32_t seconds=0;
};
// Pure projection of scheduler state. It never starts/stops a timer or touches
// original mission CountdownTimer/leaderboard fields. Ticks mean simulation
// frames, so a paused game displays the same remaining time.
inline WaveCountdown wave_countdown(bool ready,bool goal,std::uint32_t mission,bool no_production,
    std::uint32_t second,std::uint32_t next_wave_second,bool has_pending,std::uint32_t pending_second,
    const WaveState& t01,std::uint8_t interval_stacks) noexcept {
    if(!ready || goal)return {};
    std::uint32_t remaining=0xffffffffu;
    bool awaiting_home=false;
    if(mission==101){
        if(t01.pending)remaining=(wave_config::kWarningTicks-std::min(t01.warning_ticks,wave_config::kWarningTicks)+23u)/24u;
        else if(t01.active){
            const auto interval=wave_progression::interval_seconds(false,interval_stacks)*24u;
            remaining=(interval-std::min(t01.interval_ticks,interval)+wave_config::kWarningTicks+23u)/24u;
        }else if(t01.home_seen){
            const auto grace=(wave_config::kHomeGraceTicks-std::min(t01.home_ticks,wave_config::kHomeGraceTicks)+23u)/24u;
            const auto first=std::max(wave_config::kFirstElapsedSeconds,wave_progression::first_elapsed_seconds(false));
            const auto start=first>second ? first-second : 0u;
            remaining=std::max(start,grace)+(wave_config::kWarningTicks+23u)/24u;
        }else awaiting_home=true;
    }else{
        const auto due=next_wave_second ? next_wave_second : wave_progression::first_elapsed_seconds(no_production);
        remaining=(due>second ? due-second : 0u)+4u;
    }
    if(has_pending)remaining=std::min(remaining,pending_second>second ? pending_second-second : 0u);
    if(remaining!=0xffffffffu)return {WaveCountdown::Kind::Scheduled,remaining};
    return {awaiting_home ? WaveCountdown::Kind::WaitingForHome : WaveCountdown::Kind::Hidden,0};
}
inline std::string wave_countdown_text(const WaveCountdown& value){
    if(value.kind==WaveCountdown::Kind::Hidden)return {};
    if(value.kind==WaveCountdown::Kind::WaitingForHome)return "공세 대기 · 기지 도착 후";
    const auto seconds=std::min(value.seconds,99u*60u+59u);char time[16]{};
    std::snprintf(time,sizeof(time),"%02u:%02u",seconds/60u,seconds%60u);
    return std::string("공세 출발 ")+time;
}
}
