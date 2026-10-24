"""User-requested Creep March extension; frozen input documents stay untouched."""
REVISION = 2026102492
DESCRIPTION = ('점막 위 저그 지상 병력(드론 제외): 이속 +50%, 공속 +25%. '
               '아군 해처리·콜로니에 연결된 점막이 3초마다 한 겹씩 확장됩니다.')

def decorate(catalog):
    item = next(t for t in catalog['talents'] if t.get('effect_ordinal') == 75)
    item['description'] = DESCRIPTION
    item['description_revision'] = REVISION
    item['effect'].update(qa_revision=REVISION,creep_move_multiplier=1.5,
                         creep_attack_speed_multiplier=1.25,creep_attack_interval_multiplier=0.8,
                         creep_spread_interval_frames=72,creep_spread_frontier_layers=1,
                         creep_spread_from_owned_completed_providers=True,creep_excluded_units=[41])
