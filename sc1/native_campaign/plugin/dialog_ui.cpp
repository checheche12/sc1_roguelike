#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#include "dialog_ui.h"
#include "include/legendary_bundles.generated.h"
#include "include/frozen_catalog.generated.h"
#include "include/wave_timer_asset.generated.h"
#include "../dialog_assets/plain_panel_templates.generated.h"
#include <algorithm>
#include <cstring>
#include <limits>
#include <cstdio>

namespace sc1_native {
namespace {
std::atomic<DialogUi*> installed{nullptr};
constexpr std::int16_t candidate_ids[]{1,2,3,5};
constexpr std::size_t inline_flag = std::size_t(1) << 63;
using RegisterDialog = std::uint32_t (__cdecl*)(std::uint32_t (__cdecl*)(void*,std::size_t,void*,dialog::RunOriginal));
using RegisterFunction = std::uint32_t (__cdecl*)(std::uint16_t,std::size_t);
using ProcessOriginal = std::size_t (__cdecl*)(std::size_t);
using RegisterLayoutText = std::uint32_t (__cdecl*)(dialog::LayoutTextHook);

bool memory_range(const void* raw,std::size_t length,bool writable=false) noexcept {
    auto start=reinterpret_cast<std::uintptr_t>(raw);
    if(!start || !length || start>(std::numeric_limits<std::uintptr_t>::max)()-length) return false;
    const auto end=start+length;
    while(start<end) {
        MEMORY_BASIC_INFORMATION page{};
        if(!VirtualQuery(reinterpret_cast<const void*>(start),&page,sizeof(page))
            || page.State!=MEM_COMMIT || (page.Protect&(PAGE_GUARD|PAGE_NOACCESS))) return false;
        const auto mode=page.Protect&0xff;
        const bool can_write=mode==PAGE_READWRITE || mode==PAGE_WRITECOPY
            || mode==PAGE_EXECUTE_READWRITE || mode==PAGE_EXECUTE_WRITECOPY;
        if(writable ? !can_write : !(can_write || mode==PAGE_READONLY || mode==PAGE_EXECUTE_READ)) return false;
        const auto next=reinterpret_cast<std::uintptr_t>(page.BaseAddress)+page.RegionSize;
        if(next<=start) return false;
        start=(std::min)(end,next);
    }
    return true;
}
bool executable(dialog::EventHandler fn) noexcept {
    MEMORY_BASIC_INFORMATION page{};
    if(!fn || !VirtualQuery(reinterpret_cast<const void*>(fn),&page,sizeof(page))
        || page.State!=MEM_COMMIT || (page.Protect&(PAGE_GUARD|PAGE_NOACCESS))) return false;
    const auto mode=page.Protect&0xff;
    return mode==PAGE_EXECUTE || mode==PAGE_EXECUTE_READ
        || mode==PAGE_EXECUTE_READWRITE || mode==PAGE_EXECUTE_WRITECOPY;
}
std::size_t capacity(const dialog::Control* c) noexcept {
    if(!memory_range(c,sizeof(*c))) return 0;
    const auto amount=c->string.capacity&~inline_flag;
    if(!c->string.data || amount>1024*1024 || c->string.length>amount) return 0;
    // An inline data pointer must remain wholly inside the actual 16-byte SSO
    // member. The ownership high-bit alone is not proof that data is inline.
    const auto pointer=reinterpret_cast<std::uintptr_t>(c->string.data);
    const auto inline_begin=reinterpret_cast<std::uintptr_t>(c->string.inline_buffer);
    if(pointer>=inline_begin && pointer<inline_begin+16
        && (pointer!=inline_begin || amount>15)) return 0;
    return amount;
}
bool named(const dialog::Dialog* root,const char* name) noexcept {
    if(!memory_range(root,sizeof(*root))) return false;
    const auto length=std::strlen(name);
    return capacity(&root->control)>=length && root->control.string.length==length
        && memory_range(root->control.string.data,length)
        && std::memcmp(root->control.string.data,name,length)==0;
}
bool write_text(dialog::Control* c,const std::string& value) noexcept {
    if(!memory_range(c,sizeof(*c),true) || capacity(c)<value.size()
        || !memory_range(c->string.data,value.size()+1,true)) return false;
    if(c->string.data==c->string.inline_buffer && value.size()+1>16) return false;
    // Exact no-reserve branch of public bw_dat assign_scr_string. Capacity is
    // the number of payload bytes, with a separate trailing NUL byte. Preserve
    // data/capacity/SSO flags/allocator, and never allocate or free game memory.
    auto* data=const_cast<std::uint8_t*>(c->string.data);
    if(!value.empty()) std::memcpy(data,value.data(),value.size());
    data[value.size()]=0;
    c->string.length=value.size();
    return true;
}
std::size_t utf8_size(const std::string& value,std::size_t at) noexcept {
    const auto lead=static_cast<unsigned char>(value[at]);
    std::size_t size=lead<0x80 ? 1 : lead<0xe0 ? 2 : lead<0xf0 ? 3 : 4;
    if(at+size>value.size()) return 0;
    for(std::size_t i=1;i<size;++i) if((static_cast<unsigned char>(value[at+i])&0xc0)!=0x80) return 0;
    return size;
}
std::size_t take(const std::string& value,std::size_t at,std::size_t bytes,int pixels) noexcept {
    const auto begin=at;
    while(at<value.size()) {
        const auto count=utf8_size(value,at);
        if(!count || at-begin+count>bytes) break;
        const int width=count>1 ? 16 : value[at]==' ' ? 4 : 8;
        if(width>pixels) break;
        pixels-=width; at+=count;
    }
    return at-begin;
}
int line_width(const dialog::Control* c) noexcept {
    const int width=int(c->area.right)-int(c->area.left)+1;
    return width>=32 && width<=4096 ? width-16 : 0;
}
std::string hotkey_fallback(dialog::Control* c,const std::string& value) {
    // Original GameMenu PUSHBUTTONs have WS_HOTKEY. A harmless ASCII blank is
    // reserved for native hotkey consumption instead of the first UTF8 glyph.
    const auto cap=capacity(c);
    if(cap<3) return {};
    const auto bytes=cap-1;
    const auto amount=take(value,0,bytes,line_width(c));
    if(amount==value.size()) return " "+value;
    if(bytes>=3) return " "+value.substr(0,take(value,0,bytes-3,(std::max)(0,line_width(c)-24)))+"...";
    // Keep a printable body even in a3-byte native buffer, so its native draw
    // does not skip the layout callback after consuming the blank prefix.
    return " ~";
}
std::string offer_intro(const ChoiceOffer& offer) {
    std::string body=offer.kind==1 ? "재능 선택" : "저주 선택";
    for(unsigned i=0;i<offer.count;++i) {
        const auto index=offer.candidates[i]-1;
        body+='\n';body+=std::to_string(i+1)+". ";
        body+=offer.kind==1 ? frozen::talent_names[index] : frozen::curse_names[index];
        if(offer.partners[i])body+=" + "+std::string(frozen::talent_names[offer.partners[i]-1]);
        if(offer.thirds[i])body+=" + "+std::string(frozen::talent_names[offer.thirds[i]-1]);
        body+=" [";body+=offer.kind==1 ? frozen::talent_rarities[index] : frozen::curse_rarities[index];body+=']';
    }
    body+="\n번호를 누르면 설명을 확인할 수 있습니다.";
    return body;
}
std::string constructor_intro(const ChoiceOffer& offer) {
    // This native-constructor literal is replaced with offer_intro before the
    // first owned redraw. Reserve semantic text storage for every possible next
    // reward, including a longer curse in the same modal; no BwString reallocation.
    auto body=offer_intro(offer);std::string longest;
    for(unsigned kind=1;kind<=2;kind++)for(unsigned i=0;i<(kind==1 ? frozen::kTalentCount : frozen::kCurseCount);i++){
        auto detail=std::string(kind==1 ? frozen::talent_names[i] : frozen::curse_names[i])+"\n등급: "+
            (kind==1 ? frozen::talent_rarities[i] : frozen::curse_rarities[i])+"\n"+
            (kind==1 ? frozen::talent_effects[i] : frozen::curse_effects[i]);
        if(detail.size()>longest.size())longest=std::move(detail);
    }
    if(body.size()<longest.size()+16)body+="\n"+longest;
    return body;
}
std::string json_text(const std::string& value) {
    std::string result;result.reserve(value.size()+16);
    for(const auto c:value) {
        if(c=='"' || c=='\\') {result+='\\';result+=c;}
        else if(c=='\n') result+="\\n";
        else if(c=='\r') result+="\\r";
        else if(c=='\t') result+="\\t";
        else result+=c;
    }
    return result;
}
bool file_name(const std::uint8_t* filename,const char* expected) noexcept {
    const auto length=std::strlen(expected);
    if(!memory_range(filename,length+1)) return false;
    for(std::size_t i=0;i<length;++i) {
        auto c=filename[i];if(c=='\\')c='/';if(c>='A' && c<='Z')c+=('a'-'A');
        if(c!=static_cast<unsigned char>(expected[i]))return false;
    }
    return filename[length]==0;
}
std::vector<std::string> meaning_lines(const std::string& source,int width) {
    auto value=source;for(auto& c:value)if(c=='\r' || c=='\n' || c=='\t')c=' ';
    std::vector<std::string> result;
    std::size_t at=0;
    while(at<value.size()) {
        while(at<value.size() && value[at]==' ') ++at;
        if(at==value.size()) break;
        const auto count=take(value,at,value.size()-at,width);
        if(!count) return {};
        auto end=at+count;
        if(end<value.size() && value[end]!=' ') {
            std::size_t boundary=at;
            for(auto i=at;i<end;++i) if(value[i]==' ' || value[i]=='/') boundary=i+1;
            if(boundary>at) end=boundary;
        }
        auto trim=end;while(trim>at && value[trim-1]==' ') --trim;
        result.push_back(value.substr(at,trim-at));at=end;
    }
    return result;
}
bool same_offer(const ChoiceOffer& a,const ChoiceOffer& b) noexcept {
    return a.wire_version==b.wire_version && a.kind==b.kind && a.count==b.count && a.revision==b.revision
        && a.phase_version==b.phase_version && a.requested_phase==b.requested_phase && a.completed_phase==b.completed_phase
        && std::memcmp(a.token_words,b.token_words,sizeof(a.token_words))==0
        && std::memcmp(a.candidates,b.candidates,sizeof(a.candidates))==0
        && std::memcmp(a.partners,b.partners,sizeof(a.partners))==0
        && std::memcmp(a.thirds,b.thirds,sizeof(a.thirds))==0;
}
bool activation(const dialog::Event* e) noexcept { return e->type==14 && e->ext_type==2; }
bool delete_event(const dialog::Event* e) noexcept { return e->type==14 && e->ext_type==1; }
void disable(dialog::Control* c,bool value) noexcept {
    if(value) c->flags2=(c->flags2&~4u)|1u;
    else c->flags2&=~1u;
}
dialog::Event extended(std::size_t id) noexcept {
    dialog::Event e{}; e.type=14; e.ext_type=id; e.time=GetTickCount();
    // Public bw_dat bw_mouse() explicitly returns (0,0) when no mouse getter is
    // configured. API44 exposes no getter; use that fallback without converting
    // desktop cursor coordinates or fabricating keyboard input.
    e.x=0; e.y=0; e.ext_param=0; e.param=0; return e;
}
std::uint32_t __cdecl menu_event(dialog::Control* c,dialog::Event* e) {
    auto* ui=installed.load(std::memory_order_acquire); return ui ? ui->event(c,e) : 0;
}
std::uint32_t __cdecl hud_callback(dialog::Control* c,dialog::Event* e) {
    auto* ui=installed.load(std::memory_order_acquire); return ui ? ui->hud_event(c,e) : 0;
}
std::uint32_t __cdecl wave_hud_callback(dialog::Control* c,dialog::Event* e) {
    auto* ui=installed.load(std::memory_order_acquire); return ui ? ui->wave_hud_event(c,e) : 0;
}
std::uint32_t __cdecl run_hook(void* r,std::size_t u,void* h,dialog::RunOriginal o) {
    auto* ui=installed.load(std::memory_order_acquire); return ui ? ui->run_dialog(r,u,h,o) : o(r,u,h);
}
std::uint32_t __cdecl spawn_hook(void* r,std::size_t u,void* h,dialog::RunOriginal o) {
    auto* ui=installed.load(std::memory_order_acquire); return ui ? ui->spawn_dialog(r,u,h,o) : o(r,u,h);
}
std::uint8_t* __cdecl file_hook(const std::uint8_t* name,std::uint32_t* size) {
    auto* ui=installed.load(std::memory_order_acquire);return ui ? ui->file_read(name,size) : nullptr;
}
std::size_t __cdecl process_hook(std::size_t flags,ProcessOriginal original) {
    const auto result=original(flags);
    if(auto* ui=installed.load(std::memory_order_acquire)) ui->pump(GetTickCount64());
    return result;
}
const std::uint8_t* __cdecl layout_hook(std::uint32_t a,std::uint32_t b,const std::uint8_t* text,
    std::uint32_t* d,std::uint32_t draw,std::uint32_t* f,std::uint32_t g,std::uint32_t h,
    dialog::LayoutTextOriginal original) {
    auto* ui=installed.load(std::memory_order_acquire);
    return ui ? ui->layout_text(a,b,text,d,draw,f,g,h,original) : original(a,b,text,d,draw,f,g,h);
}
} // namespace

DialogUi::~DialogUi() noexcept {
    auto* expected=this; installed.compare_exchange_strong(expected,nullptr,std::memory_order_acq_rel);
    clear_render_text();
    // No engine pointers are dereferenced during process/host destruction.
}
void DialogUi::set_callbacks(const DialogUiCallbacks& c) noexcept {
    owner_.store(0,std::memory_order_release);
    callbacks_=c;
    owner_.store(GetCurrentThreadId(),std::memory_order_release);
    if(!installed.load() || installed.load()==this) installed.store(this,std::memory_order_release);
}
bool DialogUi::initialize(const samase::PluginApi* api,const DialogUiCallbacks& c) noexcept {
    if(!api || api->version<44 || api->max_func_id<80 || !api->hook_func
        || !api->hook_run_dialog || !api->hook_spawn_dialog || !api->hook_layout_draw_text || !api->hook_file_read || !c.submit || !c.pump
        || !c.session_active || !c.can_resume || (installed.load() && installed.load()!=this)) return false;
    set_callbacks(c); installed.store(this,std::memory_order_release);
    if(!reinterpret_cast<RegisterFunction>(api->hook_func)(79,reinterpret_cast<std::size_t>(&process_hook))
        || !reinterpret_cast<RegisterDialog>(api->hook_run_dialog)(&run_hook)
        || !reinterpret_cast<RegisterDialog>(api->hook_spawn_dialog)(&spawn_hook)
        || !reinterpret_cast<RegisterLayoutText>(api->hook_layout_draw_text)(&layout_hook)) {
        installed.store(nullptr,std::memory_order_release); callbacks_={}; owner_.store(0); return false;
    }
    const auto register_file=reinterpret_cast<dialog::RegisterFileRead>(api->hook_file_read);
    register_file(reinterpret_cast<const std::uint8_t*>("rez/gamemenu.ui.json"),&file_hook);
    register_file(reinterpret_cast<const std::uint8_t*>("rez/gamemenusocial.ui.json"),&file_hook);
    register_file(reinterpret_cast<const std::uint8_t*>("rez/statfluf.ui.json"),&file_hook);
    supported_=true;
    report("Native text-panel hooks registered: scoped GameMenu/Social files, Run/Spawn/ProcessEvents/LayoutDrawText");
    return true;
}
bool DialogUi::scope() const noexcept {
    const auto owner=owner_.load(std::memory_order_acquire);
    return owner && owner==GetCurrentThreadId() && callbacks_.session_active
        && callbacks_.session_active(callbacks_.context);
}
void DialogUi::report(const char* text) const noexcept {
    if(owner_.load()!=GetCurrentThreadId()) return;
    try {if(callbacks_.report) callbacks_.report(callbacks_.context,text);} catch(...) {}
}
bool DialogUi::valid_offer(const ChoiceOffer& o) const noexcept {
    if((o.wire_version!=1 && o.wire_version!=2) || (o.kind!=1 && o.kind!=2) ||
        (o.kind==1 ? (o.wire_version==2 ? o.count<1 || o.count>4:o.count!=4):(o.phase_version==2 ? o.count<1 || o.count>3:o.count!=3))
        || o.requested_phase>(o.phase_version==2?4u:3u) || o.completed_phase>(o.phase_version==2?4u:3u)) return false;
    for(unsigned i=0;i<4;++i) if(i<o.count ? (!o.candidates[i] || o.candidates[i]>(o.kind==1?frozen::kTalentCount:frozen::kCurseCount)) : o.candidates[i]!=0) return false;
    for(unsigned i=0;i<4;i++)if(o.partners[i] && (o.wire_version!=2 || o.kind!=1 || i>=o.count
        || !legendary_bundles::compatible(o.candidates[i],o.partners[i])))return false;
    for(unsigned i=0;i<4;i++)if(o.thirds[i] && (!o.partners[i] || !legendary_bundles::manual(o.candidates[i])
        || !legendary_bundles::manual(o.partners[i]) || !legendary_bundles::manual(o.thirds[i])
        || !legendary_bundles::compatible(o.candidates[i],o.thirds[i]) || !legendary_bundles::compatible(o.partners[i],o.thirds[i])))return false;
    return true;
}
void DialogUi::show(const ChoiceOffer& o) noexcept {
    if(!scope() || !valid_offer(o)) return;
    clear_render_text();
    offer_=o; pending_=true; waiting_=false; dirty_=true;
    body_write_logged_=false;
    bundle_page_=0;preview_slot_=pressed_id_=0; preview_offer_={}; deferred_clear_=deferred_error_=false;
    if(o.wire_version==2 && o.kind==1 && o.count==1){preview_slot_=1;preview_offer_=o;}
    hud_warning_=false;
}
void DialogUi::clear() noexcept {
    clear_render_text();
    pending_=waiting_=false; deferred_clear_=true; dirty_=true; preview_slot_=0;
}
void DialogUi::dismiss_error() noexcept {
    if(!scope()) return;
    clear_render_text();
    pending_=waiting_=false; deferred_clear_=false; deferred_error_=true; dirty_=true;
}
void DialogUi::reset_session() noexcept {
    clear_render_text();
    wave_timer_text_.clear();
    for(auto& h:wave_hud_)if(h.live && h.thread==GetCurrentThreadId() && revalidate_wave_hud(h)){
        if(h.cargo){h.cargo->flags&=~2u;disable(h.cargo,true);}h.cargo_token=h.pressed_token=0;h.cargo_pressed=false;
    }
    owner_.store(0,std::memory_order_release);refresh_wave_hud();wave_hud_warning_=false;
    epoch_.fetch_add(1,std::memory_order_acq_rel);
    pending_=waiting_=dirty_=deferred_clear_=deferred_error_=false;
    preview_slot_=pressed_id_=0; offer_=displayed_=preview_offer_=pressed_={};
    attempted_=false; opening_=false; last_pump_=0; owner_.store(0,std::memory_order_release);
    // HUD observation outlives a campaign session. Its old auto target is
    // invalidated by this epoch, and must be revalidated/adopted in the new one.
    // Keep original delegates until the engine sends delete; no foreign writes.
}
std::uint8_t* DialogUi::file_read(const std::uint8_t* name,std::uint32_t* out_size) noexcept {
    // This unused native HUD placeholder gets a timer and a cargo page button in
    // an authenticated campaign. Native parsing owns every control/allocation;
    // the original placeholder stays intact and no mission timer is repurposed.
    // Native HUD construction precedes campaign authentication. Supply inert,
    // blank controls at construction time; visibility and updates remain gated
    // by scope(). Waiting for scope here permanently loses the cached HUD.
    if(supported_ && file_name(name,"rez/statfluf.ui.json") && memory_range(out_size,sizeof(*out_size),true)) {
        const auto size=sizeof(wave_timer_asset::json)-1;
        auto* result=static_cast<std::uint8_t*>(HeapAlloc(GetProcessHeap(),0,size));
        if(!result)return nullptr;std::memcpy(result,wave_timer_asset::json,size);*out_size=static_cast<std::uint32_t>(size);
        return result;
    }
    // Authorization/thread first: unrelated sessions, stock menus, foreign
    // files/threads and invalid outputs always delegate the original read.
    if(!scope() || !pending_ || menu_ || native_run_depth_.load()
        || !memory_range(out_size,sizeof(*out_size),true)) return nullptr;
    const char* source=nullptr;
    if(file_name(name,"rez/gamemenu.ui.json"))source=dialog_asset::normal;
    else if(file_name(name,"rez/gamemenusocial.ui.json"))source=dialog_asset::social;
    if(!source)return nullptr;
    try {
        auto payload=std::string(source);
        const auto marker=payload.find(dialog_asset::body_marker);
        if(marker==std::string::npos)return nullptr;
        payload.replace(marker,std::strlen(dialog_asset::body_marker),json_text(constructor_intro(offer_)));
        // Exact public MTL file-hook payload pattern. This is file memory,
        // never an assumed game BwString allocator. The original native parser
        // constructs the real CTEXT, allocates its storage and cleans it up.
        auto* result=static_cast<std::uint8_t*>(HeapAlloc(GetProcessHeap(),0,payload.size()));
        if(!result)return nullptr;
        std::memcpy(result,payload.data(),payload.size());*out_size=static_cast<std::uint32_t>(payload.size());
        report("Native CTEXT constructor template supplied: plain upper text, lower numeric choices");
        return result;
    } catch(...) {return nullptr;}
}

bool DialogUi::begin_menu(dialog::Dialog* root,dialog::EventHandler original,bool spawned) noexcept {
    if(!scope() || menu_ || !pending_ || !named(root,"GameMenu") || !executable(original)) return false;
    const auto current=GetCurrentThreadId(); auto gui=gui_owner_.load();
    if(gui && gui!=current) return false;
    gui_owner_.store(current,std::memory_order_release);
    menu_=root; root_original_=original; menu_epoch_=epoch_.load(); spawned_=spawned;
    render_diagnostics_.reset();render_probe_started_=0;render_probe_reported_=false;
    armed_=false; closing_=in_resume_=false; binding_count_=0; bind_warning_=false;
    body_storage_logged_=body_write_logged_=false;
    root_init_observed_=spawned;
    report(spawned ? "GameMenu Spawn original completed; validating stock controls" : "GameMenu Run entered; original construction retained");
    return true;
}
dialog::Control* DialogUi::control(std::int16_t id) const noexcept {
    for(unsigned i=0;i<binding_count_;++i) if(bindings_[i].control->id==id) return bindings_[i].control;
    return nullptr;
}
dialog::EventHandler DialogUi::original_handler(dialog::Control* c) const noexcept {
    if(menu_ && c==&menu_->control) return root_original_;
    for(unsigned i=0;i<binding_count_;++i) if(bindings_[i].control==c) return bindings_[i].original;
    return root_original_;
}
bool DialogUi::bind_menu() noexcept {
    if(!menu_ || armed_ || !scope() || menu_epoch_!=epoch_.load() || !root_init_observed_
        || !named(menu_,"GameMenu") || !executable(root_original_)) return false;
    std::array<Binding,12> found{}; unsigned count=0;
    std::array<dialog::Control*,128> seen{}; unsigned visited=0;
    auto* next=menu_->first_child;
    while(next && visited<seen.size()) {
        if(!memory_range(next,sizeof(*next),true)) return false;
        for(unsigned i=0;i<visited;++i) if(seen[i]==next) return false;
        seen[visited++]=next;
        const auto id=next->id;
        const bool retained=id==-3 || id==-1 || (id>=1 && id<=9);
        if(retained) {
            if(id==-1 && !body_storage_logged_) {
                char info[256]{};
                std::snprintf(info,sizeof(info),"Native CTEXT storage: capacity=%llu length=%llu rect=%d,%d,%d,%d surface=%u,%u backed=%u",
                    static_cast<unsigned long long>(capacity(next)),static_cast<unsigned long long>(next->string.length),
                    next->area.left,next->area.top,next->area.right,next->area.bottom,
                    next->image.width,next->image.height,next->image.data ? 1u : 0u);
                report(info);body_storage_logged_=true;
            }
            // Empty/unresolved native title text must reach refresh's full-write
            // check, so a guarded menu can close through original Resume rather
            // than leaving the unsupported body unbound. Never read its data.
            const bool text_role=id==-3 || id==1 || id==2 || id==3 || id==5 || id==6 || id==7;
            if(next->parent!=menu_ || count==found.size()
                || (text_role && (capacity(next)<3
                || !memory_range(next->string.data,next->string.length+1,true)))) return false;
            for(unsigned i=0;i<count;++i) if(found[i].control->id==id) return false;
            auto fn=next->event_handler;
            if(fn==&menu_event) return false;
            if(id!=-1 && !executable(fn)) {
                if(!bind_warning_) {report("GameMenu retained handler not executable; constructor state not captured");bind_warning_=true;}
                return false;
            }
            found[count++]={next,fn,next->area,next->flags,next->flags2};
        }
        next=next->next;
    }
    if(next) return false;
    for(const auto id:{-3,-1,1,2,3,5,6,7}) {
        bool exists=false;for(unsigned i=0;i<count;++i) if(found[i].control->id==id) exists=true;
        if(!exists) return false;
    }
    // All retained controls, parents, mutable storage and executable callbacks
    // validate before the first handler change. Never capture a -5 sentinel.
    bindings_=found; binding_count_=count;
    for(unsigned i=0;i<count;++i) if(bindings_[i].control->id!=-1) bindings_[i].control->event_handler=&menu_event;
    menu_->control.event_handler=&menu_event;
    armed_=true;dirty_=true;layout_ready_=arrange_menu();
    report("GameMenu stock controls bound: init observed=1 childlist valid=1 handlers executable=1");
    return true;
}
bool DialogUi::arrange_menu() noexcept {
    const int root_width=int(menu_->control.area.right)-int(menu_->control.area.left)+1;
    const int root_height=int(menu_->control.area.bottom)-int(menu_->control.area.top)+1;
    if(root_width<264 || root_height<288) return false;
    auto* title=control(-1);
    // The original native constructor must already have created this panel.
    // Never resize a surface or change widget type/rectangle after init.
    // A live native CTEXT can retain its dimensions with data=null: that is
    // metadata, not evidence that an image allocation must exist. We never
    // dereference it; drawing and ownership remain with the native handler.
    const bool sized=title->image.width>=248 && title->image.height>=208;
    const bool empty=!title->image.data && !title->image.width && !title->image.height;
    if(title->area.left!=8 || title->area.top!=8 || title->area.right!=255 || title->area.bottom!=215
        || (!sized && !empty)) return false;
    unsigned i=0;
    for(const auto id:{1,2,3,5,-3}) {
        auto* button=control(static_cast<std::int16_t>(id));
        const auto left=id==-3 ? 20 : 20+56*int(i++);
        const auto top=id==-3 ? 252 : 220;
        const auto width=id==-3 ? 224 : 48;
        if(!button || button->area.left!=left || button->area.top!=top
            || button->area.right!=left+width-1 || button->area.bottom!=top+27) return false;
    }
    for(const auto id:{4,7,8,9,6}) if(auto* row=control(static_cast<std::int16_t>(id))) {
        row->flags&=~2u;disable(row,true);
    }
    report("Choice layout: native CTEXT208 panel and lower numeric buttons; no button-label explanation fallback");
    return true;
}
void DialogUi::restore_layout() noexcept {
    for(unsigned i=0;i<binding_count_;++i) {
        const auto& b=bindings_[i];
        if(memory_range(b.control,sizeof(*b.control),true)) {
            b.control->area=b.area;b.control->flags=b.flags;b.control->flags2=b.flags2;
        }
    }
    layout_ready_=false;
}
void DialogUi::restore_handlers() noexcept {
    clear_render_text(); // Original native init/delete must see only native storage.
    if(!menu_) return;
    restore_layout();
    for(unsigned i=0;i<binding_count_;++i) {
        auto& b=bindings_[i];
        if(memory_range(b.control,sizeof(*b.control),true) && b.control->event_handler==&menu_event)
            b.control->event_handler=b.original;
    }
    if(memory_range(menu_,sizeof(*menu_),true) && menu_->control.event_handler==&menu_event)
        menu_->control.event_handler=root_original_;
}
void DialogUi::detach_menu() noexcept {
    clear_render_text();
    menu_=nullptr; root_original_=nullptr; bindings_={}; binding_count_=0;
    armed_=spawned_=closing_=in_resume_=root_init_observed_=layout_ready_=false;
    preview_slot_=pressed_id_=0; in_refresh_=false;
}
std::uint32_t DialogUi::run_dialog(void* raw,std::size_t unknown,void* handler,dialog::RunOriginal original) noexcept {
    if(!original) return dialog::kResumeResult;
    native_run_depth_.fetch_add(1,std::memory_order_acq_rel);
    if(!begin_menu(static_cast<dialog::Dialog*>(raw),reinterpret_cast<dialog::EventHandler>(handler),false)) {
        const auto result=original(raw,unknown,handler);
        native_run_depth_.fetch_sub(1,std::memory_order_acq_rel);return result;
    }
    const auto result=original(raw,unknown,reinterpret_cast<void*>(&menu_event));
    // The native loop may already have destroyed every widget. Detach own state
    // only; native delete events restore handlers while the controls still live.
    detach_menu();native_run_depth_.fetch_sub(1,std::memory_order_acq_rel);
    (void)result; return dialog::kResumeResult;
}
std::uint32_t DialogUi::spawn_dialog(void* raw,std::size_t unknown,void* handler,dialog::RunOriginal original) noexcept {
    if(!original) return 0;
    const auto result=original(raw,unknown,handler); // Exact public MTL ordering.
    auto* root=static_cast<dialog::Dialog*>(raw);
    if(named(root,"Stat_F10")) observe_hud(root);
    else if(named(root,"StatFluf")) observe_wave_hud(root);
    else if(named(root,"GameMenu") && scope() && pending_ && !menu_) {
        if(begin_menu(root,root->control.event_handler,true)) {
            if(bind_menu() && !refresh()) dismiss_error();
        }
    }
    return result;
}

void DialogUi::clear_render_text() noexcept {
    std::atomic_store_explicit(&render_text_,std::shared_ptr<const RenderTable>{},std::memory_order_release);
}
std::shared_ptr<const std::string> DialogUi::stable_text(const std::string& value) {
    // Frozen names/effects and fixed status text are interned. No string is
    // mutated or retired between offers: native returned continuation pointers
    // stay valid even if the next callback uses a different render generation.
    for(const auto& saved:stable_texts_) if(*saved==value) return saved;
    auto saved=std::make_shared<const std::string>(value);
    stable_texts_.push_back(saved);return saved;
}
const std::uint8_t* DialogUi::layout_text(std::uint32_t a,std::uint32_t b,const std::uint8_t* text,
    std::uint32_t* d,std::uint32_t draw,std::uint32_t* f,std::uint32_t g,std::uint32_t h,
    dialog::LayoutTextOriginal original) noexcept {
    if(!original) return nullptr;
    // This may run on the renderer thread: do not consult scope(), callbacks,
    // epoch, native widgets, game state, VirtualQuery, or any SAMASE API.
    auto table=std::atomic_load_explicit(&render_text_,std::memory_order_acquire);
    static thread_local std::shared_ptr<const RenderTable> returned_text_lease;
    if(table) {
        auto& stats=*table->diagnostics;stats.calls.fetch_add(1,std::memory_order_relaxed);
        const auto address=reinterpret_cast<std::uintptr_t>(text);
        for(unsigned i=0;i<table->count;++i) {
            const auto& row=table->rows[i];const auto base=reinterpret_cast<std::uintptr_t>(row.native_text);
            const bool exact=address==base;
            const bool shifted=row.hotkey_prefix && address>base && address-base==1;
            const bool within_label=address>base && address-base<=row.native_length;
            if(shifted || within_label) {
                auto expected=0xffffffffu;
                if(stats.offset.compare_exchange_strong(expected,0xfffffffeu,std::memory_order_acq_rel)) {
                    stats.row.store(static_cast<std::uint16_t>(row.id));stats.a.store(a);stats.b.store(b);
                    stats.draw.store(draw);stats.g.store(g);stats.h.store(h);
                    stats.offset.store(static_cast<std::uint32_t>(address-base),std::memory_order_release);
                }
            }
            if(exact || shifted) {
                if(exact)stats.exact.fetch_add(1,std::memory_order_relaxed);
                else stats.hotkey_offset.fetch_add(1,std::memory_order_relaxed);
                returned_text_lease=table;
                const auto& value=exact && row.hotkey_prefix ? row.prefixed_text : row.text;
                const auto* replacement=reinterpret_cast<const std::uint8_t*>(value->c_str());
                return original(a,b,replacement,d,draw,f,g,h);
            }
            if(within_label)stats.near_miss.fetch_add(1,std::memory_order_relaxed);
        }
    }
    return original(a,b,text,d,draw,f,g,h);
}
DialogRenderStats DialogUi::render_stats() const noexcept {
    DialogRenderStats result;
    auto table=std::atomic_load_explicit(&render_text_,std::memory_order_acquire);
    if(!table || !table->diagnostics) return result;
    const auto& s=*table->diagnostics;
    result.calls=s.calls.load();result.exact=s.exact.load();result.hotkey_offset=s.hotkey_offset.load();result.near_miss=s.near_miss.load();
    result.offset=s.offset.load(std::memory_order_acquire);
    if(result.offset<0xfffffffeu) {
        result.row=s.row.load();result.a=s.a.load();result.b=s.b.load();result.draw=s.draw.load();result.g=s.g.load();result.h=s.h.load();
    }
    return result;
}
void DialogUi::report_render_stats(std::uint64_t now) noexcept {
    if(!menu_ || render_probe_reported_) return;
    if(!render_probe_started_) {render_probe_started_=now;return;}
    if(now-render_probe_started_<1000) return;
    const auto s=render_stats();char message[320]{};
    std::snprintf(message,sizeof(message),"Text render probe: calls=%llu exact=%llu hotkey_offset=%llu near_miss=%llu first_offset=%u row=%u args=%u,%u,%u,%u,%u",
        static_cast<unsigned long long>(s.calls),static_cast<unsigned long long>(s.exact),
        static_cast<unsigned long long>(s.hotkey_offset),static_cast<unsigned long long>(s.near_miss),
        s.offset,s.row,s.a,s.b,s.draw,s.g,s.h);
    report(message);render_probe_reported_=true;
}
bool DialogUi::refresh() noexcept {
    if(!armed_ || !menu_ || !layout_ready_ || in_refresh_ || menu_epoch_!=epoch_.load()) return false;
    in_refresh_=true;
    bool okay=true;
    try {
        auto next=std::make_shared<RenderTable>();
        if(!render_diagnostics_)render_diagnostics_=std::make_shared<RenderDiagnostics>();
        next->diagnostics=render_diagnostics_;
        const auto render_label=[&](std::int16_t id,const std::string& value) {
            auto* row=control(id);
            const bool hotkey=id!=-1;
            if(next->count==next->rows.size() || value.size()>511 || capacity(row)<3
                || (!hotkey && capacity(row)<value.size())
                || !write_text(row,hotkey ? hotkey_fallback(row,value) : value)) return false;
            next->rows[next->count++]={row->string.data,stable_text(value),stable_text(" "+value),row->string.length,id,hotkey};
            return true;
        };
        const bool selected=preview_slot_ && same_offer(preview_offer_,offer_) && pending_ && !waiting_;
        std::string body=waiting_ ? "저장 중\n선택 내용을 저장하고 있습니다." : offer_intro(offer_);
        if(selected) {
            const auto partner=offer_.partners[preview_slot_-1];
            const auto third=offer_.thirds[preview_slot_-1];
            const auto index=(third && bundle_page_==2 ? third:partner && bundle_page_ ? partner:offer_.candidates[preview_slot_-1])-1;
            body=offer_.kind==1 ? frozen::talent_names[index] : frozen::curse_names[index];
            if(partner)body+=" ["+std::to_string(bundle_page_+1)+"/"+(third?"3":"2")+"]";
            body+="\n등급: "+std::string(offer_.kind==1 ? frozen::talent_rarities[index] : frozen::curse_rarities[index]);
            const auto lines=meaning_lines(offer_.kind==1 ? frozen::talent_effects[index] : frozen::curse_effects[index],line_width(control(-1)));
            // Complete information is written to actual native CTEXT storage.
            // No clipped explanation or button-label fallback can confirm.
            okay=okay && !lines.empty() && lines.size()<=8;
            for(const auto& line:lines)body+="\n"+line;
        }
        const bool written=okay && render_label(-1,body);
        if(!body_write_logged_) {
            char info[192]{};
            std::snprintf(info,sizeof(info),"Native CTEXT body: capacity=%llu required=%llu full_write=%u",
                static_cast<unsigned long long>(capacity(control(-1))),static_cast<unsigned long long>(body.size()),written ? 1u : 0u);
            report(info);body_write_logged_=true;
        }
        okay=okay && written;
        for(unsigned i=0;i<4;++i) {
            auto* button=control(candidate_ids[i]);std::string number;
            if(i<offer_.count) {
                number=std::to_string(i+1);button->flags|=2u;
            } else button->flags&=~2u;
            okay=okay && render_label(candidate_ids[i],number);
            disable(button,!pending_ || waiting_ || i>=offer_.count);
        }
        const bool paired=selected && offer_.partners[preview_slot_-1];
        okay=okay && render_label(-3,waiting_ ? "저장 중" : paired ? (bundle_page_==(offer_.thirds[preview_slot_-1]?2u:1u) ? "묶음 확정":"다음 설명") : "확정");
        disable(control(-3),!okay || !selected || waiting_);
        if(okay) {
            std::atomic_store_explicit(&render_text_,std::shared_ptr<const RenderTable>(next),std::memory_order_release);
            displayed_=offer_;dirty_=false;
        }
        else {dirty_=true;disable(control(-3),true);}
    } catch(...) {okay=false;}
    if(!okay) {clear_render_text();dirty_=true;disable(control(-3),true);}
    in_refresh_=false;
    if(okay && menu_ && executable(root_original_)) {
        auto e=extended(6);root_original_(&menu_->control,&e); // Public redraw event.
    }
    return okay;
}
std::uint32_t DialogUi::event(dialog::Control* c,dialog::Event* e) noexcept {
    if(gui_owner_.load(std::memory_order_acquire)!=GetCurrentThreadId()
        || !menu_ || !memory_range(c,sizeof(*c)) || !memory_range(e,sizeof(*e))) return 0;
    auto original=original_handler(c);
    const bool root=c==&menu_->control;
    if(delete_event(e) && root) {
        restore_handlers();
        const auto result=executable(original) ? original(c,e) : 0;
        detach_menu();
        return result;
    }
    if(root && e->type==14 && (e->ext_type==0 || e->ext_type==7)) {
        // Native reinitialization can replace both child procedures and strings.
        // Restore delegates before it runs, discard old bindings, then recheck
        // at the next post-ProcessEvents boundary; never keep old child pointers.
        restore_handlers();bindings_={};binding_count_=0;armed_=false;
        body_storage_logged_=body_write_logged_=false;
        root_init_observed_=false;pressed_id_=0;dirty_=true;
        const auto result=executable(original) ? original(c,e) : 0;
        if(memory_range(c,sizeof(*c),true) && menu_ && c==&menu_->control) {
            if(c->event_handler!=&menu_event && executable(c->event_handler)) root_original_=c->event_handler;
            c->event_handler=&menu_event;
            root_init_observed_=e->ext_type==0;
        }
        return result;
    }
    if(menu_epoch_!=epoch_.load() || !scope()) return executable(original) ? original(c,e) : 0;
    if(activation(e)) {
        if(in_resume_ && (c==control(-3) || root)) return executable(original) ? original(c,e) : 0;
        if(!armed_ || closing_ || waiting_ || dirty_) return 1;
        const bool fresh=same_offer(displayed_,offer_)
            && (!pressed_id_ || (pressed_id_==static_cast<std::uint32_t>(static_cast<std::uint16_t>(c->id)) && same_offer(pressed_,offer_)));
        if(!fresh || !pending_) return 1;
        for(unsigned i=0;i<offer_.count;++i) if(c==control(candidate_ids[i])) {
            bundle_page_=preview_slot_==i+1 && offer_.partners[i] ? (bundle_page_+1)%(offer_.thirds[i]?3u:2u):0;
            preview_slot_=i+1;preview_offer_=offer_;dirty_=true;if(!refresh()) dismiss_error();return 1;
        }
        if(preview_slot_) {
            if(c==control(-3) && same_offer(preview_offer_,offer_)) {
                if(offer_.partners[preview_slot_-1] && bundle_page_<(offer_.thirds[preview_slot_-1]?2u:1u)){
                    ++bundle_page_;dirty_=true;if(!refresh())dismiss_error();return 1;
                }
                waiting_=true;bool submitted=false;
                try {submitted=callbacks_.submit(callbacks_.context,preview_slot_);} catch(...) {}
                if(!submitted) waiting_=false;
                dirty_=true;if(!refresh()) dismiss_error();return 1;
            }
        }
        // Root notification payload is undocumented: never infer an ID/slot
        // from ext_param/param or pass a candidate through to Save/Load/Exit.
        report("GameMenu activation consumed without native menu action");return 1;
    }
    if(!closing_ && (e->type==0 || e->type==2 || e->type==15)) return 1;
    if(armed_ && e->type==4) {pressed_id_=static_cast<std::uint16_t>(c->id);pressed_=displayed_;}
    const auto result=executable(original) ? original(c,e) : 0;
    return result;
}
void DialogUi::resume() noexcept {
    if(!armed_ || !menu_ || closing_) return;
    auto* button=control(-3);auto original=original_handler(button);
    if(!memory_range(button,sizeof(*button),true) || !executable(original)) {report("Native Resume handler is not executable; not invoked");return;}
    const bool was_spawned=spawned_;auto* owned_menu=menu_;const auto owned_epoch=menu_epoch_;
    closing_=true;in_resume_=true;restore_handlers();disable(button,false);
    // Use the current live native handler, restored before activation. No old
    // RunDialog callable is retained/replayed and no cleanup function is guessed.
    button->event_handler=original;
    auto e=extended(2);original(button,&e);
    // Native activation may destroy the widgets without a hooked delete event.
    // From here on inspect only our fields, never the returned native pointers.
    in_resume_=false;
    if(was_spawned && menu_==owned_menu && menu_epoch_==owned_epoch)detach_menu();
    // Owned Run keeps its lifetime until the original modal loop returns.
}

bool DialogUi::revalidate_hud(Hud& h) noexcept {
    if(!h.live || h.thread!=GetCurrentThreadId() || !named(h.root,"Stat_F10")) return false;
    const auto parent_handler=h.root->control.event_handler;
    if(!executable(parent_handler) || (parent_handler!=&hud_callback && parent_handler!=h.original)) return false;
    auto* button=h.root->first_child;
    if(!memory_range(button,sizeof(*button)) || button->id!=1 || button->parent!=h.root || button->next
        || !executable(button->event_handler)) return false;
    h.button=button;h.needs_rebind=false;
    if(parent_handler==h.original) h.root->control.event_handler=&hud_callback;
    return true;
}
void DialogUi::observe_hud(dialog::Dialog* root) noexcept {
    const auto current=GetCurrentThreadId();auto owner=gui_owner_.load();
    if(owner && owner!=current) return;
    gui_owner_.store(current,std::memory_order_release);
    for(auto& h:hud_) if(h.live && h.root==root) {h.needs_rebind=true;revalidate_hud(h);return;}
    for(auto& h:hud_) if(!h.live) {
        if(!executable(root->control.event_handler)) return;
        h={root,nullptr,root->control.event_handler,current,true,true};
        if(!revalidate_hud(h)) {h={};return;}
        root->control.event_handler=&hud_callback;
        report("Stat_F10 observed after Spawn original; native activation remains session-gated");
        return;
    }
}
std::uint32_t DialogUi::hud_event(dialog::Control* c,dialog::Event* e) noexcept {
    if(gui_owner_.load(std::memory_order_acquire)!=GetCurrentThreadId()
        || !memory_range(c,sizeof(*c)) || !memory_range(e,sizeof(*e))) return 0;
    for(auto& h:hud_) if(h.live && (c==&h.root->control || c==h.button || c->parent==h.root)) {
        auto original=h.original;
        if(delete_event(e) && c==&h.root->control) {
            h.live=false;h.button=nullptr;
            if(memory_range(h.root,sizeof(*h.root),true) && h.root->control.event_handler==&hud_callback)
                h.root->control.event_handler=original;
            const auto result=executable(original) ? original(c,e) : 0;
            h={};return result;
        }
        if(c==&h.root->control && e->type==14 && (e->ext_type==0 || e->ext_type==7)) {
            h.button=nullptr;h.needs_rebind=true;
            const auto result=executable(original) ? original(c,e) : 0;
            if(h.live && memory_range(h.root,sizeof(*h.root),true)) {
                const auto completed=h.root->control.event_handler;
                if(completed!=&hud_callback && executable(completed)) h.original=completed;
                h.root->control.event_handler=&hud_callback;
            }
            return result;
        }
        return executable(original) ? original(c,e) : 0;
    }
    return 0;
}

void DialogUi::set_wave_timer(const std::string& text) noexcept {
    if(owner_.load(std::memory_order_acquire)!=GetCurrentThreadId())return;
    try {wave_timer_text_=scope() ? text : std::string{};refresh_wave_hud();}catch(...){}
}
bool DialogUi::revalidate_wave_hud(WaveHud& h) noexcept {
    if(!h.live || h.thread!=GetCurrentThreadId() || !named(h.root,"StatFluf"))return false;
    const auto parent=h.root->control.event_handler;
    if(!executable(parent) || (parent!=&wave_hud_callback && parent!=h.original))return false;
    dialog::Control* timer=nullptr,*cargo=nullptr;auto* child=h.root->first_child;std::array<dialog::Control*,16> seen{};unsigned count=0;
    while(child && count<seen.size()){
        if(!memory_range(child,sizeof(*child),true) || child->parent!=h.root)return false;
        for(unsigned i=0;i<count;i++)if(seen[i]==child)return false;seen[count++]=child;
        if(child->id==wave_timer_asset::kId){
            if(timer || child->area.left!=8 || child->area.top!=128 || child->area.right!=239 || child->area.bottom!=147 || child->type!=6 || capacity(child)<std::strlen("공세 대기 · 기지 도착 후"))return false;
            timer=child;
        }
        if(child->id==wave_timer_asset::kCargoId){
            if(cargo || child->area.left!=8 || child->area.top!=104 || child->area.right!=239 || child->area.bottom!=123 || child->type!=1 || capacity(child)<std::strlen("추가 승객 보기"))return false;
            if(!executable(child->event_handler) || (child->event_handler==&wave_hud_callback && (h.cargo!=child || !executable(h.cargo_original))))return false;
            cargo=child;
        }
        child=child->next;
    }
    if(child || !timer)return false;
    h.text=timer;
    if(cargo){
        if(cargo->event_handler!=&wave_hud_callback)h.cargo_original=cargo->event_handler;
        h.cargo=cargo;cargo->event_handler=&wave_hud_callback;
    }else{h.cargo=nullptr;h.cargo_original=nullptr;h.cargo_token=h.pressed_token=0;h.cargo_pressed=false;}
    if(parent==h.original)h.root->control.event_handler=&wave_hud_callback;
    return true;
}
void DialogUi::observe_wave_hud(dialog::Dialog* root) noexcept {
    const auto current=GetCurrentThreadId();
    if(gui_owner_.load() && gui_owner_.load()!=current)return;
    for(auto& h:wave_hud_)if(h.live && h.root==root){revalidate_wave_hud(h);refresh_wave_hud();return;}
    for(auto& h:wave_hud_)if(!h.live){
        if(!executable(root->control.event_handler))return;
        h={root,nullptr,root->control.event_handler,current,true};
        if(!revalidate_wave_hud(h)){h={};return;}
        report("Independent wave timer CTEXT observed; original mission countdown and leaderboard untouched");
        refresh_wave_hud();return;
    }
}
bool DialogUi::cargo_state(std::uint64_t& token,std::uint32_t& page,std::uint32_t& passengers,std::uint32_t* page_count) const noexcept {
    token=0;page=passengers=0;if(page_count)*page_count=1;
    if(!scope() || (!callbacks_.cargo_state && !callbacks_.cargo_state_v2) || !callbacks_.cargo_toggle)return false;
    try{
        if(callbacks_.cargo_state_v2){std::uint32_t pages=1;const bool valid=callbacks_.cargo_state_v2(callbacks_.context,&token,&page,&pages,&passengers) && token && pages>=2 && pages<=3 && page<pages && passengers && passengers<=16;if(valid && page_count)*page_count=pages;return valid;}
        const bool valid=callbacks_.cargo_state(callbacks_.context,&token,&page,&passengers) && token && page<2 && passengers && passengers<=12;if(valid && page_count)*page_count=2;return valid;
    }catch(...){return false;}
}
void DialogUi::restore_wave_child(WaveHud& h) noexcept {
    if(h.cargo && memory_range(h.cargo,sizeof(*h.cargo),true) && h.cargo->parent==h.root && h.cargo->event_handler==&wave_hud_callback && executable(h.cargo_original))h.cargo->event_handler=h.cargo_original;
    h.cargo=nullptr;h.cargo_original=nullptr;h.cargo_token=h.pressed_token=0;h.cargo_pressed=false;
}
void DialogUi::refresh_wave_hud() noexcept {
    for(auto& h:wave_hud_)if(h.live && h.thread==GetCurrentThreadId() && revalidate_wave_hud(h)){
        const bool visible=scope() && !wave_timer_text_.empty();
        bool changed=visible!=bool(h.text->flags&2u);
        if(!visible)h.text->flags&=~2u;
        else {
            changed=changed || h.text->string.length!=wave_timer_text_.size()
                || !memory_range(h.text->string.data,wave_timer_text_.size())
                || std::memcmp(h.text->string.data,wave_timer_text_.data(),wave_timer_text_.size())!=0;
            if(!write_text(h.text,wave_timer_text_)){
                h.text->flags&=~2u;
                if(!wave_hud_warning_){report("Wave timer text storage invalid; timer hidden");wave_hud_warning_=true;}
                continue;
            }
            disable(h.text,true);h.text->flags|=2u;
        }
        if(h.cargo){
            std::uint64_t token=0;std::uint32_t page=0,pages=1,passengers=0;const bool show=cargo_state(token,page,passengers,&pages);
            const std::string label=pages>2 ? "승객 목록 넘기기 ("+std::to_string(page+1)+"/"+std::to_string(pages)+")" : page ? "앞쪽 승객 보기" : "추가 승객 보기";
            changed=changed || show!=bool(h.cargo->flags&2u);
            h.cargo_token=show ? token : 0;
            if(!show){h.cargo->flags&=~2u;disable(h.cargo,true);}
            else{
                changed=changed || h.cargo->string.length!=label.size() || !memory_range(h.cargo->string.data,label.size()) || std::memcmp(h.cargo->string.data,label.data(),label.size())!=0;
                if(write_text(h.cargo,label)){h.cargo->flags|=2u;disable(h.cargo,false);}else{h.cargo->flags&=~2u;disable(h.cargo,true);h.cargo_token=0;}
            }
        }
        // Same documented native redraw event as the reward CTEXT. Repaint
        // only changed text/visibility, never by inventing a DrawText ABI.
        if(changed && executable(h.original)){auto event=extended(6);h.original(&h.root->control,&event);}
    }
}

std::uint32_t DialogUi::wave_hud_event(dialog::Control* control,dialog::Event* event) noexcept {
    if(!memory_range(control,sizeof(*control)) || !memory_range(event,sizeof(*event)))return 0;
    for(auto& h:wave_hud_)if(h.live && h.thread==GetCurrentThreadId() && (control==&h.root->control || control->parent==h.root)){
        auto original=h.original;
        if(delete_event(event) && control==&h.root->control){
            restore_wave_child(h);h.live=false;h.text=nullptr;
            if(memory_range(h.root,sizeof(*h.root),true) && h.root->control.event_handler==&wave_hud_callback)h.root->control.event_handler=original;
            const auto result=executable(original) ? original(control,event) : 0;h={};return result;
        }
        if(control==h.cargo){
            const auto delegate=h.cargo_original;
            if(activation(event)){
                std::uint64_t token=0;std::uint32_t page=0,passengers=0;
                const bool current=cargo_state(token,page,passengers) && token==h.cargo_token && (!h.cargo_pressed || token==h.pressed_token) && (control->flags&2u) && !(control->flags2&1u);
                h.cargo_pressed=false;h.pressed_token=0;
                if(current)try{callbacks_.cargo_toggle(callbacks_.context,token);}catch(...){}
                refresh_wave_hud();return 1;
            }
            if(event->type==4){
                std::uint64_t token=0;std::uint32_t page=0,passengers=0;
                h.cargo_pressed=true;h.pressed_token=cargo_state(token,page,passengers) && token==h.cargo_token ? token : 0;
            }
            return executable(delegate) ? delegate(control,event) : 0;
        }
        const bool rebuild=control==&h.root->control && event->type==14 && (event->ext_type==0 || event->ext_type==7);
        if(rebuild){restore_wave_child(h);h.text=nullptr;}else refresh_wave_hud();
        const auto result=executable(original) ? original(control,event) : 0;
        if(rebuild && h.live && memory_range(h.root,sizeof(*h.root),true)){
            const auto replacement=h.root->control.event_handler;
            if(replacement!=&wave_hud_callback && executable(replacement))h.original=replacement;
            revalidate_wave_hud(h);refresh_wave_hud();
        }
        return result;
    }
    return 0;
}

void DialogUi::auto_open() noexcept {
    if(!scope() || !pending_ || waiting_ || menu_ || opening_ || native_run_depth_.load(std::memory_order_acquire)) return;
    const auto epoch=epoch_.load();
    if(attempted_ && attempted_epoch_==epoch && same_offer(opened_offer_,offer_)) return;
    for(auto& h:hud_) if(h.live && h.thread==GetCurrentThreadId() && revalidate_hud(h)) {
        auto* button=h.button;
        if(!(button->flags&2u) || (button->flags2&1u)) continue;
        const auto current=button->event_handler;
        if(!executable(current)) continue;
        attempted_=true;attempted_epoch_=epoch;opened_offer_=offer_;opening_=true;
        report("Automatic Stat_F10 activation: verified live owner/visible/enabled/executable; once per offer");
        auto e=extended(2);current(button,&e);
        // The call can synchronously enter a native RunDialog loop. in_pump_ is
        // already clear; nested ProcessEvents can keep polling durable ACKs.
        opening_=false;return;
    }
    if(!hud_warning_) {report("Automatic popup awaiting a valid live Stat_F10 button; no pointer invoked");hud_warning_=true;}
}
void DialogUi::pump(std::uint64_t now) noexcept {
    if(!scope() || in_pump_ || (last_pump_ && now-last_pump_<50)) return;
    last_pump_=now;in_pump_=true;
    try {callbacks_.pump(callbacks_.context);} catch(...) {}
    // Release BEFORE native HUD activation/Resume; those can synchronously
    // enter a modal loop and reenter this same public ProcessEvents wrapper.
    in_pump_=false;
    if(!scope()) return;
    for(auto& h:hud_) if(h.live && h.needs_rebind) revalidate_hud(h);
    refresh_wave_hud();
    if(menu_ && !closing_ && menu_epoch_==epoch_.load()) {
        if(!armed_) bind_menu();
        if(armed_ && dirty_ && !refresh()) {report("Native choice layout or complete text validation failed; keeping the offer unsaved");dismiss_error();}
        if(menu_ && armed_ && deferred_error_) {deferred_error_=false;resume();}
        else if(menu_ && armed_ && deferred_clear_ && callbacks_.can_resume(callbacks_.context)) {deferred_clear_=false;resume();}
        if(menu_)report_render_stats(now);
    }
    auto_open();
}
} // namespace sc1_native
