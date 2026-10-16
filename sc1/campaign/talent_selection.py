"""Choose new talent offers without changing catalog items or saved offers."""
from __future__ import annotations

from . import progression
from .runtime_catalog import GrowthError


# Turrets, tank modes and carried ammunition belong to their parent troop.
# Heroes deliberately retain their own unit IDs: normal troop effects do not
# become hero effects merely because a mission happens to supply a hero.
_PARENT_UNITS = {4: 3, 6: 5, 30: 5, 31: 5, 85: 83, 73: 72}


def _families(item):
    declared = item.get("offer_family")
    if isinstance(declared, str) and declared:
        return frozenset({("declared", declared)})
    targets = item.get("target_units", ())
    families = frozenset(("unit", _PARENT_UNITS.get(unit, unit)) for unit in targets)
    # Unknown targets must not make otherwise unrelated custom talents one
    # family. Validated runtime items have stable IDs.
    return families or frozenset({("item", item["id"])})


def select_candidates(eligible, mission, rng, count=4):
    """Prefer usable troops, then fresh troop families, with normal rarity odds.

    Diversity is a preference within the currently usable pool. A squad with
    only one available troop can still fill every slot from that troop, and
    other campaign troops fill slots once its usable talents are exhausted.
    The input list and its catalog items are never modified.
    """
    if type(count) is not int or count < 0:
        raise ValueError("Candidate count must be a nonnegative integer")
    remaining = list(eligible)
    if len(remaining) < count:
        raise GrowthError("choice_pool_unavailable", "현재 단계의 구현된 성장 후보가 부족합니다.")
    weights = progression.rarity_weights(mission)
    selected = []
    seen = set()
    for _ in range(count):
        active = progression.prefer_active_targets(remaining, mission)
        fresh = [item for item in active if not (_families(item) & seen)]
        pool = fresh or active
        tiers = [tier for tier in weights if any(item["rarity"] == tier for item in pool)]
        tier = rng.choices(tiers, weights=[weights[tier] for tier in tiers], k=1)[0]
        candidate = rng.choice([item for item in pool if item["rarity"] == tier])
        selected.append(candidate)
        seen.update(_families(candidate))
        remaining.remove(candidate)
    return selected
