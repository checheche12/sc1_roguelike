"""Air refresh uses real offer storage in a disposable database."""
from contextlib import closing
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from sc1.campaign.runtime_catalog import load_catalog
from sc1.manager.store import CampaignStore,GrowthChoicesPending

class AirAuditTests(unittest.TestCase):
    def test_old_health_revision_refreshes_without_rewriting_issued_offer(self):
        current=load_catalog(expected_version=2);prior=copy.deepcopy(current)
        for item in prior['talents']:
            if item.get('rework_revision')==5 and item.get('effect_ordinal') in (69,110):
                item['effect']['qa_revision']=2026101713
                item['description']='Previous health-only description'
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);catalog=folder/'catalog.json';db=folder/'record.sqlite3'
            catalog.write_text(json.dumps(prior),encoding='utf8')
            store=CampaignStore(db,new_profile='original',runtime_catalog_path=catalog)
            def load():
                try:return store.restore_growth_phase(101,2,1)
                except GrowthChoicesPending as pending:return pending.state
            state=load()
            with closing(sqlite3.connect(db)) as conn:issued=conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall()
            catalog.write_text(json.dumps(current),encoding='utf8')
            self.assertEqual(load()['offer'],state['offer'])
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute('SELECT offer_id,candidates_json FROM growth_offers').fetchall(),issued)
                pinned=json.loads(conn.execute('SELECT catalog_json FROM growth_rework_catalog').fetchone()[0])
            expected={x['id']:x for x in current['talents']}
            for item in pinned['talents']:
                if item.get('rework_revision')==5 and item.get('effect_ordinal') in (69,110):
                    new=expected[item['id']]
                    for field in ('description','effect','source_description','bit_index','rank_slot','max_rank'):
                        self.assertEqual(item.get(field),new.get(field))

    def test_bounded_corsair_and_carrier_metadata(self):
        items={x.get('effect_ordinal'):x for x in load_catalog(expected_version=2)['talents'] if x.get('rework_revision')==5}
        self.assertEqual(items[69]['effect']['qa_revision'],2026101930)
        fleet=items[110]['effect']
        self.assertEqual(fleet['qa_revision'],2026101930)
        self.assertEqual(fleet['corsair_range_tiles'],1)
        self.assertFalse(fleet['corsair_speed_bonus'])
        self.assertEqual(fleet['carrier_engagement_range_tiles'],1)
        self.assertFalse(fleet['air_control_stacks'])
        self.assertEqual(items[135]['effect']['attack_counter'],'primary_corsair_launch')
        self.assertFalse(items[135]['effect']['spells_count_as_attacks'])
        self.assertFalse(items[135]['effect']['secondary_attacks_count'])

if __name__=='__main__':unittest.main()
