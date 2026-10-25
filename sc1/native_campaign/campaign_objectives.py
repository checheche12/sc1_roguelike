"""Reviewed campaign objectives and explicit final-cinematic removals.

Victory still passes through the builder's growth and durable-save handshake.
"""
import struct

# Complete-base objectives, including the two existing defense alternatives.
# Omega checks the four production-building types for each enemy base.
FULL_VISION_MISSIONS=frozenset((103,105,108,109,201,203,206,207,301,303,
                              402,408,604,614,615,616,617,618,605,609,610))


def apply(chk,row):
    if row['mission_id']==407:return _insurgent(chk,row)
    if row['mission_id']!=206:return None
    from sc1.native_campaign import build_all_campaigns as b
    ts=b.triggers(chk)
    assert [a[26] for _,a in b.actions(ts[2])]==[13]
    assert any(a[26]==1 for _,a in b.actions(ts[5]))
    assert [(b.cf(c)['type'],b.cf(c)['unit']) for _,c in b.conditions(ts[2])]==[(3,229),(3,229)]
    enemies=b.players_for(chk,19,row['owner'])
    buildings=b.count_matches(b.units(chk),enemies,231)
    assert buildings>0 and row['owner'] not in enemies
    # Remove both the obsolete encounter and its final camera/dialogue/waits.
    # Keep empty slots so source-trigger indices remain stable for evidence.
    removed=(2,4,7)
    for index in removed:
        ts[index]=b.new_trigger([b.cond(23)],[],ts[index][2372:2400])
    cs=[b.cond(12,count=1),b.cond(2,19,0,231,10),b.cond(2,row['owner'],1,51)]
    victory=[a for _,a in b.actions(ts[5]) if a[26]==1]
    assert len(victory)==1
    ts[5]=b.new_trigger(cs,victory,ts[5][2372:2400])
    text='저그 6: "다크 템플러"\r\n- 프로토스 건물 모두 파괴\r\n- 케리건 생존'
    before=chk.getsection('STR ');sid=len(b.strings(before))+1
    chk.setsection('STR ',b.append_marker(before,text.encode('utf8')))
    startup=bytearray(ts[1]);assert startup[320+26]==12
    struct.pack_into('<I',startup,320+4,sid);ts[1]=bytes(startup)
    chk.setsection('TRIG',b''.join(ts))
    return dict(mission=206,kind='all_protoss_buildings',target_player_group=19,
                original_enemy_owners=sorted(enemies),initial_buildings=buildings,
                victory_trigger=5,obsolete_transition_trigger=2,objective_string_id=sid,
                mobile_units_required=False,tassadar_encounter_required=False,
                kerrigan_required=True,original_success_actions_preserved=False,
                final_cinematic_removed=True,removed_cinematic_triggers=list(removed),
                victory_actions_only=True)


def _insurgent(chk,row):
    from sc1.native_campaign import build_all_campaigns as b
    ts=b.triggers(chk)
    completion=[c for _,c in b.conditions(ts[8])]
    assert [b.cf(c) for c in completion]==[
        b.cf(b.cond(3,7,0,79,10,9)),b.cf(b.switch_condition(9,False))]
    assert completion[1][16]==9
    switch_actions=[a for _,a in b.actions(ts[8]) if a[26]==13]
    assert switch_actions==[b.setswitch(9),b.setswitch(10)]
    assert [c for _,c in b.conditions(ts[9])]==[b.switch_condition(10)]
    victory=[a for _,a in b.actions(ts[24]) if a[26]==1]
    assert len(victory)==1
    # Retain the exact last-combat condition and its defeat-suppression latch.
    # Set both immediately: no cinematic unit creation, Wait, or ownership
    # transfer can delay the goal or remove the player's army during rewards.
    ts[8]=b.new_trigger(completion,switch_actions,ts[8][2372:2400])
    removed=(*range(9,24),25,26,27)
    for index in removed:
        ts[index]=b.new_trigger([b.cond(23)],[],ts[index][2372:2400])
    ts[24]=b.new_trigger([b.switch_condition(10)],victory,ts[24][2372:2400])
    chk.setsection('TRIG',b''.join(ts))
    return dict(mission=407,kind='original_final_battle_without_cinematic',
                combat_completion_trigger=8,combat_conditions_preserved=True,
                completion_switch=10,defeat_suppression_switch=9,victory_trigger=24,
                final_cinematic_removed=True,removed_cinematic_triggers=list(removed),
                kerrigan_arrival_required=False,overlord_arrival_required=False,
                original_success_actions_preserved=False,victory_actions_only=True)


def header():
    ids=','.join(str(x) for x in sorted(FULL_VISION_MISSIONS))
    return '#pragma once\nnamespace campaign_visibility {\ninline constexpr U32 missions[]={'+ids+'};\n}\n'
