// Exact production TU, synthetic stock native constructor/modal. No game/DB.
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include "dialog_ui.h"
#include "include/legendary_bundles.generated.h"
#include "include/frozen_catalog.generated.h"
#include <array>
#include <cstring>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <thread>
#include <vector>
namespace {
using namespace sc1_native;
using U32=std::uint32_t;
using RunHook=U32 (__cdecl*)(void*,std::size_t,void*,dialog::RunOriginal);
using ProcessOriginal=std::size_t (__cdecl*)(std::size_t);
using ProcessHook=std::size_t (__cdecl*)(std::size_t,ProcessOriginal);
constexpr std::size_t sso_flag=std::size_t(1)<<63;
constexpr std::int16_t stock_ids[]{-3,1,2,8,9,3,5,6,7,-1};
constexpr std::int16_t candidate_ids[]{1,2,3,5},detail_ids[]{-1,1,2,3,5,6};
thread_local std::string painted;
thread_local const std::uint8_t* painted_pointer=nullptr;
thread_local std::size_t suffix_offset=0;
unsigned assertions=0,groups=0;
void check(bool okay,const char* why) {++assertions;if(!okay) {std::cerr<<why<<'\n';throw std::runtime_error(why);}}
struct Host;Host* host=nullptr;
U32 __cdecl native_root(dialog::Control*,dialog::Event*);
U32 __cdecl native_root2(dialog::Control*,dialog::Event*);
U32 __cdecl native_child(dialog::Control*,dialog::Event*);
U32 __cdecl native_hud_root(dialog::Control*,dialog::Event*);
U32 __cdecl native_hud_root2(dialog::Control*,dialog::Event*);
U32 __cdecl native_hud_button(dialog::Control*,dialog::Event*);
U32 __cdecl native_run(void*,std::size_t,void*);
U32 __cdecl native_spawn(void*,std::size_t,void*);
void __cdecl native_draw(dialog::Control*,std::int32_t,std::int32_t,const dialog::Rect*,const dialog::Rect*) {}
std::size_t __cdecl native_process(std::size_t flags) {return flags+9;}
const std::uint8_t* __cdecl native_layout(U32 a,U32 b,const std::uint8_t* text,U32* d,U32 draw,U32* f,U32 g,U32 h) {
    check(a==11 && b==12 && draw==13 && g==14 && h==15,"all layout scalar arguments preserved");
    check(d && f && *d==16 && *f==17,"layout output/input pointers preserved");
    painted=reinterpret_cast<const char*>(text);painted_pointer=text;
    return text+(suffix_offset<painted.size() ? suffix_offset : painted.size());
}
void text(dialog::Control& c,const std::string& value,std::size_t cap=15) {
    check(value.size()<=cap,"synthetic native SSO text fits");
    std::memset(c.string.inline_buffer,0xa5,16);std::memcpy(c.string.inline_buffer,value.c_str(),value.size()+1);
    c.string.data=c.string.inline_buffer;c.string.capacity=cap|sso_flag;c.string.length=value.size();
}
std::string text(const dialog::Control& c) {return {reinterpret_cast<const char*>(c.string.data),c.string.length};}
struct Host {
    DialogUi ui;samase::PluginApi api{};dialog::Dialog menu{},hud{};
    std::array<dialog::Control,11> children{};dialog::Control hud_button{};
    std::array<dialog::Rect,11> stock_area{};
    std::array<U32,11> stock_flags{},stock_flags2{};
    std::array<std::uint8_t,64> glyph{};std::array<std::uint8_t,512> body_storage{};
    RunHook run_hook=nullptr,spawn_hook=nullptr;ProcessHook process_hook=nullptr;dialog::LayoutTextHook layout_hook=nullptr;dialog::FileReadHook file_hook=nullptr;
    bool active=true,ready=false,modal=false,error_expected=false,replace_root=false,sync_delete=false,empty_body=false;
    bool register_process=true,register_run=true,register_spawn=true,register_layout=true;
    unsigned registrations=0,runs=0,spawns=0,opens=0,submits=0,last_slot=0,pumps=0,resumes=0,branches=0,scope_reads=0;
    unsigned constructor_calls=0,delete_calls=0,hud_native_events=0,reports=0;
    std::uint64_t now=100;std::size_t body_capacity=511;ChoiceOffer offer{};std::function<void()> actions,pump_action,resume_action;std::string last_report;std::vector<std::string> report_messages;
    Host() {host=this;ui.set_callbacks(callbacks());api.version=44;api.max_func_id=80;make_menu();make_hud();}
    ~Host() {host=nullptr;}
    DialogUiCallbacks callbacks();
    dialog::Control& row(std::int16_t id) {for(auto& c:children)if(c.id==id)return c;throw std::runtime_error("missing test native ID");}
    void native_body(const std::string& value) {
        check(value.size()<=body_capacity && body_capacity<body_storage.size(),"native constructor text allocation fits complete meaningful body");
        std::memcpy(body_storage.data(),value.c_str(),value.size()+1);
        auto& c=row(-1);c.string.data=body_storage.data();c.string.capacity=body_capacity;c.string.length=value.size();
    }
    void make_menu(bool social=false,bool sentinel=false) {
        menu={};children={};text(menu.control,"GameMenu");menu.control.event_handler=native_root;
        menu.control.area={184,32,447,319};std::array<std::int16_t,11> order{};const unsigned count=social ? 11u : 10u;
        for(unsigned i=0,j=0;i<count;++i) {if(social && i==6)order[i]=4;else order[i]=stock_ids[j++];}
        for(unsigned i=0;i<count;++i) {
            auto& c=children[i];c.id=order[i];c.parent=&menu;c.next=i+1<count ? &children[i+1] : nullptr;
            c.area={20,36,243,63};c.type=c.id==-1 ? 6 : 1;c.flags=c.id==8 || c.id==9 ? 0u : 2u;c.flags2=0x20;
            c.draw=native_draw;
            text(c,c.id==-1 ? "native title" : "native");
            c.event_handler=sentinel ? reinterpret_cast<dialog::EventHandler>(0xfffffffbfffffffbULL) : native_child;
        }
        row(-1).area={8,8,255,215};native_body("native constructor text");row(-3).area={20,252,243,279};menu.first_child=&children[0];
        for(unsigned i=0;i<4;++i)row(candidate_ids[i]).area={static_cast<std::int16_t>(20+56*i),220,static_cast<std::int16_t>(67+56*i),247};
        for(unsigned i=0;i<11;++i) {stock_area[i]=children[i].area;stock_flags[i]=children[i].flags;stock_flags2[i]=children[i].flags2;}
    }
    void make_hud() {
        hud={};hud_button={};text(hud.control,"Stat_F10");hud.control.area={408,388,495,407};
        hud.control.event_handler=native_hud_root;hud.first_child=&hud_button;hud_button.parent=&hud;
        hud_button.id=1;hud_button.type=1;hud_button.flags=2;hud_button.area={8,0,71,19};
        text(hud_button,"Menu");hud_button.event_handler=native_hud_button;
    }
    void construct() {
        ++constructor_calls;for(auto& c:children)if(c.parent==&menu) {c.event_handler=native_child;if(c.id!=-1)text(c,"native");}
        if(empty_body)row(-1).string={};else native_body("native constructor text");
        if(replace_root)menu.control.event_handler=native_root2;
    }
    void event(dialog::Control& c,std::uint16_t type,std::size_t id=0) {dialog::Event e{};e.type=type;e.ext_type=id;c.event_handler(&c,&e);}
    void click_id(std::int16_t id) {event(row(id),4);event(row(id),14,2);}
    void preview(unsigned slot) {click_id(candidate_ids[slot-1]);}
    void confirm() {click_id(-3);}
    void pulse() {now+=100;ui.pump(now);}
    void show(unsigned kind=1,unsigned revision=1,unsigned phase=1,unsigned first=1) {
        offer={};offer.kind=kind;offer.count=kind==1 ? 4 : 3;offer.revision=revision;
        offer.token_words[0]=revision+100;offer.requested_phase=phase;offer.completed_phase=phase ? phase-1 : 0;
        for(unsigned i=0;i<offer.count;++i)offer.candidates[i]=(first+i-1)%(kind==1?frozen::kTalentCount:frozen::kCurseCount)+1;
        ui.show(offer);
    }
    void finish() {ready=true;ui.clear();pulse();}
    void spawn_hud() {ui.spawn_dialog(&hud,0,reinterpret_cast<void*>(native_hud_root),native_spawn);}
    std::string paint(std::int16_t id) {
        U32 d=16,f=17;const auto* data=row(id).string.data;
        // Candidate model for native WS_HOTKEY preprocessing.
        ui.layout_text(11,12,data+(id==-1 ? 0 : 1),&d,13,&f,14,15,native_layout);return painted;
    }
    std::string full_detail() {
        const auto parts=body_lines();
        std::string value=parts[0]+" ["+parts[1].substr(std::string("등급: ").size())+"] ";
        for(unsigned i=2;i<parts.size();++i) {if(value.back()!=' ')value+=' ';value+=parts[i];}
        return value;
    }
    std::vector<std::string> body_lines() {
        std::vector<std::string> parts;const auto value=paint(-1);auto at=std::size_t(0);
        for(;;) {const auto end=value.find('\n',at);parts.push_back(value.substr(at,end-at));if(end==std::string::npos)break;at=end+1;}
        return parts;
    }
    void restored() {
        for(unsigned i=0;i<11;++i)if(children[i].parent) {
            check(std::memcmp(&children[i].area,&stock_area[i],sizeof(dialog::Rect))==0,"original rectangle restored before native lifecycle");
            check(children[i].flags==stock_flags[i] && children[i].flags2==stock_flags2[i],"original visible/disabled flags restored before native lifecycle");
        }
    }
    std::string expected_detail(unsigned index,unsigned kind) {
        return std::string(kind==1 ? frozen::talent_names[index] : frozen::curse_names[index])+" ["
            +(kind==1 ? frozen::talent_rarities[index] : frozen::curse_rarities[index])+"] "
            +(kind==1 ? frozen::talent_effects[index] : frozen::curse_effects[index]);
    }
};
bool active(void* p) {auto& h=*static_cast<Host*>(p);++h.scope_reads;return h.active;}
bool ready(void* p) {return static_cast<Host*>(p)->ready;}
bool submit(void* p,U32 slot) {auto& h=*static_cast<Host*>(p);++h.submits;h.last_slot=slot;return true;}
void pump(void* p) {auto& h=*static_cast<Host*>(p);++h.pumps;if(h.pump_action)h.pump_action();}
void report(void* p,const char* value) {auto& h=*static_cast<Host*>(p);++h.reports;h.last_report=value;h.report_messages.push_back(value);}
DialogUiCallbacks Host::callbacks() {return {this,submit,pump,::active,::ready,report};}
U32 __cdecl native_child(dialog::Control* c,dialog::Event* e) {
    if(e->type==14 && e->ext_type==2) {
        if(c->id==-3) {check(host->ready || host->error_expected,"Resume after publication or explicit UI error only");host->restored();
            check(host->menu.control.event_handler==native_root || host->menu.control.event_handler==native_root2,"all native root delegates restored before Resume");
            for(const auto& child:host->children)if(child.parent==&host->menu)check(child.event_handler==native_child,"all native child delegates restored before Resume");
            ++host->resumes;host->modal=false;if(host->sync_delete)host->event(host->menu.control,14,1);if(host->resume_action)host->resume_action();}
        else ++host->branches;
    }return 9;
}
U32 __cdecl native_root(dialog::Control*,dialog::Event* e) {
    if(e->type==14 && (e->ext_type==7 || e->ext_type==0))host->construct();
    if(e->type==14 && e->ext_type==1) {host->restored();++host->delete_calls;for(auto& c:host->children)if(c.parent==&host->menu && c.id!=-1)check(c.event_handler==native_child,"native handlers restored before delete");}
    if((e->type==14 && e->ext_type==2) || e->type==0 || e->type==2 || e->type==15)++host->branches;return 7;
}
U32 __cdecl native_root2(dialog::Control* c,dialog::Event* e) {return native_root(c,e);}
U32 __cdecl native_hud_root(dialog::Control*,dialog::Event* e) {
    ++host->hud_native_events;if(e->type==14 && (e->ext_type==7 || e->ext_type==0)) {host->hud_button.event_handler=native_hud_button;host->hud.control.event_handler=native_hud_root2;}return 23;
}
U32 __cdecl native_hud_root2(dialog::Control* c,dialog::Event* e) {return native_hud_root(c,e);}
U32 __cdecl native_hud_button(dialog::Control*,dialog::Event* e) {
    if(e->type==14 && e->ext_type==2) {check(e->ext_param==0 && e->param==0 && e->x==0 && e->y==0,"exact public Ext2 payload/fallback mouse coordinates");++host->opens;host->ui.run_dialog(&host->menu,0,reinterpret_cast<void*>(native_root),native_run);}return 19;
}
U32 __cdecl native_run(void* raw,std::size_t,void* handler) {
    ++host->runs;const auto deletes=host->delete_calls;host->modal=true;auto* root=static_cast<dialog::Dialog*>(raw);root->control.event_handler=reinterpret_cast<dialog::EventHandler>(handler);
    host->event(root->control,14,7);host->event(root->control,14,0);host->pulse();if(host->actions)host->actions();
    if(host->ui.open() && host->delete_calls==deletes)host->event(root->control,14,1);host->modal=false;return 17;
}
U32 __cdecl native_spawn(void* raw,std::size_t,void* handler) {
    ++host->spawns;auto* root=static_cast<dialog::Dialog*>(raw);
    check(root->control.event_handler==reinterpret_cast<dialog::EventHandler>(handler),"constructor callback unchanged before original Spawn");
    if(root==&host->menu) {check(!host->ui.open(),"no binding before Spawn original completes");host->construct();}return 31;
}
U32 __cdecl register_run(RunHook fn) {++host->registrations;host->run_hook=fn;return host->register_run;}
U32 __cdecl register_spawn(RunHook fn) {++host->registrations;host->spawn_hook=fn;return host->register_spawn;}
U32 __cdecl register_function(std::uint16_t id,std::size_t fn) {check(id==79,"public ProcessEvents79 only");++host->registrations;host->process_hook=reinterpret_cast<ProcessHook>(fn);return host->register_process;}
U32 __cdecl register_layout(dialog::LayoutTextHook fn) {++host->registrations;host->layout_hook=fn;return host->register_layout;}
void __cdecl register_file(const std::uint8_t* prefix,dialog::FileReadHook fn) {check(std::strcmp(reinterpret_cast<const char*>(prefix),"rez/gamemenu.ui.json")==0 || std::strcmp(reinterpret_cast<const char*>(prefix),"rez/gamemenusocial.ui.json")==0 || std::strcmp(reinterpret_cast<const char*>(prefix),"rez/statfluf.ui.json")==0,"only original menu and independent placeholder constructor file prefixes registered");++host->registrations;host->file_hook=fn;}
void bind_api(Host& h) {h.api.hook_run_dialog=reinterpret_cast<samase::GenericFn>(register_run);h.api.hook_spawn_dialog=reinterpret_cast<samase::GenericFn>(register_spawn);h.api.hook_func=reinterpret_cast<samase::GenericFn>(register_function);h.api.hook_layout_draw_text=reinterpret_cast<samase::GenericFn>(register_layout);h.api.hook_file_read=reinterpret_cast<samase::GenericFn>(register_file);}
void open(Host& h) {check(h.ui.run_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_run)==dialog::kResumeResult,"owned modal result is native Resume");check(!h.ui.open(),"Run return retains no foreign menu pointer");}
void api_test() {
    ++groups;for(unsigned reason=0;reason<9;++reason) {Host h;bind_api(h);
        if(reason==0)h.api.version=43;if(reason==1)h.api.max_func_id=79;if(reason==2)h.api.hook_spawn_dialog=nullptr;
        if(reason==3)h.register_process=false;if(reason==4)h.register_run=false;if(reason==5)h.register_spawn=false;
        if(reason==6)h.api.hook_layout_draw_text=nullptr;if(reason==7)h.register_layout=false;if(reason==8)h.api.hook_file_read=nullptr;
        check(!h.ui.initialize(&h.api,h.callbacks()),"unsupported/partial registration rejected");if(h.process_hook)check(h.process_hook(7,native_process)==16,"partial wrapper preserves original result");
    }
    Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"API44 public hooks install");check(h.registrations==7 && h.file_hook,"scoped original native constructor file hooks registered");
    U32 size=123;check(!h.ui.file_read(reinterpret_cast<const std::uint8_t*>(1),&size) && size==123,"original file fallback touches neither pointer nor size");check(h.process_hook(19,native_process)==28,"ProcessEvents original flags and return preserved");
}
std::string no_spaces(std::string value) {std::string result;for(const auto c:value)if(c!=' ' && c!='\r' && c!='\n' && c!='\t')result+=c;return result;}
void catalog_test() {
    ++groups;for(unsigned kind=1;kind<=2;++kind)for(unsigned index=0;index<(kind==1?frozen::kTalentCount:frozen::kCurseCount);++index) {
        Host h;h.make_menu(false,true);h.show(kind,index+1,1,index+1);std::array<dialog::Rect,11> rects{};std::array<std::uint16_t,11> types{};
        for(unsigned i=0;i<11;++i) {rects[i]=h.children[i].area;types[i]=h.children[i].type;}
        h.actions=[&] {
            check(h.paint(1)=="1" && text(h.row(-1)).find(kind==1 ? frozen::talent_names[index] : frozen::curse_names[index])!=std::string::npos,"numeric choice button and actual native text panel show corresponding candidate");
            h.preview(1);check(h.submits==0 && h.ui.previewing(),"candidate previews only");
            check(h.body_lines()[0]==(kind==1 ? frozen::talent_names[index] : frozen::curse_names[index]),"name is first complete upper-panel line");
            check(h.body_lines()[1]==std::string("등급: ")+(kind==1 ? frozen::talent_rarities[index] : frozen::curse_rarities[index]),"rarity is a separate complete line");
            if(no_spaces(h.full_detail())!=no_spaces(h.expected_detail(index,kind)))std::cerr<<"detail mismatch kind="<<kind<<" index="<<index<<" actual="<<h.full_detail()<<" expected="<<h.expected_detail(index,kind)<<"\n";
            check(no_spaces(h.full_detail())==no_spaces(h.expected_detail(index,kind)),"word-boundary effect lines retain every frozen word/number/operator");
            check(text(h.row(-1))==h.paint(-1),"complete name/rarity/effect is physically present in native CTEXT storage without renderer dependence");
            for(unsigned i=0;i<11;++i)if(h.children[i].parent) {const auto& c=h.children[i];check(c.id==-1 ? c.string.data==h.body_storage.data() && c.string.capacity==511 : c.string.data==c.string.inline_buffer && c.string.capacity==(sso_flag|15),"original native text allocation/SSO ownership retained");check(c.string.data[c.string.length]==0,"native payload plus NUL inside existing allocation");check(c.type==types[i] && std::memcmp(&c.area,&rects[i],sizeof(c.area))==0,"native constructor type/geometry/order retained afterward");check((c.flags2&~5u)==0x20,"unrelated flags2 retained");}
            for(const auto id:{6,7,8,9})check(!(h.row(static_cast<std::int16_t>(id)).flags&2),"button-label explanation rows are absent");
            for(unsigned i=0;i<4;++i)check(!(h.row(candidate_ids[i]).flags2&1) || i>=h.offer.count,"lower candidates remain enabled during upper preview");
            h.confirm();check(h.submits==1 && h.last_slot==1 && h.ui.waiting(),"explicit -3 publishes once");h.confirm();h.preview(2);check(h.submits==1,"pending durable ACK blocks doubleclick");h.finish();check(h.resumes==1,"phase snapshot closes by original Resume");
        };open(h);check(h.branches==0,"no native Save/Load/Exit candidate branch");
    }
    for(unsigned kind=1;kind<=2;kind++)for(unsigned bad:{0u,(kind==1 ? frozen::kTalentCount : frozen::kCurseCount)+1u}){
        Host h;h.show(kind);h.ui.clear();h.offer.candidates[0]=bad;h.ui.show(h.offer);check(!h.ui.pending(),"invalid expanded catalog boundary cannot become a selectable offer");
    }

}
void spawn_reinit_test() {
    ++groups;Host h;h.make_menu(true,true);h.show();check(h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn)==31,"Spawn return unchanged");check(h.ui.open() && h.body_lines()[0]=="재능 선택","native Social text-panel post-construction bind");
    h.preview(1);h.preview(2);check(h.ui.previewing() && h.submits==0,"another candidate updates upper preview without publish");h.replace_root=true;h.event(h.menu.control,14,7);h.event(h.menu.control,14,0);check(h.row(1).event_handler==native_child,"reinit uses original child callbacks");
    h.pulse();h.preview(1);check(no_spaces(h.full_detail())==no_spaces(h.expected_detail(0,1)),"reinit callback replacement revalidated");h.error_expected=true;h.ui.dismiss_error();h.pulse();check(h.resumes==1 && h.submits==0,"error closes without selection");h.event(h.menu.control,14,1);check(!h.ui.open(),"Spawn delete invalidates cached pointers");
}
void stale_test() {
    ++groups;Host h;h.show();h.actions=[&] {h.preview(1);h.event(h.row(-3),4);h.show(2,2);h.pulse();h.event(h.row(-3),14,2);check(h.submits==0,"old confirm cannot publish next offer");
        h.event(h.menu.control,14,2);h.event(h.row(1),0);h.event(h.row(1),2);h.event(h.row(1),15);check(h.submits==0 && h.branches==0,"root/unknown/Escape/hotkey cannot bypass selection");h.preview(2);h.confirm();check(h.submits==1 && h.last_slot==2,"fresh curse confirms slot");
        const auto before=h.resumes;h.pump_action=[&] {h.ui.clear();check(h.resumes==before,"clear callback cannot close mid-publication");h.ready=true;};h.pulse();h.pump_action={};check(h.resumes==before+1,"close after publication callback returns");
    };open(h);
}
void text_failure_test() {
    ++groups;for(unsigned fault=0;fault<2;++fault) {Host h;h.show(1,1,1,8);h.error_expected=true;h.actions=[&] {
        if(fault==0)for(const auto id:detail_ids) {h.row(id).string.capacity=sso_flag|2;h.row(id).string.length=0;}else {h.row(1).string.data=h.row(1).string.inline_buffer+1;h.row(1).string.length=0;}
        const auto preserved=h.row(1).flags;h.preview(1);check(h.submits==0 && (h.row(-3).flags2&1),"incomplete detail immediately disables confirm");h.confirm();check(h.submits==0 && h.row(1).flags==preserved,"bad inline offset cannot overwrite flags or submit");check(h.resumes==0,"text error closes deferred");h.pulse();check(h.resumes==1,"next pump safely dismisses text failure");
    };open(h);}
}
void phases_auto_test() {
    ++groups;Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"automatic hooks installed");h.active=false;h.spawn_hud();h.ui.reset_session();h.ui.set_callbacks(h.callbacks());h.active=true;unsigned heartbeat=0;
    for(unsigned phase=1;phase<=3;++phase) {h.make_menu();h.ready=false;h.show(1,phase*2-1,phase);h.actions=[&] {
        check(h.opens==phase && h.modal,"one automatic HUD activation per phase");check(h.body_lines()[0]=="재능 선택","same concise title in every phase");
        h.pump_action=[&] {++heartbeat;};const auto before=h.pumps;Sleep(55);check(h.process_hook(3,native_process)==12,"nested ProcessEvents original return");check(h.pumps>before && heartbeat,"synchronous auto-modal nesting keeps paused protocol pump alive");h.pump_action={};
        h.preview(1);h.confirm();check(h.submits==phase*2-1,"one talent per phase");h.pump_action=[&] {h.show(2,phase*2,phase);};h.pulse();h.pump_action={};check(h.opens==phase && h.ui.open(),"next ACK refreshes existing modal");check(h.row(5).flags2&1,"curse has3 enabled candidates");h.preview(1);h.confirm();check(h.submits==phase*2,"one curse per phase");h.finish();
    };h.pulse();check(!h.ui.open() && h.resumes==phase,"phase snapshot closes popup");}check(h.opens==3 && h.submits==6,"three phases three talent/curse pairs");
}
void stock_depth_test() {
    ++groups;Host h;h.spawn_hud();h.actions=[&] {h.show();h.pulse();check(h.opens==0,"offer during stock modal cannot open nested choices");};check(h.ui.run_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_run)==17,"stock modal preserves original result");
    h.actions=[&] {h.error_expected=true;h.ui.dismiss_error();h.pulse();};h.make_menu();h.pulse();check(h.opens==1 && h.resumes==1,"choices open on first safe pulse after stock menu");
}
void standalone_legendary_v2_test() {
    ++groups;Host h;h.offer={};h.offer.wire_version=2;h.offer.kind=1;h.offer.count=1;
    h.offer.revision=1;h.offer.requested_phase=1;h.offer.token_words[0]=101;h.offer.candidates[0]=257;
    h.ui.show(h.offer);check(h.ui.pending(),"v2 single unowned legendary is accepted by production UI");
    h.actions=[&] {
        check((h.row(1).flags&2) && !(h.row(1).flags2&1),"single legendary has one enabled choice");
        for(unsigned i=1;i<4;i++)check(!(h.row(candidate_ids[i]).flags&2) && (h.row(candidate_ids[i]).flags2&1),"unused slots are hidden and disabled");
        check(h.ui.previewing() && h.submits==0,"single legendary description is shown automatically without granting");
        check(no_spaces(h.full_detail())==no_spaces(h.expected_detail(256,1)),"complete single legendary effect appears before explicit confirmation");
        h.confirm();check(h.submits==1 && h.last_slot==1 && h.ui.waiting(),"single legendary is submitted once");
        h.confirm();check(h.submits==1,"repeat click while storing cannot grant twice");h.finish();
    };open(h);check(h.resumes==1 && !h.ui.pending(),"legendary ACK closes modal and permits the next native trigger");
    Host old;auto bad=h.offer;bad.wire_version=1;old.ui.show(bad);check(!old.ui.pending(),"v1 keeps historical four-candidate talent contract");
    bad.wire_version=3;old.ui.show(bad);check(!old.ui.pending(),"unknown offer wire version is rejected");
    bad.wire_version=2;bad.count=0;old.ui.show(bad);check(!old.ui.pending(),"empty v2 offer is rejected");
}
void hud_test() {
    ++groups;for(unsigned order=0;order<2;++order) {Host h;if(order==0)h.active=false;h.spawn_hud();if(order==0) {h.ui.reset_session();h.ui.set_callbacks(h.callbacks());h.active=true;}
        h.event(h.hud.control,14,7);h.event(h.hud.control,14,0);h.show();h.hud_button.flags=0;h.pulse();check(!h.opens,"hidden HUD ignored");h.hud_button.flags=2;h.hud_button.flags2=1;h.pulse();check(!h.opens,"disabled HUD ignored");h.hud_button.flags2=0;
        h.hud_button.event_handler=reinterpret_cast<dialog::EventHandler>(0xfffffffbfffffffbULL);h.pulse();check(!h.opens,"nonexecutable sentinel rejected");h.hud_button.event_handler=native_hud_button;auto wrapped=h.hud.control.event_handler;h.hud.control.event_handler=native_root;h.pulse();check(!h.opens,"untracked parent rejected");h.hud.control.event_handler=wrapped;
        h.actions=[&] {h.error_expected=true;h.ui.dismiss_error();h.pulse();};h.pulse();check(h.opens==1,"HUD both initialization orders and reinit activate once");h.pulse();check(h.opens==1,"once-offer latch");h.ui.reset_session();const auto previous=h.hud_native_events;h.event(h.hud.control,14,1);check(h.hud_native_events==previous+1,"native delete delegated after session reset");check(h.hud.control.event_handler==native_hud_root2,"native root restored before HUD delete");
    }
}
void thread_delete_test() {
    ++groups;Host h;h.show();h.actions=[&] {const auto reads=h.scope_reads,pumps=h.pumps;std::thread foreign([&] {h.ui.pump(999999);check(h.ui.event(reinterpret_cast<dialog::Control*>(1),reinterpret_cast<dialog::Event*>(1))==0,"foreign event rejects poisoned pointers");});foreign.join();check(h.scope_reads==reads && h.pumps==pumps,"foreign thread never reads native callbacks/offer");h.preview(1);h.confirm();h.sync_delete=true;h.finish();check(h.ui.open() && h.delete_calls==1,"Run retains only own state until original loop return after synchronous native delete");};open(h);
}
void legacy_test() {++groups;Host h;h.show(1,1,0);h.actions=[&] {check(h.body_lines()[0]=="재능 선택","legacy phase0 supported");h.preview(1);h.confirm();h.finish();};open(h);}
void backed_panel_test() {
    ++groups;Host h;h.row(-1).image={248,208,h.glyph.data()};const auto image=h.row(-1).image;
    h.show(1,1,1,8);h.actions=[&] {
        check(std::memcmp(&h.row(-1).area,&h.stock_area[9],sizeof(dialog::Rect))==0,"native-created CTEXT surface/rectangle never resized afterward");
        for(const auto id:{8,9,6})check(!(h.row(static_cast<std::int16_t>(id)).flags&2) && (h.row(static_cast<std::int16_t>(id)).flags2&1),"legacy button body rows hidden rather than used as text");
        h.preview(1);check(no_spaces(h.full_detail())==no_spaces(h.expected_detail(7,1)),"long cost effect fits two complete semantic lines");
        check(std::memcmp(&h.row(-1).image,&image,sizeof(image))==0,"surface fields and native backing pointer unchanged");
        for(unsigned i=0;i<4;++i)check(h.row(candidate_ids[i]).area.left==20+int(i)*56 && h.row(candidate_ids[i]).area.top==220 && h.row(candidate_ids[i]).area.right==67+int(i)*56 && h.row(candidate_ids[i]).area.bottom==247,"four native-created numeric buttons stay inside root");
        check(h.row(-3).area.top==252 && h.row(-3).area.bottom==279,"original confirm stays inside288px root");h.confirm();h.finish();
    };open(h);
}
void render_lifetime_test() {
    ++groups;Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"registered exact LayoutDrawText ABI");
    h.show(1,1,1,7);h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn);
    h.preview(1);auto* key=h.row(-1).string.data;const auto expected=text(h.row(-1));U32 d=16,f=17;suffix_offset=2;
    auto* suffix=h.layout_hook(11,12,key,&d,13,&f,14,15,native_layout);
    check(painted==expected && suffix==painted_pointer+2,"full native text override preserves original suffix result");
    const std::string saved=reinterpret_cast<const char*>(suffix);h.ui.clear();h.show(2,2);h.pulse();h.preview(1);const auto curse_expected=text(h.row(-1));
    check(std::string(reinterpret_cast<const char*>(suffix))==saved,"returned text remains valid after clear/new generation");
    suffix_offset=0;const auto scopes=h.scope_reads;const auto* native_data=h.row(-1).string.data;
    h.row(-1).string.data=reinterpret_cast<const std::uint8_t*>(1);std::string foreign;
    std::thread renderer([&] {U32 rd=16,rf=17;h.layout_hook(11,12,key,&rd,13,&rf,14,15,native_layout);foreign=painted;});renderer.join();
    h.row(-1).string.data=native_data;check(foreign==curse_expected && h.scope_reads==scopes,"render thread uses immutable snapshot without scope/native-control reads");
    const std::uint8_t original[]{'o','r','i','g','i','n','a','l',0};suffix_offset=3;
    check(h.layout_hook(11,12,original,&d,13,&f,14,15,native_layout)==original+3 && painted_pointer==original,"unmatched text/args/return passed through exactly");
    h.ui.clear();suffix_offset=0;h.layout_hook(11,12,key,&d,13,&f,14,15,native_layout);
    check(painted_pointer==key,"cleared menu cannot override stale native input");
    check(std::string(reinterpret_cast<const char*>(suffix))==saved,"returned suffix survives fallback calls");
    h.error_expected=true;h.ui.dismiss_error();h.pulse();h.event(h.menu.control,14,1);
}
void hotkey_render_test() {
    ++groups;
    {
        Host h;h.row(-1).image={248,208,h.glyph.data()};h.show();
        h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn);
        const auto* base=h.row(1).string.data;U32 d=16,f=17;
        for(const auto id:{1,2,3,5,-3}) {
            const auto label=text(h.row(static_cast<std::int16_t>(id)));
            check(!label.empty() && label[0]==' ',"native hotkey label reserves an ASCII blank");
        }
        check(text(h.row(-1)).find("재능 선택")==0,"non-hotkey CTEXT has no reserved prefix");
        check(text(h.row(-3)).substr(1,3)==std::string("확정").substr(0,3),"native consumed prefix preserves first Korean confirmation glyph on fallback");
        const auto native_before=h.children;const auto scopes=h.scope_reads,reports=h.reports;
        const auto* passed=h.ui.layout_text(11,12,base+2,&d,13,&f,14,15,native_layout);
        check(painted_pointer==base+2 && passed==base+2,"unknown interior offset preserves original pointer and return");
        auto stats=h.ui.render_stats();
        check(stats.calls==1 && stats.near_miss==1 && stats.exact==0 && stats.hotkey_offset==0,"unrecognized interior offset diagnosed without overriding");
        check(stats.offset==2 && stats.row==1 && stats.a==11 && stats.b==12 && stats.draw==13 && stats.g==14 && stats.h==15,"first offset and public scalar arguments recorded atomically");
        h.ui.layout_text(11,12,base,&d,13,&f,14,15,native_layout);
        check(painted==" 1","exact hotkey renderer input retains harmless prefix and numeric choice");
        h.ui.layout_text(11,12,base+1,&d,13,&f,14,15,native_layout);
        check(painted=="1","one-byte hotkey offset receives complete numeric choice");
        std::string foreign;
        std::thread renderer([&] {U32 rd=16,rf=17;h.ui.layout_text(11,12,base+1,&rd,13,&rf,14,15,native_layout);foreign=painted;});renderer.join();
        stats=h.ui.render_stats();
        check(foreign=="1" && stats.calls==4 && stats.exact==1 && stats.hotkey_offset==2 && stats.near_miss==1,"foreign renderer shares immutable text and atomic counters");
        check(h.scope_reads==scopes && h.reports==reports,"renderer never calls UI scope or report callback");
        check(std::memcmp(h.children.data(),native_before.data(),sizeof(h.children))==0,"offset rendering changes no native control/SSO/geometry bytes");
        const auto probe_reports=h.reports;for(unsigned i=0;i<12;++i)h.pulse();
        check(h.reports==probe_reports+1 && h.last_report.find("Text render probe: calls=4 exact=1 hotkey_offset=2 near_miss=1 first_offset=2 row=1 args=11,12,13,14,15")!=std::string::npos,"owner UI pump emits one useful render-match diagnostic");
        for(unsigned i=0;i<12;++i)h.pulse();check(h.reports==probe_reports+1,"render-match log is bounded to once per popup");
        h.preview(1);check(h.paint(-1)==text(h.row(-1)),"full grade/effect is native CTEXT content rather than a button label");
        check(h.paint(-3)=="확정","confirmation keeps first glyph/full text");
        h.error_expected=true;h.ui.dismiss_error();h.pulse();h.event(h.menu.control,14,1);
    }
    {
        Host h;h.show();h.actions=[&] {
            for(const auto id:candidate_ids) {h.row(id).string.capacity=sso_flag|3;h.row(id).string.length=0;}
            h.preview(1);check(h.ui.previewing() && !h.submits,"three-byte native storage can preview without publishing");
            check(text(h.row(1))==" 1" && h.row(1).string.inline_buffer[2]==0,"minimal hotkey native buffer fits complete numeric label");
            const auto before=h.children;check(h.paint(1)=="1","minimal numeric native label resolves complete number");
            check(no_spaces(h.full_detail())==no_spaces(h.expected_detail(0,1)),"full name/rarity/effect stay in actual text panel independent of numeric storage");
            check(std::memcmp(h.children.data(),before.data(),sizeof(h.children))==0,"minimal-capacity renderer preserves all native control bytes");
            h.confirm();check(h.submits==1,"explicit confirmation works after complete minimal-capacity preview");h.finish();
        };open(h);
    }
}
std::string constructor_body(const std::string& payload) {
    constexpr char marker[]="\"type\":\"CTEXT\",\"content\":\"";
    auto at=payload.find(marker);check(at!=std::string::npos,"payload retains original real CTEXT declaration");at+=sizeof(marker)-1;
    std::string result;
    for(;at<payload.size();++at) {
        const auto c=payload[at];if(c=='"')return result;
        if(c=='\\') {check(++at<payload.size(),"constructor text escape is complete");const auto escaped=payload[at];result+=escaped=='n' ? '\n' : escaped=='r' ? '\r' : escaped=='t' ? '\t' : escaped;}
        else result+=c;
    }
    throw std::runtime_error("unterminated constructor text");
}
void constructor_file_test() {
    ++groups;Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"actual public file registration signature accepted");
    constexpr auto name="rez/gamemenu.ui.json";const auto* file=reinterpret_cast<const std::uint8_t*>(name);U32 size=123;
    check(!h.file_hook(file,&size) && size==123,"no pending offer means exact stock file fallback");
    for(unsigned kind=1;kind<=2;++kind)for(unsigned first=1;first<=(kind==1?frozen::kTalentCount:frozen::kCurseCount);++first)for(unsigned social=0;social<2;++social) {
        h.show(kind,first,1,first);
        const auto* path=reinterpret_cast<const std::uint8_t*>(social ? "rez/gamemenusocial.ui.json" : name);
        auto* bytes=h.file_hook(path,&size);check(bytes && size && HeapSize(GetProcessHeap(),0,bytes)>=size,"native JSON file payload uses documented process-heap file allocation");
        const std::string payload(reinterpret_cast<const char*>(bytes),size);const auto body=constructor_body(payload);
        check(HeapFree(GetProcessHeap(),0,bytes)!=0,"engine-model can release documented file payload");
        check(payload.find("\"name\":\"GameMenu\"")!=std::string::npos && payload.find("[8,8,248,208]")!=std::string::npos,"original native dialog/positive text panel geometry declared before construction");
        check(payload.find("SC1_NATIVE_CHOICE_BODY")==std::string::npos && body.size()>=77 && body.find("                ")==std::string::npos,"meaningful candidate names/rarities/instruction reserve full detail storage without space padding");
        for(unsigned i=0;i<h.offer.count;++i) {
            const auto index=h.offer.candidates[i]-1;
            check(body.find(kind==1 ? frozen::talent_names[index] : frozen::curse_names[index])!=std::string::npos,"constructor content contains each full offered name");
            check(body.size()>=h.expected_detail(index,kind).size(),"constructor semantic body is longer than every offered full detail");
        }
    }
    h.show();h.active=false;size=123;check(!h.file_hook(file,&size) && size==123,"inactive session never replaces native file");h.active=true;
    const auto reports=h.reports,scopes=h.scope_reads;std::thread foreign([&] {U32 length=456;check(!h.file_hook(reinterpret_cast<const std::uint8_t*>(1),&length) && length==456,"foreign file hook declines before poisoned filename access");});foreign.join();
    check(h.reports==reports && h.scope_reads==scopes,"foreign file read never invokes native callbacks or logs");
    check(!h.file_hook(reinterpret_cast<const std::uint8_t*>("rez/objctdlg.ui.json"),&size),"other native dialogs always use original JSON");
    h.actions=[&] {U32 length=789;check(!h.file_hook(file,&length) && length==789,"already-owned native modal never loads a nested replacement");h.finish();};open(h);
    h.make_menu();h.show();h.ui.run_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_run);
    h.make_menu();h.show();h.row(-1).area={0,8,263,31};h.stock_area[9]=h.row(-1).area;h.error_expected=true;
    h.actions=[&] {check(h.submits==0 && !h.ui.pending(),"cached stock title without declared text panel fails closed");h.pulse();};open(h);
    check(h.resumes>=1,"unsupported native constructor result safely resumes without allocating or retyping widgets");
    h.make_menu();h.show();h.empty_body=true;
    const auto before=h.resumes;h.actions=[&] {check(h.submits==0 && !h.ui.pending() && h.resumes==before+1,"unresolved native title with null/zero storage dismisses without exposing selection");};open(h);
    bool failed_write=false;
    for(const auto& message:h.report_messages)if(message.find("Native CTEXT body: capacity=0")!=std::string::npos && message.find("full_write=0")!=std::string::npos)failed_write=true;
    check(failed_write,"empty native literal outcome records required bytes and failed complete write");
}
void native_sized_metadata_test() {
    ++groups;
    {
        Host h;h.body_capacity=232;h.row(-1).image={248,208,nullptr};const auto metadata=h.row(-1).image;
        h.show();h.actions=[&] {
            check(h.ui.pending() && h.resumes==0,"observed native232-capacity/null-data/sized metadata keeps reward menu open");
            check(text(h.row(-1)).find("재능 선택")==0,"full offer introduction reaches original232-byte native allocation");
            h.preview(1);check(no_spaces(h.full_detail())==no_spaces(h.expected_detail(0,1)),"native-sized/null-data panel retains complete selected name/rarity/effect");
            check(h.row(-1).string.capacity==232 && h.row(-1).string.data==h.body_storage.data(),"actual232-byte descriptor ownership/capacity unchanged");
            check(std::memcmp(&h.row(-1).image,&metadata,sizeof(metadata))==0,"sized/null native image metadata is never allocated or mutated");
            h.confirm();check(h.submits==1 && h.ui.waiting(),"observed native metadata allows explicit talent confirmation");
            h.show(2,2);h.pulse();check(h.resumes==0 && h.ui.pending(),"durable next curse remains in same native232-capacity panel");
            h.preview(2);h.confirm();check(h.submits==2 && h.last_slot==2,"same panel explicitly confirms curse");h.finish();
        };
        check(h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn)==31,"observed native metadata original Spawn result retained");
        h.actions();h.event(h.menu.control,14,1);check(!h.ui.open(),"observed native metadata delegates original cleanup");
        bool full_write=false;
        for(const auto& message:h.report_messages)if(message.find("Native CTEXT body: capacity=232")!=std::string::npos && message.find("full_write=1")!=std::string::npos)full_write=true;
        check(full_write && h.resumes==1,"sized/null panel logs complete native write and resumes after snapshot only");
    }
    for(unsigned reason=0;reason<4;++reason) {
        Host h;h.show();h.error_expected=true;
        h.row(-1).image=reason==0 ? dialog::Surface{247,208,nullptr}
            : reason==1 ? dialog::Surface{248,207,nullptr}
            : reason==2 ? dialog::Surface{0,208,nullptr} : dialog::Surface{0,0,h.glyph.data()};
        const auto preserved=h.row(-1).image;
        h.actions=[&] {check(!h.ui.pending() && h.submits==0 && h.resumes==1,"undersized/partial/nonempty invalid metadata fails closed without confirmation");
            check(std::memcmp(&h.row(-1).image,&preserved,sizeof(preserved))==0,"rejected native metadata never rewritten into a guessed surface");};open(h);
    }
}
void spawn_no_delete_test() {
    ++groups;Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"Spawn no-delete production hooks installed");
    for(unsigned phase=1;phase<=3;++phase) {
        h.make_menu();h.ready=false;h.show(1,phase*2-1,phase);
        check(h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn)==31 && h.ui.open(),"next phase rebinds native Spawn at reused address");
        h.preview(1);h.confirm();h.show(2,phase*2,phase);h.pulse();h.preview(1);h.confirm();
        h.resume_action=[&] {
            const auto reports=h.reports;h.ui.clear();h.now+=100;h.ui.pump(h.now);
            check(h.reports==reports && h.resumes==phase,"nested closing ProcessEvents does not refresh or repeat native Resume");
        };
        h.finish();h.resume_action={};
        check(!h.ui.open() && h.delete_calls==0 && h.resumes==phase,"Spawn snapshot releases own menu state without any root delete event");
        check(h.submits==phase*2,"each no-delete Spawn checkpoint publishes exactly one talent/curse pair");
        check(h.ui.event(reinterpret_cast<dialog::Control*>(1),reinterpret_cast<dialog::Event*>(1))==0,"detached Spawn rejects stale pointers before native access");
    }
    h.make_menu();h.ready=false;h.show();h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn);h.preview(1);h.confirm();
    h.resume_action=[&] {
        h.ui.reset_session();h.active=false;
        std::memset(&h.menu,0xcc,sizeof(h.menu));std::memset(h.children.data(),0xcc,sizeof(h.children));
    };
    h.finish();h.resume_action={};check(!h.ui.open(),"Spawn return detaches captured owned generation after epoch reset without reading poisoned widgets");
    h.make_menu();h.active=true;h.ui.set_callbacks(h.callbacks());h.ready=false;h.show(1,20,2);
    h.ui.spawn_dialog(&h.menu,0,reinterpret_cast<void*>(native_root),native_spawn);check(h.ui.open(),"new session can create choices after old Spawn generation reset");
    h.sync_delete=true;h.preview(1);h.confirm();h.finish();check(!h.ui.open() && h.delete_calls==1,"Spawn synchronous delete remains safe and does not retain native pointers");
}
unsigned wave_native_events=0;
U32 __cdecl wave_native_event(dialog::Control*,dialog::Event*){++wave_native_events;return 29;}
void independent_wave_timer_test(){
    ++groups;Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"wave HUD public file hook registered");
    U32 size=321;const auto* file=reinterpret_cast<const std::uint8_t*>("rez/statfluf.ui.json");
    h.active=false;check(!h.file_hook(file,&size) && size==321,"stock inactive HUD template stays unchanged");h.active=true;
    auto* bytes=h.file_hook(file,&size);check(bytes && size,"authenticated campaign gets native timer constructor even without an offer");
    const std::string payload(reinterpret_cast<const char*>(bytes),size);HeapFree(GetProcessHeap(),0,bytes);
    check(payload.find("\"content\":\"statfluf-1\",\"id\":-1,\"rect\":[0,0,4,4]")!=std::string::npos,"original placeholder geometry and content are retained");
    check(payload.find("\"id\":-32000")!=std::string::npos && payload.find("\"WS_DISABLED\"")!=std::string::npos,"new dedicated text is noninteractive with a unique ID");
    check(payload.find("StatLB")==std::string::npos && payload.find("StatRes")==std::string::npos,"no original leaderboard or resource text replacement");
    dialog::Dialog root{};dialog::Control placeholder{},label{};std::array<std::uint8_t,80> buffer{};
    text(root.control,"StatFluf");root.control.area={0,0,247,147};root.control.event_handler=wave_native_event;root.first_child=&placeholder;
    placeholder.parent=&root;placeholder.next=&label;placeholder.id=-1;placeholder.area={0,0,3,3};text(placeholder,"original");
    label.parent=&root;label.id=-32000;label.type=6;label.area={8,128,239,147};label.flags2=0x20;
    label.string.data=buffer.data();label.string.capacity=buffer.size()-1;label.string.length=0;
    const auto retained=placeholder;const auto parent_rect=root.control.area;const auto label_rect=label.area;const auto allocation=label.string.data;
    h.ui.set_wave_timer("공세 출발 02:34");
    check(h.ui.spawn_dialog(&root,0,reinterpret_cast<void*>(wave_native_event),native_spawn)==31,"original native Spawn return retained for timer");
    check(text(label)=="공세 출발 02:34" && (label.flags&2) && (label.flags2&1),"timer uses native allocated text and remains disabled for input");
    check(std::memcmp(&placeholder,&retained,sizeof(retained))==0,"every original placeholder field is untouched");
    check(label.string.data==allocation && label.string.capacity==79 && std::memcmp(&label.area,&label_rect,sizeof(label_rect))==0,"timer storage ownership and constructor geometry never resized");
    for(unsigned redraw=0;redraw<20;redraw++){h.pulse();check(text(label)=="공세 출발 02:34","paused simulation HUD refresh does not count wall clock down");}
    const auto events=wave_native_events;h.event(root.control,14,2);check(wave_native_events==events+1 && h.submits==0 && h.opens==0,"timer never interprets clicks or opens native selection menus");
    std::thread foreign([&]{h.ui.set_wave_timer("foreign");});foreign.join();check(text(label)=="공세 출발 02:34","foreign thread cannot write native timer");
    h.ui.set_wave_timer("공세 출발 00:10");check(text(label)=="공세 출발 00:10","pending death reinforcement display replaces later scheduled departure");
    h.ui.set_wave_timer("공세 대기 · 기지 도착 후");check(text(label)=="공세 대기 · 기지 도착 후","T01 home gate has an explicit waiting label");
    h.active=false;h.pulse();h.ui.set_wave_timer("");check(!(label.flags&2),"inactive campaign timer is hidden");h.active=true;
    h.ui.set_wave_timer("공세 출발 00:01");h.ui.reset_session();check(!(label.flags&2),"same-game session reset immediately hides old timer");
    h.ui.set_callbacks(h.callbacks());h.ui.set_wave_timer("공세 출발 00:40");check(text(label)=="공세 출발 00:40","new session updates only its retained valid HUD");
    check(std::memcmp(&root.control.area,&parent_rect,sizeof(parent_rect))==0,"HUD parent geometry remains constructor-owned");
    h.event(root.control,14,1);check(root.control.event_handler==wave_native_event,"timer restores native root handler before delete");
    std::memset(&root,0xcc,sizeof(root));std::memset(&label,0xcc,sizeof(label));h.ui.set_wave_timer("공세 출발 00:30");h.pulse();
    check(h.submits==0 && h.opens==0,"deleted native timer pointers are never reused by later refresh");
}

