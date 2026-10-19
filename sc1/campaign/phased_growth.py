"""Opt-in PHC1 growth: one durable talent/curse pair at each checkpoint.

The caller owns BEGIN IMMEDIATE and COMMIT. Legacy offers, selected history,
catalogs and snapshots are retained; only additive mapping/snapshot tables are
introduced. Reads and rejected clicks never initialize these tables.
"""
from __future__ import annotations

import json
import secrets
import uuid

from . import growth, progression, talent_pool, talent_ranks, talent_selection, rework_growth
from .runtime_catalog import GrowthError, encode_growth, validate_growth_words

TOTAL_PHASES = 3
TABLES = {"growth_phase_runs", "growth_phase_offers", "growth_phase_snapshots"}


def exists(conn):
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    present = TABLES & tables
    if present and present != TABLES:
        raise GrowthError("invalid_growth", "단계별 성장 저장 구조가 불완전합니다.")
    return bool(present)


def run(conn, mission):
    return conn.execute("SELECT * FROM growth_phase_runs WHERE mission=?", (mission,)).fetchone() if exists(conn) else None


def validate_phase(phase, nonce):
    if type(phase) is not int or phase not in (1, 2, 3):
        raise GrowthError("invalid_phase", "성장 단계는 1~3이어야 합니다.")
    if phase == 1:
        if nonce is not None:
            raise GrowthError("phase_nonce_mismatch", "첫 단계는 초기 불러오기 요청이어야 합니다.")
    elif (not isinstance(nonce, str) or len(nonce) != 32
          or any(c not in "0123456789abcdef" for c in nonce)):
        raise GrowthError("phase_nonce_mismatch", "단계 선택에 현재 출전 ID가 필요합니다.")


def _latest(conn, mission):
    return conn.execute("SELECT * FROM growth_phase_snapshots WHERE mission=? ORDER BY phase DESC LIMIT 1", (mission,)).fetchone()


def _completed(conn, row):
    latest = _latest(conn, row["mission"])
    return 3 if row["legacy"] else (latest["phase"] if latest else 0)


def _current(conn, mission, phase):
    return conn.execute("""SELECT o.* FROM growth_phase_offers p JOIN growth_offers o USING(offer_id)
        WHERE p.mission=? AND p.phase=? AND o.selected_id IS NULL
        ORDER BY CASE o.kind WHEN 'talent' THEN 0 ELSE 1 END LIMIT 1""", (mission, phase)).fetchone()


def _run_catalog(conn, mission, catalog_version=1):
    tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "growth_phase_catalogs" in tables:
        saved=conn.execute("SELECT catalog_json FROM growth_phase_catalogs WHERE mission=?",(mission,)).fetchone()
        if saved:
            return rework_growth.overlay(conn,talent_pool.apply_updates(conn, growth.apply_curse_pool_updates(conn, growth.validate_catalog(growth._json(saved[0])))))
    # Pre-expansion PHC1 runs always used the original singleton pin.
    return rework_growth.overlay(conn,talent_pool.apply_updates(conn, growth.apply_curse_pool_updates(conn, growth.validate_catalog(growth._json(growth._state(conn)["catalog_json"])))))


