"""Compile/run the unmodified pinned DAT writer against extracted stock files.

The only shims are media-only types/resources, after all DAT initialization.
No game executable, loader, process or user database is opened.
"""
from pathlib import Path
import hashlib
import json
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TATTI = HERE.parents[1] / "dat_sources/tatti3"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    csc = Path("C:/Program Files/Microsoft Visual Studio/2022/Community/MSBuild/Current/Bin/Roslyn/csc.exe")
    runtime = Path("C:/Program Files/dotnet/shared/Microsoft.NETCore.App/8.0.21")
    references = []
    for path in sorted(runtime.glob("*.dll")):
        raw = path.read_bytes()
        pe, = struct.unpack_from("<I", raw, 0x3c)
        optional = pe + 24
        directory = optional + (112 if struct.unpack_from("<H", raw, optional)[0] == 0x20b else 96)
        if struct.unpack_from("<I", raw, directory + 14 * 8)[0]:
            references.append(path)
    sources = [*sorted((HERE / "upstream").glob("*.cs")), *sorted((TATTI / "GameData").glob("*.cs")), HERE / "Headless.cs"]
    # Assert the five behavioral sources remain the pinned upstream bytes.
    pin = json.loads((TATTI / "source_pin.json").read_text())
    for item in pin["sources"]:
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Pinned Tatti source changed")
    extra = json.loads((HERE / "upstream_pin.json").read_text())
    for item in extra["sources"]:
        if sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError("Pinned support source changed")
    command = [str(csc), "/nologo", "/noconfig", "/nostdlib+", "/target:exe", "/nullable:enable", "/langversion:latest", "/deterministic+", "/out:" + str(HERE / "writer.dll"), *["/r:" + str(p) for p in references], *map(str, sources)]
    compiled = subprocess.run(command, capture_output=True, text=True)
    if compiled.returncode:
        raise RuntimeError(compiled.stdout + compiled.stderr)
    (HERE / "writer.runtimeconfig.json").write_text(json.dumps({"runtimeOptions": {"tfm": "net8.0", "framework": {"name": "Microsoft.NETCore.App", "version": "8.0.21"}}}))
    execute = ["C:/Program Files/dotnet/dotnet.exe", str(HERE / "writer.dll"), str(ROOT / "sc1/campaign_sources/raw"), str(HERE.parent), str(HERE / "reference")]
    run = subprocess.run(execute, capture_output=True, text=True)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    outputs = sorted((HERE / "reference/arr").glob("*.dat"))
    if len(outputs) != 11:
        raise ValueError("Expected all eleven official outputs")
    inputs = [*sorted((ROOT / "sc1/campaign_sources/raw/arr").glob("*.dat")), HERE.parent / "buttons.bin", TATTI / "Resources/firegraft.fgp"]
    receipt = {"repository": "neivv/tatti3", "commit": pin["commit"], "behavioral_sources_unmodified": True, "media_only_stubs": ["StringTable", "SfxData", "DdsGrp"], "compile_command": command, "execute_command": execute, "compiler_sha256": sha(csc), "writer_sha256": sha(HERE / "writer.dll"), "stdout": run.stdout.strip(), "sources": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in [*sources, Path(__file__).resolve(), HERE / "upstream_pin.json"]], "inputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p)} for p in inputs], "outputs": [{"path": p.relative_to(ROOT).as_posix(), "sha256": sha(p), "bytes": p.stat().st_size} for p in outputs], "native_game_execution": False}
    (HERE / "reference_evidence.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
