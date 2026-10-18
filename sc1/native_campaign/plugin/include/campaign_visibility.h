#pragma once
#include "campaign_visibility.generated.h"
namespace campaign_visibility {
struct Fow {Fow* prev;Fow* next;std::uint16_t unit_id,padding[3];bw::SpriteScr* sprite;};
static_assert(offsetof(Fow,sprite)==0x18 && sizeof(Fow)==0x20,"Native FOW node64");
using First=Fow* (__cdecl*)();
using Create=Fow* (__cdecl*)(U32,std::uint16_t,bw::SpriteScr*);
inline First first=nullptr;inline Create create=nullptr;
struct Seen {U32 generation=0,type=0,owner=12;bool revealed=false;};
inline std::vector<Seen> seen;inline bw::Unit* base_units=nullptr;
inline U32 active_mission=0,active_owner=12;
inline void reset() noexcept {seen.clear();base_units=nullptr;active_mission=0;active_owner=12;}
inline bool enabled(U32 mission) noexcept {return std::find(std::begin(missions),std::end(missions),mission)!=std::end(missions);}
inline bool bind_api(const samase::PluginApi* api) noexcept {
 if(!api || !api->first_fow_sprite)return false;
 first=reinterpret_cast<First>(reinterpret_cast<GenericFn (__cdecl*)()>(api->first_fow_sprite)());return first!=nullptr;
}
inline constexpr U8 create_bytes[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x48,0x83,0xec,0x20};
inline constexpr U8 create_call[]={0xe8,0xe0,0xc6,0xfb,0xff};
inline bool native_bytes(U8* base) noexcept {return base && native_engine_hooks::match(base+0x19fa10,create_bytes,sizeof(create_bytes)) && native_engine_hooks::match(base+0x1e332b,create_call,sizeof(create_call));}
inline bool bind_native() noexcept {
 if(!native_engine_hooks::verify_image() || !native_bytes(native_engine_hooks::verified_base))return false;
 create=reinterpret_cast<Create>(native_engine_hooks::verified_base+0x19fa10);return true;
}
inline bool duplicate(const bw::Unit* u,U32 mask) noexcept {
 if(!first || !rework_combat_v5::get_sprite_position)return false;
 std::uint16_t point[2]{};rework_combat_v5::get_sprite_position(u->flingy.sprite,point);
 U32 limit=0;for(auto f=first();f && limit++<65536;f=f->next){
  if(f->unit_id!=u->unit_id || !f->sprite || !(f->sprite->visibility_mask&mask))continue;
  std::uint16_t other[2]{};rework_combat_v5::get_sprite_position(f->sprite,other);
  if(point[0]==other[0] && point[1]==other[1])return true;
 }return false;
}
inline void buildings(U32 owner) {
 if(!create || !first || !g.units || !g.units_count || g.units_count>65536)return;
 if(base_units!=g.units || seen.size()!=g.units_count || active_mission!=g.mission->mission_id || active_owner!=owner){
  reset();seen.resize(g.units_count);base_units=g.units;active_mission=g.mission->mission_id;active_owner=owner;
 }
 const U32 mask=1u<<owner;
 living_units([&](bw::Unit* u){
  if(!valid_unit(u) || u->unit_id>=228 || hallucination(u) || !u->flingy.sprite)return;
  const bool resource=(u->unit_id>=176 && u->unit_id<=178) || u->unit_id==188 || u->unit_id==110 || u->unit_id==149 || u->unit_id==157;
  if(!resource && !(is_enemy(u->player) && rework_combat_v5::building(u)))return;
  auto& s=seen[std::size_t(u-g.units)];
  if(s.generation!=u->minor_unique_index || s.type!=u->unit_id || s.owner!=u->player)s={u->minor_unique_index,u->unit_id,u->player,false};
  if(s.revealed)return;
  auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);
  // Native sight creates its own last-known snapshot when sight leaves.
  if((sprite->visibility_mask&mask) || duplicate(u,mask)){s.revealed=true;return;}
  if(auto f=create(U32(u-g.units)+1,u->unit_id,sprite))if(f->sprite){f->sprite->visibility_mask=U8(mask);s.revealed=true;}
 });
}
inline void step() noexcept {
 if(!g.active||!g.mission||!enabled(g.mission->mission_id)||!g.game||!rework_combat_v5::get_tiles)return;
 auto game=g.game();const U32 owner=player_owner();
 if(!game||owner>=8||game->map_width_tiles!=g.mission->width||game->map_height_tiles!=g.mission->height||!game->map_width_tiles||game->map_width_tiles>256||!game->map_height_tiles||game->map_height_tiles>256)return;
 auto tiles=rework_combat_v5::get_tiles();if(!tiles)return;
 // Explore terrain while preserving every native current-sight bit.
 const U32 mask=~(1u<<(owner+8)),count=game->map_width_tiles*game->map_height_tiles;
 for(U32 i=0;i<count;i++)tiles[i]&=mask;
 try{buildings(owner);}catch(...){}
}
}
