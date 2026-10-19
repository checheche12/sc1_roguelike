#include "mailbox_protocol.h"
#include <algorithm>
#include "include/legendary_bundles.generated.h"
#include "include/frozen_catalog.generated.h"
#include "include/campaign_config.generated.h"
#include "include/rework_catalog.generated.h"

#define WIN32_LEAN_AND_MEAN
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#include <bcrypt.h>
#include <cstring>

#pragma comment(lib, "bcrypt.lib")

namespace sc1_native {
namespace {
constexpr char kMagic[] = "SC1CAMP-PROBE-V1";
constexpr std::uint32_t kGrowthMagic = 0x47525731;
constexpr std::uint32_t kChoiceMagic = 0x43484331;
constexpr std::uint32_t kPhaseMagic = 0x50484331;
constexpr std::size_t kAllocationBytes = 4096;
static_assert(sizeof(kMagic) == 17, "Wire signature must be exactly 16 bytes");

std::uint32_t next_even(std::uint32_t value) noexcept {
    value = (value | 1u) + 1u;
    return value == 0 ? 2 : value;
}

bool any_nonce(const std::uint32_t* words) noexcept {
    return (words[0] | words[1] | words[2] | words[3]) != 0;
}

bool equal_nonce(const std::uint32_t* left, const std::uint32_t* right) noexcept {
    return left[0] == right[0] && left[1] == right[1] && left[2] == right[2] && left[3] == right[3];
}

void write_sequence(volatile std::uint32_t* target, std::uint32_t value) noexcept {
    // Aligned atomic DWORD publication; payload is always between odd/even.
    InterlockedExchange(reinterpret_cast<volatile LONG*>(target), static_cast<LONG>(value));
}

void clear_callback(const MailboxCallbacks& callbacks) noexcept {
    if (callbacks.clear_offer) {
        try { callbacks.clear_offer(callbacks.context); } catch (...) {}
    }
}
}  // namespace

MailboxProtocol::~MailboxProtocol() noexcept {
    // DLL/static destruction may run after the host's game data is gone. Only
    // explicit lifecycle shutdown may invoke the host's unit cleanup callback.
    callbacks_ = {};
    shutdown();
}

bool MailboxProtocol::initialize(const MailboxCallbacks& callbacks, std::uint32_t mission, bool phased, std::uint32_t wire_version, std::uint32_t phase_version) noexcept {
    shutdown();
    callbacks_ = callbacks;
    offer_ = {};
    request_offer_ = {};
    mission_ = mission;
    state_ = operation_ = request_sequence_ = last_response_ = gold_ = selected_slot_ = 0;
    campaign_revision_ = completed_mask_ = error_ = 0;
    request_slot_ = 0;
    std::memset(nonce_, 0, sizeof(nonce_));
    applied_ = already_complete_ = goal_reached_ = offer_active_ = false;
    phased_ = phased;
    wire_version_ = wire_version;
    phase_version_=phase_version;
    if((phase_version_!=1 && phase_version_!=2) || (phase_version_==2 && (!phased_ || wire_version_!=2))){fail(MailboxError::InvalidSnapshot);return false;}
    if(wire_version_!=1 && wire_version_!=2){ fail(MailboxError::InvalidSnapshot); return false; }
    requested_phase_ = phased ? 1u : 0u;
    completed_phase_ = 0;
    snapshot_ = {};
    bool supported=false;for(const auto& row:campaign_config::kMissions)if(row.mission_id==mission)supported=true;
    if (!supported) {
        fail(MailboxError::UnsupportedMission);
        return false;
    }
    if (!callbacks_.apply_snapshot) {
        fail(MailboxError::MissingApplyCallback);
        return false;
    }
    std::uint32_t seed = 0;
    if (BCryptGenRandom(nullptr, reinterpret_cast<PUCHAR>(&seed), sizeof(seed),
                        BCRYPT_USE_SYSTEM_PREFERRED_RNG) < 0) {
        fail(MailboxError::RandomSource);
        return false;
    }
    mailbox_ = static_cast<volatile std::uint32_t*>(VirtualAlloc(
        nullptr, kAllocationBytes, MEM_RESERVE | MEM_COMMIT, PAGE_READWRITE));
    if (!mailbox_) {
        fail(MailboxError::Allocation);
        return false;
    }
    // VirtualAlloc returns zeroed, page-aligned MEM_PRIVATE memory. The bridge
    // excludes module .data sections, so do not replace this with a static array.
    for (std::size_t index = 0; index < 4; ++index) {
        std::uint32_t word;
        std::memcpy(&word, kMagic + index * 4, sizeof(word));
        mailbox_[index] = word;
    }
    mailbox_[4] = 1;
    mailbox_[5] = mission_;
    mailbox_[16] = wire_version_==2 ? 128 : 64;
    mailbox_[17] = kGrowthMagic;
    mailbox_[18] = wire_version_;
    mailbox_[20] = kChoiceMagic;
    mailbox_[21] = 1;
    request_sequence_ = seed & ~1u;
    publish(1, 1);
    return true;
}

void MailboxProtocol::shutdown() noexcept {
    if (mailbox_) {
        // No cross-process acknowledgement exists for unloading. Invalidate the
        // header, then quarantine this tiny allocation for the process lifetime.
        // Releasing/reusing its address could let an already checked external
        // write hit another object or a new mission. One 4 KiB inaccessible page
        // per departed session is reclaimed by Windows when the process exits.
        write_sequence(mailbox_, 0);
        DWORD previous = 0;
        VirtualProtect(const_cast<std::uint32_t*>(mailbox_), kAllocationBytes,
                       PAGE_NOACCESS, &previous);
        mailbox_ = nullptr;
        clear_callback(callbacks_);
    }
    callbacks_ = {};
    state_ = operation_ = error_ = 0;
    applied_ = goal_reached_ = offer_active_ = already_complete_ = false;
    phased_ = false;
    phase_version_=1;
    requested_phase_ = completed_phase_ = 0;
    snapshot_ = {};
    offer_ = {};
}

void MailboxProtocol::publish(std::uint32_t state, std::uint32_t operation) noexcept {
    state_ = state;
    operation_ = operation;
    if (!mailbox_) return;
    const std::uint32_t committed = next_even(request_sequence_);
    request_offer_ = operation == 3 ? offer_ : ChoiceOffer{};
    request_slot_ = operation == 3 ? selected_slot_ : 0;
    write_sequence(mailbox_ + 8, committed - 1);
    mailbox_[7] = state;
    mailbox_[9] = operation;
    for (std::size_t index = 0; index < 4; ++index) mailbox_[10 + index] = nonce_[index];
    mailbox_[14] = 0;  // T01 has no currency reward.
    mailbox_[15] = gold_;
    mailbox_[19] = applied_ ? wire_version_ : 0;
    mailbox_[22] = request_slot_;
    for (std::size_t index = 0; index < 4; ++index)
        mailbox_[23 + index] = request_offer_.token_words[index];
    mailbox_[27] = request_offer_.revision;
    mailbox_[28] = request_offer_.kind;
    mailbox_[29] = phased_ ? kPhaseMagic : 0;
    mailbox_[30] = phased_ ? phase_version_ : 0u;
    mailbox_[31] = requested_phase_;
    MemoryBarrier();
    request_sequence_ = committed;
    write_sequence(mailbox_ + 8, committed);
}

bool MailboxProtocol::valid_request() const noexcept {
    if (!mailbox_) return false;
    for (std::size_t index = 0; index < 4; ++index) {
        std::uint32_t word;
        std::memcpy(&word, kMagic + index * 4, sizeof(word));
        if (mailbox_[index] != word || mailbox_[10 + index] != nonce_[index]) return false;
        if (mailbox_[23 + index] != request_offer_.token_words[index]) return false;
    }
    return mailbox_[4] == 1 && mailbox_[5] == mission_ && mailbox_[7] == state_
        && mailbox_[8] == request_sequence_ && mailbox_[9] == operation_ && mailbox_[14] == 0
        && mailbox_[15] == gold_ && mailbox_[16] == (wire_version_==2 ? 128u : 64u) && mailbox_[17] == kGrowthMagic
        && mailbox_[18] == wire_version_ && mailbox_[19] == (applied_ ? wire_version_ : 0u)
        && mailbox_[20] == kChoiceMagic && mailbox_[21] == 1
        && mailbox_[22] == request_slot_
        && mailbox_[27] == request_offer_.revision
        && mailbox_[28] == request_offer_.kind
        && mailbox_[29] == (phased_ ? kPhaseMagic : 0u)
        && mailbox_[30] == (phased_ ? phase_version_ : 0u) && mailbox_[31] == requested_phase_;
}

bool MailboxProtocol::read_response(std::uint32_t (&words)[96]) const noexcept {
    const auto before = mailbox_[32];
    if (before < 2 || (before & 1) || before == last_response_) return false;
    MemoryBarrier();
    for (std::size_t index = 0; index < (wire_version_==2 ? 96u : 32u); ++index) words[index] = mailbox_[32 + index];
    MemoryBarrier();
    return mailbox_[32] == before && words[0] == before && words[2] == request_sequence_;
}

void MailboxProtocol::fail(MailboxError error) noexcept {
    if (state_ == 5) return;
    error_ = static_cast<std::uint32_t>(error);
    offer_active_ = false;
    publish(5, 0);
    clear_callback(callbacks_);
    if (callbacks_.on_error) {
        try { callbacks_.on_error(callbacks_.context, error_); } catch (...) {}
    }
}

bool MailboxProtocol::accept_offer(const std::uint32_t (&words)[96]) noexcept {
    ChoiceOffer next{};
    next.wire_version = wire_version_;
    next.kind = words[12];
    next.revision = words[13];
    next.count = words[14];
    next.pending_talents = words[23];
    next.pending_curses = words[24];
    for (std::size_t index = 0; index < 4; ++index) {
        next.candidates[index] = words[15 + index];
        next.token_words[index] = words[19 + index];
    }
    if (words[11] != wire_version_ || next.pending_talents > (phased_ ? 1u : 3u) || next.pending_curses > (phased_ ? 1u : 2u)
        || !any_nonce(next.token_words) || (words[25] & 0xFF000000u)) return false;
    for (std::size_t index = 3; index <= 10; ++index) if (words[index]) return false;
    if (phased_) {
        if (words[26] != kPhaseMagic || words[27] != phase_version_ || words[28] != requested_phase_
            || words[29] != completed_phase_ || words[30] != total_phases() || words[31]
            || completed_phase_ + 1 != requested_phase_) return false;
        if ((wire_version_==1 && next.pending_curses != 1) || (next.kind == 2 && next.pending_talents)) return false;
        next.phase_version=phase_version_;
        next.requested_phase = requested_phase_;
        next.completed_phase = completed_phase_;
    } else {
        for (std::size_t index = 26; index < 32; ++index) if (words[index]) return false;
    }
    if (next.kind == 1) {
        if ((wire_version_==1 ? next.count!=4 : next.count<1 || next.count>4) || next.pending_talents == 0) return false;
    } else if (next.kind == 2) {
        if ((phase_version_==2 ? next.count<1 || next.count>3 : next.count!=3) || next.pending_curses == 0 || next.candidates[3]) return false;
    } else return false;
    for (std::size_t index = 0; index < next.count; ++index) {
        const auto candidate = next.candidates[index];
        if (candidate == 0 || candidate > (next.kind == 1 ? (wire_version_==2 ? frozen::kTalentCount : frozen::kLegacyTalentCount) : (wire_version_==2 ? frozen::kCurseCount : frozen::kLegacyCurseCount))) return false;
        for (std::size_t other = 0; other < index; ++other)
            if (candidate == next.candidates[other]) return false;
    }
    if(wire_version_==2){
        const bool paired=words[36]==0x424e4431u;
        for(std::size_t index=paired?37u:32u;index<96;++index)if(words[index])return false;
        if(paired){
            if(next.kind!=1)return false;
            bool any=false;
            for(std::size_t i=0;i<4;i++){
                next.partners[i]=words[32+i];
                if(!next.partners[i])continue;
                if(i>=next.count||!legendary_bundles::compatible(next.candidates[i],next.partners[i]))return false;
                for(std::size_t j=0;j<i;j++)if(next.candidates[i]==next.partners[j]&&next.partners[i]==next.candidates[j])return false;
                any=true;
            }
            if(!any)return false;
        }
    }
    for(std::size_t index=next.count;index<4;++index)if(next.candidates[index])return false;
    for (std::size_t index = 0; index < 3; ++index)
        next.curse_counts[index] = static_cast<std::uint8_t>(words[25] >> (index * 8));
    offer_ = next;
    selected_slot_ = 0;
    offer_active_ = true;
    if (callbacks_.show_offer) {
        try { callbacks_.show_offer(callbacks_.context, offer_); }
        catch (...) { fail(MailboxError::OfferCallbackFailed); return true; }
    }
    return true;
}

bool MailboxProtocol::accept_snapshot(const std::uint32_t (&words)[96]) noexcept {
    std::uint32_t phase = 0;
    if (phased_) {
        phase = (words[10] >> 8) & 0xFF;
        if (words[10] != (0x50480000u | (phase << 8) | requested_phase_)
            || phase < 1 || phase > total_phases() || phase <= completed_phase_) return false;
        // Only a fresh stage1 restore can return a later completed snapshot.
        if (applied_ && phase != requested_phase_) return false;
        if (!applied_ && (requested_phase_ != 1 || (phase > 1 && operation_ != 1))) return false;
        if ((words[9] & 1) && phase != total_phases()) return false;
    } else if (applied_ || words[10]) return false;
    if (words[11] != wire_version_) return false;
    for(std::size_t i=0;i<16;i++)if(words[12+i]&~frozen::kTalentMasks[i])return false;
    const auto curse_limit=wire_version_==2 ? 64u : 16u;
    const auto curse_count=wire_version_==2 ? frozen::kCurseCount : frozen::kLegacyCurseCount;
    for(std::size_t i=curse_count;i<curse_limit;i++)if((words[28+i/4]>>((i%4)*8))&255u)return false;
    for(std::size_t i=0;i<curse_count;i++)if(((words[28+i/4]>>((i%4)*8))&255u)>frozen::kCurseMaxStacks[i])return false;
    if(wire_version_==1)for(std::size_t bit=frozen::kLegacyTalentCount;bit<512;++bit)if((words[12+bit/32]>>(bit%32))&1u)return false;
    if(wire_version_==2) {
        static_assert(rework_catalog::kRankCount<=29,"QA26 counter slots overlap manual ranks");
        for(std::size_t i=rework_catalog::kRankCount;i<29;++i)if(words[44+i])return false;
        for(std::size_t slot=16;slot<=18;++slot){
            const auto extended=words[91-slot],byte=(words[28+slot/4]>>((slot%4)*8))&255u;
            if(extended && byte!=std::min(extended,255u))return false;
        }
        for(std::size_t i=76;i<96;++i)if(words[i])return false;
        for(std::size_t ordinal=0;ordinal<rework_catalog::kTalentCount;++ordinal){
            const auto slot=rework_catalog::kRankSlots[ordinal];if(slot<0)continue;
            const auto bit=rework_catalog::kTalentBase+ordinal;
            const bool owned=((words[12+bit/32]>>(bit%32))&1u)!=0;
            const bool ranked=words[44+slot]!=0;
            // Slots12..20 were unique health bits before QA10. A frozen old
            // snapshot legitimately has its bit set and an unused zero rank.
            if((ranked&&!owned)||(slot<12&&owned&&!ranked))return false;
        }
    }
    if (!any_nonce(words + 4)) { fail(MailboxError::InvalidNonce); return true; }
    if (applied_) {
        if (!equal_nonce(words + 4, nonce_)) { fail(MailboxError::InvalidNonce); return true; }
        if (words[3] != gold_ || words[8] != campaign_revision_ || words[9] != completed_mask_) return false;
    }
    GrowthSnapshot snapshot{};
    snapshot.wire_version=wire_version_;
    snapshot.completed_phase = phase;
    for (std::size_t index = 0; index < 16; ++index) snapshot.talent_bits[index] = words[12 + index];
    for (std::size_t index = 0; index < curse_limit; ++index)
        snapshot.curse_counts[index] = static_cast<std::uint8_t>(words[28 + index / 4] >> ((index % 4) * 8));
    if(wire_version_==2)for(std::size_t index=0;index<32;++index)snapshot.talent_ranks[index]=words[44+index];
    if (applied_) {
        for (std::size_t index = 0; index < 16; ++index) {
            if ((snapshot.talent_bits[index] & snapshot_.talent_bits[index]) != snapshot_.talent_bits[index]
                || snapshot.curse_counts[index] < snapshot_.curse_counts[index]) return false;
        }
        for(std::size_t index=0;index<curse_limit;++index)if(snapshot.curse_counts[index]<snapshot_.curse_counts[index])return false;
        for(std::size_t slot=16;wire_version_==2 && slot<=18;++slot){
            const auto current=std::max(std::uint32_t(snapshot.curse_counts[slot]),snapshot.talent_ranks[47-slot]);
            const auto previous=std::max(std::uint32_t(snapshot_.curse_counts[slot]),snapshot_.talent_ranks[47-slot]);
            if(current<previous)return false;
        }
        for(std::uint32_t ordinal=0;ordinal<rework_catalog::kTalentCount;++ordinal)
            if(rework_catalog::rank(snapshot,ordinal)<rework_catalog::rank(snapshot_,ordinal))return false;
    }
    bool success = false;
    try { success = callbacks_.apply_snapshot(callbacks_.context, snapshot); } catch (...) {}
    if (!success) { fail(MailboxError::ApplyFailed); return true; }
    applied_ = true;
    completed_phase_ = phase;
    snapshot_ = snapshot;
    offer_active_ = false;
    clear_callback(callbacks_);
    gold_ = words[3];
    for (std::size_t index = 0; index < 4; ++index) nonce_[index] = words[4 + index];
    campaign_revision_ = words[8];
    completed_mask_ = words[9];
    already_complete_ = (completed_mask_ & 1) != 0;
    publish(2, 0);
    advance_goal();
    return true;
}

bool MailboxProtocol::accept_completion(const std::uint32_t (&words)[96]) noexcept {
    if (!equal_nonce(words + 4, nonce_)) { fail(MailboxError::InvalidNonce); return true; }
    if (words[10] || words[3] != gold_ || !(words[9] & 1) || campaign_revision_ == 0xFFFFFFFFu
        || words[8] != campaign_revision_ + 1 || words[11] != wire_version_) return false;
    for (std::size_t index = 12; index < (wire_version_==2 ? 96u : 32u); ++index) if (words[index]) return false;
    campaign_revision_ = words[8];
    completed_mask_ = words[9];
    publish(4, 0);
    return true;
}

void MailboxProtocol::tick() noexcept {
    if (!mailbox_) return;
    // Heartbeat is intentionally outside the request identity/seqlock.
    InterlockedIncrement(reinterpret_cast<volatile LONG*>(mailbox_ + 6));
    if (state_ == 5) return;
    if (!valid_request()) { fail(MailboxError::RequestCorrupted); return; }
    if (state_ != 1 && state_ != 3) return;
    std::uint32_t words[96]{};
    if (!read_response(words)) return;
    last_response_ = words[0];
    if (words[1] == 3) { fail(MailboxError::ManagerRejected); return; }
    if (state_ == 1 && words[1] == 4) {
        if (!accept_offer(words)) fail(MailboxError::InvalidOffer);
    } else if (state_ == 1 && words[1] == 1) {
        if (!accept_snapshot(words)) fail(MailboxError::InvalidSnapshot);
    } else if (state_ == 3 && words[1] == 2) {
        if (!accept_completion(words)) fail(MailboxError::InvalidCompletion);
    } else fail(MailboxError::InvalidStatus);
}

bool MailboxProtocol::submit_choice(std::uint32_t slot) noexcept {
    if (!mailbox_ || state_ != 1 || !offer_active_ || slot == 0 || slot > offer_.count) return false;
    if (!valid_request()) { fail(MailboxError::RequestCorrupted); return false; }
    selected_slot_ = slot;
    offer_active_ = false;
    publish(1, 3);
    return true;
}

bool MailboxProtocol::request_phase(std::uint32_t phase) noexcept {
    if (!mailbox_ || !phased_ || state_ != 2 || !applied_ || already_complete_
        || phase < 2 || phase > total_phases() || phase != completed_phase_ + 1) return false;
    if (!valid_request()) { fail(MailboxError::RequestCorrupted); return false; }
    requested_phase_ = phase;
    offer_ = {};
    offer_active_ = false;
    selected_slot_ = 0;
    publish(1, 4);
    return true;
}

void MailboxProtocol::advance_goal() noexcept {
    if (!goal_reached_ || state_ != 2 || !applied_) return;
    if (phased_ && completed_phase_ != total_phases()) return;
    if (phased_) requested_phase_ = total_phases();
    // Completed records are replayed with their original frozen snapshot, and
    // the map's original objective still gates victory. They never COMMIT again.
    publish(already_complete_ ? 4 : 3, already_complete_ ? 0 : 2);
}

void MailboxProtocol::on_goal_reached() noexcept {
    if (!mailbox_ || state_ == 5) return;
    goal_reached_ = true;
    advance_goal();
}

}  // namespace sc1_native

