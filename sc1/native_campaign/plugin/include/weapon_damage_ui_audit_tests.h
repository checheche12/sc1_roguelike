#pragma once
namespace host_test {
inline constexpr std::size_t weapon_damage_ui_audit_group_count=3;
namespace weapon_damage_ui_audit {
inline U32 observed(bw::Unit* source,bw::Unit* target,U32 weapon,U32 raw,U32 factor=1){
    g.normal_hit=true;
    // Each sample is the opening hit against an unmarked, full-health target.
    auto ss=rework_combat_v5::state(source);ss->focus_hits=ss->dragoon_hits=0;ss->focus_target={};
    auto ts=rework_combat_v5::state(target);ts->erosion=ts->mark=ts->armor_mark=ts->observer_mark_until=0;
    const U32 prior=rework_combat_v5::mutal_bounce_numerator;
    if(rework_combat_v5::own(source)&&rework_combat_v5::in(source->unit_id,{43,55})&&weapon==48&&rework_combat_v5::raw_rank(105))
        rework_combat_v5::mutal_bounce_numerator=3;
    auto amount=std::int32_t(raw*256);
    {rework_combat_v5::DamageScope hit(target,source,weapon,source->player,amount);target->flingy.hitpoints-=amount;}
    rework_combat_v5::mutal_bounce_numerator=prior;
    return U32((std::uint64_t(amount)*factor+128)/256);
}
inline void ranks_for(U32 id,U32 mode){
    using namespace rework_fixture;
    for(const auto& r:unit_growth::rules)if(rework_combat_v5::unit_growth_matches(r,id)){
        if(r.kind==1&&(mode==0||mode==3))ranks[r.ordinal]=3;
        if(r.kind==2&&(mode==1||mode==3))ranks[r.ordinal]=1;
    }
    if(mode>=2)for(const auto& r:legend_focus::rules)if(r.units[id/32]&(1u<<(id%32)))ranks[r.ordinal]=1;
    if(mode==3){ranks[8]=ranks[9]=3;ranks[322]=2;
        for(const auto& r:unit_legend_expansion::rules)if((r.mode==1||r.mode==11)&&!legend_focus::converted(r.ordinal)&&rework_combat_v5::expansion_matches(r,id))ranks[r.ordinal]=1;
    }
}
}
inline void weapon_ui_all_units_primary_damage_and_research(){
    using namespace rework_fixture;U32 subjects=0;
    for(U32 id=0;id<228;id++)for(U32 mode=0;mode<4;mode++){
        qa9_fixture::begin({});weapon_damage_ui_audit::ranks_for(id,mode);install();
        auto source=unit(id,1,100,100,(original_stat({0,22,id})&4u)!=0);
        auto target=unit(37,6,150,100);weapon_ui_fixture::Image image;max_hp_cache::publish(true);image.install();
        for(U32 field:{17u,19u}){
            const U32 w=owner_stat(1,{0,field,id});if(w>=130||!ordinary_weapon(w))continue;
            if(field==19)target->flags|=4u;else target->flags&=~4u;
            const U32 upgrade=owner_stat(1,{1,6,w}),factor=samase_weapon_ui::factor(id,w);
            for(U32 level:{0u,1u,2u,3u,9u}){
                if(auto slot=rework_upgrade_storage::slot(1,upgrade))*slot=U8(level);
                const U32 actual_level=rework_upgrade_storage::level(1,upgrade);
                const U32 raw=owner_stat(1,{1,14,w})+owner_stat(1,{1,15,w})*actual_level;
                target->flingy.hitpoints=256000;target->shields=0;
                const U32 expected=weapon_damage_ui_audit::observed(source,target,w,raw,factor);
                const U32 shown=image.damage(source,w)+image.bonus(source,w,actual_level*factor);
                if(shown!=expected)std::printf("UI_MISMATCH id=%u mode=%u weapon=%u level=%u raw=%u factor=%u shown=%u actual=%u\n",id,mode,w,level,raw,factor,shown,expected);
                CHECK(shown==expected);++subjects;
            }
        }
        qa9_fixture::end();
    }
    CHECK(subjects>1000);
}
inline void weapon_ui_mutal_every_manual_trait_legend_and_upgrade(){
    using namespace rework_fixture;
    for(U32 id:{43u,55u})for(U32 manual=0;manual<=4;manual++)for(U32 mode=0;mode<4;mode++){
        qa9_fixture::begin({});ranks[238]=manual;ranks[299]=(mode&1u)?1:0;ranks[105]=(mode&2u)?1:0;install();
        auto source=unit(id,1,100,100,true),target=unit(37,6,150,100);
        max_hp_cache::publish(true);weapon_ui_fixture::Image image;image.install();
        const U32 upgrade=owner_stat(1,{1,6,48});auto slot=rework_upgrade_storage::slot(1,upgrade);CHECK(slot);
        for(U32 level=0;level<=9;level++){
            *slot=U8(level);const U32 raw=owner_stat(1,{1,14,48})+owner_stat(1,{1,15,48})*level;
            target->flingy.hitpoints=256000;
            CHECK(image.damage(source,48)+image.bonus(source,48,level)==weapon_damage_ui_audit::observed(source,target,48,raw));
            if(id==43&&manual==3&&mode==3&&level==0)CHECK(image.damage(source,48)==22);
        }
        qa9_fixture::end();
    }
}
inline void weapon_ui_temporary_buffs_carrier_and_read_only(){
    using namespace rework_fixture;
    for(U32 id:{0u,43u,65u,72u,82u}){
        qa9_fixture::begin({8,9});auto source=unit(id,1,100,100,id==43||id==72||id==82),target=unit(37,6,150,100);
        install();const U32 w=(id==72||id==82)?79u:qa39_fixture::weapon(id);
        auto s=rework_combat_v5::state(source);s->portal_buff_until=150;s->fleet_buff_until=200;
        if(auto slot=rework_upgrade_storage::slot(1,owner_stat(1,{1,6,w})))*slot=3;
        max_hp_cache::publish(true);const auto before=storage;const auto state_size=rework_combat_v5::states.size();
        for(U32 frame:{100u,150u,200u}){
            game.frame_count=frame;const U32 raw=owner_stat(1,{1,14,w})+owner_stat(1,{1,15,w})*3;
            U32 total=0;CHECK(samase_weapon_ui::scaled_total(source,w,1,total));
            CHECK(total==weapon_damage_ui_audit::observed(source,target,w,raw));
            if(id==72||id==82){qa37_fixture::CarrierImage image;image.install();CHECK(image.query(source,79)==total&&image.query(source,79,true)==0);}
        }
        CHECK(storage==before&&rework_combat_v5::states.size()==state_size);
        qa9_fixture::end();
    }
}
inline void run_weapon_damage_ui_audit_groups(){weapon_ui_all_units_primary_damage_and_research();weapon_ui_mutal_every_manual_trait_legend_and_upgrade();weapon_ui_temporary_buffs_carrier_and_read_only();}
}
