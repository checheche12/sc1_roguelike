"""Explicit-PID diagnostic and experimental growth-save bridge CLI."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import threading
import time

from .protocol import BridgeError, Dispatcher, MAILBOX_SIZE, RequestRejected, UnstableMailbox, validate_header
from .windows import WindowsProcess, find_mailboxes, MailboxUnavailable
from .lifetime import watch_manager


def emit(value):
    print(json.dumps(value, ensure_ascii=False), flush=True)


def inspect_candidates(memory, *, sleep=time.sleep, addresses=None, stopped=lambda: False) -> list[dict]:
    if addresses is None:
        addresses = find_mailboxes(memory, stopped=stopped)
    before = {}
    for address in addresses:
        if stopped():
            return []
        try:
            before[address] = validate_header(memory.read(address, MAILBOX_SIZE), address)
        except OSError as exc:
            if getattr(exc, "winerror", None) not in (None, 299, 487, 998):
                raise
            continue
        except BridgeError:
            continue
    # No process modification. A changing heartbeat rejects archive copies and
    # retained memory from a previous map. Paused maps must resume then retry.
    if before:
        sleep(0.25)
    candidates = []
    for address, first in before.items():
        if stopped():
            return []
        try:
            second = validate_header(memory.read(address, MAILBOX_SIZE), address)
        except OSError as exc:
            if getattr(exc, "winerror", None) not in (None, 299, 487, 998):
                raise
            continue
        except BridgeError:
            continue
        candidates.append({"address": address, "address_hex": hex(address),
                           "mission": second[5], "state": second[7],
                           "request_sequence": second[8],
                           "heartbeat": second[6], "active": first[6] != second[6]})
    return candidates


def wait_for_active(memory, candidates, *, timeout=10.0, clock=time.monotonic,
                    sleep=time.sleep) -> list[dict]:
    """Allow a user to return from the manager UI to the paused game window."""
    deadline = clock() + timeout
    addresses = [item["address"] for item in candidates]
    while addresses and not any(item["active"] for item in candidates) and clock() < deadline:
        candidates = inspect_candidates(memory, sleep=sleep, addresses=addresses)
        addresses = [item["address"] for item in candidates]
    return candidates


def wait_for_probe(memory, candidates, *, deadline=None, interval=3.0,
                   clock=time.monotonic, sleep=time.sleep, inspect=None, report=emit,
                   stopped=lambda: False):
    """A game's menu is normal: wait read-only until a live probe appears.

    Rescan after every delay so changing maps or unloading an inactive archive
    copy cannot leave us watching stale addresses forever. Only the caller may
    bind a mailbox/open the store, after this function returns one live target.
    """
    inspect = inspect or inspect_candidates
    previous = None
    while True:
        if stopped():
            return None
        if not memory.is_running():
            raise BridgeError("스타1이 종료되었습니다. 게임을 다시 켠 뒤 연결해 주세요.")
        if deadline is not None and clock() >= deadline:
            return None
        active = [item for item in candidates if item["active"]]
        if len(active) > 1:
            raise BridgeError("활성 캠페인 지도가 여러 개 발견되어 연결하지 않았습니다. 지도를 하나만 열어 주세요.")
        if active:
            return active[0]
        status = "waiting_for_unpause" if candidates else "waiting_for_map"
        if status != previous:
            report({"event": "bridge", "status": status})
            previous = status
        delay = interval if deadline is None else min(interval, max(0, deadline - clock()))
        sleep(delay)
        if stopped():
            return None
        if deadline is not None and clock() >= deadline:
            return None
        candidates = inspect(memory)


def run_connected(memory, active, store_factory, *, stopped, deadline=None, poll_seconds=0.10,
                  clock=time.monotonic, inspect=None, report=emit, dispatcher_factory=Dispatcher):
    """Keep the PID writer guard and selected store across map generations.

    Only retired transport allocations and idle heartbeats enter discovery.
    Storage, permission and malformed ABI errors propagate unchanged. An
    explicit store rejection fails only the current map; keep the connection
    alive for a fresh map without retrying that rejected request.
    Every new binding gets a fresh Dispatcher and fresh heartbeat proof; saved
    offers/nonces remain in the same store, so a lost response is retried there.
    """
    inspect = inspect or (lambda target: inspect_candidates(target, sleep=stopped.wait, stopped=stopped.is_set))
    store = dispatch = None
    previous = None
    generation = 0
    last_stable = clock()
    rejected = None
    while not stopped.is_set() and (deadline is None or clock() < deadline):
        if not memory.is_running():
            raise BridgeError("스타1이 종료되었습니다. 게임을 다시 켠 뒤 연결해 주세요.")
        try:
            if dispatch is None:
                if active is None:
                    # Scan immediately after retirement; subsequent retries wait
                    # briefly and remain cancellable, including each scan chunk.
                    candidates = inspect(memory)
                    active = wait_for_probe(memory, candidates, deadline=deadline, interval=0.5,
                                            clock=clock, sleep=stopped.wait, inspect=inspect,
                                            report=report, stopped=stopped.is_set)
                    if active is None:
                        return
                if stopped.is_set():
                    return
                memory.bind_mailbox(active["address"])
                if store is None:
                    store = store_factory()
                dispatch = dispatcher_factory(memory, active["address"], store, clock=clock)
                rejected = None
                generation += 1
                last_stable = clock()
                previous = None
                if generation > 1:
                    report({"event": "bridge", "status": "map_rebound", "generation": generation,
                            "address_hex": hex(active["address"])})
            words = memory.bound_header()
            if (dispatch.last_heartbeat is not None and words[6] == dispatch.last_heartbeat
                    and clock() - dispatch.last_change >= dispatch.heartbeat_timeout):
                raise MailboxUnavailable("Map heartbeat is idle; awaiting a live map generation")
            try:
                if rejected is None:
                    event = dispatch.poll()
                else:
                    # The error response was published once. Observe only the
                    # heartbeat until this map retires; never retry the store.
                    if dispatch.last_heartbeat != words[6]:
                        dispatch.last_heartbeat = words[6]
                        dispatch.last_change = clock()
                    event = rejected
                last_stable = clock()
            except RequestRejected as exc:
                rejected = event = {"status": "map_request_rejected", "error_code": exc.code,
                                    "message": exc.user_message, "progress": exc.details}
                last_stable = clock()
            except UnstableMailbox:
                if clock() - last_stable > 3:
                    raise BridgeError("Map did not publish a stable request for three seconds")
                stopped.wait(poll_seconds)
                continue
            if event != previous:
                report({"event": "bridge", **event})
                previous = event
            stopped.wait(poll_seconds)
        except MailboxUnavailable as exc:
            # Revocation precedes every scan/store retry. The process handle and
            # its exclusive writer mutex stay open until the whole CLI exits.
            memory.unbind_mailbox()
            dispatch = active = None
            report({"event": "bridge", "status": "rebinding_map", "reason": str(exc)})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan", help="Read-only scan of an explicit x86/x64 StarCraft.exe PID")
    scan.add_argument("--pid", required=True, type=int)
    scan.add_argument("--expected-start-time", type=int, help="Reject a replaced process after automatic discovery")
    run = sub.add_parser("run", help="Experimental mailbox save/restore; explicit write opt-in")
    run.add_argument("--pid", required=True, type=int)
    run.add_argument("--expected-start-time", type=int, help="Reject a replaced process after automatic discovery")
    run.add_argument("--database", type=Path,
                     default=Path(__file__).resolve().parents[1] / "data" / "original.sqlite3")
    run.add_argument("--curses-per-mission", type=int, choices=range(5), default=3)
    run.add_argument("--attach-write", required=True, action="store_true")
    run.add_argument("--poll-seconds", type=float, default=0.10)
    run.add_argument("--duration", type=float, default=0,
                     help="Stop after this many seconds; 0 runs until interrupted")
    run.add_argument("--exit-with-manager", action="store_true",
                     help="Internal UI option: stop when the manager's stdin pipe closes")
    args = parser.parse_args(argv)
    if args.command == "run" and (not 0.02 <= args.poll_seconds <= 1 or args.duration < 0):
        parser.error("poll-seconds must be between .02 and 1; duration must be nonnegative")
    stopped = threading.Event()
    lifetime = None
    try:
        if getattr(args, "exit_with_manager", False):
            lifetime = stopped = watch_manager(sys.stdin.buffer)
        with WindowsProcess(args.pid, allow_write=args.command == "run",
                            expected_start_time=args.expected_start_time) as memory:
            candidates = inspect_candidates(memory, sleep=stopped.wait, stopped=stopped.is_set)
            if stopped.is_set():
                return 0
            emit({"event": "scan", "pid": args.pid, "image": memory.image_path,
                  "architecture": memory.architecture,
                  "write_enabled": args.command == "run", "candidates": candidates,
                  "live_compatibility": "unverified"})
            if args.command == "scan":
                return 0
            start = time.monotonic()
            deadline = start + args.duration if args.duration else None
            active = wait_for_probe(memory, candidates, deadline=deadline,
                                    stopped=stopped.is_set, sleep=stopped.wait,
                                    inspect=lambda target: inspect_candidates(target, sleep=stopped.wait, stopped=stopped.is_set))
            if active is None:
                if not stopped.is_set():
                    emit({"event": "stopped", "reason": "duration"})
                return 0
            if stopped.is_set():
                return 0
            # Import only when run has an active mailbox; scan creates no save.
            from sc1.manager.store import open_campaign_store
            run_connected(memory, active, lambda: open_campaign_store(args.database,curses_per_mission=args.curses_per_mission), stopped=stopped,
                          deadline=deadline, poll_seconds=args.poll_seconds)
            if not stopped.is_set():
                emit({"event": "stopped", "reason": "duration"})
            return 0
    except KeyboardInterrupt:
        emit({"event": "stopped", "reason": "interrupted"})
        return 0
    except BrokenPipeError:
        return 0
    except Exception as exc:
        if stopped.is_set():
            return 0
        emit({"event": "error", "type": type(exc).__name__, "message": str(exc)})
        return 1
    finally:
        if lifetime is not None:
            lifetime.close()


if __name__ == "__main__":
    sys.exit(main())
