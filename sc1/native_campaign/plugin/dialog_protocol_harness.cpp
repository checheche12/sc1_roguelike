// Offline C++ host for the real DialogUi + MailboxProtocol translation units.
// All controls, strings and mailbox memory are owned here. No game is opened.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <array>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <thread>
#include "dialog_ui.h"

namespace {
using U32 = std::uint32_t;
using U8 = std::uint8_t;
using namespace sc1_native;
using RunHook=U32 (__cdecl*)(void*,std::size_t,void*,dialog::RunOriginal);
using FileHook=U8* (__cdecl*)(const U8*,U32*);
using ProcessOriginal=std::size_t (__cdecl*)(std::size_t);
using ProcessHook=std::size_t (__cdecl*)(std::size_t,ProcessOriginal);
constexpr std::array<std::int16_t, 11> kIds{{-3,-1,1,2,3,4,5,6,7,8,9}};
struct Host {
    MailboxProtocol protocol;
    DialogUi ui;
    dialog::Dialog menu{};
    dialog::Dialog hud{};
    dialog::Control hud_button{};
    std::array<dialog::Control,11> controls{};
    std::array<dialog::Control,11> original_controls{};
    dialog::Rect original_root_area{};
    std::array<U8,248*208> header_surface_pixels{};
    std::array<U8,512> native_body_storage{};
    std::string template_body;
    U32 file_registrations=0,template_reads=0;
    bool template_provided=false;
    U32 layout_checks=0,restoration_checks=0,reinitializations=0;
    bool geometry_saved=false,header_surface=false;
    std::array<std::array<U8,1024>,12> strings{};
    samase::PluginApi api{};
    RunHook run_hook=nullptr;
    RunHook spawn_hook=nullptr;
    FileHook file_hook=nullptr;
    ProcessHook process_hook=nullptr;
    dialog::LayoutTextHook layout_hook=nullptr;
    U32 layout_registrations=0,render_calls=0;
    std::array<std::string,11> rendered{};
    std::string last_rendered,retained_contents;
    const U8* returned_suffix=nullptr;
    const U8* retained_suffix=nullptr;
    U32 draw_d=23,draw_f=29;
    std::uint64_t now = 1000;
    DWORD thread_id = GetCurrentThreadId();
    U32 applies=0,offers=0,clears=0,resumes=0,errors=0,frame_count=123;
    U32 pump_calls=0,recursive_blocked=0,thread_violations=0,resume_before_publication=0;
    U32 process_original_calls=0;
    U32 error_dismisses=0,stock_action_attempts=0;
    U32 auto_opens=0,constructors=0,post_construct_binds=0,cleanups=0,nested_process_calls=0;
    U32 run_entries=0,spawn_entries=0,spawn_returns=0,spawn_closes=0,native_delete_events=0;
    bool spawn_no_delete=false;
    bool phased=false,inside_auto=false,stock_fallback=false;
    U32 stock_cleanups=0;
    bool modal=false,close_requested=false,pumping=false,quitting=false,active=true;
    std::string last_report;
} host;

void require(bool value,const char* detail) { if(!value) throw std::runtime_error(detail); }
void json_string(const std::string& value) {
    constexpr char hex[]="0123456789abcdef";
    std::cout<<'"';
    for(unsigned char byte:value) {
        if(byte=='"' || byte=='\\')std::cout<<'\\'<<static_cast<char>(byte);
        else if(byte<32)std::cout<<"\\u00"<<hex[byte>>4]<<hex[byte&15];
        else std::cout<<static_cast<char>(byte);
    }
    std::cout<<'"';
}
void dump() {
    std::cout << "{\"words\":[";
    for(int i=0;i<64;++i) {if(i)std::cout<<',';std::cout<<host.protocol.mailbox_words()[i];}
    std::cout << "],\"modal_open\":" << host.modal
        << ",\"dialog_open\":" << host.ui.open()
        << ",\"waiting\":" << host.ui.waiting()
        << ",\"pending\":" << host.ui.pending()
        << ",\"applies\":" << host.applies << ",\"offers\":" << host.offers
        << ",\"clears\":" << host.clears << ",\"resumes\":" << host.resumes
        << ",\"errors\":" << host.errors << ",\"frame_count\":" << host.frame_count
        << ",\"pump_calls\":" << host.pump_calls
        << ",\"recursive_blocked\":" << host.recursive_blocked
        << ",\"thread_violations\":" << host.thread_violations
        << ",\"resume_before_publication\":" << host.resume_before_publication
        << ",\"process_original_calls\":" << host.process_original_calls
        << ",\"error_dismisses\":" << host.error_dismisses
        << ",\"stock_action_attempts\":" << host.stock_action_attempts
        << ",\"previewing\":" << host.ui.previewing()
        << ",\"auto_opens\":" << host.auto_opens
        << ",\"constructors\":" << host.constructors
        << ",\"post_construct_binds\":" << host.post_construct_binds
        << ",\"cleanups\":" << host.cleanups
        << ",\"nested_process_calls\":" << host.nested_process_calls
        << ",\"run_entries\":" << host.run_entries
        << ",\"spawn_entries\":" << host.spawn_entries
        << ",\"spawn_returns\":" << host.spawn_returns
        << ",\"spawn_closes\":" << host.spawn_closes
        << ",\"native_delete_events\":" << host.native_delete_events
        << ",\"inside_auto\":" << host.inside_auto
        << ",\"stock_fallback\":" << host.stock_fallback
        << ",\"stock_cleanups\":" << host.stock_cleanups
        << ",\"confirm_disabled\":" << bool(host.controls[0].flags2&1u)
        << ",\"layout_registrations\":" << host.layout_registrations
        << ",\"render_calls\":" << host.render_calls
        << ",\"layout_checks\":" << host.layout_checks
        << ",\"restoration_checks\":" << host.restoration_checks
        << ",\"reinitializations\":" << host.reinitializations
        << ",\"header_surface\":" << host.header_surface
        << ",\"file_registrations\":" << host.file_registrations
        << ",\"template_reads\":" << host.template_reads
        << ",\"template_provided\":" << host.template_provided
        << ",\"template_body\":";
    json_string(host.template_body);
    std::cout<<",\"native_body\":";
    const auto& body=host.controls[1];
    json_string(body.string.data?std::string(reinterpret_cast<const char*>(body.string.data),body.string.length):std::string());
    std::cout<<",\"native_body_capacity\":"<<(body.string.capacity&~(std::size_t(1)<<63))
        << ",\"rendered_texts\":[";
    for(std::size_t i=0;i<host.rendered.size();++i) {if(i)std::cout<<',';json_string(host.rendered[i]);}
    std::cout<<"],\"victory_ready\":" << host.protocol.victory_ack_ready() << "}\n" << std::flush;
}

bool can_resume(void*) {
    return host.active && !host.pumping && host.protocol.growth_applied()
        && !host.protocol.failed() && host.protocol.mailbox_words()[19]==1;
}
bool active(void*) { return host.active; }
void report(void*,const char* message) { host.last_report=message?message:""; }
bool submit(void*,U32 slot) {
    if(GetCurrentThreadId()!=host.thread_id) {++host.thread_violations;return false;}
    return host.protocol.submit_choice(slot);
}
void protocol_pump(void*) {
    if(GetCurrentThreadId()!=host.thread_id) {++host.thread_violations;return;}
    if(host.pumping) {++host.recursive_blocked;return;}
    host.pumping=true;
    ++host.pump_calls;
    host.protocol.tick();
    host.pumping=false;
}
bool apply(void*,const GrowthSnapshot&) {
    if(GetCurrentThreadId()!=host.thread_id) {++host.thread_violations;return false;}
    ++host.applies;
    // Model a synchronous foreign callback reentering the integration pump.
    protocol_pump(nullptr);
    return true;
}
void show(void*,const ChoiceOffer& offer) {++host.offers;host.ui.show(offer);}
void clear(void*) {++host.clears;host.ui.clear();}
void failed(void*,U32) {++host.errors;host.ui.dismiss_error();}

void require_restored_geometry() {
    require(host.geometry_saved,"constructor geometry not captured");
    require(std::memcmp(&host.menu.control.area,&host.original_root_area,sizeof(dialog::Rect))==0,"root geometry changed");
    for(std::size_t i=0;i<host.controls.size();++i) {
        const auto& c=host.controls[i];const auto& original=host.original_controls[i];
        require(std::memcmp(&c.area,&original.area,sizeof(c.area))==0,"native callback saw changed rectangle");
        require(c.flags==original.flags && c.flags2==original.flags2,"native callback saw changed flags");
        require(std::memcmp(&c.image,&original.image,sizeof(c.image))==0 && c.type==original.type
            && c.draw==original.draw,"native widget surface/type/draw changed");
    }
    ++host.restoration_checks;
}

U32 __cdecl root_original(dialog::Control*,dialog::Event*);
U32 __cdecl child_original(dialog::Control* control,dialog::Event* event) {
    if(control->id==-3 && event->type==dialog::kExtendedEvent && event->ext_type==dialog::kActivateButton) {
        require_restored_geometry();
        if(host.protocol.failed()) ++host.error_dismisses;
        else if(!can_resume(nullptr)) ++host.resume_before_publication;
        ++host.resumes;host.close_requested=true;
        if(host.spawn_no_delete) {
            // The asynchronous engine callback closes the modal and returns;
            // it does not send root Ext1/delete or run a nested cleanup loop.
            for(const auto& c:host.controls)
                require(c.event_handler==child_original,"Spawn Resume reached native code with plugin child handlers still installed");
            require(host.menu.control.event_handler==root_original,"Spawn Resume reached native code with plugin root handler installed");
            ++host.spawn_closes;host.modal=false;
        }
        return dialog::kResumeResult;
    }
    return 0;
}
U32 __cdecl root_original(dialog::Control*,dialog::Event* event) {
    if(event->type==dialog::kExtendedEvent && event->ext_type==1)++host.native_delete_events;
    if(event->type==dialog::kExtendedEvent && event->ext_type==dialog::kActivateButton)
        ++host.stock_action_attempts;
    if(event->type==dialog::kExtendedEvent && (event->ext_type==0 || event->ext_type==7 || event->ext_type==1))
        require_restored_geometry();
    if(event->type==dialog::kExtendedEvent && (event->ext_type==0 || event->ext_type==7))
        for(auto& control:host.controls) control.event_handler=child_original;
    if(event->type==0 && event->param==27) {
        dialog::Event activation{};activation.type=dialog::kExtendedEvent;activation.ext_type=dialog::kActivateButton;
        return host.controls[0].event_handler(&host.controls[0],&activation);
    }
    return 0;
}
dialog::Control& by_id(std::int16_t id) {
    for(auto& c:host.controls) if(c.id==id)return c;
    throw std::runtime_error("missing stock control");
}
void inline_text(dialog::Control& control,const char* value) {
    const auto size=std::strlen(value);require(size<=15,"synthetic SSO overflow");
    control.string.data=control.string.inline_buffer;control.string.capacity=(std::size_t(1)<<63)|15;
    control.string.length=size;std::memcpy(control.string.inline_buffer,value,size+1);
}
std::string constructor_body(const std::string& payload) {
    const std::string marker="\"type\":\"CTEXT\",\"content\":\"";
    const auto start=payload.find(marker);require(start!=std::string::npos,"native CTEXT constructor content missing");
    std::string result;
    for(auto at=start+marker.size();at<payload.size();++at) {
        const char c=payload[at];
        if(c=='"')return result;
        if(c=='\\') {
            require(++at<payload.size(),"truncated native CTEXT JSON escape");
            const char escaped=payload[at];
            result+=escaped=='n'?'\n':escaped=='r'?'\r':escaped=='t'?'\t':escaped;
        } else result+=c;
    }
    throw std::runtime_error("unterminated native CTEXT constructor content");
}
void make_menu() {
    // This occurs before Run's depth guard/constructor. The real file callback
    // supplies JSON only for an active pending offer; ordinary stock menus fall
    // through. Native parsing/allocation is modeled, not executed in a game.
    require(host.file_registrations==2 && host.file_hook,"missing scoped file hooks");
    U32 size=0;
    auto* payload=host.file_hook(reinterpret_cast<const U8*>("rez/gamemenu.ui.json"),&size);
    host.template_provided=payload!=nullptr;host.template_body.clear();
    if(payload) {
        host.template_body=constructor_body(std::string(reinterpret_cast<const char*>(payload),size));
        require(HeapFree(GetProcessHeap(),0,payload)!=0,"synthetic parser could not release file payload");
        ++host.template_reads;
    }
    host.menu={};host.controls={};
    host.geometry_saved=false;
    host.menu.control.area={184,32,447,319};
    inline_text(host.menu.control,"GameMenu");
    host.menu.control.event_handler=root_original;
    // The native Run constructor has not populated the child list yet.
}
void __cdecl synthetic_draw(dialog::Control*,std::int32_t,std::int32_t,const dialog::Rect*,const dialog::Rect*) {}
void construct_menu() {
    ++host.constructors;
    host.menu.first_child=&host.controls[0];
    for(std::size_t i=0;i<host.controls.size();++i) {
        auto& control=host.controls[i];control.id=kIds[i];control.parent=&host.menu;
        control.type=control.id==-1?6:1;
        control.event_handler=child_original;
        control.next=i+1<host.controls.size()?&host.controls[i+1]:nullptr;
        const auto y=static_cast<std::int16_t>(36+(static_cast<int>(i)%7)*32);
        control.area={20,y,243,static_cast<std::int16_t>(y+27)};
        control.flags=control.id==8 || control.id==9?0u:2u;control.flags2=0x20;
        control.draw=synthetic_draw;
        inline_text(control,"Stock");
    }
    by_id(-1).area={0,8,263,31};by_id(-3).area={20,252,243,279};
    if(host.template_provided) {
        require(host.template_body.size()<host.native_body_storage.size(),"meaningful constructor body exceeds synthetic native allocation");
        std::memcpy(host.native_body_storage.data(),host.template_body.c_str(),host.template_body.size()+1);
        auto& body=by_id(-1);body.area={8,8,255,215};body.string.data=host.native_body_storage.data();
        body.string.length=host.template_body.size();body.string.capacity=host.native_body_storage.size()-1;
        constexpr std::int16_t candidate_ids[]{1,2,3,5};
        for(unsigned i=0;i<4;++i) {
            const auto x=static_cast<std::int16_t>(20+56*i);
            by_id(candidate_ids[i]).area={x,220,static_cast<std::int16_t>(x+47),247};
        }
        if(host.header_surface)body.image={248,208,host.header_surface_pixels.data()};
    }
    host.original_controls=host.controls;host.original_root_area=host.menu.control.area;host.geometry_saved=true;
}

void require_choice_layout() {
    require(host.modal && host.ui.open(),"layout check without bound modal");
    require(std::memcmp(&host.menu.control.area,&host.original_root_area,sizeof(dialog::Rect))==0,"choice layout resized original root");
    constexpr std::int16_t ids[]{1,2,3,5};
    for(unsigned i=0;i<4;++i) {
        const auto& area=by_id(ids[i]).area;
        require(area.left==20+56*int(i) && area.right==67+56*int(i) && area.top==220 && area.bottom==247,"native number button bounds invalid");
    }
    const auto& confirm=by_id(-3).area;
    require(confirm.left==20 && confirm.right==243 && confirm.top==252 && confirm.bottom==279,"confirmation bounds invalid");
    const auto& header=by_id(-1).area;
    require(header.left==8 && header.top==8 && header.right==255 && header.bottom==215,"native CTEXT body bounds invalid");
    constexpr std::array<std::int16_t,6> visible{{-1,1,2,3,5,-3}};
    const unsigned count=static_cast<unsigned>(visible.size());
    for(unsigned i=0;i<count;++i) {
        const auto& a=by_id(visible[i]).area;
        require(a.left>=0 && a.top>=0 && a.right<264 && a.bottom<288,"visible control outside root");
        for(unsigned j=i+1;j<count;++j) {
            const auto& b=by_id(visible[j]).area;
            require(a.right<b.left || b.right<a.left || a.bottom<b.top || b.bottom<a.top,"upper panel and choices overlap");
        }
    }
    for(std::size_t i=0;i<host.controls.size();++i) {
        const auto& c=host.controls[i];const auto& original=host.original_controls[i];
        require(std::memcmp(&c.image,&original.image,sizeof(c.image))==0 && c.type==original.type
            && c.draw==original.draw,"choice layout changed surface/type/draw");
        require(std::memcmp(&c.area,&original.area,sizeof(c.area))==0,"post-constructor code resized or moved native widgets");
    }
    for(const auto id:{4,7,8,9,6})require(!(by_id(static_cast<std::int16_t>(id)).flags&2u),"button-label body fallback or unrelated stock action is visible");
    require(by_id(-1).string.data==host.native_body_storage.data() && by_id(-1).string.capacity==511,
            "original native CTEXT allocation ownership changed");
    ++host.layout_checks;
}

bool command(const std::string& line);
std::size_t __cdecl process_original(std::size_t flags) {
    ++host.process_original_calls;if(host.modal && host.inside_auto)++host.nested_process_calls;
    return flags+7;
}
U32 __cdecl run_original(void*,std::size_t,void* handler) {
    ++host.run_entries;
    host.modal=true;host.close_requested=false;
    host.menu.control.event_handler=reinterpret_cast<dialog::EventHandler>(handler);
    construct_menu();
    dialog::Event init{};init.type=dialog::kExtendedEvent;init.ext_type=7;
    host.menu.control.event_handler(&host.menu.control,&init);init.ext_type=0;
    host.menu.control.event_handler(&host.menu.control,&init);
    for(const auto& c:host.controls)require(c.event_handler==child_original,"binding before constructor completed");
    Sleep(55);
    require(host.process_hook(123,process_original)==130,"post-construction ProcessEvents return");
    if(!host.stock_fallback) {
        require(by_id(1).event_handler!=child_original,"post-construction controls were not bound");
        ++host.post_construct_binds;
    }
    dump();
    std::string line;
    while(!host.close_requested && std::getline(std::cin,line)) {
        if(!command(line)) break;
    }
    dialog::Event deleted{};deleted.type=14;deleted.ext_type=1;
    host.menu.control.event_handler(&host.menu.control,&deleted);
    for(const auto& c:host.controls) require(c.event_handler==child_original,"stock child delegate not restored before deletion");
    if(host.stock_fallback)++host.stock_cleanups;else ++host.cleanups;
    host.modal=false;
    return host.close_requested?dialog::kResumeResult:0;
}
U32 __cdecl spawn_menu_original(void*,std::size_t,void* handler) {
    ++host.spawn_entries;host.modal=true;host.close_requested=false;
    host.menu.control.event_handler=reinterpret_cast<dialog::EventHandler>(handler);
    construct_menu();
    dialog::Event init{};init.type=14;init.ext_type=7;
    host.menu.control.event_handler(&host.menu.control,&init);init.ext_type=0;
    host.menu.control.event_handler(&host.menu.control,&init);
    for(const auto& c:host.controls)
        require(c.event_handler==child_original,"Spawn binding preceded original constructor return");
    // No stdin loop and no ProcessEvents call: Spawn returns immediately. The
    // main host loop models subsequent engine events while gameplay is paused.
    return 1;
}
U32 __cdecl hud_original(dialog::Control*,dialog::Event* event) {
    if(event->type==14 && event->ext_type==2) {
        require(!host.modal && !host.inside_auto,"recursive auto-open");
        ++host.auto_opens;host.inside_auto=true;make_menu();
        if(host.spawn_no_delete) {
            require(host.spawn_hook(&host.menu,0,reinterpret_cast<void*>(&root_original),spawn_menu_original)==1,"Spawn GameMenu return changed");
            require(host.ui.open() && by_id(1).event_handler!=child_original,"Spawn post-construction controls were not bound");
            ++host.post_construct_binds;++host.spawn_returns;
        } else host.run_hook(&host.menu,0,reinterpret_cast<void*>(&root_original),run_original);
        host.inside_auto=false;
    }
    return 0;
}
U32 __cdecl spawn_original(void*,std::size_t,void*) {
    host.hud_button={};host.hud_button.id=1;host.hud_button.type=2;
    host.hud_button.parent=&host.hud;host.hud_button.flags=2;
    host.hud_button.event_handler=hud_original;host.hud.first_child=&host.hud_button;
    host.hud.control.event_handler=hud_original;return 1;
}
void click(dialog::Control& c) {
    dialog::Event event{};event.type=4;c.event_handler(&c,&event);
    event.type=dialog::kExtendedEvent;event.ext_type=dialog::kActivateButton;c.event_handler(&c,&event);
}
const U8* __cdecl draw_original(U32 a,U32 b,const U8* text,U32* d,U32 draw,U32* f,U32 g,U32 h) {
    require(a==11 && b==13 && d==&host.draw_d && draw==17 && f==&host.draw_f && g==19 && h==31,"layout arguments changed");
    ++host.render_calls;host.last_rendered=reinterpret_cast<const char*>(text);
    host.returned_suffix=text+(host.last_rendered.empty()?0:1);return host.returned_suffix;
}
const U8* __cdecl draw_passthrough(U32 a,U32 b,const U8* text,U32* d,U32 draw,U32* f,U32 g,U32 h) {
    require(a==11 && b==13 && d==&host.draw_d && draw==17 && f==&host.draw_f && g==19 && h==31,"fallback layout arguments changed");
    return text;
}
const U8* render(const U8* text,dialog::LayoutTextOriginal original=draw_original) {
    require(host.layout_hook!=nullptr,"missing LayoutDrawText hook");
    return host.layout_hook(11,13,text,&host.draw_d,17,&host.draw_f,19,31,original);
}
void render_all(bool foreign,bool exact=false) {
    const auto before=host.controls;
    const auto body_before=host.native_body_storage;
    std::array<const U8*,11> pointers{};
    // Model native RC_HOTKEY preprocessing: PUSHBUTTON layout receives the
    // pointer after its one-byte hotkey marker; CTEXT receives the exact base.
    for(std::size_t i=0;i<pointers.size();++i)
        pointers[i]=host.controls[i].string.data+(!exact && host.controls[i].id!=-1?1:0);
    const auto work=[&] {
        for(std::size_t i=0;i<pointers.size();++i) {
            require(render(pointers[i])==host.returned_suffix,"layout original return changed");
            host.rendered[i]=host.last_rendered;
        }
        const auto* poison=reinterpret_cast<const U8*>(std::uintptr_t(1));
        require(render(poison,draw_passthrough)==poison,"unmatched layout pointer changed or dereferenced");
    };
    if(foreign) {std::thread worker(work);worker.join();} else work();
    require(std::memcmp(host.controls.data(),before.data(),sizeof(before))==0,"renderer mutated native control/buffer/geometry");
    require(host.native_body_storage==body_before,"renderer mutated the native CTEXT allocation");
}
bool command(const std::string& line) {
    std::istringstream in(line);std::string op;in>>op;
    if(op=="QUIT") {host.quitting=true;host.close_requested=true;return false;}
    if(op=="PUMP") {
        U32 milliseconds=0;in>>milliseconds;require(milliseconds<=1000,"pump too long");Sleep(milliseconds);
        require(host.process_hook(123,process_original)==130,"ProcessEvents original return changed");
        host.now=GetTickCount64();
    } else if(op=="EVENT_PUMP") {
        require(host.process_hook!=nullptr,"missing ProcessEvents hook");
        require(host.process_hook(123,process_original)==130,"ProcessEvents original return changed");
        host.now=GetTickCount64();
    } else if(op=="THREAD_GUARD") {
        U32 result=99;
        std::thread other([&] {
            host.ui.pump(host.now+100);
            result=host.ui.event(reinterpret_cast<dialog::Control*>(std::uintptr_t(1)),
                                 reinterpret_cast<dialog::Event*>(std::uintptr_t(1)));
        });
        other.join();require(result==0,"foreign UI event was accepted");
    } else if(op=="RESPONSE") {
        auto* words=host.protocol.mailbox_words();
        std::array<U32,32> reply{};for(auto& value:reply)require(bool(in>>value),"short RESPONSE");
        words[32]=reply[0]|1u;for(int i=1;i<32;++i)words[32+i]=reply[i];MemoryBarrier();words[32]=reply[0];
    } else if(op=="OPEN" || op=="OPEN_STOCK") {
        require(!host.modal,"recursive OPEN");make_menu();
        host.stock_fallback=op=="OPEN_STOCK";
        require(host.template_provided!=host.stock_fallback,"scoped native file callback ownership mismatch");
        host.run_hook(&host.menu,0,reinterpret_cast<void*>(&root_original),run_original);
        host.stock_fallback=false;
        if(host.quitting)return false;
        dump();return true;
    } else if(op=="SPAWN_HUD") {
        host.hud={};inline_text(host.hud.control,"Stat_F10");
        require(host.spawn_hook(&host.hud,0,reinterpret_cast<void*>(&hud_original),spawn_original)==1,"Spawn return changed");
    } else if(op=="CLICK" || op=="DOWN" || op=="UP") {
        U32 slot=0;in>>slot;require(slot>=1 && slot<=4,"invalid click slot");
        require(host.modal && host.ui.open(),"click without modal");
        constexpr std::int16_t ids[]{1,2,3,5};auto& control=by_id(ids[slot-1]);dialog::Event event{};
        if(op!="UP") {event.type=4;control.event_handler(&control,&event);}
        if(op!="DOWN") {
            event.type=dialog::kExtendedEvent;event.ext_type=dialog::kActivateButton;
            control.event_handler(&control,&event);
        }
    } else if(op=="CONFIRM") {
        require(host.modal,"confirm without modal");click(by_id(-3));
    } else if(op=="SHORT_BUTTONS") {
        require(host.modal,"details fixture without modal");
        for(const auto id:{-3,1,2,3,5}) {
            auto& c=by_id(static_cast<std::int16_t>(id));
            c.string.length=0;c.string.inline_buffer[0]=0;c.string.capacity=(std::size_t(1)<<63)|3;
        }
    } else if(op=="RENDER_EXACT") {
        render_all(false,true);
    } else if(op=="RENDER" || op=="RENDER_FOREIGN") {
        render_all(op=="RENDER_FOREIGN");
    } else if(op=="LAYOUT") {
        require_choice_layout();
    } else if(op=="REINIT") {
        require(host.modal && host.ui.open(),"reinit without bound modal");
        dialog::Event init{};init.type=14;init.ext_type=7;
        host.menu.control.event_handler(&host.menu.control,&init);init.ext_type=0;
        host.menu.control.event_handler(&host.menu.control,&init);++host.reinitializations;
    } else if(op=="RETAIN") {
        int id=0;in>>id;host.retained_suffix=render(by_id(static_cast<std::int16_t>(id)).string.data);
        host.retained_contents=reinterpret_cast<const char*>(host.retained_suffix);
    } else if(op=="RETAIN_CHECK") {
        const auto* poison=reinterpret_cast<const U8*>(std::uintptr_t(1));
        require(render(poison,draw_passthrough)==poison,"unmatched layout pointer changed");
        require(host.retained_suffix && host.retained_contents==reinterpret_cast<const char*>(host.retained_suffix),"returned suffix expired after render generation changed");
    } else if(op=="BACK") {
        require(host.modal,"back without modal");click(by_id(7));
    } else if(op=="CLOSE_STOCK") {
        require(host.modal && host.stock_fallback,"not a stock fallback modal");host.close_requested=true;
    } else if(op=="ESC") {
        dialog::Event event{};event.type=0;event.param=27;
        host.menu.control.event_handler(&host.menu.control,&event);
    } else if(op=="RESUME_ATTEMPT") {
        dialog::Event event{};event.type=dialog::kExtendedEvent;event.ext_type=dialog::kActivateButton;
        host.controls[0].event_handler(&host.controls[0],&event);
    } else if(op=="ROOT_ACTIVATE") {
        U32 id=0;in>>id;dialog::Event event{};
        event.type=dialog::kExtendedEvent;event.ext_type=dialog::kActivateButton;event.ext_param=id;
        host.menu.control.event_handler(&host.menu.control,&event);
    } else if(op=="GOAL") {
        host.protocol.on_goal_reached();
    } else if(op=="PHASE") {
        U32 phase=0;in>>phase;require(host.protocol.request_phase(phase),"invalid phase transition");
    } else if(op!="DUMP") throw std::runtime_error("unknown command");
    if(!host.close_requested || !host.modal)dump();
    return true;
}
U32 __cdecl register_run(RunHook hook) {host.run_hook=hook;return 1;}
U32 __cdecl register_spawn(RunHook hook) {host.spawn_hook=hook;return 1;}
U32 __cdecl register_layout(dialog::LayoutTextHook hook) {host.layout_hook=hook;++host.layout_registrations;return 1;}
void __cdecl register_file(const U8* prefix,FileHook hook) {
    const std::string name=reinterpret_cast<const char*>(prefix);
    require(name==(host.file_registrations?"rez/gamemenusocial.ui.json":"rez/gamemenu.ui.json"),"unexpected file callback scope/order");
    require(host.file_registrations<2,"duplicate constructor file registration");
    ++host.file_registrations;host.file_hook=hook;
}
U32 __cdecl register_function(std::uint16_t id,std::size_t hook) {
    require(id==static_cast<std::uint16_t>(samase::FuncId::ProcessEvents),"wrong function hook");
    host.process_hook=reinterpret_cast<ProcessHook>(hook);return 1;
}
}

