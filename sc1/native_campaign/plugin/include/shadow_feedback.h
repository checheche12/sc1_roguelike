#pragma once
namespace shadow_feedback {
using Step=void (__cdecl*)(void*,void*,U32,U32*);
inline Step step=nullptr;
// Stock Dark Templar attack: iscript 152 PlaySnd111 and 372 AttackMelee[111].
// Append a sound-only script after all generated code. Wait returns immediately
// to our caller; this private Script is never resumed and cannot deal damage.
inline constexpr U32 offset=sizeof(movement_effects::data::kIscript);
inline constexpr U8 program[]={0x18,111,0,0x05,1};
static_assert(offset+sizeof(program)<0x10000,"sound script fits native 16-bit PC");
inline bool bind(const samase::PluginApi* api) noexcept {
 step=api&&api->step_iscript?reinterpret_cast<Step>(reinterpret_cast<GenericFn (__cdecl*)()>(api->step_iscript)()):nullptr;
 return step!=nullptr;
}
inline void append(U8* bytes,std::size_t size) noexcept {
 if(bytes&&size>=offset+sizeof(program))std::memcpy(bytes+offset,program,sizeof(program));
}
inline void strike(bw::Unit* u) noexcept {
 if(!step||!valid_unit(u)||!u->flingy.sprite||!movement_effects::get_bin)return;
 auto code=static_cast<const U8*>(movement_effects::get_bin());
 if(!code||std::memcmp(code+offset,program,sizeof(program)))return;
 auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);
 auto image=static_cast<movement_effects::Image*>(sprite->main_image);
 if(!image||image->parent!=sprite)return;
 movement_effects::Script sound{};sound.pos=std::uint16_t(offset);U32 speed=0;
 // The real image supplies positional audio; its animation remains untouched.
 step(&sound,image,0,&speed);
}
}
