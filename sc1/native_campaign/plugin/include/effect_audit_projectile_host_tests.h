// Independent offline audit. Public SDK callbacks are mocked; this is not live engine evidence.
#pragma once
namespace host_test {
namespace projectile_audit_fixture {
using namespace multi_fixture;
inline std::vector<U8> dimension_data;
inline void load_dimensions(){
    std::ifstream file("../managed_dat/arr/units.dat",std::ios::binary);CHECK(file.good());file.seekg(0,std::ios::end);const auto n=file.tellg();
    std::vector<U8> bytes(static_cast<std::size_t>(n));file.seekg(0);file.read(reinterpret_cast<char*>(bytes.data()),n);
    bool found=false;for(U32 i=0;i<u32(bytes.data()+12);i++){const auto p=bytes.data()+16+i*12;if(u16(p)!=38)continue;
        const U32 offset=u32(p+4),length=u32(p+8);CHECK(u16(p+2)==1 && length==228*8 && offset+length<=bytes.size());
        dimension_data.assign(bytes.begin()+offset,bytes.begin()+offset+length);dat[0][38]={dimension_data.data(),8,228};found=true;
    }CHECK(found);
}
inline bool range_reject=false,reenter=false;inline U32 nested_calls=0;
inline U32 __cdecl can_attack(bw::Unit* source,bw::Unit* victim,U32 detection){
    CHECK(detection==1);CHECK(source && victim);
    // Ordinary visible units do not need a detector. The prior fixture treated
    // a zero detection mask as invisible even without any cloaking effect.
    if((victim->flags&0x300u) && !(victim->detection_status&(1u<<source->player)))return 0;
    return !(victim->flags&0x04000000u) && !source->lockdown_timer && !source->stasis_timer && !source->maelstrom_timer;
}
inline U32 __cdecl range(bw::Unit*,bw::Unit*){++range_calls;return range_reject ? 1u:0u;}
inline bw::Bullet* __cdecl raw_reenter(U32 weapon,int x,int y,U32 owner,U32 direction,bw::Unit* source){
    if(multi_target::secondary() && reenter){++nested_calls;multi_target::step();}
    return raw(weapon,x,y,owner,direction,source);
}
inline bw::Bullet* __cdecl hooked_reenter(U32 weapon,int x,int y,U32 owner,U32 direction,bw::Unit* source){
    return owner_bullet_create_hook(weapon,x,y,owner,direction,source,raw_reenter);
}
inline U32 hit_damage=0,missile_damage=0,hit_divisor=0;
inline void __cdecl inspect_hit(bw::Unit*,bw::Bullet* bullet,U32 divisor){hit_damage=raw_value(1,14,bullet->weapon_id);hit_divisor=divisor;}
inline void __cdecl inspect_missile(bw::Bullet* bullet){missile_damage=raw_value(1,14,bullet->weapon_id);owner_hit_hook(bullet->target.unit,bullet,3,inspect_hit);CHECK(raw_value(1,14,bullet->weapon_id)==missile_damage);}
}
void projectile_stop_resume_preserves_layer_deadline(){
    using namespace multi_fixture;
    for(U32 stop:{1u,6u,113u}){
        begin(104);auto pair=goliath();auto main=pair.first,turret=pair.second;
        auto ground=unit(37,6,130,100),air=unit(43,6,140,100,true);target(turret,ground);CHECK(primary(turret,7));
        game.frame_count=105;multi_target::step();CHECK(shot_count(8,true)==2);const U32 due=multi_target::track(main)->layer[1].due;
        main->order=static_cast<U8>(stop);game.frame_count=106;multi_target::step();CHECK(!multi_target::track(main)->armed);
        main->order=21;target(turret,air);game.frame_count=107;
        CHECK(!multi_target::allow_primary(8,turret));CHECK(!primary(turret,8));
        game.frame_count=due-1;CHECK(!primary(turret,8));game.frame_count=due;CHECK(primary(turret,8));CHECK(primary(turret,8));
        CHECK(shot_count(8)==4);CHECK(multi_target::track(main)->armed);CHECK(multi_target::track(main)->layer[1].count==2);
    }
}
void projectile_native_behavior_coordinates(){
    using namespace multi_fixture;using namespace projectile_audit_fixture;
    begin(104);load_dimensions();auto pair=goliath();auto turret=pair.second;auto victim=unit(37,6,200,100);target(turret,victim);
    CHECK(original_stat({1,8,7})==2);CHECK(multi_target::emit(pair.first,turret,victim,7)==1);
    const int l=u16(dimension_data.data()+37*8),r=u16(dimension_data.data()+37*8+4);CHECK(l==8 && r==7);
    CHECK(shots.back().x==200-l+(l+r)/4);CHECK(shots.back().y>=95 && shots.back().y<=105);CHECK(shots.back().x!=100);
    CHECK(!g.apply_failure);auto box=multi_target::dimensions(227);CHECK(box.left==u16(dimension_data.data()+227*8));
    CHECK(multi_target::dimensions(228).left==0);dat[0][38].entry_size=2;dat[0][38].entries=912;
    CHECK(multi_target::dimensions(37).left==8);dat[0][38].entry_size=8;dat[0][38].entries=228;
    auto air=unit(43,6,100,0,true);CHECK(multi_target::emit(pair.first,turret,air,8)==2);CHECK(shots.back().x==100 && shots.back().y==95);
    begin(105);auto ship=bc();victim=unit(37,6,180,100);CHECK(original_stat({1,20,19})==75);
    CHECK(multi_target::emit(ship,ship,victim,19)==1);CHECK(shots.back().x==175 && shots.back().y==100);
    victim->flingy.position={100,20};CHECK(multi_target::emit(ship,ship,victim,19)==1);CHECK(shots.back().x==100 && shots.back().y==25);
    CHECK(ship->flingy.facing_direction==0);CHECK(ship->order_target.unit==nullptr);CHECK(!multi_target::secondary());
}
void projectile_owner_morph_recycle_and_subunit_guards(){
    using namespace multi_fixture;begin(104);auto pair=goliath();auto main=pair.first,turret=pair.second;
    auto ground=unit(37,6,130,100);unit(43,6,140,100,true);target(turret,ground);primary(turret,7);multi_target::step();const auto n=shots.size();
    main->player=6;turret->player=6;game.frame_count+=30;multi_target::step();CHECK(shots.size()==n);
    main->player=1;turret->player=1;multi_target::step();CHECK(shots.size()==n && !multi_target::track(main)->armed);
    primary(turret,7);multi_target::step();CHECK(shots.size()==n+3);
    ++main->minor_unique_index;game.frame_count+=30;multi_target::step();CHECK(!multi_target::track(main)->armed);
    main->unit_id=5;CHECK(!multi_target::body(turret));main->unit_id=3;main->subunit=nullptr;CHECK(!multi_target::body(turret));main->subunit=turret;
    turret->player=6;CHECK(!multi_target::gun(main));turret->player=1;turret->subunit=nullptr;CHECK(!multi_target::gun(main));turret->subunit=main;
    primary(turret,7);multi_target::invalidate(turret);CHECK(!multi_target::track(main)->armed);
    main->flags|=0x40u;CHECK(!multi_target::target_ok(main,turret,ground));main->flags&=~0x40u;
    turret->lockdown_timer=1;CHECK(!multi_target::target_ok(main,turret,ground));turret->lockdown_timer=0;
}
void projectile_detection_and_authoritative_range(){
    using namespace multi_fixture;using namespace projectile_audit_fixture;
    begin(105);auto ship=bc(),victim=unit(37,6,130,100);target(ship,victim);multi_target::bind(can_attack,range,hooked);range_reject=false;
    victim->detection_status=0;CHECK(multi_target::target_ok(ship,ship,victim));
    victim->flags|=0x100u;CHECK(!multi_target::target_ok(ship,ship,victim));victim->detection_status=1u<<ship->player;CHECK(multi_target::target_ok(ship,ship,victim));
    victim->detection_status=1u<<6;CHECK(!multi_target::target_ok(ship,ship,victim));victim->flags&=~0x300u;
    range_reject=true;CHECK(!multi_target::target_ok(ship,ship,victim));range_reject=false;
    // The actual API decides edge/bounds, upgrades, minimum range and height.
    // Do not substitute the old fixture's centre-distance geometry in production.
    victim->flingy.position.x=301;CHECK(multi_target::target_ok(ship,ship,victim));
    static_cast<bw::SpriteScr*>(victim->flingy.sprite)->visibility_mask=1u<<6;CHECK(!multi_target::target_ok(ship,ship,victim));
    static_cast<bw::SpriteScr*>(victim->flingy.sprite)->visibility_mask=1u<<1;victim->player=11;CHECK(!multi_target::target_ok(ship,ship,victim));victim->player=6;
    game.alliances[1][6]=1;CHECK(!multi_target::target_ok(ship,ship,victim));game.alliances[1][6]=0;game.alliances[6][1]=1;CHECK(!multi_target::target_ok(ship,ship,victim));
}
void projectile_shared_cycle_reentry_and_pool_failure(){
    using namespace multi_fixture;using namespace projectile_audit_fixture;
    begin(105);auto ship=bc(),a=unit(37,6,130,100);unit(37,6,140,100);unit(43,6,150,100,true);target(ship,a);
    multi_target::bind(can,outside,hooked_reenter);reenter=true;nested_calls=0;primary(ship,19);CHECK(shots.size()==3 && nested_calls==2);CHECK(!multi_target::secondary());
    const auto frame=game.frame_count;auto main_hit=&bullets[0];multi_target::launched(19,ship,main_hit);CHECK(shots.size()==3 && game.frame_count==frame);
    game.frame_count+=30;primary(ship,19);CHECK(shots.size()==6);CHECK(ship->order_target.unit==a && ship->order==10);reenter=false;
    begin(104);auto pair=goliath();a=unit(37,6,130,100);unit(43,6,140,100,true);target(pair.second,a);primary(pair.second,7);
    failures=1;multi_target::step();CHECK(shot_count(8,true)==1);const auto count_before=shots.size();multi_target::step();CHECK(shots.size()==count_before);
    game.frame_count=multi_target::track(pair.first)->layer[1].due;multi_target::step();CHECK(shot_count(8,true)==3);CHECK(pair.second->order_target.unit==a);
    const auto unit_track=existing_track(pair.second);CHECK(unit_track);CHECK(!unit_track->cooldown[1].launched); // synthetic missiles do not reset fractional primary clock
}
void projectile_hit_owner_and_lifetime_scopes(){
    using namespace multi_fixture;using namespace projectile_audit_fixture;
    begin(104);auto s=g.growth;s.talent_bits[0]|=1u<<25;s.completed_phase=2;CHECK(apply_snapshot(nullptr,s));auto pair=goliath();auto victim=unit(37,6,130,100);target(pair.second,victim);auto bullet=primary(pair.second,7);
    CHECK(bullet && bullet->parent==pair.first);CHECK(shots[0].damage==15);CHECK(raw_value(1,14,7)==12);
    owner_hit_hook(victim,bullet,2,inspect_hit);CHECK(hit_damage==15 && hit_divisor==2 && raw_value(1,14,7)==12);
    // A projectile retains firing player after parent death, transfer or reuse.
    pair.first->flingy.hitpoints=0;owner_missile_hook(bullet,inspect_missile);CHECK(missile_damage==15 && hit_damage==15 && hit_divisor==3);
    pair.first->flingy.hitpoints=25600;pair.first->player=6;++pair.first->minor_unique_index;owner_hit_hook(victim,bullet,1,inspect_hit);CHECK(hit_damage==15);
    bullet->parent=nullptr;owner_hit_hook(victim,bullet,1,inspect_hit);CHECK(hit_damage==15);
    bullet->player=6;owner_hit_hook(victim,bullet,1,inspect_hit);CHECK(hit_damage==12);bullet->player=11;owner_missile_hook(bullet,inspect_missile);CHECK(missile_damage==12);
    CHECK(raw_value(1,14,7)==12 && !g.normal_hit && !g.elite_hit && g.hit_bonus==0 && g.hit_source==nullptr);
}
void run_effect_audit_projectile_groups(){
    projectile_stop_resume_preserves_layer_deadline();projectile_native_behavior_coordinates();projectile_owner_morph_recycle_and_subunit_guards();
    projectile_detection_and_authoritative_range();projectile_shared_cycle_reentry_and_pool_failure();projectile_hit_owner_and_lifetime_scopes();
}
}
