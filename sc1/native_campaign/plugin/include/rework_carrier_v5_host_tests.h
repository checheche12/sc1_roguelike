#pragma once
namespace host_test {
namespace rework_carrier_tests {
using rework_cargo_tests::fresh;
inline bw::Unit* command_carrier=nullptr;
inline std::array<U32,1900> deaths{},gives{};
inline void set_pointer(U8* bytes,std::size_t offset,bw::Unit* p){std::memcpy(bytes+offset,&p,sizeof(p));}
inline bw::Unit* pointer(const U8* bytes,std::size_t offset){return rework_carrier_v5::pointer(bytes,offset);}
inline void talent(U32 ord){rework_cargo_tests::talent(ord);}
inline void begin(){rework_cargo_tests::begin();rework_carrier_v5::reset();command_carrier=nullptr;deaths={};gives={};}
inline void link(bw::Unit* c,bw::Unit* child,bool outside){
 const auto offset=outside?8u:0u;auto old=pointer(c->unit_specific.bytes,offset);set_pointer(child->unit_specific.bytes,0,c);set_pointer(child->unit_specific.bytes,8,old);set_pointer(child->unit_specific.bytes,16,nullptr);child->unit_specific.bytes[24]=outside?1:0;
 if(old)set_pointer(old->unit_specific.bytes,16,child);set_pointer(c->unit_specific.bytes,offset,child);++c->unit_specific.bytes[outside?17:16];
}
inline void unlink(bw::Unit* child){
 auto c=pointer(child->unit_specific.bytes,0),next=pointer(child->unit_specific.bytes,8),prev=pointer(child->unit_specific.bytes,16);const bool outside=child->unit_specific.bytes[24]!=0;
 if(prev)set_pointer(prev->unit_specific.bytes,8,next);else set_pointer(c->unit_specific.bytes,outside?8u:0u,next);if(next)set_pointer(next->unit_specific.bytes,16,prev);--c->unit_specific.bytes[outside?17:16];set_pointer(child->unit_specific.bytes,8,nullptr);set_pointer(child->unit_specific.bytes,16,nullptr);
}
inline bw::Unit* carrier(U32 inside=0,U32 outside=0,U32 owner=1){auto c=fresh(72,owner);for(auto& q:c->build_queue)q=228;for(U32 i=0;i<inside+outside;i++){auto p=fresh(73,owner);p->ground_cooldown=13;link(c,p,i>=inside);}return c;}
inline void __cdecl train_command(const void* data,U32 length,U32){
 if(!data || length!=1 || *static_cast<const U8*>(data)!=0x27 || !command_carrier)return;auto c=command_carrier;
 U32 queued=0,empty=5;for(U32 i=0;i<5;i++)if(c->build_queue[i]==73)++queued;else if(c->build_queue[i]==228 && empty==5)empty=i;
 const auto native_upgrade=g.extended ? g.extended[0].pointer[43*12+c->player]:game.upgrade_level_sc[c->player][43];const U32 native_limit=native_upgrade?8u:4u;
 if(U32(c->unit_specific.bytes[16])+c->unit_specific.bytes[17]+queued>=native_limit || empty==5)return;
 const auto cost=original_stat({0,40,73});if(game.minerals[c->player]<cost)return;game.minerals[c->player]-=cost;c->build_queue[empty]=73;c->secondary_order=63;
}
inline void command(bw::Unit* c){command_carrier=c;const U8 data=0x27;saved_handle=player_owner();owner_commands_hook(&data,1,0,train_command);}
inline void __cdecl stock_training_step(bw::Unit* c){
 const auto slot=std::min(4u,U32(c->current_build_slot));if(c->build_queue[slot]!=73)return;
 const auto native_upgrade=g.extended ? g.extended[0].pointer[43*12+c->player]:game.upgrade_level_sc[c->player][43];const U32 native_limit=native_upgrade?8u:4u;
 if(U32(c->unit_specific.bytes[16])+c->unit_specific.bytes[17]>=native_limit)return;
 auto child=c->secondary_order_target.unit;
 if(!child){child=fresh(73,c->player);child->flags&=~1u;child->remaining_build_time=static_cast<std::uint16_t>(original_stat({0,42,73}));c->secondary_order_target.unit=child;return;}
 if(child->remaining_build_time)--child->remaining_build_time;
 if(!child->remaining_build_time){child->flags|=1u;link(c,child,false);c->secondary_order_target.unit=nullptr;c->build_queue[slot]=228;c->current_build_slot=static_cast<U8>((slot+1)%5);}
}
inline void __cdecl stock_launch(bw::Unit* c){if(c->order_timer)return;auto child=pointer(c->unit_specific.bytes,0);if(!child)return;unlink(child);link(c,child,true);c->order_timer=7;}
inline void __cdecl stock_give(bw::Unit* u,U32 owner){
 ++gives[static_cast<std::size_t>(u-units.data())];if(u->unit_id==72){std::vector<bw::Unit*> children;for(U32 offset:{0u,8u})for(auto p=pointer(u->unit_specific.bytes,offset);p;p=pointer(p->unit_specific.bytes,8))children.push_back(p);for(auto p:children)owner_give_hook(p,owner,stock_give);}u->player=static_cast<U8>(owner);
}
inline void __cdecl stock_kill(bw::Unit* u){
 ++deaths[static_cast<std::size_t>(u-units.data())];if(u->unit_id==72){for(U32 offset:{0u,8u})while(auto p=pointer(u->unit_specific.bytes,offset)){unlink(p);owner_kill_hook(p,stock_kill);}}u->flingy.hitpoints=0;u->order=0;u->order_state=1;
}
inline void stock_queue_cost_time_birth_and_native_cap(){
 begin();talent(130);game.upgrade_level_sc[1][43]=1;game.minerals[1]=1000;auto c=carrier(4);CHECK(rework_carrier_v5::capacity(c)==8);const auto cost=original_stat({0,40,73}),time=original_stat({0,42,73});CHECK(cost>0 && time>0);
 for(U32 i=0;i<5;i++)command(c);U32 queued=0;for(auto q:c->build_queue)if(q==73)++queued;CHECK(queued==4 && game.minerals[1]==1000-4*cost);CHECK(c->unit_specific.bytes[16]==4 && game.upgrade_level_sc[1][43]==1);
 owner_secondary_hook(c,stock_training_step);auto pending=c->secondary_order_target.unit;CHECK(pending && pending->remaining_build_time==time && !(pending->flags&1u));CHECK(c->unit_specific.bytes[16]==4);
 for(U32 i=0;i<time;i++)owner_secondary_hook(c,stock_training_step);CHECK(c->unit_specific.bytes[16]==5 && !c->secondary_order_target.unit);
 for(U32 i=0;i<3*(time+1);i++)owner_secondary_hook(c,stock_training_step);const auto actual=rework_carrier_v5::census(c);CHECK(actual.valid && actual.inside==8 && actual.outside==0);
 command(c);CHECK(game.minerals[1]==1000-4*cost);for(auto q:c->build_queue)CHECK(q==228);
 // The replacement talent never changes native4/8 capacity or research.
 begin();talent(130);game.minerals[1]=1000;c=carrier(4);CHECK(rework_carrier_v5::capacity(c)==4);for(U32 i=0;i<5;i++)command(c);for(auto q:c->build_queue)CHECK(q==228);CHECK(game.minerals[1]==1000 && game.upgrade_level_sc[1][43]==0);
}
inline void launch_fractional_progress_and_negative_owners(){
 begin();talent(136);auto c=carrier(12);U32 total=0;
 for(U32 i=0;i<3;i++){game.frame_count=i+1;c->order_timer=0;owner_order_hook(c,stock_launch);total+=c->order_timer;CHECK(c->order_timer==(i==0?4:5));}
 CHECK(total==14 && c->unit_specific.bytes[17]==3);for(std::size_t i=1;i<count;i++)CHECK(units[i].ground_cooldown==13);
 auto enemy=carrier(1,0,6);game.frame_count=10;owner_order_hook(enemy,stock_launch);CHECK(enemy->order_timer==7);
 auto ordinary=carrier(1);g.growth.talent_bits[(238+136)/32]&=~(1u<<((238+136)%32));owner_order_hook(ordinary,stock_launch);CHECK(ordinary->order_timer==7);
}
inline void ammo_survives_talent_loss_give_death_and_bad_lists(){
 begin();talent(130);game.upgrade_level_sc[1][43]=1;auto c=carrier(8,4);const auto n=count;g.growth.talent_bits[(238+130)/32]&=~(1u<<((238+130)%32));CHECK(rework_carrier_v5::capacity(c)==8 && rework_carrier_v5::census(c).inside==8 && rework_carrier_v5::census(c).outside==4);
 owner_give_hook(c,2,stock_give);CHECK(rework_carrier_v5::census(c).valid && rework_carrier_v5::census(c).inside+rework_carrier_v5::census(c).outside==12);for(std::size_t i=0;i<n;i++)CHECK(units[i].player==2 && gives[i]==1);
 owner_kill_hook(c,stock_kill);for(std::size_t i=0;i<n;i++)CHECK(deaths[i]==1);
 begin();talent(130);game.upgrade_level_sc[1][43]=1;c=carrier(8);auto head=pointer(c->unit_specific.bytes,0);set_pointer(head->unit_specific.bytes,8,head);CHECK(!rework_carrier_v5::census(c).valid);const auto before=c->unit_specific;{rework_carrier_v5::BurstScope scope(c);CHECK(!scope.active);}CHECK(std::memcmp(&c->unit_specific,&before,sizeof(before))==0);
}
inline void native_extended_upgrade_precedence_without_capacity_mutation(){
 begin();talent(130);std::array<U8,61*12> levels{};samase::ExtendedArray array{levels.data(),levels.data()+levels.size(),0,0};g.extended=&array;g.extended_count=1;levels[43*12+1]=1;game.upgrade_level_sc[1][43]=0;game.minerals[1]=1000;auto c=carrier(4);
 CHECK(rework_carrier_v5::capacity(c)==8);const auto cost=original_stat({0,40,73}),time=original_stat({0,42,73});for(U32 i=0;i<5;i++)command(c);CHECK(game.minerals[1]==1000-4*cost && levels[43*12+1]==1 && game.upgrade_level_sc[1][43]==0);
 for(U32 i=0;i<4*(time+1);i++)owner_secondary_hook(c,stock_training_step);CHECK(rework_carrier_v5::census(c).inside==8 && levels[43*12+1]==1 && game.upgrade_level_sc[1][43]==0);command(c);CHECK(game.minerals[1]==1000-4*cost);
 levels[43*12+1]=0;game.upgrade_level_sc[1][43]=1;c=carrier(4);CHECK(rework_carrier_v5::capacity(c)==4);command(c);CHECK(game.minerals[1]==1000-4*cost && levels[43*12+1]==0 && game.upgrade_level_sc[1][43]==1);
 array.end=array.pointer+43*12+1;CHECK(rework_carrier_v5::original_capacity(c)==4);g.extended=nullptr;g.extended_count=0;
}
}
inline constexpr std::size_t rework_carrier_group_count=4;
inline void run_rework_carrier_groups(){rework_carrier_tests::stock_queue_cost_time_birth_and_native_cap();rework_carrier_tests::launch_fractional_progress_and_negative_owners();rework_carrier_tests::ammo_survives_talent_loss_give_death_and_bad_lists();rework_carrier_tests::native_extended_upgrade_precedence_without_capacity_mutation();}
}