#ifdef SC1_MAILBOX_PROTOCOL_TEST
// Standalone native tests and an interactive wire adapter. This executable only
// owns synthetic VirtualAlloc memory; it never opens a game or a database.
#include <array>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using sc1_native::MailboxProtocol;
using sc1_native::MailboxError;
using Reply = std::array<std::uint32_t, 96>;
#define CHECK(condition) do { if (!(condition)) throw std::runtime_error(std::string(__FUNCTION__) + ":" + std::to_string(__LINE__) + " " #condition); } while (false)

struct Host {
    std::uint32_t applies{}, offers{}, clears{}, errors{}, last_error{};
    bool accept{true};
    sc1_native::GrowthSnapshot snapshot{};
    sc1_native::ChoiceOffer offer{};
    sc1_native::MailboxCallbacks callbacks() {
        return {this,
            [](void* p, const sc1_native::GrowthSnapshot& value) { auto& h = *static_cast<Host*>(p); ++h.applies; h.snapshot = value; return h.accept; },
            [](void* p, const sc1_native::ChoiceOffer& value) { auto& h = *static_cast<Host*>(p); ++h.offers; h.offer = value; },
            [](void* p) { ++static_cast<Host*>(p)->clears; },
            [](void* p, std::uint32_t e) { auto& h = *static_cast<Host*>(p); ++h.errors; h.last_error = e; }};
    }
};

