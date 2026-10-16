"""Derive all-campaign Dat+ requirements by removing only stock BWOnly guards.

The immutable canonical inputs and the historical T01 package stay unchanged.
This is a data transformation, not evidence of successful in-game production.
"""
from __future__ import annotations

from bisect import bisect_left
import json
from pathlib import Path
import struct

from .build_support_dat import (
    CANONICAL_COUNTS, PIN, REFERENCE_EVIDENCE, ROOT, decode, encode,
    reference_assets, sha, validate_field_closure,
)

HERE = Path(__file__).resolve().parent
OUT = HERE / "all_requirements"
EVIDENCE = OUT / "all_requirements_evidence.json"
BW_ONLY = 0xFF24
# Offsets are u16 word indices; requirement buffers are raw byte fields (flags 0).
# Exact source hashes also reject an unknown/new recipe before changing it.
SPECS = {
    "UntR": ("units", 43, 64, (34, 58, 60, 61, 62, 103),
        "18912c586b0a5838fc67dc0f2f0e4ac3b5baa56bde13615878e4b28d7152b92e"),
    "UpgR": ("upgrades", 6, 16, (47, 49, 51, 52, 53, 54),
        "0ec988d5d42bb46893295c6b4ed9d0451a3286bc0c270d92be6cb818af8466fc"),
    "TecR": ("techdata", 4, 16, (24, 25, 27, 29, 30, 31, 32),
        "cde82c22479bcb07bf86844d6c08e74f0232aecd18241f50ed5673617a543d17"),
    "TecU": ("techdata", 5, 17, (28, 32),
        "564b04e033054dae6ef21c46f3aa858f7f8e6af158ccdd7861e7118b624f1498"),
}
ORDERS_BUFFER_SHA = "c49c755a0fb363958bc471fc3ba6efdb9074a408d2bd6490189375cad4277c5d"


