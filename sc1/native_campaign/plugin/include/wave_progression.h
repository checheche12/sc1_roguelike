#pragma once
// Deterministic additional-wave policy. All budgets/costs use StarCraft's
// half-supply units; no DAT stats, upgrades, mission triggers or RNG are changed.
#include <array>
#include <algorithm>
#include <cstdint>
namespace sc1_native { namespace wave_progression {
using U32=std::uint32_t;using UnitId=std::uint16_t;
// Matches CHK/SAMASE race identifiers used by campaign_waves.generated.h.
enum Race:U32 { Zerg=0,Terran=1,Protoss=2 };
inline constexpr U32 first_elapsed_seconds(bool no_production) noexcept {return no_production?360u:300u;}
inline constexpr U32 tier(U32 elapsed_seconds) noexcept {return elapsed_seconds<600?0u:elapsed_seconds<900?1u:2u;}
inline constexpr U32 live_supply_cap(bool no_production) noexcept {return no_production?24u:480u;}
inline constexpr U32 base_budget(bool no_production,U32 wave_ordinal) noexcept {return no_production?8u:16u+4u*std::min(wave_ordinal,12u);}
inline U32 budget(bool no_production,U32 wave_ordinal,U32 reinforcement_stacks) noexcept {
    const auto amount=std::uint64_t(base_budget(no_production,wave_ordinal))*(4ull+reinforcement_stacks)/4u;
    return static_cast<U32>(std::min<std::uint64_t>(amount,live_supply_cap(no_production)));
}
inline constexpr U32 interval_seconds(bool no_production,U32 interval_stacks) noexcept {
    return static_cast<U32>(std::max<std::uint64_t>(45,(no_production?1800ull:1200ull)/(10ull+interval_stacks)));
}
inline constexpr bool air_only_unit(UnitId id) noexcept {return id==8 || id==12 || id==58 || id==43 || id==44 || id==62 || id==70 || id==71 || id==60 || id==72;}
inline constexpr bool anti_air_only(UnitId id) noexcept {return id==58 || id==62 || id==60;}
inline constexpr U32 standard_supply(UnitId id) noexcept {
    switch(id){case 37:return 1;case 0:case 32:case 38:return 2;
    case 2:case 3:case 5:case 8:case 43:case 44:case 62:case 65:case 66:case 60:return 4;
    case 58:case 70:return 6;case 39:case 68:case 71:return 8;case 12:return 12;default:return 0;}
}
inline constexpr bool permitted(UnitId id) noexcept {return standard_supply(id)!=0;}
inline constexpr std::array<UnitId,20> kUnits={0,32,2,3,5,8,12,58,37,38,39,43,44,62,65,66,68,70,71,60};
using Pool=std::array<UnitId,12>;using Variants=std::array<Pool,4>;
// Basic -> mixed ground -> air/heavy. Different variants change both ordering
// and proportions. Zerg's basic tier intentionally has only its two ordinary
// ground attackers; later tiers add combat-ready units without burrow/ammo.
inline constexpr Variants kGround[3][3]={
 { // Zerg
  {{{37,37,38,37,37,37,38,37,37,38,37,37},{37,38,37,38,37,37,38,37,38,37,37,37},{38,37,37,37,38,37,37,38,37,37,37,37},{37,37,37,37,38,38,37,37,37,38,37,37}}},
  {{{38,37,38,37,39,37,38,37,38,37,37,38},{37,38,38,37,38,39,37,38,37,38,37,37},{38,38,37,38,37,37,39,38,37,37,38,37},{37,39,38,37,38,37,37,38,38,37,38,37}}},
  {{{43,38,37,39,38,44,37,43,62,38,37,39},{38,39,43,37,38,43,44,37,62,38,39,37},{39,38,37,43,44,38,37,62,43,38,37,38},{44,37,38,43,39,38,62,37,43,38,39,37}}}
 },
 { // Terran
  {{{0,0,32,0,2,0,0,32,0,0,2,0},{0,32,0,2,0,32,0,0,2,0,0,0},{2,0,0,0,32,0,2,0,0,32,0,0},{32,0,0,2,0,0,32,0,2,0,0,0}}},
  {{{3,0,2,32,5,0,3,0,2,0,32,3},{0,5,3,0,32,2,0,3,5,0,2,0},{2,3,0,5,0,32,3,2,0,3,0,32},{32,0,3,2,5,0,3,0,2,32,0,5}}},
  {{{8,3,0,5,12,0,58,3,8,5,0,32},{3,12,0,8,5,3,0,58,8,0,5,2},{5,0,8,3,58,12,0,3,5,8,0,32},{12,0,3,8,5,58,0,3,8,32,0,5}}}
 },
 { // Protoss
  {{{65,65,66,65,65,66,65,65,65,66,65,66},{66,65,66,65,65,65,66,65,66,65,65,65},{65,66,65,65,66,65,66,65,65,65,66,65},{65,65,65,66,65,66,65,66,65,65,66,65}}},
  {{{66,65,68,65,66,65,66,68,65,66,65,65},{65,68,66,65,66,66,65,68,65,66,65,66},{68,65,66,65,65,66,68,66,65,65,66,65},{66,66,65,68,65,66,65,65,68,66,65,66}}},
  {{{70,66,65,68,71,65,60,66,70,68,65,66},{68,65,70,66,60,71,65,68,66,70,65,66},{66,70,65,71,68,60,65,66,70,68,65,66},{71,65,66,70,68,65,60,66,70,65,68,66}}}
 }
};
inline constexpr Pool kAir[3][3]={
 { {{43,43,43,43,43,43,43,43,43,43,43,43}},{{43,43,62,43,43,43,62,43,43,43,43,43}},{{43,44,43,62,43,44,43,43,62,43,44,43}} },
 { {{8,8,8,8,8,8,8,8,8,8,8,8}},{{8,8,58,8,8,8,58,8,8,8,8,8}},{{8,12,8,58,8,12,8,8,58,8,12,8}} },
 { {{70,70,70,70,70,70,70,70,70,70,70,70}},{{70,70,60,70,70,70,60,70,70,70,70,70}},{{70,71,70,60,70,71,70,70,60,70,71,70}} }
};
using SupplyLookup=U32(*)(UnitId);
struct Selection{UnitId unit_id=0;U32 supply=0;bool valid=false;};
inline Selection select(U32 race,bool air_only,U32 elapsed_seconds,U32 wave_ordinal,U32 successful_unit_ordinal,
    U32 remaining_half_supply,SupplyLookup lookup=nullptr) noexcept {
    if(race>Protoss || !remaining_half_supply)return {};
    const auto& pool=air_only?kAir[race][tier(elapsed_seconds)]:kGround[race][tier(elapsed_seconds)][wave_ordinal%4];
    const auto offset=(successful_unit_ordinal+wave_ordinal/4)%pool.size();
    for(std::size_t step=0;step<pool.size();step++){
        const auto id=pool[(offset+step)%pool.size()];
        // The first successful unit must hit ground. Pure air-to-air units can
        // join only after that unit exists; failed spawns do not advance this.
        if(!successful_unit_ordinal && anti_air_only(id))continue;
        const auto supply=lookup?lookup(id):standard_supply(id);
        if(supply && supply<=remaining_half_supply)return {id,supply,true};
    }
    return {};
}
} } // namespace sc1_native::wave_progression
