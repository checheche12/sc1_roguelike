#pragma once
namespace host_test {
namespace rework_cargo_tests {
using Adapter=::sc1::sight_cargo::CargoAdapter;
inline std::array<bw::Unit*,12> selection{};
inline std::array<U32,1900> death_calls{},give_calls{};
inline void* __cdecl selected(){return selection.data();}
inline bool transport_id(U32 id){return id==11 || id==42 || id==57 || id==69;}
inline bw::Unit* fresh(U32 id,U32 owner=1){auto u=add(id,owner,600,600,10000);u->flags=1;u->flingy.sprite=reinterpret_cast<void*>(1);return u;}
inline void talent(U32 ordinal){const auto bit=238+ordinal;g.growth.talent_bits[bit/32]|=1u<<(bit%32);}
inline bool blocked_unload=false;
inline U32 unload_calls=0,detach_calls=0;
inline void __cdecl detach(bw::Unit* p,U32 hidden_flag){
 CHECK(hidden_flag==0);++detach_calls;auto carrier=p->related;CHECK(carrier!=nullptr);
 for(U32 i=0;i<8;i++){::sc1::sight_cargo::PackedWindow w{};std::memcpy(w.low.data(),carrier->loaded_units,sizeof(carrier->loaded_units));w.high=carrier->scr_carried_unit_high_bits;
  if(rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(w,i))==p){carrier->loaded_units[i]=0;carrier->scr_carried_unit_high_bits&=~(3u<<(i*2));break;}}
 p->related=nullptr;p->flags&=~0x60u;p->order=2;
}
inline void __cdecl unload_all(bw::Unit* c){++unload_calls;if(blocked_unload)return;for(U32 i=0;i<8;i++){::sc1::sight_cargo::PackedWindow w{};std::memcpy(w.low.data(),c->loaded_units,sizeof(c->loaded_units));w.high=c->scr_carried_unit_high_bits;if(auto p=rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(w,i)))if(p->related==c)detach(p,0);}}
inline void begin(){reset();blocked_unload=false;unload_calls=detach_calls=0;rework_cargo_v5::native_unload_all=unload_all;rework_cargo_v5::native_detach=detach;g.applied=true;g.growth={};g.growth.wire_version=2;rework_cargo_v5::reset();selection={};death_calls={};give_calls={};rework_cargo_v5::selection_source=selected;CHECK(rework_cargo_v5::bind());}
inline auto packed(bw::Unit* c){::sc1::sight_cargo::PackedWindow w{};std::memcpy(w.low.data(),c->loaded_units,sizeof(c->loaded_units));w.high=c->scr_carried_unit_high_bits;return w;}
inline void __cdecl board(bw::Unit* passenger){
 auto carrier=passenger->order_target.unit;if(!valid_unit(carrier) || passenger->player!=carrier->player)return;
 if(carrier->unit_id==42 || carrier->unit_id==57){const auto native_upgrade=g.extended ? g.extended[0].pointer[24*12+carrier->player]:game.upgrade_level_sc[carrier->player][24];if(!native_upgrade)return;}
 const auto w=packed(carrier);U32 used=0,empty=8;for(U32 i=0;i<8;i++){auto p=rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(w,i));if(p)used+=rework_cargo_v5::space(p);else if(empty==8)empty=i;}
 const U32 native_capacity=raw_value(0,48,carrier->unit_id);CHECK(native_capacity<=8);
 if(empty==8 || used+rework_cargo_v5::space(passenger)>native_capacity)return;
 const auto id=rework_cargo_v5::cargo.identity(passenger);carrier->loaded_units[empty]=static_cast<std::uint16_t>(id);carrier->scr_carried_unit_high_bits=static_cast<std::uint16_t>((carrier->scr_carried_unit_high_bits&~(3u<<(empty*2)))|((id>>16)<<(empty*2)));
 passenger->flags|=carrier->unit_id==125 ? 0x60u : 0x40u;passenger->related=carrier;passenger->order=2;
}
inline bw::Unit* enter(bw::Unit* c,U32 id=0){auto p=fresh(id,c->player);p->order=92;p->order_target.unit=c;owner_unit_hook(p,board);return p;}
inline void __cdecl unload(bw::Unit* carrier){
 auto w=packed(carrier);for(U32 i=0;i<8;i++){auto p=rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(w,i));if(!p || p->related!=carrier || !(p->flags&0x40u))continue;p->related=nullptr;p->flags&=~0x40u;carrier->loaded_units[i]=0;break;}
 bool remaining=false;for(auto h:carrier->loaded_units)if(h)remaining=true;if(!remaining)carrier->order=2;
}
inline void __cdecl single_unload(const void* data,U32 length,U32){
 if(!data || (length!=3 && length!=5))return;const auto b=static_cast<const U8*>(data);if(b[0]!=0x29)return;U32 id=0;std::memcpy(&id,b+1,length-1);
 auto p=rework_cargo_v5::cargo.resolve(id);if(!p || !p->related)return;auto c=p->related;const auto window=packed(c);
 for(U32 i=0;i<8;i++)if(::sc1::sight_cargo::unpack_slot(window,i)==id){p->related=nullptr;p->flags&=~0x40u;c->loaded_units[i]=0;return;}
}
inline void __cdecl native_kill(bw::Unit* u){
 ++death_calls[static_cast<std::size_t>(u-units.data())];if(transport_id(u->unit_id) || u->unit_id==125){const auto w=packed(u);for(U32 i=0;i<8;i++)if(auto p=rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(w,i)))owner_kill_hook(p,native_kill);}
 // Any still-linked bunker passengers are killed: ejection must precede this.
 u->flingy.hitpoints=0;u->order=0;u->order_state=1;u->related=nullptr;u->flags&=~0x40u;
}
inline void __cdecl native_give(bw::Unit* u,U32 owner){
 ++give_calls[static_cast<std::size_t>(u-units.data())];if(transport_id(u->unit_id) || u->unit_id==125){const auto w=packed(u);for(U32 i=0;i<8;i++)if(auto p=rework_cargo_v5::cargo.resolve(::sc1::sight_cargo::unpack_slot(w,i)))owner_give_hook(p,owner,native_give);}
 u->player=static_cast<U8>(owner);
}
inline void capacities_and_owner_tech_gate(){
 begin();talent(33);talent(74);talent(115);auto dropship=fresh(11),overlord=fresh(42),shuttle=fresh(69),enemy=fresh(11,6),illusion=fresh(11);illusion->flags|=0x40000000u;
 CHECK(rework_cargo_v5::capacity(dropship)==16 && rework_cargo_v5::capacity(shuttle)==12);CHECK(rework_cargo_v5::capacity(overlord)==8);
 auto denied=enter(overlord);CHECK(!(denied->flags&0x40u));game.upgrade_level_sc[1][24]=1;CHECK(rework_cargo_v5::capacity(overlord)==12);
 CHECK(rework_cargo_v5::capacity(enemy)==8 && rework_cargo_v5::capacity(illusion)==8);
 CHECK(enter(overlord)->flags&0x40u);
}
inline void sixteen_board_full_unload_and_mixed_overflow(){
 begin();talent(33);auto c=fresh(11);for(U32 i=0;i<16;i++)CHECK(enter(c)->flags&0x40u);auto denied=enter(c);CHECK(!(denied->flags&0x40u) && rework_cargo_v5::cargo.count(c)==16);
 auto info=rework_cargo_v5::cargo.page_info(c);CHECK(info.passengers==16 && info.used_space==16 && info.pages==2);U32 unloaded=0;
 while(rework_cargo_v5::cargo.count(c)){c->order=111;owner_unit_hook(c,unload);CHECK(++unloaded<=16);}CHECK(unloaded==16);
 begin();talent(33);c=fresh(11);for(U32 id:{5u,3u,5u,3u,5u})CHECK(enter(c,id)->flags&0x40u);CHECK(rework_cargo_v5::cargo.page_info(c).used_space==16);CHECK(rework_cargo_v5::cargo.page_info(c).pages==3);
 denied=enter(c,3);CHECK(!(denied->flags&0x40u) && rework_cargo_v5::cargo.count(c)==5);
}
inline void command_single_unload_and_generation_safe_pages(){
 begin();talent(33);auto c=fresh(11);std::array<bw::Unit*,16> passengers{};for(auto& p:passengers)p=enter(c);selection[0]=c;
 std::uint64_t token=0;U32 page=0,pages=0,total=0;CHECK(rework_cargo_v5::status(nullptr,&token,&page,&pages,&total));CHECK(total==16 && pages==2 && page==0);CHECK(rework_cargo_v5::toggle(nullptr,token));CHECK(rework_cargo_v5::cargo.page_info(c).page==1);
 // A command naming a passenger outside the visible page still reaches that
 // exact generation through its temporary bounded native window.
 const auto handle=rework_cargo_v5::cargo.identity(passengers[0]);std::array<U8,5> command{{0x29,0,0,0,0}};std::memcpy(command.data()+1,&handle,4);owner_commands_hook(command.data(),5,0,single_unload);
 CHECK(!(passengers[0]->flags&0x40u) && rework_cargo_v5::cargo.count(c)==15);
 auto old=token;++c->minor_unique_index;CHECK(!rework_cargo_v5::toggle(nullptr,old));selection[1]=fresh(0);CHECK(!rework_cargo_v5::status(nullptr,&token,&page,&pages,&total));
}
inline void death_give_exact_once_and_overflow_recovery(){
 begin();talent(33);auto c=fresh(11);for(U32 i=0;i<16;i++)enter(c);c->flingy.hitpoints=0;owner_kill_hook(c,native_kill);CHECK(death_calls[0]==1);for(U32 i=1;i<=16;i++)CHECK(death_calls[i]==1 && units[i].order==0);
 begin();talent(33);c=fresh(11);for(U32 i=0;i<16;i++)enter(c);owner_give_hook(c,2,native_give);CHECK(give_calls[0]==1);for(U32 i=1;i<=16;i++)CHECK(give_calls[i]==1 && units[i].player==2 && units[i].related==c);
 CHECK(rework_cargo_v5::cargo.count(c)==16 && rework_cargo_v5::capacity(c)==8);CHECK(!(enter(c)->flags&0x40u));
 U32 n=0;while(rework_cargo_v5::cargo.count(c)){c->order=111;owner_unit_hook(c,unload);CHECK(++n<=16);}CHECK(n==16);
}
inline void legacy_twelve_and_two_passenger_layouts(){
 begin();GrowthSnapshot s{};s.completed_phase=1;s.talent_bits[137/32]|=1u<<(137%32);CHECK(apply_snapshot(nullptr,s));auto c=fresh(11);
 CHECK(owner_stat(1,{0,48,11})==12 && rework_cargo_v5::capacity(c)==12);for(U32 i=0;i<12;i++)CHECK(enter(c)->flags&0x40u);CHECK(!(enter(c)->flags&0x40u));
 // Both engine handle layouts round-trip at full generation31. This uses the
 // real adapter, never a parallel model of its fixed-size native windows.
 for(std::size_t length:{32u,1701u}){std::vector<bw::Unit> list(length);for(auto& u:list){u.order=2;u.flingy.hitpoints=1000;u.flingy.sprite=reinterpret_cast<void*>(1);u.minor_unique_index=31;}
  Adapter adapter;CHECK(adapter.bind(list.data(),list.size(),+[](const bw::Unit*)->unsigned{return 16;},+[](const bw::Unit*)->unsigned{return 1;}));list[0].unit_id=11;
  const auto id=adapter.identity(&list[1]);CHECK(adapter.resolve(id)==&list[1]);++list[1].minor_unique_index;CHECK(adapter.resolve(id)==nullptr);
 }
}
inline void native_extended_transport_research_gate(){
 begin();talent(74);std::array<U8,61*12> levels{};samase::ExtendedArray array{levels.data(),levels.data()+levels.size(),0,0};g.extended=&array;g.extended_count=1;auto c=fresh(42);levels[24*12+1]=1;game.upgrade_level_sc[1][24]=0;
 CHECK(rework_cargo_v5::capacity(c)==12);for(U32 i=0;i<12;i++)CHECK(enter(c)->flags&0x40u);CHECK(!(enter(c)->flags&0x40u));
 levels[24*12+1]=0;game.upgrade_level_sc[1][24]=1;CHECK(rework_cargo_v5::capacity(c)==8);auto ordinary=fresh(42);CHECK(!(enter(ordinary)->flags&0x40u));
 array.end=array.pointer+24*12+1;CHECK(rework_cargo_v5::capacity(ordinary)==8 && !rework_upgrade_storage::slot(1,24));g.extended=nullptr;g.extended_count=0;
}
inline void bunker_death_preserves_native_ejection(){
 for(U32 owner:{1u,6u})for(U32 passengers:{1u,4u})for(bool lethal:{false,true})for(bool blocked:{false,true}){
  begin();blocked_unload=blocked;auto bunker=fresh(125,owner);std::array<bw::Unit*,4> inside{};
  for(U32 i=0;i<passengers;i++){inside[i]=enter(bunker,i%2 ? 32u : 0u);inside[i]->energy=std::uint16_t((50+i)*256);CHECK((inside[i]->flags&0x60u)==0x60u);}
  CHECK(rework_cargo_v5::cargo.count(bunker)==passengers);
  if(lethal)bunker->flingy.hitpoints=0;
  owner_kill_hook(bunker,native_kill);CHECK(death_calls[0]==1 && bunker->order==0);CHECK(unload_calls==1 && detach_calls==passengers);
  for(U32 i=0;i<passengers;i++){auto p=inside[i];CHECK(death_calls[p-units.data()]==0);CHECK(p->flingy.hitpoints==10000 && p->order!=0);CHECK(!p->related && !(p->flags&0x60u) && p->player==owner);CHECK(p->energy==(50+i)*256);}
  CHECK(count==passengers+1);
 }
}
inline void bunker_give_preserves_native_manifest(){
 begin();auto bunker=fresh(125);for(U32 i=0;i<4;i++)enter(bunker);const auto before=packed(bunker);
 owner_give_hook(bunker,2,native_give);const auto after=packed(bunker);
 CHECK(before.low==after.low && before.high==after.high && give_calls[0]==1);
 for(U32 i=1;i<=4;i++)CHECK(give_calls[i]==1 && units[i].player==2 && units[i].related==bunker && (units[i].flags&0x60u)==0x60u);
 owner_kill_hook(bunker,native_kill);for(U32 i=1;i<=4;i++)CHECK(death_calls[i]==0 && units[i].order!=0 && !units[i].related);
}
}
inline constexpr std::size_t rework_cargo_group_count=8;
inline void run_rework_cargo_groups(){rework_cargo_tests::capacities_and_owner_tech_gate();rework_cargo_tests::sixteen_board_full_unload_and_mixed_overflow();rework_cargo_tests::command_single_unload_and_generation_safe_pages();rework_cargo_tests::death_give_exact_once_and_overflow_recovery();rework_cargo_tests::legacy_twelve_and_two_passenger_layouts();rework_cargo_tests::native_extended_transport_research_gate();rework_cargo_tests::bunker_death_preserves_native_ejection();rework_cargo_tests::bunker_give_preserves_native_manifest();}
}