struct Fixture {
    Host host;
    MailboxProtocol protocol;
    Fixture(bool phased = false,std::uint32_t wire=1,std::uint32_t capability=1) { CHECK(protocol.initialize(host.callbacks(), 101, phased,wire,capability)); }
    Reply base(std::uint32_t status) {
        Reply reply{};
        const auto sequence = protocol.mailbox_words()[32];
        reply[0] = (sequence | 1u) + 1u;
        if (!reply[0]) reply[0] = 2;
        reply[1] = status;
        reply[2] = protocol.mailbox_words()[8];
        reply[11] = protocol.mailbox_words()[18];
        return reply;
    }
    Reply load(bool replay = false) {
        auto r = base(1);
        r[4] = 0x67452301; r[5] = 0xEFCDAB89; r[6] = 0x76543210; r[7] = 0xFEDCBA98;
        r[8] = replay ? 1 : 0; r[9] = replay ? 1 : 0;
        r[12] = 7;
        r[28] = 0x00010202;
        return r;
    }
    Reply offer(std::uint32_t round = 0) {
        auto r = base(4);
        r[12] = round < 3 ? 1 : 2;
        r[13] = round;
        r[14] = round < 3 ? 4 : 3;
        r[15] = 1; r[16] = 2; r[17] = 3; r[18] = round < 3 ? 4 : 0;
        r[19] = 0x33221100 + round; r[20] = 0x77665544; r[21] = 0xBBAA9988; r[22] = 0xFFEEDDCC;
        r[23] = round < 3 ? 3 - round : 0;
        r[24] = round < 3 ? 2 : 5 - round;
        r[25] = round == 4 ? 1 : 0;
        return r;
    }
    Reply saved() {
        auto r = base(2);
        for (std::size_t i = 0; i < 4; ++i) r[4 + i] = protocol.mailbox_words()[10 + i];
        r[3] = protocol.mailbox_words()[15];
        r[8] = protocol.campaign_revision() + 1;
        r[9] = protocol.completed_mask() | 1;
        return r;
    }
    void send(const Reply& r) {
        auto* m = protocol.mailbox_words();
        m[32] = r[0] | 1;
        for (std::size_t i = 1; i < (m[18]==2 ? 96u : 32u); ++i) m[32 + i] = r[i];
        MemoryBarrier();
        m[32] = r[0];
        protocol.tick();
    }
};

