"""Random two-unit legendary offers; the issued JSON is the durable pairing."""
from __future__ import annotations

import copy
from .runtime_catalog import GrowthError
from .talent_balance import UNIT_LEGENDARIES
HISTORICAL_UNIT_LEGENDARIES=UNIT_LEGENDARIES|{49,54,55,56,57,58,60,90,92,95,96,97,136,137,138,139,140,141,142,51,183,184,185,186,187,188,189,190,191,192,193,194,195,196,197}


def unit_legendary(item):
    return (item.get('rework_revision') == 5 and item.get('rarity')=='legendary'
            and item.get('race') in ('terran','zerg','protoss')
            and not item.get('effect',{}).get('retired'))

def paired_unit(item):
    return unit_legendary(item) or (item.get('bundle_family') is not None
            and item.get('rarity') in ('common','uncommon','rare','epic')
            and not item.get('effect',{}).get('retired'))


def families(item):
    return frozenset(item.get('bundle_families') or
                     (item.get('bundle_family',min(item['target_units'])),))


def compatible(left, right, *, historical=False):
    # Hero variants and carried ammunition use their caster/parent's coverage.
    legacy=lambda item:item.get('rework_revision')==5 and item.get('effect_ordinal') in HISTORICAL_UNIT_LEGENDARIES
    eligible=lambda item:paired_unit(item) or (historical and legacy(item))
    return (eligible(left) and eligible(right)
            and left['race'] == right['race']
            and (left['rarity']==right['rarity'] or historical and legacy(left) and legacy(right))
            and families(left).isdisjoint(families(right))
            and not set(left['target_units']) & set(right['target_units']))


def bundle_size(item):
    spec = item.get('effect', {}).get('unit_growth', {})
    return 3 if item.get('rarity') == 'common' and spec.get('kind') in ('health', 'attack') else 2


def partners_for(item, eligible):
    """A triple needs two mutually compatible families, not just two cards."""
    partners = [other for other in eligible if compatible(item, other)]
    if bundle_size(item) == 3:
        return [(a, b) for i, a in enumerate(partners) for b in partners[i+1:] if compatible(a, b)]
    return [(a,) for a in partners]


def can_bundle(item, eligible):
    partners = [x for x in eligible if compatible(item, x)]
    if bundle_size(item)==2:return bool(partners)
    return any(compatible(a,b) for i,a in enumerate(partners) for b in partners[i+1:])


def pair_options(draw, eligible, rng):
    result = []
    used_pairs = set()
    for item in draw:
        option = copy.deepcopy(item)
        if paired_unit(item):
            partners = [others for others in partners_for(item, eligible)
                        if frozenset([item['id'], *(x['id'] for x in others)]) not in used_pairs]
            if not partners:
                continue
            members = [item, *partners[rng.randrange(len(partners))]]
            used_pairs.add(frozenset(x['id'] for x in members))
            option['bundled_talent_ids'] = [x['id'] for x in members]
            option['name'] = ' + '.join(x['name'] for x in members)
            option['target'] = ' / '.join(x['target'] for x in members)
            option['target_units'] = sorted({unit for x in members for unit in x['target_units']})
            option['description'] = '\n'.join(x['name'] + ': ' + x['description'] for x in members)
        result.append(option)
    return result


def member_ids(candidate, catalog):
    identities = candidate.get('bundled_talent_ids')
    if identities is None:
        return (candidate['id'],)  # Previously issued single offers stay exact.
    if (not isinstance(identities, list) or len(identities) not in (2, 3)
            or any(not isinstance(x, str) for x in identities)
            or identities[0] != candidate['id'] or len(set(identities)) != len(identities)):
        raise GrowthError('invalid_growth', '저장된 전설 묶음이 잘못되었습니다.')
    by_id = {item['id']: item for item in catalog['talents']}
    members = [by_id.get(identity) for identity in identities]
    if (any(x is None for x in members)
            or any(not compatible(a,b,historical=True) for i,a in enumerate(members) for b in members[i+1:])
            or len(members)==3 and any(bundle_size(x)!=3 for x in members)):
        raise GrowthError('invalid_growth', '전설 묶음의 유닛이 잘못되었습니다.')
    return tuple(identities)


def generate_header(catalog, root):
    from pathlib import Path
    rows=[]
    for item in catalog['talents']:
        if paired_unit(item) or (item.get('rework_revision')==5 and item.get('effect_ordinal') in HISTORICAL_UNIT_LEGENDARIES):
            covered=sorted(families(item))
            if len(covered)>2:raise ValueError('A bundle member covers more than two unit families')
            rows.append('{%d,%d,%d,%d,%d,%d,{%d,%d}}' % (item['bit_index']+1,item.get('bundle_family',min(item['target_units'])),
                {'terran':1,'zerg':2,'protoss':3}[item['race']],('common','uncommon','rare','epic','legendary').index(item['rarity']),int(item.get('effect_ordinal') in HISTORICAL_UNIT_LEGENDARIES),int(bundle_size(item)==3),covered[0],covered[-1]))
    target=Path(root)/'sc1/native_campaign/plugin/include/legendary_bundles.generated.h'
    target.write_text('#pragma once\nnamespace legendary_bundles {\n'
        'struct Entry {unsigned index,family,race,rarity,legacy,manual;unsigned families[2];};\ninline constexpr Entry entries[]={'+','.join(rows)+'};\n'
        'inline constexpr bool manual(unsigned a) noexcept {for(auto x:entries)if(x.index==a)return x.manual;return false;}\n'
        'inline constexpr bool overlap(Entry a,Entry b) noexcept {for(auto x:a.families)for(auto y:b.families)if(x==y)return true;return false;}\n'
        'inline constexpr bool compatible(unsigned a,unsigned b) noexcept {\n'
        ' for(auto left:entries)if(left.index==a)for(auto right:entries)if(right.index==b)\n'
        '  return left.race==right.race && !overlap(left,right) && (left.rarity==right.rarity || (left.legacy&&right.legacy));return false; }\n}\n',encoding='utf8')
    return target


def selected_members(offer, catalog):
    import json
    candidates = json.loads(offer['candidates_json'])
    candidate = next((item for item in candidates if item['id'] == offer['selected_id']), None)
    if candidate is None:
        raise GrowthError('invalid_growth', '선택 이력에 전설 묶음이 없습니다.')
    return member_ids(candidate, catalog)
