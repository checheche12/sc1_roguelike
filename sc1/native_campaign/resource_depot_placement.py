"""Preserve resource-clear depot placements on the complete 32-pixel grid.

This is an offline resource-exclusion check, not a native can-build query.
The reference is OpenBW's reconstructed can_place_building implementation,
commit 4b046d5f65302b10cb0a745f0fecd37ec85b20a8, bwgame.h:2567-2571.
Each footprint tile queries resource collision bounds in a rectangle expanded
three tiles in every direction.  A 4x3 depot therefore queries the half-open
rectangle [left-96, top-96, left+128+96, top+96+96).

Checking new_forbidden <= old_forbidden across ALL on-map top-left tiles is
stronger than filtering by terrain, creep, occupancy, visibility or resources
available to the player. Those independent requirements cannot turn a formerly
resource-clear placement into a newly resource-blocked one under this rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import struct

DEPOT_TYPES = (106, 131, 154)
RESOURCE_FLAG = 0x2000
RULE_VERSION = "openbw_resource_bounds_grid_subset_v1"
SOURCE_COMMIT = "4b046d5f65302b10cb0a745f0fecd37ec85b20a8"
SOURCE_URL = f"https://github.com/OpenBW/openbw/blob/{SOURCE_COMMIT}/bwgame.h#L2567-L2571"
SOURCE_SHA256 = "5ee316ca2c008c9252f7fde7444ca5dc7f35440549be2576dc37fa228fb31ae6"


@lru_cache(maxsize=1)
def _stock_geometry():
    try:
        from .build_managed_dat import legacy_fields, source_bytes
    except ImportError:
        from build_managed_dat import legacy_fields, source_bytes
    raw = source_bytes("units")
    fields = legacy_fields("units", raw)
    flags = struct.unpack("<228I", fields[22][1])
    sizes = tuple(struct.unpack_from("<2H", fields[36][1], unit * 4) for unit in range(228))
    bounds = tuple(struct.unpack_from("<4H", fields[38][1], unit * 8) for unit in range(228))
    resources = frozenset(unit for unit, value in enumerate(flags) if value & RESOURCE_FLAG)
    if any(sizes[unit] != (128, 96) for unit in DEPOT_TYPES):
        raise ValueError("Unexpected stock resource depot placement dimensions")
    return resources, sizes, bounds, hashlib.sha256(raw).hexdigest()


def resource_type_ids():
    """Use the source DAT resource flag, including refineries and unused types."""
    return _stock_geometry()[0]


def rule_evidence():
    resources, sizes, _, dat_sha = _stock_geometry()
    return {"algorithm": RULE_VERSION, "source_url": SOURCE_URL,
            "source_commit": SOURCE_COMMIT, "source_file_sha256": SOURCE_SHA256,
            "units_dat_sha256": dat_sha, "resource_flag_field": 22,
            "resource_flag_mask": RESOURCE_FLAG, "collision_field": 38,
            "placement_size_field": 36, "resource_unit_ids": sorted(resources),
            "depot_unit_ids": list(DEPOT_TYPES),
            "depot_placement_pixels": [list(sizes[unit]) for unit in DEPOT_TYPES],
            "grid_pixels": 32, "resource_clearance_pixels": 96,
            "terrain_filter_used": False, "native_can_build_verified": False}


@lru_cache(maxsize=32768)
def _resource_tiles(x, y, unit, depot_type, map_size):
    resources, sizes, bounds, _ = _stock_geometry()
    if unit not in resources:
        return frozenset()
    if depot_type not in DEPOT_TYPES:
        raise ValueError("Only Command Center, Hatchery and Nexus are audited")
    width, height = sizes[depot_type]
    left, top, right, bottom = bounds[unit]
    # Finder bounds have inclusive resource maxima and an exclusive query end.
    # For example, a resource whose left edge exactly equals the expanded
    # depot's right edge is outside; a right edge equal to the query left is in.
    x1 = (x - left - width - 96) // 32 + 1
    x2 = (x + right + 96) // 32
    y1 = (y - top - height - 96) // 32 + 1
    y2 = (y + bottom + 96) // 32
    if map_size is not None:
        map_width, map_height = map_size
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(map_width - width // 32, x2), min(map_height - height // 32, y2)
    return frozenset((tx, ty) for ty in range(y1, y2 + 1) for tx in range(x1, x2 + 1))


def resource_forbidden_tiles(info, depot_type=106, map_size=None):
    """Return forbidden (tile_x,tile_y) DEPOT TOP-LEFT positions.

    ``info`` contains (center_x, center_y, unit_id, owner) records. ``map_size``
    is optional (width,height) in 32-pixel tiles, not pixels. Omitting it also
    compares off-map positions and is consequently more restrictive.
    """
    size = tuple(map_size) if map_size is not None else None
    result = set()
    for x, y, unit, _ in info:
        result.update(_resource_tiles(x, y, unit, depot_type, size))
    return frozenset(result)


def newly_blocked_depot_tiles(before, after, depot_type=106, map_size=None):
    """Resource-clear before, resource-forbidden after; top-left tile coords."""
    return sorted(resource_forbidden_tiles(after, depot_type, map_size)
                  - resource_forbidden_tiles(before, depot_type, map_size))


# Name the property being checked explicitly for callers preparing audits.
lost_resource_depot_tiles = newly_blocked_depot_tiles


@dataclass(frozen=True)
class ResourceDepotGuard:
    before: tuple
    map_size: tuple
    forbidden: frozenset
    resource_indices: tuple

    def check(self, after, indices=None):
        """Check only changed resources against the original global envelope."""
        resources = resource_type_ids()
        after = tuple(map(tuple, after))
        if len(after) != len(self.before):
            raise ValueError("Depot guard requires identical UNIT record counts")
        if tuple(i for i, row in enumerate(after) if row[2] in resources) != self.resource_indices:
            raise ValueError("Depot guard resource identity set changed")
        changed = [i for i in self.resource_indices if self.before[i] != after[i]]
        if any(self.before[i][2:] != after[i][2:] for i in changed):
            raise ValueError("Depot guard resource type or owner changed")
        # The optional hint is validated, so a caller cannot omit a moved patch.
        if indices is not None and not set(changed) <= set(indices):
            raise ValueError("Depot guard change indices omitted a resource")
        new_tiles = set()
        for i in changed:
            x, y, unit, _ = after[i]
            new_tiles.update(_resource_tiles(x, y, unit, DEPOT_TYPES[0], self.map_size))
        lost = sorted(new_tiles - self.forbidden)
        proof = {"algorithm": RULE_VERSION, "checked_depot_unit_ids": list(DEPOT_TYPES),
                 "depot_placement_pixels": [128, 96], "grid_pixels": 32,
                 "changed_resource_count": len(changed),
                 "original_resource_forbidden_tiles": len(self.forbidden),
                 "new_resource_forbidden_tiles_checked": len(new_tiles),
                 "newly_blocked_tile_count": len(lost),
                 "newly_blocked_tile_samples": [list(p) for p in lost[:12]],
                 "all_original_resource_clear_grid_positions_preserved": not lost,
                 "terrain_independent_subset_check": True,
                 "native_can_build_verified": False}
        return not lost, proof


def prepare_guard(chk, before):
    """Prepare once per map; no terrain/creep or mutable game access required."""
    map_size = struct.unpack("<HH", chk.getsection("DIM "))
    before = tuple(map(tuple, before))
    resources = resource_type_ids()
    return ResourceDepotGuard(before, map_size,
                              resource_forbidden_tiles(before, DEPOT_TYPES[0], map_size),
                              tuple(i for i, row in enumerate(before) if row[2] in resources))


def preserves_depot_build_positions(chk, before, after, indices=None, *unused):
    """Convenience wrapper returning (accepted, proof); cache with prepare_guard."""
    return prepare_guard(chk, before).check(after, indices)
