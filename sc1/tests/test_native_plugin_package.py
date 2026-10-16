"""Guard native original-format controls and loader/package boundaries."""
from __future__ import annotations
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from sc1.native_campaign import package_native_plugin as package


class NativePluginPackageTests(unittest.TestCase):
    def test_stock_control_keeps_active_pointer_and_exact_original_bytes(self):
        raw = package.SOURCE.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            current = root / 'current_build.json'
            current.write_bytes(b'{"manifest":"existing.json"}\n')
            (root / 'loader_pin.json').write_text(json.dumps({'sha256': 'pinned'}))
            with patch.object(package, 'ROOT', root):
                report = package.stock_control()
            manifest = json.loads(Path(report['manifest']).read_text(encoding='utf-8'))
            build = Path(report['manifest']).parent
            self.assertEqual(len(manifest['files']), 3)
            self.assertEqual({item['path'] for item in manifest['files']},
                             {'overlay/' + (prefix + '/' if prefix else '') + package.MISSION
                              for prefix in package.PREFIXES})
            for item in manifest['files']:
                self.assertEqual((build / item['path']).read_bytes(), raw)
                self.assertEqual(item['sha256'], package.SOURCE_HASH)
            self.assertEqual(current.read_bytes(), b'{"manifest":"existing.json"}\n')
            self.assertFalse(report['activated'])
            self.assertFalse(manifest['in_game_choices'])
            self.assertNotIn('overlay/staredit/scenario.chk', {item['path'] for item in manifest['files']})

    def test_stock_control_rejects_changed_source(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.chk'
            source.write_bytes(package.SOURCE.read_bytes() + b'altered')
            with patch.object(package, 'SOURCE', source):
                with self.assertRaisesRegex(ValueError, 'hash changed'):
                    package.stock_control()

    def test_original_format_is_accepted_and_expansion_payload_rejected(self):
        sections = package.verify_plain_chk(package.SOURCE.read_bytes())
        self.assertEqual(len(sections[b'MRGN']), 64 * 20)
        expansion = package.SC1 / 'campaign/build/terran01/input.chk'
        with self.assertRaisesRegex(ValueError, 'VER59'):
            package.verify_plain_chk(expansion.read_bytes())

    def test_normalized_eud_payload_is_still_rejected(self):
        # This test deliberately uses the recorded failed EUD candidate rather
        # than assuming the active package will always remain that candidate.
        candidate = package.ROOT / 'builds/terran01_20261014_085143_782418_4e9294e49182/overlay' / package.MISSION
        with self.assertRaisesRegex(ValueError, 'VER59'):
            package.verify_plain_chk(candidate.read_bytes())

    def test_gated_map_cannot_be_packaged_without_dll(self):
        with self.assertRaisesRegex(ValueError, 'requires its native plugin'):
            package.write_package(package.SOURCE.read_bytes(), mode='native_plugin', inputs={})

    def test_stock_control_cannot_replace_mod_or_include_dll(self):
        for flags in ({'activate': True}, {'plugin': b'a dll'}):
            with self.assertRaisesRegex(ValueError, 'cannot replace'):
                package.write_package(package.SOURCE.read_bytes(), mode='stock_control', inputs={}, **flags)

    def test_executable_is_not_accepted_as_plugin(self):
        pin = json.loads((package.ROOT / 'loader_pin.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError, r'x64 PE32\+ DLL'):
            package.verify_dll((package.ROOT / pin['local_filename']).read_bytes())

    def test_truncated_and_duplicate_chk_sections_are_rejected(self):
        raw = package.SOURCE.read_bytes()
        for invalid in (raw[:-1], raw + b'VER \x02\x00\x00\x00\x3b\x00'):
            with self.assertRaises(ValueError):
                package.sections(invalid)

    def test_actual_native_plugin_matches_build_and_manager_receipts(self):
        chk, plugin, inputs = package.native_inputs(
            package.ROOT / 'plain_chk_evidence.json',
            package.ROOT / 'plugin/all_campaign_native_build_evidence.json')
        # The current original-format T01 control includes the R469 marker.
        # All 63 campaign overlays have their own independent map audit.
        self.assertEqual(package.sha(chk), '22525670aa6a18bb3977d2b62f3b2f7b0ec083242d0c3f6e86743baffcf5ff30')
        self.assertEqual(inputs['runtime_catalog_sha256'], package.CATALOG_HASH)
        self.assertIn('samase_plugin_init', package.verify_dll(plugin)['exports'])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'loader_pin.json').write_text(json.dumps({'sha256': 'pinned'}))
            with patch.object(package, 'ROOT', root):
                report = package.write_package(chk, mode='native_plugin', inputs=inputs, plugin=plugin)
            manifest = json.loads(Path(report['manifest']).read_text(encoding='utf-8'))
            entries = {entry['path']: entry for entry in manifest['files']}
            self.assertEqual(len(entries), 16)
            expected_dat_names = {
                'units', 'weapons', 'flingy', 'sprites', 'images', 'upgrades',
                'techdata', 'portdata', 'mapdata', 'orders', 'buttons',
            }
            self.assertEqual({name.removeprefix('overlay/arr/').removesuffix('.dat')
                              for name in entries if name.startswith('overlay/arr/')}, expected_dat_names)
            for name in package.REQUIRED_DAT_NAMES:
                asset = (Path(report['manifest']).parent / 'overlay' / name).read_bytes()
                info = package.verify_loader_dat(asset, name)
                self.assertEqual(info['entries'], package.REQUIRED_DAT_NAMES[name])
            self.assertEqual((Path(report['manifest']).parent / 'overlay/samase/plugins').read_bytes(),
                             b'samase/native_plugin.dll\n')
            self.assertTrue(manifest['in_game_choices'])
            self.assertEqual(manifest['choice_interface'], 'native GameMenu button dialog')
            self.assertFalse(manifest['physical_choice_units'])
            self.assertFalse(manifest['native_playtest_verified'])
            self.assertFalse((root / 'current_build.json').exists())
            self.assertNotIn('overlay/staredit/scenario.chk', entries)

    def test_native_build_receipt_rejects_changed_file(self):
        path = package.ROOT / 'plugin/native_plugin.cpp'
        with self.assertRaisesRegex(ValueError, 'changed since'):
            package.checked_file(path, '0' * 64)

    def test_every_required_dat_must_be_present_before_packaging(self):
        chk, plugin, inputs = package.native_inputs(
            package.ROOT / 'plain_chk_evidence.json',
            package.ROOT / 'plugin/all_campaign_native_build_evidence.json')
        # Independent list from the pinned loader's eleven-entry read loop.
        for name in ('units', 'weapons', 'flingy', 'sprites', 'images', 'upgrades',
                     'techdata', 'portdata', 'mapdata', 'orders', 'buttons'):
            incomplete = dict(inputs)
            for key in ('managed_dat_assets', 'support_dat_assets'):
                incomplete[key] = [row for row in inputs[key] if row['name'] != f'arr/{name}.dat']
            with self.subTest(missing=name), tempfile.TemporaryDirectory() as folder:
                with patch.object(package, 'ROOT', Path(folder)):
                    with self.assertRaisesRegex(ValueError, 'complete 11-file'):
                        package.write_package(chk, mode='native_plugin', inputs=incomplete, plugin=plugin)

    def test_legacy_support_dat_cannot_replace_extended_format(self):
        for name in ('flingy', 'sprites', 'images', 'upgrades', 'techdata', 'portdata', 'mapdata', 'orders'):
            raw = (package.SC1 / 'campaign_sources/raw/arr' / (name + '.dat')).read_bytes()
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, 'Dat\\+'):
                package.verify_managed_dat(raw, f'arr/{name}.dat')

    def test_previous_failed_units_asset_is_rejected(self):
        # This exact user-executed candidate had all eleven files but only
        # units 0x42, and failed next on the loader's hexadecimal Units 41.
        failed = package.ROOT / 'builds/native_plugin_20261014_163407_126230_93dfd955d3fd/overlay/arr/units.dat'
        with self.assertRaises(ValueError):
            package.verify_loader_dat(failed.read_bytes(), 'arr/units.dat')

    def test_every_stock_extended_field_is_required_before_packaging(self):
        from sc1.native_campaign import build_support_dat as support
        assets = {**support.expected_assets(), **support.expected_managed_assets()}
        # Independent list from the pinned editor's GameData constructor and
        # LoadButtons; cover the defaults after the first observed failure.
        for name, fields in (('units', range(0x41, 0x56)),
                             ('upgrades', range(0x11, 0x1c)),
                             ('techdata', range(0x12, 0x15))):
            raw = assets[f'arr/{name}.dat']
            count = struct.unpack_from('<I', raw, 12)[0]
            for field in fields:
                # Removing the directory record leaves its unreachable data
                # in place. All remaining offsets stay valid and disjoint.
                records = [raw[16+i*12:28+i*12] for i in range(count)
                           if struct.unpack_from('<H', raw, 16+i*12)[0] != field]
                self.assertEqual(len(records), count-1)
                invalid = bytearray(raw)
                struct.pack_into('<I', invalid, 12, count-1)
                invalid[16:16+(count-1)*12] = b''.join(records)
                with self.subTest(table=name, field=hex(field)):
                    with self.assertRaisesRegex(ValueError, 'missing loader-required fields: ' + hex(field)):
                        package.verify_loader_dat(invalid, f'arr/{name}.dat')


if __name__ == '__main__':
    unittest.main()
