"""Compare EUD with load-time location bounds left intact (diagnostic only)."""
import hashlib
import importlib
import json
import struct
import argparse

from build_probes import MAPS, base_map


def build(once=False):
    import eudplib as ep
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata.chktok import CHK

    # Keep the default loader, startup and loop; change only its location
    # obfuscation key in this isolated compiler process. No vendor file edits.
    injector = importlib.import_module("eudplib.maprw.injector.apply_injector")
    def zero_location_key(size):
        assert size == 5100
        return bytes(size)
    injector.urandom = zero_location_key
    ep.CompressPayload(True)
    source = base_map(1)
    ep.LoadMap(str(source))

    def main():
        ep.f_setcurpl(ep.P1)
        ep.DoActions([
            ep.CreateUnit(1, "Terran Marine", "Start", ep.P1),
            ep.CreateUnit(1, "Terran Beacon", "Finish", ep.P12),
            ep.CreateUnit(1, "Terran Command Center", "Computer", ep.P2),
            ep.SetResources(ep.P1, ep.SetTo, 901 if once else 789, ep.Ore),
            ep.CenterView("Start"),
            ep.DisplayText("EUD ONCE: initialization has ended. Minerals 901, gas fixed at 1."
                           if once else "EUD BOUNDS: original location bounds. Minerals 789. Gas counts loops."),
        ])
        if once:
            ep.DoActions(ep.SetResources(ep.P1, ep.SetTo, 1, ep.Gas))
            return
        else:
            if ep.EUDInfLoop()():
                ep.DoActions(ep.SetResources(ep.P1, ep.Add, 1, ep.Gas))
                ep.EUDDoEvents()
            ep.EUDEndInfLoop()

    target = MAPS / ("SC1_EUD_Once_Test.scx" if once else "SC1_EUD_Bounds_Test.scx")
    ep.SaveMap(str(target), main)
    def read(path):
        archive = mpqapi.MPQ.open(str(path))
        chk = CHK()
        chk.loadchk(archive.extract_file("staredit\\scenario.chk"))
        del archive
        return chk
    original, compiled = read(source), read(target)
    before, after = original.getsection("MRGN"), compiled.getsection("MRGN")
    assert len(after) == 5100
    for offset in range(0,5100,20):
        assert before[offset:offset+16] == after[offset:offset+16]
        assert before[offset+18:offset+20] == after[offset+18:offset+20]
    assert struct.unpack_from("<4I", after,63*20)==(0,0,2048,2048)
    evidence={"schema_version":1,"path":str(target),
              "sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
              "bytes":target.stat().st_size,"load_time_location_bounds_preserved":255,
              "eud_loader":True,"eud_loop":not once,"shared_startup_helpers":True,
              "mailbox":False,"manager_required":False,"minerals":901 if once else 789,
              "native_verified":False}
    receipt = "eud_once_build_evidence.json" if once else "eud_bounds_build_evidence.json"
    (MAPS/receipt).write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(evidence))


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true")
    build(once=parser.parse_args().once)
