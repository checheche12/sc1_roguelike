#pragma once
namespace host_test {
inline constexpr std::size_t qa17_group_count=1;
inline void qa17_fog_resource_snapshots_preserve_current_sight(){
 using namespace qa12_extra;qa9_fixture::begin({});auto old=g.mission;auto mission=*old;mission.mission_id=206;g.mission=&mission;
 campaign_visibility::reset();campaign_visibility::first=first;campaign_visibility::create=create;rework_combat_v5::get_sprite_position=position;rework_combat_v5::get_tiles=qa10_fixture::get_tiles;
 created=attempts=0;fail=false;fows={};ghosts={};std::vector<bw::Unit*> nodes;
 for(U32 id:{176u,177u,178u,188u,110u,149u,157u}){
  auto u=rework_fixture::unit(id,id>=176?11:6,200+int(nodes.size())*80,100);nodes.push_back(u);
  auto sprite=static_cast<bw::SpriteScr*>(u->flingy.sprite);sprite->visibility_mask=0;sprite->position[0]=u->flingy.position.x;sprite->position[1]=100;
 }
 auto mobile=rework_fixture::unit(37,6,1000,100);static_cast<bw::SpriteScr*>(mobile->flingy.sprite)->visibility_mask=0;
 qa10_fixture::tiles.fill(0xa55affffu);campaign_visibility::step();CHECK(created==7 && attempts==7);
 U32 mineral_ghost=0;
 for(auto u:nodes){auto match=std::find_if(fows.begin(),fows.begin()+7,[&](const auto& f){return f.unit_id==u->unit_id;});CHECK(match!=fows.begin()+7);CHECK(match->sprite->visibility_mask==2);CHECK(static_cast<bw::SpriteScr*>(u->flingy.sprite)->visibility_mask==0);if(u==nodes[0])mineral_ghost=U32(match-fows.begin());}
 CHECK((qa10_fixture::tiles[0]&255u)==255u);campaign_visibility::step();CHECK(created==7);
 // Resources are last-known snapshots, never live tracking through the fog.
 static_cast<bw::SpriteScr*>(nodes[0]->flingy.sprite)->position[0]=1200;campaign_visibility::step();CHECK(created==7 && ghosts[mineral_ghost].position[0]==200);
 campaign_visibility::reset();campaign_visibility::step();CHECK(created==8 && ghosts[7].position[0]==1200); // Changed position needs its own snapshot after reset.
 g.mission=old;campaign_visibility::first=nullptr;campaign_visibility::create=nullptr;rework_combat_v5::get_tiles=nullptr;campaign_visibility::reset();qa9_fixture::end();
}
inline void run_qa17_groups(){qa17_fog_resource_snapshots_preserve_current_sight();}
}
