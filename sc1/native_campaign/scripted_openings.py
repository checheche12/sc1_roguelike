"""Original event factions must never become static or timed reinforcements."""

SOUTHWEST_EXPANSION=(128,2704)
SPAWN_EXCLUSION_RADIUS=768

def additional_spawn_allowed(mission,x,y):
    if mission['mission_id']!=402:return True
    return (x-SOUTHWEST_EXPANSION[0])**2+(y-SOUTHWEST_EXPANSION[1])**2>=SPAWN_EXCLUSION_RADIUS**2

def excluded_factions(mission):
    # EXPProtoss02 P2 holds four DTs in exact one-unit Move Unit locations.
    # P4 creates the opening hydras and drives their original suicide script.
    # Extra DTs keep Bring-at-most-zero false and strand on the holding island.
    return frozenset((1,3)) if mission['mission_id']==402 else frozenset()


def evidence(mission):
    if mission['mission_id']!=402:
        return None
    return dict(mission=402,excluded_zero_based_owners=[1,3],
                excluded_spawn_center=list(SOUTHWEST_EXPANSION),excluded_spawn_radius=SPAWN_EXCLUSION_RADIUS,
                original_dark_templars=4,holding_location_ids=[9,25,26,27],
                teleport_trigger=17,holding_empty_trigger=18,attack_ai_trigger=29,
                reason='Extra DTs in holding locations prevent the original attack-AI switch; opening ambush owners are scripted, not garrison factions.',
                original_triggers_unchanged=True)
