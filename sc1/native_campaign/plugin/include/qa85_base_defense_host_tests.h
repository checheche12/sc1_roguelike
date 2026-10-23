#pragma once
namespace host_test {
inline void qa85_added_garrisons_hold_home_without_claiming_originals(){
 using namespace rework_wave_tests;
 begin(308);base_defenses::reset();const auto origin=rework_waves::choose_origin(true);CHECK(origin);
 auto guard=add(65,origin->owner,1000,1000),original=add(65,origin->owner,1040,1000);
 guard->flags=original->flags=1;guard->order=original->order=14;
 const base_defense_data::Post post{308,65,origin->owner,1000,1000};
 base_defenses::bind(&post,1);CHECK(base_defenses::guards.size()==1&&base_defenses::guards[0].unit==guard);
 CHECK(!rework_curses::marked(guard)&&!existing_track(guard));
 guard->order_target={4000,4000,nullptr};original->order_target=guard->order_target;
 auto old_original=*original;
 game.frame_count=100;base_defenses::step(true,false,false);
 CHECK(guard->order_target.x==1000&&guard->order_target.y==1000);
 CHECK(std::memcmp(original,&old_original,sizeof(old_original))==0);
 auto attacker=add(66,player_owner(),1100,1000);attacker->flags=1;attacker->order=2;
 guard->order=10;guard->order_target={1100,1000,attacker};auto fighting=*guard;
 game.frame_count+=8;base_defenses::step(true,false,false);CHECK(std::memcmp(guard,&fighting,sizeof(fighting))==0);
 attacker->flingy.position.x=1600;game.frame_count+=8;base_defenses::step(true,false,false);CHECK(guard->order_target.unit==nullptr&&guard->order_target.x==1000);
 guard->flingy.position.x=1600;guard->order_target={4000,4000,nullptr};fighting=*guard;
 game.frame_count+=8;base_defenses::step(true,true,false);CHECK(std::memcmp(guard,&fighting,sizeof(fighting))==0);
 base_defenses::step(true,false,true);CHECK(std::memcmp(guard,&fighting,sizeof(fighting))==0);
 base_defenses::step(true,false,false);CHECK(guard->order_target.x==1000);
 ++guard->minor_unique_index;guard->order_target={4000,4000,nullptr};fighting=*guard;
 game.frame_count+=8;base_defenses::step(true,false,false);CHECK(base_defenses::guards[0].unit==nullptr&&std::memcmp(guard,&fighting,sizeof(fighting))==0);
 base_defenses::reset();guard->flingy.position.x=1000;base_defenses::bind(&post,1);CHECK(base_defenses::guards.size()==1);
 guard->player=static_cast<U8>(player_owner());game.frame_count+=8;base_defenses::step(true,false,false);CHECK(base_defenses::guards[0].unit==nullptr);
 base_defenses::reset();
 std::printf("QA85_BASE_DEFENSE original_units_untouched=1 attack_at_home=1 return_from_enemy_AI=1 pause_goal_owner_recycle_safe=1 no_wave_registration=1\n");
}
inline constexpr std::size_t qa85_base_group_count=1;
inline void run_qa85_base_groups(){qa85_added_garrisons_hold_home_without_claiming_originals();}
}
