#pragma once
namespace legend_focus {
struct Rule {unsigned ordinal,mode,base,cadence,proc,step,limit;unsigned units[8];};
inline constexpr Rule rules[]={
{49u,1u,100u,1u,300u,0u,35u,{65538u,0u,0u,280u,0u,0u,0u,0u}},
{54u,7u,200u,1u,100u,0u,0u,{524292u,0u,0u,0u,0u,0u,0u,0u}},
{55u,2u,0u,2u,700u,0u,0u,{3347054688u,0u,0u,0u,0u,0u,0u,0u}},
{56u,0u,200u,1u,0u,0u,0u,{393240u,0u,0u,0u,0u,0u,0u,0u}},
{57u,2u,100u,3u,600u,0u,0u,{939528192u,0u,0u,64u,0u,0u,0u,0u}},
{60u,0u,500u,1u,0u,0u,0u,{8192u,0u,0u,0u,0u,0u,0u,0u}},
{90u,3u,0u,1u,0u,30u,180u,{0u,2097216u,0u,0u,0u,0u,0u,0u}},
{96u,9u,50u,1u,0u,0u,0u,{0u,32768u,0u,0u,0u,0u,0u,0u}},
{105u,0u,200u,1u,0u,0u,0u,{0u,8390656u,0u,0u,0u,0u,0u,0u}},
{137u,2u,75u,4u,600u,0u,0u,{0u,0u,16388u,0u,0u,0u,0u,0u}},
{139u,5u,100u,1u,30u,0u,200u,{0u,0u,4112u,0u,0u,0u,0u,0u}},
{141u,0u,400u,1u,0u,0u,0u,{0u,0u,2097152u,0u,0u,0u,0u,0u}},
{142u,8u,75u,1u,200u,0u,0u,{0u,0u,16842816u,0u,0u,0u,0u,0u}},
{148u,3u,0u,1u,0u,20u,120u,{0u,0u,512u,0u,0u,0u,0u,0u}},
{184u,2u,25u,3u,300u,0u,0u,{1048577u,0u,0u,0u,0u,0u,0u,0u}},
{190u,6u,0u,1u,0u,1u,0u,{0u,4194336u,0u,0u,0u,0u,0u,0u}},
{194u,1u,200u,1u,200u,0u,50u,{0u,0u,8194u,0u,0u,0u,0u,0u}},
{197u,2u,0u,6u,900u,0u,0u,{0u,268435456u,0u,4u,0u,0u,0u,0u}},
};
inline constexpr bool converted(unsigned ordinal) noexcept {for(auto r:rules)if(r.ordinal==ordinal)return true;return false;}
}
