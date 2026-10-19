#pragma once
// Native range/sight/acquisition queries only read these DAT fields. Keep
// their owner view small while preserving the complete view for orders,
// damage, creation and transformation. Rebuild only at phase boundaries.
namespace owner_dat_query {
inline const OwnerEdit* source=nullptr;
inline std::size_t count=~std::size_t(0);
inline std::vector<OwnerEdit> edits;
inline void reset() noexcept {source=nullptr;count=~std::size_t(0);edits.clear();}
inline const std::vector<OwnerEdit>& values() {
 if(source!=g.owner_edits.data()||count!=g.owner_edits.size()){
  edits.clear();source=g.owner_edits.data();count=g.owner_edits.size();
  for(const auto& e:g.owner_edits)
   if((e.key.table==0&&(e.key.field==17||e.key.field==19||e.key.field==22||e.key.field==23||e.key.field==24))||
      (e.key.table==1&&(e.key.field==3||e.key.field==5)))edits.push_back(e);
 }
 return edits;
}
}