void header_and_private_memory() {
    Fixture f;
    auto* m = f.protocol.mailbox_words();
    MEMORY_BASIC_INFORMATION info{};
    CHECK(VirtualQuery(const_cast<std::uint32_t*>(m), &info, sizeof(info)) == sizeof(info));
    CHECK(info.Type == MEM_PRIVATE && info.Protect == PAGE_READWRITE);
    CHECK(info.RegionSize >= 256);
    const auto* raw = reinterpret_cast<const char*>(const_cast<const std::uint32_t*>(m));
    CHECK(std::memcmp(raw, "SC1CAMP-PROBE-V1", 16) == 0);
    CHECK(m[4] == 1 && m[5] == 101 && m[7] == 1 && m[9] == 1 && m[16] == 64);
    CHECK(m[17] == 0x47525731 && m[18] == 1 && m[19] == 0 && m[20] == 0x43484331 && m[21] == 1);
    CHECK(m[8] >= 2 && !(m[8] & 1));
    const auto request = m[8];
    f.protocol.tick();
    CHECK(m[6] == 1 && m[8] == request && f.host.applies == 0);
    for (std::size_t i = 32; i < 64; ++i) CHECK(m[i] == 0);
}

void load_applies_exactly_once() {
    Fixture f;
    f.send(f.load());
    CHECK(f.protocol.ready() && f.protocol.growth_applied() && f.host.applies == 1);
    CHECK(f.host.snapshot.talent_bits[0] == 7 && f.host.snapshot.curse_counts[0] == 2);
    CHECK(f.host.snapshot.curse_counts[1] == 2 && f.host.snapshot.curse_counts[2] == 1);
    CHECK(f.protocol.mailbox_words()[19] == 1 && f.protocol.mailbox_words()[9] == 0);
    for (int i = 0; i < 10; ++i) f.protocol.tick();
    CHECK(f.host.applies == 1 && !f.protocol.victory_ack_ready());
}

void five_choices_save_then_final_load_and_commit() {
    Fixture f;
    for (std::uint32_t round = 0; round < 5; ++round) {
        const auto r = f.offer(round);
        f.send(r);
        CHECK(f.protocol.offer_active() && f.host.offers == round + 1);
        CHECK(f.host.applies == 0 && f.host.clears == 0);
        CHECK(f.protocol.submit_choice(round < 3 ? 4 : 3));
        auto* m = f.protocol.mailbox_words();
        CHECK(m[9] == 3 && m[22] == (round < 3 ? 4u : 3u));
        CHECK(m[27] == round && m[28] == (round < 3 ? 1u : 2u));
        for (int i = 0; i < 4; ++i) CHECK(m[23 + i] == r[19 + i]);
        const auto seq = m[8];
        CHECK(!f.protocol.submit_choice(1) && m[8] == seq);
        CHECK(!f.protocol.victory_ack_ready());
    }
    f.send(f.load());
    CHECK(f.protocol.ready() && f.host.applies == 1 && f.host.clears == 1);
    f.protocol.on_goal_reached();
    CHECK(f.protocol.state() == 3 && f.protocol.mailbox_words()[9] == 2);
    CHECK(!f.protocol.victory_ack_ready());
    f.send(f.saved());
    CHECK(f.protocol.victory_ack_ready() && f.protocol.state() == 4 && f.host.applies == 1);
    f.protocol.on_goal_reached(); f.protocol.tick();
    CHECK(f.host.applies == 1 && f.protocol.mailbox_words()[9] == 0);
}

