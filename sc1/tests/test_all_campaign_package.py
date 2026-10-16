"""All-map publication rejects incomplete rosters and unpaired runtime inputs."""
from pathlib import Path
from copy import deepcopy
import json
import struct
import tempfile
import unittest
from sc1.native_campaign import package_all_campaigns as package

class AllCampaignPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Exact geometric replay is expensive. Validate the immutable inputs
        # once; tamper tests below still validate their own modified receipts.
        cls.checked_inputs = package.inputs(package.DEFAULT_MAP_RECEIPT, package.DEFAULT_DLL_RECEIPT)

    def receipt(self, mutate, check):
        with tempfile.TemporaryDirectory(dir=package.ROOT / "build") as folder:
            value = package.legacy.read_json(package.DEFAULT_MAP_RECEIPT)
            mutate(value)
            path = Path(folder) / "maps.json"
            path.write_text(json.dumps(value), encoding="utf-8")
            check(path)

    def reject(self, path):
        with self.assertRaises(ValueError):
            package.validate_maps(path)

    def test_all_original_and_brood_war_assets_are_exactly_present(self):
        outputs, _, _, receipt = self.checked_inputs
        self.assertEqual(len(outputs), 63)
        self.assertEqual(receipt["logical_mission_count"], 57)
        self.assertEqual({path.split('/')[1] for path in outputs},
                         {"Terran", "Zerg", "Protoss", "EXPTerran", "EXPZerg", "EXPProtoss"})
        for row in receipt["maps"]:
            layout = row["resource_layout"]
            self.assertEqual(layout["functional_cluster_count"], layout["cluster_count"])
            self.assertEqual(layout["functional_geyser_count"], layout["geyser_count"])

    def test_missing_or_repeated_branch_cannot_publish(self):
        self.receipt(lambda v: v["maps"].pop(), self.reject)
        self.receipt(lambda v: v["maps"].append(dict(v["maps"][0])), self.reject)

    def test_wrong_asset_or_changed_chk_is_rejected(self):
        self.receipt(lambda v: v["maps"][0].update(asset_path="campaign/Terran/Terran02/staredit/scenario.chk"), self.reject)
        self.receipt(lambda v: v["maps"][0].update(sha256="0"*64), self.reject)

    def test_roster_header_is_pinned(self):
        self.receipt(lambda v: v.update(generated_header_sha256="0"*64), self.reject)

    def test_mineral_builder_and_planner_are_pinned(self):
        self.receipt(lambda v: v.update(map_builder_sha256="0"*64), self.reject)
        self.receipt(lambda v: v.update(mineral_layout_source_sha256="0"*64), self.reject)
        self.receipt(lambda v: v.update(resource_layout_source_sha256="0"*64), self.reject)
        self.receipt(lambda v: v.update(mining_layout_audit_source_sha256="0"*64), self.reject)
        self.receipt(lambda v: v.update(resource_depot_guard_source_sha256="0"*64), self.reject)

    def test_mineral_report_does_not_authorize_other_unit_or_resource_changes(self):
        receipt = package.legacy.read_json(package.DEFAULT_MAP_RECEIPT)
        row = next(r for r in receipt["maps"] if r["mission_id"] == 101)
        mission = next(m for m in package.load_missions() if m["mission_id"] == 101)
        source = package.CHK(Path(row["source"]).read_bytes())
        output_raw = Path(row["output"]).read_bytes()
        minerals = [i for i in range(0,len(source.getsection("UNIT")),36)
                    if struct.unpack_from('<H',source.getsection("UNIT"),i+8)[0] in (176,177,178)]
        non_mineral = next(i for i in range(0,len(source.getsection("UNIT")),36)
                           if struct.unpack_from('<H',source.getsection("UNIT"),i+8)[0] not in (176,177,178))
        for byte_offset in (minerals[0]+20,non_mineral+4,minerals[0]+4):
            output = package.CHK(output_raw)
            records = bytearray(output.getsection("UNIT"));records[byte_offset] ^= 1
            output.setsection("UNIT",records)
            with self.subTest(byte_offset=byte_offset), self.assertRaises(ValueError):
                package.verify_mineral_layout(source,output,mission,row)
        changed_report = deepcopy(row);changed_report["mineral_layout"]["forged"] = True
        with self.assertRaises(ValueError):
            package.verify_mineral_layout(source,package.CHK(output_raw),mission,changed_report)
        changed_report = deepcopy(row);changed_report["resource_layout"]["forged"] = True
        with self.assertRaises(ValueError):
            package.verify_mineral_layout(source,package.CHK(output_raw),mission,changed_report)

    def test_wave_origins_and_mission_metadata_are_pinned(self):
        self.receipt(lambda v: v.update(wave_generated_header_sha256="0"*64), self.reject)
        self.receipt(lambda v: v.update(mission_metadata_sha256="0"*64), self.reject)

    def test_aliases_cannot_escape_or_override_global_map(self):
        for asset in ("../scenario.chk", "C:/scenario.chk", "staredit/scenario.chk",
                      "campaign/Terran/../staredit/scenario.chk", "campaign\\Terran\\T01\\staredit\\scenario.chk"):
            with self.subTest(asset=asset), self.assertRaises(ValueError):
                package.safe_asset(asset)

    def test_current_compiled_runtime_and_catalog_match_all_maps(self):
        outputs, plugin, inputs, maps = self.checked_inputs
        self.assertEqual(len(outputs), 63)
        expected=(400,50) if inputs.get('growth_contract',{}).get('growth_wire_version')==2 else (238,15)
        self.assertEqual((inputs["implemented_talents"],inputs["implemented_curses"]),expected)
        if expected==(400,50):
            self.assertEqual(len(inputs['catalog_pins']),3)
            self.assertEqual(inputs['growth_contract']['manual_rank_slots_used'],12)
            self.assertIn('runtime_talents_all.json',inputs['legacy_expanded_catalog'])
        self.assertTrue(inputs["manager_sources"])
        self.assertTrue(all(not Path(row["path"]).is_absolute() for row in inputs["manager_sources"]))
        self.assertIn("samase_plugin_init", package.legacy.verify_dll(plugin)["exports"])

if __name__ == "__main__":
    unittest.main()
