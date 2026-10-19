#pragma once
// Public SAMASE API44 custom-opcode/file hooks. Native Move and AttackMelee
// commands remain in the bytecode; callbacks run immediately around them.
// Layout: pinned bw_dat structs.rs Image/Iscript (x64); no executable addresses.
#include "movement_iscript.generated.h"
namespace movement_effects {
struct Script {std::uint16_t header,pos,return_pos;U8 animation,wait;};
struct Image {
    void* prev;void* next;std::uint16_t image_id;U8 drawfunc,direction;
    std::uint16_t flags;std::int8_t x_offset,y_offset;Script script;
    std::uint16_t frameset,frame;bw::Point map_position,screen_position;
    std::int16_t bounds[4];void* grp;void* drawfunc_param;U32 draw,step_frame;void* parent;
};
static_assert(sizeof(Script)==8 && offsetof(Script,pos)==2,"iscript public layout");
static_assert(sizeof(Image)==0x58 && offsetof(Image,parent)==0x50 && offsetof(Image,script)==0x18,"image public x64 layout");
using GetBin=void* (__cdecl*)();
using Opcode=void (__cdecl*)(void*,void*,void*,U32,U32*);
using HookOpcode=U32 (__cdecl*)(U32,Opcode);
using FileRead=U8* (__cdecl*)(const U8*,U32*);
using HookFile=void (__cdecl*)(const U8*,FileRead);
using MeleeEvent=void (*)(bw::Unit*) noexcept;
inline GetBin get_bin=nullptr;
inline ReadVars read_vars=nullptr;
inline MeleeEvent enter_event=nullptr,leave_event=nullptr;
struct Bracket {void* script;void* image;bw::Unit* unit;};
inline std::array<Bracket,32> brackets{};
inline std::size_t depth=0;
inline bool registered=false;
using ScriptTransform=void (*)(U8*,std::size_t) noexcept;
inline ScriptTransform script_transform=nullptr;
inline void reset() noexcept {
    while(depth){const auto value=brackets[--depth];if(leave_event)leave_event(value.unit);}
}
struct Ratio {std::uint64_t numerator=1,denominator=1;};
using RatioExtension=Ratio (*)(bw::Unit*) noexcept;
inline RatioExtension ratio_extension=nullptr;
inline Ratio ratio(bw::Unit* u) noexcept {
    Ratio r;
    if(!g.active || !g.applied || !valid_unit(u) || hallucination(u) ||
       u->unit_id>=228 || u->flingy.hitpoints<=0 || u->order==0)return r;
    if(u->player==player_owner())for(const auto& p:frozen::movement_patches)
        if(p.unit_id==u->unit_id && (g.growth.talent_bits[p.bit/32]&(1u<<(p.bit%32)))){
            talent_power::multiply(r.numerator,r.denominator,p.bit,p.numerator,p.denominator);
        }
    if(regular_enemy(u)){
        if(g.growth.curse_counts[3]){r.numerator*=40+3*g.growth.curse_counts[3];r.denominator*=40;}
        auto t=existing_track(u);auto game=g.game ? g.game() : nullptr;
        if(t && game && t->command_until>game->frame_count){r.numerator*=6;r.denominator*=5;}
    }
    if(ratio_extension){const auto extra=ratio_extension(u);r.numerator*=extra.numerator;r.denominator*=extra.denominator;}
    return r;
}
inline std::int32_t scaled(std::int32_t value,Ratio r) noexcept {
    const bool negative=value<0;
    const auto magnitude=negative ? std::uint64_t(-std::int64_t(value)) : std::uint64_t(value);
    const auto result=r.numerator&&magnitude>(0xffffffffffffffffull-r.denominator/2)/r.numerator
        ?std::uint64_t(std::min<long double>(0x7fffffffu,static_cast<long double>(magnitude)*r.numerator/r.denominator+0.5L))
        :std::min<std::uint64_t>(0x7fffffffu,(magnitude*r.numerator+r.denominator/2)/r.denominator);
    return negative ? -static_cast<std::int32_t>(result) : static_cast<std::int32_t>(result);
}
inline void after_move(bw::Unit* u,U32 dry_run,U32* speed_out) noexcept {
    if(!valid_unit(u) || u->flingy.movement_type!=2)return;
#ifdef SC1_EFFECT_MOVE_OBSERVER
    const auto observed_out=speed_out ? *speed_out:0u;
    const auto observed_live=u->flingy.current_speed;
    const auto observe=[&]() noexcept {SC1_EFFECT_MOVE_OBSERVER(u,dry_run,observed_out,speed_out ? *speed_out:0u,observed_live,u->flingy.current_speed,u->flingy.top_speed);};
#else
    const auto observe=[]() noexcept {};
#endif
    const auto r=ratio(u);if(r.numerator==r.denominator){observe();return;}
    // Apply to the result of the unchanged native Move. Engine upgrades,
    // ensnare and zero-speed/turning decisions have already been evaluated.
    if(speed_out){const auto magnitude=std::uint64_t(*speed_out);
        *speed_out=r.numerator&&magnitude>(0xffffffffffffffffull-r.denominator/2)/r.numerator
            ?U32(std::min<long double>(0xffffffffu,static_cast<long double>(magnitude)*r.numerator/r.denominator+0.5L))
            :U32(std::min<std::uint64_t>(0xffffffffu,(magnitude*r.numerator+r.denominator/2)/r.denominator));}
    if(dry_run){observe();return;} // Predictions never mutate a live unit or allocate tracks.
    auto& f=u->flingy;
    f.next_speed=scaled(f.next_speed,r);f.current_speed=scaled(f.current_speed,r);
    f.current_speed_x=scaled(f.current_speed_x,r);f.current_speed_y=scaled(f.current_speed_y,r);
    observe();
}
inline bw::Unit* image_unit(Image* image) noexcept {
    if(!image || !image->parent)return nullptr;
    if(read_vars){
        const auto id=static_cast<std::uint16_t>(samase::VarId::ActiveIscriptUnit);
        std::size_t value=0;read_vars(&id,&value,1);auto u=reinterpret_cast<bw::Unit*>(value);
        if(valid_unit(u) && u->flingy.sprite==image->parent)return u;
    }
    // Some prediction/order contexts do not set ActiveIscriptUnit. Resolve the
    // image's actual parent; never trust an unrelated stale global unit.
    for(std::size_t i=0;g.units && i<g.units_count;i++){
        auto u=&g.units[i];if(u->flingy.sprite==image->parent && u->flingy.hitpoints>0 && u->order!=0)return u;
    }
    return nullptr;
}
inline bool resume(void* pos,void* script,U32 opcode) noexcept {
    if(!pos || !script || !get_bin)return false;
    const auto base=reinterpret_cast<std::uintptr_t>(get_bin());
    const auto value=reinterpret_cast<std::uintptr_t>(pos);
    if(!base || value<=base || value-base>=sizeof(data::kIscript) || data::kIscript[value-base-1]!=opcode)return false;
    const auto offset=value-base-1;
    const auto event=std::lower_bound(std::begin(data::kEvents),std::end(data::kEvents),offset,
        [](const data::Event& x,std::uintptr_t key){return x.offset<key;});
    if(event==std::end(data::kEvents) || event->offset!=offset || event->opcode!=opcode)return false;
    auto state=static_cast<Script*>(script);state->pos=static_cast<std::uint16_t>(value-base);state->wait=0;
    return true; // SAMASE resumes native dispatch at Script.pos when wait==0.
}
inline bool effect_context() noexcept {
    return g.active && g.applied && GetCurrentThreadId()==g.game_thread.load();
}
inline void __cdecl move_opcode(void* pos,void* script,void* raw_image,U32 dry,U32* speed) noexcept {
    if(!resume(pos,script,data::kMoveOpcode) || !effect_context())return;
    after_move(image_unit(static_cast<Image*>(raw_image)),dry,speed);
}
inline void __cdecl melee_enter_opcode(void* pos,void* script,void* raw_image,U32 dry,U32*) noexcept {
    if(!resume(pos,script,data::kMeleeEnterOpcode) || dry || !effect_context() || !enter_event || !leave_event || depth==brackets.size())return;
    auto u=image_unit(static_cast<Image*>(raw_image));if(!valid_unit(u) || hallucination(u))return;
    brackets[depth++]={script,raw_image,u};enter_event(u);
}
inline void __cdecl melee_leave_opcode(void* pos,void* script,void* raw_image,U32 dry,U32*) noexcept {
    if(!resume(pos,script,data::kMeleeLeaveOpcode) || dry || !depth)return;
    // Use the pre-native source even if native damage nested other image steps.
    const auto frame=brackets[depth-1];if(frame.script!=script || frame.image!=raw_image)return;
    --depth;if(leave_event)leave_event(frame.unit);
}
inline U8* __cdecl file_read(const U8*,U32* size) noexcept {
    if(!size || !registered)return nullptr;
    // API44 hook_file_read uses process-heap ownership, as the public AICE
    // plugin does. Full 64 KiB also preserves the engine's u16 script address space.
    auto buffer=static_cast<U8*>(HeapAlloc(GetProcessHeap(),HEAP_ZERO_MEMORY,0x10000));
    if(!buffer){*size=0;return nullptr;}
    std::memcpy(buffer,data::kIscript,sizeof(data::kIscript));if(script_transform)script_transform(buffer,0x10000);*size=0x10000;return buffer;
}
inline bool bind(const samase::PluginApi* api,MeleeEvent enter,MeleeEvent leave) noexcept {
    if(!api || !api->hook_iscript_opcode || !api->hook_file_read || !api->get_iscript_bin ||
       !api->load_vars || !api->read_vars || !enter || !leave)return false;
    const auto id=static_cast<std::uint16_t>(samase::VarId::ActiveIscriptUnit);U8 support=0;
    api->load_vars(&id,&support,1);if(support<2)return false;
    auto getter=reinterpret_cast<GetBin>(reinterpret_cast<GenericFn (__cdecl*)()>(api->get_iscript_bin)());
    if(!getter)return false;
    auto hook=reinterpret_cast<HookOpcode>(api->hook_iscript_opcode);
    if(!hook(data::kMoveOpcode,move_opcode) || !hook(data::kMeleeEnterOpcode,melee_enter_opcode) ||
       !hook(data::kMeleeLeaveOpcode,melee_leave_opcode))return false;
    get_bin=getter;read_vars=api->read_vars;enter_event=enter;leave_event=leave;registered=true;
    reinterpret_cast<HookFile>(api->hook_file_read)(reinterpret_cast<const U8*>("scripts\\iscript.bin"),file_read);
    return true;
}
} // namespace movement_effects
