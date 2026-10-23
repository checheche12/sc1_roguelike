"""Opening strength accounting and first-wave timing on every mission."""
import json
import unittest
from pathlib import Path
from sc1.campaign.missions import load_missions
from sc1.native_campaign import build_all_campaigns as maps
from sc1.native_campaign import build_rework_wave_profiles as waves


class OpeningTimingTests(unittest.TestCase):
    def test_range_and_monotonic_strength(self):
        for hq in range(1,7):
            for buildings in range(hq,45):
                for workers in range(25):
                    t=waves.opening_seconds(hq,buildings,workers)
                    self.assertIn(t,range(240,301,10))
                    self.assertLessEqual(waves.opening_seconds(hq,buildings+1,workers),t)
                    self.assertLessEqual(waves.opening_seconds(hq+1,buildings+1,workers),t)
                    self.assertLessEqual(waves.opening_seconds(hq,buildings,workers+1),t)
        self.assertEqual(waves.opening_seconds(1,1,4),300)
        self.assertEqual(waves.opening_seconds(2,10,12),240)
        self.assertEqual(waves.opening_seconds(1,40,4),270)
        self.assertEqual(waves.opening_seconds(1,1,30),270)

    def test_only_owned_playable_assets_count(self):
        row=dict(mission_id=302,owner=7,no_production=False)
        own=[(100,100,154,7),(120,100,156,7),(100,120,64,7)]
        junk=[(100,100,154,6),(100,100,64,6),(100,100,214,7),(100,100,194,7)]
        a=waves.starting_strength(own,row);self.assertEqual(a,waves.starting_strength(own+junk,row))
        self.assertEqual((a['headquarters'],a['buildings'],a['effective_workers']),(1,2,5))
        row['mission_id']=309
        self.assertEqual(waves.starting_strength(own,row)['support_workers'],6)

    def test_main_island_and_map_worker_additions(self):
        rows={m['mission_id']:m for m in load_missions()}
        def strength(mid):
            row=rows[mid];chk=maps.CHK(Path(row['source']).read_bytes())
            return waves.starting_strength([maps.unit_info(u) for u in maps.units(chk)],row)
        island=strength(606)
        self.assertEqual((island['headquarters'],island['buildings'],island['effective_workers']),(2,7,4))
        zerg1=strength(201)
        self.assertEqual((zerg1['placed_workers'],zerg1['map_added_workers'],zerg1['support_workers'],zerg1['effective_workers']),(2,8,4,14))

    def test_all_generated_profiles_and_preserved_schedules(self):
        profiles=waves.derive()
        generated=json.loads((waves.ROOT/'sc1/native_campaign/rework_wave_profiles.json').read_text(encoding='utf8'))
        self.assertEqual(profiles,generated['profiles'])
        self.assertEqual(len(profiles),63)
        counts=dict(starting=0,settlement=0,disabled=0)
        for p in profiles:
            if not p['enabled']:
                counts['disabled']+=1;self.assertEqual(p['normal_first_seconds'],360)
            elif p['starting_headquarters']:
                counts['starting']+=1;s=p['starting_strength']
                self.assertEqual(p['normal_first_seconds'],waves.opening_seconds(s['headquarters'],s['buildings'],s['effective_workers']))
            else:
                counts['settlement']+=1;self.assertEqual(p['normal_first_seconds'],360)
            self.assertEqual((p['normal_interval_seconds'],p['normal_alternate_interval_seconds']),(120,150))
            self.assertEqual((p['warning_seconds'],p['appearance_seconds']),(20,4))
        self.assertEqual(counts,dict(starting=41,settlement=13,disabled=9))


if __name__=='__main__':unittest.main()
