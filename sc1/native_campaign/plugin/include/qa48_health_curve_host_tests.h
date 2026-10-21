#pragma once
namespace host_test {
inline constexpr std::size_t qa48_group_count=1;
inline void qa48_five_health_stacks_spawn_204hp_mutalisk(){
 qa33_fixture::begin(5);write_entry(&dat[0][8],43,120u*256u);
 auto muta=qa33_fixture::wave(43);
 CHECK(rework_curses::hp_percent(muta)==170);
 CHECK(muta->flingy.hitpoints==204*256&&effective_max_hp(muta)==204u*256u);
 CHECK(rework_curses::attack_percent(muta)==100&&rework_curses::speed_percent(muta)==100);
 auto original=add(43,muta->player,2000,1000),friendly=add(43,player_owner(),100,100);
 CHECK(effective_max_hp(original)==120u*256u&&effective_max_hp(friendly)==120u*256u);
 CHECK(max_hp_cache::publish(true));U32 hp=0,shields=0;
 CHECK(max_hp_cache::read_display(muta,hp,shields)&&hp==204u*256u);
 auto shielded=qa33_fixture::wave(66);const U32 base=original_stat({0,7,66});
 CHECK(rework_curses::shield_percent(shielded)==170&&effective_max_shields(shielded)==base*170/100);
}
inline void run_qa48_groups(){qa48_five_health_stacks_spawn_204hp_mutalisk();}
}
