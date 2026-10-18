"""Version 1 binary protocol shared by registered campaign and probe maps.

The map owns words 0..31; the manager owns words 32..42 in legacy maps.
Maps explicitly advertising GRW1/catalog1 grant response words 32..63. Each writer
publishes odd sequence, payload, then even nonzero sequence. The heartbeat is
independent and must keep advancing before any external write is permitted.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct
import time
import uuid
from typing import Protocol

from sc1.campaign.catalog import MISSIONS

MAGIC = b"SC1CAMP-PROBE-V1"  # Exactly 16 bytes; no trailing NUL.
VERSION = 1
MAILBOX_SIZE = 256
REQUEST_SEQUENCE = 8
RESPONSE_SEQUENCE = 32
RESPONSE_END = 43
GROWTH_MAGIC = 0x47525731
GROWTH_VERSION = 1
GROWTH_RESPONSE_END = 64
GROWTH_V2_RESPONSE_END = 128
CHOICE_MAGIC = 0x43484331
CHOICE_VERSION = 1
PHASE_MAGIC = 0x50484331
PHASE_VERSION = 1
PHASE_ACK_PREFIX = 0x50480000
# The transport holds DWORD values, but the mailbox itself may live above 4 GiB.
# The Windows adapter applies the tighter target/system address-space bound.
MAX_ADDRESS = 0x0000_8000_0000_0000
WORDS = struct.Struct("<64I")
U32 = struct.Struct("<I")


class BridgeError(RuntimeError):
    pass


class RequestRejected(BridgeError):
    """A durable store rejection has already been delivered to this map."""
    def __init__(self, code, message):
        self.code = code
        super().__init__(f"Manager rejected request ({code}): {message}")


class UnstableMailbox(BridgeError):
    pass


class Memory(Protocol):
    def read(self, address: int, size: int) -> bytes: ...
    def write(self, address: int, data: bytes) -> None: ...


class Store(Protocol):
    def restore(self, mission: int) -> dict: ...
    def complete(self, mission: int, nonce: str, gold_delta: int,
                 observed_gold: int) -> dict: ...


def validate_header(data: bytes, address: int) -> tuple[int, ...]:
    if address < 0x10000 or address % 4 or address + MAILBOX_SIZE > MAX_ADDRESS:
        raise BridgeError("Mailbox is outside aligned user memory bounds")
    if len(data) != MAILBOX_SIZE:
        raise BridgeError("Short mailbox read")
    words = WORDS.unpack(data)
    if data[:16] != MAGIC or words[4] != VERSION:
        raise BridgeError("Mailbox signature or protocol version changed")
    if words[16] not in (64,128):
        raise BridgeError("Mailbox length marker must be 64 or version-two 128 DWORDs")
    if (words[16]==128)!=(words[17]==GROWTH_MAGIC and words[18]==2):
        raise BridgeError('Extended mailbox requires explicit growth version two')
    if words[5] not in MISSIONS or words[7] not in (1, 2, 3, 4, 5):
        raise BridgeError("Mailbox mission/state is not registered in the campaign catalog")
    growth_version(words)
    choice_version(words)
    phase_version(words)
    return words


def growth_version(words: tuple[int, ...]) -> int:
    """Opt in only with the exact marker, version, and original-campaign map."""
    if words[17] == 0:
        return 0
    if (words[17] != GROWTH_MAGIC or words[18] not in (1,2) or words[19] not in (0, words[18])
            or MISSIONS[words[5]].profile != "original"):
        raise BridgeError("Unsupported growth mailbox capability or catalog version")
    return words[18]


def choice_version(words: tuple[int, ...]) -> int:
    if words[20] == 0:
        return 0
    if words[20] != CHOICE_MAGIC or words[21] != CHOICE_VERSION or not growth_version(words):
        raise BridgeError("Unsupported in-game choice mailbox capability")
    return words[21]


def phase_version(words: tuple[int, ...]) -> int:
    if words[29] == 0:
        if words[30] or words[31]:
            raise BridgeError("Incomplete phased growth mailbox capability")
        return 0
    if (words[29] != PHASE_MAGIC or words[30] not in (1,2) or words[31] not in range(1,5 if words[30]==2 else 4)
            or (words[30]==2 and growth_version(words)!=2)
            or not choice_version(words) or MISSIONS[words[5]].profile != "original"):
        raise BridgeError("Unsupported phased growth mailbox capability")
    return words[30]


@dataclass(frozen=True)
class Request:
    mission: int
    heartbeat: int
    state: int
    sequence: int
    operation: int
    nonce: str
    gold_delta: int
    observed_gold: int
    growth_version: int = 0
    growth_applied: int = 0
    choice_version: int = 0
    choice_slot: int = 0
    choice_token: str = "00" * 16
    choice_revision: int = 0
    choice_kind: int = 0
    phase_version: int = 0
    phase: int = 0

    @property
    def identity(self) -> tuple:
        # Heartbeat can change independently while the request is outstanding.
        return (self.mission, self.state, self.sequence, self.operation,
                self.nonce, self.gold_delta, self.observed_gold, self.growth_version, self.growth_applied,
                self.choice_version, self.choice_slot, self.choice_token, self.choice_revision, self.choice_kind,
                self.phase_version, self.phase)


def read_request(memory: Memory, address: int) -> Request:
    before = U32.unpack(memory.read(address + REQUEST_SEQUENCE * 4, 4))[0]
    if not before or before & 1:
        raise UnstableMailbox("Map has not committed a request")
    words = validate_header(memory.read(address, MAILBOX_SIZE), address)
    after = U32.unpack(memory.read(address + REQUEST_SEQUENCE * 4, 4))[0]
    if before != after or before != words[REQUEST_SEQUENCE] or after & 1:
        raise UnstableMailbox("Map request changed during read")
    choices = choice_version(words)
    return Request(words[5], words[6], words[7], words[8], words[9],
                   struct.pack("<4I", *words[10:14]).hex(), words[14], words[15],
                   growth_version(words), words[19] if growth_version(words) else 0,
                   choices, words[22] if choices else 0,
                   struct.pack("<4I", *words[23:27]).hex() if choices else "00" * 16,
                   words[27] if choices else 0, words[28] if choices else 0,
                   phase_version(words), words[31] if phase_version(words) else 0)


def checked_word(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
        raise BridgeError(f"Manager returned an invalid DWORD for {field}")
    return value


def phase_result(request: Request, result: dict, *, offer: bool = False) -> int:
    if (not request.phase_version or type(result.get("requested_phase")) is not int
            or result.get("requested_phase") != request.phase or type(result.get("total_phases")) is not int
            or result.get("total_phases") != (4 if request.phase_version==2 else 3)
            or type(result.get("completed_phase")) is not int):
        raise BridgeError("Manager returned mismatched phased growth metadata")
    completed = result["completed_phase"]
    if not 0 <= completed <= (4 if request.phase_version==2 else 3) or (offer and completed != request.phase - 1) or (not offer and completed < request.phase):
        raise BridgeError("Manager returned an invalid phased growth checkpoint")
    return completed


def response_payload(request: Request, result: dict, status: int) -> bytes:
    try:
        nonce = bytes.fromhex(result["nonce"])
    except (ValueError, TypeError, KeyError) as exc:
        raise BridgeError("Manager returned an invalid nonce") from exc
    if len(nonce) != 16 or nonce == bytes(16):
        raise BridgeError("Manager nonce must be 16 nonzero bytes")
    values = [status, request.sequence, checked_word(result["gold"], "gold"),
              *struct.unpack("<4I", nonce),
              checked_word(result["revision"], "revision"),
              (1 if result["completed_mask"] & MISSIONS[request.mission].completion_mask else 0) if request.growth_version
              else checked_word(result["completed_mask"], "completed_mask"), 0]
    if request.operation == 2 and nonce.hex() != request.nonce:
        raise BridgeError("Manager completion nonce does not match map request")
    if request.phase_version and status == 1:
        completed = phase_result(request, result)
        if request.phase > 1 and (nonce.hex() != request.nonce or values[2] != request.observed_gold):
            raise BridgeError("Phase snapshot changed the issued attempt identity")
        values[9] = PHASE_ACK_PREFIX | completed << 8 | request.phase
    if request.growth_version:
        # Only LOAD consumes a new growth snapshot. Completion ACKs carry a
        # canonical empty extension and cannot grant or reapply effects.
        growth = result.get("growth_words") if status == 1 else [request.growth_version] + [0] * (64 if request.growth_version==2 else 20)
        if request.growth_version==2 and status==1:
            from sc1.campaign.runtime_catalog import upgrade_growth_words, GrowthError
            try:growth=upgrade_growth_words(growth)
            except GrowthError as exc:raise BridgeError(str(exc)) from exc
        if not isinstance(growth, (list, tuple)) or len(growth) != (65 if request.growth_version==2 else 21):
            raise BridgeError("Growth response has an invalid versioned length")
        growth = [checked_word(value, f"growth[{index}]") for index, value in enumerate(growth)]
        if growth[0] != request.growth_version:
            raise BridgeError("Growth response catalog version differs from map")
        values.extend(growth)
        if request.growth_version==2:values.extend([0]*(95-len(values)))
    return struct.pack(f"<{len(values)}I", *values)


def choice_payload(request: Request, state: dict) -> bytes:
    """Multiplex a saved offer into the existing 21-word growth extension.

    Map text is compiled from the frozen catalog; this transfers numeric IDs
    and a persisted offer UUID only, never external strings or trigger code.
    """
    if not request.choice_version or not isinstance(state, dict) or state.get("state") != "choosing":
        raise BridgeError("No persisted in-game choice is available")
    offer = state.get("offer")
    if not isinstance(offer, dict) or offer.get("kind") not in ("talent", "curse"):
        raise BridgeError("Manager returned an invalid choice offer")
    kind = 1 if offer["kind"] == "talent" else 2
    candidates = offer.get("candidates")
    required = len(candidates) if isinstance(candidates,list) else 0
    if (kind==1 and required not in ((1,2,3,4) if request.growth_version==2 else (4,))) or (kind==2 and (required not in (1,2,3) if request.phase_version==2 else required!=3)):
        raise BridgeError("Manager choice has the wrong candidate count")
    try:
        token = uuid.UUID(offer["offer_id"]).bytes
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise BridgeError("Manager choice has an invalid offer UUID") from exc
    if token == bytes(16):
        raise BridgeError("Manager choice UUID is zero")
    if not all(isinstance(item, dict) for item in candidates):
        raise BridgeError("Manager choice has an invalid candidate")
    indices = [checked_word(item.get("bit_index" if kind == 1 else "byte_index"), "candidate_index") + 1
               for item in candidates]
    if len(set(indices)) != required or any(index > (512 if kind == 1 else (64 if request.growth_version==2 else 16)) for index in indices):
        raise BridgeError("Choice candidate is not supported by this map catalog")
    counts = [0] * (64 if request.growth_version==2 else 16)
    for item in state.get("curses", []):
        index, count = item["byte_index"], item["stacks"]
        if type(index) is not int or not 0 <= index < len(counts) or type(count) is not int or not 0 <= count <= 255:
            raise BridgeError("Manager returned an invalid owned curse count")
        counts[index] = count
    pending = state.get("phase_pending") if request.phase_version else state["pending"]
    if not isinstance(pending, dict):
        raise BridgeError("Manager returned no pending checkpoint choices")
    if request.phase_version and (pending.get("talent") not in (0, 1) or pending.get("curse") not in ((0,1) if request.growth_version==2 else (1,))):
        raise BridgeError("Manager returned invalid pending checkpoint choices")
    extension = [request.growth_version, kind, checked_word(offer["revision"], "offer_revision"), required,
                 *indices, *([0] * (4-required)), *struct.unpack("<4I", token),
                 checked_word(pending["talent"], "pending_talents"),
                 checked_word(pending["curse"], "pending_curses"),
                 sum(counts[item["byte_index"]] << (8*i) for i, item in enumerate(candidates)) if kind == 2 else 0, *([0] * 6)]
    assert len(extension) == 21
    if request.phase_version:
        completed = phase_result(request, state, offer=True)
        extension[15:] = [PHASE_MAGIC, request.phase_version, request.phase, completed, 4 if request.phase_version==2 else 3, 0]
    payload=[4, request.sequence, *([0] * 8), *extension]
    if request.growth_version==2:payload.extend([0]*(95-len(payload)))
    if request.growth_version==2 and kind==1:
        from sc1.campaign.legendary_bundles import member_ids
        from sc1.campaign.runtime_catalog import load_catalog
        catalog=load_catalog(expected_version=2)
        by_id={item['id']:item for item in catalog['talents']}
        partners=[0]*4
        for i,item in enumerate(candidates):
            members=member_ids(item,catalog)
            if len(members)==2:partners[i]=by_id[members[1]]['bit_index']+1
        if any(partners):payload[31:36]=[*partners,0x424E4431]
    return struct.pack(f"<{len(payload)}I",*payload)


def publish_response(memory: Memory, address: int, request: Request, payload: bytes) -> None:
    expected = 380 if request.growth_version==2 else 124 if request.growth_version else 40
    is_error = len(payload) == 40 and U32.unpack_from(payload)[0] == 3
    if len(payload) != expected and not is_error:
        raise BridgeError("Response payload length differs from advertised mailbox capability")
    if read_request(memory, address).identity != request.identity:
        raise UnstableMailbox("Map request changed while the manager saved")
    previous = U32.unpack(memory.read(address + RESPONSE_SEQUENCE * 4, 4))[0]
    # Recover safely if an earlier publisher stopped on an odd sequence.
    committed = ((previous | 1) + 1) & 0xFFFFFFFF
    if committed == 0:
        committed = 2
    memory.write(address + RESPONSE_SEQUENCE * 4, U32.pack(committed - 1))
    memory.write(address + (RESPONSE_SEQUENCE + 1) * 4, payload)
    # A changed request invalidates this response: leave the publication odd.
    if read_request(memory, address).identity != request.identity:
        raise UnstableMailbox("Map request changed during response publication")
    memory.write(address + RESPONSE_SEQUENCE * 4, U32.pack(committed))


class Dispatcher:
    """One mailbox, one manager, one outstanding map request at a time.

    Calls the durable manager API before publishing SAVED. No network, remote
    injection, thread creation, or direct game-state writes are performed.
    """

    def __init__(self, memory: Memory, address: int, store: Store,
                 *, clock=time.monotonic, heartbeat_timeout: float = 3.0):
        self.memory, self.address, self.store = memory, address, store
        self.clock, self.heartbeat_timeout = clock, heartbeat_timeout
        self.last_heartbeat = None
        self.last_change = None
        self.observed_motion = False
        self.last_published = None

    def poll(self) -> dict:
        request = read_request(self.memory, self.address)
        now = self.clock()
        if request.heartbeat != self.last_heartbeat:
            self.observed_motion = self.last_heartbeat is not None
            self.last_heartbeat, self.last_change = request.heartbeat, now
        if now - self.last_change > self.heartbeat_timeout:
            raise BridgeError("Map heartbeat stopped; reconnect after resuming the map")
        if not self.observed_motion:
            return {"status": "waiting_for_heartbeat"}
        if request.state in (2, 4, 5):
            event = {"status": {2: "running", 4: "saved", 5: "map_error"}[request.state]}
            if request.growth_version:
                event.update(growth_catalog=request.growth_version,
                             growth_applied=request.growth_applied == request.growth_version)
            return event
        if request.identity == self.last_published:
            return {"status": "waiting_for_ingame_choice" if request.choice_version and request.state == 1
                    else "waiting_for_map_ack"}
        selection = None
        if request.state == 1 and request.operation in (1, 4):
            is_later_phase = bool(request.phase_version and request.operation == 4 and request.phase > 1)
            if request.operation == 4 and not is_later_phase:
                raise BridgeError("PHASE_LOAD requires an explicit later checkpoint")
            if (request.gold_delta != 0 or
                    (not is_later_phase and (request.nonce != "00" * 16 or request.observed_gold != 0)) or
                    (is_later_phase and (request.nonce == "00" * 16 or not request.growth_applied)) or
                    (request.phase_version and request.operation == 1 and request.phase != 1)):
                raise BridgeError("LOAD request unexpectedly contains result data")
            if request.growth_version:
                from sc1.manager.store import GrowthChoicesPending
                method = getattr(self.store, "restore_growth_phase" if request.phase_version else "restore_growth", None)
                if method is None:
                    raise BridgeError("This manager does not support growth selections")
                try:
                    if request.phase_version:
                        result = self._call_store(request, method, request.mission, request.growth_version,
                                                  request.phase, nonce=request.nonce if is_later_phase else None,
                                                  **({"phase_version":2} if request.phase_version==2 else {}))
                    else:
                        result = self._call_store(request, method, request.mission, request.growth_version)
                except GrowthChoicesPending as pending:
                    if not request.choice_version:
                        return {"status": "waiting_for_choices", "mission": request.mission}
                    if not isinstance(pending.state, dict):
                        raise BridgeError("Manager did not return a persisted in-game offer")
                    selection = pending.state
            else:
                result = self._call_store(request, self.store.restore, request.mission)
            status = 1
        elif request.state == 1 and request.operation == 3 and request.choice_version:
            later_choice = bool(request.phase_version and request.phase > 1)
            if ((not later_choice and (request.growth_applied or request.nonce != "00" * 16 or request.observed_gold))
                    or (later_choice and (not request.growth_applied or request.nonce == "00" * 16)) or request.gold_delta
                    or request.choice_token == "00" * 16 or request.choice_kind not in (1, 2)
                    or not 1 <= request.choice_slot <= (4 if request.choice_kind == 1 else 3)):
                raise BridgeError("In-game choice request has invalid fields")
            method = getattr(self.store, "choose_growth_phase_slot" if request.phase_version else "choose_growth_slot", None)
            if method is None:
                raise BridgeError("This manager does not support in-game choices")
            offer_id = str(uuid.UUID(bytes=bytes.fromhex(request.choice_token)))
            kwargs = {"choice_kind": request.choice_kind}
            if request.phase_version:
                kwargs.update(phase=request.phase, nonce=request.nonce if later_choice else None)
                if request.phase_version==2:kwargs["phase_version"]=2
            chosen = self._call_store(request, method, offer_id, request.choice_slot, request.choice_revision,
                                      request.mission, request.growth_version, **kwargs)
            if chosen.get("state") == "choosing":
                selection = chosen
            else:
                if request.phase_version:
                    result = self._call_store(request, self.store.restore_growth_phase, request.mission,
                                              request.growth_version, request.phase,
                                              nonce=request.nonce if later_choice else None,
                                              **({"phase_version":2} if request.phase_version==2 else {}))
                else:
                    result = self._call_store(request, self.store.restore_growth, request.mission, request.growth_version)
            status = 1
        elif request.state == 3 and request.operation == 2:
            if request.phase_version and request.phase != (4 if request.phase_version==2 else 3):
                raise BridgeError("COMMIT requires the final growth checkpoint")
            if request.nonce == "00" * 16:
                raise BridgeError("COMMIT request is missing its attempt nonce")
            result = self._call_store(request, self.store.complete, request.mission,
                                      request.nonce, request.gold_delta, request.observed_gold)
            status = 2
        else:
            raise BridgeError("Unsupported map state/operation pair")
        current = read_request(self.memory, self.address)
        if current.heartbeat == request.heartbeat and self.clock() - now > self.heartbeat_timeout:
            raise BridgeError("Map stopped responding while the manager saved; no acknowledgment sent")
        payload = choice_payload(request, selection) if selection is not None else response_payload(request, result, status)
        publish_response(self.memory, self.address, request, payload)
        self.last_published = request.identity
        if selection is not None:
            return {"status": "choice_offered", "mission": request.mission,
                    "kind": selection["offer"]["kind"], "remaining": selection["pending"],
                    **({"phase": request.phase} if request.phase_version else {})}
        return {"status": "restored" if status == 1 else "committed",
                "mission": request.mission, "gold": result["gold"],
                "revision": result["revision"], "duplicate": result.get("duplicate", False)}

    def _call_store(self, request: Request, method, *args, **kwargs) -> dict:
        try:
            return method(*args, **kwargs)
        except ValueError as exc:
            # A rejected request is different from an I/O failure: tell the map
            # it cannot continue. Storage exceptions propagate without SAVED.
            payload = struct.pack("<10I", 3, request.sequence, 0,
                                  *struct.unpack("<4I", bytes.fromhex(request.nonce)), 0, 0, 1)
            publish_response(self.memory, self.address, request, payload)
            code = getattr(exc, "code", "rejected_request")
            raise RequestRejected(code, str(exc)) from exc
