#pragma once
// Real production hooks with synthetic units/callbacks; no game execution.
namespace host_test {
inline constexpr std::size_t spell_caster_lifetime_group_count=6;
namespace spell_lifetime_fixture {
inline bw::Unit* expected=nullptr;inline U32 calls=0,owner=1;inline std::int32_t amount=0;
inline void begin(std::initializer_list<U32> talents={}){qa9_fixture::begin(talents);expected=nullptr;calls=0;owner=1;amount=0;}
inline void record(bw::Unit* target,std::int32_t damage,bw::Unit* source,U32 player){
    CHECK(source==expected);CHECK(player==owner);
    // Models the native sprite requirement exposed by the mission 508 dump.
    CHECK(!source||(source->order&&source->flingy.hitpoints>0&&source->flingy.sprite));
    ++calls;amount=damage;target->flingy.hitpoints-=damage;
}
inline void __cdecl hp(bw::Unit* target,std::int32_t damage,bw::Unit* source,U32 player,U32){record(target,damage,source,player);}
inline void __cdecl weapon(bw::Unit* target,std::int32_t damage,U8,U32,U8,bw::Unit* source,U32 player){record(target,damage,source,player);}
inline void __cdecl missile(bw::Bullet* b){combat_effects::weapon_damage(b->target.unit,256,b->weapon_id,1,0,b->parent,b->player,weapon);}
// Alive, removed, reused by the same unit type/owner, captured, missing sprite.
inline void change(bw::Unit* source,U32 mode){
    if(mode==1){kill(source);source->flingy.sprite=nullptr;}
    if(mode==2)++source->minor_unique_index;
    if(mode==3)source->player=6;
    if(mode==4)source->flingy.sprite=nullptr;
    expected=mode ? nullptr:source;
}
}
inline void spell_irradiate_propagation_caster_lifetime(){
    using namespace rework_fixture;using namespace spell_lifetime_fixture;
    for(U32 mode=0;mode<5;mode++){
        spell_lifetime_fixture::begin({61});auto caster=unit(9,1,600,900),root=unit(37,6,1000,1000),child=unit(37,6,1100,1000);
        root->irradiate_timer=75;root->irradiated_by=caster;root->irradiate_player=1;
        rework_combat_v5::irradiation::attach(root,caster,1);change(caster,mode);
        if(mode)root->irradiated_by=nullptr; // Native death cleanup must not be undone by propagation.
        kill(root);rework_combat_v5::irradiation::on_death(root);
        CHECK(child->irradiate_timer==75);CHECK(child->irradiated_by==expected);CHECK(child->irradiate_player==1);
        auto victim=unit(42,6,1100,1020,true);const auto before=victim->flingy.hitpoints;
        combat_effects::weapon_damage(victim,256,34,1,0,child->irradiated_by,child->irradiate_player,weapon);
        CHECK(calls==1&&victim->flingy.hitpoints==before-512);qa9_fixture::end();
    }
}
inline void spell_native_damage_boundaries(){
    using namespace rework_fixture;using namespace spell_lifetime_fixture;
    for(U32 mode=0;mode<6;mode++){
        spell_lifetime_fixture::begin();auto caster=unit(9,1,100,100),target=unit(42,6,200,100,true);
        if(mode==1){kill(caster);caster->flingy.sprite=nullptr;}
        if(mode==2)caster->flingy.hitpoints=0;
        if(mode==3)caster->order=0;
        if(mode==4)caster->flingy.sprite=nullptr;
        if(mode==5)caster->player=6;
        expected=mode ? nullptr:caster;
        combat_effects::weapon_damage(target,256,34,1,0,caster,1,weapon);CHECK(calls==1&&amount==256);
        owner_damage_hook(target,128,caster,1,1,hp);CHECK(calls==2&&amount==128);
        CHECK(combat_effects::damage_player==12&&!combat_effects::weapon_damage_active());qa9_fixture::end();
    }
}
inline void spell_plague_ticks_after_caster_loss(){
    using namespace rework_fixture;using namespace spell_lifetime_fixture;
    for(U32 mode=0;mode<5;mode++){
        spell_lifetime_fixture::begin({102});auto caster=unit(46,1,100,100),target=unit(37,6,200,100);
        target->flingy.hitpoints=100*256;target->plague_timer=75;
        rework_combat_v5::attach(102,target,caster,600,0,75);change(caster,mode);
        auto saved=g.damage;g.damage=hp;const int tick=int(original_stat({1,14,60})*256/76);
        for(U32 i=0;i<3;i++){
            target->flingy.hitpoints-=tick;--target->plague_timer;pulse(101+i*8);
            CHECK(calls==i+1&&amount==tick);CHECK(target->flingy.hitpoints==100*256-int(i+1)*tick*2);
            pulse(102+i*8);CHECK(calls==i+1);
        }
        target->plague_timer=0;pulse(125);CHECK(calls==3);g.damage=saved;qa9_fixture::end();
    }
}
inline void spell_launched_projectiles_after_caster_loss(){
    using namespace rework_fixture;using namespace spell_lifetime_fixture;
    for(U32 w:{30u,84u}){std::int32_t live_amount=0;
        for(U32 mode=0;mode<5;mode++){
            spell_lifetime_fixture::begin();auto caster=unit(w==30?12:67,1,100,100),target=unit(37,6,200,100);
            auto b=bullet(caster,target,w);change(caster,mode);owner_missile_hook(b,missile);
            CHECK(calls==1);if(!mode)live_amount=amount;CHECK(amount==live_amount&&amount>0);qa9_fixture::end();
        }
    }
}
inline void spell_generated_damage_caster_loss(){
    using namespace rework_fixture;using namespace spell_lifetime_fixture;
    for(U32 mode:{0u,1u,3u,4u}){
        spell_lifetime_fixture::begin();auto caster=unit(46,1,100,100),target=unit(37,6,200,100);change(caster,mode);
        auto saved=g.damage;auto native=combat_effects::original_weapon_damage;g.damage=hp;
        rework_combat_v5::hurt(target,128,caster,1);CHECK(calls==1&&amount==128);
        combat_effects::original_weapon_damage=weapon;rework_combat_v5::weapon_hurt(target,256,60,caster,1);CHECK(calls==2&&amount==256);
        combat_effects::original_weapon_damage=nullptr;rework_combat_v5::weapon_hurt(target,64,60,caster,1);CHECK(calls==3&&amount==64);
        g.damage=saved;combat_effects::original_weapon_damage=native;qa9_fixture::end();
    }
}
inline void spell_persistent_zone_after_caster_loss(){
    using namespace rework_fixture;using namespace spell_lifetime_fixture;
    for(U32 mode=0;mode<5;mode++){
        spell_lifetime_fixture::begin({52});auto caster=unit(32,1,100,100),target=unit(37,6,200,100);
        rework_combat_v5::Persist p{};p.kind=52;p.source=rework_combat_v5::identity(caster);p.owner=1;p.x=200;p.y=100;p.until=200;p.due=101;
        rework_combat_v5::persistent.push_back(p);change(caster,mode);auto saved=g.damage;g.damage=hp;
        const auto before=target->flingy.hitpoints;pulse(101);CHECK(calls==1&&target->flingy.hitpoints<before);pulse(102);CHECK(calls==1);
        g.damage=saved;qa9_fixture::end();
    }
}
inline void run_spell_caster_lifetime_groups(){
    spell_irradiate_propagation_caster_lifetime();spell_native_damage_boundaries();spell_plague_ticks_after_caster_loss();
    spell_launched_projectiles_after_caster_loss();spell_generated_damage_caster_loss();spell_persistent_zone_after_caster_loss();
}
}
