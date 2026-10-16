#pragma once
// Included inside rework_combat_v5. One lineage belongs to one native cast.
// Branching is bounded by generation, never by a shared remaining-jump count.
namespace irradiation {
struct Node {Identity who{};std::uint64_t root=0;U32 generation=0;U8 timer=0;bool active=false;};
struct Root {Identity source{};U32 owner=12,duration=0,active=0;std::unordered_map<std::uint64_t,bool> visited;};
inline std::vector<Node> nodes;inline bw::Unit* base=nullptr;
inline std::unordered_map<std::uint64_t,Root> roots;inline std::uint64_t serial=0;
inline std::unordered_map<U32,std::vector<Identity>> cells;inline U32 cell_frame=~0u;
inline std::uint64_t key(const bw::Unit* u) noexcept {return (std::uint64_t(std::size_t(u-g.units))<<8)|u->minor_unique_index;}
inline U32 cell(int x,int y) noexcept {return (U32(x/256)&65535u)|(U32(y/256)<<16);}
inline void reset() noexcept {nodes.clear();roots.clear();cells.clear();base=nullptr;serial=0;cell_frame=~0u;}
inline void storage(){if(base!=g.units||nodes.size()!=g.units_count){reset();base=g.units;nodes.resize(g.units_count);}}
inline void grid(){if(cell_frame==now())return;cells.clear();living_units([&](bw::Unit* u){if(eligible(u))cells[cell(u->flingy.position.x,u->flingy.position.y)].push_back(identity(u));});cell_frame=now();}
inline std::vector<Identity> nearby(int x,int y,U32 radius){
    grid();std::vector<Identity> result;const int reach=int(radius)+128;
    for(int yy=std::max(0,y-reach)/256;yy<=(y+reach)/256;yy++)for(int xx=std::max(0,x-reach)/256;xx<=(x+reach)/256;xx++){
        auto it=cells.find(U32(xx)|(U32(yy)<<16));if(it!=cells.end())result.insert(result.end(),it->second.begin(),it->second.end());
    }return result;
}
inline std::uint64_t box_distance(const bw::Unit* a,const bw::Unit* b) noexcept {
    const auto aa=multi_target::dimensions(a->unit_id),bb=multi_target::dimensions(b->unit_id);
    const int ax=a->flingy.position.x,ay=a->flingy.position.y,bx=b->flingy.position.x,by=b->flingy.position.y;
    const int dx=std::max({0,bx-int(bb.left)-(ax+int(aa.right)),ax-int(aa.left)-(bx+int(bb.right))});
    const int dy=std::max({0,by-int(bb.top)-(ay+int(aa.bottom)),ay-int(aa.top)-(by+int(bb.bottom))});
    return std::uint64_t(dx)*dx+std::uint64_t(dy)*dy;
}
inline void forget(bw::Unit* u) noexcept {
    if(!valid_unit(u)||base!=g.units||nodes.size()!=g.units_count)return;auto& n=nodes[std::size_t(u-g.units)];
    if(n.active){auto root=roots.find(n.root);if(root!=roots.end()&&root->second.active)--root->second.active;n={};}
}
inline void enroll(bw::Unit* u,std::uint64_t root_id,U32 generation,bool visual){
    storage();forget(u);auto it=roots.find(root_id);if(it==roots.end())return;
    auto& root=it->second;root.visited[key(u)]=true;++root.active;
    u->irradiate_timer=U8(root.duration);u->irradiated_by=generation ? rework_combat_v5::generation(root.source):u->irradiated_by;u->irradiate_player=U8(root.owner);
    nodes[std::size_t(u-g.units)]={identity(u),root_id,generation,u->irradiate_timer,true};
    if(visual&&g.add_overlay&&!(u->flags&0x10u))if(auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite))if(sprite->main_image){
        const U32 size=std::max(1u,std::min(3u,original_stat({0,26,u->unit_id})));g.add_overlay(sprite->main_image,379u+size,0,0,1);
    }
}
inline void attach(bw::Unit* u,bw::Unit* source,U32 owner){
    storage();if(!valid_unit(u)||!u->irradiate_timer)return;
    const auto root_id=++serial;Root root{};root.source=identity(source);root.owner=owner;root.duration=u->irradiate_timer;
    roots.emplace(root_id,std::move(root));enroll(u,root_id,0,false);
}
inline void on_death(bw::Unit* dead){
    if(!valid_unit(dead)||base!=g.units||nodes.size()!=g.units_count)return;
    const auto n=nodes[std::size_t(dead-g.units)];if(!n.active||rework_combat_v5::generation(n.who)!=dead)return;
    forget(dead);if(n.generation>=5||!is_enemy(dead->player)||(!dead->irradiate_timer&&n.timer!=1))return;
    auto it=roots.find(n.root);if(it==roots.end())return;
    auto candidates=nearby(dead->flingy.position.x,dead->flingy.position.y,128);
    std::sort(candidates.begin(),candidates.end(),[&](const Identity& a,const Identity& b){const auto da=dist(dead,a.p),db=dist(dead,b.p);return da==db?a.p<b.p:da<db;});
    U32 made=0;for(const auto& id:candidates){auto u=resolve(id);if(!u||u==dead||!is_enemy(u->player)||!organic(u)||building(u)||in(u->unit_id,{35,36,97})||(u->flags&0x40u)||u->irradiate_timer||box_distance(dead,u)>128ull*128)continue;
        it=roots.find(n.root);if(it==roots.end()||it->second.visited.count(key(u)))continue;
        enroll(u,n.root,n.generation+1,true);if(++made==5)break;
    }
}
inline void step(){
    if(base!=g.units||nodes.size()!=g.units_count)return;
    std::vector<Node> due;for(auto& n:nodes){if(!n.active)continue;auto u=resolve(n.who);
        if(!u||!u->irradiate_timer){if(auto old=rework_combat_v5::generation(n.who))forget(old);else{auto r=roots.find(n.root);if(r!=roots.end()&&r->second.active)--r->second.active;n={};}continue;}
        if(U32(u->irradiate_timer)+1==n.timer)due.push_back(n);n.timer=u->irradiate_timer;
    }
    const U32 tick=original_stat({1,14,34})*256/std::max(1u,original_stat({1,16,34}));
    for(const auto& n:due){auto target=resolve(n.who);auto it=roots.find(n.root);if(!target||it==roots.end()||(target->flags&(0x10u|0x40u)))continue;
        const U32 owner=it->second.owner;auto source=rework_combat_v5::generation(it->second.source);
        for(const auto& id:nearby(target->flingy.position.x,target->flingy.position.y,128)){auto other=resolve(id);
            if(!other||other==target||!organic(other)||building(other)||in(other->unit_id,{35,36,97})||(other->flags&(0x10u|0x40u)))continue;
            const auto d=box_distance(target,other);if(d>32ull*32&&d<=128ull*128)weapon_hurt(other,tick*3,34,source,owner);
        }
    }
    for(auto it=roots.begin();it!=roots.end();)if(!it->second.active)it=roots.erase(it);else ++it;
}
}
