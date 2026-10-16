#pragma once
// Revision-five economy. Include after the common native engine helpers.
// Public layouts: bw_dat42fba427 UnitWorker1(count27), UnitBuilding(timer14),
// UnitSpecific2::resource(amount0). See analysis/runtime_rework_20261016/primary_sources.
#include "rework_catalog.generated.h"
namespace rework_economy_v5 {
inline U32 rank(const GrowthSnapshot& s,U32 id) noexcept {return rework_catalog::rank(s,id);}
inline U32 rank(U32 id) noexcept {return rank(g.growth,id);}
inline bool live(const bw::Unit* u) noexcept {return valid_unit(u) && u->order && u->flingy.hitpoints>0;}
inline bool own(const bw::Unit* u) noexcept {return live(u) && u->player==player_owner() && !hallucination(u);}
inline bool in(U32 id,std::initializer_list<U32> ids) noexcept {return std::find(ids.begin(),ids.end(),id)!=ids.end();}
inline bool worker(U32 id) noexcept {return in(id,{7,41,64});}
inline bool depot(U32 id) noexcept {return in(id,{106,131,132,133,154});}
inline bool resource(U32 id) noexcept {return in(id,{176,177,178,188,110,149,157});}
inline U32 ceiling(U32 value,U32 n,U32 d) noexcept {return static_cast<U32>((std::uint64_t(value)*n+d-1)/d);}
inline U32 price(const GrowthSnapshot& s,U32 id,U32 base) noexcept {
    U32 value=base;
    if(rank(s,7) && in(id,{106,131,154}))value=ceiling(value,7,10);
    if(rank(s,117) && in(id,{73,85}))value=ceiling(value,1,2);
    constexpr U32 ordinals[]={151,152,153,154,155,156,157,158,159,160};
    const auto group=[&](U32 ordinal){switch(ordinal){
        case 151:return in(id,{0,1,32,34});case 152:return in(id,{2,3,5});
        case 153:return in(id,{8,9,11,12,58});case 154:return in(id,{37,39});
        case 155:return in(id,{38,103});case 156:return in(id,{45,46});
        case 157:return in(id,{43,44,47,62});case 158:return in(id,{61,65,67});
        case 159:return in(id,{66,83});case 160:return in(id,{60,69,70,71,72,84});
        default:return false;}};
    for(U32 ordinal:ordinals)if(rank(s,ordinal) && group(ordinal))value=ceiling(value,4,5);
    if(rank(s,24) && id==41)value=ceiling(value,2,1);
    return value;
}
inline bool plan_stats(const GrowthSnapshot& s,std::vector<Edit>& edits) {
    const auto set=[&](U32 field,U32 id,U32 value){return plan_edit(edits,{0,field,id},0,value,1);};
    for(U32 id=0;id<228;id++){
        for(U32 field:{40u,41u}){const auto before=original_stat({0,field,id}),after=price(s,id,before);if(after!=before && !set(field,id,after))return false;}
        U32 time=original_stat({0,42,id});const U32 base_time=time;
        if(rank(s,3) && worker(id))time=std::max(1u,ceiling(time,1,2));
        if(rank(s,7) && in(id,{106,131,154}))time=std::max(1u,ceiling(time,7,10));
        const U32 flags=original_stat({0,44,id});
        if((flags&16u) && ((rank(s,20) && (flags&2u)) || (rank(s,22) && (flags&4u))))time=std::max(1u,ceiling(time,1,2));
        if(rank(s,117) && in(id,{73,85}))time=std::max(1u,ceiling(time,1,2));
        if(rank(s,4) && in(id,{109,42,156}))time=72;
        if(time!=base_time && !set(42,id,time))return false;
        if(rank(s,4) && in(id,{109,42,156}) && !plan_edit(edits,{0,45,id},1,16,1))return false;
    }
    return true;
}
struct Identity {bw::Unit* p=nullptr;U32 id=228,owner=12,unique=0;};
inline Identity identity(bw::Unit* u) noexcept {return valid_unit(u) ? Identity{u,u->unit_id,u->player,u->minor_unique_index} : Identity{};}
inline bw::Unit* resolve(const Identity& i) noexcept {return live(i.p) && i.p->unit_id==i.id && i.p->player==i.owner && i.p->minor_unique_index==i.unique ? i.p : nullptr;}
struct QueueCost {U32 id=228,mineral=0,gas=0;};
struct UnitState {
    Identity who{};bool seen=false,resource_scaled=false,twin=false,twin_pending=false,mule_free_supply=false;
    U32 last_frame=~0u,last_larva_timer=0,larva_fraction=0,larva_due=0,mule_expiry=0;
    U32 chrono_build_fraction=0,chrono_research_fraction=0,larva_due_fraction=0;
    Identity chrono_child{};U32 research_key=0;
    std::array<QueueCost,5> queue{};
    U32 queue_slot=0;bool queue_seen=false,larva_seen=false;QueueCost paid_building{};
};
inline std::vector<UnitState> states;
inline bw::Unit* state_base=nullptr;
inline bool start_box=false,scaled_resources=false,provided_applied=false,creating_mule=false,creating_twin=false,snapshot_seen=false;
inline U32 next_mule=0;
inline bool starting_bonus_credited=false;
inline U32 starting_workers=0,starting_retry=0;
inline UnitState* state(bw::Unit* u) {
    if(!valid_unit(u))return nullptr;
    if(state_base!=g.units || states.size()!=g.units_count){states.assign(g.units_count,{});state_base=g.units;}
    auto& s=states[std::size_t(u-g.units)];
    if(s.who.p!=u || s.who.owner!=u->player || s.who.unique!=u->minor_unique_index){const bool scaled=s.who.p==u && s.who.unique==u->minor_unique_index && resource(s.who.id) && resource(u->unit_id) && s.resource_scaled;s={};s.who=identity(u);s.resource_scaled=scaled;}else s.who.id=u->unit_id;
    return &s;
}
inline bool mule(bw::Unit* u) {auto s=state(u);return s && s->mule_expiry!=0;}
inline U32 amount(const bw::Unit* u) noexcept;
inline std::uint64_t distance(const bw::Unit* a,const bw::Unit* b) noexcept {auto x=std::int64_t(a->flingy.position.x)-b->flingy.position.x,y=std::int64_t(a->flingy.position.y)-b->flingy.position.y;return std::uint64_t(x*x+y*y);}
inline bw::Unit* nearest_mineral(bw::Unit* u) {
    bw::Unit* result=nullptr;std::uint64_t best=~std::uint64_t(0);
    living_units([&](bw::Unit* n){if(in(n->unit_id,{176,177,178}) && amount(n)){const auto d=distance(u,n);if(d<best){best=d;result=n;}}});return result;
}
inline void credit(U32 minerals,U32 gas) noexcept {
    auto game=g.game ? g.game() : nullptr;if(!game)return;
    auto add=[](U32& v,U32 amount){v=static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(v)+amount));};
    add(game->minerals[player_owner()],minerals);add(game->gas[player_owner()],gas);
}
inline U32 carried(const bw::Unit* u) noexcept {return u->unit_specific.bytes[27];}
inline U32 amount(const bw::Unit* u) noexcept {std::uint16_t n=0;std::memcpy(&n,u->unit_specific2.bytes,2);return n;}
inline void amount(bw::Unit* u,U32 n) noexcept {const auto v=static_cast<std::uint16_t>(std::min(65535u,n));std::memcpy(u->unit_specific2.bytes,&v,2);}
inline bool enabled() noexcept {return g.active && g.applied && g.game && GetCurrentThreadId()==g.game_thread.load();}
inline double motion_ratio(bw::Unit* u) noexcept {return own(u) && worker(u->unit_id) && rank(6) ? 1.5 : 1.0;}
inline QueueCost current_cost(U32 id) noexcept {return {id,owner_stat(player_owner(),{0,40,id}),owner_stat(player_owner(),{0,41,id})};}
inline void refresh_building(bw::Unit* u,UnitState& s) noexcept {
    if(!(original_stat({0,22,u->unit_id})&1u) || (u->flags&1u)){s.paid_building={};return;}
    const U32 queued=u->build_queue[u->current_build_slot%5];
    const U32 id=queued<228 && (original_stat({0,22,queued})&1u) ? queued:U32(u->unit_id);
    if(s.paid_building.id!=id)s.paid_building=current_cost(id);
}
inline void refresh_queue(bw::Unit* u,UnitState& s,const GrowthSnapshot& snapshot) noexcept {
    (void)snapshot;
    const U32 current=u->current_build_slot%5;
    if(s.queue_seen && current!=s.queue_slot){auto previous=s.queue;const U32 shift=(current+5-s.queue_slot)%5;for(U32 i=0;i<5;i++)s.queue[i]=i+shift<5 ? previous[i+shift]:QueueCost{};}
    s.queue_slot=current;s.queue_seen=true;
    for(U32 i=0;i<5;i++){
        const auto slot=(u->current_build_slot+i)%5,id=U32(u->build_queue[slot]);
        if(id>=228){s.queue[i]={};continue;}
        if(s.queue[i].id!=id)s.queue[i]=current_cost(id);
    }
    refresh_building(u,s);
}
inline void before_snapshot() {
    if(!g.applied)return;
    living_units([&](bw::Unit* u){if(own(u)){auto s=state(u);if(s)refresh_queue(u,*s,g.growth);}});
}
inline void supply_adjust(U32 race,int amount_) noexcept {
    auto game=g.game ? g.game() : nullptr;if(!game || race>=3)return;
    auto& used=game->supplies[race].used[player_owner()];
    used=amount_>=0 ? static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(used)+static_cast<U32>(amount_))) : used>=static_cast<U32>(-amount_) ? used-static_cast<U32>(-amount_) : 0;
}
// Native callback is the authority for a successful return: both cargo and
// resource flag must clear, and the matching native resource ledger must grow.
struct UnitScope {
    bw::Unit* unit;Identity who;U32 cargo=0,flags=0,minerals=0,gas=0;
    Identity child{};
    std::uint16_t time=0,research=0;bool watch=false;U32 frame=0;
    bw::DatTable* twin_supply_table=nullptr;U32 twin_supply_before=0;
    explicit UnitScope(bw::Unit* u):unit(u),who(identity(u)) {
        if(!enabled() || !live(u) || hallucination(u))return;
        auto game=g.game();frame=game->frame_count;
        if(mule(u) && !in(u->order,{85,86,87,88,89,90,150,151})){
            auto mineral=nearest_mineral(u);
            if(mineral && g.order)g.order(u,85,mineral->flingy.position.x,mineral->flingy.position.y,mineral,0);
            else if(g.order)g.order(u,3,u->flingy.position.x,u->flingy.position.y,nullptr,0);
        }
        if(!own(u))return;
        if(worker(u->unit_id) && in(u->order,{84,90})){cargo=carried(u);flags=u->carried_powerup_flags;minerals=game->minerals[player_owner()];gas=game->gas[player_owner()];watch=true;}
        auto production=u->secondary_order_target.unit;
        if((original_stat({0,22,u->unit_id})&1u) && u->secondary_order==38 && own(production) && !(production->flags&1u)){
            child=identity(production);time=production->remaining_build_time;
        }
        if(in(u->order,{75,76}))std::memcpy(&research,u->unit_specific.bytes+10,2);
        // Recheck the full pair's supply at actual larva morph time too. Other
        // eggs may have consumed supply since the player's queue command.
        if(rank(24) && u->unit_id==35 && u->order==42 && u->build_queue[u->current_build_slot%5]==41){
            twin_supply_table=table_for({0,46,41},false);
            if(twin_supply_table){twin_supply_before=read_entry(twin_supply_table,41);write_entry(twin_supply_table,41,4);}
        }
    }
    ~UnitScope() {
        if(twin_supply_table)write_entry(twin_supply_table,41,twin_supply_before);
        auto u=resolve(who);if(!enabled() || !own(u))return;
        auto game=g.game();
        if(watch && cargo && !carried(u) && !(u->carried_powerup_flags&3u)){
            if((flags&2u) && std::uint64_t(game->minerals[player_owner()])>=std::uint64_t(minerals)+cargo)credit((rank(0)?2u:0u)+(mule(u)?8u:0u),0);
            else if((flags&1u) && std::uint64_t(game->gas[player_owner()])>=std::uint64_t(gas)+cargo && rank(1))credit(0,2);
        }
        auto s=state(u);if(!s || s->last_frame==frame)return;
        // The native step must have advanced the existing job. This prevents
        // free progress on idle/paused/disabled structures or failed orders.
        if(rank(25) && game->elapsed_seconds>=60 && (game->elapsed_seconds-60)%90<20 && (original_stat({0,22,u->unit_id})&1u) && (u->flags&1u) && !u->lockdown_timer && !u->stasis_timer){
            auto job=resolve(child);
            if(s->chrono_child.p!=child.p || s->chrono_child.unique!=child.unique){s->chrono_child=child;s->chrono_build_fraction=0;}
            bool progressed=false;
            if(job && time>job->remaining_build_time && job->remaining_build_time>0){s->chrono_build_fraction+=time-job->remaining_build_time;const auto extra=std::min<U32>(job->remaining_build_time,s->chrono_build_fraction/2);job->remaining_build_time=static_cast<std::uint16_t>(job->remaining_build_time-extra);s->chrono_build_fraction%=2;progressed=true;}
            std::uint16_t after=0;std::memcpy(&after,u->unit_specific.bytes+10,2);
            const U32 job_key=U32(u->order)<<16|U32(u->unit_specific.bytes[12])<<8|u->unit_specific.bytes[13];
            if(s->research_key!=job_key){s->research_key=job_key;s->chrono_research_fraction=0;}
            if(in(u->order,{75,76}) && research>after && after>0){s->chrono_research_fraction+=research-after;const auto extra=std::min<U32>(after,s->chrono_research_fraction/2);after=static_cast<std::uint16_t>(after-extra);s->chrono_research_fraction%=2;std::memcpy(u->unit_specific.bytes+10,&after,2);progressed=true;}
            if(progressed)s->last_frame=frame;
        }
    }
};
struct CommandScope;
inline CommandScope* active_command_scope=nullptr;
struct CommandScope {
    U32 player=12;std::vector<std::pair<Identity,std::array<QueueCost,5>>> before;
    std::vector<std::pair<Identity,QueueCost>> buildings;
    U32 cancel_slot=0xffffffffu;bool cancel_building=false;
    U32 bank_minerals=0,bank_gas=0;
    CommandScope* parent=nullptr;bool registered=false,handled_by_packet=false;
    bw::DatTable* supply_table=nullptr;U32 supply_before=0;
    explicit CommandScope(U32 owner,const void* command=nullptr,U32 length=0,bool precise=false):player(owner) {
        if(!enabled() || owner!=player_owner())return;
        bank_minerals=g.game()->minerals[owner];bank_gas=g.game()->gas[owner];
        parent=active_command_scope;active_command_scope=this;registered=true;
        if(precise && parent)parent->handled_by_packet=true;
        const auto bytes=static_cast<const U8*>(command);
        if(bytes && length>=3 && bytes[0]==0x20)cancel_slot=bytes[1];
        cancel_building=bytes && length>=1 && in(bytes[0],{0x18,0x19,0x34});
        living_units([&](bw::Unit* u){if(own(u)){auto s=state(u);if(s){refresh_queue(u,*s,g.growth);before.emplace_back(identity(u),s->queue);if(s->paid_building.id<228)buildings.emplace_back(identity(u),s->paid_building);}}});
        const bool twin_command=bytes && length==3 && bytes[0]==0x23 && u16(bytes+1)==41;
        if(rank(24) && twin_command){supply_table=table_for({0,46,41},false);if(supply_table){supply_before=read_entry(supply_table,41);write_entry(supply_table,41,4);}}
    }
    ~CommandScope() {
        if(registered)active_command_scope=parent;
        if(supply_table)write_entry(supply_table,41,supply_before);
        if(!registered || handled_by_packet || !enabled() || player!=player_owner())return;
        std::uint64_t refund_minerals=0,refund_gas=0;bool refunded=false;
        const auto refund=[&](const QueueCost& paid,U32 percent){
            refund_minerals+=std::uint64_t(paid.mineral)*percent/100;
            refund_gas+=std::uint64_t(paid.gas)*percent/100;refunded=true;
        };
        if(cancel_building)for(const auto& previous:buildings){const auto u=previous.first.p;
            if(!valid_unit(u) || u->minor_unique_index!=previous.first.unique || u->player!=player_owner())continue;
            const bool remains=live(u) && !(u->flags&1u) && (u->unit_id==previous.second.id || u->build_queue[u->current_build_slot%5]==previous.second.id);
            if(!remains){refund(previous.second,75);auto s=state(u);if(s)s->paid_building={};}
        }
        for(const auto& previous:before){auto u=previous.first.p;if(!own(u) || u->minor_unique_index!=previous.first.unique)continue;auto s=state(u);if(!s)continue;
            std::array<U32,5> current{};for(U32 i=0;i<5;i++)current[i]=u->build_queue[(u->current_build_slot+i)%5];
            std::array<bool,5> used{};std::array<QueueCost,5> next{};
            U32 omitted=5;
            if(cancel_slot!=0xffffffffu){
                U32 old_count=0,new_count=0;for(const auto& q:previous.second)old_count+=q.id<228;for(U32 id:current)new_count+=id<228;
                const U32 requested=cancel_slot==254 && old_count ? old_count-1:cancel_slot;
                if(old_count==new_count+1 && requested<old_count){bool exact=true;for(U32 i=0;i<new_count;++i)if(current[i]!=previous.second[i+(i>=requested)].id)exact=false;if(exact)omitted=requested;}
            }
            for(U32 i=0;i<5;i++)if(current[i]<228){
                bool found=false;for(U32 j=0;j<5;j++)if(j!=omitted && !used[j] && previous.second[j].id==current[i]){next[i]=previous.second[j];used[j]=true;found=true;break;}
                if(!found)next[i]=current_cost(current[i]);
            }
            // Command processing cannot complete simulation production jobs.
            // A removed paid queue entry is a successful cancellation. Sum its
            // paid refund; do not assume the engine used today's DAT price.
            for(U32 j=0;j<5;j++)if(!used[j] && previous.second[j].id<228){
                const auto& old=previous.second[j];
                if(cancel_building && (original_stat({0,22,old.id})&1u))continue;
                const U32 percent=(original_stat({0,22,old.id})&1u) ? 75u:100u;
                refund(old,percent);
            }
            s->queue=next;s->queue_slot=u->current_build_slot%5;s->queue_seen=true;
        }
        if(refunded){
            // The actual13515 callback chain can already return the paid
            // amount through an inner owner-command hook. Applying a DAT-price
            // difference again loses resources. Reconcile this packet's bank
            // against its entry balance and the removed paid ledger. This is
            // idempotent for either native/per-packet callback nesting order.
            auto game=g.game();
            game->minerals[player_owner()]=static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(bank_minerals)+refund_minerals));
            game->gas[player_owner()]=static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(bank_gas)+refund_gas));
        }
    }
};
using CommandNext=void (__cdecl*)(const U8*,U32);
inline void __cdecl command_packet(const U8* data,U32 length,U32 player,U32,CommandNext original) {
    OwnerDatScope owner(player,player);CommandScope command(player,data,length,true);original(data,length);
}
inline bool bind_commands(const samase::PluginApi* api) noexcept {
    if(!api || !api->hook_ingame_command)return false;
    using Hook=void (__cdecl*)(const U8*,U32,U32,U32,CommandNext);
    using Length=U32 (__cdecl*)(const U8*,U32);
    using Register=U32 (__cdecl*)(U32,Hook,Length);
    const auto bind=reinterpret_cast<Register>(api->hook_ingame_command);
    for(U32 id:{0x18u,0x19u,0x20u,0x23u,0x34u})if(!bind(id,command_packet,nullptr))return false;
    return true;
}
inline void created(bw::Unit* u) {
    if(!enabled() || !valid_unit(u) || u->player!=player_owner() || hallucination(u))return;
    auto s=state(u);if(!s)return;
    refresh_building(u,*s);
    if(creating_mule){s->mule_expiry=g.game()->elapsed_seconds+45;s->mule_free_supply=true;}
}
inline void before_kill(bw::Unit* u) {
    if(!enabled() || !valid_unit(u) || u->player!=player_owner() || hallucination(u))return;
    auto s=state(u);if(!s)return;
    // KillUnit can be called after HP reached zero. Compensate precisely once;
    // the native kill still owns its normal supply subtraction.
    if(s->mule_free_supply){supply_adjust(1,static_cast<int>(owner_stat(player_owner(),{0,46,7})));s->mule_free_supply=false;}
    if(s->twin_pending){auto table=table_for({0,46,41},false);const U32 native_cost=table ? read_entry(table,41):2u;supply_adjust(0,static_cast<int>(native_cost)-4);s->twin_pending=false;}
}
inline U32 expiry(bw::Unit* u) {auto s=state(u);return s ? s->mule_expiry:0u;}
inline void transferred(bw::Unit* u,U32 expires) {
    if(!enabled() || !valid_unit(u) || !expires)return;
    auto s=state(u);if(!s)return;s->mule_expiry=expires;
    s->mule_free_supply=u->player==player_owner();
    if(s->mule_free_supply)supply_adjust(1,-static_cast<int>(owner_stat(player_owner(),{0,46,7})));
}
inline void transformed(bw::Unit* u,U32 old_id,U32 supply_before=0xffffffffu) {
    if(!enabled() || !own(u) || creating_twin)return;auto s=state(u);if(!s)return;
    auto game=g.game();auto& supply=game->supplies[0].used[player_owner()];
    if(old_id==35 && u->unit_id==36 && rank(24) && u->build_queue[u->current_build_slot%5]==41 && !s->twin_pending){
        s->twin_pending=true;
        if(supply_before!=0xffffffffu)supply=static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(supply_before)+4));else supply_adjust(0,2);
        return;
    }
    if(old_id==36 && u->unit_id==35 && s->twin_pending){
        if(supply_before!=0xffffffffu)supply=supply_before>=4 ? supply_before-4:0;else supply_adjust(0,-2);
        s->twin_pending=false;return;
    }
    if(old_id!=36 || u->unit_id!=41 || !s->twin_pending || s->twin)return;s->twin=true;s->twin_pending=false;
    creating_twin=true;auto other=spawn(41,u->flingy.position.x+20,u->flingy.position.y,player_owner());creating_twin=false;
    if(other){if(supply_before!=0xffffffffu)supply=supply_before;else supply_adjust(0,-2);auto extra=state(other);if(extra)extra->twin=true;}
    else {credit(50,0);if(supply_before!=0xffffffffu)supply=supply_before>=2 ? supply_before-2:0;else supply_adjust(0,-2);}
}
inline void after_snapshot() {
    if(!enabled())return;
    const bool first_snapshot=!snapshot_seen;snapshot_seen=true;
    if(rank(2) && !scaled_resources){
        living_units([&](bw::Unit* u){if(!resource(u->unit_id))return;auto s=state(u);if(s && !s->resource_scaled){amount(u,std::min(65535u,amount(u)*3));s->resource_scaled=true;}});
        scaled_resources=true;
    }
    if(rank(5) && !start_box && first_snapshot){U32 curses=0;for(auto n:g.growth.curse_counts)curses+=n;credit(curses*50,curses*50);start_box=true;}
    if(rank(23) && !next_mule){const auto second=g.game()->elapsed_seconds;next_mule=second<120 ? 120u:(second/120+1)*120;}
    if(rank(4) && !provided_applied){
        auto game=g.game();living_units([&](bw::Unit* u){if(own(u) && (u->flags&1u) && in(u->unit_id,{109,42,156})){
            const U32 race=u->unit_id==42 ? 0u : u->unit_id==109 ? 1u:2u;auto& supply=game->supplies[race].provided[player_owner()];supply=static_cast<U32>(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(supply)+16));
        }});provided_applied=true;
    }
}
inline void starting_bonus(const std::vector<bw::Unit*>& depots) {
    auto game=g.game();if(!g.mission || g.mission->no_production || game->frame_count<48 || starting_workers>=4 || game->frame_count<starting_retry)return;
    bw::Unit* base=nullptr;
    for(auto candidate:depots){auto mineral=nearest_mineral(candidate);if(!(candidate->flags&4u) && mineral && distance(candidate,mineral)<=768u*768u){base=candidate;break;}}
    if(!base)return;
    const U32 race=base->unit_id==106?1u:base->unit_id==154?2u:0u;
    const U32 id=race==1?7u:race==2?64u:41u;
    if(!starting_bonus_credited){credit(500,500);starting_bonus_credited=true;
        // Preserve the original free supply after adding the four workers.
        auto& provided=game->supplies[race].provided[player_owner()];provided=U32(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(provided)+8));
        message("시작 지원: 광물 500, 가스 500, 추가 일꾼 4기.");
    }
    starting_retry=game->frame_count+24;
    for(int radius=128;radius<=320 && starting_workers<4;radius+=32)for(int dy=-radius;dy<=radius && starting_workers<4;dy+=32)for(int dx=-radius;dx<=radius && starting_workers<4;dx+=32){
        if(std::max(std::abs(dx),std::abs(dy))!=radius)continue;
        const int x=int(base->flingy.position.x)+dx,y=int(base->flingy.position.y)+dy;
        bool occupied=false;living_units([&](bw::Unit* other){if(original_stat({0,22,other->unit_id})&4u)return;
            const auto p=other->flingy.position;const auto ox=std::int64_t(x)-p.x,oy=std::int64_t(y)-p.y;
            const int clearance=(original_stat({0,22,other->unit_id})&1u)?112:40;
            if(ox*ox+oy*oy<std::int64_t(clearance)*clearance)occupied=true;
        });
        if(occupied)continue;auto u=spawn(id,x,y,player_owner());if(!u)continue;++starting_workers;
        if(auto mineral=nearest_mineral(u);mineral && g.order)g.order(u,85,mineral->flingy.position.x,mineral->flingy.position.y,mineral,0);
    }
}
inline void step() {
    if(!enabled())return;auto game=g.game();const auto second=game->elapsed_seconds,frame=game->frame_count;
    std::vector<bw::Unit*> hatcheries;std::vector<bw::Unit*> minerals;std::vector<bw::Unit*> depots;std::vector<bw::Unit*> expired;
    living_units([&](bw::Unit* u){
        if(rank(2) && resource(u->unit_id)){auto s=state(u);if(s && !s->resource_scaled){amount(u,std::min(65535u,amount(u)*3));s->resource_scaled=true;}}
        if(in(u->unit_id,{176,177,178}) && amount(u))minerals.push_back(u);
        auto temporary=state(u);if(temporary && temporary->mule_expiry && second>=temporary->mule_expiry)expired.push_back(u);
        if(!own(u))return;
        if(depot(u->unit_id) && (u->flags&1u))depots.push_back(u);
        if(in(u->unit_id,{131,132,133}) && (u->flags&1u))hatcheries.push_back(u);
    });
    starting_bonus(depots);
    for(auto u:expired){auto s=state(u);if(s)s->mule_expiry=0;if(g.set_hp)g.set_hp(u,0);}
    if(rank(21))for(auto hatch:hatcheries){
        auto s=state(hatch);if(!s)continue;U32 count=0;living_units([&](bw::Unit* u){if(own(u) && u->unit_id==35 && u->related==hatch)++count;});
        if(count>=6){s->larva_due=0;continue;}
        // Native cap3 remains intact. Below3, speed its verified larva timer;
        // at3..5, continue the same period through the public create API.
        auto& timer=hatch->unit_specific.bytes[14];
        if(count<3){
            if(!s->larva_seen){timer=static_cast<U8>(ceiling(timer,10,13));s->larva_seen=true;}
            else if(timer==37 && s->last_larva_timer==0){
                s->larva_fraction+=380;const U32 checks=s->larva_fraction/13;s->larva_fraction%=13;
                timer=static_cast<U8>(checks-1);
            }
            s->last_larva_timer=timer;s->larva_due=0;
        }
        else {
            // Native larva timer37 is evaluated every9 frames (38 passes).
            // 342/1.3 uses fractional carry, rather than an invented234-frame
            // period. New larvae keep the hatchery's native connectedUnit link.
            const auto schedule=[&](){s->larva_due_fraction+=3420;const U32 interval=s->larva_due_fraction/13;s->larva_due_fraction%=13;s->larva_due=frame+interval;};
            if(!s->larva_due)schedule();
            if(frame>=s->larva_due){auto larva=spawn(35,hatch->flingy.position.x-70,hatch->flingy.position.y+30,player_owner());if(larva){larva->related=hatch;larva->order_state=0;}schedule();}
        }
    }
    if(rank(23) && second>=120){
        if(!next_mule)next_mule=120;
        if(second>=next_mule){next_mule=second+120;if(!depots.empty() && !minerals.empty()){
            bw::Unit* base=nullptr;bw::Unit* closest=nullptr;
            for(auto candidate:depots){auto mineral=nearest_mineral(candidate);if(mineral && distance(candidate,mineral)<=512u*512u){base=candidate;closest=mineral;break;}}
            if(!base || !closest)return;
            creating_mule=true;auto u=spawn(7,base->flingy.position.x+80,base->flingy.position.y+50,player_owner());creating_mule=false;
            if(u){supply_adjust(1,-static_cast<int>(owner_stat(player_owner(),{0,46,7})));if(g.order)g.order(u,85,closest->flingy.position.x,closest->flingy.position.y,closest,0);}
        }}
    }
}
inline void reset() noexcept {states.clear();state_base=nullptr;start_box=scaled_resources=provided_applied=creating_mule=creating_twin=snapshot_seen=false;next_mule=0;starting_bonus_credited=false;starting_workers=starting_retry=0;active_command_scope=nullptr;}
}
