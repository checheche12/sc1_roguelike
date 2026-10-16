"""QA6 balance overlay. Wire identities and the accepted design remain frozen."""
from __future__ import annotations
import copy
import json
from pathlib import Path

REVISION = 2026101607
POWER_QUARTERS = dict(common=6, uncommon=7, rare=8, epic=10, legendary=10)

def power_quarters(item):
    patches=item.get('effect',{}).get('patches',[])
    resource_only=bool(patches) and not item.get('effect',{}).get('movement') and all(
        p['table']=='units' and p['field'] in ('mineralCost','gasCost','timeCost','supplyProvided','supplyUsed') for p in patches)
    return 4 if item.get('category')=='economy' or resource_only else POWER_QUARTERS[item['rarity']]

# Display the live values; no edits are made to source_description or input r42.
REPLACEMENTS = {
 8:[('+3%','+4.5%')],9:[('+3%','+4.5%')],10:[('1타일','1.75타일')],
 11:[('+0.5','+0.75')],12:[('+0.5','+0.75')],13:[('1 늘','2 늘')],
 14:[('0.75초','1.875초'),('1.5타일','3.75타일')],15:[('3초','7.5초'),('15%','38%')],
 16:[('30%','75%')],17:[('1.25초','3.125초')],18:[('50%','125%')],
 26:[('+20%','+35%')],27:[('+20%','+35%')],28:[('+20%','+35%')],
 29:[('+10%','+15%'),('-3%','-4.5%')],30:[('+2','+3'),('-3%','-4.5%')],31:[('+2','+3'),('-3%','-4.5%')],
 32:[('+1','+2'),('+15%','+26.25%')],33:[('20%','40%')],34:[('1타일','2타일')],
 35:[('70%','90%')],36:[('+100','+200'),('즉시 100','즉시 200')],37:[('2.5배','4배')],38:[('30%','60%')],
 39:[('+50%','+100%'),('-50%','-90%')],40:[('속도 +50%','속도 +100%')],
 41:[('8초','20초'),('체력 8','체력 20'),('6 피해','15 피해')],
 42:[('+100','+200'),('+50%','+100%')],43:[('50%','100%')],44:[('50%','100%')],45:[('50%','100%')],
 48:[('25%','50%')],49:[('50%','125%')],50:[('15 회복','37.5 회복')],51:[('5초','12.5초')],52:[('2초','5초')],
 53:[('60%','150%')],55:[('50%','100%')],56:[('2기','4기')],57:[('3기','6기')],58:[('60%','150%')],59:[('2타일','5타일')],
 61:[('최대 2회','최대 5회')],62:[('25%','62.5%'),('최대 100','최대 250')],64:[('50%','125%')],
 67:[('+20%','+35%')],68:[('+20%','+35%')],69:[('+20%','+35%')],
 70:[('+1','+1.5 (정수 반올림)'),('-3%','-4.5%')],71:[('+2','+3'),('-3%','-4.5%')],72:[('+2','+3')],
 73:[('+2','+4')],74:[('20%','40%')],75:[('25%','50%')],76:[('100 늘','200 늘')],77:[('2배','3배')],78:[('25%','50%')],79:[('+50','+100')],
 80:[('+25%','+50%'),('+50%','+100%')],82:[('3기','4기')],83:[('50%','100%')],84:[('50%','100%')],
 88:[('25%','50%')],89:[('1%','2%')],91:[('25%','62.5%')],95:[('70%','175%')],96:[('70%','175%')],
 99:[('20%','50%')],101:[('20 회복','50 회복')],104:[('6기','12기')],105:[('60%','150%')],107:[('30초','75초')],
 108:[('+20%','+35%')],109:[('+20%','+35%')],110:[('+20%','+35%')],111:[('+1','+1.5 (정수 반올림)'),('-3%','-4.5%')],112:[('+2','+3')],
 113:[('+1','+2')],114:[('2배','3배')],115:[('20%','40%')],116:[('2 늘','4 늘')],118:[('+100','+200')],119:[('2배','3배')],120:[('25%','50%')],
 121:[('25%','50%')],122:[('4기','6기')],123:[('25%','50%')],124:[('+25%','+50%'),('+50%','+100%')],
 125:[('절반이 남습니다','전부 남습니다')],126:[('75 줄','150 줄')],127:[('+25%','+50%'),('+50%','+100%')],128:[('+25%','+50%'),('+50%','+100%')],
 129:[('25%','50%')],130:[('4기','8기'),('12기','16기')],131:[('50%','100%')],
 137:[('50%','125%')],138:[('2타일','5타일')],139:[('2기','4기')],140:[('60%','150%')],141:[('50%','125%')],
 143:[('3초','7.5초'),('-30%','-75%')],144:[('+50%','+125%'),('4개','9개')],145:[('12초','30초')],146:[('1기도','3기도')],147:[('25%','62.5%')],148:[('1기도','3기도')],149:[('100·','250·'),('75를','187.5를')],150:[('3초','5.25초'),('20%','35%')],
 161:[('8초','20초'),('8 피해','20 피해')],
}
DESCRIPTIONS = {
 19:'아군 일반 공격이 적의 체력 방어력과 보호막 방어력을 모두 무시합니다.',
 44:'과학선의 EMP 반경이 100% 넓어집니다. 아군도 맞습니다.',
 46:'고스트 핵의 낙하 경고가 5초로 줄고, 적에게 주는 핵 피해가 50% 늘어납니다.',
 47:'테란 유도탄의 표적이 죽으면 4타일 안 같은 공격층의 다른 적을 한 번 추적합니다.',
 54:'벌처가 이동하면서 지상 적을 공격합니다. 이동 사격 피해는 원래 공격의 250%입니다.',
 60:'스파이더 마인이 공중 적도 추적하며 2타일 안에서 폭발합니다. 대공 피해 +50%.',
 63:'락다운이 생체 전투 유닛에도 적용되며, 생체 대상의 지속 시간이 최대 2.5배가 됩니다.',
 65:'배틀크루저가 지상·공중을 동시에 공격합니다. 추가 공격층의 피해는 250%입니다.',
 66:'메딕이 주변 생체 아군 최대 5기를 원래 치료 속도의 125%로 추가 치료합니다. 총 에너지 소모 2배.',
 74:'수송 업그레이드가 끝난 오버로드의 수송 공간이 16칸이 되며 이동 속도 +40%.',
 81:'퀸의 기생충이 붙은 적은 아군 일반 공격 피해를 30% 더 받습니다.',
 85:'퀸이 체력 75% 이하인 커맨드 센터를 감염시킬 수 있습니다. 인페스트 에너지 비용 -25%.',
 86:'산성 포자가 최대 15중첩까지 쌓이며 지속 시간이 최대 85초까지 늘어납니다.',
 87:'스커지의 추격 대상이 죽으면 6타일 안 다른 공중 적을 한 번 추적합니다.',
 90:'히드라의 공격이 표적 뒤 적 1기를 관통해 원래 공격의 125% 피해를 줍니다.',
 92:'울트라 공격이 전방의 다른 적 최대 3기에 원래 공격의 125% 피해를 줍니다.',
 93:'뮤탈의 쐐기벌레가 최대 3회 더 튕깁니다. 튕김 피해 감쇠는 유지됩니다.',
 94:'가디언에게 직접 맞은 지상 적은 5초간 이동 속도 -50%.',
 97:'러커가 공중 적에게도 가시를 쏩니다. 대공 피해 +50%. 한 공격은 한 공격층만 맞힙니다.',
 98:'저글링이 2~4타일 떨어진 적에게 도약합니다. 재사용 약 3.2초.',
 100:'디바우러가 주변 공중 적 최대 5기에 산성 포자를 추가로 묻힙니다.',
 102:'플레이그가 적을 죽일 수 있으며 체력 피해가 2.5배가 됩니다. 아군 피해도 유지됩니다.',
 103:'다크 스웜이 아군 공중 유닛도 보호하며 보호 범위가 최소 6.25타일로 늘어납니다. 마법·광역 예외 유지.',
 106:'디바우러가 지상 적도 공격합니다. 지상 피해 250%, 산성 포자도 적용됩니다.',
 115:'셔틀의 수송 공간이 16칸이 되며 이동 속도 +40%.',
 116:'옵저버의 시야·탐지 반경 +4(최대 11), 최대 체력·보호막 +25%.',
 132:'질럿이 적에게 접근할 때 2.5초간 이동 속도 +175%로 돌진합니다.',
 133:'드라군의 위상탄은 표적이 죽으면 5타일 안 다른 적을 한 번 추적합니다.',
 134:'다크 템플러가 가까운 빈 지상 지점으로 최대 7.5타일 도약합니다. 재사용 12초.',
 135:'커세어의 네 번째 공격에 맞은 공중 적은 5초간 이동 속도 -50%.',
 136:'캐리어 출격·인터셉터 이동 속도가 2.25배가 되며 인터셉터가 체력 방어력을 무시합니다.',
 142:'스카우트가 지상·공중을 동시에 공격합니다. 추가 공격층의 피해는 250%입니다.',
}

