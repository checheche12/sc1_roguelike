"""Evidence-parser rejection tests; no StarCraft execution or measurement."""
from copy import deepcopy
import unittest
from analysis.resource_mining_20261015.engine_fixture.summarize_results import evaluate

class MiningEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture=dict(input_sha256='input-A',map_fnv=123,scope='synthetic parser test only')
        self.events=[dict(event='fixture_initialized',layout_evidence_sha256='input-A',map_fnv=123)]
        for phase in (0,1):
            for lane in range(6):
                self.events.append(dict(event='lane_result',phase=phase,lane=lane,mission=101,race='terran',
                    all_patches_harvested=True,all_patches_returned=True,deposit_reconciled=True,
                    mineral_deposit=80,returned_patches=4))
        self.events.append(dict(event='fixture_complete'))

    def test_complete_matching_measurements_are_accepted(self):
        self.assertTrue(evaluate(self.events,self.fixture)['passed'])

    def test_other_input_or_other_map_is_rejected(self):
        for key,value in (('layout_evidence_sha256','input-B'),('map_fnv',456)):
            events=deepcopy(self.events);events[0][key]=value
            self.assertFalse(evaluate(events,self.fixture)['passed'])

    def test_duplicate_lane_or_combined_runs_are_rejected(self):
        for extra in (self.events[1],self.events[0],self.events[-1]):
            self.assertFalse(evaluate(self.events+[extra],self.fixture)['passed'])

    def test_missing_lane_and_after_harvest_failure_are_rejected(self):
        self.assertFalse(evaluate(self.events[:-2]+self.events[-1:],self.fixture)['passed'])
        events=deepcopy(self.events);events[7]['all_patches_returned']=False
        self.assertFalse(evaluate(events,self.fixture)['passed'])

    def test_original_defect_can_be_measured_without_rejecting_repaired_result(self):
        events=deepcopy(self.events)
        for event in events:
            if event.get('phase')==0:
                event.update(all_patches_harvested=False,all_patches_returned=False,
                             deposit_reconciled=False,mineral_deposit=0,returned_patches=0)
        report=evaluate(events,self.fixture)
        self.assertTrue(report['passed'])
        self.assertIsNone(report['comparisons'][0]['deposit_ratio'])

if __name__=='__main__':unittest.main()
