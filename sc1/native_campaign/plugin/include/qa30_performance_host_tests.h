#pragma once
namespace host_test {
inline constexpr std::size_t qa30_performance_group_count=7;
inline std::vector<bw::Unit*> qa30_reference_nearby(int x,int y,U32 radius,bw::Unit* excluded,U32 limit,bool enemy,int layer,bool bio){
 using namespace rework_combat_v5;std::vector<bw::Unit*> result;
 living_units([&](bw::Unit* u){if(u==excluded||!eligible(u)||(enemy?!is_enemy(u->player):u->player!=player_owner())||(layer>=0&&air(u)!=(layer!=0))||(bio&&!organic(u))||dist(x,y,u->flingy.position.x,u->flingy.position.y)>std::uint64_t(radius)*radius)return;result.push_back(u);});
 std::sort(result.begin(),result.end(),[&](bw::Unit* a,bw::Unit* b){const auto da=dist(x,y,a->flingy.position.x,a->flingy.position.y),db=dist(x,y,b->flingy.position.x,b->flingy.position.y);return da==db?a<b:da<db;});
 if(result.size()>limit)result.resize(limit);return result;
}
inline void qa30_nearest_prefix_matches_full_sort_with_live_mutations(){
 reset();for(U32 i=0;i<1000;++i){auto u=add(i%3?37u:43u,i%4?6u:1u,100+int(i%31)*16,100+int(i/31)*16);u->flags=1|(i%3?0u:4u);if(i%13==0)u->stasis_timer=1;if(i%17==0)u->flags|=0x4000000u;if(i%19==0)u->order=0;}
 refresh_units();
 for(U32 radius:{0u,32u,192u,1024u})for(U32 limit:{0u,1u,6u,32u,64u,2000u})for(int layer:{-1,0,1})for(bool enemy:{false,true})for(bool bio:{false,true}){
  const auto actual=rework_combat_v5::around(340,340,radius,&units[500],limit,enemy,layer,bio);
  CHECK(actual==qa30_reference_nearby(340,340,radius,&units[500],limit,enemy,layer,bio));
 }
 units[501].flingy.position={340,340};units[501].player=1;units[501].stasis_timer=0;units[501].flags=1;units[501].order=3;
 CHECK(rework_combat_v5::around(340,340,32,nullptr,1,false)==qa30_reference_nearby(340,340,32,nullptr,1,false,-1,false));
}
inline void qa30_query_views_refresh_and_restore_nested_owners(){
 qa13_fixture::begin();auto s=qa30_air_snapshot(1);CHECK(apply_snapshot(nullptr,s));auto own=add(70,1,100,100),enemy=add(70,6,100,100);
 const auto w=original_stat({0,17,70}),base=original_stat({1,5,w});
 CHECK(owner_range_hook(own,w,audit_weapon_range_return)==base+32);
 CHECK(owner_dat_query::values().size()<g.owner_edits.size());
 {OwnerDatScope outer(1,1,own);const auto hp=raw_value(0,8,70);CHECK(hp>original_stat({0,8,70}));CHECK(owner_range_hook(enemy,w,audit_weapon_range_return)==base);CHECK(raw_value(0,8,70)==hp&&raw_value(1,5,w)==base+32);}
 s.completed_phase=2;s.talent_bits[(238+10)/32]|=1u<<((238+10)%32);CHECK(apply_snapshot(nullptr,s));
 CHECK(owner_range_hook(own,w,audit_weapon_range_return)==owner_stat(1,{1,5,w}));CHECK(owner_range_hook(enemy,w,audit_weapon_range_return)==base);
 CHECK(raw_value(1,5,w)==base);qa13_fixture::end();
}
inline void qa30_pending_buffers_reuse_storage_and_drop_dead_targets(){
 using namespace rework_fixture;qa9_fixture::begin({});auto source=unit(0,1,100,100),target=unit(37,6,130,100);
 for(U32 i=0;i<800;++i)rework_combat_v5::queue(source,target,0,35,10000);
 pulse(100);pulse(101);const auto a=rework_combat_v5::pending_shots.capacity(),b=rework_combat_v5::pending_work.capacity();CHECK(a>=800&&b>=800);
 for(U32 frame=102;frame<106;++frame){pulse(frame);CHECK(rework_combat_v5::pending_shots.size()==800);CHECK(rework_combat_v5::pending_shots.capacity()==a&&rework_combat_v5::pending_work.capacity()==b);}
 kill(target);pulse(10100);CHECK(rework_combat_v5::pending_shots.empty()&&multi_fixture::shots.empty());qa9_fixture::end();
}
inline void qa30_larva_census_keeps_each_hatchery_and_owner_separate(){
 reset();CHECK(apply_snapshot(nullptr,economy_snapshot({21})));std::array<bw::Unit*,4> h{};
 for(auto& hatch:h){hatch=economy_add(131);hatch->flags=1;hatch->unit_specific.bytes[14]=37;}
 std::vector<bw::Unit*> larvae;
 for(U32 i=0;i<11;++i){auto u=economy_add(35);u->related=h[i<6?0:i<8?2:3];larvae.push_back(u);}
 auto enemy=economy_add(35,6);enemy->related=h[1];rework_economy_v5::step();
 for(U32 i=0;i<4;++i)CHECK(rework_economy_v5::larva_counts[std::size_t(h[i]-g.units)]==(i==0?6u:i==1?0u:i==2?2u:3u));
 CHECK(!rework_economy_v5::state(h[0])->larva_due&&h[0]->unit_specific.bytes[14]==37);
 CHECK(h[1]->unit_specific.bytes[14]==29&&h[2]->unit_specific.bytes[14]==29&&rework_economy_v5::state(h[3])->larva_due>game.frame_count);
 larvae[0]->player=6;larvae[6]->related=h[1];++game.frame_count;rework_economy_v5::step();
 CHECK(rework_economy_v5::larva_counts[std::size_t(h[0]-g.units)]==5&&rework_economy_v5::larva_counts[std::size_t(h[1]-g.units)]==1&&rework_economy_v5::larva_counts[std::size_t(h[2]-g.units)]==1);
}
inline void qa30_energy_ui_publishes_changes_and_skips_identical_values(){
 using namespace rework_binding_fixture;begin_energy();auto u=add(1,1,100,100);u->energy=200*256;rework_energy_ui::publish();
 auto& entry=rework_energy_ui::cache[std::size_t(u-g.units)];const auto first=entry.sequence.load();U32 energy=0,bonus=0;
 CHECK(rework_energy_ui::read(u,energy,bonus)&&energy==200*256);
 rework_energy_ui::publish();CHECK(entry.sequence.load()==first);
 --u->energy;rework_energy_ui::publish();CHECK(entry.sequence.load()==first+2&&rework_energy_ui::read(u,energy,bonus)&&energy==200*256-1);
 g.growth={};rework_energy_ui::publish();CHECK(!rework_energy_ui::read(u,energy,bonus));end_energy();
}
inline void qa30_impacted_homing_metadata_never_retargets_again(){
 using namespace rework_fixture;qa9_fixture::begin({133});auto source=unit(66,1,100,100),target=unit(43,6,130,100,true),other=unit(43,6,140,100,true);
 source->order=10;const auto w=original_stat({0,17,66});CHECK(original_stat({1,8,w})==1);auto b=bullet(source,target,w);rework_combat_v5::projectiles.at(b).impact=true;kill(target);
 pulse(101);CHECK(b->target.unit==target&&!rework_combat_v5::projectiles.at(b).retargeted);
 rework_combat_v5::projectiles.at(b).impact=false;pulse(102);CHECK(b->target.unit==other&&rework_combat_v5::projectiles.at(b).retargeted);qa9_fixture::end();
}
inline void qa30_unit_scan_scratch_is_reentrant_and_exception_safe(){
 reset();for(U32 i=0;i<20;++i)add(37,1,100,100);refresh_units();U32 outer=0,inner=0;
 living_units([&](bw::Unit*){++outer;living_units([&](bw::Unit*){++inner;});});CHECK(outer==20&&inner==400&&unit_scan_scratch::depth==0);
 CHECK(unit_scan_scratch::buffers.size()>=2);auto pointer=unit_scan_scratch::buffers[0].data();
 try{living_units([&](bw::Unit*){throw std::runtime_error("fixture");});}catch(const std::runtime_error&){}
 CHECK(unit_scan_scratch::depth==0);outer=0;living_units([&](bw::Unit*){++outer;});CHECK(outer==20&&pointer==unit_scan_scratch::buffers[0].data());
}
inline void run_qa30_performance_groups(){qa30_unit_scan_scratch_is_reentrant_and_exception_safe();qa30_nearest_prefix_matches_full_sort_with_live_mutations();qa30_query_views_refresh_and_restore_nested_owners();qa30_pending_buffers_reuse_storage_and_drop_dead_targets();qa30_larva_census_keeps_each_hatchery_and_owner_separate();qa30_energy_ui_publishes_changes_and_skips_identical_values();qa30_impacted_homing_metadata_never_retargets_again();}
}
