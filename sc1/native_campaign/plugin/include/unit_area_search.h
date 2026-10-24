#pragma once
// SAMASE API44 ForEachUnitInArea (rect:u16[4], callback(Unit*,void*)->u32,
// context)->usize. Use the engine's current position index, not a frame cache.
// Hidden units are supplemented because the old scan includes that list.
// ABI reference: neivv/samase_plugin, samase_shim/src/lib.rs ForEachUnitInArea.
namespace unit_area_search {
struct Rect {std::uint16_t left,top,right,bottom;};
static_assert(sizeof(Rect)==8,"Native search rectangle");
using Visit=U32 (__cdecl*)(bw::Unit*,void*);
using Search=std::uintptr_t (__cdecl*)(Rect*,Visit,void*);
inline Search native_search=nullptr;
inline std::deque<std::vector<bw::Unit*>> buffers;
inline std::size_t depth=0;
struct Lease {
 std::vector<bw::Unit*>& result;
 static std::vector<bw::Unit*>& acquire(){
  if(depth==buffers.size())buffers.emplace_back();auto& v=buffers[depth];
  v.clear();v.reserve(g.units_count);++depth;return v;
 }
 Lease():result(acquire()){}~Lease(){--depth;}
};
struct Context {std::vector<bw::Unit*>& units;std::vector<U8>& seen;};
inline U32 __cdecl collect(bw::Unit* u,void* opaque) noexcept {
 auto& context=*static_cast<Context*>(opaque);
 if(!valid_unit(u))return 0;
 const auto index=static_cast<std::size_t>(u-g.units);
 if(context.seen[index])return 0;context.seen[index]=1;
 // Capacity is reserved before entering native code; no allocation or game
 // mutation occurs in this callback, and each unit can be added only once.
 if(u->flingy.hitpoints>0&&u->order)context.units.push_back(u);
 return 0;
}
template<class F> void nearby(int x,int y,U32 radius,F fn){
 // Keep unusual/off-map rectangles on the original path. The extra pixel
 // includes exact-radius centers regardless of native right/bottom convention.
 const auto left=std::int64_t(x)-radius,top=std::int64_t(y)-radius;
 const auto right=std::int64_t(x)+radius+1,bottom=std::int64_t(y)+radius+1;
 // Wider circles measured slower through the native collector at 1000 units.
 // Retain the original scan there; this threshold never changes eligibility.
 if(radius>256||!native_search||!g.active||!g.applied||GetCurrentThreadId()!=g.game_thread.load()||
    left<0||top<0||right>32767||bottom>32767){living_units(fn);return;}
 refresh_units();if(!g.units||!g.units_count)return;
 unit_scan_scratch::Lease seen;Lease scratch;Context context{scratch.result,seen.seen};
 Rect rect{static_cast<std::uint16_t>(left),static_cast<std::uint16_t>(top),static_cast<std::uint16_t>(right),static_cast<std::uint16_t>(bottom)};
 native_search(&rect,collect,&context);
 auto u=g.first_hidden?g.first_hidden():nullptr;
 for(std::size_t n=0;valid_unit(u)&&n<g.units_count;++n){
  auto next=reinterpret_cast<bw::Unit*>(u->flingy.next);collect(u,&context);u=next;
 }
 // Finish the engine query before invoking callers, keeping nested queries
 // independent and the native result stack balanced.
 for(auto unit:scratch.result)fn(unit);
}
}
