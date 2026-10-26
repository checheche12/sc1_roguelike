"""Publication rejects mixed catalogs, incomplete effect coverage and source drift."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from sc1 import build_portable
from sc1.campaign.runtime_catalog import load_catalog
from sc1.native_campaign import build_native_runtime as native
from sc1.native_campaign import package_all_campaigns as package


class ReworkPackagingTests(unittest.TestCase):
    def setUp(self):
        self.original=load_catalog(Path(native.ROOT.parent/'campaign/runtime_talents.json'))
        self.legacy=load_catalog()
        self.rework=load_catalog(expected_version=2)
        for kind in ('talents','curses'):
            for item in self.rework[kind]:item['implemented']=True

    def test_layout_extends_both_historical_catalogs(self):
        contract=native.validate_catalog_bundle(self.original,self.legacy,self.rework)
        self.assertEqual((contract['implemented_talents'],contract['implemented_curses']),(562,50))
        self.assertEqual((contract['mailbox_words'],contract['snapshot_words'],contract['manual_rank_slots_used']),(128,65,21))
        self.assertEqual(contract['legacy_wire_versions'],[1])

    def test_native_copy_matches_the_catalog_used_by_the_manager(self):
        from sc1.campaign.generate_native_catalog import render
        header=(native.PLUGIN/'include/frozen_catalog.generated.h').read_text(encoding='utf8')
        native.validate_native_catalog(self.rework,header)
        self.assertEqual(header,render(self.rework))

    def test_qa57_goliath_and_tank_stale_descriptions_block_release(self):
        from sc1.campaign.generate_native_catalog import render
        for index,old_text in ((293,'시즈 탱크가 같은 적을 2회 공격할 때마다 그 적에게 원래 공격의 700% 추가 피해. 공성 모드로 이동하며 정지 시 사격합니다.'),
                               (294,'골리앗의 일반 공격 피해 +100%.')):
            with self.subTest(index=index):
                old=copy.deepcopy(self.rework)
                old['talents'][index]['description']=old_text
                with self.assertRaisesRegex(ValueError,'Generated native catalog differs'):
                    native.validate_native_catalog(self.rework,render(old))

    def test_all_native_display_fields_block_release_when_stale(self):
        from sc1.campaign.generate_native_catalog import render
        for kind in ('talents','curses'):
            for field,value in (('name','stale name'),('description','stale effect'),('rarity','common')):
                with self.subTest(kind=kind,field=field):
                    old=copy.deepcopy(self.rework)
                    item=next(x for x in old[kind] if x.get('rework_revision')==5 and x['rarity']!='common')
                    item[field]=value
                    with self.assertRaisesRegex(ValueError,'Generated native catalog differs'):
                        native.validate_native_catalog(self.rework,render(old))

    def test_pending_effect_or_rewritten_old_meaning_cannot_publish(self):
        for kind,change in (('talents',lambda x:x.update(implemented=False)),
                            ('curses',lambda x:x.update(implemented=False))):
            broken=copy.deepcopy(self.rework);change(broken[kind][-1])
            with self.assertRaises(ValueError):native.validate_catalog_bundle(self.original,self.legacy,broken)
        broken=copy.deepcopy(self.rework);broken['talents'][0]['description']='Changed historical interpretation'
        with self.assertRaises(ValueError):native.validate_catalog_bundle(self.original,self.legacy,broken)
        broken=copy.deepcopy(self.rework);manuals=[x for x in broken['talents'] if x.get('repeatable')];manuals[1]['rank_slot']=manuals[0]['rank_slot']
        with self.assertRaises(ValueError):native.validate_catalog_bundle(self.original,self.legacy,broken)

    def test_runtime_receipt_must_pin_all_catalogs_and_real_v2_interop(self):
        with tempfile.TemporaryDirectory(prefix='rework-package-',dir=package.ROOT/'build') as folder:
            root=Path(folder);campaign=root/'campaign';campaign.mkdir();(root/'native_campaign').mkdir()
            pins={}
            for name,value in zip(native.CATALOG_NAMES,(self.original,self.legacy,self.rework)):
                path=campaign/name;raw=json.dumps(value,ensure_ascii=False).encode();path.write_bytes(raw)
                pins[name]={'path':str(path),'sha256':hashlib.sha256(raw).hexdigest()}
            receipt={'growth_protocol':'PHC1 v2','growth_wire_version':2,'catalogs':pins,
                     'growth_contract':native.validate_catalog_bundle(self.original,self.legacy,self.rework),
                     'rework_catalog':pins['runtime_talents_v5.json']['path'],'rework_catalog_sha256':pins['runtime_talents_v5.json']['sha256'],
                     'mailbox_offline_tests':[{'name':'rework_v2_python_native','result':{'passed':True}}],
                     'native_dialog_ui_tests':{'passed':True,'groups':19,'production_translation_units_used':True}}
            with patch.object(package,'ROOT',root/'native_campaign'):
                path,raw,all_pins,contract=package.runtime_catalog_inputs(receipt)
                self.assertEqual(path,campaign/'runtime_talents_v5.json');self.assertEqual(len(all_pins),3)
                for field in ('mailbox_offline_tests','growth_contract','native_dialog_ui_tests'):
                    broken=copy.deepcopy(receipt);broken[field]=[] if field=='mailbox_offline_tests' else {}
                    with self.assertRaises(ValueError):package.runtime_catalog_inputs(broken)
                broken=copy.deepcopy(receipt);broken['catalogs'].pop('runtime_talents_all.json')
                with self.assertRaises(ValueError):package.runtime_catalog_inputs(broken)
                (campaign/'runtime_talents_v5.json').write_bytes(raw+b' ')
                with self.assertRaises(ValueError):package.runtime_catalog_inputs(receipt)

    def test_portable_closure_keeps_frozen_data_and_excludes_player_files(self):
        with tempfile.TemporaryDirectory(prefix='rework-portable-') as folder:
            root=Path(folder)
            paths=['sc1/__init__.py','sc1/portable_runtime.py','sc1/campaign/rework_growth.py','sc1/campaign/talent_campaign_policy.py','sc1/bridge/protocol.py','sc1/manager/store.py']
            paths+=['sc1/campaign/'+name for name in build_portable.CAMPAIGN_DATA]
            paths+=['sc1/effect_lab/'+name for name in build_portable.LAB_ASSETS]
            for name in paths:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(name.encode())
            for name in ('sc1/data/player.sqlite3','sc1/data/talent-site/board.json','sc1/campaign/autosave.json'):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'private')
            selected={path.relative_to(root).as_posix() for path in build_portable.runtime_sources(root)}
            self.assertEqual(selected,set(paths))
            manifest={'growth_wire_version':2,'inputs':{'manager_sources':[{'path':name,'sha256':build_portable.sha(root/name)} for name in paths if name not in ('sc1/__init__.py','sc1/portable_runtime.py')]}}
            build_portable.verify_manager_closure(root,manifest)
            broken=copy.deepcopy(manifest);broken['inputs']['manager_sources']=[x for x in broken['inputs']['manager_sources'] if not x['path'].endswith('runtime_talents_v5.json')]
            with self.assertRaises(ValueError):build_portable.verify_manager_closure(root,broken)
            (root/'sc1/campaign/runtime_talents_v5.json').write_bytes(b'mixed release')
            with self.assertRaises(ValueError):build_portable.verify_manager_closure(root,manifest)

    def test_manager_verified_with_native_cannot_drift_before_publication(self):
        with tempfile.TemporaryDirectory(prefix='rework-source-pins-') as folder:
            root=Path(folder)
            names=['sc1/__init__.py','sc1/portable_runtime.py','sc1/campaign/rework_growth.py',
                   'sc1/campaign/talent_campaign_policy.py','sc1/bridge/protocol.py','sc1/manager/store.py']
            names+=['sc1/campaign/'+name for name in build_portable.CAMPAIGN_DATA]
            names+=['sc1/effect_lab/'+name for name in build_portable.LAB_ASSETS]
            for name in names:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(name.encode())
            rows=native.manager_source_entries(root)
            receipt={'growth_protocol':'PHC1 v2','manager_sources':rows,
                     'manager_sources_unchanged_across_compile':True}
            with patch.object(package,'WORKSPACE',root):
                self.assertEqual(package.manager_inputs(receipt),rows)
                for field in ('manager_sources','manager_sources_unchanged_across_compile'):
                    broken=copy.deepcopy(receipt);broken.pop(field)
                    with self.assertRaises(ValueError):package.manager_inputs(broken)
                (root/'sc1/campaign/talent_campaign_policy.py').write_bytes(b'changed weights')
                with self.assertRaises(ValueError):package.manager_inputs(receipt)
                # Even an apparently harmless new module alters the shipped
                # import closure and must undergo the matching native roundtrip.
                (root/'sc1/campaign/talent_campaign_policy.py').write_bytes(b'sc1/campaign/talent_campaign_policy.py')
                (root/'sc1/bridge/additional.py').write_bytes(b'')
                with self.assertRaises(ValueError):package.manager_inputs(receipt)


if __name__=='__main__':unittest.main()
