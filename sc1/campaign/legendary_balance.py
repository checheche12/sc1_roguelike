"""Bounded battlefield effects for the less expressive legendary cards."""
def decorate(catalog):
    notes = {
        64: ('야마토 3발이 각각 200% 피해를 줍니다. 총 에너지 75. 추가탄은 4타일 안 다른 적을 우선하며 부족하면 주 대상에 집중합니다. 탄착지 3타일 안 다른 적 최대 6기에 기본 야마토의 50% 폭발 피해. 직접 피격 대상 제외, 중복 폭발 없음.',
             {'blast_radius_pixels': 96, 'blast_targets_per_cast': 6, 'blast_native_damage_percent': 50}),
        103: ('다크 스웜이 아군 공중 유닛도 보호하고 범위가 최소 10타일로 늘어납니다. 안의 아군 전투 병력은 초당 최대 체력 1% 회복. 겹친 군체 회복은 중복되지 않으며 마법·광역 예외는 유지됩니다.',
              {'swarm_max_hp_regen_percent_per_second': 1, 'overlapping_regen_stacks': False}),
        147: ('환영의 일반 공격이 원래 피해의 100%를 실제로 줍니다. 환영 소멸 시 3타일 안 적 최대 4기에 환영 최대 체력의 25%(최대 100) 폭발 피해를 줍니다.',
              {'death_blast_radius_pixels': 96, 'death_blast_targets': 4, 'death_blast_max_hp_percent': 25, 'death_blast_damage_cap': 100}),
        149: ('스테이시스 해제 시 갇혔던 적에게 보호막 400과 체력 300 + 최대 체력 25% 피해. 폭발 주변 3타일 안 적 최대 6기는 3초간 이동 속도가 50% 감소합니다.',
              {'release_slow_radius_pixels': 96, 'release_slow_targets': 6, 'release_slow_percent': 50, 'release_slow_frames': 72}),
    }
    for item in catalog['talents']:
        ordinal=item.get('effect_ordinal')
        if item.get('rework_revision')!=5 or ordinal not in notes:continue
        text,effect=notes[ordinal]
        item['description']=text
        item['effect'].update(effect,qa_revision=2026101926)
    return catalog