void odd_and_stale_response_are_ignored() {
    Fixture f;
    auto r = f.load();
    r[0] |= 1; f.send(r);
    CHECK(f.host.applies == 0 && !f.protocol.failed());
    r[0] = 4; r[2] -= 2; f.send(r);
    CHECK(f.host.applies == 0 && !f.protocol.failed());
    r[0] = 6; r[2] = f.protocol.mailbox_words()[8]; f.send(r);
    CHECK(f.host.applies == 1 && f.protocol.ready());
}

void invalid_growth_never_applies() {
    for (int variant = 0; variant < 7; ++variant) {
        Fixture f; auto r = f.load();
        if (variant == 0) r[11] = 2;
        // Expanded catalogs legitimately own bit127. Inject the first bit
        // beyond the frozen catalog while retaining the out-of-range guard.
        static_assert(frozen::kTalentCount < 512, "invalid-bit fixture needs an unused wire bit");
        if (variant == 1) r[12 + frozen::kTalentCount / 32] |= 1u << (frozen::kTalentCount % 32);
        if (variant == 2) r[27] = 1;
        if (variant == 3) r[31] |= 0x01000000;
        if (variant == 4) r[31] = 0xffffffff;
        if (variant == 5) r[10] = 1;
        if (variant == 6) r[30] = 4u<<8; // slot9 has a source-defined cap3
        f.send(r);
        CHECK(f.protocol.failed() && f.host.applies == 0 && !f.protocol.victory_ack_ready());
    }
}

void invalid_offer_never_reaches_ui() {
    for (int variant = 0; variant < 12; ++variant) {
        Fixture f; auto r = f.offer();
        if (variant == 0) r[11] = 2;
        if (variant == 1) r[12] = 3;
        if (variant == 2) r[14] = 3;
        if (variant == 3) r[15] = frozen::kTalentCount + 1;
        if (variant == 4) r[15] = r[16];
        if (variant == 5) r[19] = r[20] = r[21] = r[22] = 0;
        if (variant == 6) r[23] = 0;
        if (variant == 7) r[23] = 4;
        if (variant == 8) r[24] = 3;
        if (variant == 9) r[25] = 0x01000000;
        if (variant == 10) r[31] = 1;
        if (variant == 11) r[3] = 1;
        f.send(r);
        CHECK(f.protocol.failed() && f.host.offers == 0 && f.host.applies == 0);
    }
}

void zero_nonce_and_error_ack_fail_closed() {
    { Fixture f; auto r = f.load(); r[4] = r[5] = r[6] = r[7] = 0; f.send(r);
      CHECK(f.protocol.error_code() == static_cast<std::uint32_t>(MailboxError::InvalidNonce)); }
    { Fixture f; auto r = f.base(3); r[10] = 1; f.send(r);
      CHECK(f.protocol.failed() && f.host.applies == 0 && f.host.errors == 1); }
    { Fixture f; f.send(f.base(9)); CHECK(f.protocol.failed() && f.host.applies == 0); }
}

void completion_validation_never_reapplies() {
    for (int variant = 0; variant < 6; ++variant) {
        Fixture f; f.send(f.load()); f.protocol.on_goal_reached(); auto r = f.saved();
        if (variant == 0) ++r[4];
        if (variant == 1) r[9] = 0;
        if (variant == 2) ++r[3];
        if (variant == 3) ++r[8];
        if (variant == 4) r[12] = 7;
        if (variant == 5) r[11] = 0;
        f.send(r);
        CHECK(f.protocol.failed() && !f.protocol.victory_ack_ready() && f.host.applies == 1);
    }
}

void early_goal_waits_for_load_and_durable_ack() {
    Fixture f; f.protocol.on_goal_reached();
    CHECK(f.protocol.state() == 1 && !f.protocol.victory_ack_ready());
    f.send(f.load());
    CHECK(f.protocol.state() == 3 && !f.protocol.victory_ack_ready());
    f.send(f.saved());
    CHECK(f.protocol.victory_ack_ready());
}

void completed_replay_requires_objective_and_never_commits() {
    Fixture f; f.send(f.load(true));
    CHECK(f.protocol.ready() && f.protocol.already_completed() && !f.protocol.victory_ack_ready());
    f.protocol.on_goal_reached();
    CHECK(f.protocol.victory_ack_ready() && f.protocol.mailbox_words()[9] == 0 && f.host.applies == 1);
}

void callback_failure_is_fatal() {
    Fixture f; f.host.accept = false; f.send(f.load());
    CHECK(f.protocol.failed() && !f.protocol.growth_applied() && !f.protocol.victory_ack_ready());
    CHECK(f.host.last_error == static_cast<std::uint32_t>(MailboxError::ApplyFailed));
}

void reset_quarantines_old_mailbox_and_rejects_old_ack() {
    Fixture f; auto stale = f.load(); auto* old = f.protocol.mailbox_words();
    CHECK(f.protocol.initialize(f.host.callbacks()));
    CHECK(f.protocol.mailbox_words() != old);
    MEMORY_BASIC_INFORMATION info{};
    CHECK(VirtualQuery(const_cast<std::uint32_t*>(old), &info, sizeof(info)) == sizeof(info));
    CHECK(info.Type == MEM_PRIVATE && info.Protect == PAGE_NOACCESS);
    stale[2] = f.protocol.mailbox_words()[8] - 2;
    f.send(stale);
    CHECK(f.host.applies == 0 && f.protocol.state() == 1);
    f.send(f.load()); CHECK(f.protocol.ready());
    f.protocol.shutdown(); f.protocol.tick(); f.protocol.on_goal_reached();
    CHECK(!f.protocol.mailbox_words() && !f.protocol.victory_ack_ready());
}

void destruction_never_calls_host_but_explicit_shutdown_does() {
    Host host;
    volatile std::uint32_t* retired = nullptr;
    {
        MailboxProtocol protocol;
        CHECK(protocol.initialize(host.callbacks()));
        retired = protocol.mailbox_words();
    }
    CHECK(host.clears == 0 && host.errors == 0);
    MEMORY_BASIC_INFORMATION info{};
    CHECK(VirtualQuery(const_cast<std::uint32_t*>(retired), &info, sizeof(info)) == sizeof(info));
    CHECK(info.Type == MEM_PRIVATE && info.Protect == PAGE_NOACCESS);
    {
        MailboxProtocol protocol;
        CHECK(protocol.initialize(host.callbacks()));
        protocol.shutdown();
        CHECK(host.clears == 1);
        protocol.shutdown();
        CHECK(host.clears == 1);
    }
    CHECK(host.clears == 1);
}

void slots_and_request_ownership() {
    Fixture f; f.send(f.offer());
    CHECK(!f.protocol.submit_choice(0) && !f.protocol.submit_choice(5));
    const auto* m = f.protocol.mailbox_words();
    Reply saved{}; for (int i = 0; i < 32; ++i) saved[i] = m[32 + i];
    CHECK(f.protocol.submit_choice(1));
    for (int i = 0; i < 32; ++i) CHECK(saved[i] == m[32 + i]);
    f.send(f.offer(3)); CHECK(!f.protocol.submit_choice(4) && f.protocol.submit_choice(3));
}

