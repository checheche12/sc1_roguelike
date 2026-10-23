"""Additive revision-five offer policy and durable integer manual ranks."""
from __future__ import annotations
import copy
import json
from . import progression, talent_campaign_policy as policy, rank_policy
from .runtime_catalog import GrowthError, load_catalog, validate_catalog, encode_growth
from .curse_balance import REAR_ID, RESERVE_ID

SKIPPED_CURSE='__no_future_added_waves__'
SKIPPED_FINAL='__campaign_clear_no_final_reward__'
RETIRED_TALENTS=frozenset(('bbf067dc-0ced-5875-a519-2c0443580c8d','9653d275-b027-51c6-bb5d-920e2bab74c4','0092e1dd-7b0d-5974-9145-b2713cd19dee','19d1a884-1eea-5c77-906f-8941cde82c77'))


def retired(item):
    return item['id'] in RETIRED_TALENTS or item['id'] in (REAR_ID,RESERVE_ID) or bool(item.get('effect',{}).get('retired'))


def unit_offer_removed(item):
    effect=item.get('effect',{})
    return effect.get('unit_manual_removed',False) or effect.get('unit_trait_removed',False)

def option_has_retired(item,catalog):
    removed=lambda x:retired(x) or unit_offer_removed(x)
    if removed(item):return True
    by_id={x['id']:x for kind in ('talents','curses') for x in catalog[kind]}
    return any(identity in by_id and removed(by_id[identity]) for identity in item.get('bundled_talent_ids',[item['id']]))


def enabled(catalog):
    return catalog.get('rework_revision')==5


def enable(conn, catalog_path=None):
    """Only an explicit wire-v2 LOAD enables this sidecar; old pins stay exact."""
    catalog=load_catalog(catalog_path,expected_version=2)
    conn.execute('CREATE TABLE IF NOT EXISTS growth_rework_catalog (id INTEGER PRIMARY KEY CHECK(id=1),catalog_json TEXT NOT NULL)')
    conn.execute('INSERT OR IGNORE INTO growth_rework_catalog VALUES (1,?)',
                 (json.dumps(catalog,ensure_ascii=False,sort_keys=True),))
    pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog WHERE id=1').fetchone()[0])
    changed=False
    for kind,index in (('talents','bit_index'),('curses','byte_index')):
        latest={item['id']:item for item in catalog[kind] if item.get('effect',{}).get('qa_revision')}
        for old in pinned[kind]:
            new=latest.get(old['id'])
            if new is None or new[index]!=old[index] or new.get('source_description')!=old.get('source_description'):continue
            # Display-only updates have their own revision; mechanics stay exact.
            if new.get('description_revision',0)>old.get('description_revision',0):
                old.update(description=new['description'],description_revision=new['description_revision']);changed=True
                for field in ('effect_subject','target'):
                    if field in new:old[field]=new[field]
            for flag in ('unit_manual_removed','unit_trait_removed'):
                if new.get('effect',{}).get(flag) and not old.get('effect',{}).get(flag):
                    old['effect'].update(offer_retired=True,**{flag:True});changed=True
            if new['effect']['qa_revision']<=old.get('effect',{}).get('qa_revision',0):continue
            # Correct future display/mechanics metadata only. Issued offers,
            # frozen input text, indices, ranks and completed checkpoints stay.
            old.update(description=new['description'],effect=copy.deepcopy(new['effect']))
            for field in ('category','rarity','target','target_units','balance_revision','pre_balance_description','pre_balance_effect','repeatable','rank_slot','max_rank','max_stacks','choice_max_stacks','bundle_family','bundle_families','wire_storage','name','candidate_weight_percent'):
                if field in new:old[field]=copy.deepcopy(new[field])
            changed=True
        if kind=='talents':
            known={x['id'] for x in pinned[kind]};positions={x[index] for x in pinned[kind]}
            for new in catalog[kind]:
                if new.get('expansion_revision')!=2026102038 or new['id'] in known:continue
                if new[index] in positions:raise GrowthError('catalog_incompatible','새 재능의 전송 위치가 기존 기록과 충돌합니다.')
                pinned[kind].append(copy.deepcopy(new));known.add(new['id']);positions.add(new[index]);changed=True
    if changed:
        for field in ('balance_revision','talent_power_quarters','economy_talents_scaled','legendary_expansion_revision','legendary_common_offer_probability','wave_balance_revision','wave_count_multiplier_percent','wave_roster_review','unit_growth_revision','unit_growth_summary','talent_retirement_revision','legend_focus_revision','legend_base_balance_revision','single_target_legend_ordinals','effect_description_revision'):
            if field in catalog:pinned[field]=copy.deepcopy(catalog[field])
        if 'talent_power_quarters' in catalog:pinned.pop('talent_power_halves',None)
        validate_catalog(pinned,2)
        conn.execute('UPDATE growth_rework_catalog SET catalog_json=? WHERE id=1',
                     (json.dumps(pinned,ensure_ascii=False,sort_keys=True),))
    return catalog


