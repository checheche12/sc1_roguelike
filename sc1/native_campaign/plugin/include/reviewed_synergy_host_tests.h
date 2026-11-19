#pragma once
// Included inside host_test. Exercise each pair with both individual talents as controls.
namespace reviewed_synergy_tests {
using namespace rework_fixture;
namespace c=rework_combat_v5;
inline void begin_pair(U32 mask,U32 a,U32 b){
    qa9_fixture::begin({});ranks[a]=mask&1;ranks[b]=(mask>>1)&1;
}
inline void rift(U32 mask){
    begin_pair(mask,143,145);relocation();
    auto caster=unit(71,1,1000,1000,true);caster->order=137;caster->order_state=1;caster->order_timer=0;
    caster->order_target={500,500,nullptr};caster->energy=200*256;
    {c::OrderScope cast(caster);caster->energy-=150*256;caster->order=3;}
    auto expiry=[](){U32 end=0,count_=0;for(const auto& field:c::persistent)if(field.kind==143){end=field.until;++count_;}CHECK(count_<=1);return end;};
    const auto initial=expiry();CHECK(bool(initial)==bool(mask&1));pulse(148);CHECK(expiry()==initial);
    auto a=unit(37,1,500,500);auto b=unit(37,1,510,510);auto enemy=unit(37,6,1050,1010);
    placement_allowed=false;pulse(196);CHECK(expiry()==initial&&a->flingy.position.x==500);
    placement_allowed=true;pulse(244);
    CHECK((a->flingy.position.x==1000)==bool(mask&2));CHECK((b->flingy.position.x==1000)==bool(mask&2));
    CHECK(expiry()==(mask==3?244+talent_power::v5(143,72):initial));
    if(mask==3)CHECK(c::state(enemy)->slow_ends[2]==expiry());
    qa9_fixture::end();
}
inline void medic(U32 mask){
    begin_pair(mask,41,50);auto m=unit(34,1,100,100),p=unit(0,1,135,100);
    p->flingy.hitpoints=int(effective_max_hp(p)/4);auto hp=p->flingy.hitpoints;m->energy=100*256;
    auto shot=bullet(m,p,102);{c::MissileScope hit(shot);}
    CHECK(p->flingy.hitpoints==std::min(int(effective_max_hp(p)),hp+(mask==3?int(talent_power::v5(50,15*256)):0)));
    CHECK(m->energy==(mask==3?90:100)*256);
    auto paid=m->energy;{c::MissileScope repeat(shot);}CHECK(m->energy==paid);
    if(mask==3){
        auto next=unit(0,1,145,100);next->flingy.hitpoints=256;
        auto cast=bullet(m,next,102);{c::MissileScope hit(cast);}CHECK(next->flingy.hitpoints==256);
        game.frame_count+=600;m->energy=9*256;cast=bullet(m,next,102);{c::MissileScope hit(cast);}CHECK(next->flingy.hitpoints==256);
    }
    qa9_fixture::end();
}
inline void lethal(bw::Unit* ghost,bw::Unit* victim){
    std::int32_t amount=500*256;g.normal_hit=true;
    {c::DamageScope impact(victim,ghost,2,1,amount);kill(victim);}g.normal_hit=false;
}
inline void ghost(U32 mask){
    begin_pair(mask,49,63);auto ghost_=unit(1,1,400,400),victim=unit(37,6,430,400);
    auto shot=bullet(ghost_,victim,32);{c::MissileScope hit(shot);victim->lockdown_timer=70;}
    victim->lockdown_timer=27;auto state_=c::state(victim);state_->lockdown_reserve=270;
    victim->flingy.hitpoints=int(effective_max_hp(victim)/5);
    auto next=unit(37,6,480,400);auto before=multi_fixture::next_bullet;lethal(ghost_,victim);
    CHECK(multi_fixture::next_bullet==before+(mask==3?1:0));
    if(mask==3){
        auto transfer=&multi_fixture::bullets[before];CHECK(transfer->target.unit==next);
        {c::MissileScope hit(transfer);next->lockdown_timer=131;}
        CHECK(next->lockdown_timer==255&&c::state(next)->lockdown_reserve==42);
        CHECK(!c::state(next)->direct_lock_caster.p);auto fresh=unit(37,6,490,400);
        next->flingy.hitpoints=256;before=multi_fixture::next_bullet;lethal(ghost_,next);CHECK(multi_fixture::next_bullet==before&&!fresh->lockdown_timer);
        shot=bullet(ghost_,fresh,32);{c::MissileScope hit(shot);fresh->lockdown_timer=60;}
        auto other=unit(1,1,420,415);unit(37,6,500,400);fresh->flingy.hitpoints=256;
        before=multi_fixture::next_bullet;lethal(other,fresh);CHECK(multi_fixture::next_bullet==before);
    }
    qa9_fixture::end();
}
inline void guardian(U32 mask){
    begin_pair(mask,88,94);auto src=unit(44,1,400,400,true),victim=unit(37,6,450,400);
    auto nearby_enemy=unit(37,6,465,400),fly=unit(43,6,462,400,true),outside=unit(37,6,500,400);
    c::ordinary_hit(src,victim,256,46,false);
    CHECK(c::state(victim)->slow_ends[0]==(mask&2?220u:0u));
    CHECK(c::state(nearby_enemy)->slow_ends[0]==(mask==3?148u:0u));
    CHECK(!c::state(fly)->slow_ends[0]&&!c::state(outside)->slow_ends[0]);
    if(mask==3){c::mark_slow(nearby_enemy,50,120,94);c::ordinary_hit(src,victim,256,46,false);CHECK(c::state(nearby_enemy)->slow_ends[0]==220);}
    qa9_fixture::end();
}
inline void ling(U32 mask){
    begin_pair(mask,190,98);relocation();auto src=unit(37,1,100,300),victim=unit(0,6,200,300);src->order=10;
    src->flags|=0x8000000u;multi_fixture::target(src,victim);pulse(100);
    CHECK((src->flingy.position.x==168)==bool(mask&2));
    c::ordinary_hit(src,victim,256,40,false);
    CHECK(c::state(victim)->erosion==(mask&1?(mask==3?66u:33u):0u));
    auto initial=c::state(victim)->erosion;c::ordinary_hit(src,victim,256,40,false);
    CHECK(c::state(victim)->erosion==initial+(mask&1?33u:0u));
    if(mask==3){
        src->flingy.position.x=100;c::state(src)->leap_due=0;multi_fixture::target(src,victim);pulse(150);
        game.frame_count=175;c::ordinary_hit(src,victim,256,40,false);CHECK(c::state(victim)->erosion==132);
    }
    qa9_fixture::end();
}
inline void recharge(U32 mask){
    begin_pair(mask,114,323);auto caster=unit(67,1,300,300),p=unit(65,1,320,300);
    auto track=track_unit(p);track->last_damage_frame=100;p->shields=0;
    phase_echo_cast(caster,142);auto base_shields=p->shields;CHECK(bool(base_shields)==bool(mask&2));
    pulse(171);CHECK(p->shields==base_shields);pulse(172);CHECK((p->shields>base_shields)==(mask==3));
    if(mask==3){{DamageObservationScope hit(p,6);p->shields-=256;}CHECK(!track->echo_recharge);auto after=p->shields;
        pulse(315);CHECK(p->shields==after);pulse(316);CHECK(p->shields>after);}
    qa9_fixture::end();
}
inline void corsair(U32 mask){
    begin_pair(mask,197,135);auto ship=unit(60,1,100,100,true),target_=unit(43,6,180,100,true);
    auto close=unit(43,6,220,100,true),second=unit(43,6,240,100,true),ground=unit(37,6,190,100);
    target_->flingy.hitpoints=10000*256;
    for(U32 i=1;i<=6;++i){game.frame_count=100+i;c::ordinary_hit(ship,target_,256,100,false);}
    CHECK(c::state(target_)->slow_ends[1]==(mask&2?104+talent_power::v5(135,48):0u));
    CHECK(c::state(close)->slow_ends[1]==(mask==3?c::state(target_)->slow_ends[1]:0u));
    CHECK(!c::state(second)->slow_ends[1]&&!c::state(ground)->slow_ends[1]);
    if(mask==3){
        game.frame_count=107;c::state(ship)->focus_hits=5;c::state(close)->slow_ends[1]=0;g.normal_hit=true;
        std::int32_t amount=10000*256;{c::DamageScope impact(target_,ship,100,1,amount);kill(target_);}g.normal_hit=false;
        CHECK(c::state(close)->slow_ends[1]==c::state(target_)->slow_ends[1]);
    }
    qa9_fixture::end();
}
}
inline void run_reviewed_synergy_groups(){
    for(U32 mask=0;mask<4;++mask){
        using namespace reviewed_synergy_tests;
        rift(mask);medic(mask);ghost(mask);guardian(mask);ling(mask);recharge(mask);corsair(mask);
    }
}
