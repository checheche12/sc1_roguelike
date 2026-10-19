#pragma once
// Native armor bonus is shared by damage and tooltips. Original campaigns
// keep is_bw=0 while permitting BW units/upgrades. Enable the native Ultra
// branch without replacing research storage, armor arithmetic or game mode.
namespace campaign_ultra_armor {
inline constexpr U32 gate_rva=0x1e7dd7;
inline constexpr U8 predicate[]={0x80,0xb8,0x50,0x03,0x01,0x00,0x00};
inline constexpr U8 before[]={0x75,0x21},after[]={0xeb,0x21};
inline constexpr U8 target[]={0x48,0x89,0x7c,0x24,0x30};
inline U8* image=nullptr;inline bool queued=false;
inline bool witnesses(U8* base) noexcept {
 return base&&native_engine_hooks::match(base+gate_rva-7,predicate,sizeof(predicate))&&native_engine_hooks::match(base+0x1e7dfa,target,sizeof(target));
}
inline bool register_at(U8* base,native_engine_hooks::WriteExeMemory write) noexcept {
 if(queued)return image==base;
 if(!write||!witnesses(base)||!native_engine_hooks::match(base+gate_rva,before,sizeof(before)))return false;
 if(!write(reinterpret_cast<std::size_t>(base+gate_rva),after,sizeof(after)))return false;
 image=base;queued=true;return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {
 return api&&api->write_exe_memory&&native_engine_hooks::verify_image()&&register_at(native_engine_hooks::verified_base,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));
}
inline bool verify_installation() noexcept {return queued&&witnesses(image)&&native_engine_hooks::match(image+gate_rva,after,sizeof(after));}
}