int main(int argc,char** argv) {
    try {
        for(int i=1;i<argc;++i) {
            const std::string arg=argv[i];
            if(arg=="--phased")host.phased=true;
            else if(arg=="--header-surface")host.header_surface=true;
            else if(arg=="--spawn-no-delete")host.spawn_no_delete=true;
            else throw std::runtime_error("unknown host mode");
        }
        DialogUiCallbacks callbacks{nullptr,submit,protocol_pump,active,can_resume,report};
        host.api.version=44;host.api.max_func_id=80;
        host.api.hook_run_dialog=reinterpret_cast<samase::GenericFn>(&register_run);
        host.api.hook_spawn_dialog=reinterpret_cast<samase::GenericFn>(&register_spawn);
        host.api.hook_layout_draw_text=reinterpret_cast<samase::GenericFn>(&register_layout);
        host.api.hook_file_read=reinterpret_cast<samase::GenericFn>(&register_file);
        host.api.hook_func=reinterpret_cast<samase::GenericFn>(&register_function);
        require(host.ui.initialize(&host.api,callbacks),"dialog initialization failed");
        require(host.protocol.initialize({nullptr,apply,show,clear,failed},101,host.phased),"protocol initialize failed");
        dump();std::string line;
        while(!host.quitting && std::getline(std::cin,line))if(!command(line))break;
        host.active=false;host.ui.reset_session();host.protocol.shutdown();
        return 0;
    } catch(const std::exception& error) {
        std::cerr<<error.what()<<'\n';return 1;
    }
}