def _initialize(conn, mission, catalog_path, catalog_version):
    catalog = growth.initialize(conn, catalog_path, catalog_version)
    growth.initialize_campaign(conn, mission)
    if not exists(conn):
        conn.execute("""CREATE TABLE growth_phase_runs (
            mission INTEGER PRIMARY KEY, catalog_version INTEGER NOT NULL,
            active_phase INTEGER NOT NULL CHECK(active_phase BETWEEN 1 AND 3),
            legacy INTEGER NOT NULL CHECK(legacy IN (0,1)),
            baseline_talents_json TEXT NOT NULL, baseline_curses_json TEXT NOT NULL)""")
        conn.execute("""CREATE TABLE growth_phase_offers (
            offer_id TEXT PRIMARY KEY REFERENCES growth_offers(offer_id),
            mission INTEGER NOT NULL REFERENCES growth_phase_runs(mission),
            phase INTEGER NOT NULL CHECK(phase BETWEEN 1 AND 3),
            kind TEXT NOT NULL CHECK(kind IN ('talent','curse')),
            UNIQUE(mission,phase,kind))""")
        conn.execute("""CREATE TABLE growth_phase_snapshots (
            mission INTEGER NOT NULL REFERENCES growth_phase_runs(mission),
            phase INTEGER NOT NULL CHECK(phase BETWEEN 1 AND 3),
            nonce TEXT NOT NULL REFERENCES attempts(nonce), catalog_version INTEGER NOT NULL,
            words_json TEXT NOT NULL, load_response_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY(mission,phase))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS growth_phase_catalogs (
        mission INTEGER PRIMARY KEY, catalog_json TEXT NOT NULL)""")
    if run(conn, mission):
        pinned = _run_catalog(conn, mission, catalog_version)
        conn.execute("INSERT OR IGNORE INTO growth_phase_catalogs VALUES (?,?)",
                     (mission, json.dumps(pinned, ensure_ascii=False, sort_keys=True)))
        return pinned
    catalog = growth.expand_saved_catalog(conn, mission, catalog_path, catalog_version)
    conn.execute("INSERT INTO growth_phase_catalogs VALUES (?,?)", (mission,json.dumps(catalog,ensure_ascii=False,sort_keys=True)))
    attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
    frozen = conn.execute("SELECT * FROM growth_snapshots WHERE mission=?", (mission,)).fetchone()
    legacy = bool(frozen or (attempt and attempt["state"] == "complete"))
    # Consume only rewards from this campaign's immediate predecessor. Exact old
    # offer IDs/history survive C1-to-PHC1 conversion.
    for prior in progression.campaign_missions(mission):
        if mission not in progression.next_missions(prior):
            continue
        previous = conn.execute("SELECT nonce FROM attempts WHERE mission=? AND state='complete'", (prior,)).fetchone()
        if previous:
            conn.execute("UPDATE growth_offers SET mission=?,rarity=CASE WHEN kind='curse' THEN ? ELSE rarity END WHERE mission IS NULL AND source LIKE ?",
                         (mission, progression.curse_tier(mission), f"victory:{previous['nonce']}:%"))
    state = growth._state(conn, mission)
    owned, stacks = growth._json(state["talents_json"]), growth._json(state["curses_json"])
    rework_growth.encode(conn,mission,catalog, owned, stacks)
    baseline_ranks=rework_growth.ranks(conn,mission)
    # C1 could already have selected future talents. Keep global ownership and
    # history intact, but remove this mission's selected effects from the fixed
    # baseline. A checkpoint snapshot adds only its completed pairs back.
    mapped = []
    if not legacy:
        for kind in ("talent", "curse"):
            old = conn.execute("SELECT * FROM growth_offers WHERE mission=? AND kind=? ORDER BY sequence", (mission, kind)).fetchall()
            if len(old) > 3:
                raise GrowthError("invalid_growth", "이 임무의 선택권 수를 안전하게 변환할 수 없습니다.")
            for index, offer in enumerate(old, 1):
                mapped.append((offer["offer_id"], mission, index, kind))
                if offer["selected_id"] is not None:
                    identity = offer["selected_id"]
                    if kind == "talent":
                        if identity not in owned:
                            raise GrowthError("invalid_growth", "선택 이력과 보유 재능이 다릅니다.")
                        if next(x for x in catalog['talents'] if x['id']==identity).get('repeatable'):
                            baseline_ranks[identity]=baseline_ranks.get(identity,1)-1
                            if baseline_ranks[identity]==0:
                                del baseline_ranks[identity]
                                owned.remove(identity)
                        else:owned.remove(identity)
                    else:
                        if stacks.get(identity, 0) < 1:
                            raise GrowthError("invalid_growth", "선택 이력과 저주 중첩이 다릅니다.")
                        stacks[identity] -= 1
                        if not stacks[identity]:
                            del stacks[identity]
    conn.execute("INSERT INTO growth_phase_runs VALUES (?,?,1,?,?,?)",
                 (mission, catalog_version, int(legacy), json.dumps(owned), json.dumps(stacks)))
    conn.executemany("INSERT INTO growth_phase_offers VALUES (?,?,?,?)", mapped)
    conn.execute('CREATE TABLE IF NOT EXISTS growth_phase_rank_baselines (mission INTEGER PRIMARY KEY,ranks_json TEXT NOT NULL)')
    conn.execute('INSERT OR IGNORE INTO growth_phase_rank_baselines VALUES (?,?)',(mission,json.dumps(baseline_ranks,sort_keys=True)))
    if not legacy:
        for phase in (1, 2, 3):
            for kind in ("talent", "curse"):
                if conn.execute("SELECT 1 FROM growth_phase_offers WHERE mission=? AND phase=? AND kind=?", (mission, phase, kind)).fetchone():
                    continue
                identity = str(uuid.uuid4())
                conn.execute("INSERT INTO growth_offers (offer_id,source,mission,kind,rarity) VALUES (?,?,?,?,?)",
                             (identity, f"phase:{mission}:{phase}:{kind}", mission, kind, progression.curse_tier(mission) if kind == "curse" else None))
                conn.execute("INSERT INTO growth_phase_offers VALUES (?,?,?,?)", (identity, mission, phase, kind))
    return catalog


