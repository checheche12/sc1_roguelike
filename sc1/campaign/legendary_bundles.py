"""Random two-unit legendary offers; the issued JSON is the durable pairing."""
from __future__ import annotations

import copy
from .runtime_catalog import GrowthError
from .talent_balance import UNIT_LEGENDARIES


def unit_legendary(item):
    return item.get('rework_revision') == 5 and item.get('effect_ordinal') in UNIT_LEGENDARIES


def compatible(left, right):
    # Hero variants and carried ammunition use their caster/parent's coverage.
    return (unit_legendary(left) and unit_legendary(right)
            and left['race'] == right['race']
            and not set(left['target_units']) & set(right['target_units']))


def pair_options(draw, eligible, rng):
    result = []
    used_pairs = set()
    for item in draw:
        option = copy.deepcopy(item)
        if unit_legendary(item):
            partners = [other for other in eligible if compatible(item, other)
                        and frozenset((item['id'], other['id'])) not in used_pairs]
            if not partners:
                continue
            partner = partners[rng.randrange(len(partners))]
            used_pairs.add(frozenset((item['id'], partner['id'])))
            option['bundled_talent_ids'] = [item['id'], partner['id']]
            option['name'] = item['name'] + ' + ' + partner['name']
            option['target'] = item['target'] + ' / ' + partner['target']
            option['target_units'] = sorted(set(item['target_units'] + partner['target_units']))
            option['description'] = (item['name'] + ': ' + item['description']
                                     + '\n' + partner['name'] + ': ' + partner['description'])
        result.append(option)
    return result


def member_ids(candidate, catalog):
    identities = candidate.get('bundled_talent_ids')
    if identities is None:
        return (candidate['id'],)  # Previously issued single offers stay exact.
    if (not isinstance(identities, list) or len(identities) != 2
            or any(not isinstance(x, str) for x in identities)
            or identities[0] != candidate['id'] or len(set(identities)) != 2):
        raise GrowthError('invalid_growth', '저장된 전설 묶음이 잘못되었습니다.')
    by_id = {item['id']: item for item in catalog['talents']}
    left, right = (by_id.get(identity) for identity in identities)
    if left is None or right is None or not compatible(left, right):
        raise GrowthError('invalid_growth', '전설 묶음의 유닛이 잘못되었습니다.')
    return tuple(identities)


def generate_header(catalog, root):
    from pathlib import Path
    rows=[]
    for item in catalog['talents']:
        if unit_legendary(item):
            rows.append('{%d,%d,%d}' % (item['bit_index']+1,min(item['target_units']),
                                       {'terran':1,'zerg':2,'protoss':3}[item['race']]))
    target=Path(root)/'sc1/native_campaign/plugin/include/legendary_bundles.generated.h'
    target.write_text('#pragma once\nnamespace legendary_bundles {\n'
        'struct Entry {unsigned index,family,race;};\ninline constexpr Entry entries[]={'+','.join(rows)+'};\n'
        'inline constexpr bool compatible(unsigned a,unsigned b) noexcept {\n'
        ' for(auto left:entries)if(left.index==a)for(auto right:entries)if(right.index==b)\n'
        '  return left.race==right.race && left.family!=right.family;return false; }\n}\n',encoding='utf8')
    return target


def selected_members(offer, catalog):
    import json
    candidates = json.loads(offer['candidates_json'])
    candidate = next((item for item in candidates if item['id'] == offer['selected_id']), None)
    if candidate is None:
        raise GrowthError('invalid_growth', '선택 이력에 전설 묶음이 없습니다.')
    return member_ids(candidate, catalog)
