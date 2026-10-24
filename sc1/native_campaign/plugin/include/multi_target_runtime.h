// Native multi-target attacks. Included inside native_plugin's anonymous namespace.
// API44 callbacks are cached only during plugin initialization. No direct HP edits.
// Source behavior: neivv/teippi Unit::CanAttackUnit/GetCooldown/AttackAtPoint,
// Bullet::Initialize (the spawner order_target is authoritative at creation).
#pragma once
namespace multi_target {
using CanAttackFn=U32 (__cdecl*)(bw::Unit*,bw::Unit*,U32);
using OutsideRangeFn=U32 (__cdecl*)(bw::Unit*,bw::Unit*);
struct Clock { U32 due=0, frame=0, count=0; bool used=false, natural=false; };
struct Track {
    bw::Unit* pointer=nullptr; U32 id=228, owner=12, unique=0;
    bool armed=false; Clock layer[2]{}; U32 bc_frame=0; bool bc_used=false;
};
inline CanAttackFn can_attack=nullptr;
inline OutsideRangeFn outside_range=nullptr;
inline CreateBulletFn create_bullet=nullptr;
inline std::vector<Track> tracks;
inline bw::Unit* tracked_array=nullptr;
inline U32 depth=0;
inline bool secondary() noexcept {return depth!=0;}
inline void bind(CanAttackFn attack,OutsideRangeFn range,CreateBulletFn create) noexcept {
    can_attack=attack;outside_range=range;create_bullet=create;
}
inline void reset() noexcept {tracks.clear();tracked_array=nullptr;depth=0;}
inline void invalidate(bw::Unit* unit) noexcept {
    for(auto& state:tracks)if(state.pointer==unit || (valid_unit(state.pointer) && state.pointer->subunit==unit))state={};
}
inline bool alive(const bw::Unit* u) noexcept {return valid_unit(u) && u->flingy.hitpoints>0 && u->order!=0;}
inline bool flying(const bw::Unit* u) noexcept {return (u->flags&4u)!=0;}
inline bw::Unit* body(bw::Unit* spawner) noexcept {
    if(!alive(spawner))return nullptr;
    if(spawner->unit_id==4){
        auto main=spawner->subunit;
        return alive(main) && main->unit_id==3 && main->subunit==spawner && main->player==spawner->player ? main : nullptr;
    }
    return spawner;
}
inline bw::Unit* gun(bw::Unit* main) noexcept {
    if(!alive(main))return nullptr;
    if(main->unit_id!=3)return main;
    auto turret=main->subunit;
    return alive(turret) && turret->unit_id==4 && turret->subunit==main && turret->player==main->player ? turret : nullptr;
}
inline bool enabled(bw::Unit* main) noexcept {
    if(!g.active || !g.applied || !g.game || !g.game() || GetCurrentThreadId()!=g.game_thread || !can_attack || !outside_range || !create_bullet || !alive(main) || main->player!=player_owner())return false;
    for(const auto& effect:frozen::multi_target_patches)
        if(main->unit_id==effect.unit_id && (g.growth.talent_bits[effect.bit/32]&(1u<<(effect.bit%32))))return true;
    return false;
}
inline Track* track(bw::Unit* main) {
    if(!valid_unit(main))return nullptr;
    if(tracked_array!=g.units || tracks.size()!=g.units_count){tracks.assign(g.units_count,{});tracked_array=g.units;}
    auto& t=tracks[static_cast<std::size_t>(main-g.units)];
    if(t.pointer!=main || t.id!=main->unit_id || t.owner!=main->player || t.unique!=main->minor_unique_index){
        t={};t.pointer=main;t.id=main->unit_id;t.owner=main->player;t.unique=main->minor_unique_index;
    }
    return &t;
}
inline bool attack_order(U32 order) noexcept {
    // Attack, attack-unit/fixed/tile, attack-move, stay-in-range, turret attack,
    // hold and patrol. Deliberately excludes move/stop and all spell orders.
    return order==8 || order==10 || order==11 || order==12 || order==14 || order==21 ||
        order==22 || order==107 || order==152 || order==157 || order==158 || order==159;
}
inline bool firing_allowed(bw::Unit* main,bw::Unit* spawner) noexcept {
    // CanAttackUnit also checks lockdown/stasis/maelstrom; Dweb and transport
    // restrictions are explicit because they are checked elsewhere by BW.
    constexpr U32 blocked=0x8u|0x20u|0x40u|0x400u|0x8000u|0x40000000u;
    return alive(main) && alive(spawner) && (main->flags&1u) && !main->lockdown_timer && !main->stasis_timer && !main->maelstrom_timer && !(main->flags&blocked) && !(spawner->flags&blocked) &&
        attack_order(main->order) && (main==spawner || attack_order(spawner->order));
}
inline U32 weapon_for(bw::Unit* spawner,bool air) noexcept {
    return original_stat({0,air ? 19u : 17u,spawner->unit_id});
}
inline U32 factor(U32 weapon) noexcept {
    // This is weapons.dat damageFactor, not units.dat maxGroundHits/maxAirHits.
    return std::max(1u,std::min(8u,original_stat({1,17,weapon})));
}
inline bool target_ok(bw::Unit* main,bw::Unit* spawner,bw::Unit* target) noexcept {
    if(!alive(target) || target==main || target==spawner || !is_enemy(target->player) || !firing_allowed(main,spawner))return false;
    // Detection alone does not establish ordinary fog-of-war visibility.
    auto sprite=static_cast<const bw::SpriteScr*>(target->flingy.sprite);
    if(!sprite || !(sprite->visibility_mask&(1u<<main->player)))return false;
    const U32 weapon=weapon_for(spawner,flying(target));if(weapon>=130)return false;
    OwnerDatScope scope(main->player,main->player,spawner);
    return can_attack(spawner,target,1)!=0 && outside_range(spawner,target)==0;
}
inline std::uint64_t distance_sq(bw::Unit* a,bw::Unit* b) noexcept {
    const auto x=std::int64_t(a->flingy.position.x)-b->flingy.position.x;
    const auto y=std::int64_t(a->flingy.position.y)-b->flingy.position.y;
    return static_cast<std::uint64_t>(x*x+y*y);
}
inline bw::Unit* choose(bw::Unit* main,bw::Unit* spawner,int layer,bw::Unit* excluded,bw::Unit* excluded2=nullptr) {
    if(!firing_allowed(main,spawner))return nullptr;
    bw::Unit* best=nullptr;std::uint64_t distance=~std::uint64_t(0);
    living_units([&](bw::Unit* candidate){
        if(candidate==excluded || candidate==excluded2 || (layer>=0 && flying(candidate)!=(layer!=0)))return;
        const auto d=distance_sq(main,candidate);
        // A candidate that cannot beat the current nearest valid target need
        // not enter the owner DAT scope or either native targeting query.
        if(d>distance || (d==distance && best && candidate>=best))return;
        if(!target_ok(main,spawner,candidate))return;
        best=candidate;distance=d;
    });
    return best;
}

inline U32 direction_to(bw::Unit* from,bw::Unit* target) noexcept {
    const double dx=double(target->flingy.position.x)-from->flingy.position.x;
    const double dy=double(target->flingy.position.y)-from->flingy.position.y;
    if(dx==0 && dy==0)return from->flingy.facing_direction;
    // BW: north=0, east=64, south=128; this does not turn the real unit.
    const auto direction=static_cast<int>(std::lround(std::atan2(dx,-dy)*(128.0/3.14159265358979323846)));
    return static_cast<U32>(direction)&255u;
}
struct Dimensions {std::uint16_t left,top,right,bottom;};
static_assert(sizeof(Dimensions)==8,"units.dat dimensions are four u16 values");
inline Dimensions dimensions(U32 id) noexcept {
    // This is a structured DAT field, not four ordinary per-unit scalar keys.
    // bw_dat UnitId::dimensions casts field38.data to DimensionRect[entries].
    Dimensions result{};const auto getter=g.dat_getters[0];if(!getter)return result;
    std::size_t fields=0;auto tables=getter(&fields);if(!tables || fields<=38)return result;
    const auto& field=tables[38];if(!field.data)return result;
    const bool structures=field.entry_size==sizeof(Dimensions) && id<field.entries;
    const bool flat_words=field.entry_size==2 && std::uint64_t(id+1)*4<=field.entries;
    if(!structures && !flat_words)return result;
    std::memcpy(&result,static_cast<const U8*>(field.data)+std::size_t(id)*sizeof(result),sizeof(result));
    return result;
}
inline bw::Point32 launch_position(bw::Unit* spawner,bw::Unit* target,U32 weapon,U32 direction) noexcept {
    // FireWeapon selects the position before CreateBullet. The callback does
    // not relocate an AppearOnTargetUnit bullet from its supplied coordinates.
    // References: GPTP weapon_fire.cpp; OpenBW bwgame.h fire_weapon.
    const U32 behavior=original_stat({1,8,weapon});
    if(behavior==2){
        const auto box=dimensions(target->unit_id);
        const int left=box.left,top=box.top,right=box.right,bottom=box.bottom;
        const int mx=(left+right)/4,my=(top+bottom)/4;
        const int x1=target->flingy.position.x-left+mx,x2=target->flingy.position.x+right-mx;
        const int y1=target->flingy.position.y-top+my,y2=target->flingy.position.y+bottom-my;
        const int cx=x1+(x2-x1)/2,cy=y1+(y2-y1)/2;
        const int dx=spawner->flingy.position.x-cx,dy=spawner->flingy.position.y-cy;
        double t=1.0;
        if(dx<0)t=std::min(t,double(x1-cx)/dx);else if(dx>0)t=std::min(t,double(x2-cx)/dx);
        if(dy<0)t=std::min(t,double(y1-cy)/dy);else if(dy>0)t=std::min(t,double(y2-cy)/dy);
        return {std::clamp(cx+static_cast<int>(dx*t),x1,x2),std::clamp(cy+static_cast<int>(dy*t),y1,y2)};
    }
    if(behavior==3)return {target->flingy.position.x,target->flingy.position.y};
    const int forward=static_cast<int>(original_stat({1,20,weapon}));
    const int upward=static_cast<int>(original_stat({1,21,weapon}));
    const double radians=direction*(3.14159265358979323846/128.0);
    const int vx=static_cast<int>(std::lround(std::sin(radians)*256.0));
    const int vy=static_cast<int>(std::lround(-std::cos(radians)*256.0));
    return {spawner->flingy.position.x+vx*forward/256,spawner->flingy.position.y+vy*forward/256-upward};
}
struct TargetScope {
    bw::Unit* unit; decltype(bw::Unit::order_target) saved;
    TargetScope(bw::Unit* u,bw::Unit* target) noexcept:unit(u),saved(u->order_target){
        unit->order_target.unit=target;unit->order_target.x=target->flingy.position.x;unit->order_target.y=target->flingy.position.y;
    }
    ~TargetScope(){unit->order_target=saved;}
};
struct SecondaryScope {SecondaryScope() noexcept {++depth;}~SecondaryScope(){--depth;}};
inline U32 emit(bw::Unit* main,bw::Unit* spawner,bw::Unit* target,U32 weapon) {
    if(!target_ok(main,spawner,target) || weapon!=weapon_for(spawner,flying(target)))return 0;
    OwnerDatScope owner(main->player,main->player,spawner);TargetScope destination(spawner,target);SecondaryScope recursion;
    const U32 direction=direction_to(spawner,target);U32 made=0;
    for(U32 i=0;i<factor(weapon);i++){
        if(!target_ok(main,spawner,target))break;
        const auto position=launch_position(spawner,target,weapon,direction);
        auto bullet=create_bullet(weapon,position.x,position.y,main->player,direction,spawner);
        if(bullet)++made;
    }
    return made;
}
inline U32 period(bw::Unit* spawner,U32 weapon) noexcept {
    // Original GetCooldown status modifiers. Secondary clocks intentionally do
    // not advance the global RNG; the vanilla primary retains its random +/-1.
    U32 value=original_stat({1,16,weapon});
    if(spawner->acid_spore_count)value+=std::max(3u,value/8)*spawner->acid_spore_count;
    const int bonus=(spawner->stim_timer ? 1 : 0)+((spawner->flags&0x20000000u) ? 1 : 0)-(spawner->ensnare_timer ? 1 : 0);
    if(bonus>0)value/=2;else if(bonus<0)value+=value/4;
    value=std::max(5u,std::min(250u,value));
    std::uint64_t num=1,den=1;
    for(const auto& p:frozen::patches)if(p.table==1 && p.field==16 && p.id==weapon &&
        (g.growth.talent_bits[p.bit/32]&(1u<<(p.bit%32)))){talent_power::multiply(num,den,p.bit,p.numerator,p.denominator);}
    return static_cast<U32>(std::max<std::uint64_t>(1,std::min<std::uint64_t>(255,(value*num+den/2)/den)));
}
inline bool ready(const Clock& c,U32 frame) noexcept {return !c.used || static_cast<std::int32_t>(frame-c.due)>=0;}
inline bool allow_primary(U32 weapon,bw::Unit* spawner) {
    if(secondary())return true;auto main=body(spawner);
    if(!enabled(main) || main->unit_id!=3 || gun(main)!=spawner || (weapon!=7 && weapon!=8))return true;
    auto t=track(main);if(!t)return true;
    const auto frame=g.game()->frame_count;const auto& c=t->layer[weapon==8 ? 1 : 0];
    // Natural primary timing remains entirely with BW (including RNG jitter).
    // Only a recently synthesized opposite-layer attack blocks an early
    // natural shot when the player changes the primary target layer.
    // Stop/move disarms periodic extras, but cannot erase a spent layer cycle.
    return c.natural || ready(c,frame);
}
inline void launched(U32 weapon,bw::Unit* spawner,bw::Bullet* result) {
    if(!result || secondary())return;auto main=body(spawner);
    if(!enabled(main) || gun(main)!=spawner || !firing_allowed(main,spawner))return;
    auto primary=spawner->order_target.unit;
    if(!target_ok(main,spawner,primary) || weapon!=weapon_for(spawner,flying(primary)))return;
    const auto frame=g.game()->frame_count;auto t=track(main);if(!t)return;
    if(main->unit_id==3){
        const auto layer=flying(primary) ? 1u : 0u;auto& c=t->layer[layer];
        if(c.used && c.natural && c.frame==frame){++c.count;return;}
        c={frame+period(spawner,weapon),frame,1,true,true};t->armed=true;
    }else if(main->unit_id==12){
        // A BC has factor 1, one attackwith opcode, and one primary per frame.
        if(t->bc_used && t->bc_frame==frame)return;t->bc_frame=frame;t->bc_used=true;
        auto first=choose(main,spawner,-1,primary);
        if(first)emit(main,spawner,first,weapon_for(spawner,flying(first)));
        auto second=choose(main,spawner,-1,primary,first);
        if(second)emit(main,spawner,second,weapon_for(spawner,flying(second)));
    }
}
inline void step() {
    if(!g.active || !g.applied || !g.game || !g.game() || GetCurrentThreadId()!=g.game_thread || secondary())return;
    for(auto& state:tracks)if(state.pointer && (!enabled(state.pointer) || state.pointer->unit_id!=state.id || state.pointer->player!=state.owner || state.pointer->minor_unique_index!=state.unique))state={};
    std::vector<bw::Unit*> mains;
    living_units([&](bw::Unit* unit){if(unit->unit_id==3 && enabled(unit))mains.push_back(unit);});
    const auto frame=g.game()->frame_count;
    for(auto main:mains){
        auto spawner=gun(main);if(!spawner)continue;auto t=track(main);if(!t || !t->armed)continue;
        if(!firing_allowed(main,spawner)){t->armed=false;continue;}
        // A real engine attack must establish engagement. Retain no separate
        // order target: stop/move, dying targets and lost detection halt extras.
        auto primary=spawner->order_target.unit;
        if(!target_ok(main,spawner,primary))continue;
        const U32 layer=flying(primary) ? 0u : 1u;
        {
            auto& c=t->layer[layer];if(!ready(c,frame))continue;
            auto target=flying(primary)==(layer!=0) ? primary : choose(main,spawner,static_cast<int>(layer),nullptr);
            if(!target)continue;const auto weapon=weapon_for(spawner,layer!=0);
            // Consume the cycle even on pool exhaustion; never retry every
            // frame or turn a partial two-missile bundle into an extra burst.
            c={frame+period(spawner,weapon),frame,0,true,false};
            emit(main,spawner,target,weapon);
        }
    }
}
} // namespace multi_target
