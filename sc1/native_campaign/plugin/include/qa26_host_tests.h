#pragma once
namespace host_test {
inline constexpr std::size_t qa26_group_count=3;
inline void __cdecl qa26_yamato_dispatch(bw::Bullet* shot){
 auto target=shot->target.unit;CHECK(target);
 rework_fixture::yamato_targets.push_back(target);
 std::int32_t amount=260*256;
 {rework_combat_v5::DamageScope hit(target,nullptr,30,1,amount);}
 target->flingy.hitpoints-=amount;
}
inline void qa26_yamato_blasts_are_bounded_and_do_not_hit_allies(){
 using namespace rework_fixture;qa9_fixture::begin({64});
 auto bc=unit(12,1,100,100),target=unit(37,6,150,100);
 auto a=unit(37,6,155,100),b=unit(37,6,160,100),ally=unit(37,1,170,100);
 std::vector<bw::Unit*> extras;for(int i=0;i<8;i++)extras.push_back(unit(37,6,180+i*4,100));
 auto outside=unit(37,6,500,100);auto shot=bullet(bc,target,30);yamato_targets.clear();
 const auto damage=original_stat({1,14,30})*128u;const auto health=extras.front()->flingy.hitpoints;
 {rework_combat_v5::MissileScope impact(shot,qa26_yamato_dispatch);qa26_yamato_dispatch(shot);}
 CHECK(yamato_targets.size()==3&&yamato_targets[1]==a&&yamato_targets[2]==b);
 U32 hit=0;for(auto enemy:extras){if(enemy->flingy.hitpoints!=health){++hit;CHECK(enemy->flingy.hitpoints==health-int(damage));}}
 CHECK(hit==6&&ally->flingy.hitpoints==256000&&outside->flingy.hitpoints==256000);
 const auto after=extras.front()->flingy.hitpoints;
 {rework_combat_v5::MissileScope impact(shot,qa26_yamato_dispatch);}
 CHECK(extras.front()->flingy.hitpoints==after);qa9_fixture::end();
}
inline void qa26_swarm_sustain_does_not_stack_or_heal_enemies(){
 using namespace rework_fixture;qa9_fixture::begin({103});
 auto friend_unit=unit(0,1,100,100),enemy=unit(0,6,120,100),outside=unit(0,1,900,100);
 const auto maximum=effective_max_hp(friend_unit),heal=U32(std::uint64_t(maximum)*3/100);
 friend_unit->flingy.hitpoints=int(maximum/2);enemy->flingy.hitpoints=outside->flingy.hitpoints=100;
 auto field_unit=unit(202,1,100,100);rework_combat_v5::Persist field{};field.target=rework_combat_v5::identity(field_unit);field.kind=83;field.owner=1;field.x=100;field.y=100;field.remaining=160;field.ticks=160;field.until=1000;
 rework_combat_v5::persistent.push_back(field);rework_combat_v5::persistent.push_back(field);
 pulse(101);CHECK(friend_unit->flingy.hitpoints==int(maximum/2+heal));
 pulse(102);CHECK(friend_unit->flingy.hitpoints==int(maximum/2+heal));
 pulse(125);CHECK(friend_unit->flingy.hitpoints==int(maximum/2+2*heal));
 CHECK(enemy->flingy.hitpoints==100&&outside->flingy.hitpoints==100);qa9_fixture::end();
}
inline void qa26_illusion_blast_and_stasis_slow_keep_owner_and_once_guards(){
 using namespace rework_fixture;qa9_fixture::begin({147});
 auto illusion=unit(65,1,100,100);illusion->flags|=0x40000000u;rework_combat_v5::state(illusion)->materialized=true;
 std::vector<bw::Unit*> enemies;for(int i=0;i<6;i++)enemies.push_back(unit(37,6,120+i*3,100));
 auto ally=unit(0,1,120,110);const auto damage=U32(std::min<std::uint64_t>(150u*256u,(std::uint64_t(effective_max_hp(illusion))+std::uint64_t(effective_max_shields(illusion))*256u)/2u));
 rework_combat_v5::death(illusion);U32 hit=0;for(auto enemy:enemies)if(enemy->flingy.hitpoints!=256000){++hit;CHECK(enemy->flingy.hitpoints==256000-int(damage));}
 CHECK(hit==6&&ally->flingy.hitpoints==256000);const auto after=enemies.front()->flingy.hitpoints;
 rework_combat_v5::death(illusion);CHECK(enemies.front()->flingy.hitpoints==after);qa9_fixture::end();
 qa9_fixture::begin({149});auto released=unit(37,6,100,100),close_enemy=unit(37,6,120,100),distant_enemy=unit(37,6,500,100);ally=unit(0,1,120,110);
 auto s=rework_combat_v5::state(released);s->stasis_owner=1;s->stasis_before=80;released->stasis_timer=0;
 pulse(101);CHECK(rework_combat_v5::state(close_enemy)->slow_percent==50&&rework_combat_v5::state(close_enemy)->slow_until==173);
 CHECK(rework_combat_v5::state(distant_enemy)->slow_until==0&&rework_combat_v5::state(ally)->slow_until==0);qa9_fixture::end();
}
inline void run_qa26_groups(){qa26_yamato_blasts_are_bounded_and_do_not_hit_allies();qa26_swarm_sustain_does_not_stack_or_heal_enemies();qa26_illusion_blast_and_stasis_slow_keep_owner_and_once_guards();}
}
