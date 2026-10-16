#pragma once
// Derived from original mission Defeat requirements, not ordinary army-loss conditions.
namespace objective_guards {
struct Origin { U32 mission_id,unit_id,owner,x,y; };
inline constexpr Origin origins[] = {
    {608,61,1,976,1949},
    {608,61,1,926,2064},
};
}
