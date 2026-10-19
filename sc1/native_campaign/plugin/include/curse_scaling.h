#pragma once
#include <algorithm>
#include <cstdint>
namespace sc1_native { namespace curse_scaling {
using U32=std::uint32_t;
// Shared by wire decoding and native application: the tail contains curse
// counters rather than manual talent ranks. Validate both entry points alike.
template<U32 RankCount,class Snapshot> inline bool valid_rank_storage(const Snapshot& s) noexcept {
 static_assert(RankCount<=29,"Extended curse counters overlap manual ranks");
 if(s.wire_version==1){for(U32 i=0;i<32;++i)if(s.talent_ranks[i])return false;return true;}
 if(s.wire_version!=2)return false;
 for(U32 i=RankCount;i<29;++i)if(s.talent_ranks[i])return false;
 for(U32 slot=16;slot<=18;++slot){
  const auto extended=s.talent_ranks[47-slot];
  if(extended && U32(s.curse_counts[slot])!=std::min(extended,255u))return false;
 }
 return true;
}
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
