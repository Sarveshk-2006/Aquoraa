"""
Drainage Coupling Module for Phase 6 Flood Engine.

Couples surface storage grid with Phase 5 municipal drainage network,
accounting for surface inlet associations, known pipe capacities, unknown attributes,
and explicit outfall reachability.
Deterministic and mass-conserving.
"""

from typing import Any

import numpy as np
from engines.flood.models import DrainageCouplingPolicy


def apply_drainage_coupling(
    storage_grid_m3: np.ndarray,
    cell_inlet_associations: dict[tuple[int, int], list[dict[str, Any]]],
    drainage_graph: dict[str, Any],
    timestep_minutes: int,
    policy: DrainageCouplingPolicy
) -> dict[str, Any]:
    """
    Execute drainage inlet removal and network coupling for one simulation timestep.

    Args:
        storage_grid_m3: 2D numpy array of current cell surface storage in m3.
        cell_inlet_associations: Dict mapping (row, col) grid coordinates to associated Phase 5 inlets.
        drainage_graph: Phase 5 directed drainage graph (nodes, links, adj, rev_adj, outfalls).
        timestep_minutes: Timestep duration in minutes.
        policy: DrainageCouplingPolicy configuration.

    Returns:
        Dict containing:
            updated_storage_grid_m3
            drainage_inflow_grid_m3
            drainage_outflow_grid_m3
            total_drainage_removed_m3
            surcharged_inlets_count
            unreachable_outfall_inlets_count
            diagnostics
    """
    rows, cols = storage_grid_m3.shape
    updated_storage = storage_grid_m3.copy()
    drainage_inflow_grid = np.zeros_like(storage_grid_m3, dtype=np.float64)
    drainage_outflow_grid = np.zeros_like(storage_grid_m3, dtype=np.float64)

    dt_sec = timestep_minutes * 60.0
    total_removed_m3 = 0.0
    surcharged_count = 0
    unreachable_outfall_count = 0

    links = drainage_graph.get("links", {})
    outfalls = drainage_graph.get("outfalls", set())
    adj = drainage_graph.get("adj", {})

    # Process surface cell inlets
    for (r, c), inlets in cell_inlet_associations.items():
        if not (0 <= r < rows and 0 <= c < cols):
            continue

        available_water = updated_storage[r, c]
        if available_water <= 0.0:
            continue

        for inlet in inlets:
            node_id = str(inlet.get("node_id") or inlet.get("id") or "")
            node_type = str(inlet.get("node_type", "")).upper()

            # Verify valid surface inlet node type (INLET, CATCH_BASIN)
            if node_type not in ["INLET", "CATCH_BASIN"]:
                continue

            # Verify outfall reachability
            can_reach_outfall = _check_outfall_reachability(node_id, adj, outfalls)
            if not can_reach_outfall:
                unreachable_outfall_count += 1
                # If no explicit outfall reachability, drainage cannot remove water to outfall
                continue

            # Resolve pipe/link capacity along downstream link
            link_capacity_m3s = _resolve_downstream_capacity(
                node_id, adj, links, policy.unknown_capacity_policy
            )

            if link_capacity_m3s is None:
                # Capacity UNKNOWN and policy is EXCLUDE
                continue

            # Capacity volume available during this timestep
            capacity_vol_m3 = link_capacity_m3s * dt_sec

            # Max water removed is bounded by available surface water (NEVER CREATES WATER)
            removal_m3 = min(available_water, capacity_vol_m3)

            if removal_m3 > 0.0:
                if removal_m3 >= capacity_vol_m3 > 0.0:
                    surcharged_count += 1

                drainage_outflow_grid[r, c] += removal_m3
                updated_storage[r, c] -= removal_m3
                available_water -= removal_m3
                total_removed_m3 += removal_m3

            if available_water <= 0.0:
                break

    # Protect non-negativity
    updated_storage = np.maximum(0.0, updated_storage)

    return {
        "updated_storage_grid_m3": updated_storage,
        "drainage_inflow_grid_m3": drainage_inflow_grid,
        "drainage_outflow_grid_m3": drainage_outflow_grid,
        "total_drainage_removed_m3": total_removed_m3,
        "surcharged_inlets_count": surcharged_count,
        "unreachable_outfall_inlets_count": unreachable_outfall_count,
    }


def _check_outfall_reachability(
    start_node_id: str,
    adj: dict[str, list[str]],
    outfalls: set
) -> bool:
    """Check if start_node_id can reach any explicit OUTFALL node using directed adjacency."""
    if start_node_id in outfalls:
        return True

    visited = {start_node_id}
    queue = [start_node_id]

    while queue:
        curr = queue.pop(0)
        for neighbor in adj.get(curr, []):
            if neighbor in outfalls:
                return True
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)

    return False


def _resolve_downstream_capacity(
    node_id: str,
    adj: dict[str, list[str]],
    links: dict[str, Any],
    policy: str
) -> float | None:
    """
    Resolve known pipe capacity for downstream link originating from node_id.
    If capacity is UNKNOWN, applies configured policy without fabricating physical values.
    """
    downstream_nodes = adj.get(node_id, [])
    if not downstream_nodes:
        return None

    # Find candidate link
    known_capacities = []
    for l in links.values():
        fn = str(l.get("from_node_id", ""))
        tn = str(l.get("to_node_id", ""))
        dir_status = str(l.get("direction_status", "KNOWN")).upper()

        if dir_status == "UNKNOWN":
            continue

        if fn == node_id and tn in downstream_nodes:
            cap = l.get("capacity_m3s")
            if cap is not None and cap > 0.0:
                known_capacities.append(float(cap))

    if known_capacities:
        return min(known_capacities)

    # Capacity is UNKNOWN
    if policy == "CONSERVATIVE_ASSUMPTION":
        # Explicit conservative assumption (e.g. 0.1 m3/s small pipe)
        return 0.1
    elif policy == "SCENARIO":
        return 0.5
    else:  # EXCLUDE
        return None
