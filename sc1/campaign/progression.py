"""Campaign metadata shared by selection and durable progression.

Mission IDs never double as completion-bit positions. The map manifest is the
single source for race, ordinal and checkpoint eligibility.
"""
from .missions import mission_for_id, load_missions
from .runtime_catalog import GrowthError

CURSE_TIERS = ('common','common','common','uncommon','common','common','rare','common','uncommon','rare')

def metadata(mission):
    try:
        entry = mission_for_id(mission)
    except (KeyError, ValueError) as exc:
        raise GrowthError('growth_mission_unsupported', '등록된 본편 임무가 아닙니다.') from exc
    if not entry:
        raise GrowthError('growth_mission_unsupported', '등록된 본편 임무가 아닙니다.')
    return entry

def campaign_key(mission):
    return str(metadata(mission)['campaign_id'])

def campaign_missions(mission):
    key = campaign_key(mission)
    return [item['mission_id'] for item in load_missions() if str(item['campaign_id']) == key]

def curse_tier(mission):
    return CURSE_TIERS[min(10, metadata(mission)['ordinal']) - 1]

def rarity_weights(mission):
    ordinal = metadata(mission)['ordinal']
    values = (40,30,20,8,2) if ordinal <= 3 else (30,30,25,11,4) if ordinal <= 6 else (20,25,30,18,7)
    return dict(zip(('common','uncommon','rare','epic','legendary'), values))

def next_missions(mission):
    entry = metadata(mission)
    if entry['final']:
        return []
    return [identity for identity in entry['next_mission_ids']
            if str(metadata(identity)['campaign_id']) == str(entry['campaign_id'])]

def item_eligible(item, mission, kind):
    entry = metadata(mission)
    if not item['implemented'] or mission not in item['missions']:
        return False
    if kind == 'talent' and item['race'] not in ('shared', entry['race']):
        return False
    requirements = item.get('requirements', {})
    if entry.get('no_production') and requirements.get('production'):
        return False
    if requirements.get('squad_only') and not entry.get('no_production'):
        return False
    if entry['ordinal'] < requirements.get('minimum_ordinal', 1):
        return False
    if requirements.get('air_access') and not entry.get('air_access', True):
        return False
    if requirements.get('alternate_entry') and not entry.get('alternate_entry', False):
        return False
    return True


def prefer_active_targets(items, mission):
    """On squad missions, show available troops first without erasing ownership.

    Production-only effects are already excluded by item_eligible. If fewer
    than four current-troop effects remain, unowned campaign troop effects may
    fill the other slots; the usable candidates still receive priority.
    """
    entry=metadata(mission)
    if not entry.get('no_production'):
        return items
    available=set(entry.get('available_unit_ids',entry.get('starting_unit_ids',[])))
    relevant=[item for item in items if set(item.get('target_units',[])) & available]
    return relevant or items
