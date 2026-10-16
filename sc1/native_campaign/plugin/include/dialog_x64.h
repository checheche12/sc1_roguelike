#pragma once
// Public neivv/aise bw_dat SCR repr(C) layouts, commit42fba4276cbe30e73baefc7f3ad07cadaa2aa2b1.
// No executable addresses, private vtables or 1.16.1 packed structures.
#include <cstddef>
#include <cstdint>

namespace sc1_native { namespace dialog {
struct Control;
struct Dialog;
struct Event;
using EventHandler = std::uint32_t (__cdecl*)(Control*, Event*);
struct Rect { std::int16_t left, top, right, bottom; };
struct Surface { std::uint16_t width, height; std::uint8_t* data; };
struct BwString { const std::uint8_t* data; std::size_t length, capacity; std::uint8_t inline_buffer[16]; };
struct Control {
    Control* next;
    Rect area;
    Surface image;
    BwString string;
    std::uint32_t flags, flags2;
    std::uint16_t unknown;
    std::int16_t id;
    std::uint16_t type, misc_u16;
    void* user_ptr;
    EventHandler event_handler;
    void (__cdecl* draw)(Control*, std::int32_t, std::int32_t, const Rect*, const Rect*);
    Dialog* parent;
};
struct Dialog {
    Control control;
    Surface surface;
    Control* highlighted;
    Control* first_child;
    Control* active;
};
struct Event {
    std::size_t ext_type, ext_param;
    std::uint64_t param;
    std::uint16_t type;
    std::int16_t x, y;
    std::uint32_t time;
};
using RunOriginal = std::uint32_t (__cdecl*)(void*, std::size_t, void*);
// API44 hook_file_read registers one prefix and a callback. Registration has
// no result; null callback result delegates the original file read.
using FileReadHook = std::uint8_t* (__cdecl*)(const std::uint8_t*, std::uint32_t*);
using RegisterFileRead = void (__cdecl*)(const std::uint8_t*, FileReadHook);
// Public API44 hook_layout_draw_text, used by MTL tooltip.rs 42522c8b....
using LayoutTextOriginal = const std::uint8_t* (__cdecl*)(
    std::uint32_t, std::uint32_t, const std::uint8_t*, std::uint32_t*,
    std::uint32_t, std::uint32_t*, std::uint32_t, std::uint32_t);
using LayoutTextHook = const std::uint8_t* (__cdecl*)(
    std::uint32_t, std::uint32_t, const std::uint8_t*, std::uint32_t*,
    std::uint32_t, std::uint32_t*, std::uint32_t, std::uint32_t, LayoutTextOriginal);
static_assert(sizeof(void*) == 8, "Native SCR dialog requires x64");
static_assert(sizeof(Surface) == 16 && sizeof(BwString) == 40, "SCR string/surface ABI");
static_assert(sizeof(Control) == 120 && sizeof(Dialog) == 160 && sizeof(Event) == 40, "SCR dialog ABI");
static_assert(offsetof(Control, string) == 32 && offsetof(Control, id) == 82, "SCR control ID/string ABI");
static_assert(offsetof(Control, event_handler) == 96 && offsetof(Control, parent) == 112, "SCR callbacks ABI");
static_assert(offsetof(Dialog, first_child) == 144 && offsetof(Event, type) == 24, "SCR children/event ABI");
constexpr std::uint16_t kExtendedEvent = 14;
// Primary source: samase_scarf f1681db...src/dialog.rs:2130, button-activation branch.
constexpr std::size_t kActivateButton = 2;
constexpr std::uint32_t kResumeResult = 0xFFFFFFFDu; // Original GameMenu button -3.
} } // namespace sc1_native::dialog