def _authorize(conn, mission, phase, nonce):
    validate_phase(phase, nonce)
    row = run(conn, mission)
    if row is None:
        raise GrowthError("growth_not_prepared", "현재 임무의 단계 선택이 준비되지 않았습니다.")
    if phase > 1:
        attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
        if attempt is None or attempt["nonce"] != nonce:
            raise GrowthError("phase_nonce_mismatch", "현재 출전과 단계 선택 ID가 다릅니다.")
        if _completed(conn, row) < phase - 1:
            raise GrowthError("phase_out_of_order", "이전 단계의 재능과 저주 선택을 먼저 마쳐 주세요.")
    return row


def _diverse_curses(conn, mission, offer, eligible, rng):
    """Prefer least-seen options over the previous three same-tier offers."""
    if len(eligible) == 3:
        return eligible
    missions = progression.campaign_missions(mission)
    placeholders = ','.join('?' for _ in missions)
    rows = conn.execute(f'''SELECT candidates_json FROM growth_offers
        WHERE kind='curse' AND rarity=? AND mission IN ({placeholders})
          AND candidates_json IS NOT NULL AND offer_id!=?
        ORDER BY sequence DESC LIMIT 3''',
        (offer['rarity'], *missions, offer['offer_id'])).fetchall()
    recent = [set(item['id'] for item in json.loads(row[0])) for row in rows]
    counts = {item['id']: sum(item['id'] in previous for previous in recent) for item in eligible}
    candidates = []
    for count in sorted(set(counts.values())):
        group = [item for item in eligible if counts[item['id']] == count]
        candidates.extend(rng.sample(group, min(3 - len(candidates), len(group))))
        if len(candidates) == 3:
            break
    if recent and {item['id'] for item in candidates} == recent[0]:
        outside = [item for item in eligible if item not in candidates]
        if outside:
            minimum = min(counts[item['id']] for item in outside)
            candidates[-1] = rng.choice([item for item in outside if counts[item['id']] == minimum])
    return candidates


