"""Additive revision-five offer policy and durable integer manual ranks."""
from __future__ import annotations
import copy
import json
from . import progression, talent_campaign_policy as policy, rank_policy
from .runtime_catalog import GrowthError, load_catalog, validate_catalog, encode_growth
from .curse_balance import REAR_ID, RESERVE_ID

SKIPPED_CURSE='__no_future_added_waves__'
SKIPPED_FINAL='__campaign_clear_no_final_reward__'
RETIRED_TALENTS=frozenset(('bbf067dc-0ced-5875-a519-2c0443580c8d',))


def retired(item):
    return item['id'] in RETIRED_TALENTS or item['id'] in (REAR_ID,RESERVE_ID) or bool(item.get('effect',{}).get('retired'))


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
            if new['effect']['qa_revision']<=old.get('effect',{}).get('qa_revision',0):continue
            # Correct future display/mechanics metadata only. Issued offers,
            # frozen input text, indices, ranks and completed checkpoints stay.
            old.update(description=new['description'],effect=copy.deepcopy(new['effect']))
            for field in ('rarity','balance_revision','pre_balance_description','pre_balance_effect','repeatable','rank_slot','max_rank','max_stacks','choice_max_stacks'):
                if field in new:old[field]=copy.deepcopy(new[field])
            changed=True
    if changed:
        for field in ('balance_revision','talent_power_quarters','economy_talents_scaled'):
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
                    for field in ('rarity','balance_revision','pre_balance_description','pre_balance_effect','repeatable','rank_slot','max_rank','max_stacks','choice_max_stacks'):
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
        if retired(item) or (identity in owned and not item.get('repeatable')):
            raise GrowthError('duplicate_talent','이미 보유했거나 삭제된 재능입니다.')
    for identity in identities:acquire(conn,mission,catalog,owned,identity)


def acquire(conn,mission,catalog,owned,identity):
    item=next(x for x in catalog['talents'] if x['id']==identity)
    if retired(item):raise GrowthError('retired_talent','삭제된 재능은 선택할 수 없습니다.')
    if identity in owned and not item.get('repeatable'):
        raise GrowthError('duplicate_talent','이미 보유한 재능입니다.')
    if item.get('repeatable'):
        values=ranks(conn,mission)
        if rank_policy.exhausted(item,owned,values):
            raise GrowthError('talent_rank_limit','이 재능은 최대 4회까지 선택할 수 있습니다.')
        values[identity]=values.get(identity,1 if identity in owned else 0)+1
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
    return {item['id'] for row in rows for item in json.loads(row[0])
            if item.get('repeatable') and item.get('rarity')=='common'
            and item.get('category') in ('combat','military')}


def candidates(catalog,mission,phase,owned,rng,*,recent_manuals=(),rank_counts=None):
    from .legendary_bundles import unit_legendary,compatible,pair_options
    reward=policy.reward_policy(mission,phase)
    available=[]
    by_id={}
    entry=progression.metadata(mission)
    def usable_on(item,identity):
        metadata=progression.metadata(identity)
        if item.get('category')=='economy':
            return progression.item_eligible(item,identity,'talent') and not metadata.get('no_production')
        targets=set(item.get('target_units',()))
        available=set(metadata.get('available_unit_ids',metadata.get('starting_unit_ids',())))
        return progression.item_eligible(item,identity,'talent') and (not targets or bool(targets&available))
    rank_counts=rank_counts or {}
    for item in catalog['talents']:
        if retired(item):continue
        if rank_policy.exhausted(item,owned,rank_counts):continue
        if item.get('rework_revision')!=5 or not progression.item_eligible(item,mission,'talent'):continue
        # Every legendary choice must be usable on this mission. Native coverage can
        # provide exact mission eligibility for technologies/target availability.
        usable=usable_on(item,mission)
        available.append(policy.Candidate(item['id'],item['rarity'],item['category'],usable,item.get('repeatable',False)))
        by_id[item['id']]=item
    midpoint=policy.legendary_ordinal(mission)
    pending=midpoint is not None and entry['ordinal']<midpoint
    if pending:
        midpoint_mission=next(m for m in progression.campaign_missions(mission) if progression.metadata(m)['ordinal']==midpoint)
        potential=[item for item in catalog['talents'] if item.get('rework_revision')==5
                   and item['rarity']=='legendary' and item['id'] not in owned
                   and progression.item_eligible(item,midpoint_mission,'talent')]
        reserve=set(sorted(item['id'] for item in potential if usable_on(item,midpoint_mission))[-4:])
        # Keep companions for the guaranteed anchors too. A squad mission may
        # only supply one caster family; its second unit can help later missions.
        for item in potential:
            if item['id'] not in reserve or not unit_legendary(item):continue
            partners=[other for other in potential if compatible(item,other)]
            if partners and not any(other['id'] in reserve for other in partners):
                reserve.add(sorted(other['id'] for other in partners)[0])
        if reserve:available=[x for x in available if x.id not in reserve]
    usable_legends=[by_id[x.id] for x in available if x.rarity=='legendary']
    available=[x for x in available if not unit_legendary(by_id[x.id])
               or any(compatible(by_id[x.id],other) for other in usable_legends)]
    try:draw=policy.draw_candidates(reward,available,owned,rng,recent_manuals=recent_manuals,exhausted_fallback=True)
    except ValueError as exc:raise GrowthError('choice_pool_unavailable',str(exc)) from exc
    if not draw:raise GrowthError('choice_pool_unavailable','현재 단계에 사용 가능한 개편 재능이 없습니다.')
    return pair_options([by_id[x.id] for x in draw],usable_legends,rng)
