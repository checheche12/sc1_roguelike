#pragma once
#include "wave_progression.h"
#include "../wave_runtime.h"
#include <fstream>
#include <set>
#include <vector>
namespace host_test {
namespace progression_fixture {
using namespace sc1_native;using namespace wave_progression;
inline std::vector<UnitId> plan(U32 race,bool air,U32 second,U32 ordinal,U32 budget_left){
    std::vector<UnitId> result;for(U32 made=0;made<480;made++){
        const auto unit=select(race,air,second,ordinal,made,budget_left);if(!unit.valid)break;
        CHECK(unit.supply>0 && unit.supply<=budget_left);CHECK(permitted(unit.unit_id));
        CHECK(!air || air_only_unit(unit.unit_id));CHECK(made || !anti_air_only(unit.unit_id));
        result.push_back(unit.unit_id);budget_left-=unit.supply;
    }return result;
}
struct Troop{UnitId id;int owner,x,y;};
struct Simulator{
    WaveRuntime waves;std::vector<Troop> troops;std::vector<UnitId> created;U32 frame=0,second=0,warnings=0,first_spawn=0xffffffffu;bool home=true,blocked=false,fail=false;
    static U32 count(void* p,int owner,int id,const WaveRect* rect){auto& s=*static_cast<Simulator*>(p);
        if(owner==1 && id==7)return s.home?1u:0u;if(s.blocked && rect && owner==1 && id==kWaveAnyUnit)return 1;
        U32 n=0;for(const auto& u:s.troops)if((owner<0 || owner==u.owner) && (id<0 || id==u.id) &&
            (!rect || (u.x>=rect->left && u.x<=rect->right && u.y>=rect->top && u.y<=rect->bottom)))++n;return n;
    }
    static void* spawn(void* p,UnitId id,int x,int y,std::uint8_t owner){auto& s=*static_cast<Simulator*>(p);if(s.fail)return nullptr;
        s.troops.push_back({id,owner,x,y});s.created.push_back(id);s.first_spawn=std::min(s.first_spawn,s.second);return &s;}
    static void attack(void* p,std::uint8_t owner,const WaveRect* area,int x,int y){auto& s=*static_cast<Simulator*>(p);
        for(auto& u:s.troops)if(u.owner==owner && u.x>=area->left && u.x<=area->right && u.y>=area->top && u.y<=area->bottom){u.x=x;u.y=y;}}
    static void warning(void* p,U32,const WavePoint*){++static_cast<Simulator*>(p)->warnings;}
    WaveHost host(){return {this,count,spawn,attack,warning,standard_supply};}
    void tick(bool ready=true,bool goal=false,std::uint8_t stacks=0,std::uint8_t fast=0){second=frame/24;auto h=host();waves.tick(frame,ready,second,stacks,goal,h,fast);++frame;}
    void through(U32 target,bool ready=true,bool goal=false,std::uint8_t stacks=0,std::uint8_t fast=0){while(frame<=target*24)tick(ready,goal,stacks,fast);}
    U32 supply()const{U32 n=0;for(const auto& u:troops)n+=standard_supply(u.id);return n;}
};
}
void progression_time_and_budget(){
    using namespace sc1_native::wave_progression;
    CHECK(first_elapsed_seconds(false)==300 && first_elapsed_seconds(true)==360);
    CHECK(tier(0)==0 && tier(299)==0 && tier(599)==0 && tier(600)==1 && tier(899)==1 && tier(900)==2);
    CHECK(base_budget(false,0)==16 && base_budget(false,12)==64 && base_budget(false,0xffffffffu)==64);
    CHECK(base_budget(true,0)==8 && base_budget(true,0xffffffffu)==8);
    CHECK(live_supply_cap(false)==480 && live_supply_cap(true)==24);
    for(U32 stacks:{0u,1u,3u,15u,255u,0xffffffffu})for(U32 wave:{0u,1u,4u,12u,0xffffffffu}){
        CHECK(budget(false,wave,stacks)<=480 && budget(true,wave,stacks)<=24);
        CHECK(interval_seconds(false,stacks)>=45 && interval_seconds(true,stacks)>=45);
    }
    CHECK(interval_seconds(false,0)==120 && interval_seconds(true,0)==180);
    CHECK(interval_seconds(false,1)==109 && interval_seconds(true,1)==163);
}
void progression_compositions_and_costs(){
    using namespace progression_fixture;
    // Independently parse the sealed managed extended DAT descriptor for field46.
    std::ifstream input("../managed_dat/arr/units.dat",std::ios::binary);CHECK(input.good());input.seekg(0,std::ios::end);const auto size=input.tellg();
    std::vector<unsigned char> bytes(static_cast<std::size_t>(size));input.seekg(0);input.read(reinterpret_cast<char*>(bytes.data()),size);
    const auto get16=[&](std::size_t p){return U32(bytes[p])|(U32(bytes[p+1])<<8);};
    const auto get32=[&](std::size_t p){return get16(p)|(get16(p+2)<<16);};
    U32 offset=0,width=0;for(U32 i=0;i<get32(12);i++)if(get16(16+12*i)==46){width=1u<<get16(18+12*i);offset=get32(20+12*i);}
    CHECK(offset && width==1);std::set<UnitId> unique;
    for(const auto id:kUnits){CHECK(unique.insert(id).second);CHECK(bytes[offset+id]==standard_supply(id));}
    for(U32 race=0;race<3;race++)for(bool air:{false,true})for(U32 second:{300u,600u,900u})for(U32 wave=0;wave<8;wave++)for(U32 budget_left=1;budget_left<=64;budget_left++){
        const auto a=plan(race,air,second,wave,budget_left),b=plan(race,air,second,wave,budget_left);CHECK(a==b);
        U32 used=0;for(const auto id:a)used+=standard_supply(id);CHECK(used<=budget_left);
    }
    for(U32 race=0;race<3;race++){
        const auto basic=plan(race,false,300,0,64),middle=plan(race,false,600,0,64),late=plan(race,false,900,0,64);
        CHECK(std::none_of(basic.begin(),basic.end(),air_only_unit));CHECK(std::none_of(middle.begin(),middle.end(),air_only_unit));
        CHECK(std::any_of(late.begin(),late.end(),air_only_unit));CHECK(std::set<UnitId>(late.begin(),late.end()).size()>=5);
        std::set<std::vector<UnitId>> variants;for(U32 wave=0;wave<4;wave++)variants.insert(plan(race,false,900,wave,32));CHECK(variants.size()==4);
    }
    CHECK(air_only_unit(70) && air_only_unit(72)); // Original Protoss island-origin metadata; Carrier never enters a pool.
    CHECK(!select(3,false,900,0,0,480).valid && !select(Zerg,false,900,0,0,0).valid);
    const auto oversized=[](UnitId)->U32{return 500;};CHECK(!select(Terran,false,900,0,0,480,oversized).valid);
    // Forbidden requires-special-orders/ammunition and transportation units.
    for(U32 id:{11u,30u,33u,42u,59u,69u,72u,83u,85u,103u})CHECK(!permitted(static_cast<UnitId>(id)));
}
void progression_t01_scheduler(){
    using namespace progression_fixture;Simulator s;s.through(299);CHECK(s.created.empty() && s.warnings==0 && !s.waves.state().active);
    s.through(304);CHECK(s.first_spawn>=300 && s.first_spawn<=304);CHECK(!s.created.empty() && s.supply()<=16);
    for(const auto id:s.created)CHECK(id==37 || id==38);
    const auto prior_created=s.created.size();const auto warnings=s.warnings;auto h=s.host();s.waves.tick(s.frame-1,true,s.second,0,false,h);CHECK(s.created.size()==prior_created && s.warnings==warnings);
    s.through(560);const auto early=s.created;CHECK(std::none_of(early.begin(),early.end(),air_only_unit));
    Simulator late;late.frame=850*24;late.through(914);CHECK(std::any_of(late.created.begin(),late.created.end(),air_only_unit));
    CHECK(std::find(late.created.begin(),late.created.end(),UnitId(39))!=late.created.end());CHECK(late.supply()<=16);
    late.waves.reset();CHECK(!late.waves.state().active && !late.waves.state().pending && late.waves.state().stage==0);
}
void progression_t01_safety_and_caps(){
    using namespace progression_fixture;
    Simulator not_ready;not_ready.through(400,false);CHECK(not_ready.created.empty() && !not_ready.waves.state().active);
    Simulator done;done.through(400,true,true);CHECK(done.created.empty());
    Simulator home;home.home=false;home.through(400);CHECK(home.created.empty());home.home=true;home.through(459);CHECK(home.created.empty());home.through(465);CHECK(!home.created.empty());
    Simulator blocked;blocked.blocked=true;blocked.through(350);CHECK(blocked.created.empty() && blocked.warnings==0);blocked.blocked=false;blocked.through(419);CHECK(blocked.created.empty());blocked.through(425);CHECK(!blocked.created.empty());
    Simulator fail;fail.fail=true;fail.through(310);CHECK(fail.created.empty() && fail.waves.state().stage==0 && !fail.waves.state().pending);
    Simulator capped;for(U32 i=0;i<480;i++)capped.troops.push_back({37,6,1056,1600});capped.through(400);CHECK(capped.created.empty() && capped.warnings==0);
    Simulator stacks;stacks.through(299,true,false,255,255);CHECK(stacks.created.empty());stacks.through(304,true,false,255,255);CHECK(stacks.supply()<=480 && !stacks.created.empty());
}
inline constexpr std::size_t wave_progression_group_count=4;
void run_wave_progression_groups(){progression_time_and_budget();progression_compositions_and_costs();progression_t01_scheduler();progression_t01_safety_and_caps();}
}
