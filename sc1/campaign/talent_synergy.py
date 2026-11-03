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
    return followup(catalog)
