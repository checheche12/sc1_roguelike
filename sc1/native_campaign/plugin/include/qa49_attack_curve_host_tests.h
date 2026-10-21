#pragma once
namespace host_test {
inline constexpr std::size_t qa49_group_count=1;
inline void qa49_accumulated_attack_damage_and_owner_isolation(){
 qa33_fixture::begin(5);g.growth.curse_counts[17]=5;
 auto enemy=qa33_fixture::wave(0);
 CHECK(rework_curses::attack_percent(enemy)==170&&rework_curses::hp_percent(enemy)==170);
 auto player=add(0,player_owner(),100,100,10000);
 auto original=add(0,enemy->player,2000,1000);
 CHECK(rework_curses::attack_percent(original)==100&&rework_curses::attack_percent(player)==100);
 g.normal_hit=true;g.hit_bonus=0;g.elite_hit=false;g.bullet_hit_context=false;
 owner_damage_hook(player,1000,enemy,enemy->player,1,direct_damage);
 CHECK(player->flingy.hitpoints==8300);
 owner_damage_hook(player,1000,original,original->player,1,direct_damage);
 CHECK(player->flingy.hitpoints==7300);
 g.growth.curse_counts[17]=10;CHECK(rework_curses::attack_percent(enemy)==290);
 g.growth.curse_counts[17]=255;g.growth.talent_ranks[30]=256;
 CHECK(rework_curses::count(17)==256&&rework_curses::attack_percent(enemy)==67940);
}
inline void run_qa49_groups(){qa49_accumulated_attack_damage_and_owner_isolation();}
}
