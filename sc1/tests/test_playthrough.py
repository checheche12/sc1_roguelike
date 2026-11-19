"""New-game-plus transactions, durable choices, and extended rank transport."""
import copy
import json
from pathlib import Path
import random
import sqlite3
import struct
import tempfile
import unittest
import uuid
from unittest.mock import patch

from sc1.campaign import growth, playthrough_ranks, rank_policy, rework_growth
from sc1.campaign.missions import load_missions
from sc1.campaign.runtime_catalog import GrowthError, encode_growth, load_catalog
from sc1.manager.store import open_campaign_store
from sc1.tests.test_difficulty import finish, restore


class PlaythroughTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_catalog(expected_version=2)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'record.sqlite3'
        self.store = open_campaign_store(self.path, curses_per_mission=1)

    def mark_final(self, campaign=1):
        final = next(m for m in load_missions() if m['campaign_id'] == campaign and m['final'])
        with self.store._connect() as conn:
            conn.execute('UPDATE campaign SET completed_mask=completed_mask | ?', (1 << final['completion_bit'],))

    def seed(self):
        with self.store._connect() as conn:
            conn.execute('BEGIN IMMEDIATE')
            growth.initialize(conn, catalog_version=2)
            talent = next(t for t in self.catalog['talents'] if t.get('effect_ordinal') == 199)
            curse = self.catalog['curses'][0]
            growth._save_state(conn,101,4,[talent['id']],{curse['id']:1})
            rework_growth.save_ranks(conn,101,{talent['id']:4})
        self.mark_final()
        return talent

    def test_actual_new_choices_reconnect_replay_and_campaign_isolation(self):
        nonce = None
        for phase in range(1,5):
            last,_ = finish(self.store,phase,nonce)
            nonce = last['nonce']
        self.store.complete(101,nonce,0,last['gold'])
        before = self.store.growth_status(101)
        finish(self.store,1,mission=201)
        with self.store._connect() as conn:
            old_offers = [dict(r) for r in conn.execute('SELECT * FROM growth_offers WHERE mission=101')]
            other = [tuple(r) for r in conn.execute('SELECT * FROM growth_offers WHERE mission=201')]
        self.mark_final()
        result = self.store.start_next_playthrough(1,expected_number=1,curses_per_mission=0)
        self.assertEqual(result['number'],2)
        self.assertFalse(result['can_advance'])
        after = self.store.growth_status(101)
        self.assertEqual({t['id'] for t in before['talents']},{t['id'] for t in after['talents']})
        self.assertEqual(after['curses'],[])
        pending = restore(self.store,1)
        self.store = open_campaign_store(self.path,curses_per_mission=4)
        self.assertEqual(restore(self.store,1)['offer'],pending['offer'])
        self.assertEqual(restore(self.store,1)['curses_per_mission'],0)
        fresh=None;choices=[]
        for phase in range(1,5):
            current,selected=finish(self.store,phase,fresh)
            fresh=current['nonce'];choices+=selected
        self.assertNotEqual(nonce,fresh)
        self.assertEqual(choices.count('talent'),3)
        self.assertNotIn('curse',choices)
        self.store.complete(101,fresh,0,current['gold'])
        self.assertEqual(restore(self.store,1)['growth_words'],current['growth_words'])
        with self.store._connect() as conn:
            archive=json.loads(conn.execute('SELECT archive_json FROM campaign_playthrough_archives').fetchone()[0])
            self.assertEqual(archive['tables']['growth_offers'],old_offers)
            self.assertEqual([tuple(r) for r in conn.execute('SELECT * FROM growth_offers WHERE mission=201')],other)
            self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(),[])
        with self.assertRaises(GrowthError):
            self.store.start_next_playthrough(1,expected_number=1,curses_per_mission=4)

    def test_locked_and_invalid_requests_leave_database_exact(self):
        before=self.path.read_bytes()
        for cid,number,count in ((1,1,3),(True,1,3),(1,1,5),(1,False,3)):
            with self.assertRaises(GrowthError):
                self.store.start_next_playthrough(cid,expected_number=number,curses_per_mission=count)
            self.assertEqual(self.path.read_bytes(),before)

    def test_legacy_completion_with_growth_only_in_another_campaign(self):
        self.seed()
        self.mark_final(3)
        result = self.store.start_next_playthrough(3, expected_number=1, curses_per_mission=0, carry_curses=True)
        self.assertEqual(result['number'], 2)
        self.assertEqual(self.store.growth_status(301)['talents'], [])
        self.assertEqual(self.store.playthrough_status(1)['number'], 1)
        self.assertTrue(self.store.growth_status(101)['talents'])
        self.assertEqual(restore(self.store, 1, mission=301)['state'], 'choosing')

    def test_transition_failure_rolls_back_archive_and_reset(self):
        self.seed()
        before=self.path.read_bytes()
        with patch.object(growth,'_save_state',side_effect=RuntimeError('disk failure')):
            with self.assertRaises(RuntimeError):
                self.store.start_next_playthrough(1,expected_number=1,curses_per_mission=2)
        self.assertEqual(self.path.read_bytes(),before)

    def test_rank_cap_increases_on_each_transition_and_acquisition_enforces_it(self):
        talent=self.seed()
        for number in (2,3,4,5):
            self.store.start_next_playthrough(1,expected_number=number-1,curses_per_mission=number%5)
            with self.store._connect() as conn:
                conn.execute('BEGIN IMMEDIATE')
                catalog=playthrough_ranks.for_mission(conn,101,self.catalog)
                item=next(t for t in catalog['talents'] if t['id']==talent['id'])
                self.assertEqual(item['max_rank'],number+3)
                owned=json.loads(growth._state(conn,101)['talents_json'])
                rework_growth.acquire(conn,101,catalog,owned,item['id'])
                with self.assertRaises(GrowthError):rework_growth.acquire(conn,101,catalog,owned,item['id'])
                self.assertEqual(rework_growth.ranks(conn,101)[item['id']],number+3)
            self.mark_final()
        self.assertEqual(self.store.playthrough_status(1)['number'],5)

    def test_encoding_all_extended_fields_preserves_legacy_bits_and_wide_curses(self):
        original=copy.deepcopy(self.catalog)
        for number in (2,5,20,254,1000):
            catalog=playthrough_ranks.project(self.catalog,number)
            selected=[t for t in catalog['talents'] if t.get('effect_ordinal') in playthrough_ranks.fields() and t.get('rework_revision')==5]
            counts={t['id']:t['max_rank'] for t in selected if t.get('repeatable')}
            owned=[t['id'] for t in selected]
            curse=next(c for c in catalog['curses'] if c['byte_index']==16)
            words=encode_growth(catalog,owned,{curse['id']:1000},counts)
            self.assertEqual(len(words),65)
            self.assertEqual(words[16],0x80000000)
            self.assertEqual(words[64],1000)
            for item in selected:
                field=playthrough_ranks.fields()[item['effect_ordinal']]
                value=(words[field['word']]>>field['shift'])&((1<<field['width'])-1)
                self.assertEqual(value,counts.get(item['id'],1))
                if not item.get('wire_storage'):
                    self.assertTrue(words[1+item['bit_index']//32]&(1<<(item['bit_index']%32)))
        self.assertEqual(self.catalog,original)
        self.assertIs(playthrough_ranks.project(self.catalog,1),self.catalog)

    def test_inherited_wide_curse_offer_saturates_only_display_counter(self):
        from sc1.bridge.protocol import Request, BridgeError, choice_payload
        request=Request(101,1,1,2,4,'01'*16,0,0,growth_version=2,growth_applied=2,
                        choice_version=1,phase_version=2,phase=3)
        state=dict(state='choosing',requested_phase=3,completed_phase=2,total_phases=4,
            phase_pending={'talent':0,'curse':1},curses=[],
            offer=dict(offer_id=str(uuid.uuid4()),kind='curse',revision=1,candidates=[]))
        for index in (16,17,18,19):
            state['offer']['candidates']=[{'byte_index':index}]
            for count in (255,300,0xffffffff):
                state['curses']=[{'byte_index':index,'stacks':count}]
                words=struct.unpack('<95I',choice_payload(request,state))
                self.assertEqual(words[24],255)
                self.assertEqual(state['curses'][0]['stacks'],count)
        for index,count in ((0,256),(20,256),(16,0x100000000),(16,-1),(16,True),(True,1),(64,1)):
            state['curses']=[{'byte_index':index,'stacks':count}]
            with self.assertRaisesRegex(BridgeError,'invalid owned curse count'):
                choice_payload(request,state)

    def test_exhausted_economy_and_legend_guarantees_use_remaining_manuals(self):
        catalog=playthrough_ranks.project(self.catalog,2)
        owned=[t['id'] for t in catalog['talents'] if not t.get('repeatable')]
        for mission,phase in ((101,1),(102,2),(105,1)):
            result=rework_growth.candidates(catalog,mission,phase,owned,random.Random(7))
            self.assertTrue(result)
            self.assertTrue(all(t.get('repeatable') for t in result))

    def test_old_protocol_cannot_create_an_attempt_in_new_playthrough(self):
        self.seed()
        self.store.start_next_playthrough(1,expected_number=1,curses_per_mission=1)
        before=self.path.read_bytes()
        for callback in (lambda:self.store.restore(101),lambda:self.store.restore_growth(101,2),
                         lambda:self.store.restore_growth_phase(101,2,1,phase_version=1)):
            with self.assertRaises(GrowthError):callback()
            self.assertEqual(self.path.read_bytes(),before)

    def test_all_option_combinations_are_pinned_and_preserve_saved_ranks(self):
        talent=self.seed()
        curse=next(c for c in self.catalog['curses'] if c['byte_index']==16)
        for number,(carry,scaling) in enumerate(((False,False),(False,True),(True,False),(True,True)),2):
            with self.subTest(carry=carry,scaling=scaling):
                with self.store._connect() as conn:
                    state=growth._state(conn,101)
                    growth._save_state(conn,101,state['revision']+1,[talent['id']],{curse['id']:300})
                    rework_growth.save_ranks(conn,101,{talent['id']:8})
                self.mark_final()
                self.store.start_next_playthrough(1,expected_number=number-1,curses_per_mission=0,
                    carry_curses=carry,rank_scaling=scaling)
                self.store=open_campaign_store(self.path,curses_per_mission=4)
                setting=self.store.playthrough_status(1)
                self.assertEqual((setting['carry_curses'],setting['rank_scaling'],setting['curses_per_mission']),(carry,scaling,0))
                status=self.store.growth_status(101)
                shown=next(t for t in status['talents'] if t['id']==talent['id'])
                maximum=number+3 if scaling else 4
                self.assertEqual(shown['max_rank'],maximum)
                self.assertEqual(shown['stacks'],min(8,maximum))
                self.assertEqual(bool(status['growth_words'][16]&0x80000000),scaling)
                self.assertEqual(status['growth_words'][64],300 if carry else 0)
                with self.store._connect() as conn:
                    self.assertEqual(rework_growth.ranks(conn,101)[talent['id']],8)
                    archive=json.loads(conn.execute('SELECT archive_json FROM campaign_playthrough_archives WHERE number=?',(number-1,)).fetchone()[0])
                    self.assertEqual(json.loads(archive['growth_state']['curses_json']),{curse['id']:300})

    def test_disabling_then_enabling_restores_earned_rank_without_new_reward(self):
        talent=self.seed()
        self.store.start_next_playthrough(1,expected_number=1,curses_per_mission=0,rank_scaling=True)
        with self.store._connect() as conn:
            rework_growth.acquire(conn,101,playthrough_ranks.for_mission(conn,101,self.catalog),[talent['id']],talent['id'])
        for number,scaling,expected in ((3,False,4),(4,True,5)):
            self.mark_final()
            self.store.start_next_playthrough(1,expected_number=number-1,curses_per_mission=0,rank_scaling=scaling)
            from sc1.campaign.display_text import current_owned_descriptions
            status=current_owned_descriptions(self.store.growth_status(101))
            shown=next(t for t in status['talents'] if t['id']==talent['id'])
            self.assertEqual(shown['stacks'],expected)
            self.assertIn(f"최대 {number+3 if scaling else 4}회",shown['description'])
            with self.store._connect() as conn:self.assertEqual(rework_growth.ranks(conn,101)[talent['id']],5)

    def test_old_three_column_settings_migrate_only_during_transition(self):
        self.seed()
        with self.store._connect() as conn:
            conn.execute('CREATE TABLE campaign_playthroughs(campaign TEXT PRIMARY KEY,number INTEGER NOT NULL,curses_per_mission INTEGER NOT NULL)')
            conn.executemany('INSERT INTO campaign_playthroughs VALUES (?,?,?)',[('1',2,3),('2',2,1)])
        before=self.path.read_bytes()
        self.assertEqual(self.store.playthrough_status(1)['rank_bonus'],1)
        self.assertFalse(self.store.playthrough_status(1)['carry_curses'])
        self.assertEqual(self.path.read_bytes(),before)
        self.store.start_next_playthrough(1,expected_number=2,curses_per_mission=2,carry_curses=True,rank_scaling=False)
        self.assertEqual(self.store.playthrough_status(1)['rank_bonus'],0)
        self.assertTrue(self.store.playthrough_status(1)['carry_curses'])
        self.assertEqual(self.store.playthrough_status(2)['rank_bonus'],1)
        self.assertFalse(self.store.playthrough_status(2)['carry_curses'])

    def test_invalid_option_types_do_not_write(self):
        self.seed()
        before=self.path.read_bytes()
        for carry,scaling in ((1,True),(False,0),('keep',True),(False,None)):
            with self.assertRaises(GrowthError):
                self.store.start_next_playthrough(1,expected_number=1,curses_per_mission=0,carry_curses=carry,rank_scaling=scaling)
            self.assertEqual(self.path.read_bytes(),before)

    def test_pending_first_choice_preserves_inherited_rank_on_reconnect(self):
        talent = self.seed()
        self.store.start_next_playthrough(1, expected_number=1, curses_per_mission=0)
        expected = self.store.growth_status(101)['growth_words']
        field = playthrough_ranks.fields()[talent['effect_ordinal']]
        self.assertEqual((expected[field['word']] >> field['shift']) & 255, 4)
        first = restore(self.store, 1)
        self.assertEqual(first['state'], 'choosing')
        self.assertEqual(first['growth_words'], expected)
        reopened = open_campaign_store(self.path)
        self.assertEqual(restore(reopened, 1)['growth_words'], expected)


class PlaythroughWindowTests(unittest.TestCase):
    from sc1.tests.test_growth_ui import GrowthWindowTests
    setUp=GrowthWindowTests.setUp
    tearDown=GrowthWindowTests.tearDown

    def test_hidden_dialog_applies_selected_campaign_and_curse_setting(self):
        import tkinter as tk
        from tkinter import ttk
        from sc1.tests.test_growth_ui import descendants
        final=next(m for m in load_missions() if m['campaign_id']==2 and m['final'])
        with self.app.store._connect() as conn:
            conn.execute('UPDATE campaign SET completed_mask=?',(1<<final['completion_bit'],))
        original=tk.Toplevel;windows=[];errors=[]
        def hidden(*args,**kwargs):
            window=original(*args,**kwargs);window.withdraw();windows.append(window);return window
        def use_dialog():
            window=windows[0]
            try:
                widgets=list(descendants(window))
                selectors=[w for w in widgets if isinstance(w,ttk.Combobox)]
                selectors[0].current(1);selectors[0].event_generate('<<ComboboxSelected>>')
                selectors[1].current(0)
                next(w for w in widgets if isinstance(w,ttk.Radiobutton) and w.cget('text')=='그대로 가져오기').invoke()
                next(w for w in widgets if isinstance(w,ttk.Checkbutton)).invoke()
                next(w for w in widgets if isinstance(w,ttk.Button) and w.cget('text')=='다음 회차 시작').invoke()
                self.assertEqual(self.app.store.playthrough_status(2)['number'],2)
                self.assertEqual(self.app.store.playthrough_status(2)['curses_per_mission'],0)
                self.assertTrue(self.app.store.playthrough_status(2)['carry_curses'])
                self.assertFalse(self.app.store.playthrough_status(2)['rank_scaling'])
                self.assertEqual(self.app.store.playthrough_status(1)['number'],1)
            except BaseException as exc:errors.append(exc)
            finally:window.destroy()
        self.root.after(1,use_dialog)
        with patch('sc1.manager.ui.tk.Toplevel',side_effect=hidden),patch('sc1.manager.ui.messagebox.askyesno',return_value=True),patch('sc1.manager.ui.messagebox.showerror') as error:
            self.app.show_playthrough()
        error.assert_not_called()
        if errors:raise errors[0]


if __name__=='__main__':unittest.main()
