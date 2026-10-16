// Owner-scoped effects for frozen curse slots9..14. Included by native_plugin.cpp.
bool curse_regular(const bw::Unit* u) noexcept {
    return regular_enemy(u) && !(u->flags&0x44000000u) && u->unit_id!=47 && u->unit_id!=50;
}
void heal_enemy(bw::Unit* u,U32 amount) noexcept {
    if((!curse_regular(u) && !rework_curses::marked(u)) || u->flingy.hitpoints<=0 || !u->order || !amount)return;
    const auto hp=std::min<std::uint64_t>(effective_max_hp(u),std::uint64_t(u->flingy.hitpoints)+amount);
    OwnerDatScope scope(u->player,u->player,u);g.set_hp(u,static_cast<std::int32_t>(hp));
}
void ground_pulse(int x,int y,U32 player,U32 sprite=361) noexcept {
    if(g.lone_sprite && g.mission && player<12 && x>=0 && y>=0 && x<static_cast<int>(g.mission->width*32) && y<static_cast<int>(g.mission->height*32))g.lone_sprite(sprite,x,y,player);
}
void role_marker(bw::Unit* u,int x,int y,U32 image=377) noexcept {
    if(!g.add_overlay || !u || !u->flingy.sprite)return;
    auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);
    if(sprite->main_image)g.add_overlay(sprite->main_image,image,x,y,1);
}
U32 charged_attack(bw::Unit* u,U32 weapon) noexcept {
    auto body=effect_body(u);
    if(!curse_regular(body) || !ordinary_weapon(weapon))return 0;auto t=track_unit(body);if(!t)return 0;
    const auto frame=g.game()->frame_count;const auto stack=std::min(3u,U32(g.growth.curse_counts[9]));
    const bool primary=original_stat({0,17,u->unit_id})==weapon || original_stat({0,19,u->unit_id})==weapon;
    if(!primary)return 0;
    if(frame>=t->first_attack_end){
        t->first_attack_bonus=stack && frame-t->last_attack_frame>=192 && frame-t->last_damage_frame>=192 ? 10u+10u*stack : 0;
        const auto cooldown=original_stat({0,17,u->unit_id})==weapon ? u->ground_cooldown : u->air_cooldown;
        t->first_attack_end=frame+std::max(1u,U32(cooldown));
    }
    t->last_attack_frame=frame;
    return t->first_attack_bonus+(frame<t->command_until ? 25u : 0u);
}
void assign_wave_roles(bw::Unit* u,UnitTrack& t) {
    if(!curse_regular(u))return;
    t.medic=false;
    // Keep at least one ordinary member in small formations. Select an existing
    // unmarked member when a new member arrives; this never adds another unit.
    if(g.wave_spawn_number && g.wave_spawn_number<=std::min(3u,U32(g.growth.curse_counts[12])))
        for(std::size_t i=0;i<g.tracks.size();i++){auto& previous=g.tracks[i];
            if(&previous==&t || !previous.spawned || previous.wave_id!=t.wave_id || previous.medic || previous.owner!=t.owner)continue;
            previous.medic=true;role_marker(&g.units[i],-16,-24);break;
        }
    t.commander=g.growth.curse_counts[13] && !g.wave_spawn_number;
    if(t.medic)role_marker(u,-16,-24);if(t.commander)role_marker(u,16,-24,379);
    if(g.wave_spawn_number>=2u*std::min(3u,U32(g.growth.curse_counts[14])))return;
    for(std::size_t i=0;i<g.tracks.size();i++){
        auto& other=g.tracks[i];if(i==static_cast<std::size_t>(u-g.units) || !other.spawned || other.wave_id!=t.wave_id || other.owner!=t.owner || other.pair_index!=0xffffffffu || other.pair_used)continue;
        auto partner=&g.units[i];if(!curse_regular(partner) || partner->flingy.hitpoints<=0)continue;
        t.pair_index=static_cast<U32>(i);t.pair_unique=partner->minor_unique_index;
        other.pair_index=static_cast<U32>(u-g.units);other.pair_unique=u->minor_unique_index;
        role_marker(u,0,20,378);role_marker(partner,0,20,378);break;
    }
}
void curse_death(bw::Unit* u,bool direct_combat) {
    auto t=existing_track(u);if(!t || !regular_enemy(u) || t->death_processed)return;t->death_processed=true;
    rework_waves::note_death(u,direct_combat);
    // Count the lethal damage callback once. A stale native last-attacker byte
    // on a trigger-removed unit is not evidence of a player combat kill.
    if(direct_combat && !t->spawned && g.growth.curse_counts[6]){
        if(++g.kills_for_wave>=20){g.kills_for_wave=0;g.death_wave_due=true;}
    }
    if(!curse_regular(u))return;
    const auto frame=g.game()->frame_count;const auto pos=u->flingy.position;
    const bool combat=u->last_attacking_player==player_owner() && frame-t->last_damage_frame<=2;
    if(t->spawned && combat && g.growth.curse_counts[10]){
        bool merged=false;for(auto& b:g.bombs){const auto dx=std::int64_t(b.x)-pos.x,dy=std::int64_t(b.y)-pos.y;
            if(frame-b.created<=12 && dx*dx+dy*dy<=32ll*32){merged=true;break;}}
        if(!merged && g.bombs.size()<1600){
            g.bombs.push_back({pos.x,pos.y,frame,frame+24,4u+4u*std::min(3u,U32(g.growth.curse_counts[10])),u->player});
            ground_pulse(pos.x,pos.y,u->player);message("사망 지점의 소형 폭약: 1초 뒤 폭발합니다.");
        }
    }
    if(t->commander && combat && g.growth.curse_counts[13]){
        U32 left=4u+4u*std::min(3u,U32(g.growth.curse_counts[13]));
        living_units([&](bw::Unit* other){auto track=existing_track(other);if(!left || other==u || !curse_regular(other) || !track || track->wave_id!=t->wave_id || track->command_until)return;
            const auto p=other->flingy.position;const auto dx=std::int64_t(p.x)-pos.x,dy=std::int64_t(p.y)-pos.y;
            if(dx*dx+dy*dy<=192ll*192){track->command_until=frame+192;role_marker(other,16,0,379);--left;}
        });
    }
    if(t->pair_index<g.units_count && !t->pair_used){
        auto partner=&g.units[t->pair_index];auto other=existing_track(partner);
        if(other && curse_regular(partner) && partner->flingy.hitpoints>0 && partner->minor_unique_index==t->pair_unique && other->wave_id==t->wave_id && !other->pair_used){
            other->pair_due=frame+48;other->pair_used=true;role_marker(partner,0,20,379);
        }t->pair_used=true;
    }
}
void update_diversity() {
    const auto frame=g.game()->frame_count;if(frame==g.last_diversity_frame)return;g.last_diversity_frame=frame;
    std::vector<bw::Unit*> living;living_units([&](bw::Unit* u){living.push_back(u);});
    for(auto u:living){auto t=track_unit(u);if(!t)continue;
        if(u->flingy.hitpoints<t->hp || u->shields<t->shields){t->last_damage_frame=frame;t->last_damage=g.game()->elapsed_seconds;}
        t->hp=u->flingy.hitpoints;t->shields=u->shields;
        if(!curse_regular(u))continue;
        if(t->pair_due && frame>=t->pair_due){t->pair_due=0;heal_enemy(u,effective_max_hp(u)*35u/100u);}
        if(frame%24)continue;
        if(g.growth.curse_counts[9] && frame-t->last_attack_frame>=192 && frame-t->last_damage_frame>=192)role_marker(u,0,-32,377);
        if(t->commander){role_marker(u,16,-24,379);const auto p=u->flingy.position;for(const auto d:{-192,192}){ground_pulse(p.x+d,p.y,u->player,367);ground_pulse(p.x,p.y+d,u->player,367);}for(const auto x:{-136,136})for(const auto y:{-136,136})ground_pulse(p.x+x,p.y+y,u->player,367);}
        if(t->command_until>frame)role_marker(u,16,0,379);
        if(t->pair_index<g.units_count && !t->pair_used){role_marker(u,0,20,378);
            if(static_cast<U32>(u-g.units)<t->pair_index){auto partner=&g.units[t->pair_index];const auto p=u->flingy.position,q=partner->flingy.position;
                if(partner->minor_unique_index==t->pair_unique && partner->flingy.hitpoints>0)for(int n=1;n<=8;n++)ground_pulse(p.x+(q.x-p.x)*n/9,p.y+(q.y-p.y)*n/9,u->player,367);
            }}
        if(t->pair_due)role_marker(u,0,20,379);
        if(!t->medic)continue;role_marker(u,-16,-24,377);bw::Unit* best=nullptr;U32 maximum=1;
        for(auto other:living){auto track=existing_track(other);if(other==u || !curse_regular(other) || !track || track->medic || track->wave_id!=t->wave_id || (track->healed_frame && frame-track->healed_frame<24))continue;
            const auto p=other->flingy.position,q=u->flingy.position;const auto dx=int(p.x)-q.x,dy=int(p.y)-q.y;const auto maxhp=effective_max_hp(other);
            if(dx*dx+dy*dy>96*96 || other->flingy.hitpoints>=static_cast<int>(maxhp))continue;
            if(!best || std::uint64_t(other->flingy.hitpoints)*maximum<std::uint64_t(best->flingy.hitpoints)*maxhp){best=other;maximum=maxhp;}
        }
        if(best){heal_enemy(best,6u*256u);existing_track(best)->healed_frame=frame;}
    }
    for(std::size_t i=0;i<g.bombs.size();){const auto bomb=g.bombs[i];if(frame<bomb.due){if(frame%6==0)ground_pulse(bomb.x,bomb.y,bomb.owner);++i;continue;}
        for(auto u:living){auto t=track_unit(u);if(!t || u->player!=player_owner() || !regular_combat_type(u->unit_id) || (u->flags&0x44000004u) || protected_objective_unit(u) || (t->bomb_hit_frame && frame-t->bomb_hit_frame<24))continue;
            const auto p=u->flingy.position;const auto dx=int(p.x)-bomb.x,dy=int(p.y)-bomb.y;if(dx*dx+dy*dy>24*24)continue;
            U32 damage=bomb.damage*256;const auto shield=std::min(damage,static_cast<U32>(std::max(0,u->shields)));u->shields-=shield;damage-=shield;t->bomb_hit_frame=frame;
            if(damage){const bool normal=g.normal_hit;g.normal_hit=false;OwnerDatScope scope(u->player,bomb.owner,u);g.damage(u,static_cast<int>(damage),nullptr,bomb.owner,1);g.normal_hit=normal;}
        }g.bombs.erase(g.bombs.begin()+static_cast<std::ptrdiff_t>(i));
    }
}
