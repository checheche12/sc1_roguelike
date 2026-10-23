"""Live QA65 balance and transport changes; frozen design text stays intact."""
REVISION=2026102265


def decorate(catalog):
    by={x['effect_ordinal']:x for x in catalog['talents'] if x.get('rework_revision')==5}
    # Unit-family decoration runs after legendary_expansion; retain the newer
    # reviewed cloud size when refreshing a campaign's pinned catalog.
    by[103]['effect'].update(qa_revision=2026102267,swarm_radius_tiles=5)
    by[18]['description']='아군 일반 공격마다 원래 피해의 50%인 공격을 한 번 더 합니다. 원거리는 탄환을 추가 발사하며, 러커의 관통 가시는 명중한 적마다 50% 추가 타격합니다.'
    by[18]['effect'].update(qa_revision=REVISION,instant_projectile_supported=True,lurker_bonus_per_pierced_target=True)
    mutal=by[105]
    mutal['description']='뮤탈리스크의 일반 공격 피해 +100%. 쐐기벌레가 최대 6번 튕깁니다. 튕길 때마다 첫 명중 피해의 1/7씩 감소합니다(7/7→6/7→5/7→4/7→3/7→2/7→1/7).'
    mutal['notes']='한 쐐기벌레당 최초 명중 포함 최대 7회. 다른 튕김 재능과 함께 획득해도 최대 6번 튕깁니다.'
    mutal['effect'].update(qa_revision=REVISION,design_role='bouncing_attack',legendary_bounces=6,bounce_damage_numerators=[7,6,5,4,3,2,1],bounce_damage_denominator=7,bounce_decay='linear_from_first_hit',projectile_damage_percent=200,projectile_count=1)
    guardian=by[191]
    guardian['description']='가디언의 일반 공격 피해 +150%. 명중하면 3타일 안 다른 지상 적 최대 6기에도 강화된 공격의 100% 피해를 줍니다.'
    guardian['effect'].update(qa_revision=REVISION,bonus=150,secondary_uses_boosted_attack=True)
    for ordinal,subject in ((33,'드롭십'),(74,'오버로드'),(115,'셔틀')):
        item=by[ordinal]
        item['description']=f'{subject}의 이동 속도 +40%.'
        item['effect'].update(qa_revision=2026102490,transport_capacity_bonus=0,movement_speed_bonus_percent=40,offer_retired=True,transport_speed_offer_removed=True)
        item['notes']='수송 공간 확대 효과 제거. 기본 수송 공간과 수송 기술 요구 조건을 유지합니다.'
    by[322]['candidate_weight_percent']=300
    by[322]['effect']['qa_revision']=REVISION
    if 'single_target_legend_ordinals' in catalog:
        catalog['single_target_legend_ordinals']=[x for x in catalog['single_target_legend_ordinals'] if x!=105]
    return catalog
