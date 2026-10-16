#pragma once
// Only plugin-created wave identities receive orders. Coordinates are refreshed
// from current player units; original map/AI troops are never commandeered.
namespace wave_targeting {
struct Target {bool valid=false;int x=0,y=0;bw::Unit* base=nullptr;U8 unique=0;};
inline Target target{};
inline bool sampled=false;
inline U32 sample_frame=0;
inline void reset() noexcept {target={};sampled=false;sample_frame=0;}
inline bool headquarters(U32 id) noexcept {return id==106 || id==131 || id==132 || id==133 || id==154;}
inline bool worker(U32 id) noexcept {return id==7 || id==41 || id==64;}
inline bool usable(const bw::Unit* u) noexcept {
    return valid_unit(u) && u->flingy.hitpoints>0 && u->order!=0 && u->player==player_owner() &&
        !(u->flags&(0x40u|0x40000000u)) && u->unit_id<228 && g.mission &&
        u->flingy.position.x>=0 && u->flingy.position.y>=0 &&
        u->flingy.position.x<static_cast<int>(g.mission->width*32) && u->flingy.position.y<static_cast<int>(g.mission->height*32);
}
inline std::int64_t distance(int x,int y,int tx,int ty) noexcept {
    const auto dx=std::int64_t(x)-tx,dy=std::int64_t(y)-ty;return dx*dx+dy*dy;
}
inline void refresh(bool force=false) {
    const auto game=g.game ? g.game():nullptr;if(!g.active || !g.mission || !game){reset();return;}
    const U32 frame=game->frame_count;
    if(!force && sampled && frame-sample_frame<24)return;
    sampled=true;sample_frame=frame;
    std::vector<bw::Unit*> own;
    living_units([&](bw::Unit* u){if(usable(u))own.push_back(u);});
    bw::Unit* best=nullptr;U32 best_rank=0,best_score=0,current_rank=0,current_score=0;
    for(auto u:own){
        if(!headquarters(u->unit_id))continue;
        // A landed, complete economy is preferred to a lifted or unfinished
        // secondary headquarters. A lone flying CC is still followed.
        const U32 rank=((u->flags&4u) ? 0u:2u)+((u->flags&1u) ? 1u:0u);
        U32 score=0;const auto p=u->flingy.position;
        for(auto neighbor:own){if(neighbor==u)continue;const auto q=neighbor->flingy.position;
            if(distance(p.x,p.y,q.x,q.y)>512ll*512)continue;
            if(worker(neighbor->unit_id))score+=3;
            else if(original_stat({0,22,neighbor->unit_id})&1u)score+=4;
            else if(regular_combat_type(neighbor->unit_id))++score;
        }
        if(u==target.base && u->minor_unique_index==target.unique){current_rank=rank;current_score=score;}
        if(!best || rank>best_rank || (rank==best_rank && score>best_score)){
            best=u;best_rank=rank;best_score=score;
        }
    }
    // Stable selection for near-equal bases. A new developed base takes over
    // from an abandoned start; a captured/destroyed/recycled base never sticks.
    if(best && usable(target.base) && headquarters(target.base->unit_id) && target.base->minor_unique_index==target.unique &&
       current_rank==best_rank && current_score+3>=best_score)best=target.base;
    if(best){const auto p=best->flingy.position;target={true,p.x,p.y,best,best->minor_unique_index};return;}
    // Baseless scenarios follow an actual surviving army/hero position nearest
    // its center, never an empty map-start coordinate or a centroid in water.
    std::vector<bw::Unit*> army,workers,buildings;
    for(auto u:own){const auto flags=original_stat({0,22,u->unit_id});
        if(regular_combat_type(u->unit_id) || ((flags&0x40u) && u->unit_id<106))army.push_back(u);
        else if(worker(u->unit_id))workers.push_back(u);
        else if(flags&1u)buildings.push_back(u);
    }
    const auto& choices=!army.empty()?army:!workers.empty()?workers:buildings;
    if(choices.empty()){target={};return;}
    std::int64_t sum_x=0,sum_y=0;for(auto u:choices){sum_x+=u->flingy.position.x;sum_y+=u->flingy.position.y;}
    const int x=static_cast<int>(sum_x/static_cast<std::int64_t>(choices.size())),y=static_cast<int>(sum_y/static_cast<std::int64_t>(choices.size()));
    best=choices.front();auto nearest=distance(x,y,best->flingy.position.x,best->flingy.position.y);
    for(auto u:choices){const auto d=distance(x,y,u->flingy.position.x,u->flingy.position.y);if(d<nearest){best=u;nearest=d;}}
    const auto p=best->flingy.position;target={true,p.x,p.y,nullptr,0};
}
inline bool marked(const bw::Unit* u) noexcept {
    const auto t=existing_track(u);
    return t && t->spawned && t->wave_id!=0 && (regular_enemy(u) || rework_curses::marked(u)) && u->flingy.hitpoints>0 && u->order!=0;
}
inline bool engaged(const bw::Unit* u,U32 frame,const UnitTrack& t) noexcept {
    if(u->ground_cooldown || u->air_cooldown || (t.last_attack_frame && frame-t.last_attack_frame<48))return true;
    const auto victim=u->order_target.unit;
    if(multi_target::attack_order(u->order) && valid_unit(victim) && victim->flingy.hitpoints>0 && victim->order!=0 &&
       victim->player<8 && victim->player!=u->player && g.game()->alliances[u->player][victim->player]==0)return true;
    // The turret owns the weapon timer/target; the body owns the wave identity.
    const auto turret=u->subunit;
    return valid_unit(turret) && turret->subunit==u && turret->player==u->player &&
        (turret->ground_cooldown || turret->air_cooldown ||
         (valid_unit(turret->order_target.unit) && turret->order_target.unit->flingy.hitpoints>0 &&
          turret->order_target.unit->order!=0 && turret->order_target.unit->player<8 &&
          g.game()->alliances[u->player][turret->order_target.unit->player]==0));
}
inline bool reorderable(U32 order) noexcept {
    // BWAPI Order enum: ordinary idle/movement/attack orders only. Spell,
    // morph, siege transitions, boarding and burrow commands are left intact.
    return order==1 || order==2 || order==3 || order==6 || order==7 || order==13 || order==14 || order==23 ||
        order==107 || order==156 || order==157 || order==158 || order==159 || order==160 ||
        order==8 || order==9 || order==10 || order==11 || order==12 || order==21;
}
inline bool detector(const bw::Unit* u) noexcept {return valid_unit(u) && (u->unit_id==9 || u->unit_id==42 || u->unit_id==84);}
inline void issue(bw::Unit* u) {
    if(!g.order || !g.active || counter(kGoalCounter) || !marked(u) || rework_curses::appearing(u))return;
    refresh();if(!target.valid)return;
    auto raid=rework_curses::raid_target(u);int aim_x=raid?raid->flingy.position.x:target.x,aim_y=raid?raid->flingy.position.y:target.y;
    const auto game=g.game();const U32 frame=game->frame_count;auto t=existing_track(u);if(!t)return;
    const bool support=detector(u);
    if(support){
        // Follow a live member of this exact army. AttackMove sends unarmed
        // detectors ahead to the enemy base and leaves the cloaked wall intact.
        bw::Unit* leader=nullptr;std::int64_t best=std::numeric_limits<std::int64_t>::max();
        living_units([&](bw::Unit* other){auto tracked=existing_track(other);
            if(other==u || !marked(other) || detector(other) || other->player!=u->player || !tracked || tracked->wave_id!=t->wave_id)return;
            const auto p=other->flingy.position;const auto d=distance(p.x,p.y,aim_x,aim_y);
            if(!leader || d<best){leader=other;best=d;}
        });
        if(!leader)return;aim_x=leader->flingy.position.x;aim_y=leader->flingy.position.y;
    }
    const auto position=u->flingy.position;
    if(!t->wave_position_seen || distance(position.x,position.y,t->wave_position_x,t->wave_position_y)>=16ll*16){
        t->wave_position_seen=true;t->wave_position_x=position.x;t->wave_position_y=position.y;t->wave_position_frame=frame;
    }
    if((u->flags&0x40u) || u->lockdown_timer || u->stasis_timer || u->maelstrom_timer || !reorderable(u->order) || engaged(u,frame,*t))return;
    if(t->wave_ordered && frame-t->wave_order_frame<48)return;
    const bool moving=u->order==6 || u->order==14 || u->order==157 || u->order==158 || u->order==159;
    if(t->wave_ordered && moving && distance(u->order_target.x,u->order_target.y,aim_x,aim_y)<64ll*64 && frame-t->wave_position_frame<8u*24u)return;
    t->wave_ordered=true;t->wave_order_frame=frame;t->wave_position_frame=frame;
    g.order(u,support?6u:kAttackMove,static_cast<U32>(aim_x),static_cast<U32>(aim_y),nullptr,228);
}
inline void step(bool ready,bool goal) {
    if(!ready || goal || !g.active)return;
    const auto game=g.game ? g.game():nullptr;if(!game)return;
    // Simulation frames only; pause and modal UI pumps never advance this scan.
    if(sampled && game->frame_count-sample_frame<24)return;
    refresh();living_units([&](bw::Unit* u){if(marked(u))issue(u);});
}
}
