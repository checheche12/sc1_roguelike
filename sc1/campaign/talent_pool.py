"""Append approved missing talents without rewriting pinned offers or loadouts."""
from __future__ import annotations
import copy
import hashlib
import json
from .runtime_catalog import GrowthError, load_catalog, validate_catalog

APPENDED = {
    '5e871f9a-f71b-475b-82a1-0879d54d9d30': (104, 'rare', 3, 'independent_layers', 2),
    'f08eec6e-b40c-4b25-8fb2-cd5710d54401': (105, 'epic', 12, 'shared_cycle', 3),
}

def merge(catalog, entries, revision=2):
    if revision == 3:
        from . import talent_ranks
        legacy = [item for item in entries if item.get('id') in APPENDED]
        ranked = [item for item in entries if item.get('id') not in APPENDED]
        return talent_ranks.merge(merge(catalog, legacy, 2), ranked)
    if revision != 2 or len(entries) != len(APPENDED):
        raise GrowthError('catalog_incompatible', '승인되지 않은 재능 목록 확장입니다.')
    result = copy.deepcopy(catalog)
    known = {item['id']: item for item in result['talents']}
    positions = {item['bit_index']: item['id'] for item in result['talents']}
    seen = set()
    for item in entries:
        expected = APPENDED.get(item.get('id'))
        effect = item.get('effect', {})
        if (expected is None or item['id'] in seen or not isinstance(effect, dict)
                or (item.get('bit_index'), item.get('rarity'), effect.get('unit_id'),
                    effect.get('mode'), effect.get('max_targets')) != expected
                or item.get('race') != 'terran' or effect.get('type') != 'multi_target'):
            raise GrowthError('catalog_incompatible', '추가 재능의 원문 ID·등급·전송 위치가 다릅니다.')
        seen.add(item['id'])
        if item['bit_index'] in positions and positions[item['bit_index']] != item['id']:
            raise GrowthError('catalog_incompatible', '기존 재능의 전송 위치를 변경할 수 없습니다.')
        if item['id'] in known:
            old = known[item['id']]
            if any(old.get(key) != item.get(key) for key in (
                    'bit_index', 'race', 'rarity', 'name', 'source_description', 'effect')):
                raise GrowthError('catalog_incompatible', '기존 재능 효과를 변경할 수 없습니다.')
        else:
            result['talents'].append(copy.deepcopy(item))
    result['talent_pool_revision'] = revision
    return validate_catalog(result)

def apply_updates(conn, catalog):
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='growth_talent_pool_updates'").fetchone()
    if not exists:
        return catalog
    row = conn.execute('SELECT revision,talents_json FROM growth_talent_pool_updates ORDER BY revision DESC LIMIT 1').fetchone()
    if row and row[0] > catalog.get('talent_pool_revision', 1):
        return merge(catalog, json.loads(row[1]), row[0])
    return catalog

def upgrade(conn, catalog, catalog_path=None, catalog_version=1):
    # Called only after authorized LOAD, never by read-only inspection or clicks.
    if catalog_path is not None or catalog.get('rework_revision')==5:
        return catalog
    packaged = load_catalog(expected_version=catalog_version)
    revision = packaged.get('talent_pool_revision', 1)
    if revision <= catalog.get('talent_pool_revision', 1):
        # Another campaign may already have expanded the singleton catalog,
        # while an older mission still owns its original per-run pin. Append a
        # sidecar for those pins too; issued offers and pins remain immutable.
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'growth_talent_pool_updates' in tables and conn.execute(
                'SELECT 1 FROM growth_talent_pool_updates WHERE revision>=?',(revision,)).fetchone():
            return catalog
        pins = [row[0] for row in conn.execute('SELECT catalog_json FROM growth_state')]
        if 'growth_phase_catalogs' in tables:
            pins.extend(row[0] for row in conn.execute('SELECT catalog_json FROM growth_phase_catalogs'))
        if not any(json.loads(pin).get('talent_pool_revision',1) < revision for pin in pins):
            return catalog
    entries = [item for item in packaged['talents'] if item['id'] in APPENDED or revision == 3 and item.get('offer_family')]
    merged = merge(catalog, entries, revision)
    conn.execute('''CREATE TABLE IF NOT EXISTS growth_talent_pool_updates (
        revision INTEGER PRIMARY KEY, talents_json TEXT NOT NULL,
        packaged_sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)''')
    raw = json.dumps(packaged, ensure_ascii=False, sort_keys=True)
    conn.execute('INSERT OR IGNORE INTO growth_talent_pool_updates (revision,talents_json,packaged_sha256) VALUES (?,?,?)',
                 (revision, json.dumps(entries, ensure_ascii=False, sort_keys=True),
                  hashlib.sha256(raw.encode('utf8')).hexdigest()))
    return merged
