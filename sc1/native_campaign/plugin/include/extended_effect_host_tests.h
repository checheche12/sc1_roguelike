// Every published talent's data/mutation path is exercised through production
// callbacks. Synthetic engine inputs do not establish real effect reachability,
// projectile collision, movement distance, attack animation timing or DPS.
namespace host_test {
Key inspect_key{};U32 observed_field=0;
void __cdecl inspect_field(bw::Unit*){observed_field=raw_value(inspect_key.table,inspect_key.field,inspect_key.id);}
void __cdecl inspect_command(const void*,U32,U32){observed_field=raw_value(inspect_key.table,inspect_key.field,inspect_key.id);}
U32 expected_patch(U32 base,const frozen::Patch& p){
    const std::uint64_t v=base;
    if(p.op==0)return p.numerator;if(p.op==1)return base+p.numerator;
    if(p.op==2)return static_cast<U32>(std::max<std::uint64_t>(1,(v*p.numerator+p.denominator/2)/p.denominator));
    if(p.op==3)return static_cast<U32>((v*p.numerator+p.denominator-1)/p.denominator);
    return static_cast<U32>((v*p.numerator+p.denominator/2)/p.denominator);
}
void every_talent_owner_callback_and_reapply(){
    for(U32 bit=0;bit<frozen::kLegacyTalentCount;bit++){
        reset();GrowthSnapshot snapshot{};snapshot.talent_bits[bit/32]=1u<<(bit%32);snapshot.completed_phase=1;
        CHECK(apply_snapshot(nullptr,snapshot));U32 effects=0;
        for(const auto& patch:frozen::patches){if(patch.bit!=bit)continue;++effects;
            inspect_key={patch.table,patch.field,patch.id};const auto stock=original_stat(inspect_key),expected=expected_patch(stock,patch);
            CHECK(owner_stat(1,inspect_key)==expected && owner_stat(6,inspect_key)==stock && owner_stat(11,inspect_key)==stock);
            const U32 id=patch.table==0 ? patch.id : 0u;auto own=add(id,1,100,100),enemy=add(id,6,900,900),neutral=add(id,11,1200,1200);
            if(patch.table==1 && patch.field==16){
                // The native iscript pass resets a weapon cooldown; the post-step
                // hook changes only the owning unit's elapsed cooldown instance.
                write_entry(&dat[0][17],0,patch.id);own->ground_cooldown=enemy->ground_cooldown=neutral->ground_cooldown=static_cast<U8>(stock);
                note_attack_launch(own,patch.id);note_attack_launch(enemy,patch.id);note_attack_launch(neutral,patch.id);apply_unit_motion();CHECK(own->ground_cooldown==expected && enemy->ground_cooldown==stock && neutral->ground_cooldown==stock);
                const auto once=own->ground_cooldown;note_attack_launch(own,patch.id);apply_unit_motion();CHECK(own->ground_cooldown==once);
            }else{
                const U32 engine_expected=patch.table==0 && patch.field==48 && (patch.id==11 || patch.id==42 || patch.id==57 || patch.id==69) ? std::min(expected,8u):expected;
                owner_unit_hook(own,inspect_field);CHECK(observed_field==engine_expected);
                owner_unit_hook(enemy,inspect_field);CHECK(observed_field==stock);
                owner_unit_hook(neutral,inspect_field);CHECK(observed_field==stock);
                saved_handle=1;owner_commands_hook(nullptr,0,0,inspect_command);CHECK(observed_field==engine_expected);
                saved_handle=6;owner_commands_hook(nullptr,0,0,inspect_command);CHECK(observed_field==stock);
            }
            CHECK(raw_value(inspect_key.table,inspect_key.field,inspect_key.id)==stock);
        }
        for(const auto& movement:frozen::movement_patches)if(movement.bit==bit){++effects;
            auto own=add(movement.unit_id,1,100,100),enemy=add(movement.unit_id,6,900,900),neutral=add(movement.unit_id,11,1200,1200);
            own->flingy.top_speed=enemy->flingy.top_speed=neutral->flingy.top_speed=1000;apply_unit_motion();
            CHECK(own->flingy.top_speed==(1000*movement.numerator+movement.denominator/2)/movement.denominator);
            CHECK(enemy->flingy.top_speed==1000 && neutral->flingy.top_speed==1000);
        }
        // Historical104/105 are pure abilities. Rank126/135 intentionally add
        // HP/armor as well; the per-key loop above and the fixed rank regression
        // check those edits. All four share target/cadence/owner callback tests.
        for(const auto& multi:frozen::multi_target_patches)if(multi.bit==bit){
            ++effects;CHECK(multi.unit_id==3 || multi.unit_id==12);
            if(bit==104 || bit==105)CHECK(g.friendly_edits.empty());
            else {CHECK(bit==126 || bit==135);CHECK(!g.friendly_edits.empty());}
        }
        CHECK(effects>0);const auto before=g.friendly_edits;std::vector<int> hp;for(std::size_t i=0;i<count;i++)hp.push_back(units[i].flingy.hitpoints);
        snapshot.completed_phase=2;CHECK(apply_snapshot(nullptr,snapshot));CHECK(g.friendly_edits.size()==before.size());
        for(std::size_t i=0;i<before.size();i++)CHECK(g.friendly_edits[i].after==before[i].after);
        for(std::size_t i=0;i<count;i++)CHECK(units[i].flingy.hitpoints==hp[i]);
    }
}
void continuous_attack_cooldown(){
    reset();GrowthSnapshot s{};s.talent_bits[0]=1u<<2;CHECK(apply_snapshot(nullptr,s));
    auto own=add(0,1,100,100),enemy=add(0,6,900,900),neutral=add(0,11,1200,1200);const auto base=original_stat({1,16,0});U32 shots[3]{};int first[3]={-1,-1,-1};
    for(U32 frame=0;frame<240;frame++){
        game.frame_count=frame;U32 index=0;for(auto unit:{own,enemy,neutral}){if(unit->ground_cooldown)--unit->ground_cooldown;if(!unit->ground_cooldown){unit->ground_cooldown=static_cast<U8>(base);note_attack_launch(unit,0);++shots[index];if(first[index]<0)first[index]=static_cast<int>(frame);}++index;}
        apply_unit_motion();
    }
    // Fractional scheduling alternates11/12; fixed12 would yield only20shots.
    CHECK(first[0]==0 && first[1]==0 && first[2]==0);CHECK(shots[0]==21 && shots[1]==16 && shots[1]==shots[2]);CHECK(raw_value(1,16,0)==base);
    const auto track=existing_track(own);const auto fraction=track->cooldown[0].fraction;
    own->ground_cooldown=static_cast<U8>(base);++game.frame_count;apply_unit_motion();CHECK(own->ground_cooldown==base && track->cooldown[0].fraction==fraction);
    // Ground and air keep independent fractional sequences; stopping a timer
    // or changing the weapon does not consume a shot or rescale progress.
    own->air_cooldown=static_cast<U8>(base);note_attack_launch(own,0);apply_unit_motion();CHECK(own->air_cooldown==12);
    const auto air_fraction=track->cooldown[1].fraction;own->air_cooldown=10;apply_unit_motion();CHECK(own->air_cooldown==10 && track->cooldown[1].fraction==air_fraction);
    write_entry(&dat[0][17],0,4);own->ground_cooldown=9;apply_unit_motion();CHECK(own->ground_cooldown==9 && track->cooldown[0].fraction==0);
    reset();CHECK(apply_snapshot(nullptr,s));own=add(0,1,100,100);U32 total=0;
    for(U32 shot=0;shot<13;shot++){game.frame_count=total;own->ground_cooldown=15;note_attack_launch(own,0);apply_unit_motion();total+=own->ground_cooldown;}
    CHECK(total==150); //13attacks per150frames versus10at native15: exactly+30%.

}
void six_new_curse_effects(){
    reset();GrowthSnapshot s{};for(U32 i=9;i<15;i++)s.curse_counts[i]=1;CHECK(apply_snapshot(nullptr,s));game.frame_count=100;game.elapsed_seconds=4;
    auto first=add(0,6,500,500,6000),second=add(0,6,520,500,4000),third=add(0,6,540,500,2000);refresh_units();g.current_wave_id=1;g.wave_spawn_number=0;
    mark_wave_unit(first);mark_wave_unit(second);mark_wave_unit(third);
    CHECK(existing_track(first)->commander && existing_track(first)->medic);CHECK(existing_track(first)->pair_index==static_cast<U32>(second-g.units));
    game.frame_count=292;first->ground_cooldown=15;CHECK(charged_attack(first,0)==20);game.frame_count=294;CHECK(charged_attack(first,0)==20);
    game.frame_count=307;CHECK(charged_attack(first,0)==0);existing_track(first)->last_damage_frame=500;game.frame_count=600;CHECK(charged_attack(first,0)==0);
    // Real HP loss only heals a hostile attacker; shields and self/friendly hits do not.
    auto human=add(0,1,500,500,10000);const auto old=first->flingy.hitpoints;g.normal_hit=true;owner_damage_hook(human,1000,first,6,1,fake_damage);g.normal_hit=false;CHECK(first->flingy.hitpoints==old+100);
    const auto shield_only_hp=first->flingy.hitpoints;g.normal_hit=true;owner_damage_hook(human,0,first,6,1,fake_damage);g.normal_hit=false;CHECK(first->flingy.hitpoints==shield_only_hp);
    const auto old2=first->flingy.hitpoints;g.normal_hit=true;owner_damage_hook(second,1000,first,6,1,fake_damage);g.normal_hit=false;CHECK(first->flingy.hitpoints==old2);
    game.frame_count=624;const auto third_hp=third->flingy.hitpoints;update_diversity();CHECK(third->flingy.hitpoints==third_hp+1536);
    existing_track(first)->last_damage_frame=624;first->last_attacking_player=1;owner_kill_hook(first,kill);
    CHECK(g.bombs.size()==1 && existing_track(second)->pair_due==672 && existing_track(second)->command_until==816);
    // A nearby simultaneous combat death merges its warning/damage payload.
    auto duplicate=add(0,6,508,500,1000);refresh_units();auto dup=track_unit(duplicate);dup->spawned=true;dup->wave_id=99;dup->last_damage_frame=624;duplicate->last_attacking_player=1;owner_kill_hook(duplicate,kill);CHECK(g.bombs.size()==1);
    auto worker=add(7,1,500,500,10000),hero=add(20,1,500,500,10000),air=add(8,1,500,500,10000);air->flags|=4;auto ally=add(0,2,500,500,10000);game.starting_player_types[2]=3;
    CHECK(ground_pulses>0);const auto hp=human->flingy.hitpoints;human->shields=512;game.frame_count=647;update_diversity();CHECK(human->flingy.hitpoints==hp);
    game.frame_count=648;update_diversity();CHECK(human->shields==0 && human->flingy.hitpoints==hp-1536);CHECK(worker->flingy.hitpoints==10000 && hero->flingy.hitpoints==10000 && air->flingy.hitpoints==10000 && ally->flingy.hitpoints==10000);
    const auto pair_hp=second->flingy.hitpoints;game.frame_count=671;update_diversity();CHECK(second->flingy.hitpoints==pair_hp);
    game.frame_count=672;update_diversity();CHECK(second->flingy.hitpoints==std::min(static_cast<int>(effective_max_hp(second)),pair_hp+static_cast<int>(effective_max_hp(second)*35/100)));
    second->flingy.top_speed=1000;apply_unit_motion();CHECK(second->flingy.top_speed==1200);game.frame_count=816;apply_unit_motion();CHECK(second->flingy.top_speed==1000);
}
void over_ninety_wave_capacity(){
    reset();const auto& home=sc1_native::wave_config::kHome;add(7,1,(home.left+home.right)/2,(home.top+home.bottom)/2);sc1_native::WaveHost host{nullptr,wave_count,wave_spawn,wave_attack,wave_warning};
    for(U32 frame=1;frame<10000;frame++){
        g.waves.tick(frame,true,300,255,false,host);
        // Host path simulation: successful groups leave the entry; live
        // additional troops remain counted across later waves.
        for(std::size_t i=1;i<count;i++)if(existing_track(&units[i]) && existing_track(&units[i])->spawned)units[i].flingy.position={1056,1600};
    }
    const auto lings=wave_count(nullptr,6,37,nullptr),hydras=wave_count(nullptr,6,38,nullptr);CHECK(lings+hydras>90 && added_supply()<=480);CHECK(count<=1600);
}
void run_extended_effect_groups(){every_talent_owner_callback_and_reapply();continuous_attack_cooldown();six_new_curse_effects();over_ninety_wave_capacity();}
}
