#pragma once
namespace host_test {
namespace target_search_fixture {
inline U32 searches=0,native_depth=0;
inline std::uintptr_t __cdecl search(unit_area_search::Rect* rect,unit_area_search::Visit visit,void* context){
 CHECK(native_depth++==0);++searches;
 // Reverse engine order, duplicate callbacks and a broad collision margin:
 // exact center distance, deduplication and final ordering belong to callers.
 std::array<bool,1900> listed{};auto a=active;for(std::size_t n=0;valid_unit(a)&&n<count;++n){listed[std::size_t(a-units.data())]=true;a=reinterpret_cast<bw::Unit*>(a->flingy.next);}
 for(std::size_t i=count;i-->0;){auto u=&units[i];
  const auto p=u->flingy.position;
  if(listed[i]&&p.x>=int(rect->left)-32&&p.x<=int(rect->right)+32&&p.y>=int(rect->top)-32&&p.y<=int(rect->bottom)+32){CHECK(visit(u,context)==0);CHECK(visit(u,context)==0);}
 }
 --native_depth;return 0;
}
struct Binding {
 unit_area_search::Search saved=unit_area_search::native_search;
 Binding(){unit_area_search::native_search=search;searches=native_depth=0;}
 ~Binding(){unit_area_search::native_search=saved;}
};
inline std::vector<bw::Unit*> reference(int x,int y,U32 radius,bw::Unit* excluded,U32 limit,bool enemy,int layer,bool bio){
 using namespace rework_combat_v5;std::vector<bw::Unit*> result;if(!limit)return result;
 living_units([&](bw::Unit* u){if(u==excluded||!eligible(u)||(u->flags&0x40u)||(enemy?!is_enemy(u->player):u->player!=player_owner())||
  (layer>=0&&air(u)!=(layer!=0))||(bio&&!organic(u))||dist(x,y,u->flingy.position.x,u->flingy.position.y)>std::uint64_t(radius)*radius)return;result.push_back(u);});
 const auto less=[&](bw::Unit* a,bw::Unit* b){const auto da=dist(x,y,a->flingy.position.x,a->flingy.position.y),db=dist(x,y,b->flingy.position.x,b->flingy.position.y);return da==db?a<b:da<db;};
 if(result.size()>limit){std::nth_element(result.begin(),result.begin()+limit,result.end(),less);result.resize(limit);}std::sort(result.begin(),result.end(),less);return result;
}
inline bw::Unit* reference_choose(bw::Unit* main,bw::Unit* spawner,int layer,bw::Unit* excluded,bw::Unit* excluded2){
 using namespace multi_target;bw::Unit* best=nullptr;std::uint64_t distance=~std::uint64_t(0);
 living_units([&](bw::Unit* u){if(u==excluded||u==excluded2||(layer>=0&&flying(u)!=(layer!=0))||!target_ok(main,spawner,u))return;
  const auto d=distance_sq(main,u);if(d<distance||(d==distance&&(!best||u<best))){best=u;distance=d;}});return best;
}
inline void compare(int x,int y,U32 radius,bw::Unit* excluded=nullptr,U32 limit=65536,bool enemy=true,int layer=-1,bool bio=false){
 const auto expected=reference(x,y,radius,excluded,limit,enemy,layer,bio);
 CHECK(rework_combat_v5::around(x,y,radius,excluded,limit,enemy,layer,bio)==expected);
}
}
inline void target_search_spatial_matches_all_filters(){
 using namespace target_search_fixture;reset();g.applied=true;Binding binding;U32 random=0x3a104;
 const auto next=[&](){random^=random<<13;random^=random>>17;random^=random<<5;return random;};
 for(U32 i=0;i<500;++i){auto u=add(i%2?37u:65u,i%3?6u:1u,int(next()%2048),int(next()%2048),256000,i%11==0);u->flags=1u|(i%5==0?4u:0u)|(i%7==0?0x40u:0u)|(i%13==0?0x4000000u:0u);if(i%17==0)u->stasis_timer=1;if(i%19==0)u->flingy.hitpoints=0;if(i%23==0)u->order=0;}
 refresh_units();
 for(U32 trial=0;trial<240;++trial){const int x=int(next()%2048),y=int(next()%2048);const U32 radii[]={0,1,32,64,96,128,192,512,1024,65536};
  for(U32 limit:{0u,1u,2u,32u,65536u})for(int layer:{-1,0,1})compare(x,y,radii[trial%10],&units[next()%count],limit,trial%2!=0,layer,trial%3==0);
 }CHECK(searches>0);
 for(int x:{-10,0,1,32767})compare(x,100,64);
 unit_area_search::native_search=nullptr;compare(1000,1000,128);unit_area_search::native_search=search;
}
inline void target_search_same_frame_lifecycle_and_nested_queries(){
 using namespace target_search_fixture;reset();g.applied=true;Binding binding;
 auto a=add(37,6,1000,1000),b=add(37,6,1128,1000),c=add(37,6,872,1000),h=add(37,6,1000,1000,2560,true);
 refresh_units();compare(1000,1000,128,nullptr,2);compare(1000,1000,0);
 b->flingy.position={2000,2000};compare(1000,1000,128);b->flingy.position={1000,1000};compare(1000,1000,0);
 a->flingy.hitpoints=0;compare(1000,1000,128);a->flingy.hitpoints=2560;++a->minor_unique_index;a->player=1;compare(1000,1000,128);compare(1000,1000,128,nullptr,65536,false);
 c->order=0;compare(1000,1000,128);add(65,6,1001,1000);compare(1000,1000,128);
 h->flags|=0x40;compare(1000,1000,128);h->flags=0;compare(1000,1000,128);h->stasis_timer=1;compare(1000,1000,128);h->stasis_timer=0;
 std::size_t nested=0;unit_area_search::nearby(1000,1000,128,[&](bw::Unit*){CHECK(native_depth==0);compare(1000,1000,128);++nested;});CHECK(nested>0&&unit_area_search::depth==0);
}
inline void target_search_pruning_preserves_target_and_reduces_native_calls(){
 using namespace target_search_fixture;multi_fixture::begin(105);auto main=multi_fixture::bc();main->flingy.position={1000,1000};
 for(U32 i=0;i<500;++i){auto u=multi_fixture::unit(i%2?37u:43u,i%7?6u:1u,1000+int(i%25)*8,1000+int(i/25)*8,i%2==0);if(i%9==0)u->detection_status=0;if(i%11==0)u->flags|=0x4000000u;if(i%13==0)static_cast<bw::SpriteScr*>(u->flingy.sprite)->visibility_mask=0;}
 refresh_units();
 for(int layer:{-1,0,1})for(U32 k=0;k<20;++k){auto excluded=&units[k+1],excluded2=&units[k+20];const auto expected=reference_choose(main,main,layer,excluded,excluded2);CHECK(multi_target::choose(main,main,layer,excluded,excluded2)==expected);}
 // Put a nearby valid unit first in the living-list traversal.
 auto nearest=multi_fixture::unit(37,6,1001,1000);refresh_units();multi_fixture::can_calls=0;CHECK(reference_choose(main,main,-1,nullptr,nullptr)==nearest);const auto before=multi_fixture::can_calls;
 multi_fixture::can_calls=0;CHECK(multi_target::choose(main,main,-1,nullptr)==nearest);CHECK(multi_fixture::can_calls<before/10);
 nearest->flingy.hitpoints=0;CHECK(multi_target::choose(main,main,-1,nullptr)==reference_choose(main,main,-1,nullptr,nullptr));
 main->stasis_timer=1;CHECK(multi_target::choose(main,main,-1,nullptr)==nullptr);CHECK(multi_target::choose(nullptr,nullptr,-1,nullptr)==nullptr);
}
inline constexpr std::size_t target_search_group_count=3;
inline void run_target_search_groups(){target_search_spatial_matches_all_filters();target_search_same_frame_lifecycle_and_nested_queries();target_search_pruning_preserves_target_and_reduces_native_calls();}
}
