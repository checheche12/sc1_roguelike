"""Display current spawned rosters from the native roster source of truth."""
import re

NAMES={0:'마린',2:'벌처',3:'골리앗',5:'시즈 탱크',8:'레이스',12:'배틀크루저',20:'레이너(마린)',23:'듀크(탱크)',28:'하이페리온',29:'노라드 II',
 37:'저글링',38:'히드라',39:'울트라',43:'뮤탈리스크',44:'가디언',47:'스커지',48:'토라스크',51:'감염된 케리건',53:'헌터 킬러',55:'쿠쿨자(뮤탈)',56:'쿠쿨자(가디언)',
 58:'발키리',60:'커세어',61:'다크 템플러',62:'디바우러',65:'질럿',66:'드라군',67:'하이 템플러',68:'아콘',70:'스카우트',71:'아비터',72:'캐리어',75:'제라툴',77:'피닉스(질럿)',78:'피닉스(드라군)',79:'태사다르',80:'모조',83:'리버',22:'마젤란',34:'메딕',103:'러커'}

def decorate(catalog,root):
 text=(root/'sc1/native_campaign/plugin/include/rework_wave_policy.h').read_text(encoding='utf8')
 enum=re.search(r'enum Slot:U32\s*\{(.*?)\};',text,re.S)[1]
 slots={name:int(value) for name,value in re.findall(r'(\w+)\s*=\s*(\d+)',enum)}
 entries={};rows=[]
 for line in text.splitlines():
  match=re.match(r'\s*\{(\w+),(\d+),(\d+),[^,]+,(\d+),(\d+),',line)
  if not match or match[1] not in slots:continue
  name,cadence,grade,hp,attack=match.groups();slot=slots[name]
  if slot<26:continue
  percent={0:115,1:150,2:175,3:200}[int(grade)];members=[]
  for unit,count,hero in re.findall(r'\{(\d+),(\d+)(,true)?\}',line[match.end():]):
   unit,count=int(unit),int(count)
   if not count:continue
   previous=count if hero else (count*85+50)//100
   current=(previous*percent+50)//100
   label=NAMES[unit]
   if name=='Heavy':label='종족별 중화기 병력'
   if name=='Flank':label='종족별 기동 병력'
   if name in ('Vanguard','Catastrophe'):label='종족별 선두 병력' if not members else '종족별 보병'
   members.append(dict(unit_id=unit,name=label,hero=bool(hero),previous_count=previous,count=current))
  cadence=int(cadence);phrase={1:'매 공세에',2:'두 공세마다',3:'세 공세마다'}[cadence]
  description=phrase+' '+'·'.join(x['name']+' '+str(x['count'])+'기' for x in members)+'가 추가됩니다.'
  if name=='Hunters':description+=' 히드라는 최대 체력 +43%·공격력 +30%, 다른 병력은 최대 체력 +10%.'
  elif name in ('Vanguard','Catastrophe'):
   description+=f' 선두 병력 최대 체력 +{int(hp)*110//100-100}%'
   if int(attack)>100:description+=f'·공격력 +{int(attack)-100}%'
   description+=', 호위 병력 최대 체력 +10%.'
  else:description+=' 이 편성 전체 최대 체력 +10%.'
  description+=' 중첩·물량 저주와 동시 병력 상한 적용.'
  entries[slot]=dict(description=description,effect=dict(qa_revision=2026102038,wave_strength_revision=2026102038,
   wave_count_multiplier_percent=percent,wave_grade=int(grade),base_delivered_roster=members))
  rows.append(dict(slot=slot,grade=int(grade),count_multiplier_percent=percent,members=members))
 for item in catalog['curses']:
  entry=entries.get(item['byte_index'])
  if item.get('rework_revision')!=5 or entry is None:continue
  item['description']=entry['description'];item['effect'].update(entry['effect'])
 catalog['wave_balance_revision']=2026102038
 catalog['wave_count_multiplier_percent']={'normal':115,'rare':150,'epic':175,'legendary':200}
 catalog['wave_roster_review']=rows
 return catalog
