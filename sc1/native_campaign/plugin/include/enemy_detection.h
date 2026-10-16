#pragma once
// Respond to witnessed damage from a concealed attacker. Never reveal the map
// or change detection bits: a real detector must travel from a safe enemy base.
namespace enemy_detection {
struct Contact {bool active=false;int x=0,y=0;U32 frame=0,next=0,wave=0;rework_combat_v5::Identity escort{};};
inline std::array<Contact,8> contacts{};inline U32 last=~0u;
inline void reset() noexcept {contacts={};last=~0u;}
inline void note(bw::Unit* victim,bw::Unit* source) noexcept {
    if(!g.active||!g.applied||!g.mission||g.mission->no_production||!valid_unit(victim)||!valid_unit(source)||victim->player>=8||!is_enemy(victim->player)||source->player!=player_owner()||hallucination(source)||!(source->flags&(0x10u|0x300u)))return;
    auto game=g.game?g.game():nullptr;if(!game)return;
    auto& c=contacts[victim->player];c.active=true;c.x=source->flingy.position.x;c.y=source->flingy.position.y;c.frame=game->frame_count;
    if(auto t=existing_track(victim))if(t->spawned)c.wave=t->wave_id;
}
inline void step(bool ready,bool blocked,bool goal){
    auto game=g.game?g.game():nullptr;if(!ready||blocked||goal||!g.active||!g.applied||!g.mission||!game)return;
    const U32 frame=game->frame_count;if(last!=~0u&&frame-last<24)return;last=frame;
    for(U32 owner=0;owner<8;owner++){auto& c=contacts[owner];if(!c.active||!is_enemy(owner))continue;
        if(frame-c.frame>30u*24u){c.active=false;continue;}
        auto detector=rework_combat_v5::resolve(c.escort);
        if(!detector&&frame>=c.next){
            bool covered=false;living_units([&](bw::Unit* u){if(u->player==owner&&(u->flags&1u)&&u->flingy.hitpoints>0&&!u->is_blind&&(original_stat({0,22,u->unit_id})&0x8000u)&&wave_targeting::distance(u->flingy.position.x,u->flingy.position.y,c.x,c.y)<=224ll*224)covered=true;});
            if(covered)continue;
            const sc1_native::campaign_wave_config::Origin* origin=nullptr;
            for(const auto& candidate:sc1_native::campaign_wave_config::kOrigins)if(candidate.mission_id==g.mission->mission_id&&candidate.owner==owner&&origin_safe(candidate)){origin=&candidate;break;}
            c.next=frame+10u*24u;if(!origin)continue;
            const U32 previous_wave=g.current_wave_id;g.current_wave_id=c.wave?c.wave:++g.next_wave_id;
            detector=rework_waves::create(sc1_native::rework_wave::detector(origin->race),0,100,100,false,owner);
            g.current_wave_id=previous_wave;
            if(detector)c.escort=rework_combat_v5::identity(detector);
        }
        if(!detector||rework_curses::appearing(detector)||!g.order||detector->lockdown_timer||detector->stasis_timer||detector->maelstrom_timer)continue;
        if(auto t=existing_track(detector)){t->wave_ordered=true;t->wave_order_frame=frame;}
        // A position move makes unarmed Overlords/Observers reach the actual
        // contact instead of waiting for an attack target they cannot acquire.
        if(wave_targeting::distance(detector->flingy.position.x,detector->flingy.position.y,c.x,c.y)>96ll*96)
            g.order(detector,6,U32(c.x),U32(c.y),nullptr,228);
    }
}
}
