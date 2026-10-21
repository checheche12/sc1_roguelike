import json
from contextlib import closing
import sqlite3
import struct
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from sc1.campaign.mission_progress import locked_progress
from sc1.manager.store import open_campaign_store, ProtocolError
from sc1.manager.ui import ManagerWindow
from sc1.bridge.protocol import Dispatcher, RequestRejected, read_request
from sc1.tests.test_bridge import BASE
from sc1.tests.test_phased_bridge import PhaseMemory


class ExtendedMemory(PhaseMemory):
    def __init__(self):
        super().__init__()
        self.data.extend(bytes(256))
        self.set(5, 304); self.set(16, 128); self.set(18, 2); self.set(30, 2)

    def write(self, address, data):
        offset = address - BASE
        assert 128 <= offset < offset + len(data) <= 512
        self.writes.append((address, bytes(data)))
        self.data[offset:offset+len(data)] = data


class MissionProgress(unittest.TestCase):
    def test_empty_record_names_missing_and_first_playable_mission(self):
        value = locked_progress(304, 0)
        self.assertEqual(value['completed_count'], 0)
        self.assertIsNone(value['last_completed'])
        self.assertEqual([x['mission_id'] for x in value['missing_prerequisites']], [301,302,303])
        self.assertEqual(value['next_missions'][0]['mission_id'], 301)
        self.assertIn('출격', value['message'])
        self.assertIn('0/10', value['message'])
        self.assertLessEqual(len(value['native_message'].encode('utf8')), 332)

    def test_completed_progress_uses_current_campaign_and_preserves_rejected_record(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'temporary.sqlite3'
            store = open_campaign_store(path)
            with closing(sqlite3.connect(path)) as conn:
                conn.execute('UPDATE campaign SET completed_mask=?', ((1<<20)|(1<<21)|1,))
                conn.commit()
            before = path.read_bytes()
            with self.assertRaises(ProtocolError) as caught:
                store.restore_growth_phase(304,2,1,phase_version=2)
            details = caught.exception.details
            self.assertEqual(caught.exception.code, 'mission_locked')
            self.assertEqual(details['completed_count'], 2)
            self.assertEqual(details['last_completed']['mission_id'], 302)
            self.assertEqual([x['mission_id'] for x in details['missing_prerequisites']], [303])
            self.assertEqual(details['next_missions'][0]['mission_id'], 303)
            self.assertIn('불길 속으로', str(caught.exception))
            self.assertIn('고지', str(caught.exception))
            self.assertEqual(path.read_bytes(), before)

    def test_actual_rejection_publishes_bounded_utf8_reason_without_acknowledging_load(self):
        with tempfile.TemporaryDirectory() as folder:
            store = open_campaign_store(Path(folder) / 'temporary.sqlite3')
            memory = ExtendedMemory()
            dispatch = Dispatcher(memory, BASE, store)
            request = read_request(memory, BASE)
            with self.assertRaises(RequestRejected) as caught:
                dispatch._call_store(request, store.restore_growth_phase, 304, 2, 1, phase_version=2)
            self.assertEqual(caught.exception.code, 'mission_locked')
            self.assertEqual(memory.get(33), 3)
            self.assertEqual(memory.get(43), 0x45525231)
            size = memory.get(44)
            text = bytes(memory.data[180:180+size]).decode('utf8')
            self.assertIn('선행 임무 미완료', text)
            self.assertIn('0/10', text)
            self.assertIn('다음:', text)
            app = Mock()
            ManagerWindow.update_connection_status(app, json.dumps(dict(status='map_request_rejected', error_code='mission_locked', message=caught.exception.user_message)))
            self.assertIn('마지막 완료', app.connection.set.call_args.args[0])


if __name__ == '__main__':
    unittest.main()
