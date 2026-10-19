#pragma once
#include <algorithm>
#include <cstdint>
namespace sc1_native { namespace curse_scaling {
using U32=std::uint32_t;
// Snapshot tail rank slots29..31 are reserved for QA26 curse counters.
// The original byte remains saturated so pre-QA26 snapshots remain readable.
template<class Snapshot> inline U32 count(const Snapshot& s,U32 slot) noexcept {
 if(slot>=64)return 0;
 return s.wire_version==2 && slot>=16 && slot<=18
  ?std::max(U32(s.curse_counts[slot]),s.talent_ranks[47-slot]):U32(s.curse_counts[slot]);
}
inline constexpr U32 bonus(U32 stacks,U32 first,U32 step=5) noexcept {
 if(!stacks)return 0;
 if(stacks>40000)return 0xffffffffu;
 return U32(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(stacks)*(2ull*first+std::uint64_t(stacks-1)*step)/2));
}
inline U32 scale(U32 amount,U32 percent) noexcept {
 const auto factor=100ull+percent;
 if(amount>0xffffffffull*100/factor)return 0xffffffffu;
 return U32(std::uint64_t(amount)*factor/100);
}
} }
