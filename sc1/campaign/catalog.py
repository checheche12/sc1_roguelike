"""Explicit mission IDs and record profiles supported by the current maps.

These IDs are wire identifiers, not completion-bit positions. Adding future
missions requires an intentional catalog entry; arbitrary IDs are rejected.
"""
from dataclasses import dataclass
from types import MappingProxyType
from .missions import load_missions


PROBE_PROFILE = "probe"
ORIGINAL_PROFILE = "original"
PROFILE_NAMES = (PROBE_PROFILE, ORIGINAL_PROFILE)


@dataclass(frozen=True)
class Mission:
    mission_id: int
    profile: str
    completion_bit: int
    reward: int
    label: str
    allow_completed_replay: bool = False
    required_mask: int = 0

    @property
    def completion_mask(self) -> int:
        return 1 << self.completion_bit


MISSIONS = MappingProxyType({
    1: Mission(1, PROBE_PROFILE, 0, 123, "시험 A"),
    2: Mission(2, PROBE_PROFILE, 1, 0, "시험 B", required_mask=1),
    **{m["mission_id"]: Mission(m["mission_id"], ORIGINAL_PROFILE, m["completion_bit"], 0,
        m.get("label", m.get("name", str(m["mission_id"]))), allow_completed_replay=True,
        required_mask=m["required_mask"]) for m in load_missions()},
})


def missions_for_profile(profile: str) -> tuple[Mission, ...]:
    return tuple(mission for mission in MISSIONS.values() if mission.profile == profile)
