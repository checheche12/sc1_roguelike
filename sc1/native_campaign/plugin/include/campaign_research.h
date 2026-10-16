#pragma once
// The13515 native completion setters skip BW research/upgrade writes when
// Game::is_bw is zero. Original campaign maps retain that mode even though
// their Dat+ requirements deliberately permit BW units. Preserve the native
// completion path (including cancel/disabled/timer checks), exposing BW mode
// only while a real expansion research order is being processed.
namespace campaign_research {
struct Scope {
    bw::Game* game=nullptr;
    Scope(const Scope&)=delete;Scope& operator=(const Scope&)=delete;
    explicit Scope(const bw::Unit* unit) noexcept {
        if(!g.active || !g.mission || !valid_unit(unit) || hallucination(unit) ||
           !(unit->flags&1u) || unit->flingy.hitpoints<=0)return;
        const bool tech=unit->order==75 && unit->unit_specific.bytes[12]>=24 && unit->unit_specific.bytes[12]<44;
        const bool upgrade=unit->order==76 && unit->unit_specific.bytes[13]>=46 && unit->unit_specific.bytes[13]<61;
        if(!tech && !upgrade)return;
        auto current=g.game?g.game():nullptr;
        if(current && !current->is_bw){game=current;game->is_bw=1;}
    }
    ~Scope(){if(game)game->is_bw=0;}
};
}
