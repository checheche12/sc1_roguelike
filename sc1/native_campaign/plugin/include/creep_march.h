#pragma once
// Inside rework_combat_v5. API44 PlaceCreepRect takes tile x/y/w/h/round.
// Tile flags occupy the high 16 bits of map_tile_flags (public BW tile layout).
namespace creep_march {
using Place=void (__cdecl*)(U32,U32,U32,U32,U32);
inline Place place=nullptr;
inline U32 last_tick=~0u,expansions=0,placed_tiles=0;
inline constexpr U32 interval=72; // Three game seconds per frontier layer.
inline bool has_creep(U32 tile) noexcept {return (tile&0x40400000u)!=0;}
inline bool boosted(const bw::Unit* u) noexcept {
 if(!rank(75)||!own(u)||air(u)||!soldier(u->unit_id)||!race_type(u->unit_id,1)||!get_tiles||!g.game)return false;
 auto game=g.game();auto tiles=get_tiles();const auto x=U32(u->flingy.position.x)/32,y=U32(u->flingy.position.y)/32;
 return game&&tiles&&x<game->map_width_tiles&&y<game->map_height_tiles&&has_creep(tiles[y*game->map_width_tiles+x]);
}
inline bool legal(const U32* tiles,U32 x,U32 y,U32 width,U32 height) noexcept {
 if(!tiles||x>=width||y>=height)return false;
 const U32 flags=tiles[y*width+x]>>16;
 // Match native terrain restrictions, and leave occupied non-creep tiles alone.
 if(flags&(0x80u|0x2000u|0x800u))return false;
 return y+1==height || !(tiles[(y+1)*width+x]&0x00800000u);
}
inline void reset() noexcept {last_tick=~0u;expansions=placed_tiles=0;}
inline void step(){
 if(!rank(75)||!place||!get_tiles||!g.game)return;
 const U32 frame=now();if(last_tick==~0u){last_tick=frame;return;}if(frame-last_tick<interval)return;last_tick=frame;
 auto game=g.game();auto tiles=get_tiles();if(!game||!tiles)return;
 const U32 width=game->map_width_tiles,height=game->map_height_tiles;
 if(!width||!height||width>256||height>256)return;
 std::vector<U8> seen(std::size_t(width)*height,0);std::vector<U32> connected,frontier;
 living_units([&](bw::Unit* u){
  if(!own(u)||!(u->flags&1u)||!in(u->unit_id,{131,132,133,143,144,146}))return;
  const U32 x=U32(u->flingy.position.x)/32,y=U32(u->flingy.position.y)/32;
  if(x>=width||y>=height)return;const U32 cell=y*width+x;
  if(!seen[cell]&&has_creep(tiles[cell])){seen[cell]=1;connected.push_back(cell);}
 });
 // Discover the old connected region first. Newly placed cells cannot spread
 // again in this tick, so expansion stays gradual instead of filling the map.
 for(std::size_t cursor=0;cursor<connected.size();++cursor){const U32 cell=connected[cursor];const int x=int(cell%width),y=int(cell/width);
  for(int dy=-1;dy<=1;++dy)for(int dx=-1;dx<=1;++dx){
   const int nx=x+dx,ny=y+dy;if((!dx&&!dy)||nx<0||ny<0||nx>=int(width)||ny>=int(height))continue;
   const U32 next=U32(ny)*width+U32(nx);if(seen[next])continue;seen[next]=1;
   if(has_creep(tiles[next]))connected.push_back(next);
   else if(legal(tiles,U32(nx),U32(ny),width,height))frontier.push_back(next);
  }
 }
 if(frontier.empty())return;
 U32 added=0;for(U32 cell:frontier){place(cell%width,cell/width,1,1,0);if(has_creep(tiles[cell]))++added;}
 if(added){++expansions;placed_tiles+=added;}
}
}
