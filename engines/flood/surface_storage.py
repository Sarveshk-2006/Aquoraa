"""
Surface Storage Module for Phase 6 Flood Engine.

Manages cell-level surface water accumulation, depression storage thresholds,
and mobile surface water volume calculations.
"""



def update_surface_storage(
    current_storage_m3: float,
    runoff_volume_m3: float,
    depression_capacity_m3: float
) -> dict[str, float]:
    """
    Update cell surface water storage with new runoff volume and partition into
    trapped depression storage vs mobile surface water available for routing.

    Args:
        current_storage_m3: Previous surface storage volume in m3.
        runoff_volume_m3: New runoff volume added in current timestep in m3.
        depression_capacity_m3: Total depression storage threshold for the cell in m3.

    Returns:
        Dict containing:
            total_storage_m3
            depression_water_m3
            available_mobile_water_m3
    """
    current_storage_m3 = max(current_storage_m3, 0.0)
    runoff_volume_m3 = max(runoff_volume_m3, 0.0)
    depression_capacity_m3 = max(depression_capacity_m3, 0.0)

    total_storage = current_storage_m3 + runoff_volume_m3

    if total_storage <= depression_capacity_m3:
        depression_water = total_storage
        available_mobile_water = 0.0
    else:
        depression_water = depression_capacity_m3
        available_mobile_water = total_storage - depression_capacity_m3

    return {
        "total_storage_m3": total_storage,
        "depression_water_m3": depression_water,
        "available_mobile_water_m3": available_mobile_water,
    }