def _issue(conn, mission, phase, catalog):
    offer = _current(conn, mission, phase)
    if offer is None:
        return
    state = growth._state(conn, mission)
    if rework_growth.enabled(catalog) and phase==3 and progression.metadata(mission)['final']:
        # Preserve issued JSON for history. Already selected rewards stay exact.
        conn.execute('UPDATE growth_offers SET selected_id=?,selected_revision=?,selected_at=CURRENT_TIMESTAMP WHERE offer_id=?',
                     (rework_growth.SKIPPED_FINAL,state['revision'],offer['offer_id']))
        return _issue(conn,mission,phase,catalog)
    if offer["candidates_json"] is not None and rework_growth.enabled(catalog) :
        # Reissue pending offers containing a removed talent, or entirely
        # exhausted pre-cap offers. Archive their exact JSON and UUID first;
        # selected offers and immutable snapshots never enter this branch.
        from .rank_policy import exhausted
        owned=growth._json(state['talents_json']);counts=rework_growth.ranks(conn,mission)
        by_id={x['id']:x for x in catalog['talents']}
        saved=growth._json(offer['candidates_json'])
        has_retired=any(rework_growth.retired(x) for x in saved)
        if saved and (has_retired or (offer['kind']=='talent' and all(exhausted(by_id[x['id']],owned,counts) for x in saved))):
            if has_retired:
                conn.execute('CREATE TABLE IF NOT EXISTS growth_offer_retirement_history (offer_id TEXT PRIMARY KEY,candidates_json TEXT NOT NULL,offered_revision INTEGER)')
                conn.execute('INSERT OR IGNORE INTO growth_offer_retirement_history VALUES (?,?,?)',
                             (offer['offer_id'],offer['candidates_json'],offer['offered_revision']))
            conn.execute('CREATE TABLE IF NOT EXISTS growth_offer_cap_history (offer_id TEXT PRIMARY KEY,candidates_json TEXT NOT NULL,offered_revision INTEGER)')
            conn.execute('INSERT OR IGNORE INTO growth_offer_cap_history VALUES (?,?,?)',
                         (offer['offer_id'],offer['candidates_json'],offer['offered_revision']))
            replacement=str(uuid.uuid4())
            conn.execute('PRAGMA defer_foreign_keys=ON')
            conn.execute('UPDATE growth_offers SET offer_id=?,candidates_json=NULL,offered_revision=NULL WHERE offer_id=?',
                         (replacement,offer['offer_id']))
            conn.execute('UPDATE growth_phase_offers SET offer_id=? WHERE offer_id=?',(replacement,offer['offer_id']))
            offer=_current(conn,mission,phase)
    if offer["candidates_json"] is not None:
        # Preserve C1 UUID and exact candidate order. Only a newly activated
        # pending offer's CAS revision follows intervening phase selections.
        if offer["offered_revision"] != state["revision"]:
            conn.execute("UPDATE growth_offers SET offered_revision=? WHERE offer_id=?", (state["revision"], offer["offer_id"]))
        return
    owned, stacks = growth._json(state["talents_json"]), growth._json(state["curses_json"])
    rework_growth.encode(conn,mission,catalog, owned, stacks)
    kind = offer["kind"]
    if rework_growth.enabled(catalog):
        if kind=='curse' and not rework_growth.has_future_production(mission):
            # A final squad/secret mission cannot ever activate an added wave.
            # Retain held curses and complete this newly issued entitlement as
            # dormant, keeping the talent and victory handshake reachable.
            conn.execute('UPDATE growth_offers SET selected_id=?,selected_revision=?,selected_at=CURRENT_TIMESTAMP WHERE offer_id=?',
                         (rework_growth.SKIPPED_CURSE,state['revision'],offer['offer_id']))
            return _issue(conn,mission,phase,catalog)
        if kind=='talent':
            candidates=rework_growth.candidates(catalog,mission,phase,owned,secrets.SystemRandom(),
                recent_manuals=rework_growth.recent_manuals(conn,mission,offer['offer_id']),
                rank_counts=rework_growth.ranks(conn,mission))
            conn.execute('UPDATE growth_offers SET candidates_json=?,offered_revision=? WHERE offer_id=?',
                         (json.dumps(candidates,ensure_ascii=False,sort_keys=True),state['revision'],offer['offer_id']))
            return
        conn.execute('UPDATE growth_offers SET rarity=? WHERE offer_id=?',(rework_growth.curse_tier(mission,phase),offer['offer_id']))
        offer=_current(conn,mission,phase)
    eligible = [item for item in catalog["talents" if kind == "talent" else "curses"]
                if (rework_growth.curse_eligible(item,mission) if kind=='curse' and rework_growth.enabled(catalog) else progression.item_eligible(item, mission, kind))
                and (not rework_growth.enabled(catalog) or item.get('rework_revision')==5)
                and (kind != 'talent' or talent_ranks.eligible(item, owned, catalog))
                and (kind != "talent" or item["id"] not in owned)
                and (kind != "curse" or (item["rarity"] == offer["rarity"] and stacks.get(item["id"], 0) < item.get('choice_max_stacks',item["max_stacks"])))]
    required = 4 if kind == "talent" else 3
    if len(eligible) < required:
        raise GrowthError("choice_pool_unavailable", f"현재 단계의 구현된 성장 후보가 부족합니다. 임무 {mission}, 단계 {phase}, {kind}, 등급 {offer['rarity']}, 후보 {len(eligible)}개")
    rng = secrets.SystemRandom()
    if kind == "curse":
        candidates = _diverse_curses(conn, mission, offer, eligible, rng)
    else:
        candidates = talent_selection.select_candidates(eligible, mission, rng)
    conn.execute("UPDATE growth_offers SET candidates_json=?,offered_revision=? WHERE offer_id=?",
                 (json.dumps(candidates, ensure_ascii=False, sort_keys=True), state["revision"], offer["offer_id"]))


