namespace host_test {
inline void completion_diagnostic_is_read_only_and_bounded(){
    reset();make_chk();init_units(original);CHECK(g.active);
    const auto before=game;
    CHECK(completion_diagnostics::step(&game,100));
    for(U32 n=101;n<30100;n+=47)CHECK(!completion_diagnostics::step(&game,n));
    CHECK(completion_diagnostics::step(&game,30100));
    CHECK(std::memcmp(&before,&game,sizeof(game))==0);
    CHECK(completion_diagnostics::state.samples==2);
    CHECK(!counter(kReadyCounter)&&!counter(kAckCounter));
    CHECK(set_counter(kRouteCounter,1)&&set_counter(kGoalCounter,1));
    const auto goal=game;
    CHECK(completion_diagnostics::step(&game,30101));
    CHECK(std::memcmp(&goal,&game,sizeof(game))==0);
    CHECK(!counter(kReadyCounter)&&!counter(kAckCounter));
    init_game();CHECK(!completion_diagnostics::state.seen);
    CHECK(!completion_diagnostics::step(&game,60101));
}
}
