#pragma once
namespace host_test {
inline void dat_fixed_width_access_preserves_unaligned_bytes(){
 for(U32 width:{1u,2u,3u,4u})for(U32 offset=0;offset<8;++offset)for(U32 value:{0u,1u,255u,256u,65535u,65536u,0x89abcdefu,0xffffffffu}){
  std::array<U8,48> actual{},expected{};actual.fill(0x5a);expected=actual;
  bw::DatTable t{actual.data()+offset,width,8};
  std::memcpy(expected.data()+offset+width*3,&value,width);write_entry(&t,3,value);CHECK(actual==expected);
  U32 before=0;std::memcpy(&before,expected.data()+offset+width*3,width);CHECK(read_entry(&t,3)==before);
 }
}
inline void dat_prepared_views_preserve_nested_mutation_and_phase_updates(){
 reset();g.applied=true;
 for(U32 table:{0u,1u})for(U32 field:{5u,7u,8u,16u,17u,19u,22u,23u,24u,48u})for(U32 id:{0u,11u,42u,57u,69u,98u,100u}){
  auto t=&dat[table][field];if(id>=t->entries)continue;
  const auto original=read_entry(t,id);g.owner_edits.push_back({{table,field,id},t,original,(original+3)&maximum(t),(original+7)&maximum(t)});
 }
 owner_dat_query::reset();auto hero=add(98,1,100,100);refresh_units();
 const auto before=[&](){std::vector<U32> r;for(const auto& e:g.owner_edits)r.push_back(read_entry(e.table,e.key.id));return r;};
 const auto expected=[&](U32 owner,U32 weapon_owner,bool query,bool special,const std::vector<U32>& prior){
  auto r=prior;
  for(std::size_t i=0;i<g.owner_edits.size();++i){const auto& e=g.owner_edits[i];
   if(query&&!((e.key.table==0&&(e.key.field==17||e.key.field==19||e.key.field==22||e.key.field==23||e.key.field==24))||(e.key.table==1&&(e.key.field==3||e.key.field==5))))continue;
   if(e.key.table==1&&e.key.field==16)continue;
   const auto who=e.key.table==1?weapon_owner:owner;U32 next=who==1?e.friendly:who==6?e.enemy:e.original;
   if(e.key.table==0&&e.key.field==48&&(e.key.id==11||e.key.id==42||e.key.id==57||e.key.id==69))next=std::min(next,8u);
   if(who==1&&special&&e.key.table==1&&e.key.field==5&&e.key.id==100)next=e.original;
   r[i]=next&maximum(e.table);
  }return r;
 };
 const auto baseline=before();
 for(U32 owner:{1u,6u,12u})for(U32 weapon_owner:{1u,6u,12u})for(bool query:{false,true})for(bool special:{false,true}){
  const auto first=expected(owner,weapon_owner,query,special,baseline);
  {OwnerDatScope scope(owner,weapon_owner,nullptr,special?hero:nullptr,query);CHECK(before()==first);
   // Native or another scope may temporarily alter a field even under an
   // identical owner. A nested prepared view must reapply, then restore it.
   auto& e=g.owner_edits.front();write_entry(e.table,e.key.id,33);const auto changed=before();
   {OwnerDatScope nested(owner,weapon_owner,nullptr,special?hero:nullptr,query);CHECK(before()==expected(owner,weapon_owner,query,special,changed));}
   CHECK(before()==changed);write_entry(e.table,e.key.id,first.front());
   {OwnerDatScope enemy(6,1,nullptr,hero,!query);CHECK(before()==expected(6,1,!query,true,first));}
   CHECK(before()==first);
  }CHECK(before()==baseline);
 }
 // Same vector allocation and count, new phase values: explicit invalidation.
 for(auto& e:g.owner_edits)e.friendly=(e.friendly+1)&maximum(e.table);
 owner_dat_query::reset();{OwnerDatScope scope(1,1,nullptr);CHECK(before()==expected(1,1,false,false,baseline));}CHECK(before()==baseline);
}
inline void indexed_ranks_and_movement_match_original_lookup(){
 GrowthSnapshot snapshot{};U32 random=0x97a31025u;
 const auto next=[&](){random^=random<<13;random^=random>>17;random^=random<<5;return random;};
 for(U32 trial=0;trial<128;++trial){
  for(auto& word:snapshot.talent_bits)word=next();for(auto& word:snapshot.talent_ranks)word=next();
  for(U32 ordinal=0;ordinal<rework_catalog::kTalentCount+2;++ordinal){
   U32 expected=0;for(auto f:rework_catalog::kPackedFields)if(f.ordinal==ordinal){expected=(rework_catalog::word(snapshot,f.word)>>f.shift)&((1u<<f.width)-1u);break;}
   CHECK(rework_catalog::packed_rank(snapshot,ordinal)==expected);
  }
  CHECK(rework_catalog::packed_rank(snapshot,0xffffffffu)==0);
 }
 for(U32 id=0;id<228;++id){
  std::vector<std::size_t> expected,actual;
  for(std::size_t i=0;i<std::size(frozen::movement_patches);++i)if(frozen::movement_patches[i].unit_id==id)expected.push_back(i);
  for(int i=movement_effects::legacy_index.head[id];i>=0;i=movement_effects::legacy_index.next[std::size_t(i)]){actual.push_back(std::size_t(i));CHECK(actual.size()<=std::size(frozen::movement_patches));}
  CHECK(actual==expected); // Same members AND original multiplication order.
 }
}
inline constexpr std::size_t dat_performance_group_count=3;
inline void run_dat_performance_groups(){dat_fixed_width_access_preserves_unaligned_bytes();dat_prepared_views_preserve_nested_mutation_and_phase_updates();indexed_ranks_and_movement_match_original_lookup();}
}
