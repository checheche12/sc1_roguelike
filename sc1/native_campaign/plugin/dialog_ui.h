#pragma once
#include <array>
#include <atomic>
#include <cstdint>
#include <memory>
#include <string>
#include <vector>
#include "mailbox_protocol.h"
#include "include/samase_api44.h"
#include "include/dialog_x64.h"

namespace sc1_native {
struct DialogUiCallbacks {
    void* context = nullptr;
    bool (*submit)(void*, std::uint32_t slot) = nullptr;
    void (*pump)(void*) = nullptr;
    bool (*session_active)(void*) = nullptr;
    bool (*can_resume)(void*) = nullptr;
    void (*report)(void*, const char*) = nullptr;
    // Backend validates a single selected, owned carrier with >8 used space.
    bool (*cargo_state)(void*, std::uint64_t* token, std::uint32_t* page, std::uint32_t* passengers) = nullptr;
    bool (*cargo_toggle)(void*, std::uint64_t token) = nullptr;
    bool (*cargo_state_v2)(void*, std::uint64_t* token, std::uint32_t* page, std::uint32_t* pages, std::uint32_t* passengers) = nullptr;
};
struct DialogRenderStats {
    std::uint64_t calls = 0, exact = 0, hotkey_offset = 0, near_miss = 0;
    std::uint32_t offset = 0xffffffffu, row = 0;
    std::uint32_t a = 0, b = 0, draw = 0, g = 0, h = 0;
};

// Original native widget types/IDs/order/flags remain engine-owned. A scoped
// file hook declares the existing CTEXT body before native construction. No
// widget type, surface, allocation ownership or rectangle changes afterward.
class DialogUi final {
public:
    ~DialogUi() noexcept;
    bool initialize(const samase::PluginApi*, const DialogUiCallbacks&) noexcept;
    void set_callbacks(const DialogUiCallbacks&) noexcept;
    void show(const ChoiceOffer&) noexcept;
    void clear() noexcept;
    void dismiss_error() noexcept;
    void reset_session() noexcept;
    void pump(std::uint64_t monotonic_ms) noexcept;
    bool pending() const noexcept { return pending_; }
    bool waiting() const noexcept { return waiting_; }
    bool open() const noexcept { return menu_ != nullptr; }
    bool supported() const noexcept { return supported_; }
    bool previewing() const noexcept { return preview_slot_ != 0; }
    // Scoped GameMenu/Social constructor JSON; every unowned read falls back.
    std::uint8_t* file_read(const std::uint8_t*, std::uint32_t*) noexcept;
    std::uint32_t run_dialog(void*, std::size_t, void*, dialog::RunOriginal) noexcept;
    std::uint32_t spawn_dialog(void*, std::size_t, void*, dialog::RunOriginal) noexcept;
    std::uint32_t event(dialog::Control*, dialog::Event*) noexcept;
    std::uint32_t hud_event(dialog::Control*, dialog::Event*) noexcept;
    const std::uint8_t* layout_text(std::uint32_t, std::uint32_t, const std::uint8_t*,
        std::uint32_t*, std::uint32_t, std::uint32_t*, std::uint32_t, std::uint32_t,
        dialog::LayoutTextOriginal) noexcept;
    DialogRenderStats render_stats() const noexcept;
    void set_wave_timer(const std::string&) noexcept;
    std::uint32_t wave_hud_event(dialog::Control*, dialog::Event*) noexcept;

private:
    struct Binding {
        dialog::Control* control = nullptr; dialog::EventHandler original = nullptr;
        dialog::Rect area{}; std::uint32_t flags = 0, flags2 = 0;
    };
    struct RenderRow {
        const std::uint8_t* native_text = nullptr; // Address only; render never dereferences it.
        std::shared_ptr<const std::string> text;
        std::shared_ptr<const std::string> prefixed_text;
        std::size_t native_length = 0;
        std::int16_t id = 0;
        bool hotkey_prefix = false;
    };
    struct RenderDiagnostics {
        std::atomic<std::uint64_t> calls{0}, exact{0}, hotkey_offset{0}, near_miss{0};
        std::atomic<std::uint32_t> offset{0xffffffffu}, row{0}, a{0}, b{0}, draw{0}, g{0}, h{0};
    };
    struct RenderTable {
        std::array<RenderRow, 12> rows{}; unsigned count = 0;
        std::shared_ptr<RenderDiagnostics> diagnostics;
    };
    struct Hud {
        dialog::Dialog* root = nullptr;
        dialog::Control* button = nullptr;
        dialog::EventHandler original = nullptr;
        std::uint32_t thread = 0;
        bool live = false, needs_rebind = false;
    };
    struct WaveHud {
        dialog::Dialog* root=nullptr; dialog::Control* text=nullptr;
        dialog::EventHandler original=nullptr; std::uint32_t thread=0; bool live=false;
        dialog::Control* cargo=nullptr; dialog::EventHandler cargo_original=nullptr;
        std::uint64_t cargo_token=0,pressed_token=0; bool cargo_pressed=false;
    };
    void observe_wave_hud(dialog::Dialog*) noexcept;
    bool revalidate_wave_hud(WaveHud&) noexcept;
    void refresh_wave_hud() noexcept;
    bool cargo_state(std::uint64_t&,std::uint32_t&,std::uint32_t&,std::uint32_t* pages=nullptr) const noexcept;
    void restore_wave_child(WaveHud&) noexcept;
    bool scope() const noexcept;
    bool valid_offer(const ChoiceOffer&) const noexcept;
    bool begin_menu(dialog::Dialog*, dialog::EventHandler, bool spawned) noexcept;
    bool bind_menu() noexcept;
    bool arrange_menu() noexcept;
    void restore_layout() noexcept;
    void detach_menu() noexcept;
    void restore_handlers() noexcept;
    bool refresh() noexcept;
    void clear_render_text() noexcept;
    void report_render_stats(std::uint64_t) noexcept;
    std::shared_ptr<const std::string> stable_text(const std::string&);
    void resume() noexcept;
    void auto_open() noexcept;
    void observe_hud(dialog::Dialog*) noexcept;
    bool revalidate_hud(Hud&) noexcept;
    dialog::Control* control(std::int16_t) const noexcept;
    dialog::EventHandler original_handler(dialog::Control*) const noexcept;
    void report(const char*) const noexcept;
    DialogUiCallbacks callbacks_{};
    std::atomic<std::uint32_t> owner_{0}, gui_owner_{0}, epoch_{0};
    std::atomic<unsigned> native_run_depth_{0};
    ChoiceOffer offer_{}, displayed_{}, pressed_{}, preview_offer_{}, opened_offer_{};
    std::uint32_t preview_slot_ = 0, pressed_id_ = 0, menu_epoch_ = 0;
    std::uint32_t attempted_epoch_ = 0;
    bool supported_ = false, pending_ = false, waiting_ = false, dirty_ = false;
    bool deferred_clear_ = false, deferred_error_ = false, in_pump_ = false;
    bool opening_ = false, attempted_ = false, armed_ = false, spawned_ = false;
    bool root_init_observed_ = false;
    bool layout_ready_ = false;
    bool closing_ = false, in_resume_ = false, in_refresh_ = false;
    bool bind_warning_ = false, hud_warning_ = false;
    bool body_storage_logged_ = false, body_write_logged_ = false;
    std::uint64_t last_pump_ = 0;
    dialog::Dialog* menu_ = nullptr;
    dialog::EventHandler root_original_ = nullptr;
    std::array<Binding, 12> bindings_{};
    unsigned binding_count_ = 0;
    std::array<Hud, 4> hud_{};
    std::array<WaveHud, 4> wave_hud_{};
    std::string wave_timer_text_;
    bool wave_hud_warning_=false;
    std::shared_ptr<const RenderTable> render_text_;
    std::shared_ptr<RenderDiagnostics> render_diagnostics_;
    std::uint64_t render_probe_started_ = 0;
    bool render_probe_reported_ = false;
    // Interned immutable UTF8 survives all offer/reset/delete generations until
    // DLL destruction, so a native returned suffix pointer is never transient.
    std::vector<std::shared_ptr<const std::string>> stable_texts_;
};
} // namespace sc1_native
