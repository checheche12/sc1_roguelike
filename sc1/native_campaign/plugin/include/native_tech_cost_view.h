#pragma once
// The native engine also reads its original U16 energy array directly.
// SAMASE's extended techdata view alone does not cover those reads. Scope the
// witnessed original cell with the same owner lifetime as extended DAT edits.
namespace native_tech_cost_view {
inline std::uint16_t* yamato=nullptr;
inline U8* image=nullptr;
inline const char* last_error="not_bound";
inline constexpr U32 energy_array=0xe58520;
inline constexpr U32 sites[]={0x3ee0ee,0x3ee149,0x3ee161};
inline constexpr U8 prefixes[][5]={{0x45,0x0f,0xb7,0x8c,0x40},{0x41,0x0f,0xb7,0x8c,0x50},{0x41,0x0f,0xb7,0x84,0x50}};
inline bool read_exact(const void* address,void* output,std::size_t size) noexcept {
 SIZE_T got=0;return ReadProcessMemory(GetCurrentProcess(),address,output,size,&got)!=0 && got==size;
}
inline std::uint16_t* resolve() noexcept {
 // SAMASE relocates extended DAT arrays and rewrites these three operands.
 // The original executable array is then cleared; it is not a live witness.
 if(!image){last_error="not_bound";return nullptr;}
 std::uintptr_t array=0;
 for(U32 i=0;i<3;i++){
  U8 instruction[9]{};
  if(!read_exact(image+sites[i],instruction,sizeof(instruction)) ||
     std::memcmp(instruction,prefixes[i],5)){last_error="energy_instruction_changed";return nullptr;}
  std::int32_t displacement=0;std::memcpy(&displacement,instruction+5,4);
  const auto current=reinterpret_cast<std::uintptr_t>(image)+std::intptr_t(displacement);
  if(i && current!=array){last_error="energy_references_disagree";return nullptr;}
  array=current;
 }
 return reinterpret_cast<std::uint16_t*>(array+8*2);
}
inline bool bind(U8* base) noexcept {
 if(!base)return false;image=base;yamato=resolve();return yamato!=nullptr;
}
inline bool verify_after_dat() noexcept {
 auto current=resolve();std::uint16_t value=0;
 if(!current)return false;
 if(!read_exact(current,&value,2)){last_error="energy_array_unreadable";return false;}
 if(value!=150){last_error="energy_baseline_changed";return false;}
 yamato=current;last_error="verified";return true;
}
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