def words(raw: bytes) -> tuple[int, ...]:
    if len(raw) % 2:
        raise ValueError("Requirement words must be aligned")
    return struct.unpack("<" + "H" * (len(raw) // 2), raw)


def recipe(buffer: bytes, offset: int) -> tuple[int, ...] | None:
    """Return one terminated recipe, distinguishing disabled from enabled-empty."""
    if not offset:
        return None
    ops = words(buffer)
    if offset >= len(ops):
        raise ValueError("Requirement offset outside buffer")
    try:
        end = ops.index(0xFFFF, offset)
    except ValueError as exc:
        raise ValueError("Unterminated requirement recipe") from exc
    return ops[offset:end + 1]


def remove_bw_only(tag: str, offsets: bytes, buffer: bytes) -> tuple[bytes, bytes, dict]:
    """Delete precisely the known leading no-argument opcode and rebase offsets."""
    table, _, _, affected, expected_sha = SPECS[tag]
    if sha(buffer) != expected_sha:
        raise ValueError(f"{tag}: stock requirement buffer hash changed")
    old_offsets = words(offsets)
    old_words = words(buffer)
    if len(old_offsets) != CANONICAL_COUNTS[table]:
        raise ValueError(f"{tag}: requirement offset entry count changed")
    found = {i for i, offset in enumerate(old_offsets)
             if offset and offset < len(old_words) and old_words[offset] == BW_ONLY}
    if found != set(affected):
        raise ValueError(f"{tag}: unexpected BWOnly owners {sorted(found)}")
    positions = sorted(old_offsets[i] for i in affected)
    if len(set(positions)) != len(positions):
        raise ValueError(f"{tag}: aliased BWOnly entries")
    # No blind replacement: all occurrences must be precisely those known
    # leading opcodes. Arguments, OR branches, upgrade levels and sentinels stay.
    if positions != [i for i, op in enumerate(old_words) if op == BW_ONLY]:
        raise ValueError(f"{tag}: BWOnly occurs outside the known recipe starts")
    if any(offset >= len(old_words) for offset in old_offsets):
        raise ValueError(f"{tag}: invalid requirement offset")
    new_words = tuple(op for i, op in enumerate(old_words) if i not in set(positions))
    new_offsets = tuple(offset - bisect_left(positions, offset) if offset else 0
                        for offset in old_offsets)
    new_buffer = struct.pack("<" + "H" * len(new_words), *new_words)
    new_offset_bytes = struct.pack("<" + "H" * len(new_offsets), *new_offsets)
    changed = []
    for entry, (before, after) in enumerate(zip(old_offsets, new_offsets)):
        old_recipe = recipe(buffer, before)
        new_recipe = recipe(new_buffer, after)
        expected = old_recipe[1:] if entry in affected else old_recipe
        if new_recipe != expected or bool(before) != bool(after):
            raise ValueError(f"{tag}: non-BW condition changed for entry {entry}")
        if entry in affected:
            changed.append({
                "entry_id": entry,
                "old_offset_words": before,
                "new_offset_words": after,
                "before": [f"0x{x:04x}" for x in old_recipe],
                "after": [f"0x{x:04x}" for x in new_recipe],
            })
    return new_offset_bytes, new_buffer, {
        "tag": tag, "table": table, "removed_opcode": "0xff24",
        "removed_count": len(positions), "removed_word_positions": positions,
        "old_buffer_size": len(buffer), "new_buffer_size": len(new_buffer),
        "old_buffer_sha256": sha(buffer), "new_buffer_sha256": sha(new_buffer),
        "old_offsets_sha256": sha(offsets), "new_offsets_sha256": sha(new_offset_bytes),
        "recipes": changed,
    }


def derive_assets(canonical: dict[str, bytes]) -> tuple[dict[str, bytes], list[dict]]:
    """Return only the three changed files; preserve every other DAT field."""
    validate_field_closure(canonical)
    modified = {}
    reports = []
    for tag, (table, offset_field, buffer_field, _, _) in SPECS.items():
        name = f"arr/{table}.dat"
        count, fields = decode(modified.get(name, canonical[name]))
        if fields[offset_field][0] != 1 or fields[buffer_field][0] != 0:
            raise ValueError(f"{tag}: requirement field type changed")
        offsets, buffer, report = remove_bw_only(
            tag, fields[offset_field][1], fields[buffer_field][1])
        fields[offset_field] = (1, offsets)
        fields[buffer_field] = (0, buffer)
        modified[name] = encode(count, fields)
        reports.append(report)
    # orders and buttons are intentionally retained byte for byte. The stock
    # merge-to-Dark-Archon BW gate is TecU entry 28, already transformed above.
    _, order_fields = decode(canonical["arr/orders.dat"])
    if sha(order_fields[32][1]) != ORDERS_BUFFER_SHA or BW_ONLY in words(order_fields[32][1]):
        raise ValueError("Stock order requirements changed; explicit review required")
    allowed = {"units": {43, 64}, "upgrades": {6, 16}, "techdata": {4, 5, 16, 17}}
    for name, transformed in modified.items():
        old_count, old_fields = decode(canonical[name])
        new_count, new_fields = decode(transformed)
        table = Path(name).stem
        if old_count != new_count or old_fields.keys() != new_fields.keys():
            raise ValueError(f"{table}: DAT topology changed")
        if any(old_fields[field] != new_fields[field]
               for field in old_fields.keys() - allowed[table]):
            raise ValueError(f"{table}: a non-requirement field changed")
    complete = dict(canonical)
    complete.update(modified)
    validate_field_closure(complete)
    return modified, reports


def expected_assets() -> dict[str, bytes]:
    """Pure reproducible package overlay; no output writes or game access."""
    assets, _ = derive_assets(reference_assets())
    return assets


def build(out: Path = OUT) -> dict:
    """Write the isolated all-campaign overlay and its source/field proof."""
    canonical = reference_assets()
    assets, buffers = derive_assets(canonical)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, data in sorted(assets.items()):
        target = out / Path(name).name
        target.write_bytes(data)
        try:
            display_path = target.relative_to(ROOT).as_posix()
        except ValueError:
            display_path = str(target.resolve())
        rows.append({"name": name, "path": display_path, "size": len(data),
                     "sha256": sha(data), "source_sha256": sha(canonical[name])})
    report = {
        "schema": "sc1_all_campaign_requirements_v1",
        "scope": "All-campaign package overlay only; historical T01 inputs unchanged",
        "tatti_commit": PIN,
        "canonical_reference_evidence_sha256": sha(REFERENCE_EVIDENCE.read_bytes()),
        "builder_sha256": sha(Path(__file__).read_bytes()),
        "source_assets": [{"name": name, "sha256": sha(data)}
                          for name, data in sorted(canonical.items())],
        "assets": rows, "requirements": buffers,
        "total_removed_bw_only": sum(row["removed_count"] for row in buffers),
        "changed_fields": {"units": [43, 64], "upgrades": [6, 16],
                           "techdata": [4, 5, 16, 17]},
        "preserved": {
            "all_other_dat_fields": True, "buttons_byte_identical": True,
            "orders_byte_identical": True, "costs_and_stats": True,
            "buildings_addons_research_state_conditions": True,
            "disabled_and_enabled_empty_requirements": True,
            "upgrade_level_branches_and_terminators": True,
            "techdata_broodwar_flag_field_10": True,
            "upgrades_broodwar_flag_field_11": True,
            "campaign_index_and_game_is_bw": "Not modified by this builder",
        },
        "evidence_scope": {
            "canonical_bytes_and_exact_condition_preservation_verified": True,
            "in_game_button_visibility_verified": False,
            "in_game_training_morph_research_verified": False,
            "separate_tech_upgrade_BW_flags_and_engine_guards": "Unchanged; live verification still required",
        },
        "primary_references": [
            {"url": "https://github.com/neivv/tatti3/blob/" + PIN + "/datspec.md",
             "use": "Dat+ requirement offset and raw buffer field format"},
            {"url": "https://github.com/neivv/aise/blob/master/src/datreq.rs",
             "use": "Opcode 0xff24 is no-argument BwOnly; not an original-engine execution proof"},
        ],
    }
    (out / EVIDENCE.name).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                   encoding="utf-8")
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps({"assets": result["assets"],
                      "removed_bw_only": result["total_removed_bw_only"]}, indent=2))
