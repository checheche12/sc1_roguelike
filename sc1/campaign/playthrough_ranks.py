"""Additive NG+ rank encoding; historical 65-word snapshots stay byte-exact.

The formerly unused bit511 selects a compact layout for rank words0..27.
Repeatable ranks use eight bits, unit traits one bit. Wide curse words28..31
and every historical ownership bit0..436 keep their original positions.
"""
import copy
import re
from functools import lru_cache

MAX_RANK = 255
MARKER = 1 << 31


@lru_cache(maxsize=1)
def fields():
    from .rank_policy import RANK_SLOTS
    from .unit_growth import specifications
    rows = [(ordinal, 8) for ordinal, slot in sorted(RANK_SLOTS.items(), key=lambda pair: pair[1])]
    rows += [(s['ordinal'], 8 if s['kind'] in ('health', 'attack', 'tower') else 1) for s in specifications()]
    offset = 0
    result = {}
    for ordinal, width in rows:
        # Never straddle uint32 words.
        if offset % 32 + width > 32:
            offset += 32 - offset % 32
        result[ordinal] = dict(word=33 + offset // 32, shift=offset % 32, width=width)
        offset += width
    assert offset <= 28 * 32
    return result


def project(catalog, number, rank_scaling=True):
    if number <= 1 or catalog.get('catalog_version') != 2:
        return catalog
    result = copy.deepcopy(catalog)
    result['playthrough_number'] = number
    result['rank_scaling'] = rank_scaling
    for item in result['talents']:
        if item.get('repeatable') and 'max_rank' in item:
            base = item.get('base_max_rank', item['max_rank'])
            item['base_max_rank'] = base
            item['max_rank'] = min(MAX_RANK, base + number - 1) if rank_scaling else base
            item['description'] = describe(item['description'], item['max_rank'])
    return result


def for_mission(conn, mission, catalog):
    from .playthrough import current
    cycle=current(conn,mission)
    return project(catalog, cycle['number'], cycle['rank_scaling'])


def describe(text, maximum):
    return re.sub(r'최대\s*\d+\s*(회|중첩)', lambda m: f'최대 {maximum}{m[1]}', text)


def encode(words, catalog, talents, ranks):
    # Build only the NG+ part after normal validation. Legacy packed fields are
    # not written first: ranks over7 must never spill into adjacent ownership.
    words[14] &= (1 << 21) - 1
    words[15] = 0
    words[16] = MARKER
    words[33:61] = [0] * 28
    # Store the bonus in previously packed bits437..444, for native validation.
    bonus = min(253, catalog['playthrough_number'] - 1)
    words[14] |= bonus << 21
    for item in catalog['talents']:
        if item['id'] not in talents:
            continue
        field = fields().get(item.get('effect_ordinal')) if item.get('rework_revision') == 5 else None
        if field is None:
            continue
        count = min(ranks.get(item['id'], 1), item['max_rank']) if item.get('repeatable') else 1
        words[field['word']] |= count << field['shift']
    return words


def generate_header(root):
    from .unit_growth import specifications
    from .rank_policy import RANK_SLOTS
    count = max(fields()) + 1
    specs = {s['ordinal']: s for s in specifications()}
    rows = []
    masks = [0] * 28
    for ordinal in range(count):
        f = fields().get(ordinal)
        if f:
            slot = f['word'] - 33
            masks[slot] |= ((1 << f['width']) - 1) << f['shift']
            base = 4 if ordinal in RANK_SLOTS else 2 if specs[ordinal]['kind'] == 'tower' else 4 if f['width'] == 8 else 1
            rows.append(f"{{{slot},{f['shift']},{f['width']},{base}}}")
        else:
            rows.append('{0,0,0,0}')
    text = '''#pragma once
#include <algorithm>
#include <cstdint>
namespace playthrough_ranks {
struct Field {unsigned slot,shift,width,base;};
inline constexpr Field fields[]={FIELDS};
inline constexpr unsigned masks[]={MASKS};
template<class S> inline bool enabled(const S& s) noexcept {return (s.talent_bits[15]&0x80000000u)!=0;}
template<class S> inline unsigned bonus(const S& s) noexcept {return enabled(s)?(s.talent_bits[13]>>21)&255u:0;}
template<class S> inline unsigned rank(const S& s,unsigned ordinal) noexcept {
 if(ordinal>=sizeof(fields)/sizeof(fields[0]))return 0;auto f=fields[ordinal];
 if(f.width)return (s.talent_ranks[f.slot]>>f.shift)&((1u<<f.width)-1u);
 const auto bit=238+ordinal;return (s.talent_bits[bit/32]>>(bit%32))&1u;
}
template<class S> inline bool valid(const S& s) noexcept {
 if(!enabled(s)||bonus(s)==0||bonus(s)>253)return false;
 if((s.talent_bits[13]&0xe0000000u)||s.talent_bits[14]||s.talent_bits[15]!=0x80000000u)return false;
 for(unsigned i=0;i<28;++i)if(s.talent_ranks[i]&~masks[i])return false;
 for(unsigned i=0;i<sizeof(fields)/sizeof(fields[0]);++i){auto f=fields[i];if(!f.width)continue;
  auto n=rank(s,i);if(n>(f.width==1?1u:std::min(255u,f.base+bonus(s))))return false;
  if(i<199){auto bit=238+i;bool owned=(s.talent_bits[bit/32]>>(bit%32))&1u;if(owned!=(n!=0))return false;}
 }
 return true;
}
}
'''.replace('FIELDS', ','.join(rows)).replace('MASKS', ','.join(str(m)+'u' for m in masks))
    target = root / 'sc1/native_campaign/plugin/include/playthrough_ranks.generated.h'
    target.write_text(text, encoding='utf8')
    return target
