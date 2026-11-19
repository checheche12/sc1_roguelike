"""Explicit per-campaign new-game-plus transitions, within the caller's transaction."""
import json

from . import growth, progression
from .missions import load_missions
from .runtime_catalog import GrowthError


def table_exists(conn, name):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def current(conn, mission):
    if table_exists(conn, 'campaign_playthroughs'):
        row = conn.execute('SELECT * FROM campaign_playthroughs WHERE campaign=?',
                           (progression.campaign_key(mission),)).fetchone()
        if row:
            result=dict(row)
            result['carry_curses']=bool(result.get('carry_curses',False))
            result['rank_scaling']=bool(result.get('rank_scaling',True))
            return result
    return dict(campaign=progression.campaign_key(mission), number=1, curses_per_mission=None,
                carry_curses=False,rank_scaling=True)


def campaign_status(conn, campaign_id):
    rows = [m for m in load_missions() if m['campaign_id'] == campaign_id]
    if type(campaign_id) is not int or not rows:
        raise GrowthError('growth_campaign_unsupported', '등록된 캠페인이 아닙니다.')
    mask = conn.execute('SELECT completed_mask FROM campaign WHERE id=1').fetchone()[0]
    result = current(conn, rows[0]['mission_id'])
    result['can_advance'] = any(m['final'] and mask & (1 << m['completion_bit']) for m in rows)
    result['first_mission'] = min(rows, key=lambda m: m['ordinal'])['mission_id']
    result['rank_bonus'] = min(253, result['number'] - 1) if result['rank_scaling'] else 0
    return result


def start_next(conn, campaign_id, expected_number, curses_per_mission, *, carry_curses=False, rank_scaling=True):
    from .checkpoint_growth import curse_stages
    curse_stages(curses_per_mission)
    if type(carry_curses) is not bool or type(rank_scaling) is not bool:
        raise GrowthError('invalid_playthrough_option','저주 계승과 회차 보정 설정은 켜기 또는 끄기로 지정해 주세요.')
    before = campaign_status(conn, campaign_id)
    if type(expected_number) is not int or expected_number != before['number']:
        raise GrowthError('stale_playthrough', '회차가 변경되었습니다. 현재 기록을 다시 확인해 주세요.')
    if not before['can_advance']:
        raise GrowthError('campaign_not_complete', '이 캠페인의 마지막 임무를 완료한 뒤 다음 회차를 시작할 수 있습니다.')
    mission = before['first_mission']
    missions = progression.campaign_missions(mission)
    slots = ','.join('?' for _ in missions)
    nonces = [r[0] for r in conn.execute(f'SELECT nonce FROM attempts WHERE mission IN ({slots})', missions)]
    # Archive exact rows before removing the active mission keys. All other
    # campaigns, legacy catalogs and ownership/rank IDs remain untouched.
    archive = {'playthrough': before, 'tables': {}}
    predicates = []
    for table in ('growth_checkpoint_offers', 'growth_checkpoint_snapshots', 'growth_checkpoint_catalogs',
                  'growth_checkpoint_rank_baselines', 'growth_checkpoint_runs', 'growth_phase_offers',
                  'growth_phase_snapshots', 'growth_phase_catalogs', 'growth_phase_rank_baselines',
                  'growth_phase_runs', 'growth_snapshots'):
        predicates.append((table, f'mission IN ({slots})', missions))
    if nonces:
        nonce_slots = ','.join('?' for _ in nonces)
        predicates += [(t, f'nonce IN ({nonce_slots})', nonces) for t in ('growth_rewards', 'results')]
    offer_where = f'mission IN ({slots})'
    offer_args = list(missions)
    for nonce in nonces:
        offer_where += ' OR source LIKE ?'
        offer_args.append(f'victory:{nonce}:%')
    predicates += [('growth_offers', offer_where, offer_args), ('attempts', f'mission IN ({slots})', missions)]
    for table, where, args in predicates:
        if table_exists(conn, table):
            archive['tables'][table] = [dict(r) for r in conn.execute(f'SELECT * FROM {table} WHERE {where}', args)]
    if growth.exists(conn):
        archive['growth_state'] = dict(growth._state(conn, mission))
    if table_exists(conn, 'growth_manual_ranks'):
        archive['manual_ranks'] = [dict(r) for r in conn.execute(
            'SELECT * FROM growth_manual_ranks WHERE campaign=?', (before['campaign'],))]
    conn.execute('''CREATE TABLE IF NOT EXISTS campaign_playthroughs (
        campaign TEXT PRIMARY KEY, number INTEGER NOT NULL CHECK(number>=2),
        curses_per_mission INTEGER NOT NULL CHECK(curses_per_mission BETWEEN 0 AND 4),
        carry_curses INTEGER NOT NULL DEFAULT 0 CHECK(carry_curses IN (0,1)),
        rank_scaling INTEGER NOT NULL DEFAULT 1 CHECK(rank_scaling IN (0,1)))''')
    # Earlier development records always reset curses and applied the bonus.
    # Add defaults only on an explicit transition; viewing a record is read-only.
    columns={r[1] for r in conn.execute('PRAGMA table_info(campaign_playthroughs)')}
    for name,default in (('carry_curses',0),('rank_scaling',1)):
        if name not in columns:
            conn.execute(f'ALTER TABLE campaign_playthroughs ADD COLUMN {name} INTEGER NOT NULL DEFAULT {default} CHECK({name} IN (0,1))')
    conn.execute('''CREATE TABLE IF NOT EXISTS campaign_playthrough_archives (
        campaign TEXT NOT NULL, number INTEGER NOT NULL, archive_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(campaign,number))''')
    conn.execute('INSERT INTO campaign_playthrough_archives(campaign,number,archive_json) VALUES (?,?,?)',
                 (before['campaign'], before['number'], json.dumps(archive, ensure_ascii=False, sort_keys=True)))
    for table, where, args in predicates:
        if table in archive['tables']:
            conn.execute(f'DELETE FROM {table} WHERE {where}', args)
    if growth.exists(conn):
        # A campaign completed on an older map may have no growth row even
        # though another campaign in this record already has a catalog.
        growth.initialize_campaign(conn, mission)
        state = growth._state(conn, mission)
        stacks=json.loads(state['curses_json']) if carry_curses else {}
        growth._save_state(conn, mission, state['revision'] + 1, json.loads(state['talents_json']), stacks)
    clear_mask = 0
    for identity in missions:
        clear_mask |= 1 << progression.metadata(identity)['completion_bit']
    conn.execute('UPDATE campaign SET completed_mask=completed_mask & ?, revision=revision+1 WHERE id=1', (~clear_mask,))
    conn.execute('''INSERT INTO campaign_playthroughs(campaign,number,curses_per_mission,carry_curses,rank_scaling)
        VALUES (?,?,?,?,?) ON CONFLICT(campaign) DO UPDATE SET number=excluded.number,
        curses_per_mission=excluded.curses_per_mission,carry_curses=excluded.carry_curses,rank_scaling=excluded.rank_scaling''',
                 (before['campaign'], before['number'] + 1, curses_per_mission, int(carry_curses), int(rank_scaling)))
    return campaign_status(conn, campaign_id)
