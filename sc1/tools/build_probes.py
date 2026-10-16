"""Build two isolated SC:R EUD growth-persistence probes; never starts a game."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "maps"
VENDOR = ROOT / "vendor"
MAGIC = b"SC1CAMP-PROBE-V1"
SOURCE_COMMIT = "979f2fb4e8ffa4ec62e5872bddc4c0b36ae006cf"


def base_map(mission: int) -> Path:
    """Replace sample's content; retain MIT fixture terrain and editor defaults."""
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata.chktok import CHK

    source = mpqapi.MPQ.open(str(VENDOR / "eudplib-basemap.scx"))
    chk = CHK()
    chk.loadchk(source.extract_file("staredit\\scenario.chk"))
    del source
    strings = [
        f"SC1 Growth Probe {'A' if mission == 1 else 'B'}".encode(),
        b"Single-player growth-storage prototype. Live compatibility UNTESTED. Move Marine to beacon after manager connects.",
        b"Start", b"Finish", b"Anywhere", b"Probe Player", b"Computer",
    ]
    offset = 2 + 2 * len(strings)
    offsets = []
    for string in strings:
        offsets.append(offset)
        offset += len(string) + 1
    chk.setsection("STR ", struct.pack("<" + "H" * (len(strings) + 1), len(strings), *offsets)
                   + b"\0".join(strings) + b"\0")
    chk.setsection("SPRP", struct.pack("<HH", 1, 2))
    # SC:R single-player custom UMS requires a computer opponent to start.
    # P2 is passive: no AI script or attacks are issued to its command center.
    owners = bytes([6, 5] + [0] * 10)
    chk.setsection("OWNR", owners)
    chk.setsection("IOWN", owners)
    chk.setsection("SIDE", bytes([1, 1] + [7] * 9 + [4]))
    chk.setsection("FORC", bytes([0, 1] + [0] * 6) + struct.pack("<4H", 6, 7, 0, 0) + bytes(4))
    chk.setsection("COLR", bytes(range(8)))
    chk.setsection("TRIG", b"")
    chk.setsection("MBRF", b"")
    chk.setsection("SWNM", bytes(1024))
    chk.setsection("WAV ", bytes(2048))
    chk.setsection("MASK", bytes(64 * 64))
    for section, count in (("UNIx", 228), ("UNIS", 228), ("UPGx", 61), ("UPGS", 46), ("TECx", 44), ("TECS", 24)):
        chk.setsection(section, bytes([1]) * count + bytes(len(chk.getsection(section)) - count))
    locations = bytearray(255 * 20)
    for index, bounds, name in ((0, (320, 960, 448, 1088), 3),
                                (1, (1344, 960, 1472, 1088), 4),
                                (2, (1664, 1600, 1856, 1792), 7),
                                (63, (0, 0, 2048, 2048), 5)):
        struct.pack_into("<4IHH", locations, index * 20, *bounds, name, 0)
    chk.setsection("MRGN", bytes(locations))
    # Both enabled players have a start location. Units are made by EUD.
    starts = bytearray()
    for player, x, y in ((0, 384, 1024), (1, 1760, 1696)):
        start = bytearray(36)
        struct.pack_into("<IHHHHHH", start, 0, player + 1, x, y, 214, 0, 0, 0)
        start[16] = player
        starts.extend(start)
    chk.setsection("UNIT", bytes(starts))
    destination = MAPS / "build" / f"probe_{mission}_base.scx"
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the fixture's valid MPQ listfile. mpqapi.create does not populate
    # an internal listfile, and adding reserved (listfile) is not supported.
    destination.write_bytes((VENDOR / "eudplib-basemap.scx").read_bytes())
    with tempfile.NamedTemporaryFile(delete=False, dir=destination.parent, suffix=".chk") as temp:
        temp.write(chk.savechk())
        temp_path = Path(temp.name)
    try:
        archive = mpqapi.MPQ.open(str(destination))
        archive.add_file("staredit\\scenario.chk", str(temp_path))
        archive.compact()
        del archive
    finally:
        temp_path.unlink()
    return destination



# Keep base_map available to older diagnostic builders. Production A/B builds
# now run the official CLI through this compatibility entry point.
from build_official_probes import build_one, inspect_maps, main


if __name__ == "__main__":
    main()
