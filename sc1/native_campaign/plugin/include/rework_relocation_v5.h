#pragma once
// Exact 13515 native MoveUnit and Recall placement helpers. The signatures and
// call arguments are witnessed by OrderNukeLaunch and the stock Recall helper.
// This changes the native unit/search/collision state, never only its sprite.
namespace rework_relocation {
using Move=void (__cdecl*)(bw::Unit*,U32,U32);
using Place=U32 (__cdecl*)(bw::Unit*,const bw::Point*,bw::Point*,const void*,U32,U32);
inline Move native_move=nullptr;
inline Place native_place=nullptr;
struct SplitRegion {std::uint16_t flags,region_false,region_true;};
struct Region {std::uint16_t walkability,group,tile_count;U8 ground_neighbours,all_neighbours;void* temporary;std::uint16_t* neighbour_ids;U32 center[2];std::int16_t area[4];U8 priority,ignored_neighbours,padding[30];};
struct Pathing {std::uint16_t count,padding;void* ids;void* unknown_split;std::uint16_t tiles[256*256];SplitRegion split[25000];Region regions[5000];};
static_assert(sizeof(SplitRegion)==6 && sizeof(Region)==72 && offsetof(Pathing,tiles)==24 && offsetof(Pathing,regions)==281096,"Pinned public x64 Pathing layout");
using GetPathing=Pathing* (__cdecl*)();
inline GetPathing pathing_source=nullptr;
inline bool region_id(const Pathing* path,const bw::Point& point,U32& result) noexcept {
    if(!path || point.x<0 || point.y<0 || point.x>=8192 || point.y>=8192)return false;
    result=path->tiles[(U32(point.y)/32)*256+U32(point.x)/32];
    if(result>=0x2000){const U32 split=result-0x2000;if(split>=25000)return false;const auto& s=path->split[split];const U32 mini=(U32(point.x)&31)/8+((U32(point.y)&31)/8)*4;result=(s.flags&(1u<<mini)) ? s.region_true:s.region_false;}
    return result<path->count && result<5000;
}
inline bool connected(const bw::Point& from,const bw::Point& to) noexcept {
    auto path=pathing_source ? pathing_source():nullptr;U32 a=0,b=0;
    return region_id(path,from,a) && region_id(path,to,b) && path->regions[a].group==path->regions[b].group;
}
inline constexpr U8 move_bytes[]={0x48,0x89,0x5c,0x24,0x08,0x48,0x89,0x6c,0x24,0x10,0x48,0x89,0x74,0x24,0x18,0x57,0x41,0x56,0x41,0x57,0x48,0x83,0xec,0x20};
inline constexpr U8 place_bytes[]={0x4c,0x8b,0xdc,0x56,0x41,0x54,0x41,0x55,0x41,0x56,0x48,0x83,0xec,0x68,0x49,0x8b,0xf1,0x4d,0x8b,0xe8,0x4c,0x8b,0xf2,0x4c,0x8b,0xe1};
inline constexpr U8 recall_placement[]={0xe8,0x82,0x39,0x01,0x00,0x33,0xdb,0x4c,0x8d,0x44,0x24,0x60,0x89,0x5c,0x24,0x28,0x48,0x8d,0x54,0x24,0x68,0x45,0x33,0xc9,0x89,0x5c,0x24,0x20,0x48,0x8b,0xcf,0xe8,0x63,0x94,0x1d,0x00};
inline constexpr U8 nuke_move[]={0x44,0x0f,0xb7,0xc1,0x48,0x8b,0xcb,0xe8,0x1c,0x6d,0x00,0x00};
inline bool bind() noexcept {
    if(!native_engine_hooks::verify_image())return false;
    auto base=native_engine_hooks::verified_base;
    const native_engine_hooks::Bytes witnesses[]={
        {0x1e6df0,move_bytes,sizeof(move_bytes)}, {0x3ac8f0,place_bytes,sizeof(place_bytes)},
        {0x1d3469,recall_placement,sizeof(recall_placement)}, {0x1e00c8,nuke_move,sizeof(nuke_move)}
    };
    for(const auto& w:witnesses)if(!native_engine_hooks::match(base+w.rva,w.expected,w.length))return false;
    native_move=reinterpret_cast<Move>(base+0x1e6df0);
    native_place=reinterpret_cast<Place>(base+0x3ac8f0);
    // The already registered owner-scoped issue_order callback performs the
    // native stop/order transition; no additional unverified function is used.
    return true;
}
inline bool move(bw::Unit* u,int x,int y,unsigned max_adjust_pixels,bool require_ground_connection=true) noexcept {
    if(!native_move || !native_place || !g.active || !g.applied || !valid_unit(u) ||
       !u->flingy.sprite || !u->order || u->flingy.hitpoints<=0 || (u->flags&(0x20u|0x40u|0x8000000u)) || u->stasis_timer)return false;
    auto game=g.game ? g.game():nullptr;
    if(!game || x<0 || y<0 || x>=int(game->map_width_tiles)*32 || y>=int(game->map_height_tiles)*32)return false;
    const bw::Point previous=u->flingy.position;
    const bw::Point desired{static_cast<std::int16_t>(x),static_cast<std::int16_t>(y)};
    if(require_ground_connection && !(u->flags&4u) && !connected(previous,desired))return false;
    bw::Point placed{};
    OwnerDatScope scope(u->player,u->player,u);
    native_move(u,U32(x),U32(y));
    const bool found=native_place(u,&desired,&placed,nullptr,0,0)!=0;
    const auto dx=std::int64_t(placed.x)-x,dy=std::int64_t(placed.y)-y;
    const bool allowed=found && placed.x>=0 && placed.y>=0 && placed.x<int(game->map_width_tiles)*32 &&
        placed.y<int(game->map_height_tiles)*32 && dx*dx+dy*dy<=std::int64_t(max_adjust_pixels)*max_adjust_pixels;
    if(!allowed || (require_ground_connection && !(u->flags&4u) && !connected(previous,placed))){native_move(u,U32(previous.x),U32(previous.y));return false;}
    if(g.order)g.order(u,1,U32(previous.x),U32(previous.y),nullptr,228);
    native_move(u,U32(placed.x),U32(placed.y));
    return true;
}
}
