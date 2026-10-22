"""QA38 append-only unit legends and explicit rarity migrations.

The editable board, accepted input, historical indices and issued offers are
not rewritten. New identities and ordinals below are permanent wire contracts.
"""
from __future__ import annotations
import copy
import json
import uuid

REVISION = 2026102038
PROMOTIONS = (16,49,51,54,55,56,57,58,60,90,92,95,96,97,136,137,138,139,140,141,142)
# Replacement epics use a restrained primary bonus and one secondary hit;
# their promoted originals keep their previous effective numerical strength.
REPLACEMENTS = (
 (16,'단계식 전투 훈련',0,0,0),
 (49,'분산 저격탄',35,50,1),(51,'전술 탄두',35,50,1),
 (54,'기동 파쇄탄',35,50,1),(55,'공성 충격탄',35,50,1),
 (56,'연동 표적 조준',35,50,1),(57,'보조 함포',35,50,1),
 (58,'집속 미사일',35,50,1),(60,'지뢰 파편',35,50,1),
 (90,'보조 독가시',35,50,1),(92,'넓은 칼날',35,50,1),
 (95,'감염 파편',35,50,1),(96,'갈귀 파편',35,50,1),
 (97,'갈라지는 가시',35,50,1),(136,'요격기 보조 화력',20,25,1),
 (137,'보조 위상탄',35,50,1),(138,'그림자 검격',35,50,1),
 (139,'분기 사이오닉',35,50,1),(140,'유동 사이오닉',35,50,1),
 (141,'갑충 파편탄',35,50,1),(142,'정찰기 보조 화기',35,50,1),
)
# ordinal, race, name, target, unit IDs, native mode, primary bonus,
# secondary damage percent, targets, cadence, radius pixels, description.
LEGENDS = (
 ('terran','전장 정비 중추','SCV',[7],2,0,0,0,24,96,
  'SCV 주변 3타일의 아군 테란 기계 유닛과 건물이 초당 체력 12를 회복합니다. 여러 SCV의 정비는 중첩되지 않습니다.'),
 ('terran','가우스 포화','마린·짐 레이너(마린)',[0,20],1,0,100,3,3,96,
  '마린의 세 번째 일반 공격마다 주 대상에게 200% 추가 피해, 주변 3타일의 다른 적 최대 3기에 100% 피해를 줍니다. 추가 공격은 다시 발동시키지 않습니다.'),
 ('terran','지옥불 분사','파이어뱃·구이 몬태그',[10,32],1,100,100,3,1,64,
  '파이어뱃의 일반 공격 피해가 100% 증가하고, 명중 지점 2타일 안 다른 지상 적 최대 3기에 원래 공격의 100% 피해를 줍니다.'),
 ('terran','망령 편대','레이스·톰 카잔스키',[8,21],1,100,200,3,1,128,
  '레이스의 일반 공격 피해 +100%. 명중 지점 4타일 안 같은 공격층의 다른 적 최대 3기에도 기본 공격의 200% 피해를 줍니다.'),
 ('terran','강습 전투 관제','드롭십',[11],3,30,0,0,24,128,
  '드롭십 주변 4타일의 아군 테란 병력은 일반 공격 피해가 30% 증가합니다. 범위를 떠나도 2초간 유지되며 여러 드롭십과 중첩되지 않습니다.'),
 ('zerg','군체 재생핵','드론',[41],4,0,0,0,24,96,
  '드론 주변 3타일의 아군 저그 병력은 초당 최대 체력의 2%를 회복합니다. 같은 효과는 중첩되지 않으며 대군주 회복과는 높은 쪽만 적용됩니다.'),
 ('zerg','군체의 심장','오버로드·이그드라실',[42,57],4,0,0,0,24,128,
  '오버로드 주변 4타일의 아군 저그 병력은 초당 최대 체력의 3%를 회복합니다. 드론과 다른 오버로드의 회복은 중첩되지 않습니다.'),
 ('zerg','광란의 발톱','저글링·포식자',[37,54],1,0,100,3,3,48,
  '저글링의 세 번째 일반 공격마다 주 대상에게 200% 추가 피해, 주변 1.5타일의 다른 지상 적 최대 3기에 100% 피해를 줍니다.'),
 ('zerg','군락 포격','가디언·쿠쿨자(가디언)',[44,56],1,0,100,6,1,96,
  '가디언의 일반 공격이 명중하면 3타일 안 다른 지상 적 최대 6기에도 원래 공격의 100% 피해를 줍니다.'),
 ('zerg','최후의 군체','브루드링',[40],5,0,0,6,1,64,
  '브루드링이 전투 또는 수명 만료로 죽으면 2타일 안 지상 적 최대 6기에 피해 60을 줍니다. 한 브루드링당 한 번만 발동합니다.'),
 ('protoss','수정망의 심장','프로브',[64],6,0,0,0,24,96,
  '프로브 주변 3타일의 아군 프로토스 병력은 초당 보호막 12를 회복합니다. 여러 프로브의 효과는 중첩되지 않습니다.'),
 ('protoss','태양의 쌍검','질럿·피닉스(질럿)',[65,77],1,50,75,2,1,48,
  '질럿의 일반 공격 피해가 50% 증가하고 명중 지점 1.5타일 안 다른 지상 적 최대 2기에 원래 공격의 75% 피해를 줍니다.'),
 ('protoss','차원 보호장','셔틀',[69],7,25,0,0,24,128,
  '셔틀 주변 4타일의 아군 프로토스 병력은 받는 일반 공격 피해가 25% 감소합니다. 범위를 떠나도 2초간 유지되며 여러 셔틀과 중첩되지 않습니다.'),
 ('protoss','관측 조준망','옵저버',[84],8,25,0,0,24,160,
  '옵저버가 5타일 안에서 탐지한 적은 아군의 일반 공격 피해를 25% 더 받습니다. 마지막 관측 후 2초간 유지되며 여러 옵저버와 중첩되지 않습니다.'),
 ('protoss','분열 연쇄','커세어·라자갈',[60,98],1,0,100,2,1,96,
  '커세어의 일반 공격이 명중하면 3타일 안 다른 공중 적 최대 2기에도 원래 공격의 100% 피해를 줍니다. 추가 공격은 다시 연쇄되지 않습니다.'),
)
RADIATION_ORDINAL = 162 + len(REPLACEMENTS) + len(LEGENDS)
UNIT_FAMILIES = {
 'terran': [('SCV',[7]),('마린',[0,20]),('파이어뱃',[10,32]),('고스트',[1,16,99,100,104]),('메딕',[34]),('벌처',[2,19]),('스파이더 마인',[13]),('골리앗',[3,4,17,18]),('시즈 탱크',[5,6,23,24,25,26,30,31]),('레이스',[8,21]),('드롭십',[11]),('과학선',[9,22]),('배틀크루저',[12,27,28,29,102]),('발키리',[58])],
 'zerg': [('드론',[41]),('오버로드',[42,57]),('저글링',[37,54]),('히드라리스크',[38,53]),('러커',[103]),('울트라리스크',[39,48]),('디파일러',[46,52]),('퀸',[45,49]),('뮤탈리스크',[43,55]),('가디언',[44,56]),('디바우러',[62]),('스커지',[47]),('감염된 테란',[50]),('브루드링',[40])],
 'protoss': [('프로브',[64]),('질럿',[65,77]),('드라군',[66,78]),('하이 템플러',[67,79]),('다크 템플러',[61,74,75]),('아콘',[68,76]),('다크 아콘',[63]),('셔틀',[69]),('리버',[81,83]),('스캐럽',[85]),('스카우트',[70,80,88]),('캐리어',[72,82]),('인터셉터',[73]),('커세어',[60,98]),('아비터',[71,86]),('옵저버',[84])],
}

