#pragma once
namespace legendary_bundles {
struct Entry {unsigned index,family,race;};
inline constexpr Entry entries[]={{300,9,1},{301,9,1},{302,1,1},{303,12,1},{304,12,1},{305,34,1},{341,46,2},{342,46,2},{343,45,2},{344,43,2},{345,62,2},{346,45,2},{383,67,3},{384,71,3},{385,63,3},{386,67,3},{387,73,3},{388,71,3}};
inline constexpr bool compatible(unsigned a,unsigned b) noexcept {
 for(auto left:entries)if(left.index==a)for(auto right:entries)if(right.index==b)
  return left.race==right.race && left.family!=right.family;return false; }
}
