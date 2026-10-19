"""Runtime balance overrides; frozen workshop inputs and wire slots stay intact."""
REAR_ID = '09224f2f-b115-5c53-adb3-883bb36075cd'
RESERVE_ID = '9abf9771-866f-55b7-a4ba-ba28bb5e6faf'
QA_REVISION = 2026102038


def decorate(catalog):
    updates = {
        15: ('뮤탈리스크가 1/2/3중첩에 따라 2·6·10기씩 일꾼 근처에 직접 등장합니다. 최대 3중첩이며 증원량 증가가 적용됩니다.',
             {'units_formula': '2,6,10 (capped at3)', 'units_sequence': [2, 6, 10]}),
        16: ('추가 공세 병력 수가 선택할 때마다 기본 편성 대비 +20%, +24%, +28%…씩 누적 증가합니다. 중첩 상한 없음. 1/2/3중첩 누적 +20/+44/+72%.',
             {'first_increment_percent': 20, 'increment_step_percent': 4, 'unlimited_stacks': True}),
        17: ('추가 공세 병력의 일반 공격력이 선택할 때마다 기본 공격력 대비 +15%, +19%, +23%…씩 누적 증가합니다. 중첩 상한 없음. 1/2/3중첩 누적 +15/+34/+57%.',
             {'first_increment_percent': 15, 'increment_step_percent': 4, 'unlimited_stacks': True}),
        18: ('추가 공세 병력의 최대 체력과 최대 보호막이 선택할 때마다 각각 기본 수치 대비 +20%, +24%, +28%…씩 누적 증가합니다. 중첩 상한 없음. 1/2/3중첩 누적 각각 +20/+44/+72%.',
             {'first_increment_percent': 20, 'increment_step_percent': 4, 'unlimited_stacks': True,
              'health_and_shields': True}),
        19: ('추가 공세 병력의 일반 공격 속도와 이동 속도가 선택할 때마다 각각 기본 속도 대비 +15%, +16%, +17%…씩 누적 증가합니다. 중첩 상한 없음. 1/2/3중첩 누적 각각 +15/+31/+48%. 마법 시전 속도는 바뀌지 않습니다.',
             {'first_increment_percent': 15, 'increment_step_percent': 1, 'unlimited_stacks': True,
              'attack_and_movement_speed': True}),
        20: ('원래 적 전투 유닛을 20기 잡으면 인구 9의 지원군이 옵니다. 추가 중첩마다 인구 +4, 재사용 60초.',
             {'supply_base': 9, 'supply_per_extra_stack': 4}),
        21: ('공세마다 중첩당 정예 1기: 최대 체력 +60%·일반 공격력 +25%. 최대 3중첩.',
             {'elite_hp_percent': 160, 'elite_attack_percent': 125}),
        22: ('공세 선두 4기가 20초간 일반 공격 피해를 28% 덜 받습니다. 추가 중첩마다 2기 추가, 최대 8기.',
             {'damage_reduction_percent': 28}),
        23: ('추가 공세 병력이 일반 공격으로 준 실제 체력 피해의 12%/중첩을 회복합니다. 최대 2중첩.',
             {'lifesteal_percent_per_stack': 12}),
        24: ('삭제된 저주입니다. 새 선택지에 등장하지 않으며 기존 획득 기록의 효과도 비활성화됩니다.',
             {'retired': True, 'runtime_disabled': True}),
        25: ('삭제된 저주입니다. 새 선택지에 등장하지 않으며 기존 획득 기록의 효과도 비활성화됩니다.',
             {'retired': True, 'runtime_disabled': True}),
    }
    for item in catalog['curses']:
        slot = item['byte_index']
        if item.get('rework_revision') != 5:
            continue
        effect = item['effect']
        if slot in updates:
            description, values = updates[slot]
            item['description'] = description
            effect.update(values)
            if slot == 15:
                # Historic higher counts remain valid history; new picks stop at3.
                item['choice_max_stacks'] = 3
            elif slot in (16, 17, 18, 19):
                item['max_stacks'] = 0xffffffff
                if slot == 19:
                    item['rarity'] = 'common'
                    effect.pop('speed_percent_per_stack', None)
        elif slot >= 26:
            note = ' 이 편성 전체의 최대 체력이 기존보다 10% 증가합니다.'
            if not item['description'].endswith(note):
                item['description'] += note
            effect['roster_hp_percent'] = 110
        effect['qa_revision'] = QA_REVISION
        if slot == 18:
            effect['qa_revision'] = QA_REVISION
    return catalog
