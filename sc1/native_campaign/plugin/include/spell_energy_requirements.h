#pragma once
// Included inside rework_combat_v5. The existing successful-cast refund is
// retained exactly (including Q8 fractions); validation may use its net cost.
inline U32 spell_tech(U32 order) noexcept {
    switch(order){
    case 115:return 1;case 122:return 2;case 141:return 6;case 143:return 7;case 113:case 114:return 8;
    case 121:return 13;case 119:return 14;case 144:return 15;case 145:return 16;case 146:return 17;case 120:return 18;
    case 142:return 19;case 148:return 20;case 137:return 21;case 147:return 22;
    case 180:return 24;case 181:return 25;case 182:return 27;case 184:return 29;case 185:return 30;case 186:return 31;
    case 175:case 176:case 178:return 34;default:return 44;
    }
}
inline U32 cast_energy_refund(bw::Unit* u,U32 order,U32 spent) noexcept {
    U32 refund=0;
    if(group(38,u->unit_id)&&rank(38))refund=spent*std::min(90u,talent_power::v5(38,30))/100;
    if(group(78,u->unit_id)&&rank(78))refund=spent*talent_power::v5(78,25)/100;
    if(group(120,u->unit_id)&&rank(120))refund=spent*talent_power::v5(120,25)/100;
    if(order==137&&rank(126))refund=std::min(spent,refund+talent_power::v5(126,75*256));
    return std::min(spent,refund);
}
struct SpellEnergyAdvance {
    Identity who{};U32 amount=0;
    void begin(bw::Unit* u,U32 order) noexcept {
        if(!g.active||!g.applied||!g.game||GetCurrentThreadId()!=g.game_thread.load()||!own(u))return;
        const U32 tech=spell_tech(order);if(tech>=44)return;
        const U32 base=owner_stat(u->player,{4,3,tech})*256,refund=cast_energy_refund(u,order,base);
        if(!refund||base>65535u||u->energy>=base||u->energy<base-refund)return;
        who=identity(u);amount=base-u->energy;u->energy=std::uint16_t(base);
    }
    void restore() noexcept {
        // Ownership changes do not keep the advance; slot reuse never inherits
        // its cleanup. No reserve energy or maximum-energy state is changed.
        if(amount)if(auto u=generation(who))u->energy=std::uint16_t(U32(u->energy)-std::min(U32(u->energy),amount));
        amount=0;
    }
};
struct SpellEnergyRequirementScope {
    SpellEnergyAdvance advance;
    SpellEnergyRequirementScope(bw::Unit* u,U32 order) noexcept {advance.begin(u,order);}
    ~SpellEnergyRequirementScope(){advance.restore();}
};
inline U32 targeted_spell_order(const U8* data,U32 length) noexcept {
    // Native TargetedOrder packet: command,x,y,target,fow-unit,order,queued.
    if(!data)return 0;
    if(length==11&&data[0]==0x15)return data[9];
    return length==13&&data[0]==0x61 ? data[11]:0;
}
struct SpellCommandEnergyScope {
    std::vector<SpellEnergyAdvance> advances;
    SpellCommandEnergyScope(U32 player,const U8* data,U32 length){
        const U32 order=targeted_spell_order(data,length);
        if(player!=player_owner()||spell_tech(order)>=44)return;
        try{living_units([&](bw::Unit* u){SpellEnergyAdvance a;a.begin(u,order);if(a.amount){try{advances.push_back(a);}catch(...){a.restore();throw;}}});}
        catch(...){for(auto& a:advances)a.restore();throw;}
    }
    ~SpellCommandEnergyScope(){for(auto it=advances.rbegin();it!=advances.rend();++it)it->restore();}
};
