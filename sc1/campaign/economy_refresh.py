"""November economy refresh; saved talent IDs and the mission supply box stay intact."""

REVISION = 2026111501


def decorate(catalog):
    by = {x['effect_ordinal']: x for x in catalog['talents']
          if x.get('rework_revision') == 5}
    changes = {
        2: ('광물·가스의 남은 매장량이 3배가 됩니다. 같은 광물에서 아군 일꾼 2기가 동시에 채취할 수 있습니다. 한 번의 운반량은 바뀌지 않습니다.',
            dict(resource_amount_multiplier=3, simultaneous_mineral_workers=2)),
        7: ('건설 시간 -50%. 완공 시 일꾼 4기 지원(임무당 3회). 시작 기지·레어·하이브 제외. 다른 건설 가속과 중첩.',
            dict(base_build_time_reduction_percent=50, expansion_workers=4, expansion_grant_limit=3)),
        23: ('삭제된 재능입니다. 더 이상 선택하거나 효과를 받을 수 없습니다.',
             dict(retired=True, runtime_disabled=True, offer_retired=True)),
        25: ('아군 건물의 유닛 생산·연구 속도가 항상 25% 빨라집니다. 실제 작업이 진행 중일 때 적용됩니다.',
             dict(continuous_production_research_speed_percent=25)),
    }
    for ordinal, (description, effect) in changes.items():
        item = by[ordinal]
        item['description'] = description
        item['effect'].update(qa_revision=REVISION, **effect)
    by[52]['description'] = '명중 지점에 5초간 잔류 화염. 지옥불 분사와 조합하면 전방 3타일·120도 지상에 남습니다. 지속 피해 중복 불가.'
    by[52]['effect'].update(qa_revision=2026111502, persistent_ground_visual=True, cone_synergy_ordinal=185, cone_radius_pixels=96, cone_angle_degrees=120, cone_anchored_at_attack=True)
    by[185]['description'] = '일반 공격 피해 +100%. 전방 3타일·120도 추가 화염(원래 피해 100%). 대공·잔류 화염과 조합됩니다.'
    by[185]['effect'].update(qa_revision=2026111502, cone_flame_visual=True, residual_cone_synergy_ordinal=52)
    catalog['economy_refresh_revision'] = REVISION
    return catalog
