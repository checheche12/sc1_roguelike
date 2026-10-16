#pragma once
// Offline host: exercises the exact registered callbacks with captured native
// Move results; it does not claim that the SCR dispatcher has run live.
namespace host_test {
namespace movement_fixture {
inline bw::Unit* active_script=nullptr;
inline std::array<bw::SpriteScr,64> sprites{};
inline std::array<movement_effects::Image,64> images{};
inline std::vector<U32> registered_ops;
inline movement_effects::FileRead reader=nullptr;
inline U32 enters=0,leaves=0;
inline std::vector<bw::Unit*> stack;
inline bool rejected_opcode=false;
inline void* __cdecl bin(){return const_cast<U8*>(movement_effects::data::kIscript);}
inline void __cdecl vars(const std::uint16_t* ids,std::size_t* out,std::size_t n){
    for(std::size_t i=0;i<n;i++){CHECK(ids[i]==static_cast<std::uint16_t>(samase::VarId::ActiveIscriptUnit));out[i]=reinterpret_cast<std::size_t>(active_script);}
}
inline U32 __cdecl register_opcode(U32 op,movement_effects::Opcode callback){
    CHECK(require_init());CHECK(callback);registered_ops.push_back(op);return rejected_opcode ? 0:1;
}
inline void __cdecl register_file(const U8* name,movement_effects::FileRead callback){
    CHECK(require_init());CHECK(std::strcmp(reinterpret_cast<const char*>(name),"scripts\\iscript.bin")==0);reader=callback;
}
inline void enter(bw::Unit* u) noexcept {++enters;stack.push_back(u);note_attack_launch(u,original_stat({0,17,u->unit_id}));}
inline void leave(bw::Unit* u) noexcept {++leaves;if(!stack.empty() && stack.back()==u)stack.pop_back();}
inline U32 offset(U32 opcode){for(auto e:movement_effects::data::kEvents)if(e.opcode==opcode)return e.offset;throw std::runtime_error("missing event");}
inline void invoke(U32 opcode,movement_effects::Image* image,U32 dry=0,U32* speed=nullptr){
    auto pos=const_cast<U8*>(movement_effects::data::kIscript)+offset(opcode)+1;
    auto callback=opcode==0xcd ? movement_effects::move_opcode : opcode==0xce ? movement_effects::melee_enter_opcode : movement_effects::melee_leave_opcode;
    callback(pos,&image->script,image,dry,speed);CHECK(image->script.pos==offset(opcode)+1 && image->script.wait==0);
}
inline void begin(){
    movement_effects::reset();reset();refresh_units();g.applied=true;
    movement_effects::get_bin=bin;movement_effects::read_vars=vars;movement_effects::enter_event=enter;movement_effects::leave_event=leave;
    sprites={};images={};active_script=nullptr;enters=leaves=0;stack.clear();
}
inline bw::Unit* unit(U32 id,U32 owner){
    auto u=add(id,owner,500,500);const auto i=static_cast<std::size_t>(u-units.data());CHECK(i<images.size());
    u->flingy.sprite=&sprites[i];u->flingy.movement_type=2;images[i].parent=&sprites[i];sprites[i].main_image=&images[i];return u;
}
inline movement_effects::Image* image(bw::Unit* u){return &images[static_cast<std::size_t>(u-units.data())];}
inline void native_move_result(bw::Unit* u,int distance=2560){
    // Native Move produces next/current speed and direction vector. It reads
    // native upgrade/ensnare state first. One invocation replaces old results.
    u->flingy.current_speed=u->flingy.next_speed=distance;
    u->flingy.current_speed_x=distance*3/5;u->flingy.current_speed_y=-distance*4/5;
}
inline void bit(U32 n){g.growth.talent_bits[n/32]|=1u<<(n%32);}
}
void movement_six_native_move_routes(){
    using namespace movement_fixture;
    for(const auto& patch:frozen::movement_patches){
        if(patch.bit!=17 && patch.bit!=24 && patch.bit!=48 && patch.bit!=52 && patch.bit!=55 && patch.bit!=73)continue;
        begin();bit(patch.bit);auto own=unit(patch.unit_id,1),enemy=unit(patch.unit_id,6),neutral=unit(patch.unit_id,11);
        for(auto u:{own,enemy,neutral}){
            for(U32 cycle=0;cycle<5;cycle++){
                native_move_result(u);active_script=u;invoke(0xcd,image(u));
                const int expected=u==own ? static_cast<int>((2560*patch.numerator+patch.denominator/2)/patch.denominator):2560;
                CHECK(u->flingy.next_speed==expected && u->flingy.current_speed==expected);
                CHECK(u->flingy.current_speed_x==(u==own ? static_cast<int>((1536*patch.numerator+patch.denominator/2)/patch.denominator):1536));
                CHECK(u->flingy.current_speed_y==(u==own ? -static_cast<int>((2048*patch.numerator+patch.denominator/2)/patch.denominator):-2048));
            }
        }
        // Owner transfer, type change and recycled generation read live identity.
        own->player=6;native_move_result(own);invoke(0xcd,image(own));CHECK(own->flingy.next_speed==2560);
        own->player=1;own->unit_id=19;native_move_result(own);invoke(0xcd,image(own));CHECK(own->flingy.next_speed==2560);
        own->unit_id=static_cast<std::uint16_t>(patch.unit_id);++own->minor_unique_index;native_move_result(own);invoke(0xcd,image(own));CHECK(own->flingy.next_speed>2560);
    }
}
void movement_enemy_commands_and_exclusions(){
    using namespace movement_fixture;begin();g.growth.curse_counts[3]=2;
    auto enemy=unit(38,6),own=unit(38,1),ally=unit(38,5),neutral=unit(38,11),hero=unit(53,6),illusion=unit(38,6);
    game.alliances[1][5]=game.alliances[5][1]=1;illusion->flags|=0x40000000u;
    game.frame_count=100;track_unit(enemy)->command_until=110;
    for(auto u:{enemy,own,ally,neutral,hero,illusion}){
        native_move_result(u);active_script=u;invoke(0xcd,image(u));
        CHECK(u->flingy.next_speed==(u==enemy ? 3533:2560));
    }
    game.frame_count=110;native_move_result(enemy);invoke(0xcd,image(enemy));CHECK(enemy->flingy.next_speed==2944);
    ++enemy->minor_unique_index;native_move_result(enemy);invoke(0xcd,image(enemy));CHECK(enemy->flingy.next_speed==2944);
    g.growth.curse_counts[3]=0;native_move_result(enemy);invoke(0xcd,image(enemy));CHECK(enemy->flingy.next_speed==2560);
    illusion->flags=0;g.growth.curse_counts[3]=1;native_move_result(illusion);invoke(0xcd,image(illusion));CHECK(illusion->flingy.next_speed==2752);
}
void movement_prediction_and_engine_state_preserved(){
    using namespace movement_fixture;begin();bit(17);auto u=unit(3,1);active_script=u;
    native_move_result(u,1280);const auto before=u->flingy;U32 prediction=1280;
    invoke(0xcd,image(u),1,&prediction);CHECK(prediction==1536);CHECK(std::memcmp(&before,&u->flingy,sizeof(before))==0);CHECK(g.tracks.empty());
    invoke(0xcd,image(u));CHECK(u->flingy.next_speed==1536); // Slow result preserved then scaled.
    native_move_result(u,0);invoke(0xcd,image(u));CHECK(!u->flingy.current_speed && !u->flingy.next_speed);
    u->flingy.movement_type=0;native_move_result(u);prediction=2560;invoke(0xcd,image(u),0,&prediction);CHECK(u->flingy.next_speed==2560 && prediction==2560);
    u->flingy.movement_type=2;g.applied=false;native_move_result(u);invoke(0xcd,image(u));CHECK(u->flingy.next_speed==2560);
}
void movement_callback_identity_and_thread(){
    using namespace movement_fixture;begin();bit(17);auto own=unit(3,1),enemy=unit(3,6);
    active_script=enemy;native_move_result(own);invoke(0xcd,image(own));CHECK(own->flingy.next_speed==3072);CHECK(!enemy->flingy.next_speed);
    auto orphan=*image(own);orphan.parent=reinterpret_cast<void*>(0x1234);native_move_result(own);invoke(0xcd,&orphan);CHECK(own->flingy.next_speed==2560);
    g.game_thread=GetCurrentThreadId()+1;invoke(0xcd,image(own));CHECK(own->flingy.next_speed==2560);g.game_thread=GetCurrentThreadId();
    auto old=image(own)->script;movement_effects::move_opcode(const_cast<U8*>(movement_effects::data::kIscript)+3,&image(own)->script,image(own),0,nullptr);
    CHECK(std::memcmp(&old,&image(own)->script,sizeof(old))==0);
}
void movement_melee_launch_and_pairing(){
    using namespace movement_fixture;begin();bit(35);auto ling=unit(37,1),enemy=unit(37,6);
    active_script=ling;ling->ground_cooldown=8;apply_unit_motion(); // Order sets native cooldown before native melee fires.
    game.frame_count=1;ling->ground_cooldown=7;invoke(0xce,image(ling));CHECK(enters==1 && movement_effects::depth==1);
    active_script=enemy;invoke(0xce,image(enemy));CHECK(movement_effects::depth==2);
    invoke(0xcf,image(enemy));CHECK(movement_effects::depth==1);invoke(0xcf,image(ling));CHECK(!movement_effects::depth && stack.empty() && leaves==2);
    apply_unit_motion();CHECK(ling->ground_cooldown==5); // 8 /1.3 rounded, minus elapsed frame.
    const auto applied=ling->ground_cooldown;game.frame_count=2;--ling->ground_cooldown;
    invoke(0xce,image(ling));invoke(0xcf,image(ling));apply_unit_motion();CHECK(ling->ground_cooldown==applied-1); // Multi-hit in same attack is not another reset.
    invoke(0xce,image(ling),1);CHECK(!movement_effects::depth && enters==3);
    invoke(0xce,image(ling));CHECK(movement_effects::depth==1);movement_effects::reset();CHECK(!movement_effects::depth && stack.empty());
}
void movement_register_and_file_ownership(){
    using namespace movement_fixture;begin();registered_ops.clear();reader=nullptr;rejected_opcode=false;
    api.get_iscript_bin=reinterpret_cast<GenericFn>(factory<bin>);api.hook_iscript_opcode=reinterpret_cast<GenericFn>(register_opcode);
    api.hook_file_read=reinterpret_cast<GenericFn>(register_file);api.read_vars=vars;
    plugin_init_open=true;CHECK(movement_effects::bind(&api,enter,leave));plugin_init_open=false;
    CHECK(registered_ops==std::vector<U32>({0xcd,0xce,0xcf}));CHECK(reader && late_init_calls==0);
    const auto init_count=init_calls;U32 size=0;auto bytes=reader(nullptr,&size);CHECK(bytes && size==0x10000);
    CHECK(std::memcmp(bytes,movement_effects::data::kIscript,sizeof(movement_effects::data::kIscript))==0);
    CHECK(bytes[size-1]==0);CHECK(HeapFree(GetProcessHeap(),0,bytes));CHECK(init_calls==init_count);
    auto u=unit(3,1);bit(17);native_move_result(u);invoke(0xcd,image(u));CHECK(init_calls==init_count);
    rejected_opcode=true;registered_ops.clear();reader=nullptr;plugin_init_open=true;CHECK(!movement_effects::bind(&api,enter,leave));plugin_init_open=false;CHECK(!reader);
    rejected_opcode=false;
}
void run_movement_effect_groups(){movement_six_native_move_routes();movement_enemy_commands_and_exclusions();movement_prediction_and_engine_state_preserved();movement_callback_identity_and_thread();movement_melee_launch_and_pairing();movement_register_and_file_ownership();}
} // namespace host_test
