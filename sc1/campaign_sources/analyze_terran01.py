"""Decode original Terran01 CHK structures, without normalizing or building them."""
from collections import Counter
from pathlib import Path
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parent
CONDITIONS = ['None','CountdownTimer','Command','Bring','Accumulate','Kill','CommandMost','CommandMostAt','MostKills','HighestScore','MostResources','Switch','ElapsedTime','Briefing','Opponents','Deaths','CommandLeast','CommandLeastAt','LeastKills','LowestScore','LeastResources','Score','Always','Never']
ACTIONS = ['None','Victory','Defeat','PreserveTrigger','Wait','PauseGame','UnpauseGame','Transmission','PlayWAV','DisplayText','CenterView','CreateUnitWithProperties','SetMissionObjectives','SetSwitch','SetCountdownTimer','RunAIScript','RunAIScriptAt','LeaderBoardControl','LeaderBoardControlAt','LeaderBoardResources','LeaderBoardKills','LeaderBoardScore','KillUnit','KillUnitAt','RemoveUnit','RemoveUnitAt','SetResources','SetScore','MinimapPing','TalkingPortrait','MuteUnitSpeech','UnmuteUnitSpeech','LeaderBoardComputerPlayers','LeaderBoardGoalControl','LeaderBoardGoalControlAt','LeaderBoardGoalResources','LeaderBoardGoalKills','LeaderBoardGoalScore','MoveLocation','MoveUnit','LeaderBoardGreed','SetNextScenario','SetDoodadState','SetInvincibility','CreateUnit','SetDeaths','Order','Comment','GiveUnits','ModifyUnitHitPoints','ModifyUnitEnergy','ModifyUnitShields','ModifyUnitResourceAmount','ModifyUnitHangarCount','PauseTimer','UnpauseTimer','Draw','SetAllianceStatus','DisableDebugMode','EnableDebugMode']
BRIEFING = ['None','Wait','PlaySound','TextMessage','MissionObjectives','ShowPortrait','HidePortrait','SpeakingPortrait','Transmission','EnableSkipTutorial']

def digest(data):
    return hashlib.sha256(data).hexdigest()

def parse_sections(data):
    pos, out, ordered = 0, {}, []
    while pos < len(data):
        name, size = struct.unpack_from('<4sI', data, pos)
        name = name.decode('ascii')
        pos += 8
        assert pos + size <= len(data)
        value = data[pos:pos+size]
        ordered.append({'name':name,'offset':pos-8,'bytes':size,'sha256':digest(value)})
        assert name not in out, f'duplicate section {name}'
        out[name] = value
        pos += size
    assert pos == len(data)
    return out, ordered

def analyze(path):
    raw = path.read_bytes()
    sections, ordered = parse_sections(raw)
    block = sections['STR ']
    count = struct.unpack_from('<H',block)[0]
    strings = {}
    for i in range(1, count+1):
        off = struct.unpack_from('<H',block,i*2)[0]
        chunk = block[off:block.index(b'\0',off)]
        try:
            strings[i] = chunk.decode('utf-8')
        except UnicodeDecodeError:
            strings[i] = chunk.decode('cp949', 'replace')
    unit_data = sections['UNIT']
    units = []
    assert len(unit_data) % 36 == 0
    for i in range(0, len(unit_data), 36):
        unit = unit_data[i:i+36]
        units.append({'index':i//36,'x':int.from_bytes(unit[4:6],'little'),'y':int.from_bytes(unit[6:8],'little'),
            'unit_id':int.from_bytes(unit[8:10],'little'),'player':unit[16]+1,'resources':int.from_bytes(unit[20:24],'little')})
    triggers = {}
    for key in ('TRIG','MBRF'):
        block=sections[key]
        assert len(block)%2400==0
        rows=[]
        for base in range(0,len(block),2400):
            record=block[base:base+2400]
            conditions=[]
            for i in range(16):
                loc,player,amount,unit,comparison,kind,resource,flags,internal=struct.unpack_from('<IIIHBBBBH',record,i*20)
                if kind:
                    conditions.append({'slot':i,'kind':kind,'name':CONDITIONS[kind] if kind<len(CONDITIONS) else str(kind),
                        'location':loc,'player':player,'amount':amount,'unit':unit,'comparison':comparison,'resource_or_switch':resource,'flags':flags})
            actions=[]
            names=BRIEFING if key=='MBRF' else ACTIONS
            for i in range(64):
                loc,text,wav,time,player,amount,unit,kind,modifier,flags,padding,internal=struct.unpack_from('<IIIIIIHBBBBH',record,320+i*32)
                if kind:
                    row={'slot':i,'kind':kind,'name':names[kind] if kind<len(names) else str(kind),'location':loc,
                        'string_id':text,'wav_id':wav,'time':time,'player':player,'amount':amount,'unit':unit,'modifier':modifier,'flags':flags}
                    if text: row['text']=strings.get(text,f'<invalid {text}>')
                    if wav: row['wav']=strings.get(wav,f'<invalid {wav}>')
                    if key=='TRIG' and kind in (15,16): row['ai_script']=struct.pack('<I',amount).decode('ascii','replace')
                    actions.append(row)
            rows.append({'index':base//2400,'conditions':conditions,'actions':actions,'flags':int.from_bytes(record[2368:2372],'little'),
                'owners':[i for i,b in enumerate(record[2372:2399]) if b],'sha256':digest(record)})
        triggers[key]=rows
    wav_ids=[n for n in struct.unpack('<'+'I'*(len(sections['WAV '])//4), sections['WAV ']) if n]
    switches=sorted({c['resource_or_switch'] for t in triggers['TRIG'] for c in t['conditions'] if c['kind']==11}
                    |{a['amount'] for t in triggers['TRIG'] for a in t['actions'] if a['kind']==13})
    title,description=struct.unpack('<HH',sections['SPRP'])
    return {'path':str(path.relative_to(ROOT)),'bytes':len(raw),'sha256':digest(raw),'title':strings[title],'description':strings[description],
        'sections':ordered,'dimensions':list(struct.unpack('<HH',sections['DIM '])), 'tileset':int.from_bytes(sections['ERA '],'little'),
        'version':int.from_bytes(sections['VER '],'little'),'owners':list(sections['OWNR']),'sides':list(sections['SIDE']),
        'strings':strings,'units':units,'unit_counts':dict(Counter(f"P{u['player']}:unit{u['unit_id']}" for u in units)),
        'used_switches_zero_based':switches,'wav_paths':[strings[i] for i in wav_ids],
        'triggers':triggers,'terminal_triggers':[t for t in triggers['TRIG'] if any(a['kind'] in (1,2,41,56) for a in t['actions'])]}

def main():
    variants={
        'sd': ROOT/'raw/SD/campaign/Terran/Terran01/staredit/scenario.chk',
        'kokr': ROOT/'raw/locales/koKR/Assets/campaign/Terran/Terran01/staredit/scenario.chk'}
    records={key:analyze(path) for key,path in variants.items()}
    for name,value in records.items():
        (ROOT/f'terran01_{name}_analysis.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps({'variant':name,'title':value['title'],'dimensions':value['dimensions'],'triggers':len(value['triggers']['TRIG']),
            'briefing':len(value['triggers']['MBRF']),'units':len(value['units']),'switches':value['used_switches_zero_based'],
            'terminal':value['terminal_triggers'],'wav':value['wav_paths']},ensure_ascii=False))

if __name__=='__main__':
    main()
