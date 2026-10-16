// Offline exercise of the production multi_target_runtime and owner bullet hook.
namespace host_test {
namespace multi_fixture {
struct Shot {U32 weapon,owner,frame;bw::Unit* spawner;bw::Unit* target;U32 damage;bool secondary;int x,y;};
inline std::vector<Shot> shots;
inline std::array<bw::Bullet,4096> bullets{};
inline std::array<bw::SpriteScr,1900> sprites{};
inline U32 next_bullet=0, failures=0, can_calls=0, range_calls=0;
inline bool fail_all=false;
inline U32 __cdecl can(bw::Unit* source,bw::Unit* target,U32 detection){
    ++can_calls;CHECK(detection==1);CHECK(source && target);
    return target->detection_status && !(target->flags&0x04000000u) && !source->lockdown_timer && !source->stasis_timer && !source->maelstrom_timer ? 1u : 0u;
}
inline U32 __cdecl outside(bw::Unit* source,bw::Unit* target){
    ++range_calls;const auto weapon=multi_target::weapon_for(source,multi_target::flying(target));
    const U32 range=raw_value(1,5,weapon);
    return multi_target::distance_sq(source,target)>std::uint64_t(range)*range ? 1u : 0u;
}
inline bw::Bullet* __cdecl raw(U32 weapon,int x,int y,U32 owner,U32 direction,bw::Unit* spawner){
    CHECK(weapon<130 && direction<256);
    CHECK(spawner->order_target.unit!=nullptr);
    if(fail_all || failures){if(failures)--failures;return nullptr;}
    CHECK(next_bullet<bullets.size());auto& b=bullets[next_bullet++];b={};
    b.weapon_id=static_cast<U8>(weapon);b.player=static_cast<U8>(owner);b.parent=multi_target::body(spawner);
    b.target=spawner->order_target;
    shots.push_back({weapon,owner,game.frame_count,spawner,b.target.unit,raw_value(1,14,weapon),multi_target::secondary(),x,y});
    return &b;
}
inline bw::Bullet* __cdecl hooked(U32 weapon,int x,int y,U32 owner,U32 direction,bw::Unit* source){
    return owner_bullet_create_hook(weapon,x,y,owner,direction,source,raw);
}
inline void begin(U32 bit){
    reset();multi_target::reset();shots.clear();next_bullet=failures=can_calls=range_calls=0;fail_all=false;
    multi_target::bind(can,outside,hooked);GrowthSnapshot s{};s.talent_bits[bit/32]=1u<<(bit%32);s.completed_phase=1;
    CHECK(apply_snapshot(nullptr,s));g.applied=true;game.frame_count=100;
}
inline bw::Unit* unit(U32 id,U32 owner,int x,int y,bool air=false){
    auto u=add(id,owner,x,y,256000);CHECK(u!=nullptr);u->detection_status=0xffffffffu;u->flags=1u|(air ? 4u : 0u);auto& sprite=sprites[static_cast<std::size_t>(u-units.data())];sprite={};sprite.visibility_mask=0xff;u->flingy.sprite=&sprite;return u;
}
inline void target(bw::Unit* source,bw::Unit* destination){source->order_target.unit=destination;source->order_target.x=destination->flingy.position.x;source->order_target.y=destination->flingy.position.y;}
inline bw::Unit* bc(){auto u=unit(12,1,100,100,true);u->order=10;return u;}
inline std::pair<bw::Unit*,bw::Unit*> goliath(){auto main=unit(3,1,100,100),turret=unit(4,1,100,100);main->subunit=turret;turret->subunit=main;main->order=21;turret->order=22;return {main,turret};}
inline bw::Bullet* primary(bw::Unit* source,U32 weapon){return hooked(weapon,source->flingy.position.x,source->flingy.position.y,source->player,source->flingy.facing_direction,source);}
inline U32 shot_count(U32 weapon,bool only_secondary=false){U32 n=0;for(const auto& shot:shots)if(shot.weapon==weapon && (!only_secondary || shot.secondary))++n;return n;}
}
void multi_bc_targets_and_original_weapon_damage(){
    using namespace multi_fixture;begin(105);auto source=bc();auto a=unit(37,6,130,100),b=unit(37,6,140,100),c=unit(43,6,150,100,true),d=unit(43,6,160,100,true);
    target(source,a);const auto saved=source->order_target;auto hit=primary(source,19);CHECK(hit!=nullptr);CHECK(shots.size()==3);
    CHECK(shots[0].target==a && shots[1].target==b && shots[2].target==c);CHECK(shot_count(19)==2 && shot_count(20)==1);
    CHECK(source->order_target.unit==saved.unit && source->order_target.x==saved.x && source->order_target.y==saved.y);
    CHECK(source->ground_cooldown==0 && source->air_cooldown==0 && source->order==10);CHECK(!multi_target::secondary());
    for(const auto& shot:shots){CHECK(shot.owner==1 && shot.spawner==source);CHECK(shot.damage==25);CHECK(shot.target!=d);}
    CHECK(a->flingy.hitpoints==256000 && b->flingy.hitpoints==256000 && c->flingy.hitpoints==256000); // no parallel direct-damage path
    const auto before=shots.size();multi_target::launched(19,source,hit);CHECK(shots.size()==before); // duplicate notification, same cycle
    game.frame_count+=30;target(source,c);primary(source,20);CHECK(shots.size()==6);CHECK(shots[3].weapon==20 && shots[4].weapon==19 && shots[5].weapon==19);
    begin(105);source=bc();a=unit(37,6,130,100);target(source,a);primary(source,19);CHECK(shots.size()==1);
    b=unit(37,6,140,100);game.frame_count+=30;primary(source,19);CHECK(shots.size()==3);CHECK(shots.back().target==b);
    c=unit(37,6,150,100);game.frame_count+=30;primary(source,19);CHECK(shots.size()==6 && shot_count(20)==0); // all three may share a layer
}
void multi_target_detection_range_owner_and_status(){
    using namespace multi_fixture;begin(105);auto source=bc(),a=unit(37,6,130,100);target(source,a);
    auto invisible=unit(37,6,101,100);invisible->detection_status=0;
    auto fog=unit(37,6,101,101);static_cast<bw::SpriteScr*>(fog->flingy.sprite)->visibility_mask=0;
    auto missing_sprite=unit(37,6,101,102);missing_sprite->flingy.sprite=nullptr;
    auto invincible=unit(37,6,102,100);invincible->flags|=0x04000000u;
    auto neutral=unit(37,11,103,100);auto friendly=unit(37,1,104,100);auto distant=unit(37,6,1000,100);
    auto dead=unit(37,6,105,100);dead->flingy.hitpoints=0;
    primary(source,19);CHECK(shots.size()==1 && can_calls>0 && range_calls>0);
    CHECK(!multi_target::target_ok(source,source,fog) && !multi_target::target_ok(source,source,missing_sprite));
    for(auto blocked:{0x8u,0x20u,0x40u,0x400u,0x8000u,0x40000000u}){source->flags|=blocked;CHECK(!multi_target::target_ok(source,source,a));source->flags&=~blocked;}
    source->lockdown_timer=1;CHECK(!multi_target::target_ok(source,source,a));source->lockdown_timer=0;
    source->stasis_timer=1;CHECK(!multi_target::target_ok(source,source,a));source->stasis_timer=0;
    source->maelstrom_timer=1;CHECK(!multi_target::target_ok(source,source,a));source->maelstrom_timer=0;
    CHECK(!multi_target::target_ok(source,source,neutral) && !multi_target::target_ok(source,source,friendly) && !multi_target::target_ok(source,source,distant));
    source->player=6;CHECK(!multi_target::enabled(source));source->player=11;CHECK(!multi_target::enabled(source));source->player=1;
    source->unit_id=23;CHECK(!multi_target::enabled(source));source->unit_id=12;
    g.growth.talent_bits[3]=0;CHECK(!multi_target::enabled(source));g.growth.talent_bits[3]=1u<<9;
    const auto thread=g.game_thread.load();g.game_thread=0;CHECK(!multi_target::enabled(source));g.game_thread=thread;
    auto game_callback=g.game;g.game=nullptr;CHECK(!multi_target::enabled(source));g.game=game_callback;
}
void multi_goliath_independent_clocks_and_bundle(){
    using namespace multi_fixture;begin(104);auto [main,turret]=goliath();auto ground=unit(37,6,130,100);target(main,ground);target(turret,ground);
    CHECK(original_stat({0,17,3})==130 && original_stat({0,19,3})==130);CHECK(multi_target::factor(7)==1 && multi_target::factor(8)==2);
    primary(turret,7);multi_target::step();CHECK(shots.size()==1);
    game.frame_count=105;auto air=unit(43,6,130,100,true);multi_target::step();CHECK(shot_count(8,true)==2);
    CHECK(shots[1].target==air && shots[2].target==air && shots[1].spawner==turret);CHECK(bullets[1].parent==main && bullets[2].parent==main);
    CHECK(turret->order_target.unit==ground && main->order_target.unit==ground);
    const auto t=multi_target::track(main);CHECK(t->layer[0].due==122 && t->layer[1].due==127);
    multi_target::step();CHECK(shots.size()==3);
    game.frame_count=121;primary(turret,7);CHECK(shot_count(7)==2); // vanilla -1 jitter is preserved
    CHECK(t->layer[1].due==127);game.frame_count=126;multi_target::step();CHECK(shot_count(8,true)==2);
    game.frame_count=127;multi_target::step();CHECK(shot_count(8,true)==4 && shot_count(7)==2);
    // Switching primary layer cannot duplicate the synthetic Hellfire bundle.
    target(turret,air);game.frame_count=128;CHECK(primary(turret,8)==nullptr);CHECK(shot_count(8)==4);
    game.frame_count=149;CHECK(primary(turret,8)!=nullptr);CHECK(primary(turret,8)!=nullptr);CHECK(shot_count(8)==6);
    CHECK(t->layer[1].count==2 && t->layer[1].due==171);multi_target::step();CHECK(shot_count(8)==6);
    CHECK(shot_count(7,true)==1); // opposite ground layer uses its own expired deadline
    const auto size=shots.size();multi_target::step();CHECK(shots.size()==size);
    // The natural primary was never synthesized by the frame callback.
    CHECK(shots[3].secondary==false);
}
void multi_stop_move_target_loss_and_identity(){
    using namespace multi_fixture;
    for(auto order:{1u,6u,113u}){begin(104);auto [main,turret]=goliath();auto a=unit(37,6,130,100);unit(43,6,130,100,true);target(main,a);target(turret,a);primary(turret,7);main->order=static_cast<U8>(order);multi_target::step();CHECK(shots.size()==1);CHECK(!multi_target::track(main)->armed);}
    begin(104);auto [main,turret]=goliath();auto a=unit(37,6,130,100);unit(43,6,130,100,true);target(main,a);target(turret,a);primary(turret,7);
    a->detection_status=0;multi_target::step();CHECK(shots.size()==1);a->detection_status=0xffffffffu;
    a->flingy.hitpoints=0;multi_target::step();CHECK(shots.size()==1);a->flingy.hitpoints=256000;
    ++main->minor_unique_index;multi_target::step();CHECK(shots.size()==1 && !multi_target::track(main)->armed);
    primary(turret,7);CHECK(multi_target::track(main)->armed);main->player=6;turret->player=6;multi_target::step();CHECK(shots.size()==2);
    main->player=1;turret->player=1;multi_target::step();CHECK(shots.size()==2 && !multi_target::track(main)->armed);
    turret->subunit=nullptr;CHECK(multi_target::body(turret)==nullptr && multi_target::gun(main)==nullptr);
}
void multi_failure_restoration_and_no_recursion(){
    using namespace multi_fixture;begin(105);auto source=bc(),a=unit(37,6,130,100);unit(43,6,140,100,true);unit(43,6,150,100,true);target(source,a);
    const auto saved=source->order_target;failures=1;CHECK(primary(source,19)==nullptr);CHECK(shots.empty());
    CHECK(primary(source,19)!=nullptr && shots.size()==3);CHECK(source->order_target.unit==saved.unit && source->order_target.x==saved.x && source->order_target.y==saved.y);
    CHECK(!multi_target::secondary());CHECK(shots[1].secondary && shots[2].secondary);CHECK(shots.size()==3); // hooked children did not expand
    begin(104);auto [main,turret]=goliath();a=unit(37,6,130,100);unit(43,6,140,100,true);target(main,a);target(turret,a);primary(turret,7);fail_all=true;multi_target::step();
    CHECK(shots.size()==1 && multi_target::track(main)->layer[1].due==122);fail_all=false;game.frame_count=101;multi_target::step();CHECK(shots.size()==1);
    game.frame_count=122;multi_target::step();CHECK(shots.size()==3);CHECK(turret->order_target.unit==a && !multi_target::secondary());
    multi_target::reset();CHECK(multi_target::tracks.empty() && !multi_target::secondary());
}
void multi_cooldown_status_and_direction(){
    using namespace multi_fixture;begin(104);auto [main,turret]=goliath();CHECK(multi_target::period(turret,7)==22);
    turret->acid_spore_count=2;CHECK(multi_target::period(turret,7)==28);turret->acid_spore_count=0;
    turret->stim_timer=1;CHECK(multi_target::period(turret,7)==11);turret->flags|=0x20000000u;CHECK(multi_target::period(turret,7)==11);
    turret->ensnare_timer=1;CHECK(multi_target::period(turret,7)==11);turret->stim_timer=0;CHECK(multi_target::period(turret,7)==22);
    turret->flags&=~0x20000000u;CHECK(multi_target::period(turret,7)==27);
    auto north=unit(37,6,100,90),east=unit(37,6,110,100),south=unit(37,6,100,110),west=unit(37,6,90,100);
    CHECK(multi_target::direction_to(main,north)==0 && multi_target::direction_to(main,east)==64 && multi_target::direction_to(main,south)==128 && multi_target::direction_to(main,west)==192);
    for(auto order:{8u,10u,11u,12u,14u,21u,22u,107u,152u,157u,158u,159u})CHECK(multi_target::attack_order(order));
    for(auto order:{0u,1u,6u,113u,141u,145u,187u})CHECK(!multi_target::attack_order(order));
}
void run_multi_target_groups(){
    multi_bc_targets_and_original_weapon_damage();multi_target_detection_range_owner_and_status();multi_goliath_independent_clocks_and_bundle();
    multi_stop_move_target_loss_and_identity();multi_failure_restoration_and_no_recursion();multi_cooldown_status_and_direction();
}
} // namespace host_test
