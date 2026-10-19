#pragma once
// API44 drawing only. Public SCR DrawCommand layout; buffer offsets attested
// against the same13515 image already required by the native runtime.
namespace area_visuals {
struct Scale {double x=1,y=1;bool enlarged() const noexcept{return x>1.00001||y>1.00001;}};
struct Frame {
 U32 owner=12;bool active=false;
 std::array<Scale,999> images{};
 std::unordered_map<const void*,Scale> fields,irradiates;
 std::unordered_map<const void*,U32> spell_owners;
};
inline std::shared_ptr<const Frame> published;
inline std::atomic<std::uint64_t> epoch{0},scaled_images{0},scaled_vertices{0},rejected_geometry{0};
inline U32 last_publish=~0u;inline bool registered=false;
using Image=movement_effects::Image;
using Draw=void (__cdecl*)(void*);
using HookDraw=U32 (__cdecl*)(void (__cdecl*)(void*,Draw));
using LoadVars=void (__cdecl*)(const std::uint16_t*,U8*,std::size_t);
inline ReadVars read_vars=nullptr;
inline rework_combat_v5::GetSpritePosition get_position=nullptr;
struct LoneSprite {LoneSprite* prev;LoneSprite* next;std::int32_t hp;bw::SpriteScr* sprite;};
static_assert(sizeof(LoneSprite)==32&&offsetof(LoneSprite,sprite)==24,"Public lone sprite x64 ABI");
using GetLone=LoneSprite* (__cdecl*)();inline GetLone first_lone=nullptr;
struct Event {U32 weapon=130,owner=12,until=0;int x=0,y=0;};
inline std::array<Event,256> events{};inline U32 event_cursor=0;
inline std::array<bool,130> interested{};
inline bool effect(U32 image,U32 weapon) noexcept {
 switch(weapon){case 33:return image==555||image==556;case 58:return image==383;case 70:case 71:return image==548;
 case 83:return image==364;case 84:return image==525||(image>=550&&image<=553);case 108:return image==998;default:return false;}
}
inline void note(U32 weapon,U32 owner,int x,int y) noexcept {
 if(weapon>=interested.size()||!interested[weapon])return;
 if(!effect(555,weapon)&&weapon!=58&&weapon!=70&&weapon!=71&&weapon!=83&&weapon!=84&&weapon!=108)return;
 if(!g.game)return;events[event_cursor++%events.size()]={weapon,owner,g.game()->frame_count+96,x,y};last_publish=~0u;
}
struct Subcommands {std::uintptr_t unused;void* first;};
struct Command {
 U32 render_target,is_hd;std::uintptr_t textures[7];U32 mode,shader;
 std::size_t vertex_offset,index_offset;U32 allocated_vertices,used_vertices;
 std::uint16_t unused,blend;Subcommands before,after;float constants[20];
};
struct Commands {
 Command commands[8192];U8 subcommands[0x20000];U32 subcommand_bytes;
 std::uintptr_t sort[3],unused[6];std::uint16_t count;U32 other;
};
struct Vertices {std::size_t capacity_floats,used_bytes;U8* data;};
static_assert(sizeof(Command)==0xd8&&offsetof(Command,vertex_offset)==0x48&&offsetof(Command,used_vertices)==0x5c,"SCR draw command ABI");
static_assert(sizeof(Commands)==0x1d0058&&offsetof(Commands,count)==0x1d0050,"SCR draw commands ABI");
static_assert(offsetof(Vertices,data)==0x10&&offsetof(Vertices,used_bytes)==8,"SCR vertex buffer prefix");
inline std::size_t vertex_stride(U32 shader) noexcept {
 // Native13515 shader input masks (shader record+0x18). The allocator at
 // 0x798000 sums these attribute widths, independently of reserved capacity,
 // alignment padding and recycled holes. DrawCommand offsets cannot tell us
 // a vertex's width: a 1024-vertex batch releases its unused tail for reuse.
 constexpr U8 formats[]={3,3,1,3,19,19,19,3,3,3,3,35,3,3,3,3,3,3,3,3,3,3,7,3,3,3,3,3,3,3,3,3,15,15,7,7,3,3,3,3,3,3,3};
 if(shader>=std::size(formats))return 0;
 const auto mask=formats[shader];std::size_t bytes=0;
 for(U32 bit=0;bit<6;++bit)if(mask&(1u<<bit))bytes+=bit==4?4:8;
 return bytes;
}
inline bool candidate(U32 id) noexcept {
 switch(id){case 337:case 364:case 380:case 381:case 382:case 383:case 525:case 548:case 549:
 case 550:case 551:case 552:case 553:case 555:case 556:case 951:case 998:return true;default:return false;}
}
inline void store(std::shared_ptr<const Frame> frame) noexcept {
 std::atomic_store_explicit(&published,std::move(frame),std::memory_order_release);epoch.fetch_add(1,std::memory_order_release);
}
inline void reset() noexcept {store({});last_publish=~0u;events={};interested={};event_cursor=0;}
inline const std::shared_ptr<const Frame>& current() noexcept {
 struct Cache {std::uint64_t epoch=~std::uint64_t(0);std::shared_ptr<const Frame> frame;};
 static thread_local Cache cache;
 const auto serial=epoch.load(std::memory_order_acquire);
 if(cache.epoch!=serial){cache.frame=std::atomic_load_explicit(&published,std::memory_order_acquire);cache.epoch=serial;}
 return cache.frame;
}
inline void publish(bool force=false) {
 if(!registered&&!force)return;
 if(!g.active||!g.applied){if(published)reset();return;}
 const U32 now=g.game()->frame_count;if(!force&&last_publish!=~0u&&now-last_publish<4)return;last_publish=now;
 auto frame=std::make_shared<Frame>();frame->active=true;frame->owner=player_owner();
 const auto ratio=[&](U32 weapon){const auto base=original_stat({1,13,weapon});return base?std::max(1.0,double(owner_stat(frame->owner,{1,13,weapon}))/base):1.0;};
 const auto set=[&](std::initializer_list<U32> ids,double scale){for(auto id:ids)frame->images[id]={scale,scale};};
 set({525,550,551,552,553},ratio(84));set({555,556},ratio(33));set({548,549},ratio(70));
 if(rework_combat_v5::rank(80))set({383},double(64+talent_power::v5(80,16))/64);
 if(rework_combat_v5::rank(127)||rework_combat_v5::rank(149))set({364},std::max(rework_combat_v5::rank(127)?double(48+talent_power::v5(127,12))/48:1.0,(talent_power::enabled&&rework_combat_v5::rank(149))?1.5:1.0));
 if(rework_combat_v5::rank(124))set({998},double(48+talent_power::v5(124,12))/48);
 interested={};interested[33]=frame->images[555].enlarged();interested[58]=frame->images[383].enlarged();interested[70]=interested[71]=frame->images[548].enlarged();
 interested[83]=frame->images[364].enlarged();interested[84]=frame->images[525].enlarged();interested[108]=frame->images[998].enlarged();
 for(const auto& pair:rework_combat_v5::projectiles){auto bullet=pair.first;const auto& shot=pair.second;
  if(bullet&&bullet->flingy.sprite&&shot.weapon<interested.size()&&interested[shot.weapon])
   frame->spell_owners[bullet->flingy.sprite]=shot.source.owner;
 }
 U32 visited=0;
 if(first_lone&&get_position&&std::any_of(interested.begin(),interested.end(),[](bool value){return value;}))for(auto lone=first_lone(),previous=static_cast<LoneSprite*>(nullptr);lone&&lone!=previous&&visited++<16384;){
  auto sprite=lone->sprite;if(sprite&&sprite->main_image){auto image=static_cast<Image*>(sprite->main_image);
   if(candidate(image->image_id)){std::uint16_t position[2]{};get_position(sprite,position);const Event* best=nullptr;bool ambiguous=false;std::int64_t nearest=~std::uint64_t(0)>>1;
    for(const auto& event:events)if(event.owner<12&&event.until>=now&&effect(image->image_id,event.weapon)){
     const auto dx=std::int64_t(position[0])-event.x,dy=std::int64_t(position[1])-event.y;const auto distance=dx*dx+dy*dy;
     if(distance<=32ll*32){if(best&&best->owner!=event.owner)ambiguous=true;if(!best||distance<nearest||(distance==nearest&&event.until>best->until)){best=&event;nearest=distance;}}
    }if(best&&!ambiguous)frame->spell_owners[sprite]=best->owner;
   }
  }
  previous=lone;lone=lone->next;if(frame->spell_owners.size()>16384)break;
 }
 for(const auto& field:rework_combat_v5::persistent){
  if(field.owner!=frame->owner||field.until<now||!rework_combat_v5::resolve(field.target))continue;
  auto unit=field.target.p;if(!unit->flingy.sprite)continue;
  if(field.kind==83)frame->fields[unit->flingy.sprite]={double(field.remaining)/80,double(field.ticks?field.ticks:field.remaining)/80};
  if(field.kind==128)frame->fields[unit->flingy.sprite]={double(field.remaining)/60,double(field.ticks)/40};
 }
 if(rework_combat_v5::rank(61)){
  namespace irr=rework_combat_v5::irradiation;
  for(const auto& node:irr::nodes)if(node.active){
   auto root=irr::roots.find(node.root);auto unit=rework_combat_v5::resolve(node.who);
   if(unit&&unit->irradiate_timer&&unit->flingy.sprite&&root!=irr::roots.end()&&root->second.owner==frame->owner)
    frame->irradiates[unit->flingy.sprite]={4,4};
  }
 }
 store(std::move(frame));
 if(registered&&now%240==0)log_event("PERF area_visuals images=%llu vertices=%llu unsupported_geometry=%llu",
  static_cast<unsigned long long>(scaled_images.load(std::memory_order_relaxed)),static_cast<unsigned long long>(scaled_vertices.load(std::memory_order_relaxed)),static_cast<unsigned long long>(rejected_geometry.load(std::memory_order_relaxed)));
}
inline Scale scale(const Frame& frame,const Image& image) noexcept {
 if(!frame.active||!image.parent||image.image_id>=frame.images.size())return {};
 if(image.image_id==337||image.image_id==951){auto it=frame.fields.find(image.parent);return it==frame.fields.end()?Scale{}:it->second;}
 if(image.image_id>=380&&image.image_id<=382){auto it=frame.irradiates.find(image.parent);return it==frame.irradiates.end()?Scale{}:it->second;}
 const auto owner=frame.spell_owners.find(image.parent);
 return owner!=frame.spell_owners.end()&&owner->second==frame.owner?frame.images[image.image_id]:Scale{};
}
inline std::uint64_t transform(Commands& commands,Vertices& vertices,U32 first,std::size_t old_bytes,const Image& image,Scale amount,int center_x,int center_y,const U32* old_used=nullptr) noexcept {
 if(first>commands.count||commands.count>8192||!vertices.data||!std::isfinite(amount.x)||!std::isfinite(amount.y)||amount.x<1||amount.y<1||amount.x>64||amount.y>64||
  vertices.capacity_floats>0x1000000||vertices.used_bytes>vertices.capacity_floats*4||vertices.used_bytes<old_bytes||image.bounds[2]<=0||image.bounds[3]<=0)return 0;
 struct Range {std::size_t begin,end,stride;U32 count;double anchor_x,anchor_y;};std::array<Range,64> ranges{};U32 count=0;
 // Validate the whole image before writing anything. Some native images emit
 // multiple commands, and the vertex allocation can move during original().
 for(U32 index=old_used?0:first;index<commands.count;++index){const auto& command=commands.commands[index];
  const U32 prior=index<first&&old_used?old_used[index]:0;if(command.used_vertices==prior)continue;
  if(command.used_vertices<prior||count==ranges.size())return 0;
  const auto begin=command.vertex_offset;const auto allocated=command.allocated_vertices;const auto stride=vertex_stride(command.shader);
  if(!stride||command.mode>1||begin%4||!allocated||allocated>65536||!command.used_vertices||command.used_vertices>allocated||command.used_vertices-prior>256||
     begin>vertices.used_bytes||command.used_vertices>(vertices.used_bytes-begin)/stride)return 0;
  const auto changed_begin=begin+prior*stride,end=begin+command.used_vertices*stride;
  // New commands may live below old_bytes. Only live vertices of other
  // commands are protected; their unused reservations are not live geometry.
  for(U32 next=0;next<commands.count;++next){if(next==index)continue;const auto& other=commands.commands[next];if(!other.used_vertices)continue;
   const auto other_stride=vertex_stride(other.shader),other_begin=other.vertex_offset;
   if(other_begin>=end)continue;
   if(!other_stride||other_begin>vertices.used_bytes||other.used_vertices>(vertices.used_bytes-other_begin)/other_stride)return 0;
   if(other_begin+other.used_vertices*other_stride>changed_begin)return 0;
  }
  double left=1e30,right=-1e30,top=1e30,bottom=-1e30;
  for(U32 v=prior;v<command.used_vertices;++v){float xy[2];std::memcpy(xy,vertices.data+begin+v*stride,8);
   if(!std::isfinite(xy[0])||!std::isfinite(xy[1])||std::abs(xy[0])>1e7||std::abs(xy[1])>1e7)return 0;
   left=std::min(left,double(xy[0]));right=std::max(right,double(xy[0]));top=std::min(top,double(xy[1]));bottom=std::max(bottom,double(xy[1]));
  }
  if(right<=left||bottom<=top)return 0;
  const double anchor_x=left+(double(center_x)-image.map_position.x-image.bounds[0])*(right-left)/image.bounds[2];
  const double anchor_y=top+(double(center_y)-image.map_position.y-image.bounds[1])*(bottom-top)/image.bounds[3];
  ranges[count++]={changed_begin,end,stride,command.used_vertices-prior,anchor_x,anchor_y};
 }
 std::uint64_t changed=0;
 for(U32 i=0;i<count;++i){const auto& r=ranges[i];for(U32 v=0;v<r.count;++v){float xy[2];auto at=vertices.data+r.begin+v*r.stride;std::memcpy(xy,at,8);
  xy[0]=float(r.anchor_x+(xy[0]-r.anchor_x)*amount.x);xy[1]=float(r.anchor_y+(xy[1]-r.anchor_y)*amount.y);std::memcpy(at,xy,8);++changed;
 }}return changed;
}
inline void __cdecl draw(void* raw,Draw original) {
 if(!original)return;auto image=static_cast<Image*>(raw);
 const auto snapshot=current();const auto amount=image&&candidate(image->image_id)&&snapshot?scale(*snapshot,*image):Scale{};
 if(!amount.enlarged()||!read_vars||!get_position){original(raw);return;}
 const std::uint16_t ids[]={62,63};std::size_t values[2]{};read_vars(ids,values,2);
 auto commands=reinterpret_cast<Commands*>(values[0]);auto vertices=reinterpret_cast<Vertices*>(values[1]);
 if(!commands||!vertices||commands->count>8192){original(raw);return;}
 const auto first=commands->count;const auto used=vertices->used_bytes;std::array<U32,8192> old_used;
 for(U32 i=0;i<first;++i)old_used[i]=commands->commands[i].used_vertices;
 std::uint16_t center[2]{};get_position(image->parent,center);
 original(raw); // Exactly one native render; no spell replay or extra sprites.
 read_vars(ids,values,2);if(values[0]!=reinterpret_cast<std::size_t>(commands)||values[1]!=reinterpret_cast<std::size_t>(vertices))return;
 const auto changed=transform(*commands,*vertices,first,used,*image,amount,center[0],center[1],old_used.data());
 if(changed){scaled_images.fetch_add(1,std::memory_order_relaxed);scaled_vertices.fetch_add(changed,std::memory_order_relaxed);}
 else rejected_geometry.fetch_add(1,std::memory_order_relaxed);
}
inline bool bind(const samase::PluginApi* api) {
 if(registered)return true;
 if(!api||api->version!=44||!api->hook_draw_image||!api->read_vars||!api->load_vars||!api->get_sprite_position||!api->first_lone_sprite)return false;
 const std::uint16_t ids[]={62,63};U8 support[2]{};api->load_vars(ids,support,2);if(support[0]<2||support[1]<2)return false;
 auto position=reinterpret_cast<rework_combat_v5::GetSpritePosition>(reinterpret_cast<GenericFn (__cdecl*)()>(api->get_sprite_position)());if(!position)return false;
 auto lone=reinterpret_cast<GetLone>(reinterpret_cast<GenericFn (__cdecl*)()>(api->first_lone_sprite)());if(!lone)return false;
 if(!reinterpret_cast<HookDraw>(api->hook_draw_image)(draw))return false;
 read_vars=api->read_vars;get_position=position;first_lone=lone;rework_combat_v5::area_visual_event=note;registered=true;return true;
}
}
