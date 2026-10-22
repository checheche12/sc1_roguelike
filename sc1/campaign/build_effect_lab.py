"""Build the isolated 256x256 ordinary-trigger effect lab (no game launch)."""
from pathlib import Path
import collections,hashlib,html,json,struct,sys,tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
MARKER=b'SC1_EFFECT_LAB_V1_QA65'
ROSTER=[0,1,2,3,5,7,8,9,11,12,13,32,34,37,38,39,40,41,42,43,44,45,46,47,50,58,60,61,62,63,64,65,66,67,68,69,70,71,72,81,84,103]
BUILDINGS=[106,109,111,112,113,114,115,116,117,118,120,122,124,125,131,132,133,134,135,136,137,138,139,140,141,142,143,144,146,149,154,155,156,157,159,160,162,163,164,165,166,167,169,170,171,172]

def generate_controls(catalog,root=ROOT):
    lines=['#pragma once','namespace effect_lab_data {','struct Talent {unsigned word,shift,width,slot,maximum;};','inline constexpr Talent talents[]={']
    for t in catalog['talents']:
        storage=t.get('wire_storage');slot=t.get('rank_slot',-1)
        if storage:word,shift,width=storage['word'],storage['shift'],storage['width']
        else:word,shift,width=t['bit_index']//32+1,t['bit_index']%32,1
        maximum=t.get('max_rank',4 if slot>=0 else 1)
        lines.append('{'+','.join(str(x)+'u' for x in (word,shift,width,slot if slot>=0 else 0xffffffff,maximum))+'},')
    lines+=['};','inline constexpr unsigned roster[]={'+','.join(str(x)+'u' for x in ROSTER)+'};','}']
    path=root/'sc1/native_campaign/plugin/include/effect_lab.generated.h';path.write_text('\n'.join(lines)+'\n',encoding='utf8');return path

def strings(values):
    pos=2+2*len(values);offsets=[]
    for value in values:offsets.append(pos);pos+=len(value)+1
    assert pos<65536
    return struct.pack('<'+'H'*(len(values)+1),len(values),*offsets)+b'\0'.join(values)+b'\0'

def unit(index,uid,owner,x,y,resources=0):
    b=bytearray(36);struct.pack_into('<IHHHHHH',b,0,index,x,y,uid,0,0,0);b[16]=owner
    if resources:struct.pack_into('<H',b,14,0x10);struct.pack_into('<I',b,20,resources)
    return bytes(b)

