#pragma once
// QA6 scales the benefit of a talent, never the base statistic or its cost.
#include "talent_power.generated.h"
namespace talent_power {
#ifdef SC1_NATIVE_HOST_TEST
inline bool enabled=false; // Historical mechanism fixtures; QA6 suite opts in.
#else
inline constexpr bool enabled=true;
#endif
inline U32 quarters(U32 bit) noexcept {return enabled&&bit<std::size(kPowerQuarters) ? kPowerQuarters[bit]:4u;}
inline U32 amount(U32 bit,std::uint64_t value) noexcept {
    return U32(std::min<std::uint64_t>(0x7fffffffu,(std::uint64_t(value)*quarters(bit)+2)/4));
}
inline U32 v5(U32 ordinal,std::uint64_t value) noexcept {return amount(238+ordinal,value);}
inline double ratio(U32 bit,double value) noexcept {
    return std::max(0.1,1.0+(value-1.0)*quarters(bit)/4.0);
}
inline double rate(U32 ordinal,double value) noexcept {return ratio(238+ordinal,value);}
inline void multiply(std::uint64_t& n,std::uint64_t& d,U32 bit,U32 a,U32 b) noexcept {
    std::uint64_t x=a,y=b;
    if(enabled){y=std::uint64_t(b)*4;x=std::uint64_t(std::max<std::int64_t>(std::int64_t(y)/10,std::int64_t(y)+(std::int64_t(a)-b)*quarters(bit)));}
    const auto common=std::gcd(x,y);x/=common;y/=common;
    const auto c1=std::gcd(n,y);n/=c1;y/=c1;
    const auto c2=std::gcd(d,x);d/=c2;x/=c2;
    n*=x;d*=y;
}
inline U32 duration(U32 ordinal,U32 value,U32 maximum=255) noexcept {
    return std::min(maximum,U32(double(value)*rate(ordinal,1.5)));
}
inline U32 discount(U32 ordinal,U32 value,U32 numerator,U32 denominator) noexcept {
    const auto ratio_=rate(ordinal,double(numerator)/denominator);
    return value ? std::max(1u,U32(std::ceil(value*ratio_-1e-9))):0u;
}
inline bool numeric(Key key) noexcept {
    return key.table==0 ? (key.field==7||key.field==8||key.field==23||key.field==24||key.field==27||key.field==40||key.field==41||key.field==42||key.field==45||key.field==48):
        key.table==1&&(key.field==5||key.field==11||key.field==12||key.field==13||key.field==14||key.field==15||key.field==16);
}
inline bool legacy_patch(std::vector<Edit>& edits,const frozen::Patch& p) {
    const Key key{p.table,p.field,p.id};
    if(!enabled||(key.table==0&&(key.field==40||key.field==41||key.field==42||key.field==45)))return plan_edit(edits,key,p.op,p.numerator,p.denominator);
    if(!numeric(key)){
        if(!plan_edit(edits,key,p.op,p.numerator,p.denominator))return false;
        // A damage-type conversion is qualitative. Give its weapon a modest
        // direct firepower bonus as well; IDs and native type remain intact.
        return key.table!=1||key.field!=7||!ordinary_weapon(key.id)||plan_edit(edits,{1,14,key.id},4,5,4);
    }
    auto table=table_for(key,true);if(!table)return false;
    const U32 before=effect_value(edits,key,original_stat(key));
    // Evaluate with the existing native rounding rules, then scale only the
    // favorable delta. IDs, flags, damage types and drawbacks are untouched.
    auto trial=edits;if(!plan_edit(trial,key,p.op,p.numerator,p.denominator))return false;
    const U32 after=effect_value(trial,key,before);
    const bool lower=(key.table==0&&(key.field==40||key.field==41||key.field==42))||(key.table==1&&key.field==16);
    U32 value=after;
    if(p.op==2&&((lower&&p.numerator<p.denominator)||(!lower&&p.numerator>p.denominator))){
        std::uint64_t n=1,d=1;multiply(n,d,p.bit,p.numerator,p.denominator);
        value=U32(std::min<std::uint64_t>(0xffffffffu,(std::uint64_t(before)*n+d/2)/d));
    }else{
        if(lower&&after<before)value=std::max(U32(std::ceil(before*0.1)),before-std::min(before,amount(p.bit,before-after)));
        if(!lower&&after>before)value=before+amount(p.bit,after-before);
    }
    if(key.table==0&&key.field==24)value=std::min(11u,value);
    if(key.table==0&&key.field==48)value=std::min(16u,value);
    if(table->entry_size==1)value=std::min(255u,value);
    if(table->entry_size==2)value=std::min(65535u,value);
    return plan_edit(edits,key,0,value,1);
}
}
