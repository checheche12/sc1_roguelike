"""Read installed campaign sources without changing game files or running the game."""
from pathlib import Path
import hashlib,json,re
from datetime import datetime,timezone
from casc_readonly import ROOT,Storage

def main():
    inv=json.loads((ROOT/'campaign_inventory.json').read_text(encoding='utf-8'))
    pattern=re.compile(r'^(?:SD|locales\\koKR\\Assets)\\campaign\\(?:EXP)?(?:Terran|Zerg|Protoss)\\[^\\]+\\staredit\\scenario\.chk$',re.I)
    names={r['name']:r for r in inv if r['available'] and pattern.match(r['name'])}
    tilesets=('badlands','platform','install','ashworld','jungle','desert','ice','twilight')
    records=[]
    with Storage('D:/blizard/StarCraft') as storage:
        for name in sorted(names):
            row=names[name];dest=ROOT/'raw'/Path(name.replace('\\','/'))
            data=dest.read_bytes() if dest.exists() else storage.read(name)
            assert len(data)==row['bytes'] and hashlib.md5(data).hexdigest()==row['ckey'],name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists():dest.write_bytes(data)
            records.append({'asset':name,'path':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
        for tileset in tilesets:
            for ext in ('cv5','vf4'):
                name=f'TileSet/{tileset}.{ext}';dest=ROOT/'raw'/name
                data=dest.read_bytes() if dest.exists() else storage.read(name)
                dest.parent.mkdir(parents=True,exist_ok=True)
                if not dest.exists():dest.write_bytes(data)
                records.append({'asset':name,'path':str(dest.relative_to(ROOT)),'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)})
    report={'schema_version':1,'built_at_utc':datetime.now(timezone.utc).isoformat(),'scope':'All base-game and Brood War original campaign CHKs plus terrain flags; tutorial and deleted missions retained only as source evidence','game_files_modified':False,'game_process_accessed':False,'readonly_casc_dll_sha256':hashlib.sha256((ROOT/'tools/CascLib-readonly/build-ninja/CascLib.dll').read_bytes()).hexdigest(),'readonly_adapter_sha256':hashlib.sha256((ROOT/'casc_readonly.py').read_bytes()).hexdigest(),'extractor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'files':records}
    (ROOT/'all_campaign_extraction_receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'files':len(records),'bytes':sum(r['bytes'] for r in records)}))
if __name__=='__main__':main()
