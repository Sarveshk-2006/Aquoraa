"""
Terrain & Surface-Flow Processing Engine.

Provides pure deterministic geospatial functions for DEM validation, slope, aspect,
D8 flow direction, D8 flow accumulation, DEM-derived surface drainage proxy extraction,
and pour-point catchment delineation.

PHYSICS/GIS FIRST PRINCIPLE:
- Flow accumulation is NOT runoff or discharge.
- DEM-derived surface drainage proxy is NOT municipal drainage network.
- DEM-derived catchments are NOT municipal stormwater catchments.
- All metric calculations use projected metric Analysis CRS (horizontal distances in meters).
"""

from typing import Any

import numpy as np
import structlog
try:
    import rasterio
    from rasterio.features import shapes
    from rasterio.transform import Affine
except ImportError:
    class StubAffine:
        def __init__(self, *args, **kwargs):
            self.a, self.b, self.c = 1.0, 0.0, 0.0
            self.d, self.e, self.f = 0.0, -1.0, 0.0
        @classmethod
        def translation(cls, x, y): return StubAffine()
        @classmethod
        def scale(cls, x, y): return StubAffine()
        def __mul__(self, other): return (0.0, 0.0) if isinstance(other, (tuple, list)) else StubAffine()
        def __invert__(self): return StubAffine()
    Affine = StubAffine
    shapes = lambda *a, **k: []
    rasterio = None
from app.geospatial.validation import ensure_valid_polygon
from shapely.geometry import MultiPolygon, shape

logger = structlog.get_logger("aquora.geospatial.terrain")

# D8 Direction Encoding Rules (ESRI standard)
# 1: East (0, 1)
# 2: Southeast (1, 1)
# 4: South (1, 0)
# 8: Southwest (1, -1)
# 16: West (0, -1)
# 32: Northwest (-1, -1)
# 64: North (-1, 0)
# 128: Northeast (-1, 1)

D8_OFFSETS = [
    (0, 1, 1),       # East
    (1, 1, 2),       # Southeast
    (1, 0, 4),       # South
    (1, -1, 8),      # Southwest
    (0, -1, 16),     # West
    (-1, -1, 32),    # Northwest
    (-1, 0, 64),     # North
    (-1, 1, 128),    # Northeast
]


def validate_dem_array_and_metadata(
    elevation_array: np.ndarray,
    metadata: dict[str, Any]
) -> dict[str, Any]:
    """
    Validate DEM elevation array structure, dimensions, finite values, CRS, and vertical units.
    """
    if elevation_array.ndim != 2:
        raise ValueError(f"DEM elevation array must be 2D, got shape {elevation_array.shape}")
    
    height, width = elevation_array.shape
    if height == 0 or width == 0:
        raise ValueError("DEM elevation array cannot have zero dimensions")
    
    transform_raw = metadata.get("transform")
    if not transform_raw:
        raise ValueError("DEM metadata missing affine transform matrix")
    
    if isinstance(transform_raw, Affine):
        transform = transform_raw
    else:
        transform = Affine(*transform_raw[:6])
    
    dx = abs(transform.a)
    dy = abs(transform.e)
    if dx <= 0 or dy <= 0:
        raise ValueError(f"Invalid DEM resolution (dx={dx}, dy={dy})")
    
    crs = metadata.get("crs")
    if not crs:
        raise ValueError("DEM metadata missing CRS definition")
    
    vertical_units = metadata.get("vertical_units", "meters")
    nodata = metadata.get("nodata", -9999.0)
    
    valid_mask = np.isfinite(elevation_array)
    if nodata is not None:
        valid_mask &= (elevation_array != nodata)
    
    if not np.any(valid_mask):
        raise ValueError("DEM elevation array contains no valid finite elevation values")
    
    valid_elevations = elevation_array[valid_mask]
    min_elev = float(np.min(valid_elevations))
    max_elev = float(np.max(valid_elevations))
    
    return {
        "valid": True,
        "width": width,
        "height": height,
        "resolution_dx": dx,
        "resolution_dy": dy,
        "cell_area_m2": dx * dy,
        "crs": str(crs),
        "vertical_units": vertical_units,
        "min_elevation_m": min_elev,
        "max_elevation_m": max_elev,
        "nodata": nodata,
        "valid_cells_count": int(np.sum(valid_mask)),
        "total_cells_count": width * height,
    }