def overlay(conn, catalog):
    table=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='growth_rework_catalog'").fetchone()
    if not table:return catalog
    row=conn.execute('SELECT catalog_json FROM growth_rework_catalog WHERE id=1').fetchone()
    if row is None:return catalog
    extra=validate_catalog(json.loads(row[0]),2)
    result=copy.deepcopy(catalog)
    for kind,index in (('talents','bit_index'),('curses','byte_index')):
        positions={x[index]:x['id'] for x in result[kind]}
        known={x['id'] for x in result[kind]}
        for item in extra[kind]:
            if item.get('rework_revision')!=5 and item.get('balance_revision') not in (6,7,9):continue
            if item[index] in positions and positions[item[index]]!=item['id']:
                raise GrowthError('catalog_incompatible','기존 성장 위치와 개편안 위치가 충돌합니다.')
            if item['id'] not in known:result[kind].append(copy.deepcopy(item))
            elif item.get('effect',{}).get('qa_revision'):
                existing=next(x for x in result[kind] if x['id']==item['id'])
                if existing.get('source_description')==item.get('source_description'):
                    existing.update(description=item['description'],effect=copy.deepcopy(item['effect']))
                    for field in ('category','rarity','target','target_units','balance_revision','pre_balance_description','pre_balance_effect','repeatable','rank_slot','max_rank','max_stacks','choice_max_stacks','bundle_family','bundle_families','wire_storage','name','candidate_weight_percent'):
                        if field in item:existing[field]=copy.deepcopy(item[field])
    result.update(catalog_version=2,rework_revision=5,policy_revision=5)
    return validate_catalog(result,2)


def ranks(conn,mission):
    table=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='growth_manual_ranks'").fetchone()
    if not table:return {}
    return {row[0]:row[1] for row in conn.execute('SELECT talent_id,rank FROM growth_manual_ranks WHERE campaign=?',
                                                (progression.campaign_key(mission),))}


def save_ranks(conn,mission,values):
    conn.execute('''CREATE TABLE IF NOT EXISTS growth_manual_ranks (
        campaign TEXT NOT NULL,talent_id TEXT NOT NULL,rank INTEGER NOT NULL CHECK(rank BETWEEN 1 AND 4294967295),
        PRIMARY KEY(campaign,talent_id))''')
    for identity,count in values.items():
        if type(count) is not int or not 1<=count<=0xFFFFFFFF:raise GrowthError('invalid_growth','교범 중첩이 잘못되었습니다.')
        conn.execute('INSERT INTO growth_manual_ranks VALUES (?,?,?) ON CONFLICT(campaign,talent_id) DO UPDATE SET rank=excluded.rank',
                     (progression.campaign_key(mission),identity,count))


def encode(conn,mission,catalog,owned,stacks):
    values={key:value for key,value in ranks(conn,mission).items() if key in owned}
    return encode_growth(catalog,owned,stacks,values)


def acquire_option(conn,mission,catalog,owned,candidate):
    from .legendary_bundles import member_ids
    identities=member_ids(candidate,catalog)
    # Validate the entire pair before mutating either ownership or ranks.
    by_id={item['id']:item for item in catalog['talents']}
    for identity in identities:
        item=by_id[identity]
        if retired(item) or unit_offer_removed(item) or rank_policy.exhausted(item,owned,ranks(conn,mission),catalog):
            raise GrowthError('duplicate_talent','이미 보유했거나 삭제된 재능입니다.')
    for identity in identities:acquire(conn,mission,catalog,owned,identity)


def acquire(conn,mission,catalog,owned,identity):
    item=next(x for x in catalog['talents'] if x['id']==identity)
    if retired(item) or unit_offer_removed(item):raise GrowthError('retired_talent','삭제된 재능은 선택할 수 없습니다.')
    if identity in owned and not item.get('repeatable'):
        raise GrowthError('duplicate_talent','이미 보유한 재능입니다.')
    if item.get('repeatable'):
        values=ranks(conn,mission)
        if rank_policy.exhausted(item,owned,values,catalog):
            raise GrowthError('talent_rank_limit',f"이 재능은 최대 {item.get('max_rank',4)}회까지 선택할 수 있습니다.")
        progress=rank_policy.unit_manual_progress(item,owned,values,catalog)
        values[identity]=(progress[1] if progress is not None else values.get(identity,1 if identity in owned else 0))+1
        save_ranks(conn,mission,values)
    if identity not in owned:owned.append(identity)


def has_future_production(mission):
    entry=progression.metadata(mission)
    return any(not progression.metadata(m).get('no_production')
               and progression.metadata(m)['ordinal']>=entry['ordinal']
               for m in progression.campaign_missions(mission))


