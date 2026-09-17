"""
Generic Vector Utilities for Geospatial Processing.

Provides reusable, vendor-neutral spatial operations on Shapely geometries and GeoPandas GeoDataFrames.
Strictly scoped to foundational GIS operations (reprojection, bounding box extraction, envelope generation,
intersection checks).
"""

import geopandas as gpd
import structlog
from app.geospatial.crs import CRSManager
from pyproj import CRS
from shapely.geometry import box
from shapely.geometry.base import BaseGeometry

logger = structlog.get_logger("aquora.geospatial.vector")


def extract_bounds(geometry: BaseGeometry) -> tuple[float, float, float, float]:
    """
    Extract spatial bounding box tuple (minx, miny, maxx, maxy) from a Shapely geometry.
    """
    if geometry is None or geometry.is_empty:
        raise ValueError("Cannot extract bounds from null or empty geometry")
    return geometry.bounds


def create_envelope(
    bounds: tuple[float, float, float, float]
) -> BaseGeometry:
    """
    Create a 2D rectangular box polygon envelope from bounds (minx, miny, maxx, maxy).
    """
    minx, miny, maxx, maxy = bounds
    if minx > maxx or miny > maxy:
        raise ValueError(f"Invalid bounding box coordinates: {bounds}")
    return box(minx, miny, maxx, maxy)


def reproject_geometry(
    geometry: BaseGeometry,
    source_crs: str | int | CRS,
    target_crs: str | int | CRS
) -> BaseGeometry:
    """
    Reproject a Shapely geometry from source_crs to target_crs using CRSManager.
    """
    return CRSManager.transform_geometry(geometry, source_crs, target_crs)


def reproject_gdf(
    gdf: gpd.GeoDataFrame,
    target_crs: str | int | CRS
) -> gpd.GeoDataFrame:
    """
    Reproject a GeoPandas GeoDataFrame to target_crs.
    """
    if gdf.crs is None:
        raise ValueError("GeoDataFrame must have a defined CRS before reprojecting")
    
    parsed_target = CRSManager.parse_crs(target_crs)
    if CRSManager.are_crs_equal(gdf.crs, parsed_target):
        return gdf
    
    return gdf.to_crs(parsed_target)


def check_intersects(
    geom_a: BaseGeometry,
    geom_b: BaseGeometry
) -> bool:
    """
    Check if two geometries intersect spatially.
    """
    if geom_a is None or geom_b is None or geom_a.is_empty or geom_b.is_empty:
        return False
    return geom_a.intersects(geom_b)


def check_contains(
    container: BaseGeometry,
    contained: BaseGeometry
) -> bool:
    """
    Check if container geometry spatially contains contained geometry.
    """
    if container is None or contained is None or container.is_empty or contained.is_empty:
        return False
    return container.contains(contained)
