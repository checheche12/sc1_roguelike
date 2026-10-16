"""Minimal EUD runtime comparison: stock actions, no mailbox or formatted text."""
import hashlib
import json

from build_probes import MAPS, base_map


def build():
    import eudplib as ep
    ep.CompressPayload(True)
    ep.LoadMap(str(base_map(1)))

    def main():
        ep.f_setcurpl(ep.P1)
        ep.DoActions([
            ep.CreateUnit(1, "Terran Marine", "Start", ep.P1),
            ep.CreateUnit(1, "Terran Beacon", "Finish", ep.P12),
            ep.CreateUnit(1, "Terran Command Center", "Computer", ep.P2),
            ep.SetResources(ep.P1, ep.SetTo, 123, ep.Ore),
            ep.CenterView("Start"),
            ep.DisplayText("EUD CONTROL: Select/drag/move Marine and pan camera. No manager needed. Gas counts EUD loops."),
        ])
        if ep.EUDInfLoop()():
            ep.DoActions(ep.SetResources(ep.P1, ep.Add, 1, ep.Gas))
            ep.EUDDoEvents()
        ep.EUDEndInfLoop()

    target = MAPS / "SC1_EUD_Control_Test.scx"
    ep.SaveMap(str(target), main)
    evidence = {"schema_version": 1, "path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "bytes": target.stat().st_size, "kind": "minimal_eud_runtime_comparison",
                "mailbox": False, "formatted_text": False, "manager_required": False,
                "minerals": 123, "gas_counts_loops": True, "native_verified": False}
    (MAPS / "eud_control_build_evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    build()
