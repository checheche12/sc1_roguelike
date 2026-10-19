"""Append-only per-unit manuals, traits and compact v2 storage contracts.

Existing 437 ownership bits, 21 manual words and four wide curse counters
retain their meaning. New fields occupy spare rank words21..27 and bits437+.
Each field stays inside one word. No map or mailbox size changes are needed.
"""
import copy
import uuid
from functools import lru_cache
from .legendary_expansion import UNIT_FAMILIES, REVISION

BASE=437
NO_ATTACK={34,11,9,42,46,45,67,63,69,84}
CASTERS={1,34,9,46,45,67,63,60,71}
OLD_MANUALS=(8,9,26,27,28,29,30,31,67,68,69,70,71,72,108,109,110,111,112)

@lru_cache(maxsize=None)
def identity(ordinal):
 return str(uuid.uuid5(uuid.NAMESPACE_URL,'sc1-roguelike/qa38/unit-growth/'+str(ordinal)))

@lru_cache(maxsize=1)
def specifications():
 rows=[];families=[]
 for race,units in UNIT_FAMILIES.items():
  for name,ids in units:families.append((race,name,ids))
 for race,name,ids in families:
  rows.append(dict(race=race,target=name,units=ids,kind='health',rarity='common',name=name+' 생존 교범',
   description=name+'의 최대 체력'+('·최대 보호막' if race=='protoss' else '')+'이 중첩당 28% 증가합니다. 최대 4회. 기존 병과 체력 교범과 합산해 최대 4중첩입니다.'))
  if ids[0] not in NO_ATTACK:
   base=ids[0]
   if race=='terran':parent=29 if base in (0,1,10) else 30 if base in (2,3,5) else 31
   elif race=='zerg':parent=70 if base in (37,39,40,50) else 71 if base in (38,103) else 72
   else:parent=111 if base in (65,66,61,68,81,85) else 112
   damage={7:'+3',13:'+3',41:'+3',64:'+3',0:'+15%',1:'+15%',10:'+15%',2:'+4.5',3:'+3',5:'전차 +6·공성 +12',8:'지상 +6·공중 +12',12:'+6',58:'+3',37:'+1.5',39:'+6',50:'+60',40:'+1.5',43:'+6',44:'+6',38:'+3',103:'+3',62:'+3',47:'+3',65:'+1.5',66:'+3',61:'+6',68:'+6',81:'+15',85:'+15',70:'지상 +6·공중 미사일 각각 +6(2발 합계 +12)',72:'인터셉터 +1',73:'+1',60:'+3',71:'+3'}[base]
   rows.append(dict(race=race,target=name,units=ids,kind='attack',rarity='common',name=name+' 화력 교범',parent=parent,
    description=name+'의 공격력이 중첩당 '+damage+', 공격 간격이 중첩당 4.5% 감소합니다. 최대 4회. 소수점 공격력은 중첩 합계를 반올림합니다. 기존 병과 교범과 합산해 최대 4중첩.'+(' 모체·탄약 유닛 교범은 높은 쪽만 적용합니다.' if base in (72,73,81,85) else '')))
 for i,(race,name,ids) in enumerate(families):
  tier=('uncommon','rare','epic')[i%3];attack=ids[0] not in NO_ATTACK;caster=ids[0] in CASTERS
  armor=1 if tier=='uncommon' else 2 if tier=='epic' else 0
  hp=20 if tier=='rare' else 30 if tier=='epic' and not attack else 0
  damage=20 if tier=='rare' and attack else 35 if tier=='epic' and attack else 0
  speed=10 if tier=='uncommon' else 20 if not attack else 0
  energy=(50 if tier=='rare' else 100 if tier=='epic' else 0) if caster else 0
  parts=[]
  if armor:parts.append('체력 방어력 +'+str(armor))
  if hp:parts.append('최대 체력'+('·보호막' if race=='protoss' else '')+' +'+str(hp)+'%')
  if damage:parts.append('일반 공격 피해 +'+str(damage)+'%')
  if speed:parts.append('이동 속도 +'+str(speed)+'%')
  if energy:parts.append('최대 에너지 +'+str(energy)+'(현재 에너지 즉시 지급 없음)')
  rows.append(dict(race=race,target=name,units=ids,kind='trait',rarity=tier,name=name+' '+{'uncommon':'기동 장갑','rare':'정예 전투체','epic':'전장 완성형'}[tier],
   description=name+' 전용: '+', '.join(parts)+'. 1회 획득.',armor=armor,hp=hp,damage=damage,speed=speed,energy=energy))
 rows.append(dict(race='protoss',target='다크 템플러',units=[61,74,75],kind='shadow',rarity='legendary',name='그림자 격노',
  description='전투 중 자동으로 6타일 안 지상 적을 5회 순간이동하며 벱니다. 회당 일반 공격의200% 피해. 다른 적 우선·부족하면 재타격. 시전 중 무적, 종료 후 원위치 복귀. 재사용12초.'))
 # The order is a durable field contract. No field crosses a word boundary.
 word,shift=54,0  # growth words33+21, through33+27
 for i,spec in enumerate(rows):
  width=1 if spec['kind'] in ('trait','shadow') else 3
  if shift+width>32:word+=1;shift=0
  if word==61:word,shift=14,21 # physical bit437 starts in growth word14
  spec.update(ordinal=BASE-238+i,index=BASE+i,storage=dict(word=word,shift=shift,width=width))
  shift+=width
  assert 54<=word<=60 or 14<=word<=16
 assert len(rows)==123 and rows[-1]['storage']['word']<=16
 return rows

