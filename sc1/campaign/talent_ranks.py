"""Append-only troop upgrade ranks; historical talent bits retain their effects."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from .runtime_catalog import GrowthError, validate_catalog

PATH = Path(__file__).with_name('talent_rank_catalog.json')
REVISION = 3


def additions():
    value = json.loads(PATH.read_text(encoding='utf-8'))
    if value.get('schema_version') != 1 or value.get('revision') != REVISION:
        raise GrowthError('catalog_incompatible', '병력 특성 목록 버전이 잘못되었습니다.')
    entries = value.get('talents', [])
    if len(entries) != 132 or sorted(x.get('bit_index', -1) for x in entries) != list(range(106, 238)):
        raise GrowthError('catalog_incompatible', '병력 특성의 전송 위치가 잘못되었습니다.')
    return entries


def merge(catalog, entries):
    expected = {item['id']: item for item in additions()}
    incoming = {item['id']: item for item in entries}
    if len(incoming) != len(entries) or incoming != expected:
        raise GrowthError('catalog_incompatible', '승인된 병력 특성 목록과 다릅니다.')
    result = copy.deepcopy(catalog)
    current = {item['id']: item for item in result['talents']}
    positions = {item['bit_index']: item['id'] for item in result['talents']}
    for item in entries:
        if positions.get(item['bit_index'], item['id']) != item['id']:
            raise GrowthError('catalog_incompatible', '기존 재능의 전송 위치를 변경할 수 없습니다.')
        if item['id'] in current:
            if current[item['id']] != item:
                raise GrowthError('catalog_incompatible', '기존 병력 특성 단계를 변경할 수 없습니다.')
        else:
            result['talents'].append(copy.deepcopy(item))
    result['talent_pool_revision'] = REVISION
    return validate_catalog(result)


def eligible(item, owned, catalog):
    """Only the next rank is offered; completed historical choices stay valid."""
    if catalog.get('talent_pool_revision', 1) < REVISION:
        return True
    if not item.get('offer_family'):
        return False
    previous = item.get('requires_talent_id')
    return previous is None or previous in owned
