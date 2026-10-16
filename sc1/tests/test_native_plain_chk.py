"""Plain native-campaign asset preservation and portable wave behavior.

Only checked-in/local source assets and an isolated compiled test program are
used. These checks never load StarCraft, a native DLL or a campaign database.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import unittest

from sc1.native_campaign import build_plain_chk as builder


class PlainNativeChkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = builder.SOURCE.read_bytes()
        cls.original = builder.CHK(cls.raw)
        cls.output, cls.report, cls.config = builder.make_plain_chk(cls.raw)
        cls.chk = builder.CHK(cls.output)

    def test_original_source_hash_and_entire_legacy_section_set_order_retained(self):
        self.assertEqual(builder.digest(self.raw), builder.SOURCE_SHA256)
        self.assertEqual(self.chk.order, self.original.order)
        self.assertEqual(len(self.chk.order), 30)
        self.assertEqual(self.chk.getsection('VER '), struct.pack('<H', 59))
        self.assertEqual(self.chk.getsection('IVER'), struct.pack('<H', 10))
        self.assertFalse({b'STRx', b'UNIx', b'PUPx', b'PTEx', b'UPGx', b'TECx', b'TYPE', b'IVE2'} & set(self.chk.order))
        self.assertEqual(builder.CHK(self.output).save(), self.output)
        for name in self.original.order:
            if name not in (b'UNIT', b'TRIG', b'STR '):
                self.assertEqual(len(self.chk.sections[name]), len(self.original.sections[name]), name)

    def test_original_load_metadata_locations_stats_costs_audio_briefing_exact(self):
        for name in ('IOWN', 'VCOD', 'VER ', 'IVER', 'ERA ', 'DIM ', 'MTXM', 'ISOM', 'TILE', 'DD2 ',
                     'THG2', 'MASK', 'MRGN', 'UNIS', 'UPGS', 'TECS', 'UPRP', 'UPUS', 'MBRF', 'SPRP', 'WAV '):
            self.assertEqual(self.chk.getsection(name), self.original.getsection(name), name)
        self.assertEqual(len(self.chk.getsection('MRGN')), 64 * 20)
        self.assertEqual(len(self.chk.getsection('UNIS')), 4048)
        self.assertEqual(len(self.chk.getsection('UPGR')), 38 * 46)
        self.assertEqual(len(self.chk.getsection('PTEC')), 38 * 24)

    def test_legacy_strings_keep_all_original_ids_bytes_aliases_and_append_ascii(self):
        before = builder.strings(self.original.getsection('STR '))
        after = builder.strings(self.chk.getsection('STR '))
        self.assertEqual(after, before + [builder.FINGERPRINT])
        self.assertEqual(self.report['fingerprint_string_id'], len(before) + 1)
        self.assertEqual(builder.FINGERPRINT, b'SC1_NATIVE_T01_V1_R469_C1')
        old_offsets = struct.unpack_from('<' + 'H' * len(before), self.original.getsection('STR '), 2)
        new_offsets = struct.unpack_from('<' + 'H' * len(after), self.chk.getsection('STR '), 2)
        self.assertEqual(tuple(offset + 2 for offset in old_offsets), new_offsets[:-1])
        self.assertLess(len(self.chk.getsection('STR ')), 65536)

    def test_only_single_original_victory_action_changed_conditions_force1_owner_preserved(self):
        before, after = self.original.getsection('TRIG'), self.chk.getsection('TRIG')
        at = 2400 + 320
        expected = bytearray(before)
        expected[at:at + 32] = bytes.fromhex(self.report['victory']['replacement_action_hex'])
        self.assertEqual(after[:9 * 2400], expected)
        for index in range(9):
            self.assertEqual(after[index * 2400:index * 2400 + 320], before[index * 2400:index * 2400 + 320])
            self.assertEqual(after[index * 2400 + 2368:(index + 1) * 2400], before[index * 2400 + 2368:(index + 1) * 2400])
        action = struct.unpack_from('<IIIIIIHBBBBH', after, at)
        self.assertEqual((action[4], action[5], action[6], action[7], action[8], action[9]), (11, 1, 226, 45, 7, 20))
        self.assertEqual(self.report['victory']['original_owner_name'], 'Force1')
        self.assertEqual(after[2400 + 2372 + 18], 1)
        self.assertEqual(after[2400 + 2372 + 17], 0)

    def test_gate_is_ordinary_p2_single_shot_victory_after_growth_goal_and_ack(self):
        gate = self.chk.getsection('TRIG')[9 * 2400:]
        self.assertEqual(len(gate), 2400)
        for index, unit in enumerate((225, 226, 227)):
            condition = struct.unpack_from('<IIIHBBBBH', gate, index * 20)
            self.assertEqual(condition, (0, 11, 1, unit, 0, 15, 0, 0, 0))
        self.assertEqual(gate[60:320], bytes(260))
        self.assertEqual(struct.unpack_from('<IIIIIIHBBBBH', gate, 320), (0, 0, 0, 0, 0, 0, 0, 1, 0, 4, 0, 0))
        self.assertEqual(gate[352:2368], bytes(2016))
        self.assertEqual(gate[2368:2372], bytes(4))
        self.assertEqual(gate[2372:2399], bytes([0, 1] + [0] * 25))

    def test_native_objective_contract_matches_every_original_victory_condition(self):
        # Independent source-asset contract for the native T01 goal detector:
        # Command AtLeast uses completed counts, with no hidden extra condition.
        expected = [(0, 1, 10, 0, 0, 2, 0, 0, 0),
                    (0, 1, 1, 111, 0, 2, 0, 0, 0),
                    (0, 1, 1, 19, 0, 2, 0, 0, 0)]
        for chk in (self.original, self.chk):
            data = chk.getsection('TRIG')[2400:2720]
            conditions = [struct.unpack_from('<IIIHBBBBH', data, i * 20)
                          for i in range(16) if data[i * 20 + 15]]
            self.assertEqual(conditions, expected)

    def test_audit_rejects_source_death_conditions_actions_and_physical_counter_types(self):
        audit = builder.audit_counters(self.original)
        self.assertEqual(audit['unit_ids'], {'growth_ready': 225, 'goal': 226, 'ack': 227})
        self.assertEqual(audit['source_deaths_condition_count'], 0)
        self.assertEqual(audit['source_setdeaths_action_count'], 0)
        for section, offset, value in (('TRIG', 15, 15), ('TRIG', 320 + 26, 45)):
            clone = builder.CHK(self.raw)
            data = bytearray(clone.getsection(section))
            data[offset] = value
            clone.setsection(section, data)
            with self.assertRaises(AssertionError):
                builder.audit_counters(clone)
        clone = builder.CHK(self.raw)
        data = bytearray(clone.getsection('UNIT'))
        struct.pack_into('<H', data, 8, 225)
        clone.setsection('UNIT', data)
        with self.assertRaises(AssertionError):
            builder.audit_counters(clone)

    def test_original49_units_and_46_static_lings_one5000_geyser_only(self):
        old, new = self.original.getsection('UNIT'), self.chk.getsection('UNIT')
        self.assertEqual(new[:len(old)], old)
        extra = builder.difficulty.records(new[len(old):])
        self.assertEqual(len(extra), 47)
        self.assertTrue(all(builder.difficulty.unit_info(record)[2:] == (37, 4) for record in extra[:46]))
        self.assertEqual(builder.difficulty.unit_info(extra[-1])[2:], (188, 11))
        self.assertEqual(struct.unpack_from('<I', extra[-1], 20)[0], 5000)
        serials = [struct.unpack_from('<I', record)[0] for record in builder.difficulty.records(new)]
        self.assertEqual(len(serials), len(set(serials)))
        self.assertEqual(len(new), 96 * 36)

    def test_safe_terrain_additions_and_native_wave_cells_remain_connected(self):
        _, clear = builder.difficulty.load_grid()
        for record in builder.difficulty.records(self.chk.getsection('UNIT')):
            x, y, unit, _ = builder.difficulty.unit_info(record)
            if unit not in (106, 109, 176, 177, 178, 188):
                continue
            hx, hy = (64, 48) if unit == 106 else ((48, 32) if unit == 109 else ((64, 32) if unit == 188 else (32, 16)))
            for yy in range(max(0, (y - hy - 12) // 8), min(len(clear), (y + hy + 12) // 8 + 1)):
                for xx in range(max(0, (x - hx - 12) // 8), min(len(clear[0]), (x + hx + 12) // 8 + 1)):
                    clear[yy][xx] = False
        connected = builder.difficulty.accessible(clear)
        for origin in self.config['origins']:
            self.assertEqual(len(origin['cells']), 90)
            self.assertTrue(all((x // 8, y // 8) in connected for x, y in origin['cells']), origin['name'])
        static = [point for row in self.config['static_reinforcements'] for point in row['added']]
        self.assertEqual(len(static), 46)
        self.assertTrue(all((x // 8, y // 8) in connected for x, y in static))

    def test_added_gas_preserves_original_command_center_rebuild_position(self):
        from sc1.native_campaign import resource_depot_placement as depot
        before=list(map(builder.difficulty.unit_info,builder.difficulty.records(self.original.getsection('UNIT'))))
        after=list(map(builder.difficulty.unit_info,builder.difficulty.records(self.chk.getsection('UNIT'))))
        old_bad=before+[(1056,1856,188,11)]
        self.assertEqual(self.config['geyser']['position'],[1056,1920])
        for kind in depot.DEPOT_TYPES:
            with self.subTest(depot=kind):
                self.assertNotIn((31,53),depot.resource_forbidden_tiles(before,kind,(64,64)))
                self.assertIn((31,53),depot.resource_forbidden_tiles(old_bad,kind,(64,64)))
                self.assertNotIn((31,53),depot.resource_forbidden_tiles(after,kind,(64,64)))
                self.assertFalse(depot.newly_blocked_depot_tiles(old_bad,after,kind,(64,64)))

    def test_unlock_only_p2_legacy_fields_leaves_bw_defaults_other_players_unchanged(self):
        scope = self.config['native_route']
        units = set(scope['legacy_unlocked_unit_ids'])
        self.assertFalse(units & builder.BW_ONLY_UNITS)
        for name, size, ids in (('PUNI', 228, units), ('UPGR', 46, map(int, scope['legacy_upgrade_maximums'])),
                                ('PTEC', 24, scope['legacy_available_technology_ids'])):
            before, after = self.original.getsection(name), self.chk.getsection(name)
            rows = (1, 14) if name == 'PUNI' else (1, 13, 27)
            ids = tuple(ids)
            allowed = {row * size + index for row in rows for index in ids}
            self.assertTrue(all(a == b for index, (a, b) in enumerate(zip(before, after)) if index not in allowed), name)
        for unit in builder.BW_ONLY_UNITS:
            for row in range(25):
                self.assertEqual(self.chk.getsection('PUNI')[row * 228 + unit], self.original.getsection('PUNI')[row * 228 + unit])
        for index, level in scope['legacy_upgrade_maximums'].items():
            index = int(index)
            self.assertLess(index, 46)
            data = self.chk.getsection('UPGR')
            self.assertEqual((data[46 + index], data[13 * 46 + index], data[27 * 46 + index]), (level, 0, 0))
        for index in scope['legacy_available_technology_ids']:
            self.assertLess(index, 24)
            data = self.chk.getsection('PTEC')
            self.assertEqual((data[24 + index], data[13 * 24 + index], data[27 * 24 + index]),
                             (1, int(index in (4, 6)), 0))
        self.assertFalse(scope['bw_original_mode_production_verified'])

    def test_p7_only_slot_changes_and_original_human_terran_stays(self):
        for name in ('OWNR', 'SIDE', 'FORC'):
            before, after = self.original.getsection(name), self.chk.getsection(name)
            self.assertEqual(before[:6] + before[7:], after[:6] + after[7:], name)
        self.assertEqual(self.chk.getsection('OWNR')[6], 5)
        self.assertEqual(self.chk.getsection('SIDE')[6], 0)
        self.assertEqual(self.chk.getsection('FORC')[6], self.chk.getsection('FORC')[4])
        self.assertEqual(self.chk.getsection('OWNR')[1], 6)
        self.assertEqual(self.chk.getsection('SIDE')[1], 1)
        self.assertEqual(self.chk.getsection('IOWN'), self.original.getsection('IOWN'))

    def test_exact_generated_header_and_receipt_output_matches_frozen_assets(self):
        self.assertEqual(builder.DEFAULT_OUTPUT.read_bytes(), self.output)
        self.assertEqual(builder.WAVE_HEADER.read_text(encoding='utf-8'), builder.wave_header(self.config))
        receipt = json.loads(builder.DEFAULT_RECEIPT.read_text(encoding='utf-8'))
        self.assertEqual(receipt['sha256'], builder.digest(self.output))
        self.assertEqual(receipt['fingerprint_string_id'], self.report['fingerprint_string_id'])
        self.assertFalse(receipt['native_load_verified'])
        self.assertFalse(receipt['game_process_accessed'])
        self.assertFalse(receipt['euddraft_called'])

    def test_rejects_wrong_source_negative_truncated_or_duplicate_chk_sections(self):
        with self.assertRaises(ValueError):
            builder.make_plain_chk(self.raw + b'bad')
        for bad in (b'BAD', b'VER ' + struct.pack('<I', 0xFFFFFF00), self.raw + self.raw[:10]):
            with self.assertRaises(ValueError):
                builder.CHK(bad)


WAVE_HARNESS = r'''
#include "wave_runtime.h"
#include "include/wave_config.generated.h"
#include "include/wave_progression.h"
#include <algorithm>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>
using namespace sc1_native;
void require(bool result, const char* message) { if (!result) throw std::runtime_error(message); }
// Independent pinned units.dat half-supply values. The former fixture counted
// Hydralisks as four and recognized only two troop types as Men; current waves
// also use the middle/late compositions and Hydralisks cost two half-supply.
unsigned half_supply(int type) {
    switch (type) {
        case 37: return 1;
        case 0: case 32: case 38: return 2;
        case 2: case 3: case 5: case 8: case 43: case 44: case 62:
        case 65: case 66: case 60: return 4;
        case 58: case 70: return 6;
        case 39: case 68: case 71: return 8;
        case 12: return 12;
        default: return 0;
    }
}
struct Unit { int owner; int type; int x; int y; bool ordered = false; };
struct Fixture {
    WaveRuntime runtime;
    std::vector<Unit> units, created;
    std::vector<unsigned> warnings;
    std::vector<int> attack_owners;
    std::uint32_t frame = 0, elapsed = 0;
    std::uint32_t global_override = 0;
    bool ready = true, goal = false, fail_creation = false;
    std::uint8_t stacks = 0;
    static std::uint32_t count(void* context, int owner, int type, const WaveRect* area) {
        auto& f = *static_cast<Fixture*>(context);
        if (!area && owner == -1 && type == -1 && f.global_override) return f.global_override;
        std::uint32_t amount = 0;
        for (const auto& u : f.units) {
            if (owner != -1 && u.owner != owner) continue;
            if (type == -2 && !half_supply(u.type)) continue;
            if (type >= 0 && u.type != type) continue;
            if (area && (u.x < area->left || u.x > area->right || u.y < area->top || u.y > area->bottom)) continue;
            ++amount;
        }
        return amount;
    }
    static void* spawn(void* context, std::uint16_t type, std::int32_t x, std::int32_t y, std::uint8_t owner) {
        auto& f = *static_cast<Fixture*>(context);
        if (f.fail_creation) return nullptr;
        require(owner == 6, "Created only the dedicated P7 pool");
        f.units.push_back(Unit{owner, type, x, y});
        f.created.push_back(f.units.back());
        return reinterpret_cast<void*>(static_cast<std::uintptr_t>(f.created.size()));
    }
    static void attack(void* context, std::uint8_t owner, const WaveRect* area, std::int32_t x, std::int32_t y) {
        auto& f = *static_cast<Fixture*>(context);
        require(owner == 6 && area && x == 1056 && y == 1600, "P7 entry-only attack target");
        f.attack_owners.push_back(owner);
        for (auto& u : f.units) {
            if (u.owner == owner && half_supply(u.type)
                && u.x >= area->left && u.x <= area->right && u.y >= area->top && u.y <= area->bottom) u.ordered = true;
        }
    }
    static void warning(void* context, std::uint32_t origin, const WavePoint* point) {
        auto& f = *static_cast<Fixture*>(context);
        require(origin < 4 && point, "Only configured origins can warn");
        f.warnings.push_back(origin);
    }
    WaveHost host() { return WaveHost{this, count, spawn, attack, warning}; }
    void tick() { runtime.tick(++frame, ready, elapsed, stacks, goal, host()); }
    void run(unsigned amount) { while (amount--) tick(); }
    void prepared() {
        elapsed = 299;
        units.push_back(Unit{1, 7, 1056, 1600});
        run(1440);
        require(runtime.state().home_ticks == 1440 && !runtime.state().active, "Grace accumulated before trigger time");
        elapsed = 300;
    }
    unsigned created_supply(std::size_t begin = 0) const {
        unsigned used = 0;
        for (std::size_t i = begin; i < created.size(); ++i) used += half_supply(created[i].type);
        return used;
    }
    unsigned living_supply() const {
        unsigned used = 0;
        for (const auto& u : units) if (u.owner == 6) used += half_supply(u.type);
        return used;
    }
    void clear_enemies() { units.erase(std::remove_if(units.begin(), units.end(), [](const Unit& u) { return u.owner == 6; }), units.end()); }
    void clear_blockers() { units.erase(std::remove_if(units.begin(), units.end(), [](const Unit& u) { return u.owner == 1 && u.type == 0; }), units.end()); }
    void block(unsigned origin, int owner = 1) {
        auto p = wave_config::kOrigins[origin].center;
        units.push_back(Unit{owner, 0, p.x, p.y});
    }
    std::size_t one_wave() {
        auto before = created.size(), previous = warnings.size();
        unsigned budget = 5000;
        while (warnings.size() == previous && budget--) tick();
        require(warnings.size() != previous, "Wave must be scheduled within one period");
        budget = 100;
        while (runtime.state().pending && budget--) tick();
        require(!runtime.state().pending, "Warning delay must finish");
        return created.size() - before;
    }
};
int main(int argc, char** argv) {
    try {
        require(argc == 2, "Choose a test case");
        const std::string name = argv[1];
        if (name == "timing") {
            Fixture f; f.elapsed = 9999; f.run(2000);
            require(f.warnings.empty() && !f.runtime.state().home_seen, "No SCV means no activation");
            f.units.push_back(Unit{1, 0, 1056, 1600}); f.run(2000);
            require(!f.runtime.state().home_seen, "Marine does not count as arrival");
            f.elapsed = 299; f.units.push_back(Unit{1, 7, 1056, 1600}); f.run(1439);
            require(f.warnings.empty(), "Full SCV grace required"); f.tick();
            require(f.warnings.empty() && !f.runtime.state().active, "No warning at299seconds even after full grace");
            f.elapsed = 300; f.tick(); require(f.runtime.state().pending == 1 && f.warnings.size() == 1, "First warning at300seconds");
            f.run(94); require(f.created.empty(), "96-hook warning required"); f.tick();
            require(f.created_supply() == 16, "First wave consumes exactly16half-supply");
            require(Fixture::count(&f,6,37,nullptr) && Fixture::count(&f,6,38,nullptr), "First wave mixes ordinary Zerglings and Hydralisks");
        } else if (name == "gate") {
            Fixture f; f.units.push_back(Unit{1, 7, 1056, 1600}); f.elapsed = 9999; f.ready = false; f.run(5000);
            require(f.runtime.state().home_ticks == 0 && f.warnings.empty(), "Growth pending freezes waves");
            f.ready = true; f.run(1440); require(f.runtime.state().pending != 0, "Wave ready");
            const auto warning = f.runtime.state().warning_ticks; f.goal = true; f.run(5000);
            require(f.created.empty() && f.runtime.state().warning_ticks == warning, "Goal reached freezes pending spawn");
        } else if (name == "alternate") {
            Fixture f; f.prepared(); f.block(0); f.one_wave(); require(f.created_supply() == 16, "Alternate wave fills16half-supply");
            require(f.warnings.back() == 1, "West chosen when east is guarded");
        } else if (name == "blocked") {
            Fixture f; f.prepared(); for (unsigned i = 0; i != 4; ++i) f.block(i);
            f.tick(); require(f.warnings.empty() && !f.runtime.state().due, "Blocked attempt discarded");
            f.clear_blockers(); f.run(2878); require(f.warnings.empty(), "No immediate catchup");
            f.tick(); require(f.warnings.size() == 1, "Next regular period"); f.run(95);
            require(f.created_supply() == 16 && f.runtime.state().stage == 1, "Only one normal wave");
        } else if (name == "recheck") {
            Fixture f; f.prepared(); f.tick(); f.block(0, 2); f.run(95);
            require(!f.created.empty() && !f.runtime.state().pending && f.runtime.state().stage == 1, "Unsafe warned entry is skipped while safe alternate entries remain usable");
            const auto blocked=wave_config::kOrigins[0].bounds;
            for(const auto& u:f.created) require(u.x<blocked.left || u.x>blocked.right || u.y<blocked.top || u.y>blocked.bottom, "P3 guarded entry never receives a unit");
            require(f.units[1].owner==2 && !f.units[1].ordered, "Original rescue blocker stays untouched");
            Fixture all;all.prepared();all.tick();for(unsigned i=0;i<4;i++)all.block(i,2);all.run(95);
            require(all.created.empty() && !all.runtime.state().pending && all.runtime.state().stage==0, "Every newly blocked entry cancels the attempt");
        } else if (name == "caps") {
            for (int mode = 0; mode != 3; ++mode) {
                Fixture f; f.prepared();
                if (mode == 2) f.global_override = 1600;
                else for (int i = 0; i != (mode == 0 ? 480 : 240); ++i) f.units.push_back(Unit{6, mode == 0 ? 37 : 38, 1056, 1480});
                f.run(100); require(f.warnings.empty() && f.created.empty(), "240supply and1600global unit ceilings enforced");
            }
            for(int type:{37,38}){Fixture f;f.prepared();for(int i=0;i<(type==37 ? 71 : 23);i++)f.units.push_back(Unit{6,type,1056,1480});
                f.one_wave();require(f.created_supply()==16,"Historical71ling/23hydra reservation no longer blocks a safe wave");}
            Fixture edge;edge.prepared();for(int i=0;i<479;i++)edge.units.push_back(Unit{6,37,1056,1480});
            require(edge.one_wave()==1 && Fixture::count(&edge,6,37,nullptr)==480,"A near-full pool adds only its remaining half-supply without overshoot");
        } else if (name == "escalation") {
            Fixture f; f.prepared();
            for (unsigned i = 0; i != 15; ++i) {
                const auto start = f.created.size(); f.one_wave();
                const auto expected = 16 + 4 * std::min(i,12u);
                require(wave_progression::base_budget(false,i)==expected,"Wave budget rises by4half-supply then saturates at64");
                // Entry spacing can leave part of a budget unused (the fixture
                // keeps troops at their spawn cells until the next test step).
                // Successful creation must never spend above the budget.
                require(f.created_supply(start)>0 && f.created_supply(start)<=expected,"Placed troops stay within the ordinal supply budget");
                require(f.runtime.state().stage == i+1, "Every successful wave advances its ordinal even after budget saturation");
                f.clear_enemies();
            }
            for (unsigned second : {599u,600u,899u,900u}) {
                Fixture tier; tier.prepared(); tier.elapsed = second; tier.one_wave();
                require(tier.created_supply() == 16, "Time tier does not increase the first-wave supply budget");
                const auto has_air = std::any_of(tier.created.begin(),tier.created.end(),[](const Unit& u){return u.type==43 || u.type==44 || u.type==62;});
                const auto has_ultralisk = Fixture::count(&tier,6,39,nullptr)>0;
                require(has_air == (second>=900), "Air units begin at900seconds, never at899");
                require(has_ultralisk == (second>=600), "Middle ground tier begins at600seconds, never at599");
            }
        } else if (name == "stack_caps") {
            Fixture f;f.prepared();for(int i=0;i<6;i++){f.one_wave();f.clear_enemies();}
            for(int i=0;i<70;i++)f.units.push_back(Unit{6,i<48 ? 37 : 38,1056,1480});
            const auto prior = f.living_supply(); f.stacks=255; f.one_wave();
            require(f.living_supply()>prior+40 && f.living_supply()<=480,"High stacks exceed the unmodified40half-supply budget without violating240supply cap");
            // Some verified entry rectangles overlap. A real attack order moves
            // the created troops out before the next scheduled reinforcement.
            for(unsigned attempt=0;attempt<20 && f.living_supply()<480;++attempt){
                for(auto& u:f.units)if(u.owner==6 && u.ordered){u.x=1056;u.y=1480;}
                f.one_wave();require(f.living_supply()<=480,"Every wave respects remaining half-supply capacity");
            }
            require(f.living_supply()==480,"Subsequent safe waves fill remaining capacity exactly");
            require(f.units.size()<1600,"Higher supply cap still respects engine reserve");
            auto amount=f.created.size();f.run(2880);require(f.created.size()==amount,"Full240supply pool blocks the next wave");
        } else if (name == "budget_success") {
            Fixture f; f.prepared(); f.stacks = 1;
            f.one_wave();require(f.created_supply() == 20, "One stack adds25percent to first16half-supply budget");
            f.clear_enemies(); auto warnings = f.warnings.size();
            while (f.warnings.size() == warnings) f.tick();
            const auto prior = f.created.size();
            for(unsigned i=0;i<4;i++)f.block(i); f.run(95);
            require(f.runtime.state().stage == 1 && f.created.size()==prior, "Skipped attempt neither advances stage nor creates units");
            f.clear_blockers(); f.one_wave();
            require(f.created_supply(prior) == 25 && f.runtime.state().stage==2, "Next successful wave uses20base plus25percent, with no skipped-wave catchup");
        } else if (name == "occupied") {
            Fixture f; f.prepared(); f.tick(); const auto p = wave_config::kOrigins[0].cells[0];
            f.units.push_back(Unit{11, 176, p.x, p.y}); f.run(95);
            require(f.created_supply()==16 && f.units[1].x==p.x && f.units[1].y==p.y && f.units[1].owner==11 && f.units[1].type==176 && !f.units[1].ordered, "Other verified cells fill the16half-supply budget while original neutral position/type/order stay unchanged");
            for(const auto& u:f.created)require(u.x!=p.x || u.y!=p.y,"Occupied original cell is never used");
        } else if (name == "failure") {
            Fixture f; f.prepared(); f.stacks = 1; f.fail_creation = true; f.one_wave();
            require(f.created.empty() && f.runtime.state().stage == 0, "All native creation failures discarded");
            f.fail_creation = false; f.one_wave(); require(f.created_supply()==20 && f.runtime.state().stage==1, "Next ordinary attempt does not include failed units");
        } else if (name == "retry") {
            Fixture f; const auto p = wave_config::kOrigins[0].cells[0];
            f.units.push_back(Unit{6, 37, p.x, p.y}); f.units.push_back(Unit{4, 37, p.x, p.y}); f.run(720);
            require(f.units[0].ordered && !f.units[1].ordered && f.attack_owners.size() == 4, "Only P7 entry units get720-hook retry");
        } else if (name == "reset") {
            Fixture f; f.units.push_back(Unit{1, 7, 1056, 1600}); f.tick();
            f.runtime.tick(f.frame, true, 0, 0, false, f.host()); require(f.runtime.state().home_ticks == 1, "Same frame processed once");
            f.runtime.reset(); require(!f.runtime.state().home_seen && !f.runtime.state().has_frame && f.runtime.state().stage == 0, "New mission resets every state field");
        } else throw std::runtime_error("Unknown test case");
        std::cout << "PASS " << name << '\n'; return 0;
    } catch (const std::exception& e) { std::cerr << e.what() << '\n'; return 1; }
}
'''


class NativeWaveRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='sc1_native_wave_')
        cls.addClassCleanup(cls.temporary.cleanup)
        folder = Path(cls.temporary.name)
        harness = folder / 'wave_test.cpp'
        harness.write_text(WAVE_HARNESS, encoding='utf-8')
        cls.executable = folder / 'wave_test.exe'
        source = builder.ROOT / 'plugin/wave_runtime.cpp'
        include = builder.ROOT / 'plugin'
        compiler = shutil.which('clang++') or shutil.which('g++')
        if compiler:
            command = [compiler, '-std=c++17', '-Wall', '-Wextra', '-Werror', '-I', str(include),
                       str(source), str(harness), '-o', str(cls.executable)]
        else:
            setup = Path('C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvars64.bat')
            if not setup.is_file():
                raise unittest.SkipTest('No portable C++17 compiler is available')
            batch = folder / 'compile.cmd'
            batch.write_text('@echo off\ncall "' + str(setup) + '" >nul\n'
                             + 'if errorlevel 1 exit /b %errorlevel%\n'
                             + 'cl /nologo /std:c++17 /EHsc /W4 /WX /utf-8 /Od "'
                             + '/I' + str(include) + '" "' + str(source) + '" "' + str(harness)
                             + '" "/Fe:' + str(cls.executable) + '" /Fo:.\\\n', encoding='utf-8')
            command = ['cmd', '/d', '/c', str(batch)]
        result = subprocess.run(command, cwd=folder, capture_output=True, text=True, errors='replace', timeout=60,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise AssertionError('Portable wave test compilation failed:\n' + result.stdout + result.stderr)

    def case(self, name):
        result = subprocess.run([str(self.executable), name], capture_output=True, text=True, timeout=20,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout.strip(), 'PASS ' + name)

    def test_home_grace_trigger_time_and_warning_delay(self): self.case('timing')
    def test_growth_pending_and_goal_reached_freeze_waves(self): self.case('gate')
    def test_ally_near_first_entry_uses_alternate(self): self.case('alternate')
    def test_all_blocked_skips_without_catchup(self): self.case('blocked')
    def test_rechecks_p3_proximity_before_spawn(self): self.case('recheck')
    def test_global_and_added_supply_capacity_limits(self): self.case('caps')
    def test_time_tiers_and_supply_budget_growth_saturates(self): self.case('escalation')
    def test_curse_wave_and_active_pool_caps(self): self.case('stack_caps')
    def test_supply_budget_only_advances_on_successful_wave(self): self.case('budget_success')
    def test_occupied_cell_does_not_move_original_unit(self): self.case('occupied')
    def test_native_creation_failure_is_not_queued(self): self.case('failure')
    def test_stuck_retry_orders_only_p7_at_entries(self): self.case('retry')
    def test_frame_deduplication_and_new_mission_reset(self): self.case('reset')


if __name__ == '__main__':
    unittest.main()
