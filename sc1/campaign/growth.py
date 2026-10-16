"""Selection transactions and immutable mission loadouts.

All mutations use the caller's BEGIN IMMEDIATE transaction. No function commits
or opens a database; completion rewards therefore share the result ACK boundary.
"""
from __future__ import annotations

import copy
import hashlib
import json
import secrets
import sqlite3
import uuid

from . import progression, talent_pool, talent_ranks, talent_selection, rework_growth

from .runtime_catalog import (GrowthError, encode_growth, load_catalog,
                              validate_catalog, validate_growth_words)

INITIAL_MISSION = 101
EMPTY_WORDS = [1] + [0] * 20
RARITY_WEIGHTS = {"common": 40, "uncommon": 30, "rare": 20, "epic": 8, "legendary": 2}
GROWTH_TABLES = {"growth_state", "growth_offers", "growth_snapshots", "growth_rewards"}


class GrowthChoicesPending(Exception):
    """A normal wait state; it must not become a protocol ValueError/ERROR ACK."""
    def __init__(self, message="게임 안에서 재능 3개와 저주 2개 선택을 먼저 마쳐 주세요.", *, state=None):
        self.state = state
        super().__init__(message)


def exists(conn: sqlite3.Connection) -> bool:
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    present = GROWTH_TABLES & tables
    if present and present != GROWTH_TABLES:
        raise GrowthError("invalid_growth", "성장 기록의 저장 구조가 불완전합니다.")
    return bool(present)


def _json(value):
    try:
        return json.loads(value)
    except (TypeError, ValueError) as exc:
        raise GrowthError("invalid_growth", "성장 기록을 읽을 수 없습니다.") from exc


def _saved_catalog(conn, catalog_version=None):
    row = _state(conn)
    base = validate_catalog(_json(row["catalog_json"]))
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "growth_catalog_extensions" in tables:
        extra = conn.execute("SELECT catalog_json FROM growth_catalog_extensions WHERE id=1").fetchone()
        if extra:
            base = validate_catalog(_json(extra[0]))
    return rework_growth.overlay(conn,talent_pool.apply_updates(conn, apply_curse_pool_updates(conn, base)))



def _merge_curse_pool(catalog, entries, revision):
    """Keep pinned items exact and append only compatible packaged curse slots."""
    result = copy.deepcopy(catalog)
    incoming = {item["id"]: item for item in entries}
    positions = {item["byte_index"]: item["id"] for item in entries}
    if len(incoming) != len(entries) or len(positions) != len(entries):
        raise GrowthError("catalog_incompatible", "저주 추가 목록의 ID 또는 위치가 중복됩니다.")
    for item in result["curses"]:
        replacement = incoming.get(item["id"])
        if replacement is None or any(replacement.get(key) != item.get(key)
                for key in ("byte_index", "race", "rarity", "name", "source_description", "max_stacks")):
            raise GrowthError("catalog_incompatible", "기존 저주를 변경하는 목록 확장은 적용할 수 없습니다.")
        if item.get("effect") not in (replacement.get("effect"), replacement.get("legacy_effect")):
            raise GrowthError("catalog_incompatible", "기존 저주 효과를 변경할 수 없습니다.")
    known = {item["id"] for item in result["curses"]}
    result["curses"].extend(copy.deepcopy(item) for item in entries if item["id"] not in known)
    result["curse_pool_revision"] = revision
    return validate_catalog(result)


def apply_curse_pool_updates(conn, catalog):
    """Read additive user-authorized updates without changing any pinned row."""
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "growth_curse_pool_updates" not in tables:
        return catalog
    saved = conn.execute("SELECT revision,curses_json FROM growth_curse_pool_updates ORDER BY revision DESC LIMIT 1").fetchone()
    if saved and saved["revision"] > catalog.get("curse_pool_revision", 1):
        return _merge_curse_pool(catalog, _json(saved["curses_json"]), saved["revision"])
    return catalog