def decorate(catalog):
    catalog['balance_revision']=7
    catalog.pop('talent_power_halves',None)
    catalog['talent_power_quarters']=POWER_QUARTERS.copy()
    catalog['economy_talents_scaled']=False
    for item in catalog['talents']:
        if item.get('balance_revision')==7:continue
        original=item['description'];q=power_quarters(item)
        item['balance_revision']=7
        item['pre_balance_description']=original
        item['pre_balance_effect']=copy.deepcopy(item['effect'])
        item['effect'].update(qa_revision=REVISION,benefit_power_quarters=q)
        if item.get('rework_revision')==5:
            ordinal=item['effect_ordinal']
            text=original
            for a,b in REPLACEMENTS.get(ordinal,[]):text=text.replace(a,b)
            item['description']=original if q==4 else DESCRIPTIONS.get(ordinal,text)
            if ordinal in (11,12):item['effect']['armor_per_rank']=0.75
            if ordinal==29:item['effect']['weapon_damage_percent_per_rank']=15
            if ordinal==51:item['effect']['armor_mark_frames']=300
        else:
            # Old set-valued cards depend on the map's original DAT values.
            # Keep that reference explicit rather than inventing a fixed total.
            item['description']=f'수치 보너스 {q/4:g}배 · 기준 효과: {original}'
            if q==4:item['description']=original
            if item['effect']['type']=='multi_target':
                item['description']=original+' 대상 유닛 최대 체력 +25%, 방어력 +1.'
            elif any(p['field']=='damageType' for p in item['effect'].get('patches',[])):
                item['description']=original+' 해당 무기의 공격력 +25%.'
    return catalog


def historical(item):
    result=copy.deepcopy(item)
    if result.pop('balance_revision',None) in (6,7):
        result['description']=result.pop('pre_balance_description')
        result['effect']=result.pop('pre_balance_effect')
    return result


def generate_header(catalog, root):
    values=[power_quarters(item) for item in sorted(catalog['talents'],key=lambda x:x['bit_index'])]
    target=Path(root)/'sc1/native_campaign/plugin/include/talent_power.generated.h'
    target.write_text('#pragma once\nnamespace talent_power {\ninline constexpr unsigned kPowerQuarters[400]={'
                      +','.join(map(str,values))+'};\n}\n',encoding='utf8')
    return target
