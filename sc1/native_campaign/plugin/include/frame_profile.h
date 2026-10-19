#pragma once
// Eight timings per simulation frame, one aggregate log every240 active frames.
// The wall interval includes engine work outside this plugin's frame callback.
namespace frame_profile {
inline LARGE_INTEGER frequency{};inline LONGLONG start=0,last=0,previous=0;
inline std::array<double,7> totals{};inline double maximum=0,wall=0;inline U32 frames=0;
inline void reset() noexcept {totals.fill(0);start=last=previous=0;maximum=wall=0;frames=0;}
inline void begin() noexcept {if(!frequency.QuadPart)QueryPerformanceFrequency(&frequency);LARGE_INTEGER t{};QueryPerformanceCounter(&t);start=last=t.QuadPart;}
inline double ms(LONGLONG ticks) noexcept {return double(ticks)*1000.0/double(frequency.QuadPart);}
inline void mark(U32 section) noexcept {LARGE_INTEGER t{};QueryPerformanceCounter(&t);if(section<totals.size())totals[section]+=ms(t.QuadPart-last);last=t.QuadPart;}
inline void finish(bool active,U32 frame,std::size_t capacity) noexcept {
 if(!active){reset();return;}
 maximum=std::max(maximum,ms(last-start));if(previous)wall+=ms(start-previous);previous=start;
 if(++frames<240)return;
 log_event("PERF runtime frame=%u frames=%u callback_avg_ms=%.3f callback_max_ms=%.3f wall_avg_ms=%.3f protocol_enemy_ms=%.3f motion_ms=%.3f hp_ms=%.3f combat_ms=%.3f economy_ui_ms=%.3f waves_ms=%.3f targeting_ms=%.3f unit_capacity=%zu",
  frame,frames,std::accumulate(totals.begin(),totals.end(),0.0)/frames,maximum,wall/(frames-1),totals[0]/frames,totals[1]/frames,totals[2]/frames,totals[3]/frames,totals[4]/frames,totals[5]/frames,totals[6]/frames,capacity);
 totals.fill(0);maximum=wall=0;frames=0;previous=0;
}
}