def curse_eligible(item,mission):
    if not item.get('implemented') or retired(item):return False
    if not progression.metadata(mission).get('no_production'):
        return progression.item_eligible(item,mission,'curse')
    ordinal=progression.metadata(mission)['ordinal']
    return any(not progression.metadata(m).get('no_production')
               and progression.metadata(m)['ordinal']>ordinal and m in item['missions']
               for m in progression.campaign_missions(mission))


def curse_tier(mission,phase=2):
    """Every mission cycles common / upper tier / common, including branch maps."""
    if type(phase) is not int or phase not in (1,2,3):
        raise ValueError('Curse phase must be1,2or3')
    if phase!=2:return 'common'
    entry=progression.metadata(mission)
    total=policy.logical_mission_count(mission);ordinal=entry['ordinal']
    if ordinal>=(total+1)//2:return 'legendary'
    if ordinal>=(total*35+99)//100:return 'epic'
    if ordinal>=(total+4)//5:return 'rare'
    return 'uncommon'


def recent_manuals(conn,mission,offer_id):
    """Read the last three displayed talent rewards in this campaign.

    Unchosen cards count too. Economic/legendary rewards age the window;
    reconnects, curses and unissued placeholders do not. Existing offer JSON
    is the durable history, so no migration or saved-choice rewrite is needed.
    """
    missions=progression.campaign_missions(mission)
    placeholders=','.join('?' for _ in missions)
    rows=conn.execute(f'''SELECT candidates_json FROM growth_offers
        WHERE kind='talent' AND mission IN ({placeholders})
          AND candidates_json IS NOT NULL AND offer_id!=?
        ORDER BY sequence DESC LIMIT ?''',
        (*missions,offer_id,policy.RECENT_MANUAL_REWARDS)).fetchall()
    return {identity for row in rows for item in json.loads(row[0]) for identity in item.get('bundled_talent_ids',[item['id']])
            if item.get('repeatable') and item.get('rarity')=='common'
            and item.get('category') in ('combat','military')}


def candidates(catalog,mission,phase,owned,rng,*,recent_manuals=(),rank_counts=None):
    from .legendary_bundles import paired_unit,can_bundle,pair_options
    reward=policy.reward_policy(mission,phase)
    available=[]
    by_id={}
    entry=progression.metadata(mission)
    opening=reward.guaranteed_legendary
    campaign_missions=progression.campaign_missions(mission) if opening else ()
    def usable_on(item,identity):
        metadata=progression.metadata(identity)
        if item.get('category')=='economy':
            return progression.item_eligible(item,identity,'talent') and not metadata.get('no_production')
        targets=set(item.get('target_units',()))
        available=set(metadata.get('available_unit_ids',metadata.get('starting_unit_ids',())))
        return progression.item_eligible(item,identity,'talent') and (not targets or bool(targets&available))
    rank_counts=rank_counts or {}
    for item in catalog['talents']:
        if retired(item) or item.get("effect",{}).get("offer_retired"):continue
        if rank_policy.exhausted(item,owned,rank_counts,catalog):continue
        if item.get('rework_revision')!=5:continue
        if opening:
            # Choose a build before its units arrive. Both bundle members must
            # be usable somewhere in this same campaign, including squad starts.
            if item['rarity']!='legendary' or item['race'] not in ('shared',entry['race']):continue
            usable=any(usable_on(item,identity) for identity in campaign_missions)
            if not usable:continue
        else:
            if not progression.item_eligible(item,mission,'talent'):continue
            usable=usable_on(item,mission)
        available.append(policy.Candidate(item['id'],item['rarity'],item['category'],usable,item.get('repeatable',False),item.get('candidate_weight_percent',100)))
        by_id[item['id']]=item
    usable_legends=[by_id[x.id] for x in available]
    available=[x for x in available if not paired_unit(by_id[x.id])
               or can_bundle(by_id[x.id],usable_legends)]
    try:
        if reward.guaranteed_legendary:
            shared=[x for x in available if x.rarity=='legendary' and by_id[x.id]['race']=='shared' and x.usable]
            faction=[x for x in available if x.rarity=='legendary' and by_id[x.id]['race']==entry['race'] and x.usable]
            draw=[]
            if shared and (not faction or rng.randrange(3)==0):draw.append(shared[rng.randrange(len(shared))])
            for _ in range(min(4-len(draw),len(faction))):draw.append(faction.pop(rng.randrange(len(faction))))
            # A depleted faction pool does not force duplicate ownership or
            # introduce extra common slots. Existing issued JSON never redraws.
            if len(draw)>1:rng.shuffle(draw)
        else:draw=policy.draw_candidates(reward,available,owned,rng,recent_manuals=recent_manuals,exhausted_fallback=True)
    except ValueError as exc:raise GrowthError('choice_pool_unavailable',str(exc)) from exc
    if not draw:raise GrowthError('choice_pool_unavailable','현재 단계에 사용 가능한 개편 재능이 없습니다.')
    return pair_options([by_id[x.id] for x in draw],usable_legends,rng)
