// Offline synthetic host only. Includes the real production translation unit.
// Never discovers, opens, launches, or reads a game process or installation.
#include "native_host_fixture.generated.h"
#include "wave_config.generated.h"
#include <stdexcept>
#include <string>
#include <fstream>
namespace host_test {
int checks=0;
#define CHECK(x) do {++checks;if (!(x)) throw std::runtime_error(std::string(__func__)+":"+std::to_string(__LINE__)+": " #x);} while(0)
bw::Game game{};
std::array<bw::Unit,1900> units{};
bw::DatTable dat[3][96]{};
std::size_t dat_counts[3]={64,64,64};
std::array<std::array<std::array<U8,228*4>,64>,3> storage{};
samase::PluginApi api{};
std::size_t count=0;
bw::Unit* active=nullptr,*hidden=nullptr;
std::size_t saved_handle=std::numeric_limits<std::size_t>::max();
bool fail_spawn=false;
std::vector<std::string> printed;
struct Marker{U32 image;int y;};std::vector<Marker> markers;U32 ground_pulses=0;
void* __cdecl lone_sprite(U32 id,int,int,U32){CHECK(id==361 || id==367);++ground_pulses;return nullptr;}
void* __cdecl overlay(void* parent,U32 image,int,int y,U32){markers.push_back({image,y});return parent;}
U32 kills=0,hps=0,orders=0,finishes=0,loaded_calls=0;
bool plugin_init_open=false;
U32 init_calls=0,late_init_calls=0,dat_factory_calls=0,extended_array_calls=0;
U32 dat_getter_calls=0,mutate_calls=0,read_var_calls=0,free_calls=0;
samase::ExtendedArray* provided_extended=nullptr;
std::size_t provided_extended_count=0;
bool require_init(){++init_calls;if(plugin_init_open)return true;++late_init_calls;return false;}
std::vector<U8> chk;
bw::Game* __cdecl get_game(){return &game;}
bw::Unit* __cdecl get_active(){return active;}
bw::Unit* __cdecl get_hidden(){return hidden;}
void __cdecl get_array(bw::Unit** p,std::size_t* n){*p=units.data();*n=units.size();}
bw::DatTable* __cdecl dat0(std::size_t* n){++dat_getter_calls;*n=dat_counts[0];return dat[0];}
bw::DatTable* __cdecl dat1(std::size_t* n){++dat_getter_calls;*n=dat_counts[1];return dat[1];}
bw::DatTable* __cdecl dat2(std::size_t* n){++dat_getter_calls;*n=dat_counts[2];return dat[2];}
GenericFn __cdecl get_dat(U32 t){++dat_factory_calls;if(!require_init())return nullptr;return t<3 ? reinterpret_cast<GenericFn>(t==2 ? dat2 : t ? dat1 : dat0) : nullptr;}
void* __cdecl mutate(U32 t,U32 f){++mutate_calls;return t<2 && f<64 ? &dat[t][f] : nullptr;}
void __cdecl set_hp(bw::Unit* u,std::int32_t hp){++hps;u->flingy.hitpoints=hp;}
void __cdecl kill(bw::Unit* u){++kills;u->flingy.hitpoints=0;u->order=0;}
void __cdecl order(bw::Unit* u,U32 id,U32 x,U32 y,bw::Unit*,U32){++orders;u->order=static_cast<U8>(id);u->order_target.x=static_cast<std::int16_t>(x);u->order_target.y=static_cast<std::int16_t>(y);}
void __cdecl finish(bw::Unit*){++finishes;}
void __cdecl text(const U8* value){printed.emplace_back(reinterpret_cast<const char*>(value));}
U32 __cdecl zero(){return 0;}
void __cdecl read_vars(const std::uint16_t*,std::size_t* out,std::size_t){++read_var_calls;*out=saved_handle;}
std::size_t __cdecl ext(samase::ExtendedArray** p){++extended_array_calls;if(!require_init())return 0;*p=provided_extended;return provided_extended_count;}
U8* __cdecl read_map(const U8*,std::size_t* n){*n=chk.size();if(chk.empty())return nullptr;auto p=new U8[chk.size()];std::memcpy(p,chk.data(),chk.size());return p;}
void __cdecl free_memory(U8* p){++free_calls;delete[] p;}
bw::Unit* add(U32 id,U32 owner,int x,int y,int hp=2560,bool hide=false) {
    if (count>=units.size()) return nullptr;
    auto p=&units[count++];*p={};p->unit_id=static_cast<std::uint16_t>(id);p->player=static_cast<U8>(owner);
    p->minor_unique_index=static_cast<U8>(count);p->order=3;p->flingy.hitpoints=hp;
    p->flingy.position={static_cast<std::int16_t>(x),static_cast<std::int16_t>(y)};
    auto& head=hide ? hidden : active;p->flingy.next=reinterpret_cast<bw::Flingy*>(head);head=p;return p;
}
bw::Unit* __cdecl create(U32 id,int x,int y,U32 owner,const U8* skins){
    CHECK(skins!=nullptr);CHECK(skins[0]==owner);CHECK(skins[1]==owner);
    return fail_spawn ? nullptr : add(id,owner,x,y);
}
void __cdecl original(){++loaded_calls;}
template<auto Fn> GenericFn __cdecl factory(){return require_init() ? reinterpret_cast<GenericFn>(Fn) : nullptr;}
void __cdecl direct_damage(bw::Unit* u,int amount,bw::Unit*,U32,U32){u->flingy.hitpoints-=amount;}
U32 __cdecl no_attack(bw::Unit*,bw::Unit*,U32){return 0;}
U32 __cdecl outside_attack_range(bw::Unit*,bw::Unit*){return 1;}
bw::Bullet* __cdecl no_bullet(U32,int,int,U32,U32,bw::Unit*){return nullptr;}
U32 __cdecl allow_tech(bw::Unit*,U32,bw::Unit*,U32,U32,U32,std::uint16_t*){return 1;}
GenericFn __cdecl get_function(std::uint16_t id){if(!require_init())return nullptr;if(id==static_cast<std::uint16_t>(samase::FuncId::CheckTechTargeting))return reinterpret_cast<GenericFn>(allow_tech);if(id==static_cast<std::uint16_t>(samase::FuncId::UnitSetHp))return reinterpret_cast<GenericFn>(set_hp);if(id==static_cast<std::uint16_t>(samase::FuncId::DamageUnit))return reinterpret_cast<GenericFn>(direct_damage);if(id==static_cast<std::uint16_t>(samase::FuncId::CanAttackUnit))return reinterpret_cast<GenericFn>(no_attack);if(id==static_cast<std::uint16_t>(samase::FuncId::IsOutsideAttackRange))return reinterpret_cast<GenericFn>(outside_attack_range);return nullptr;}
void __cdecl load_vars(const std::uint16_t*,U8* out,std::size_t n){const bool okay=require_init();for(std::size_t i=0;i<n;i++)out[i]=okay ? 2 : 0;}
U32 __cdecl register_units(void (__cdecl*)(GenericFn)){return require_init() ? 1u : 0u;}
U32 __cdecl register_step(GenericFn,U32){return require_init() ? 1u : 0u;}
void __cdecl register_first_file(GenericFn){(void)require_init();}
U32 __cdecl register_save(const U8*,samase::SaveHook,samase::LoadHook,GenericFn){return require_init() ? 1u : 0u;}
U32 raw_value(U32 t,U32 f,U32 id){return read_entry(&dat[t][f],id);}
// Legacy numeric expectations now inspect the appropriate isolated owner view.
U32 value(U32 t,U32 f,U32 id){const U32 owner=(t==0 && f==8 && (id==37 || id==38)) || (t==1 && f==14) ? 6u : 1u;
    if(t==1 && f==16)return owner_stat(owner,{t,f,id});OwnerDatScope scope(owner,owner);return raw_value(t,f,id); }
void reset() {
    abandon_session();g.baseline.clear();std::memset(&game,0,sizeof(game));std::memset(units.data(),0,sizeof(units));std::memset(&storage,0,sizeof(storage));count=0;active=hidden=nullptr;
    CHECK(late_init_calls==0);init_calls=dat_factory_calls=extended_array_calls=0;
    dat_getter_calls=mutate_calls=read_var_calls=free_calls=0;
    provided_extended=nullptr;provided_extended_count=0;
    dat_counts[0]=dat_counts[1]=dat_counts[2]=64;
    markers.clear();ground_pulses=0;kills=hps=orders=finishes=loaded_calls=0;saved_handle=std::numeric_limits<std::size_t>::max();fail_spawn=false;chk.clear();printed.clear();
    api={};api.version=44;api.extended_dat=get_dat;api.mutate_dat=mutate;api.read_vars=read_vars;
    api.extended_arrays=ext;api.free_memory=free_memory;api.add_overlay_iscript=reinterpret_cast<GenericFn>(factory<overlay>);api.create_lone_sprite=reinterpret_cast<GenericFn>(factory<lone_sprite>);
    api.game=factory<get_game>;api.first_active_unit=factory<get_active>;api.first_hidden_unit=factory<get_hidden>;
    api.unit_array_len=factory<get_array>;api.create_unit=factory<create>;api.finish_unit_pre=api.finish_unit_post=factory<finish>;
    api.create_bullet=reinterpret_cast<GenericFn>(factory<no_bullet>);
    api.issue_order=factory<order>;api.print_text=factory<text>;api.read_map_file=factory<read_map>;
    api.is_multiplayer=api.is_replay=factory<zero>;api.get_func=get_function;api.max_func_id=80;
    api.hook_on_first_file_access=reinterpret_cast<GenericFn>(register_first_file);
    api.load_vars=load_vars;api.hook_init_units=register_units;api.hook_step_objects=register_step;api.extend_save=register_save;
    for(U32 t=0;t<3;t++)for(U32 f=0;f<64;f++)dat[t][f]={storage[t][f].data(),4,228};
    const char* stock_paths[]={"../managed_dat/arr/units.dat","../managed_dat/arr/weapons.dat","../support_dat/arr/flingy.dat"};
    for(U32 table=0;table<3;table++){
        std::ifstream file(stock_paths[table],std::ios::binary);CHECK(file.good());file.seekg(0,std::ios::end);const auto n=file.tellg();
        std::vector<U8> data(static_cast<std::size_t>(n));file.seekg(0);file.read(reinterpret_cast<char*>(data.data()),n);
        for(U32 i=0;i<u32(data.data()+12);i++){
            auto d=data.data()+16+i*12;const U32 field=u16(d),width=1u<<u16(d+2),offset=u32(d+4),length=u32(d+8);
            if(field>=64 || length>storage[table][field].size())continue;
            std::memcpy(storage[table][field].data(),data.data()+offset,length);dat[table][field].entry_size=width;dat[table][field].entries=length/width;
        }
    }
    for(const auto& e:expected_stats){dat[e.table][e.field].entry_size=e.width;write_entry(&dat[e.table][e.field],e.id,e.before);}
    plugin_init_open=true;const bool bound=bind_api(&api);plugin_init_open=false;CHECK(bound);
    CHECK(dat_factory_calls==3 && extended_array_calls==1 && late_init_calls==0);
    g.mission=&campaign_config::kMissions[0];g.campaign_index=2;
    g.active=true;g.applied=false;g.hooks_ready=true;g.game_thread=GetCurrentThreadId();g.pumping=false;
    g.dialog.set_callbacks(dialog_callbacks());
    game.campaign_mission=2;game.map_width_tiles=game.map_height_tiles=64;game.elapsed_seconds=180;
    game.starting_player_types[4]=game.starting_player_types[6]=1;game.starting_player_types[1]=2;
}
GrowthSnapshot all(){GrowthSnapshot s{};s.talent_bits[0]=0x1ffff;s.curse_counts[0]=2;s.curse_counts[1]=1;s.curse_counts[2]=1;return s;}
void exact_stats_hp_supply() {
    reset();game.supplies[1].used[1]=14;game.supplies[1].provided[1]=80;
    auto marine=add(0,1,600,800,5120);auto vulture=add(2,1,610,800,10240);
    auto hidden_vulture=add(2,1,620,800,20480,true);auto dead=add(2,1,630,800,0);
    auto raynor=add(19,1,640,800,38400);auto enemy=add(37,4,900,800,4480);
    auto hydra=add(38,6,1000,800,20480);auto neutral=add(37,11,1100,800,4480);
    CHECK(apply_snapshot(nullptr,all()));
    for(const auto& e:expected_stats) {
        U32 expected=e.all_talents;
        if(e.table==0 && e.field==8 && (e.id==37 || e.id==38))expected=(e.before*11+5)/10;
        if(e.table==1 && e.field==14)expected=(e.before*43+39)/40;
        CHECK(value(e.table,e.field,e.id)==expected);
    }
    CHECK(marine->flingy.hitpoints==6400);CHECK(vulture->flingy.hitpoints==6400);
    CHECK(hidden_vulture->flingy.hitpoints==12800);CHECK(dead->flingy.hitpoints==0);
    CHECK(raynor->flingy.hitpoints==38400);CHECK(enemy->flingy.hitpoints==4928);
    CHECK(hydra->flingy.hitpoints==22528);CHECK(neutral->flingy.hitpoints==4480);
    CHECK(game.supplies[1].used[1]==10);CHECK(game.supplies[1].provided[1]==80);
    CHECK(hps==5);CHECK(!apply_snapshot(nullptr,all()));CHECK(game.supplies[1].used[1]==10);
    init_game();for(const auto& e:expected_stats)CHECK(value(e.table,e.field,e.id)==e.before);
    // Model next-map map-specific data loaded between pre-init and init_units.
    write_entry(&dat[0][8],0,777);init_units(original);CHECK(value(0,8,0)==777);CHECK(loaded_calls==1);
}
void validation_atomicity_and_stacks() {
    reset();auto s=all();s.talent_bits[15]=1;CHECK(!apply_snapshot(nullptr,s));CHECK(value(0,8,0)==10240);
    s=all();s.curse_counts[15]=1;CHECK(!apply_snapshot(nullptr,s));CHECK(g.baseline.empty());
    s=all();dat[1][16].entries=4;CHECK(!apply_snapshot(nullptr,s));CHECK(value(0,8,0)==10240);
    reset();s={};s.curse_counts[1]=255;s.curse_counts[2]=255;CHECK(apply_snapshot(nullptr,s));
    CHECK(value(1,14,35)==101);CHECK(value(1,14,38)==202);CHECK(value(0,8,37)==237440);CHECK(value(0,8,38)==542720);
    reset();s={};s.curse_counts[1]=1;CHECK(apply_snapshot(nullptr,s));CHECK(value(1,14,35)==6);CHECK(value(1,14,38)==11);
}
void ui_lifetime() {
    reset();ChoiceOffer o{};o.kind=1;o.count=4;
    for(U32 i=0;i<4;i++)o.candidates[i]=i+1;
    show_offer(nullptr,o);CHECK(g.offer_active);CHECK(g.dialog.pending());CHECK(count==0);CHECK(finishes==0);CHECK(orders==0);CHECK(kills==0);
    show_offer(nullptr,o);CHECK(count==0);CHECK(orders==0);CHECK(kills==0);
    clear_offer(nullptr);CHECK(!g.offer_active);CHECK(!g.dialog.pending());clear_offer(nullptr);CHECK(count==0);CHECK(kills==0);
    // Host create contract requires both skin bytes, including failure path.
    fail_spawn=true;CHECK(spawn(37,1000,1000,6)==nullptr);CHECK(finishes==0);
    fail_spawn=false;CHECK(spawn(37,1000,1000,6)!=nullptr);CHECK(count==1);CHECK(finishes==2);
    CHECK(spawn(37,1000,1000,12)==nullptr);CHECK(count==1);
}
void section(const char* tag,const std::vector<U8>& p) {
    chk.insert(chk.end(),tag,tag+4);U32 n=static_cast<U32>(p.size());auto b=reinterpret_cast<U8*>(&n);
    chk.insert(chk.end(),b,b+4);chk.insert(chk.end(),p.begin(),p.end());
}
void make_chk(const campaign_config::Mission* mission=nullptr) {
    if(!mission)mission=&campaign_config::kMissions[0];
    const auto word=[](U32 v){return std::vector<U8>{static_cast<U8>(v),static_cast<U8>(v>>8)};};
    chk.clear();section("VER ",word(mission->chk_version));auto d=word(mission->width);auto h=word(mission->height);d.insert(d.end(),h.begin(),h.end());section("DIM ",d);
    std::vector<U8> p(12,0);p[mission->owner]=6;section("OWNR",p);p[mission->owner]=static_cast<U8>(mission->race);section("SIDE",p);
    p={1,0,4,0};p.insert(p.end(),mission->marker,mission->marker+std::strlen(mission->marker)+1);section("STR ",p);
}

void fingerprint_and_save_scope() {
    reset();make_chk();CHECK(is_our_chk(chk.data(),chk.size()));
    chk[8]=206;CHECK(!is_our_chk(chk.data(),chk.size()));chk[8]=59;
    CHECK(!is_our_chk(chk.data(),chk.size()-1));chk.back()='x';CHECK(!is_our_chk(chk.data(),chk.size()));
    make_chk();init_units(original);CHECK(g.active);CHECK(g.protocol.state()==1);CHECK(g.protocol.mailbox_words()[19]==0);
    init_game();saved_handle=1;make_chk();init_units(original);CHECK(!g.active);CHECK(!g.protocol.mailbox_words());CHECK(!counter(kReadyCounter));
    reset();game.campaign_mission=1;init_units(original);CHECK(!g.active);CHECK(load_extension(nullptr,0)==1);
    const U8 save[4]={'T','0','1',1};CHECK(load_extension(save,4)==0);
}
void loaded_save_handle_regression() {
    for(auto fresh:{std::size_t(0),std::size_t(0xffffffffu),std::numeric_limits<std::size_t>::max()}) {
        reset();saved_handle=fresh;CHECK(!loaded_save());make_chk();init_units(original);
        CHECK(g.active);CHECK(g.protocol.mailbox_words());CHECK(g.protocol.state()==1);
        CHECK(!counter(kReadyCounter));CHECK(!counter(kAckCounter));
    }
    // Opaque handles are values, never addresses to dereference. Even the
    // deliberately unreadable synthetic handle1 safely means save loading.
    for(auto handle:{std::size_t(1),std::size_t(0x12345678)}) {
        reset();saved_handle=handle;CHECK(loaded_save());make_chk();init_units(original);
        CHECK(!g.active);CHECK(!g.protocol.mailbox_words());CHECK(printed.empty());
    }
}
void original_objectives_reminder() {
    reset();game.player_objectives_string[1]=19;game.leaderboard_type=3;
    game.leaderboard_parameter=0;game.leaderboard_string=24;
    original_objectives_status(&game,false);CHECK(printed.empty());
    g.offer_active=true;original_objectives_status(&game,true);CHECK(printed.empty());
    g.offer_active=false;original_objectives_status(&game,true);CHECK(printed.size()==1);
    CHECK(printed.back().find("레이너 찾기")!=std::string::npos);
    for(int i=0;i<500;i++)original_objectives_status(&game,true);CHECK(printed.size()==1);
    game.player_objectives_string[1]=9;original_objectives_status(&game,true);CHECK(printed.size()==2);
    CHECK(printed.back().find("레이너 생존")!=std::string::npos);
    CHECK(game.player_objectives_string[1]==9);CHECK(game.leaderboard_type==3);
    CHECK(game.leaderboard_parameter==0);CHECK(game.leaderboard_string==24);
}
using Reply=std::array<U32,96>;
Reply reply(U32 status) {
    Reply r{};auto m=g.protocol.mailbox_words();r[0]=(m[32]|1u)+1;r[1]=status;r[2]=m[8];r[11]=m[18];return r;
}
void publish(const Reply& r){auto m=g.protocol.mailbox_words();m[32]=r[0]|1;for(U32 i=1;i<(m[18]==2 ? 96u:32u);i++)m[32+i]=r[i];MemoryBarrier();m[32]=r[0];}
void tick(){++game.frame_count;frame();}
Reply load_reply(U32 phase=3){auto r=reply(1);r[4]=1;r[5]=2;r[6]=3;r[7]=4;r[10]=0x50480000u|(phase<<8)|g.protocol.requested_phase();r[12]=0x1ffff;r[28]=0x10102;return r;}
void mailbox_ui_goal_integration() {
    reset();make_chk();init_units(original);CHECK(g.protocol.state()==1);CHECK(g.protocol.phased());
    auto o=reply(4);o[12]=1;o[14]=4;o[15]=1;o[16]=2;o[17]=3;o[18]=4;o[19]=123;o[23]=1;o[24]=1;
    o[26]=0x50484331;o[27]=1;o[28]=1;o[29]=0;o[30]=3;
    publish(o);tick();CHECK(g.offer_active);CHECK(count==0);CHECK(!counter(kReadyCounter));
    CHECK(submit_dialog_choice(nullptr,2));CHECK(g.protocol.state()==1);CHECK(g.protocol.mailbox_words()[9]==3);CHECK(g.protocol.mailbox_words()[22]==2);CHECK(!g.offer_active);
    CHECK(!submit_dialog_choice(nullptr,2));
    publish(load_reply(1));tick();CHECK(g.protocol.state()==2);CHECK(!counter(kReadyCounter));CHECK(kills==0);CHECK(count==0);CHECK(orders==0);
    CHECK(g.protocol.completed_phase()==1 && dialog_can_resume(nullptr));
    tick();CHECK(g.protocol.ready()); // unfinished Barracks does not request stage2
    game.completed_units_count[111][kOwner]=1;tick();CHECK(g.protocol.state()==1);
    CHECK(g.protocol.mailbox_words()[9]==4 && g.protocol.mailbox_words()[31]==2);
    CHECK(g.protocol.mailbox_words()[19]==g.protocol.mailbox_words()[18] && !dialog_can_resume(nullptr));
    auto hp=value(0,8,0);publish(load_reply(2));protocol_pump(nullptr);
    CHECK(g.protocol.ready() && g.protocol.completed_phase()==2 && dialog_can_resume(nullptr));
    CHECK(!counter(kReadyCounter));CHECK(value(0,8,0)==hp);
    CHECK(set_counter(kGoalCounter,1));protocol_pump(nullptr);CHECK(g.protocol.ready()); // paused pump never opens next stage
    tick();CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==3);
    publish(load_reply(3));tick();CHECK(g.protocol.state()==3);CHECK(!counter(kReadyCounter));CHECK(!counter(kAckCounter));
    auto r=reply(2);for(int i=0;i<4;i++)r[4+i]=g.protocol.mailbox_words()[10+i];r[8]=1;r[9]=1;publish(r);tick();
    CHECK(g.protocol.state()==4);CHECK(counter(kReadyCounter));CHECK(counter(kGoalCounter));CHECK(counter(kAckCounter));CHECK(value(0,8,0)==hp);
    CHECK(g.protocol.mailbox_words()[31]==3);tick();CHECK(value(0,8,0)==hp);CHECK(g.waves.state().stage==0);
    init_game();CHECK(!g.protocol.mailbox_words());CHECK(value(0,8,0)==10240);
}
void early_goal_orders_remaining_phases() {
    reset();make_chk();init_units(original);CHECK(set_counter(kGoalCounter,1));
    protocol_pump(nullptr);CHECK(g.protocol.state()==1);publish(load_reply(1));protocol_pump(nullptr);
    CHECK(g.protocol.ready() && g.protocol.completed_phase()==1);CHECK(!counter(kReadyCounter));
    for(int i=0;i<10;i++)protocol_pump(nullptr);CHECK(g.protocol.requested_phase()==1);
    tick();CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==2);
    publish(load_reply(2));tick();CHECK(g.protocol.ready());CHECK(!counter(kReadyCounter));
    tick();CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==3);
    publish(load_reply(3));tick();CHECK(g.protocol.state()==3);CHECK(!counter(kReadyCounter));CHECK(!counter(kAckCounter));
    auto r=reply(2);for(int i=0;i<4;i++)r[4+i]=g.protocol.mailbox_words()[10+i];r[8]=1;r[9]=1;publish(r);protocol_pump(nullptr);
    CHECK(!counter(kReadyCounter) && !counter(kAckCounter));tick();
    CHECK(counter(kReadyCounter) && counter(kGoalCounter) && counter(kAckCounter));
    CHECK(g.waves.state().stage==0);
    // Restart restores stage2 once; next goal requests stage3 without rerolling1/2.
    init_game();make_chk();init_units(original);publish(load_reply(2));protocol_pump(nullptr);
    CHECK(g.applied_phase==2 && g.protocol.completed_phase()==2);CHECK(!counter(kReadyCounter));
    CHECK(set_counter(kGoalCounter,1));tick();CHECK(g.protocol.requested_phase()==3);
}
void cumulative_snapshots_preserve_live_ratios_and_supply() {
    reset();game.supplies[1].used[1]=14;
    auto marine=add(0,1,500,500,5120);auto vulture=add(2,1,500,500,10240);
    auto enemy=add(37,4,500,500,4480);auto raynor=add(19,1,500,500,38400);
    GrowthSnapshot s{};s.completed_phase=1;s.talent_bits[0]=(1u<<1)|(1u<<6);
    s.curse_counts[0]=s.curse_counts[1]=s.curse_counts[2]=1;
    CHECK(apply_snapshot(nullptr,s));CHECK(marine->flingy.hitpoints==6400);CHECK(enemy->flingy.hitpoints==4928);
    CHECK(value(1,14,35)==6 && value(1,14,38)==11);const auto cooldown=value(1,16,4);
    marine->flingy.hitpoints=3200;const auto hps_before=hps;
    s.completed_phase=2;s.talent_bits[0]|=1u<<7;s.curse_counts[0]=s.curse_counts[1]=s.curse_counts[2]=2;
    CHECK(apply_snapshot(nullptr,s));CHECK(marine->flingy.hitpoints==3200);CHECK(vulture->flingy.hitpoints==6400);
    CHECK(enemy->flingy.hitpoints==5376);CHECK(value(0,8,37)==10752);CHECK(value(1,16,4)==cooldown);
    CHECK(value(1,14,35)==6 && value(1,14,38)==12);CHECK(game.supplies[1].used[1]==12);CHECK(hps==hps_before+2);
    auto new_vulture=add(2,1,500,500,6400);game.supplies[1].used[1]+=2;
    s.completed_phase=3;s.talent_bits[0]|=1u;s.curse_counts[0]=s.curse_counts[1]=s.curse_counts[2]=3;
    CHECK(apply_snapshot(nullptr,s));CHECK(marine->flingy.hitpoints==3200);CHECK(new_vulture->flingy.hitpoints==6400);
    CHECK(game.supplies[1].used[1]==14);CHECK(enemy->flingy.hitpoints==5824);
    CHECK(value(1,14,35)==7 && value(1,14,38)==13);CHECK(value(1,16,4)==cooldown);CHECK(raynor->flingy.hitpoints==38400);
    CHECK(!apply_snapshot(nullptr,s));CHECK(game.supplies[1].used[1]==14);
    init_game();for(const auto& e:expected_stats)CHECK(value(e.table,e.field,e.id)==e.before);
}
void stage1_growth_keeps_waves_playable() {
    reset();make_chk();init_units(original);publish(load_reply(1));protocol_pump(nullptr);game.elapsed_seconds=300;
    const auto& home=sc1_native::wave_config::kHome;
    add(7,1,(home.left+home.right)/2,(home.top+home.bottom)/2)->flags=1;
    add(106,1,(home.left+home.right)/2,(home.top+home.bottom)/2)->flags=1;
    game.completed_units_count[111][kOwner]=1;tick();
    CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==2 && !counter(kReadyCounter));
    const auto frame_before=game.frame_count,clock_before=rework_waves::timeline.active_ticks;
    for(int i=0;i<200;i++)protocol_pump(nullptr);
    CHECK(game.frame_count==frame_before && rework_waves::timeline.active_ticks==clock_before);
    CHECK(rework_waves::current && rework_waves::timeline.home);
    // Seed a late simulation boundary; the policy suite separately exercises
    // every intervening readiness/pause tick. A pending manager phase must not
    // suspend ordinary play or discard the already applied growth snapshot.
    rework_waves::timeline.active_ticks=(rework_waves::current->first-24)*24;
    for(int i=0;i<600;i++)tick();
    CHECK(g.protocol.state()==1 && !counter(kReadyCounter));
    CHECK(rework_waves::timeline.ordinal==1);
    CHECK(rework_waves::live_supply()==27 && count>2);
}
void paused_protocol_pump_and_reentrancy() {
    reset();make_chk();init_units(original);CHECK(g.protocol.state()==1);
    CHECK(dialog_session_active(nullptr));CHECK(!dialog_can_resume(nullptr));
    publish(load_reply());g.pumping=true;protocol_pump(nullptr);CHECK(!g.applied);CHECK(!counter(kReadyCounter));
    g.pumping=false;const auto thread=g.game_thread.load();g.game_thread=thread+1;
    protocol_pump(nullptr);CHECK(!g.applied);CHECK(!counter(kReadyCounter));g.game_thread=thread;
    const auto frame_before=game.frame_count;const auto ticks_before=g.waves.state().home_ticks;
    protocol_pump(nullptr);CHECK(g.applied);CHECK(!counter(kReadyCounter));CHECK(game.frame_count==frame_before);CHECK(g.waves.state().home_ticks==ticks_before);
    CHECK(dialog_can_resume(nullptr));g.pumping=true;CHECK(!dialog_can_resume(nullptr));g.pumping=false;
    CHECK(set_counter(kGoalCounter,1));protocol_pump(nullptr);CHECK(g.protocol.state()==3);CHECK(!counter(kReadyCounter));
    auto r=reply(2);for(int i=0;i<4;i++)r[4+i]=g.protocol.mailbox_words()[10+i];r[8]=1;r[9]=1;publish(r);
    protocol_pump(nullptr);CHECK(g.protocol.state()==4);CHECK(!counter(kReadyCounter));CHECK(counter(kGoalCounter));CHECK(!counter(kAckCounter));
    CHECK(dialog_can_resume(nullptr));
    CHECK(game.frame_count==frame_before);CHECK(count==0);CHECK(orders==0);CHECK(kills==0);
    tick();CHECK(counter(kReadyCounter) && counter(kAckCounter));
}
void failure_keeps_victory_closed() {
    reset();make_chk();init_units(original);publish(load_reply());protocol_pump(nullptr);
    CHECK(!counter(kReadyCounter));tick();CHECK(counter(kReadyCounter));CHECK(dialog_can_resume(nullptr));
    CHECK(set_counter(kGoalCounter,1));protocol_pump(nullptr);CHECK(g.protocol.state()==3);
    publish(reply(3));protocol_pump(nullptr);
    CHECK(g.protocol.failed());CHECK(!counter(kReadyCounter));CHECK(counter(kGoalCounter));CHECK(!counter(kAckCounter));
    CHECK(!dialog_can_resume(nullptr));CHECK(!g.dialog.pending());CHECK(!g.dialog.waiting());
    CHECK(!submit_dialog_choice(nullptr,1));CHECK(count==0);CHECK(kills==0);CHECK(orders==0);
}
void extended_deaths_fail_closed() {
    reset();std::array<samase::ExtendedArray,11> a{};std::array<U8,228*12*4> data{};
    g.extended=a.data();g.extended_count=a.size();a[10].pointer=data.data();a[10].end=data.data()+data.size();
    CHECK(set_counter(225,1));CHECK(game.deaths[225][11]==1);CHECK(counter(225));
    a[10].end=data.data()+4;CHECK(!set_counter(225,9));CHECK(counter(225));
    CHECK(set_counter(225,0));CHECK(!counter(225));CHECK(game.deaths[225][11]==0);
    CHECK(u32(data.data()+(225*12+11)*4)==1); // Invalid diagnostic table is untouched.
    game.deaths[225][11]=1;CHECK(!counter(225)); // Stale diagnostics cannot grant progress.
    mirror_handshake();CHECK(game.deaths[225][11]==0);
    g.extended=nullptr;g.extended_count=0;
}

