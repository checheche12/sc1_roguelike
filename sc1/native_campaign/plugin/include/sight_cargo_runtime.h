#pragma once
// Bounded core for the sight/cargo adapter. This file does not install hooks.
// Engine integration is deliberately gated until fog/detection and transport
// lifecycle adapters have been verified. Never expose a capacity > 8 to an
// engine loop over Unit::loaded_units[8].
#include <array>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include "bw_dat_x64.h"

namespace sc1::sight_cargo {
constexpr std::size_t kEnginePassengerSlots = 8;
constexpr std::size_t kLogicalPassengerSlots = 16;
constexpr unsigned kLogicalSpace = 12;
constexpr unsigned kMaximumLogicalSpace = 16;
constexpr unsigned kEngineSightMaximum = 11;

struct SightPlan {
    unsigned engine_range;
    unsigned requested_range;
    unsigned detection_range;
    bool needs_extension;
};
// baseline is original UnitSightRange with the talent DAT delta removed.
// It therefore already includes research and the native blind/building rules.
constexpr SightPlan plan_sight(unsigned baseline, bool enabled, bool blind,
                               bool active_detector) noexcept {
    const unsigned requested = enabled && !blind ? baseline + 2u : baseline;
    return {baseline, requested, active_detector && !blind ? requested : 0u,
            requested > kEngineSightMaximum};
}

struct IntegrationProof {
    bool fog_mask_and_retraction = false;
    bool detection_and_visibility = false;
    bool shared_vision_and_parasite = false;
    bool cargo_order_passthrough = false;
    bool cargo_lifecycle = false;
    bool cargo_passenger_ui = false;
    constexpr bool sight_ready() const noexcept {
        return fog_mask_and_retraction && detection_and_visibility && shared_vision_and_parasite;
    }
    constexpr bool cargo_ready() const noexcept {
        return cargo_order_passthrough && cargo_lifecycle && cargo_passenger_ui;
    }
};

struct Passenger {
    // Full generation-tagged engine lookup ID; not a raw pointer or array index.
    std::uint32_t handle = 0;
    std::uint8_t space = 0;
};
struct Window {
    std::array<Passenger, kEnginePassengerSlots> passengers{};
    std::size_t count = 0;
    unsigned space = 0;
};
class CargoLedger {
    std::array<Passenger, kLogicalPassengerSlots> passengers_{};
    std::size_t count_ = 0;
    unsigned used_ = 0;
    unsigned capacity_ = kLogicalSpace;
public:
    explicit CargoLedger(unsigned capacity=kLogicalSpace) noexcept :capacity_(capacity>=8 && capacity<=kMaximumLogicalSpace?capacity:kLogicalSpace){}
    std::size_t count() const noexcept { return count_; }
    unsigned used() const noexcept { return used_; }
    unsigned available() const noexcept { return capacity_ - used_; }
    const Passenger* find(std::uint32_t handle) const noexcept {
        for (std::size_t i = 0; i < count_; ++i)
            if (passengers_[i].handle == handle) return &passengers_[i];
        return nullptr;
    }
    bool can_board(Passenger p) const noexcept {
        return p.handle != 0 && p.space > 0 && p.space <= kEnginePassengerSlots &&
               count_ < kLogicalPassengerSlots && p.space <= available() && !find(p.handle);
    }
    // Call only after the original engine board operation confirms that the
    // same generation handle is hidden and linked to this carrier.
    bool commit_board(Passenger p) noexcept {
        if (!can_board(p)) return false;
        passengers_[count_++] = p;
        used_ += p.space;
        return true;
    }
    bool commit_leave(std::uint32_t handle) noexcept {
        for (std::size_t i = 0; i < count_; ++i) if (passengers_[i].handle == handle) {
            used_ -= passengers_[i].space;
            for (std::size_t j = i + 1; j < count_; ++j) passengers_[j - 1] = passengers_[j];
            passengers_[--count_] = {};
            return true;
        }
        return false;
    }
    // An exact fixed-size value, not a pointer to or write into the engine.
    // Reserving a boarding passenger guarantees both a free slot and adequate
    // engine-visible space while the separate ledger enforces logical 12.
    Window engine_window(unsigned reserve_space = 0) const noexcept {
        Window result{};
        if (reserve_space > kEnginePassengerSlots) return result;
        const auto max_count = reserve_space ? kEnginePassengerSlots - 1 : kEnginePassengerSlots;
        for (std::size_t i = 0; i < count_; ++i) {
            const auto p = passengers_[i];
            if (result.count < max_count && result.space + p.space + reserve_space <= kEnginePassengerSlots) {
                result.passengers[result.count++] = p;
                result.space += p.space;
            }
        }
        return result;
    }
    const std::array<Passenger, kLogicalPassengerSlots>& all() const noexcept { return passengers_; }
    void clear() noexcept { passengers_ = {}; count_ = 0; used_ = 0; }
};

// SCR's 8 physical slots use 16 low bits and 2 high bits per slot. Higher
// generation values are rejected, never truncated into a different unit ID.
struct PackedWindow {
    std::array<std::uint16_t, kEnginePassengerSlots> low{};
    std::uint16_t high = 0;
};
inline bool pack_window(const Window& source, PackedWindow& target) noexcept {
    if (source.count > kEnginePassengerSlots) return false;
    PackedWindow next{};
    for (std::size_t i = 0; i < source.count; ++i) {
        const auto handle = source.passengers[i].handle;
        if (handle == 0 || handle > 0x3ffffu) return false;
        next.low[i] = static_cast<std::uint16_t>(handle);
        next.high |= static_cast<std::uint16_t>((handle >> 16u) << (2u * i));
    }
    target = next;
    return true;
}
constexpr std::uint32_t unpack_slot(const PackedWindow& source, std::size_t index) noexcept {
    return index < kEnginePassengerSlots
        ? source.low[index] | (static_cast<std::uint32_t>((source.high >> (2u * index)) & 3u) << 16u)
        : 0u;
}
} // namespace sc1::sight_cargo

