"""Regression proof for the isolated all-campaign BWOnly transformation."""
from pathlib import Path
import json
import struct
import tempfile
import unittest

from sc1.native_campaign import build_all_requirements as allreq
from sc1.native_campaign.build_support_dat import (
    REFERENCE, decode, encode, reference_assets, sha, validate_field_closure,
)


class AllRequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = reference_assets()
        cls.derived, cls.reports = allreq.derive_assets(cls.original)

    def test_exact_overlay_and_all_other_fields_unchanged(self):
        self.assertEqual(set(self.derived),
                         {"arr/units.dat", "arr/upgrades.dat", "arr/techdata.dat"})
        allowed = {"units": {43, 64}, "upgrades": {6, 16}, "techdata": {4, 5, 16, 17}}
        full = dict(self.original)
        full.update(self.derived)
        validate_field_closure(full)
        for name, before in self.original.items():
            if name not in self.derived:
                self.assertEqual(full[name], before)
                continue
            old_n, old_fields = decode(before)
            new_n, new_fields = decode(full[name])
            self.assertEqual(old_n, new_n)
            self.assertEqual(old_fields.keys(), new_fields.keys())
            changed = {field for field in old_fields if old_fields[field] != new_fields[field]}
            self.assertEqual(changed, allowed[Path(name).stem])
        # These BW metadata flags are not requirement opcodes and are not
        # silently cleared by the builder.
        for name, field in [("techdata", 10), ("upgrades", 11)]:
            self.assertEqual(decode(self.original[f"arr/{name}.dat"])[1][field],
                             decode(full[f"arr/{name}.dat"])[1][field])

    def test_only_21_known_leading_words_deleted(self):
        self.assertEqual(sum(report["removed_count"] for report in self.reports), 21)
        for tag, (table, off_field, buf_field, owners, _) in allreq.SPECS.items():
            old = decode(self.original[f"arr/{table}.dat"])[1]
            new = decode(self.derived[f"arr/{table}.dat"])[1]
            old_offsets = allreq.words(old[off_field][1])
            old_words = allreq.words(old[buf_field][1])
            positions = {old_offsets[i] for i in owners}
            self.assertEqual(allreq.words(new[buf_field][1]),
                             tuple(value for i, value in enumerate(old_words) if i not in positions))
            self.assertEqual(len(old[buf_field][1]) - len(new[buf_field][1]), 2 * len(owners))
            self.assertNotIn(0xFF24, allreq.words(new[buf_field][1]))

    def test_building_addon_and_lurker_research_constraints_preserved(self):
        fields = decode(self.derived["arr/units.dat"])[1]
        offsets = allreq.words(fields[43][1])
        expected = {
            34: (0xff02, 111, 0xff08, 0xff05, 112, 0xffff),
            58: (0xff02, 114, 0xff08, 0xff05, 0xff04, 115, 123, 0xffff),
            60: (0xff02, 167, 0xffff),
            61: (0xff02, 160, 165, 0xffff),
            62: (0xff02, 43, 137, 0xffff),
            103: (0xff02, 38, 0xff25, 32, 0xffff),
        }
        for entry, ops in expected.items():
            self.assertEqual(allreq.recipe(fields[64][1], offsets[entry]), ops)
        # Dark Archon merge still requires the selected Dark Templar.
        tech = decode(self.derived["arr/techdata.dat"])[1]
        use_offsets = allreq.words(tech[5][1])
        self.assertEqual(allreq.recipe(tech[17][1], use_offsets[28]),
                         (0xff02, 61, 0xffff))
        self.assertEqual(allreq.recipe(tech[17][1], use_offsets[32]),
                         (0xff0f, 0xff02, 38, 0xffff))

    def test_every_full_recipe_including_upgrade_branches_is_preserved(self):
        # Bound each complete entry by the next entry's ID marker, rather than
        # the first ffff, so all three upgrade-level branches are inspected.
        empty_count = disabled_count = 0
        for tag, (table, off_field, buf_field, owners, _) in allreq.SPECS.items():
            old = decode(self.original[f"arr/{table}.dat"])[1]
            new = decode(self.derived[f"arr/{table}.dat"])[1]
            a, b = allreq.words(old[off_field][1]), allreq.words(new[off_field][1])
            aw, bw = allreq.words(old[buf_field][1]), allreq.words(new[buf_field][1])
            old_ends = {x: y - 1 for x, y in zip(sorted(set(a) - {0}), sorted(set(a) - {0})[1:])}
            new_ends = {x: y - 1 for x, y in zip(sorted(set(b) - {0}), sorted(set(b) - {0})[1:])}
            for entry, (before, after) in enumerate(zip(a, b)):
                self.assertEqual(bool(before), bool(after))
                if not before:
                    disabled_count += 1
                    continue
                old_ops = aw[before:old_ends.get(before, len(aw) - 1)]
                new_ops = bw[after:new_ends.get(after, len(bw) - 1)]
                self.assertEqual(new_ops, old_ops[1:] if entry in owners else old_ops)
                if old_ops == (0xffff,):
                    empty_count += 1
                    self.assertNotEqual(after, 0)
        self.assertGreater(disabled_count, 0)
        order_fields = decode(self.original["arr/orders.dat"])[1]
        empty_count += sum(allreq.recipe(order_fields[32][1], offset) == (0xffff,)
                           for offset in allreq.words(order_fields[17][1]))
        # The canonical writer migrates the two stock empty order recipes to
        # explicit guards. Disabled 0 still must not be treated as empty.
        self.assertIsNone(allreq.recipe(b"\0\0\xff\xff", 0))
        self.assertEqual(allreq.recipe(b"\0\0\xff\xff", 1), (0xffff,))
        self.assertNotIn("arr/orders.dat", self.derived)

    def test_unknown_source_and_wrong_field_type_fail_closed(self):
        corrupt = dict(self.original)
        n, fields = decode(corrupt["arr/units.dat"])
        raw = bytearray(fields[64][1])
        raw[10] ^= 1
        fields[64] = (0, bytes(raw))
        corrupt["arr/units.dat"] = encode(n, fields)
        with self.assertRaisesRegex(ValueError, "buffer hash changed"):
            allreq.derive_assets(corrupt)
        corrupt = dict(self.original)
        n, fields = decode(corrupt["arr/units.dat"])
        fields[64] = (1, fields[64][1])
        corrupt["arr/units.dat"] = encode(n, fields)
        with self.assertRaises(ValueError):
            allreq.derive_assets(corrupt)

    def test_offset_aliases_and_out_of_range_rejected(self):
        fields = decode(self.original["arr/units.dat"])[1]
        offsets = bytearray(fields[43][1])
        struct.pack_into("<H", offsets, 58 * 2, allreq.words(offsets)[34])
        with self.assertRaisesRegex(ValueError, "aliased"):
            allreq.remove_bw_only("UntR", bytes(offsets), fields[64][1])
        offsets = bytearray(fields[43][1])
        struct.pack_into("<H", offsets, 0, 65535)
        with self.assertRaisesRegex(ValueError, "invalid requirement offset"):
            allreq.remove_bw_only("UntR", bytes(offsets), fields[64][1])

    def test_reproducible_outputs_manifest_and_immutable_sources(self):
        before = {name: sha(raw) for name, raw in self.original.items()}
        self.assertEqual(allreq.expected_assets(), self.derived)
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            evidence = allreq.build(out)
            for row in evidence["assets"]:
                actual = Path(row["path"]).read_bytes()
                self.assertEqual(actual, self.derived[row["name"]])
                self.assertEqual(sha(actual), row["sha256"])
            self.assertEqual(json.loads((out / allreq.EVIDENCE.name).read_text(encoding="utf-8")), evidence)
            self.assertFalse(evidence["evidence_scope"]["in_game_training_morph_research_verified"])
            self.assertEqual(evidence["total_removed_bw_only"], 21)
        self.assertEqual({name: sha(raw) for name, raw in reference_assets().items()}, before)

    def test_checked_in_overlay_matches_reproducible_bytes(self):
        evidence = json.loads(allreq.EVIDENCE.read_text(encoding="utf-8"))
        for row in evidence["assets"]:
            self.assertEqual((allreq.ROOT / row["path"]).read_bytes(), self.derived[row["name"]])
            self.assertEqual(row["sha256"], sha(self.derived[row["name"]]))
        self.assertEqual(evidence["builder_sha256"], sha(Path(allreq.__file__).read_bytes()))


if __name__ == "__main__":
    unittest.main()
