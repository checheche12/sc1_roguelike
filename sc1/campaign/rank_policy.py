"""Stable v2 rank slots and the QA10 combat cap; never rewrite old ranks."""
MAX_RANK=4
MANUAL_ORDINALS=(8,9,11,12,29,30,31,70,71,72,111,112)
HEALTH_ORDINALS=(26,27,28,67,68,69,108,109,110)
RANK_SLOTS={ordinal:slot for slot,ordinal in enumerate(MANUAL_ORDINALS+HEALTH_ORDINALS)}

def effective(item,count=1):
    return min(count,item.get('max_rank',0xffffffff)) if item.get('repeatable') else 1

def exhausted(item,owned,ranks):
    return (item['id'] in owned and (not item.get('repeatable') or
        ranks.get(item['id'],1)>=item.get('max_rank',0xffffffff)))