namespace sc1::sight_cargo {
// Uses the same full lookup ID as the pinned loader (11 index bits up to 1700
// units; 13 above 1700), proven at loader RVA 0xb2291.
class CargoAdapter {
public:
    using Enabled = bool (*)(const bw::Unit*);
    using Space = unsigned (*)(const bw::Unit*);
    using Capacity = unsigned (*)(const bw::Unit*);
    struct PageInfo { unsigned page = 0, pages = 1, passengers = 0, used_space = 0; };
    struct Token { bw::Unit* carrier = nullptr; std::uint32_t identity = 0; bool changed = false,boarding_denied=false; };
private:
    bw::Unit* units_ = nullptr;
    std::size_t length_ = 0;
    Enabled enabled_ = nullptr;
    Space space_ = nullptr;
    Capacity capacity_ = nullptr;
    bool writing_ = false;
    unsigned command_depth_ = 0;
    std::array<std::uint32_t,8191> page_identity_{};
    std::array<std::uint8_t,8191> page_{};
    bool valid(const bw::Unit* u) const noexcept {
        if (!units_ || !u) return false;
        const auto base = reinterpret_cast<std::uintptr_t>(units_);
        const auto addr = reinterpret_cast<std::uintptr_t>(u);
        return addr >= base && (addr - base) % sizeof(bw::Unit) == 0 &&
            (addr - base) / sizeof(bw::Unit) < length_;
    }
    bool alive(const bw::Unit* u) const noexcept {
        return valid(u) && u->flingy.sprite && u->flingy.hitpoints>0 && u->order!=0;
    }
    bool linked(const bw::Unit* passenger, const bw::Unit* carrier) const noexcept {
        return alive(passenger) && passenger->related == carrier && (passenger->flags & 0x40u) != 0;
    }
    bool eligible(const bw::Unit* carrier) const noexcept {
        if (!alive(carrier) || (!enabled_ && !capacity_) || !space_ ||
            (carrier->unit_id != 11 && carrier->unit_id != 69 && !(capacity_ && (carrier->unit_id==42 || carrier->unit_id==57))) || (carrier->flags & 0x40000000u)) return false;
        if (capacity_ ? capacity_(carrier)>8 : enabled_(carrier)) return true;
        unsigned used = 0, passengers = 0;
        for (std::size_t i = 0; i < length_; ++i) if (linked(units_+i,carrier)) {
            used += space_(units_+i); ++passengers;
            if (used > 8 || passengers > 8) return true;
        }
        return false;
    }
    bool collect(bw::Unit* carrier, CargoLedger& ledger) const noexcept {
        ledger.clear();
        if (!valid(carrier) || !carrier->flingy.sprite || !space_) return false;
        // The original engine owns the passenger Unit, its hidden-list entry,
        // related pointer and InTransport flag. These are authoritative even
        // while its handle is outside the current physical window.
        for (std::size_t i = 0; i < length_; ++i) {
            auto p = units_ + i;
            if (!linked(p, carrier)) continue;
            const auto size = space_(p);
            if (size == 0 || size > 8 || !ledger.commit_board({identity(p), static_cast<std::uint8_t>(size)}))
                return false;
        }
        return true;
    }
    bool write(bw::Unit* carrier, const Window& w) noexcept {
        PackedWindow packed{};
        if (!valid(carrier) || !pack_window(w, packed)) return false;
        for (std::size_t i = 0; i < 8; ++i) carrier->loaded_units[i] = packed.low[i];
        // In the 1700-unit layout the high-bits member is not cargo data.
        if (length_ > 1700) carrier->scr_carried_unit_high_bits = packed.high;
        return true;
    }
    Window visible_window(const CargoLedger& ledger, unsigned page = 0) const noexcept {
        Window w{}; unsigned current = 0;
        for (const auto p : ledger.all()) {
            if (!p.handle) break;
            if (w.space + p.space > 8 || w.count == 8) {
                if (current == page) break;
                w = {}; ++current;
            }
            w.passengers[w.count++] = p; w.space += p.space;
        }
        return w;
    }
    unsigned selected_page(bw::Unit* carrier, const CargoLedger& ledger) noexcept {
        const auto index = static_cast<std::size_t>(carrier-units_);
        const auto id = identity(carrier);
        if (page_identity_[index] != id || ledger.used() <= 8) { page_identity_[index] = id; page_[index] = 0; }
        if(page_[index]>=page_count(ledger))page_[index]=0;return page_[index];
    }
    unsigned page_count(const CargoLedger& ledger) const noexcept {unsigned pages=1,used=0,count=0;for(auto p:ledger.all()){if(!p.handle)break;if(used+p.space>8 || count==8){++pages;used=count=0;}used+=p.space;++count;}return pages;}
    unsigned available(bw::Unit* carrier, const CargoLedger& ledger) const noexcept {
        const unsigned requested=capacity_?capacity_(carrier):(enabled_(carrier)?12u:8u);
        const unsigned capacity=std::max(8u,std::min(kMaximumLogicalSpace,requested));
        return ledger.used() < capacity ? capacity-ledger.used() : 0u;
    }
public:
    bool bind(bw::Unit* units, std::size_t count, Enabled enabled, Space space) noexcept {
        if (!units || count == 0 || count > 8191 || !enabled || !space) return false;
        units_ = units; length_ = count; enabled_ = enabled; capacity_=nullptr;space_ = space; writing_ = false; command_depth_ = 0; page_identity_ = {}; page_ = {}; return true;
    }
    bool bind(bw::Unit* units,std::size_t count,Capacity capacity,Space space) noexcept {
        if(!units || !count || count>8191 || !capacity || !space)return false;
        units_=units;length_=count;capacity_=capacity;enabled_=nullptr;space_=space;writing_=false;command_depth_=0;page_identity_={};page_={};return true;
    }
    void reset() noexcept { units_ = nullptr; length_ = 0; enabled_ = nullptr;capacity_=nullptr; space_ = nullptr; writing_ = false;command_depth_=0; }
    std::uint32_t identity(const bw::Unit* u) const noexcept {
        if (!valid(u) || u->minor_unique_index > 31) return 0;
        const unsigned shift = length_ > 1700 ? 13u : 11u;
        return static_cast<std::uint32_t>(u - units_ + 1) | (static_cast<std::uint32_t>(u->minor_unique_index) << shift);
    }
    bw::Unit* resolve(std::uint32_t id) const noexcept {
        const unsigned shift = length_ > 1700 ? 13u : 11u;
        const auto index = id & ((1u << shift) - 1u);
        if (index == 0 || index > length_) return nullptr;
        auto u = units_ + index - 1;
        return alive(u) && identity(u) == id ? u : nullptr;
    }
    // Caller supplies the original owner-scoped order callback. Capacity DAT
    // MUST be <=8 there; this adapter never writes DAT or replaces pathing.
    Token before_order(bw::Unit* u) noexcept {
        if (writing_ || !alive(u)) return {};
        bw::Unit* carrier = nullptr;
        bw::Unit* boarding = nullptr;
        if (u->order == 92 && alive(u->order_target.unit)) {
            carrier = u->order_target.unit; boarding = u;
        } else if (u->order >= 93 && u->order <= 96) {
            carrier = u; boarding = u->order_target.unit;
        } else if (u->order == 111 || u->order == 112) {
            carrier = u;
        }
        if (!eligible(carrier)) return {};
        CargoLedger ledger{kMaximumLogicalSpace};
        if (!collect(carrier, ledger)) return {};
        auto w = ledger.engine_window();
        if (u == carrier && (u->order == 111 || u->order == 112)) {
            w = {};
            for (const auto p : ledger.all()) if (p.handle && w.count < 8) { w.passengers[w.count++] = p; w.space += p.space; }
        }
        bool denied=false;
        if (alive(boarding) && boarding->player == carrier->player && !linked(boarding, carrier)) {
            const auto needed = space_(boarding);
            const auto id = identity(boarding);
            if (needed > 0 && needed <= available(carrier,ledger) && ledger.can_board({id, static_cast<std::uint8_t>(needed)}))
                w = ledger.engine_window(needed);
            else {
                denied=true;
                w = ledger.engine_window();
            }
        }
        writing_ = true; const bool changed = write(carrier, w); writing_ = false;
        return {carrier, identity(carrier), changed,denied};
    }
    void after_order(Token token) noexcept {
        if (!token.changed || resolve(token.identity) != token.carrier) return;
        CargoLedger ledger{kMaximumLogicalSpace};
        if (!collect(token.carrier, ledger)) return;
        writing_ = true; write(token.carrier, visible_window(ledger,selected_page(token.carrier,ledger))); writing_ = false;
    }
    // For single-passenger unload commands, which may run outside order steps,
    // refill at the next simulation boundary; no game field is changed except
    // the eight handles and their documented high bits.
    void before_commands() noexcept {
        if (command_depth_++ || !units_) return;
        for (std::size_t i = 0; i < length_; ++i) {
            auto carrier = units_ + i;
            if (!eligible(carrier)) continue;
            CargoLedger ledger{kMaximumLogicalSpace};
            if (!collect(carrier, ledger)) continue;
            // Preserve the selected native window for single-unit unload and
            // lifecycle commands. Boarding gets its reserved window at the
            // authoritative native order callback, never by emptying all HUDs.
            write(carrier, visible_window(ledger,selected_page(carrier,ledger)));
        }
    }
    void after_commands() noexcept {
        if (command_depth_ && --command_depth_ == 0) refresh();
    }
    void refresh() noexcept {
        if (!units_) return;
        for (std::size_t i = 0; i < length_; ++i) {
            auto carrier = units_ + i;
            if (!eligible(carrier)) continue;
            CargoLedger ledger{kMaximumLogicalSpace};
            if (collect(carrier, ledger)) write(carrier, visible_window(ledger,selected_page(carrier,ledger)));
        }
    }
    template<class Callback> void for_each_passenger(bw::Unit* carrier, Callback callback) {
        if (!valid(carrier)) return;
        // Capture full identities before a callback can kill or transfer units.
        CargoLedger ledger{kMaximumLogicalSpace};
        if (!collect(carrier, ledger)) return;
        const auto all = ledger.all();
        for (const auto p : all) if (p.handle) {
            auto unit = resolve(p.handle);
            if (unit && linked(unit, carrier)) {
                CargoLedger current{kMaximumLogicalSpace};
                if (!collect(carrier, current)) return;
                Window present{}; present.passengers[present.count++] = p; present.space = p.space;
                for (const auto other : current.all()) if (other.handle && other.handle != p.handle && present.count < 8) {
                    present.passengers[present.count++] = other; present.space += other.space;
                }
                if (!write(carrier, present)) return;
                callback(unit);
                if (alive(carrier) && collect(carrier, current)) write(carrier, visible_window(current,selected_page(carrier,current)));
            }
        }
    }
    PageInfo page_info(bw::Unit* carrier) noexcept {
        CargoLedger ledger{kMaximumLogicalSpace};
        if (!eligible(carrier) || !collect(carrier,ledger)) return {};
        return {selected_page(carrier,ledger), page_count(ledger),
                static_cast<unsigned>(ledger.count()),ledger.used()};
    }
    bool toggle_page(bw::Unit* carrier) noexcept {
        CargoLedger ledger{kMaximumLogicalSpace};
        if (!eligible(carrier) || !collect(carrier,ledger) || ledger.used()<=8) return false;
        const auto current=selected_page(carrier,ledger),next=(current+1)%page_count(ledger);
        page_[carrier-units_] = static_cast<std::uint8_t>(next);
        return write(carrier,visible_window(ledger,next));
    }
    bool hide_window(bw::Unit* carrier) noexcept {return valid(carrier) && write(carrier,{});}
    bool present_passenger(std::uint32_t handle) noexcept {
        auto passenger=resolve(handle);if(!passenger)return false;auto carrier=passenger->related;if(!eligible(carrier) || !linked(passenger,carrier))return false;
        CargoLedger ledger{kMaximumLogicalSpace};if(!collect(carrier,ledger))return false;const auto p=ledger.find(handle);if(!p)return false;
        Window visible{};visible.passengers[visible.count++]=*p;visible.space=p->space;
        for(auto other:ledger.all())if(other.handle && other.handle!=handle && visible.count<8 && visible.space+other.space<=8){visible.passengers[visible.count++]=other;visible.space+=other.space;}
        return write(carrier,visible);
    }
    unsigned count(const bw::Unit* carrier) const noexcept {
        unsigned result = 0;
        if (valid(carrier)) for (std::size_t i = 0; i < length_; ++i) if (linked(units_ + i, carrier)) ++result;
        return result;
    }
};
} // namespace sc1::sight_cargo

