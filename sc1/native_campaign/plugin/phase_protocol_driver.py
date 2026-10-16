"""Real PHC1 Dispatcher/store <-> native mailbox, using temporary fixtures only.

The C++ CLI owns its VirtualAlloc mailbox. Python mirrors only those 256 bytes
in a bytearray and transfers the manager half over stdin; it never opens a game
process or player database. Run with the SC1_MAILBOX_PROTOCOL_TEST executable.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from sc1.bridge.protocol import Dispatcher, PHASE_MAGIC, WORDS, read_request, validate_header
from sc1.manager.store import open_campaign_store

BASE = 0x10000


class Host:
    def __init__(self, executable):
        self.process = subprocess.Popen([str(executable), "--phase-wire"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8")
        self.receive()

    def receive(self):
        line = self.process.stdout.readline()
        if not line.startswith("DUMP "):
            raise AssertionError("Native wire host stopped: " + line)
        values = [int(value) for value in line.split()[1:]]
        if len(values) != 70:
            raise AssertionError("Native wire host must emit 64 words and six counters")
        self.words, self.counters = values[:64], values[64:]
        validate_header(WORDS.pack(*self.words), BASE)
        return self.words

    def command(self, command):
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()
        return self.receive()

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.write("QUIT\n")
            self.process.stdin.flush()
        code = self.process.wait(timeout=5)
        error = self.process.stderr.read()
        for pipe in (self.process.stdin, self.process.stdout, self.process.stderr):
            pipe.close()
        if code:
            raise AssertionError(f"Native host exit {code}: {error}")


class Memory:
    def __init__(self, host):
        self.host = host
        self.refresh()

    def refresh(self):
        self.data = bytearray(WORDS.pack(*self.host.words))

    def read(self, address, size):
        return bytes(self.data[address - BASE:address - BASE + size])

    def write(self, address, value):
        offset = address - BASE
        self.data[offset:offset + len(value)] = value

    def deliver(self):
        words = WORDS.unpack(self.data)
        self.host.command("RESPONSE " + " ".join(map(str, words[32:])))


def verify(executable, scenario):
    checks = 0
    trace = []

    def check(condition, reason):
        nonlocal checks
        checks += 1
        if not condition:
            raise AssertionError(f"{scenario}: {reason}")

    with tempfile.TemporaryDirectory(prefix="sc1-phase-wire-") as folder:
        db = Path(folder) / "synthetic.sqlite3"
        store = open_campaign_store(db)
        if scenario == "c1_frozen_legacy_restore":
            state = store.prepare_growth()
            while state["offer"]:
                offer = state["offer"]
                state = store.choose_growth_slot(offer["offer_id"], 1, offer["revision"],
                                                choice_kind=1 if offer["kind"] == "talent" else 2)
            legacy = store.restore_growth(101)
        host = Host(executable)
        memory = Memory(host)
        clock = [0.0]
        dispatcher = Dispatcher(memory, BASE, store, clock=lambda: clock[0])

        def command(value):
            clock[0] += 0.1
            host.command(value)
            memory.refresh()
            return read_request(memory, BASE)

        def poll(deliver=True):
            memory.refresh()
            event = dispatcher.poll()
            if event["status"] in ("choice_offered", "restored", "committed"):
                words = WORDS.unpack(memory.data)
                trace.append({"event": event, "requested_phase": host.words[31],
                              "response_status": words[33], "response_phase_tag": words[42],
                              "offer_phase_words": list(words[58:64]) if words[33] == 4 else None})
                if deliver:
                    memory.deliver()
            return event

        def new_dispatcher():
            nonlocal dispatcher, store
            store = open_campaign_store(db)
            dispatcher = Dispatcher(memory, BASE, store, clock=lambda: clock[0])
            check(poll()["status"] == "waiting_for_heartbeat", "Restart requires new heartbeat proof")
            command("TICK")

        def reset_to_latest(completed, words, nonce):
            before = db.read_bytes()
            applies, offers = host.counters[:2]
            request = command("RESET")
            check(request.phase == 1 and request.nonce == "00" * 16, "Fresh map emits phase1 LOAD")
            new_dispatcher()
            check(poll(deliver=False)["status"] == "restored", "Reconnect restores completed checkpoint")
            response = WORDS.unpack(memory.data)
            check(response[42] == 0x50480000 | completed << 8 | 1, "Initial LOAD advertises highest completed phase")
            check(list(response[43:]) == words, "Reconnect payload excludes future partial pair effects")
            memory.deliver(); memory.refresh()
            check(host.words[7] == 2 and host.words[19] == 1, "Restored map is running after apply")
            check(host.counters[0] == applies + 1 and host.counters[1] == offers, "Restore applies once without a new offer")
            check(read_request(memory, BASE).nonce == nonce, "Reconnect retains the immutable attempt nonce")
            check(db.read_bytes() == before, "Reconnect does not alter selection history or immutable snapshots")

        try:
            check(host.words[29:32] == [PHASE_MAGIC, 1, 1], "Native advertises exact PHC1 capability")
            check(poll()["status"] == "waiting_for_heartbeat", "Initial heartbeat proof")
            command("TICK")
            event = poll()
            if scenario == "c1_frozen_legacy_restore":
                check(event["status"] == "restored", "Frozen C1 restores without new offers")
                check(host.words[42] == 0x50480301, "Frozen C1 is completed phase3")
                check(host.words[43:] == legacy["growth_words"], "Frozen C1 preserves exact 3+2 loadout")
                check(host.counters[0] == 1 and host.counters[1] == 0, "Legacy restored once without any selector")
                nonce = legacy["nonce"]
            else:
                check(event["status"] == "choice_offered", "Initial talent candidate persists before offer")
                nonce = None
                previous_words = [1] + [0] * 20
                for phase in (1, 2, 3):
                    if phase > 1:
                        request = command(f"PHASE {phase}")
                        check(request.operation == 4 and request.state == 1 and request.phase == phase,
                              "Native checkpoint emits PHASE_LOAD")
                        check(request.nonce == nonce and request.growth_applied == 1, "Later LOAD retains applied attempt")
                        check(poll()["status"] == "choice_offered", "Only requested checkpoint gets an offer")
                    if phase == 1:
                        command("GOAL")
                        check(host.words[7] == 1 and not host.counters[5], "Early objective cannot bypass initial pair")
                    for kind in (1, 2):
                        state = store.growth_status()
                        offer = state["offer"]
                        check(offer["kind"] == ("talent" if kind == 1 else "curse"), "One talent then one curse per phase")
                        check(host.words[58:64] == [PHASE_MAGIC, 1, phase, phase - 1, 3, 0], "Choice ACK phase metadata is exact")
                        check(host.words[55:57] == [1 if kind == 1 else 0, 1], "Choice ACK counts only this phase's pair")
                        applies = host.counters[0]
                        slot = 4 if kind == 1 else 3
                        before = db.read_bytes()
                        request = command(f"CHOOSE {slot}")
                        check(request.operation == 3 and request.phase == phase, "Native selection operation and phase")
                        check(request.choice_slot == slot and request.choice_kind == kind, "Native selected slot and kind")
                        check(request.choice_token == uuid.UUID(offer["offer_id"]).bytes.hex(), "Exact persisted UUID bytes")
                        check(request.choice_revision == offer["revision"], "Exact saved CAS revision")
                        check(request.nonce == ("00" * 16 if phase == 1 else nonce), "Selection uses required attempt nonce")
                        check(db.read_bytes() == before, "Native selection never writes SQLite directly")
                        identity = request.identity
                        command("CHOOSE 1")
                        check(read_request(memory, BASE).identity == identity, "Pending duplicate button cannot replace selection")
                        if scenario == "phase2_partial_restart" and phase == 2 and kind == 1:
                            check(poll(deliver=False)["status"] == "choice_offered", "Partial choice committed before lost ACK")
                            persisted = store.growth_status()["offer"]
                            check(host.counters[0] == applies, "Partial pair is not applied")
                            new_dispatcher()
                            check(poll(deliver=False)["status"] == "choice_offered", "Manager restart retries the same saved choice")
                            check(store.growth_status()["offer"] == persisted, "Lost ACK never rerolls the next offer")
                            reset_to_latest(1, previous_words, nonce)
                            command("PHASE 2")
                            check(poll()["status"] == "choice_offered", "Restarted checkpoint resumes unfinished curse")
                            check(store.growth_status()["offer"] == persisted, "Partial-pair UUID and candidates survive map restart")
                            continue
                        event = poll(deliver=False)
                        if kind == 1:
                            check(event["status"] == "choice_offered", "Talent selection yields the same-phase curse")
                            check(host.counters[0] == applies, "Talent alone has no effect application")
                            check(store.growth_status()["growth_words"] == previous_words, "Half pair does not enter applied snapshot")
                        else:
                            check(event["status"] == "restored", "Pair completion yields immutable cumulative LOAD")
                            response = WORDS.unpack(memory.data)
                            check(response[42] == 0x50480000 | phase << 8 | phase, "Snapshot phase tag is exact")
                            check(host.counters[0] == applies, "No apply before receiving durable LOAD ACK")
                            previous_words = list(response[43:])
                        memory.deliver(); memory.refresh()
                        check(host.counters[3] == 0 and host.words[7] != 5, "C++ accepts real Python payload")
                        if kind == 2:
                            check(host.counters[0] == applies + 1 and host.words[19] == 1, "Pair snapshot applies exactly once")
                            request = read_request(memory, BASE)
                            if nonce is not None:
                                check(request.nonce == nonce, "Phase application keeps the first nonce")
                            nonce = request.nonce
                            command("TICK")
                            check(host.counters[0] == applies + 1, "Repeated response is not reapplied")
                    if phase == 1:
                        identity = read_request(memory, BASE).identity
                        command("PHASE 3")
                        check(read_request(memory, BASE).identity == identity, "Native rejects out-of-order checkpoint")
                        check(host.words[7] == 2 and not host.counters[5], "Early goal still waits for later pairs")
                    elif phase == 2 and scenario == "phase2_partial_restart":
                        reset_to_latest(2, previous_words, nonce)
                check(store.growth_status()["pending"] == {"talent": 0, "curse": 0}, "Exactly three complete pairs consumed")

            request = command("GOAL")
            check(request.state == 3 and request.operation == 2 and request.phase == 3,
                  "COMMIT always carries phase3 including highest-snapshot restore")
            check(request.nonce == nonce and request.growth_applied == 1, "COMMIT retains restored attempt identity")
            check(not host.counters[5], "Victory is gated before durable COMMIT ACK")
            applies = host.counters[0]
            check(poll(deliver=False)["status"] == "committed", "Real SQLite result commits before ACK delivery")
            commit_words = WORDS.unpack(memory.data)
            check(commit_words[42] == 0 and list(commit_words[43:]) == [1] + [0] * 20, "COMMIT has canonical zero extension")
            check(not host.counters[5] and host.counters[0] == applies, "Lost completion ACK grants neither victory nor reapply")
            new_dispatcher()
            event = poll(deliver=False)
            check(event["status"] == "committed" and event["duplicate"], "Restart safely resends one durable completion")
            check(WORDS.unpack(memory.data)[40] == 1, "Completion campaign revision advances exactly once")
            memory.deliver(); memory.refresh()
            check(host.words[7] == 4 and host.counters[5] == 1, "Victory only after C++ validates completion ACK")
            check(host.counters[0] == applies, "Completion never reapplies cumulative effects")
            with closing(sqlite3.connect(db)) as conn:
                check(conn.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 1, "One completion receipt")
                check(conn.execute("SELECT talent_choices,curse_choices FROM growth_rewards").fetchall() == [(3, 3)], "Exactly one next-mission 3+3 reward")
            check(store.growth_status()["upcoming"] == {"talent": 3, "curse": 3}, "Future rights remain unassigned")
            final_words = store.restore_growth_phase(101, 1, 1)["growth_words"]
            reset_to_latest(3, final_words, nonce)
            before = db.read_bytes()
            request = command("GOAL")
            check(request.state == 4 and request.operation == 0 and request.phase == 3, "Completed replay reaches victory without another COMMIT")
            check(host.counters[5] == 1 and db.read_bytes() == before, "Replay has no new receipt or reward")
            return {"scenario": scenario, "passed": True, "assertions": checks,
                    "native_counters": dict(zip(("applies", "offers", "clears", "errors", "error_code", "victory_ready"), host.counters)),
                    "trace": trace, "temporary_sqlite_only": True,
                    "actual_dispatcher_store_serializer": True, "actual_game_accessed": False,
                    "user_database_accessed": False}
        finally:
            host.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    results = [verify(args.executable.resolve(), scenario) for scenario in
               ("three_pairs", "phase2_partial_restart", "c1_frozen_legacy_restore")]
    print(json.dumps({"passed": True, "assertions": sum(r["assertions"] for r in results),
                      "scenarios": results, "actual_game_accessed": False, "user_database_accessed": False}))


if __name__ == "__main__":
    main()
