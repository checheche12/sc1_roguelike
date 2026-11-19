#pragma once
namespace host_test {
namespace playthrough_fixture {
inline GrowthSnapshot snapshot(U32 bonus){GrowthSnapshot s{};s.wire_version=2;s.talent_bits[15]=0x80000000u;s.talent_bits[13]=bonus<<21;return s;}
inline void set(GrowthSnapshot& s,U32 ordinal,U32 value){
 auto f=playthrough_ranks::fields[ordinal];CHECK(f.width!=0);
 s.talent_ranks[f.slot]=(s.talent_ranks[f.slot]&~(((1u<<f.width)-1u)<<f.shift))|(value<<f.shift);
 if(ordinal<199){auto bit=238+ordinal;if(value)s.talent_bits[bit/32]|=1u<<(bit%32);else s.talent_bits[bit/32]&=~(1u<<(bit%32));}
}
}
inline void playthrough_rank_codec_boundaries(){
 using namespace playthrough_fixture;
 for(U32 bonus:{1u,4u,20u,253u}){
  auto s=snapshot(bonus);
  for(U32 ordinal=0;ordinal<std::size(playthrough_ranks::fields);++ordinal){auto f=playthrough_ranks::fields[ordinal];if(!f.width)continue;
   const U32 stacks=f.width==1?1u:std::min(255u,f.base+bonus);set(s,ordinal,stacks);
   CHECK(rework_catalog::rank(s,ordinal)==stacks);CHECK(rework_catalog::valid_packed(s));
  }
  auto corrupt=s;corrupt.talent_bits[14]=1;CHECK(!rework_catalog::valid_packed(corrupt));
  corrupt=s;corrupt.talent_ranks[27]|=0x80000000u;CHECK(!rework_catalog::valid_packed(corrupt));
 }
 auto invalid=snapshot(1);set(invalid,199,6);CHECK(!rework_catalog::valid_packed(invalid));
 invalid=snapshot(1);set(invalid,8,1);invalid.talent_bits[(238+8)/32]&=~(1u<<((238+8)%32));CHECK(!rework_catalog::valid_packed(invalid));
 invalid=snapshot(0);CHECK(!rework_catalog::valid_packed(invalid));
}
inline void playthrough_native_health_damage_and_tower(){
 using namespace playthrough_fixture;
 for(U32 stacks:{5u,8u,16u}){
  qa13_fixture::begin();auto s=snapshot(stacks-4);set(s,201,stacks);set(s,202,stacks);
  auto marine=add(0,1,100,100,40*256),enemy=add(0,6,200,100,40*256);
  CHECK(apply_snapshot(nullptr,s));
  const U32 hp=U32((std::uint64_t(original_stat({0,8,0}))*(100+28*stacks)+50)/100);
  CHECK(effective_max_hp(marine)==hp);CHECK(effective_max_hp(enemy)==original_stat({0,8,0}));
  CHECK(rework_combat_v5::infantry_damage_rank(marine,0)==stacks);
  CHECK(rework_combat_v5::infantry_ui_value(marine,0,100)==100+15*stacks);
  qa13_fixture::end();
 }
 struct ReductionCase {U32 infantry,firebat;std::int32_t expected;};
 for(auto test:{ReductionCase{0,0,1000000},{1,0,900000},{1,1,810000},{2,2,656100},
                {4,5,387420},{5,5,348678},{5,6,313811},{10,10,121577},{255,255,0}}){
  qa13_fixture::begin();auto s=snapshot(253);set(s,29,test.infantry);set(s,204,test.firebat);
  auto firebat=add(32,1,100,100,40*256),enemy=add(0,6,200,100,40*256);
  CHECK(apply_snapshot(nullptr,s));g.normal_hit=true;
  std::int32_t damage=1000000;
  {rework_combat_v5::DamageScope hit(firebat,enemy,0,1,damage);CHECK(damage==test.expected);}
  qa13_fixture::end();
 }
 qa13_fixture::begin();auto s=snapshot(1);set(s,322,3);
 auto tower=add(124,1,100,100);CHECK(apply_snapshot(nullptr,s));
 CHECK(rework_combat_v5::tower_rank(g.growth,124)==3);
 CHECK(effective_max_hp(tower)==original_stat({0,8,124})*4);
 CHECK(owner_stat(6,{0,8,124})==original_stat({0,8,124}));qa13_fixture::end();
}
}
