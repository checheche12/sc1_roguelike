#pragma once
#include "campaign_visibility.generated.h"
namespace campaign_visibility {
inline bool enabled(U32 mission) noexcept {
    return std::find(std::begin(missions),std::end(missions),mission)!=std::end(missions);
}
inline void step() noexcept {
    if(!g.active||!g.mission||!enabled(g.mission->mission_id)||!g.game||!rework_combat_v5::get_tiles)return;
    auto game=g.game();const U32 owner=player_owner();
    if(!game||owner>=8||game->map_width_tiles!=g.mission->width||game->map_height_tiles!=g.mission->height||!game->map_width_tiles||game->map_width_tiles>256||!game->map_height_tiles||game->map_height_tiles>256)return;
    auto tiles=rework_combat_v5::get_tiles();if(!tiles)return;
    // Public active-tile layout: low byte = hidden players, next = unexplored
    // players; terrain/pathing/creep occupy the upper half. Explore terrain for
    // the human only. Keep current visibility native so areas outside allied
    // sight remain under fog, including after each periodic visibility refresh.
    const U32 mask=~(1u<<(owner+8));
    const U32 count=game->map_width_tiles*game->map_height_tiles;
    for(U32 i=0;i<count;i++)tiles[i]&=mask;
}
}
