"""Current effect copy, independent of mechanics and frozen source records."""
REVISION=2026102042
QA61_DESCRIPTION_REVISION=2026102262
QA61_DESCRIPTIONS={
 54:'벌처의 공격 유형이 일반형으로 바뀝니다. 이동 중에도 사격하며, 공격 피해는 정지 시 2배·이동 중 3배입니다.',
 141:'리버의 스캐럽은 공격 피해가 150% 증가하며(원래의 2.5배), 생산 미네랄 비용이 0이 됩니다. 갑충탄 생산 속도 +50%(1.5배). 리버 이동 속도 +100%(기본의 2배).',
 322:'미사일 터렛·스포어 콜로니·포톤 캐논: 획득마다 최대 체력 +100%, 대공 피해 +50%, 대공 표적 +1기. 포톤 캐논 보호막도 +100%. 최대 2회.',
}

# Remove only reviewed editorial clauses; actual triggers and limits remain.
OMIT=(
 '주 대상만 타격하며 주변 추가 피해·튕김은 없습니다.',
 '추가 타격은 주변에 퍼지지 않습니다.',
 '추가 공격은 다시 발동시키지 않습니다.',
 '추가 공격은 다시 연쇄되지 않습니다.',
 '추가 화염은 다시 발동시키지 않습니다.',
 '체력 증가와 방어력 무시 효과는 없습니다.',
 '지상 공격은 없습니다.',
 '공격해야 방출됩니다.',
 '반사는 재반사되지 않습니다.',
 '탐지 능력은 생기지 않습니다.',
 '초당 피해는 그대로입니다.',
 '튕김 피해 감쇠는 유지됩니다.',
 '같은 히드라의 독은 겹치지 않습니다.',
 '최대 에너지를 넘지 않습니다.',
 '격납고 수용량은 기본 연구를 따릅니다.',
 '아군 피해도 유지됩니다.',
 '원래 아군 피해도 유지됩니다.',
 '같은 시전의 중복 감염은 없습니다.',
 '겹친 군체 회복은 중복되지 않으며 마법·광역 예외는 유지됩니다.',
 '자동 야마토는 추가탄을 만들지 않습니다.',
 '방어막 흡수·초과 피해는 제외.',
 '한 공격은 한 공격층만 맞힙니다.',
 '기본 범위 공격은 유지합니다.',
 '대상이 죽거나 소유자가 바뀌면 초기화.',
 '기본 감속에 85%를 더 곱하지 않고 최종 속도를 15%로 맞춥니다.',
 '범위·지속 시간 강화와 함께 적용됩니다.',
 '소수점 공격력은 중첩 합계를 반올림합니다.',
 '기존 병과 체력 교범과 합산해 최대 4중첩입니다.',
 '기존 병과 교범과 합산해 최대 4중첩.',
 '모체·탄약 유닛 교범은 높은 쪽만 적용합니다.',
 '마법 시전 속도는 바뀌지 않습니다.',
 '중첩·물량 저주와 동시 병력 상한 적용.',
 '지상·공중 무기는 각각 원래 피해와 공격 횟수를 사용합니다.',
 '1회 획득.',
 '캐리어의 요격기에 적용.',
)
REPLACE=(
 ('(현재 에너지 즉시 지급 없음)',''),
 ('(직격 대상 제외·중복 없음)',''),
 ('이며 생산 시간은 그대로입니다.','입니다.'),
 ('전염마다 온전한 지속시간을 받으며 같은 시전의 중복 감염은 없습니다.','전염 시 지속 시간이 갱신됩니다.'),
 ('원래 아군 피해를 유지하며 같은 방사선의 피해는 중복되지 않습니다.',''),
 ('범위를 떠나도 2초간 유지되며 여러 드롭십과 중첩되지 않습니다.','효과는 범위를 벗어난 뒤 2초간 지속됩니다.'),
 ('범위를 떠나도 2초간 유지되며 여러 셔틀과 중첩되지 않습니다.','효과는 범위를 벗어난 뒤 2초간 지속됩니다.'),
 ('공성 모드 이동 유지. 이동 중 공격 불가.','공성 모드로 이동하며 정지 시 사격합니다.'),
 ('이동 사격 유지.','이동 중에도 사격합니다.'),
 ('대상 인구수 제한 없이 주 대상을 포함해','주 대상을 포함해'),
 ('중첩 상한 없음.','무제한 중첩.'),
)

def clean_description(text):
 """Also clean saved offer display without changing its persisted JSON."""
 import re
 text=str(text or '')
 for old,new in REPLACE:text=text.replace(old,new)
 for clause in sorted(OMIT,key=len,reverse=True):text=text.replace(clause,'')
 return '\n'.join(re.sub(r' {2,}',' ',line).strip() for line in text.splitlines()).strip()

