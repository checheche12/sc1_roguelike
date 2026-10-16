"""Campaign overlay packaging with local, receipt-verified compiled assets.

Never executes the downloaded loader or a game. Packaging outputs live only
in temporary directories; installed CASC and user progress are not modified.
"""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sc1.native_campaign import build_overlay as overlay
from sc1.tests.test_original_campaign import builder


class NativeOverlayTests(unittest.TestCase):
    def test_exact_compiled_chk_and_eight_wavs_round_trip_under_all_campaign_paths(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(overlay,'ROOT',Path(folder)):
            receipt=json.loads(builder.RECEIPT.read_text(encoding='utf-8'))
            result=overlay.build(builder.OUTPUT,receipt['sha256'],builder.RECEIPT)
            manifest_path=Path(result['manifest']);manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
            self.assertEqual(len(manifest['files']),27)
            self.assertTrue(manifest['all_real_sections_byte_identical'])
            self.assertFalse(manifest['scenario_chk_preserved_byte_for_byte'])
            self.assertTrue(manifest['chk_normalization']['strict_section_lengths_valid'])
            self.assertFalse(manifest['native_playtest_verified'])
            self.assertFalse(manifest['eud_in_native_campaign_verified'])
            self.assertFalse(manifest['game_files_modified'])
            self.assertNotIn('--map',manifest['launch_argv'])
            _,raw=builder.read_chk(builder.OUTPUT)
            for prefix in ('Locales/koKR/Assets','','SD'):
                path=manifest_path.parent/'overlay'/prefix/'campaign/Terran/Terran01/staredit/scenario.chk'
                self.assertEqual(path.read_bytes(),raw[:-8])
                self.assertEqual(manifest['chk_normalization']['removed_tail']['bytes'],8)
            for entry in manifest['files']:
                data=(manifest_path.parent/entry['path']).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),entry['sha256'])
            for slot in ('Terran02','Terran03'):
                self.assertFalse(any(slot in entry['path'] for entry in manifest['files']))

    def test_bad_source_hash_and_foreign_source_create_no_overlay(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(overlay,'ROOT',Path(folder)):
            with self.assertRaises(ValueError):overlay.build(builder.OUTPUT,'0'*64,builder.RECEIPT)
            with self.assertRaises(ValueError):overlay.build(Path(folder)/'foreign.scx','0'*64,builder.RECEIPT)
            self.assertEqual(list(Path(folder).iterdir()),[])

    def test_strip_only_final_fake_isom_and_keep_payload_offsets(self):
        prefix=b'VER '+(2).to_bytes(4,'little')+b'\xce\0'
        payload=b'payload\x00' * 5
        prefix+=b'STRx'+len(payload).to_bytes(4,'little')+payload
        raw=prefix+b'ISOM'+(0xF6058684).to_bytes(4,'little')
        result,info=overlay.campaign_chk(raw)
        self.assertEqual(result,prefix)
        self.assertEqual(info['removed_tail']['declared_signed_length'],-167410044)
        self.assertTrue(info['payload_offsets_preserved'])
        self.assertEqual(result.index(payload),raw.index(payload))

    def test_valid_chk_needs_no_change_including_real_isom_section(self):
        raw=b'ISOM'+(4).to_bytes(4,'little')+b'abcd'+b'VER '+(2).to_bytes(4,'little')+b'\xce\0'
        result,info=overlay.campaign_chk(raw)
        self.assertEqual(result,raw);self.assertIsNone(info['removed_tail'])

    def test_other_truncation_or_nonfinal_fake_tail_is_rejected(self):
        bad=[b'ABC',b'STRx'+(9999).to_bytes(4,'little')+b'short',
             b'JUNK'+(0xffffffff).to_bytes(4,'little'),
             b'ISOM'+(0xffffffff).to_bytes(4,'little')+b'VER '+(2).to_bytes(4,'little')+b'\xce\0']
        for raw in bad:
            with self.subTest(raw=raw),self.assertRaises(ValueError):overlay.campaign_chk(raw)

    def test_archive_member_traversal_and_unpinned_loader_are_rejected(self):
        for path in ('../staredit/wav/a.wav','/staredit/wav/a.wav','C:/staredit/wav/a.wav',
                     'staredit/wav/../../escape.wav','arr/units.dat','staredit/wav/a.exe'):
            with self.subTest(path=path), self.assertRaises(ValueError):overlay.safe_member(path)
        pin=json.loads(overlay.PIN_PATH.read_text(encoding='utf-8'))
        with self.assertRaises(ValueError):overlay.verify_loader(b'not the pinned executable',pin)


if __name__=='__main__':unittest.main()
