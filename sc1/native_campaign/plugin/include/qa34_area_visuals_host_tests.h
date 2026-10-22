#pragma once
namespace host_test {
inline constexpr std::size_t qa34_area_group_count=6;
inline void area_hd_reserved_batch_tail_does_not_define_vertex_stride(){
 using namespace area_fixture;
 auto commands=std::make_unique<Commands>();commands->count=2;
 auto& batch=commands->commands[0];batch.allocated_vertices=1024;batch.used_vertices=8;batch.shader=26;
 auto& other=commands->commands[1];other.vertex_offset=128;other.allocated_vertices=other.used_vertices=4;other.shader=25;
 std::vector<U8> data(16384,0xa5);quad(data,0,16);quad(data,64,16);quad(data,128,16);const auto before=data;
 Vertices buffer{data.size()/4,data.size(),data.data()};const U32 saved_used[]={4,4};
 CHECK(transform(*commands,buffer,2,data.size(),image(),{2,3},524,618,saved_used)==4);
 float xy[2];std::memcpy(xy,data.data()+64,8);CHECK(xy[0]==80&&xy[1]==180);
 CHECK(std::memcmp(data.data(),before.data(),64)==0);
 CHECK(std::memcmp(data.data()+128,before.data()+128,data.size()-128)==0);
 for(U32 v=0;v<4;++v)CHECK(std::memcmp(data.data()+64+v*16+8,before.data()+64+v*16+8,8)==0);
}
inline void area_new_image_can_reuse_a_freed_vertex_allocation(){
 using namespace area_fixture;auto commands=std::make_unique<Commands>();commands->count=2;
 auto& old=commands->commands[0];old.allocated_vertices=1024;old.used_vertices=4;old.shader=26;
 auto& fresh=commands->commands[1];fresh.vertex_offset=64;fresh.allocated_vertices=fresh.used_vertices=4;fresh.shader=25;
 std::vector<U8> data(16384,0xa5);quad(data,0,16);quad(data,64,16);const auto before=data;
 Vertices buffer{data.size()/4,data.size(),data.data()};const U32 saved_used[]={4};
 CHECK(transform(*commands,buffer,1,data.size(),image(),{2,2},524,618,saved_used)==4);
 float xy[2];std::memcpy(xy,data.data()+64,8);CHECK(xy[0]==80&&xy[1]==190);
 CHECK(std::memcmp(data.data(),before.data(),64)==0);
 CHECK(std::memcmp(data.data()+128,before.data()+128,data.size()-128)==0);
 // An actual overlap with another image must leave the entire buffer intact.
 data=before;fresh.vertex_offset=48;CHECK(transform(*commands,buffer,1,data.size(),image(),{2,2},524,618,saved_used)==0);CHECK(data==before);
}
inline void area_alignment_padding_is_not_a_vertex_attribute(){
 using namespace area_fixture;auto commands=std::make_unique<Commands>();commands->count=2;
 auto& effect=commands->commands[0];effect.allocated_vertices=effect.used_vertices=4;effect.shader=0;
 auto& next=commands->commands[1];next.vertex_offset=80;next.allocated_vertices=next.used_vertices=4;next.shader=25;
 std::vector<U8> data(144,0xa5);quad(data,0,16);quad(data,80,16);const auto before=data;
 Vertices buffer{data.size()/4,data.size(),data.data()};const U32 saved_used[]={0,4};
 CHECK(transform(*commands,buffer,2,data.size(),image(),{2,2},524,618,saved_used)==4);
 CHECK(std::memcmp(data.data()+64,before.data()+64,data.size()-64)==0);
 for(U32 v=0;v<4;++v){float xy[2];std::memcpy(xy,data.data()+v*16,8);CHECK(xy[0]==(v%2?160:80)&&xy[1]==(v/2?230:190));CHECK(std::memcmp(data.data()+v*16+8,before.data()+v*16+8,8)==0);}
}
inline void area_all_effect_images_scale_normalized_hd_vertices(){
 using namespace area_fixture;
 for(U32 id:{337u,364u,380u,381u,382u,383u,525u,548u,549u,550u,551u,552u,553u,555u,556u,951u,998u}){
  auto commands=std::make_unique<Commands>();commands->count=1;auto& command=commands->commands[0];command.shader=25;command.allocated_vertices=1024;command.used_vertices=4;
  std::vector<U8> data(16384,0xa5);quad(data,0,16,.001f);const auto before=data;Vertices buffer{data.size()/4,data.size(),data.data()};auto view=image();view.image_id=std::uint16_t(id);
  CHECK(transform(*commands,buffer,0,0,view,{2,3},524,618)==4);
  const float wanted[4][2]={{.08f,.18f},{.16f,.18f},{.08f,.24f},{.16f,.24f}};
  for(U32 v=0;v<4;++v){float xy[2];std::memcpy(xy,data.data()+v*16,8);CHECK(std::abs(xy[0]-wanted[v][0])<.000001f&&std::abs(xy[1]-wanted[v][1])<.000001f);CHECK(std::memcmp(data.data()+v*16+8,before.data()+v*16+8,8)==0);}
  CHECK(std::memcmp(data.data()+64,before.data()+64,data.size()-64)==0);
 }
}
inline void area_registered_callback_scales_recycled_hd_geometry(){
 using namespace area_fixture;reset();gpu=std::make_unique<Commands>();gpu->count=1;
 auto& old=gpu->commands[0];old.shader=26;old.allocated_vertices=1024;old.used_vertices=4;
 bytes.assign(16384,0xa5);quad(bytes,0,16);vertices={bytes.size()/4,bytes.size(),bytes.data()};
 const auto saved=bytes;const auto old_reader=area_visuals::read_vars;const auto old_position=get_position;
 area_visuals::read_vars=variables;get_position=position;
 bw::SpriteScr sprite{};auto view=image();view.parent=&sprite;
 auto state=std::make_shared<Frame>();state->active=true;state->owner=1;state->images[525]={2,2};state->spell_owners[&sprite]=1;store(state);
 const auto native=[](void*){++originals;gpu->count=2;auto& fresh=gpu->commands[1];fresh={};fresh.shader=25;fresh.is_hd=1;fresh.vertex_offset=64;fresh.allocated_vertices=fresh.used_vertices=4;quad(bytes,64,16);};
 const auto calls=originals;draw(&view,native);CHECK(originals==calls+1);
 float xy[2];std::memcpy(xy,bytes.data()+64,8);CHECK(xy[0]==80&&xy[1]==190);
 CHECK(std::memcmp(bytes.data(),saved.data(),64)==0&&std::memcmp(bytes.data()+128,saved.data()+128,bytes.size()-128)==0);
 const auto scaled=bytes;gpu->commands[1].shader=43;const U32 saved_used[]={4,0};
 CHECK(transform(*gpu,vertices,2,vertices.used_bytes,view,{2,2},524,618,saved_used)==0);CHECK(bytes==scaled);
 area_visuals::read_vars=old_reader;get_position=old_position;reset();gpu.reset();
}
inline void area_hd_camera_clipping_preserves_the_world_pivot(){
 using namespace area_fixture;
 U8 grp[6+2*(4+sizeof(void*))]{};grp[0]=2;grp[2]=40;grp[4]=20;grp[8]=3;grp[9]=4;grp[6+4+sizeof(void*)+2]=40;grp[6+4+sizeof(void*)+3]=20;
 for(float zoom:{1.0f,.001f})for(U32 camera=0;camera<40;++camera){
  auto commands=std::make_unique<Commands>();commands->count=1;auto& command=commands->commands[0];command.is_hd=1;command.shader=25;command.allocated_vertices=command.used_vertices=4;
  std::vector<U8> data(64,0xa5);quad(data,0,16,zoom);for(U32 n=0;n<4;++n){float xy[2];std::memcpy(xy,data.data()+n*16,8);xy[0]-=camera*zoom;xy[1]-=std::min(camera,19u)*zoom;std::memcpy(data.data()+n*16,xy,8);}
  auto view=image();view.grp=grp;view.frame=1;U32 width=0,height=0;CHECK(frame_dimensions(view,width,height)&&width==40&&height==20);view.bounds[0]=std::int16_t(camera);view.bounds[1]=std::int16_t(std::min(camera,19u));view.bounds[2]=std::int16_t(40-camera);view.bounds[3]=std::int16_t(20-std::min(camera,19u));
  Vertices buffer{16,64,data.data()};CHECK(transform(*commands,buffer,0,0,view,{2,3},524,618)==4);
  for(U32 n=0;n<4;++n){float xy[2];std::memcpy(xy,data.data()+n*16,8);CHECK(std::abs(xy[0]-(n%2?160-camera:80-camera)*zoom)<.001f);CHECK(std::abs(xy[1]-(n/2?240-std::min(camera,19u):180-std::min(camera,19u))*zoom)<.001f);}
  const auto before=data;view.grp=nullptr;CHECK(transform(*commands,buffer,0,0,view,{2,3},524,618)==0);CHECK(data==before);
 }
}
inline void run_qa34_area_groups(){area_hd_reserved_batch_tail_does_not_define_vertex_stride();area_new_image_can_reuse_a_freed_vertex_allocation();area_alignment_padding_is_not_a_vertex_attribute();area_all_effect_images_scale_normalized_hd_vertices();area_registered_callback_scales_recycled_hd_geometry();area_hd_camera_clipping_preserves_the_world_pivot();}
}
