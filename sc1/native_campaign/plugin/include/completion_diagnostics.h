// Read-only evidence for an intermittent ending stall. Never release a gate.
namespace completion_diagnostics {
struct State {
    bool seen=false;
    std::uint64_t last_ms=0;
    std::array<U32,10> signature{};
    U32 samples=0;
};
inline State state{};
inline void reset() noexcept {state={};}
inline bool step(bw::Game* game,std::uint64_t now) noexcept {
    if(!game || !g.active || !g.mission)return false;
    const auto owner=player_owner();
    const std::array<U32,10> signature{{g.mission->mission_id,counter_value(kRouteCounter),
        counter(kGoalCounter)?1u:0u,counter(kReadyCounter)?1u:0u,counter(kAckCounter)?1u:0u,
        g.protocol.state(),g.protocol.completed_phase(),g.protocol.requested_phase(),
        g.dialog.open()?1u:0u,g.protocol.error_code()}};
    // Also run from the paused UI pump: a stalled simulation still leaves evidence.
    if(state.seen && state.signature==signature && now-state.last_ms<30000)return false;
    state.seen=true;state.signature=signature;state.last_ms=now;++state.samples;
    log_event("Completion diagnostic: mission=%u frame=%u elapsed=%u route=%u goal=%u ready=%u ack=%u state=%u completed=%u requested=%u dialog=%u error=%u objective=%u victory=%u switches=%08x/%08x/%08x/%08x/%08x/%08x/%08x/%08x",
        signature[0],game->frame_count,game->elapsed_seconds,signature[1],signature[2],signature[3],signature[4],
        signature[5],signature[6],signature[7],signature[8],signature[9],game->player_objectives_string[owner],
        U32(game->victory_state[owner]),game->switches[0],game->switches[1],game->switches[2],game->switches[3],
        game->switches[4],game->switches[5],game->switches[6],game->switches[7]);
    return true;
}
}
