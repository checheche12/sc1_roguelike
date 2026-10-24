"""Freeze the user-edited r42 design into a separate, append-only wire-v2 catalog.

Never writes the editable board or changes the legacy catalog. A coverage receipt
is required to mark a new native mechanism as available to the offer sampler.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'analysis/runtime_rework_20261016/input_board_r42.json'
TARGET = Path(__file__).with_name('runtime_talents_v5.json')
CONTRACT = Path(__file__).with_name('runtime_v5_contract.json')
HEADER = ROOT / 'sc1/native_campaign/plugin/include/rework_catalog.generated.h'
NUCLEAR_GUIDANCE_ID = '93f1cae8-5d40-5c23-b27f-4c5939d77a5a'
NUCLEAR_GUIDANCE_DESCRIPTION = '고스트 핵의 낙하 경고가 1.5초로 줄고, 핵 생산 시간은 30초, 필요 인구수는 2가 됩니다. 적에게 주는 핵 피해가 50% 늘어납니다.'
NUCLEAR_GUIDANCE_MECHANISM = 'own Ghost-related missile order125state4 fixed36-frame warning; owner nuclear missile training720frames supply4half-units; native sigorder2 resumes launch; already elapsed warning retained; scripted unrelated nukes excluded'
NUCLEAR_GUIDANCE_QA_RECORD = 'analysis/qa_fixes_20261016/nuclear_guidance_5s/verification.json'
INFANTRY_MANUAL_ID = '2550fdb4-cace-5c0a-bc97-bfc04e0c0f33'
WORKER_RAID_ID = 'rework-rule-worker-raid'
RESERVE_ID = '9abf9771-866f-55b7-a4ba-ba28bb5e6faf'
GHOST_MARK_ID = '9653d275-b027-51c6-bb5d-920e2bab74c4'
HEAVY_ID = '2f180084-63f4-5068-97f6-cf14ba35eb58'
FLANK_ID = 'f54b8a38-c9de-5c10-91cb-83a96e0351cd'
REAR_ID = '09224f2f-b115-5c53-adb3-883bb36075cd'
RAYNOR_ID = '2cb56ab3-e19f-56a7-89fc-03ce9e6cd08d'
GROUND_ARMOR_ID = '1ec96c5e-bd7f-5b05-a4e2-1707b863f061'
AIR_ARMOR_ID = '12dda10f-da28-5df4-9a3b-5f8d1aa30d81'
COMBAT_QA_RECORD = 'analysis/qa_fixes_20261016/infantry_waves/verification.json'
QA_EFFECTS = {
    GROUND_ARMOR_ID: ('아군 지상 병력과 영웅의 방어력 +0.5. 반복해서 고를 수 있습니다.',
                      {'armor_per_rank': 0.5},
                      'ground soldier health armor+rank/2; integer DAT part plus odd Q8 half at native HP callback, after native size factor; shields/Matrix/native minimum preserved'),
    AIR_ARMOR_ID: ('아군 공중 병력과 영웅의 방어력 +0.5. 반복해서 고를 수 있습니다.',
                   {'armor_per_rank': 0.5},
                   'air soldier health armor+rank/2; integer DAT part plus odd Q8 half at native HP callback, after native size factor; shields/Matrix/native minimum preserved'),
    INFANTRY_MANUAL_ID: ('마린·파이어뱃·고스트의 공격력 +10%, 공격 간격 -3%. 반복해서 고를 수 있습니다.',
                         {'weapon_damage_percent_per_rank': 10, 'weapon_damage_stacking': 'additive'},
                         'owner infantry Q8 ordinary damage*(1+rank/10), projectile rank captured once; cooldown0.97^rank; rounded integer tooltip'),
    WORKER_RAID_ID: ('뮤탈리스크가 중첩에 따라 2·6·12·20기씩 일꾼 근처에 직접 등장합니다. 증원량 증가도 적용됩니다.',
                    {'units_formula': 'n*(n+1)', 'units_sequence': [2, 6, 12, 20], 'direct_mining_line_spawn': True},
                    'worker-raid count=n*(n+1), direct mining-line spawn explicitly allowed by user;20sec warning4sec appearance; live hostile owner, reinforcement/shared supply limits; worker-target attack orders'),
    RESERVE_ID: ('두 번째 공세부터 15초 뒤 혼합 예비대가 옵니다. 규모는 중첩당 본 공세의 50%입니다.',
                {'main_wave_budget_percent_per_stack': 50, 'departure_delay_seconds': 15, 'mixed_composition': True},
                'mixed race/time-appropriate reserve; half captured main-wave budget per stack; departure15sec later from second main wave'),
    GHOST_MARK_ID: ('고스트에게 맞은 적은 5초간 아군 일반 공격에 방어력이 0이 됩니다. 방어 업그레이드와 보호막 방어도 무시합니다.',
                    {'armor_mark_frames': 120, 'marked_armor': 0, 'include_armor_upgrades': True, 'include_shield_armor': True},
                    'Ghost ordinary-hit mark120frames; allied ordinary native damage scopes zero health base/upgrade and shield armor; refresh without stacking'),
    HEAVY_ID: ('공세마다 골리앗·히드라·드라군 중 중화기 병력 4기 추가. 중첩마다 4기씩 늘고 증원량 증가도 적용됩니다.',
               {'units_per_stack': 4, 'first_normal_wave_eligible': True},
               'race-matched heavy4per stack; reinforcement scaling includes first member; available on first normal wave'),
    FLANK_ID: ('두 공세마다 벌처·저글링·질럿 중 기동대 8기가 다른 길로 옵니다. 중첩마다 8기씩 늘고 증원량 증가도 적용됩니다.',
               {'units_per_stack': 8, 'first_normal_wave_eligible': True},
               'race-matched flank8per stack via alternate safe origin; reinforcement scaling; first normal wave then2-wave cadence'),
    REAR_ID: ('두 번째 공세부터 매 공세에 보병 편성이 추가될 수 있습니다. 기본 10기, 20분부터 15기이며 중첩과 증원량 증가가 적용됩니다.',
              {'units_per_stack': 12, 'late_units_per_stack': 18, 'late_seconds': 1200, 'base_delivered_units': 10, 'late_delivered_units': 15, 'wave_cadence': 1, 'shared_special_roster_limit': 2},
              'race-matched rear12per stack then18at1200sec departure; global85percent gives10/15 at one stack; reinforcement scaling; eligible each wave from second; shared2-special selection retained'),
    RAYNOR_ID: ('두 공세마다 적 레이너(마린) 2기·마린 20기·메딕 4기가 옵니다.',
                {'roster': [{'unit': 20, 'count': 2, 'hero': True}, {'unit': 0, 'count': 20}, {'unit': 34, 'count': 4}]},
                'rare Raynor roster doubled2heroes20marines4medics; hero count fixed; ordinary escort reinforcement scaling retained'),
}


def build(coverage=None):
    from .missions import load_missions
    legacy = json.loads(Path(__file__).with_name('runtime_talents_all.json').read_text(encoding='utf8'))
    board = json.loads(SOURCE.read_text(encoding='utf8'))
    talents = [x for x in board['items'] if x['kind'] == 'talent' and x['category'] != 'rules']
    curses = [x for x in board['items'] if x['kind'] == 'curse']
    assert (len(legacy['talents']), len(legacy['curses']),len(talents),len(curses)) == (238,15,162,35)
    receipt = copy.deepcopy(coverage or {})
    nuclear_coverage = receipt.get('items', {}).get(NUCLEAR_GUIDANCE_ID)
    if nuclear_coverage is not None:
        nuclear_coverage.update(mechanism=NUCLEAR_GUIDANCE_MECHANISM, actual_engine_verified=False)
        records = nuclear_coverage.setdefault('coverage_receipts', [])
        if NUCLEAR_GUIDANCE_QA_RECORD not in records:
            records.append(NUCLEAR_GUIDANCE_QA_RECORD)
    for identity, (_, _, mechanism) in QA_EFFECTS.items():
        metadata = receipt.get('items', {}).get(identity)
        if metadata is not None:
            metadata.update(mechanism=mechanism, actual_engine_verified=False)
            records = metadata.setdefault('coverage_receipts', [])
            if COMBAT_QA_RECORD not in records:
                records.append(COMBAT_QA_RECORD)
            if identity == REAR_ID:
                record = 'analysis/mission_balance_qa14_20261017/verification.json'
                if record not in records:records.append(record)
    supported = set(receipt.get('implemented_ids', ()))
    display_path=ROOT/'analysis/runtime_rework_20261016/display_copy.json'
    display=json.loads(display_path.read_text(encoding='utf8')) if display_path.is_file() else {}
    display=display.get('items',display)
    rows = load_missions()
    catalog = copy.deepcopy(legacy)
    catalog.update(catalog_version=2, policy_revision=5, design_revision=board['revision'],
                   design_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                   wire_version=2, rework_revision=5, native_coverage=receipt)
    from .rank_policy import MAX_RANK, RANK_SLOTS
    rank_slot = len(RANK_SLOTS)
    contract = dict(schema_version=1, policy_revision=5, wire_version=2,
                    source=str(SOURCE.relative_to(ROOT)).replace('\\','/'), source_sha256=catalog['design_sha256'],
                    legacy_talents=238,legacy_curses=15, new_talents=[],new_curses=[],
                    deleted_standalone_torrasque_retained=False,
                    snapshot_layout=dict(version=0,talent_bits=[1,16],curse_bytes=[17,32],talent_ranks=[33,64],words=65))
    for kind, items, start, index_key in [('talent',talents,238,'bit_index'),('curse',curses,15,'byte_index')]:
        for ordinal, raw in enumerate(items):
            item = copy.deepcopy(raw)
            repeatable = kind == 'talent' and ordinal in RANK_SLOTS
            item.update({index_key:start+ordinal,'implemented':item['id'] in supported,
                         'native_status':'implemented' if item['id'] in supported else 'pending_mechanism',
                         'source_description':item['description'],'rework_revision':5,'effect_ordinal':ordinal,
                         'repeatable':repeatable,'effect':{'type':'rework_v5','ordinal':ordinal,'source_id':item['id']},
                         'target_units':[],'requirements':{'production':item['category']=='economy'}})
            # The native adapter's concrete target coverage is authoritative.
            metadata = receipt.get('items',{}).get(item['id'],{})
            item['target_units'] = metadata.get('target_units',[])
            allowed = metadata.get('missions')
            item['missions'] = [row['mission_id'] for row in rows
                                if (kind == 'curse' or item['race'] in ('shared',row['race']))
                                and (allowed is None or row['mission_id'] in allowed)]
            if repeatable:
                item['rank_slot']=RANK_SLOTS[ordinal]
                item['max_rank']=MAX_RANK
            if kind=='curse':
                # Explicit stacks survive; finite roster cards can recur across
                # the campaign without exhausting the three-candidate tier.
                item['max_stacks']=2 if item['id']=='38dd4adc-e24d-5434-b938-4a98ae51d38d' else 3 if '최대 3' in item['description'] or item['id'] in ('1e777144-aefd-5715-9379-986f6aa5a3ee','82ba819d-e68c-570a-ac0d-d03031a5a80c','ea65cda4-34dd-5334-99e8-4085fd00133e','f77ecb43-931b-583f-b975-38b924080322','f1d772f8-e1b9-57c9-966c-7e3cc5657ff7') else 255
                item['requirements']={'added_wave':True}
            # Published display copy is separate from the frozen mechanic text.
            # Stack caps and all native contracts above use original source.
            override=display.get(item['id'],{}) if isinstance(display,dict) else {}
            for field in ('name','target','description'):
                if isinstance(override.get(field),str) and override[field].strip():item[field]=override[field]
            # Latest QA corrections override display drafts while retaining the
            # frozen user text in source_description and the original input.
            if item['id'] == NUCLEAR_GUIDANCE_ID:
                item['description'] = NUCLEAR_GUIDANCE_DESCRIPTION
                item['effect'].update(nuclear_warning_frames=36,nuclear_build_time_frames=720,nuclear_supply_required=2)
                item['effect']['qa_revision'] = 20261016
            if item['id'] in QA_EFFECTS:
                description, effect, _ = QA_EFFECTS[item['id']]
                item['description'] = description
                item['effect'].update(effect)
                item['effect']['qa_revision'] = 20261016
            catalog['talents' if kind=='talent' else 'curses'].append(item)
            contract['new_talents' if kind=='talent' else 'new_curses'].append(copy.deepcopy(item))
    from .talent_balance import decorate, generate_header
    decorate(catalog)
    from .curse_balance import decorate as decorate_curses
    decorate_curses(catalog)
    from .legendary_balance import decorate as decorate_legends
    decorate_legends(catalog)
    from .legendary_expansion import decorate as expand_legends, generate_header as generate_expansion
    expand_legends(catalog)
    generate_expansion(catalog, ROOT)
    from .unit_growth import decorate as expand_units,generate_header as generate_units
    expand_units(catalog);generate_units(catalog,ROOT)
    from .talent_retirement import decorate as retire_talents
    from .legend_focus import decorate as focus_legends,generate_header as generate_focus
    focus_legends(catalog)
    from .legend_base_balance import decorate as balance_legend_bases, generate_header as generate_legend_bases
    balance_legend_bases(catalog)
    # Retire after balance decorators so historical effects cannot re-enable
    # removed legends or overwrite their migration revision and description.
    retire_talents(catalog)
    generate_legend_bases(catalog,ROOT);generate_focus(catalog,ROOT)
    from .wave_balance import decorate as decorate_wave_balance
    decorate_wave_balance(catalog, ROOT)
    from .effect_copy import decorate as clean_effect_copy
    clean_effect_copy(catalog)
    from .air_legend_balance import decorate as air_legend_balance
    air_legend_balance(catalog);generate_expansion(catalog,ROOT)
    from .creep_march import decorate as extend_creep_march
    extend_creep_march(catalog)
    contract['new_curses']=copy.deepcopy(catalog['curses'][15:])
    contract['balance_revision']=9
    contract['new_talents']=copy.deepcopy(catalog['talents'][238:])
    generate_header(catalog, ROOT)
    from .legendary_bundles import generate_header as generate_bundles
    generate_bundles(catalog, ROOT)
    contract['rank_slots_used']=rank_slot
    for path,value in ((TARGET,catalog),(CONTRACT,contract)):
        path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    generate_rank_header(catalog)
    return catalog


def generate_rank_header(catalog,root=ROOT):
    talents=catalog['talents'][238:];curses=catalog['curses'][15:]
    rank_slots=[x.get('rank_slot',-1) for x in talents]
    lines=['#pragma once','#include <cstdint>','namespace rework_catalog {',
           f'inline constexpr std::uint32_t kTalentBase=238, kTalentCount={len(talents)}, kCurseBase=15, kCurseCount=35;',
           f'inline constexpr std::uint32_t kRankCount=28;',
           'inline constexpr int kRankSlots[kTalentCount]={'+','.join(map(str,rank_slots))+'};',
           'template<class Snapshot> inline std::uint32_t rank(const Snapshot& s,std::uint32_t ordinal) noexcept {',
           ' if(ordinal>=kTalentCount)return 0; const auto slot=kRankSlots[ordinal];',
           ' if(ordinal>=199u)return packed_rank(s,ordinal);',
           ' const auto bit=kTalentBase+ordinal; const auto owned=(s.talent_bits[bit/32]>>(bit%32))&1u;',
           ' if(slot>=0){const auto n=s.talent_ranks[slot];return n ? (n>4u?4u:n):owned;} return owned; }',
           'inline constexpr const char* kTalentSourceIds[kTalentCount]={'+','.join(json.dumps(x['id']) for x in talents)+'};',
           'inline constexpr const char* kCurseSourceIds[35]={'+','.join(json.dumps(x['id']) for x in curses)+'};','}']
    from .unit_growth import specifications
    packed=['struct Field {unsigned ordinal,word,shift,width;};','inline constexpr Field kPackedFields[]={']
    masks=[0]*65;owned=[0]*16
    for bit in range(437):owned[bit//32]|=1<<(bit%32)
    for spec in specifications():
        f=spec['storage'];packed.append('{'+','.join(map(str,(spec['ordinal'],f['word'],f['shift'],f['width'])))+'},')
        masks[f['word']]|=((1<<f['width'])-1)<<f['shift']
    packed+=['};','inline constexpr unsigned kOwnershipMasks[16]={'+','.join(str(x)+'u' for x in owned)+'};',
      'template<class S> inline unsigned word(const S& s,unsigned w) noexcept {return w<=16?s.talent_bits[w-1]:s.talent_ranks[w-33];}',
      'template<class S> inline unsigned packed_rank(const S& s,unsigned ordinal) noexcept {for(auto f:kPackedFields)if(f.ordinal==ordinal)return (word(s,f.word)>>f.shift)&((1u<<f.width)-1u);return 0;}',
      'template<class S> inline bool valid_packed(const S& s) noexcept {for(auto f:kPackedFields)if(f.width==3&&packed_rank(s,f.ordinal)>4)return false;']
    packed.append(' if(packed_rank(s,322u)>2u)return false;')
    for w in range(54,61):packed.append(f' if(s.talent_ranks[{w-33}]&~{masks[w]}u)return false;')
    packed+=[' return true;}']
    at=next(i for i,line in enumerate(lines) if line.startswith('template<class Snapshot>'))
    lines[at:at]=packed
    target=root/'sc1/native_campaign/plugin/include/rework_catalog.generated.h'
    target.write_text('\n'.join(lines)+'\n',encoding='utf8')
    return target

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--coverage',type=Path)
    args=parser.parse_args()
    result=build(json.loads(args.coverage.read_text(encoding='utf8')) if args.coverage else None)
    print(json.dumps({'talents':len(result['talents']),'curses':len(result['curses']),'catalog':str(TARGET)}))
