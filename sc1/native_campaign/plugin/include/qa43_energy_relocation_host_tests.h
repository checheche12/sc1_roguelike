#pragma once
namespace host_test {
inline constexpr std::size_t qa43_group_count=2;
namespace qa43_fixture {
struct EnergyImage {
 U8* memory=nullptr;U8* previous_image=native_tech_cost_view::image;
 std::uint16_t* previous=native_tech_cost_view::yamato;
 static constexpr U32 relocated=0x146ded0; // Captured QA42 SAMASE operand.
 EnergyImage(){
  memory=static_cast<U8*>(VirtualAlloc(nullptr,0x1500000,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));CHECK(memory);
  *cell(native_tech_cost_view::energy_array)=150;*cell(relocated)=150;
  references(native_tech_cost_view::energy_array);CHECK(native_tech_cost_view::bind(memory));
 }
 ~EnergyImage(){native_tech_cost_view::yamato=previous;native_tech_cost_view::image=previous_image;VirtualFree(memory,0,MEM_RELEASE);}
 std::uint16_t* cell(U32 rva){return reinterpret_cast<std::uint16_t*>(memory+rva+16);}
 void references(U32 rva){for(U32 i=0;i<3;i++){auto p=memory+native_tech_cost_view::sites[i];std::memcpy(p,native_tech_cost_view::prefixes[i],5);std::memcpy(p+5,&rva,4);}}
 void relocate(){references(relocated);*cell(native_tech_cost_view::energy_array)=0;}
};
}
inline void qa43_relocated_energy_accepts_snapshot_and_scopes_native_deduction(){
 using namespace qa12_fixture;begin(64,false);qa43_fixture::EnergyImage image;
 CHECK(native_tech_cost_view::verify_after_dat());image.relocate();g.applied=false;
 CHECK(apply_snapshot(nullptr,talent(64)));CHECK(native_tech_cost_view::yamato==image.cell(image.relocated));
 auto own=produce(12),enemy=produce(12,6);complete(own,50);complete(enemy,150);
 owner_unit_hook(own,qa38_fixture::native_cost);CHECK(qa38_fixture::paid&&own->energy==0);
 owner_unit_hook(enemy,qa38_fixture::native_cost);CHECK(qa38_fixture::paid&&enemy->energy==0);
 CHECK(*image.cell(image.relocated)==150&&*image.cell(native_tech_cost_view::energy_array)==0);
 {OwnerDatScope own_scope(1,1,own);CHECK(*image.cell(image.relocated)==50);{OwnerDatScope enemy_scope(6,6,enemy);CHECK(*image.cell(image.relocated)==150);}CHECK(*image.cell(image.relocated)==50);}
 CHECK(*image.cell(image.relocated)==150);end();
}
inline void qa43_relocation_requires_all_instruction_witnesses_and_original_cost(){
 qa43_fixture::EnergyImage image;image.relocate();CHECK(native_tech_cost_view::verify_after_dat());
 auto instruction=image.memory+native_tech_cost_view::sites[1];instruction[0]^=1;
 CHECK(!native_tech_cost_view::verify_after_dat());CHECK(std::strcmp(native_tech_cost_view::last_error,"energy_instruction_changed")==0);
 image.references(image.relocated);const U32 wrong=native_tech_cost_view::energy_array;std::memcpy(instruction+5,&wrong,4);
 CHECK(!native_tech_cost_view::verify_after_dat());CHECK(std::strcmp(native_tech_cost_view::last_error,"energy_references_disagree")==0);
 image.references(image.relocated);*image.cell(image.relocated)=0;
 CHECK(!native_tech_cost_view::verify_after_dat());CHECK(std::strcmp(native_tech_cost_view::last_error,"energy_baseline_changed")==0);
 *image.cell(image.relocated)=150;CHECK(native_tech_cost_view::verify_after_dat());
}
inline void run_qa43_groups(){qa43_relocated_energy_accepts_snapshot_and_scopes_native_deduction();qa43_relocation_requires_all_instruction_witnesses_and_original_cost();}
}
