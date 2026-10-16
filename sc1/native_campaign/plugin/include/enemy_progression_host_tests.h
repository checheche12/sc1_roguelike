#pragma once
namespace host_test {
namespace enemy_progression_tests {
namespace ep=enemy_progression;
inline void begin(){rework_wave_tests::begin(101);ep::reset();game.frame_count=0;ep::step(true,false,false);}
inline void to(U32 second){while(ep::second()<second){game.frame_count+=24;ep::step(true,false,false);}}
inline void six_exact_technology_boundaries(){
 begin();to(359);for(U32 id=0;id<61;id++)CHECK(!rework_upgrade_storage::level(4,id));
 to(360);for(U32 id=0;id<16;id++)CHECK(rework_upgrade_storage::level(4,id)==1);
 CHECK(rework_upgrade_storage::level(4,27)==1&&!rework_upgrade_storage::level(4,29));CHECK(ep::researched(4,0)&&!ep::researched(4,5));
 to(479);CHECK(!rework_upgrade_storage::level(4,29));to(480);CHECK(rework_upgrade_storage::level(4,29)==1&&rework_upgrade_storage::level(4,26)==1&&ep::researched(4,5));
 to(599);CHECK(rework_upgrade_storage::level(4,0)==1&&!ep::researched(4,19));to(600);CHECK(rework_upgrade_storage::level(4,0)==2&&ep::researched(4,19));
 to(719);CHECK(!rework_upgrade_storage::level(4,43));to(720);CHECK(rework_upgrade_storage::level(4,43)==1&&ep::researched(4,7));
 to(839);CHECK(rework_upgrade_storage::level(4,15)==2&&!ep::researched(4,22));to(840);CHECK(rework_upgrade_storage::level(4,15)==3&&ep::researched(4,22));
 to(959);CHECK(!rework_upgrade_storage::level(4,28)&&!ep::researched(4,15));to(960);CHECK(rework_upgrade_storage::level(4,28)==1&&rework_upgrade_storage::level(4,53)==1&&ep::researched(4,15));
 std::array<bool,61> seen{};for(const auto& row:ep::upgrades){CHECK(row.minute>=6&&row.minute<=16&&!(row.minute%2)&&row.id>=16&&row.id<61&&!seen[row.id]);seen[row.id]=true;CHECK(rework_upgrade_storage::level(4,row.id)==1);}
 CHECK(std::count(seen.begin(),seen.end(),true)==34);for(U32 id:{18u,45u,46u,48u,50u,55u,56u,57u,58u,59u,60u})CHECK(!rework_upgrade_storage::level(4,id));
 std::array<bool,44> techs{};for(const auto& row:ep::technologies){CHECK(!techs[row.id]);techs[row.id]=true;CHECK(ep::researched(4,row.id));}
 to(1200);CHECK(rework_upgrade_storage::level(4,0)==3&&rework_upgrade_storage::level(4,28)==1);
}
inline void owner_isolation_and_original_levels(){
 begin();const U32 player=player_owner();game.alliances[player][2]=game.alliances[2][player]=1;game.starting_player_types[3]=3;game.starting_player_types[7]=7;
 game.upgrade_level_sc[4][0]=5;game.upgrade_level_sc[4][27]=2;game.tech_level_sc[4][19]=1;to(960);
 CHECK(rework_upgrade_storage::level(4,0)==5&&rework_upgrade_storage::level(4,27)==2&&ep::researched(4,19));
 for(U32 owner:{player,2u,3u,7u,8u,11u}){for(U32 id=0;id<61;id++)CHECK(!rework_upgrade_storage::level(owner,id));for(U32 id=0;id<44;id++)CHECK(!ep::researched(owner,id));}
 game.alliances[player][2]=game.alliances[2][player]=0;to(961);CHECK(rework_upgrade_storage::level(2,0)==3&&ep::researched(2,15));
}
inline void extended_storage_bounds_and_real_native_layout(){
 begin();std::array<U8,61*12> upgrades{};std::array<U8,44*12> techs{};std::array<samase::ExtendedArray,3> arrays{};
 arrays[0]={upgrades.data(),upgrades.data()+upgrades.size(),0,0};arrays[2]={techs.data(),techs.data()+techs.size(),0,0};g.extended=arrays.data();g.extended_count=3;
 upgrades[4]=4;game.upgrade_level_sc[4][0]=0;to(960);CHECK(upgrades[4]==4&&game.upgrade_level_sc[4][0]==4);
 CHECK(upgrades[53*12+4]==1&&techs[32*12+4]==1&&game.tech_level_bw[4][8]==1);CHECK(!upgrades[0*12+player_owner()]&&!techs[19*12+player_owner()]);
 arrays[0].end=arrays[0].pointer+4;arrays[2].end=arrays[2].pointer+4;
 game.upgrade_level_sc[4][16]=0;game.tech_level_sc[4][19]=0;ep::upgrade(4,16,1);ep::research(4,19);CHECK(!game.upgrade_level_sc[4][16]&&!game.tech_level_sc[4][19]);
 CHECK(!ep::tech_slot(12,0)&&!ep::tech_slot(4,44));g.extended_count=1;CHECK(!ep::tech_slot(4,19));g.extended=nullptr;g.extended_count=0;
}
inline void clock_pauses_selection_goal_and_session_reset(){
 begin();to(359);const auto before=ep::active_ticks;
 for(U32 i=0;i<500;i++){game.frame_count+=24;ep::step(true,true,false);}CHECK(ep::active_ticks==before&&!rework_upgrade_storage::level(4,0));
 for(U32 i=0;i<100;i++){game.frame_count+=24;ep::step(false,false,false);}CHECK(ep::active_ticks==before);
 game.frame_count+=24;ep::step(true,false,true);CHECK(ep::active_ticks==before);to(360);CHECK(rework_upgrade_storage::level(4,0)==1);
 ep::reset();CHECK(!ep::initialized&&!ep::second());ep::step(true,false,false);CHECK(!ep::second());
}
inline void native_speed_flags_flingy_and_late_births(){
 begin();auto ling=add(37,4,1800,1600);ling->flingy.movement_type=2;
 auto overlord=add(42,4,1800,1600);overlord->flingy.movement_type=0;overlord->flingy.top_speed=213;
 auto ally=add(42,player_owner(),1200,1200);ally->flingy.top_speed=213;
 to(360);CHECK((ling->flags&0x10000000u)&&!(ling->flags&0x20000000u));CHECK(overlord->flingy.top_speed==213);
 to(480);CHECK((overlord->flags&0x10000000u)&&overlord->flingy.top_speed==853&&ally->flingy.top_speed==213);
 auto late=add(42,4,1800,1600);late->flingy.movement_type=0;ep::refresh_motion(late);CHECK(late->flingy.top_speed==853);
 for(U32 i=0;i<50;i++){ep::refresh_motion(overlord);apply_unit_motion();CHECK(overlord->flingy.top_speed==853);}
 overlord->ensnare_timer=1;ep::refresh_motion(overlord);CHECK(overlord->flingy.top_speed==213);overlord->ensnare_timer=0;
 to(960);CHECK(ling->flags&0x20000000u);auto ultra=add(39,4,2000,1600);ultra->flingy.movement_type=2;ep::refresh_motion(ultra);CHECK(ultra->flags&0x10000000u);
}
inline void __cdecl give(bw::Unit* u,U32 owner){u->player=U8(owner);}
inline void overlord_escort_speed_and_identity_restoration(){
 begin();auto original=add(42,4,1800,1600);original->flingy.top_speed=213;
 auto escort=add(42,4,1800,1700);escort->flingy.top_speed=213;rework_waves::finish_created(escort,0,100,100,1800,1700);
 apply_unit_motion();CHECK(escort->flingy.top_speed==1707&&original->flingy.top_speed==213);for(U32 i=0;i<20;i++)apply_unit_motion();CHECK(escort->flingy.top_speed==1707&&existing_track(escort)->base_speed==213);
 escort->ensnare_timer=1;apply_unit_motion();CHECK(escort->flingy.top_speed==853);escort->ensnare_timer=0;
 owner_give_hook(escort,player_owner(),give);CHECK(escort->flingy.top_speed==213&&!rework_curses::marked(escort));apply_unit_motion();CHECK(escort->flingy.top_speed==213);
 auto recycled=add(42,4,1700,1600);recycled->flingy.top_speed=213;rework_waves::finish_created(recycled,0,100,100,1700,1600);++recycled->minor_unique_index;CHECK(ep::escort_base(recycled,213)==213);
}
inline bw::SpriteScr visible{};
inline bw::Unit* target(U32 id=0,int x=1940,int y=1600,U32 hp=160){auto t=add(id,player_owner(),x,y,int(hp*256));t->flags=1;visible.visibility_mask=0xff;t->flingy.sprite=&visible;return t;}
inline bw::Unit* caster(U32 id){auto u=add(id,4,1800,1600);u->energy=200*256;u->flags=1;rework_waves::finish_created(u,0,100,100,1800,1600);auto v=rework_curses::identity(u);u->flags=(u->flags&~0x04009000u)|v->saved_flags;v->appearance_until=0;game.frame_count=96;u->order=14;return u;}
inline U32 __cdecl deny(bw::Unit*,U32,bw::Unit*,U32,U32,U32,std::uint16_t*){return 0;}
inline void research_energy_visibility_native_guards(){
 begin();auto u=caster(67);target();target(0,1960,1620);const auto v=rework_curses::identity(u);rework_waves::auto_spell(u,*v);CHECK(u->order==14);
 ep::research(4,19);game.frame_count+=24;u->energy=74*256;rework_waves::auto_spell(u,*v);CHECK(u->order==14);u->energy=75*256;
 visible.visibility_mask=0;game.frame_count+=24;rework_waves::auto_spell(u,*v);CHECK(u->order==14);visible.visibility_mask=0xff;
 rework_waves::native_tech_target=deny;game.frame_count+=24;rework_waves::auto_spell(u,*v);CHECK(u->order==14&&!v->last_spell);rework_waves::native_tech_target=allow_tech;
 u->lockdown_timer=1;game.frame_count+=24;rework_waves::auto_spell(u,*v);CHECK(u->order==14);u->lockdown_timer=0;
 game.frame_count+=24;rework_waves::auto_spell(u,*v);CHECK(u->order==142&&u->energy==75*256&&v->last_spell==game.frame_count);
 auto original=add(67,4,1800,1600);original->energy=200*256;const auto unchanged=*original;rework_waves::auto_spell(original,*v);CHECK(std::memcmp(original,&unchanged,sizeof(unchanged))==0);
 u->player=U8(player_owner());u->order=14;game.frame_count+=200;rework_waves::auto_spell(u,*v);CHECK(u->order==14);
}
inline void all_spell_roles_use_real_order_numbers(){
 struct Case{U32 unit,tech,order,victim;};
 for(const auto& c:std::array<Case,10>{{{67,19,142,0},{9,7,143,0},{71,22,147,0},{12,8,113,0},{1,1,115,5},{45,13,121,0},{46,15,144,0},{63,29,180,9},{60,25,177,0},{34,30,181,9}}}){
  begin();ep::research(4,c.tech);auto u=caster(c.unit);auto a=target(c.victim,1940,1600,200);target(c.victim,1960,1620);target(c.victim,1940,1640);a->energy=100*256;
  rework_waves::auto_spell(u,*rework_curses::identity(u));CHECK(u->order==c.order&&u->order_target.unit==a&&u->energy==200*256);
 }
 begin();ep::research(4,17);auto queen=caster(45);target();target(0,1960,1620);target(0,1940,1640);rework_waves::auto_spell(queen,*rework_curses::identity(queen));CHECK(queen->order==146);
}
inline void area_reservations_friendly_fire_and_protected_targets(){
 begin();ep::research(4,19);auto a=caster(67),b=caster(67);auto first=target();target(0,1960,1620);
 auto friend_unit=add(37,4,1940,1600);friend_unit->flags=1;rework_waves::auto_spell(a,*rework_curses::identity(a));CHECK(a->order==14);
 friend_unit->flingy.hitpoints=0;game.frame_count+=24;rework_waves::auto_spell(a,*rework_curses::identity(a));CHECK(a->order==142);
 rework_waves::auto_spell(b,*rework_curses::identity(b));CHECK(b->order==14);
 game.frame_count+=144;rework_waves::auto_spell(b,*rework_curses::identity(b));CHECK(b->order==142);
 b->order=14;game.frame_count+=200;g.objective_units.emplace_back(first,first->minor_unique_index);rework_waves::auto_spell(b,*rework_curses::identity(b));CHECK(b->order==14);g.objective_units.clear();
 rework_waves::reset_spells();CHECK(!rework_waves::spell_cursor);first->flags|=0x300u;CHECK(!rework_waves::spell_candidate(a,first,false));first->detection_status|=1u<<a->player;CHECK(rework_waves::spell_candidate(a,first,false));
}
inline bw::Unit* ally(U32 id,int x=1900,int y=1600){auto u=add(id,4,x,y);u->flags=1;rework_waves::finish_created(u,0,100,100,x,y);auto v=rework_curses::identity(u);u->flags=(u->flags&~0x04009000u)|v->saved_flags;v->appearance_until=0;return u;}
inline void support_spells_consume_and_native_target_denial(){
 begin();ep::research(4,14);auto defiler=caster(46);auto front=ally(37);target();rework_waves::auto_spell(defiler,*rework_curses::identity(defiler));CHECK(defiler->order==119&&defiler->order_target.unit==front);
 begin();ep::research(4,16);defiler=caster(46);defiler->energy=50*256;auto original=add(37,4,1870,1600);original->flags=1;auto food=ally(37);rework_waves::auto_spell(defiler,*rework_curses::identity(defiler));CHECK(defiler->order==145&&defiler->order_target.unit==food&&original->flingy.hitpoints>0);
 begin();ep::research(4,6);auto vessel=caster(9);front=ally(5);target();rework_waves::auto_spell(vessel,*rework_curses::identity(vessel));CHECK(vessel->order==141&&vessel->order_target.unit==front);
 begin();ep::research(4,24);auto medic=caster(34);front=ally(5);front->lockdown_timer=10;rework_waves::auto_spell(medic,*rework_curses::identity(medic));CHECK(medic->order==176&&medic->order_target.unit==front);
 begin();ep::research(4,2);vessel=caster(9);auto templar=target(67);templar->energy=100*256;rework_waves::auto_spell(vessel,*rework_curses::identity(vessel));CHECK(vessel->order==122);
 begin();ep::research(4,27);auto archon=caster(63);target(12,1940,1600,250);rework_waves::native_tech_target=deny;rework_waves::auto_spell(archon,*rework_curses::identity(archon));CHECK(archon->order==14);rework_waves::native_tech_target=allow_tech;
}
}
inline constexpr std::size_t enemy_progression_group_count=10;
inline void run_enemy_progression_groups(){using namespace enemy_progression_tests;six_exact_technology_boundaries();owner_isolation_and_original_levels();extended_storage_bounds_and_real_native_layout();clock_pauses_selection_goal_and_session_reset();native_speed_flags_flingy_and_late_births();overlord_escort_speed_and_identity_restoration();research_energy_visibility_native_guards();all_spell_roles_use_real_order_numbers();area_reservations_friendly_fire_and_protected_targets();support_spells_consume_and_native_target_denial();}
}
