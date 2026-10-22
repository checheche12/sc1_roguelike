#pragma once
namespace host_test {
inline constexpr std::size_t qa63_group_count=4;
namespace qa63_fixture {
inline U32 tech_calls=0,weapon_calls=0;inline bw::Unit* denied=nullptr;
inline U32 __cdecl tech(bw::Unit*,U32 id,bw::Unit*,U32,U32,U32,std::uint16_t*){++tech_calls;CHECK(id==13);return 0;}
inline U32 __cdecl weapon(bw::Unit* source,U32 id,bw::Unit* target){++weapon_calls;CHECK(source->unit_id==45||source->unit_id==49);CHECK(id==57);return target!=denied&&!target->stasis_timer;}
inline void __cdecl broodlings(bw::Bullet* b){
 auto target=b->target.unit;CHECK(target&&target->flingy.hitpoints>0);
 for(U32 n=0;n<2;n++){auto born=rank_fixture::create_full(40,target->flingy.position.x+int(n)*4,target->flingy.position.y,b->player,nullptr);CHECK(born);born->death_timer=1800;born->flingy.hitpoints=int(original_stat({0,8,40}));}
 target->flingy.hitpoints=0;target->order=0;
}
}
inline void qa63_unsupported_tech13_does_not_block_native_weapon_fanout(){
 using namespace rework_fixture;qa9_fixture::begin({104});
 const auto old_tech=rework_combat_v5::native_tech_target;const auto old_weapon=rework_combat_v5::native_weapon_target;
 rework_combat_v5::native_tech_target=qa63_fixture::tech;rework_combat_v5::native_weapon_target=qa63_fixture::weapon;qa63_fixture::tech_calls=qa63_fixture::weapon_calls=0;
 auto queen=unit(45,1,100,100,true),primary=unit(37,6,200,100),immune=unit(37,6,201,100);qa63_fixture::denied=immune;
 auto unseen=unit(37,6,202,100);static_cast<bw::SpriteScr*>(unseen->flingy.sprite)->visibility_mask=0;
 auto stasis=unit(37,6,203,100);stasis->stasis_timer=1;
 auto robot=unit(83,6,204,100),airborne=unit(43,6,205,100,true),structure=unit(106,6,206,100),hero=unit(54,6,207,100),ally=unit(37,1,208,100),outside=unit(37,6,329,100);
 for(U32 n=0;n<5;n++)unit(37,6,210+int(n),100);
 multi_target::can_attack=nullptr;queen->energy=0;bullet(queen,primary,57);
 CHECK(rework_combat_v5::pending_shots.size()==3&&qa63_fixture::tech_calls==0&&qa63_fixture::weapon_calls>=3);
 for(const auto& shot:rework_combat_v5::pending_shots)for(auto excluded:{immune,unseen,stasis,robot,airborne,structure,hero,ally,outside})CHECK(shot.target.p!=excluded);
 pulse(101);CHECK(multi_fixture::shots.size()==4&&rework_combat_v5::pending_shots.empty()&&queen->energy==0);
 CHECK(qa63_fixture::tech_calls==0);rework_combat_v5::native_tech_target=old_tech;rework_combat_v5::native_weapon_target=old_weapon;qa63_fixture::denied=nullptr;qa9_fixture::end();
}
inline void qa63_four_impacts_create_twentyfour_double_strength_broodlings(){
 using namespace rework_fixture;qa9_fixture::begin({104});install();
 const auto old_weapon=rework_combat_v5::native_weapon_target;rework_combat_v5::native_weapon_target=qa63_fixture::weapon;
 auto queen=unit(49,1,100,100,true),primary=unit(37,6,200,100),old=unit(40,1,90,100);old->flingy.hitpoints=7*256;
 for(U32 n=0;n<3;n++)unit(37,6,220+int(n)*20,100);
 const auto w=original_stat({0,17,40});CHECK(owner_stat(1,{1,14,w})==original_stat({1,14,w})*2);
 auto b=bullet(queen,primary,57);owner_missile_hook(b,qa63_fixture::broodlings);pulse(101);CHECK(multi_fixture::next_bullet==4);
 for(U32 n=1;n<4;n++)owner_missile_hook(&multi_fixture::bullets[n],qa63_fixture::broodlings);
 U32 birth_count=0;living_units([&](bw::Unit* u){if(u->unit_id==40&&u->player==1&&u!=old){++birth_count;CHECK(U32(u->flingy.hitpoints)==original_stat({0,8,40})*2);CHECK(u->death_timer==1800);}});
 CHECK(birth_count==24&&old->flingy.hitpoints==7*256&&rework_combat_v5::pending_shots.empty());
 CHECK(owner_stat(6,{0,8,40})==original_stat({0,8,40}));rework_combat_v5::native_weapon_target=old_weapon;qa9_fixture::end();
}
inline void qa63_energy100_matches_precheck_tooltip_spend_and_discounts(){
 using namespace rework_fixture;
 for(U32 id:{45u,49u})for(bool efficiency:{false,true}){
  qa9_fixture::begin({104});if(efficiency)ranks[78]=1;write_entry(&dat[4][3],13,150);install();auto queen=unit(id,1,100,100,true);queen->order=121;
  CHECK(owner_stat(1,{4,3,13})==100&&owner_stat(6,{4,3,13})==150);yamato_cost_ui::publish();
  const U32 cost=100*256-rework_combat_v5::cast_energy_refund(queen,121,100*256);
  CHECK(spell_energy_check::required(queen,150*256)==cost&&spell_energy_check::required(queen,100*256)==cost);
  CHECK(yamato_cost_ui::value(queen,13,150)==(cost+255)/256);
  const U32 ensnare=75*256-rework_combat_v5::cast_energy_refund(queen,146,75*256);CHECK(spell_energy_check::required(queen,75*256)==ensnare&&yamato_cost_ui::value(queen,17,75)==(ensnare+255)/256);
  queen->energy=std::uint16_t(cost);qa56_fixture::casts=0;owner_order_hook(queen,qa56_fixture::pay);CHECK(qa56_fixture::cast&&qa56_fixture::casts==1&&queen->energy==0);
  queen->order=121;queen->energy=std::uint16_t(cost-1);owner_order_hook(queen,qa56_fixture::pay);CHECK(!qa56_fixture::cast&&queen->energy==cost-1&&qa56_fixture::casts==1);
  queen->energy=std::uint16_t(cost);owner_order_hook(queen,qa56_fixture::cancel);CHECK(queen->energy==cost);
  queen->player=6;CHECK(spell_energy_check::required(queen,150*256)==150*256&&yamato_cost_ui::value(queen,13,150)==150);queen->player=1;queen->flags|=0x40000000u;CHECK(spell_energy_check::required(queen,150*256)==150*256);
  qa9_fixture::end();
 }
 qa9_fixture::begin({});write_entry(&dat[4][3],13,150);auto queen=unit(45,1,100,100,true);install();yamato_cost_ui::publish();CHECK(owner_stat(1,{4,3,13})==150&&yamato_cost_ui::value(queen,13,150)==150);qa9_fixture::end();
}
inline void qa63_all_six_spell_births_erode_armor_and_receive_subzero_bonus(){
 using namespace rework_fixture;qa9_fixture::begin({104,190});install();auto queen=unit(45,1,100,100,true),victim=unit(37,6,200,100),target=unit(37,6,400,100);
 auto b=bullet(queen,victim,57);owner_missile_hook(b,qa63_fixture::broodlings);std::vector<bw::Unit*> babies;
 living_units([&](bw::Unit* u){if(u->unit_id==40&&u->player==1)babies.push_back(u);});CHECK(babies.size()==6);
 U32 birth_count=0;for(auto u:babies){const auto w=original_stat({0,17,40});multi_fixture::target(u,target);combat_effects::melee_enter(u);combat_effects::weapon_damage(target,256,U8(w),1,0,u,1,qa9_fixture::damage);combat_effects::melee_leave(u);CHECK(rework_combat_v5::state(target)->erosion==33*++birth_count);}
 CHECK(rework_combat_v5::state(target)->erosion==198);g.normal_hit=true;
 for(auto u:babies){const auto erosion=rework_combat_v5::state(target)->erosion;std::int32_t amount=256;{rework_combat_v5::DamageScope scope(target,u,40,1,amount);CHECK(amount==int(256+erosion*256/100));}}
 auto unrelated=unit(38,1,400,100);std::int32_t amount=256;{rework_combat_v5::DamageScope scope(target,unrelated,38,1,amount);CHECK(amount==256);}
 qa9_fixture::end();
}
inline void run_qa63_groups(){qa63_unsupported_tech13_does_not_block_native_weapon_fanout();qa63_four_impacts_create_twentyfour_double_strength_broodlings();qa63_energy100_matches_precheck_tooltip_spend_and_discounts();qa63_all_six_spell_births_erode_armor_and_receive_subzero_bonus();}
}
