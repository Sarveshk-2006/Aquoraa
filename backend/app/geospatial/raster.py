"""
Generic Raster Utilities for Geospatial Processing.

Provides reusable raster metadata inspection, affine coordinate transformation, and window calculation
utilities using Rasterio, NumPy, and PyProj.
Strictly scoped to metadata extraction and spatial indexing. No flood, DEM, or hydrological calculations.
"""

import math
from typing import Any
import numpy as np
import structlog

try:
    import rasterio
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
    rasterio = None

logger = structlog.get_logger("aquora.geospatial.raster")


def extract_raster_metadata_from_dataset(dataset: rasterio.DatasetReader) -> dict[str, Any]:
    """
    Extract structured metadata dictionary from an open Rasterio DatasetReader.
    """
    transform: Affine = dataset.transform
    crs_str = str(dataset.crs) if dataset.crs else None
    
    return {
        "crs": crs_str,
        "bounds": (dataset.bounds.left, dataset.bounds.bottom, dataset.bounds.right, dataset.bounds.top),
        "width": dataset.width,
        "height": dataset.height,
        "count": dataset.count,
        "resolution": (abs(transform.a), abs(transform.e)),
        "nodata": dataset.nodata,
        "driver": dataset.driver,
        "dtype": str(dataset.dtypes[0]) if dataset.dtypes else None,
        "transform": [transform.a, transform.b, transform.c, transform.d, transform.e, transform.f],
    }


def extract_raster_metadata(source: str | rasterio.DatasetReader) -> dict[str, Any]:
    """
    Extract metadata from a raster file path or an existing DatasetReader.
    """
    if isinstance(source, rasterio.DatasetReader):
        return extract_raster_metadata_from_dataset(source)
    
    with rasterio.open(source) as ds:
        return extract_raster_metadata_from_dataset(ds)


def coordinate_to_pixel(
    transform_matrix: Affine | list | tuple,
    x: float,
    y: float
) -> tuple[int, int]:
    """
    Convert spatial coordinate (x, y) to raster pixel index (row, col).
    
    Returns (row, col).
    """
    if not isinstance(transform_matrix, Affine):
        transform_matrix = Affine(*transform_matrix[:6])
    
    # ~transform_matrix inverts Affine matrix
    inv_transform = ~transform_matrix
    col, row = inv_transform * (x, y)
    return int(floor_or_int(row)), int(floor_or_int(col))


def pixel_to_coordinate(
    transform_matrix: Affine | list | tuple,
    row: int,
    col: int
) -> tuple[float, float]:
    """
    Convert raster pixel index (row, col) to spatial coordinate (x, y) at pixel center.
    
    Returns (x, y).
    """
    if not isinstance(transform_matrix, Affine):
        transform_matrix = Affine(*transform_matrix[:6])
    
    x, y = transform_matrix * (col + 0.5, row + 0.5)
    return float(x), float(y)


def floor_or_int(val: float) -> int:
    """Helper for deterministic pixel indexing."""
    return int(np.floor(val))
