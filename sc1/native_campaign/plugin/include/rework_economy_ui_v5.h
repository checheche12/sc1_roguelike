#pragma once
// Read-only owner-aware production costs. Pinned StarCraft13515 tooltip only;
// never writes a DAT array from drawing. The original formatter still chooses
// unit/morph costs, race, and two-units-per-egg supply arithmetic.
namespace rework_economy_ui {
using U64=std::uint64_t;
constexpr std::size_t capacity=65536;
inline std::atomic<U64> sequence{0};
inline std::atomic<bool> enabled{false},passthrough{false};
inline std::atomic<std::uintptr_t> unit_base{0};
inline std::atomic<std::size_t> unit_count{0};
inline std::array<std::atomic<U64>,12*228> values{};
inline std::uintptr_t writer_base=0;
inline std::size_t writer_count=0;
inline U32 writer_owner=12;
inline U64 pack(U32 mineral,U32 gas,U32 supply) noexcept {return U64(mineral&0xffffu)|(U64(gas&0xffffu)<<16)|(U64(supply&255u)<<32);}
inline U32 identity(const bw::Unit* u) noexcept {return U32(u->unit_id)|(U32(u->player)<<16)|(U32(u->minor_unique_index)<<24);}
inline void reset() noexcept {
    enabled.store(false,std::memory_order_release);sequence.fetch_add(1,std::memory_order_acq_rel);
    unit_base.store(0,std::memory_order_relaxed);unit_count.store(0,std::memory_order_relaxed);
    writer_base=0;writer_count=0;writer_owner=12;sequence.fetch_add(1,std::memory_order_release);
}
inline bool publish(bool force=false) noexcept {
    if(!g.active || !g.applied || !g.units || g.units_count>capacity){reset();return false;}
    const auto base=reinterpret_cast<std::uintptr_t>(g.units);const U32 own=player_owner();
    if(!force && writer_base==base && writer_count==g.units_count && writer_owner==own && enabled.load(std::memory_order_acquire))return true;
    sequence.fetch_add(1,std::memory_order_acq_rel);
    unit_base.store(base,std::memory_order_relaxed);unit_count.store(g.units_count,std::memory_order_relaxed);
    for(U32 owner=0;owner<12;owner++)for(U32 id=0;id<228;id++){
        U32 supply=owner_stat(owner,{0,46,id});
        // The simulation reserves four half-supply for one twin-drone egg.
        // Drone lacks the native two-units flag, so the unchanged UI /2 gives2.
        if(owner==own && id==41 && rework_economy_v5::rank(g.growth,24))supply=4;
        values[owner*228+id].store(pack(owner_stat(owner,{0,40,id}),owner_stat(owner,{0,41,id}),supply),std::memory_order_relaxed);
    }
    writer_base=base;writer_count=g.units_count;writer_owner=own;
    sequence.fetch_add(1,std::memory_order_release);enabled.store(true,std::memory_order_release);return true;
}
inline bool read(const bw::Unit* unit,U32 id,U64& result) noexcept {
    if(id>=228 || !unit || passthrough.load(std::memory_order_acquire) || !enabled.load(std::memory_order_acquire))return false;
    const auto start=sequence.load(std::memory_order_acquire);if(start&1u)return false;
    const auto base=unit_base.load(std::memory_order_relaxed),address=reinterpret_cast<std::uintptr_t>(unit),count=unit_count.load(std::memory_order_relaxed);
    if(address<base || (address-base)%sizeof(bw::Unit) || (address-base)/sizeof(bw::Unit)>=count || count>capacity)return false;
    const U32 key=identity(unit),owner=(key>>16)&255u;
    if((key&0xffffu)>=228 || owner>=12 || (unit->flags&0x40000000u))return false;
    const U64 value=values[owner*228+id].load(std::memory_order_relaxed);
    if(sequence.load(std::memory_order_acquire)!=start || !enabled.load(std::memory_order_acquire) || identity(unit)!=key)return false;
    result=value;return true;
}
inline constexpr U32 cost_site=0x3ee2c0,selected_rva=0x10a4458,output_rva=0x10a37b0;
inline constexpr U32 supply_sites[3]={0x3ee21c,0x3ee244,0x3ee262};
inline constexpr U8 cost_original[]={0x66,0x89,0x05,0xe9,0x54,0xcb,0x00,0x66,0x89,0x0d,0xe4,0x54,0xcb,0x00};
inline constexpr U8 supply_original[3][9]={
    {0x47,0x0f,0xb6,0x94,0x01,0x30,0xcc,0xe5,0x00},
    {0x47,0x0f,0xb6,0x94,0x01,0x30,0xcc,0xe5,0x00},
    {0x43,0x0f,0xb6,0x84,0x01,0x30,0xcc,0xe5,0x00}};
// The fallback cost reads are also witnessed, including their sole relocatable
// displacement. They must still resolve to the public API units.dat arrays.
inline constexpr U32 cost_reads[4]={0x3ee077,0x3ee080,0x3ee278,0x3ee281};
inline constexpr U8 cost_read_original[4][9]={
    {0x41,0x0f,0xb7,0x8c,0x40,0xe0,0xc4,0xe5,0x00},
    {0x41,0x0f,0xb7,0x84,0x40,0x10,0xc3,0xe5,0x00},
    {0x43,0x0f,0xb7,0x8c,0x48,0xe0,0xc4,0xe5,0x00},
    {0x43,0x0f,0xb7,0x84,0x48,0x10,0xc3,0xe5,0x00}};
inline constexpr U8 unit_id_witness[]={0x45,0x0f,0xb7,0x4e,0x1a};
inline constexpr U8 category_witness[]={0x41,0x0f,0xb6,0xcf,0x83,0xe9,0x01,0x0f,0x84,0xc0,0x01,0x00,0x00,0x83,0xe9,0x01};
inline constexpr U8 final_witness[]={0x48,0x8b,0x5d,0xd8,0x48,0x8b,0x45,0xd0};
inline constexpr U8 relay_unwind[]={1,16,9,0,16,0x42,12,0x02,10,0x02,8,0x02,6,0x02,4,0x02,3,0x02,2,0x02,1,0x02,0,0};
inline U8* module=nullptr,*code=nullptr;
inline std::atomic<const U8*> native_supply{nullptr};
inline std::array<RUNTIME_FUNCTION,4> unwind{};
inline U8 originals[4][14]{},branches[4][14]{},expected_code[4][128]{};
inline std::size_t code_sizes[4]{};
inline U8 read_witnesses[4][9]{};
inline bool queued=false,ready=false;
inline const char* last_error="not_bound";
inline const bw::Unit* selected() noexcept {
    const bw::Unit* unit=nullptr;
    return module && native_engine_hooks::read_exact(module+selected_rva,&unit,sizeof(unit)) ? unit:nullptr;
}
inline U64 costs(const bw::Unit* unit,U32 id,U32 mineral,U32 gas) noexcept {
    U64 value=0;return read(unit,id,value) ? (value&0xffffffffu):pack(mineral,gas,0);
}
// R15B is the native tooltip category: 1=unit, 2=upgrade, 3=energy,
// 4=technology, 5=unit without supply. The shared output stores also receive
// technology prices; never reinterpret their IDs as units.dat indices.
inline void __cdecl store_costs(U32 id,U32 mineral,U32 gas,U32 category) noexcept {
    if(!module)return;category&=255u;
    const U64 result=(category==1 || category==5) ? costs(selected(),id,mineral,gas):pack(mineral,gas,0);
    const std::uint16_t out[2]={std::uint16_t(result),std::uint16_t(result>>16)};
    // These two words are the formatter's own output, not simulation/DAT data.
    std::memcpy(module+output_rva,out,sizeof(out));
}
inline U32 __cdecl supply(U32 id) noexcept {
    U64 value=0;if(read(selected(),id,value))return U32(value>>32)&255u;
    const auto original=native_supply.load(std::memory_order_acquire);return original && id<228 ? original[id]:0;
}
inline bool fail(const char* reason) noexcept {ready=false;passthrough.store(true,std::memory_order_release);last_error=reason;return false;}
inline const void* field(U32 id,U32 width) noexcept {
    if(!g.dat_getters[0])return nullptr;std::size_t count=0;const auto tables=g.dat_getters[0](&count);
    return tables && id<count && tables[id].data && tables[id].entry_size==width && tables[id].entries>=228 ? tables[id].data:nullptr;
}
inline bool relocated_read(U8* base,U32 rva,const U8 (&expected)[9],const void* array,U8* captured) noexcept {
    U8 bytes[9];if(!base || !array || !native_engine_hooks::read_exact(base+rva,bytes,sizeof(bytes)) || std::memcmp(bytes,expected,5))return false;
    std::int32_t displacement=0;std::memcpy(&displacement,bytes+5,4);
    if(reinterpret_cast<std::intptr_t>(base)+displacement!=reinterpret_cast<std::intptr_t>(array))return false;
    if(captured)std::memcpy(captured,bytes,9);return true;
}
inline bool witnesses() noexcept {
    if(!module || !native_engine_hooks::match(module+0x3ee026,category_witness,sizeof(category_witness)) ||
       !native_engine_hooks::match(module+0x3ee1f3,unit_id_witness,sizeof(unit_id_witness)) ||
       !native_engine_hooks::match(module+cost_site+sizeof(cost_original),final_witness,sizeof(final_witness)))return false;
    for(U32 i=0;i<4;i++)if(!native_engine_hooks::match(module+cost_reads[i],read_witnesses[i],9))return false;
    return true;
}
inline bool verify_at(const void* mineral,const void* gas,const void* supply_array) noexcept {
    // mutate_dat may move a public array. Only its already identified address
    // operand may change; accept that change solely against the current API
    // table. Supply relays no longer execute their original operand and use
    // the newly published public pointer for baseline fallback instead.
    if(!queued || !code || !supply_array)return fail("not_bound");
    for(U32 i=0;i<4;i++)if(!relocated_read(module,cost_reads[i],cost_read_original[i],i%2 ? mineral:gas,read_witnesses[i]))return fail("cost_operand_changed");
    if(!queued || !code || !witnesses())return fail("witness_changed");
    for(U32 i=0;i<4;i++){
        const U32 site=i ? supply_sites[i-1]:cost_site;const std::size_t size=i ? 9:14;
        if(!native_engine_hooks::match(module+site,branches[i],size) || !native_engine_hooks::match(code+i*128,expected_code[i],code_sizes[i]))return fail("branch_or_relay_changed");
    }
    if(!native_engine_hooks::match(code+1024,relay_unwind,sizeof(relay_unwind)))return fail("unwind_changed");
    native_supply.store(static_cast<const U8*>(supply_array),std::memory_order_release);
    ready=true;passthrough.store(false,std::memory_order_release);last_error="verified";return true;
}
inline bool verify_installation() noexcept {return verify_at(field(40,2),field(41,2),field(46,1));}
inline void emit_relay(U32 index) noexcept {
    auto out=code+index*128;std::size_t n=0;
    const auto put=[&](std::initializer_list<U8> bytes){for(U8 b:bytes)out[n++]=b;};
    // Save all volatile registers and flags. Native supply branches retain
    // their existing R8/R9/RAX inputs, race masks, and two-per-egg multiplier.
    put({0x9c,0x50,0x51,0x52,0x41,0x50,0x41,0x51,0x41,0x52,0x41,0x53,0x48,0x83,0xec,0x28});
    if(!index)put({0x41,0x89,0xc8,0x89,0xc2,0x41,0x0f,0xb7,0x4e,0x1a,0x45,0x89,0xf9});
    else put({0x44,0x89,0xc9});
    put({0x48,0xb8});const auto target=reinterpret_cast<std::uintptr_t>(index ? reinterpret_cast<void*>(supply):reinterpret_cast<void*>(store_costs));
    std::memcpy(out+n,&target,8);n+=8;put({0xff,0xd0});
    if(index)put({0x48,0x89,0x44,0x24,U8(index==3 ? 0x58:0x30)});
    put({0x48,0x83,0xc4,0x28,0x41,0x5b,0x41,0x5a,0x41,0x59,0x41,0x58,0x5a,0x59,0x58,0x9d,0xc3});
    code_sizes[index]=n;std::memcpy(expected_code[index],out,n);
    unwind[index]={index*128,index*128+static_cast<DWORD>(n),1024};
}
inline bool register_at(U8* base,const void* mineral,const void* gas,const void* supply_array,native_engine_hooks::WriteExeMemory writer) noexcept {
    if(queued)return module==base;
    if(code || !base || !writer || !native_engine_hooks::match(base+cost_site,cost_original,sizeof(cost_original)))return fail("original_mismatch");
    for(U32 i=0;i<3;i++)if(!relocated_read(base,supply_sites[i],supply_original[i],supply_array,originals[i+1]))return fail("supply_operand_mismatch");
    for(U32 i=0;i<4;i++)if(!relocated_read(base,cost_reads[i],cost_read_original[i],i%2 ? mineral:gas,read_witnesses[i]))return fail("cost_operand_mismatch");
    module=base;native_supply=static_cast<const U8*>(supply_array);
    if(!witnesses()){module=nullptr;native_supply=nullptr;return fail("formatter_witness_mismatch");}
    code=native_engine_hooks::nearby_code(base+cost_site);if(!code)return fail("allocate");
    std::memcpy(originals[0],cost_original,14);
    for(U32 i=0;i<4;i++)emit_relay(i);
    std::memcpy(code+1024,relay_unwind,sizeof(relay_unwind));
    for(U32 i=0;i<4;i++){
        const U32 site=i ? supply_sites[i-1]:cost_site;const std::size_t size=i ? 9:14;
        const auto delta=reinterpret_cast<std::intptr_t>(code+i*128)-reinterpret_cast<std::intptr_t>(base+site+5);
        if(delta<INT32_MIN || delta>INT32_MAX){VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("relay_too_far");}
        std::memset(branches[i],0x90,size);branches[i][0]=0xe8;const auto relative=std::int32_t(delta);std::memcpy(branches[i]+1,&relative,4);
    }
    DWORD old=0;if(!VirtualProtect(code,4096,PAGE_EXECUTE_READ,&old) || !FlushInstructionCache(GetCurrentProcess(),code,4096)){
        VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("relay_protection");}
    if(!RtlAddFunctionTable(unwind.data(),4,reinterpret_cast<DWORD64>(code))){VirtualFree(code,0,MEM_RELEASE);code=nullptr;return fail("relay_unwind");}
    // Queued patches cannot be withdrawn through API44. On a partial queue
    // failure retain executable passthrough relays for any accepted branch.
    queued=true;passthrough.store(true,std::memory_order_release);
    for(U32 i=0;i<4;i++)if(!writer(reinterpret_cast<std::size_t>(base+(i ? supply_sites[i-1]:cost_site)),branches[i],i ? 9:14))return fail("write_registration_rejected");
    last_error="registered_waiting_for_loader";return true;
}
inline bool bind(const samase::PluginApi* api) noexcept {
    return api && api->write_exe_memory && native_engine_hooks::verify_image() &&
        register_at(native_engine_hooks::verified_base,field(40,2),field(41,2),field(46,1),reinterpret_cast<native_engine_hooks::WriteExeMemory>(api->write_exe_memory));
}
}