namespace sc1::sight_cargo {
struct SightDescriptor {
    std::int32_t width = 0, height = 0, minimum_width = 3, minimum_height = 3;
    std::uint32_t minimum_count = 0, extended_count = 0;
    void* nodes = nullptr;
};
static_assert(sizeof(SightDescriptor) == 32, "13515 sight descriptor");
static_assert(offsetof(SightDescriptor, nodes) == 24, "13515 sight nodes");
class SightAdapter {
public:
    using Generate = void (*)(SightDescriptor*, std::uint32_t, std::uint32_t);
    using Release = void (*)(SightDescriptor*, std::uint32_t);
    using Original = void (*)(std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t, std::uint32_t);
    using Air = void (*)(std::int32_t, std::int32_t, SightDescriptor*, std::uint32_t*, std::uint32_t, std::uint32_t);
    using Environment = bool (*)(std::uint32_t*&, std::uint32_t&, std::uint32_t&);
private:
    Generate generate_ = nullptr; Release release_ = nullptr;
    Original original_ = nullptr; Air air_ = nullptr; Air edge_ = nullptr;
    Environment environment_ = nullptr;
    std::array<SightDescriptor, 2> masks_{};
    std::uint32_t mask_width_ = 0;
    bool ready_ = false;
    bool ensure_masks(std::uint32_t map_width) {
        if (mask_width_ == map_width && masks_[0].nodes && masks_[1].nodes) return true;
        reset_masks();
        masks_[0].width = masks_[0].height = 27; // 2 * sight12 + 3
        masks_[1].width = masks_[1].height = 29; // 2 * sight13 + 3
        generate_(masks_.data(), 2, map_width);
        for (const auto& m : masks_) if (!m.nodes || m.minimum_count != 9 || m.extended_count == 0 || m.extended_count > 841) {
            reset_masks(); return false;
        }
        mask_width_ = map_width; return true;
    }
public:
    void reset_masks() noexcept {
        if (release_ && (masks_[0].nodes || masks_[1].nodes)) release_(masks_.data(), 2);
        masks_ = {}; mask_width_ = 0;
    }
    bool bind(Generate generate, Release release, Original original, Air air, Air edge, Environment env) noexcept {
        reset_masks(); generate_ = generate; release_ = release; original_ = original;
        air_ = air; edge_ = edge; environment_ = env;
        ready_ = generate_ && release_ && original_ && air_ && edge_ && environment_;
        return ready_;
    }
    bool ready() const noexcept { return ready_; }
    void disable() noexcept { ready_ = false; reset_masks(); }
    void reveal(std::uint32_t x, std::uint32_t y, std::uint32_t in_air, std::uint32_t vision_mask,
                std::uint32_t range, std::uint32_t extra) {
        if (!original_) return;
        if (!ready_ || range < 12 || range > 13 || !in_air || vision_mask > 255 || extra != 0) {
            original_(x, y, in_air, vision_mask, range, extra); return;
        }
        std::uint32_t* tiles = nullptr; std::uint32_t width = 0, height = 0;
        if (!environment_(tiles, width, height) || !tiles || !width || !height || width > 256 || height > 256 ||
            x / 32 >= width || y / 32 >= height || !ensure_masks(width)) return;
        auto& mask = masks_[range - 12];
        const auto tx = static_cast<std::int32_t>(x / 32), ty = static_cast<std::int32_t>(y / 32);
        const auto radius = mask.width / 2;
        const bool clipped = tx < radius || ty < radius || tx + radius >= static_cast<std::int32_t>(width) ||
                             ty + radius >= static_cast<std::int32_t>(height);
        const auto and_mask = ~(vision_mask | (vision_mask << 8));
        // These are the original engine air-mask consumers, including its
        // footprint ordering and map-edge clipping. Reveal timing, shared
        // vision, parasite and ordinary retraction remain the original caller's.
        (clipped ? edge_ : air_)(tx, ty, &mask, tiles + tx + ty * width, vision_mask, and_mask);
    }
};
} // namespace sc1::sight_cargo
