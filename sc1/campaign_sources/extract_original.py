"""Extract installed SC1 base-campaign CHKs and first mission audio; never write the game."""
from pathlib import Path
import hashlib
import json
import re
from datetime import datetime, timezone
from casc_local import ROOT, DLL, Storage

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    game = Path('D:/blizard/StarCraft')
    source = ROOT / 'raw'
    inventory = json.loads((ROOT / 'campaign_inventory.json').read_text(encoding='utf-8'))
    pattern = re.compile(r'^(?:SD|locales\\koKR\\Assets)\\campaign\\(Terran|Zerg|Protoss)\\[^\\]+\\staredit\\scenario\.chk$', re.I)
    audio = re.compile(r'^(?:SD|locales\\koKR\\Assets)\\campaign\\Terran\\Terran01\\staredit\\wav\\', re.I)
    selected = [r for r in inventory if r['available'] and (pattern.match(r['name']) or audio.match(r['name']))]
    records = []
    with Storage(game) as storage:
        for row in sorted(selected, key=lambda r: r['name'].lower()):
            data = storage.read(row['name'])
            assert len(data) == row['bytes']
            assert hashlib.md5(data).hexdigest() == row['ckey']
            dest = source.joinpath(*row['name'].split('\\'))
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                assert dest.read_bytes() == data, 'Never overwrite a changed original asset'
            else:
                dest.write_bytes(data)
            records.append(dict(row, path=str(dest.relative_to(ROOT)), sha256=sha(data)))
    package = ROOT / 'tools/CascLib-3.0'
    receipt = {
        'schema_version': 1, 'created_at': datetime.now(timezone.utc).isoformat(),
        'game_path': str(game), 'game_build_info': (game / '.build.info').read_text(encoding='utf-8'),
        'local_only': True, 'strict_casc_checks': True, 'all_ckey_md5_match': True,
        'game_files_modified': False, 'game_process_accessed': False,
        'extractor': {'library': 'CascLib 3.0', 'source_url': 'https://github.com/ladislav-zezula/CascLib/tree/3.0',
            'source_commit_prefix': '4971d36', 'source_zip_sha256': sha((package/'source.zip').read_bytes()),
            'dll_sha256': sha(DLL.read_bytes()), 'build': 'cmake -A x64 -DCASC_UNICODE=ON -DCASC_BUILD_SHARED_LIB=ON; cmake --build --config Release --target casc'},
        'count': len(records), 'files': records,
        'scope': 'Original base-game three-race CHKs, tutorial included for provenance only; SD and installed Korean localization; Terran01 audio only. No map build or installation.'
    }
    (ROOT / 'extraction_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'extracted': len(records), 'bytes': sum(r['bytes'] for r in records), 'receipt': str(ROOT/'extraction_receipt.json')}, ensure_ascii=False))

if __name__ == '__main__':
    main()
