"""Reviewed campaign objective corrections; original success actions survive."""
import struct

# Complete-base objectives, including the two existing defense alternatives.
# Omega checks the four production-building types for each enemy base.
FULL_VISION_MISSIONS=frozenset((103,105,108,109,201,203,206,207,301,303,
                              402,408,604,614,615,616,617,618,605,609,610))


def apply(chk,row):
    if row['mission_id']!=206:return None
    from sc1.native_campaign import build_all_campaigns as b
    ts=b.triggers(chk)
    assert [a[26] for _,a in b.actions(ts[2])]==[13]
    assert any(a[26]==1 for _,a in b.actions(ts[5]))
    assert [(b.cf(c)['type'],b.cf(c)['unit']) for _,c in b.conditions(ts[2])]==[(3,229),(3,229)]
    enemies=b.players_for(chk,19,row['owner'])
    buildings=b.count_matches(b.units(chk),enemies,231)
    assert buildings>0 and row['owner'] not in enemies
    # The original cleanup switch opens a separate Tassadar encounter. This
    # mission now ends at base destruction; keep its actions but disable that
    # obsolete transition, so no earlier cinematic races the growth handshake.
    transition=bytearray(ts[2]);transition[:320]=bytes(320);transition[:20]=b.cond(23)
    ts[2]=bytes(transition)
    ending=bytearray(ts[5]);ending[:320]=bytes(320)
    cs=[b.cond(12,count=1),b.cond(2,19,0,231,10),b.cond(2,row['owner'],1,51)]
    for i,c in enumerate(cs):ending[i*20:(i+1)*20]=c
    assert ending[320:]==ts[5][320:];ts[5]=bytes(ending)
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
                kerrigan_required=True,original_success_actions_preserved=True)


def header():
    ids=','.join(str(x) for x in sorted(FULL_VISION_MISSIONS))
    return '#pragma once\nnamespace campaign_visibility {\ninline constexpr U32 missions[]={'+ids+'};\n}\n'
