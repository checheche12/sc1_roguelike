#pragma once
// Included inside rework_economy_v5. Public bw_dat x64 Worker1 byte26,
// Worker2 pointer0 and Resource byte3. Native orders retain ownership of the
// harvest queue, animation, 75-frame timer, cargo and resource subtraction.
// References: OpenBW 4b046d5: try_gather_resource/gather_queue_next;
// teippi 05c006c2: Order_HarvestMinerals/AcquireResource.
inline bw::Unit* harvest_target(const bw::Unit* u) noexcept {
    bw::Unit* target=nullptr;std::memcpy(&target,u->unit_specific2.bytes,sizeof(target));return target;
}
struct MineralOccupancy {U32 count=0;bool all_owned=true;};
inline MineralOccupancy mineral_occupancy(bw::Unit* mineral) {
    MineralOccupancy out{};
    // Native harvesters touch the patch; use the current engine area index,
    // with the full-list fallback when that API is unavailable.
    unit_area_search::nearby(mineral->flingy.position.x,mineral->flingy.position.y,128,[&](bw::Unit* u){
        if(live(u)&&worker(u->unit_id)&&u->unit_specific.bytes[26]&&harvest_target(u)==mineral){
            ++out.count;if(!own(u))out.all_owned=false;
        }
    });return out;
}
struct MineralGatherScope {
    Identity targets[2]{};
    explicit MineralGatherScope(bw::Unit* u) {
        if(!enabled()||!rank(2)||!live(u)||!worker(u->unit_id)||hallucination(u))return;
        auto target=u->order_target.unit,previous=harvest_target(u);
        bw::Unit* candidates[]={target,previous};
        for(U32 i=0;i<2;++i){
            auto p=candidates[i];
            if((i&&p==target)||!live(p)||!in(p->unit_id,{176,177,178})||!amount(p)||p->unit_specific2.bytes[3]>1)continue;
            targets[i]=identity(p);const auto occupancy=mineral_occupancy(p);
            if(occupancy.count)p->unit_specific2.bytes[3]=1;
            // A free second slot is visible only to an owned worker entering
            // the native admission path. Never unlink/reorder waiting workers.
            if(p==target&&own(u)&&in(u->order,{85,86})&&!u->unit_specific.bytes[26]&&
               occupancy.count==1&&occupancy.all_owned)p->unit_specific2.bytes[3]=0;
        }
    }
    ~MineralGatherScope(){
        for(const auto& entry:targets){auto p=resolve(entry);if(!p)continue;
            // FinishedMining clears the stock single-worker reservation. Keep
            // it occupied when the other worker (or the next queued one) remains.
            if(mineral_occupancy(p).count)p->unit_specific2.bytes[3]=1;
        }
    }
};
