#pragma once
namespace host_test {
inline bool reference_placement_clear(int x,int y,bool raid){
 bool clear=true;U32 alive=0;
 living_units([&](bw::Unit* u){++alive;const auto p=u->flingy.position;const auto dx=std::int64_t(x)-p.x,dy=std::int64_t(y)-p.y,d=dx*dx+dy*dy;
  if(d<1600||(!raid&&wave_protected_unit(u)&&d<512ll*512))clear=false;});
 return clear&&alive<1550;
}
inline void placement_spatial_equivalence_and_batch_lifetime(){
 rework_wave_tests::begin(310);
 game.alliances[player_owner()][2]=1;game.starting_player_types[3]=3;
 for(U32 i=0;i<600;++i){auto u=add(i%7==0?176u:i%5==0?106u:65u,i%8,int((i*353)%8000),int((i*157)%8000));u->flags=1;if(i%17==0)u->order=0;if(i%19==0)u->flingy.hitpoints=0;}
 add(65,player_owner(),1000,1000)->flags=1;refresh_units();
 std::vector<std::pair<int,int>> points={{0,0},{8191,8191},{-32,-32},{1039,1000},{1040,1000},{1511,1000},{1512,1000}};
 for(U32 i=0;i<200;++i)points.push_back({int((i*463)%8192),int((i*521)%8192)});
 for(bool raid:{false,true}){
  std::vector<bool> expected;for(auto p:points)expected.push_back(reference_placement_clear(p.first,p.second,raid));
  {rework_waves::placement::Batch batch;for(std::size_t i=0;i<points.size();++i)CHECK(rework_waves::clear_cell(points[i].first,points[i].second,raid)==expected[i]);
   for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==310){CHECK(rework_waves::placement::safe(o)==origin_safe(o));CHECK(rework_waves::placement::base(o)==origin_has_live_base(o));}
  }
 }
 CHECK(rework_waves::placement::depth==0&&!rework_waves::placement::ready);
 units[1].player=U8(player_owner());units[1].flingy.position={6000,6000};units[1].flingy.hitpoints=256;units[1].order=3;
 {rework_waves::placement::Batch batch;CHECK(!rework_waves::clear_cell(6100,6000));}
 units[1].flingy.hitpoints=0;
 {rework_waves::placement::Batch batch;CHECK(rework_waves::clear_cell(6100,6000)==reference_placement_clear(6100,6000,false));}
}
inline void placement_creation_updates_supply_and_blocked_retry_is_linear(){
 rework_wave_tests::begin(310);g.current_wave_id=10;g.growth.curse_counts[16]=12;
 {rework_waves::placement::Batch batch;
  auto first=rework_waves::create(65,0);CHECK(first);const auto cost=std::max(1u,original_stat({0,46,65}));CHECK(rework_waves::live_supply()==cost);
  CHECK(!rework_waves::clear_cell(first->flingy.position.x,first->flingy.position.y));
  auto second=rework_waves::create(65,0);CHECK(second&&second!=first);CHECK(rework_waves::live_supply()==2*cost);
  CHECK(wave_targeting::distance(first->flingy.position.x,first->flingy.position.y,second->flingy.position.x,second->flingy.position.y)>=1600);
 }
 rework_wave_tests::begin(310);g.growth.curse_counts[16]=12;g.current_wave_id=10;
 for(const auto& o:sc1_native::campaign_wave_config::kOrigins)if(o.mission_id==310)for(U32 i=0;i<o.cell_count;++i)add(65,o.owner,o.cells[i].x,o.cells[i].y)->flags=1;
 while(count<1500)add(65,0,2000,2000)->flags=1;
 rework_waves::primary=rework_waves::choose_origin(true);CHECK(rework_waves::primary);rework_waves::timeline.active_ticks=1200*24;rework_waves::timeline.ordinal=10;
 rework_waves::main_wave();CHECK(!rework_waves::deferred.empty());const auto queued=rework_waves::deferred.size();
 host_unit_scans=host_unit_visits=0;rework_waves::timeline.active_ticks+=24;rework_waves::retry_dispatch();
 CHECK(count==1500&&rework_waves::deferred.size()==queued);CHECK(host_unit_scans<=2&&host_unit_visits<=3000);
 CHECK(rework_waves::placement::depth==0&&!rework_waves::placement::ready);
}
inline constexpr std::size_t placement_performance_group_count=2;
inline void run_placement_performance_groups(){placement_spatial_equivalence_and_batch_lifetime();placement_creation_updates_supply_and_blocked_retry_is_linear();}
}
