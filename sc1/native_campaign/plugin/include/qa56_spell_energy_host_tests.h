#pragma once
namespace host_test {
inline constexpr std::size_t qa56_group_count=5;
namespace qa56_fixture {
inline bool cast=false;inline U32 casts=0,validation_order=0;inline bw::Unit* commanded=nullptr;
inline void __cdecl pay(bw::Unit* u){const U32 tech=rework_combat_v5::spell_tech(u->order),cost=raw_value(4,3,tech)*256;cast=u->energy>=cost;if(cast){u->energy=std::uint16_t(u->energy-cost);u->order=3;++casts;}}
inline void __cdecl cancel(bw::Unit*){cast=false;}
inline U32 __cdecl validate(bw::Unit* u,U32 order,bw::Unit*,U32,U32,std::uint16_t*){return u->energy>=owner_stat(u->player,{4,3,rework_combat_v5::spell_tech(order)})*256;}
inline void __cdecl command(const U8*,U32){CHECK(commanded);if(validate(commanded,validation_order,nullptr,0,0,nullptr))commanded->order=U8(validation_order);}
struct Case {U32 ordinal,unit,order,cost;};
inline constexpr Case cases[]={{38,1,115,100},{38,9,143,75},{38,34,180,50},{78,45,121,150},{78,46,144,150},{78,45,146,75},{120,67,142,75},{120,63,182,150},{120,60,181,125},{120,71,147,100},{126,71,137,150}};
inline bw::Unit* begin(Case c){qa9_fixture::begin({c.ordinal});auto u=rework_fixture::unit(c.unit,1,100,100);u->order=U8(c.order);write_entry(&dat[4][3],rework_combat_v5::spell_tech(c.order),c.cost);casts=0;return u;}
inline U32 net(bw::Unit* u,Case c){return c.cost*256-rework_combat_v5::cast_energy_refund(u,c.order,c.cost*256);}
}
inline void qa56_exact_discount_energy_spends_once_and_one_q8_less_fails(){
 using namespace qa56_fixture;
 for(auto c:cases){auto u=begin(c);const U32 cost=net(u,c);u->energy=std::uint16_t(cost);
  owner_order_hook(u,pay);CHECK(cast&&casts==1&&u->energy==0);
  if(cost){u->order=U8(c.order);u->energy=std::uint16_t(cost-1);owner_order_hook(u,pay);CHECK(!cast&&casts==1&&u->energy==cost-1);}
  u->order=U8(c.order);u->energy=std::uint16_t(cost+10*256);owner_order_hook(u,pay);CHECK(cast&&u->energy==10*256);
  std::printf("QA56_ENERGY unit=%u order=%u original_q8=%u required_q8=%u boundary=ok\n",c.unit,c.order,c.cost*256,cost);qa9_fixture::end();
 }
}
inline void qa56_cancel_validation_and_nested_owners_leave_no_energy(){
 using namespace qa56_fixture;Case c{120,67,142,75};auto u=begin(c);const U32 cost=net(u,c);u->energy=std::uint16_t(cost);
 owner_order_hook(u,cancel);CHECK(!cast&&u->energy==cost);
 std::uint16_t error=0;CHECK(rework_combat_v5::order_target_hook(u,c.order,u,0,0,&error,validate));CHECK(u->energy==cost);
 {rework_combat_v5::SpellEnergyRequirementScope outer(u,c.order);CHECK(u->energy==75*256);{rework_combat_v5::SpellEnergyRequirementScope inner(u,c.order);CHECK(!inner.advance.amount);}CHECK(u->energy==75*256);}CHECK(u->energy==cost);
 u->player=6;owner_order_hook(u,pay);CHECK(!cast&&u->energy==cost);u->player=1;u->flags|=0x40000000u;owner_order_hook(u,pay);CHECK(!cast&&u->energy==cost);u->flags&=~0x40000000u;
 {rework_combat_v5::SpellEnergyRequirementScope scope(u,c.order);u->player=6;}CHECK(u->energy==cost);
 u->player=1;{rework_combat_v5::SpellEnergyRequirementScope scope(u,c.order);++u->minor_unique_index;u->energy=17;}CHECK(u->energy==17);qa9_fixture::end();
}
inline void qa56_targeted_packet_validation_and_actual_cast_share_cost(){
 using namespace qa56_fixture;Case c{120,67,142,75};auto u=begin(c);const U32 cost=net(u,c);u->energy=std::uint16_t(cost);u->order=3;
 auto other=rework_fixture::unit(67,1,120,100);other->energy=std::uint16_t(cost+256);auto enemy=rework_fixture::unit(67,6,140,100);enemy->energy=12*256;
 U8 packet[11]{};packet[0]=0x15;packet[9]=U8(c.order);commanded=u;validation_order=c.order;
 rework_combat_v5::motion_command(packet,11,1,0,command);CHECK(u->order==c.order&&u->energy==cost&&other->energy==cost+256&&enemy->energy==12*256);
 owner_order_hook(u,pay);CHECK(cast&&u->energy==0);
 u->energy=std::uint16_t(cost);u->order=3;rework_combat_v5::motion_command(packet,10,1,0,command);CHECK(u->order==3&&u->energy==cost);
 packet[0]=0x14;rework_combat_v5::motion_command(packet,11,1,0,command);CHECK(u->order==3&&u->energy==cost);qa9_fixture::end();
}
inline void qa56_recall_zero_cost_stacking_and_reserves_are_not_minted(){
 using namespace qa56_fixture;Case c{120,71,137,150};auto u=begin(c);rework_fixture::ranks[126]=1;u->energy=0;
 auto s=rework_combat_v5::state(u);const U32 reserve=s->energy_reserve;owner_order_hook(u,pay);CHECK(cast&&u->energy==0&&s->energy_reserve==reserve);
 u->order=137;owner_order_hook(u,cancel);CHECK(u->energy==0&&s->energy_reserve==reserve);qa9_fixture::end();
}
inline void qa56_pinned_client_precheck_real_call_relay_and_cheat_policy(){
 using namespace qa56_fixture;namespace check=spell_energy_check;
 auto memory=static_cast<U8*>(VirtualAlloc(nullptr,0x1100000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(memory);
 CHECK(!check::register_at(memory,qa12_extra::write));
 std::memcpy(memory+check::checker,check::original_checker,sizeof(check::original_checker));
 const U8 prologue[]={0x48,0x83,0xec,0x28},epilogue[]={0x48,0x83,0xc4,0x28,0xc3};
 for(U32 i=0;i<4;i++){std::memcpy(memory+check::sites[i],check::calls[i],5);std::memcpy(memory+check::sites[i]-4,prologue,4);std::memcpy(memory+check::sites[i]+5,epilogue,5);}
 CHECK(check::register_at(memory,qa12_extra::write)&&check::verify_installation());auto native=reinterpret_cast<check::Requirement>(memory+check::site-4);
 for(auto c:cases){auto u=begin(c);check::publish();const U32 cost=net(u,c);u->energy=std::uint16_t(cost);
  for(U32 site:check::sites){auto client=reinterpret_cast<check::Requirement>(memory+site-4);u->energy=std::uint16_t(cost);
   CHECK(check::required(u,c.cost*256)==cost&&client(u,c.cost*256)==0);
   if(cost){u->energy=std::uint16_t(cost-1);CHECK(client(u,c.cost*256)==1);}
   u->player=6;u->energy=0;CHECK(check::required(u,c.cost*256)==c.cost*256&&client(u,c.cost*256)==1);u->player=1;
  }qa9_fixture::end();
 }
 auto u=begin({38,1,115,100});check::publish();u->energy=0;auto cheat=reinterpret_cast<U32*>(memory+0x1053e30);*cheat=0x800;CHECK(native(u,100*256)==0);*cheat=0;CHECK(native(u,100*256)==1);
 // Recreate QA58's three unpatched client calls: the native checker rejects
 // the correctly discounted40 energy before any order can be submitted.
 u->energy=40*256;
 for(U32 i=0;i<3;i++){auto client=reinterpret_cast<check::Requirement>(memory+check::sites[i]-4);
  std::memcpy(memory+check::sites[i],check::calls[i],5);CHECK(client(u,100*256)==1);
  std::memcpy(memory+check::sites[i],check::branches[i],5);CHECK(client(u,100*256)==0);
 }
 for(U32 site:check::sites){memory[site]^=1;CHECK(!check::verify_installation());memory[site]^=1;CHECK(check::verify_installation());}
 CHECK(VirtualFree(check::code,0,MEM_RELEASE));check::code=check::module=nullptr;check::queued=false;check::original_requirement=nullptr;check::reset();CHECK(VirtualFree(memory,0,MEM_RELEASE));qa9_fixture::end();
}
inline void run_qa56_groups(){qa56_exact_discount_energy_spends_once_and_one_q8_less_fails();qa56_cancel_validation_and_nested_owners_leave_no_energy();qa56_targeted_packet_validation_and_actual_cast_share_cost();qa56_recall_zero_cost_stacking_and_reserves_are_not_minted();qa56_pinned_client_precheck_real_call_relay_and_cheat_policy();}
}
