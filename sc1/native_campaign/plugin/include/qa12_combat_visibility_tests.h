#pragma once
namespace host_test {
inline constexpr std::size_t qa12_extra_group_count=6;
namespace qa12_extra {
inline U32 yamato_hits=0;
inline void __cdecl impact(bw::Bullet* b){
 ++yamato_hits;auto target=b->target.unit;CHECK(target && rework_combat_v5::DamageScope::current_percent==200);
 std::int32_t damage=260*256;{rework_combat_v5::DamageScope hit(target,nullptr,30,1,damage);}target->flingy.hitpoints-=damage;
}
inline bool cast_succeeded=false;
inline void __cdecl cast(bw::Unit* u){const auto cost=raw_value(4,3,8)*256;cast_succeeded=u->energy>=cost;if(cast_succeeded)u->energy=std::uint16_t(u->energy-cost);}
inline std::array<campaign_visibility::Fow,16> fows{};
inline std::array<bw::SpriteScr,16> ghosts{};inline U32 created=0,attempts=0;inline bool fail=false;
inline campaign_visibility::Fow* __cdecl first(){return created?fows.data():nullptr;}
inline void __cdecl position(void* value,std::uint16_t* out){auto s=static_cast<bw::SpriteScr*>(value);out[0]=std::uint16_t(s->position[0]);out[1]=std::uint16_t(s->position[1]);}
inline campaign_visibility::Fow* __cdecl create(U32 index,std::uint16_t type,bw::SpriteScr* sprite){
 ++attempts;CHECK(index && index<=g.units_count);CHECK(g.units[index-1].flingy.sprite==sprite);if(fail)return nullptr;CHECK(created<16);
 ghosts[created]=*sprite;auto& node=fows[created];node={};node.unit_id=type;node.sprite=&ghosts[created];if(created)fows[created-1].next=&node;++created;return &node;
}
inline U32 __cdecl write(std::size_t address,const U8* bytes,std::size_t length){std::memcpy(reinterpret_cast<void*>(address),bytes,length);return 1;}
}
inline void qa12_yamato_primary_extras_and_single_target(){
 using namespace rework_fixture;
 for(U32 neighbours=0;neighbours<3;neighbours++)for(bool dead_caster:{false,true}){
  qa9_fixture::begin({64});auto caster=unit(12,1,100,100),target=unit(106,6,200,100);caster->energy=100*256;target->flingy.hitpoints=4000*256;
  std::array<bw::Unit*,2> others{};for(U32 i=0;i<neighbours;i++){others[i]=unit(106,6,300+int(i),100);others[i]->flingy.hitpoints=4000*256;}
  auto outside=unit(106,6,330,100),ally=unit(106,1,210,100);auto shot=bullet(caster,target,30);if(dead_caster)kill(caster);
  qa12_extra::yamato_hits=0;{rework_combat_v5::MissileScope missile(shot,qa12_extra::impact);qa12_extra::impact(shot);}
  CHECK(qa12_extra::yamato_hits==3);CHECK(target->flingy.hitpoints==(4000-520*int(3-neighbours))*256);
  for(U32 i=0;i<neighbours;i++)CHECK(others[i]->flingy.hitpoints==(4000-520)*256);
  CHECK(outside->flingy.hitpoints==256000 && ally->flingy.hitpoints==256000 && caster->energy==100*256);qa9_fixture::end();
 }
}
inline void qa12_yamato_seventy_five_native_cost_and_owner_scope(){
 using namespace qa12_fixture;begin(64,false);g.applied=false;CHECK(apply_snapshot(nullptr,talent(64)));
 CHECK(raw_value(4,3,8)==150 && owner_stat(1,{4,3,8})==75 && owner_stat(6,{4,3,8})==150);
 auto caster=produce(12),enemy=produce(12,6);complete(caster,75);complete(enemy,75);
 // Exact engine ordering: energy requirement is tested before deduction.
 qa12_extra::cast_succeeded=false;owner_unit_hook(caster,qa12_extra::cast);CHECK(qa12_extra::cast_succeeded && caster->energy==0);
 complete(caster,74);owner_unit_hook(caster,qa12_extra::cast);CHECK(!qa12_extra::cast_succeeded && caster->energy==74*256);
 owner_unit_hook(enemy,qa12_extra::cast);CHECK(!qa12_extra::cast_succeeded && enemy->energy==75*256);
 complete(enemy,150);owner_unit_hook(enemy,qa12_extra::cast);CHECK(qa12_extra::cast_succeeded && enemy->energy==0);
 {OwnerDatScope own(1,1,caster);CHECK(raw_value(4,3,8)==75);{OwnerDatScope foe(6,6,enemy);CHECK(raw_value(4,3,8)==150);}CHECK(raw_value(4,3,8)==75);}CHECK(raw_value(4,3,8)==150);
 end();
}
inline void qa12_fog_buildings_only_last_known_and_retry(){
 using namespace qa12_extra;qa9_fixture::begin({});auto old=g.mission;auto mission=*old;mission.mission_id=206;g.mission=&mission;
 campaign_visibility::reset();campaign_visibility::first=first;campaign_visibility::create=create;rework_combat_v5::get_sprite_position=position;rework_combat_v5::get_tiles=qa10_fixture::get_tiles;created=attempts=0;fail=false;fows={};ghosts={};
 auto enemy=rework_fixture::unit(106,6,200,100),mobile=rework_fixture::unit(37,6,210,100),own=rework_fixture::unit(106,1,220,100),fake=rework_fixture::unit(106,6,230,100);fake->flags|=0x40000000u;
 for(auto u:{enemy,mobile,own,fake}){auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);sprite->visibility_mask=0;sprite->position[0]=u->flingy.position.x;sprite->position[1]=u->flingy.position.y;}
 qa10_fixture::tiles.fill(0xa55affffu);campaign_visibility::step();CHECK(created==1 && attempts==1 && fows[0].unit_id==106 && ghosts[0].visibility_mask==2);
 CHECK(static_cast<bw::SpriteScr*>(enemy->flingy.sprite)->visibility_mask==0 && (qa10_fixture::tiles[0]&255u)==255u);
 static_cast<bw::SpriteScr*>(enemy->flingy.sprite)->position[0]=300;campaign_visibility::step();CHECK(created==1 && ghosts[0].position[0]==200);
 ++enemy->minor_unique_index;fail=true;campaign_visibility::step();CHECK(created==1 && attempts==2);fail=false;campaign_visibility::step();CHECK(created==2 && attempts==3 && ghosts[1].position[0]==300);
 campaign_visibility::reset();campaign_visibility::step();CHECK(created==2 && attempts==3); // Existing ghost deduplicates.
 auto visible=rework_fixture::unit(109,6,400,100);campaign_visibility::step();CHECK(created==2); // Native sight handles it.
 (void)visible;g.mission=old;campaign_visibility::first=nullptr;campaign_visibility::create=nullptr;rework_combat_v5::get_tiles=nullptr;campaign_visibility::reset();qa9_fixture::end();
}
inline void qa12_native_helpers_reject_changed_witnesses(){
 const auto size=0x400000u;auto memory=static_cast<U8*>(VirtualAlloc(nullptr,size,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(memory);
 using namespace campaign_visibility;std::memcpy(memory+0x19fa10,create_bytes,sizeof(create_bytes));std::memcpy(memory+0x1e332b,create_call,sizeof(create_call));
 CHECK(native_bytes(memory));memory[0x1e332b]^=1;CHECK(!native_bytes(memory));memory[0x1e332b]^=1;
 using namespace rework_cargo_v5;std::memcpy(memory+0x1e1e60,unload_bytes,sizeof(unload_bytes));std::memcpy(memory+0x1e1250,detach_bytes,sizeof(detach_bytes));std::memcpy(memory+0x1e1fe9,detach_call,sizeof(detach_call));
 CHECK(rework_cargo_v5::native_bytes(memory));memory[0x1e1250]^=1;CHECK(!rework_cargo_v5::native_bytes(memory));CHECK(VirtualFree(memory,0,MEM_RELEASE));
}
inline void qa12_yamato_tooltip_native_relay_and_boundary(){
 using namespace qa12_fixture;namespace ui=yamato_cost_ui;begin(64);auto caster=produce(12),enemy=produce(12,6);complete(caster);complete(enemy);ui::publish();
 CHECK(ui::value(caster,8,150)==75 && ui::value(enemy,8,150)==150 && ui::value(caster,7,100)==100 && ui::value(nullptr,8,150)==150);
 auto memory=static_cast<U8*>(VirtualAlloc(nullptr,0x1450000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(memory);std::memcpy(memory+ui::site,ui::original,8);
 CHECK(ui::register_at(memory,qa12_extra::write) && ui::verify_installation());
 std::vector<U8> body={0x53,0x48,0x83,0xec,0x20,0x89,0xcb,0x41,0x89,0xd1,0x48,0xb8};economy_ui_fixture::append64(body,reinterpret_cast<std::uintptr_t>(ui::code));
 for(int byte:{0xff,0xd0,0x48,0x83,0xc4,0x20,0x5b,0xc3})body.push_back(U8(byte));
 auto helper=economy_ui_fixture::executable(body);
 for(auto selected:{caster,enemy}){std::memcpy(memory+0x10a4458,&selected,sizeof(selected));reinterpret_cast<void (__cdecl*)(U32,U32)>(helper)(8,150);std::uint16_t result=0;std::memcpy(&result,memory+ui::output,2);CHECK(result==(selected==caster?75:150));}
 memory[ui::site]^=1;CHECK(!ui::verify_installation());memory[ui::site]^=1;CHECK(ui::verify_installation());
 CHECK(VirtualFree(helper,0,MEM_RELEASE));CHECK(RtlDeleteFunctionTable(&ui::unwind));CHECK(VirtualFree(ui::code,0,MEM_RELEASE));CHECK(VirtualFree(memory,0,MEM_RELEASE));ui::code=ui::module=nullptr;ui::queued=false;ui::reset();end();
}
inline void qa12_detector_following_survives_prior_target_refresh(){
 using namespace wave_target_tests;
 for(U32 id:{9u,42u,84u,22u,57u}){
  rework_wave_tests::begin(101);auto base=add(106,player_owner(),1800,1000);base->flags=1;
  auto leader=wave(0,4,1000,1000),escort=wave(id,4,1000,1050);leader->flags=escort->flags=1;
  rework_curses::identities.resize(g.units_count);auto& identity=rework_curses::identities[std::size_t(escort-g.units)];identity.wave=1;identity.unique=escort->minor_unique_index;identity.owner=escort->player;identity.type=escort->unit_id;
  auto original=add(id,4,900,900);const auto before=*original;
  CHECK(wave_targeting::detector(escort));
  // Production tick invokes major_original_assault (and its target refresh)
  // before wave_targeting::step. Reproduce that exact cache ordering.
  for(U32 frame=0;frame<=240;frame+=24){
   game.frame_count=frame;leader->flingy.position.x=std::int16_t(1000+frame*2);leader->order=14;
   wave_targeting::refresh();wave_targeting::step(true,false);
  }
  CHECK(escort->order==6 && escort->order_target.x==leader->flingy.position.x);
  const auto n=issued.size();wave_targeting::step(true,false);CHECK(issued.size()==n);
  for(U32 ai_idle:{49u,163u}){game.frame_count+=48;escort->order=U8(ai_idle);wave_targeting::refresh();wave_targeting::step(true,false);CHECK(escort->order==6);}
  game.frame_count+=48;escort->order=114;wave_targeting::step(true,false);CHECK(escort->order==114); // Preserve casting.
  game.frame_count+=48;escort->order=3;escort->stasis_timer=1;wave_targeting::step(true,false);CHECK(escort->order==3);escort->stasis_timer=0;
  game.frame_count+=48;escort->player=U8(player_owner());wave_targeting::step(true,false);CHECK(escort->order==3);
  CHECK(std::memcmp(original,&before,sizeof(before))==0);
 }
 wave_targeting::reset();
}
inline void run_qa12_extra_groups(){qa12_yamato_primary_extras_and_single_target();qa12_yamato_seventy_five_native_cost_and_owner_scope();qa12_fog_buildings_only_last_known_and_retry();qa12_native_helpers_reject_changed_witnesses();qa12_yamato_tooltip_native_relay_and_boundary();qa12_detector_following_survives_prior_target_refresh();}
}
