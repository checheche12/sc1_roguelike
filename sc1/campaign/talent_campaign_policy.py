"""Pure revision-five policy, used when wire-v2 issues a new persisted offer.

The runtime may apply this policy only while issuing a new offer. An offer
whose candidates are already stored, every historical catalog entry, and
every frozen loadout retain their original meaning.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil

from . import progression
from .missions import load_missions


REVISION = 5
AWARDS_PER_MISSION = 3
ECONOMY_AWARDS_PER_CAMPAIGN = 5
ECONOMY_PHASE = 2
ORDINARY_LEGENDARY_PER_10000 = 100
RARITY_WEIGHTS = {"common": 40, "uncommon": 29, "rare": 25,
                  "epic": 5, "legendary": 1}
RARITY_ORDER = tuple(RARITY_WEIGHTS)
RECENT_MANUAL_REWARDS = 3
RECENT_MANUAL_WEIGHT = 95
NORMAL_CANDIDATE_WEIGHT = 100

# These are logical ordinals, never scenario IDs. Branch variants therefore
# receive the same category without creating an additional reward entitlement.
# Every selected mission supports production. Final missions are avoided so
# an economic reward has time to contribute to the remaining campaign.
# BW Terran has only five non-final production missions: ordinal 1 is needed.
ECONOMY_ORDINALS = {
    1: (2, 3, 5, 7, 9),
    2: (2, 4, 6, 8, 9),
    3: (2, 4, 5, 7, 9),
    4: (2, 3, 4, 6, 7),
    5: (1, 3, 4, 5, 6),
    6: (2, 4, 6, 8, 9),
}


@dataclass(frozen=True)
class RewardPolicy:
    campaign_id: int
    ordinal: int
    phase: int
    category: str
    guaranteed_legendary: bool
    ordinary_legendary_per_10000: int
    policy_revision: int = REVISION


def logical_mission_count(mission: int) -> int:
    """Count distinct campaign ordinals, including only one of each branch."""
    campaign = progression.metadata(mission)["campaign_id"]
    return len({row["ordinal"] for row in load_missions()
                if row["campaign_id"] == campaign})


def legendary_ordinal(mission: int) -> int | None:
    """The first mission of each main campaign; the secret stays separate."""
    entry = progression.metadata(mission)
    if entry["campaign_id"] not in ECONOMY_ORDINALS:
        return None
    return 1


def midpoint_legendary_ordinal(mission: int) -> int | None:
    """First logical mission beyond halfway; branches share one entitlement."""
    if progression.metadata(mission)['campaign_id'] not in ECONOMY_ORDINALS:
        return None
    return logical_mission_count(mission) // 2 + 1


def progress_band(mission: int) -> int:
    """0/1/2 for logical campaign thirds; branch assets do not advance time."""
    ordinal = progression.metadata(mission)["ordinal"]
    return min(2, (ordinal - 1) * 3 // logical_mission_count(mission))


def rarity_weights() -> dict[str, int]:
    """Base weights for EACH ordinary military slot, at every campaign stage."""
    return dict(RARITY_WEIGHTS)


def rolled_rarity(roll: int) -> str:
    if type(roll) is not int or not 0 <= roll < 100:
        raise ValueError("A rarity roll must be an integer from 0 through 99")
    boundary = 0
    for rarity, weight in RARITY_WEIGHTS.items():
        boundary += weight
        if roll < boundary:
            return rarity
    raise AssertionError("Rarity weights must sum to 100")


def repeatable(rarity: str, category: str) -> bool:
    """All common military manuals remain eligible after acquisition."""
    return rarity == "common" and category in ("combat", "military")


def firepower_cooldown(base_ticks: int, stacks: int) -> float:
    """Ideal 3% multiplicative period, with a one-tick engine floor.

    Keep the fraction: rounding every 15-tick Marine attack up would erase
    the first 3% rank. The engine adapter must carry fractional ticks.
    """
    if type(base_ticks) is not int or base_ticks < 1:
        raise ValueError("Base cooldown must be a positive integer")
    if type(stacks) is not int or stacks < 0:
        raise ValueError("Stacks must be a nonnegative integer")
    return max(1.0, base_ticks * .97 ** stacks)


def firepower_intervals(base_ticks: int, stacks: int, attacks: int) -> tuple[int, ...]:
    """Reference fractional carry; cumulative timing error stays below 1 tick."""
    period = firepower_cooldown(base_ticks, stacks)
    if type(attacks) is not int or attacks < 0:
        raise ValueError("Attack count must be a nonnegative integer")
    deadlines = [ceil(i * period) for i in range(attacks + 1)]
    return tuple(right - left for left, right in zip(deadlines, deadlines[1:]))


@dataclass(frozen=True)
class Candidate:
    id: str
    rarity: str
    category: str = "military"
    usable: bool = True
    repeatable: bool | None = None


def draw_candidates(policy: RewardPolicy, catalog, owned, rng, limit: int = 4,
                    *, midpoint_pending: bool = False,
                    recent_manuals=(), exhausted_fallback=False) -> tuple[Candidate, ...]:
    """Pure offer sampler. Persist its result once; never redraw issued offers.

    Common manuals may repeat across rewards, but never within one offer.
    Other owned kinds are excluded. A depleted tier falls downward rather
    than promoting a common roll to rare/epic. Common alone may fall back to
    uncommon if its usable pool is empty. If no such pool remains, an offer
    is shorter. Economy draws uniformly from unowned economic candidates.
    The opening reward shows up to four distinct usable unowned legendaries.
    """
    if type(limit) is not int or limit < 1:
        raise ValueError("An offer must have a positive integer candidate count")
    catalog = tuple(catalog)
    if len({x.id for x in catalog}) != len(catalog):
        raise ValueError("Candidate IDs must be unique")
    if any(x.rarity not in RARITY_WEIGHTS for x in catalog):
        raise ValueError("Unknown rarity")
    if any(x.category not in ("combat", "military", "economy") for x in catalog):
        raise ValueError("Only military and economy cards belong in reward offers")
    owned = set(owned)
    recent_manuals = set(recent_manuals)
    pool = [x for x in catalog if x.usable
            and ((x.category == "economy") == (policy.category == "economy"))
            and (x.id not in owned or (repeatable(x.rarity, x.category) if x.repeatable is None else x.repeatable))]
    if policy.guaranteed_legendary:
        legends = [x for x in pool if x.rarity == "legendary" and x.id not in owned]
        if not legends:
            raise ValueError("Guaranteed reward requires an unowned usable legendary")
        result = []
        for _ in range(min(limit, len(legends))):
            result.append(legends.pop(rng.randrange(len(legends))))
        return tuple(result)
    if midpoint_pending:
        legends = sorted((x for x in pool if x.rarity == "legendary"), key=lambda x: x.id)
        for reserved in legends[-limit:]:
            pool.remove(reserved)
    result = []
    for _ in range(limit):
        if policy.category == "economy":
            choices = pool
        else:
            rarity = rolled_rarity(rng.randrange(100))
            index = RARITY_ORDER.index(rarity)
            fallback = RARITY_ORDER[index::-1] if index else ("common", "uncommon")
            choices = []
            for tier in fallback:
                choices = [x for x in pool if x.rarity == tier]
                if choices:
                    break
        if not choices:
            continue
        # A displayed common manual has 95% of its normal sampling weight for
        # three later talent rewards. The rarity roll and owned effects stay
        # exact. No redraw of stored offers, cumulative penalty or hard cap.
        weights = [RECENT_MANUAL_WEIGHT if x.id in recent_manuals
                   and repeatable(x.rarity, x.category)
                   else NORMAL_CANDIDATE_WEIGHT for x in choices]
        if len(set(weights)) == 1:
            choice = choices[rng.randrange(len(choices))]
        else:
            roll = rng.randrange(sum(weights))
            for candidate, weight in zip(choices, weights):
                if roll < weight:
                    choice = candidate
                    break
                roll -= weight
        result.append(choice)
        pool.remove(choice)
    if not result and exhausted_fallback:
        # QA10 capped pools need one reachable entitlement when every rolled
        # tier is exhausted. Never promote the remaining slots of a nonempty
        # normal offer. Midpoint-reserved legends were removed above.
        for _ in range(min(limit,len(pool))):result.append(pool.pop(rng.randrange(len(pool))))
    return tuple(result)


def reward_policy(mission: int, phase: int) -> RewardPolicy:
    if type(phase) is not int or phase not in (1, 2, 3):
        raise ValueError("Reward phase must be an integer from 1 through 3")
    entry = progression.metadata(mission)
    campaign, ordinal = entry["campaign_id"], entry["ordinal"]
    economy = (phase == ECONOMY_PHASE
               and ordinal in ECONOMY_ORDINALS.get(campaign, ()))
    if economy and entry.get("no_production"):
        raise ValueError("An economic reward cannot be scheduled without production")
    guaranteed = (phase == 1 and ordinal in (legendary_ordinal(mission), midpoint_legendary_ordinal(mission)))
    return RewardPolicy(
        campaign, ordinal, phase, "economy" if economy else "military",
        guaranteed, 0 if economy or guaranteed else ORDINARY_LEGENDARY_PER_10000)


def legendary_candidate_count(policy: RewardPolicy, rng, candidates: int = 4) -> int:
    """Count base legendary rolls, before availability and duplicate filtering.

    Ordinary offers roll independently per slot (1% each); the guarantee
    presents four cards. Economy never uses military rarity rolls.
    """
    if type(candidates) is not int or candidates < 1:
        raise ValueError("An offer must have a positive integer candidate count")
    if policy.guaranteed_legendary:
        return candidates
    if not policy.ordinary_legendary_per_10000:
        return 0
    return sum(rng.randrange(10000) < policy.ordinary_legendary_per_10000
               for _ in range(candidates))


def campaign_schedule(mission: int) -> tuple[RewardPolicy, ...]:
    """One representative per logical mission, ordered by ordinal and phase."""
    campaign = progression.metadata(mission)["campaign_id"]
    representatives = {}
    for row in load_missions():
        if row["campaign_id"] == campaign:
            representatives.setdefault(row["ordinal"], row["mission_id"])
    return tuple(reward_policy(representatives[ordinal], phase)
                 for ordinal in sorted(representatives) for phase in (1, 2, 3)
                 if not (phase==3 and progression.metadata(representatives[ordinal])['final']))
