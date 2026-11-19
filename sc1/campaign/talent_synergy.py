"""Independent owned talents compose without changing their saved identities."""
REVISION=2026110302
FOLLOWUP_REVISION=2026110303

def followup(catalog):
    by={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
    groups={
        'attack_interval_bonuses_multiply':(16,162),
        'cloud_radius_bonuses_add':(83,103),
        'free_yamato_combines_triple_cast':(64,65),
        'spread_spores_inherit_amplification':(100,106),
        'mechanical_irradiate_matches_legend_multiplier':(61,198),
        'lockdown_duration_bonuses_preserve_full_duration':(45,63),
        'independent_slow_durations_and_multipliers':(94,135,143,149),
        'added_air_range_preserves_shared_bonus':(10,59,138),
        'fast_supply_inherits_building_time_discount':(4,20,22),
        'generated_attacks_share_target_damage_rules':(19,190,92,113,150),
    }
    for flag,ordinals in groups.items():
        for ordinal in ordinals:by[ordinal]['effect'].update(qa_revision=FOLLOWUP_REVISION,**{flag:True})
    by[80]['effect'].update(qa_revision=FOLLOWUP_REVISION,radius_bonus_percent=100,radius_pixels=128)
    notes={
        16:' 단계식 전투 훈련과 함께 적용됩니다.',162:' 전투 예열과 함께 적용됩니다.',
        83:' 하늘을 덮는 군체와 함께 선택하면 반경이 7.5타일이 됩니다.',
        103:' 확장 다크 스웜과 함께 선택하면 반경이 7.5타일이 됩니다.',
        64:' 전방위 전함의 무료 야마토에도 적용됩니다.',
        65:' 삼중 야마토를 함께 선택하면 무료 야마토도 3발로 강화됩니다.',
        100:' 산성 폭풍의 포자 강화도 적용됩니다.',
        4:' 건설 효율화·소환 공정 개선의 시간 감소도 함께 적용됩니다.',
    }
    for ordinal,note in notes.items():
        if note not in by[ordinal]['description']:by[ordinal]['description']+=note
    ship=by[65]
    ship['description']='배틀크루저: 지상·공중 독립 사격, 피해 100%. 일반 사격 합산 매 4번째에 무료 야마토도 동시 발사(추가탄 제외). 야마토 준비 동작 약 3배 가속. 삼중 야마토와 조합하면 무료탄도 3발.'
    ship['effect'].update(qa_revision=2026110702,auto_yamato_counts_independent_batteries=True,
                          auto_yamato_retries_until_valid_launch=True,
                          auto_yamato_simultaneous_with_fourth_attack=True,
                          auto_yamato_replaces_normal_attack=False,auto_yamato_launch_delay_frames=0)
    catalog['talent_synergy_revision']=FOLLOWUP_REVISION
    return catalog

def decorate(catalog):
    by={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
    item=by[49]
    text=' 공격 유형이 일반형으로 바뀝니다.'
    if text not in item['description']:item['description']+=text
    item['effect'].update(qa_revision=REVISION,weapon_damage_type=3)
    for n in (44,62,127,149):
        item=by[n];text=' 다른 재능의 범위 증가분과 합산됩니다.'
        if text not in item['description']:item['description']+=text
        item['effect'].update(qa_revision=REVISION,radius_bonus_stacking='additive')
    for item in by.values():
        effect=item['effect'];spec=effect.get('unit_growth',{})
        if effect.get('retired') or spec.get('kind') not in ('attack','health'):continue
        for target in (item,spec):
            target['description']=target['description'].replace('기존 병과 체력 교범과 합산해 최대 4중첩입니다.','서로 다른 교범의 강화는 합산됩니다.').replace('기존 병과 교범과 합산해 최대 4중첩.','서로 다른 교범의 강화는 합산됩니다.').replace('모체·탄약 유닛 교범은 높은 쪽만 적용합니다.','모체와 탄약 유닛의 공격 교범은 함께 적용됩니다.')
        effect.update(qa_revision=REVISION,independent_manuals_stack=True)
    catalog['talent_synergy_revision']=REVISION
    followup(catalog)
    return reviewed_pairs(frontline_manuals(catalog))


def frontline_manuals(catalog):
    # Broad manuals still work in older saves alongside the unit's own manual.
    broad = {29, 70, 111}
    unit_manuals = {204, 228, 234, 248, 252, 257}
    note = '남은 일반 공격 피해가 중첩마다 10%씩 줄어듭니다.'
    for item in catalog['talents']:
        ordinal = item.get('effect_ordinal')
        if item.get('rework_revision') != 5 or ordinal not in broad | unit_manuals:
            continue
        effect = item['effect']
        if ordinal in broad:
            item['description'] = item['description'].replace(
                '일반 공격으로 받는 피해도 중첩당 10% 줄어듭니다.', note
            ).replace('일반 공격으로 받는 피해 -10%.', note)
        else:
            for description in (item, effect['unit_growth']):
                if note not in description['description']:
                    description['description'] += ' ' + note
        effect.update(frontline_damage_multiplier_per_rank=0.9, qa_revision=2026111901)
        item['description_revision'] = 2026111901
    return catalog


def reviewed_pairs(catalog):
    by = {t['effect_ordinal']: t for t in catalog['talents'] if t.get('rework_revision') == 5}
    pairs = (
        (143, 145, '아군이 소환문으로 이동하면 도착지 균열 1개 갱신.'),
        (41, 50, '체력 30% 이하 생체 아군에게 정화 적중 시 응급 처치 1회. 비용·재사용 시간 공유.'),
        (49, 63, '직접 봉쇄한 적을 저격 처치하면 6타일 내 1기에 남은 봉쇄 전이. 연쇄 없음.'),
        (88, 94, '포격에 맞은 주변 지상 적도 2초 감속.'),
        (190, 98, '착지 후 1초 내 첫 타격이 도약 대상에 명중하면 방어력 감소 2회.'),
        (114, 323, '잔향으로 회복 시 재충전 대기 3초. 다시 피격되면 6초.'),
        (197, 135, '감속 중인 적에게 과부하 발동 시 3타일 내 다른 공중 적 1기에 남은 감속 전달.'),
    )
    # Keep the complete pair on the native card's eight visible lines.
    by[63]['description'] = '고스트 락다운: 생체 병력도 봉쇄(지속 최대 2배). 6타일 내 적 최대 6기 추가. 봉쇄·탄착 예정인 적은 후순위.'
    by[145]['description'] = '아비터 리콜 후 48초간 2초마다 출발지 4타일 내 아군을 재소환. 첫 리콜·재소환 시 일반 공격 피해 +20%, 30초. 재통과 시 시간 갱신.'
    for first, second, note in pairs:
        for ordinal, partner in ((first, second), (second, first)):
            item = by[ordinal]
            item['effect'].update(synergy_partner_ordinal=partner, qa_revision=2026111902)
            text = f" [{by[partner]['name']}] {note}"
            if text not in item['description']:
                item['description'] += text
            item['description_revision'] = 2026111902
    return catalog
