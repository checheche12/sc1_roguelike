"""Build original Terran01 with preserved local assets and the official CLI.

Run via sc1/vendor/eud-venv/Scripts/python.exe -B. --inspect-only never builds.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import time
import wave

from build_official_euddraft_baseline import read_chk, digest, RELEASE_DIR
from build_official_probes import release_info
from terran01_difficulty import apply as apply_difficulty
from terran01_choices import make_config as make_choice_config

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'campaign_sources'
CAMPAIGN = ROOT / 'campaign'
BUILD = CAMPAIGN / 'build/terran01'
OUTPUT = CAMPAIGN / 'maps/SC1_Original_Terran01.scx'
PLUGIN = ROOT / 'plugins/original_campaign.py'
DIFFICULTY_PLUGIN = ROOT / 'plugins/original_terran01_hard.py'
TALENT_PLUGIN = ROOT / 'plugins/original_talents.py'
TALENT_CATALOG = CAMPAIGN / 'runtime_talents.json'
CHOICE_PLUGIN = ROOT / 'plugins/original_choices.py'
RECEIPT = CAMPAIGN / 'terran01_build_evidence.json'
SOURCE = SOURCES / 'raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk'
SOURCE_HASH = '79d22b2fc00db3289528c2a70eef378d4ccf73880dcaaea36c6263145a20b381'
TITLE = 'Original T01 - 강화 황무지'
MAGIC = b'SC1CAMP-PROBE-V1'
# BWAPI UnitTypes enum and bundled eudplib EncodeUnit agree on these IDs.
BW_UNITS = {34:'Terran Medic', 58:'Terran Valkyrie', 60:'Protoss Corsair',
            61:'Protoss Dark Templar', 62:'Zerg Devourer', 63:'Protoss Dark Archon', 103:'Zerg Lurker'}
BW_UNIT_SOURCE = 'https://github.com/bwapi/bwapi/blob/main/bwapi/include/BWAPI/UnitType.h'
SCHEMA_SOURCE = 'https://github.com/TheNitesWhoSay/Chkdraft/blob/master/src/mapping_core/chk.h'
EXACT_SECTIONS = ('OWNR','ERA ','DIM ','SIDE','MTXM','THG2','MASK','FORC','MBRF','PUNI','PUPx','PTEx','COLR')

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def make_chk(raw):
    from eudplib.core.mapdata.chktok import CHK
    chk=CHK(); assert chk.loadchk(raw)
    return chk

def extend_rows(data, old_count, new_count):
    """Upgrade/technology restrictions: 12+12+1+1+12 rows, byte indexed."""
    assert len(data)==38*old_count
    rows=[]
    for row in range(38):
        # Added entries explicitly unavailable/unresearched/max0; local settings.
        rows.append(data[row*old_count:(row+1)*old_count]+bytes(new_count-old_count))
    return b''.join(rows)

def extend_costs(data, old_count, new_count, fields, padding=False):
    assert len(data)==old_count*(1+2*fields)
    out=data[:old_count]+bytes([1])*(new_count-old_count)
    if padding: out+=b'\0'
    for i in range(fields):
        start=old_count+i*old_count*2
        out+=data[start:start+old_count*2]+bytes((new_count-old_count)*2)
    return out

def legacy_to_expansion(chk):
    original=dict(chk.sections)
    assert chk.getsection('VER ')==struct.pack('<H',59)
    unis=chk.getsection('UNIS'); assert len(unis)==4048
    # The 228 unit fields are unchanged; weapon arrays expand 100 ->130.
    chk.setsection('UNIx', unis[:3648]+unis[3648:3848]+bytes(60)+unis[3848:4048]+bytes(60))
    chk.setsection('PUPx',extend_rows(chk.getsection('UPGR'),46,61))
    chk.setsection('PTEx',extend_rows(chk.getsection('PTEC'),24,44))
    chk.setsection('UPGx',extend_costs(chk.getsection('UPGS'),46,61,6,True))
    chk.setsection('TECx',extend_costs(chk.getsection('TECS'),24,44,4))
    mrgn=chk.getsection('MRGN'); assert len(mrgn)==1280
    chk.setsection('MRGN',mrgn+bytes(5100-len(mrgn)))
    chk.setsection('COLR',bytes(range(8)))
    chk.setsection('VER ',struct.pack('<H',205))
    puni=bytearray(chk.getsection('PUNI')); assert len(puni)==5700
    changes=[]
    for unit,name in BW_UNITS.items():
        for player in range(12):
            for offset in (player*228+unit,13*228+player*228+unit):
                if puni[offset]: changes.append({'offset':offset,'old':puni[offset],'new':0,'unit':unit,'name':name})
                puni[offset]=0
        offset=12*228+unit
        if puni[offset]: changes.append({'offset':offset,'old':puni[offset],'new':0,'unit':unit,'name':name})
        puni[offset]=0
    chk.setsection('PUNI',puni)
    verify_conversion(original,chk)
    return {'original_fields_verified':True,'puni_bw_only_changes':changes,
            'new_upgrade_technology_fields':'All new entries unavailable, unresearched, maximum0; costs use defaults',
            'schema_source':SCHEMA_SOURCE,'bw_unit_ids':BW_UNITS,'bw_unit_source':BW_UNIT_SOURCE}

def verify_conversion(original, converted):
    for old,new,a,b in (('UPGR','PUPx',46,61),('PTEC','PTEx',24,44)):
        src,dst=original[old.encode()],converted.getsection(new)
        assert len(dst)==38*b
        for row in range(38):
            assert dst[row*b:row*b+a]==src[row*a:(row+1)*a]
            assert dst[row*b+a:(row+1)*b]==bytes(b-a)
    for old,new,a,b,n,pad in (('UPGS','UPGx',46,61,6,1),('TECS','TECx',24,44,4,0)):
        src,dst=original[old.encode()],converted.getsection(new)
        assert dst[:a]==src[:a] and dst[a:b]==bytes([1])*(b-a)
        for i in range(n):
            assert dst[b+pad+i*b*2:b+pad+i*b*2+a*2]==src[a+i*a*2:a+(i+1)*a*2]
    src,dst=original[b'UNIS'],converted.getsection('UNIx')
    assert len(dst)==4168 and dst[:3848]==src[:3848] and dst[3908:4108]==src[3848:4048]
    assert dst[3848:3908]==bytes(60) and dst[4108:4168]==bytes(60)
    assert converted.getsection('MRGN')[:1280]==original[b'MRGN']
    src,dst=original[b'PUNI'],converted.getsection('PUNI')
    for i in range(5700):
        unit=i%228
        assert dst[i]==(0 if unit in BW_UNITS else src[i])
    for section in ('UNIT','MTXM','THG2','MASK','OWNR','SIDE','FORC','TRIG','MBRF'):
        assert converted.getsection(section)==original[section.encode()]

def parse_strings(chk):
    data=chk.getsection('STR ')
    n=struct.unpack_from('<H',data)[0]
    return [data[off:data.index(b'\0',off)] for off in struct.unpack_from('<'+'H'*n,data,2)]

def replace_title(chk):
    strings=parse_strings(chk)
    title_id=struct.unpack_from('<H',chk.getsection('SPRP'))[0]
    assert title_id==1 and strings[0]==b''
    strings[0]=TITLE.encode('utf-8')
    offset=2+len(strings)*2; offsets=[]
    for string in strings:
        offsets.append(offset); offset+=len(string)+1
    assert offset<65536
    chk.setsection('STR ',struct.pack('<H',len(strings))+struct.pack('<'+'H'*len(strings),*offsets)+b'\0'.join(strings)+b'\0')

def patch_victory(chk):
    triggers=bytearray(chk.getsection('TRIG')); assert len(triggers)==9*2400
    assert not any(triggers[t+c*20+15]==11 for t in range(0,len(triggers),2400) for c in range(16))
    assert not any(triggers[t+320+a*32+26]==13 for t in range(0,len(triggers),2400) for a in range(64))
    wins=[(t//2400,a) for t in range(0,len(triggers),2400) for a in range(64) if triggers[t+320+a*32+26]==1]
    assert wins==[(1,0)]
    offset=2400+320
    old=bytes(triggers[offset:offset+32])
    # Ordinary action struct: player2 field is switch index; modifier4 = Set.
    replacement=struct.pack('<IIIIIIHBBBBH',0,0,0,0,0,255,0,13,4,4,0,0)
    triggers[offset:offset+32]=replacement
    chk.setsection('TRIG',triggers)
    return {'trigger_index':1,'action_index':0,'old_hex':old.hex(),'new_hex':replacement.hex(),
            'only_trigger_patch_bytes':[offset,offset+32],'switch_editor_number':256,'switch_zero_based':255}

def audio_assets():
    ffmpeg=shutil.which('ffmpeg'); assert ffmpeg, 'ffmpeg must be installed for local Korean OGG decoding'
    output=BUILD/'audio'; output.mkdir(parents=True,exist_ok=True)
    entries=[]
    source_folder=SOURCE.parent/'wav'
    for source in sorted(source_folder.glob('*.ogg')):
        destination=output/(source.stem+'.wav')
        cmd=[ffmpeg,'-nostdin','-v','error','-y','-i',str(source),'-map_metadata','-1','-ac','1','-ar','22050','-c:a','pcm_s16le','-fflags','+bitexact',str(destination)]
        subprocess.run(cmd,check=True,capture_output=True,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        with wave.open(str(destination),'rb') as wav:
            assert wav.getnchannels()==1 and wav.getsampwidth()==2 and wav.getframerate()==22050
            duration=wav.getnframes()/wav.getframerate()
        entries.append({'source':str(source.relative_to(ROOT)),'source_sha256':digest(source.read_bytes()),
            'path':str(destination.relative_to(ROOT)),'archive_name':'staredit\\wav\\'+destination.name,
            'sha256':digest(destination.read_bytes()),'bytes':destination.stat().st_size,'duration_seconds':duration,
            'format':'PCM signed16 little-endian, mono22050Hz','command':cmd})
    assert len(entries)==8
    return entries

def prepare_input():
    import ctypes as C
    raw=SOURCE.read_bytes(); assert digest(raw)==SOURCE_HASH
    chk=make_chk(raw); original=dict(chk.sections)
    conversion=legacy_to_expansion(chk)
    difficulty=apply_difficulty(chk)
    choices=make_choice_config(chk)
    replace_title(chk)
    patch=patch_victory(chk)
    for name,data in original.items():
        if name not in (b'PUNI',b'VER ',b'MRGN',b'STR ',b'TRIG',b'UNIT',b'OWNR',b'SIDE',b'FORC'):
            assert chk.getsection(name)==data
    strings=parse_strings(chk)
    old_strings=parse_strings(make_chk(raw))
    assert strings[1:]==old_strings[1:]
    audio=audio_assets()
    referenced={strings[n-1].decode('ascii').lower() for n in struct.unpack('<512I',chk.getsection('WAV ')) if n}
    assert referenced=={a['archive_name'].lower() for a in audio}
    input_path=BUILD/'input.scx'
    # CHK.savechk adds a randomized protection tail; keep the prepared source
    # transparent and preserve its original editor ISOM instead.
    serialized=b''.join(name+struct.pack('<I',len(data))+data for name,data in chk.sections.items())
    chk_path=BUILD/'input.chk';chk_path.write_bytes(serialized)
    if input_path.exists(): input_path.unlink()  # Known generated file, under BUILD.
    # The Rust create wrapper omits the internal listfile required by the
    # official sector-size cloning path. Use local StormLib's documented
    # MPQ_CREATE_LISTFILE flag for this new, workspace-only source archive.
    dll=C.WinDLL(str(ROOT.parent/'tools/vendor/stormlib/x64/StormLib.dll'),use_last_error=True)
    create=dll.SFileCreateArchive;create.restype=C.c_bool;create.argtypes=[C.c_wchar_p,C.c_uint32,C.c_uint32,C.POINTER(C.c_void_p)]
    add=dll.SFileAddFileEx;add.restype=C.c_bool;add.argtypes=[C.c_void_p,C.c_wchar_p,C.c_char_p,C.c_uint32,C.c_uint32,C.c_uint32]
    close=dll.SFileCloseArchive;close.restype=C.c_bool;close.argtypes=[C.c_void_p]
    archive=C.c_void_p()
    if not create(str(input_path),0x00100000,1024,C.byref(archive)): raise C.WinError(C.get_last_error())
    try:
        files=[('staredit\\scenario.chk',chk_path)]+[(a['archive_name'],ROOT/a['path']) for a in audio]
        for name,path in files:
            if not add(archive,str(path),name.encode('ascii'),0x80000200,2,2): raise C.WinError(C.get_last_error())
    finally:
        if not close(archive): raise C.WinError(C.get_last_error())
    check,input_raw=read_chk(input_path); assert input_raw==serialized and check.sections==chk.sections
    result={'source_sha256':SOURCE_HASH,'input_sha256':digest(input_path.read_bytes()),
        'conversion':conversion,'difficulty':difficulty,'victory_patch':patch,'audio':audio,'all_original_strings_except_empty_title_preserved':True}
    write_json(BUILD/'difficulty.json',difficulty)
    write_json(BUILD/'choices.json', choices)
    catalog = json.loads(TALENT_CATALOG.read_text(encoding='utf-8'))
    assert catalog['catalog_version'] == 1 and catalog['source_board_revision'] == 469
    assert len(catalog['talents']) == 17 and len(catalog['curses']) == 3
    assert all(item['implemented'] and item['missions'] == [101] for item in catalog['talents'] + catalog['curses'])
    write_json(BUILD/'runtime_talents.json', catalog)
    write_json(BUILD/'input_preparation.json',result)
    return result

def inspect_output():
    from eudplib.bindings._rust import mpqapi
    from eudplib.core.mapdata import fixmapdata
    output,raw=read_chk(OUTPUT); prepared,_=read_chk(BUILD/'input.scx')
    source=make_chk(SOURCE.read_bytes())
    # Re-check conversion independently before examining the compiled map.
    converted=make_chk(SOURCE.read_bytes()); conversion=legacy_to_expansion(converted)
    difficulty=apply_difficulty(converted)
    choices=make_choice_config(converted)
    assert choices == json.loads((BUILD/'choices.json').read_text(encoding='utf-8'))
    assert difficulty==json.loads((BUILD/'difficulty.json').read_text(encoding='utf-8'))
    for name in ('UNIx','PUPx','PTEx','UPGx','TECx','PUNI','MRGN','COLR','UNIT','OWNR','SIDE','FORC'):
        assert prepared.getsection(name)==converted.getsection(name)
    for name in EXACT_SECTIONS:
        assert output.getsection(name)==prepared.getsection(name),name
    # Official CreateUnitWithProperties allocates one originally unused slot
    # for the temporary invulnerable selector/beacons. No stock action uses it.
    from eudplib import UnitProperty
    assert prepared.getsection('UPUS') == bytes(64)
    assert prepared.getsection('UPRP')[:20] == bytes(20)
    expected_properties = bytes(UnitProperty(invincible=True)) + prepared.getsection('UPRP')[20:]
    assert output.getsection('UPRP') == expected_properties
    normalized=prepared.clone();fixmapdata._fix_map_data(normalized)
    for name in ('UNIT','UNIx','UPGx','TECx'):
        assert output.getsection(name)==normalized.getsection(name),name
    assert output.getsection('VER ')==struct.pack('<H',206)
    assert struct.unpack_from('<H',OUTPUT.read_bytes(),14)[0]==15
    data=output.getsection('STRx')
    assert raw.count(MAGIC)==1 and data.count(MAGIC)==1
    mailbox=data.index(MAGIC); assert mailbox%4==0
    words=struct.unpack_from('<64I',data,mailbox)
    assert words[4:6]==(1,101) and words[6:16]==(0,)*10 and words[16]==64
    assert words[17:19] == (0x47525731, 1) and words[19] == 0
    assert words[20:22] == (0x43484331, 1) and words[22:] == (0,)*42
    catalog = json.loads((BUILD/'runtime_talents.json').read_text(encoding='utf-8'))
    assert catalog == json.loads(TALENT_CATALOG.read_text(encoding='utf-8'))
    strings=parse_strings(prepared)
    # Location names and empty editor strings are reusable slots in official
    # eudplib TBL allocation. Verify every actual game-facing string reference.
    required_strings=set(struct.unpack('<HH',prepared.getsection('SPRP')))
    required_strings.update(struct.unpack('<4H',prepared.getsection('FORC')[8:16]))
    required_strings.update(n for n in struct.unpack('<512I',prepared.getsection('WAV ')) if n)
    for section in ('TRIG','MBRF'):
        block=prepared.getsection(section)
        for t in range(0,len(block),2400):
            for a in range(64):
                start=t+320+a*32
                if block[start+26]:
                    required_strings.update(n for n in struct.unpack_from('<II',block,start+4) if n)
    for index in sorted(required_strings-{0}):
        value=strings[index-1]
        offset=struct.unpack_from('<I',data,index*4)[0]
        assert data[offset:data.index(b'\0',offset)]==value,('string',index)
    trigger_section=prepared.getsection('TRIG')
    trigger_offsets=[]
    for index in range(9):
        t=trigger_section[index*2400:(index+1)*2400]
        actions=b''.join(t[i:i+32] for i in range(320,2368,32) if t[i+26])
        conditions=b''.join(t[i:i+20] for i in range(0,320,20) if t[i+15] not in (0,22))
        # Official inliner may reorder per-owner trigger chains. Require each
        # complete condition/action body and its one-shot flags in the payload.
        candidates=[]; cursor=0
        while True:
            found=data.find(actions,cursor)
            if found<0: break
            cursor=found+1; start=found-328
            if start>=0 and data[start+8:start+8+len(conditions)]==conditions and data[start+8+len(conditions)+15]==0:
                assert struct.unpack_from('<I',data,start+2376)[0]==0
                candidates.append(start)
        assert len(candidates)==1,('stock trigger payload matches',index,candidates)
        trigger_offsets.append(candidates[0])
    # Every trigger originally belongs to P2 or Force1, whose sole member is P2.
    assert prepared.getsection('FORC')[1]==0 and all(prepared.getsection('FORC')[p]!=0 for p in range(8) if p!=1)
    for left,right in zip(trigger_offsets,trigger_offsets[1:]):
        assert struct.unpack_from('<I',data,left+4)[0]==0x191943C8+right
    # Official inlining groups the entire P2/Force1 chain into one dispatcher.
    compiled=output.getsection('TRIG'); assert len(compiled)==72*2400
    dispatcher=compiled[-4800:-2400]
    assert struct.unpack_from('<I',dispatcher)[0]==1024
    assert struct.unpack_from('<I',dispatcher,2368)[0]==0x10000008
    assert dispatcher[2372:2399]==bytes([0,1])+bytes(25)
    prep=json.loads((BUILD/'input_preparation.json').read_text(encoding='utf-8'))
    archive=mpqapi.MPQ.open(str(OUTPUT))
    try:
        for a in prep['audio']: assert digest(archive.extract_file(a['archive_name']))==a['sha256']
    finally: del archive
    return {'path':str(OUTPUT.relative_to(ROOT)),'sha256':digest(OUTPUT.read_bytes()),'bytes':OUTPUT.stat().st_size,
        'internal_title':TITLE,'scenario_chk_bytes':len(raw),'mission_id':101,'human_player':'P2','reward_delta':0,
        'mailbox_words_verified':True,'mailbox_strx_offset_not_runtime_address':mailbox,
        'all_9_original_trigger_bodies_and_order_verified':True,'payload_trigger_offsets':trigger_offsets,
        'only_original_victory_replaced':True,'original_defeats_and_resource_actions_preserved':True,
        'original_dialogue_objective_and_briefing_strings_verified':True,'briefing_bytes_preserved':True,
        'audio_files_verified':len(prep['audio']),'audio':prep['audio'],'conversion':conversion,
        'difficulty':difficulty,'difficulty_config':'campaign/build/terran01/difficulty.json',
        'exact_gameplay_sections_verified':list(EXACT_SECTIONS),'normalized_sections_verified':['UNIT','UNIx','UPGx','TECx'],
        'source':str(SOURCE.relative_to(ROOT)),'source_sha256':SOURCE_HASH,'source_receipt':'campaign_sources/extraction_receipt.json',
        'native_verified':False,'installed_in_game':False,'talents_implemented':True,
        'growth_catalog_version':1,'growth_source_board_revision':catalog['source_board_revision'],
        'implemented_talent_count':len(catalog['talents']),'implemented_curse_count':len(catalog['curses']),
        'ingame_choices':True,'choices':choices,'choice_unit_property_slot':1,
        'unused_property_slot_verified':True}

def build():
    BUILD.mkdir(parents=True,exist_ok=True);OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    protected={p:digest(p.read_bytes()) for p in (ROOT/'maps').glob('*.scx')}
    if OUTPUT.exists() or RECEIPT.exists():
        backup=ROOT/'backups'/('original_t01_build_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        for p in (OUTPUT,RECEIPT,BUILD/'input_preparation.json',BUILD/'official_cli_build.log',BUILD/'difficulty.json',BUILD/'runtime_talents.json',BUILD/'choices.json'):
            if p.exists():
                dest=backup/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    official=release_info();preparation=prepare_input()
    config=BUILD/'campaign.eds'
    config.write_text('[main]\ninput: input.scx\noutput: ../../maps/SC1_Original_Terran01.scx\n\n[../../../plugins/original_campaign.py]\nmission: 101\ndifficulty: difficulty.json\ndifficulty_plugin: ../../../plugins/original_terran01_hard.py\ntalent_catalog: runtime_talents.json\ntalent_plugin: ../../../plugins/original_talents.py\nchoices: choices.json\nchoices_plugin: ../../../plugins/original_choices.py\n\n[eudTurbo]\n\n[freeze]\nfreeze: 0\n',encoding='utf-8')
    command=[official['executable'],str(config)]
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';started=time.time_ns()
    result=subprocess.run(command,cwd=BUILD,input='\n',capture_output=True,text=True,encoding='utf-8',errors='replace',
        timeout=180,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    log=result.stdout+'\n'+result.stderr
    (BUILD/'official_cli_build.log').write_text(log,encoding='utf-8');print(log)
    assert result.returncode==0 and '[Error]' not in log and 'euddraft 0.11.0.0' in log
    assert OUTPUT.exists() and OUTPUT.stat().st_mtime_ns>=started
    prefix='SC1_ORIGINAL_BUILD_INFO='
    lines=[line[len(prefix):] for line in log.splitlines() if line.startswith(prefix)];assert len(lines)==1
    info=json.loads(lines[0]);assert info['mission']==101 and info['freeze_enabled'] is False
    evidence=inspect_output()
    for p,h in protected.items():assert digest(p.read_bytes())==h
    for name,h in official['file_sha256'].items():assert digest((RELEASE_DIR/name).read_bytes())==h
    evidence.update({'schema_version':1,'status':'official_cli_compiled_structurally_verified_native_pending',
        'official_cli_version':'0.11.0.0','eudplib_version':'0.81.0','official_cli_command':command,
        'official_executable_sha256':official['executable_sha256'],'official_asset_sha256':official['package_sha256'],
        'official_package_files_unchanged':True,'config':str(config.relative_to(ROOT)),'config_sha256':digest(config.read_bytes()),
        'plugin':str(PLUGIN.relative_to(ROOT)),'plugin_sha256':digest(PLUGIN.read_bytes()),'build_info':info,
        'difficulty_plugin':str(DIFFICULTY_PLUGIN.relative_to(ROOT)),
        'difficulty_plugin_sha256':digest(DIFFICULTY_PLUGIN.read_bytes()),
        'difficulty_config_sha256':digest((BUILD/'difficulty.json').read_bytes()),
        'talent_plugin':str(TALENT_PLUGIN.relative_to(ROOT)),
        'talent_plugin_sha256':digest(TALENT_PLUGIN.read_bytes()),
        'talent_catalog':str(TALENT_CATALOG.relative_to(ROOT)),
        'talent_catalog_sha256':digest(TALENT_CATALOG.read_bytes()),
        'frozen_build_catalog_sha256':digest((BUILD/'runtime_talents.json').read_bytes()),
        'choices_plugin':str(CHOICE_PLUGIN.relative_to(ROOT)),
        'choices_plugin_sha256':digest(CHOICE_PLUGIN.read_bytes()),
        'choices_config_sha256':digest((BUILD/'choices.json').read_bytes()),
        'input_preparation':str((BUILD/'input_preparation.json').relative_to(ROOT)),
        'input_sha256':preparation['input_sha256'],'build_log':str((BUILD/'official_cli_build.log').relative_to(ROOT)),
        'victory_patch':preparation['victory_patch'],'other_maps_unchanged':True,
        'eudTurbo':True,'freeze_enabled':False,'sector_size':15,'injector_monkeypatch':False,
        'limitations':['Native controls, Korean text/briefing/audio and completion ACK gate require playtesting.',
            'Engine default balance parity between original and BroodWar rulesets is not proven.',
            'Only Terran01 is built/strengthened; no automatic next-map action.',
            '17 talents and3 curses are implemented forT01; remaining workshop entries are drafts.',
            'Terran DAT edits affect regular friendly Terran types globally inT01; Raynor19/weapon5 are excluded.',
            'Difficulty balance, growth effects, wave pathing and the new geyser need native playtesting.']})
    write_json(RECEIPT,evidence)
    print(json.dumps({'output':str(OUTPUT),'receipt':str(RECEIPT),'sha256':evidence['sha256']},ensure_ascii=False))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inspect-only',action='store_true');args=parser.parse_args()
    if args.inspect_only:
        result=inspect_output();receipt=json.loads(RECEIPT.read_text(encoding='utf-8'))
        assert result['sha256']==receipt['sha256'] and digest(PLUGIN.read_bytes())==receipt['plugin_sha256']
        assert digest(DIFFICULTY_PLUGIN.read_bytes())==receipt['difficulty_plugin_sha256']
        assert digest((BUILD/'difficulty.json').read_bytes())==receipt['difficulty_config_sha256']
        assert digest(TALENT_PLUGIN.read_bytes())==receipt['talent_plugin_sha256']
        assert digest(TALENT_CATALOG.read_bytes())==receipt['talent_catalog_sha256']
        assert digest(CHOICE_PLUGIN.read_bytes())==receipt['choices_plugin_sha256']
        assert digest((BUILD/'choices.json').read_bytes())==receipt['choices_config_sha256']
        print(json.dumps(result,ensure_ascii=False,indent=2))
    else:build()

if __name__=='__main__':main()
