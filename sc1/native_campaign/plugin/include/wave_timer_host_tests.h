#pragma once
#include "wave_timer.h"
namespace host_test {
void run_wave_timer_groups(){
    using namespace sc1_native;
    WaveState s{};
    CHECK(wave_countdown(false,false,101,false,0,0,false,0,s,0).kind==WaveCountdown::Kind::Hidden);
    CHECK(wave_countdown(true,true,101,false,500,0,false,0,s,0).kind==WaveCountdown::Kind::Hidden);
    CHECK(wave_countdown(true,false,101,false,500,0,false,0,s,0).kind==WaveCountdown::Kind::WaitingForHome);
    s.home_seen=true;
    CHECK(wave_countdown(true,false,101,false,20,0,false,0,s,0).seconds==284);
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,0).seconds==104);
    s.home_ticks=wave_config::kHomeGraceTicks-1;
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,0).seconds==104);
    s.home_ticks=wave_config::kHomeGraceTicks;
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,0).seconds==104);
    s.active=true;s.interval_ticks=24;
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,0).seconds==123);
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,255).seconds==48);
    s.pending=1;s.warning_ticks=1;
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,0).seconds==4);
    s.warning_ticks=73;
    CHECK(wave_countdown(true,false,101,false,200,0,false,0,s,0).seconds==1);
    // Earlier death-triggered reinforcement or a later split batch takes
    // priority over regular/T01 schedule only when it actually is sooner.
    CHECK(wave_countdown(true,false,101,false,200,0,true,210,s,0).seconds==1);
    s={};
    CHECK(wave_countdown(true,false,101,false,200,0,true,210,s,0).seconds==10);
    for(const auto& mission:campaign_config::kMissions){
        if(mission.mission_id==101)continue;
        const auto first=wave_progression::first_elapsed_seconds(mission.no_production);
        CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,0,0,false,0,s,0).seconds==first+4);
        CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,first-1,first,false,0,s,0).seconds==5);
        CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,first,first+120,true,first+4,s,0).seconds==4);
        CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,first+4,first+120,true,first+16,s,0).seconds==12);
        CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,300,420,true,310,s,0).seconds==10);
        CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,300,301,true,310,s,0).seconds==5);
        // Rendering/polling while simulation is paused cannot change time.
        const auto paused=wave_countdown(true,false,mission.mission_id,mission.no_production,300,420,true,310,s,0);
        for(int render=0;render<20;render++)CHECK(wave_countdown(true,false,mission.mission_id,mission.no_production,300,420,true,310,s,0).seconds==paused.seconds);
    }
    CHECK(wave_countdown_text({}).empty());
    CHECK(wave_countdown_text({WaveCountdown::Kind::WaitingForHome,0})=="공세 대기 · 기지 도착 후");
    CHECK(wave_countdown_text({WaveCountdown::Kind::Scheduled,154})=="공세 출발 02:34");
    CHECK(wave_countdown_text({WaveCountdown::Kind::Scheduled,0})=="공세 출발 00:00");
    CHECK(wave_countdown_text({WaveCountdown::Kind::Scheduled,99999})=="공세 출발 99:59");
}
}
