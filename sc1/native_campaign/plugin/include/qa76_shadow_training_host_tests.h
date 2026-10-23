#pragma once
namespace host_test {
namespace qa76_fixture {
inline std::vector<bw::Point> strike_positions;
inline bw::Point incoming{};
inline void __cdecl damage(bw::Unit* u,std::int32_t amount,U8 weapon,U32 divisor,U8 direction,bw::Unit* source,U32 owner){
 strike_positions.push_back(source->flingy.position);qa75_fixture::record_damage(u,amount,weapon,divisor,direction,source,owner);
}
inline U32 __cdecl wrong_side_place(bw::Unit*,const bw::Point*,bw::Point* result,const void*,U32,U32){*result=incoming;return 1;}
inline U32 train_steps=0;
inline void __cdecl train(bw::Unit* factory){
 auto child=factory->secondary_order_target.unit;if(!child || (child->flags&1u) || factory->lockdown_timer)return;
 ++train_steps;g.set_hp(child,std::int32_t(std::min<std::uint64_t>(effective_max_hp(child),std::uint64_t(child->flingy.hitpoints)+child->build_hp_gain)));
 if(child->remaining_build_time)--child->remaining_build_time;
 else {child->flags|=1u;factory->secondary_order_target.unit=nullptr;}
}
}
inline void qa76_shadow_five_tiles_fallback_and_opposite_each_hit(){
 using namespace rework_fixture;using namespace qa76_fixture;
 for(const auto offset:std::array<bw::Point,5>{{{-192,0},{192,0},{0,-192},{0,192},{-120,-120}}}){
  qa9_fixture::begin({321});relocation();projectile_audit_fixture::load_dimensions();
  auto u=unit(61,1,500+offset.x,500+offset.y),a=unit(37,6,500,500);u->order=10;multi_fixture::target(u,a);
  const auto origin=u->flingy.position;const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=damage;
  qa75_fixture::victims.clear();strike_positions.clear();rework_combat_v5::shadow_begin(u,a);auto s=rework_combat_v5::state(u);
  auto previous=origin;
  for(U32 i=0;i<5;i++){
   game.frame_count=100+i*4;rework_combat_v5::focus_tick(u,*s);CHECK(strike_positions.size()==i+1);
   const auto p=strike_positions.back();CHECK(std::int64_t(previous.x-500)*(p.x-500)+std::int64_t(previous.y-500)*(p.y-500)<0);previous=p;
  }
  CHECK(std::all_of(qa75_fixture::victims.begin(),qa75_fixture::victims.end(),[&](auto v){return v==a;}));
  CHECK(!s->shadow_active&&u->flingy.position.x==origin.x&&u->flingy.position.y==origin.y);
  combat_effects::original_weapon_damage=saved;relocation_end();qa9_fixture::end();
 }
 // A previously hit alternative still beats the last victim: A,B,A,B,A.
 qa9_fixture::begin({321});relocation();projectile_audit_fixture::load_dimensions();auto u=unit(61,1,500,500),a=unit(37,6,692,500),b=unit(37,6,852,500);
 const auto saved=combat_effects::original_weapon_damage;combat_effects::original_weapon_damage=damage;qa75_fixture::victims.clear();strike_positions.clear();u->order=10;multi_fixture::target(u,a);rework_combat_v5::shadow_begin(u,a);auto s=rework_combat_v5::state(u);
 for(U32 i=0;i<5;i++){game.frame_count=100+i*4;rework_combat_v5::focus_tick(u,*s);CHECK(qa75_fixture::victims.size()==i+1&&qa75_fixture::victims.back()==(i%2?b:a));}
 combat_effects::original_weapon_damage=saved;relocation_end();qa9_fixture::end();
 // Collision search returning the original side must not teleport or strike.
 qa9_fixture::begin({321});relocation();u=unit(61,1,684,500);a=unit(37,6,692,500);u->order=10;incoming=u->flingy.position;
 rework_relocation::native_place=wrong_side_place;CHECK(!rework_combat_v5::shadow_cross_target(u,a)&&moves==0&&u->flingy.position.x==incoming.x);
 relocation_end();qa9_fixture::end();
 std::printf("QA76_SHADOW trigger=6 chain=5 damage_percent=200 fallback_only=1 opposite_each_hit=1 return=1\n");
}
inline void qa76_training_acceleration_advances_health_and_preserves_damage(){
 using namespace qa76_fixture;
 const std::pair<U32,U32> trainees[]={{106,7},{111,0},{111,32},{111,1},{111,34},{113,2},{113,3},{113,5},{114,8},{114,9},{114,11},{114,12},{114,58},{154,64},{160,65},{160,66},{160,67},{160,61},{155,69},{155,83},{155,84},{167,70},{167,71},{167,72},{167,60},{130,50}};
 for(const auto& row:trainees)for(bool boosted:{false,true}){
  const auto id=row.second;
  reset();game.elapsed_seconds=60;CHECK(apply_snapshot(nullptr,economy_snapshot(boosted?std::initializer_list<U32>{25}:std::initializer_list<U32>{})));
  auto factory=economy_add(row.first);factory->flags|=1;factory->secondary_order=38;
  auto child=economy_add(id);child->flags&=~1u;factory->secondary_order_target.unit=child;
  const auto maximum=effective_max_hp(child),duration=std::max(1u,owner_stat(1,{0,42,id}));
  const auto initial=maximum/10;child->flingy.hitpoints=std::int32_t(initial);child->remaining_build_time=std::uint16_t(duration);
  child->build_hp_gain=std::uint16_t((maximum-initial+duration-1)/duration);train_steps=0;
  auto veteran=economy_add(id);veteran->flags|=1;veteran->flingy.hitpoints=std::int32_t(maximum/2);
  for(U32 frame=1;frame<=duration+2&&!(child->flags&1u);frame++){
   game.frame_count=frame;game.elapsed_seconds=60+frame/24;owner_secondary_hook(factory,train);
  }
  CHECK((child->flags&1u)&&child->flingy.hitpoints==std::int32_t(maximum));
  CHECK(veteran->flingy.hitpoints==std::int32_t(maximum/2));
  const auto timer_only=std::min<std::uint64_t>(maximum,std::uint64_t(initial)+std::uint64_t(train_steps)*child->build_hp_gain);
  if(boosted)CHECK(timer_only<maximum);
  child->flingy.hitpoints-=256;const auto damaged=child->flingy.hitpoints;++game.frame_count;owner_secondary_hook(factory,train);CHECK(child->flingy.hitpoints==damaged);
  if(id==66&&boosted)std::printf("QA76_DRAGOON timer_only_hp_q8=%llu fixed_hp_q8=%u max_hp_q8=%u veteran_unchanged=1 post_completion_damage_preserved=1\n",static_cast<unsigned long long>(timer_only),maximum,maximum);
 }
 std::printf("QA76_TRAINING unit_types=%zu boosted_and_unboosted=1 full_hp=1 completed_damage_preserved=1\n",std::size(trainees));
 // Extra progress is the native per-frame gain, never an unconditional heal.
 reset();game.elapsed_seconds=60;CHECK(apply_snapshot(nullptr,economy_snapshot({25})));auto factory=economy_add(160),child=economy_add(66);factory->flags|=1;factory->secondary_order=38;factory->secondary_order_target.unit=child;child->flags&=~1u;child->remaining_build_time=50;child->build_hp_gain=10;child->flingy.hitpoints=100;
 for(U32 frame=1;frame<=2;frame++){game.frame_count=frame;owner_secondary_hook(factory,train);}CHECK(child->remaining_build_time==47&&child->flingy.hitpoints==130);
 factory->lockdown_timer=10;const auto hp=child->flingy.hitpoints;const auto time=child->remaining_build_time;++game.frame_count;owner_secondary_hook(factory,train);CHECK(child->flingy.hitpoints==hp&&child->remaining_build_time==time);
}
inline constexpr std::size_t qa76_group_count=2;
inline void run_qa76_groups(){qa76_shadow_five_tiles_fallback_and_opposite_each_hit();qa76_training_acceleration_advances_health_and_preserves_damage();}
}
