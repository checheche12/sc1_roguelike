#pragma once
namespace qa87_valkyrie {
namespace volley=rework_combat_v5::valkyrie_volley;
inline std::array<U8,65536> code{};
inline std::array<movement_effects::Image,16> images{};
inline movement_effects::GetBin saved_bin=nullptr;
inline shadow_feedback::Step saved_step=nullptr;
inline ReadVars saved_read=nullptr;
inline U32 locks=0;
inline void* __cdecl bin(){return code.data();}
// Interpret the actual patched bytecode with explicit native opcode fixtures.
// This proves command-lock reachability/adapter behavior, not live visuals.
inline void __cdecl script(movement_effects::Image* image,movement_effects::Script* s,U32 dry,U32*){
    auto u=reinterpret_cast<bw::Unit*>(rework_fixture::script_context[1]);CHECK(valid_unit(u));
    CHECK(u->flingy.sprite==image->parent);
    if(s->wait&&--s->wait)return;
    for(U32 budget=0;budget<40;budget++){
        auto at=s->pos;CHECK(at<code.size());const auto op=code[s->pos++];
        if(op==volley::select_opcode){volley::select(code.data()+at+1,s,image,dry,nullptr);continue;}
        if(op==volley::release_opcode){volley::detach(code.data()+at+1,s,image,dry,nullptr);continue;}
        if(op==5){s->wait=code[s->pos++];return;}
        if(op==0x25){CHECK(code[s->pos++]==2);
            if(!dry)for(U32 missile=0;missile<multi_target::factor(103);missile++)rework_fixture::hooked(103,u->flingy.position.x,u->flingy.position.y,u->player,u->flingy.facing_direction,u);
            continue;}
        if(op==0x2e){if(!dry){u->flags|=0x2000u;static_cast<bw::SpriteScr*>(u->flingy.sprite)->flags|=0x80;++locks;}continue;}
        if(op==0x2f){if(!dry){u->flags&=~0x2000u;static_cast<bw::SpriteScr*>(u->flingy.sprite)->flags&=~0x80u;}continue;}
        if(op==0x2a){if(!dry)u->flingy.flingy_flags&=~8u;continue;}
        if(op==7){s->pos=std::uint16_t(code[s->pos]|U32(code[s->pos+1])<<8);if(s->pos==volley::idle)return;continue;}
        CHECK(false);
    }
    CHECK(false);
}
inline void begin(bool legend=true){
    saved_bin=movement_effects::get_bin;saved_step=shadow_feedback::step;saved_read=movement_effects::read_vars;
    talent_power::enabled=true;rework_fixture::begin(legend?std::initializer_list<U32>{58}:std::initializer_list<U32>{});rework_fixture::install();
    code.fill(0);std::memcpy(code.data(),movement_effects::data::kIscript,sizeof(movement_effects::data::kIscript));
    rework_combat_v5::script_transform(code.data(),code.size());images={};locks=0;
    movement_effects::get_bin=bin;movement_effects::read_vars=nullptr;shadow_feedback::step=script;
    rework_combat_v5::script_context_read=rework_fixture::script_read;rework_combat_v5::script_context_write=rework_fixture::script_write;
}
inline void end(){rework_fixture::finish();talent_power::enabled=false;movement_effects::get_bin=saved_bin;movement_effects::read_vars=saved_read;shadow_feedback::step=saved_step;}
inline movement_effects::Image* image(bw::Unit* u){return static_cast<movement_effects::Image*>(static_cast<bw::SpriteScr*>(u->flingy.sprite)->main_image);}
inline bw::Unit* ship(bw::Unit* target,U32 owner=1){
    auto u=rework_fixture::unit(58,owner,100,100,true);auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);
    auto& im=images[std::size_t(u-g.units)];im.parent=sprite;im.script={std::uint16_t(volley::stock_header),std::uint16_t(volley::entry),0,U8(rework_combat_v5::air(target)?3:2),0};
    sprite->main_image=sprite->first_image=&im;u->order=10;multi_fixture::target(u,target);
    u->ground_cooldown=u->air_cooldown=64;u->flingy.flingy_flags=8;u->flingy.current_speed=1536;u->flingy.current_speed_x=1536;
    u->flingy.move_target={2000,100,nullptr};return u;
}
inline void advance(bw::Unit* u,U32 frame){game.frame_count=frame;rework_fixture::script_context={reinterpret_cast<std::size_t>(&u->flingy),reinterpret_cast<std::size_t>(u),0};script(image(u),&image(u)->script,0,nullptr);}
inline bool command(bw::Unit* u,U32 order,int x,int y){
    if(u->flags&0x2000u)return false; // Native NoBrkCode queues this command.
    u->order=U8(order);u->order_target={std::int16_t(x),std::int16_t(y),nullptr};u->flingy.move_target=u->order_target;
    u->flingy.next_move_waypoint={std::int16_t(x),std::int16_t(y)};image(u)->script.animation=11;image(u)->script.pos=38305;return true;
}
}
inline void qa87_valkyrie_unlocked_ground_air_and_eight_native_missiles(){
    using namespace qa87_valkyrie;
    for(bool air:{false,true})for(U32 order:{6u,152u}){
        begin();auto target=rework_fixture::unit(air?43:37,6,180,100,air),u=ship(target);
        advance(u,100);CHECK(multi_fixture::shots.empty());advance(u,101);
        CHECK(multi_fixture::shots.size()==2&&locks==0&&!(u->flags&0x2000u)&&!(u->flingy.flingy_flags&8u));
        CHECK(!(static_cast<bw::SpriteScr*>(u->flingy.sprite)->flags&0x80u)&&volley::volleys.size()==1);
        CHECK(command(u,order,10,400)); // Same frame as the first native pair.
        for(U32 frame=102;frame<=141;frame++){
            // Alternate directions after firing: no forced forward drift.
            if(frame==112||frame==122)CHECK(command(u,order,int(frame)*3,700-int(frame)));
            u->flingy.position.x=std::int16_t(100+frame-101);
            const auto motion=u->flingy;const auto animation=image(u)->script;const auto aim=u->order_target;
            rework_fixture::script_context={111,222,333};const auto globals=rework_fixture::script_context;
            game.frame_count=frame;volley::step();
            CHECK(std::memcmp(&motion,&u->flingy,sizeof(motion))==0&&std::memcmp(&animation,&image(u)->script,sizeof(animation))==0);
            CHECK(u->order==order&&u->order_target.unit==aim.unit&&u->order_target.x==aim.x&&u->order_target.y==aim.y&&rework_fixture::script_context==globals);
            CHECK(multi_fixture::shots.size()==(frame<111?2u:frame<121?4u:frame<131?6u:8u));
        }
        CHECK(volley::volleys.empty()&&multi_fixture::shots.size()==8);
        for(const auto& b:rework_combat_v5::projectiles)CHECK(b.second.percent==(air?100u:150u));
        CHECK(multi_fixture::shots[2].x==110&&multi_fixture::shots[4].x==120&&multi_fixture::shots[6].x==130);
        end();
    }
    std::printf("QA87_VALKYRIE ground_air=1 move_patrol_on_first_pair=1 reversals_preserved=1 native_missiles=8 pairs_at=0,10,20,30 no_forced_motion=1\n");
}
inline void qa87_valkyrie_stock_isolation_and_script_validation(){
    using namespace qa87_valkyrie;
    for(U32 test=0;test<4;test++){
        begin(test!=0);auto target=rework_fixture::unit(43,6,180,100,true),u=ship(target,test==1?6:1);
        if(test==2)u->flags|=0x40000000u;if(test==3)g.applied=false;
        advance(u,100);advance(u,101);CHECK(locks==1&&u->flags&0x2000u&&!command(u,6,10,100));CHECK(volley::volleys.empty());end();
    }
    begin();CHECK(std::memcmp(code.data()+volley::stock_entry,volley::stock,sizeof(volley::stock))==0);
    const auto once=code;rework_combat_v5::script_transform(code.data(),code.size());CHECK(code==once);
    for(U32 animation:{2u,3u,5u,6u}){const auto p=volley::stock_header+8+animation*2;CHECK((code[p]|U32(code[p+1])<<8)==volley::entry);}
    auto target=rework_fixture::unit(43,6,180,100,true),u=ship(target);auto s=image(u)->script;
    volley::select(code.data()+volley::entry+1,&s,image(u),1,nullptr);CHECK(s.pos==volley::stock_entry&&volley::volleys.empty());
    s=image(u)->script;volley::select(code.data()+volley::entry+2,&s,image(u),0,nullptr);CHECK(s.pos==volley::entry);
    code[volley::stock_entry]^=1;const auto malformed=code;volley::append(code.data(),code.size());CHECK(code==malformed);end();
}
inline void qa87_valkyrie_death_capture_disable_and_no_repeat(){
    using namespace qa87_valkyrie;
    for(U32 test=0;test<9;test++){
        begin();auto target=rework_fixture::unit(37,6,180,100),u=ship(target);advance(u,100);advance(u,101);
        auto s=image(u)->script;volley::detach(code.data()+volley::release+1,&s,image(u),0,nullptr);CHECK(volley::volleys.size()==1);
        if(test==0)u->flingy.hitpoints=0;else if(test==1)++u->minor_unique_index;else if(test==2)u->player=6;
        else if(test==3)u->lockdown_timer=1;else if(test==4)u->stasis_timer=1;else if(test==5)target->flingy.hitpoints=0;
        else if(test==6)++target->minor_unique_index;else if(test==7)target->player=1;else rework_fixture::ranks[58]=0;
        game.frame_count=111;volley::step();CHECK(multi_fixture::shots.size()==2);
        game.frame_count=141;volley::step();CHECK(volley::volleys.empty());end();
    }
    begin();auto target=rework_fixture::unit(43,6,180,100,true),u=ship(target);advance(u,100);advance(u,101);
    u->ground_cooldown=u->air_cooldown=1;game.frame_count=111;volley::step();CHECK(u->ground_cooldown==30&&u->air_cooldown==30);
    volley::step();CHECK(multi_fixture::shots.size()==4);rework_combat_v5::reset();CHECK(volley::volleys.empty());end();
}
inline void qa87_valkyrie_mobile_acquires_one_target_and_shared_cycle(){
    using namespace qa87_valkyrie;
    for(bool air:{false,true})for(U32 order:{6u,152u}){
        begin();auto target=rework_fixture::unit(air?43:37,6,150,100,air);auto other=rework_fixture::unit(air?37:43,6,170,100,!air);auto u=ship(target);
        u->flingy.flingy_flags=0;u->ground_cooldown=u->air_cooldown=0;CHECK(command(u,order,50,500));
        const auto motion=u->flingy;const auto anim=image(u)->script;auto s=rework_combat_v5::state(u);
        // Native range reads the owner-scoped ground slot, including the new layer.
        const auto saved_range=multi_target::outside_range;
        multi_target::outside_range=[](bw::Unit* source,bw::Unit* victim)->U32 {
            const U32 w=raw_value(0,rework_combat_v5::air(victim)?19:17,source->unit_id),range=raw_value(1,5,w);
            return multi_target::distance_sq(source,victim)>std::uint64_t(range)*range;
        };
        volley::mobile(u,*s,100);CHECK(multi_fixture::shots.size()==2&&volley::volleys.size()==1);
        CHECK(u->order==order&&u->order_target.unit==nullptr&&u->order_target.x==50&&u->order_target.y==500);
        CHECK(std::memcmp(&motion,&u->flingy,sizeof(motion))==0&&std::memcmp(&anim,&image(u)->script,sizeof(anim))==0);
        CHECK(u->ground_cooldown==64&&u->air_cooldown==64&&s->next_ground==164&&s->next_air==164);
        for(U32 frame=100;frame<=140;frame++){
            game.frame_count=frame;volley::mobile(u,*s,frame);volley::step();
            CHECK(multi_fixture::shots.size()<=(frame<110?2u:frame<120?4u:frame<130?6u:8u));
        }
        CHECK(multi_fixture::shots.size()==8);
        for(const auto& shot:multi_fixture::shots)CHECK(shot.target==target&&shot.target!=other);
        for(const auto& b:rework_combat_v5::projectiles)CHECK(b.second.percent==(air?100u:150u));
        u->ground_cooldown=u->air_cooldown=0;game.frame_count=164;u->order=1;volley::mobile(u,*s,164);CHECK(multi_fixture::shots.size()==8);
        u->order=6;target->flingy.position.x=other->flingy.position.x=3000;volley::mobile(u,*s,164);CHECK(multi_fixture::shots.size()==8);
        target->flingy.position.x=150;u->lockdown_timer=1;volley::mobile(u,*s,164);CHECK(multi_fixture::shots.size()==8);
        u->lockdown_timer=0;rework_fixture::ranks[58]=0;volley::mobile(u,*s,164);CHECK(multi_fixture::shots.size()==8);
        rework_fixture::ranks[58]=1;volley::mobile(u,*s,164);CHECK(multi_fixture::shots.size()==10);
        multi_target::outside_range=saved_range;end();
    }
}