void unsupported_mission_and_corrupt_request_fail_closed() {
    Host host; MailboxProtocol p;
    CHECK(!p.initialize(host.callbacks(), 999) && !p.mailbox_words() && p.failed());
    Fixture f; f.protocol.mailbox_words()[9] = 99; f.protocol.tick();
    CHECK(f.protocol.failed() && f.host.applies == 0);
}

void maximum_supported_snapshot_is_valid() {
    Fixture f;auto r=f.load();for(std::size_t bit=0;bit<frozen::kLegacyTalentCount;++bit)r[12+bit/32]|=1u<<(bit%32);
    for(std::size_t i=0;i<4;i++)r[28+i]=0;
    for(std::size_t i=0;i<frozen::kLegacyCurseCount;i++)r[28+i/4]|=frozen::kCurseMaxStacks[i]<<((i%4)*8);f.send(r);
    CHECK(f.protocol.ready());for(std::size_t i=0;i<frozen::kLegacyCurseCount;i++)CHECK(f.host.snapshot.curse_counts[i]==frozen::kCurseMaxStacks[i]);
    CHECK(f.host.snapshot.curse_counts[15]==0);
}

void dump(Fixture& f) {
    std::cout << "DUMP";
    for (std::uint32_t i = 0; i < f.protocol.mailbox_words()[16]; ++i) std::cout << ' ' << f.protocol.mailbox_words()[i];
    std::cout << ' ' << f.host.applies << ' ' << f.host.offers << ' ' << f.host.clears
              << ' ' << f.host.errors << ' ' << f.protocol.error_code()
              << ' ' << f.protocol.victory_ack_ready() << '\n' << std::flush;
}

int wire_loop(bool phased = false,std::uint32_t wire=1,std::uint32_t capability=1) {
    Fixture f(phased,wire,capability); dump(f);
    std::string command;
    while (std::cin >> command) {
        if (command == "QUIT") return 0;
        if (command == "RESPONSE") {
            Reply r{}; for (std::size_t i=0;i<(wire==2 ? 96u : 32u);++i) if (!(std::cin >> r[i])) return 2;
            f.send(r);
        } else if (command == "TICK") f.protocol.tick();
        else if (command == "CHOOSE") { std::uint32_t slot; if (!(std::cin >> slot)) return 2; f.protocol.submit_choice(slot); }
        else if (command == "GOAL") f.protocol.on_goal_reached();
        else if (command == "RESET") { if (!f.protocol.initialize(f.host.callbacks(), 101, phased,wire,capability)) return 2; }
        else if (command == "PHASE") { std::uint32_t phase; if (!(std::cin >> phase)) return 2; f.protocol.request_phase(phase); }
        else if (command != "DUMP") return 2;
        dump(f);
    }
    return 0;
}

void qa16_bundle_numeric_offer_validation() {
    for(unsigned invalid=0;invalid<6;invalid++){
        Fixture f(true,2);auto r=f.offer();r[23]=1;r[24]=0;r[26]=0x50484331;r[27]=1;r[28]=1;r[29]=0;r[30]=3;
        r[14]=1;r[15]=300;r[16]=r[17]=r[18]=0;r[32]=302;r[36]=0x424e4431;
        if(invalid==1)r[32]=301; // same unit family
        if(invalid==2)r[32]=257; // global extra attack
        if(invalid==3)r[32]=341; // other race
        if(invalid==4)r[36]=0;   // missing marker
        if(invalid==5)r[33]=302; // absent slot
        f.send(r);CHECK(invalid ? f.protocol.failed():f.protocol.offer_active());
        if(!invalid)CHECK(f.host.offer.partners[0]==302&&f.protocol.submit_choice(1));
    }
}
void rework_v2_extended_snapshot_and_single_offer() {
    // QA26 counters cross byte255 without spilling into adjacent curse bytes.
    for(std::uint32_t count:{4u,255u,256u,1000u,0xffffffffu}){
        Fixture extended(true,2);auto payload=extended.load();payload[10]=0x50480101;
        for(std::size_t slot=16;slot<=18;++slot){
            payload[28+slot/4]|=std::min(count,255u)<<((slot%4)*8);
            payload[91-slot]=count;
        }
        extended.send(payload);CHECK(extended.protocol.ready());
        CHECK(extended.host.snapshot.talent_ranks[31]==count);
        CHECK(extended.host.snapshot.curse_counts[19]==0);
        CHECK(extended.protocol.request_phase(2));auto next=extended.load();next[10]=0x50480202;
        next[32]=payload[32];
        for(std::size_t slot=16;slot<=18;++slot)next[91-slot]=payload[91-slot];
        next[32]=(next[32]&~255u)|std::min(count-1,255u);
        next[75]=count-1;extended.send(next);
        CHECK(extended.protocol.failed()); // Decreasing the wide count is rejected.
    }
    {Fixture invalid(true,2);auto payload=invalid.load();payload[10]=0x50480101;
     payload[75]=256;invalid.send(payload);CHECK(invalid.protocol.failed());}
    Fixture f(true,2);auto* m=f.protocol.mailbox_words();
    CHECK(m[16]==128 && m[18]==2);
    auto offer=f.offer();offer[23]=1;offer[24]=0;
    offer[26]=0x50484331;offer[27]=1;offer[28]=1;offer[29]=0;offer[30]=3;
    offer[14]=1;offer[15]=257;offer[16]=offer[17]=offer[18]=0;
    f.send(offer);CHECK(f.protocol.offer_active() && f.host.offer.count==1);
    CHECK(!f.protocol.submit_choice(2) && f.protocol.submit_choice(1));
    auto r=f.load();r[10]=0x50480101;
    const std::uint32_t bit=rework_catalog::kTalentBase+8;
    r[12+bit/32]|=1u<<(bit%32);r[44]=19;
    r[28+49/4]|=3u<<((49%4)*8);
    f.send(r);CHECK(f.protocol.ready() && m[19]==2);
    CHECK(f.host.snapshot.wire_version==2 && f.host.snapshot.talent_ranks[0]==19);
    CHECK(f.host.snapshot.curse_counts[49]==3 && rework_catalog::rank(f.host.snapshot,8)==4);
    CHECK(f.protocol.request_phase(2));
    r=f.load();r[10]=0x50480202;r[12+bit/32]|=1u<<(bit%32);r[44]=3;
    r[28+49/4]|=3u<<((49%4)*8);f.send(r);
    CHECK(f.protocol.failed() && f.host.applies==1);
}

void qa10_health_bit_fallback_and_capped_phase_transition() {
    Fixture f(true,2);auto r=f.load();r[10]=0x50480101;
    const auto manual=rework_catalog::kTalentBase+8,health=rework_catalog::kTalentBase+26;
    r[12+manual/32]|=1u<<(manual%32);r[44]=19;
    r[12+health/32]|=1u<<(health%32);f.send(r);
    CHECK(f.protocol.ready()&&f.host.snapshot.talent_ranks[12]==0);
    CHECK(rework_catalog::rank(f.host.snapshot,26)==1&&rework_catalog::rank(f.host.snapshot,8)==4);
    CHECK(f.protocol.request_phase(2));r=f.load();r[10]=0x50480202;
    r[12+manual/32]|=1u<<(manual%32);r[44]=4;
    r[12+health/32]|=1u<<(health%32);r[44+12]=2;f.send(r);
    CHECK(f.protocol.ready()&&f.host.applies==2);
    CHECK(rework_catalog::rank(f.host.snapshot,26)==2&&rework_catalog::rank(f.host.snapshot,8)==4);
}

