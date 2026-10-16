"""Player-facing targets and append-only multi-target updates."""
import copy
import json
from contextlib import closing
from pathlib import Path
import random
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from sc1.campaign import growth, phased_growth, talent_pool
from sc1.campaign.display_text import concise_description
from sc1.campaign.runtime_catalog import load_catalog, validate_catalog, encode_growth, GrowthError
from sc1.manager.store import open_campaign_store, GrowthChoicesPending

HERE = Path(__file__).resolve().parents[1] / 'campaign'
LEGACY = HERE / 'runtime_talents.json'
UNIT_NAMES = {0:'마린',1:'고스트',2:'벌쳐',3:'골리앗',4:'골리앗',5:'시즈탱크',6:'시즈탱크',
7:'SCV',8:'레이스',9:'사이언스 베슬',11:'드롭십',12:'배틀크루저',30:'시즈탱크',31:'시즈탱크',
32:'파이어뱃',34:'메딕',37:'저글링',38:'히드라리스크',39:'울트라리스크',41:'드론',42:'오버로드',
43:'뮤탈리스크',44:'가디언',45:'여왕',46:'디파일러',47:'스커지',50:'인페스티드 테란',58:'발키리',
60:'커세어',61:'다크 템플러',62:'디바우러',63:'다크 아콘',64:'프로브',65:'질럿',66:'드라군',
67:'하이 템플러',68:'아콘',69:'셔틀',70:'스카우트',71:'아비터',72:'캐리어',73:'인터셉터',83:'리버',
84:'옵저버',85:'스캐럽',103:'러커'}

class DisplayTextTests(unittest.TestCase):
    def test_every_actual_target_and_owner_is_named(self):
        catalog = load_catalog()
        self.assertEqual(len(catalog['talents']), 238)
        for item in catalog['talents']:
            text = concise_description(item)
            self.assertEqual(item['description'], text)
            self.assertTrue(text.startswith('아군 '), item['name'])
            self.assertTrue(item['target_units'], item['name'])
            if item.get('target_scope') == 'army_and_heroes':
                self.assertIn('아군', text)
                self.assertIn('영웅', text)
            else:
                for unit in item['target_units']:
                    self.assertIn(UNIT_NAMES[unit], text, item['name'])
            self.assertLessEqual(len(text), 48)
            self.assertNotIn('100/130', text)
            self.assertNotIn('구현', text)
        scopes = ['적 추가 공세','적 일반 공격','적 전투 유닛','적','적 추가 공세',
                  '적 추가 공세','기존 적','적 추가 공세','적 추가 공세','적',
                  '적 추가 공세','적 일반 공격','적 공세 구호반','적 공세 지휘관','적 공세']
        for item, scope in zip(catalog['curses'], scopes):
            text = concise_description(item)
            self.assertIn(scope, text, item['name'])
            self.assertLessEqual(len(text), 64)
            self.assertTrue(any(c.isdigit() for c in text), item['name'])
        self.assertIn('아군 지상 전투병', catalog['curses'][10]['description'])

    def test_legacy_display_does_not_modify_pinned_items(self):
        old = load_catalog(LEGACY)
        original = copy.deepcopy(old)
        marine = next(x for x in old['talents'] if x['bit_index'] == 2)
        self.assertEqual(concise_description(marine), '아군 마린 공격속도 30% 증가')
        for item in old['talents'] + old['curses']:
            self.assertTrue(concise_description(item))
        self.assertEqual(old, original)

    def test_original_ids_rarities_and_new_bit_payload(self):
        catalog = load_catalog()
        board = json.loads((HERE/'design_snapshots/r469_20261014_153314_623339/board.json').read_text(encoding='utf8'))
        originals = {x['id']: x for x in board['items']}
        for item in catalog['talents'][104:106]:
            old = originals[item['id']]
            self.assertEqual(item['source_description'], old['description'])
            self.assertEqual(item['rarity'], old['rarity'])
            self.assertEqual(item['name'], old['name'])
        words = encode_growth(catalog, list(talent_pool.APPENDED), {})
        self.assertEqual(words[4], (1 << 8) | (1 << 9))
        self.assertEqual(sum(x != 0 for x in words[1:]), 1)

    def test_multi_target_schema_rejects_wrong_units_counts_or_recursive_effects(self):
        for key, value in [('unit_id', 8), ('max_targets', 4), ('mode', 'unknown'),
                           ('full_weapon_damage', False), ('recursive_secondary_attacks', True)]:
            changed = load_catalog()
            changed['talents'][104]['effect'][key] = value
            with self.assertRaises(GrowthError):
                validate_catalog(changed)

    def test_header_contains_current_text_and_multi_target_contract(self):
        header = (HERE.parent/'native_campaign/plugin/include/frozen_catalog.generated.h').read_text(encoding='utf8')
        self.assertIn('{104,3,0,2}', header)
        self.assertIn('{105,12,1,3}', header)
        self.assertIn('kTalentCount = 400', header)
        self.assertIn('kLegacyTalentCount = 238', header)
        catalog=load_catalog(expected_version=2)
        for item in catalog['talents'] + catalog['curses']:
            self.assertIn(json.dumps(item['description'], ensure_ascii=False), header)

class AddedTalentAndCurseRotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'run.sqlite3'
        self.store = open_campaign_store(self.path, runtime_catalog_path=LEGACY)
    def tearDown(self):
        self.tmp.cleanup()
    def rows(self, sql, args=()):
        with closing(sqlite3.connect(self.path)) as conn:
            return conn.execute(sql, args).fetchall()
    def load(self, mission=101, phase=1, nonce=None):
        try:
            return self.store.restore_growth_phase(mission, 1, phase, nonce=nonce)
        except GrowthChoicesPending as pending:
            return pending.state
    def choose(self, state, mission=101, phase=1, nonce=None, slot=1):
        offer = state['offer']
        return self.store.choose_growth_phase_slot(offer['offer_id'],slot,offer['revision'],mission,1,
            choice_kind=1 if offer['kind']=='talent' else 2,phase=phase,nonce=nonce)
    def test_old_three_curse_offer_stays_exact_then_full_pool_rotates_through_next_mission(self):
        state = self.choose(self.load())
        old_offer = copy.deepcopy(state['offer'])
        self.assertEqual({x['byte_index'] for x in old_offer['candidates']}, {0,1,2})
        old_pin = self.rows('SELECT catalog_json FROM growth_state')
        old_run_pin = self.rows('SELECT * FROM growth_phase_catalogs')
        self.store = open_campaign_store(self.path)
        self.assertEqual(self.load()['offer'], old_offer)
        self.choose(self.load())
        response = self.load()
        phase_one = self.rows('SELECT * FROM growth_phase_snapshots')
        nonce = response['nonce']
        shown = [{x['id'] for x in old_offer['candidates']}]
        for mission, phases in [(101,(2,3)),(102,(1,2,3))]:
            if mission == 102:
                nonce = None
            for phase in phases:
                state = self.load(mission,phase,nonce)
                state = self.choose(state,mission,phase,nonce)
                ids = {x['id'] for x in state['offer']['candidates']}
                self.assertEqual(len(ids),3)
                self.assertNotEqual(ids,shown[-1])
                shown.append(ids)
                self.choose(state,mission,phase,nonce)
                response = self.load(mission,phase,nonce)
                nonce = response['nonce']
            if mission == 101:
                self.store.complete(101,nonce,0,response['gold'])
        common = {x['id'] for x in load_catalog()['curses'] if x['rarity']=='common'}
        self.assertEqual(shown[0] | shown[1], common)
        self.assertEqual(set.union(*shown),common)
        self.assertEqual(self.rows('SELECT catalog_json FROM growth_state'),old_pin)
        self.assertEqual(self.rows('SELECT * FROM growth_phase_catalogs WHERE mission=101'),old_run_pin)
        self.assertEqual(self.rows('SELECT * FROM growth_phase_snapshots WHERE mission=101 AND phase=1'),phase_one)
        saved = self.rows('SELECT candidates_json FROM growth_offers WHERE offer_id=?',(old_offer['offer_id'],))[0][0]
        self.assertEqual(json.loads(saved),old_offer['candidates'])
        self.assertEqual(len(self.rows('SELECT * FROM growth_curse_pool_updates')),1)
        self.assertEqual(len(self.rows('SELECT * FROM growth_talent_pool_updates')),1)
    def test_new_talent_can_be_selected_from_old_pin_and_restored(self):
        state = self.choose(self.load())
        self.choose(state)
        response = self.load()
        nonce = response['nonce']
        self.store = open_campaign_store(self.path)
        class PreferNew(random.Random):
            def choices(self, values, weights=None, k=1):
                return ['common' if 'common' in values else values[0]]
            def choice(self, values):
                return next((x for x in values if isinstance(x,dict) and x.get('bit_index')==106),values[0])
        with patch.object(phased_growth.secrets,'SystemRandom',return_value=PreferNew(7)):
            state = self.load(101,2,nonce)
            slot = next(i+1 for i,x in enumerate(state['offer']['candidates']) if x['bit_index']==106)
            state = self.choose(state,101,2,nonce,slot)
            self.choose(state,101,2,nonce)
        result = self.load(101,2,nonce)
        self.assertTrue(result['growth_words'][4] & (1<<10))
        self.assertEqual(self.load(101,2,nonce)['growth_words'],result['growth_words'])
        with closing(sqlite3.connect(self.path)) as conn:
            conn.row_factory = sqlite3.Row
            active = phased_growth._run_catalog(conn,101)
            self.assertEqual(len(active['talents']),151)
            self.assertEqual(len(active['curses']),15)
    def test_readonly_and_custom_catalog_never_add_pool_tables(self):
        self.load()
        before = self.path.read_bytes()
        self.store.growth_status(101)
        self.assertEqual(self.path.read_bytes(),before)
        self.assertFalse(self.rows("SELECT name FROM sqlite_master WHERE name IN ('growth_talent_pool_updates','growth_curse_pool_updates')"))
    def test_conflicting_slot_or_original_identity_fails_closed(self):
        base = load_catalog(LEGACY)
        new = load_catalog()['talents'][104:106]
        for key,value in [('bit_index',2),('rarity','common'),('id','unknown')]:
            entries = copy.deepcopy(new)
            entries[0][key] = value
            with self.assertRaises(GrowthError):
                talent_pool.merge(base,entries)
        collision = copy.deepcopy(base)
        collision['talents'][0]['bit_index'] = 104
        with self.assertRaises(GrowthError):
            talent_pool.merge(collision,new)
    def test_curse_rotation_uses_recent_frequency_and_three_eligible_fallback(self):
        self.store = open_campaign_store(self.path)
        state = self.choose(self.load())
        with closing(sqlite3.connect(self.path)) as conn:
            conn.row_factory = sqlite3.Row
            offer = growth._current(conn,101)
            pool = [x for x in load_catalog()['curses'] if x['rarity']=='common']
            previous = pool[:3]
            conn.execute("INSERT INTO growth_offers (offer_id,source,mission,kind,rarity,candidates_json) VALUES ('old','old',101,'curse','common',?)",(json.dumps(previous),))
            choice = phased_growth._diverse_curses(conn,101,offer,pool,random.Random(5))
            self.assertTrue({x['id'] for x in pool[3:]} <= {x['id'] for x in choice})
            self.assertEqual(phased_growth._diverse_curses(conn,101,offer,pool[:3],random.Random(5)),pool[:3])
            conn.rollback()

if __name__ == '__main__':
    unittest.main()
