"""Actual owned-growth widget labels, with disposable old catalog pins only."""
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from sc1.campaign import growth,rework_growth,talent_balance
from sc1.campaign.display_text import concise_description,current_owned_descriptions
from sc1.campaign.runtime_catalog import load_catalog
from sc1.manager.store import CampaignStore,GrowthChoicesPending


class CurrentGrowthDisplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='qa7-display-disposable-');self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'original.sqlite3';self.current=load_catalog(expected_version=2)
        old=copy.deepcopy(self.current);old['talents']=[talent_balance.historical(x) for x in old['talents']]
        for group in ('talents','curses'):
            for item in old[group]:
                item['description']='과거에 저장된 설명';item['effect'].pop('qa_revision',None)
        old_path=Path(self.tmp.name)/'old_catalog.json';old_path.write_text(json.dumps(old,ensure_ascii=False),encoding='utf8')
        self.store=CampaignStore(self.path,new_profile='original',runtime_catalog_path=old_path)
        try:self.store.restore_growth_phase(101,2,1)
        except GrowthChoicesPending:pass
        self.manual=self.current['talents'][267];self.economy=self.current['talents'][238];self.curse=self.current['curses'][15]
        with self.store._connect() as conn:
            growth._save_state(conn,101,7,[self.current['talents'][0]['id'],self.manual['id'],self.economy['id']],{self.curse['id']:2})
            rework_growth.save_ranks(conn,101,{self.manual['id']:3})
        self.store.runtime_catalog_path=None

    def test_read_projection_refreshes_both_kinds_without_touching_database(self):
        raw=self.path.read_bytes();saved=self.store.growth_status();before=copy.deepcopy(saved)
        shown=current_owned_descriptions(saved)
        self.assertEqual(saved,before);self.assertEqual(self.path.read_bytes(),raw)
        for key in ('growth_words','revision','offer','history','pending','upcoming'):
            self.assertEqual(shown[key],saved[key])
        by_id={x['id']:x for x in shown['talents']+shown['curses']}
        self.assertEqual(by_id[self.manual['id']]['stacks'],3)
        self.assertEqual(by_id[self.curse['id']]['stacks'],2)
        for canonical in (self.manual,self.economy,self.curse,self.current['talents'][0]):
            self.assertEqual(concise_description(by_id[canonical['id']]),canonical['description'])
        self.assertIn('+15%',concise_description(by_id[self.manual['id']]))
        self.assertIn('2 더',concise_description(by_id[self.economy['id']]))

    def test_current_description_beats_source_and_old_summary(self):
        for item in self.current['talents']+self.current['curses'][15:]:
            if item.get('rework_revision')==5 or item['effect'].get('qa_revision'):
                self.assertEqual(concise_description(item),item['description'])

    def test_incompatible_or_newer_pin_never_gets_reinterpreted(self):
        saved=self.store.growth_status()
        for field,new in (('bit_index',500),('source_description','different accepted source')):
            broken=copy.deepcopy(saved);broken['talents'][1][field]=new
            self.assertEqual(current_owned_descriptions(broken)['talents'][1],broken['talents'][1])
        newer=copy.deepcopy(saved);newer['talents'][1]['effect']['qa_revision']=9999999999
        self.assertEqual(current_owned_descriptions(newer)['talents'][1],newer['talents'][1])

    def test_withdrawn_growth_window_uses_current_labels_and_keeps_record_exact(self):
        from sc1.manager.ui import ManagerWindow
        from sc1.tests.test_growth_ui import descendants
        from tkinter import ttk
        root=tk.Tk();root.withdraw();app=ManagerWindow(root,self.path)
        before=self.path.read_bytes();windows=[];labels=[];errors=[];original=tk.Toplevel
        def hidden(*args,**kwargs):
            dialog=original(*args,**kwargs);dialog.withdraw();windows.append(dialog);return dialog
        def inspect():
            try:
                dialog=windows[0];self.assertEqual(dialog.state(),'withdrawn')
                labels.extend(str(w.cget('text')) for w in descendants(dialog) if isinstance(w,ttk.Label))
                dialog.destroy()
            except BaseException as exc:errors.append(exc);windows[0].destroy()
        try:
            root.after(1,inspect)
            with patch('sc1.manager.ui.tk.Toplevel',side_effect=hidden):app.show_growth()
            if errors:raise errors[0]
            self.assertIn(self.manual['description'],labels);self.assertIn(self.economy['description'],labels);self.assertIn(self.curse['description'],labels)
            self.assertNotIn('과거에 저장된 설명',labels);self.assertEqual(self.path.read_bytes(),before)
        finally:
            app.closed=True
            for timer in root.tk.call('after','info'):root.after_cancel(timer)
            root.destroy();app=None;root=None;windows.clear()
            import gc
            gc.collect()
