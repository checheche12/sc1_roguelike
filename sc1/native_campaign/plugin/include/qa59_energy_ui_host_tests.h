#pragma once
namespace host_test {
inline constexpr std::size_t qa59_group_count=3;
inline void qa59_discounted_tooltip_native_store_and_actual_cost(){
 using namespace qa56_fixture;namespace ui=yamato_cost_ui;
 auto memory=static_cast<U8*>(VirtualAlloc(nullptr,0x1450000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(memory);
 std::memcpy(memory+ui::site,ui::original,8);CHECK(ui::register_at(memory,qa12_extra::write)&&ui::verify_installation());
 std::vector<U8> body={0x53,0x48,0x83,0xec,0x20,0x89,0xcb,0x41,0x89,0xd1,0x48,0xb8};economy_ui_fixture::append64(body,reinterpret_cast<std::uintptr_t>(ui::code));
 for(int byte:{0xff,0xd0,0x48,0x83,0xc4,0x20,0x5b,0xc3})body.push_back(U8(byte));
 auto helper=economy_ui_fixture::executable(body);
 for(auto c:cases){auto u=begin(c);ui::publish();const U32 cost=net(u,c),tech=rework_combat_v5::spell_tech(c.order);
  auto selected=u;std::memcpy(memory+0x10a4458,&selected,sizeof(selected));reinterpret_cast<void (__cdecl*)(U32,U32)>(helper)(tech,c.cost);
  std::uint16_t display=0;std::memcpy(&display,memory+ui::output,2);CHECK(display==(cost+255)/256);
  CHECK(spell_energy_check::required(u,c.cost*256)==cost);u->energy=std::uint16_t(cost);owner_order_hook(u,pay);CHECK(cast&&u->energy==0);
  u->player=6;CHECK(ui::value(u,tech,c.cost)==c.cost);u->player=1;u->flags|=0x40000000u;CHECK(ui::value(u,tech,c.cost)==c.cost);
  std::printf("QA59_TOOLTIP unit=%u tech=%u original=%u required_q8=%u displayed=%u actual_spend_q8=%u\n",c.unit,tech,c.cost,cost,display,cost);qa9_fixture::end();
 }
 CHECK(VirtualFree(helper,0,MEM_RELEASE));CHECK(RtlDeleteFunctionTable(&ui::unwind));CHECK(VirtualFree(ui::code,0,MEM_RELEASE));CHECK(VirtualFree(memory,0,MEM_RELEASE));ui::code=ui::module=nullptr;ui::queued=false;ui::reset();
}
inline void qa59_yamato_and_recall_combined_discounts_match_precheck(){
 using namespace rework_fixture;namespace ui=yamato_cost_ui;
 qa12_fixture::begin(64,false);g.applied=false;auto snapshot=qa12_fixture::talent(64);snapshot.talent_bits[276/32]|=1u<<(276%32);
 CHECK(apply_snapshot(nullptr,snapshot));auto u=qa12_fixture::produce(12);u->order=113;ui::publish();
 // Terran caster efficiency covers Ghost/Medic/Vessel, not Battlecruisers.
 CHECK(owner_stat(1,{4,3,8})==50);CHECK(spell_energy_check::required(u,150*256)==50*256);CHECK(ui::value(u,8,150)==50);
 u->energy=50*256;qa56_fixture::casts=0;owner_order_hook(u,qa56_fixture::pay);CHECK(qa56_fixture::cast&&u->energy==0&&qa56_fixture::casts==1);
 CHECK(ui::value(u,7,100)==100);qa9_fixture::end();
 qa9_fixture::begin({120,126});u=unit(71,1,100,100);write_entry(&dat[4][3],21,150);u->order=137;ui::publish();
 CHECK(spell_energy_check::required(u,150*256)==0&&ui::value(u,21,150)==0);u->energy=0;owner_order_hook(u,qa56_fixture::pay);CHECK(qa56_fixture::cast&&u->energy==0);qa9_fixture::end();
}
inline void qa59_cost_snapshot_reset_and_original_units(){
 using namespace qa56_fixture;namespace ui=yamato_cost_ui;
 auto u=begin({38,1,115,100});ui::publish();CHECK(ui::value(u,1,100)==40);
 u->player=6;CHECK(ui::value(u,1,100)==100);u->player=1;
 g.active=false;ui::publish();CHECK(ui::value(u,1,100)==100&&spell_energy_check::required(u,100*256)==100*256);qa9_fixture::end();
 qa9_fixture::begin({});u=rework_fixture::unit(1,1,100,100);ui::publish();CHECK(ui::value(u,1,100)==100);qa9_fixture::end();
}
inline void run_qa59_groups(){qa59_discounted_tooltip_native_store_and_actual_cost();qa59_yamato_and_recall_combined_discounts_match_precheck();qa59_cost_snapshot_reset_and_original_units();}
}
