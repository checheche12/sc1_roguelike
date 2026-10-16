"""Durable, separate original-campaign and persistence-probe records.

The SQLite transaction is the acknowledgement boundary: methods return only
after COMMIT succeeds. A failed/uncertain call can safely be retried with the
same attempt nonce and payload. No game process is accessed here.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path
import secrets
import sqlite3
from typing import Any
import uuid

from sc1.campaign.catalog import (MISSIONS, ORIGINAL_PROFILE, PROFILE_NAMES,
                                  PROBE_PROFILE, Mission, missions_for_profile)
from sc1.campaign import growth, phased_growth, rework_growth
from sc1.campaign.progression import metadata
from sc1.campaign.missions import load_missions
from sc1.campaign.growth import GrowthChoicesPending
from sc1.campaign.runtime_catalog import GrowthError

PROTOCOL_VERSION = 1
SCHEMA_VERSION = 1
PROBE_REWARDS = {mission.mission_id: mission.reward for mission in missions_for_profile(PROBE_PROFILE)}


class ProtocolError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _integer(value: Any, field: str) -> int:
    if type(value) is not int or not 0 <= value <= 0xFFFFFFFF:
        raise ProtocolError("invalid_value", f"{field} must be an unsigned 32-bit integer")
    return value


class CampaignStore:
    """One profile per database, safe across manager restarts.

    Separate store instances/processes serialize writes through SQLite. This
    prototype does not invent defeat/abandonment or final class-balance rules.
    Reopening an unfinished probe keeps its nonce and original snapshot.
    """

    def __init__(self, db_path: str | Path, *, new_profile: str = PROBE_PROFILE,
                 runtime_catalog_path: str | Path | None = None):
        if new_profile not in PROFILE_NAMES:
            raise ProtocolError("unknown_profile", "Unknown record profile")
        self.path = Path(db_path).resolve()
        self.runtime_catalog_path = runtime_catalog_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.profile = self._initialize(new_profile)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = FULL")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _initialize(self, new_profile: str) -> str:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if tables:
                if "metadata" not in tables:
                    raise ProtocolError("schema_version", "This is not an SC1 campaign database")
                version = conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()
                if version is None or version[0] != str(SCHEMA_VERSION):
                    raise ProtocolError("schema_version", "Unsupported database version; file was not migrated")
                required = {"metadata", "campaign", "attempts", "results"}
                if not required.issubset(tables):
                    raise ProtocolError("invalid_database", "Campaign database is incomplete")
                stored_profile = conn.execute("SELECT value FROM metadata WHERE key='profile'").fetchone()
                # Schema 1 predates profiles. Preserve those files verbatim and
                # interpret them as probes; never turn probe rewards into a
                # production campaign balance just because a new UI opens it.
                profile = stored_profile[0] if stored_profile else PROBE_PROFILE
                if profile not in PROFILE_NAMES:
                    raise ProtocolError("unknown_profile", "Unsupported database profile; file was not migrated")
                conn.commit()
                return profile
            conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            conn.execute("INSERT INTO metadata VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
            conn.execute("INSERT INTO metadata VALUES ('profile', ?)", (new_profile,))
            conn.execute("""CREATE TABLE campaign (
                id INTEGER PRIMARY KEY CHECK(id=1), gold INTEGER NOT NULL CHECK(gold>=0),
                revision INTEGER NOT NULL CHECK(revision>=0), completed_mask INTEGER NOT NULL,
                growth_json TEXT NOT NULL)""")
            sample_growth = {"class": None, "unlocked_units": [], "roster": [], "perks": [], "curses": [], "rest_counts": {}}
            conn.execute("INSERT INTO campaign VALUES (1,0,0,0,?)", (json.dumps(sample_growth),))
            conn.execute("""CREATE TABLE attempts (
                nonce TEXT PRIMARY KEY, mission INTEGER NOT NULL UNIQUE,
                protocol_version INTEGER NOT NULL, start_gold INTEGER NOT NULL,
                start_revision INTEGER NOT NULL, state TEXT NOT NULL CHECK(state IN ('active','complete')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            conn.execute("""CREATE TABLE results (
                nonce TEXT PRIMARY KEY REFERENCES attempts(nonce), request_json TEXT NOT NULL,
                response_json TEXT NOT NULL, committed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)""")
            conn.commit()
            return new_profile

    def _validate_request(self, mission: int, protocol_version: int) -> Mission:
        if type(protocol_version) is not int or protocol_version != PROTOCOL_VERSION:
            raise ProtocolError("protocol_version", "Map/manager protocol versions differ")
        entry = MISSIONS.get(_integer(mission, "mission"))
        if entry is None:
            raise ProtocolError("unknown_mission", "This mission is not registered in the campaign catalog")
        if entry.profile != self.profile:
            raise ProtocolError("profile_mismatch", f"Mission {mission} requires '{entry.profile}' records; this file is '{self.profile}'")
        if entry.profile == ORIGINAL_PROFILE:
            canonical = metadata(mission).get("shared_reward_mission_id", mission)
            return MISSIONS[canonical]
        return entry

    @staticmethod
    def _snapshot(row: sqlite3.Row) -> dict:
        return {"protocol_version": PROTOCOL_VERSION, "gold": row["gold"],
                "revision": row["revision"], "completed_mask": row["completed_mask"]}

    def status(self) -> dict:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM campaign WHERE id=1").fetchone()
            result = self._snapshot(row)
            result["growth"] = json.loads(row["growth_json"])
            result["attempts"] = [dict(r) for r in conn.execute("SELECT * FROM attempts ORDER BY mission")]
            result["database"] = str(self.path)
            result["profile"] = self.profile
            result["sample_only"] = self.profile == PROBE_PROFILE
            result["supported_missions"] = [mission.mission_id for mission in missions_for_profile(self.profile)]
            result["growth_selection"] = (phased_growth.status(conn, self._latest_growth_mission(conn)) if self.profile == ORIGINAL_PROFILE
                                          else {"state": "unsupported"})
            return result

    @staticmethod
    def _latest_growth_mission(conn, campaign_id=None):
        candidates=[m['mission_id'] for m in load_missions()
                    if campaign_id is None or m['campaign_id']==campaign_id]
        if growth.exists(conn):
            for row in conn.execute("SELECT mission FROM growth_offers WHERE mission IS NOT NULL ORDER BY COALESCE(selected_at,created_at) DESC,sequence DESC"):
                if row[0] in candidates:return row[0]
        return candidates[0] if candidates else 101

    def growth_status_for_campaign(self, campaign_id: int) -> dict:
        if type(campaign_id) is not int or campaign_id not in {m['campaign_id'] for m in load_missions()}:
            raise GrowthError('growth_campaign_unsupported','등록된 캠페인이 아닙니다.')
        with self._connect() as conn:
            mission=self._latest_growth_mission(conn,campaign_id)
            self._validate_request(mission,PROTOCOL_VERSION)
            return phased_growth.status(conn,mission)

    def growth_status(self, mission: int | None = None) -> dict:
        """Read selection state without creating or migrating any tables."""
        with self._connect() as conn:
            mission = self._latest_growth_mission(conn) if mission is None else mission
            entry = self._validate_request(mission, PROTOCOL_VERSION)
            return phased_growth.status(conn, entry.mission_id)

    @staticmethod
    def _require_unphased(conn, mission):
        if phased_growth.run(conn, mission):
            raise GrowthError("phased_protocol_required", "이 기록은 단계별 성장 선택을 지원하는 지도로 불러와 주세요.")

    def restore_growth_phase(self, mission: int, catalog_version: int, phase: int, *,
                             nonce: str | None = None) -> dict:
        """Opt into PHC1; persist only this checkpoint's displayed candidates."""
        entry = self._validate_growth(mission, catalog_version,allow_rework=True)
        mission = entry.mission_id
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._check_mission_access(conn, entry)
            if catalog_version==2:
                rework_growth.enable(conn,self.runtime_catalog_path)
            response = phased_growth.restore(conn, mission, catalog_version, phase, nonce,
                lambda: self._restore_response(conn, entry, PROTOCOL_VERSION), self.runtime_catalog_path)
            conn.commit()
        if response.get("state") == "choosing":
            raise GrowthChoicesPending("게임 안에서 현재 단계의 재능 1개와 저주 1개를 선택해 주세요.", state=response)
        return response

    def choose_growth_phase_slot(self, offer_id: str, choice_slot: int, expected_revision: int,
                                 mission: int = 101, catalog_version: int = 1, *,
                                 choice_kind: int, phase: int, nonce: str | None = None) -> dict:
        """Resolve one persisted slot and freeze a completed pair atomically."""
        entry = self._validate_growth(mission, catalog_version,allow_rework=True)
        mission = entry.mission_id
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            response = phased_growth.choose_slot(conn, mission, catalog_version, phase, nonce,
                offer_id, choice_slot, expected_revision, choice_kind,
                lambda: self._restore_response(conn, entry, PROTOCOL_VERSION))
            conn.commit()
        return response

    def _validate_growth(self, mission: int, catalog_version: int, protocol_version: int = PROTOCOL_VERSION, *,allow_rework=False):
        entry = self._validate_request(mission, protocol_version)
        if entry.profile != ORIGINAL_PROFILE:
            raise GrowthError("growth_mission_unsupported", "등록된 본편 임무에서만 성장 선택을 지원합니다.")
        if type(catalog_version) is not int or catalog_version not in ((1,2) if allow_rework else (1,)):
            raise GrowthError("catalog_version", "지원하지 않는 성장 목록 버전입니다.")
        return entry

    def prepare_growth(self, mission: int = 101, catalog_version: int = 1) -> dict:
        """Persist initial rights/current offer, or read a frozen/completed record."""
        mission = self._validate_growth(mission, catalog_version).mission_id
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._require_unphased(conn, mission)
            result = growth.prepare(conn, mission, self.runtime_catalog_path, catalog_version)
            conn.commit()
            return result

    def choose_growth(self, offer_id: str, candidate_id: str, expected_revision: int,
                      mission: int = 101, catalog_version: int = 1) -> dict:
        """Compare-and-set one selection; identical lost-ACK retries are safe."""
        mission = self._validate_growth(mission, catalog_version).mission_id
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._require_unphased(conn, mission)
            result = growth.choose(conn, mission, offer_id, candidate_id, expected_revision,
                                   self.runtime_catalog_path, catalog_version)
            conn.commit()
            return result

    def choose_growth_slot(self, offer_id: str, choice_slot: int, expected_revision: int,
                           mission: int = 101, catalog_version: int = 1, *,
                           choice_kind: int) -> dict:
        """Resolve a game's 1-based slot against its durable offer atomically.

        The map sends no candidate identity. Slot resolution and selection share
        one write transaction, including idempotent retries of a selected offer.
        This endpoint never prepares a missing offer or migrates an old record.
        """
        mission = self._validate_growth(mission, catalog_version).mission_id
        try:
            if not isinstance(offer_id, str) or str(uuid.UUID(offer_id)) != offer_id:
                raise ValueError("noncanonical offer UUID")
        except (ValueError, AttributeError) as exc:
            raise GrowthError("invalid_offer_id", "선택지 ID가 잘못되었습니다.") from exc
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._require_unphased(conn, mission)
            if not growth.exists(conn):
                raise GrowthError("growth_not_prepared", "게임에서 선택지가 표시될 때까지 기다려 주세요.")
            row = conn.execute("SELECT * FROM growth_offers WHERE offer_id=?", (offer_id,)).fetchone()
            if row is None or row["mission"] != mission:
                raise GrowthError("unknown_offer", "현재 임무의 선택지가 아닙니다.")
            if type(choice_kind) is not int or choice_kind not in (1, 2):
                raise GrowthError("invalid_choice_kind", "선택 종류가 잘못되었습니다.")
            kind = "talent" if choice_kind == 1 else "curse"
            if row["kind"] != kind:
                raise GrowthError("choice_kind_mismatch", "표시된 선택지와 선택 종류가 다릅니다.")
            if type(choice_slot) is not int or not 1 <= choice_slot <= (4 if kind == "talent" else 3):
                raise GrowthError("invalid_choice_slot", "표시된 후보 번호를 선택해 주세요.")
            if type(expected_revision) is not int or not 0 <= expected_revision <= 0xFFFFFFFF:
                raise GrowthError("invalid_choice_revision", "선택 저장 번호가 잘못되었습니다.")
            if row["candidates_json"] is None or row["offered_revision"] is None:
                raise GrowthError("offer_not_ready", "아직 게임에 표시할 준비가 되지 않은 선택지입니다.")
            if row["offered_revision"] != expected_revision:
                raise GrowthError("stale_choice", "선택 기록이 바뀌었습니다. 게임의 현재 선택지를 다시 확인해 주세요.")
            try:
                candidates = json.loads(row["candidates_json"])
            except (TypeError, ValueError) as exc:
                raise GrowthError("invalid_growth", "저장된 후보 목록을 읽을 수 없습니다.") from exc
            if (not isinstance(candidates, list) or len(candidates) != (4 if kind == "talent" else 3)
                    or any(not isinstance(item, dict) or not isinstance(item.get("id"), str)
                           or not item["id"] for item in candidates)
                    or len({item["id"] for item in candidates}) != len(candidates)):
                raise GrowthError("invalid_growth", "저장된 후보 목록의 형식이 잘못되었습니다.")
            candidate_id = candidates[choice_slot - 1]["id"]
            result = growth.choose(conn, mission, offer_id, candidate_id, expected_revision,
                                   self.runtime_catalog_path, catalog_version)
            conn.commit()
            return result

    def restore_growth(self, mission: int, catalog_version: int = 1, *,
                       protocol_version: int = PROTOCOL_VERSION) -> dict:
        """Freeze a loadout before ACK; a pending offer is a recoverable wait.

        Old completed records replay with no invented talents. The original
        campaign, attempt nonce, and completion receipt remain unchanged.
        """
        entry = self._validate_growth(mission, catalog_version, protocol_version)
        mission = entry.mission_id
        pending = None
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._require_unphased(conn, mission)
            growth.initialize(conn, self.runtime_catalog_path, catalog_version)
            attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
            completed = bool(attempt and attempt["state"] == "complete")
            if not completed:
                choices = growth.prepare(conn, mission, self.runtime_catalog_path, catalog_version)
                if choices["state"] == "choosing":
                    pending = choices
            if pending is None:
                response = self._restore_response(conn, entry, protocol_version)
                response["growth_words"] = growth.freeze(conn, response, catalog_version, legacy=completed)
            # Persist pending candidates too. Raising inside the transaction
            # would roll them back and let reconnects reroll the offer.
            conn.commit()
        if pending is not None:
            raise GrowthChoicesPending(state=pending)
        return response

    def restore(self, mission: int, protocol_version: int = PROTOCOL_VERSION) -> dict:
        entry = self._validate_request(mission, protocol_version)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            response = self._restore_response(conn, entry, protocol_version)
            conn.commit()
        return response

    @staticmethod
    def _campaign_advanced(conn, mission, start_revision):
        # Other campaigns share a database but must not invalidate a paused run.
        key = metadata(mission)["campaign_id"]
        for row in conn.execute("SELECT a.mission,r.response_json FROM results r JOIN attempts a USING(nonce)"):
            if metadata(row["mission"])["campaign_id"] == key and json.loads(row["response_json"])["revision"] > start_revision:
                return True
        return False

    def _check_mission_access(self, conn, entry):
        """Reject locked LOAD before issuing any candidates or migration rows."""
        state = conn.execute("SELECT * FROM campaign WHERE id=1").fetchone()
        if state["completed_mask"] & entry.required_mask != entry.required_mask:
            raise ProtocolError("mission_locked", "Complete the preceding mission before loading this map")
        attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (entry.mission_id,)).fetchone()
        if attempt and attempt["state"] != "complete" and (self._campaign_advanced(conn, entry.mission_id, attempt["start_revision"]) if entry.profile == ORIGINAL_PROFILE else attempt["start_revision"] != state["revision"]):
            raise ProtocolError("stale_attempt", "Campaign changed after this attempt was issued")

    def _restore_response(self, conn, entry, protocol_version):
        mission = entry.mission_id
        state = conn.execute("SELECT * FROM campaign WHERE id=1").fetchone()
        attempt = conn.execute("SELECT * FROM attempts WHERE mission=?", (mission,)).fetchone()
        if attempt and attempt["state"] == "complete":
            if not entry.allow_completed_replay:
                raise ProtocolError("mission_complete", "This probe is already complete; use the next map or a new probe database")
            if not state["completed_mask"] & entry.completion_mask:
                raise ProtocolError("invalid_database", "Completed attempt is missing its completion record")
            return {**self._snapshot(state), "nonce": attempt["nonce"], "mission": mission,
                    "duplicate": False, "already_completed": True}
        if state["completed_mask"] & entry.required_mask != entry.required_mask:
            raise ProtocolError("mission_locked", "Complete the preceding mission before loading this map")
        if attempt is None:
            nonce = secrets.token_hex(16)
            conn.execute("""INSERT INTO attempts
                (nonce,mission,protocol_version,start_gold,start_revision,state)
                VALUES (?,?,?,?,?,'active')""", (nonce, mission, protocol_version, state["gold"], state["revision"]))
        else:
            nonce = attempt["nonce"]
            if (self._campaign_advanced(conn, mission, attempt["start_revision"]) if entry.profile == ORIGINAL_PROFILE else attempt["start_revision"] != state["revision"]):
                raise ProtocolError("stale_attempt", "Campaign changed after this attempt was issued")
        return {**self._snapshot(state), "nonce": nonce, "mission": mission, "duplicate": False}

    def complete(self, mission: int, nonce: str, gold_delta: int,
                 observed_gold: int, protocol_version: int = PROTOCOL_VERSION) -> dict:
        entry = self._validate_request(mission, protocol_version)
        mission = entry.mission_id
        _integer(gold_delta, "gold_delta")
        _integer(observed_gold, "observed_gold")
        if not isinstance(nonce, str) or len(nonce) != 32 or any(c not in "0123456789abcdef" for c in nonce):
            raise ProtocolError("invalid_nonce", "Attempt nonce must be 32 lowercase hexadecimal characters")
        request = json.dumps({"protocol_version": protocol_version, "mission": mission,
                              "nonce": nonce, "gold_delta": gold_delta, "observed_gold": observed_gold}, sort_keys=True)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            previous = conn.execute("SELECT * FROM results WHERE nonce=?", (nonce,)).fetchone()
            if previous:
                if previous["request_json"] != request:
                    raise ProtocolError("conflicting_duplicate", "The same attempt was submitted with different result data")
                response = json.loads(previous["response_json"])
                response["duplicate"] = True
                conn.commit()
                return response
            phased_growth.check_completion(conn, mission)
            attempt = conn.execute("SELECT * FROM attempts WHERE nonce=?", (nonce,)).fetchone()
            if not attempt or attempt["state"] != "active":
                raise ProtocolError("unknown_attempt", "No active attempt matches this result")
            if attempt["mission"] != mission or attempt["protocol_version"] != protocol_version:
                raise ProtocolError("attempt_mismatch", "Result belongs to another mission or protocol")
            if gold_delta != entry.reward:
                raise ProtocolError("invalid_reward", "Unexpected reward for this mission")
            if observed_gold != attempt["start_gold"]:
                raise ProtocolError("snapshot_mismatch", "Map did not report the issued starting gold")
            state = conn.execute("SELECT * FROM campaign WHERE id=1").fetchone()
            if ((self._campaign_advanced(conn, mission, attempt["start_revision"]) if entry.profile == ORIGINAL_PROFILE else state["revision"] != attempt["start_revision"]) or state["gold"] != attempt["start_gold"]):
                raise ProtocolError("stale_attempt", "Campaign changed after this attempt was issued")
            gold = _integer(state["gold"] + gold_delta, "result_gold")
            revision = _integer(state["revision"] + 1, "result_revision")
            mask = state["completed_mask"] | entry.completion_mask
            response = {"protocol_version": PROTOCOL_VERSION, "mission": mission, "nonce": nonce,
                        "gold": gold, "revision": revision, "completed_mask": mask, "duplicate": False}
            conn.execute("UPDATE campaign SET gold=?,revision=?,completed_mask=? WHERE id=1", (gold, revision, mask))
            conn.execute("UPDATE attempts SET state='complete' WHERE nonce=?", (nonce,))
            conn.execute("INSERT INTO results (nonce,request_json,response_json) VALUES (?,?,?)",
                         (nonce, request, json.dumps(response, sort_keys=True)))
            if not phased_growth.award_completion(conn, nonce):
                growth.award_completion(conn, nonce)
            self._commit_result(conn)
        return response

    def _commit_result(self, conn: sqlite3.Connection) -> None:
        """Seam used by the failure-injection test; never acknowledge above this boundary."""
        conn.commit()


def open_campaign_store(db_path: str | Path, *, new_profile: str = ORIGINAL_PROFILE,
                        runtime_catalog_path: str | Path | None = None) -> CampaignStore:
    """Open an existing profile unchanged; new application records are original.

    CampaignStore's default remains probe for existing integrations/tests. All
    application entry points use this factory so a newly named file has an
    explicit original profile while legacy probe files remain probe records.
    """
    return CampaignStore(db_path, new_profile=new_profile, runtime_catalog_path=runtime_catalog_path)
