#pragma once
// Button activation and both targeted-order branches check energy separately.
// Preserve the original checker (including its cheat policy) and change only
// its required Q8 amount. Render/input callers read an immutable policy.
namespace spell_energy_check {
inline std::atomic<U32> owner{12};
inline std::atomic<std::uintptr_t> units{0};inline std::atomic<std::size_t> count{0};
inline std::atomic<std::uint64_t> policy{0};
inline U8* module=nullptr,*code=nullptr;inline U8 branches[4][5]{},expected[14]{};inline bool queued=false;
using Requirement=U32 (__cdecl*)(const bw::Unit*,U32);
inline Requirement original_requirement=nullptr;
inline constexpr U32 site=0x418014,checker=0x1da770;
inline constexpr U32 sites[]={0x3a993f,0x3a9b31,0x417fbd,site};
inline constexpr U8 calls[][5]={{0xe8,0x2c,0x0e,0xe3,0xff},{0xe8,0x3a,0x0c,0xe3,0xff},{0xe8,0xae,0x27,0xdc,0xff},{0xe8,0x57,0x27,0xdc,0xff}};
inline constexpr U8 original_call[]={0xe8,0x57,0x27,0xdc,0xff};
inline constexpr U8 original_checker[]={0x33,0xc0,0xf7,0x05,0xb4,0x96,0xe7,0x00,0x00,0x08,0x00,0x00,0x75,0x0a,0x66,0x39,0x91,0xe6,0x00,0x00,0x00,0x0f,0x92,0xc0,0xc3};
inline void reset() noexcept {owner.store(12,std::memory_order_release);units.store(0);count.store(0);policy.store(0);}
inline void publish() noexcept {
    owner.store(12,std::memory_order_release);
    if(!g.active||!g.applied||!g.units||g.units_count>65536)return;
    const auto rate=[](U32 ordinal,U32 base){return rework_combat_v5::rank(ordinal)?talent_power::v5(ordinal,base):0u;};
    const std::uint64_t value=std::min(90u,rate(38,30))|(std::uint64_t(rate(78,25))<<8)|
        (std::uint64_t(rate(120,25))<<16)|(std::uint64_t(rate(126,75*256))<<24)|
        (std::uint64_t(talent_power::enabled&&rework_combat_v5::rank(64)?1:0)<<56);
    if(!value)return;
    units.store(reinterpret_cast<std::uintptr_t>(g.units),std::memory_order_relaxed);count.store(g.units_count,std::memory_order_relaxed);policy.store(value,std::memory_order_relaxed);owner.store(player_owner(),std::memory_order_release);
}
inline U32 required(const bw::Unit* u,U32 base) noexcept {
    const U32 own=owner.load(std::memory_order_acquire);const auto start=units.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(u);
    if(own>=8||!start||address<start||(address-start)%sizeof(bw::Unit)||(address-start)/sizeof(bw::Unit)>=count.load(std::memory_order_relaxed)||u->player!=own||(u->flags&0x40000000u))return base;
    const auto value=policy.load(std::memory_order_relaxed);U32 rate=0;
    if((value&(1ull<<56))&&rework_combat_v5::in(u->unit_id,{12,27,28,29,102}))base=std::min(base,50*256u);
    if(rework_combat_v5::group(38,u->unit_id))rate=U32(value&255u);
    if(rework_combat_v5::group(78,u->unit_id))rate=U32(value>>8)&255u;
    if(rework_combat_v5::group(120,u->unit_id))rate=U32(value>>16)&255u;
    U32 refund=base*std::min(100u,rate)/100;
    // Recall is the Arbiter's only150-energy native spell. Stasis is100.
    if((u->unit_id==71||u->unit_id==86)&&base==150*256u)refund=std::min(base,refund+U32(value>>24));
    return base-std::min(base,refund);
}
inline U32 __cdecl check(const bw::Unit* u,U32 base) noexcept {return original_requirement?original_requirement(u,required(u,base)):1u;}
inline bool verify_installation() noexcept {
    if(!queued||!module||!code||!native_engine_hooks::match(code,expected,14)||!native_engine_hooks::match(module+checker,original_checker,sizeof(original_checker)))return false;
    for(U32 i=0;i<4;i++)if(!native_engine_hooks::match(module+sites[i],branches[i],5))return false;
    return true;
}
inline bool register_at(U8* base,native_engine_hooks::WriteExeMemory writer) noexcept {
    if(queued)return module==base;
    if(code||!base||!writer||!native_engine_hooks::match(base+checker,original_checker,sizeof(original_checker)))return false;
    for(U32 i=0;i<4;i++)if(!native_engine_hooks::match(base+sites[i],calls[i],5))return false;
    auto relay=native_engine_hooks::nearby_code(base+site);if(!relay)return false;
    native_engine_hooks::absolute_jump(relay,reinterpret_cast<void*>(check));DWORD old=0;
    for(U32 i=0;i<4;i++){
        const auto delta=reinterpret_cast<std::intptr_t>(relay)-reinterpret_cast<std::intptr_t>(base+sites[i]+5);
        if(delta<INT32_MIN||delta>INT32_MAX){VirtualFree(relay,0,MEM_RELEASE);return false;}
        branches[i][0]=0xe8;const auto relative=std::int32_t(delta);std::memcpy(branches[i]+1,&relative,4);
    }
    if(!VirtualProtect(relay,4096,PAGE_EXECUTE_READ,&old)||!FlushInstructionCache(GetCurrentProcess(),relay,4096)){VirtualFree(relay,0,MEM_RELEASE);return false;}
    // Earlier queued calls may already reference the relay if a later API write
    // fails. Keep its memory alive and let startup verification fail closed.
    code=relay;module=base;std::memcpy(expected,relay,14);original_requirement=reinterpret_cast<Requirement>(base+checker);
    for(U32 i=0;i<4;i++)if(!writer(reinterpret_cast<std::size_t>(base+sites[i]),branches[i],5))return false;
    queued=true;return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {return api&&api->write_exe_memory&&native_engine_hooks::verify_image()&&register_at(native_engine_hooks::verified_base,reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));}
}
