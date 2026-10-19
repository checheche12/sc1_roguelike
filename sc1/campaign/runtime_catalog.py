"""Validated, versioned effects that the current maps actually implement.

The writing workshop is deliberately not a runtime dependency. A record pins
this small catalog on its first selection, so edits cannot reroll saved offers.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

DEFAULT_CATALOG = Path(__file__).with_name("runtime_talents_all.json")
REWORK_CATALOG = Path(__file__).with_name("runtime_talents_v5.json")
RARITIES = ("common", "uncommon", "rare", "epic", "legendary")


class GrowthError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def validate_catalog(value: dict, expected_version: int | None = None) -> dict:
    if expected_version is None and isinstance(value,dict):
        expected_version=value.get('catalog_version')
    if type(expected_version) is not int or expected_version not in (1,2):
        raise GrowthError("catalog_version", "지원하지 않는 성장 목록 버전입니다.")
    if (not isinstance(value, dict) or type(value.get("schema_version")) is not int
            or value["schema_version"] != 1 or type(value.get("catalog_version")) is not int
            or value["catalog_version"] != expected_version):
        raise GrowthError("catalog_version", "성장 목록과 관리자 버전이 다릅니다.")
    ids = set()
    rank_slots=set()
    packed=set()
    for kind, index_key, limit in (("talents", "bit_index", 512), ("curses", "byte_index", 64 if expected_version==2 else 16)):
        items = value.get(kind)
        if not isinstance(items, list):
            raise GrowthError("invalid_catalog", "재능 또는 저주 목록이 없습니다.")
        indices = set()
        for item in items:
            if not isinstance(item, dict):
                raise GrowthError("invalid_catalog", "잘못된 성장 항목입니다.")
            identity, index = item.get("id"), item.get(index_key)
            storage=item.get('wire_storage')
            if storage is not None:
                from .unit_growth import specifications,identity as unit_identity
                spec=next((s for s in specifications() if s['index']==index),None)
                if (kind!='talents' or expected_version!=2 or spec is None or spec['storage']!=storage
                        or identity!=unit_identity(spec['ordinal'])):
                    raise GrowthError('invalid_catalog','유닛별 성장 저장 위치가 잘못되었습니다.')
                cells={(storage['word'],b) for b in range(storage['shift'],storage['shift']+storage['width'])}
                if cells & packed:raise GrowthError('invalid_catalog','유닛별 성장 저장 위치가 중복됩니다.')
                packed.update(cells)
            if (not isinstance(identity, str) or not identity.strip() or identity in ids
                    or type(index) is not int or not 0 <= index < (1024 if storage else limit) or index in indices):
                raise GrowthError("invalid_catalog", "성장 항목의 ID 또는 전송 위치가 잘못되거나 중복됩니다.")
            ids.add(identity)
            indices.add(index)
            if kind=='talents' and storage is None:
                cell=(1+index//32,index%32)
                if cell in packed:raise GrowthError('invalid_catalog','유닛 성장과 기존 비트가 겹칩니다.')
                packed.add(cell)
            if (any(not isinstance(item.get(key), str) or not item[key].strip()
                    for key in ("name", "target", "description"))
                    or item.get("rarity") not in RARITIES
                    or type(item.get("implemented")) is not bool
                    or not isinstance(item.get("missions"), list)
                    or any(type(mission) is not int or mission <= 0 for mission in item["missions"])):
                raise GrowthError("invalid_catalog", "성장 항목의 설명, 등급 또는 지원 임무가 잘못되었습니다.")
            if kind == "talents" and item.get("race") not in ("terran", "zerg", "protoss", "shared"):
                raise GrowthError("invalid_catalog", "재능 종족이 잘못되었습니다.")
            if item.get('repeatable'):
                slot=item.get('rank_slot')
                if (expected_version!=2 or kind!='talents' or (item.get('rarity')!='common' and item.get('effect_ordinal') not in (26,27,28,67,68,69,108,109,110))
                        or (storage is None and (type(slot) is not int or not 0<=slot<32 or slot in rank_slots))):
                    raise GrowthError('invalid_catalog','반복 교범의 영구 중첩 위치가 잘못되었습니다.')
                if 'max_rank' in item and (type(item['max_rank']) is not int or item['max_rank']!=4):
                    raise GrowthError('invalid_catalog','전투 재능의 중첩 한도가 잘못되었습니다.')
                if storage is None:
                    rank_slots.add(slot)
                    cells={(33+slot,b) for b in range(32)}
                    if cells&packed:raise GrowthError('invalid_catalog','교범과 유닛 성장 위치가 겹칩니다.')
                    packed.update(cells)
            effect = item.get("effect", {})
            if not isinstance(effect, dict):
                raise GrowthError("invalid_catalog", "성장 효과 형식이 잘못되었습니다.")
            if effect.get("type") == "multi_target":
                expected = {"independent_layers": (3, 2), "shared_cycle": (12, 3)}.get(effect.get("mode"))
                if (kind != "talents" or expected is None
                        or type(effect.get("unit_id")) is not int or type(effect.get("max_targets")) is not int
                        or (effect["unit_id"], effect["max_targets"]) != expected
                        or effect.get("full_weapon_damage") is not True
                        or effect.get("recursive_secondary_attacks") is not False
                        or item.get("target_units") != [effect["unit_id"]]):
                    raise GrowthError("invalid_catalog", "다중 대상 공격의 유닛·대상 수·피해 규칙이 잘못되었습니다.")
            if kind == "curses" and (type(item.get("max_stacks")) is not int
                                      or not 1 <= item["max_stacks"] <= (0xffffffff if expected_version==2 and item["byte_index"] in (16,17,18,19) else 255)):
                raise GrowthError("invalid_catalog", "저주 중첩 저장 범위가 잘못되었습니다.")
    ranked = {item['id']: item for item in value['talents'] if item.get('offer_family') is not None}
    family_ranks = set()
    for item in ranked.values():
        family, rank = item.get('offer_family'), item.get('rank')
        if (not isinstance(family, str) or not family.strip() or type(rank) is not int
                or rank not in (1, 2, 3) or (family, rank) in family_ranks):
            raise GrowthError('invalid_catalog', '병력 특성의 계열 또는 단계가 잘못되었습니다.')
        family_ranks.add((family, rank))
        previous = item.get('requires_talent_id')
        if rank == 1:
            if previous is not None:
                raise GrowthError('invalid_catalog', '첫 특성 단계에는 선행 재능이 없어야 합니다.')
        else:
            parent = ranked.get(previous)
            if (parent is None or parent['offer_family'] != family or parent['rank'] != rank - 1
                    or parent['race'] != item['race']):
                raise GrowthError('invalid_catalog', '병력 특성의 선행 단계가 잘못되었습니다.')
    return copy.deepcopy(value)


def load_catalog(path: str | Path | None = None, expected_version: int = 1) -> dict:
    try:
        value = json.loads(Path(path or (REWORK_CATALOG if expected_version==2 else DEFAULT_CATALOG)).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise GrowthError("catalog_unavailable", "구현된 성장 목록을 읽을 수 없습니다. 관리자 설치를 확인해 주세요.") from exc
    return validate_catalog(value, expected_version)


def encode_growth(catalog: dict, talents: list[str], curses: dict[str, int], ranks: dict[str,int] | None = None) -> list[int]:
    """21 uint32 words: version, 512 talent bits, sixteen curse counts."""
    version=catalog['catalog_version']
    words = [version] + [0] * (64 if version==2 else 20)
    ranks={} if ranks is None else ranks
    if not isinstance(ranks,dict) or any(not isinstance(identity,str) for identity in ranks):
        raise GrowthError('invalid_growth','교범 중첩 기록의 형식이 잘못되었습니다.')
    known_talents = {item["id"]: item for item in catalog["talents"]}
    known_curses = {item["id"]: item for item in catalog["curses"]}
    if (not isinstance(talents, list) or any(not isinstance(identity, str) for identity in talents)
            or not isinstance(curses, dict) or any(not isinstance(identity, str) for identity in curses)):
        raise GrowthError("invalid_growth", "보유 성장 기록의 형식이 잘못되었습니다.")
    if len(talents) != len(set(talents)):
        raise GrowthError("invalid_growth", "중복된 보유 재능 기록입니다.")
    owned = set(talents)
    for identity in talents:
        if identity not in known_talents or not known_talents[identity]["implemented"]:
            raise GrowthError("invalid_growth", "보유 재능에 지원하지 않는 항목이 있습니다.")
        previous = known_talents[identity].get('requires_talent_id')
        if previous is not None and previous not in owned:
            raise GrowthError('invalid_growth', '병력 특성의 이전 단계가 보유 기록에 없습니다.')
        item=known_talents[identity]
        index = item["bit_index"]
        storage=item.get('wire_storage')
        if storage is None:words[1 + index // 32] |= 1 << (index % 32)
        else:
            count=ranks.get(identity,1) if item.get('repeatable') else 1
            if type(count) is not int or not 1<=count<=0xffffffff:raise GrowthError('invalid_growth','유닛 교범 중첩이 잘못되었습니다.')
            words[storage['word']]|=min(count,item.get('max_rank',1))<<storage['shift']
        if known_talents[identity].get('repeatable'):
            count=ranks.get(identity,1)
            if type(count) is not int or not 1<=count<=0xFFFFFFFF:
                raise GrowthError('invalid_growth','교범 중첩은 양의 32비트 정수여야 합니다.')
            if storage is None:words[33+known_talents[identity]['rank_slot']]=min(count,known_talents[identity].get('max_rank',0xffffffff))
    if any(identity not in owned or not known_talents[identity].get('repeatable') for identity in ranks):
        raise GrowthError('invalid_growth','보유하지 않은 교범 중첩입니다.')
    for identity, count in curses.items():
        item = known_curses.get(identity)
        if (not item or not item["implemented"] or type(count) is not int
                or not 0 <= count <= item["max_stacks"]):
            raise GrowthError("invalid_growth", "보유 저주의 중첩 기록이 잘못되었습니다.")
        index = item["byte_index"]
        if version==2 and index in (16,17,18,19):
            words[80-index]=count
            count=min(count,255)
        words[17 + index // 4] |= count << (8 * (index % 4))
    return words


def validate_growth_words(value) -> list[int]:
    """Reject damaged immutable snapshots before any response can reach a map."""
    if (not isinstance(value, list) or not value or type(value[0]) is not int
            or value[0] not in (1,2) or len(value)!=(65 if value[0]==2 else 21)
            or any(type(word) is not int or not 0 <= word <= 0xFFFFFFFF for word in value)):
        raise GrowthError("invalid_growth", "출전 성장 기록의 전송 형식이 잘못되었습니다.")
    return list(value)


def upgrade_growth_words(value):
    """Losslessly carry historical wire-v1 bits/counts in a wire-v2 response."""
    words=validate_growth_words(value)
    return words if words[0]==2 else [2,*words[1:17],*words[17:21],*([0]*44)]
