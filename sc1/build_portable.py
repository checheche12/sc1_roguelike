"""Build a relocatable Windows distribution with its own CPython/Tk runtime."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
NATIVE=ROOT/"sc1/native_campaign"
sys.path.insert(0,str(ROOT))
CAMPAIGN_DATA=("missions.json","runtime_talents.json","runtime_talents_all.json",
               "runtime_talents_v5.json","runtime_v5_contract.json","talent_rank_catalog.json")
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)

def runtime_sources(root=None):
    """Explicit application closure: Python modules and frozen catalogs only."""
    root=Path(root or ROOT)
    sources=[path for folder in ('campaign','manager','bridge') for path in sorted((root/'sc1'/folder).glob('*.py'))]
    sources += [root/'sc1'/name for name in ('__init__.py','portable_runtime.py')]
    sources += [root/'sc1/campaign'/name for name in CAMPAIGN_DATA]
    if any(not path.is_file() for path in sources):raise ValueError('A required portable runtime source/catalog is missing')
    return sources

def verify_manager_closure(output,manifest):
    output=Path(output).resolve()
    rows=manifest.get('inputs',{}).get('manager_sources',[])
    for row in rows:
        path=(output/row['path']).resolve()
        if Path(row['path']).is_absolute() or not path.is_relative_to(output) or not path.is_file() or sha(path)!=row['sha256']:
            raise ValueError('Portable manager source differs from native package: '+row['path'])
    if manifest.get('growth_wire_version')==2:
        names={row['path'] for row in rows}
        required={'sc1/campaign/'+name for name in CAMPAIGN_DATA}
        required |= {'sc1/campaign/rework_growth.py','sc1/campaign/talent_campaign_policy.py','sc1/bridge/protocol.py','sc1/manager/store.py'}
        if not required<=names:raise ValueError('Revision-five portable manager dependency pins are incomplete')

def activate_manager(output):
    """Point desktop entry scripts at an immutable matching manager/package."""
    output=Path(output).resolve()
    if not output.is_relative_to((ROOT/"sc1/dist").resolve()):
        raise ValueError("The active manager release must be inside sc1/dist")
    receipt=read(output/"distribution.json")
    verified={}
    for row in receipt["files"]:
        path=(output/row["path"]).resolve()
        if not path.is_relative_to(output) or path in verified or sha(path)!=row["sha256"]:
            raise ValueError("Changed manager release file: "+row["path"])
        verified[path]=row["sha256"]
    native=output/"sc1/native_campaign"
    manifest_path=(native/read(native/"current_build.json")["manifest"]).resolve()
    if verified.get(manifest_path)!=receipt["source_manifest_sha256"]:
        raise ValueError("Manager release and campaign package differ")
    for row in read(manifest_path)["inputs"]["manager_sources"]:
        if verified.get((output/row["path"]).resolve())!=row["sha256"]:
            raise ValueError("Manager release source differs: "+row["path"])
    for name in ("Start_Campaign.exe","runtime/pythonw.exe"):
        if (output/name) not in verified:
            raise ValueError("Missing bundled manager runtime: "+name)
    pointer=ROOT/"sc1/manager_release.json"
    temporary=pointer.with_suffix(".json.tmp")
    temporary.write_text(json.dumps({"schema_version":1,
        "directory":output.relative_to(ROOT/"sc1").as_posix(),
        "distribution_sha256":sha(output/"distribution.json")},indent=2)+"\n",encoding="utf-8")
    os.replace(temporary,pointer)
    return str(pointer)

def build(output, manifest_path=None):
    from sc1.manager import installation
    package=installation._package(manifest_path)
    sources=runtime_sources()
    output=Path(output).resolve()
    if not output.is_relative_to(ROOT) or output.exists():
        raise ValueError("Use a new output directory inside the workspace")
    source_runtime=Path(sys.base_prefix)
    if sys.version_info[:3]!=(3,11,8):
        raise ValueError("This release pins the verified CPython 3.11.8 runtime")
    output.mkdir(parents=True)
    runtime=output/"runtime"; runtime.mkdir()
    for name in ("python.exe","pythonw.exe","python3.dll","python311.dll","vcruntime140.dll","vcruntime140_1.dll","LICENSE.txt"):
        copy(source_runtime/name,runtime/name)
    for source in (source_runtime/"DLLs").iterdir():
        if source.suffix.lower() in (".dll",".pyd") and not source.name.startswith(("_test","_ctypes_test")):
            copy(source,runtime/"DLLs"/source.name)
    ignored={"site-packages","test","tests","__pycache__","idlelib","ensurepip"}
    bundled_stdlib=source_runtime/"python311.zip"
    if not (source_runtime/"Lib").is_dir() and bundled_stdlib.is_file():
        # Rebuild the native launcher from source even when the build itself
        # runs on our portable Python instead of a system Python installation.
        with zipfile.ZipFile(bundled_stdlib) as archive:
            if 'encodings/__init__.py' not in archive.namelist() or archive.testzip() is not None:
                raise ValueError('Bundled Python standard library is incomplete')
        copy(bundled_stdlib,runtime/"python311.zip")
    else:
        with zipfile.ZipFile(runtime/"python311.zip","w",zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
            for source in sorted((source_runtime/"Lib").rglob("*")):
                relative=source.relative_to(source_runtime/"Lib")
                if source.is_file() and not any(p in ignored for p in relative.parts) and source.suffix not in (".pyc",".pyo"):
                    archive.write(source,relative.as_posix())
    shutil.copytree(source_runtime/"tcl",runtime/"tcl",ignore=shutil.ignore_patterns("demos","msgs"))
    (runtime/"python311._pth").write_text("python311.zip\nDLLs\n.\n..\n",encoding="ascii")
    # Runtime source closure is explicit; no user record/workshop/cache is copied.
    for source in sources:copy(source,output/source.relative_to(ROOT))
    verify_manager_closure(output,package['manifest'])
    pin=read(NATIVE/"loader_pin.json")
    copy(NATIVE/"loader_pin.json",output/"sc1/native_campaign/loader_pin.json")
    copy(NATIVE/pin["local_filename"],output/"sc1/native_campaign"/pin["local_filename"])
    release=output/"sc1/native_campaign/builds/release"
    for row in package["manifest"]["files"]:
        copy(package["path"].parent/row["path"],release/row["path"])
    copy(package["path"],release/"manifest.json")
    pointer=output/"sc1/native_campaign/current_build.json"
    pointer.write_text('{"manifest":"builds/release/manifest.json"}\n',encoding="utf-8")
    (output/"sc1/data").mkdir()
    from sc1.build_environment import msvc_environment
    compiler, environment = msvc_environment(ROOT)
    intermediate=NATIVE/"build/portable_launcher"; intermediate.mkdir(parents=True,exist_ok=True)
    command=[str(compiler),"/nologo","/std:c++17","/EHsc","/MT","/utf-8","/W4","/WX",
             str(ROOT/"sc1/portable_launcher.cpp"),"/Fo:"+str(intermediate/"launcher.obj"),
             "/Fe:"+str(output/"Start_Campaign.exe"),"/link","/SUBSYSTEM:WINDOWS","/MACHINE:X64","user32.lib","shell32.lib"]
    result=subprocess.run(command,env=environment,cwd=intermediate,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (intermediate/"compile.log").write_bytes(result.stdout)
    if result.returncode: raise RuntimeError(result.stdout.decode("utf-8",errors="replace"))
    copy(output/"Start_Campaign.exe",output/"Campaign_Patcher.exe")
    for generated in output.glob("*.obj"): generated.unlink()
    licenses=output/"licenses"; licenses.mkdir()
    copy(source_runtime/"LICENSE.txt",licenses/"Python-LICENSE.txt")
    for source in (ROOT/"sc1/licenses").glob("*"):
        if source.is_file(): copy(source,licenses/source.name)
    # Tcl/Tk license files travel with the original runtime tree.
    (output/"사용방법.txt").write_text(
        "스타크래프트 캠페인 관리자\n\n"
        "1. ZIP 파일 전체를 쓰기 가능한 폴더에 압축 해제하세요. 파이썬 설치는 필요 없습니다.\n"
        "2. Start_Campaign.exe 또는 Campaign_Patcher.exe를 실행하세요.\n"
        "3. 저장 기록을 선택하고 스타크래프트 설치 경로를 지정하세요.\n"
        "4. 캠페인 패치를 설치한 뒤 '스타크래프트 시작' 버튼을 누르세요.\n"
        "5. 실행 파일 옆 runtime/sc1 폴더를 함께 보관하세요.\n\n"
        "지원: Windows 64비트, StarCraft Remastered "+pin["game_file_version_observed"]+"\n"
        "게임 및 사용자 저장 파일은 포함하지 않습니다. 패치는 설치 폴더의 별도 SC1CampaignGrowth 폴더에 배치합니다.\n"
        "캠페인 성장 기록은 sc1/data에 보관됩니다. 기존 기록은 관리자에서 직접 선택할 수 있습니다.\n"
        "임무는 새로 시작해 주세요. 임무 중 저장·불러오기는 지원하지 않습니다.\n"
        "재능·저주와 완료 기록은 자동 저장됩니다.\n"
        "전체 63개 지도는 구현·자동 검사되었으며 모든 임무 실전 완주 검증은 아직 진행 중입니다.\n",encoding="utf-8-sig")
    receipt={"schema_version":1,"built_at_utc":datetime.now(timezone.utc).isoformat(),"runtime":"CPython 3.11.8 x64 + Tk",
             "source_manifest_sha256":package["sha256"],"external_python_required":False,
             "includes_user_databases":False,"includes_workshop_data":False,
             'growth_wire_version':package['manifest'].get('growth_wire_version',1),
             'growth_contract':package['manifest'].get('growth_contract',{}),
             'catalogs':{name:{'sha256':sha(output/'sc1/campaign'/name)} for name in CAMPAIGN_DATA if name.startswith('runtime_talents')},
             "files":[{"path":p.relative_to(output).as_posix(),"sha256":sha(p),"bytes":p.stat().st_size}
                      for p in sorted(output.rglob("*")) if p.is_file()]}
    (output/"distribution.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"directory":str(output),"files":len(receipt["files"]),"bytes":sum(x["bytes"] for x in receipt["files"])}

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--manifest",type=Path)
    parser.add_argument("--activate-manager",action="store_true",
                        help="Use this sealed release for Start_Campaign.cmd and Start_Manager.cmd")
    args=parser.parse_args()
    result=build(args.output,args.manifest)
    if args.activate_manager:
        result["manager_release_pointer"]=activate_manager(args.output)
    print(json.dumps(result,ensure_ascii=False,indent=2))
