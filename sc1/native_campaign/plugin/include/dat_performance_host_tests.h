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
inline void unit_growth_index_matches_linear_reference(){
 using namespace rework_combat_v5;
 reset();const auto prior=rank_lookup;rank_lookup=nullptr;GrowthSnapshot snapshot{};U32 random=0xc1041025;
 const auto next=[&](){random^=random<<13;random^=random>>17;random^=random<<5;return random;};
 for(bool enabled:{false,true}){talent_power::enabled=enabled;
  for(U32 trial=0;trial<24;++trial){
   for(auto& word:snapshot.talent_bits)word=next();for(auto& word:snapshot.talent_ranks)word=next();
   for(U32 id=0;id<258;++id)for(bool ammo:{false,true}){
    std::vector<std::uint16_t> expected;
    for(std::size_t i=0;i<std::size(unit_growth::rules);++i)if(unit_growth_matches(unit_growth::rules[i],id,ammo))expected.push_back(static_cast<std::uint16_t>(i));
    if(id<256)CHECK(unit_growth_index[ammo][id]==expected);
    for(U32 kind=0;kind<4;++kind){U32 value=0;if(enabled)for(auto i:expected){const auto& r=unit_growth::rules[i];if(r.kind==kind)value=std::max(value,rank(snapshot,r.ordinal));}CHECK(unit_growth_rank(snapshot,id,kind,ammo)==value);}
    for(U32 field=0;field<6;++field){U32 value=0;if(enabled)for(auto i:expected){const auto& r=unit_growth::rules[i];if(r.kind==2&&rank(snapshot,r.ordinal))value=std::max(value,field==0?r.armor:field==1?r.hp:field==2?r.damage:field==3?r.speed:r.energy);}CHECK(unit_trait_value(snapshot,id,field,ammo)==value);}
    U32 parent=0;for(const auto& r:unit_growth::rules)if(r.kind==1&&unit_growth_matches(r,id,true)){parent=r.parent;break;}CHECK(unit_attack_parent(id)==parent);
   }
  }
 }
 CHECK(unit_growth_rank(snapshot,0xffffffffu,1,true)==0);CHECK(unit_trait_value(snapshot,0xffffffffu,3,true)==0);CHECK(unit_attack_parent(0xffffffffu)==0);
 rank_lookup=prior;talent_power::enabled=false;
}

inline void health_plan_preserves_nested_views_and_fallback(){
 using namespace hp_engine_fixture;reset();Image image;
 GrowthSnapshot snapshot{};snapshot.talent_bits[0]=1u<<1;snapshot.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,snapshot));
 auto own=add(0,1,100,100),enemy=add(0,6,100,100);bw::SpriteScr sprite{};movement_effects::Image main{};sprite.main_image=&main;own->flingy.sprite=enemy->flingy.sprite=&sprite;own->flags=enemy->flags=1;
 max_hp_engine::image_dat_getter=get_images;refresh_units();CHECK(owner_dat_query::narrow_health_allowed(own));
 const auto fields=[&](){std::vector<U32> v;for(const auto& e:g.owner_edits)v.push_back(read_entry(e.table,e.key.id));return v;};
 const auto base=fields();
 {OwnerDatScope outer(6,6,enemy);const auto before=fields();
  for(U32 phase=0;phase<2;++phase){
   if(phase){for(auto& e:g.owner_edits)if(e.key.table==0&&e.key.field==8&&e.key.id==0)e.friendly+=256;owner_dat_query::reset();}
   {OwnerHpScope health(own);
    for(std::size_t i=0;i<g.owner_edits.size();++i){const auto& e=g.owner_edits[i];const bool included=e.key.table==0&&e.key.id==0&&(e.key.field==6||e.key.field==7||e.key.field==8||e.key.field==22);CHECK(read_entry(e.table,e.key.id)==(included?e.friendly:before[i]));}
    const auto hp=raw_value(0,8,0);write_entry(&dat[0][8],0,123);
    {OwnerHpScope inner(own);CHECK(raw_value(0,8,0)!=123);}
    CHECK(raw_value(0,8,0)==123);write_entry(&dat[0][8],0,hp);
   }CHECK(fields()==before);
  }
 }CHECK(fields()==base);
 const auto check_full=[&](){std::vector<U32> expected;{OwnerDatScope full(1,1,own);expected=fields();}{OwnerHpScope health(own);CHECK(fields()==expected);}CHECK(fields()==base);};
 void* nonnull=reinterpret_cast<void*>(1);std::memcpy(image_dat[10].data,&nonnull,sizeof(nonnull));CHECK(!owner_dat_query::narrow_health_allowed(own));check_full();
 std::memset(image_dat[10].data,0,sizeof(void*));own->unit_id=125;CHECK(!owner_dat_query::narrow_health_allowed(own));check_full();own->unit_id=0;
 own->flingy.sprite=nullptr;CHECK(!owner_dat_query::narrow_health_allowed(own));check_full();own->flingy.sprite=&sprite;
 max_hp_engine::image_dat_getter=nullptr;CHECK(!owner_dat_query::narrow_health_allowed(own));check_full();
}

