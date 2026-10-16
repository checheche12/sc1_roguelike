#pragma once
// Exact 1.23.10.13515 adapter. Include after native_engine_hooks.h.
#include "sight_cargo_runtime.h"
namespace sight_cargo_engine {
namespace sight_cargo = ::sc1::sight_cargo;
inline sight_cargo::SightAdapter sight;
inline constexpr U8 sig_generate[] = {0x48,0x89,0x6c,0x24,0x18,0x56,0x41,0x56,0x41,0x57,0x48,0x83,0xec,0x20,0x45,0x33,0xd2,0x45,0x8b,0xf8,0x8b,0xea,0x48,0x8b,0xf1,0x48,0x8b,0xc1};
inline constexpr U8 sig_release[] = {0x85,0xd2,0x74,0x52,0x57,0x48,0x83,0xec,0x20,0x48,0x89,0x5c,0x24,0x30,0x8b,0xfa,0x48,0x89,0x74,0x24,0x38,0x48,0x8d,0x59,0x18};
inline constexpr U8 sig_air[] = {0x41,0x8b,0x40,0x14,0x49,0x8b,0x50,0x18,0x85,0xc0,0x74,0x24,0x44,0x8b,0x44,0x24,0x30,0x48,0x83,0xc2,0x10};
inline constexpr U8 sig_edge[] = {0x48,0x89,0x5c,0x24,0x10,0x57,0x45,0x8b,0x50,0x14,0x8b,0xda,0x49,0x8b,0x40,0x18,0x8b,0xf9,0x45,0x85,0xd2,0x74,0x5f};
inline constexpr U8 sig_original[] = {0x41,0x81,0xf9,0xff,0x00,0x00,0x00,0x0f,0x87,0x3e,0x01,0x00,0x00,0x53,0x41,0x56,0x41,0x57,0x48,0x83,0xec,0x30,0x8b,0x44,0x24,0x70,0x41,0x8b,0xd9,0x44,0x8b,0xf2,0x44,0x8b,0xf9,0x83,0xf8,0x0c,0x0f,0x83,0x16,0x01,0x00,0x00};
inline constexpr U8 sig_detect[] = {0x41,0xb8,0x60,0x01,0x00,0x00};
inline constexpr U8 sig_call0[] = {0xe8,0xf5,0x8b,0x1a,0x00};
inline constexpr U8 sig_call1[] = {0xe8,0xeb,0x4e,0x1a,0x00};
inline constexpr U8 sig_call2[] = {0xe8,0x67,0x4a,0x1a,0x00};
inline constexpr U8 sig_call3[] = {0xe8,0x55,0xc4,0x17,0x00};
inline constexpr native_engine_hooks::CallSpec calls[] = {
    {{0x1b6eb6,sig_call0,5},0x35fab0},
    {{0x1babc0,sig_call1,5},0x35fab0},
    {{0x1bb044,sig_call2,5},0x35fab0},
    {{0x1e3656,sig_call3,5},0x35fab0}
};
inline constexpr native_engine_hooks::Bytes witnesses[] = {
    {0x34fa20,sig_generate,sizeof(sig_generate)},
    {0x34f6a0,sig_release,sizeof(sig_release)},
    {0x3608c0,sig_air,sizeof(sig_air)},
    {0x360900,sig_edge,sizeof(sig_edge)},
    {0x35fab0,sig_original,sizeof(sig_original)},
    {0x1d58fc,sig_detect,sizeof(sig_detect)}
};

inline native_engine_hooks::Hook hooks[4];
inline native_engine_hooks::Patch detection;
inline bool installed = false;
inline void __cdecl reveal(std::uint32_t x, std::uint32_t y, std::uint32_t in_air, std::uint32_t mask,
                           std::uint32_t range, std::uint32_t extra) {
    sight.reveal(x,y,in_air,mask,range,extra);
}
inline bool uninstall() noexcept {
    bool okay = native_engine_hooks::uninstall_patch(detection);
    for (unsigned i = 4; i != 0; --i) okay = native_engine_hooks::uninstall_call(calls[i-1],hooks[i-1]) && okay;
    installed = false; sight.disable(); return okay;
}
inline bool install(sight_cargo::SightAdapter::Environment environment) noexcept {
    if (installed) return true;
    if (!environment || !native_engine_hooks::verify_image()) return false;
    auto base = native_engine_hooks::verified_base;
    for (const auto& w : witnesses) if (!native_engine_hooks::match(base+w.rva,w.expected,w.length)) return false;
    for (const auto& c : calls) if (!native_engine_hooks::match(base+c.site.rva,c.site.expected,c.site.length)) return false;
    if (!sight.bind(reinterpret_cast<sight_cargo::SightAdapter::Generate>(base+0x34fa20),
                    reinterpret_cast<sight_cargo::SightAdapter::Release>(base+0x34f6a0),
                    reinterpret_cast<sight_cargo::SightAdapter::Original>(base+0x35fab0),
                    reinterpret_cast<sight_cargo::SightAdapter::Air>(base+0x3608c0),
                    reinterpret_cast<sight_cargo::SightAdapter::Air>(base+0x360900),environment)) return false;
    for (unsigned i = 0; i < 4; ++i) if (!native_engine_hooks::install_call(calls[i],reinterpret_cast<void*>(&reveal),hooks[i])) {
        uninstall(); return false;
    }
    constexpr U8 expanded_search[] = {0x41,0xb8,0xa0,0x01,0x00,0x00};
    if (!native_engine_hooks::install_patch({0x1d58fc,sig_detect,sizeof(sig_detect)},expanded_search,detection)) {
        uninstall(); return false;
    }
    installed = true; return true;
}
} // namespace sight_cargo_engine
