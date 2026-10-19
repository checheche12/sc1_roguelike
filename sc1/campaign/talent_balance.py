"""QA6 balance overlay. Wire identities and the accepted design remain frozen."""
from __future__ import annotations
import copy
import json
from pathlib import Path

REVISION = 2026101610
UNIT_LEGENDARIES = frozenset((61,62,63,64,65,66,102,103,104,105,106,107,144,145,146,147,148,149))
POWER_QUARTERS = dict(common=6, uncommon=7, rare=8, epic=10, legendary=10)

def power_quarters(item):
    if item.get('rework_revision')==5 and item.get('effect_ordinal')==47:return 8
    if item.get("rework_revision")==5 and item.get("effect_ordinal") in (18,148):return 4
    if item.get("rework_revision")==5 and item.get("effect_ordinal") in UNIT_LEGENDARIES:return 16
    patches=item.get('effect',{}).get('patches',[])
    resource_only=bool(patches) and not item.get('effect',{}).get('movement') and all(
        p['table']=='units' and p['field'] in ('mineralCost','gasCost','timeCost','supplyProvided','supplyUsed') for p in patches)
    return 4 if item.get('category')=='economy' or resource_only else POWER_QUARTERS[item['rarity']]

# Display the live values; no edits are made to source_description or input r42.
REPLACEMENTS = {
 8:[('+3%','+4.5%')],9:[('+3%','+4.5%')],10:[('1타일','1.75타일')],
 11:[('+0.5','+0.5')],12:[('+0.5','+0.5')],13:[('1 늘','2 늘')],
 14:[('0.75초','1.875초'),('1.5타일','3.75타일')],15:[('3초','7.5초'),('15%','38%')],
 16:[('30%','75%')],17:[('1.25초','3.125초')],18:[('50%','125%')],
 26:[('+20%','+28%')],27:[('+20%','+28%')],28:[('+20%','+28%')],
 29:[('+10%','+15%'),('-3%','-4.5%')],30:[('+2','+3'),('-3%','-4.5%')],31:[('+2','+3'),('-3%','-4.5%')],
 32:[('+1','+2'),('+15%','+26.25%')],33:[('20%','40%')],34:[('1타일','2타일')],
 35:[('70%','90%')],36:[('+100','+200'),('즉시 100','즉시 200')],37:[('2.5배','4배')],38:[('30%','60%')],
 39:[('+50%','+100%'),('-50%','-90%')],40:[('속도 +50%','속도 +100%')],
 41:[('8초','20초'),('체력 8','체력 20'),('6 피해','15 피해')],
 42:[('+100','+200'),('+50%','+100%')],43:[('50%','100%')],44:[('50%','100%')],45:[('50%','100%')],
 48:[('25%','50%')],49:[('50%','125%')],50:[('15 회복','37.5 회복')],51:[('5초','12.5초')],52:[('2초','5초')],
 53:[('60%','150%')],55:[('50%','100%')],56:[('2기','4기')],57:[('3기','6기')],58:[('60%','150%')],59:[('2타일','5타일')],
 61:[('최대 2회','최대 5회')],62:[('25%','62.5%'),('최대 100','최대 250')],64:[('50%','125%')],
 67:[('+20%','+28%')],68:[('+20%','+28%')],69:[('+20%','+28%')],
 70:[('+1','+1.5 (정수 반올림)'),('-3%','-4.5%')],71:[('+2','+3'),('-3%','-4.5%')],72:[('+2','+3')],
 73:[('+2','+4')],74:[('20%','40%')],75:[('25%','50%')],76:[('100 늘','200 늘')],77:[('2배','3배')],78:[('25%','50%')],79:[('+50','+100')],
 80:[('+25%','+50%'),('+50%','+100%')],82:[('3기','4기')],83:[('50%','100%')],84:[('50%','100%')],
 88:[('25%','50%')],89:[('1%','2%')],91:[('25%','62.5%')],95:[('70%','175%')],96:[('70%','175%')],
 99:[('20%','50%')],101:[('20 회복','50 회복')],104:[('6기','12기')],105:[('60%','150%')],107:[('30초','75초')],
 108:[('+20%','+28%')],109:[('+20%','+28%')],110:[('+20%','+28%')],111:[('+1','+1.5 (정수 반올림)'),('-3%','-4.5%')],112:[('+2','+3')],
 113:[('+1','+2')],114:[('2배','3배')],115:[('20%','40%')],116:[('2 늘','4 늘')],118:[('+100','+200')],119:[('2배','3배')],120:[('25%','50%')],
 121:[('25%','50%')],122:[('4기','6기')],123:[('25%','50%')],124:[('+25%','+50%'),('+50%','+100%')],
 125:[('절반이 남습니다','전부 남습니다')],126:[('75 줄','150 줄')],127:[('+25%','+50%'),('+50%','+100%')],128:[('+25%','+50%'),('+50%','+100%')],
 129:[('25%','50%')],130:[('4기','8기'),('12기','16기')],131:[('50%','100%')],
 137:[('50%','125%')],138:[('2타일','5타일')],139:[('2기','4기')],140:[('60%','150%')],141:[('50%','125%')],
 143:[('3초','7.5초'),('-30%','-75%')],144:[('+50%','+125%'),('4개','9개')],145:[('12초','30초')],146:[('1기도','3기도')],147:[('25%','62.5%')],148:[('1기도','3기도')],149:[('100·','250·'),('75를','187.5를')],150:[('3초','5.25초'),('20%','35%')],
 161:[('8초','20초'),('8 피해','20 피해')],
}
DESCRIPTIONS = {
 53:'마린·짐 레이너(마린)가 한 번 공격할 때 기본탄 100% 한 발과 추가탄 35% 두 발을 쏩니다. 총 피해 170%.',
 5:'임무 시작 시 보유 저주 수 × 37.5만큼 미네랄·가스를 받습니다. 총합의 소수점은 버립니다.',
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

DESCRIPTIONS.update({56: '골리앗이 서로 다른 적 최대 3기를 동시에 공격합니다. 각 대상에게 원래 피해를 줍니다.', 61: '이레디에이트 피해 3배, 효과 반경 4타일. 감염된 적이 죽으면 4타일 안 생체 적 최대 5기에 전염되며, 최초 시전부터 최대 5단계까지 이어집니다. 전염마다 온전한 지속시간을 받으며 같은 시전의 중복 감염은 없습니다. 원래 아군 피해도 유지됩니다.', 62: 'EMP가 보호막·에너지가 없는 적에게도 체력 피해 200을 줍니다. 제거한 보호막·에너지의 100%를 추가 피해로 주며 대상당 최대 600. EMP 반경은 기본의 2배가 됩니다.', 63: '락다운이 생체 전투 유닛에도 적용되며, 생체 대상 지속 시간이 최대 4배가 됩니다. 시전 성공 시 주 대상의 3타일 안 다른 적 전투 유닛 최대 2기도 추가 봉쇄합니다.', 64: '야마토 3발이 각각 원래의 200% 피해를 줍니다. 추가 2발은 주 대상의 4타일 안 다른 적을 우선 공격하며, 적이 부족하면 살아 있는 주 대상에 집중합니다. 에너지 소모는 총 75입니다.', 65: '배틀크루저가 지상·공중을 동시에 공격합니다. 추가 공격층의 피해는 400%입니다.', 66: '메딕이 주 치료 대상의 4타일 안 생체 아군 최대 8기를 원래 치료 속도의 200%로 추가 치료합니다. 공중 생체 아군도 치료하며 총 에너지 소모는 2배입니다.', 102: '플레이그가 적을 죽일 수 있으며 체력 피해가 4배가 됩니다. 아군 피해도 유지됩니다.', 103: '다크 스웜이 아군 공중 유닛도 보호하며 보호 범위가 최소 10타일로 늘어납니다. 마법·광역 예외는 유지됩니다.', 104: '퀸의 스폰 브루들링이 총 18기를 만듭니다. 브루들링의 최대 체력·공격력도 2배가 됩니다. 증식 브루들링과 합쳐도 총 18기입니다.', 105: '뮤탈이 쐐기벌레를 2발씩 쏩니다. 각 발은 100% 피해를 주며 따로 튕깁니다.', 106: '디바우러가 지상 적도 공격합니다. 지상 피해 400%, 공중 피해 200%이며 산성 포자도 적용됩니다.', 107: '퀸이 인페스트로 체력 50% 이하인 적 전투 유닛을 120초간 조종합니다. 성공하면 4타일 안 조건을 만족하는 다른 적 1기도 추가 지배합니다. 에너지 150.', 144: '하이 템플러의 스톰 피해 +100%, 반경 +200%. 서로 다른 스톰의 피해가 같은 지점에서 최대 13개 겹칩니다.', 145: '아비터가 리콜한 뒤 48초간 소환문을 남깁니다. 2초마다 같은 출발지 4타일 안의 아군을 같은 도착지로 소환합니다.', 146: '다크 아콘이 마인드 컨트롤한 적의 4타일 안 다른 적 최대 4기도 지배합니다. 추가 대상 인구는 주 대상 이하입니다.', 147: '하이 템플러가 만든 환영의 일반 공격이 원래 피해의 100%를 실제 피해로 줍니다.', 148: '인터셉터가 주변의 다른 적 4기도 공격합니다. 각 대상에게 원래 피해를 줍니다.', 149: '아비터의 스테이시스가 끝나면 갇혔던 적에게 보호막 피해 400과 체력 피해 300 + 최대 체력의 25%를 줍니다.'})

DESCRIPTIONS[72]='뮤탈리스크의 공격력 +6, 다른 저그 공중 전투 유닛의 공격력 +3. 해당 유닛들의 공격 간격이 4.5% 줄어듭니다. 반복해서 고를 수 있습니다.'

DESCRIPTIONS[70]='저글링·브루들링의 공격력 중첩당 +1.5(중첩 합계를 정수 반올림), 울트라리스크의 공격력 중첩당 +6. 해당 유닛들의 공격 간격이 중첩당 4.5% 줄어듭니다. 반복해서 고를 수 있습니다.'

DESCRIPTIONS[89]='잠복 후 3초간 공격하거나 맞지 않으면 초당 최대 체력의 6%를 추가 회복합니다.'

DESCRIPTIONS[148]='인터셉터가 주변의 다른 적 2기도 공격합니다. 각 대상에게 원래 피해를 줍니다.'

DESCRIPTIONS.update({
 14:'삭제된 재능입니다. 더 이상 선택하거나 효과를 받을 수 없습니다.',
 36:'고스트·메딕·과학선의 최대 에너지 +200. 획득 시 기존 병력과 이후 생산 완료된 병력에 현재 에너지 200을 한 번 지급합니다.',
 76:'퀸·디파일러의 최대 에너지 +200. 획득 시 기존 병력과 이후 생산 완료된 병력에 현재 에너지 200을 한 번 지급합니다.',
 118:'하이 템플러·다크 아콘·아비터·커세어의 최대 에너지 +200. 획득 시 기존 병력과 이후 생산 완료된 병력에 현재 에너지 200을 한 번 지급합니다.',
 8:'아군 지상 전투 유닛의 일반 공격 피해 +15%, 이동 속도 +4.5%. 중첩당 적용되며 최대 4회 선택할 수 있습니다.',
 9:'아군 공중 전투 유닛의 일반 공격 피해 +15%, 이동 속도 +4.5%. 중첩당 적용되며 최대 4회 선택할 수 있습니다.',
 29:'마린·파이어뱃·고스트의 공격력 중첩당 +15%, 공격 간격 -4.5%. 파이어뱃은 일반 공격으로 받는 피해도 중첩당 10% 줄어듭니다. 최대 4회.',
 30:'중첩당 벌처 공격력 +4.5, 전차 모드 +6, 공성 모드 +12, 골리앗 +3. 공격 간격 -4.5%. 소수점 공격력은 중첩 합계를 반올림하며 최대 4회.',
 31:'중첩당 배틀크루저 공격력 +6, 다른 테란 공중 전투 유닛 +3. 공격 간격 -4.5%. 최대 4회.',
 70:'중첩당 저글링·브루들링 공격력 +1.5, 울트라리스크 +6, 감염된 테란 +60. 공격 간격 -4.5%, 일반 공격으로 받는 피해 -10%. 소수점 공격력은 중첩 합계를 반올림하며 최대 4회.',
 111:'중첩당 질럿 공격력 +1.5, 드라군 +3, 다크 템플러·아콘 +6, 리버·스캐럽 +15. 공격 간격 -4.5%. 질럿·다크 템플러는 일반 공격으로 받는 피해도 중첩당 10% 줄어듭니다. 공격력 합계 반올림, 최대 4회.',
 91:'러커가 잠복한 상태에서 우클릭 이동과 어택땅(A+지점)을 할 수 있습니다. 이동 속도는 기본의 62.5%이며 이동 중에는 공격하지 않습니다.',
})

DESCRIPTIONS.update({
 18:'아군 일반 공격마다 원래 피해의 50%인 공격을 한 번 더 합니다. 원거리는 탄환을 추가 발사합니다.',
 85:'퀸이 체력 75% 이하인 커맨드 센터를 감염시킬 수 있습니다.',
 107:'퀸이 인페스트로 체력 50% 이하인 적 전투 유닛을 120초간 조종합니다. 성공하면 4타일 안 조건을 만족하는 다른 적 1기도 추가 지배합니다.',
})

DESCRIPTIONS.update({
 47:'레이스·발키리·배틀크루저(영웅 포함) 사거리 +1타일, 이동 속도 +20%. 레이스·배틀크루저는 이동 사격. 표적을 잃은 테란 유도탄은 4타일 안 적을 한 번 재추적.',
 65:'야마토 준비 동작 약 3배 가속. 일반 공격 4회마다 무료 야마토 1발. 지상·공중 포대는 따로 사격하며 추가 포대 피해 100%. 자동 야마토는 추가탄을 만들지 않습니다.',
 69:'저그 공중군 체력 중첩당 +28%, 최대 4회. 첫 선택에 가디언·디바우러(영웅 포함) 사거리 +1타일, 이동 속도 +20%. 기동 보너스 중첩 없음.',
 72:'중첩당 뮤탈리스크·가디언(영웅 포함)의 공격력 +6, 다른 저그 공중 전투 유닛의 공격력 +3. 공격 간격 -4.5%. 최대 4회.',
 110:'공중군 체력·보호막 중첩당 +28%(최대 4회). 첫 선택: 스카우트·커세어·아비터 사거리 +1타일, 캐리어 교전 거리 +1타일. 스카우트·캐리어·아비터 이동 속도 +20%. 영웅 포함, 기동 보너스 중첩 없음.',
 112:'프로토스 공격 항공기와 인터셉터의 공격력 중첩당 +3, 공격 간격 -4.5%. 최대 4회.',
 153:'레이스·발키리·배틀크루저·과학선·드롭십의 생산 비용 -20%, 생산 시간 -20%.',
 157:'뮤탈·가디언·디바우러·스커지의 생산·변태 비용 -20%, 생산·변태 시간 -20%.',
 160:'스카우트·커세어·캐리어·아비터·셔틀·옵저버의 생산 비용 -20%, 생산 시간 -20%.',
})

def decorate(catalog):
    catalog['balance_revision']=9
    catalog.pop('talent_power_halves',None)
    catalog['talent_power_quarters']=POWER_QUARTERS.copy()
    catalog['economy_talents_scaled']=False
    for item in catalog['talents']:
        if item.get('rework_revision')==5 and item.get('effect_ordinal')==47:item['rarity']='uncommon'
        if item.get('balance_revision')==9:continue
        original=item['description'];q=power_quarters(item)
        item['balance_revision']=9
        item['pre_balance_description']=original
        item['pre_balance_effect']=copy.deepcopy(item['effect'])
        item['effect'].update(qa_revision=REVISION,benefit_power_quarters=q)
        if item.get('rework_revision')==5:
            ordinal=item['effect_ordinal']
            text=original
            for a,b in REPLACEMENTS.get(ordinal,[]):text=text.replace(a,b)
            item['description']=DESCRIPTIONS[5] if ordinal==5 else original if q==4 and ordinal not in (18,148,153,157,160) else DESCRIPTIONS.get(ordinal,text)
            if item.get('max_rank')==4 and ordinal not in (8,9,29,30,31,69,70,72,110,111,112):
                item['description']=item['description'].replace('반복해서 고를 수 있습니다.','')+' 중첩당 적용, 최대 4회 선택할 수 있습니다.'
            if ordinal in (18,85,107):item['effect']['qa_revision']=2026101816
            if ordinal==148:item['effect'].update(qa_revision=2026101933,additional_targets=2,additional_target_damage_percent=100)
            if ordinal==53:item['effect'].update(qa_revision=2026101929,primary_attack_percent=100,extra_attack_percent=35,extra_attack_count=2,total_attack_percent=170)
            if ordinal in (47,65,69,110,112,153,157,160):item['effect']['qa_revision']=2026101929
            if ordinal in (47,69,110):item['effect'].update(air_control_range_tiles=1,air_control_speed_percent=20,air_control_stacks=False)
            if ordinal==47:item['effect']['moving_air_primary_attack_percent']=100
            if ordinal==65:item['effect'].update(auto_yamato_every_primary_attacks=4,auto_yamato_percent=100,auto_yamato_energy=0,secondary_layer_percent=100,yamato_prelaunch_wait_frames=0,yamato_cast_speed_approx_multiplier=3,yamato_cast_speed_stacks=False)
            if ordinal in (153,157,160):item['effect']['production_time_reduction_percent']=20
            if ordinal==18:item['effect']['extra_attack_percent']=50
            if ordinal in (85,107):item['effect']['energy_cost']=0
            if ordinal in (11,12):item['effect']['armor_per_rank']=0.5
            if ordinal in (26,27,28,67,68,69,108,109,110):item['effect']['health_percent_per_rank']=28
            if ordinal in (108,109,110):item['effect']['shield_percent_per_rank']=28
            if ordinal==5:item['effect'].update(resources_per_curse=37.5,resource_total_rounding='floor')
            if ordinal in (5,11,12,26,27,28,67,68,69,108,109,110):item['effect']['qa_revision']=2026101713
            if ordinal==29:item['effect']['weapon_damage_percent_per_rank']=15
            if ordinal==51:item['effect']['armor_mark_frames']=300
            if ordinal in (14,36,64,76,118):item['effect']['qa_revision']=2026101712
            if ordinal==14:item['effect']['retired']=True
            if ordinal in (36,76,118):
                item['effect'].update(energy_grant_on_acquisition=True,energy_grant_on_production=True,energy_grant_once=True)
            # Apply the latest revision last: QA13 health metadata must not
            # overwrite the new fleet revision and block pinned-store refresh.
            if ordinal in (69,110,135):item['effect']['qa_revision']=2026101930
            if ordinal==110:item['effect'].update(corsair_range_tiles=1,corsair_speed_bonus=False,carrier_engagement_range_tiles=1)
            if ordinal==135:item['effect'].update(attack_counter='primary_corsair_launch',spells_count_as_attacks=False,secondary_attacks_count=False)
            if ordinal==72:item['effect'].update(qa_revision=2026101931,mutalisk_guardian_attack_per_rank=6,other_air_attack_per_rank=3)
            if ordinal==105:item['effect'].update(qa_revision=2026101932,projectile_damage_percent=100,projectile_count=2)
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
    if result.pop('balance_revision',None) in (6,7,9):
        result['description']=result.pop('pre_balance_description')
        result['effect']=result.pop('pre_balance_effect')
    return result


def generate_header(catalog, root):
    values=[power_quarters(item) for item in sorted(catalog['talents'],key=lambda x:x['bit_index'])]
    target=Path(root)/'sc1/native_campaign/plugin/include/talent_power.generated.h'
    target.write_text('#pragma once\nnamespace talent_power {\ninline constexpr unsigned kPowerQuarters[400]={'
                      +','.join(map(str,values))+'};\n}\n',encoding='utf8')
    return target
