#pragma once
namespace host_test {
inline constexpr std::size_t area_visual_group_count=5;
namespace area_fixture {
using namespace area_visuals;
inline void quad(std::vector<U8>& bytes,std::size_t offset,std::size_t stride,float zoom=1){
 const float points[4][2]={{100,200},{140,200},{100,220},{140,220}};
 for(U32 i=0;i<4;++i){float xy[]={points[i][0]*zoom,points[i][1]*zoom};std::memcpy(bytes.data()+offset+i*stride,xy,8);}
}
inline Image image(){Image value{};value.image_id=525;value.map_position={500,600};value.bounds[0]=4;value.bounds[1]=8;value.bounds[2]=40;value.bounds[3]=20;return value;}
inline std::unique_ptr<Commands> gpu;inline Vertices vertices{};inline std::vector<U8> bytes,previous;
inline U32 originals=0,registrations=0;inline void (__cdecl* callback)(void*,Draw)=nullptr;
inline void __cdecl position(void*,std::uint16_t* xy){xy[0]=524;xy[1]=618;}
inline LoneSprite* lone_head=nullptr;
inline LoneSprite* __cdecl lone(){return lone_head;}
inline GenericFn __cdecl lone_factory(){CHECK(require_init());return reinterpret_cast<GenericFn>(lone);}
inline GenericFn __cdecl position_factory(){CHECK(require_init());return reinterpret_cast<GenericFn>(position);}
inline U32 __cdecl hook(void (__cdecl* value)(void*,Draw)){CHECK(require_init());++registrations;callback=value;return 1;}
inline void __cdecl supports(const std::uint16_t* ids,U8* values,std::size_t n){CHECK(require_init());CHECK(n==2&&ids[0]==62&&ids[1]==63);values[0]=values[1]=2;}
inline void __cdecl variables(const std::uint16_t* ids,std::size_t* values,std::size_t n){CHECK(n==2&&ids[0]==62&&ids[1]==63);values[0]=reinterpret_cast<std::size_t>(gpu.get());values[1]=reinterpret_cast<std::size_t>(&vertices);}
inline void __cdecl original(void*){
 ++originals;gpu->count=1;auto& command=gpu->commands[0];command={};command.allocated_vertices=command.used_vertices=4;
 bytes.assign(64,0xa5);quad(bytes,0,16);vertices={16,64,bytes.data()};
}
}
inline void area_visual_geometry_scales_native_xy_preserving_other_attributes(){
 using namespace area_fixture;
 for(std::size_t stride:{8u,16u,20u,24u,32u})for(float zoom:{1.0f,2.0f}){
  auto commands=std::make_unique<Commands>();commands->count=1;auto& command=commands->commands[0];command.allocated_vertices=command.used_vertices=4;
  command.shader=stride==8?2u:stride==20?6u:stride==24?11u:stride==32?32u:0u;
  std::vector<U8> data(stride*4,0xa5);quad(data,0,stride,zoom);const auto before=data;
  Vertices buffer{data.size()/4,data.size(),data.data()};const auto view=image();const auto saved=view;
  CHECK(transform(*commands,buffer,0,0,view,{2,3},524,618)==4);
  const float wanted[4][2]={{80,180},{160,180},{80,240},{160,240}};
  for(U32 i=0;i<4;++i){float xy[2];std::memcpy(xy,data.data()+i*stride,8);CHECK(std::abs(xy[0]-wanted[i][0]*zoom)<0.001f&&std::abs(xy[1]-wanted[i][1]*zoom)<0.001f);
   for(std::size_t at=8;at<stride;++at)CHECK(data[i*stride+at]==before[i*stride+at]);}
  CHECK(std::memcmp(&view,&saved,sizeof(view))==0);
 }
}
inline void area_visual_batched_vertices_and_malformed_geometry_are_isolated(){
 using namespace area_fixture;auto commands=std::make_unique<Commands>();commands->count=1;
 auto& command=commands->commands[0];command.allocated_vertices=command.used_vertices=8;
 std::vector<U8> data(128,0xa5);quad(data,0,16);quad(data,64,16);const auto before=data;
 Vertices buffer{32,128,data.data()};const U32 used[]={4};CHECK(transform(*commands,buffer,1,128,image(),{2,2},524,618,used)==4);
 CHECK(std::memcmp(before.data(),data.data(),64)==0);float first[2];std::memcpy(first,data.data()+64,8);CHECK(first[0]==80&&first[1]==190);
 for(U32 bad=0;bad<6;++bad){data=before;commands->count=1;command={};command.allocated_vertices=command.used_vertices=4;buffer={32,64,data.data()};
  if(bad==0)command.vertex_offset=4;
  if(bad==1)command.used_vertices=5;
  if(bad==2)buffer.capacity_floats=1;
  if(bad==3)buffer.used_bytes=63;
  if(bad==4){commands->count=2;commands->commands[1]=command;}
  if(bad==5){const float invalid=std::numeric_limits<float>::infinity();std::memcpy(data.data(),&invalid,4);}
  const auto saved=data;CHECK(transform(*commands,buffer,0,0,image(),{2,2},524,618)==0);CHECK(data==saved);
 }
}
inline void area_visual_actual_policy_uses_owner_stats_fields_and_irradiation_lineage(){
 qa13_fixture::begin();auto snapshot=economy_snapshot({44,61,80,124,127,129,144});CHECK(apply_snapshot(nullptr,snapshot));
 using namespace rework_combat_v5;bw::SpriteScr field_sprite{},enemy_sprite{},own_sprite{};
 auto field=add(202,12,600,600);field->flingy.sprite=&field_sprite;
 Persist zone{};zone.target=identity(field);zone.owner=player_owner();zone.kind=83;zone.until=1000;zone.remaining=zone.ticks=320;persistent.push_back(zone);
 auto irradiated=add(0,6,700,700);irradiated->flingy.sprite=&enemy_sprite;irradiated->irradiate_timer=75;auto caster=add(9,player_owner(),100,100);
 bw::Bullet storm{};storm.flingy.sprite=&own_sprite;projectiles[&storm].source.owner=player_owner();projectiles[&storm].weapon=84;
 irradiation::attach(irradiated,caster,player_owner());area_visuals::publish(true);const auto state=area_visuals::current();CHECK(state&&state->active);
 area_visuals::Image image{};image.parent=&own_sprite;own_sprite.player=U8(player_owner());image.image_id=525;
 CHECK(std::abs(area_visuals::scale(*state,image).x-double(owner_stat(player_owner(),{1,13,84}))/original_stat({1,13,84}))<0.00001);
 own_sprite.player=6;CHECK(area_visuals::scale(*state,image).enlarged()); // Source identity, not a neutral/colored visual owner.
 auto hostile=std::make_shared<area_visuals::Frame>(*state);hostile->spell_owners[&own_sprite]=6;CHECK(!area_visuals::scale(*hostile,image).enlarged());
 image.image_id=337;image.parent=&field_sprite;CHECK(area_visuals::scale(*state,image).x==4&&area_visuals::scale(*state,image).y==4);
 image.image_id=380;image.parent=&enemy_sprite;CHECK(area_visuals::scale(*state,image).x==4);
 image.image_id=0;CHECK(!area_visuals::scale(*state,image).enlarged());
 const auto old_lone=area_visuals::first_lone;const auto old_position=area_visuals::get_position;
 bw::SpriteScr cloud{};area_visuals::Image cloud_image{};cloud_image.image_id=383;cloud_image.parent=&cloud;cloud.main_image=&cloud_image;cloud.player=12;
 area_visuals::LoneSprite lone{};lone.sprite=&cloud;area_fixture::lone_head=&lone;area_visuals::first_lone=area_fixture::lone;area_visuals::get_position=area_fixture::position;
 area_visuals::note(58,player_owner(),524,618);area_visuals::publish(true);CHECK(area_visuals::scale(*area_visuals::current(),cloud_image).enlarged());
 area_visuals::note(58,6,524,618);area_visuals::publish(true);CHECK(!area_visuals::scale(*area_visuals::current(),cloud_image).enlarged()); // Ambiguous overlapping sources keep native visuals.
 game.frame_count=120;area_visuals::note(58,6,524,618);area_visuals::publish(true);CHECK(!area_visuals::scale(*area_visuals::current(),cloud_image).enlarged());
 area_visuals::first_lone=old_lone;area_visuals::get_position=old_position;area_fixture::lone_head=nullptr;
 area_visuals::reset();CHECK(!area_visuals::current());qa13_fixture::end();
}
inline void area_visual_registered_callback_rereads_reallocated_vertex_storage(){
 using namespace area_fixture;reset();gpu=std::make_unique<Commands>();vertices={};bytes.clear();originals=registrations=0;
 const auto was_registered=registered;const auto old_reader=area_visuals::read_vars;const auto old_position=get_position;const auto old_lone=first_lone;const auto old_event=rework_combat_v5::area_visual_event;
 registered=false;samase::PluginApi local{};local.version=44;local.read_vars=variables;local.load_vars=supports;local.hook_draw_image=reinterpret_cast<GenericFn>(hook);local.get_sprite_position=reinterpret_cast<GenericFn>(position_factory);local.first_lone_sprite=reinterpret_cast<GenericFn>(lone_factory);
 plugin_init_open=true;CHECK(bind(&local));plugin_init_open=false;CHECK(registrations==1&&callback==draw);
 auto state=std::make_shared<Frame>();state->active=true;state->owner=1;state->images[525]={2,2};
 bw::SpriteScr sprite{};sprite.player=1;auto view=image();view.parent=&sprite;state->spell_owners[&sprite]=1;store(state);
 callback(&view,original);CHECK(originals==1&&vertices.data==bytes.data());float xy[2];std::memcpy(xy,bytes.data(),8);CHECK(xy[0]==80&&xy[1]==190);
 area_visuals::reset();gpu->count=0;vertices.used_bytes=0;callback(&view,original);CHECK(originals==2);std::memcpy(xy,bytes.data(),8);CHECK(xy[0]==100&&xy[1]==200);
 registered=was_registered;area_visuals::read_vars=old_reader;get_position=old_position;first_lone=old_lone;rework_combat_v5::area_visual_event=old_event;gpu.reset();
}
inline void area_haste_reaches_native_iscript_move_and_prediction_without_overflow(){
 using namespace movement_fixture;
 for(U32 rank:{1u,3u,256u,0xffffffffu}){
  begin();g.growth.wire_version=2;g.growth.curse_counts[19]=U8(std::min(rank,255u));g.growth.talent_ranks[28]=rank;g.current_wave_id=1;
  auto enemy=unit(37,6);rework_waves::finish_created(enemy,0,100,100,500,500);auto tag=rework_curses::identity(enemy);CHECK(tag);enemy->flags=(enemy->flags&~0x04009000u)|tag->saved_flags;tag->appearance_until=0;
  auto friendly=unit(37,player_owner());movement_effects::ratio_extension=rework_combat_v5::movement_extension;
  active_script=enemy;native_move_result(enemy);const auto saved=enemy->flingy;U32 prediction=2560;
  invoke(0xcd,image(enemy),1,&prediction);const auto expected=U32(std::min<std::uint64_t>(0xffffffffu,(2560ull*rework_curses::speed_percent(enemy)+50)/100));
  CHECK(prediction==expected&&std::memcmp(&saved,&enemy->flingy,sizeof(saved))==0);
  invoke(0xcd,image(enemy));CHECK(enemy->flingy.next_speed==std::int32_t(std::min(0x7fffffffu,expected)));
  active_script=friendly;native_move_result(friendly);invoke(0xcd,image(friendly));CHECK(friendly->flingy.next_speed==2560);
 }
 CHECK(movement_effects::scaled(0x7fffffff,{0xffffffffffffffffull,100})==0x7fffffff);
}
inline void run_area_visual_groups(){area_visual_geometry_scales_native_xy_preserving_other_attributes();area_visual_batched_vertices_and_malformed_geometry_are_isolated();area_visual_actual_policy_uses_owner_stats_fields_and_irradiation_lineage();area_visual_registered_callback_rereads_reallocated_vertex_storage();area_haste_reaches_native_iscript_move_and_prediction_without_overflow();}
}
