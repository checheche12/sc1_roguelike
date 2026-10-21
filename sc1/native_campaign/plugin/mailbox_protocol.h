#pragma once

#include <cstddef>
#include <cstdint>

// GRW1 / CHC1 protocol version 1. The frame hook is the sole caller; no worker
// thread or game memory address is accessed by this component.
namespace sc1_native {

struct GrowthSnapshot {
    std::uint32_t talent_bits[16]{};
    std::uint8_t curse_counts[64]{};
    std::uint32_t talent_ranks[32]{};
    std::uint32_t wire_version{1};
    std::uint32_t completed_phase{};      // PHC1 only; legacy snapshots use 0
};

struct ChoiceOffer {
    std::uint32_t wire_version{1};        // v2 permits a standalone talent confirmation
    std::uint32_t kind{};                 // 1 talent, 2 curse
    std::uint32_t count{};                // v1: 4 talent; v2: 1..4 talent; 3 curse
    std::uint32_t candidates[4]{};        // catalog bit/byte index + 1
    std::uint32_t partners[4]{};          // optional second legendary, same index encoding
    std::uint32_t thirds[4]{};            // optional third common unit manual (BND2)
    std::uint32_t token_words[4]{};       // UUID.bytes, read as little-endian DWORDs
    std::uint32_t revision{};
    std::uint32_t pending_talents{};
    std::uint32_t pending_curses{};
    std::uint8_t curse_counts[16]{};
    std::uint32_t phase_version{};        // 1: three checkpoints, 2: four checkpoints
    std::uint32_t requested_phase{};      // PHC1 UI metadata; legacy 0
    std::uint32_t completed_phase{};
};

enum class MailboxError : std::uint32_t {
    None = 0, Allocation = 1, RandomSource = 2, UnsupportedMission = 3,
    MissingApplyCallback = 4, ManagerRejected = 5, InvalidStatus = 6,
    InvalidOffer = 7, InvalidSnapshot = 8, InvalidNonce = 9,
    ApplyFailed = 10, InvalidCompletion = 11, RequestCorrupted = 12,
    OfferCallbackFailed = 13
};

struct MailboxCallbacks {
    void* context{};
    bool (*apply_snapshot)(void*, const GrowthSnapshot&){};
    void (*show_offer)(void*, const ChoiceOffer&){};
    void (*clear_offer)(void*){};
    void (*on_error)(void*, std::uint32_t){};
};

class MailboxProtocol final {
public:
    MailboxProtocol() noexcept = default;
    // Retires the mailbox without host callbacks; use explicit shutdown while
    // game data is valid when temporary choice units also require cleanup.
    ~MailboxProtocol() noexcept;
    MailboxProtocol(const MailboxProtocol&) = delete;
    MailboxProtocol& operator=(const MailboxProtocol&) = delete;

    // A fresh MEM_PRIVATE/PAGE_READWRITE mailbox and fresh request sequence are
    // allocated per mission. Call shutdown before restoring game/DAT state.
    bool initialize(const MailboxCallbacks& callbacks, std::uint32_t mission = 101,
                    bool phased = false, std::uint32_t wire_version = 1, std::uint32_t phase_version = 1) noexcept;
    void shutdown() noexcept;
    void tick() noexcept;
    bool submit_choice(std::uint32_t slot) noexcept;
    bool request_phase(std::uint32_t phase) noexcept;
    void on_goal_reached() noexcept;

    bool ready() const noexcept { return state_ == 2; }
    bool failed() const noexcept { return state_ == 5; }
    bool victory_ack_ready() const noexcept { return state_ == 4 && goal_reached_ && applied_ && (!phased_ || completed_phase_ == total_phases()); }
    bool offer_active() const noexcept { return offer_active_; }
    bool growth_applied() const noexcept { return applied_; }
    bool already_completed() const noexcept { return already_complete_; }
    bool phased() const noexcept { return phased_; }
    std::uint32_t requested_phase() const noexcept { return requested_phase_; }
    std::uint32_t total_phases() const noexcept {return phase_version_==2 ? 4u : 3u;}
    std::uint32_t phase_version() const noexcept {return phase_version_;}
    std::uint32_t completed_phase() const noexcept { return completed_phase_; }
    std::uint32_t state() const noexcept { return state_; }
    std::uint32_t error_code() const noexcept { return error_; }
    const char* rejection_message() const noexcept { return rejection_message_; }
    std::uint32_t campaign_revision() const noexcept { return campaign_revision_; }
    std::uint32_t completed_mask() const noexcept { return completed_mask_; }
    const ChoiceOffer& current_offer() const noexcept { return offer_; }
    std::uintptr_t address() const noexcept { return reinterpret_cast<std::uintptr_t>(mailbox_); }
    volatile std::uint32_t* mailbox_words() const noexcept { return mailbox_; }

private:
    void publish(std::uint32_t state, std::uint32_t operation) noexcept;
    void fail(MailboxError error) noexcept;
    void advance_goal() noexcept;
    bool read_response(std::uint32_t (&words)[96]) const noexcept;
    bool valid_request() const noexcept;
    bool accept_offer(const std::uint32_t (&words)[96]) noexcept;
    bool accept_snapshot(const std::uint32_t (&words)[96]) noexcept;
    bool accept_completion(const std::uint32_t (&words)[96]) noexcept;

    volatile std::uint32_t* mailbox_{};
    MailboxCallbacks callbacks_{};
    ChoiceOffer offer_{};
    ChoiceOffer request_offer_{};
    std::uint32_t mission_{101};
    std::uint32_t state_{};
    std::uint32_t operation_{};
    std::uint32_t request_sequence_{};
    std::uint32_t last_response_{};
    std::uint32_t gold_{};
    std::uint32_t nonce_[4]{};
    std::uint32_t selected_slot_{};
    std::uint32_t request_slot_{};
    std::uint32_t campaign_revision_{};
    std::uint32_t completed_mask_{};
    std::uint32_t error_{};
    char rejection_message_[333]{};
    std::uint32_t requested_phase_{};
    std::uint32_t completed_phase_{};
    std::uint32_t wire_version_{1};
    std::uint32_t phase_version_{1};
    GrowthSnapshot snapshot_{};
    bool phased_{};
    bool applied_{};
    bool already_complete_{};
    bool goal_reached_{};
    bool offer_active_{};
};

}  // namespace sc1_native