def effect_subject(item):
 """Name the acting unit, its ammunition, or the affected group."""
 import re
 if item.get('rework_revision')==5:
  ordinal=item.get('effect_ordinal')
  if ordinal==148:return '캐리어의 인터셉터'
  if ordinal==141:return '리버의 스캐럽'
 from .legendary_expansion import UNIT_FAMILIES
 units=set(item.get('target_units',()))
 if units:
  for families in UNIT_FAMILIES.values():
   for name,ids in families:
    if units<=set(ids):return name
 target=str(item.get('target') or '').strip()
 if target=='전역':return '아군 전체'
 return re.sub(r'\s*[·/,]\s*','·',target) or ('적 추가 공세' if 'byte_index' in item else '아군')

def with_subject(item,text=None):
 """Prefix only the missing subject; numbers and trigger text stay exact."""
 text=clean_description(item.get('description') if text is None else text)
 if not text or item.get('effect',{}).get('retired') or item.get('effect',{}).get('offer_retired'):return text
 subject=effect_subject(item)
 aliases={'뮤탈리스크':'뮤탈','히드라리스크':'히드라','울트라리스크':'울트라','시즈 탱크':'시즈탱크'}
 alias=aliases.get(subject)
 if alias and text.startswith(alias) and not text.startswith(subject):text=subject+text[len(alias):]
 if text.startswith(subject) or text.startswith(('아군 '+subject,'적 '+subject)):return text
 if subject.startswith('아군') and text.startswith('아군'):return text
 if subject.startswith('적 추가 공세') and text.startswith('추가 공세'):return '적 '+text
 if text.startswith('일반 공격'):return subject+'의 '+text
 if text.startswith('같은 '):
  end=ord(subject[-1]);particle='이' if 0xac00<=end<=0xd7a3 and (end-0xac00)%28 else '가'
  return subject+particle+' '+text
 return subject+': '+text

def describe_effect(item):
 """Saved bundles keep their stored text while each member gains its actor."""
 identities=item.get('bundled_talent_ids')
 if isinstance(identities,list) and len(identities) in (2,3):
  from .runtime_catalog import load_catalog
  by_id={x['id']:x for x in load_catalog(expected_version=2)['talents']}
  lines=str(item.get('description') or '').splitlines()
  if len(lines)==len(identities) and all(identity in by_id for identity in identities):
   result=[]
   for identity,line in zip(identities,lines):
    title,sep,body=line.partition(':')
    result.append((title+': ' if sep else '')+with_subject(by_id[identity],body if sep else line))
   return '\n'.join(result)
 return with_subject(item)

def decorate(catalog):
 for kind in ('talents','curses'):
  for item in catalog[kind]:
   if item.get('rework_revision')!=5:continue
   before=item['description'];after=clean_description(before)
   if kind=='talents':
    ordinal=item['effect_ordinal']
    if ordinal==48:after='테란 기계의 단일 원거리 일반 공격이 주변 적 최대 3기에 50% 피해를 줍니다.'
    elif ordinal==58:
     after='발키리가 이동 중에도 공중·지상 적에게 8발의 광역 미사일을 연속 발사합니다. 공중 피해 100%, 지상 피해 150%(공중의 1.5배).'
     item['effect'].pop('immediate_movement_after_first_shot',None)
     item['effect'].update(qa_revision=2026102489,moving_fire=True,ground_damage_percent=150,air_damage_percent=100,missiles_per_volley=8,uninterrupted_volley=True)
    elif ordinal==82:
     after='퀸의 인스네어가 적의 공격 속도·이동 속도를 각각 85% 감소시킵니다.'
     item['target']='퀸 인스네어'
    elif ordinal==91:after='러커가 잠복 상태로 기본 속도의 62.5%로 이동합니다. 정지 시 공격합니다.'
    elif ordinal==97:after='러커가 공중 적에게도 원래 공격의 100% 피해로 가시를 쏩니다.'
    elif ordinal==96:after=after.replace('과잉 자폭을 피하도록 주변 표적을 분배합니다.','공중 표적을 자동으로 분산 추격합니다.')
    elif ordinal==149:after=after.replace('기존 보호막','보호막')
    elif ordinal==223:
     after='발키리 미사일 한 발의 공격력이 중첩당 +1, 공격 간격이 중첩당 4.5% 감소합니다. 최대 4회.'
     item['effect'].update(qa_revision=2026102489,damage_per_missile_per_rank=1,attack_interval_reduction_percent_per_rank=4.5)
     item['effect']['unit_growth']['description']=after
   if not item.get('effect',{}).get('retired'):
    after=with_subject(item,after);item['effect_subject']=effect_subject(item)
    item['description_revision']=REVISION
   if after!=before:
    item['description']=after;item['description_revision']=REVISION
 for item in catalog['talents']:
  if item.get('rework_revision')==5 and item.get('effect_ordinal') in QA61_DESCRIPTIONS:
   item['description']=QA61_DESCRIPTIONS[item['effect_ordinal']]
   item['description_revision']=QA61_DESCRIPTION_REVISION
 catalog['effect_description_revision']=QA61_DESCRIPTION_REVISION
 return catalog