def _freeze(conn, row, phase, response):
    previous = conn.execute("SELECT * FROM growth_phase_snapshots WHERE mission=? AND phase=?", (row["mission"], phase)).fetchone()
    if previous:
        return validate_growth_words(growth._json(previous["words_json"]))
    if _current(conn, row["mission"], phase):
        raise GrowthError("phase_incomplete", "현재 단계의 선택이 끝나지 않았습니다.")
    catalog = _run_catalog(conn, row["mission"], row["catalog_version"])
    owned, stacks = growth._json(row["baseline_talents_json"]), growth._json(row["baseline_curses_json"])
    saved=conn.execute('SELECT ranks_json FROM growth_phase_rank_baselines WHERE mission=?',(row['mission'],)).fetchone() if conn.execute("SELECT 1 FROM sqlite_master WHERE name='growth_phase_rank_baselines'").fetchone() else None
    ranks=json.loads(saved[0]) if saved else {}
    selected = conn.execute("""SELECT o.kind,o.selected_id,o.candidates_json FROM growth_phase_offers p
        JOIN growth_offers o USING(offer_id) WHERE p.mission=? AND p.phase<=?
        ORDER BY p.phase, p.kind""", (row["mission"], phase)).fetchall()
    if len(selected) != phase * 2 or any(item["selected_id"] is None for item in selected):
        raise GrowthError("phase_incomplete", "이전 단계의 선택 기록이 불완전합니다.")
    for item in selected:
        if item['selected_id'] in (rework_growth.SKIPPED_CURSE,rework_growth.SKIPPED_FINAL):continue
        if item["kind"] == "talent":
            from .legendary_bundles import selected_members
            for identity in selected_members(item,catalog):
                talent=next(x for x in catalog['talents'] if x['id']==identity)
                if talent.get('repeatable'):ranks[identity]=ranks.get(identity,1 if identity in owned else 0)+1
                if identity not in owned:owned.append(identity)
        else:
            stacks[item["selected_id"]] = stacks.get(item["selected_id"], 0) + 1
    words = encode_growth(catalog, owned, stacks,ranks)
    conn.execute("INSERT INTO growth_phase_snapshots (mission,phase,nonce,catalog_version,words_json,load_response_json) VALUES (?,?,?,?,?,?)",
                 (row["mission"], phase, response["nonce"], row["catalog_version"], json.dumps(words), json.dumps(response, sort_keys=True)))
    if phase == 1:
        # Retain the C1 immutable-loadout contract too. Later PHC1 checkpoints
        # are additive snapshots; this row is never overwritten.
        conn.execute("INSERT INTO growth_snapshots (nonce,mission,catalog_version,words_json,load_response_json) VALUES (?,?,?,?,?)",
                     (response["nonce"], row["mission"], row["catalog_version"], json.dumps(words), json.dumps(response, sort_keys=True)))
    return words


def _freeze_ready_pairs(conn, row, make_response):
    """C1 migration may already contain several complete consecutive pairs."""
    for phase in range(_completed(conn, row) + 1, 4):
        if _current(conn, row["mission"], phase):
            break
        _freeze(conn, row, phase, make_response())
        conn.execute("UPDATE growth_phase_runs SET active_phase=? WHERE mission=?", (phase, row["mission"]))


