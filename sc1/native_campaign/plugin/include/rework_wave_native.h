#pragma once
// Native adapter: include after spawn/mark_wave_unit/origin_safe and targeting.
// All state is keyed by native slot + unique byte + owner + type, never type alone.
// Include rework_wave_profiles.generated.h at global scope before this header.
namespace rework_curses {
struct Identity {U8 unique=0,owner=12;std::uint16_t type=228;U32 wave=0,slot=0,hp=100,attack=100,appearance_until=0,saved_flags=0,last_spell=0,last_scan=0;U32 cast_order=0,cast_begin=0,cast_fired=0;bool cast_launched=false;bool elite=false,barrier=false;};
inline std::vector<Identity> identities;
inline const bw::Unit* body(const bw::Unit* u) noexcept {
 if(!valid_unit(u))return nullptr;U32 main=228;
 if(u->unit_id==73 || u->unit_id==85){bw::Unit* parent=nullptr;std::memcpy(&parent,u->unit_specific.bytes,sizeof(parent));const U32 expected=u->unit_id==73?72u:83u;return valid_unit(parent) && parent->unit_id==expected && parent->player==u->player?parent:nullptr;}
 switch(u->unit_id){case 4:main=3;break;case 6:main=5;break;case 24:main=23;break;case 26:main=25;break;case 31:main=30;break;default:return u;}
 const auto parent=u->subunit;return valid_unit(parent) && parent->unit_id==main && parent->subunit==u && parent->player==u->player?parent:nullptr;
}
inline Identity* identity(const bw::Unit* u) noexcept {
 u=body(u);
 if(!valid_unit(u) || identities.size()!=g.units_count)return nullptr;
 auto& v=identities[static_cast<std::size_t>(u-g.units)];
 return v.wave && v.unique==u->minor_unique_index && v.owner==u->player && v.type==u->unit_id?&v:nullptr;
}
inline bool marked(const bw::Unit* u) noexcept {u=body(u);auto v=identity(u);auto t=existing_track(u);return g.active && g.applied && g.mission && !g.mission->no_production && v && t && t->spawned && is_enemy(u->player) && !(u->flags&0x40000000u);}
inline U32 count(U32 slot) noexcept {return slot==25?0u:sc1_native::curse_scaling::count(g.growth,slot);}
inline U32 hp_percent(const bw::Unit* u) noexcept {if(!marked(u))return 100;const auto v=identity(u);U32 p=sc1_native::curse_scaling::scale(100,sc1_native::curse_scaling::bonus(count(18),10));if(v->elite)p=sc1_native::curse_scaling::scale(p,60);return U32(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(p)*v->hp/100));}
inline U32 attack_percent(const bw::Unit* u) noexcept {if(!marked(u))return 100;const auto v=identity(u);U32 p=sc1_native::curse_scaling::scale(100,sc1_native::curse_scaling::bonus(count(17),10));if(v->elite)p=sc1_native::curse_scaling::scale(p,25);return U32(std::min<std::uint64_t>(0xffffffffu,std::uint64_t(p)*v->attack/100));}
inline U32 speed_fortieths(const bw::Unit* u) noexcept {return marked(u)?40u+4u*std::min(3u,count(19)):40u;}
inline U32 lifesteal_percent(const bw::Unit* u) noexcept {return marked(u)?12u*std::min(2u,count(23)):0u;}
inline bool barrier(const bw::Unit* u) noexcept {const auto v=identity(u);const auto t=existing_track(u);return marked(u) && v && v->barrier && t && g.game()->elapsed_seconds-t->spawn_second<20;}
inline bool appearing(const bw::Unit* u) noexcept {const auto v=identity(u);return marked(u) && v && v->appearance_until!=0;}
inline void forget(bw::Unit* u) noexcept {
 if(!valid_unit(u) || identities.size()!=g.units_count)return;
 auto& v=identities[static_cast<std::size_t>(u-g.units)];if(v.wave && v.unique==u->minor_unique_index && v.type==u->unit_id){if(v.appearance_until)u->flags=(u->flags&~0x04009000u)|v.saved_flags;v={};}
}
inline void before_give(bw::Unit* u,U32 next_owner) noexcept {if(valid_unit(u) && u->player!=next_owner)forget(u);}
inline void transformed(bw::Unit* u,U32 old_id) noexcept {
 if(!valid_unit(u) || identities.size()!=g.units_count)return;auto& v=identities[static_cast<std::size_t>(u-g.units)];
 const bool tank=(old_id==5 && u->unit_id==30) || (old_id==30 && u->unit_id==5);
 const bool duke=(old_id==23 && u->unit_id==25) || (old_id==25 && u->unit_id==23);
 if(v.wave && v.owner==u->player && v.unique==u->minor_unique_index && v.type==old_id && (tank || duke || old_id==u->unit_id))v.type=u->unit_id;
 else if(v.wave && v.owner==u->player && v.unique==u->minor_unique_index && v.type==old_id){if(v.appearance_until)u->flags=(u->flags&~0x04009000u)|v.saved_flags;v={};}
}
}
namespace rework_waves {
void reset_spells() noexcept;
namespace policy=sc1_native::rework_wave;
inline policy::Timeline timeline;
inline const policy::Profile* current=nullptr;
inline U32 pending_kind=0,pending_spawn_at=0,raid_next=0,support_kills=0,support_last=0,reserve_at=0,unit_ordinal=0;
inline bool support_due=false,spawned_pending=false;
inline U32 last_main_budget=0,reserve_supply=0;
inline std::array<U32,2> selected{{0,0}};
inline const sc1_native::campaign_wave_config::Origin* primary=nullptr;
inline bw::Unit* raid_worker=nullptr;inline U8 raid_worker_unique=0;inline U32 raid_worker_frame=0;inline bool raid_worker_sampled=false;
inline void reset() noexcept {reset_spells();if(g.units && rework_curses::identities.size()==g.units_count)for(std::size_t i=0;i<g.units_count;i++)rework_curses::forget(&g.units[i]);timeline.reset();current=nullptr;pending_kind=pending_spawn_at=raid_next=support_kills=support_last=reserve_at=unit_ordinal=0;last_main_budget=reserve_supply=0;support_due=spawned_pending=false;selected={0,0};primary=nullptr;raid_worker=nullptr;raid_worker_sampled=false;raid_worker_frame=0;raid_worker_unique=0;rework_curses::identities.clear();}
inline bool enabled() noexcept {return g.mission && !g.mission->no_production && (current=policy::profile(g.mission->mission_id)) && current->enabled;}
inline U32 opening_second() noexcept {
 if(!current)return 0;
 return current->mission==404?std::max(current->first,timeline.ready_at+current->base_grace):current->first;
}
inline bool usable_home() {
 bool hq=false,worker=false;
 living_units([&](bw::Unit* u){if(u->player!=player_owner() || u->flingy.hitpoints<=0 || !u->order || !(u->flags&1u) || (u->flags&(4u|0x40000040u)))return;
  if(wave_targeting::headquarters(u->unit_id))hq=true;if(wave_targeting::worker(u->unit_id))worker=true;});
 return hq && worker;
}
inline U32 capabilities() {
 U32 value=0;for(const auto& origin:sc1_native::campaign_wave_config::kOrigins)if(g.mission && origin.mission_id==g.mission->mission_id && origin_safe(origin)){
  const bool only_air=sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(origin.unit1)) && sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(origin.unit2));if(!only_air)value|=policy::GroundPath;}
 living_units([&](bw::Unit* u){if(u->player!=player_owner() || !(u->flags&1u) || u->flingy.hitpoints<=0)return;
  const auto flags=original_stat({0,22,u->unit_id});auto gun=effect_body(u);if(valid_unit(gun)&&valid_unit(gun->subunit)&&gun->subunit->subunit==gun)gun=gun->subunit;
  if((u->flags&1u)&&!(u->flags&(0x40u|0x40000000u))&&(owner_stat(u->player,{0,19,u->unit_id})<130||(valid_unit(gun)&&owner_stat(u->player,{0,19,gun->unit_id})<130)))value|=policy::AntiAir;if(flags&0x8000u)value|=policy::Detection;});
 return value;
}
inline bool major_original_assault() {
 wave_targeting::refresh();if(!wave_targeting::target.valid)return false;U32 count=0;
 living_units([&](bw::Unit* u){const auto t=existing_track(u);if(!regular_enemy(u) || (t && t->spawned))return;const auto p=u->flingy.position;
  const auto victim=u->order_target.unit;const bool attacking=valid_unit(victim)&&victim->player==player_owner()&&victim->flingy.hitpoints>0&&multi_target::attack_order(u->order);
  if(wave_targeting::distance(p.x,p.y,wave_targeting::target.x,wave_targeting::target.y)<=768ll*768 && (u->ground_cooldown || u->air_cooldown || attacking))++count;});
 return count>=12;
}
inline const sc1_native::campaign_wave_config::Origin* choose_origin(bool ground,bool alternate=false) {
 const sc1_native::campaign_wave_config::Origin* found=nullptr;
 for(U32 pass=0;pass<2;pass++)for(const auto& o:sc1_native::campaign_wave_config::kOrigins){
  if(!origin_safe(o) || (!pass && !origin_has_live_base(o)))continue;
  const bool only_air=sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(o.unit1)) && sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(o.unit2));
  if(ground && only_air)continue;if(alternate && &o==primary)continue;found=&o;return found;}
 return found;
}
inline bool live_hero(U32 slot) {
 bool found=false;living_units([&](bw::Unit* u){const auto v=rework_curses::identity(u);if(v && rework_curses::marked(u) && v->slot==slot && (original_stat({0,22,u->unit_id})&0x40u))found=true;});return found;
}
inline void select_specials() {
 selected={0,0};const auto caps=capabilities();U32 n=0;const auto start=timeline.cursor;
 std::array<bool,std::size(policy::kRosters)> allowed{};
 for(std::size_t i=0;i<std::size(policy::kRosters);i++){
  const auto& r=policy::kRosters[i];if(r.slot==policy::Reserve || !rework_curses::count(r.slot))continue;
  const bool hero=live_hero(r.slot);allowed[i]=timeline.eligible(*current,r,caps)&&!hero;
  log_event("V5 special curse eligibility: slot=%u eligible=%u unlock=%u departure=%u caps=%u required=%u live_hero=%u last_delivered=%u",r.slot,allowed[i]?1u:0u,timeline.unlock_second(*current,r),timeline.departure_at,caps,r.requirements,hero?1u:0u,timeline.delivered[r.slot-24]);
 }
 // Give a newly unlocked/previously capacity-blocked curse its first delivery
 // before repeating other compositions. Keep the two-roster and cadence limits.
 for(U32 pass=0;pass<2 && n<2;pass++)for(U32 step=0;step<std::size(policy::kRosters) && n<2;step++){
  const auto idx=(start+step)%std::size(policy::kRosters);const auto& r=policy::kRosters[idx];
  if(!allowed[idx] || (timeline.delivered[r.slot-24]!=0)!=(pass==1))continue;
  selected[n++]=r.slot;timeline.cursor=static_cast<U32>((idx+1)%std::size(policy::kRosters));}
 log_event("V5 special curse selection: slots=%u,%u normal_ordinal=%u",selected[0],selected[1],timeline.ordinal+1);
}
inline bool clear_cell(int x,int y,bool worker_raid=false) {
 bool clear=true;U32 alive=0;living_units([&](bw::Unit* u){++alive;const auto p=u->flingy.position;const auto dx=std::int64_t(x)-p.x,dy=std::int64_t(y)-p.y;
  if(dx*dx+dy*dy<40ll*40)clear=false;if(!worker_raid && wave_protected_unit(u) && dx*dx+dy*dy<512ll*512)clear=false;});return clear && alive<1550;
}
inline U32 live_supply() {U32 supply=0;living_units([&](bw::Unit* u){auto t=existing_track(u);if(t && t->spawned && is_enemy(u->player))supply+=std::max(1u,original_stat({0,46,u->unit_id}));});return supply;}
inline const sc1_native::campaign_wave_config::Origin* raid_owner() noexcept {
 for(const auto& origin:sc1_native::campaign_wave_config::kOrigins)if(g.mission&&origin.mission_id==g.mission->mission_id&&is_enemy(origin.owner))return &origin;return nullptr;
}
inline bw::Unit* mining_worker_target() noexcept {
 const U32 frame=g.game()->frame_count;
 if(raid_worker_sampled&&raid_worker_frame==frame&&(!raid_worker||(wave_targeting::usable(raid_worker)&&raid_worker->minor_unique_index==raid_worker_unique&&wave_targeting::worker(raid_worker->unit_id))))return raid_worker;
 bw::Unit* best=nullptr;std::int64_t score=std::numeric_limits<std::int64_t>::max();U32 best_rank=0,best_workers=0;
 living_units([&](bw::Unit* worker){if(!wave_targeting::usable(worker)||!wave_targeting::worker(worker->unit_id)||!(worker->flags&1u))return;
  const auto p=worker->flingy.position;std::int64_t nearest=std::numeric_limits<std::int64_t>::max();U32 neighbors=0;bool economy=false;
  living_units([&](bw::Unit* other){const auto q=other->flingy.position;const auto d=wave_targeting::distance(p.x,p.y,q.x,q.y);
   if(other->unit_id>=176&&other->unit_id<=178&&other->flingy.hitpoints>0)nearest=std::min(nearest,d);
   if(!wave_targeting::usable(other))return;
   if(wave_targeting::worker(other->unit_id)&&d<=256ll*256)++neighbors;
   if(wave_targeting::headquarters(other->unit_id)&&(other->flags&1u)&&!(other->flags&4u)&&d<=512ll*512)economy=true;
  });
  const U32 rank=(economy?2u:0u)+(nearest<=384ll*384?1u:0u);
  if(!best||rank>best_rank||(rank==best_rank&&(neighbors>best_workers||(neighbors==best_workers&&nearest<score)))){best=worker;score=nearest;best_rank=rank;best_workers=neighbors;}
 });raid_worker=best;raid_worker_unique=best?best->minor_unique_index:0;raid_worker_frame=frame;raid_worker_sampled=true;return best;
}
inline bw::Unit* finish_created(bw::Unit* u,U32 slot,U32 hp,U32 attack,int x,int y) {
 mark_wave_unit(u);if(rework_curses::identities.size()!=g.units_count)rework_curses::identities.assign(g.units_count,{});
 auto& v=rework_curses::identities[static_cast<std::size_t>(u-g.units)];v={};v.unique=u->minor_unique_index;v.owner=u->player;v.type=u->unit_id;v.wave=g.current_wave_id;v.slot=slot;v.hp=hp;v.attack=attack;
 v.elite=unit_ordinal<std::min(3u,rework_curses::count(21));const U32 barrier=rework_curses::count(22);v.barrier=barrier && unit_ordinal<4+2*(std::min(3u,barrier)-1);
 constexpr U32 arrival_flags=0x04009000u;v.saved_flags=u->flags&arrival_flags;v.appearance_until=timeline.second()+4;
 if(g.order)g.order(u,23,x,y,nullptr,228);u->flags|=arrival_flags;
 if(u->flingy.hitpoints>0 && g.set_hp)g.set_hp(u,static_cast<std::int32_t>(std::min<std::uint64_t>(0x7fffffffu,std::uint64_t(original_stat({0,8,u->unit_id}))*rework_curses::hp_percent(u)/100u)));
 if(original_stat({0,22,u->unit_id})&0x200000u)u->energy=std::max<std::uint16_t>(u->energy,200*256);
 ground_pulse(x,y,u->player,367);role_marker(u,0,-24,379);max_hp_cache::publish_unit(u);++unit_ordinal;return u;
}
inline bw::Unit* create(U32 id,U32 slot,U32 hp=100,U32 attack=100,bool alternate=false,U32 required_owner=12) {
 if(slot==policy::Rear)return nullptr;
 if(!enabled() || live_supply()+std::max(1u,original_stat({0,46,id}))>policy::live_supply_cap(g.mission->mission_id))return nullptr;
 // Explicit user exception: only worker-raid Mutalisks appear directly at the
 // mining line. Other waves retain the512px allied clearance at real origins.
 if(slot==policy::Raid&&(id==43 || id==9 || id==42 || id==84)){
  const auto owner=raid_owner();auto worker=mining_worker_target();if(!owner||!worker||(required_owner<12&&owner->owner!=required_owner))return nullptr;const auto center=worker->flingy.position;
  for(int radius=64;radius<=384;radius+=32)for(int dy=-radius;dy<=radius;dy+=32)for(int dx=-radius;dx<=radius;dx+=32){
   if(std::max(std::abs(dx),std::abs(dy))!=radius)continue;const int x=int(center.x)+dx,y=int(center.y)+dy;
   if(x<16||y<16||x>=int(g.mission->width*32)-16||y>=int(g.mission->height*32)-16||!clear_cell(x,y,true))continue;
   OwnerDatScope scope(owner->owner,owner->owner);auto u=spawn(id,x,y,owner->owner);if(u)return finish_created(u,slot,hp,attack,x,y);
  }return nullptr;
 }
 const bool ground=!(original_stat({0,22,id})&4u);auto preferred=choose_origin(ground,alternate);if(!preferred && alternate)preferred=choose_origin(ground);if(!preferred)return nullptr;
 for(U32 pass=0;pass<2;pass++)for(const auto& candidate:sc1_native::campaign_wave_config::kOrigins){
 const auto origin=&candidate;if((pass==0)!=(origin==preferred) || !origin_safe(*origin))continue;
 if(required_owner<12&&origin->owner!=required_owner)continue;
 const bool only_air=sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(origin->unit1)) && sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(origin->unit2));if(ground && only_air)continue;
 for(U32 i=0;i<origin->cell_count;i++){
  const auto p=origin->cells[(i+unit_ordinal)%origin->cell_count];if(!clear_cell(p.x,p.y))continue;
  OwnerDatScope scope(origin->owner,origin->owner);auto u=spawn(id,p.x,p.y,origin->owner);if(!u)continue;
  return finish_created(u,slot,hp,attack,p.x,p.y);
 }}
 return nullptr;
}
inline U32 infantry(U32 race) noexcept {return race==0?37u:race==2?65u:0u;}
inline U32 count_spawn(U32 id,U32 count,U32 slot,U32 hp=100,U32 attack=100,bool alternate=false) {U32 done=0;for(U32 i=0;i<count && i<480;i++){if(!create(id,slot,hp,attack,alternate))break;++done;}return done;}
inline bw::Unit* add_detector(U32 slot=0) {
 bw::Unit* present=nullptr;bw::Unit* leader=nullptr;living_units([&](bw::Unit* u){auto t=existing_track(u);if(t && t->wave_id==g.current_wave_id && wave_targeting::marked(u)){if(wave_targeting::detector(u))present=u;else if(!leader)leader=u;}});
 if(present)return present;
 if(!leader)return nullptr;
 U32 race=primary?primary->race:g.mission->race;
 if(!primary)for(const auto& origin:sc1_native::campaign_wave_config::kOrigins)if(origin.mission_id==g.mission->mission_id&&origin.owner==leader->player){race=origin.race;break;}
 return create(policy::detector(race),slot,100,100,false,leader->player);
}
inline void normal_units(U32 half_supply,U32 slot=0) {
 // Main waves, death support and reserves share this one reduction. Keep the
 // stored main/reserve budgets unscaled to avoid reducing reserves twice.
 half_supply=policy::reduced_amount(half_supply);
 const U32 race=primary?primary->race:g.mission->race;U32 used=0;const bool anti_air=(capabilities()&policy::AntiAir)!=0;
 if(!anti_air&&primary&&sc1_native::wave_progression::air_only_unit(std::uint16_t(primary->unit1))&&sc1_native::wave_progression::air_only_unit(std::uint16_t(primary->unit2)))return;
 const U32 detection_cost=std::max(1u,original_stat({0,46,policy::detector(race)}));
 if(half_supply<=detection_cost)return;
 // Reserve a real cell for detection before the combat units fill an origin.
 // Mixed-owner fallback origins must not strand the detector without a cell.
 auto detection=add_detector(slot);
 if(!detection)detection=create(policy::detector(race),slot,100,100,false,primary?primary->owner:12u);
 if(detection)half_supply-=detection_cost;
 const bool air_only=primary&&sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(primary->unit1))&&sc1_native::wave_progression::air_only_unit(static_cast<std::uint16_t>(primary->unit2));
 for(U32 i=0;i<480 && used<half_supply;i++){
  const auto pick=sc1_native::wave_progression::select(race,air_only,timeline.second(),timeline.ordinal,i,half_supply-used,wave_supply,anti_air);if(!pick.valid)break;
  if(!create(pick.unit_id,slot))break;used+=pick.supply;}
 if(used && !detection)add_detector(slot);
}
inline void roster(const policy::Roster& r) {
 if(!timeline.eligible(*current,r,capabilities()) || live_hero(r.slot))return;
 U32 created=0;
 for(std::size_t i=0;i<r.units.size();i++){
  auto m=r.units[i];if(!m.count)continue;
  if(r.slot==policy::Rear)m.unit=static_cast<std::uint16_t>(infantry(primary->race)),m.count=(timeline.departure_at?timeline.departure_at:timeline.second())>=1200?18:12;
  if(r.slot==policy::Heavy)m.unit=static_cast<std::uint16_t>(primary->race==0?38:primary->race==2?66:3);
  if(r.slot==policy::Flank)m.unit=static_cast<std::uint16_t>(primary->race==0?37:primary->race==2?65:2);
  if(r.slot==policy::Vanguard){if(!i)m.unit=static_cast<std::uint16_t>(primary->race==0?39:primary->race==2?68:5);else m.unit=static_cast<std::uint16_t>(infantry(primary->race));}
  if(r.slot==policy::Catastrophe){if(!i)m.unit=static_cast<std::uint16_t>(primary->race==0?39:primary->race==2?68:12);else m.unit=static_cast<std::uint16_t>(infantry(primary->race));}
  if(sc1_native::wave_progression::air_only_unit(m.unit)&&!(capabilities()&policy::AntiAir))continue;
  if(r.slot==policy::Rear || r.slot==policy::Heavy || r.slot==policy::Flank)m.count=policy::stacked_count(m.count,rework_curses::count(r.slot));
  // All ordinary low-grade reinforcements scale; only the first member of
  // higher-grade special rosters is capped. Ordinary escorts scale;
  // heroes and the explicitly fixed special-unit counts never do.
  if(!m.hero && (i>0 || !r.grade))m.count=policy::scaled_count(m.count,rework_curses::count(16));
  if(!m.hero)m.count=policy::reduced_amount(m.count);
  const bool boosted=r.slot==policy::Hunters?m.unit==38:(r.slot==policy::Vanguard || r.slot==policy::Catastrophe)?i==0:true;
  created+=count_spawn(m.unit,m.count,r.slot,(boosted?r.hp_percent:100)*110u/100u,boosted?r.attack_percent:100,r.slot==policy::Flank);
 }
 if(created)timeline.mark_delivered(r.slot);
 log_event("V5 special curse delivery: slot=%u units=%u live_half_supply=%u cap=%u normal_ordinal=%u",r.slot,created,live_supply(),policy::live_supply_cap(g.mission->mission_id),timeline.ordinal+1);
}
inline void selected_units() {
 for(auto slot:selected)if(slot)for(const auto& r:policy::kRosters)if(r.slot==slot)roster(r);
}
inline void main_wave() {
 last_main_budget=policy::scaled_count(policy::normal_budget(timeline.ordinal,g.mission->mission_id),rework_curses::count(16));
 if(g.mission->mission_id==404){
  // Reserve space for owned curse compositions before normal filler consumes
  // the shared cap. Keep one detector.
  if(primary)create(policy::detector(primary->race),0,100,100,false,primary->owner);
  selected_units();normal_units(last_main_budget);
 }else{normal_units(last_main_budget);selected_units();}
}
inline void note_death(bw::Unit* u,bool direct) noexcept {
 if(!direct || !enabled() || !rework_curses::count(20) || !regular_enemy(u))return;
 const auto t=existing_track(u);if(t && t->spawned)return;
 if(timeline.second()<opening_second() || !timeline.home)return;
 if(++support_kills>=20){support_kills=0;if(!support_last || timeline.second()-support_last>=60)support_due=true;}
}
inline void ammunition(bw::Unit* u) {
 // Stock TrainFighter performs creation, supply bookkeeping, the parent/child
 // links and hiding. Do not manufacture a partially linked hanger ourselves.
 // Pinned bw_dat: carrier counts bytes16/17; currentBuildUnit is the unit
 // member of secondary_order_target. BWAPI CUnit and OpenBW independently
 // document these native roles (references archived beside build evidence).
 if(u->unit_id!=72 && u->unit_id!=83)return;
 const auto inside=u->unit_specific.bytes[16],outside=u->unit_specific.bytes[17];const U32 maximum=u->unit_id==72?8u:5u;
 if(U32(inside)+outside>=maximum)return;
 const U32 fighter=u->unit_id==72?73u:85u;const auto index=std::min(4u,U32(u->current_build_slot));
 if(u->secondary_order!=63 || u->secondary_order_state>=3){
  u->build_queue[index]=static_cast<std::uint16_t>(fighter);u->secondary_order=63;u->secondary_order_state=0;u->secondary_order_wait=0;
 }
 const auto child=u->secondary_order_target.unit;
 if(valid_unit(child) && child->player==u->player && child->unit_id==fighter && !(child->flags&1u))child->remaining_build_time=std::min<std::uint16_t>(child->remaining_build_time,1);
}
#include "enemy_spell_runtime.h"
inline void caster_order(bw::Unit* u,rework_curses::Identity& v) {auto_spell(u,v);}
inline void release_and_orders() {
 std::array<bw::Unit*,spell_search::casters_per_frame> due{};
 living_units([&](bw::Unit* u){
  if(rework_curses::body(u)!=u)return;
  if(rework_curses::identities.size()==g.units_count){const auto& raw=rework_curses::identities[static_cast<std::size_t>(u-g.units)];if(raw.wave && raw.unique==u->minor_unique_index && raw.type==u->unit_id && raw.owner!=u->player)rework_curses::forget(u);}
  auto v=rework_curses::identity(u);if(!v)return;
  if(!is_enemy(u->player)){rework_curses::forget(u);return;}
  ammunition(u);
  if(v->appearance_until && timeline.second()>=v->appearance_until){u->flags=(u->flags&~0x04009000u)|v->saved_flags;v->appearance_until=0;wave_targeting::issue(u);}
  if(v->appearance_until)return;resume_yamato(u,*v);
  if(spell_due(u,*v))for(std::size_t i=0;i<due.size();i++){
   auto other=due[i];auto previous=other?rework_curses::identity(other):nullptr;
   if(!previous||v->last_scan<previous->last_scan||(v->last_scan==previous->last_scan&&u<other)){
    for(std::size_t j=due.size()-1;j>i;j--)due[j]=due[j-1];due[i]=u;break;
   }
  }
  // Lurkers stop only once they reach an actual hostile target; retain native
  // burrow/weapon execution and never rewrite the original map AI.
  if(u->unit_id==103 && !(u->flags&0x10u) && g.order && (!v->last_scan || g.game()->frame_count-v->last_scan>=24)){v->last_scan=g.game()->frame_count;bool close_target=false;living_units([&](bw::Unit* p){if(p->player==player_owner() && wave_targeting::distance(p->flingy.position.x,p->flingy.position.y,u->flingy.position.x,u->flingy.position.y)<192ll*192)close_target=true;});if(close_target)g.order(u,116,0,0,nullptr,228);}
 });
 for(auto u:due)if(u)if(auto v=rework_curses::identity(u))caster_order(u,*v);
}
inline void tick(bool ready,bool blocked,bool goal) {
 if(!enabled() || goal){if(current || timeline.initialized)reset();return;}
 const bool home=usable_home();const bool busy=blocked || g.dialog.open() || major_original_assault();
 timeline.advance(*current,g.game()->frame_count,ready,busy,home);release_and_orders();
 if(!home){pending_kind=pending_spawn_at=raid_next=reserve_at=support_kills=0;last_main_budget=reserve_supply=0;support_due=false;primary=nullptr;return;}
 if(!ready || busy || !home)return;
 if(!raid_next)raid_next=std::max(current->first,timeline.ready_at+current->base_grace);
 if(!pending_kind){
  if(timeline.due(*current)){pending_kind=1;timeline.warn();pending_spawn_at=timeline.departure_at-4;select_specials();}
  else if(support_due && !reserve_at && timeline.second()>=opening_second() && (!support_last || timeline.second()-support_last>=60)){pending_kind=2;timeline.warn();pending_spawn_at=timeline.departure_at-4;support_due=false;support_last=timeline.second();selected={0,0};}
  else if(rework_curses::count(15) && !reserve_at && timeline.second()>=raid_next && (capabilities()&policy::AntiAir)){pending_kind=3;timeline.warn();pending_spawn_at=timeline.departure_at-4;raid_next=timeline.second()+current->interval;selected={0,0};}
  else if(reserve_at && timeline.second()+4>=reserve_at){pending_kind=4;pending_spawn_at=reserve_at-4;timeline.departure_at=reserve_at;reserve_at=0;selected={0,0};}
  if(pending_kind){primary=pending_kind==3?raid_owner():choose_origin(true);if(!primary&&pending_kind!=3)primary=choose_origin(false);if(!primary){pending_kind=0;timeline.finished(*current);return;}spawned_pending=false;unit_ordinal=0;g.wave_spawn_number=0;g.current_wave_id=++g.next_wave_id;log_event("V5 added wave warning kind=%u departure=%u normal_ordinal=%u",pending_kind,timeline.departure_at,timeline.ordinal+1);message(pending_kind==4?"후속 예비대가 모습을 드러냅니다. 모습을 드러낸 후 4초 뒤 출발합니다.":"추가 공세가 20초 뒤 모습을 드러냅니다. 모습을 드러낸 후 4초 뒤 출발합니다.");}
 }
 if(pending_kind && !spawned_pending && timeline.second()>=pending_spawn_at){
  spawned_pending=true;
  if(pending_kind==1)main_wave();
  else if(pending_kind==2)normal_units(18+8*(std::min(3u,rework_curses::count(20))-1));
  else if(pending_kind==3)count_spawn(43,policy::raid_count(rework_curses::count(15),rework_curses::count(16)),15);
  else normal_units(reserve_supply,24);
  if(unit_ordinal)add_detector(pending_kind==3?policy::Raid:pending_kind==4?policy::Reserve:0u);
  log_event("V5 added wave created kind=%u units=%u live_half_supply=%u active_second=%u",pending_kind,unit_ordinal,live_supply(),timeline.second());
 }
 if(pending_kind && timeline.second()>=timeline.departure_at){const auto kind=pending_kind;pending_kind=0;timeline.warning_at=timeline.departure_at=0;if(kind==1){timeline.finished(*current);if(rework_curses::count(24) && timeline.ordinal>=2){reserve_at=timeline.second()+15;reserve_supply=policy::reserve_budget(last_main_budget,rework_curses::count(24));}}primary=nullptr;}
}
inline sc1_native::WaveCountdown countdown(bool ready,bool goal) noexcept {
 if(!ready || goal || !g.mission || g.mission->no_production || !current || !current->enabled)return {};
 if(!timeline.home)return {sc1_native::WaveCountdown::Kind::WaitingForHome,0};
 U32 next=timeline.countdown(*current);if(reserve_at)next=std::min(next,reserve_at>timeline.second()?reserve_at-timeline.second():0u);
 return {sc1_native::WaveCountdown::Kind::Scheduled,next};
}
}
namespace rework_curses {
inline bw::Unit* raid_target(const bw::Unit* u) noexcept {const auto value=identity(u);return value&&value->slot==sc1_native::rework_wave::Raid&&marked(u)?rework_waves::mining_worker_target():nullptr;}
}
