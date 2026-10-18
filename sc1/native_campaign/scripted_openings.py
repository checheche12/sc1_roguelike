"""Reviewed scripted openings and factions excluded from extra reinforcements."""
import struct

SOUTHWEST_EXPANSION=(128,2704)
SPAWN_EXCLUSION_RADIUS=768

def additional_spawn_allowed(mission,x,y):
    if mission['mission_id']!=402:return True
    return (x-SOUTHWEST_EXPANSION[0])**2+(y-SOUTHWEST_EXPANSION[1])**2>=SPAWN_EXCLUSION_RADIUS**2

def excluded_factions(mission):
    # EXPProtoss02 P2 holds four DTs in exact one-unit Move Unit locations.
    # P4 creates the opening hydras and drives their original suicide script.
    # Extra DTs keep Bring-at-most-zero false and strand on the holding island.
    if mission['mission_id']==402:return frozenset((1,3))
    # Uraj's landing army must clear this small base before the player can
    # establish an economy. It is not a source for additional enemy armies.
    return frozenset((5,)) if mission['mission_id']==404 else frozenset()


def apply(chk,mission):
    """Change only the four reviewed Probe drops and their resource actions."""
    if mission['mission_id']!=404:return None
    raw=bytearray(chk.getsection('TRIG'))
    trigger=15;changes=[]
    for action,count in ((4,3),(7,3),(10,2),(14,2)):
        offset=trigger*2400+320+action*32
        before=bytes(raw[offset:offset+32])
        assert struct.unpack_from('<I',before)[0]==3
        assert struct.unpack_from('<I',before,16)[0]==mission['owner']==1
        assert struct.unpack_from('<H',before,24)[0]==64
        assert before[26:28]==bytes((44,1)),('Uraj Probe drop changed',action)
        raw[offset+27]=count
        changes.append(dict(trigger=trigger,action=action,before=before.hex(),after=bytes(raw[offset:offset+32]).hex()))
    for action,resource,old_amount,bonus in ((15,0,800,1500),(16,1,100,500)):
        offset=trigger*2400+320+action*32
        before=bytes(raw[offset:offset+32])
        assert struct.unpack_from('<I',before,16)[0]==mission['owner']
        assert struct.unpack_from('<I',before,20)[0]==old_amount
        assert struct.unpack_from('<H',before,24)[0]==resource
        assert before[26:28]==bytes((26,8)),('Uraj resource action changed',action)
        # CHK ValueModifier is SetTo=7, Add=8, Subtract=9. The original
        # landing also uses Add; preserve that operation and increase its amount.
        struct.pack_into('<I',raw,offset+20,bonus);raw[offset+27]=8
        changes.append(dict(trigger=trigger,action=action,before=before.hex(),after=bytes(raw[offset:offset+32]).hex()))
    chk.setsection('TRIG',bytes(raw))
    return dict(mission=404,probe_drops_before=[1,1,1,1],probe_drops_after=[3,3,2,2],
                probes=10,landing_mineral_bonus=1500,landing_gas_bonus=500,
                original_landing_resource_actions_replaced=True,resource_operation='Add',changes=changes,
                original_drop_conditions_waits_audio_and_combat_units_preserved=True,
                personal_records_changed=False,live_game_verified=False)


def evidence(mission):
    if mission['mission_id']==404:
        return dict(mission=404,excluded_zero_based_owners=[5],probes=10,
                    landing_mineral_bonus=1500,landing_gas_bonus=500,
                    original_landing_resource_actions_replaced=True,resource_operation='Add',
                    original_triggers_unchanged=False,
                    reason='Preserve the original landing army and opening-base opponents; strengthen the landing economy and remove additional static enemies.')
    if mission['mission_id']!=402:
        return None
    return dict(mission=402,excluded_zero_based_owners=[1,3],
                excluded_spawn_center=list(SOUTHWEST_EXPANSION),excluded_spawn_radius=SPAWN_EXCLUSION_RADIUS,
                original_dark_templars=4,holding_location_ids=[9,25,26,27],
                teleport_trigger=17,holding_empty_trigger=18,attack_ai_trigger=29,
                reason='Extra DTs in holding locations prevent the original attack-AI switch; opening ambush owners are scripted, not garrison factions.',
                original_triggers_unchanged=True)