def calculate_slope(
    elevation_array: np.ndarray,
    transform: Affine | list | tuple,
    nodata: float | None = None
) -> np.ndarray:
    """
    Calculate terrain slope in degrees using 2nd order finite difference method.
    Requires transform resolution in projected metric distance (meters).
    Output non-negative slope in degrees [0, 90]. Nodata cells preserve nodata/NaN.
    """
    if not isinstance(transform, Affine):
        transform = Affine(*transform[:6])
    
    dx = abs(transform.a)
    dy = abs(transform.e)
    
    elev = elevation_array.astype(np.float64, copy=True)
    if nodata is not None:
        elev[elev == nodata] = np.nan
    
    # Calculate gradients using central differences
    fy, fx = np.gradient(elev, dy, dx)
    
    # Slope in radians: arctan(sqrt(fx^2 + fy^2))
    slope_rad = np.arctan(np.sqrt(fx**2 + fy**2))
    slope_deg = np.degrees(slope_rad)
    
    # Clean up nan / invalid values
    if nodata is not None:
        slope_deg[np.isnan(slope_deg)] = nodata
    
    return np.clip(slope_deg, 0.0, 90.0)


def calculate_aspect(
    elevation_array: np.ndarray,
    transform: Affine | list | tuple,
    nodata: float | None = None
) -> np.ndarray:
    """
    Calculate terrain aspect in degrees [0, 360°] clockwise from North.
    Flat terrain (gradient == 0) is assigned -1.0 (undefined aspect).
    Nodata cells preserve nodata.
    """
    if not isinstance(transform, Affine):
        transform = Affine(*transform[:6])
    
    dx = abs(transform.a)
    dy = abs(transform.e)
    
    elev = elevation_array.astype(np.float64, copy=True)
    if nodata is not None:
        elev[elev == nodata] = np.nan
    
    fy, fx = np.gradient(elev, dy, dx)
    
    # Aspect calculation in compass degrees:
    # 0 = North, 90 = East, 180 = South, 270 = West
    aspect_rad = np.arctan2(-fx, fy)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg[aspect_deg < 0] += 360.0
    
    # Handle flat areas where both gradients are 0
    flat_mask = (fx == 0) & (fy == 0)
    aspect_deg[flat_mask] = -1.0
    
    if nodata is not None:
        aspect_deg[np.isnan(elev)] = nodata
        
    return aspect_deg


def calculate_d8_flow_direction(
    elevation_array: np.ndarray,
    transform: Affine | list | tuple,
    nodata: float | None = None
) -> np.ndarray:
    """
    Calculate deterministic D8 downslope flow direction array.
    
    Uses metric horizontal distances:
    - Cardinal neighbor distance: dx or dy
    - Diagonal neighbor distance: sqrt(dx^2 + dy^2)
    
    Slope drop = (elev_center - elev_neighbor) / distance.
    Selects neighbor with maximum positive drop.
    If no positive drop exists (sink/flat), assigns 0 (SINK / NO_FLOW).
    """
    if not isinstance(transform, Affine):
        transform = Affine(*transform[:6])
    
    dx = abs(transform.a)
    dy = abs(transform.e)
    diag_dist = np.sqrt(dx**2 + dy**2)
    
    height, width = elevation_array.shape
    elev = elevation_array.astype(np.float64, copy=True)
    if nodata is not None:
        elev[elev == nodata] = np.nan
    
    flow_dir = np.zeros((height, width), dtype=np.uint8)
    
    # Distance lookup for 8 directions
    dist_lookup = [
        dx,         # 1: East
        diag_dist,  # 2: Southeast
        dy,         # 4: South
        diag_dist,  # 8: Southwest
        dx,         # 16: West
        diag_dist,  # 32: Northwest
        dy,         # 64: North
        diag_dist   # 128: Northeast
    ]
    
    max_drop = np.zeros((height, width), dtype=np.float64)
    
    for idx, (dr, dc, code) in enumerate(D8_OFFSETS):
        dist = dist_lookup[idx]
        
        # Calculate shifted neighbor slice bounds
        r_src_start = max(0, -dr)
        r_src_end = min(height, height - dr)
        c_src_start = max(0, -dc)
        c_src_end = min(width, width - dc)
        
        r_dst_start = max(0, dr)
        r_dst_end = min(height, height + dr)
        c_dst_start = max(0, dc)
        c_dst_end = min(width, width + dc)
        
        center_slice = elev[r_src_start:r_src_end, c_src_start:c_src_end]
        neighbor_slice = elev[r_dst_start:r_dst_end, c_dst_start:c_dst_end]
        
        drop = (center_slice - neighbor_slice) / dist
        
        # Valid drop mask: positive drop and non-NaN
        valid_drop = np.isfinite(drop) & (drop > max_drop[r_src_start:r_src_end, c_src_start:c_src_end])
        
        # Update flow direction and max drop deterministically
        dst_flow = flow_dir[r_src_start:r_src_end, c_src_start:c_src_end]
        dst_max = max_drop[r_src_start:r_src_end, c_src_start:c_src_end]
        
        dst_flow[valid_drop] = code
        dst_max[valid_drop] = drop[valid_drop]
    
    if nodata is not None:
        flow_dir[np.isnan(elev)] = 0
        
    return flow_dir


