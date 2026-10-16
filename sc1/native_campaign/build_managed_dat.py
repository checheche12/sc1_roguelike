"""Build minimal SAMASE Dat+ tables from the read-only vanilla CASC extracts.

No game, user progress database, or installed file is opened by this builder.
The one representation change is units field 0x2b: vanilla's unused ffff
placeholders become offsets into the exact stock unit-requirements buffer.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "managed_dat"
TATTI = HERE / "dat_sources/tatti3"
PIN = "eb940dab410e9e197db9634322e91fb67a0b7f0f"
FGP_SHA = "1a64ce14dbb7e947ac3c4ff3e929f7b02bca6f1da2746ec7728d449180177c68"
REQ_SHA = "18912c586b0a5838fc67dc0f2f0e4ac3b5baa56bde13615878e4b28d7152b92e"
SOURCES = {
    "units": (228, 19876, "da2ee6f116b77329048ec6be9e02721a527fde23d4b05b1b1336e634490abcba"),
    "weapons": (130, 5460, "80de165015519f9bed46ea8858195c2d2d0120b65b9e55e1c0a50b19135f4b62"),
}
# bytes per entry, then the few vanilla-only subset ranges. Multi-component
# u16 fields retain their component width in the Dat+ descriptor flags.
UNIT_WIDTHS = [1,2,2,2,4,1,1,2,4,1,1,1,1,1,1,1,1,1,1,1,1,1,4,1,1,1,1,1,1,2,2,2,2,2,2,2,4,4,8,2,2,2,2,2,1,1,1,1,1,2,2,2,1,2]
WEAPON_WIDTHS = [2,4,1,2,4,4,1,1,1,1,1,2,2,2,2,2,1,1,1,1,1,1,2,2]
SUBSETS = {3:(106,96), 29:(0,106), 32:(0,106), 33:(0,106), 34:(0,106), 35:(0,106), 37:(106,96)}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_bytes(name: str) -> bytes:
    data = (ROOT / f"sc1/campaign_sources/raw/arr/{name}.dat").read_bytes()
    _, length, digest = SOURCES[name]
    if len(data) != length or sha(data) != digest:
        raise ValueError(f"{name}: original CASC source pin mismatch")
    return data


def legacy_fields(name: str, data: bytes) -> dict[int, tuple[int, bytes]]:
    entries, size, _ = SOURCES[name]
    if len(data) != size:
        raise ValueError("incorrect vanilla DAT length")
    widths = UNIT_WIDTHS if name == "units" else WEAPON_WIDTHS
    result = {}
    pos = 0
    for field, width in enumerate(widths):
        start, count = SUBSETS.get(field, (0,entries)) if name == "units" else (0,entries)
        default = (228).to_bytes(width,"little") if name == "units" and field == 3 else bytes(width)
        body = default * start + data[pos:pos + width*count] + default * (entries-start-count)
        pos += width*count
        scalar_width = 2 if name == "units" and field in (36,37,38) else width
        result[field] = ({1:0,2:1,4:2}[scalar_width], body)
    if pos != len(data):
        raise ValueError("legacy schema does not consume the complete source")
    return result


def original_requirements() -> tuple[bytes,bytes,dict[int,tuple[int,...]]]:
    data = (TATTI / "Resources/firegraft.fgp").read_bytes()
    if sha(data) != FGP_SHA:
        raise ValueError("official stock Firegraft resource pin mismatch")
    pos = 0
    sections = {}
    while pos < len(data):
        tag, length = struct.unpack_from("<4sI", data, pos)
        pos += 8
        if tag in sections or pos + length > len(data):
            raise ValueError("invalid Firegraft section")
        sections[tag] = data[pos:pos+length]
        pos += length
    section = sections[b"UntR"]
    count, = struct.unpack_from("<H", section)
    offsets = bytearray(228*2)
    buffer = bytearray(b"\0\0")
    expected = {}
    seen = set()
    pos = 2
    for _ in range(count):
        unit, size = section[pos:pos+2]
        end = pos+2+size*2
        enabled = section[end]
        ops = section[pos+2:end]
        if unit >= 228 or unit in seen:
            raise ValueError("invalid or duplicate requirement unit")
        seen.add(unit)
        if enabled:
            buffer += struct.pack("<H",unit)
            struct.pack_into("<H",offsets,unit*2,len(buffer)//2)
            if not ops.endswith(b"\xff\xff"):
                ops += b"\xff\xff"
            buffer += ops
            expected[unit] = struct.unpack("<"+"H"*(len(ops)//2),ops)
        pos=end+1
    buffer += b"\xff\xff"
    if pos != len(section) or len(expected) != 91 or sha(buffer) != REQ_SHA:
        raise ValueError("stock requirements oracle mismatch")
    return bytes(offsets), bytes(buffer), expected


def encode(entries: int, fields: dict[int,tuple[int,bytes]]) -> bytes:
    # Minor 10 is the pinned official writer's current minor; it is not a
    # request for additional editor defaults. All bytes are specified here.
    header = bytearray(struct.pack("<IHHII",0x2b746144,1,10,entries,len(fields)))
    payload = bytearray()
    offset = 16+12*len(fields)
    for field,(flags,body) in sorted(fields.items()):
        header += struct.pack("<HHII",field,flags,offset+len(payload),len(body))
        payload += body
    return bytes(header+payload)


def build() -> dict:
    offsets, buffer, requirements = original_requirements()
    assets = []
    preserved_fields = 0
    for name,(entries,_,_) in SOURCES.items():
        raw = source_bytes(name)
        fields = legacy_fields(name,raw)
        preserved_fields += len(fields) - (name == "units")
        if name == "units":
            if fields[43][1] != b"\xff\xff"*228:
                raise ValueError("vanilla requirement field is no longer the unused placeholder")
            fields[43] = (1,offsets)
            fields[64] = (1,buffer)
        encoded = encode(entries,fields)
        target = OUT / f"arr/{name}.dat"
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(encoded)
        assets.append({"name":f"arr/{name}.dat","path":target.relative_to(ROOT).as_posix(),"sha256":sha(encoded),"bytes":len(encoded),"entry_count":entries,"field_count":len(fields),"source_sha256":sha(raw)})
    tracked = [Path(__file__).resolve(), ROOT/"sc1/tests/test_managed_dat.py", TATTI/"source_pin.json", *sorted(TATTI.rglob("*.cs")),TATTI/"datspec.md",TATTI/"Resources/firegraft.fgp",HERE/"dat_sources/stock_requirements_oracle.json"]
    oracle = json.loads((HERE/"dat_sources/stock_requirements_oracle.json").read_text(encoding="utf-8"))
    if oracle["requirements_sha256"] != REQ_SHA or not oracle["exact_contiguous_match"]:
        raise ValueError("stock EXE requirements evidence missing")
    receipt = {
        "schema_version":1,"status":"offline_built_live_unverified","managed_dat_assets":assets,
        "stock_values_preserved":True,"stock_values_scope":"All 77 gameplay fields retain every legacy entry/component byte. Units 0x2b unused ffff placeholders are semantically reencoded; subset padding uses the pinned official defaults.",
        "requirements_preserved":True,"requirements_scope":"Units 0x2b/0x40 reproduce the exact 1090-byte stock EXE buffer: 91 enabled units, 137 disabled. No other DAT/tech/upgrade/order requirements are overridden.",
        "requirements_sha256":REQ_SHA,"requirements_enabled":len(requirements),"requirements_disabled":228-len(requirements),
        "representation_exceptions":[{"table":"units","field":43,"before":"228 unused 0xffff words","after":"u16 indices into added field 0x40","reason":"SAMASE Dat+ requires an explicit unit requirements buffer; do not retain legacy placeholders as offsets."}],
        "unchanged_gameplay_field_count":preserved_fields,"entry_counts":{"units":228,"weapons":130},
        "extra_fields":{"units":[64],"weapons":[]},"reserved_editor_entries_added":False,
        "source_repository":"neivv/tatti3","source_commit":PIN,
        "path_evidence":f"https://github.com/neivv/tatti3/blob/{PIN}/GameData/GameData.cs#L533-L542",
        "format_evidence":f"https://github.com/neivv/tatti3/blob/{PIN}/datspec.md",
        "sources":[{"path":p.relative_to(ROOT).as_posix(),"sha256":sha(p.read_bytes())} for p in tracked],
        "native_play_verified":False,
    }
    (OUT/"managed_dat_evidence.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return receipt


if __name__ == "__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
