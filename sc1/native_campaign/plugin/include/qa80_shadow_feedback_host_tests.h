#pragma once
namespace host_test {
namespace qa80_fixture {
inline std::array<U8,65536> code{};
inline std::array<bw::Unit*,8*12> selections{};
inline U32 sounds=0,commands=0,unique=0;inline bool queued=false;
inline bw::Unit* casting=nullptr;
inline void* __cdecl bin(){return code.data();}
inline bw::Unit** __cdecl selected(){return selections.data();}
inline void __cdecl sound(void* script,void* image,U32 dry,U32* speed){
 auto s=static_cast<movement_effects::Script*>(script);auto img=static_cast<movement_effects::Image*>(image);
 CHECK(!dry&&speed&&casting&&s!=&img->script&&img->parent==casting->flingy.sprite);
 // Decode only the native sound and terminating wait; no weapon/attack opcode.
 CHECK(s->pos==shadow_feedback::offset&&code[s->pos++]==0x18);
 CHECK((code[s->pos]|U32(code[s->pos+1])<<8)==111);s->pos+=2;
 CHECK(code[s->pos++]==5&&code[s->pos++]==1);++sounds;
}
inline void __cdecl command(const U8*,U32){
 // Intentionally ignores native disable predicates: selection filtering must
 // still prevent an order or Shift queue from ever reaching the caster.
 for(U32 i=0;i<12;i++)if(auto u=selections[unique*12+i]){
  ++commands;if(queued)++u->highlight_order_count;else{u->order=6;u->order_target={1200,1200,nullptr};}
 }
}
inline U32 __cdecl blocked(bw::Unit*,const bw::Point*,bw::Point*,const void*,U32,U32){return 0;}
inline std::vector<U32> registered;
inline U32 __cdecl register_command(U32 id,void (__cdecl*)(const U8*,U32,U32,U32,rework_combat_v5::CommandNext),U32 (__cdecl*)(const U8*,U32)){registered.push_back(id);return 1;}
}
inline void qa80_sound_per_successful_strike_only(){
 using namespace qa80_fixture;using namespace rework_fixture;
 const auto old_bin=movement_effects::get_bin;
 for(U32 id:{61u,74u,75u})for(U32 scenario:{0u,1u,2u}){
  qa9_fixture::begin({321});relocation();projectile_audit_fixture::load_dimensions();
  auto u=unit(id,1,500,500),enemy=unit(37,6,692,500);u->order=10;multi_fixture::target(u,enemy);casting=u;
  bw::SpriteScr sprite{};movement_effects::Image image{};sprite.main_image=&image;image.parent=&sprite;image.script={7,8,9,10,11};u->flingy.sprite=&sprite;
  const auto animation=image.script;code.fill(0);std::memcpy(code.data(),movement_effects::data::kIscript,sizeof(movement_effects::data::kIscript));
  rework_combat_v5::script_transform(code.data(),code.size());shadow_feedback::step=sound;movement_effects::get_bin=bin;sounds=0;
  const auto saved_damage=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa75_fixture::record_damage;qa75_fixture::victims.clear();
  rework_combat_v5::shadow_begin(u,enemy);auto s=rework_combat_v5::state(u);CHECK(s->shadow_active&&sounds==0);
  if(scenario==1)enemy->flingy.hitpoints=0;
  if(scenario==2)rework_relocation::native_place=blocked;
  for(U32 i=0;i<5;i++){game.frame_count=100+i*4;rework_combat_v5::focus_tick(u,*s);rework_combat_v5::focus_tick(u,*s);}
  CHECK(sounds==(scenario==0?5u:0u)&&sounds==qa75_fixture::victims.size());
  CHECK(std::memcmp(&animation,&image.script,sizeof(animation))==0&&!s->shadow_active);
  CHECK(u->flingy.position.x==500&&u->flingy.position.y==500);
  combat_effects::original_weapon_damage=saved_damage;shadow_feedback::step=sound_step;movement_effects::get_bin=old_bin;relocation_end();qa9_fixture::end();
 }
 casting=nullptr;
 std::printf("QA80_SHADOW_AUDIO stock_sound=111 each_hit=1 no_duplicate_same_frame=1 dead_target_silent=1 failed_move_silent=1 animation_unchanged=1\n");
}
inline void qa80_commands_filter_unique_selection_and_never_cancel_cast(){
 using namespace qa80_fixture;using namespace rework_fixture;
 const auto old_selections=rework_combat_v5::command_selections;
 for(U32 id:{61u,74u,75u})for(U32 packet:{0x14u,0x15u,0x60u,0x61u,0x1au,0x2bu})for(bool queue:{false,true}){
  qa9_fixture::begin({321});relocation();auto u=unit(id,1,500,500),enemy=unit(37,6,692,500),other=unit(65,1,510,500);u->order=10;multi_fixture::target(u,enemy);
  u->flags|=1;other->flags|=1;selections.fill(nullptr);unique=0;selections[0]=u;selections[1]=other;selections[12]=other;
  rework_combat_v5::command_selections=selected;const auto saved_damage=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=qa75_fixture::record_damage;qa75_fixture::victims.clear();
  rework_combat_v5::shadow_begin(u,enemy);auto s=rework_combat_v5::state(u);CHECK(s->shadow_active);
  queued=queue;commands=0;const U8 data[]={U8(packet),0};
  for(U32 i=0;i<5;i++){
   game.frame_count=100+i*4;
   if(packet==0x1a||packet==0x2b)rework_combat_v5::shadow_command(data,2,1,unique,command);else rework_combat_v5::motion_command(data,2,1,unique,command);
   CHECK(commands==i+1&&u->order==10&&u->order_target.unit==enemy&&u->highlight_order_count==0);
   CHECK(selections[0]==u&&selections[1]==other&&selections[12]==other&&!u->lockdown_timer&&!(u->flags&0x400u));
   {rework_combat_v5::CommandScope outer(1);CHECK((u->flags&0x400u)&&!u->lockdown_timer);
    {rework_combat_v5::CommandScope inner(1);rework_combat_v5::focus_tick(u,*s);}
    CHECK((u->flags&0x400u)&&!u->lockdown_timer);}
   CHECK(!(u->flags&0x400u)&&qa75_fixture::victims.size()==i+1);
  }
  CHECK(!s->shadow_active&&u->flingy.position.x==500&&u->flingy.position.y==500);
  rework_combat_v5::motion_command(data,2,1,unique,command);CHECK(commands==7);
  CHECK(queue?u->highlight_order_count==1:u->order==6);
  combat_effects::original_weapon_damage=saved_damage;relocation_end();qa9_fixture::end();
 }
 selections.fill(nullptr);rework_combat_v5::command_selections=old_selections;
 reset();api.selections=reinterpret_cast<GenericFn>(factory<selected>);api.hook_ingame_command=reinterpret_cast<GenericFn>(register_command);registered.clear();
 plugin_init_open=true;CHECK(rework_combat_v5::bind_motion_commands(&api));plugin_init_open=false;
 CHECK(registered==std::vector<U32>({0x14,0x15,0x60,0x61,0x1a,0x2b}));rework_combat_v5::command_selections=old_selections;
 std::printf("QA80_SHADOW_COMMANDS classic_remastered=1 unique_player_row=1 mixed_selection=1 queued_ignored=1 no_synthetic_lockdown=1 reentrant_cast_survives=1 selection_restored=1 five_hits_return=1 unlock=1\n");
}
inline constexpr std::size_t qa80_group_count=2;
inline void run_qa80_groups(){qa80_sound_per_successful_strike_only();qa80_commands_filter_unique_selection_and_never_cancel_cast();}
}
