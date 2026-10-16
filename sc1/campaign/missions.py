"""Original campaign mission metadata, independent of player save data."""
from functools import lru_cache
import json
from pathlib import Path
PATH=Path(__file__).with_name('missions.json')
@lru_cache(maxsize=1)
def _load():
    data=json.loads(PATH.read_text(encoding='utf-8'))
    rows=data['missions'] if isinstance(data,dict) else data
    assert len({r['mission_id'] for r in rows})==len(rows)
    return rows

def load_missions():
    return [dict(row) for row in _load()]

def mission_for_id(mission_id):
    for row in _load():
        if row['mission_id']==int(mission_id):return dict(row)
    raise ValueError(f'Unsupported original campaign mission: {mission_id}')

def canonical_mission_id(mission_id):
    row=mission_for_id(mission_id)
    return row.get('shared_reward_mission_id',row['mission_id'])