void dedicated_counter_mirror_contract() {
    reset();std::array<samase::ExtendedArray,11> arrays{};std::array<U32,261*12> counts{};
    auto start=reinterpret_cast<U8*>(counts.data());const auto end=start+sizeof(counts);
    g.extended=arrays.data();g.extended_count=arrays.size();arrays[10].pointer=start;arrays[10].end=end;
    for(auto id:{kRouteCounter,kMiddleCounter,kReadyCounter,kGoalCounter,kAckCounter}) {
        CHECK(set_counter(id,1));CHECK(counts[id*12+kCounterOwner]==1);
        CHECK(game.deaths[id][kCounterOwner]==1 && counter(id));
        counts[id*12+kCounterOwner]=0;game.deaths[id][kCounterOwner]=0;CHECK(counter(id));
        CHECK(set_counter(id,0));CHECK(!counter(id));
        counts[id*12+kCounterOwner]=1;game.deaths[id][kCounterOwner]=1;CHECK(!counter(id));
        mirror_handshake();CHECK(counts[id*12+kCounterOwner]==0 && game.deaths[id][kCounterOwner]==0);
    }
    counts[222*12+kCounterOwner]=7;game.deaths[222][kCounterOwner]=8;
    counts[kGoalCounter*12+kOwner]=9;game.deaths[kGoalCounter][kOwner]=10;
    CHECK(!set_counter(222,1));CHECK(!counter(222));CHECK(!set_counter(228,1));
    CHECK(counts[222*12+kCounterOwner]==7 && game.deaths[222][kCounterOwner]==8);
    CHECK(set_counter(kGoalCounter,1));
    CHECK(counts[kGoalCounter*12+kOwner]==9 && game.deaths[kGoalCounter][kOwner]==10);
    const auto before_counts=counts;
    const auto invalid_diagnostics_do_not_block=[&] {
        for(auto id:{kReadyCounter,kGoalCounter,kAckCounter}) {
            CHECK(!set_counter(id,3));CHECK(set_counter(id,1));CHECK(counter(id));
            CHECK(game.deaths[id][kCounterOwner]==1);
            CHECK(set_counter(id,0));CHECK(!counter(id));CHECK(game.deaths[id][kCounterOwner]==0);
        }
        CHECK(counts==before_counts);
    };
    arrays[10].end=start+4;invalid_diagnostics_do_not_block();
    arrays[10].end=end;arrays[10].pointer=nullptr;invalid_diagnostics_do_not_block();
    arrays[10].pointer=start;arrays[10].end=nullptr;invalid_diagnostics_do_not_block();
    arrays[10].pointer=start+4;arrays[10].end=start;invalid_diagnostics_do_not_block();
    arrays[10].pointer=start;arrays[10].end=end;
    g.extended_count=10;invalid_diagnostics_do_not_block();
    g.extended_count=arrays.size();g.extended=nullptr;invalid_diagnostics_do_not_block();
    g.extended=arrays.data();g.extended_count=0;invalid_diagnostics_do_not_block();
    g.extended=nullptr;g.extended_count=0;
    CHECK(set_counter(kGoalCounter,0));CHECK(!counter(kGoalCounter));CHECK(counts==before_counts);
}

