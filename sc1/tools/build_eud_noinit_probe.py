"""Isolate injector/loop from eudplib's optional shared startup helpers.

Diagnostic only. Overrides are local to this build process; vendor files and
the existing persistence probes are unchanged.
"""
import hashlib
import json

from build_probes import MAPS, base_map


def build():
    import eudplib as ep
    from eudplib.maprw.injector import mainloop

    disabled = ["_detect_locale", "_f_inituserplayerid", "_f_initisusercp",
                "_f_initstacktrace", "_f_initstattext"]
    for name in disabled:
        setattr(mainloop, name, lambda: None)
    ep.CompressPayload(True)
    ep.LoadMap(str(base_map(1)))

    def main():
        ep.f_setcurpl(ep.P1)
        ep.DoActions([
            ep.CreateUnit(1, "Terran Marine", "Start", ep.P1),
            ep.CreateUnit(1, "Terran Beacon", "Finish", ep.P12),
            ep.CreateUnit(1, "Terran Command Center", "Computer", ep.P2),
            ep.SetResources(ep.P1, ep.SetTo, 456, ep.Ore),
            ep.CenterView("Start"),
            ep.DisplayText("EUD NOINIT diagnostic. Minerals 456. Gas counts loops."),
        ])
        if ep.EUDInfLoop()():
            ep.DoActions(ep.SetResources(ep.P1, ep.Add, 1, ep.Gas))
            ep.EUDDoEvents()
        ep.EUDEndInfLoop()

    target = MAPS / "SC1_EUD_NoInit_Test.scx"
    ep.SaveMap(str(target), main)
    evidence = {"schema_version": 1, "path": str(target),
                "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "bytes": target.stat().st_size, "disabled_startup_helpers": disabled,
                "mailbox": False, "formatted_text": False, "manager_required": False,
                "minerals": 456, "gas_counts_loops": True, "native_verified": False}
    (MAPS / "eud_noinit_build_evidence.json").write_text(
        json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    build()