def calculate_d8_flow_accumulation(
    flow_dir: np.ndarray,
    nodata: float | None = None
) -> np.ndarray:
    """
    Calculate deterministic upstream D8 flow accumulation raster (cell counts).
    
    Returns array where each cell contains the number of upstream contributing cells
    (including itself). Monotonically increases along downstream flow paths.
    """
    height, width = flow_dir.shape
    in_degree = np.zeros((height, width), dtype=np.int32)
    
    # Calculate in-degree for each cell
    for r in range(height):
        for c in range(width):
            code = flow_dir[r, c]
            if code == 0:
                continue
            for dr, dc, d8_code in D8_OFFSETS:
                if code == d8_code:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        in_degree[nr, nc] += 1
                    break
    
    # Accumulation array initialized to 1 for all valid cells
    accumulation = np.ones((height, width), dtype=np.int32)
    if nodata is not None:
        accumulation[flow_dir == 0] = 0
    
    # Queue of cells with 0 in-degree (headwater ridge cells)
    queue = [(r, c) for r in range(height) for c in range(width) if in_degree[r, c] == 0 and flow_dir[r, c] != 0]
    
    head = 0
    while head < len(queue):
        r, c = queue[head]
        head += 1
        
        code = flow_dir[r, c]
        if code == 0:
            continue
            
        for dr, dc, d8_code in D8_OFFSETS:
            if code == d8_code:
                nr, nc = r + dr, c + dc
                if 0 <= nr < height and 0 <= nc < width:
                    accumulation[nr, nc] += accumulation[r, c]
                    in_degree[nr, nc] -= 1
                    if in_degree[nr, nc] == 0 and flow_dir[nr, nc] != 0:
                        queue.append((nr, nc))
                break
                
    return accumulation


def extract_surface_drainage_proxy(
    flow_accumulation: np.ndarray,
    cell_area_m2: float,
    threshold_area_m2: float
) -> np.ndarray:
    """
    Extract DEM-derived surface drainage proxy boolean raster based on physical threshold area in m2.
    
    Derived cell count threshold = ceil(threshold_area_m2 / cell_area_m2).
    EXPLICIT BOUNDARY: This is a terrain surface-flow proxy, NOT a municipal sewer pipe network.
    """
    if cell_area_m2 <= 0:
        raise ValueError(f"Invalid cell area {cell_area_m2} m2")
    if threshold_area_m2 <= 0:
        raise ValueError(f"Invalid threshold area {threshold_area_m2} m2")
        
    required_cells = int(np.ceil(threshold_area_m2 / cell_area_m2))
    return (flow_accumulation >= required_cells).astype(np.uint8)


