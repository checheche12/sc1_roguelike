#pragma once
// Native range/sight/acquisition queries only read these DAT fields. Keep
// their owner view small while preserving the complete view for orders,
// damage, creation and transformation. Rebuild only at phase boundaries.
namespace owner_dat_query {
inline const OwnerEdit* source=nullptr;
inline std::size_t count=~std::size_t(0);
inline std::vector<OwnerEdit> edits;
struct Prepared {bw::DatTable* table;U32 id,value;};
struct Plan {bool ready=false;std::vector<Prepared> edits;};
inline std::array<Plan,36> plans;
inline std::array<std::array<Plan,228>,3> health_plans;
inline void invalidate_plans() noexcept {
 for(auto& p:plans)p.ready=false;
 for(auto& view:health_plans)for(auto& p:view)p.ready=false;
}
// Defined alongside the pinned health adapter. Unverified image/overlay paths
// keep the full view; only the witnessed simple HP path can use four fields.
bool narrow_health_allowed(const bw::Unit*) noexcept;
inline void reset() noexcept {source=nullptr;count=~std::size_t(0);edits.clear();invalidate_plans();}
inline const std::vector<OwnerEdit>& values() {
 if(source!=g.owner_edits.data()||count!=g.owner_edits.size()){
  edits.clear();source=g.owner_edits.data();count=g.owner_edits.size();
  invalidate_plans();
  for(const auto& e:g.owner_edits)
   if((e.key.table==0&&(e.key.field==17||e.key.field==19||e.key.field==22||e.key.field==23||e.key.field==24))||
      (e.key.table==1&&(e.key.field==3||e.key.field==5)))edits.push_back(e);
 }
 return edits;
}
inline const std::vector<Prepared>& health_plan(U32 view,U32 id) {
 values();auto& p=health_plans[view][id];
 if(!p.ready){
  p.edits.clear();
  for(const auto& e:g.owner_edits)
   if(e.key.table==0&&e.key.id==id&&(e.key.field==6||e.key.field==7||e.key.field==8||e.key.field==22))
    p.edits.push_back({e.table,id,view==1?e.friendly:view==2?e.enemy:e.original});
  p.ready=true;
 }
 return p.edits;
}
// Cache only immutable target values, never the current DAT contents or
// whether a write is needed. Every nested scope still observes and restores
// exact current values, including another owner and intervening native edits.
inline const std::vector<Prepared>& plan(bool query,U32 unit_view,U32 weapon_view,bool raszagal) {
 const auto& queries=values();
 auto& p=plans[(query?18u:0u)+(raszagal?9u:0u)+unit_view*3u+weapon_view];
 if(!p.ready){
  p.edits.clear();const auto& input=query?queries:g.owner_edits;p.edits.reserve(input.size());
  for(const auto& e:input){
   if(e.key.table==1&&e.key.field==16)continue; // Cooldown belongs to the launch clock.
   const auto view=e.key.table==1?weapon_view:unit_view;
   U32 next=view==1?e.friendly:view==2?e.enemy:e.original;
   if(e.key.table==0&&e.key.field==48&&(e.key.id==11||e.key.id==42||e.key.id==57||e.key.id==69))next=std::min(next,8u);
   if(view==1&&raszagal&&e.key.table==1&&e.key.field==5&&e.key.id==100)next=e.original;
   p.edits.push_back({e.table,e.key.id,next});
  }
  p.ready=true;
 }
 return p.edits;
}
}
