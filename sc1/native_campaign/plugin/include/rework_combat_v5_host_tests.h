#pragma once
// Deterministic synthetic host checks. These test native-adapter behavior with
// explicit mock callbacks; they do not establish actual SC:R engine/UI proof.
namespace host_test {
namespace rework_fixture {
inline std::array<U32,rework_catalog::kTalentCount> ranks{};
inline U32 lookup(const GrowthSnapshot&,U32 ordinal) noexcept {return ordinal<ranks.size() ? ranks[ordinal] : 0;}
inline bw::Bullet* __cdecl hooked(U32 w,int x,int y,U32 owner,U32 direction,bw::Unit* source){
    auto b=owner_bullet_create_hook(w,x,y,owner,direction,source,multi_fixture::raw);
    if(b&&rework_combat_v5::projectiles.find(b)==rework_combat_v5::projectiles.end())rework_combat_v5::launched(w,source,b);
    return b;
}
inline void begin(std::initializer_list<U32> talents={}){
    reset();rework_combat_v5::reset();ranks.fill(0);for(auto n:talents)ranks[n]=1;
    rework_combat_v5::bind(lookup);g.applied=true;g.growth={};game.frame_count=100;
    multi_fixture::shots.clear();multi_fixture::next_bullet=multi_fixture::failures=0;multi_fixture::fail_all=false;
    multi_target::bind(multi_fixture::can,multi_fixture::outside,hooked);refresh_units();
}
inline void install(){
    GrowthSnapshot s{};std::vector<Edit> edits;CHECK(rework_combat_v5::plan_stats(s,edits));
    g.baseline=edits;g.friendly_edits=edits;g.owner_edits.clear();for(const auto& e:edits)g.owner_edits.push_back({e.key,e.table,e.before,e.after,e.before});
}
inline bw::Unit* unit(U32 id,U32 owner,int x,int y,bool flying=false){return multi_fixture::unit(id,owner,x,y,flying);}
inline bw::Bullet* bullet(bw::Unit* source,bw::Unit* target,U32 w){multi_fixture::target(source,target);return hooked(w,source->flingy.position.x,source->flingy.position.y,source->player,0,source);}
inline void pulse(U32 frame){game.frame_count=frame;rework_combat_v5::step();}
inline void finish(){rework_combat_v5::reset();rework_combat_v5::rank_lookup=nullptr;combat_effects::damage_enter=nullptr;combat_effects::damage_leave=nullptr;combat_effects::damage_filter=nullptr;combat_effects::damage_skip=nullptr;movement_effects::ratio_extension=nullptr;movement_effects::script_transform=nullptr;rework_combat_v5::get_sprite_position=nullptr;rework_combat_v5::set_sprite_position=nullptr;rework_combat_v5::native_give=nullptr;rework_combat_v5::native_kill=nullptr;rework_combat_v5::script_context_read=nullptr;rework_combat_v5::script_context_write=nullptr;}
inline U32 native_area_calls=0;
inline std::array<std::uint16_t,2> bullet_position{};
inline void __cdecl sprite_get(void*,std::uint16_t* out){out[0]=bullet_position[0];out[1]=bullet_position[1];}
inline void __cdecl sprite_set(void*,const std::uint16_t* in){bullet_position={in[0],in[1]};}
inline void __cdecl area(bw::Bullet* b){
    ++native_area_calls;const int radius=b->weapon_id==58 ? 64:48;
    living_units([&](bw::Unit* u){if(!rework_combat_v5::eligible(u)||u==b->parent||std::abs(int(u->flingy.position.x)-b->target.x)>radius||std::abs(int(u->flingy.position.y)-b->target.y)>radius)return;
        if(b->weapon_id==58)u->ensnare_timer=75;
        if(b->weapon_id==83)u->stasis_timer=80;
        if(b->weapon_id==108&&rework_combat_v5::organic(u)){if(hallucination(u))kill(u);else u->maelstrom_timer=100;}
    });
}
inline U32 native_order_calls=0;
inline void __cdecl native_cast(bw::Unit* u){
    ++native_order_calls;auto target=u->order_target.unit;
    if(u->order==148&&target){for(U32 i=0;i<2;i++){auto n=unit(target->unit_id,u->player,target->flingy.position.x+int(i)*10,target->flingy.position.y);n->flags|=0x40000000u;n->death_timer=1350;rework_combat_v5::created(n);}u->energy=std::uint16_t(u->energy-100*256);u->order=3;}
    if(u->order==182&&target){target->player=u->player;u->energy=std::uint16_t(u->energy-150*256);u->shields=0;u->order=3;}
    if(u->order==141&&target){target->defensive_matrix_dmg=250*256;target->matrix_timer=168;u->energy=std::uint16_t(u->energy-100*256);u->order=3;}
    if(u->order==6){u->flingy.move_target.x=u->order_target.x;u->flingy.move_target.y=u->order_target.y;}
}
inline void __cdecl give(bw::Unit* u,U32 owner){u->player=U8(owner);}
inline U32 __cdecl max200(bw::Unit*){return 200*256;}
inline U32 __cdecl targeting(bw::Unit*,U32 tech,bw::Unit* target,U32,U32,U32,std::uint16_t*){
    if(tech==1)return (raw_value(0,22,target->unit_id)&0x40000000u) ? 1u:0u;
    if(tech==12)return target->unit_id==106&&U32(target->flingy.hitpoints)<=effective_max_hp(target)/2;
    if(tech==27)return !protected_objective_unit(target)&&!(raw_value(0,22,target->unit_id)&0x40u);
    return 0;
}
inline rework_relocation::Pathing pathing{};inline bool placement_allowed=true;inline U32 moves=0;
inline rework_relocation::Pathing* __cdecl get_pathing(){return &pathing;}
inline void __cdecl move(bw::Unit* u,U32 x,U32 y){++moves;u->flingy.position={std::int16_t(x),std::int16_t(y)};u->flingy.exact_position={int(x)*256,int(y)*256};}
inline U32 __cdecl place(bw::Unit*,const bw::Point* desired,bw::Point* result,const void*,U32 a,U32 b){CHECK(!a&&!b);*result=*desired;return placement_allowed ? 1u:0u;}
inline void relocation(){pathing={};pathing.count=1;pathing.regions[0].group=1;rework_relocation::pathing_source=get_pathing;rework_relocation::native_move=move;rework_relocation::native_place=place;placement_allowed=true;moves=0;}
inline void relocation_end(){rework_relocation::native_move=nullptr;rework_relocation::native_place=nullptr;rework_relocation::pathing_source=nullptr;}
inline std::array<std::size_t,3> script_context{};inline U32 script_writes=0;
inline void __cdecl script_read(const std::uint16_t* ids,std::size_t* out,std::size_t length){CHECK(length==3);for(std::size_t i=0;i<length;i++){CHECK(ids[i]==rework_combat_v5::script_context_ids[i]);out[i]=script_context[i];}}
inline void __cdecl script_write(const std::uint16_t* ids,const std::size_t* in,std::size_t length){CHECK(length==3);++script_writes;for(std::size_t i=0;i<length;i++){CHECK(ids[i]==rework_combat_v5::script_context_ids[i]);script_context[i]=in[i];}}
inline bw::Bullet* __cdecl checked_bullet(U32 w,int x,int y,U32 owner,U32 direction,bw::Unit* source){CHECK(script_context[0]==reinterpret_cast<std::size_t>(&source->flingy)&&script_context[1]==reinterpret_cast<std::size_t>(source)&&script_context[2]==0);return multi_fixture::raw(w,x,y,owner,direction,source);}
inline std::vector<bw::Unit*> yamato_targets;
inline void __cdecl yamato(bw::Bullet* b){
    auto target=b->target.unit;CHECK(target&&rework_combat_v5::DamageScope::current_primary==target);yamato_targets.push_back(target);
    const bool extra=rework_combat_v5::DamageScope::current_secondary;CHECK(rework_combat_v5::DamageScope::current_percent==(extra ? 50u:100u));
    std::int32_t amount=260*256;{rework_combat_v5::DamageScope hit(target,nullptr,30,1,amount);}target->flingy.hitpoints-=amount;
    if(extra){CHECK(b->flingy.position.x==target->flingy.position.x&&b->flingy.exact_position.x==int(target->flingy.position.x)*256);CHECK(bullet_position[0]==target->flingy.position.x);b->flags^=8;b->target={1,2,nullptr};b->flingy.position={3,4};b->flingy.exact_position={5,6};bullet_position={7,8};}
}
}
inline void rework_stats_and_repeatable_fractional(){
    using namespace rework_fixture;begin({26,27,28,29,11});install();
    CHECK(owner_stat(1,{0,8,0})==original_stat({0,8,0})*6/5);
    CHECK(owner_stat(1,{0,8,5})==original_stat({0,8,5})*6/5);
    CHECK(owner_stat(1,{0,8,30})==original_stat({0,8,30})*6/5);
    CHECK(owner_stat(1,{0,8,9})==original_stat({0,8,9})*6/5);
    CHECK(owner_stat(6,{0,8,0})==original_stat({0,8,0}));
    CHECK(owner_stat(2,{0,8,0})==original_stat({0,8,0}));
    auto source=unit(0,1,100,100);ranks[29]=1;
    U32 ticks=0;for(U32 i=0;i<1000;i++)ticks+=rework_combat_v5::fractional_period(source,0,8,rework_combat_v5::cooldown_ratio(source,0));
    CHECK(ticks>=7759&&ticks<=7760);CHECK(rework_combat_v5::cooldown_ratio(source,0)<1);
    ranks[29]=10000;for(U32 i=0;i<20;i++)CHECK(rework_combat_v5::fractional_period(source,0,8,rework_combat_v5::cooldown_ratio(source,0))==1);
    source->player=6;CHECK(rework_combat_v5::cooldown_ratio(source,0)==1);
    CHECK(raw_value(0,8,0)==original_stat({0,8,0}));finish();
}
inline void rework_medic_actual_pulses_and_lifecycle(){
    using namespace rework_fixture;begin();auto medic=unit(34,1,100,100),enemy=unit(37,6,120,100),a=unit(37,6,130,100),b=unit(37,6,140,100),c=unit(37,6,150,100),ally=unit(0,1,125,100);
    auto shot=bullet(medic,enemy,107);{rework_combat_v5::MissileScope scope(shot);enemy->is_blind=1;}pulse(124);CHECK(enemy->flingy.hitpoints==256000&&a->flingy.hitpoints==256000);
    begin({161});medic=unit(34,1,100,100);enemy=unit(37,6,120,100);a=unit(37,6,130,100);b=unit(37,6,140,100);c=unit(37,6,150,100);ally=unit(0,1,125,100);
    shot=bullet(medic,enemy,107);{rework_combat_v5::MissileScope scope(shot);enemy->is_blind=1;}
    pulse(123);CHECK(enemy->flingy.hitpoints==256000);pulse(124);
    CHECK(enemy->flingy.hitpoints==256000-8*256);CHECK(a->flingy.hitpoints==256000-8*256);CHECK(b->flingy.hitpoints==256000-8*256);CHECK(c->flingy.hitpoints==256000);CHECK(ally->flingy.hitpoints==256000);
    // A recast refreshes one schedule, never adds a second simultaneous aura.
    game.frame_count=130;shot=bullet(medic,enemy,107);{rework_combat_v5::MissileScope scope(shot);enemy->is_blind=1;}CHECK(rework_combat_v5::persistent.size()==1);
    pulse(148);CHECK(enemy->flingy.hitpoints==256000-16*256);
    enemy->player=1;pulse(172);CHECK(rework_combat_v5::persistent.empty());CHECK(enemy->flingy.hitpoints==256000-16*256);
    begin({41});medic=unit(34,1,100,100);ally=unit(0,1,120,100);ally->flingy.hitpoints=20*256;enemy=unit(37,6,130,100);a=unit(37,6,140,100);b=unit(37,6,150,100);c=unit(37,6,160,100);
    shot=bullet(medic,ally,102);{rework_combat_v5::MissileScope scope(shot);ally->ensnare_timer=0;}pulse(124);
    CHECK(ally->flingy.hitpoints==28*256);CHECK(enemy->flingy.hitpoints==256000-6*256);CHECK(a->flingy.hitpoints==256000-6*256);CHECK(b->flingy.hitpoints==256000-6*256);CHECK(c->flingy.hitpoints==256000);finish();
}
inline void rework_infantry_percentage_damage(){
    using namespace rework_fixture;begin({29});install();auto marine=unit(0,1,100,100),target=unit(37,6,150,100);g.normal_hit=true;
    CHECK(owner_stat(1,{1,14,0})==original_stat({1,14,0}));
    for(U32 stacks:{1u,2u,10u}){ranks[29]=stacks;std::int32_t amount=6*256;
        {rework_combat_v5::DamageScope hit(target,marine,0,1,amount);CHECK(amount==std::int32_t(6*256*(10+stacks)/10));}}
    ranks[29]=1;CHECK(rework_combat_v5::infantry_ui_value(marine,0,6)==7);CHECK(rework_combat_v5::infantry_ui_value(marine,0,20)==22);
    marine->player=6;std::int32_t amount=6*256;{rework_combat_v5::DamageScope hit(target,marine,0,1,amount);CHECK(amount==6*256);}CHECK(rework_combat_v5::infantry_ui_value(marine,0,6)==6);
    marine->player=1;marine->flags|=0x40000000u;amount=6*256;{rework_combat_v5::DamageScope hit(target,marine,0,1,amount);CHECK(amount==6*256);}marine->flags&=~0x40000000u;
    auto vehicle=unit(2,1,100,100);amount=20*256;{rework_combat_v5::DamageScope hit(target,vehicle,1,1,amount);CHECK(amount==20*256);}
    g.normal_hit=false;amount=100*256;{rework_combat_v5::DamageScope hit(target,marine,30,1,amount);CHECK(amount==100*256);}g.normal_hit=true;
    auto shot=bullet(marine,target,0);CHECK(rework_combat_v5::projectiles.at(shot).infantry_rank==1);ranks[29]=2;kill(marine);g.bullet_hit_context=true;
    {rework_combat_v5::MissileScope missile(shot);amount=6*256;rework_combat_v5::DamageScope hit(target,nullptr,0,1,amount);CHECK(amount==6*256*11/10);}
    CHECK(!rework_combat_v5::DamageScope::current_projectile&&rework_combat_v5::DamageScope::current_infantry_rank==0);
    CHECK(rework_combat_v5::infantry_damage(0x7fffffff,0xffffffffu)==0x7fffffff);finish();
}
inline void rework_ghost_zero_armor_five_seconds(){
    using namespace rework_fixture;begin({51});auto ghost=unit(1,1,100,100),marine=unit(0,1,110,100),target=unit(66,6,150,100),other=unit(66,6,170,100);
    target->shields=80*256;game.upgrade_level_sc[6][15]=3;game.upgrade_level_sc[6][4]=3;
    const auto armor=raw_value(0,27,66),upgrade=raw_value(0,25,66);g.normal_hit=true;
    rework_combat_v5::ordinary_hit(ghost,target,10*256,2,false);
    CHECK(rework_combat_v5::state(target)->armor_mark==220);
    for(U32 frame:{100u,219u}){game.frame_count=frame;std::int32_t damage=10*256;
        {rework_combat_v5::DamageScope hit(target,marine,0,1,damage);CHECK(raw_value(0,27,66)==0&&raw_value(0,25,66)==61);CHECK(rework_upgrade_storage::level(6,15)==0);}
        CHECK(raw_value(0,27,66)==armor&&raw_value(0,25,66)==upgrade);CHECK(rework_upgrade_storage::level(6,15)==3);
        {rework_combat_v5::DamageScope hit(other,marine,0,1,damage);CHECK(raw_value(0,27,66)==armor&&raw_value(0,25,66)==upgrade);}
    }
    game.frame_count=220;std::int32_t damage=10*256;
    {rework_combat_v5::DamageScope hit(target,marine,0,1,damage);CHECK(raw_value(0,27,66)==armor&&raw_value(0,25,66)==upgrade);CHECK(rework_upgrade_storage::level(6,15)==3);}
    game.frame_count=230;rework_combat_v5::ordinary_hit(ghost,target,10*256,2,false);CHECK(rework_combat_v5::state(target)->armor_mark==350);
    g.normal_hit=false;{rework_combat_v5::DamageScope hit(target,marine,30,1,damage);CHECK(raw_value(0,27,66)==armor&&raw_value(0,25,66)==upgrade);CHECK(rework_upgrade_storage::level(6,15)==3);}g.normal_hit=true;
    // The mark is on this target instance, with native extended upgrade
    // storage restored even when compatibility bytes have a different value.
    std::array<U8,61*12> levels{};levels[15*12+6]=5;samase::ExtendedArray extended{levels.data(),levels.data()+levels.size(),0,0};g.extended=&extended;g.extended_count=1;
    {rework_combat_v5::DamageScope hit(target,marine,0,1,damage);CHECK(levels[15*12+6]==0&&game.upgrade_level_sc[6][15]==0);}
    CHECK(levels[15*12+6]==5&&game.upgrade_level_sc[6][15]==3);g.extended=nullptr;g.extended_count=0;
    ++target->minor_unique_index;{rework_combat_v5::DamageScope hit(target,marine,0,1,damage);CHECK(raw_value(0,27,66)==armor&&raw_value(0,25,66)==upgrade);}
    finish();
}
inline void rework_half_armor_native_health_callback(){
    using namespace rework_fixture;
    for(U32 ordinal:{11u,12u})for(U32 stacks:{1u,2u,3u}){
        begin();ranks[ordinal]=stacks;install();auto target=unit(ordinal==11?0:8,1,100,100,ordinal==12),source=unit(0,6,150,100);g.normal_hit=true;
        CHECK(owner_stat(1,{0,27,target->unit_id})==original_stat({0,27,target->unit_id})+stacks/2);
        std::int32_t damage=6*256;
        {rework_combat_v5::DamageScope hit(target,source,0,1,damage);
            const auto before=target->flingy.hitpoints;owner_damage_hook(target,damage-std::int32_t(stacks/2)*256,source,6,1,direct_damage);
            CHECK(before-target->flingy.hitpoints==6*256-std::int32_t(stacks)*128);
            auto other=unit(0,6,180,100);{rework_combat_v5::DamageScope nested(other,target,0,1,damage);CHECK(rework_combat_v5::DamageScope::current==&nested);}CHECK(rework_combat_v5::DamageScope::current==&hit);
        }
        CHECK(!rework_combat_v5::DamageScope::current);finish();
    }
    begin({11});auto target=unit(66,1,100,100),source=unit(0,6,150,100);g.normal_hit=true;
    // Large-sized Dragoon: explosive half-armor reduces128 Q8;
    // Ghost concussive large-size hits reduce32 Q8, preserving native ratios.
    CHECK(original_stat({0,26,66})==3);
    for(auto pair:{std::pair<U32,U32>{8,128},{2,32}}){std::int32_t damage=10*256;
        {rework_combat_v5::DamageScope hit(target,source,pair.first,1,damage);CHECK(hit.half_armor_reduction==pair.second);CHECK(rework_combat_v5::post_armor_damage(target,1000)==1000-int(pair.second));CHECK(rework_combat_v5::post_armor_damage(target,128)==128);}}
    target->shields=2560;std::int32_t damage=10*256;
    {rework_combat_v5::DamageScope hit(target,source,0,1,damage);CHECK(rework_combat_v5::post_armor_damage(target,64)==0);CHECK(target->shields==2560);}
    g.normal_hit=false;{rework_combat_v5::DamageScope hit(target,source,84,1,damage);CHECK(rework_combat_v5::post_armor_damage(target,1000)==1000);}g.normal_hit=true;
    target->player=6;{rework_combat_v5::DamageScope hit(target,source,0,1,damage);CHECK(rework_combat_v5::post_armor_damage(target,1000)==1000);}finish();
}
inline void rework_projectile_counts_and_moving_orders(){
    using namespace rework_fixture;begin({53});auto marine=unit(0,1,100,100),target=unit(37,6,120,100);marine->order=10;
    auto b=bullet(marine,target,0);CHECK(rework_combat_v5::projectiles.at(b).percent==100);CHECK(multi_fixture::shots.size()==1);pulse(102);CHECK(multi_fixture::shots.size()==2);pulse(104);CHECK(multi_fixture::shots.size()==3);pulse(105);CHECK(multi_fixture::shots.size()==3);
    U32 sum=0;for(const auto& entry:rework_combat_v5::projectiles)sum+=entry.second.percent;CHECK(sum==170);CHECK(rework_combat_v5::pending_shots.empty());
    begin({54});auto vulture=unit(2,1,100,100);target=unit(37,6,120,100);vulture->order=6;vulture->order_target={600,700,nullptr};const auto saved=vulture->order_target;
    pulse(100);CHECK(multi_fixture::shots.size()==1);CHECK(vulture->order==6&&vulture->order_target.x==saved.x&&vulture->order_target.y==saved.y&&vulture->order_target.unit==nullptr);pulse(101);CHECK(multi_fixture::shots.size()==1);
    vulture->lockdown_timer=1;pulse(200);CHECK(multi_fixture::shots.size()==1);finish();
}
inline void rework_emp_storm_and_armor_semantics(){
    using namespace rework_fixture;begin({62});auto caster=unit(9,1,100,100),target=unit(68,6,120,100);target->energy=200*256;target->shields=200*256;
    auto b=bullet(caster,target,33);{rework_combat_v5::MissileScope scope(b);target->energy=0;target->shields=0;}CHECK(target->flingy.hitpoints==256000-100*256);
    b=bullet(caster,target,33);{rework_combat_v5::MissileScope scope(b);}CHECK(target->flingy.hitpoints==256000-100*256);
    begin({144});caster=unit(67,1,100,100);target=unit(37,6,120,100);U32 hits=0;
    for(U32 i=0;i<5;i++){b=bullet(caster,target,84);b->flingy.position={120,100};{rework_combat_v5::MissileScope scope(b);if(!target->is_under_storm){++hits;target->is_under_storm=1;}}}CHECK(hits==4);
    begin({19});caster=unit(0,1,100,100);target=unit(66,6,120,100);const auto armor=raw_value(0,27,66),upgrade=raw_value(0,25,66);const auto shield_upgrade=game.upgrade_level_sc[6][15];g.normal_hit=true;
    std::int32_t damage=10*256;{rework_combat_v5::DamageScope scope(target,caster,0,1,damage);CHECK(raw_value(0,27,66)==0);CHECK(raw_value(0,25,66)==61);CHECK(game.upgrade_level_sc[6][15]==shield_upgrade);}CHECK(raw_value(0,27,66)==armor&&raw_value(0,25,66)==upgrade);finish();
}
inline void rework_mobile_siege_burrow_and_ownership(){
    using namespace rework_fixture;begin({55,91});auto siege=unit(30,1,100,100);siege->flags|=0x80000u;siege->order=6;siege->flingy.movement_type=2;siege->flingy.top_speed=1;siege->movement_state=5;
    auto lurker=unit(103,1,150,100);lurker->flags|=0x10u|0x10000000u;lurker->movement_state=2;auto enemy=unit(30,6,200,100);enemy->flingy.top_speed=1;
    pulse(100);CHECK(siege->unit_id==30&&siege->flingy.movement_type==0&&siege->flingy.top_speed==512);CHECK((siege->flags&0x20000u)&&!(siege->flags&0x80000u));CHECK(!rework_combat_v5::allow_primary(siege));CHECK(enemy->flingy.top_speed==1);
    CHECK(lurker->flags&0x10u);{rework_combat_v5::CommandScope scope(1);CHECK(!(lurker->flags&0x10u));}CHECK(lurker->flags&0x10u);CHECK(lurker->flingy.top_speed==384);
    CHECK(siege->movement_state==9&&lurker->movement_state==9);rework_combat_v5::invalidate(siege);CHECK(siege->flingy.movement_type==2&&siege->flingy.top_speed==1);CHECK(siege->flags&0x80000u);CHECK(siege->movement_state==5);finish();
}
inline void rework_native_area_replay_and_restoration(){
    using namespace rework_fixture;
    for(const auto pair:{std::pair<U32,U32>{80,58},{127,83},{124,108}}){
        begin({pair.first});auto caster=unit(pair.first==80 ? 45:pair.first==127 ? 71:63,1,50,50);
        const int base=pair.second==58 ? 64:48,expanded=pair.second==58 ? 80:60;
        auto inner=unit(37,6,500+base-1,500),outer=unit(37,6,500+expanded-1,500),ally=unit(37,1,500,500+expanded-1),outside=unit(37,6,500+expanded+1,500);
        auto immune=unit(37,6,500-expanded+1,500);immune->flags|=0x4000000u;
        auto b=bullet(caster,inner,pair.second);b->target.x=500;b->target.y=500;b->flingy.position={500,500};b->flingy.exact_position={128000,128000};b->flingy.sprite=caster->flingy.sprite;
        rework_combat_v5::get_sprite_position=sprite_get;rework_combat_v5::set_sprite_position=sprite_set;bullet_position={500,500};native_area_calls=0;
        {rework_combat_v5::MissileScope scope(b,area);area(b);}
        const auto timer=[&](bw::Unit* u){return pair.second==58 ? u->ensnare_timer:pair.second==83 ? u->stasis_timer:u->maelstrom_timer;};
        const U32 expected=pair.second==58 ? 112:pair.second==83 ? 120:150;
        CHECK(timer(inner)==expected&&timer(outer)==expected&&timer(ally)==expected);CHECK(!timer(outside)&&!timer(immune));CHECK(immune->flags&0x4000000u);
        CHECK(b->target.x==500&&b->target.y==500&&b->target.unit==inner);CHECK(b->flingy.position.x==500&&b->flingy.exact_position.x==128000);CHECK(bullet_position[0]==500&&bullet_position[1]==500);CHECK(native_area_calls==3);
        CHECK(!(caster->flags&0x4000000u)&&!(outside->flags&0x4000000u));finish();
    }
    // With no talent only the one native dispatch occurs.
    begin();auto caster=unit(45,1,50,50),outer=unit(37,6,579,500);auto b=bullet(caster,outer,58);b->target.x=b->target.y=500;native_area_calls=0;
    {rework_combat_v5::MissileScope scope(b,area);area(b);}CHECK(native_area_calls==1&&!outer->ensnare_timer);finish();
}
inline void rework_matrix_reserve_and_energy_overflow(){
    using namespace rework_fixture;begin({36,37,42});auto vessel=unit(9,1,100,100),target=unit(0,1,120,100);vessel->energy=200*256;vessel->order=141;multi_fixture::target(vessel,target);
    {rework_combat_v5::OrderScope scope(vessel,native_cast);native_cast(vessel);}auto shield=rework_combat_v5::matrix_state(target);
    CHECK(U32(target->defensive_matrix_dmg)+shield->reserve==350*256);CHECK(target->matrix_timer==252);
    auto attacker=unit(37,6,140,100);g.normal_hit=true;
    const U32 initial=target->defensive_matrix_dmg;std::int32_t damage=20*256;
    {rework_combat_v5::DamageScope scope(target,attacker,35,1,damage);CHECK(!scope.absorbed_all);CHECK(damage==0&&target->defensive_matrix_dmg==256);target->defensive_matrix_dmg=128;}
    CHECK(target->defensive_matrix_dmg==initial);CHECK(U32(target->defensive_matrix_dmg)+shield->reserve==330*256);
    // Exhaust a reserve with a sub-half-HP remainder without rounding capacity.
    shield->reserve=100;damage=150;{rework_combat_v5::DamageScope scope(target,attacker,35,1,damage);CHECK(damage==0);target->defensive_matrix_dmg=128;}CHECK(!shield->reserve&&target->defensive_matrix_dmg==initial-50);
    target->acid_spore_count=3;shield->reserve=1000;damage=256;{rework_combat_v5::DamageScope scope(target,attacker,35,1,damage);CHECK(!target->acid_spore_count);CHECK(damage==0);}CHECK(target->acid_spore_count==3&&shield->reserve==0&&target->defensive_matrix_dmg==initial-74);
    CHECK(rework_combat_v5::max_energy_hook(vessel,max200)==65535);auto s=rework_combat_v5::state(vessel);vessel->energy=200*256;rework_combat_v5::add_energy(vessel,*s,100*256);CHECK(U32(vessel->energy)+s->energy_reserve==300*256);
    vessel->energy=std::uint16_t(vessel->energy-75*256);rework_combat_v5::refill_energy(vessel,*s);CHECK(U32(vessel->energy)+s->energy_reserve==225*256&&s->energy_reserve==0);
    vessel->energy=1000;s->energy_seen=true;s->last_energy=992;pulse(101);CHECK(vessel->energy==1012);
    vessel->energy=0;pulse(102);CHECK(!vessel->energy&&!s->energy_reserve);
    target->matrix_timer=0;shield->reserve=1000;pulse(103);CHECK(!shield->reserve);finish();
}
inline U32 __cdecl order_targeting(bw::Unit* u,U32 order,bw::Unit* target,U32 x,U32 y,std::uint16_t* error){return rework_fixture::targeting(u,order==115?1:12,target,228,x,y,error);}
inline void rework_feedback_targeting_and_spell_costs(){
    using namespace rework_fixture;begin({123,15,63,85,38});auto archon=unit(63,1,100,100),enemy=unit(9,6,120,100);auto s=rework_combat_v5::state(enemy);s->energy_reserve=44*256;
    std::int32_t damage=256*256;g.normal_hit=false;{rework_combat_v5::DamageScope scope(enemy,archon,106,1,damage);CHECK(damage==375*256);}CHECK(!s->energy_reserve&&s->mark==172);
    auto ghost=unit(1,1,100,100),organic=unit(37,6,120,100);std::uint16_t error=0;const auto flags=raw_value(0,22,37);
    CHECK(rework_combat_v5::order_target_hook(ghost,115,organic,0,0,&error,order_targeting)==1);CHECK(raw_value(0,22,37)==flags);ghost->player=6;CHECK(!rework_combat_v5::order_target_hook(ghost,115,organic,0,0,&error,order_targeting));
    auto queen=unit(45,1,100,100),cc=unit(106,6,120,100);cc->flingy.hitpoints=std::int32_t(effective_max_hp(cc)*7/10);const auto hp=cc->flingy.hitpoints;
    CHECK(!rework_combat_v5::order_target_hook(queen,27,cc,0,0,&error,order_targeting));CHECK(cc->flingy.hitpoints==hp);
    cc->flingy.hitpoints=std::int32_t(effective_max_hp(cc)*8/10);CHECK(!rework_combat_v5::order_target_hook(queen,27,cc,0,0,&error,order_targeting));
    cc->flingy.hitpoints=std::int32_t(effective_max_hp(cc)*4/10);CHECK(rework_combat_v5::order_target_hook(queen,27,cc,0,0,&error,order_targeting));
    ghost->player=1;ghost->energy=200*256;ghost->order=115;{rework_combat_v5::OrderScope scope(ghost);ghost->energy-=100*256;}CHECK(ghost->energy==130*256);
    {rework_combat_v5::OrderScope scope(ghost);}CHECK(ghost->energy==130*256);finish();
}
inline void rework_acid_twelve_ground_lifecycle_and_native_hit(){
    using namespace rework_fixture;begin({86,100,106});auto devourer=unit(62,1,100,100,true),target=unit(43,6,120,100,true);target->acid_spore_count=9;std::fill(std::begin(target->acid_spore_timers),std::end(target->acid_spore_timers),U8(150));
    for(U32 i=0;i<4;i++){auto b=bullet(devourer,target,104);{rework_combat_v5::MissileScope scope(b);target->acid_spore_timers[0]=151;}}
    CHECK(target->acid_spore_count==12);auto acid=rework_combat_v5::acid_state(target);CHECK(rework_combat_v5::extra_acid(*acid)==3);CHECK(target->acid_spore_timers[0]==150);for(U32 i=0;i<acid->extra.size();i++)CHECK(acid->extra[i]==(i<3?225:0));
    target->player=1;pulse(108);CHECK(target->acid_spore_count==12&&rework_combat_v5::extra_acid(*rework_combat_v5::acid_state(target))==3);
    for(U32 frame=116;frame<=1900;frame+=8)pulse(frame);CHECK(target->acid_spore_count==9&&rework_combat_v5::extra_acid(*rework_combat_v5::acid_state(target))==0);
    target->player=6;auto ground=unit(37,6,125,100);auto b=bullet(devourer,ground,104);b->flingy.position={125,100};{rework_combat_v5::MissileScope scope(b);}CHECK(ground->acid_spore_count==1);CHECK(ground->acid_spore_timers[0]==225);
    // One native impact cannot add the same custom ground spore twice.
    {rework_combat_v5::MissileScope scope(b);}CHECK(ground->acid_spore_count==1);
    CHECK(target->acid_spore_count==10);rework_combat_v5::add_spore(target,225,true);CHECK(target->acid_spore_count==11);target->acid_spore_count=0;pulse(1908);CHECK(!rework_combat_v5::extra_acid(*rework_combat_v5::acid_state(target)));
    rework_combat_v5::add_spore(target,225,true);rework_combat_v5::state(target)->mark=9999;rework_combat_v5::created(target);CHECK(!rework_combat_v5::state(target)->mark&&!rework_combat_v5::extra_acid(*rework_combat_v5::acid_state(target)));finish();
}
inline void rework_hallucination_mind_chain_and_native_orders(){
    using namespace rework_fixture;begin({122,147});auto templar=unit(67,1,100,100),target=unit(65,1,120,100);templar->order=148;templar->energy=200*256;multi_fixture::target(templar,target);native_order_calls=0;
    {rework_combat_v5::OrderScope scope(templar,native_cast);HallucinationCreationScope created(true);native_cast(templar);}CHECK(native_order_calls==2&&templar->energy==100*256&&templar->order==3);
    U32 hallucinations=0;living_units([&](bw::Unit* u){if(hallucination(u)){++hallucinations;CHECK(u->death_timer==1350&&rework_combat_v5::state(u)->materialized);}});CHECK(hallucinations==4);
    begin({125,146});auto caster=unit(63,1,100,100);target=unit(37,6,120,100);auto extra=unit(37,6,130,100),too_big=unit(39,6,140,100);caster->energy=200*256;caster->shields=180*256;caster->order=182;multi_fixture::target(caster,target);native_order_calls=0;
    {rework_combat_v5::OrderScope scope(caster,native_cast);native_cast(caster);}CHECK(target->player==1&&extra->player==1&&too_big->player==6);CHECK(caster->energy==50*256&&caster->shields==90*256&&native_order_calls==2);CHECK(caster->order==3&&caster->order_target.unit==target);finish();
}
inline void rework_split_bounce_and_dying_ammunition(){
    using namespace rework_fixture;begin({137,131});auto dragoon=unit(66,1,100,100),primary=unit(37,6,150,100),a=unit(37,6,160,100),b=unit(37,6,170,100);unit(43,6,160,100,true);auto shot=bullet(dragoon,primary,66);shot->flingy.top_speed=100;
    g.bullet_hit_context=true;{rework_combat_v5::MissileScope impact(shot);g.normal_hit=true;std::int32_t damage=20*256;{rework_combat_v5::DamageScope hit(primary,dragoon,66,1,damage);}}
    CHECK(multi_fixture::shots.size()==3&&rework_combat_v5::pending_shots.empty());CHECK(multi_fixture::shots[1].target==a&&multi_fixture::shots[2].target==b);CHECK(multi_fixture::shots[1].x==150&&multi_fixture::shots[1].y==100);
    for(U32 i=1;i<3;i++){auto extra=&multi_fixture::bullets[i];CHECK(rework_combat_v5::projectiles.at(extra).secondary&&rework_combat_v5::projectiles.at(extra).percent==50);{rework_combat_v5::MissileScope impact(extra);std::int32_t amount=20*256;{rework_combat_v5::DamageScope hit(extra->target.unit,dragoon,66,1,amount);CHECK(amount==10*256);}}}CHECK(multi_fixture::shots.size()==3);finish();
    begin({141});auto scarab=unit(85,1,100,100);primary=unit(37,6,110,100);a=unit(37,6,120,100);b=unit(37,6,130,100);shot=bullet(scarab,primary,82);g.bullet_hit_context=true;g.normal_hit=true;
    {rework_combat_v5::MissileScope impact(shot);std::int32_t amount=100*256;{rework_combat_v5::DamageScope hit(primary,scarab,82,1,amount);}}
    CHECK(multi_fixture::shots.size()==3);CHECK(multi_fixture::shots[1].x==a->flingy.position.x&&multi_fixture::shots[2].x==b->flingy.position.x);kill(scarab);pulse(101);CHECK(multi_fixture::shots.size()==3);finish();
    begin({93});auto muta=unit(43,1,100,100,true);primary=unit(43,6,120,100,true);shot=bullet(muta,primary,48);shot->bounces_remaining=2;
    const U32 expected[4]={2700,900,300,100};for(U32 n=0;n<4;n++){if(n)shot->bounces_remaining=U8(3-n);rework_combat_v5::MissileScope impact(shot);CHECK(shot->bounces_remaining==3-n);std::int32_t amount=2700;rework_combat_v5::DamageScope hit(primary,muta,48,n<2 ? 1:n==2 ? 3:9,amount);CHECK(U32(amount/(n<2 ? 1:n==2 ? 3:9))==expected[n]);}finish();
}
inline void rework_medic_rate_network_emergency_and_stim(){
    using namespace rework_fixture;begin({40,50,66,39});auto medic=unit(34,1,100,100),patient=unit(0,1,120,100),a=unit(0,1,125,100),b=unit(0,1,130,100),c=unit(0,1,135,100);medic->order=176;medic->energy=100*256;multi_fixture::target(medic,patient);
    patient->flingy.hitpoints=10*256;a->flingy.hitpoints=b->flingy.hitpoints=c->flingy.hitpoints=10*256;
    {rework_combat_v5::OrderScope scope(medic);patient->flingy.hitpoints+=256;medic->energy-=128;}
    CHECK(patient->flingy.hitpoints==std::int32_t(26*256+128));CHECK(a->flingy.hitpoints==10*256+192&&b->flingy.hitpoints==10*256+192&&c->flingy.hitpoints==10*256);CHECK(medic->energy==100*256-384-10*256);
    game.frame_count=101;const auto hp=patient->flingy.hitpoints;{rework_combat_v5::OrderScope scope(medic);patient->flingy.hitpoints+=256;medic->energy-=128;}CHECK(patient->flingy.hitpoints==hp+384);
    auto marine=unit(0,1,200,100);marine->flingy.hitpoints=30*256;{rework_combat_v5::CommandScope command(1);marine->flingy.hitpoints-=10*256;marine->stim_timer=37;}CHECK(marine->flingy.hitpoints==25*256&&marine->stim_timer==55);
    const auto before=marine->flingy.hitpoints;{rework_combat_v5::CommandScope command(6);}CHECK(marine->flingy.hitpoints==before&&marine->stim_timer==55);finish();
}
inline void rework_nuclear_warning_morph_once_and_reset(){
    using namespace rework_fixture;begin({46,101,55});auto ghost=unit(1,1,100,100),nuke=unit(14,1,100,100);nuke->related=ghost;nuke->order=125;nuke->order_state=4;movement_effects::Image image{};auto sprite=static_cast<bw::SpriteScr*>(nuke->flingy.sprite);sprite->main_image=&image;
    const auto& code=movement_effects::data::kIscript;const auto read16=[&](U32 at){return U32(code[at])|(U32(code[at+1])<<8);};U32 header=0;
    for(U32 at=read16(0);at+4<sizeof(code)&&read16(at)!=65535;at+=4)if(read16(at)==131){header=read16(at+2);break;}
    CHECK(header!=0);const U32 start=read16(header+8+21*2);
    image.image_id=316;image.script.header=std::uint16_t(header);image.script.animation=21;image.script.pos=std::uint16_t(start+2);image.script.wait=125;const auto original=image;
    pulse(100);CHECK(rework_combat_v5::state(nuke)->nuke_adjusted);CHECK(image.script.pos==start+4&&image.script.wait==35);
    for(U32 i=1;i<=36;i++){
        if(image.script.wait)--image.script.wait;
        else if(image.script.pos==start+4){nuke->order_signal|=code[start+5];image.script.pos+=2;}
        pulse(100+i);CHECK(bool(nuke->order_signal&2)==(i==36));
    }
    static_assert(rework_combat_v5::kNuclearWarningFrames==36,"One and a half game seconds");image.script.wait=20;pulse(221);CHECK(image.script.wait==20);
    auto delayed=original;delayed.script.wait=115;CHECK(rework_combat_v5::fixed_nuclear_warning(&delayed));CHECK(delayed.script.wait==25&&delayed.script.pos==start+4);
    auto late=original;late.script.pos=std::uint16_t(start+4);CHECK(rework_combat_v5::fixed_nuclear_warning(&late));CHECK(late.script.wait==0);
    auto bad=original;bad.script.header=0;CHECK(!rework_combat_v5::fixed_nuclear_warning(&bad));CHECK(bad.script.wait==125);
    auto scripted=unit(14,1,150,100);scripted->order=125;scripted->order_state=4;auto original_image=original;static_cast<bw::SpriteScr*>(scripted->flingy.sprite)->main_image=&original_image;pulse(222);CHECK(original_image.script.wait==125);
    auto enemy_ghost=unit(1,6,200,100),enemy_nuke=unit(14,6,200,100);enemy_nuke->related=enemy_ghost;enemy_nuke->order=125;enemy_nuke->order_state=4;auto enemy_image=original;static_cast<bw::SpriteScr*>(enemy_nuke->flingy.sprite)->main_image=&enemy_image;pulse(223);CHECK(enemy_image.script.wait==125);
    rework_combat_v5::created(nuke);image=original;pulse(224);CHECK(image.script.wait==35&&rework_combat_v5::state(nuke)->nuke_adjusted);
    begin({101,55});ghost=unit(1,1,100,100);nuke=unit(14,1,100,100);nuke->related=ghost;nuke->order=125;nuke->order_state=4;image=original;static_cast<bw::SpriteScr*>(nuke->flingy.sprite)->main_image=&image;pulse(100);CHECK(image.script.wait==125);
    auto morph=unit(44,1,300,100),ling=unit(37,1,310,100),enemy=unit(37,6,320,100);ling->flingy.hitpoints=10*256;enemy->flingy.hitpoints=10*256;morph->flags&=~1u;
    rework_combat_v5::transformed(morph,59);pulse(108);CHECK(ling->flingy.hitpoints==10*256);morph->flags|=1;pulse(109);CHECK(ling->flingy.hitpoints==30*256&&enemy->flingy.hitpoints==10*256);
    ling->flingy.hitpoints=10*256;rework_combat_v5::transformed(morph,59);pulse(110);CHECK(ling->flingy.hitpoints==10*256);rework_combat_v5::created(morph);rework_combat_v5::transformed(morph,59);pulse(111);CHECK(ling->flingy.hitpoints==30*256);
    auto siege=unit(30,1,400,100);siege->flingy.top_speed=777;siege->flingy.movement_type=2;siege->flags|=0x80000u;pulse(112);CHECK(siege->flingy.movement_type==0);rework_combat_v5::reset();CHECK(siege->flingy.movement_type==2&&siege->flingy.top_speed==777&&(siege->flags&0x80000u));finish();
}
inline void rework_native_fields_owner_and_air_rules(){
    using namespace rework_fixture;begin({83,103,128});auto defiler=unit(46,1,100,100),victim=unit(37,6,300,300);auto shot=bullet(defiler,victim,59);bw::Unit* swarm=nullptr;
    {rework_combat_v5::MissileScope impact(shot);swarm=unit(202,11,300,300);swarm->death_timer=900;}CHECK(rework_combat_v5::persistent.size()==1);
    auto own_air=unit(43,1,400,300,true),enemy_air=unit(43,6,400,300,true),enemy_ground=unit(37,6,400,300),outside=unit(37,6,500,300);
    CHECK(rework_combat_v5::swarm_protects(own_air,0));CHECK(!rework_combat_v5::swarm_protects(enemy_air,0));CHECK(rework_combat_v5::swarm_protects(enemy_ground,0));CHECK(!rework_combat_v5::swarm_protects(outside,0));CHECK(!rework_combat_v5::swarm_protects(enemy_ground,35));CHECK(!rework_combat_v5::swarm_protects(enemy_ground,84));
    auto corsair=unit(60,1,600,600,true);shot=bullet(corsair,victim,101);bw::Unit* web=nullptr;{rework_combat_v5::MissileScope impact(shot);web=unit(105,11,600,600);web->death_timer=600;}CHECK(web->death_timer==900);
    auto enemy=unit(0,6,650,600),ally=unit(0,1,650,600),air_unit=unit(8,6,650,600,true);CHECK(!rework_combat_v5::allow_primary(enemy)&&!rework_combat_v5::allow_primary(ally)&&rework_combat_v5::allow_primary(air_unit));g.bullet_hit_context=false;CHECK(!rework_combat_v5::damage_allowed(ally,enemy,0,true));CHECK(rework_combat_v5::damage_allowed(ally,enemy,0,false));
    g.bullet_hit_context=true;CHECK(rework_combat_v5::damage_allowed(ally,enemy,0,true));game.frame_count=1001;CHECK(rework_combat_v5::allow_primary(enemy));swarm->order=0;CHECK(!rework_combat_v5::swarm_protects(enemy_ground,0));finish();
}
inline void rework_actual_iscript_layer_cfg_and_stat_weapons(){
    using namespace rework_fixture;begin({58,59,96,97,106,138,111});install();
    CHECK(owner_stat(1,{0,17,58})==original_stat({0,19,58}));CHECK(owner_stat(6,{0,17,58})==130);CHECK(owner_stat(1,{0,19,32})==original_stat({0,17,32}));CHECK(owner_stat(1,{0,17,47})==original_stat({0,19,47}));CHECK(owner_stat(1,{0,19,103})==original_stat({0,17,103}));CHECK(owner_stat(1,{0,17,62})==original_stat({0,19,62}));CHECK(owner_stat(1,{0,19,61})==original_stat({0,17,61}));CHECK(owner_stat(1,{1,14,82})==original_stat({1,14,82})+1);
    std::vector<U8> bytes(std::begin(movement_effects::data::kIscript),std::end(movement_effects::data::kIscript));CHECK(bytes.size()==42933);const auto original=bytes;
    rework_combat_v5::script_transform(bytes.data(),bytes.size());const auto read=[&](std::size_t p){return U32(bytes[p])|(U32(bytes[p+1])<<8);};U32 checked=0;
    for(U32 at=read(0);at+4<bytes.size();at+=4){const auto id=read(at),header=read(at+2);if(id==65535)break;
        if(!rework_combat_v5::in(id,{69,152,354,372,0,357,362}))continue;const bool from_ground=rework_combat_v5::in(id,{69,152,354,372});
        for(const auto pair:{std::pair<U32,U32>{2,3},{5,6},{8,9}}){const auto from=header+8+(from_ground ? pair.first:pair.second)*2,to=header+8+(from_ground ? pair.second:pair.first)*2;CHECK(read(to)==read(from)&&read(to)>0);}
        ++checked;
    }CHECK(checked==7);U32 idle=0,body_header=0,turret_header=0;for(U32 at=read(0);at+4<bytes.size();at+=4){const auto id=read(at),header=read(at+2);if(id==65535)break;if(id==92)body_header=header;if(id==93){turret_header=header;idle=read(header+8+12*2);}}
    CHECK(body_header&&turret_header&&idle&&bytes[idle]==5&&bytes[idle+1]==125);CHECK(read(body_header+8+11*2)==idle&&read(body_header+8+12*2)==idle&&read(turret_header+8+11*2)==idle);CHECK(bytes!=original);const auto once=bytes;rework_combat_v5::script_transform(bytes.data(),bytes.size());CHECK(bytes==once);finish();
}
inline void rework_idle_melee_finishes_native_attack_animation(){
    using namespace rework_fixture;begin();auto dt=unit(61,1,100,100);dt->order=3;
    const auto& code=movement_effects::data::kIscript;const auto read16=[&](U32 at){return U32(code[at])|(U32(code[at+1])<<8);};U32 header=0;
    for(U32 at=read16(0);at+4<sizeof(code)&&read16(at)!=65535;at+=4)if(read16(at)==354){header=read16(at+2);break;}
    CHECK(header);movement_effects::Image image{};image.script.header=std::uint16_t(header);image.script.animation=8;image.script.pos=42810;image.script.wait=5;
    static_cast<bw::SpriteScr*>(dt->flingy.sprite)->main_image=&image;rework_combat_v5::finish_idle_melee_animation(dt);
    CHECK(image.script.animation==12&&image.script.pos==read16(header+32)&&image.script.wait==0);
    image.script.animation=9;dt->order=10;rework_combat_v5::finish_idle_melee_animation(dt);CHECK(image.script.animation==9);
    dt->order=6;dt->flingy.current_speed=1;rework_combat_v5::finish_idle_melee_animation(dt);CHECK(image.script.animation==9);
    dt->order=3;rework_combat_v5::finish_idle_melee_animation(dt);CHECK(image.script.animation==12);
    image.script.animation=9;dt->flingy.current_speed=0;dt->player=6;rework_combat_v5::finish_idle_melee_animation(dt);CHECK(image.script.animation==9);finish();
}
inline void rework_relocation_jump_fixed_recall_and_native_placement(){
    using namespace rework_fixture;begin({134,98,126,143,145});relocation();auto dt=unit(61,1,100,100);dt->order=6;dt->order_target={300,100,nullptr};pulse(100);CHECK(dt->flingy.position.x==196&&dt->order==6&&dt->order_target.x==300);const auto jump=rework_combat_v5::state(dt)->blink_due;CHECK(jump==388);
    dt->order_target.x=400;pulse(101);CHECK(dt->flingy.position.x==196);placement_allowed=false;game.frame_count=400;dt->order_target.x=500;pulse(400);CHECK(dt->flingy.position.x==196&&rework_combat_v5::state(dt)->blink_due==jump);placement_allowed=true;
    auto ling=unit(37,1,100,300),target=unit(0,6,200,300);ling->order=10;ling->flags|=0x8000000u;multi_fixture::target(ling,target);pulse(401);CHECK(ling->flingy.position.x==168&&ling->order==10);
    auto arbiter=unit(71,1,1000,1000,true);arbiter->energy=200*256;arbiter->order=137;arbiter->order_state=1;arbiter->order_timer=0;arbiter->order_target={500,500,nullptr};
    {rework_combat_v5::OrderScope scope(arbiter);arbiter->energy-=150*256;arbiter->order=3;}CHECK(arbiter->energy==125*256);
    auto ally=unit(37,1,500,500),enemy=unit(37,6,510,500),burrowed=unit(37,1,520,500),building=unit(131,1,530,500);burrowed->flags|=0x10u;
    pulse(472);CHECK(ally->flingy.position.x==500);pulse(473);CHECK(ally->flingy.position.x==1000&&ally->flingy.position.y==1000);CHECK(enemy->flingy.position.x==510&&burrowed->flingy.position.x==520&&building->flingy.position.x==530);
    arbiter->flingy.position={1500,1500};auto later=unit(37,1,500,500);pulse(545);CHECK(later->flingy.position.x==1000&&later->flingy.position.y==1000);auto slowed=unit(37,6,1010,1000);pulse(546);CHECK(rework_combat_v5::speed_ratio(slowed)==1);relocation_end();finish();
}
inline void rework_lethal_plague_chain_irradiate_and_brood_count(){
    using namespace rework_fixture;begin({84,102,43,61,82,104});auto defiler=unit(46,1,100,100),target=unit(37,6,120,100);target->flingy.hitpoints=256;auto b=bullet(defiler,target,60);{rework_combat_v5::MissileScope scope(b);target->plague_timer=75;}CHECK(target->plague_timer==112);pulse(101);CHECK(target->flingy.hitpoints==256);target->plague_timer=111;pulse(108);CHECK(target->flingy.hitpoints<=0);
    auto ally=unit(37,1,120,120);ally->flingy.hitpoints=256;b=bullet(defiler,ally,60);{rework_combat_v5::MissileScope scope(b);ally->plague_timer=75;}ally->plague_timer=111;pulse(116);CHECK(ally->flingy.hitpoints<=0);
    auto vessel=unit(9,1,100,300),infected=unit(37,6,120,300),next=unit(37,6,130,300),last=unit(37,6,140,300),fourth=unit(37,6,150,300);b=bullet(vessel,infected,34);{rework_combat_v5::MissileScope scope(b);infected->irradiate_timer=75;}CHECK(infected->irradiate_timer==112);
    rework_combat_v5::death(infected);kill(infected);CHECK(next->irradiate_timer==112);rework_combat_v5::death(next);kill(next);CHECK(last->irradiate_timer==112);rework_combat_v5::death(last);kill(last);CHECK(!fourth->irradiate_timer);
    auto queen=unit(45,1,500,500);target=unit(37,6,520,500);b=bullet(queen,target,57);const auto previous=count;{rework_combat_v5::MissileScope scope(b);auto first=unit(40,1,520,500),second=unit(40,1,530,500);first->death_timer=second->death_timer=1800;kill(target);}CHECK(count==previous+6);CHECK(finishes==8);for(std::size_t i=previous;i<count;i++)CHECK(units[i].death_timer==1800);finish();
}
inline void rework_storm_multiple_centers_and_consume_real_cap(){
    using namespace rework_fixture;begin({144});auto caster=unit(67,1,100,100),target=unit(37,6,130,100);U32 hits=0;
    for(U32 n=0;n<5;n++)for(int x:{120,150}){auto b=bullet(caster,target,84);b->flingy.position={std::int16_t(x),100};{rework_combat_v5::MissileScope scope(b);if(!target->is_under_storm){++hits;target->is_under_storm=1;}}}CHECK(hits==8);finish();
    begin({76,79});auto defiler=unit(46,1,100,100),victim=unit(37,1,120,100);defiler->energy=250*256;defiler->order=145;multi_fixture::target(defiler,victim);CHECK(rework_combat_v5::max_energy_hook(defiler,max200)==65535);
    auto consume=bullet(defiler,victim,61);{rework_combat_v5::MissileScope scope(consume);kill(victim);defiler->energy=65535;defiler->order=3;}auto s=rework_combat_v5::state(defiler);CHECK(U32(defiler->energy)+s->energy_reserve==300*256);const U32 total=U32(defiler->energy)+s->energy_reserve;defiler->energy-=100;pulse(101);CHECK(U32(defiler->energy)+s->energy_reserve==total-100&&defiler->energy==65535);finish();
    for(U32 type:{46u,52u}){
        begin({79});defiler=unit(type,1,100,100);victim=unit(37,1,120,100);defiler->energy=0;consume=bullet(defiler,victim,61);
        {rework_combat_v5::MissileScope scope(consume);kill(victim);defiler->energy=50*256;}
        CHECK(defiler->energy==100*256);{rework_combat_v5::MissileScope repeated(consume);}CHECK(defiler->energy==100*256);finish();
        begin({79});defiler=unit(type,1,100,100);victim=unit(37,1,120,100);defiler->energy=0;consume=bullet(defiler,victim,61);
        {rework_combat_v5::MissileScope invalid(consume);}CHECK(defiler->energy==0&&rework_combat_v5::live(victim));finish();
        begin({79});defiler=unit(type,1,100,100);victim=unit(37,1,120,100);victim->flags|=0x40000000u;defiler->energy=0;consume=bullet(defiler,victim,61);
        {rework_combat_v5::MissileScope illusion(consume);kill(victim);}CHECK(defiler->energy==0);finish();
    }
}
inline void rework_native_script_source_scope_restore(){
    using namespace rework_fixture;begin();auto source=unit(12,1,100,100),target=unit(15,6,120,100),other=unit(0,1,200,100);multi_fixture::target(source,target);rework_combat_v5::script_context_read=script_read;rework_combat_v5::script_context_write=script_write;
    script_context={0,0,1234};script_writes=0;auto b=owner_bullet_create_hook(19,100,100,1,0,source,checked_bullet);CHECK(b&&script_context[0]==0&&script_context[1]==0&&script_context[2]==1234&&script_writes==2);
    script_context={0,0,999};{rework_combat_v5::ScriptSourceScope outer(source);CHECK(script_context[1]==reinterpret_cast<std::size_t>(source));{rework_combat_v5::ScriptSourceScope nested(other);CHECK(script_context[1]==reinterpret_cast<std::size_t>(source));}CHECK(script_context[1]==reinterpret_cast<std::size_t>(source));script_context={111,222,333};}CHECK(script_context[0]==0&&script_context[1]==0&&script_context[2]==999);
    const std::array<std::size_t,3> native={reinterpret_cast<std::size_t>(&other->flingy),reinterpret_cast<std::size_t>(other),555};script_context=native;script_writes=0;{rework_combat_v5::ScriptSourceScope scope(source);}CHECK(script_context==native&&script_writes==0);
    script_context={0,0,777};multi_target::create_bullet=checked_bullet;CHECK(rework_combat_v5::emit(source,target,19,50));CHECK(script_context[1]==0&&script_context[2]==777);finish();
}
inline void rework_goliath_body_weapon_and_ground_suicide_guards(){
    using namespace rework_fixture;begin({56});auto body=unit(3,1,100,100),turret=unit(4,1,100,100),primary=unit(15,6,120,100),extra=unit(15,6,130,100);body->subunit=turret;turret->subunit=body;turret->flags=0x0c110000;turret->flingy.hitpoints=1;turret->order=22;CHECK(rework_combat_v5::can_fire(turret));
    CHECK(original_stat({0,17,3})==130);CHECK(rework_combat_v5::weapon(body,false)==7&&rework_combat_v5::weapon(body,true)==8);bullet(body,primary,7);pulse(100);CHECK(multi_fixture::shots.size()==2&&multi_fixture::shots[1].target==extra&&multi_fixture::shots[1].secondary);finish();
    begin({96});auto scourge=unit(47,1,100,100,true),target=unit(15,6,120,100);auto b=bullet(scourge,target,55);{rework_combat_v5::MissileScope impact(b);kill(scourge);}CHECK(target->flingy.hitpoints==256000-77*256);
    {rework_combat_v5::MissileScope impact(b);}CHECK(target->flingy.hitpoints==256000-77*256);
    scourge=unit(47,1,100,100,true);target=unit(15,6,120,100);b=bullet(scourge,target,55);{rework_combat_v5::MissileScope impact(b);target->flingy.hitpoints-=10*256;}CHECK(target->flingy.hitpoints==256000-10*256);
    target=unit(15,6,120,100);b=bullet(scourge,target,55);b->flags|=1;{rework_combat_v5::MissileScope impact(b);}CHECK(target->flingy.hitpoints==256000);
    target=unit(15,6,120,100);b=bullet(scourge,target,55);target->defensive_matrix_dmg=64000;target->matrix_timer=100;{rework_combat_v5::MissileScope impact(b);target->defensive_matrix_dmg-=1000;}CHECK(target->flingy.hitpoints==256000&&target->defensive_matrix_dmg==63000);
    target=unit(15,6,120,100);b=bullet(scourge,target,55);target->defensive_matrix_dmg=65535;target->matrix_timer=100;auto matrix=rework_combat_v5::matrix_state(target);matrix->reserve=1000;{rework_combat_v5::MissileScope impact(b);matrix->reserve-=100;}CHECK(target->flingy.hitpoints==256000&&matrix->reserve==900);
    scourge=unit(47,1,100,100,true);target=unit(15,6,120,100);b=bullet(scourge,target,55);CHECK(rework_combat_v5::projectiles.at(b).percent==70);{rework_combat_v5::MissileScope impact(b);kill(scourge);std::int32_t amount=110*256;{rework_combat_v5::DamageScope damage(target,nullptr,55,1,amount);CHECK(amount==77*256);}target->flingy.hitpoints-=amount;}CHECK(target->flingy.hitpoints==256000-77*256);finish();
    begin({58,95});auto valk=unit(58,1,100,100,true);target=unit(15,6,120,100);b=bullet(valk,target,103);CHECK(rework_combat_v5::projectiles.at(b).percent==60);
    auto infested=unit(50,1,100,100);target=unit(42,6,120,100,true);b=bullet(infested,target,54);CHECK(rework_combat_v5::projectiles.at(b).percent==70);{rework_combat_v5::MissileScope impact(b);kill(infested);std::int32_t amount=500*256;{rework_combat_v5::DamageScope damage(target,nullptr,54,1,amount);CHECK(amount==350*256);}target->flingy.hitpoints-=amount;}CHECK(target->flingy.hitpoints==256000-350*256);finish();
}
inline void rework_synthetic_native_weapon_factors(){
    using namespace rework_fixture;begin({56});auto body=unit(3,1,100,100),turret=unit(4,1,100,100),primary=unit(15,6,120,100),air_target=unit(42,6,130,100,true);body->subunit=turret;turret->subunit=body;
    CHECK(multi_target::factor(8)==2);bullet(body,primary,7);pulse(100);CHECK(multi_fixture::shots.size()==3);CHECK(multi_fixture::shots[1].weapon==8&&multi_fixture::shots[2].weapon==8&&multi_fixture::shots[1].target==air_target&&multi_fixture::shots[2].target==air_target);finish();
    begin({142});auto scout=unit(70,1,100,100,true);primary=unit(15,6,120,100);air_target=unit(42,6,130,100,true);scout->order=10;multi_fixture::target(scout,primary);CHECK(multi_target::factor(74)==2);pulse(100);CHECK(multi_fixture::shots.size()==2);for(const auto& shot:multi_fixture::shots)CHECK(shot.weapon==74&&shot.target==air_target);finish();
}
inline void rework_bc_dual_triple_counts_once_per_layer(){
    using namespace rework_fixture;begin({57,65});auto bc=unit(12,1,100,100,true),primary=unit(15,6,120,100);unit(15,6,125,100);unit(15,6,130,100);unit(42,6,120,110,true);unit(42,6,125,110,true);unit(42,6,130,110,true);bc->order=10;multi_fixture::target(bc,primary);
    bullet(bc,primary,19);pulse(100);pulse(101);CHECK(multi_fixture::shots.size()==6);U32 ground=0,air=0;std::vector<bw::Unit*> ground_targets,air_targets;
    for(const auto& shot:multi_fixture::shots)if(shot.weapon==19){++ground;ground_targets.push_back(shot.target);}else if(shot.weapon==20){++air;air_targets.push_back(shot.target);}
    CHECK(ground==3&&air==3);std::sort(ground_targets.begin(),ground_targets.end());std::sort(air_targets.begin(),air_targets.end());CHECK(std::unique(ground_targets.begin(),ground_targets.end())==ground_targets.end());CHECK(std::unique(air_targets.begin(),air_targets.end())==air_targets.end());CHECK(rework_combat_v5::pending_shots.empty());finish();
}
inline void rework_dead_caster_spell_scalars_durations_and_yamato(){
    using namespace rework_fixture;
    for(U32 mode=0;mode<3;mode++){
        begin({121});auto caster=unit(67,1,100,100),target=unit(37,6,120,100);auto shot=bullet(caster,target,84);CHECK(rework_combat_v5::projectiles.at(shot).percent==125);
        if(mode==1)kill(caster);if(mode==2)caster->player=6;
        for(U32 tick=0;tick<2;tick++){rework_combat_v5::MissileScope impact(shot);std::int32_t amount=32*256;rework_combat_v5::DamageScope damage(target,mode ? nullptr:caster,84,1,amount);CHECK(amount==40*256);}CHECK(rework_combat_v5::projectiles.at(shot).percent==125);finish();
    }
    begin({121});auto caster=unit(67,6,100,100),target=unit(37,1,120,100);auto shot=bullet(caster,target,84);CHECK(rework_combat_v5::projectiles.at(shot).percent==100);finish();
    begin({62,15});caster=unit(9,1,100,100);target=unit(68,6,120,100);target->energy=100*256;target->shields=100*256;auto target_state=rework_combat_v5::state(target);target_state->energy_reserve=40*256;shot=bullet(caster,target,33);kill(caster);
    {rework_combat_v5::MissileScope impact(shot);target->energy=0;target->shields=0;}CHECK(target->flingy.hitpoints==256000-60*256&&target_state->energy_reserve==0&&target_state->mark==172);finish();
    begin({80,127,149});caster=unit(45,1,100,100);target=unit(37,6,120,100);shot=bullet(caster,target,58);caster->player=6;{rework_combat_v5::MissileScope impact(shot);target->ensnare_timer=75;}CHECK(target->ensnare_timer==112);
    caster=unit(71,1,100,100);shot=bullet(caster,target,83);kill(caster);target->shields=150*256;{rework_combat_v5::MissileScope impact(shot);target->stasis_timer=80;}CHECK(target->stasis_timer==120&&rework_combat_v5::state(target)->stasis_owner==1);target->stasis_timer=0;pulse(101);CHECK(target->shields==50*256&&target->flingy.hitpoints==256000-75*256);finish();
    for(U32 mode=0;mode<3;mode++){
        begin({64});caster=unit(12,1,100,100);target=unit(37,6,150,100);auto a=unit(37,6,160,100),b=unit(37,6,170,100),outside=unit(37,6,220,100),ally=unit(37,1,165,100);shot=bullet(caster,target,30);shot->flingy.position={150,100};shot->flingy.exact_position={38400,25600};shot->flingy.sprite=caster->flingy.sprite;shot->flags=16;rework_combat_v5::get_sprite_position=sprite_get;rework_combat_v5::set_sprite_position=sprite_set;bullet_position={150,100};yamato_targets.clear();
        if(mode==1)kill(caster);if(mode==2)caster->player=6;
        {rework_combat_v5::MissileScope impact(shot,yamato);yamato(shot);}CHECK(yamato_targets.size()==3&&yamato_targets[0]==target&&yamato_targets[1]==a&&yamato_targets[2]==b);CHECK(target->flingy.hitpoints==256000-260*256&&a->flingy.hitpoints==256000-130*256&&b->flingy.hitpoints==256000-130*256);CHECK(outside->flingy.hitpoints==256000&&ally->flingy.hitpoints==256000);
        CHECK(shot->target.unit==target&&shot->target.x==150&&shot->target.y==100&&shot->flingy.position.x==150&&shot->flingy.position.y==100&&shot->flingy.exact_position.x==38400&&shot->flingy.exact_position.y==25600&&shot->flags==16);CHECK(bullet_position[0]==150&&bullet_position[1]==100);CHECK(rework_combat_v5::DamageScope::current_percent==100&&!rework_combat_v5::DamageScope::current_secondary&&!rework_combat_v5::DamageScope::current_primary);CHECK(multi_fixture::shots.size()==1&&rework_combat_v5::pending_shots.empty());
        {rework_combat_v5::MissileScope impact(shot,yamato);}CHECK(yamato_targets.size()==3);finish();
    }
}
inline void rework_spell_recast_native_timer_write_witness(){
    using namespace rework_fixture;
    const auto timer=[](bw::Unit* u,U32 weapon)->U8& {return weapon==58 ? u->ensnare_timer:weapon==60 ? u->plague_timer:u->irradiate_timer;};
    for(const auto pair:{std::pair<U32,U32>{80,58},{84,60},{43,34}}){
        begin({pair.first,61,102,15});auto caster=unit(pair.second==34 ? 9:pair.second==58 ? 45:46,1,100,100),target=unit(37,6,120,100),neighbor=unit(37,6,130,100),untouched=unit(37,6,1000,100),immune=unit(37,6,140,100);immune->flags|=0x4000000u;
        CHECK(pair.second!=34||original_stat({1,16,34})==75);
        for(U32 previous:{0u,1u,75u,112u}){
            timer(target,pair.second)=U8(previous);timer(neighbor,pair.second)=112;timer(untouched,pair.second)=timer(immune,pair.second)=75;
            auto shot=bullet(caster,target,pair.second);{rework_combat_v5::MissileScope impact(shot);CHECK(timer(target,pair.second)==(previous==75 ? 74:previous));CHECK(timer(untouched,pair.second)==74&&timer(immune,pair.second)==74);timer(target,pair.second)=75;timer(neighbor,pair.second)=75;}
            CHECK(timer(target,pair.second)==112&&timer(neighbor,pair.second)==112);CHECK(timer(untouched,pair.second)==75&&timer(immune,pair.second)==75);CHECK(rework_combat_v5::state(target)->mark==172&&rework_combat_v5::state(neighbor)->mark==172);CHECK(!rework_combat_v5::state(untouched)->mark&&!rework_combat_v5::state(immune)->mark);
        }
        timer(target,pair.second)=75;auto shot=bullet(caster,target,pair.second);{rework_combat_v5::MissileScope missed(shot);shot->flags|=1;}CHECK(timer(target,pair.second)==75&&timer(untouched,pair.second)==75);
        shot=bullet(caster,target,pair.second);kill(caster);{rework_combat_v5::MissileScope impact(shot);timer(target,pair.second)=75;}CHECK(timer(target,pair.second)==112);finish();
        begin({pair.first});caster=unit(9,6,100,100);target=unit(37,1,120,100);timer(target,pair.second)=75;shot=bullet(caster,target,pair.second);{rework_combat_v5::MissileScope impact(shot);CHECK(timer(target,pair.second)==75);timer(target,pair.second)=75;}CHECK(timer(target,pair.second)==75);finish();
        begin();caster=unit(9,1,100,100);target=unit(37,6,120,100);timer(target,pair.second)=75;shot=bullet(caster,target,pair.second);{rework_combat_v5::MissileScope impact(shot);CHECK(timer(target,pair.second)==75);timer(target,pair.second)=75;}CHECK(timer(target,pair.second)==75);finish();
        begin({pair.first});caster=unit(9,1,100,100);target=unit(37,6,120,100);timer(target,pair.second)=75;shot=bullet(caster,target,pair.second);{rework_combat_v5::MissileScope impact(shot);CHECK(timer(target,pair.second)==74);target->player=1;}CHECK(timer(target,pair.second)==75);finish();
    }
    // The native max(base,remaining) effects must never multiply an unchanged
    // already-extended timer on a repeated dispatch.
    begin({45,127,124});auto caster=unit(71,1,100,100),target=unit(37,6,120,100);
    for(U32 w:{32u,83u,108u}){target->lockdown_timer=target->stasis_timer=target->maelstrom_timer=200;auto shot=bullet(caster,target,w);{rework_combat_v5::MissileScope impact(shot);}CHECK(target->lockdown_timer==200&&target->stasis_timer==200&&target->maelstrom_timer==200);}finish();
}
inline void rework_native_upgrade_storage_and_shield_beneficiaries();
namespace qa86_valkyrie {
inline U32 fixed_calls=0,ordinary_calls=0;
// Model only the order adapter contract; this is not a live engine test.
inline void __cdecl native_order(bw::Unit* u){
    if(u->order!=11){++ordinary_calls;u->flingy.current_speed=0;return;}
    ++fixed_calls;const auto target=u->order_target.unit;
    const U32 w=raw_value(0,rework_combat_v5::air(target)?19:17,u->unit_id);
    CHECK(w==103&&raw_value(1,3,w)==3);
    const auto direction=multi_target::direction_to(u,target);
    const auto delta=(U32(u->flingy.facing_direction)-direction)&255u;
    if(std::min(delta,256u-delta)>raw_value(1,18,w)){u->order_wait=0;return;}
    u->flingy.flingy_flags|=8;u->ground_cooldown=u->air_cooldown=64;
}
inline U32 __cdecl outside(bw::Unit* u,bw::Unit* target){
    const U32 w=raw_value(0,rework_combat_v5::air(target)?19:17,u->unit_id),range=raw_value(1,5,w);
    return multi_target::distance_sq(u,target)>std::uint64_t(range)*range;
}
inline void begin(){rework_fixture::begin({58});rework_fixture::install();multi_target::outside_range=outside;fixed_calls=ordinary_calls=0;}
inline bw::Unit* ship(bw::Unit* target){
    auto u=rework_fixture::unit(58,1,100,100,true);u->order=10;u->order_state=0;
    u->flingy.current_speed=1536;u->flingy.current_speed_x=-1536;u->flingy.facing_direction=64;
    u->flingy.move_target={20,100,nullptr};multi_fixture::target(u,target);return u;
}
}
inline void rework_valkyrie_backshot_both_layers_and_volley_end(){
    using namespace qa86_valkyrie;
    for(bool air:{false,true}){
        begin();auto target=rework_fixture::unit(air?43:37,6,120,100,air),u=ship(target);
        std::array<U8,64> queued{};void* queue=queued.data();u->order_queue_begin=u->order_queue_end=queue;
        u->energy=1234;const auto move=u->flingy.move_target;
        owner_order_hook(u,native_order);
        CHECK(fixed_calls==1&&ordinary_calls==0&&u->order==10&&u->order_state==1);
        CHECK(u->flingy.current_speed==1536&&u->flingy.current_speed_x==-1536);
        CHECK(u->order_target.unit==target&&u->order_queue_begin==queue&&u->order_queue_end==queue&&u->energy==1234);
        CHECK(u->flingy.move_target.x==move.x&&u->flingy.move_target.y==move.y);
        // StartingAttack covers the initial wait as well as all four salvos.
        for(U32 frame=101;frame<142;frame++){
            game.frame_count=frame;owner_order_hook(u,native_order);
            CHECK(fixed_calls==1&&ordinary_calls==0&&u->flingy.current_speed==1536);
        }
        u->flingy.flingy_flags&=~8u;game.frame_count=142;owner_order_hook(u,native_order);
        CHECK(ordinary_calls==1&&u->flingy.current_speed==0&&!rework_combat_v5::state(u)->valkyrie_backshot);
        CHECK(multi_fixture::shots.empty()); // The adapter adds no extra shots.
        u->order_queue_begin=u->order_queue_end=nullptr;rework_fixture::finish();
    }
}
inline void rework_valkyrie_backshot_guards_angle_and_cancellation(){
    using namespace qa86_valkyrie;
    for(U32 test=0;test<18;test++){
        begin();auto target=rework_fixture::unit(37,6,120,100),u=ship(target);
        switch(test){
        case 0:rework_fixture::ranks[58]=0;break;case 1:u->player=6;break;
        case 2:u->flags|=0x40000000u;break;case 3:u->order=6;break;case 4:u->order=1;break;
        case 5:u->order=14;break;case 6:u->flingy.current_speed=0;break;case 7:u->order_state=1;break;
        case 8:u->air_cooldown=1;break;case 9:u->lockdown_timer=1;break;case 10:u->stasis_timer=1;break;
        case 11:u->maelstrom_timer=1;break;case 12:static_cast<bw::SpriteScr*>(target->flingy.sprite)->visibility_mask=0;break;
        case 13:target->flingy.position.x=3000;break;case 14:target->player=1;break;
        case 15:target->flingy.hitpoints=0;break;case 16:u->order_target.unit=nullptr;break;case 17:u->flingy.flingy_flags|=8;break;
        }
        CHECK(!rework_combat_v5::valkyrie_backshot_order(u,native_order)&&fixed_calls==0);
        rework_fixture::finish();
    }
    for(U32 delta:{0u,32u,33u,128u}){
        begin();auto target=rework_fixture::unit(43,6,120,100,true),u=ship(target);u->flingy.facing_direction=U8(64u-delta);
        owner_order_hook(u,native_order);CHECK(fixed_calls==1&&ordinary_calls==0);
        CHECK(bool(u->flingy.flingy_flags&8u)==(delta<=32)&&u->flingy.current_speed==1536);
        rework_fixture::finish();
    }
    for(U32 test=0;test<6;test++){
        begin();auto target=rework_fixture::unit(37,6,120,100),u=ship(target);owner_order_hook(u,native_order);
        CHECK(rework_combat_v5::state(u)->valkyrie_backshot);
        if(test==0)u->order=6;else if(test==1)target->flingy.hitpoints=0;else if(test==2)++target->minor_unique_index;
        else if(test==3)u->lockdown_timer=1;else if(test==4)game.frame_count+=48;else ++u->minor_unique_index;
        CHECK(!rework_combat_v5::valkyrie_backshot_order(u,native_order));
        CHECK(!rework_combat_v5::state(u)->valkyrie_backshot);rework_fixture::finish();
    }
}
inline void run_rework_combat_v5_groups(){rework_half_armor_native_health_callback();rework_ghost_zero_armor_five_seconds();rework_infantry_percentage_damage();rework_stats_and_repeatable_fractional();rework_medic_actual_pulses_and_lifecycle();rework_projectile_counts_and_moving_orders();rework_emp_storm_and_armor_semantics();rework_mobile_siege_burrow_and_ownership();rework_native_area_replay_and_restoration();rework_matrix_reserve_and_energy_overflow();rework_feedback_targeting_and_spell_costs();rework_acid_twelve_ground_lifecycle_and_native_hit();rework_hallucination_mind_chain_and_native_orders();rework_split_bounce_and_dying_ammunition();rework_medic_rate_network_emergency_and_stim();rework_nuclear_warning_morph_once_and_reset();rework_native_fields_owner_and_air_rules();rework_actual_iscript_layer_cfg_and_stat_weapons();rework_idle_melee_finishes_native_attack_animation();rework_relocation_jump_fixed_recall_and_native_placement();rework_lethal_plague_chain_irradiate_and_brood_count();rework_storm_multiple_centers_and_consume_real_cap();rework_native_script_source_scope_restore();rework_goliath_body_weapon_and_ground_suicide_guards();rework_synthetic_native_weapon_factors();rework_bc_dual_triple_counts_once_per_layer();rework_dead_caster_spell_scalars_durations_and_yamato();rework_spell_recast_native_timer_write_witness();rework_native_upgrade_storage_and_shield_beneficiaries();rework_valkyrie_backshot_both_layers_and_volley_end();rework_valkyrie_backshot_guards_angle_and_cancellation();}
inline void rework_native_upgrade_storage_and_shield_beneficiaries(){
    using namespace rework_fixture;begin({113});install();
    std::array<U8,61*12> levels{};samase::ExtendedArray native_levels{levels.data(),levels.data()+levels.size(),0,0};g.extended=&native_levels;g.extended_count=1;
    levels[15*12+1]=2;game.upgrade_level_sc[1][15]=7;levels[0*12+1]=3;game.upgrade_level_sc[1][0]=1;levels[60*12+1]=4;game.upgrade_level_bw[1][14]=2;
    CHECK(rework_combat_v5::upgrade_level(1,0)==3&&rework_combat_v5::upgrade_level(1,15)==2&&rework_combat_v5::upgrade_level(1,60)==4);
    CHECK(!rework_combat_v5::upgrade_level(12,0)&&!rework_combat_v5::upgrade_level(1,61));g.normal_hit=true;
    auto attacker=unit(0,6,100,100);
    for(const auto id:{66u,78u,64u,162u,0u}){
        auto target=unit(id,1,120,100);target->shields=10*256;std::int32_t damage=10*256;const bool benefits=id==66||id==78;
        {rework_combat_v5::DamageScope scope(target,attacker,0,1,damage);CHECK(levels[15*12+1]==(benefits ? 3:2));CHECK(game.upgrade_level_sc[1][15]==(benefits ? 3:7));}
        CHECK(levels[15*12+1]==2&&game.upgrade_level_sc[1][15]==7);
    }
    auto target=unit(66,6,120,100);target->shields=10*256;levels[15*12+6]=4;game.upgrade_level_sc[6][15]=1;std::int32_t damage=10*256;
    {rework_combat_v5::DamageScope scope(target,attacker,0,1,damage);CHECK(levels[15*12+6]==4&&game.upgrade_level_sc[6][15]==1);}
    target=unit(66,1,120,100);target->shields=10*256;target->flags|=0x40000000u;
    {rework_combat_v5::DamageScope scope(target,attacker,0,1,damage);CHECK(levels[15*12+1]==2&&game.upgrade_level_sc[1][15]==7);}target->flags&=~0x40000000u;
    g.normal_hit=false;{rework_combat_v5::DamageScope scope(target,attacker,30,1,damage);CHECK(levels[15*12+1]==2&&game.upgrade_level_sc[1][15]==7);}g.normal_hit=true;
    levels[15*12+1]=255;{rework_combat_v5::DamageScope scope(target,attacker,0,1,damage);CHECK(levels[15*12+1]==255&&game.upgrade_level_sc[1][15]==255);}CHECK(game.upgrade_level_sc[1][15]==7);levels[15*12+1]=2;
    native_levels.end=levels.data()+1;CHECK(!rework_combat_v5::upgrade_level(1,15));
    {rework_combat_v5::DamageScope scope(target,attacker,0,1,damage);CHECK(levels[15*12+1]==2&&game.upgrade_level_sc[1][15]==7);}
    native_levels.end=levels.data()+levels.size();g.extended_count=0;CHECK(!rework_combat_v5::upgrade_level(1,15));g.extended_count=1;g.extended=nullptr;CHECK(!rework_combat_v5::upgrade_level(1,15));g.extended_count=0;
    CHECK(rework_combat_v5::upgrade_level(1,15)==7);{rework_combat_v5::DamageScope scope(target,attacker,0,1,damage);CHECK(game.upgrade_level_sc[1][15]==8);}CHECK(game.upgrade_level_sc[1][15]==7);
    finish();
}
inline constexpr std::size_t rework_combat_v5_group_count=31;
}