def identity(ordinal):
 return str(uuid.uuid5(uuid.NAMESPACE_URL,'sc1-roguelike/qa38/talent/'+str(ordinal)))

def entries(catalog):
 by_ord={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
 result=[]
 for parent,name,bonus,percent,count in REPLACEMENTS:
  old=by_ord[parent];ordinal=162+len(result)
  description=('같은 적을 계속 공격하면 공격 간격이 최대 30% 짧아집니다. 표적 변경·3초 중단 시 초기화.' if parent==16 else
    f'일반 공격 피해 +{bonus}%. 일반 공격이 명중하면 2타일 안 같은 공격층의 다른 적 1기에 원래 공격의 {percent}% 피해를 줍니다. 추가 공격은 다시 발동시키지 않습니다.')
  result.append(dict(ordinal=ordinal,race=old['race'],name=name,target=old['target'],units=copy.deepcopy(old['target_units']),
   rarity='epic',mode=9 if parent==16 else 1,bonus=bonus,percent=percent,count=count,cadence=1,radius=64,
   description=description,replaces_epic_id=old['id']))
 for race,name,target,units,mode,bonus,percent,count,cadence,radius,description in LEGENDS:
  result.append(dict(ordinal=162+len(result),race=race,name=name,target=target,units=units,rarity='legendary',mode=mode,
   bonus=bonus,percent=percent,count=count,cadence=cadence,radius=radius,description=description))
 result.append(dict(ordinal=RADIATION_ORDINAL,race='terran',name='분자 붕괴 방사선',target='과학선 이레디에이트',units=[9,22],
  rarity='epic',mode=10,bonus=0,percent=0,count=0,cadence=8,radius=32,
  description='아군 과학선의 이레디에이트가 기계 유닛에도 원래 방사선 피해를 줍니다. 방사선 연쇄와 함께 선택하면 확장 피해 반경도 적용됩니다. 원래 아군 피해를 유지하며 같은 방사선의 피해는 중복되지 않습니다.'))
 return result

def decorate(catalog):
 from .missions import load_missions
 by_ord={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
 for ordinal in PROMOTIONS:
  item=by_ord[ordinal];item['rarity']='legendary';item['previous_rarity']='epic'
  item['effect'].update(qa_revision=REVISION,rarity_promoted=True)
 item=by_ord[145];item['rarity']='epic';item['previous_rarity']='legendary'
 item['description']='아비터가 리콜한 뒤 48초간 소환문을 남깁니다. 2초마다 출발지 4타일 안 아군을 같은 도착지로 소환합니다. 첫 리콜과 소환문으로 이동한 아군은 30초간 일반 공격 피해 +20%. 재통과하면 지속시간만 갱신됩니다.'
 item['effect'].update(qa_revision=REVISION,recall_attack_bonus_percent=20,recall_buff_frames=720,recall_buff_stacks=False)
 by_ord[107]['effect'].update(qa_revision=REVISION,retired=True)
 by_ord[107]['description']='삭제된 재능입니다. 더 이상 선택하거나 효과를 받을 수 없습니다.'
 changes={
  61:('이레디에이트 피해 3배, 피해 반경 4타일. 감염된 적이 죽으면 6타일 안 생체 적 최대 5기에 전염되며 최초 시전부터 최대 5단계까지 이어집니다. 전염마다 온전한 지속시간을 받으며 같은 시전의 중복 감염은 없습니다. 원래 아군 피해도 유지됩니다.',dict(infection_radius_pixels=192)),
  63:('락다운은 생체 전투 유닛에도 적용되며 생체 대상 지속 시간이 최대 4배가 됩니다. 주 대상 주변 6타일 안 다른 적 최대 6기 추가 봉쇄. 아직 봉쇄되지 않고 락다운 탄도 향하지 않는 적 우선.',dict(chain_radius_pixels=192,chain_total_targets=7,prefer_unlocked_unclaimed_targets=True)),
  64:('야마토 준비 동작 약 3배 가속. 3발 각각 200% 피해, 에너지 50. 추가탄은 4타일 안 다른 적 우선, 부족하면 주 대상 집중. 탄착지 3타일 안 다른 적 최대 6기에 기본 야마토의 50% 폭발 피해(직격 대상 제외·중복 없음).',dict(energy_cost=50)),
  102:('플레이그가 적을 죽일 수 있으며 체력 피해가 4배, 반경은 기본의 2배가 됩니다. 아군 피해도 유지됩니다.',dict(radius_multiplier=2)),
  103:('다크 스웜이 반경 5타일의 지상 유닛과 아군 공중 유닛을 보호합니다. 안의 아군 전투 병력은 초당 최대 체력 3% 회복. 겹친 군체 회복은 중복되지 않으며 마법·광역 예외는 유지됩니다.',dict(swarm_max_hp_regen_percent_per_second=3,swarm_radius_tiles=5)),
  104:('스폰 브루들링이 대상당 6기를 만듭니다. 주 대상 4타일 안의 시전 가능한 적 최대 3기도 추가 공격해 총 4기에서 최대 24기를 만듭니다. 브루들링 최대 체력·공격력 2배. 스폰 브루들링 에너지 소모 100.',dict(broodlings_per_target=6,additional_cast_targets=3,additional_cast_radius_pixels=128,broodling_energy_cost=100,additional_cast_targeting='native_weapon_flags')),
  146:('다크 아콘이 마인드 컨트롤한 적의 4타일 안 다른 적 최대 4기도 지배합니다. 대상 인구수 제한 없이 주 대상을 포함해 최대 5기를 지배합니다.',dict(chain_total_targets=5,additional_target_supply_limit=False)),
 }
 for ordinal,(description,effect) in changes.items():
  by_ord[ordinal]['description']=description;by_ord[ordinal]['effect'].update(effect,qa_revision=REVISION)
 by_ord[103]['effect']['qa_revision']=2026102267
 # Target coverage includes native parent bodies, turrets and carried ammo.
 by_ord[55]['target_units']=[5,6,23,24,25,26,30,31]
 by_ord[57]['target_units']=[12,27,28,29,102]
 by_ord[148]['target_units']=[72,73,82];by_ord[148]['target']='캐리어·인터셉터'
 rows=load_missions()
 for spec in entries(catalog):
  ordinal=spec['ordinal'];effect={k:copy.deepcopy(spec[k]) for k in ('mode','bonus','percent','count','cadence','radius')}
  effect.update(type='rework_v5',ordinal=ordinal,source_id=identity(ordinal),qa_revision=REVISION,benefit_power_quarters=4)
  if 'replaces_epic_id' in spec:effect['replaces_epic_id']=spec['replaces_epic_id']
  item=dict(id=identity(ordinal),name=spec['name'],race=spec['race'],rarity=spec['rarity'],target=spec['target'],
   description=spec['description'],source_description=spec['description'],bit_index=238+ordinal,
   category='combat',kind='talent',implemented=True,native_status='implemented',rework_revision=5,effect_ordinal=ordinal,
   repeatable=False,effect=effect,target_units=spec['units'],requirements={'production':False},
   missions=[x['mission_id'] for x in rows if spec['race'] in ('shared',x['race'])],expansion_revision=REVISION)
  item.update(balance_revision=9,pre_balance_description=item['description'],pre_balance_effect=copy.deepcopy(effect))
  if item['bit_index']<len(catalog['talents']):
   assert catalog['talents'][item['bit_index']]['id']==item['id']
   catalog['talents'][item['bit_index']]=item
  else:
   assert len(catalog['talents'])==item['bit_index']
   catalog['talents'].append(item)
 assert len(catalog['talents'])<=1024
 catalog['legendary_expansion_revision']=REVISION
 catalog['legendary_common_offer_probability']={'numerator':1,'denominator':3,'scope':'guaranteed_four_choices','maximum_common_slots':1}
 return catalog

def generate_header(catalog,root):
 from pathlib import Path
 lines=['#pragma once','namespace unit_legend_expansion {',
  'struct Rule {unsigned ordinal,mode,bonus,percent,count,cadence,radius;unsigned units[8];};',
  'inline constexpr Rule rules[]={']
 for spec in entries(catalog):
  if spec['ordinal']==191:spec['bonus']=catalog['talents'][238+191]['effect']['bonus']
  mask=[0]*8
  for unit in spec['units']:mask[unit//32]|=1<<(unit%32)
  lines.append('{'+','.join(str(spec[k])+'u' for k in ('ordinal','mode','bonus','percent','count','cadence','radius'))+',{' + ','.join(str(x)+'u' for x in mask)+'}},')
 lines+=['};',f'inline constexpr unsigned kRadiationOrdinal={RADIATION_ORDINAL};','}']
 target=Path(root)/'sc1/native_campaign/plugin/include/unit_legend_expansion.generated.h'
 target.write_text('\n'.join(lines)+'\n',encoding='utf8')
 return target
