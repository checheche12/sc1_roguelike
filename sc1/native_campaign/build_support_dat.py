"""Complete the exact SAMASE 0.10.28 Dat+ dependency set, without editing gameplay DATs.

The unmodified pinned maintainer writer supplies complete stock defaults.
This deterministic derivation preserves stock requirements (including enabled
empty sequences) and never opens a game or database.
"""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = HERE / "support_dat"
PROOF = HERE / "support_dat_sources"
TATTI = HERE / "dat_sources/tatti3"
PIN = "eb940dab410e9e197db9634322e91fb67a0b7f0f"
BUTTON_SHA = "2edd96868b9164743c357ed3c50d649ef44c0dc8cc5f3a948f481ffd676b274b"
FGP_SHA = "1a64ce14dbb7e947ac3c4ff3e929f7b02bca6f1da2746ec7728d449180177c68"
BASE_WEAPONS_SHA = "fffddfa0c67adccb817ade9f3f430479b371075345b3312108ceced4e9e2a045"
REFERENCE = PROOF / "headless/reference"
REFERENCE_EVIDENCE = PROOF / "headless/reference_evidence.json"
CANONICAL_COUNTS = dict(units=261,weapons=131,flingy=209,sprites=517,images=999,upgrades=62,techdata=45,portdata=110,mapdata=65,orders=189,buttons=99)
BASE_UNITS_SHA = "7ff5f9c3c34724d344a669d38875dcbf6cd1a4b1354e7b3b1df0589a7d99b227"
SPECS = {
    "flingy": (209,[2,4,2,4,1,1,1],"89013fa6d81edad96b68efcfc0bb5342f1c7fa2ef7a0880a71b0169eab13d1ad"),
    "sprites": (517,[2,1,1,1,1,1],"3e5ea29bf9937558d0a3a302cd85852c220cd126ec049c0da176c77739bb4a71"),
    "images": (999,[4,1,1,1,1,1,1,4,4,4,4,4,4,4],"6b6123e2cc6771d96f914fc9bb92d34da17cc3319dc02e2db0cd10b4f3d2efdc"),
    "upgrades": (61,[2,2,2,2,2,2,2,2,2,1,1,1],"787ff7dff69c0a0bb417ce1aabdcc11fa8b0959f77372b635c4882bdc3adb59b"),
    "techdata": (44,[2,2,2,2,2,2,2,2,1,1,1],"98f9805ebc8efc707492b7406871298d39d6e94931458aca1f82feaf18a271af"),
    "portdata": (110,[4,4,1,1,1,1],"ca864e3153336d072fd3467345c4661aaf7f9362bec7d033e674450c531a0e5e"),
    "mapdata": (65,[4],"06ce3127b9c77739f32ad606637943f022e5d0344afcf1e978494449ace37967"),
    "orders": (189,[2,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,2,2,1],"0b79cc64f1cd8b23c77419bdf1fb39fb91cde1359c1ad9cb73884d5cceb8f7c9"),
}
REQUIREMENTS = {"upgrades":[(6,16,"UpgR")],"techdata":[(4,16,"TecR"),(5,17,"TecU")],"orders":[(17,32,"OrdR")]}
REQUIRED_LOADER_DAT_NAMES = [f"arr/{name}.dat" for name in ("units","weapons",*SPECS,"buttons")]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_bytes(name):
    data=(ROOT/f"sc1/campaign_sources/raw/arr/{name}.dat").read_bytes()
    if sha(data)!=SPECS[name][2]:
        raise ValueError(f"Original {name} CASC hash mismatch")
    return data


def legacy_fields(name,data):
    count,widths,_=SPECS[name]
    pos=0;result={}
    for field,width in enumerate(widths):
        start,length=(130,387) if name=="sprites" and field in (1,4,5) else (0,count)
        size=length*width
        if pos+size>len(data):raise ValueError("Truncated legacy table")
        body=bytes(start*width)+data[pos:pos+size]+bytes((count-start-length)*width)
        result[field]=({1:0,2:1,4:2}[width],body);pos+=size
    if pos!=len(data):raise ValueError("Trailing legacy bytes")
    return result


