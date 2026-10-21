"""Explain mission access using only the caller's committed completion mask."""
import re
from .missions import load_missions

CAMPAIGNS = {1: '본편 테란', 2: '본편 저그', 3: '본편 프로토스',
             4: '브루드워 프로토스', 5: '브루드워 테란', 6: '브루드워 저그'}


def mission_name(row):
    for objective in row.get('original_objectives', ()):
        title = re.search('["“]([^"”]+)["”]', objective.splitlines()[0])
        if title:
            return f"{row['ordinal']}번 {title.group(1)}"
    return row.get('label', str(row['mission_id']))


def locked_progress(mission, completed_mask):
    rows = load_missions()
    requested = next(row for row in rows if row['mission_id'] == mission)
    campaign = sorted((row for row in rows if row['campaign_id'] == requested['campaign_id']
                       and row['shared_reward_mission_id'] == row['mission_id']), key=lambda row: row['ordinal'])
    done = [row for row in campaign if completed_mask & (1 << row['completion_bit'])]
    missing = [row for row in campaign if requested['required_mask'] & (1 << row['completion_bit'])
               and not completed_mask & (1 << row['completion_bit'])]
    available = [row for row in campaign if row not in done
                 and completed_mask & row['required_mask'] == row['required_mask']]
    entry = lambda row: {'mission_id': row['mission_id'], 'name': mission_name(row)}
    result = dict(campaign=CAMPAIGNS[requested['campaign_id']], requested=entry(requested),
                  completed_count=len(done), total_count=len(campaign),
                  last_completed=entry(done[-1]) if done else None,
                  missing_prerequisites=[entry(row) for row in missing], next_missions=[entry(row) for row in available])
    last = result['last_completed']['name'] if done else '없음'
    next_names = ' / '.join(row['name'] for row in result['next_missions']) or '없음'
    missing_names = ', '.join(row['name'] for row in result['missing_prerequisites']) or '없음'
    result['message'] = (f"선행 임무 미완료: {missing_names}\n"
                         f"현재 기록: {result['campaign']} {len(done)}/{len(campaign)}개 완료. 마지막 완료: {last}\n"
                         f"이어서 진행: {next_names}\n이미 플레이했다면 기존 진행 기록을 열고 임무를 다시 시작하세요.")
    short = lambda text: text if len(text) <= 16 else text[:15] + '…'
    first_missing = short(result['missing_prerequisites'][0]['name']) if missing else '이전 임무'
    more = f" 외 {len(missing)-1}개" if len(missing) > 1 else ''
    result['native_message'] = (f"선행 임무 미완료: {first_missing}{more}\n"
                                f"{result['campaign']} {len(done)}/{len(campaign)} 완료 · 마지막: {short(last)}\n"
                                f"다음: {short(result['next_missions'][0]['name']) if available else '없음'}")
    return result
