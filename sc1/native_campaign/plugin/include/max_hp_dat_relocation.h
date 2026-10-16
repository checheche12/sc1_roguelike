#pragma once
// SAMASE expands DAT arrays before plugin entry. Only the ten explicitly
// identified address operands may differ from the pinned stock functions.
// Each changed operand must resolve to the matching public API array.
inline Entry runtime_entries[5];
inline U8 runtime_bodies[5][128]{};
inline native_engine_hooks::Bytes runtime_witnesses[5][2]{};
inline U8 runtime_add_body[sizeof(add_original_bytes)]{};
inline native_engine_hooks::Bytes runtime_add_witnesses[2]{};
inline native_engine_hooks::Spec runtime_add_spec{};
inline GetDat image_dat_getter=nullptr;

inline const void* damage_overlay_array() noexcept {
    if(!image_dat_getter)return nullptr;
    std::size_t count=0;const auto tables=image_dat_getter(&count);
    // Loaded images.dat field 10 contains native LO pointers, not file indices.
    if(!tables || count<=10 || tables[10].entry_size!=sizeof(void*) || tables[10].entries<999)return nullptr;
    return tables[10].data;
}

inline const void* units_field(U32 field,U32 width) noexcept {
    if(!g.dat_getters[0])return nullptr;
    std::size_t count=0;const auto tables=g.dat_getters[0](&count);
    if(!tables || field>=count || tables[field].entry_size!=width || tables[field].entries<228)return nullptr;
    return tables[field].data;
}
inline bool relocate_dat_operand(U8* base,U32 rva,U8* expected,std::size_t offset,
                                 std::size_t origin,const void* public_array) noexcept {
    std::int32_t stock=0,actual=0;
    std::memcpy(&stock,expected+offset,4);
    if(!native_engine_hooks::read_exact(base+rva+offset,&actual,4))
        return native_engine_hooks::install_failed("hp_dat_operand_unreadable");
    const auto target=reinterpret_cast<std::intptr_t>(base)+static_cast<std::intptr_t>(origin)+actual;
    if(!public_array || target!=reinterpret_cast<std::intptr_t>(public_array)){
        log_event("Maximum-health DAT relocation rejected: rva=%x offset=%zu target=%p api_array=%p",rva,offset,reinterpret_cast<void*>(target),public_array);
        return native_engine_hooks::install_failed("hp_dat_operand_target_mismatch");
    }
    if(actual!=stock)std::memcpy(expected+offset,&actual,4);return true;
}
inline bool prepare_runtime_specs(U8* base) noexcept {
    const U8* bodies[]={original_0_bytes,original_1_bytes,original_2_bytes,original_3_bytes,original_4_bytes};
    const std::size_t sizes[]={sizeof(original_0_bytes),sizeof(original_1_bytes),sizeof(original_2_bytes),sizeof(original_3_bytes),sizeof(original_4_bytes)};
    const void* hp=units_field(8,4);
    for(std::size_t i=0;i<5;i++){
        runtime_entries[i]=entries[i];std::memcpy(runtime_bodies[i],bodies[i],sizes[i]);
        if(i<4 && !relocate_dat_operand(base,entries[i].spec.rva,runtime_bodies[i],entries[i].displacement,
                                       entries[i].spec.rva+entries[i].spec.stolen,hp))return false;
        for(std::size_t j=0;j<entries[i].spec.witness_count;j++)runtime_witnesses[i][j]=entries[i].spec.witnesses[j];
        runtime_witnesses[i][0].expected=runtime_bodies[i]+entries[i].spec.stolen;
        runtime_entries[i].spec.prologue=runtime_bodies[i];runtime_entries[i].spec.witnesses=runtime_witnesses[i];
    }
    const auto composite=entries[4].spec.rva;
    if(!relocate_dat_operand(base,composite,runtime_bodies[4],23,0,units_field(6,1)) ||
       !relocate_dat_operand(base,composite,runtime_bodies[4],34,0,units_field(7,2)) ||
       !relocate_dat_operand(base,composite,runtime_bodies[4],45,0,hp))return false;
    std::memcpy(runtime_add_body,add_original_bytes,sizeof(add_original_bytes));
    if(!relocate_dat_operand(base,add_spec.rva,runtime_add_body,34,0,hp) ||
       !relocate_dat_operand(base,add_spec.rva,runtime_add_body,57,0,hp))return false;
    if(!relocate_dat_operand(base,add_spec.rva,runtime_add_body,132,0,damage_overlay_array()))return false;
    runtime_add_spec=add_spec;
    for(std::size_t i=0;i<std::size(add_witnesses);i++)runtime_add_witnesses[i]=add_witnesses[i];
    runtime_add_spec.prologue=runtime_add_body;runtime_add_spec.witnesses=runtime_add_witnesses;
    runtime_add_witnesses[0].expected=runtime_add_body+add_spec.stolen;
    return true;
}