def status(conn, mission=101, requested_phase=None):
    row = run(conn, mission)
    if row is None:
        return growth.status(conn, mission)
    result = growth.status(conn, mission)
    phase = row["active_phase"] if requested_phase is None else requested_phase
    completed = _completed(conn, row)
    current = _current(conn, mission, phase) if phase > completed else None
    attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
    result.update(phased_growth=True, requested_phase=phase, completed_phase=completed, total_phases=3,
                  state="choosing" if current else "in_mission", offer=None)
    result["phase_pending"] = {kind: conn.execute("""SELECT COUNT(*) FROM growth_phase_offers p
        JOIN growth_offers o USING(offer_id) WHERE p.mission=? AND p.phase=?
        AND p.kind=? AND o.selected_id IS NULL""", (mission, phase, kind)).fetchone()[0]
        for kind in ("talent", "curse")}
    if current and current["candidates_json"] is not None:
        result["offer"] = growth._offer(current)
    if attempt and attempt["state"] == "complete":
        result["state"] = "waiting_next_map" if sum(result["upcoming"].values()) else "legacy_complete"
    latest = _latest(conn, mission)
    if latest:
        result["growth_words"] = validate_growth_words(growth._json(latest["words_json"]))
    elif not row["legacy"]:
        result["growth_words"] = encode_growth(_run_catalog(conn, mission), growth._json(row["baseline_talents_json"]), growth._json(row["baseline_curses_json"]))
    return result


def restore(conn, mission, catalog_version, phase, nonce, make_response, catalog_path=None):
    validate_phase(phase, nonce)
    if phase == 1:
        _initialize(conn, mission, catalog_path, catalog_version)
    row = _authorize(conn, mission, phase, nonce)
    growth.upgrade_curse_pool(conn, catalog_path, catalog_version)
    talent_pool.upgrade(conn, growth._saved_catalog(conn, catalog_version), catalog_path, catalog_version)
    catalog = _run_catalog(conn, mission, catalog_version)
    if row["legacy"]:
        response = make_response()
        words = growth.freeze(conn, response, catalog_version, legacy=True)
        return {**response, "growth_words": words, "requested_phase": phase, "completed_phase": 3, "total_phases": 3}
    completed = _completed(conn, row)
    if phase > completed:
        conn.execute("UPDATE growth_phase_runs SET active_phase=? WHERE mission=?", (phase, mission))
        _issue(conn, mission, phase, catalog)
        if _current(conn, mission, phase):
            return status(conn, mission, phase)
        _freeze_ready_pairs(conn, row, make_response)
    response = make_response()
    latest = _latest(conn, mission)
    if latest is None or latest["nonce"] != response["nonce"] or latest["catalog_version"] not in (catalog_version,1 if catalog_version==2 else catalog_version):
        raise GrowthError("snapshot_mismatch", "단계별 출전 성장 정보가 다릅니다.")
    return {**response, "growth_words": validate_growth_words(growth._json(latest["words_json"])),
            "requested_phase": phase, "completed_phase": latest["phase"], "total_phases": 3}


