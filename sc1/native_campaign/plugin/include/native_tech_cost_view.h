#pragma once
// The native engine also reads its original U16 energy array directly.
// SAMASE's extended techdata view alone does not cover those reads. Scope the
// witnessed original cell with the same owner lifetime as extended DAT edits.
namespace native_tech_cost_view {
inline std::uint16_t* yamato=nullptr;
inline constexpr U32 energy_array=0xe58520;
inline bool bind(U8* image) noexcept {
 if(!image)return false;yamato=reinterpret_cast<std::uint16_t*>(image+energy_array+8*2);return true;
}
inline bool verify_after_dat() noexcept {std::uint16_t value=0;if(!yamato)return false;std::memcpy(&value,yamato,2);return value==150;}
struct Scope {
 std::uint16_t* cell=nullptr;std::uint16_t previous=0;
 void begin(U32 owner) noexcept {
  if(!yamato||!(g.growth.talent_bits[302/32]&(1u<<(302%32))))return;
  std::memcpy(&previous,yamato,2);if(previous!=150&&previous!=50)return;
  cell=yamato;const std::uint16_t value=owner==player_owner()?50u:150u;std::memcpy(cell,&value,2);
 }
 ~Scope() noexcept {if(cell)std::memcpy(cell,&previous,2);}
};
}
