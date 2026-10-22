#pragma once
namespace host_test {
namespace rework_binding_fixture {
inline U32 moved=0;inline bool placement=true;inline int adjust=0;
inline rework_relocation::Pathing* path=nullptr;
inline rework_relocation::Pathing* __cdecl get_path(){return path;}
inline void __cdecl move(bw::Unit* u,U32 x,U32 y){++moved;u->flingy.position={std::int16_t(x),std::int16_t(y)};}
inline U32 __cdecl place(bw::Unit* u,const bw::Point* requested,bw::Point* out,const void* region,U32 a,U32 b){CHECK(!region && !a && !b);CHECK(u->flingy.position.x!=requested->x || u->flingy.position.y!=requested->y);*out=*requested;out->x=std::int16_t(out->x+adjust);return placement;}
inline U32 __cdecl base_energy(U8,std::uint16_t,void*){return 200u*256;}
inline void begin_energy(){
    reset();rework_combat_v5::bind([](const GrowthSnapshot& s,U32 ordinal) noexcept {return rework_catalog::rank(s,ordinal);});
    g.applied=true;g.growth={};g.growth.wire_version=2;const U32 bit=238+36;g.growth.talent_bits[bit/32]|=1u<<(bit%32);refresh_units();
}
inline void end_energy(){rework_energy_ui::reset();rework_combat_v5::rank_lookup=nullptr;combat_effects::damage_enter=nullptr;combat_effects::damage_leave=nullptr;movement_effects::ratio_extension=nullptr;}
}
inline void rework_relocation_native_transaction(){
    using namespace rework_binding_fixture;
    reset();g.applied=true;auto unit=add(0,1,100,100);unit->flingy.sprite=unit;refresh_units();
    auto saved_move=rework_relocation::native_move;auto saved_place=rework_relocation::native_place;auto saved_path=rework_relocation::pathing_source;
    rework_relocation::native_move=move;rework_relocation::native_place=place;rework_relocation::pathing_source=get_path;
    path=new rework_relocation::Pathing{};path->count=2;path->regions[0].group=1;path->regions[1].group=2;
    moved=0;placement=true;adjust=0;CHECK(rework_relocation::move(unit,130,100,16));CHECK(moved==1 && unit->flingy.position.x==130 && unit->order==1);
    unit->order=3;moved=0;placement=false;CHECK(!rework_relocation::move(unit,160,100,16));CHECK(moved==0 && unit->flingy.position.x==130 && unit->order==3);
    placement=true;adjust=17;moved=0;CHECK(!rework_relocation::move(unit,160,100,16));CHECK(moved==0 && unit->flingy.position.x==130);
    adjust=0;path->tiles[(100/32)*256+160/32]=1;moved=0;CHECK(!rework_relocation::move(unit,160,100,16));CHECK(moved==0);
    CHECK(rework_relocation::move(unit,160,100,16,false));CHECK(unit->flingy.position.x==160);
    // Native split-region minitiles and generation-independent ground groups.
    path->tiles[(100/32)*256+200/32]=0x2000;path->split[0]={0,0,1};CHECK(rework_relocation::connected({130,100},{200,100}));
    path->split[0].flags=0xffff;CHECK(!rework_relocation::connected({130,100},{200,100}));
    moved=0;CHECK(!rework_relocation::move(unit,-1,100,16));unit->flags|=0x40;CHECK(!rework_relocation::move(unit,200,100,16,false));CHECK(moved==0);
    delete path;path=nullptr;rework_relocation::native_move=saved_move;rework_relocation::native_place=saved_place;rework_relocation::pathing_source=saved_path;
}
inline void rework_energy_full_value_and_isolation(){
    using namespace rework_binding_fixture;begin_energy();auto own=add(1,1,100,100),enemy=add(1,6,100,100);refresh_units();
    own->energy=65535;enemy->energy=12800;auto state=rework_combat_v5::state(own);CHECK(state);state->energy_reserve=300*256-65535;rework_energy_ui::publish();
    U32 energy=0,bonus=0;CHECK(rework_energy_ui::read(own,energy,bonus));CHECK(energy==300*256 && bonus==100*256);CHECK(rework_energy_ui::current(own)==300);
    rework_energy_ui::original_maximum=base_energy;CHECK(rework_energy_ui::maximum(1,1,&game,own)==300*256);CHECK(rework_energy_ui::maximum(6,1,&game,enemy)==200*256);CHECK(rework_energy_ui::current(enemy)==50);
    CHECK(rework_energy_ui::maximum(6,1,&game,own)==200*256);CHECK(rework_energy_ui::maximum(1,9,&game,own)==200*256);
    const auto id=own->minor_unique_index;++own->minor_unique_index;CHECK(!rework_energy_ui::read(own,energy,bonus));own->minor_unique_index=id;
    rework_energy_ui::cache[0].sequence.fetch_add(1);CHECK(!rework_energy_ui::read(own,energy,bonus));rework_energy_ui::cache[0].sequence.fetch_add(1);
    end_energy();CHECK(rework_energy_ui::current(own)==255);rework_energy_ui::original_maximum=nullptr;
}
inline void rework_energy_actual_x64_status_bridge(){
    using namespace rework_binding_fixture;using namespace rework_energy_ui;
    begin_energy();auto own=add(1,1,100,100);refresh_units();own->energy=65535;rework_combat_v5::state(own)->energy_reserve=300*256-65535;rework_energy_ui::publish();
    CHECK(!ready && !relays);auto base=static_cast<U8*>(VirtualAlloc(nullptr,0x2bf000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));CHECK(base);
    std::memcpy(base+sites[0],maximum_call,5);std::memcpy(base+sites[1],current_read,8);
    const U8 maximum_stub[]={0xb8,0x00,0xc8,0x00,0x00,0xc3};std::memcpy(base+0x1cdf67,maximum_stub,sizeof(maximum_stub));
    // An actual x64 caller recreates SAMASE's saved Unit* stack slot. The
    // installed call's relay must pass this fourth argument without truncation.
    const U8 prefix[]={0x48,0x83,0xec,0x48,0x48,0x89,0x4c,0x24,0x38,0x48,0x89,0xc8,0x0f,0xb7,0x90,0x8c,0,0,0,0x0f,0xb6,0x48,0x68,0x45,0x31,0xc0,0x48,0xb8};
    auto bridge=base+0x1000;std::memcpy(bridge,prefix,sizeof(prefix));CHECK(install_at(base));CHECK(verify_installation());
    std::int32_t delta=0;std::memcpy(&delta,base+sites[0]+1,4);const auto target=reinterpret_cast<std::uintptr_t>(base+sites[0]+5+delta);std::memcpy(bridge+sizeof(prefix),&target,8);
    const U8 suffix[]={0xff,0xd0,0x48,0x83,0xc4,0x48,0xc3};std::memcpy(bridge+sizeof(prefix)+8,suffix,sizeof(suffix));
    // Execute the real patched eight-byte current-energy site, including EDX
    // assignment, inside a synthetic caller that saves the nonvolatile R15.
    auto current_bridge=base+sites[1]-16;std::memset(current_bridge,0x90,16);
    const U8 current_prefix[]={0x41,0x57,0x48,0x83,0xec,0x20,0x49,0x89,0xcf};std::memcpy(current_bridge,current_prefix,sizeof(current_prefix));
    const U8 current_suffix[]={0x89,0xd0,0x48,0x83,0xc4,0x20,0x41,0x5f,0xc3};std::memcpy(base+sites[1]+8,current_suffix,sizeof(current_suffix));
    CHECK(FlushInstructionCache(GetCurrentProcess(),base,0x2bf000));using Invoke=U32 (__cdecl*)(bw::Unit*);
    CHECK(reinterpret_cast<Invoke>(bridge)(own)==300*256);CHECK(reinterpret_cast<Invoke>(current_bridge)(own)==300);
    ++own->minor_unique_index;CHECK(reinterpret_cast<Invoke>(bridge)(own)==200*256);CHECK(reinterpret_cast<Invoke>(current_bridge)(own)==255);
    ready=false;module=nullptr;auto release=relays;relays=nullptr;original_maximum=nullptr;VirtualFree(release,0,MEM_RELEASE);VirtualFree(base,0,MEM_RELEASE);end_energy();
}
inline void rework_energy_unknown_image_rejected(){
    using namespace rework_energy_ui;auto base=static_cast<U8*>(VirtualAlloc(nullptr,0x2bf000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(base);
    CHECK(!install_at(base));CHECK(!ready && !relays);std::memcpy(base+sites[0],maximum_call,5);CHECK(!install_at(base));CHECK(native_engine_hooks::match(base+sites[0],maximum_call,5));VirtualFree(base,0,MEM_RELEASE);
}
inline constexpr std::size_t rework_binding_group_count=4;
inline void run_rework_binding_groups(){rework_relocation_native_transaction();rework_energy_full_value_and_isolation();rework_energy_actual_x64_status_bridge();rework_energy_unknown_image_rejected();}
}
