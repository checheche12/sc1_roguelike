#pragma once
// Production economy adapters against owned synthetic units and real DAT assets.
namespace host_test {
inline constexpr std::size_t rework_economy_group_count=9;
inline GrowthSnapshot economy_snapshot(std::initializer_list<U32> ordinals,U32 phase=1){
    GrowthSnapshot s{};s.wire_version=2;s.completed_phase=phase;
    for(U32 ordinal:ordinals){const U32 bit=238+ordinal;s.talent_bits[bit/32]|=1u<<(bit%32);}return s;
}
inline bw::Unit* economy_add(U32 id,U32 owner=1,int x=500,int y=500){auto u=add(id,owner,x,y);std::fill(std::begin(u->build_queue),std::end(u->build_queue),std::uint16_t(228));return u;}
inline bw::Unit* __cdecl economy_create_supply(U32 id,int x,int y,U32 owner,const U8* skins){
    auto u=create(id,x,y,owner,skins);if(u && id==7)game.supplies[1].used[owner]+=raw_value(0,46,id);
    if(u && id==41)game.supplies[0].used[owner]+=raw_value(0,46,id);
    if(u && id==64)game.supplies[2].used[owner]+=raw_value(0,46,id);
    if(u)std::fill(std::begin(u->build_queue),std::end(u->build_queue),std::uint16_t(228));return u;
}
inline void __cdecl economy_return_original(bw::Unit* u){
    const U32 cargo=u->unit_specific.bytes[27];if(u->carried_powerup_flags&2u)game.minerals[u->player]+=cargo;else if(u->carried_powerup_flags&1u)game.gas[u->player]+=cargo;
    u->unit_specific.bytes[27]=0;u->carried_powerup_flags=0;
}
inline bw::Unit* economy_selected=nullptr;
inline void __cdecl economy_cancel_duplicate(const void*,U32,U32){economy_selected->build_queue[1]=228;game.minerals[1]+=raw_value(0,40,0);}
inline void __cdecl economy_native_morph(bw::Unit* u,U32 id){
    const U32 old=u->unit_id;
    if(old==35 && id==36)game.supplies[0].used[u->player]+=raw_value(0,46,41);
    if(old==36 && id==35)game.supplies[0].used[u->player]-=raw_value(0,46,41);
    u->unit_id=static_cast<std::uint16_t>(id);
}
inline std::vector<U32> economy_packet_ids;
inline U32 __cdecl economy_register_packet(U32 id,void (__cdecl* hook)(const U8*,U32,U32,U32,rework_economy_v5::CommandNext),U32 (__cdecl* length)(const U8*,U32)){
    CHECK(require_init());CHECK(hook==rework_economy_v5::command_packet && length==nullptr);economy_packet_ids.push_back(id);return 1;
}
inline void economy_discount_components_and_rounding(){
    struct Sample{U32 ordinal,id,mineral,gas;};
    const Sample rows[]={{151,0,40,0},{152,5,120,80},{153,12,320,240},{154,37,40,0},{155,103,40,80},
        {156,45,80,80},{157,44,40,80},{158,65,80,0},{159,66,100,40},{160,72,280,200}};
    for(const auto& row:rows){reset();auto s=economy_snapshot({row.ordinal});CHECK(apply_snapshot(nullptr,s));
        if(owner_stat(1,{0,40,row.id})!=row.mineral || owner_stat(1,{0,41,row.id})!=row.gas)throw std::runtime_error("economy price ordinal"+std::to_string(row.ordinal)+" actual "+std::to_string(owner_stat(1,{0,40,row.id}))+"/"+std::to_string(owner_stat(1,{0,41,row.id})));
        CHECK(owner_stat(1,{0,40,row.id})==row.mineral && owner_stat(1,{0,41,row.id})==row.gas);
        CHECK(owner_stat(6,{0,40,row.id})==original_stat({0,40,row.id}));
        CHECK(owner_stat(1,{0,40,7})==50);
        CHECK(rework_economy_v5::price(s,row.id,1)==1 && rework_economy_v5::price(s,row.id,0)==0);
    }
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({7,117})));
    CHECK(owner_stat(1,{0,40,106})==280 && owner_stat(1,{0,40,131})==210 && owner_stat(1,{0,40,154})==280);
    CHECK(owner_stat(1,{0,40,132})==150 && owner_stat(1,{0,41,132})==100); // Lair is additional morph payment.
    CHECK(owner_stat(1,{0,40,73})==13 && owner_stat(1,{0,40,85})==8);
}
inline void economy_times_supply_and_owner_isolation(){
    reset();auto missile=economy_add(14);auto silo=economy_add(108);missile->flags|=1;game.supplies[1].used[1]=16;
    CHECK(apply_snapshot(nullptr,economy_snapshot({46})));
    CHECK(owner_stat(1,{0,42,14})==720 && owner_stat(1,{0,46,14})==4);
    CHECK(game.supplies[1].used[1]==4);
    std::uint64_t tooltip=0;CHECK(rework_economy_ui::read(silo,14,tooltip));CHECK(((tooltip>>32)&255u)==4);
    CHECK(owner_stat(6,{0,42,14})==original_stat({0,42,14}) && owner_stat(6,{0,46,14})==16);
    CHECK(owner_stat(1,{0,40,14})==original_stat({0,40,14}) && owner_stat(1,{0,41,14})==original_stat({0,41,14}));
    reset();auto depot=economy_add(109);depot->flags|=1;game.supplies[1].provided[1]=16;
    auto s=economy_snapshot({3,4,6,7,20,22,117});CHECK(apply_snapshot(nullptr,s));
    CHECK(game.supplies[1].provided[1]==32 && game.supplies[1].provided[6]==0);
    for(U32 id:{7u,41u,64u})CHECK(owner_stat(1,{0,42,id})==(original_stat({0,42,id})+1)/2);
    for(U32 id:{109u,42u,156u}){CHECK(owner_stat(1,{0,42,id})==72);CHECK(owner_stat(1,{0,45,id})==original_stat({0,45,id})+16);}
    CHECK(owner_stat(1,{0,42,111})==(original_stat({0,42,111})+1)/2);
    CHECK(owner_stat(1,{0,42,160})==(original_stat({0,42,160})+1)/2);
    CHECK(owner_stat(1,{0,42,106})==rework_economy_v5::ceiling(rework_economy_v5::ceiling(original_stat({0,42,106}),7,10),1,2));
    auto worker=economy_add(7),enemy=economy_add(7,6),marine=economy_add(0);
    CHECK(rework_economy_v5::motion_ratio(worker)==1.5 && rework_economy_v5::motion_ratio(enemy)==1.0 && rework_economy_v5::motion_ratio(marine)==1.0);
    s.completed_phase=2;CHECK(apply_snapshot(nullptr,s));CHECK(game.supplies[1].provided[1]==32);
}
inline void economy_resources_and_start_only_box(){
    reset();game.elapsed_seconds=0;auto mineral=economy_add(176,11),geyser=economy_add(188,11);
    rework_economy_v5::amount(mineral,1500);rework_economy_v5::amount(geyser,3000);
    auto s=economy_snapshot({2,5});s.curse_counts[0]=2;s.curse_counts[49]=3;
    CHECK(apply_snapshot(nullptr,s));CHECK(rework_economy_v5::amount(mineral)==4500 && rework_economy_v5::amount(geyser)==9000);
    CHECK(game.minerals[1]==250 && game.gas[1]==250);
    geyser->unit_id=110;geyser->player=1;rework_economy_v5::step();CHECK(rework_economy_v5::amount(geyser)==9000);
    auto later=economy_add(177,11);rework_economy_v5::amount(later,1000);rework_economy_v5::step();CHECK(rework_economy_v5::amount(later)==3000);
    s.completed_phase=2;CHECK(apply_snapshot(nullptr,s));CHECK(rework_economy_v5::amount(mineral)==4500 && game.minerals[1]==250);
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({})));s=economy_snapshot({5},2);s.curse_counts[0]=2;
    CHECK(apply_snapshot(nullptr,s));CHECK(game.minerals[1]==0 && game.gas[1]==0); // Acquired after game start.
}
inline void economy_successful_resource_returns_only(){
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({0,1})));auto u=economy_add(7);game.minerals[1]=100;game.gas[1]=50;
    u->order=90;u->unit_specific.bytes[27]=8;u->carried_powerup_flags=2;
    owner_unit_hook(u,economy_return_original);
    CHECK(game.minerals[1]==110);
    u->order=84;u->unit_specific.bytes[27]=8;u->carried_powerup_flags=1;
    owner_unit_hook(u,economy_return_original);
    CHECK(game.gas[1]==60);
    u->order=90;u->unit_specific.bytes[27]=8;u->carried_powerup_flags=2;
    {rework_economy_v5::UnitScope step(u);}CHECK(game.minerals[1]==110);
    {rework_economy_v5::UnitScope step(u);u->unit_specific.bytes[27]=0;u->carried_powerup_flags=0;}CHECK(game.minerals[1]==110);
    auto enemy=economy_add(7,6);enemy->order=90;enemy->unit_specific.bytes[27]=8;enemy->carried_powerup_flags=2;
    owner_unit_hook(enemy,economy_return_original);
    CHECK(game.minerals[6]==8 && game.minerals[1]==110);
}
inline void economy_actual_paid_cancellation_and_duplicate_queue(){
    reset();auto barracks=economy_add(111);barracks->flags|=1;barracks->build_queue[0]=0;
    CHECK(apply_snapshot(nullptr,economy_snapshot({})));rework_economy_v5::before_snapshot();
    CHECK(apply_snapshot(nullptr,economy_snapshot({151},2)));game.minerals[1]=100;
    const U8 cancel_first[]={0x20,0,0};
    {rework_economy_v5::CommandScope command(1);barracks->build_queue[1]=0;}
    auto state=rework_economy_v5::state(barracks);CHECK(state->queue[0].mineral==50 && state->queue[1].mineral==40);
    saved_handle=1;economy_selected=barracks;owner_commands_hook(cancel_first,3,0,economy_cancel_duplicate);
    CHECK(game.minerals[1]==150 && state->queue[0].mineral==40); // Correct refund50, remaining paid40.
    reset();auto cc=economy_add(106);cc->order=44;CHECK(apply_snapshot(nullptr,economy_snapshot({})));
    rework_economy_v5::created(cc);CHECK(apply_snapshot(nullptr,economy_snapshot({7},2)));game.minerals[1]=0;
    const U8 cancel_building[]={0x18};
    {rework_economy_v5::CommandScope command(1,cancel_building,1);cc->flingy.hitpoints=0;cc->order=0;game.minerals[1]+=210;}
    CHECK(game.minerals[1]==300); // 75% of actual400, rather than new280 price.
    reset();auto single=economy_add(111);single->flags|=1;single->build_queue[0]=0;
    CHECK(apply_snapshot(nullptr,economy_snapshot({})));rework_economy_v5::before_snapshot();CHECK(apply_snapshot(nullptr,economy_snapshot({151},2)));
    {rework_economy_v5::CommandScope command(1);single->build_queue[1]=0;}
    economy_selected=single;game.minerals[1]=100;
    const U8 combined[]={0x20,0,0,0x20,0,0};
    {rework_economy_v5::CommandScope outer(1,combined,6);
        rework_economy_v5::command_packet(combined,3,1,1,[](const U8*,U32){economy_selected->build_queue[1]=228;game.minerals[1]+=raw_value(0,40,0);});
        rework_economy_v5::command_packet(combined+3,3,1,1,[](const U8*,U32){economy_selected->build_queue[0]=228;game.minerals[1]+=raw_value(0,40,0);});
    }
    CHECK(game.minerals[1]==190 && rework_economy_v5::active_command_scope==nullptr);
    // Actual13515 callback observation: Marine paid40, later DAT50, inner
    // return already40. Do not subtract the price difference twice.
    for(U32 native_refund:{40u,50u}){
        reset();auto b=economy_add(111);b->flags|=1;CHECK(apply_snapshot(nullptr,economy_snapshot({151})));
        {rework_economy_v5::CommandScope enqueue(1);b->build_queue[0]=0;}
        CHECK(rework_economy_v5::state(b)->queue[0].mineral==40);
        CHECK(apply_snapshot(nullptr,economy_snapshot({},2)));game.minerals[1]=9960;game.gas[1]=500;
        {rework_economy_v5::CommandScope cancel(1,cancel_first,3,true);b->build_queue[0]=228;game.minerals[1]+=native_refund;}
        CHECK(game.minerals[1]==10000 && game.gas[1]==500);
    }
    // SAMASE can place hook_process_commands INSIDE hook_ingame_command.
    // Both scopes then observe the same successful native50 refund; the outer
    // packet must retain the inner scope's already corrected40, not remove10.
    reset();auto nested=economy_add(111);nested->flags|=1;CHECK(apply_snapshot(nullptr,economy_snapshot({151})));
    {rework_economy_v5::CommandScope enqueue(1);nested->build_queue[0]=0;}
    CHECK(apply_snapshot(nullptr,economy_snapshot({},2)));game.minerals[1]=9960;economy_selected=nested;saved_handle=1;
    rework_economy_v5::command_packet(cancel_first,3,1,1,[](const U8* bytes,U32 length){
        owner_commands_hook(bytes,length,0,[](const void*,U32,U32){economy_selected->build_queue[0]=228;game.minerals[1]+=50;});
        CHECK(game.minerals[1]==10000);
    });
    CHECK(game.minerals[1]==10000 && rework_economy_v5::active_command_scope==nullptr);
    // Mineral/gas morph components can also be refunded by either historical
    // or current native pricing; each cancellation must restore the paid pair.
    for(U32 native_refund:{80u,100u}){
        reset();auto egg=economy_add(59);egg->build_queue[0]=44;CHECK(apply_snapshot(nullptr,economy_snapshot({157})));
        rework_economy_v5::before_snapshot();CHECK(apply_snapshot(nullptr,economy_snapshot({},2)));game.minerals[1]=960;game.gas[1]=920;
        const U8 cancel_morph[]={0x19};
        {rework_economy_v5::CommandScope cancel(1,cancel_morph,1,true);egg->unit_id=43;egg->build_queue[0]=228;game.minerals[1]+=native_refund==80 ? 40u:50u;game.gas[1]+=native_refund;}
        CHECK(game.minerals[1]==1000 && game.gas[1]==1000);
    }
    auto packet_api=api;packet_api.hook_ingame_command=reinterpret_cast<GenericFn>(economy_register_packet);
    economy_packet_ids.clear();plugin_init_open=true;const bool registered=rework_economy_v5::bind_commands(&packet_api);plugin_init_open=false;
    CHECK(registered && economy_packet_ids==std::vector<U32>({0x18,0x19,0x20,0x23,0x34}));
}
inline void economy_mule_lifetime_orders_supply_and_return(){
    reset();game.elapsed_seconds=0;auto base=economy_add(106);base->flags|=1;auto mineral=economy_add(176,11,550,550);rework_economy_v5::amount(mineral,1500);
    game.supplies[1].used[1]=20;g.create=economy_create_supply;CHECK(apply_snapshot(nullptr,economy_snapshot({23,0})));
    game.elapsed_seconds=119;rework_economy_v5::step();CHECK(count==2);
    game.elapsed_seconds=120;rework_economy_v5::step();CHECK(count==3 && game.supplies[1].used[1]==20);
    auto mule=&units[2];CHECK(rework_economy_v5::mule(mule));
    for(U32 forbidden:{3u,10u,30u,33u,34u,81u,84u,149u,152u}){mule->order=static_cast<U8>(forbidden);rework_economy_v5::UnitScope order(mule);CHECK(mule->order==85);}
    game.minerals[1]=100;mule->order=90;mule->unit_specific.bytes[27]=8;mule->carried_powerup_flags=2;
    {rework_economy_v5::UnitScope returning(mule);mule->unit_specific.bytes[27]=0;mule->carried_powerup_flags=0;game.minerals[1]+=8;}
    CHECK(game.minerals[1]==118);
    game.elapsed_seconds=164;rework_economy_v5::step();CHECK(mule->flingy.hitpoints>0);
    const U32 deadline=rework_economy_v5::expiry(mule);mule->player=6;game.supplies[1].used[6]=2;
    rework_economy_v5::transferred(mule,deadline);CHECK(rework_economy_v5::expiry(mule)==165 && game.supplies[1].used[6]==2);
    mule->order=10;{rework_economy_v5::UnitScope enemy_order(mule);CHECK(mule->order==85);}
    mule->player=1;game.supplies[1].used[1]=22;rework_economy_v5::transferred(mule,deadline);CHECK(game.supplies[1].used[1]==20);
    game.elapsed_seconds=165;rework_economy_v5::step();CHECK(mule->flingy.hitpoints==0);
    rework_economy_v5::before_kill(mule);rework_economy_v5::before_kill(mule);CHECK(game.supplies[1].used[1]==22);
    game.supplies[1].used[1]-=2;CHECK(game.supplies[1].used[1]==20);
}
inline void economy_twin_drone_supply_cancel_and_failed_second(){
    for(U32 scenario=0;scenario<3;++scenario){
        reset();g.create=economy_create_supply;CHECK(apply_snapshot(nullptr,economy_snapshot({24})));
        auto larva=economy_add(35);larva->build_queue[0]=41;larva->order=42;game.supplies[0].used[1]=10;game.minerals[1]=900;
        {rework_economy_v5::UnitScope morph(larva);CHECK(raw_value(0,46,41)==4);owner_transform_hook(larva,36,economy_native_morph);}
        CHECK(raw_value(0,46,41)==2 && game.supplies[0].used[1]==14 && rework_economy_v5::state(larva)->twin_pending);
        if(scenario==0){owner_transform_hook(larva,35,economy_native_morph);CHECK(game.supplies[0].used[1]==10);continue;}
        fail_spawn=scenario==2;owner_transform_hook(larva,41,economy_native_morph);
        CHECK(game.supplies[0].used[1]==(scenario==1 ? 14u:12u));CHECK(count==(scenario==1 ? 2u:1u));
        CHECK(game.minerals[1]==(scenario==1 ? 900u:950u));
    }
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({})));auto old_egg=economy_add(36);old_egg->build_queue[0]=41;
    rework_economy_v5::before_snapshot();CHECK(apply_snapshot(nullptr,economy_snapshot({24},2)));game.minerals[1]=950;game.supplies[0].used[1]=12;
    const U8 cancel[]={0x19};
    {rework_economy_v5::CommandScope command(1,cancel,1);CHECK(raw_value(0,46,41)==2);old_egg->unit_id=35;old_egg->build_queue[0]=228;game.minerals[1]+=100;game.supplies[0].used[1]-=2;rework_economy_v5::transformed(old_egg,36,12);}
    CHECK(game.minerals[1]==1000 && game.supplies[0].used[1]==10); // Old single egg never becomes a paid pair.
}
inline void economy_larva_cap_and_chrono_actual_progress(){
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({21})));g.create=economy_create_supply;
    auto hatch=economy_add(131);hatch->flags|=1;for(U32 i=0;i<3;i++){auto larva=economy_add(35);larva->related=hatch;}
    game.frame_count=0;rework_economy_v5::step();CHECK(count==4);
    for(U32 i=0;i<3;i++){game.frame_count=rework_economy_v5::state(hatch)->larva_due;rework_economy_v5::step();}
    CHECK(count==7);game.frame_count+=10000;rework_economy_v5::step();CHECK(count==7);
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({21})));hatch=economy_add(131);hatch->flags|=1;
    rework_economy_v5::step();U32 elapsed=0;
    for(U32 cycle=0;cycle<13;cycle++){hatch->unit_specific.bytes[14]=37;rework_economy_v5::step();elapsed+=(U32(hatch->unit_specific.bytes[14])+1)*9;hatch->unit_specific.bytes[14]=0;rework_economy_v5::step();}
    CHECK(elapsed==3420); // 13 accelerated periods equal ten stock342-frame periods.
    reset();game.elapsed_seconds=60;CHECK(apply_snapshot(nullptr,economy_snapshot({25})));
    auto factory=economy_add(154);factory->flags|=1;factory->secondary_order=38;auto child=economy_add(64);child->remaining_build_time=100;factory->secondary_order_target.unit=child;
    for(U32 frame=1;frame<=4;frame++){game.frame_count=frame;{rework_economy_v5::UnitScope idle(factory);} // Primary callback cannot suppress secondary progress.
        {rework_economy_v5::UnitScope progress(factory);--child->remaining_build_time;}}
    CHECK(child->remaining_build_time==94);
    game.elapsed_seconds=80;++game.frame_count;{rework_economy_v5::UnitScope outside(factory);--child->remaining_build_time;}CHECK(child->remaining_build_time==93);
    game.elapsed_seconds=150;factory->order=75;std::uint16_t research=100;std::memcpy(factory->unit_specific.bytes+10,&research,2);
    for(U32 frame=10;frame<14;frame++){game.frame_count=frame;rework_economy_v5::UnitScope progress(factory);std::memcpy(&research,factory->unit_specific.bytes+10,2);--research;std::memcpy(factory->unit_specific.bytes+10,&research,2);}
    std::memcpy(&research,factory->unit_specific.bytes+10,2);CHECK(research==94);
}
inline void economy_starting_grant_once_and_retry(){
    for(U32 race:{0u,1u,2u}){
        reset();CHECK(apply_snapshot(nullptr,economy_snapshot({})));g.create=economy_create_supply;
        const U32 depot_id=race==0?131u:race==2?154u:106u,worker_id=race==0?41u:race==2?64u:7u;
        auto base=economy_add(depot_id,player_owner(),1000,1000);base->flags=1;
        auto mineral=economy_add(176,11,1200,1000);rework_economy_v5::amount(mineral,1500);
        game.minerals[player_owner()]=200;game.gas[player_owner()]=100;
        game.frame_count=47;rework_economy_v5::step();CHECK(!rework_economy_v5::starting_bonus_credited);
        game.frame_count=48;fail_spawn=true;rework_economy_v5::step();CHECK(rework_economy_v5::starting_bonus_credited&&rework_economy_v5::starting_workers==0);
        CHECK(game.minerals[player_owner()]==700&&game.gas[player_owner()]==600);
        fail_spawn=false;game.frame_count=72;rework_economy_v5::step();CHECK(rework_economy_v5::starting_workers==4);
        CHECK(game.supplies[race].used[player_owner()]==8&&game.supplies[race].provided[player_owner()]==8);
        U32 workers=0;living_units([&](bw::Unit* u){if(u->unit_id==worker_id&&u->player==player_owner()){++workers;CHECK(u->order==85);}});CHECK(workers==4);
        const auto made=count;game.frame_count=240;rework_economy_v5::step();CHECK(count==made&&game.minerals[player_owner()]==700);
        CHECK(apply_snapshot(nullptr,economy_snapshot({},2)));rework_economy_v5::step();CHECK(count==made&&game.gas[player_owner()]==600);
    }
    reset();CHECK(apply_snapshot(nullptr,economy_snapshot({})));game.frame_count=240;rework_economy_v5::step();CHECK(!rework_economy_v5::starting_bonus_credited);
    for(const auto& m:campaign_config::kMissions)if(m.no_production){g.mission=&m;break;}
    auto base=economy_add(106);base->flags=1;auto mineral=economy_add(176,11,700,500);rework_economy_v5::amount(mineral,1500);
    rework_economy_v5::step();CHECK(!rework_economy_v5::starting_bonus_credited&&rework_economy_v5::starting_workers==0);
}
inline void run_rework_economy_groups(){
    economy_starting_grant_once_and_retry();
    economy_discount_components_and_rounding();economy_times_supply_and_owner_isolation();economy_resources_and_start_only_box();
    economy_successful_resource_returns_only();economy_actual_paid_cancellation_and_duplicate_queue();economy_mule_lifetime_orders_supply_and_return();
    economy_twin_drone_supply_cancel_and_failed_second();economy_larva_cap_and_chrono_actual_progress();
}
}
