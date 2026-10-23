#pragma once
// Included inside rework_combat_v5 after the native weapon/target helpers.
namespace valkyrie_volley {
inline constexpr U32 stock_entry=38317,stock_header=38242,idle=31138;
inline constexpr U8 stock[]={5,1,0x2e,0x25,2,5,10,0x25,2,5,10,0x25,2,5,10,0x25,2,5,10,0x2f,0x2a,7,0xa2,0x79};
inline constexpr U32 entry=shadow_feedback::offset+sizeof(shadow_feedback::program);
inline constexpr U32 select_opcode=0xd0,release_opcode=0xd1,release=entry+5,finish=entry+6,salvo=entry+12;
// Select -> wait1 -> native AttackWith2 -> detach remaining salvos ->
// native GotoRepeatAttk -> wait for the volley -> idle. Keep the live attack
// animation for its original duration, without either command-lock opcode.
// The final AttackWith2/wait1 is a private script for each remaining pair.
inline constexpr U8 program[]={select_opcode,5,1,0x25,2,release_opcode,0x2a,5,40,7,0xa2,0x79,0x25,2,5,1};
static_assert(entry+sizeof(program)<0x10000,"Valkyrie script fits native PC");
struct Volley {Identity source,target;U32 started,remaining=3,next=0,layer=0;};
inline std::vector<Volley> volleys;
inline void reset() noexcept {volleys.clear();}
inline bool enabled(bw::Unit* u) noexcept {return own(u)&&u->unit_id==58&&rank(58);}
inline bool busy(bw::Unit* u) noexcept {
    for(const auto& v:volleys)if(resolve(v.source)==u&&U32(now()-v.started)<40u)return true;
    return false;
}
inline void append(U8* bytes,std::size_t size) noexcept {
    if(!bytes||size<entry+sizeof(program)||std::memcmp(bytes+stock_entry,stock,sizeof(stock))||
       std::memcmp(bytes+stock_header,"SCPE",4))return;
    std::memcpy(bytes+entry,program,sizeof(program));
    for(U32 animation:{2u,3u,5u,6u}){
        auto p=bytes+stock_header+8+animation*2;p[0]=U8(entry&255u);p[1]=U8(entry>>8);
    }
}
inline bool context(void* pos,void* script,void* raw,U32 expected,movement_effects::Image*& image,bw::Unit*& u) noexcept {
    if(!pos||!script||!raw||!movement_effects::get_bin)return false;
    auto bytes=static_cast<const U8*>(movement_effects::get_bin());
    if(!bytes||pos!=bytes+expected+1||std::memcmp(bytes+entry,program,sizeof(program)))return false;
    image=static_cast<movement_effects::Image*>(raw);u=movement_effects::image_unit(image);
    auto s=static_cast<movement_effects::Script*>(script);s->wait=0;s->pos=std::uint16_t(expected==entry?stock_entry:finish);
    return image->script.header==stock_header&&valid_unit(u)&&u->flingy.sprite&&
        static_cast<bw::SpriteScr*>(u->flingy.sprite)->main_image==image;
}
inline void __cdecl select(void* pos,void* script,void* raw,U32 dry,U32*) noexcept {
    movement_effects::Image* image=nullptr;bw::Unit* u=nullptr;
    if(!context(pos,script,raw,entry,image,u)||dry||!movement_effects::effect_context()||!enabled(u))return;
    static_cast<movement_effects::Script*>(script)->pos=std::uint16_t(busy(u)?finish:entry+1);
}
inline void schedule(bw::Unit* u,bw::Unit* target) {
    volleys.push_back({identity(u),identity(target),now(),3,now()+10,air(target)?1u:0u});
    u->ground_cooldown=U8(std::max(40u,U32(u->ground_cooldown)));
    u->air_cooldown=U8(std::max(40u,U32(u->air_cooldown)));
}
inline void __cdecl detach(void* pos,void* script,void* raw,U32 dry,U32*) noexcept {
    movement_effects::Image* image=nullptr;bw::Unit* u=nullptr;
    if(!context(pos,script,raw,release,image,u)||dry||!movement_effects::effect_context()||!enabled(u)||busy(u))return;
    auto target=u->order_target.unit;
    if(!target_ok(u,target,103,false))return;
    // The first native pair has already fired. Only the following three pairs
    // are scheduled; Move/Patrol/Stop can replace the real order immediately.
    try{schedule(u,target);}
    catch(...){return;}
    // Preserve the original 40-frame volley floor when haste shortens the
    // weapon cooldown. This is a weapon clock, never a movement/order lock.
}
inline bool bind(const samase::PluginApi* api) noexcept {
    if(!api||!api->hook_iscript_opcode)return false;
    auto hook=reinterpret_cast<movement_effects::HookOpcode>(api->hook_iscript_opcode);
    return hook(select_opcode,select)&&hook(release_opcode,detach);
}
inline bool fire(bw::Unit* u,bw::Unit* target) {
    if(!shadow_feedback::step||!movement_effects::get_bin||!script_context_read||!script_context_write)return false;
    auto bytes=static_cast<const U8*>(movement_effects::get_bin());
    auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);
    auto image=sprite?static_cast<movement_effects::Image*>(sprite->main_image):nullptr;
    if(!bytes||std::memcmp(bytes+entry,program,sizeof(program))||!image||image->parent!=sprite)return false;
    // Native AttackWith retains Halo scatter, launch offsets, damage factor,
    // sound and projectile creation. It never edits the ship's live animation.
    OwnerDatScope view(u->player,u->player,u);multi_target::TargetScope aim(u,target);
    struct Context {
        std::size_t saved[3]{};
        explicit Context(bw::Unit* source){script_context_read(script_context_ids,saved,3);
            const std::size_t values[]={reinterpret_cast<std::size_t>(&source->flingy),reinterpret_cast<std::size_t>(source),0};
            script_context_write(script_context_ids,values,3);}
        ~Context(){script_context_write(script_context_ids,saved,3);}
    } context(u);
    movement_effects::Script shot{};shot.pos=std::uint16_t(salvo);U32 speed=0;
    shadow_feedback::step(image,&shot,0,&speed);return true;
}
inline void step() {
    for(auto it=volleys.begin();it!=volleys.end();){
        auto u=resolve(it->source),target=resolve(it->target);const U32 age=now()-it->started;
        if(!enabled(u)||!can_fire(u)||u->stasis_timer||age>=40u){it=volleys.erase(it);continue;}
        u->ground_cooldown=U8(std::max(40u-age,U32(u->ground_cooldown)));
        u->air_cooldown=U8(std::max(40u-age,U32(u->air_cooldown)));
        if(it->remaining&&std::int32_t(now()-it->next)>=0){
            if(!target||air(target)!=(it->layer!=0)||!target_ok(u,target,103,false))it->remaining=0;
            else {fire(u,target);--it->remaining;it->next+=10;}
        }
        ++it;
    }
}
inline void mobile(bw::Unit* u,UnitState& s,U32 frame) {
    if(!enabled(u)||!in(u->order,{6,152})||!can_fire(u)||u->stasis_timer||
       u->ground_cooldown||u->air_cooldown||(u->flingy.flingy_flags&8u)||busy(u)||
       std::int32_t(frame-std::max(s.next_ground,s.next_air))<0)return;
    // One shared air/ground volley, matching the other moving-fire talents.
    // Native AttackWith runs on a private Script; the live movement order,
    // waypoints, facing and animation are never borrowed or replaced.
    for(auto target:around(u->flingy.position.x,u->flingy.position.y,1024,nullptr,64,true)){
        if(!target_ok(u,target,103))continue;
        const U32 period=std::max(40u,fractional_period(u,air(target)?1u:0u,multi_target::period(u,103),cooldown_ratio(u,103)));
        if(!fire(u,target))return;
        schedule(u,target);s.next_ground=s.next_air=frame+period;
        u->ground_cooldown=u->air_cooldown=U8(std::min(255u,period));break;
    }
}
}
inline bool bind_valkyrie_volley(const samase::PluginApi* api) noexcept {return valkyrie_volley::bind(api);}
