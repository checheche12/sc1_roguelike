"""Offline standalone smoke check; never launches or attaches to StarCraft."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import tkinter
import traceback
from sc1 import __version__, RELEASE_CHANNEL

ROOT = Path(__file__).resolve().parents[1]

def main():
    report = {"python": sys.version, "executable": sys.executable,
              "root": str(ROOT), "sys_path": sys.path,
              "external_python_required": False, "game_started": False,
              "user_database_accessed": False}
    output = ROOT / "portable_self_test.json"
    try:
        from sc1.manager import installation
        from sc1.manager.store import open_campaign_store
        from sc1.manager.store import GrowthChoicesPending
        from sc1.campaign.runtime_catalog import load_catalog
        from sc1.campaign.missions import load_missions
        from sc1.manager import ui
        from sc1.bridge import __main__ as bridge
        package = installation._package()
        distribution=json.loads((ROOT/"distribution.json").read_text(encoding="utf-8"))
        assert distribution['version']==__version__ and distribution['release_channel']==RELEASE_CHANNEL
        report.update(version=__version__,release_channel=RELEASE_CHANNEL)
        for row in distribution["files"]:
            source=(ROOT/row["path"]).resolve()
            assert source.is_relative_to(ROOT)
            assert hashlib.sha256(source.read_bytes()).hexdigest()==row["sha256"], row["path"]
        child=subprocess.run([sys.executable,"-X","utf8","-m","sc1.bridge","--help"],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=20)
        assert child.returncode==0, child.stderr.decode("utf-8",errors="replace")
        assert b"usage:" in child.stdout
        report["windowed_bridge_subprocess"]=True
        report["distribution_files_verified"]=len(distribution["files"])
        assert all(Path(p).resolve().is_relative_to(ROOT) for p in sys.path if p)
        with tempfile.TemporaryDirectory(prefix="portable-probe-", dir=ROOT) as temporary:
            store = open_campaign_store(Path(temporary) / "record.sqlite3")
            assert store.status()
            wire=package['manifest'].get('growth_wire_version',1)
            if wire==2:
                nonce=None
                for phase in (1,2,3):
                    try:state=store.restore_growth_phase(101,2,phase,nonce=nonce)
                    except GrowthChoicesPending as pending:state=pending.state
                    while state.get('offer'):
                        offer=state['offer']
                        state=store.choose_growth_phase_slot(offer['offer_id'],1,offer['revision'],101,2,
                            choice_kind=1 if offer['kind']=='talent' else 2,phase=phase,nonce=nonce)
                    state=store.restore_growth_phase(101,2,phase,nonce=nonce)
                    nonce=state['nonce']
                    assert len(state['growth_words'])==65 and state['growth_words'][0]==2
                store.complete(101,nonce,0,0)
                report['revision_five_three_phase_sqlite_roundtrip']=True
            window = tkinter.Tk()
            window.withdraw()
            report["tk_version"] = window.tk.call("info", "patchlevel")
            manager = ui.ManagerWindow(window,Path(temporary)/"record.sqlite3",preferences_path=Path(temporary)/"preferences.json")
            assert window.title().endswith(" · "+__version__)
            report['manager_window_title']=window.title()
            assert not manager.auto_connect_enabled
            assert manager.process is None
            assert any(button.cget("text")=="스타크래프트 시작" for button in manager.installation_buttons)
            window.update_idletasks()
            report["manager_window_initialized"]=True
            report["game_does_not_auto_start"]=True
            manager.close()
        catalog = load_catalog(expected_version=package['manifest'].get('growth_wire_version',1))
        legacy=load_catalog()
        report.update(passed=True, scenarios=len(load_missions()),
                      talents=len(catalog["talents"]), curses=len(catalog["curses"]),
                      legacy_talents=len(legacy['talents']),legacy_curses=len(legacy['curses']),
                      growth_wire_version=package['manifest'].get('growth_wire_version',1),
                      payload_files=len(package["manifest"]["files"]),
                      manifest_sha256=package["sha256"],
                      tkinter_import=True, manager_import=True, bridge_import=True,
                      temporary_sqlite_roundtrip=True, relocated_package_validated=True)
        code = 0
    except Exception:
        report.update(passed=False, error=traceback.format_exc())
        code = 1
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return code

if __name__ == "__main__":
    raise SystemExit(main())
