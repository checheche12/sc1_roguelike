"""Desktop launch must use a matching sealed release, never mutable sources."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from sc1 import build_portable

ROOT=Path(__file__).resolve().parents[2]


class ManagerReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="manager-release-",dir=ROOT/"analysis")
        self.root=Path(self.tmp.name)
        self.sc1=self.root/"sc1"
        self.release=self.sc1/"dist/release with spaces"
        self.release.mkdir(parents=True)
        for name in ("Resolve_Manager.ps1","Start_Manager.ps1"):
            shutil.copy2(ROOT/"sc1"/name,self.sc1/name)
        self.files={
            "Start_Campaign.exe":b"launcher",
            "runtime/pythonw.exe":b"bundled-python",
            "sc1/campaign/runtime_talents_all.json":b"sealed catalog",
            "sc1/native_campaign/current_build.json":b'{"manifest":"builds/release/manifest.json"}',
        }
        manifest={"inputs":{"manager_sources":[{
            "path":"sc1/campaign/runtime_talents_all.json",
            "sha256":hashlib.sha256(b"sealed catalog").hexdigest()}]}}
        manifest_raw=json.dumps(manifest).encode()
        self.files["sc1/native_campaign/builds/release/manifest.json"]=manifest_raw
        for name,raw in self.files.items():
            path=self.release/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(raw)
        self.receipt={"source_manifest_sha256":hashlib.sha256(manifest_raw).hexdigest(),
                      "files":[{"path":name,"sha256":hashlib.sha256(raw).hexdigest()} for name,raw in self.files.items()]}
        (self.release/"distribution.json").write_text(json.dumps(self.receipt),encoding="utf-8")
        with patch.object(build_portable,"ROOT",self.root):
            build_portable.activate_manager(self.release)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self):
        return subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File",
            str(self.sc1/"Start_Manager.ps1"),"-CheckOnly"],capture_output=True,timeout=30)

    def test_development_edits_do_not_break_sealed_manager_and_preferences_stay(self):
        development=self.sc1/"campaign/runtime_talents_all.json"
        development.parent.mkdir(); development.write_bytes(b"in-progress different catalog")
        result=self.check()
        self.assertEqual(result.returncode,0,result.stderr.decode(errors="replace"))
        plan=json.loads(result.stdout)
        self.assertEqual(Path(plan["Executable"]),self.release/"Start_Campaign.exe")
        self.assertEqual(Path(plan["Preferences"]),self.sc1/"data/manager_preferences.json")
        self.assertFalse(plan["ExternalPythonRequired"])
        self.assertFalse(plan["StartsGame"])
        self.assertFalse((self.sc1/"data").exists())

    def test_changed_released_catalog_is_rejected(self):
        (self.release/"sc1/campaign/runtime_talents_all.json").write_bytes(b"tampered")
        self.assertNotEqual(self.check().returncode,0)
        before=(self.sc1/"manager_release.json").read_bytes()
        with patch.object(build_portable,"ROOT",self.root):
            with self.assertRaises(ValueError): build_portable.activate_manager(self.release)
        self.assertEqual((self.sc1/"manager_release.json").read_bytes(),before)

    def test_modified_receipt_and_outside_pointer_are_rejected(self):
        (self.release/"distribution.json").write_text("{}",encoding="utf-8")
        self.assertNotEqual(self.check().returncode,0)
        (self.sc1/"manager_release.json").write_text(json.dumps({"schema_version":1,"directory":"../outside",
            "distribution_sha256":"0"*64}),encoding="utf-8")
        self.assertNotEqual(self.check().returncode,0)

    def test_missing_release_does_not_fall_back_to_development(self):
        (self.sc1/"manager_release.json").unlink()
        self.assertNotEqual(self.check().returncode,0)


if __name__=="__main__": unittest.main()
