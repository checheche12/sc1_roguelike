"""Offline dialog/mailbox integration against a synthetic native C++ host.

This opens only a newly created TemporaryDirectory SQLite database. The child
executable owns synthetic controls and heap/VirtualAlloc memory; no game runs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sc1.bridge.protocol import Dispatcher, WORDS, publish_response, read_request
from sc1.manager.store import CampaignStore

BASE = 0x10000
CONTROL_IDS = [-3, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def frozen_text(name):
    source = (ROOT / "sc1/native_campaign/plugin/include/frozen_catalog.generated.h").read_text(encoding="utf-8")
    match = re.search(r"\b" + name + r"\[\]\s*=\s*\{([^;]*)\};", source)
    if not match:
        raise AssertionError("Missing frozen display text: " + name)
    return json.loads("[" + match.group(1) + "]")


def render_offer(host, offer, check):
    host.command("LAYOUT")
    check(host.state["layout_checks"] > 0, "Native CTEXT and number buttons retain their constructor bounds without overlaps")
    host.command("RENDER")
    rows = dict(zip(CONTROL_IDS, host.state["rendered_texts"]))
    prefix = "talent" if offer["kind"] == "talent" else "curse"
    names, rarities = frozen_text(prefix + "_names"), frozen_text(prefix + "_rarities")
    key = "bit_index" if offer["kind"] == "talent" else "byte_index"
    body = host.state["native_body"]
    check(rows[-1] == body and host.state["native_body_capacity"] == 511,
          "Complete list text is present in original native CTEXT allocation before auxiliary rendering")
    lines = body.splitlines()
    for slot, (control_id, candidate) in enumerate(zip((1, 2, 3, 5), offer["candidates"]), 1):
        check(rows[control_id] == str(slot), "Lower PUSHBUTTON is a simple number after native hotkey preprocessing")
        check(lines[slot] == f"{slot}. {names[candidate[key]]} [{rarities[candidate[key]]}]",
              "Actual native body contains the full numbered candidate name and rarity")
    check(host.state["file_registrations"] == 2 and host.state["template_reads"] >= 1,
          "Two scoped file hooks supplied a meaningful CTEXT payload before native construction")
    check("번호를 누르면" in host.state["template_body"] and "SC1_NATIVE_CHOICE_BODY" not in host.state["template_body"],
          "Constructor body uses real offer information and instruction, without placeholder padding")
    check(host.state["layout_registrations"] == 1, "Typed LayoutDrawText hook registered exactly once")
    host.command("RENDER_EXACT")
    exact_rows = dict(zip(CONTROL_IDS, host.state["rendered_texts"]))
    check(all(exact_rows[control_id] == " " + str(slot)
              for slot, control_id in enumerate((1, 2, 3, 5)[:len(offer["candidates"])], 1)),
          "Exact numeric PUSHBUTTON rendering retains its ASCII hotkey prefix")


def render_detail(host, offer, slot, check, *, foreign=False):
    host.command("LAYOUT")
    check(host.state["layout_checks"] > 0, "Preview retains the upper panel and lower candidate layout")
    host.command("RENDER_FOREIGN" if foreign else "RENDER")
    rows = dict(zip(CONTROL_IDS, host.state["rendered_texts"]))
    prefix = "talent" if offer["kind"] == "talent" else "curse"
    key = "bit_index" if prefix == "talent" else "byte_index"
    index = offer["candidates"][slot - 1][key]
    normalize = lambda value: "".join(value.split())
    body = host.state["native_body"]
    check(body == rows[-1] and host.state["native_body_capacity"] == 511,
          "Full detail text is written to actual native CTEXT storage, without button-label fallback")
    lines = body.splitlines()
    check(lines[0] == frozen_text(prefix + "_names")[index], "Native preview starts with the complete frozen name")
    check(lines[1] == "등급: " + frozen_text(prefix + "_rarities")[index], "Native preview separately states rarity")
    check(normalize("".join(lines[2:])) == normalize(frozen_text(prefix + "_effects")[index]),
          "Native preview preserves the entire frozen semantic effect")
    check(all(rows[control_id] == str(slot) for slot, control_id in enumerate((1, 2, 3, 5)[:len(offer["candidates"])], 1)),
          "Number buttons remain below the plain-text preview for a different explicit selection")


class NativeHost:
    def __init__(self, executable: Path, *, phased=False, header_surface=False, spawn_no_delete=False):
        self.process = subprocess.Popen(
            [str(executable), *(["--phased"] if phased else []), *(["--header-surface"] if header_surface else []),
             *(["--spawn-no-delete"] if spawn_no_delete else [])], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8")
        self.state = self.receive()

    def receive(self):
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("C++ host stopped: " + self.process.stderr.read())
        value = json.loads(line)
        if "error" in value:
            raise AssertionError(value["error"])
        self.state = value
        return value

    def command(self, value: str):
        self.process.stdin.write(value + "\n")
        self.process.stdin.flush()
        return self.receive()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write("QUIT\n")
            self.process.stdin.flush()
        code = self.process.wait(timeout=5)
        error = self.process.stderr.read()
        if code:
            raise AssertionError(f"C++ host exit {code}: {error}")


class HeapMailbox:
    def __init__(self, host: NativeHost):
        self.host = host
        self.refresh()

    def refresh(self):
        self.data = bytearray(WORDS.pack(*self.host.state["words"]))

    def read(self, address, size):
        return bytes(self.data[address - BASE:address - BASE + size])

    def write(self, address, value):
        offset = address - BASE
        self.data[offset:offset + len(value)] = value

    def deliver(self):
        response = WORDS.unpack(self.data)[32:]
        self.host.command("RESPONSE " + " ".join(map(str, response)))


def verify(executable: Path, *, early_goal=False):
    checks = 0
    outcomes = []

    def check(condition, detail):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(detail)

    with tempfile.TemporaryDirectory(prefix="sc1-dialog-protocol-") as folder:
        db = Path(folder) / "synthetic-campaign.sqlite3"
        store = CampaignStore(db, new_profile="original")
        host = NativeHost(executable)
        clock = [0.0]
        memory = HeapMailbox(host)
        dispatcher = Dispatcher(memory, BASE, store, clock=lambda: clock[0])

        def pump(milliseconds=100):
            clock[0] += milliseconds / 1000
            host.command(f"PUMP {milliseconds}")
            memory.refresh()

        def poll(deliver=True):
            memory.refresh()
            event = dispatcher.poll()
            if deliver and event["status"] in ("choice_offered", "restored", "committed"):
                memory.deliver()
            return event

        try:
            check(poll()["status"] == "waiting_for_heartbeat", "Initial heartbeat proof")
            host.command("EVENT_PUMP")
            memory.refresh()
            check(host.state["process_original_calls"] == 1, "Registered ProcessEvents preserves original dispatch")
            check(poll()["status"] == "choice_offered", "Initial persisted offer")
            pump()
            check(host.state["offers"] == 1, "Exactly one first offer callback")
            host.command("OPEN")
            check(host.state["dialog_open"] and host.state["modal_open"], "Native modal attached")
            if early_goal:
                host.command("GOAL")
                check(not host.state["victory_ready"], "Early objective cannot bypass growth LOAD")
            initial_frame = host.state["frame_count"]
            initial_heartbeat = host.state["words"][6]
            initial_pumps = host.state["pump_calls"]
            host.command("THREAD_GUARD")
            check(host.state["words"][6] == initial_heartbeat and host.state["pump_calls"] == initial_pumps,
                  "Foreign thread cannot pump or inspect poisoned UI event pointers")
            for _ in range(42):
                pump()
                check(poll()["status"] == "waiting_for_ingame_choice", "Paused heartbeat stays connected")
            check(host.state["frame_count"] == initial_frame, "Paused pump never advances game frames")
            check(host.state["words"][6] > initial_heartbeat, "Paused heartbeat advances")
            outcomes.append("4.2 seconds of simulated paused UI time remain connected without advancing a game frame")

            identity = read_request(memory, BASE).identity
            host.command("ESC")
            memory.refresh()
            check(host.state["modal_open"], "Escape does not dismiss required choices")
            check(read_request(memory, BASE).identity == identity, "Escape is not selection progress")
            host.command("RESUME_ATTEMPT")
            memory.refresh()
            check(host.state["modal_open"] and host.state["resumes"] == 0, "Original Resume button cannot bypass choices")
            check(read_request(memory, BASE).identity == identity, "Resume attempt is not selection progress")
            host.command("ROOT_ACTIVATE 1")
            memory.refresh()
            check(host.state["stock_action_attempts"] == 0, "Unmapped root activation cannot enter native Save/Load branch")
            check(read_request(memory, BASE).identity == identity, "Unmapped root activation is not a guessed slot")
            outcomes.append("Escape cannot consume a choice or resume gameplay")

            counts = []
            for index in range(5):
                current = store.growth_status()
                offer = current["offer"]
                if index == 0:
                    render_offer(host, offer, check)
                counts.append(len(offer["candidates"]))
                slot = len(offer["candidates"])
                before_preview = read_request(memory, BASE).identity
                host.command(f"CLICK {slot}")
                pump()
                check(host.state["previewing"] and not host.state["waiting"], "Candidate opens detail preview only")
                check(read_request(memory, BASE).identity == before_preview, "Viewing details does not choose or save")
                render_detail(host, offer, slot, check)
                host.command("CONFIRM")
                pump()
                request = read_request(memory, BASE)
                check(request.operation == 3 and request.choice_slot == slot, "Native button produces CHC1 slot")
                check(request.choice_revision == offer["revision"], "Displayed revision preserved")
                check(request.choice_token == uuid.UUID(offer["offer_id"]).bytes.hex(), "Displayed UUID bytes preserved")
                check(request.choice_kind == (1 if offer["kind"] == "talent" else 2), "Displayed kind preserved")
                check(host.state["waiting"], "Buttons wait for persistence")
                selected_identity = request.identity
                before = db.read_bytes()
                host.command("CLICK 1")
                pump()
                check(read_request(memory, BASE).identity == selected_identity, "Repeated pending click cannot alter request")
                check(db.read_bytes() == before, "UI never writes SQLite")

                if index == 0:
                    check(poll(deliver=False)["status"] == "choice_offered", "Durable choice before deliberately lost ACK")
                    persisted = store.growth_status()
                    pump()
                    check(host.state["waiting"] and host.state["offers"] == 1, "Lost ACK does not advance visible offer")
                    dispatcher = Dispatcher(memory, BASE, CampaignStore(db), clock=lambda: clock[0])
                    check(poll()["status"] == "waiting_for_heartbeat", "Restarted manager proves liveness")
                    pump()
                    check(poll()["status"] == "choice_offered", "Same CHC1 token retries idempotently")
                    check(store.growth_status() == persisted, "Retry preserves durable offer and history")
                    outcomes.append("Lost durable ACK plus manager restart retransmits the identical persisted next offer")
                else:
                    check(poll()["status"] == ("restored" if index == 4 else "choice_offered"), "Expected persisted response kind")
                check(host.state["resumes"] == 0, "Response bytes alone cannot resume")
                if index < 4:
                    host.command("DOWN 1")
                pump()
                if index < 4:
                    check(host.state["dialog_open"] and not host.state["waiting"], "ACK refreshes same native modal")
                    check(host.state["offers"] == index + 2, "Next offer appears exactly once")
                    render_offer(host, store.growth_status()["offer"], check)
                    current_request = read_request(memory, BASE).identity
                    host.command("UP 1")
                    pump()
                    check(read_request(memory, BASE).identity == current_request, "Old mouse release cannot select the next offer")
                    check(not host.state["waiting"], "Old mouse release preserves next offer buttons")
                    check(not host.state["waiting"], "Any stale read-only preview still requires a new explicit confirmation")
            check(counts == [4, 4, 4, 3, 3], "Required offer counts")
            check(host.state["applies"] == 1, "Final LOAD applies once")
            check(host.state["words"][7] == (3 if early_goal else 2) and host.state["words"][19] == 1, "Final LOAD publication complete")
            check(not host.state["modal_open"] and not host.state["dialog_open"], "Final LOAD closes native modal")
            check(host.state["resumes"] == 1 and host.state["resume_before_publication"] == 0, "Resume follows complete state publication")
            check(host.state["frame_count"] == initial_frame, "Entire modal transaction leaves game frame unchanged")
            check(host.state["thread_violations"] == 0, "Apply runs on the owning UI thread")
            check(host.state["recursive_blocked"] == 1, "Nested callback cannot recursively publish")
            check(host.state["constructors"] == 1 and host.state["post_construct_binds"] == 1,
                  "Stock constructor completes before callback binding")
            check(host.state["cleanups"] == 1, "Native delete restores every stock handler")
            check(host.state["restoration_checks"] >= 4, "Original geometry/flags are restored before native Resume and delete")
            outcomes.append("4/4/4/3/3 native buttons apply final LOAD once and close only after growth publication")

            host.command("GOAL")
            memory.refresh()
            check(host.state["words"][7] == 3, "Goal requests durable COMMIT")
            pump()
            check(poll()["status"] == "committed", "Durable victory record committed")
            pump()
            check(host.state["victory_ready"] and host.state["applies"] == 1, "COMMIT enables victory without effect reapply")
            outcomes.append("Victory remains gated by durable COMMIT ACK")
            return {"passed": True, "assertions": checks, "outcomes": outcomes,
                    "scenario": "goal_before_final_load" if early_goal else "normal_objective_after_resume",
                    "candidate_counts": counts, "final_host_state": host.state,
                    "actual_game_accessed": False, "user_database_accessed": False,
                    "temporary_sqlite_only": True, "uses_real_dispatcher_and_store": True,
                    "simulation_limit": "Synthetic native controls and event loop; no engine rendering or real UI interaction verified."}
        finally:
            host.close()


def verify_fatal_ack(executable: Path):
    with tempfile.TemporaryDirectory(prefix="sc1-dialog-fatal-") as folder:
        store = CampaignStore(Path(folder) / "synthetic.sqlite3", new_profile="original")
        host = NativeHost(executable)
        memory = HeapMailbox(host)
        dispatcher = Dispatcher(memory, BASE, store)
        try:
            dispatcher.poll()
            host.command("EVENT_PUMP"); memory.refresh()
            assert dispatcher.poll()["status"] == "choice_offered"
            memory.deliver(); host.command("PUMP 100"); host.command("OPEN")
            memory.refresh(); request = read_request(memory, BASE)
            fatal = struct.pack("<10I", 3, request.sequence, 0, 0, 0, 0, 0, 0, 0, 1)
            publish_response(memory, BASE, request, fatal)
            memory.deliver(); host.command("PUMP 100")
            assert host.state["words"][7] == 5
            assert host.state["errors"] == 1 and host.state["applies"] == 0
            assert host.state["resumes"] == 1 and not host.state["modal_open"]
            assert host.state["error_dismisses"] == 1 and host.state["resume_before_publication"] == 0
            assert not host.state["victory_ready"]
            return {"passed": True, "assertions": 6, "scenario": "fatal_ack_dismisses_without_progress",
                    "final_host_state": host.state}
        finally:
            host.close()


def verify_phased_auto_modal(executable: Path, *, spawn_no_delete=False):
    checks = 0
    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError("PHC1 auto modal: " + reason)
    with tempfile.TemporaryDirectory(prefix="sc1-phased-modal-") as folder:
        db = Path(folder) / "synthetic.sqlite3"
        store = CampaignStore(db, new_profile="original")
        host = NativeHost(executable, phased=True, spawn_no_delete=spawn_no_delete)
        memory = HeapMailbox(host)
        dispatcher = Dispatcher(memory, BASE, store)

        def pump():
            host.command("PUMP 100"); memory.refresh()

        def poll(deliver=True):
            memory.refresh()
            event = dispatcher.poll()
            if deliver and event["status"] in ("choice_offered", "restored", "committed"):
                memory.deliver()
            return event

        try:
            check(poll()["status"] == "waiting_for_heartbeat", "First heartbeat is read-only")
            host.command("SPAWN_HUD")
            host.command("EVENT_PUMP"); memory.refresh()
            check(poll()["status"] == "choice_offered", "Persist initial phase1 talent")
            nonce = None
            for phase in (1, 2, 3):
                if phase > 1:
                    host.command(f"PHASE {phase}"); memory.refresh()
                    request = read_request(memory, BASE)
                    check(request.operation == 4 and request.phase == phase and request.nonce == nonce,
                          "New checkpoint retains the attempt and requests its own pair")
                    check(poll()["status"] == "choice_offered", "Checkpoint has a durable offer")
                pump()
                check(host.state["modal_open"] and host.state["dialog_open"], "HUD activation opens a bound native modal")
                check(host.state["auto_opens"] == phase, "Exactly one automatic popup per checkpoint")
                check(host.state["constructors"] == phase and host.state["post_construct_binds"] == phase,
                      "Every popup binds only after original construction")
                initial_heartbeat = host.state["words"][6]
                nested_before = host.state["nested_process_calls"]
                process_before = host.state["process_original_calls"]
                if spawn_no_delete:
                    check(host.state["spawn_entries"] == phase and host.state["spawn_returns"] == phase,
                          "Each native Spawn returns immediately before further modal events")
                    check(not host.state["inside_auto"] and host.state["run_entries"] == 0,
                          "Asynchronous Spawn does not inherit a RunDialog or HUD activation stack")
                for _ in range(32):
                    pump()
                    check(poll()["status"] == "waiting_for_ingame_choice", "Real paused ProcessEvents pump remains connected beyond 3-second timeout")
                if spawn_no_delete:
                    check(host.state["words"][6] > initial_heartbeat and host.state["process_original_calls"] >= process_before + 32
                          and host.state["nested_process_calls"] == 0,
                          "Independent ProcessEvents keep paused Spawn heartbeat alive after its original call returned")
                else:
                    check(host.state["words"][6] > initial_heartbeat and host.state["nested_process_calls"] >= nested_before + 32,
                          "Nested ProcessEvents runs while the outer automatic activation remains on the stack")
                check(host.state["frame_count"] == 123, "Paused modal never advances the game frame")
                if phase == (3 if spawn_no_delete else 1):
                    host.command("GOAL")
                    check(not host.state["victory_ready"], "Early original objective waits for all three pairs")
                for kind in (1, 2):
                    offer = store.growth_status()["offer"]
                    render_offer(host, offer, check)
                    slot = 4 if kind == 1 else 3
                    before = db.read_bytes()
                    identity = read_request(memory, BASE).identity
                    host.command(f"CLICK {slot}"); pump()
                    check(host.state["previewing"] and read_request(memory, BASE).identity == identity,
                          "Candidate preview does not publish a selection")
                    check(db.read_bytes() == before, "Details never mutate the saved record")
                    render_detail(host, offer, slot, check, foreign=True)
                    host.command("CLICK 1"); pump()
                    check(host.state["previewing"] and read_request(memory, BASE).identity == identity,
                          "Another candidate updates only the upper preview without spending a right")
                    host.command(f"CLICK {slot}"); pump()
                    host.command("CONFIRM"); pump()
                    request = read_request(memory, BASE)
                    check(request.operation == 3 and request.phase == phase and request.choice_kind == kind,
                          "Only explicit confirm publishes the phase choice")
                    check(request.choice_slot == slot and request.choice_revision == offer["revision"]
                          and request.choice_token == uuid.UUID(offer["offer_id"]).bytes.hex(),
                          "Confirmation retains exact visible UUID, revision and slot")
                    check(request.nonce == ("00" * 16 if phase == 1 else nonce), "Confirmation carries the phase nonce")
                    check(host.state["waiting"] and host.state["applies"] == phase - 1,
                          "Waiting for ACK never applies a partial pair")
                    current_request = request.identity
                    host.command("CONFIRM"); pump()
                    check(read_request(memory, BASE).identity == current_request, "Pending confirm cannot publish twice")
                    if phase == 2 and kind == 1:
                        check(poll(deliver=False)["status"] == "choice_offered", "Persist before intentionally dropped ACK")
                        next_offer = store.growth_status()["offer"]
                        pump()
                        check(host.state["waiting"] and host.state["modal_open"], "Lost ACK keeps current modal waiting")
                        dispatcher = Dispatcher(memory, BASE, CampaignStore(db))
                        check(poll()["status"] == "waiting_for_heartbeat", "Restarted manager proves liveness")
                        pump()
                        check(poll()["status"] == "choice_offered", "Restart retransmits the same saved choice")
                        check(store.growth_status()["offer"] == next_offer, "Persisted UUID and candidate order survive lost ACK")
                    else:
                        check(poll()["status"] == ("choice_offered" if kind == 1 else "restored"),
                              "ACK advances within pair or publishes its cumulative snapshot")
                    check(host.state["resumes"] == phase - 1, "Raw response bytes do not resume the modal")
                    pump()
                    if kind == 1:
                        check(host.state["modal_open"] and not host.state["waiting"] and not host.state["previewing"],
                              "Next persisted offer resets preview and reuses the current modal")
                    else:
                        check(not host.state["modal_open"] and not host.state["dialog_open"], "Each complete pair closes its own stock modal")
                        check(host.state["applies"] == phase and host.state["words"][19] == 1,
                              "Each cumulative checkpoint applies exactly once before closing")
                        check(host.state["resumes"] == phase and host.state["resume_before_publication"] == 0,
                              "Native Resume follows final state publication")
                        if spawn_no_delete:
                            check(host.state["spawn_closes"] == phase and host.state["cleanups"] == 0
                                  and host.state["native_delete_events"] == 0,
                                  "Spawn closes only through original Resume; no root delete event or Run cleanup is supplied")
                            check(host.state["restoration_checks"] >= 3 * phase,
                                  "Each asynchronous Resume sees original handlers, geometry and flags before close")
                        else:
                            check(host.state["cleanups"] == phase, "Each stock dialog runs original delete cleanup")
                            check(host.state["restoration_checks"] >= 4 * phase,
                                  "Each phase restores original layout/flags before native Resume and delete")
                        new_nonce = read_request(memory, BASE).nonce
                        if nonce:
                            check(new_nonce == nonce, "All checkpoints share the immutable attempt nonce")
                        nonce = new_nonce
                check(host.state["frame_count"] == 123, "No phase advances synthetic gameplay")
            check(host.state["words"][7] == 3 and host.state["words"][31] == 3,
                  "Goal emits COMMIT only after final pair")
            check(not host.state["victory_ready"], "Final pair completion alone is not victory")
            check(poll()["status"] == "committed", "Completion is durable before native ACK")
            pump()
            check(host.state["victory_ready"] and host.state["applies"] == 3, "COMMIT unlocks victory without reapplying growth")
            check(host.state["errors"] == 0 and host.state["thread_violations"] == 0, "No native protocol or thread error")
            check(host.state["recursive_blocked"] == 3, "Every snapshot callback blocks recursive protocol entry")
            return {"passed": True, "assertions": checks,
                    "scenario": "phased_async_spawn_without_delete_three_pairs" if spawn_no_delete else "phased_stock_hud_nested_modal_three_pairs",
                    "candidate_counts": [4,3,4,3,4,3], "final_host_state": host.state,
                    "real_pause_interval_seconds_per_phase": 3.2,
                    "actual_game_accessed": False, "user_database_accessed": False,
                    "temporary_sqlite_only": True, "uses_real_dispatcher_and_store": True,
                    "simulation_limit": "Synthetic native controls/constructor and Stat_F10 activation; Run uses nested events, Spawn returns before independent paused events and never sends delete. Actual engine rendering/event cadence and gameplay checkpoint conditions remain unverified."}
        finally:
            host.close()


def verify_offer_during_stock_fallback(executable: Path):
    checks = 0
    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError("Stock fallback modal: " + reason)
    with tempfile.TemporaryDirectory(prefix="sc1-stock-modal-") as folder:
        store = CampaignStore(Path(folder) / "synthetic.sqlite3", new_profile="original")
        host = NativeHost(executable, header_surface=True)
        memory = HeapMailbox(host)
        dispatcher = Dispatcher(memory, BASE, store)
        try:
            check(dispatcher.poll()["status"] == "waiting_for_heartbeat", "Heartbeat proof before unowned menu")
            host.command("SPAWN_HUD")
            host.command("OPEN_STOCK"); memory.refresh()
            check(host.state["stock_fallback"] and host.state["modal_open"] and not host.state["dialog_open"],
                  "Preexisting stock modal stays owned by original callbacks")
            check(dispatcher.poll()["status"] == "choice_offered", "Pending offer may arrive while stock modal is open")
            memory.deliver()
            for _ in range(4):
                host.command("PUMP 100"); memory.refresh()
                check(host.state["auto_opens"] == 0 and not host.state["dialog_open"],
                      "Pending offer cannot recursively auto-open inside an unowned stock modal")
            check(host.state["pending"] and host.state["offers"] == 1, "Saved offer remains pending for later display")
            host.command("CLOSE_STOCK")
            check(not host.state["modal_open"] and host.state["stock_cleanups"] == 1, "Original stock modal exits normally")
            host.command("PUMP 100"); memory.refresh()
            check(host.state["auto_opens"] == 1 and host.state["dialog_open"],
                  "Pending offer auto-opens only after original modal returns")
            request = read_request(memory, BASE)
            publish_response(memory, BASE, request, struct.pack("<10I", 3, request.sequence, 0, 0, 0, 0, 0, 0, 0, 1))
            memory.deliver(); host.command("PUMP 100")
            check(not host.state["modal_open"] and host.state["error_dismisses"] == 1,
                  "Failure safely dismisses the later owned modal")
            check(not host.state["victory_ready"] and host.state["applies"] == 0, "Fallback/error path grants no progress")
            return {"passed": True, "assertions": checks, "scenario": "offer_arrives_inside_unowned_stock_modal",
                    "final_host_state": host.state, "actual_game_accessed": False, "user_database_accessed": False}
        finally:
            host.close()


def verify_native_body_with_small_number_buttons(executable: Path):
    checks = 0
    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError("Immutable renderer: " + reason)
    with tempfile.TemporaryDirectory(prefix="sc1-dialog-short-detail-") as folder:
        path = Path(folder) / "synthetic.sqlite3"
        store = CampaignStore(path, new_profile="original")
        host = NativeHost(executable, header_surface=True)
        memory = HeapMailbox(host)
        dispatcher = Dispatcher(memory, BASE, store)
        try:
            check(dispatcher.poll()["status"] == "waiting_for_heartbeat", "Heartbeat proof")
            host.command("EVENT_PUMP"); memory.refresh()
            check(dispatcher.poll()["status"] == "choice_offered", "Persisted offer before display")
            memory.deliver(); host.command("PUMP 100"); host.command("OPEN")
            memory.refresh(); request = read_request(memory, BASE)
            offer = store.growth_status()["offer"]
            before = path.read_bytes()
            host.command("REINIT"); host.command("PUMP 100")
            check(host.state["reinitializations"] == 1 and host.state["restoration_checks"] >= 4,
                  "Native reinitialization sees original rectangles and flags before binding again")
            host.command("SHORT_BUTTONS"); host.command("CLICK 1")
            check(host.state["previewing"] and not host.state["confirm_disabled"], "Three-byte numeric button storage and native CTEXT storage keep full detail and confirmation")
            render_detail(host, offer, 1, check)
            main_text = host.state["rendered_texts"]
            render_detail(host, offer, 1, check, foreign=True)
            check(host.state["rendered_texts"] == main_text, "Renderer thread reads the same immutable snapshot")
            check(not host.state["waiting"] and host.state["applies"] == 0 and before == path.read_bytes(),
                  "Text rendering and preview grant no choice or effect")
            host.command("RETAIN -1")
            host.command("CLICK 2"); host.command("PUMP 100")
            render_detail(host, offer, 2, check)
            host.command("RETAIN_CHECK")
            memory.refresh()
            check(read_request(memory, BASE).identity == request.identity, "Returned text suffix survives generation change and fallback without selection")
            host.command("CLICK 1"); host.command("CONFIRM"); memory.refresh()
            request = read_request(memory, BASE)
            check(request.operation == 3 and request.choice_slot == 1 and host.state["waiting"],
                  "Only explicit confirmation publishes the selected candidate")
            check(before == path.read_bytes(), "Even confirmation waits for the manager before SQLite mutation")
            publish_response(memory, BASE, request, struct.pack("<10I", 3, request.sequence, 0, 0, 0, 0, 0, 0, 0, 1))
            memory.deliver(); host.command("PUMP 100")
            check(not host.state["modal_open"] and host.state["error_dismisses"] == 1, "Fatal result safely dismisses the preview modal")
            host.command("RETAIN_CHECK"); host.command("RENDER")
            rows = dict(zip(CONTROL_IDS, host.state["rendered_texts"]))
            check(rows[-1] == host.state["native_body"], "Closed dialog clears renderer overrides and still returns the real native body unchanged")
            check(not host.state["victory_ready"], "Display path never grants victory")
            return {"passed": True, "assertions": checks, "scenario": "full_native_ctext_with_three_byte_number_buttons",
                    "final_host_state": host.state, "actual_game_accessed": False, "user_database_accessed": False}
        finally:
            host.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    executable = args.executable.resolve()
    scenarios = [verify(executable), verify(executable, early_goal=True), verify_fatal_ack(executable),
                 verify_phased_auto_modal(executable), verify_offer_during_stock_fallback(executable)]
    scenarios.append(verify_native_body_with_small_number_buttons(executable))
    scenarios.append(verify_phased_auto_modal(executable, spawn_no_delete=True))
    print(json.dumps({"passed": all(item["passed"] for item in scenarios),
                      "assertions": sum(item["assertions"] for item in scenarios),
                      "scenarios": scenarios, "actual_game_accessed": False,
                      "user_database_accessed": False}, ensure_ascii=False))