def upgrade_curse_pool(conn, catalog_path=None, catalog_version=1):
    """Authorized LOAD can extend unissued choices; issued JSON stays immutable.

    The 2026-10-15 request permits new curse options in future choices. Existing
    catalog pins, candidate rows, selections and snapshots are never rewritten.
    Explicit custom catalog paths keep their exact test/deployment contract.
    """
    saved = _saved_catalog(conn, catalog_version)
    if rework_growth.enabled(saved):return saved
    if catalog_path is not None:
        return saved
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "growth_curse_pool_updates" in tables and conn.execute(
            "SELECT 1 FROM growth_curse_pool_updates WHERE revision=2").fetchone():
        return saved
    packaged = load_catalog(expected_version=catalog_version)
    revision = packaged.get("curse_pool_revision", 1)
    if revision == 1:
        return saved
    if type(revision) is not int or revision != 2:
        raise GrowthError("catalog_incompatible", "승인되지 않은 저주 목록 확장입니다.")
    merged = _merge_curse_pool(saved, packaged["curses"], revision)
    conn.execute("""CREATE TABLE IF NOT EXISTS growth_curse_pool_updates (
        revision INTEGER PRIMARY KEY, curses_json TEXT NOT NULL,
        packaged_sha256 TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    raw = json.dumps(packaged, ensure_ascii=False, sort_keys=True)
    conn.execute("INSERT OR IGNORE INTO growth_curse_pool_updates (revision,curses_json,packaged_sha256) VALUES (?,?,?)",
                 (revision, json.dumps(packaged["curses"], ensure_ascii=False, sort_keys=True),
                  hashlib.sha256(raw.encode("utf-8")).hexdigest()))
    return merged


def initialize(conn: sqlite3.Connection, catalog_path=None, catalog_version=1) -> dict:
    if exists(conn):
        return _saved_catalog(conn, catalog_version)
    catalog = load_catalog(catalog_path, catalog_version)
    conn.execute("""CREATE TABLE growth_state (
        id INTEGER PRIMARY KEY CHECK(id=1), catalog_json TEXT NOT NULL,
        revision INTEGER NOT NULL CHECK(revision>=0), talents_json TEXT NOT NULL,
        curses_json TEXT NOT NULL)""")
    conn.execute("INSERT INTO growth_state VALUES (1,?,0,'[]','{}')", (json.dumps(catalog, ensure_ascii=False, sort_keys=True),))
    conn.execute("""CREATE TABLE growth_offers (
        sequence INTEGER PRIMARY KEY AUTOINCREMENT, offer_id TEXT NOT NULL UNIQUE,
        source TEXT NOT NULL UNIQUE, mission INTEGER, kind TEXT NOT NULL CHECK(kind IN ('talent','curse')),
        rarity TEXT, candidates_json TEXT, offered_revision INTEGER,
        selected_id TEXT, selected_revision INTEGER, selected_at TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE growth_snapshots (
        nonce TEXT PRIMARY KEY REFERENCES attempts(nonce), mission INTEGER NOT NULL UNIQUE,
        catalog_version INTEGER NOT NULL, words_json TEXT NOT NULL,
        load_response_json TEXT NOT NULL, legacy INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("""CREATE TABLE growth_rewards (
        nonce TEXT PRIMARY KEY REFERENCES attempts(nonce),
        talent_choices INTEGER NOT NULL, curse_choices INTEGER NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    return catalog



def initialize_campaign(conn, mission):
    """Add per-campaign state; the original Terran row remains authoritative."""
    race = progression.campaign_key(mission)
    if race == "1":
        return
    conn.execute("""CREATE TABLE IF NOT EXISTS growth_campaign_states (
        race TEXT PRIMARY KEY,
        revision INTEGER NOT NULL CHECK(revision>=0),
        talents_json TEXT NOT NULL, curses_json TEXT NOT NULL)""")
    conn.execute("INSERT OR IGNORE INTO growth_campaign_states VALUES (?,0,'[]','{}')", (race,))


def _save_state(conn, mission, revision, owned, stacks):
    race = progression.campaign_key(mission)
    values = (revision, json.dumps(owned), json.dumps(stacks))
    if race == "1":
        conn.execute("UPDATE growth_state SET revision=?,talents_json=?,curses_json=? WHERE id=1", values)
    else:
        conn.execute("UPDATE growth_campaign_states SET revision=?,talents_json=?,curses_json=? WHERE race=?", (*values,race))


def expand_saved_catalog(conn, mission, catalog_path=None, catalog_version=1):
    """Add a pinned expansion without rewriting old catalog/offer/snapshot rows.

    Existing mission runs keep their exact catalog. The first newly supported
    mission can opt into a packaged extension, and each old bit/effect/rarity is
    checked for compatibility before any sidecar is saved.
    """
    saved = _saved_catalog(conn, catalog_version)
    if rework_growth.enabled(saved):return saved
    if catalog_path is not None or saved.get("campaign_expansion"):
        return saved
    if mission == 101:
        return saved
    from .runtime_catalog import load_catalog
    expanded = load_catalog(expected_version=catalog_version)
    if not expanded.get("campaign_expansion"):
        return saved
    for kind, index in (("talents", "bit_index"), ("curses", "byte_index")):
        current = {item['id']: item for item in expanded[kind]}
        for item in saved[kind]:
            replacement = current.get(item['id'])
            for key in (index, 'race', 'rarity', 'name', 'source_description'):
                if replacement is None or replacement.get(key) != item.get(key):
                    raise GrowthError('catalog_incompatible', '기존 성장 항목을 바꾸는 목록 확장은 적용할 수 없습니다.')
            # The old T01 effect is kept in the expansion compatibility field.
            if replacement.get('legacy_effect', replacement.get('effect')) != item.get('effect'):
                raise GrowthError('catalog_incompatible', '기존 성장 효과가 달라 목록을 확장할 수 없습니다.')
    conn.execute("""CREATE TABLE IF NOT EXISTS growth_catalog_extensions (
        id INTEGER PRIMARY KEY CHECK(id=1), catalog_json TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
    conn.execute("INSERT OR IGNORE INTO growth_catalog_extensions (id,catalog_json) VALUES (1,?)",
                 (json.dumps(expanded, ensure_ascii=False, sort_keys=True),))
    return _saved_catalog(conn, catalog_version)

def _add_offers(conn, source, mission, talent_count, curse_count):
    for index, kind in enumerate(["talent"] * talent_count + ["curse"] * curse_count):
        source_key = f"{source}:{index}"
        if conn.execute("SELECT 1 FROM growth_offers WHERE source=?", (source_key,)).fetchone():
            continue
        conn.execute("""INSERT INTO growth_offers
            (offer_id,source,mission,kind,rarity) VALUES (?,?,?,?,?)""",
                     (str(uuid.uuid4()), source_key, mission, kind, "common" if kind == "curse" else None))


def _current(conn, mission):
    return conn.execute("SELECT * FROM growth_offers WHERE mission=? AND selected_id IS NULL ORDER BY sequence LIMIT 1", (mission,)).fetchone()


def _offer(row):
    return {"offer_id": row["offer_id"], "kind": row["kind"], "rarity": row["rarity"],
            "revision": row["offered_revision"], "candidates": json.loads(row["candidates_json"])}


def _state(conn, mission=INITIAL_MISSION):
    race = progression.campaign_key(mission)
    if race == "1":
        row = conn.execute("SELECT * FROM growth_state WHERE id=1").fetchone()
    else:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        row = (conn.execute("SELECT * FROM growth_campaign_states WHERE race=?", (race,)).fetchone()
               if "growth_campaign_states" in tables else None)
        if row is None:
            return {"revision":0, "talents_json":"[]", "curses_json":"{}"}
    if row is None:
        raise GrowthError("invalid_growth", "성장 기록이 불완전합니다.")
    return row


def _issue(conn, mission, catalog):
    row = _current(conn, mission)
    if row is None or row["candidates_json"] is not None:
        return
    state = _state(conn, mission)
    owned = _json(state["talents_json"])
    stacks = _json(state["curses_json"])
    encode_growth(catalog, owned, stacks)
    kind = row["kind"]
    eligible = [item for item in catalog["talents" if kind == "talent" else "curses"]
                if progression.item_eligible(item, mission, kind)
                and (kind != 'talent' or talent_ranks.eligible(item, owned, catalog))
                and (kind != "talent" or item["id"] not in owned)
                and (kind != "curse" or (item["rarity"] == row["rarity"]
                                         and stacks.get(item["id"], 0) < item["max_stacks"]))]
    required = 4 if kind == "talent" else 3
    if len(eligible) < required:
        raise GrowthError("choice_pool_unavailable", f"이 임무에 구현된 {'재능 4개' if kind == 'talent' else '같은 등급 저주 3개'} 후보가 부족합니다. 목록 업데이트가 필요합니다.")
    if kind == "curse":
        # Version 1 has exactly three common curses. Keep their presentation
        # order fixed so both selections offer the same understandable set.
        candidates = eligible if len(eligible) == 3 else secrets.SystemRandom().sample(eligible, 3)
    else:
        candidates = talent_selection.select_candidates(eligible, mission, secrets.SystemRandom(), required)
    conn.execute("UPDATE growth_offers SET candidates_json=?,offered_revision=? WHERE offer_id=?",
                 (json.dumps(candidates, ensure_ascii=False, sort_keys=True), state["revision"], row["offer_id"]))


def prepare(conn, mission, catalog_path=None, catalog_version=1):
    catalog = initialize(conn, catalog_path, catalog_version)
    attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
    if attempt and attempt["state"] == "complete":
        return status(conn, mission)
    if conn.execute("SELECT 1 FROM growth_snapshots WHERE mission=?", (mission,)).fetchone():
        return status(conn, mission)
    if mission != INITIAL_MISSION:
        raise GrowthError("phased_protocol_required", "이 임무는 시작·중간·클리어 직전의 단계별 성장 지도로 불러와 주세요.")
    _add_offers(conn, "initial:101", mission, 3, 2)
    _issue(conn, mission, catalog)
    return status(conn, mission)


def status(conn, mission=INITIAL_MISSION):
    attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
    completed = bool(attempt and attempt["state"] == "complete")
    if not exists(conn):
        return {"state": "legacy_complete" if completed else "not_started", "mission": mission,
                "revision": 0, "offer": None, "talents": [], "curses": [], "history": [],
                "pending": {"talent": 0, "curse": 0}, "upcoming": {"talent": 0, "curse": 0}}
    row = _state(conn, mission)
    catalog = _saved_catalog(conn)
    owned = _json(row["talents_json"])
    stacks = _json(row["curses_json"])
    current_words = rework_growth.encode(conn,mission,catalog, owned, stacks)
    pending = {kind: conn.execute("SELECT COUNT(*) FROM growth_offers WHERE mission=? AND kind=? AND selected_id IS NULL", (mission, kind)).fetchone()[0] for kind in ("talent", "curse")}
    upcoming = {kind: conn.execute("SELECT COUNT(*) FROM growth_offers o JOIN attempts a ON o.source LIKE 'victory:' || a.nonce || ':%' WHERE o.mission IS NULL AND o.kind=? AND o.selected_id IS NULL AND a.mission=?", (kind, mission)).fetchone()[0] for kind in ("talent", "curse")}
    frozen = conn.execute("SELECT * FROM growth_snapshots WHERE mission=?", (mission,)).fetchone()
    current = _current(conn, mission)
    if completed:
        mode = "waiting_next_map" if sum(upcoming.values()) else "legacy_complete"
    elif frozen:
        mode = "in_mission"
    elif sum(pending.values()):
        mode = "choosing"
    else:
        mode = "ready"
    history = [{"offer_id": entry["offer_id"], "kind": entry["kind"], "selected_id": entry["selected_id"],
                "selected_at": entry["selected_at"], "revision": entry["selected_revision"]}
               for entry in conn.execute("SELECT * FROM growth_offers WHERE selected_id IS NOT NULL ORDER BY sequence")
               if entry["mission"] in progression.campaign_missions(mission)]
    return {"state": mode, "mission": mission, "revision": row["revision"],
            "catalog_version": catalog["catalog_version"],
            "offer": _offer(current) if current and current["candidates_json"] and mode == "choosing" else None,
            "pending": pending, "upcoming": upcoming, "history": history,
            "talents": [{**item,"stacks":min(rework_growth.ranks(conn,mission).get(item['id'],1),item.get('max_rank',0xffffffff))} for item in catalog["talents"] if item["id"] in owned],
            "curses": [{**item, "stacks": stacks[item["id"]]} for item in catalog["curses"] if stacks.get(item["id"], 0)],
            "growth_words": validate_growth_words(_json(frozen["words_json"])) if frozen else current_words}


def choose(conn, mission, offer_id, candidate_id, expected_revision, catalog_path=None, catalog_version=1):
    if type(expected_revision) is not int or expected_revision < 0:
        raise GrowthError("invalid_choice_revision", "선택 저장 번호가 잘못되었습니다.")
    if not isinstance(offer_id, str) or not isinstance(candidate_id, str):
        raise GrowthError("invalid_choice", "선택 항목이 잘못되었습니다.")
    # A stale or fabricated click must never enable/migrate an old record.
    # Only an explicit prepare or a growth-capable map LOAD initializes it.
    if not exists(conn):
        raise GrowthError("growth_not_prepared", "게임에서 선택지가 표시될 때까지 기다려 주세요.")
    catalog = _saved_catalog(conn, catalog_version)
    row = conn.execute("SELECT * FROM growth_offers WHERE offer_id=?", (offer_id,)).fetchone()
    if row is None or row["mission"] != mission:
        raise GrowthError("unknown_offer", "현재 임무의 선택지가 아닙니다.")
    if row["selected_id"] is not None:
        if row["selected_id"] == candidate_id and row["offered_revision"] == expected_revision:
            return {**status(conn, mission), "duplicate": True}
        raise GrowthError("conflicting_choice", "이미 다른 내용으로 저장한 선택입니다. 현재 기록을 다시 확인해 주세요.")
    attempt = conn.execute("SELECT state FROM attempts WHERE mission=?", (mission,)).fetchone()
    if ((attempt and attempt["state"] == "complete")
            or conn.execute("SELECT 1 FROM growth_snapshots WHERE mission=?", (mission,)).fetchone()):
        raise GrowthError("growth_locked", "출전 시 확정한 성장은 임무 중이나 재플레이에서 바꿀 수 없습니다.")
    current = _current(conn, mission)
    state = _state(conn, mission)
    if (current is None or current["offer_id"] != offer_id or row["candidates_json"] is None
            or state["revision"] != expected_revision or row["offered_revision"] != expected_revision):
        raise GrowthError("stale_choice", "선택 기록이 바뀌었습니다. 현재 선택지를 다시 확인해 주세요.")
    candidates = json.loads(row["candidates_json"])
    selected = next((item for item in candidates if item["id"] == candidate_id), None)
    if selected is None:
        raise GrowthError("invalid_choice", "표시된 후보 중 하나를 선택해 주세요.")
    owned, stacks = _json(state["talents_json"]), _json(state["curses_json"])
    encode_growth(catalog, owned, stacks)
    if row["kind"] == "talent":
        if candidate_id in owned:
            raise GrowthError("duplicate_talent", "이미 보유한 재능입니다.")
        owned.append(candidate_id)
    else:
        stacks[candidate_id] = stacks.get(candidate_id, 0) + 1
    encode_growth(catalog, owned, stacks)
    next_revision = expected_revision + 1
    _save_state(conn, mission, next_revision, owned, stacks)
    conn.execute("UPDATE growth_offers SET selected_id=?,selected_revision=?,selected_at=CURRENT_TIMESTAMP WHERE offer_id=?",
                 (candidate_id, next_revision, offer_id))
    _issue(conn, mission, catalog)
    return {**status(conn, mission), "duplicate": False}


def freeze(conn, response, catalog_version=1, *, legacy=False):
    existing = conn.execute("SELECT * FROM growth_snapshots WHERE mission=?", (response["mission"],)).fetchone()
    if existing:
        if existing["catalog_version"] not in (catalog_version,1 if catalog_version==2 else catalog_version) or existing["nonce"] != response["nonce"]:
            raise GrowthError("snapshot_mismatch", "이 임무의 성장 복원 정보가 다릅니다.")
        return validate_growth_words(_json(existing["words_json"]))
    state = _state(conn, response["mission"])
    catalog = _saved_catalog(conn, catalog_version)
    words = list(EMPTY_WORDS) if legacy else encode_growth(catalog, _json(state["talents_json"]), _json(state["curses_json"]))
    conn.execute("INSERT INTO growth_snapshots (nonce,mission,catalog_version,words_json,load_response_json,legacy) VALUES (?,?,?,?,?,?)",
                 (response["nonce"], response["mission"], catalog_version, json.dumps(words), json.dumps(response, sort_keys=True), int(legacy)))
    return words


def award_completion(conn, nonce):
    if not exists(conn):
        return
    snapshot = conn.execute("SELECT * FROM growth_snapshots WHERE nonce=? AND legacy=0", (nonce,)).fetchone()
    if snapshot is None:
        return
    inserted = conn.execute("INSERT OR IGNORE INTO growth_rewards (nonce,talent_choices,curse_choices) VALUES (?,2,2)", (nonce,)).rowcount
    if inserted:
        # Mission 102 has no registered map yet. Keep these rights durable and
        # unassigned, never offer unsupported effects or spend them on a replay.
        _add_offers(conn, f"victory:{nonce}", None, 2, 2)