def choose_slot(conn, mission, catalog_version, phase, nonce, offer_id, slot, revision, kind, make_response):
    row = _authorize(conn, mission, phase, nonce)
    try:
        if not isinstance(offer_id, str) or str(uuid.UUID(offer_id)) != offer_id:
            raise ValueError()
    except (ValueError, AttributeError) as exc:
        raise GrowthError("invalid_offer_id", "선택지 ID가 잘못되었습니다.") from exc
    if type(kind) is not int or kind not in (1, 2):
        raise GrowthError("invalid_choice_kind", "선택 종류가 잘못되었습니다.")
    if type(slot) is not int or not 1 <= slot <= (4 if kind == 1 else 3):
        raise GrowthError("invalid_choice_slot", "표시된 후보 번호를 선택해 주세요.")
    if type(revision) is not int or not 0 <= revision <= 0xFFFFFFFF:
        raise GrowthError("invalid_choice_revision", "선택 저장 번호가 잘못되었습니다.")
    catalog = _run_catalog(conn, mission, catalog_version)
    offer = conn.execute("""SELECT o.*,p.phase AS mapped_phase FROM growth_offers o
        JOIN growth_phase_offers p USING(offer_id) WHERE o.offer_id=? AND p.mission=?""", (offer_id, mission)).fetchone()
    if offer is None:
        raise GrowthError("unknown_offer", "현재 임무의 선택지가 아닙니다.")
    if offer["mapped_phase"] != phase:
        raise GrowthError("phase_mismatch", "다른 단계의 선택지입니다.")
    if offer["kind"] != ("talent" if kind == 1 else "curse"):
        raise GrowthError("choice_kind_mismatch", "표시된 선택 종류가 다릅니다.")
    if offer["candidates_json"] is None or offer["offered_revision"] is None:
        raise GrowthError("offer_not_ready", "아직 표시되지 않은 선택지입니다.")
    candidates = growth._json(offer["candidates_json"])
    if (not isinstance(candidates, list) or (len(candidates) not in (1,2,3,4) if kind==1 else len(candidates)!=3)
            or any(not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"] for item in candidates)
            or len({item["id"] for item in candidates}) != len(candidates)):
        raise GrowthError("invalid_growth", "저장된 후보 목록이 잘못되었습니다.")
    if slot>len(candidates):
        raise GrowthError('invalid_choice_slot','표시된 후보 번호를 선택해 주세요.')
    identity = candidates[slot - 1]["id"]
    if offer["selected_id"] is not None:
        if offer["selected_id"] == identity and offer["offered_revision"] == revision:
            return {**status(conn, mission, phase), "duplicate": True}
        raise GrowthError("conflicting_choice", "이미 다른 내용으로 저장한 선택입니다.")
    if row["legacy"] or phase <= _completed(conn, row):
        raise GrowthError("growth_locked", "확정한 단계의 성장은 바꿀 수 없습니다.")
    current = _current(conn, mission, phase)
    state = growth._state(conn, mission)
    if (row["active_phase"] != phase or current is None or current["offer_id"] != offer_id
            or state["revision"] != revision or offer["offered_revision"] != revision):
        raise GrowthError("stale_choice", "현재 게임에 표시된 선택지를 확인해 주세요.")
    owned, stacks = growth._json(state["talents_json"]), growth._json(state["curses_json"])
    if kind == 1:
        rework_growth.acquire_option(conn,mission,catalog,owned,candidates[slot - 1])
    else:
        stacks[identity] = stacks.get(identity, 0) + 1
    rework_growth.encode(conn,mission,catalog, owned, stacks)
    growth._save_state(conn, mission, revision + 1, owned, stacks)
    conn.execute("UPDATE growth_offers SET selected_id=?,selected_revision=?,selected_at=CURRENT_TIMESTAMP WHERE offer_id=?", (identity, revision + 1, offer_id))
    _issue(conn, mission, phase, catalog)
    if _current(conn, mission, phase) is None:
        _freeze_ready_pairs(conn, row, make_response)
    return {**status(conn, mission, phase), "duplicate": False}


def check_completion(conn, mission):
    row = run(conn, mission)
    if row and _completed(conn, row) != 3:
        raise GrowthError("phase_incomplete", "클리어 직전의 재능과 저주 선택을 먼저 마쳐 주세요.")


def award_completion(conn, nonce):
    if not exists(conn):
        return False
    row = conn.execute("SELECT p.* FROM growth_phase_runs p JOIN attempts a USING(mission) WHERE a.nonce=?", (nonce,)).fetchone()
    if row is None:
        return False
    snapshot = conn.execute("SELECT * FROM growth_snapshots WHERE nonce=? AND legacy=0", (nonce,)).fetchone()
    if snapshot is not None:
        inserted = conn.execute("INSERT OR IGNORE INTO growth_rewards (nonce,talent_choices,curse_choices) VALUES (?,?,?)", (nonce, *([3,3] if progression.next_missions(row["mission"]) else [0,0]))).rowcount
        if inserted and progression.next_missions(row["mission"]):
            growth._add_offers(conn, f"victory:{nonce}", None, 3, 3)
    return True
