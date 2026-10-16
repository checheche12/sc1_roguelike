"""Build expanded runtime content from preserved design snapshots, never live drafts."""
import copy
import json
from pathlib import Path
from sc1.native_campaign.build_managed_dat import legacy_fields, source_bytes
from sc1.campaign.missions import load_missions
from sc1.campaign.display_text import apply_display_descriptions
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
UNIT_FIELDS = {'maxHp':8,'maxShields':7,'armor':27,'sightRange':24,'seekRange':23,
               'mineralCost':40,'gasCost':41,'timeCost':42,'supplyUsed':46,'spaceProvided':48}
WEAPON_FIELDS = {'maxRange':5,'damageType':7,'damageAmount':14,'cooldown':16,'innerSplash':11,'middleSplash':12,'outerSplash':13}
RARITY_LABELS = dict(zip(('common','uncommon','rare','epic','legendary'),('일반','고급','희귀','영웅','전설')))
REGULAR_COMBAT_UNITS = sorted({0,1,2,3,4,5,6,30,31,8,9,11,12,32,34,
    37,38,39,40,43,44,45,46,47,50,58,60,61,62,63,65,66,67,68,69,70,71,72,73,83,84,103})

def build():
    catalog = json.loads((HERE/'runtime_talents.json').read_text(encoding='utf-8'))
    sources = ['sc1/campaign/design_snapshots/r469_20261014_153314_623339/board.json',
               'sc1/design/zerg_protoss_more_drafts.json','sc1/design/variety_more_drafts.json']
    items = []
    for source in sources:
        body = json.loads((ROOT/source).read_text(encoding='utf-8'))
        items.extend(body['items'] if isinstance(body,dict) else body)
    byname = {x['name']:x for x in items}
    missions = load_missions()
    all_ids = [m['mission_id'] for m in missions]
    units = legacy_fields('units',source_bytes('units'))
    def uval(field, uid):
        flags,body = units[field]; width = 1 << flags
        return int.from_bytes(body[uid*width:(uid+1)*width],'little')
    def weapons(ids):
        result = set()
        for uid in ids:
            for unit in {uid,uval(1,uid)}:
                if unit < 228:
                    result.update(w for f in (17,19) if (w:=uval(f,unit)) < 130)
        return sorted(result)
    def patch(table,ids,field,value,op='add'):
        return {'table':table,'ids':ids,'field':field,'op':op,'value':value}
    def add(name, patches=(), movement=(), production=False, targets=()):
        original = byname[name]
        item = {k:copy.deepcopy(original[k]) for k in ('id','name','race','rarity','target','description')}
        item.update(bit_index=len(catalog['talents']), implemented=True,
                    source_description=original['description'], source_files=sources,
                    missions=[m['mission_id'] for m in missions if item['race'] in ('shared',m['race'])],
                    effect={'type':'stat_patches','patches':list(patches)},
                    requirements={'production':production}, target_units=list(targets),
                    implementation_note='오프라인 구현. 실제 전 임무 완주·화면·밸런스 검증 전.')
        if movement:
            item['effect']['movement'] = list(movement)
        catalog['talents'].append(item)
    def stat(name, ids, field, amount, op='add', production=False):
        add(name,[patch('units',ids,field,amount,op)],production=production,targets=ids)
    def weapon(name,ids,field,amount,op='add'):
        add(name,[patch('weapons',weapons(ids),field,amount,op)],targets=ids)
    def move(name,ids,n,d=100):
        add(name,movement=[{'unit_id':u,'numerator':n,'denominator':d} for u in ids],targets=ids)
    def range_(name,ids,tiles=1):
        add(name,[patch('weapons',weapons(ids),'maxRange',tiles*32),patch('units',ids,'seekRange',tiles)],targets=ids)
    for item in catalog['talents']+catalog['curses']:
        item['legacy_effect'] = copy.deepcopy(item['effect'])
        item['missions'] = [m['mission_id'] for m in missions if item['race'] in ('shared',m['race'])]
        item['description'] = item['source_description']
        item['implementation_note'] = '본편·확장 캠페인 오프라인 구현, 실전 검증 전.'
        item['requirements'] = {'production': item.get('bit_index') == 15}
        item['target_units'] = sorted({u for p in item['effect'].get('patches',[]) if p['table']=='units' for u in p['ids']})
    legacy_targets=[[0],[0],[0],[32],[1],[1],[2],[2],[5,6],[30,31],[3],[8],[8],[58],[12],[7,41,64],[7,41,64]]
    # Retain the immutable T01 effect under legacy_effect for stored campaigns,
    # while the expanded contract describes the native all-campaign targets.
    attack_units=[uid for uid in range(228) if any(uval(f,uid)<130 for f in (17,19))]
    catalog['curses'][1]['effect'].update(units=attack_units,weapons=weapons(range(228)),
        owner_scope='hostile_only',exclude_hallucinations=True)
    catalog['curses'][1]['target_units']=attack_units
    catalog['curses'][2]['effect'].update(units=REGULAR_COMBAT_UNITS,
        owner_scope='hostile_only',exclude_hallucinations=True)
    catalog['curses'][2]['target_units']=REGULAR_COMBAT_UNITS.copy()
    for item,targets in zip(catalog["talents"],legacy_targets): item["target_units"]=targets
    for idx in (15,16):
        catalog['talents'][idx]['effect']['patches'][0]['ids']=[7,41,64]
        catalog['talents'][idx]['target_units']=[7,41,64]
    # Terran: all effects retain the user's rarity and exact promised mechanic.
    move('고관절 개선',[3],120); move('레이스 출격 준비 완료',[8],120)
    move('신속 이동',[11],200); move('엔진 개선',[12],150)
    stat('두꺼운 방열 장갑',[32],'armor',1)
    weapon('고압 화염 노즐',[32],'damageAmount',2)
    stat('의무관 방호복',[34],'maxHp',20*256)
    move('구급반의 빠른 발',[34],115)
    # Ground-only Goliath damage: its turret ground weapon is 7.
    add('기관포 구경 확대',[patch('weapons',[7],'damageAmount',3)],targets=[3,4])
    stat('보행 병기의 추가 장갑',[3],'armor',1)
    stat('튼튼한 수송 동체',[11],'maxHp',40*256)
    stat('미사일함 생존 설계',[58],'maxHp',40*256)
    stat('과학선 보호 격벽',[9],'maxHp',40*256)
    range_('멀리 뻗는 미사일 레일',[58])
    stat('접이식 수송 좌석',[11],'spaceProvided',4)
    add('밀집 편대용 폭발탄',[patch('weapons',[103],field,[6,5],'ratio') for field in ('innerSplash','middleSplash','outerSplash')],targets=[58])
    stat('과학선 광역 감지기',[9],'sightRange',2)
    # Zerg.
    stat('작지만 단단하다',[37],'maxHp',10*256); weapon('쉴 틈 없는 발톱',[37],'cooldown',[4,5],'ratio')
    range_('한 칸 더 뻗는 가시',[38]); stat('단단한 비늘',[38],'maxHp',20*256)
    range_('깊숙이 뻗는 가시',[103]); stat('더 거대한 몸집',[39],'maxHp',100*256)
    stat('겹겹의 갑각',[39],'armor',2); stat('찢어지지 않는 날개',[43],'maxHp',20*256)
    range_('더 멀리 포격',[44]); stat('두꺼운 비행 갑각',[62],'maxHp',50*256)
    weapon('산성 주머니 증설',[62],'cooldown',[3,4],'ratio'); move('더 빠른 돌진',[47],125)
    weapon('알찬 폭약 주머니',[47],'damageAmount',[5,4],'ratio')
    stat('안심되는 보급선',[42],'maxHp',50*256); move('폭탄은 빨라야 한다',[50],130)
    weapon('작은 발톱도 날카롭게',[37],'damageAmount',1); stat('배까지 감싼 갑각',[37],'armor',1)
    weapon('굵게 자란 가시',[38],'damageAmount',2); move('미끄러지는 복부',[38],115)
    stat('땅속에서도 튼튼하게',[103],'maxHp',30*256); weapon('더 굵은 지하 가시',[103],'damageAmount',4)
    move('거구의 긴 보폭',[39],115); stat('거수의 빠른 부화',[39],'timeCost',[4,5],'ratio',True)
    stat('유연한 날개 갑피',[43],'armor',1); weapon('단단해진 쐐기벌레',[43],'damageAmount',2)
    stat('포격용 두꺼운 몸통',[44],'maxHp',30*256); move('포대도 움직여야 한다',[44],125)
    stat('산성에도 버티는 외피',[62],'armor',1); stat('끝까지 날아가는 몸',[47],'maxHp',10*256)
    stat('여왕의 생존 갑피',[45],'maxHp',30*256); stat('쉽게 꺾이지 않는 독낭',[46],'maxHp',25*256)
    stat('보급낭 빠른 부화',[42],'timeCost',[3,4],'ratio',True); stat('폭발물 운반용 조직',[50],'maxHp',30*256)
    weapon('산성 포낭 재장전',[44],'cooldown',[4,5],'ratio')
    add('빈틈없이 터지는 폭약',[patch('weapons',weapons([50]),field,[115,100],'ratio') for field in ('innerSplash','middleSplash','outerSplash')],targets=[50])
    # Protoss.
    stat('한 겹 더 두른 보호막',[65],'maxShields',20); weapon('양손을 더 빠르게',[65],'cooldown',[4,5],'ratio')
    stat('흔들리지 않는 보행체',[66],'maxHp',20*256); range_('더 멀리 뻗는 위상포',[66])
    move('그림자 걸음',[61],120); stat('더 짙은 사이오닉 껍질',[68],'maxShields',100)
    range_('손끝을 넘는 번개',[68]); move('빠른 왕복 수송',[69],140)
    stat('조금 더 넓은 내부',[69],'spaceProvided',4); stat('오래 버티는 공성체',[83],'maxHp',40*256)
    stat('스캐럽 조립 가속',[85],'timeCost',[7,10],'ratio',True); move('먼저 가서 볼게',[84],130)
    stat('더 멀리 보는 관측',[84],'sightRange',2)
    add('지상전도 준비 완료',[patch('weapons',[uval(17,70)],'damageAmount',8)],targets=[70])
    move('추격용 엔진',[70],125); stat('격납고의 빠른 손',[73],'timeCost',[7,10],'ratio',True)
    stat('버티는 자의 육체',[65],'maxHp',20*256); stat('전열 기사의 갑주',[65],'armor',1)
    stat('보행체 보호장 보강',[66],'maxShields',30); weapon('고밀도 분열탄',[66],'damageAmount',3)
    stat('명상을 지키는 체력',[67],'maxHp',20*256); move('뒤처지지 않는 현자',[67],120)
    stat('그림자 속의 생명력',[61],'maxHp',20*256); stat('어둠을 두른 보호장',[61],'maxShields',30)
    stat('혼돈을 담는 외벽',[63],'maxShields',50); stat('충격을 버티는 수송선',[69],'maxHp',40*256)
    stat('두꺼운 공성 장갑',[83],'armor',1); stat('들켜도 한 번은 버틴다',[84],'maxShields',20)
    stat('정찰 편대의 방호장',[70],'maxShields',40); stat('분열함의 외장 보강',[60],'armor',1)
    stat('튼튼한 모함 골격',[72],'maxHp',60*256); stat('중재함 생존 설계',[71],'maxHp',40*256)
    range_('긴 사거리 요격 장비',[70]); range_('멀리 퍼지는 분열장',[60])
    add('돌아올 수 있는 요격기',[patch('units',[73],'maxHp',20*256),patch('units',[73],'maxShields',20)],targets=[73])
    # User-authored frozen entries restored as append-only runtime talents.
    for name,unit,mode,maximum in (('동시공격',3,'independent_layers',2),
                                   ('다중 무기 작업',12,'shared_cycle',3)):
        add(name,targets=[unit])
        catalog['talents'][-1]['effect'] = {
            'type':'multi_target','unit_id':unit,'mode':mode,'max_targets':maximum,
            'full_weapon_damage':True,'recursive_secondary_attacks':False}
    # Reaver attack period is hardcoded, so the draft is intentionally excluded.
    contracts=json.loads((HERE/'expanded_curse_contract.json').read_text(encoding='utf-8'))['curses']
    diversity=json.loads((HERE/'curse_diversity_contract.json').read_text(encoding='utf-8'))
    contracts += diversity['curses']
    curse_specs=[(entry['name'],entry['effect'],entry.get('max_stacks',255)) for entry in contracts]
    for name,effect,max_stacks in curse_specs:
        original=byname[name]
        item={k:copy.deepcopy(original[k]) for k in ('id','name','race','rarity','target','description')}
        item.update(byte_index=len(catalog['curses']),source_description=original['description'], source_numbers=original.get('numbers',''),
                    effect=effect,missions=all_ids,implemented=True,max_stacks=max_stacks,
                    implementation_note='범용 네이티브 효과 구현. 실제 캠페인 밸런스 검증 전.')
        catalog['curses'].append(item)
    catalog.update(campaign_expansion=True,source_files=sources,talent_pool_revision=2,curse_pool_revision=diversity['catalog_pool_revision'],
        implementation_scope='Original + Brood War native campaign runtime; offline verification required. User workshop and legacy catalog untouched.',
        notes=['All rarity, names and original effect text come from preserved designs.',
               'One-time talents remain unique per campaign; variants share mission reward identity.',
               'Owner-scoped DAT stat patches and movement patches; native gameplay unverified.'])
    apply_display_descriptions(catalog)
    from sc1.campaign import talent_ranks
    catalog = talent_ranks.merge(catalog, talent_ranks.additions())
    (HERE/'runtime_talents_all.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return catalog

if __name__=='__main__':
    result=build()
    print(json.dumps({'talents':len(result['talents']),'curses':len(result['curses']),
      'by_race':{r:sum(i['race'] in (r,'shared') for i in result['talents']) for r in ('terran','zerg','protoss')}},ensure_ascii=False))
