"""Run with python -m sc1.manager; no third-party runtime dependencies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

from .store import CampaignStore, ProtocolError, open_campaign_store
from .preferences import DEFAULT_DATABASE, PREFERENCES_PATH
from sc1.campaign.catalog import ORIGINAL_PROFILE, PROFILE_NAMES

def run_demo(db_path: Path) -> dict:
    """Manager-only simulation. It deliberately never attaches to a game."""
    manager_a = CampaignStore(db_path)
    first = manager_a.restore(1)
    result = manager_a.complete(1, first["nonce"], 123, first["gold"])
    del manager_a
    manager_b = CampaignStore(db_path)
    repeated = manager_b.complete(1, first["nonce"], 123, first["gold"])
    restored = manager_b.restore(2)
    confirmed = manager_b.complete(2, restored["nonce"], 0, restored["gold"])
    if (result["gold"], repeated["gold"], restored["gold"], confirmed["gold"]) != (123, 123, 123, 123):
        raise RuntimeError("Persistence probe failed")
    return {"test_kind": "manager_only_simulation", "native_game_tested": False,
            "database": str(db_path), "first_commit": result,
            "duplicate_commit": repeated, "restored_in_probe_b": restored,
            "probe_b_commit": confirmed}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="SC1 original campaign records and legacy persistence probes")
    parser.add_argument("--db", type=Path, help="Record file; the UI remembers its last successful selection")
    parser.add_argument("--preferences", type=Path, default=PREFERENCES_PATH,
                        help="Manager settings path; use a separate path for isolated tests")
    parser.add_argument("--new-profile", choices=PROFILE_NAMES, default=ORIGINAL_PROFILE,
                        help="Profile for a new file only; existing metadata always takes precedence")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    ui = sub.add_parser("ui")
    ui.add_argument("--auto-connect", action="store_true",
                    help="Wait for the launcher-created game and connect without a manual button")
    ui.add_argument("--game-image", help="Restrict automatic connection to this StarCraft.exe image")
    ui.add_argument("--game-start-after", type=int, default=0,
                    help="Minimum Windows creation FILETIME for the launcher-created game")
    sub.add_parser("demo", help="Run an isolated temporary manager-only probe")
    restore = sub.add_parser("restore")
    restore.add_argument("--mission", type=int, required=True)
    restore.add_argument("--protocol-version", type=int, default=1)
    complete = sub.add_parser("complete")
    complete.add_argument("--mission", type=int, required=True)
    complete.add_argument("--nonce", required=True)
    complete.add_argument("--gold-delta", type=int, required=True)
    complete.add_argument("--observed-gold", type=int, required=True)
    complete.add_argument("--protocol-version", type=int, default=1)
    args = parser.parse_args(argv)
    if args.command == "ui":
        from .auto_connect import AutoConnectTarget
        if not args.auto_connect and (args.game_image or args.game_start_after):
            parser.error("game-image and game-start-after require auto-connect")
        try:
            target = AutoConnectTarget(args.game_image, args.game_start_after) if args.auto_connect else None
        except ValueError as exc:
            parser.error(str(exc))
    try:
        if args.command == "ui":
            from .ui import launch
            launch(args.db, new_profile=args.new_profile, auto_connect_target=target, preferences_path=args.preferences)
            return 0
        if args.command == "demo":
            with tempfile.TemporaryDirectory(prefix="sc1-manager-probe-") as tmp:
                response = run_demo(Path(tmp) / "probe.sqlite3")
                response["database"] = "temporary database (removed after demo)"
        else:
            store = open_campaign_store(args.db or DEFAULT_DATABASE, new_profile=args.new_profile)
            if args.command == "status":
                response = store.status()
            elif args.command == "restore":
                response = store.restore(args.mission, args.protocol_version)
            else:
                response = store.complete(args.mission, args.nonce, args.gold_delta,
                                          args.observed_gold, args.protocol_version)
        print(json.dumps(response, ensure_ascii=True, indent=2))
        return 0
    except (ProtocolError, OSError, sqlite3.Error) as exc:
        print(json.dumps({"error": getattr(exc, "code", "storage_error"), "message": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