def decorate(catalog):
 from .missions import load_missions
 by_ord={x.get('effect_ordinal'):x for x in catalog['talents'] if x.get('rework_revision')==5}
 for ordinal in OLD_MANUALS:
  # Keep old ownership mechanics and frozen offers. Future rolls use unit cards.
  by_ord[ordinal]['effect'].update(qa_revision=REVISION,offer_retired=True)
 for race,name,units in [(r,n,u) for r,fs in UNIT_FAMILIES.items() for n,u in fs]:
  for item in catalog['talents']:
   if item.get('rework_revision')==5 and item.get('race')==race and set(item.get('target_units',()))<=set(units) and item.get('target_units') and not item['effect'].get('retired'):
    item['bundle_family']={73:72,85:81}.get(min(units),min(units));item['effect']['qa_revision']=REVISION
 missions=load_missions()
 for s in specifications():
  repeat=s['kind'] in ('health','attack');ordinal=s['ordinal'];effect=dict(type='rework_v5',ordinal=ordinal,qa_revision=REVISION,benefit_power_quarters=4,unit_growth=copy.deepcopy(s))
  item=dict(id=identity(ordinal),name=s['name'],race=s['race'],rarity=s['rarity'],target=s['target'],target_units=s['units'],
   description=s['description'],source_description=s['description'],effect=effect,bit_index=s['index'],wire_storage=s['storage'],
   category='combat',kind='talent',implemented=True,native_status='implemented',rework_revision=5,effect_ordinal=ordinal,
   repeatable=repeat,requirements={'production':False},missions=[x['mission_id'] for x in missions if x['race']==s['race']],
   expansion_revision=REVISION,balance_revision=9,bundle_family={73:72,85:81}.get(min(s['units']),min(s['units'])))
  item.update(pre_balance_description=item['description'],pre_balance_effect=copy.deepcopy(effect))
  if repeat:item['max_rank']=4
  if s['index']<len(catalog['talents']):
   assert catalog['talents'][s['index']]['id']==item['id']
   catalog['talents'][s['index']]=item
  else:
   assert s['index']==len(catalog['talents'])
   catalog['talents'].append(item)
 catalog['unit_growth_revision']=REVISION
 catalog['unit_growth_summary']=dict(unit_families=44,health_manuals=44,attack_manuals=34,new_unit_traits=44,paired_unit_rewards=True)
 return catalog

def generate_header(catalog,root):
 rows=specifications();lines=['#pragma once','namespace unit_growth {',
 'struct Rule {unsigned ordinal,kind,parent,armor,hp,damage,speed,energy;unsigned units[8];};','inline constexpr Rule rules[]={']
 for s in rows:
  mask=[0]*8
  for unit in s['units']:mask[unit//32]|=1<<(unit%32)
  fields=[s['ordinal'],{'health':0,'attack':1,'trait':2,'shadow':3}[s['kind']],s.get('parent',0),*[s.get(k,0) for k in ('armor','hp','damage','speed','energy')]]
  lines.append('{'+','.join(str(x)+'u' for x in fields)+',{'+','.join(str(x)+'u' for x in mask)+'}},')
 lines+=['};','}']
 target=root/'sc1/native_campaign/plugin/include/unit_growth.generated.h';target.write_text('\n'.join(lines)+'\n',encoding='utf8')