struct CargoModel {std::uint64_t token=123;U32 page=0,passengers=6,toggles=0;bool available=true;U32 pages=2;};
CargoModel cargo_model;
bool cargo_state(void*,std::uint64_t* token,U32* page,U32* passengers){if(!cargo_model.available)return false;*token=cargo_model.token;*page=cargo_model.page;*passengers=cargo_model.passengers;return true;}
bool cargo_toggle(void*,std::uint64_t token){if(!cargo_model.available || token!=cargo_model.token)return false;++cargo_model.toggles;cargo_model.page=(cargo_model.page+1)%cargo_model.pages;return true;}
bool cargo_state_v2(void* ctx,std::uint64_t* token,U32* page,U32* pages,U32* passengers){*pages=cargo_model.pages;return cargo_state(ctx,token,page,passengers);}
unsigned cargo_native_events=0;
U32 __cdecl cargo_native_event(dialog::Control*,dialog::Event*){++cargo_native_events;return 41;}
void cargo_page_button_test(){
    ++groups;Host h;bind_api(h);cargo_model={};auto callbacks=h.callbacks();callbacks.cargo_state=cargo_state;callbacks.cargo_toggle=cargo_toggle;
    check(h.ui.initialize(&h.api,callbacks),"cargo HUD registers through original native constructor");
    U32 size=0;auto bytes=h.ui.file_read(reinterpret_cast<const std::uint8_t*>("rez/statfluf.ui.json"),&size);check(bytes && size,"cargo constructor bytes available");std::string payload(reinterpret_cast<const char*>(bytes),size);HeapFree(GetProcessHeap(),0,bytes);
    check(payload.find("\"type\":\"PUSHBUTTON\"")!=std::string::npos && payload.find("\"id\":-31999")!=std::string::npos,"dedicated native PUSHBUTTON has distinct ID");
    dialog::Dialog root{};dialog::Control placeholder{},label{},button{};std::array<std::uint8_t,80> label_buffer{},button_buffer{};
    text(root.control,"StatFluf");root.control.area={0,0,247,147};root.control.event_handler=wave_native_event;root.first_child=&placeholder;
    placeholder.parent=&root;placeholder.next=&label;placeholder.id=-1;placeholder.area={0,0,3,3};text(placeholder,"original");
    label.parent=&root;label.next=&button;label.id=-32000;label.type=6;label.area={8,128,239,147};label.string.data=label_buffer.data();label.string.capacity=79;
    button.parent=&root;button.id=-31999;button.type=1;button.area={8,104,239,123};button.event_handler=cargo_native_event;button.string.data=button_buffer.data();button.string.capacity=79;
    const auto original_placeholder=placeholder;const auto original_button_area=button.area;
    h.ui.set_wave_timer("공세 출발 02:34");h.ui.spawn_dialog(&root,0,reinterpret_cast<void*>(wave_native_event),native_spawn);
    check((button.flags&2) && !(button.flags2&1) && text(button)=="추가 승객 보기","six two-space passengers expose second page, despite count below nine");check(text(label)=="공세 출발 02:34","cargo does not overwrite wave timer");
    h.event(button,4);h.event(button,14,2);check(cargo_model.toggles==1 && cargo_model.page==1 && text(button)=="앞쪽 승객 보기","one click changes to later cargo page and updates return label");
    h.event(button,4);cargo_model.token=456;h.pulse();h.event(button,14,2);check(cargo_model.toggles==1,"selection changed after mouse-down cannot toggle another transport");
    h.event(button,4);h.event(button,14,2);check(cargo_model.toggles==2 && cargo_model.page==0,"fresh click works for new selection");
    cargo_model.available=false;h.pulse();check(!(button.flags&2) && (button.flags2&1),"no expanded owned selection hides and disables page button");h.event(button,14,2);check(cargo_model.toggles==2,"hidden button ignores stale activation");
    cargo_model.available=true;h.pulse();const auto before=cargo_native_events;h.event(button,5);check(cargo_native_events==before+1,"unowned mouse-up rendering delegates to original native child");
    const auto events=wave_native_events;h.event(root.control,14,2);check(wave_native_events==events+1 && cargo_model.toggles==2,"root notification is never guessed as cargo command");
    std::thread foreign([&]{h.event(button,14,2);});foreign.join();check(cargo_model.toggles==2,"foreign thread cannot toggle cargo");
    check(std::memcmp(&placeholder,&original_placeholder,sizeof(placeholder))==0 && std::memcmp(&button.area,&original_button_area,sizeof(button.area))==0,"placeholder and constructor-owned button geometry remain unchanged");
    h.ui.reset_session();check(!(button.flags&2),"session reset immediately hides cargo button");h.ui.set_callbacks(callbacks);h.pulse();check(button.flags&2,"new authenticated session can reuse revalidated HUD");
    callbacks.cargo_state_v2=cargo_state_v2;cargo_model.page=0;cargo_model.pages=3;cargo_model.passengers=16;h.ui.set_callbacks(callbacks);h.pulse();
    check((button.flags&2) && text(button)=="승객 목록 넘기기 (1/3)","logical16 mixed-space cargo exposes three native HUD pages");
    h.event(button,4);h.event(button,14,2);check(cargo_model.page==1 && text(button)=="승객 목록 넘기기 (2/3)","second of three pages is labelled accurately");
    h.event(button,4);h.event(button,14,2);check(cargo_model.page==2 && text(button)=="승객 목록 넘기기 (3/3)","third native window remains clickable");
    h.event(button,4);h.event(button,14,2);check(cargo_model.page==0 && text(button)=="승객 목록 넘기기 (1/3)","three-page native button cycles to first window");
    cargo_model.pages=4;h.pulse();check(!(button.flags&2),"invalid cargo page count hides callback output");cargo_model.pages=3;cargo_model.passengers=17;h.pulse();check(!(button.flags&2),"logical capacity guard rejects more than16 passengers");cargo_model.passengers=16;h.pulse();check(button.flags&2,"valid logical16 metadata restores the native button");
    const auto total_toggles=cargo_model.toggles;
    h.event(root.control,14,1);check(root.control.event_handler==wave_native_event && button.event_handler==cargo_native_event,"both root and added button delegates restored before native delete");
    std::memset(&root,0xcc,sizeof(root));std::memset(&button,0xcc,sizeof(button));h.pulse();check(cargo_model.toggles==total_toggles,"deleted widget memory is not reused");
}

}
void bundled_legendary_pages_test() {
    ++groups;
    const unsigned ids[]={300,301,302,303,304,305,341,342,343,344,345,346,383,384,385,386,387,388};
    for(auto left:ids)for(auto right:ids){
        if(!legendary_bundles::compatible(left,right))continue;
        Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"bundle UI initialized");
        h.show();h.offer.wire_version=2;h.offer.count=2;h.offer.candidates[0]=left;h.offer.partners[0]=right;h.offer.candidates[1]=257;
        for(unsigned i=2;i<4;i++)h.offer.candidates[i]=0;h.ui.show(h.offer);
        h.actions=[&]{
            const auto intro=h.paint(-1);check(intro.find(frozen::talent_names[left-1])!=std::string::npos && intro.find(frozen::talent_names[right-1])!=std::string::npos,"both names on persisted option");
            h.preview(1);check(h.paint(-1).find(frozen::talent_names[left-1])!=std::string::npos,"first complete member shown");
            check(no_spaces(h.paint(-1)).find(no_spaces(frozen::talent_effects[left-1]))!=std::string::npos,"first effect not clipped");
            h.confirm();check(h.submits==0&&!h.ui.waiting(),"first click moves to second explanation");
            check(no_spaces(h.paint(-1)).find(no_spaces(frozen::talent_effects[right-1]))!=std::string::npos,"second effect not clipped");
            h.confirm();check(h.submits==1&&h.last_slot==1,"both effects confirmed through one durable choice");h.finish();
        };open(h);
    }
}
void checkpoint_v2_small_curse_lists_test() {
    ++groups;
    for(unsigned count=1;count<=3;++count) {
        Host h;bind_api(h);check(h.ui.initialize(&h.api,h.callbacks()),"checkpoint UI hooks installed");
        h.show(2,count,4);h.offer.wire_version=2;h.offer.phase_version=2;h.offer.count=count;
        for(unsigned i=count;i<4;++i)h.offer.candidates[i]=0;
        h.ui.show(h.offer);h.actions=[&] {
            check(h.ui.pending() && h.ui.open(),"phase4 curse list opens with available candidates");
            h.preview(1);h.confirm();check(h.submits==1 && h.last_slot==1,"phase4 curse confirms one durable slot");
            h.finish();
        };
        open(h);check(!h.ui.open() && h.resumes==1,"small curse list resumes after confirmation");
    }
}
int main(int argc,char** argv) {try {if(argc==2 && std::strcmp(argv[1],"native_metadata")==0)native_sized_metadata_test();else if(argc==2 && std::strcmp(argv[1],"spawn_no_delete")==0)spawn_no_delete_test();else {api_test();bundled_legendary_pages_test();checkpoint_v2_small_curse_lists_test();catalog_test();spawn_reinit_test();stale_test();text_failure_test();phases_auto_test();standalone_legendary_v2_test();stock_depth_test();hud_test();thread_delete_test();legacy_test();backed_panel_test();render_lifetime_test();hotkey_render_test();constructor_file_test();native_sized_metadata_test();spawn_no_delete_test();independent_wave_timer_test();cargo_page_button_test();}std::cout<<"{\"passed\":true,\"groups\":"<<groups<<",\"assertions\":"<<assertions<<"}\n";return 0;}catch(const std::exception& e) {std::cerr<<"FAILED: "<<e.what()<<'\n';return 1;}}
