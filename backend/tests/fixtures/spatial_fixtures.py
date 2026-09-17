"""
Geospatial Test Fixtures for Infrastructure Verification.

ALL DATA DEFINED IN THIS FILE ARE EXPLICITLY LABELED AS 'TEST FIXTURE ONLY'.
THEY DO NOT REPRESENT REAL CITY DATA, FLOOD OBSERVATIONS, DEM ELEVATION, OR RAINFALL DATA.
"""

import numpy as np
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, Point, Polygon

# 1. Synthetic Geometry Fixtures (TEST FIXTURE ONLY)
SAMPLE_POINT_4326 = Point(12.4924, 41.8902)  # (Lon, Lat)

SAMPLE_LINE_4326 = LineString([
    (12.4900, 41.8900),
    (12.4950, 41.8950)
])

SAMPLE_POLYGON_4326 = Polygon([
    (12.4900, 41.8900),
    (12.4950, 41.8900),
    (12.4950, 41.8950),
    (12.4900, 41.8950),
    (12.4900, 41.8900)
])

# Self-intersecting bowtie polygon (invalid geometry for validation/repair testing)
INVALID_BOWTIE_POLYGON = Polygon([
    (0, 0),
    (0, 2),
    (2, 0),
    (2, 2),
    (0, 0)
])


def create_synthetic_geotiff(file_path: str, width: int = 4, height: int = 4) -> str:
    """
    Creates a tiny synthetic 4x4 GeoTIFF file on disk for raster metadata testing.
    LABEL: TEST FIXTURE ONLY.
    """
    transform = from_origin(12.4900, 41.8950, 0.001, 0.001)
    data = np.ones((1, height, width), dtype=np.float32) * 100.0

    with rasterio.open(
        file_path,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=data.dtype,
        crs='EPSG:4326',
        transform=transform,
        nodata=-9999.0
    ) as dst:
        dst.write(data)

    return file_path