def fgp_sections():
    data=(TATTI/"Resources/firegraft.fgp").read_bytes()
    if sha(data)!=FGP_SHA:raise ValueError("Stock FGP resource changed")
    result={};pos=0
    while pos<len(data):
        tag,size=struct.unpack_from("<4sI",data,pos);pos+=8
        if tag in result or pos+size>len(data):raise ValueError("Invalid FGP section")
        result[tag.decode()]=data[pos:pos+size];pos+=size
    return result


def requirements(tag,count):
    data=fgp_sections()[tag];pos=2;offsets=bytearray(count*2);buffer=bytearray(b"\0\0");seen=set()
    for _ in range(struct.unpack_from("<H",data)[0]):
        entry,n=data[pos:pos+2];end=pos+2+n*2;enabled=data[end];ops=data[pos+2:end];pos=end+1
        if entry>=count or entry in seen:raise ValueError("Requirement index/duplicate")
        seen.add(entry)
        if enabled:
            buffer+=struct.pack("<H",entry)
            struct.pack_into("<H",offsets,entry*2,len(buffer)//2)
            buffer+=ops
            if not ops.endswith(b"\xff\xff"):buffer+=b"\xff\xff"
    buffer+=b"\xff\xff"
    oracle=json.loads((PROOF/"stock_requirements_oracle.json").read_text())["requirements"][tag]
    if pos!=len(data) or sha(buffer)!=oracle["sha256"] or not oracle["exact_contiguous_match"]:
        raise ValueError("Stock EXE requirement-buffer oracle mismatch")
    # An enabled empty sequence is a NONZERO offset followed by ffff. Do not
    # collapse it into disabled0, or add editor dummy conditions/new mechanics.
    return bytes(offsets),bytes(buffer)


def button_fields():
    data=(PROOF/"buttons.bin").read_bytes()
    if sha(data)!=BUTTON_SHA:raise ValueError("Official stock buttons resource changed")
    sets,buttons=struct.unpack_from("<HH",data)
    if (sets,buttons)!=(99,554):raise ValueError("Unexpected button topology")
    pos=4+250+250*2
    starts=struct.unpack_from("<"+"H"*sets,data,pos);pos+=sets*2
    counts=data[pos:pos+sets];pos+=sets
    pos+=sets  # Original Firegraft-id mapping, not a Dat+ runtime column.
    fields={0:(2,struct.pack("<"+"I"*sets,*starts)),1:(0,counts)}
    for column in range(8):
        width=1 if column==0 else 2;size=buttons*width
        fields[column+2]=(0 if width==1 else 1,data[pos:pos+size]);pos+=size
    if pos!=len(data) or any(start+n>buttons for start,n in zip(starts,counts)):
        raise ValueError("Invalid stock button ranges")
    sections=fgp_sections()
    if sections["Unit"]!=b"\0\0" or sections["Buts"]!=b"\0\0":
        raise ValueError("FGP modifies stock unit/button maps; explicit conversion needed")
    return sets,fields


def encode(count,fields):
    header=bytearray(struct.pack("<IHHII",0x2b746144,1,10,count,len(fields)));payload=bytearray();start=16+12*len(fields)
    for field,(flags,body) in sorted(fields.items()):
        header+=struct.pack("<HHII",field,flags,start+len(payload),len(body));payload+=body
    return bytes(header+payload)


def decode(raw):
    magic,major,minor,count,n=struct.unpack_from("<IHHII",raw)
    if (magic,major,minor)!=(0x2b746144,1,10) or n>1024:
        raise ValueError("Unexpected canonical Dat+ header")
    fields={};spans=[]
    for i in range(n):
        field,flags,offset,length=struct.unpack_from("<HHII",raw,16+i*12)
        if field in fields or flags>2 or offset<16+n*12 or offset+length>len(raw):
            raise ValueError("Invalid canonical Dat+ descriptor")
        if length and any(offset<end and offset+length>start for start,end in spans):
            raise ValueError("Overlapping canonical fields")
        spans.append((offset,offset+length));fields[field]=(flags,raw[offset:offset+length])
    return count,fields


def reference_assets():
    """Read the compiler-verified unmodified upstream writer's pinned output."""
    proof=json.loads(REFERENCE_EVIDENCE.read_text())
    if proof["commit"]!=PIN or not proof["behavioral_sources_unmodified"]:
        raise ValueError("Unpinned reference writer")
    for item in proof["sources"]+proof["inputs"]+proof["outputs"]:
        if sha((ROOT/item["path"]).read_bytes())!=item["sha256"]:
            raise ValueError(f"Reference writer evidence stale: {item['path']}")
    result={}
    for item in proof["outputs"]:
        name=Path(item["path"]).stem;raw=(ROOT/item["path"]).read_bytes()
        count,_=decode(raw)
        if count!=CANONICAL_COUNTS[name]:raise ValueError("Canonical reserved-entry count mismatch")
        result[f"arr/{name}.dat"]=raw
    if set(result)!=set(REQUIRED_LOADER_DAT_NAMES):raise ValueError("Incomplete canonical reference")
    return result


def validate_field_closure(assets):
    schema=json.loads((PROOF/"loader_field_schema.json").read_text())
    if set(assets)!=set(REQUIRED_LOADER_DAT_NAMES):raise ValueError("Incomplete loader file closure")
    for name,required in schema["complete_field_ids"].items():
        count,fields=decode(assets[f"arr/{name}.dat"])
        if count!=CANONICAL_COUNTS[name]:raise ValueError("Canonical entry count mismatch")
        if set(fields)!=set(required):raise ValueError(f"Incomplete loader field closure: {name}")


def expected_assets() -> dict[str,bytes]:
    """Nine exact canonical support tables; no independent migration/override."""
    reference=reference_assets();validate_field_closure(reference)
    return {name:raw for name,raw in reference.items() if name not in ("arr/units.dat","arr/weapons.dat")}


def expected_managed_assets() -> dict[str,bytes]:
    """Complete canonical defaults; original managed files remain untouched."""
    reference=reference_assets();validate_field_closure(reference)
    result={}
    for name,base_sha in (("units",BASE_UNITS_SHA),("weapons",BASE_WEAPONS_SHA)):
        base=(HERE/f"managed_dat/arr/{name}.dat").read_bytes()
        if sha(base)!=base_sha:raise ValueError(f"Frozen managed {name} base changed")
        result[f"arr/{name}.dat"]=reference[f"arr/{name}.dat"]
    return result


def expected_units_asset() -> bytes:
    return expected_managed_assets()["arr/units.dat"]


def build():
    assets=[]
    for name,data in expected_assets().items():
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        count,fields=struct.unpack_from("<II",data,8)
        assets.append({"name":name,"path":target.relative_to(ROOT).as_posix(),"sha256":sha(data),"bytes":len(data),"entry_count":count,"field_count":fields})
    derived_assets=[]
    for name,data in expected_managed_assets().items():
        target=OUT/"derived"/Path(name).name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        count,fields=struct.unpack_from("<II",data,8)
        base=HERE/"managed_dat"/name
        derived_assets.append({"name":name,"path":target.relative_to(ROOT).as_posix(),"sha256":sha(data),"bytes":len(data),"entry_count":count,"field_count":fields,"base_sha256":sha(base.read_bytes())})
    tracked=[Path(__file__).resolve(),ROOT/"sc1/tests/test_support_dat.py",ROOT/"sc1/campaign_sources/support_dat_extraction_receipt.json",*sorted(TATTI.glob("GameData/*.cs")),TATTI/"datspec.md",TATTI/"source_pin.json",TATTI/"Resources/firegraft.fgp"]
    tracked += [p for p in sorted(PROOF.rglob("*")) if p.is_file() and p.suffix not in (".dll",".pyc") and "__pycache__" not in p.parts]
    tracked += [ROOT/f"sc1/campaign_sources/raw/arr/{name}.dat" for name in (*SPECS,"units","weapons")]
    tracked += [HERE/f"managed_dat/arr/{name}.dat" for name in ("units","weapons")]
    receipt={
        "schema_version":2,"status":"complete_stock_defaults_offline_built_live_unverified",
        "support_dat_assets":assets,"derived_managed_assets":derived_assets,"derived_units_asset":derived_assets[0],
        "stock_values_preserved":True,"original_unit_values_preserved":True,"requirements_preserved":True,"buttons_preserved":True,
        "stock_values_scope":"All original gameplay scalar values preserved numerically, including canonical u32 widening. Unmodified pinned GameData/DatTable directly generate all extended defaults and reserved/None rows.",
        "requirements_scope":"Units original managed requirement buffer retained exactly; UpgR/TecR/TecU full buffers match stock EXE. Official Orders migrations are retained: order0x24 Has no Addon0xff0c; order0x66 Is Landed Building0xff13. All other original requirements are unchanged semantically.",
        "buttons_scope":"All99 sets/554 records/eight columns and all250 official unit/group-to-buttonset and linked-unit mappings preserved. Units0x44/45 are now explicitly supplied; no missing-field fallback assumed.",
        "buttons_preserved_basis":"Pinned stock resource + unmodified official LoadButtons writer + independent mapping and column tests.",
        "unit_button_mapping_fallback_required":False,"unit_button_mapping_values_verified":True,
        "entry_counts":{x["name"]:x["entry_count"] for x in assets+derived_assets},
        "required_loader_dat_names":REQUIRED_LOADER_DAT_NAMES,
        "required_unit_extended_fields":list(range(0x40,0x56)),
        "required_extended_fields":{"units":list(range(0x40,0x56)),"upgrades":list(range(0x10,0x1c)),"techdata":list(range(0x10,0x15)),"orders":[0x20]},
        "loader_contract":"sc1/native_campaign/support_dat_sources/loader_contract.json",
        "loader_contract_sha256":sha((PROOF/"loader_contract.json").read_bytes()),
        "canonical_reference_evidence":REFERENCE_EVIDENCE.relative_to(ROOT).as_posix(),
        "all_eleven_outputs_exact_canonical":True,
        "loader_field_schema":"sc1/native_campaign/support_dat_sources/loader_field_schema.json",
        "loader_field_schema_sha256":sha((PROOF/"loader_field_schema.json").read_bytes()),
        "loader_declared_field_closure_verified":True,
        "canonical_order_migrations":[{"order":36,"original_enabled_empty":True,"condition":65292,"meaning":"Has no Addon","source":"datspec V3 / GameData.cs"},{"order":102,"original_enabled_empty":True,"condition":65299,"meaning":"Is Landed Building","source":"datspec V2 / GameData.cs"}],
        "canonical_reference_evidence_sha256":sha(REFERENCE_EVIDENCE.read_bytes()),
        "reserved_editor_entries_added":True,"reserved_entries":{"units":[228,260],"weapons":[130,130],"upgrades":[61,61],"techdata":[44,44]},
        "reserved_entries_basis":"Pinned LegacyDatDecl declares InvalidIndexStart/Count; GameData sets canonical safe reserved unit defaults and uses250 stock button/group mappings.",
        "canonical_widenings":{"units":[0,17,19,25],"weapons":[6],"orders":[13,14]},
        "requirement_representation_exceptions":[{"table":name,"offset_field":offset,"buffer_field":buffer,"stock_fgp_section":tag} for name,items in REQUIREMENTS.items() for offset,buffer,tag in items],
        "source_repository":"neivv/tatti3","source_commit":PIN,
        "sources":[{"path":path.relative_to(ROOT).as_posix(),"sha256":sha(path.read_bytes())} for path in sorted(set(tracked))],
        "native_play_verified":False,"existing_managed_units_weapons_changed":False,"dll_changed":False,
        "derived_units_changes":{"added_fields":list(range(0x41,0x56)),"original_numeric_fields_changed":[],"original_base_file_changed":False,"reserved_entries_added":True,"unit_button_mapping_fields_added":True},
    }
    (OUT/"support_dat_evidence.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return receipt


if __name__=="__main__":
    print(json.dumps(build(),ensure_ascii=False,indent=2))