void extended_completed_phase_milestones() {
    reset();
    std::array<samase::ExtendedArray,11> arrays{};
    // Match the canonical Dat+ unit count. The legacy Game arrays are separate
    // and deliberately stale, as in a real extended-DAT game.
    std::array<U32,261*12> completed{},death_counts{};
    provided_extended=arrays.data();provided_extended_count=arrays.size();
    plugin_init_open=true;CHECK(bind_api(&api));plugin_init_open=false;
    const auto initial_calls=init_calls,acquisitions=extended_array_calls;
    CHECK(acquisitions==2 && late_init_calls==0);
    auto completed_start=reinterpret_cast<U8*>(completed.data());
    auto completed_end=completed_start+sizeof(completed);
    auto death_start=reinterpret_cast<U8*>(death_counts.data());
    // Endpoints become available after init; cached descriptors must be read
    // dynamically, with no later call to the init-only acquisition factory.
    arrays[8].pointer=completed_start;arrays[8].end=completed_end;
    arrays[10].pointer=death_start;arrays[10].end=death_start+sizeof(death_counts);
    make_chk();init_units(original);publish(load_reply(1));protocol_pump(nullptr);
    CHECK(g.protocol.ready() && g.protocol.completed_phase()==1);
    CHECK(game.completed_units_count[111][kOwner]==0);
    const auto stays_in_phase1=[] {
        tick();CHECK(g.protocol.ready());CHECK(g.protocol.requested_phase()==1);
        CHECK(g.protocol.completed_phase()==1);CHECK(!counter(kReadyCounter));
        CHECK(!counter(kGoalCounter));CHECK(!counter(kAckCounter));
    };
    stays_in_phase1(); // No finished Barracks.
    completed[111*12+(kOwner+1)]=1;
    stays_in_phase1(); // Another player's finished Barracks is irrelevant.
    game.completed_units_count[111][kOwner]=1;
    stays_in_phase1(); // Stale legacy1 cannot override valid extended0.
    const auto required_offset=(111*12+kOwner)*sizeof(U32);
    arrays[8].end=completed_start+required_offset+sizeof(U32)-1;
    stays_in_phase1(); // Three readable bytes do not form a u32 counter.
    arrays[8].end=completed_end;arrays[8].pointer=nullptr;
    stays_in_phase1();
    arrays[8].pointer=completed_start;arrays[8].end=nullptr;
    stays_in_phase1();
    arrays[8].pointer=completed_start+4;arrays[8].end=completed_start;
    stays_in_phase1(); // Reversed endpoints fail closed.
    arrays[8].pointer=completed_start;arrays[8].end=completed_end;
    g.extended_count=8;
    stays_in_phase1(); // A declared descriptor list without slot8 is not legacy.
    g.extended_count=arrays.size();
    g.extended=nullptr;
    stays_in_phase1(); // Positive descriptor count with null list also fails closed.
    g.extended=arrays.data();
    g.extended_count=0;
    stays_in_phase1(); // Nonnull list with zero advertised entries is invalid.
    g.extended_count=arrays.size();
    game.completed_units_count[111][kOwner]=0;
    completed[111*12+kOwner]=1;
    const auto frame_before=game.frame_count;
    protocol_pump(nullptr);
    CHECK(game.frame_count==frame_before && g.protocol.requested_phase()==1);
    // A callback on the wrong thread must neither consume nor request phases.
    const auto owner_thread=g.game_thread.load();g.game_thread=owner_thread+1;
    tick();CHECK(g.protocol.requested_phase()==1);g.game_thread=owner_thread;
    tick();CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==2);
    CHECK(g.protocol.mailbox_words()[9]==4 && g.protocol.mailbox_words()[31]==2);
    CHECK(game.completed_units_count[111][kOwner]==0);
    publish(load_reply(2));protocol_pump(nullptr);
    CHECK(g.protocol.ready() && g.protocol.completed_phase()==2);
    CHECK(!counter(kReadyCounter) && !counter(kAckCounter));
    // Model original CHK SetSwitch(goal, Set) with both diagnostic tables stale.
    game.switches[campaign_config::kGoalSwitch/32]|=1u<<(campaign_config::kGoalSwitch%32);
    CHECK(game.deaths[kGoalCounter][kCounterOwner]==0);
    protocol_pump(nullptr);CHECK(g.protocol.ready());
    tick();CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==3);
    publish(load_reply(3));protocol_pump(nullptr);
    CHECK(g.protocol.state()==3 && !counter(kReadyCounter) && counter(kGoalCounter));
    CHECK(!counter(kAckCounter)); // Original Victory still awaits durable ACK.
    auto ack=reply(2);for(int i=0;i<4;i++)ack[4+i]=g.protocol.mailbox_words()[10+i];
    ack[8]=1;ack[9]=1;publish(ack);protocol_pump(nullptr);
    CHECK(g.protocol.state()==4 && !counter(kReadyCounter) && !counter(kAckCounter));tick();
    CHECK(counter(kReadyCounter) && counter(kGoalCounter) && counter(kAckCounter));
    for(auto id:{kReadyCounter,kGoalCounter,kAckCounter}) {
        CHECK(death_counts[id*12+kCounterOwner]==1);
        CHECK(game.deaths[id][kCounterOwner]==1);
    }
    CHECK(init_calls==initial_calls && extended_array_calls==acquisitions && late_init_calls==0);
    init_game();CHECK(!g.protocol.mailbox_words());
    g.extended=nullptr;g.extended_count=0;provided_extended=nullptr;provided_extended_count=0;
}
void original_goal_completed_counts_and_ack_mirror() {
    reset();std::array<samase::ExtendedArray,11> arrays{};
    std::array<U32,261*12> completed{},total{},death_counts{};
    provided_extended=arrays.data();provided_extended_count=arrays.size();
    plugin_init_open=true;CHECK(bind_api(&api));plugin_init_open=false;
    const auto acquisitions=extended_array_calls,initial_calls=init_calls;
    auto completed_start=reinterpret_cast<U8*>(completed.data());
    const auto completed_end=completed_start+sizeof(completed);
    arrays[7].pointer=reinterpret_cast<U8*>(total.data());
    arrays[7].end=arrays[7].pointer+sizeof(total);
    arrays[8].pointer=completed_start;arrays[8].end=completed_end;
    arrays[10].pointer=reinterpret_cast<U8*>(death_counts.data());
    arrays[10].end=arrays[10].pointer+sizeof(death_counts);
    make_chk();init_units(original);publish(load_reply(2));protocol_pump(nullptr);
    CHECK(g.protocol.ready() && g.protocol.completed_phase()==2);
    const auto gate=[] {return counter(kRouteCounter) && counter(kReadyCounter) && counter(kGoalCounter) && counter(kAckCounter);};
    const auto stays_before_goal=[&] {
        tick();CHECK(g.protocol.ready() && g.protocol.completed_phase()==2);
        CHECK(g.protocol.requested_phase()==1); // Highest snapshot restored by initial LOAD.
        CHECK(!counter(kGoalCounter));CHECK(!gate());
        CHECK(death_counts[kGoalCounter*12+kCounterOwner]==0);
        CHECK(game.deaths[kGoalCounter][kCounterOwner]==0);
    };
    // Command AtLeast uses completed units. Total/live units and the stale
    // legacy Game counts cannot substitute for the authoritative Dat+ array8.
    for(auto id:{0u,111u,19u}) {
        total[id*12+kOwner]=17;
        game.completed_units_count[id][kOwner]=17;
        completed[id*12+(kOwner+1)]=17;
    }
    stays_before_goal(); // Another owner's completed units are irrelevant.
    completed[0*12+kOwner]=9;completed[111*12+kOwner]=1;completed[19*12+kOwner]=1;
    stays_before_goal();
    completed[0*12+kOwner]=17;completed[19*12+kOwner]=0;
    stays_before_goal(); // Raynor is absent, even with >10 Marines.
    completed[19*12+kOwner]=1;completed[111*12+kOwner]=0;
    stays_before_goal(); // An unfinished Barracks exists only in total[].
    completed[111*12+kOwner]=1;
    const auto needed=(111*12+kOwner+1)*sizeof(U32);
    arrays[8].end=completed_start+needed-1;stays_before_goal();
    arrays[8].end=completed_end;arrays[8].pointer=nullptr;stays_before_goal();
    arrays[8].pointer=completed_start;arrays[8].end=nullptr;stays_before_goal();
    arrays[8].pointer=completed_start+4;arrays[8].end=completed_start;stays_before_goal();
    arrays[8].pointer=completed_start;arrays[8].end=completed_end;
    g.extended_count=8;stays_before_goal();
    g.extended_count=arrays.size();g.extended=nullptr;stays_before_goal();
    g.extended=arrays.data();g.extended_count=0;stays_before_goal();
    g.extended_count=arrays.size();
    // Paused UI callbacks may exchange protocol messages, but cannot evaluate
    // world milestones or advance the wave/frame clocks.
    const auto frame_before=game.frame_count,home_before=g.waves.state().home_ticks;
    for(int i=0;i<12;++i)protocol_pump(nullptr);
    CHECK(game.frame_count==frame_before && g.waves.state().home_ticks==home_before);
    CHECK(g.protocol.ready() && !counter(kGoalCounter));
    const auto owner_thread=g.game_thread.load();g.game_thread=owner_thread+1;
    tick();CHECK(g.protocol.ready() && !counter(kGoalCounter));g.game_thread=owner_thread;
    for(auto id:{0u,111u,19u})game.completed_units_count[id][kOwner]=0;
    // Exact live failure: extended completed17/1/1, both goal counters zero,
    // stock trigger never emitted goal. Native frame must request phase3 once.
    CHECK(completed[0*12+kOwner]==17 && completed[111*12+kOwner]==1 && completed[19*12+kOwner]==1);
    tick();CHECK(g.protocol.state()==1 && g.protocol.requested_phase()==3);
    CHECK(g.protocol.mailbox_words()[9]==4 && g.protocol.mailbox_words()[31]==3);
    CHECK(death_counts[kGoalCounter*12+kCounterOwner]==1 && game.deaths[kGoalCounter][kCounterOwner]==1);
    CHECK(!gate());
    const auto request=g.protocol.mailbox_words()[8];tick();CHECK(g.protocol.mailbox_words()[8]==request);
    publish(load_reply(3));protocol_pump(nullptr);
    CHECK(g.protocol.state()==3 && g.protocol.completed_phase()==3);
    CHECK(!gate());
    CHECK(death_counts[kGoalCounter*12+kCounterOwner]==1 && game.deaths[kGoalCounter][kCounterOwner]==1);
    CHECK(death_counts[kReadyCounter*12+kCounterOwner]==0 && game.deaths[kReadyCounter][kCounterOwner]==0);
    CHECK(death_counts[kAckCounter*12+kCounterOwner]==0 && game.deaths[kAckCounter][kCounterOwner]==0);
    auto ack=reply(2);for(int i=0;i<4;i++)ack[4+i]=g.protocol.mailbox_words()[10+i];
    ack[8]=1;ack[9]=1;publish(ack);protocol_pump(nullptr);
    CHECK(g.protocol.state()==4 && !gate());tick();CHECK(gate());
    CHECK(init_calls==initial_calls && extended_array_calls==acquisitions && late_init_calls==0);
    init_game();CHECK(!g.protocol.mailbox_words());
    g.extended=nullptr;g.extended_count=0;provided_extended=nullptr;provided_extended_count=0;
}
void wave_host_integration() {
    reset();g.applied=true;g.growth.wire_version=2;const auto& h=sc1_native::wave_config::kHome;
    add(7,1,(h.left+h.right)/2,(h.top+h.bottom)/2)->flags=1;add(106,1,(h.left+h.right)/2,(h.top+h.bottom)/2)->flags=1;
    for(U32 f=1;f<2000;f++){game.frame_count=f;rework_waves::tick(false,false,false);}
    CHECK(count==2 && rework_waves::timeline.active_ticks==0);
    CHECK(rework_waves::current && rework_waves::timeline.home);rework_waves::timeline.active_ticks=(rework_waves::current->first-24)*24;
    for(U32 f=2000;f<2600;f++){game.frame_count=f;rework_waves::tick(true,false,false);}
    CHECK(rework_waves::live_supply()==27 && count>2);CHECK(rework_waves::timeline.ordinal==1);CHECK(orders>0 && orders<=count*2);
    const auto n=count;
    for(U32 f=2600;f<5000;f++){game.frame_count=f;rework_waves::tick(true,false,true);}
    CHECK(count==n && rework_waves::countdown(true,true).kind==sc1_native::WaveCountdown::Kind::Hidden);
    const auto& rect=sc1_native::wave_config::kOrigins[0].bounds;
    auto p5=add(37,4,rect.left,rect.top);p5->order=3;wave_attack(nullptr,6,&rect,1000,1000);CHECK(p5->order==3);
    const auto live_before=added_supply();auto hero=add(23,4,rect.left,rect.top);track_unit(hero)->spawned=true;
    CHECK(!regular_enemy(hero));CHECK(added_supply()==live_before+std::max(1u,original_stat({0,46,23})));
    hero->player=static_cast<U8>(player_owner());CHECK(added_supply()==live_before);
    hero->player=4;hero->flags|=0x40000000u;CHECK(added_supply()==live_before);
}
void api_lifecycle_boundaries() {
    reset();const auto init_count=init_calls;
    CHECK(init_count==25 && !plugin_init_open);
    // The registration object is not a runtime API. Invalidating it after bind
    // models that boundary, while cached direct callbacks remain executable.
    api={};make_chk();init_units(original);
    CHECK(g.active && g.api_version==44 && read_var_calls==1 && free_calls==1);
    CHECK(dat_factory_calls==3 && extended_array_calls==1 && late_init_calls==0);
    auto s=all();s.completed_phase=1;CHECK(apply_snapshot(nullptr,s));
    const auto first_mutations=mutate_calls;CHECK(first_mutations>0 && dat_getter_calls>0);
    s.completed_phase=2;s.curse_counts[1]=2;CHECK(apply_snapshot(nullptr,s));
    s.completed_phase=3;s.curse_counts[2]=2;CHECK(apply_snapshot(nullptr,s));
    CHECK(g.applied_phase==3 && mutate_calls>first_mutations);
    const auto before_restore=dat_getter_calls;init_game();
    CHECK(dat_getter_calls>before_restore && g.baseline.empty());
    for(const auto& e:expected_stats)CHECK(value(e.table,e.field,e.id)==e.before);
    CHECK(init_calls==init_count && late_init_calls==0);
    // Restarts still use the cached reader and callbacks, not a fresh factory.
    init_units(original);CHECK(g.active && g.protocol.state()==1);
    CHECK(init_calls==init_count && read_var_calls==2 && free_calls==2);
    auto saved=g.dat_getters[0];g.dat_getters[0]=nullptr;
    CHECK(!apply_snapshot(nullptr,all()));CHECK(g.baseline.empty());g.dat_getters[0]=saved;
    CHECK(table_for({3,8,0},false)==nullptr);
    CHECK(late_init_calls==0);
}
// Public API44 mutate_dat returns one DatTable descriptor. Its descriptor may
// differ from the read getter's descriptor; its data is not the descriptor.
bw::DatTable detached_dat[2][64]{};
std::array<std::array<std::array<U8,228*4>,64>,2> detached_storage{};
bool detached_ready[2][64]{};
int mutation_fault=0;
void* __cdecl mutate_contract(U32 t,U32 f) {
    ++mutate_calls;
    if(t>=2 || f>=64 || mutation_fault==1)return nullptr;
    auto& copy=detached_dat[t][f];
    if(!detached_ready[t][f]) {
        copy=dat[t][f];
        std::memcpy(detached_storage[t][f].data(),copy.data,std::size_t(copy.entries)*copy.entry_size);
        copy.data=detached_storage[t][f].data();dat[t][f].data=copy.data;detached_ready[t][f]=true;
    }
    if(mutation_fault==2)copy.entry_size=3;
    if(mutation_fault==3)copy.entries=0;
    if(mutation_fault==4)copy.data=nullptr;
    return &copy;
}
void dat_mutation_contract_and_diagnostics() {
    reset();std::memset(detached_ready,0,sizeof(detached_ready));mutation_fault=0;g.mutate_dat=mutate_contract;
    CHECK(apply_snapshot(nullptr,all()));CHECK(g.apply_failure==nullptr);
    CHECK(&detached_dat[0][8]!=&dat[0][8]);CHECK(value(0,8,0)==12800);
    CHECK(value(1,14,35)==6);CHECK(value(1,14,38)==11);
    init_game();for(const auto& e:expected_stats)CHECK(value(e.table,e.field,e.id)==e.before);
    const char* reasons[]={"mutate_rejected","entry_width","entry_bounds","data_null"};
    for(int fault=1;fault<=4;++fault) {
        reset();std::memset(detached_ready,0,sizeof(detached_ready));mutation_fault=fault;g.mutate_dat=mutate_contract;
        CHECK(!apply_snapshot(nullptr,all()));CHECK(!g.applied && g.baseline.empty());
        CHECK(g.apply_failure && std::strcmp(g.apply_failure,reasons[fault-1])==0);
        for(const auto& e:expected_stats)CHECK(value(e.table,e.field,e.id)==e.before);
    }
    reset();std::array<samase::ExtendedArray,11> arrays{};std::array<U8,228*12*4> counters{};
    provided_extended=arrays.data();provided_extended_count=arrays.size();
    plugin_init_open=true;CHECK(bind_api(&api));plugin_init_open=false;
    const auto acquisitions=extended_array_calls;
    // Descriptor storage is acquired during init; its endpoints may be filled
    // later. The runtime must observe those endpoints without reacquisition.
    arrays[10].pointer=counters.data();arrays[10].end=counters.data()+4;
    CHECK(apply_snapshot(nullptr,all()));CHECK(g.applied && !g.apply_failure);
    CHECK(set_counter(kReadyCounter,1));CHECK(counter(kReadyCounter));
    arrays[10].end=counters.data()+counters.size();mirror_handshake();
    CHECK(u32(counters.data()+(kReadyCounter*12+kCounterOwner)*4)==1);
    CHECK(set_counter(kReadyCounter,1));CHECK(counter(kReadyCounter));CHECK(game.deaths[kReadyCounter][kCounterOwner]==1);
    CHECK(extended_array_calls==acquisitions && late_init_calls==0);
    g.extended=nullptr;g.extended_count=0;provided_extended=nullptr;provided_extended_count=0;
}
void real_managed_dat_assets() {
    reset();std::array<std::vector<U8>,2> assets;
    const char* paths[]={"../managed_dat/arr/units.dat","../managed_dat/arr/weapons.dat"};
    for(U32 t=0;t<2;++t) {
        std::ifstream file(paths[t],std::ios::binary);CHECK(file.good());
        file.seekg(0,std::ios::end);const auto size=file.tellg();CHECK(size>0 && size<100000);
        assets[t].resize(static_cast<std::size_t>(size));file.seekg(0);file.read(reinterpret_cast<char*>(assets[t].data()),size);CHECK(file.good());
        const auto& bytes=assets[t];CHECK(bytes.size()>=16);CHECK(u32(bytes.data())==0x2b746144);
        CHECK(u16(bytes.data()+4)==1);CHECK(u32(bytes.data()+8)==(t==0 ? 228u : 130u));
        const U32 fields=u32(bytes.data()+12);CHECK(fields==(t==0 ? 55u : 24u));
        std::memset(dat[t],0,sizeof(dat[t]));dat_counts[t]=0;
        for(U32 i=0;i<fields;++i) {
            const auto desc=bytes.data()+16+i*12;
            const auto id=u16(desc),flags=u16(desc+2);const auto offset=u32(desc+4),length=u32(desc+8);
            CHECK(id<96 && flags<3 && offset+length<=bytes.size());
            const U32 width=1u<<flags;CHECK(length%width==0);
            dat[t][id]={assets[t].data()+offset,width,length/width};
            dat_counts[t]=(std::max)(dat_counts[t],std::size_t(id)+1);
        }
    }
    const auto before=assets;
    for(const auto& e:expected_stats)CHECK(value(e.table,e.field,e.id)==e.before);
    GrowthSnapshot s=all();s.completed_phase=1;CHECK(apply_snapshot(nullptr,s));
    CHECK(value(0,8,0)==12800 && value(0,8,37)==9856);CHECK(value(1,14,35)==6);
    s.completed_phase=2;s.curse_counts[2]=2;CHECK(apply_snapshot(nullptr,s));CHECK(value(0,8,37)==10752);
    s.completed_phase=3;s.curse_counts[1]=3;CHECK(apply_snapshot(nullptr,s));CHECK(value(1,14,35)==7);
    CHECK(!apply_snapshot(nullptr,s));CHECK(late_init_calls==0);
    // Entire files, including requirement offsets/buffer and every unrelated
    // stat, must return byte-for-byte to their actual generated baselines.
    init_game();CHECK(assets==before);CHECK(g.baseline.empty());
    for(U32 t=0;t<2;++t)for(U32 f=0;f<64;++f)dat[t][f]={storage[t][f].data(),4,228};
}
}
#include "all_campaign_host_tests.h"
#include "extended_effect_host_tests.h"
#include "wave_timer_host_tests.h"
#include "multi_target_host_tests.h"
#include "effect_audit_lifecycle_host_tests.h"
#include "effect_audit_projectile_host_tests.h"
#include "effect_audit_curses_host_tests.h"
#include "movement_effects_host_tests.h"
#include "combat_effects_host_tests.h"
#include "max_hp_host_tests.h"
#include "max_hp_engine_host_tests.h"
#include "samase_status_ui_host_tests.h"
#include "samase_weapon_ui_host_tests.h"
#include "samase_armor_ui_host_tests.h"
#include "trampoline_unwind_host_tests.h"
#include "wave_targeting_host_tests.h"
#include "rework_wave_host_tests.h"
#include "enemy_progression_host_tests.h"
#include "enemy_performance_host_tests.h"
#include "targeting_bridge_host_tests.h"
#include "rework_cargo_v5_host_tests.h"
#include "rework_carrier_v5_host_tests.h"
#include "rework_economy_host_tests.h"
#include "rework_binding_host_tests.h"
#include "rework_lighting_v5_host_tests.h"
#include "rework_combat_v5_host_tests.h"
#include "rework_economy_ui_host_tests.h"
#include "rework_shield_ui_v5_host_tests.h"
#include "wave_progression_host_tests.h"
#include "talent_rank_host_tests.h"
#include "talent_power_host_tests.h"
int main() {
    using namespace host_test;
    try {
        char perf_only[8]{};if(GetEnvironmentVariableA("SC1_ENEMY_PERF_ONLY",perf_only,sizeof(perf_only))){run_enemy_performance_groups();return 0;}
        exact_stats_hp_supply();validation_atomicity_and_stacks();ui_lifetime();fingerprint_and_save_scope();
        loaded_save_handle_regression();original_objectives_reminder();
        mailbox_ui_goal_integration();early_goal_orders_remaining_phases();cumulative_snapshots_preserve_live_ratios_and_supply();stage1_growth_keeps_waves_playable();paused_protocol_pump_and_reentrancy();failure_keeps_victory_closed();extended_deaths_fail_closed();dedicated_counter_mirror_contract();extended_completed_phase_milestones();original_goal_completed_counts_and_ack_mirror();wave_host_integration();api_lifecycle_boundaries();dat_mutation_contract_and_diagnostics();real_managed_dat_assets();
        run_all_campaign_groups();run_extended_effect_groups();run_wave_timer_groups();run_multi_target_groups();run_effect_audit_lifecycle_groups();run_effect_audit_projectile_groups();run_effect_audit_curses_regression_groups();
        run_movement_effect_groups();
        run_combat_effects_groups();run_max_hp_groups();run_max_hp_engine_groups();
        run_samase_status_ui_groups();
        run_samase_weapon_ui_groups();
        run_samase_armor_ui_groups();
        run_trampoline_unwind_groups();
        run_wave_targeting_groups();
        run_rework_wave_groups();
        run_enemy_progression_groups();
        run_enemy_performance_groups();
        run_targeting_bridge_groups();
        run_rework_cargo_groups();
        run_rework_carrier_groups();
        run_rework_economy_groups();
        run_rework_binding_groups();
        run_rework_lighting_v5_groups();
        run_rework_combat_v5_groups();
        run_rework_economy_ui_groups();
        run_rework_shield_ui_v5_groups();
        run_wave_progression_groups();
        run_talent_rank_groups();
        run_talent_power_groups();
        abandon_session();g.baseline.clear();g.game=nullptr;
        CHECK(late_init_calls==0);
        std::printf("PASS native host integration: %zu groups, %d checks; game process never accessed.\n",87u+talent_power_group_count+std::size(combat_audit::cases)+max_hp_engine_group_count+samase_status_ui_group_count+samase_weapon_ui_group_count+samase_armor_ui_group_count+trampoline_unwind_group_count+wave_targeting_group_count+wave_progression_group_count+talent_rank_group_count+rework_wave_group_count+enemy_progression_group_count+enemy_performance_group_count+targeting_bridge_group_count+rework_cargo_group_count+rework_carrier_group_count+rework_economy_group_count+rework_binding_group_count+rework_lighting_v5_group_count+rework_combat_v5_group_count+rework_economy_ui_group_count+rework_shield_ui_v5_group_count,checks);return 0;
    } catch(const std::exception& e){std::fprintf(stderr,"FAIL %s reason=%s\n",e.what(),g.apply_failure ? g.apply_failure : "none");return 1;}
}