def delineate_catchment(
    flow_dir: np.ndarray,
    transform: Affine | tuple | list,
    pour_point_xy: tuple[float, float],
    snap_tolerance_m: float = 100.0,
    flow_accumulation: np.ndarray | None = None,
    crs_str: str = "EPSG:32633"
) -> dict[str, Any]:
    """
    Delineate terrain catchment boundary from D8 flow direction and pour point coordinate.
    
    1. Maps pour point to raster cell grid.
    2. Snaps pour point within tolerance to cell of maximum flow accumulation if provided.
    3. Traverses D8 flow direction upstream to delineate contributing cell mask.
    4. Polygonizes raster mask and calculates metric catchment area in m2.
    """
    if not isinstance(transform, Affine):
        transform = Affine(*transform[:6])
    
    dx = abs(transform.a)
    dy = abs(transform.e)
    cell_area_m2 = dx * dy
    height, width = flow_dir.shape
    
    px, py = pour_point_xy
    inv_transform = ~transform
    col_float, row_float = inv_transform * (px, py)
    start_col, start_row = int(np.floor(col_float)), int(np.floor(row_float))
    
    if not (0 <= start_row < height and 0 <= start_col < width):
        raise ValueError(f"Pour point ({px}, {py}) falls outside DEM bounds")
    
    snapped_row, snapped_col = start_row, start_col
    snapped = False
    snap_distance = 0.0
    
    # Pour point snapping within tolerance radius
    if flow_accumulation is not None and snap_tolerance_m > 0:
        radius_cells_x = int(np.ceil(snap_tolerance_m / dx))
        radius_cells_y = int(np.ceil(snap_tolerance_m / dy))
        
        best_acc = flow_accumulation[start_row, start_col]
        
        for r in range(max(0, start_row - radius_cells_y), min(height, start_row + radius_cells_y + 1)):
            for c in range(max(0, start_col - radius_cells_x), min(width, start_col + radius_cells_x + 1)):
                dist = np.sqrt(((r - start_row) * dy)**2 + ((c - start_col) * dx)**2)
                if dist <= snap_tolerance_m:
                    acc = flow_accumulation[r, c]
                    if acc > best_acc:
                        best_acc = acc
                        snapped_row, snapped_col = r, c
                        snapped = True
                        snap_distance = dist
                        
    snapped_x, snapped_y = transform * (snapped_col + 0.5, snapped_row + 0.5)
    
    # Reverse lookup for upstream traversal: map each cell to upstream neighbors pointing to it
    upstream_map: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for r in range(height):
        for c in range(width):
            code = flow_dir[r, c]
            if code == 0:
                continue
            for dr, dc, d8_code in D8_OFFSETS:
                if code == d8_code:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        upstream_map.setdefault((nr, nc), []).append((r, c))
                    break
                    
    # Upstream BFS from snapped pour point
    catchment_mask = np.zeros((height, width), dtype=np.uint8)
    stack = [(snapped_row, snapped_col)]
    catchment_mask[snapped_row, snapped_col] = 1
    
    while stack:
        curr = stack.pop()
        for upstream_cell in upstream_map.get(curr, []):
            if catchment_mask[upstream_cell] == 0:
                catchment_mask[upstream_cell] = 1
                stack.append(upstream_cell)
                
    contributing_cells = int(np.sum(catchment_mask))
    area_m2 = contributing_cells * cell_area_m2
    
    # Polygonize catchment mask
    shapes_gen = shapes(catchment_mask, mask=(catchment_mask == 1), transform=transform)
    polygons = [shape(geom) for geom, val in shapes_gen if val == 1]
    
    if not polygons:
        from shapely.geometry import box
        bounds = (snapped_x - dx, snapped_y - dy, snapped_x + dx, snapped_y + dy)
        raw_geom = box(*bounds)
    else:
        if len(polygons) == 1:
            raw_geom = polygons[0]
        else:
            raw_geom = MultiPolygon(polygons)
        
    valid_geom = ensure_valid_polygon(raw_geom)
    
    return {
        "original_pour_point": {"x": px, "y": py},
        "snapped_pour_point": {"x": float(snapped_x), "y": float(snapped_y)},
        "snapped": snapped,
        "snap_distance_m": float(snap_distance),
        "contributing_cells_count": contributing_cells,
        "area_m2": float(area_m2),
        "area_km2": float(area_m2 / 1e6),
        "crs": crs_str,
        "geometry": valid_geom,
        "mask_array": catchment_mask,
    }