def checklist(catalog):
    rows=[]
    for kind,key,cmd in (('재능','talents','t'),('저주','curses','c')):
        for i,t in enumerate(catalog[key]):
            command=f'-{cmd} {i} 1';desc=t['description'];retired=t.get('effect',{}).get('retired',False)
            units=', '.join(map(str,t.get('target_units',[])))
            rows.append(f'<tr data-search="{html.escape(kind+" "+t["name"]+" "+t.get("race","")+" "+desc,quote=True)}"><td><input type="checkbox" data-key="{cmd}{i}"></td><td>{kind} {i}</td><td>{html.escape(t["name"])}</td><td>{html.escape(t.get("rarity", ""))}</td><td>{html.escape(desc)}<br><small>유닛 ID: {units}; {"사용 중단된 과거 효과" if retired else "개별 적용 후 기본 상태와 비교"}</small></td><td><button onclick="navigator.clipboard.writeText(\'{command}\')">{command}</button></td></tr>')
    result='''<!doctype html><html lang="ko"><meta charset="utf-8"><title>효과 통합 시험 목록</title><style>body{font:16px system-ui;margin:28px;max-width:1500px;background:#151b24;color:#edf4ff}input,button{font:inherit}#q{width:70%;padding:10px}table{border-collapse:collapse;width:100%}th,td{padding:10px;border:1px solid #46546a;text-align:left}small{color:#abc}button{cursor:pointer}thead{position:sticky;top:0;background:#253044}</style><h1>256×256 효과 통합 시험장</h1><p>Start_Effect_Lab.cmd 실행 → 싱글 플레이 → 사용자 지정 게임 → SC1_Roguelike/SC1_Effect_Lab.scx → 유즈맵 설정. 채팅창에 아래 명령을 입력합니다. 캠페인 기록 연결은 필요 없습니다.</p><p><b>-help</b> 도움말 · <b>-clear</b> 효과 해제 · <b>-t 번호 단계</b> 재능 · <b>-c 번호 중첩</b> 저주 · <b>-reset</b> 시험 병력 초기화 · <b>-heal</b> 체력/마나 회복 · <b>-hurt</b> 아군 체력 절반 · <b>-spawn 유닛ID 수 소유자</b> 생성(아군0, 적6) · <b>-case 1~8</b> 시험 세트 · <b>-up 업그레이드ID 단계</b> 무기/방어 업그레이드 · <b>-wave</b> 선택한 저주의 추가 공세.</p><p>세트: 1 히드라, 2 러커(직접 잠복), 3 뮤탈, 4 가디언, 5 마법, 6 타워, 7 수송, 8 근접/스플래시. -case는 시험 구역 병력만 교체하며 적용 재능은 유지합니다. -reset은 효과와 이동 병력을 초기화합니다. -spawn으로 일반 유닛·영웅·건물을 추가할 수 있습니다.</p><p>예: -clear → -t 256 1 → -t 335 1 → -case 2 → 러커 잠복 → 공중 적 A 클릭/우클릭. 타워 -t 560 1/2; 뮤탈 -t 343 1; 가디언 -t 429 1. 먼저 효과 하나를 시험하고 조합을 더하세요. 전체 효과 동시 활성화는 서로 덮어쓸 수 있어 권장하지 않습니다.</p><p>체크 표시는 이 브라우저에 보관되며 실제 게임에서 직접 확인한 항목만 표시하세요. 이 목록의 생성이나 자동 검사는 전투 검증 완료를 뜻하지 않습니다. 과거 호환 효과와 사용 중단 효과도 식별을 위해 표시합니다.</p><p><b>-race 1/2/3</b>은 테란/저그/프로토스 캠페인 문맥입니다. 시작 자원·일꾼 효과는 해당 문맥을 고른 뒤 -clear 후 재적용하세요. 생산비·수송·탄약 효과는 적용 후 새로 생성한 유닛으로 비교하세요. 업그레이드는 -up 번호 0으로 되돌리며 지도 전체를 처음 상태로 되돌리려면 임무를 다시 시작합니다. 시험 세트 위치는 미니맵의 (75,75) 타일 근처입니다.</p><input id="q" placeholder="이름·종족·효과 검색"><span id="count"></span><table><thead><tr><th>실전 확인</th><th>번호</th><th>이름</th><th>등급</th><th>기대 효과</th><th>복사</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table><script>const rows=[...document.querySelectorAll('tbody tr')];q.oninput=()=>{let n=0;for(const r of rows){r.hidden=!r.dataset.search.toLowerCase().includes(q.value.toLowerCase());if(!r.hidden)n++}count.textContent=' '+n+' / '+rows.length};for(const c of document.querySelectorAll('[data-key]')){c.checked=localStorage.getItem('effectlab-'+c.dataset.key)==='true';c.onchange=()=>localStorage.setItem('effectlab-'+c.dataset.key,c.checked)}q.oninput();</script></html>'''
    return result