void rework_v2_rejects_rank_bit_mismatch_and_reserved_payload() {
    for(bool mismatch:{false,true}) {
        Fixture f(false,2);auto r=f.load();
        if(mismatch)r[44]=1;else r[95]=1;
        f.send(r);CHECK(f.protocol.failed() && f.host.applies==0);
    }
}


Reply phase_load(Fixture& f, std::uint32_t phase, bool replay = false) {
    auto r=f.load(replay);
    r[10]=0x50480000u | (phase<<8) | f.protocol.requested_phase();
    r[12]=(1u<<phase)-1;
    r[28]=phase;
    return r;
}
Reply phase_offer(Fixture& f, bool curse = false) {
    auto r=f.offer(curse ? 3u : 0u);
    r[23]=curse ? 0u : 1u; r[24]=1;
    r[26]=0x50484331; r[27]=1; r[28]=f.protocol.requested_phase();
    r[29]=f.protocol.completed_phase(); r[30]=3;
    return r;
}
void phased_three_pairs_and_ack() {
    Fixture f(true);auto* m=f.protocol.mailbox_words();
    CHECK(m[29]==0x50484331 && m[30]==1 && m[31]==1 && m[19]==0);
    CHECK(f.protocol.phased() && f.protocol.completed_phase()==0 && !f.protocol.request_phase(2));
    f.protocol.on_goal_reached();
    for(std::uint32_t phase=1;phase<=3;phase++) {
        if(phase>1) {
            CHECK(f.protocol.request_phase(phase));
            CHECK(m[9]==4 && m[19]==1 && m[31]==phase && m[10]!=0);
            CHECK(!f.protocol.request_phase(phase));
        }
        for(bool curse:{false,true}) {
            f.send(phase_offer(f,curse));CHECK(f.protocol.offer_active());
            CHECK(f.host.offer.requested_phase==phase && f.host.offer.completed_phase==phase-1);
            CHECK(f.protocol.submit_choice(curse ? 3u : 4u));
            CHECK(m[9]==3 && m[31]==phase && ((m[10]!=0)==(phase>1)));
        }
        auto r=phase_load(f,phase);f.send(r);
        CHECK(f.host.applies==phase && f.host.snapshot.completed_phase==phase);
        CHECK(f.protocol.completed_phase()==phase && m[19]==1);
        CHECK(f.protocol.state()==(phase==3 ? 3u : 2u));
        CHECK(!f.protocol.victory_ack_ready());
        f.send(r);CHECK(f.host.applies==phase); // duplicate response sequence
    }
    CHECK(m[9]==2 && m[31]==3);
    f.send(f.saved());CHECK(f.protocol.victory_ack_ready() && f.host.applies==3);
    CHECK(!f.protocol.request_phase(3));
}
void phased_restore_highest_and_replay() {
    for(std::uint32_t phase=1;phase<=3;phase++) {
        Fixture f(true);f.send(phase_load(f,phase));
        CHECK(f.host.applies==1 && f.protocol.completed_phase()==phase && f.protocol.ready());
        CHECK(f.protocol.requested_phase()==1 && !f.protocol.victory_ack_ready());
        f.protocol.on_goal_reached();
        if(phase==3) {
            CHECK(f.protocol.state()==3 && f.protocol.mailbox_words()[31]==3);
            f.send(f.saved());CHECK(f.protocol.victory_ack_ready());
        } else {
            CHECK(f.protocol.ready() && f.protocol.request_phase(phase+1));
        }
    }
    Fixture replay(true);replay.send(phase_load(replay,3,true));
    CHECK(!replay.protocol.victory_ack_ready());replay.protocol.on_goal_reached();
    CHECK(replay.protocol.victory_ack_ready() && replay.protocol.mailbox_words()[9]==0);
    CHECK(replay.protocol.mailbox_words()[31]==3 && replay.host.applies==1);
}
void phased_snapshot_validation() {
    for(int variant=0;variant<13;variant++) {
        Fixture f(true);f.send(phase_load(f,1));CHECK(f.protocol.request_phase(2));
        auto r=phase_load(f,2);
        if(variant==0)r[10]=0;
        if(variant==1)r[10]=0x50480201;
        if(variant==2)r[10]=0x50480102;
        if(variant==3)r[10]=0x50480302;
        if(variant==4)r[10]=0x51480202;
        if(variant==5)r[4]++;
        if(variant==6)r[3]++;
        if(variant==7)r[8]++;
        if(variant==8)r[9]++;
        if(variant==9)r[12]=2; // removed previous talent
        if(variant==10)r[28]=0; // removed previous curse
        if(variant==11)r[27]=1;
        if(variant==12)r[31]=0x01000000;
        f.send(r);CHECK(f.protocol.failed() && f.host.applies==1 && !f.protocol.victory_ack_ready());
    }
    Fixture f(true);f.send(phase_offer(f));CHECK(f.protocol.submit_choice(1));
    f.send(phase_load(f,3));CHECK(f.protocol.failed() && f.host.applies==0);
}
void phased_offer_validation() {
    for(int variant=0;variant<10;variant++) {
        Fixture f(true);auto r=phase_offer(f);
        if(variant==0)r[26]=0;
        if(variant==1)r[27]=2;
        if(variant==2)r[28]=2;
        if(variant==3)r[29]=1;
        if(variant==4)r[30]=2;
        if(variant==5)r[31]=1;
        if(variant==6)r[23]=2;
        if(variant==7)r[24]=2;
        if(variant==8)r[24]=0;
        if(variant==9){r=phase_offer(f,true);r[23]=1;}
        f.send(r);CHECK(f.protocol.failed() && f.host.offers==0 && f.host.applies==0);
    }
}
void phased_later_apply_failure_and_request_corruption() {
    Fixture f(true);f.send(phase_load(f,1));CHECK(!f.protocol.request_phase(3));
    CHECK(f.protocol.request_phase(2));f.host.accept=false;f.send(phase_load(f,2));
    CHECK(f.protocol.failed() && f.protocol.completed_phase()==1 && !f.protocol.victory_ack_ready());
    Fixture corrupted(true);corrupted.protocol.mailbox_words()[31]=3;corrupted.protocol.tick();
    CHECK(corrupted.protocol.failed() && corrupted.host.applies==0);
}
int phase_tests() {
    const std::vector<std::function<void()>> tests={phased_three_pairs_and_ack,
        phased_restore_highest_and_replay,phased_snapshot_validation,phased_offer_validation,
        phased_later_apply_failure_and_request_corruption};
    for(const auto& test:tests)test();
    std::cout << "{\"phase_cpp_tests\":" << tests.size() << ",\"passed\":true,\"game_accessed\":false,\"database_accessed\":false}\n";
    return 0;
}

