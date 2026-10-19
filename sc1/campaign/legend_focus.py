"""QA39 single-target builds, utility demotions and explicit spell replacement."""
REVISION=2026102039
# ordinal,name,mode,base bonus,cadence,proc percent,ramp step,limit
# Modes:0 steady,1 execute,2 periodic,3 ramp,4 active reflection,
# 5 stored retaliation,6 armor erosion,7 moving hunt,8 giant hunter.
SPECS=(
 (49,'집행 저격',1,100,1,300,0,35),
 (54,'사냥꾼 주행 사격',7,200,1,100,0,0),
 (55,'결전 공성포',2,0,2,700,0,0),
 (56,'삼중 집중 조준',0,200,1,0,0,0),
 (57,'집중 전함 포격',2,100,3,600,0,0),
 (60,'대형 성형 지뢰',0,500,1,0,0,0),
 (90,'집중 독침',3,0,1,0,30,180),
 (96,'정밀 갈귀',9,50,1,0,0,0),
 (105,'집중 쐐기',0,200,1,0,0,0),
 (137,'과충전 위상탄',2,75,4,600,0,0),
 (139,'응축 보복',5,100,1,30,0,200),
 (141,'결전 갑충탄',0,400,1,0,0,0),
 (142,'거대 표적 사냥',8,75,1,200,0,0),
 (148,'집중 요격',3,0,1,0,20,120),
 (184,'가우스 집중 포화',2,25,3,300,0,0),
 (190,'끝없는 갑각 분쇄',6,0,1,0,1,0),
 (194,'태양의 결투',1,200,1,200,0,50),
 (197,'위상 과부하',2,0,6,900,0,0),
)
CONVERTED=frozenset(x[0] for x in SPECS)
DEMOTIONS=frozenset((136,138,140))
def decorate(catalog):
 by={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
 for ordinal,name,mode,base,cadence,proc,step,limit in SPECS:
  item=by[ordinal];item['name']=name
  text=[]
  if base:text.append(f'일반 공격 피해 +{base}%.')
  if mode==1:text.append(f'대상 체력이 {limit}% 이하면 피해 +{proc}% 추가.')
  if mode==2:text.append(f'같은 적을 {cadence}회 공격할 때마다 그 적에게 원래 공격의 {proc}% 추가 피해.')
  if mode==3:text.append(f'같은 적을 연속 공격하면 피해가 타격당 {step}%씩 최대 {limit}% 추가 증가. 표적 변경·3초 중단 시 초기화.')
  if mode==4:text.append(f'직접 공격 후 3초간 받은 일반 공격의 실제 체력 피해 {proc}%를 공격자에게 반사. 초당 최대 {limit}. 반사는 재반사되지 않습니다.')
  if mode==5:text.append(f'받은 일반 공격의 실제 체력·보호막 피해 {proc}%를 최대 {limit}까지 저장해 다음 직접 공격의 주 대상에게 돌려줍니다. 공격해야 방출됩니다.')
  if mode==6:text.append('저글링의 공격마다 그 적의 체력 방어력을 1씩 끝없이 깎습니다. 0 아래의 누적분은 저글링의 추가 피해가 됩니다. 대상이 죽거나 소유자가 바뀌면 초기화.')
  if mode==7:text.append(f'이동 사격 유지. 이동 중 피해 +{proc}% 추가(총400%). 정지 시 총300%.')
  if mode==8:text.append(f'대형 유닛·건물에게 피해 +{proc}% 추가.')
  if mode==9:text.append('최대 체력3배. 공중 적을 추격할 때 받는 일반 공격 피해75% 감소. 과잉 자폭을 피하도록 주변 표적을 분배합니다. 지상 공격은 없습니다.')
  if ordinal==55:text.append('공성 모드 이동 유지. 이동 중 공격 불가.')
  if ordinal==148:text.append('캐리어의 요격기에 적용.')
  item['description']=' '.join(text)+' 주 대상만 타격하며 주변 추가 피해·튕김은 없습니다.'
  if ordinal==197:item['description']='기본 범위 공격은 유지합니다. 같은 공중 적을 6회 공격할 때마다 그 주 대상에게 원래 공격의 900% 추가 피해를 줍니다. 추가 타격은 주변에 퍼지지 않습니다.'
  item['effect'].update(qa_revision=REVISION,focus_legend=True,focus_mode=mode,base_bonus_percent=base,
   focus_cadence=cadence,focus_proc_percent=proc,focus_step_percent=step,focus_limit=limit,legacy_area_effect_disabled=True,
   design_role='single_target',reflection_requires_attacking=mode==4,reflection_only_releases_on_attack=mode==5)
 for ordinal in DEMOTIONS:
  item=by[ordinal];item['rarity']='epic';item['previous_rarity']='legendary';item['effect'].pop('rarity_promoted',None)
  item['effect']['qa_revision']=REVISION
 by[105]['effect'].update(projectile_count=1,projectile_damage_percent=300)
 by[148]['effect'].update(additional_targets=0,additional_target_damage_percent=0)
 by[136]['description']='캐리어 출격·인터셉터 이동 속도가 2.25배가 됩니다. 체력 증가와 방어력 무시 효과는 없습니다.'
 by[136]['effect'].update(ignore_health_armor=False,health_bonus_percent=0)
 by[140]['description']='아콘이 이동하면서 공격합니다. 이동 중과 정지 시 모두 원래 공격의 100% 피해를 줍니다.'
 by[140]['effect']['moving_attack_percent']=100
 item=by[82];item['name']='마비성 인스네어';item['description']='퀸의 인스네어에 걸린 적의 공격 속도·이동 속도가 각각 85% 감소합니다. 기본 감속에 85%를 더 곱하지 않고 최종 속도를 15%로 맞춥니다. 범위·지속 시간 강화와 함께 적용됩니다.'
 item['effect'].update(qa_revision=REVISION,broodling_extra_disabled=True,ensnare_attack_speed_reduction_percent=85,ensnare_movement_speed_reduction_percent=85)
 by[104]['description']=by[104]['description'].replace(' 증식 브루들링과 합쳐도 대상당 최대 6기.','')
 by[104]['effect']['qa_revision']=REVISION
 by[106]['description']='디바우러가 지상 적도 공격합니다. 지상 피해400%, 공중 피해200%. 이 디바우러가 묻힌 산성 포자의 중첩당 추가 피해·공격 속도 저하 효과가2배가 됩니다.'
 by[106]['effect'].update(qa_revision=REVISION,acid_spore_effect_multiplier=2)
 by[92]['description']='울트라의 주 대상 공격에 더해 전방의 다른 지상 적 최대3기에게 원래 공격의70% 피해를 줍니다. 주 대상·추가 타격으로 실제 깎은 체력·보호막만큼 자신의 체력을 회복합니다. 방어막 흡수·초과 피해는 제외.'
 by[92]['effect'].update(qa_revision=REVISION,cleave_extra_targets=3,cleave_damage_percent=70,actual_hp_shield_lifesteal_percent=100)
 by[97]['description']='러커가 공중 적에게도 가시를 쏩니다. 대공 피해는 원래 공격의100%이며 추가 피해 증가는 없습니다. 한 공격은 한 공격층만 맞힙니다.'
 by[97]['effect'].update(qa_revision=REVISION,air_attack_percent=100)
 by[185]['description']='파이어뱃의 일반 공격 피해+100%. 전방3타일·120도 부채꼴 안 다른 지상 적들에게 원래 공격의100% 화염을 보냅니다. 추가 화염은 다시 발동시키지 않습니다.'
 by[185]['effect'].update(qa_revision=REVISION,mode=11,bonus=100,cone_radius_pixels=96,cone_angle_degrees=120)
 by[149]['description']='스테이시스 필드 반경 1.5배. 해제된 아군은 체력·보호막을 완전히 회복합니다. 적에게는 기존 보호막400·체력300+최대체력25% 피해와 주변 감속을 줍니다.'
 by[149]['effect'].update(qa_revision=REVISION,stasis_radius_multiplier=1.5,stasis_friendly_full_health_shields=True)
 catalog['legend_focus_revision']=REVISION;catalog['single_target_legend_ordinals']=sorted(CONVERTED)
 return catalog

def generate_header(catalog,root):
 by={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
 lines=['#pragma once','namespace legend_focus {','struct Rule {unsigned ordinal,mode,base,cadence,proc,step,limit;unsigned units[8];};','inline constexpr Rule rules[]={']
 for spec in SPECS:
  ordinal=spec[0];units=([73] if ordinal==148 else [85] if ordinal==141 else by[ordinal]['target_units']);mask=[0]*8
  for unit in units:mask[unit//32]|=1<<(unit%32)
  values=[ordinal,*spec[2:]]
  lines.append('{'+','.join(str(n)+'u' for n in values)+',{'+','.join(str(x)+'u' for x in mask)+'}},')
 lines+=['};','inline constexpr bool converted(unsigned ordinal) noexcept {for(auto r:rules)if(r.ordinal==ordinal)return true;return false;}','}']
 (root/'sc1/native_campaign/plugin/include/legend_focus.generated.h').write_text('\n'.join(lines)+'\n',encoding='utf8')