#include "hp_scope_native_fixture.generated.h"
inline void health_scopes_match_original_native_hp_and_strength(){
 using namespace hp_engine_fixture;reset();Image image;hp_scope_native_fixture::populate(image.base);
 struct FlagsAlias {bw::DatTable before;FlagsAlias(U8* p):before(dat[0][22]){std::memcpy(p,before.data,228*4);dat[0][22].data=p;}~FlagsAlias(){abandon_session();dat[0][22]=before;}} flags(image.base+0xe5a3e0);
 // Native strength is precomputed by type; preserve it and exercise both
 // native recomputation outputs after HP changes (including energy users).
 for(U32 id=0;id<456;++id){const U32 score=id+100;std::memcpy(image.base+0xeb2ac0+id*4,&score,4);}
 bw::SpriteScr sprite{};movement_effects::Image main{},selection{};sprite.main_image=&main;sprite.first_image=&selection;sprite.flags=8;sprite.visibility_mask=1;selection.drawfunc=11;image.base[0x10908e0]=1;
 auto u=add(0,1,0,0);u->flingy.sprite=&sprite;refresh_units();
 GrowthSnapshot snapshot{};snapshot.talent_bits[0]=1u<<1;snapshot.curse_counts[2]=1;CHECK(apply_snapshot(nullptr,snapshot));image.install();
 const auto native_set=reinterpret_cast<SetHp>(image.base+0x1a8430);
 const auto fields=[&](){std::vector<U32> v;for(const auto& e:g.owner_edits)v.push_back(read_entry(e.table,e.key.id));return v;};
 for(bool cached:{false,true})for(U32 id=0;id<106;++id)for(U32 owner:{1u,6u,11u})for(U32 mode=0;mode<3;++mode){
  u->unit_id=static_cast<std::uint16_t>(id);u->player=static_cast<U8>(owner);u->flags=1u|(mode==1?0x40000000u:0u);u->energy=25000;u->shields=7777;
  auto track=track_unit(u);track->elite=mode==2;if(cached)CHECK(max_hp_cache::publish(true));else max_hp_cache::reset();CHECK(owner_dat_query::narrow_health_allowed(u));
  for(bool addition:{false,true})for(int amount:{0,255,256,999999}){
   OwnerDatScope outer(owner==6?1u:6u,owner==6?1u:6u);const auto before=fields();
   u->flingy.hitpoints=static_cast<int>(effective_max_hp(u)/2);const auto initial=*u;selection.flags=0;
   {OwnerDatScope full(owner,owner,u);if(addition)max_hp_engine::original_add(u,amount);else native_set(u,amount);}
   const auto expected=*u;const auto selection_expected=selection.flags;CHECK(fields()==before);*u=initial;selection.flags=0;
   if(addition)max_hp_engine::add_hp(u,amount);else owner_hp_hook(u,amount,native_set);
   CHECK(u->flingy.hitpoints==expected.flingy.hitpoints);CHECK(std::memcmp(reinterpret_cast<const U8*>(u)+0x1d0,reinterpret_cast<const U8*>(&expected)+0x1d0,4)==0);CHECK(selection.flags==selection_expected);CHECK(fields()==before);
  }
 }
}
inline constexpr std::size_t dat_performance_group_count=6;
inline void run_dat_performance_groups(){dat_fixed_width_access_preserves_unaligned_bytes();dat_prepared_views_preserve_nested_mutation_and_phase_updates();indexed_ranks_and_movement_match_original_lookup();unit_growth_index_matches_linear_reference();health_plan_preserves_nested_views_and_fallback();health_scopes_match_original_native_hp_and_strength();}
}
