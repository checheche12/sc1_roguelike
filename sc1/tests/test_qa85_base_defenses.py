"""Sized enemy bases, no inherited actor flags, and exact map append contract."""
import json
import struct
import unittest
from pathlib import Path
from sc1.native_campaign import base_defenses as defense,build_all_campaigns as maps
from sc1.campaign.missions import load_missions

class BaseDefenseTests(unittest.TestCase):
    def test_large_bases_and_existing_armies_receive_more_support(self):
        budgets=[defense.budget(score,4) for score in (6,20,40,70)]
        self.assertEqual([b[1] for b in budgets],[6,12,20,28])
        self.assertEqual([b[2] for b in budgets],[2,4,6,8])
        self.assertGreater(defense.budget(6,60)[1],defense.budget(6,4)[1])
        self.assertEqual(defense.budget(100,500)[1],40)

    def test_factions_and_separate_bases_are_not_merged(self):
        points=[(200,200,106,4),(300,200,111,4),(400,200,124,4),
                (200,250,154,5),(2000,2000,106,4),(3000,3000,124,4)]
        self.assertEqual(defense.clusters(points,{4,5}),[[0,1,2],[3],[4]])
        self.assertEqual(defense.clusters(points,{5}),[[3]])

    def test_new_units_have_no_objective_flags_links_or_partial_health(self):
        r=defense.record(65,4,1000,1200,123)
        self.assertEqual(len(r),36)
        self.assertEqual(maps.unit_info(r),(1000,1200,65,4))
        self.assertEqual(r[10:16],bytes(6))
        self.assertEqual(r[17:20],bytes((100,100,100)))
        self.assertEqual(r[20:],bytes(16))

    def test_all_shipped_map_reports_and_compiled_guard_positions_agree(self):
        root=Path(maps.__file__).parent
        receipt=json.loads((root/'all_campaign_maps_evidence.json').read_text(encoding='utf8'))
        missions={r['mission_id']:r for r in load_missions()};posts=[];changed=0
        for row in receipt['maps']:
            report=row['base_defenses'];chk=maps.CHK(Path(row['output']).read_bytes())
            after=chk.save();prefix=chk.getsection('UNIT')[:report['base_unit_count']*36]
            defense.undo(chk,report);self.assertEqual(chk.getsection('UNIT'),prefix)
            if missions[row['mission_id']]['no_production']:self.assertEqual(report['added'],[])
            for added in report['added']:
                self.assertIn(added['owner'],row['difficulty']['hostile_owners'])
                self.assertNotEqual(added['owner'],row['owner'])
                if added['role']=='defender':posts.append('{'+','.join(map(str,(row['mission_id'],added['unit'],added['owner'],*added['position'])))+'},')
            serials=[struct.unpack_from('<I',r)[0] for r in maps.units(maps.CHK(after))]
            extra=serials[report['base_unit_count']:]
            self.assertEqual(len(extra),len(set(extra)));self.assertFalse(set(extra)&set(serials[:report['base_unit_count']]))
            changed+=bool(report['added'])
        self.assertGreaterEqual(changed,50)
        header=(root/'plugin/include/base_defenses.generated.h').read_text(encoding='utf8').splitlines()
        self.assertEqual([s for s in header if s.startswith('{')],posts)

if __name__=='__main__':unittest.main()