def build(output=None,base=None,terrain_root=None):
    from eudplib.bindings._rust import mpqapi
    from sc1.native_campaign.build_plain_chk import CHK
    output=Path(output or ROOT/'sc1/effect_lab');output.mkdir(parents=True,exist_ok=True)
    base=Path(base or ROOT/'sc1/vendor/eudplib-basemap.scx')
    archive=mpqapi.MPQ.open(str(base));chk=CHK(archive.extract_file('staredit\\scenario.chk'));del archive
    # Flat jungle ground from the MIT template; use verified walkable variants.
    tiles=[32,33,48,49];size=256
    if terrain_root:
        tr=Path(terrain_root);cv5=(tr/'jungle.cv5').read_bytes();vf4=(tr/'jungle.vf4').read_bytes()
        for tile in tiles:
            mega=struct.unpack_from('<H',cv5,(tile>>4)*52+20+(tile&15)*2)[0]
            assert all(v&1 for v in struct.unpack_from('<16H',vf4,mega*32)),tile
    chk.setsection('VER ',struct.pack('<H',205));chk.setsection('DIM ',struct.pack('<HH',size,size))
    chk.setsection('MTXM',struct.pack('<'+'H'*(size*size),*(tiles[(x&1)+2*(y&1)] for y in range(size) for x in range(size))))
    chk.setsection('TILE',chk.getsection('MTXM'));chk.setsection('MASK',bytes(size*size));chk.setsection('ISOM',bytes((size//2+1)*(size+1)*8))
    values=[b'SC1 Effect Lab 256',b'Isolated native effect sandbox. Enter -help. No campaign record.',b'Anywhere',b'Player',b'Targets',MARKER,b'Lab ready: -help / -t index rank / -c index stacks / -case 1..8 / -reset',b'Lab base']
    chk.setsection('STR ',strings(values));chk.setsection('SPRP',struct.pack('<HH',1,2));chk.setsection('WAV ',bytes(2048));chk.setsection('MBRF',b'');chk.setsection('THG2',b'');chk.setsection('DD2 ',b'')
    owners=bytes([6,0,0,0,0,0,5,0,0,0,0,0]);chk.setsection('OWNR',owners);chk.setsection('IOWN',owners);chk.setsection('SIDE',bytes([1,7,7,7,7,7,0,7,7,7,7,4]))
    chk.setsection('FORC',bytes([0,0,0,0,0,0,1,0])+struct.pack('<4H',4,5,0,0)+bytes(4));chk.setsection('COLR',bytes(range(8)))
    locations=bytearray(255*20);struct.pack_into('<4IHH',locations,0,0,0,2048,2048,8,0);struct.pack_into('<4IHH',locations,63*20,0,0,8192,8192,3,0);chk.setsection('MRGN',locations)
    units=[]
    def add(uid,owner,x,y,res=0):units.append(unit(len(units)+1,uid,owner,x,y,res))
    add(214,0,800,800);add(214,6,7200,7200)
    for y in range(6,256,12):
        for x in range(6,256,12):add(101,0,x*32,y*32)
    for i,uid in enumerate(ROSTER):add(uid,0,512+(i%10)*128,512+(i//10)*128)
    for i,uid in enumerate(BUILDINGS):add(uid,0,512+(i%10)*192,1600+(i//10)*192)
    for i in range(12):
        for uid,y in ((109,512),(156,704),(42,896)):add(uid,0,3840+i*128,y)
    for i in range(8):add(176,11,320+i*64,320,50000)
    for x,y in ((320,448),(1000,320),(2000,320)):add(188,11,x,y,50000)
    # Enemy bases and mixed organic/mechanical/shield/air targets in distant courts.
    for i,uid in enumerate((106,131,154,124,144,162)):add(uid,6,6500+i%3*192,6500+i//3*192)
    for i,uid in enumerate((0,3,37,38,39,65,66,43,42,70,12,9)):add(uid,6,3000+(i%6)*96,2400+(i//6)*192)
    for i,uid in enumerate((42,43,44,70,8,12)):add(uid,6,4500+i*96,1500)
    for i in range(8):add(7,6,4400+i*72,4400)
    chk.setsection('UNIT',b''.join(units))
    # Standard UMS defaults, every race trainable and all abilities researched.
    for tag,count in (('UNIx',228),('UNIS',228),('UPGx',61),('UPGS',46),('TECx',44),('TECS',24)):
        chk.setsection(tag,bytes([1])*count+bytes(len(chk.getsection(tag))-count))
    chk.setsection('PUNI',bytes([1])*(228*12+228)+bytes(228*12))
    for tag,count in (('PUPx',61),('UPGR',46)):
        chk.setsection(tag,bytes([3])*(count*12)+bytes(count*12)+bytes([3])*count+bytes(count)+bytes(count*12))
    for tag,count in (('PTEx',44),('PTEC',24)):
        chk.setsection(tag,bytes([1])*(count*12*2+count*2)+bytes(count*12))
    def action(kind,player=0,amount=0,unitid=0,modifier=0,string=0,location=0):
        return struct.pack('<IIIIIIHBBBBH',location,string,0,0,player,amount,unitid,kind,modifier,4,0,0)
    trig=bytearray(2400);trig[15]=22
    actions=[action(26,amount=50000,unitid=2,modifier=7),action(9,string=7),action(12,string=7),action(10,location=1)]
    for i,a in enumerate(actions):trig[320+i*32:352+i*32]=a
    trig[2372]=1;chk.setsection('TRIG',trig)
    raw=chk.save();(output/'scenario.chk').write_bytes(raw)
    dest=output/'SC1_Effect_Lab.scx';dest.write_bytes(base.read_bytes())
    with tempfile.NamedTemporaryFile(dir=output,suffix='.chk',delete=False) as tmp:tmp.write(raw);path=Path(tmp.name)
    try:
        archive=mpqapi.MPQ.open(str(dest));archive.add_file('staredit\\scenario.chk',str(path));archive.compact();del archive
    finally:path.unlink()
    archive=mpqapi.MPQ.open(str(dest));assert archive.extract_file('staredit\\scenario.chk')==raw;del archive
    catalog=json.loads((ROOT/'sc1/campaign/runtime_talents_v5.json').read_text(encoding='utf8'));generate_controls(catalog)
    (output/'Effect_Checklist.html').write_text(checklist(catalog),encoding='utf8')
    proof=dict(passed=True,width=256,height=256,marker=MARKER.decode(),placed_units=len(units),talents=len(catalog['talents']),curses=len(catalog['curses']),stock_triggers=1,eud_payload=False,user_database_accessed=False,game_launched=False,live_gameplay_verified=False,terrain_walkability_verified=bool(terrain_root),map_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),chk_sha256=hashlib.sha256(raw).hexdigest())
    (output/'build_evidence.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf8');return proof

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--base');p.add_argument('--output');p.add_argument('--terrain-root');a=p.parse_args();print(json.dumps(build(a.output,a.base,a.terrain_root)))