void print_python_driver() {
    // Extract with --python-driver and run from the repository root, passing
    // this test executable. It imports the unchanged real Python serializers.
    std::cout << R"PY(import json, pathlib, struct, subprocess, sys, uuid
sys.path.insert(0, str(pathlib.Path.cwd()))
from sc1.bridge.protocol import (read_request, choice_payload, response_payload,
                                publish_response, validate_header, WORDS)
from sc1.campaign.runtime_catalog import load_catalog, encode_growth

BASE = 0x10000
class Memory:
    def __init__(self, words): self.data = bytearray(WORDS.pack(*words))
    def read(self, address, size): return bytes(self.data[address-BASE:address-BASE+size])
    def write(self, address, data): self.data[address-BASE:address-BASE+len(data)] = data

executable = pathlib.Path(sys.argv[1]).resolve()
process = subprocess.Popen([str(executable), '--wire'], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           text=True, encoding='utf-8')
def receive():
    line = process.stdout.readline()
    if not line.startswith('DUMP '): raise AssertionError('C++ harness output: ' + line)
    values = [int(value) for value in line.split()[1:]]
    assert len(values) == 70
    words, counters = values[:64], values[64:]
    validate_header(WORDS.pack(*words), BASE)
    return words, counters
def command(text):
    process.stdin.write(text + '\n'); process.stdin.flush()
    return receive()
def deliver(words, payload):
    memory = Memory(words)
    request = read_request(memory, BASE)
    publish_response(memory, BASE, request, payload)
    manager_half = WORDS.unpack(memory.data)[32:]
    return command('RESPONSE ' + ' '.join(str(word) for word in manager_half))

try:
    catalog = load_catalog()
    words, counters = receive()
    original_nonce = '0123456789abcdef1032547698badcfe'
    selected, curses = [], {}
    for round_index in range(5):
        kind = 1 if round_index < 3 else 2
        candidates = ([item for item in catalog['talents'] if item['id'] not in selected][:4]
                      if kind == 1 else catalog['curses'][:3])
        token = uuid.UUID(int=uuid.UUID('00112233-4455-6677-8899-aabbccddeeff').int + round_index)
        state = {'state':'choosing','offer':{'offer_id':str(token),
                 'kind':'talent' if kind == 1 else 'curse','revision':round_index,
                 'candidates':candidates},
                 'pending':{'talent':max(0,3-round_index),'curse':2 if round_index<3 else 5-round_index},
                 'curses':[{**item,'stacks':curses[item['id']]} for item in catalog['curses'] if item['id'] in curses]}
        request = read_request(Memory(words), BASE)
        words, counters = deliver(words, choice_payload(request, state))
        assert words[7] == 1 and counters[0] == 0 and counters[1] == round_index + 1
        slot = 4 if kind == 1 else 3
        words, counters = command('CHOOSE ' + str(slot))
        selected_request = read_request(Memory(words), BASE)
        assert selected_request.operation == 3 and selected_request.choice_slot == slot
        assert selected_request.choice_kind == kind and selected_request.choice_revision == round_index
        assert selected_request.choice_token == token.bytes.hex()
        identity = candidates[slot-1]['id']
        if kind == 1: selected.append(identity)
        else: curses[identity] = curses.get(identity,0) + 1
    growth = encode_growth(catalog, selected, curses)
    result = {'nonce':original_nonce,'gold':0,'revision':0,'completed_mask':0,'growth_words':growth}
    request = read_request(Memory(words), BASE)
    words, counters = deliver(words, response_payload(request, result, 1))
    assert words[7] == 2 and words[19] == 1 and counters[0] == 1 and counters[2] == 1
    words, counters = command('GOAL')
    request = read_request(Memory(words), BASE)
    assert request.state == 3 and request.operation == 2 and request.nonce == original_nonce
    assert request.growth_applied == 1 and not counters[5]
    receipt = {**result,'revision':1,'completed_mask':1}
    words, counters = deliver(words, response_payload(request, receipt, 2))
    assert words[7] == 4 and counters[0] == 1 and counters[5] == 1
    words, counters = command('RESET')
    request = read_request(Memory(words), BASE)
    words, counters = deliver(words, response_payload(request, receipt, 1))
    assert words[7] == 2 and counters[0] == 2 and not counters[5]
    words, counters = command('GOAL')
    assert words[7] == 4 and words[9] == 0 and counters[5] == 1
    words, counters = command('RESET')
    request = read_request(Memory(words), BASE)
    fatal = struct.pack('<10I',3,request.sequence,0,0,0,0,0,0,0,1)
    words, counters = deliver(words, fatal)
    assert words[7] == 5 and counters[0] == 2 and counters[3] == 1 and not counters[5]
    print(json.dumps({'python_payload_compatibility':True,'candidate_counts':[4,4,4,3,3],
          'uuid_bytes_exact':True,'nonce_exact':True,'load_apply_once':True,
          'commit_zero_extension_no_reapply':True,'replay_no_duplicate_commit':True,
          'short_fatal_ack_accepted':True,'game_accessed':False,'database_accessed':False}))
finally:
    if process.poll() is None:
        process.stdin.write('QUIT\n'); process.stdin.flush()
    code = process.wait(timeout=5)
    error = process.stderr.read()
    process.stdin.close(); process.stdout.close(); process.stderr.close()
    if code: raise RuntimeError('C++ harness failed: ' + error)
)PY";
}
}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc == 2 && std::string(argv[1]) == "--wire") return wire_loop();
        if (argc == 2 && std::string(argv[1]) == "--phase-wire") return wire_loop(true);
        if (argc == 2 && std::string(argv[1]) == "--rework-wire") return wire_loop(true,2);
        if (argc == 2 && std::string(argv[1]) == "--checkpoint-wire") return wire_loop(true,2,2);
        if (argc == 2 && std::string(argv[1]) == "--phase-tests") return phase_tests();
        if (argc == 2 && std::string(argv[1]) == "--python-driver") { print_python_driver(); return 0; }
        const std::vector<std::function<void()>> tests = {
            header_and_private_memory, load_applies_exactly_once,
            five_choices_save_then_final_load_and_commit, odd_and_stale_response_are_ignored,
            invalid_growth_never_applies, invalid_offer_never_reaches_ui,
            zero_nonce_and_error_ack_fail_closed, completion_validation_never_reapplies,
            early_goal_waits_for_load_and_durable_ack,
            completed_replay_requires_objective_and_never_commits, callback_failure_is_fatal,
            reset_quarantines_old_mailbox_and_rejects_old_ack,
            destruction_never_calls_host_but_explicit_shutdown_does, slots_and_request_ownership,
            unsupported_mission_and_corrupt_request_fail_closed, maximum_supported_snapshot_is_valid,
            qa16_bundle_numeric_offer_validation,rework_v2_extended_snapshot_and_single_offer,qa10_health_bit_fallback_and_capped_phase_transition,rework_v2_rejects_rank_bit_mismatch_and_reserved_payload
        };
        for (const auto& test : tests) test();
        std::cout << "{\"cpp_tests\":" << tests.size() << ",\"passed\":true,\"game_accessed\":false,\"database_accessed\":false}\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
#endif  // SC1_MAILBOX_PROTOCOL_TEST
