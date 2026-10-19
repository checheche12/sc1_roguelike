"""Stable v2 rank slots and the QA10 combat cap; never rewrite old ranks."""
MAX_RANK=4
MANUAL_ORDINALS=(8,9,11,12,29,30,31,70,71,72,111,112)
HEALTH_ORDINALS=(26,27,28,67,68,69,108,109,110)
RANK_SLOTS={ordinal:slot for slot,ordinal in enumerate(MANUAL_ORDINALS+HEALTH_ORDINALS)}

def effective(item,count=1):
    return min(count,item.get('max_rank',0xffffffff)) if item.get('repeatable') else 1

def unit_manual_progress(item,owned,ranks,catalog):
    """Old broad ranks and parent/ammo aliases count toward the same cap."""
    spec=item.get('effect',{}).get('unit_growth')
    if not spec or spec['kind'] not in ('health','attack'):return None
    family=item.get('bundle_family');kind=spec['kind']
    own=set(owned);new=old=0
    aliases=set(item['target_units'])
    if kind=='attack':
        if family==72:aliases.update((72,73,82))
        if family==81:aliases.update((81,83,85))
    for other in catalog['talents']:
        if other['id'] not in own:continue
        value=min(4,ranks.get(other['id'],1));effect=other.get('effect',{})
        unit=effect.get('unit_growth')
        if unit and unit['kind']==kind and (other.get('bundle_family')==family if kind=='attack' else bool(aliases&set(other['target_units']))):new=max(new,value)
        elif other.get('rework_revision')==5 and other.get('effect_ordinal') in (HEALTH_ORDINALS if kind=='health' else MANUAL_ORDINALS[4:]):
            if aliases&set(other.get('target_units',())):old=max(old,value)
    return old,new

def exhausted(item,owned,ranks,catalog=None):
    if catalog is not None:
        progress=unit_manual_progress(item,owned,ranks,catalog)
        if progress is not None and sum(progress)>=MAX_RANK:return True
    return (item['id'] in owned and (not item.get('repeatable') or
        ranks.get(item['id'],1)>=item.get('max_rank',0xffffffff)))
