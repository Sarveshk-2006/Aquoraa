"""
Unit Tests for Phase 2 Geospatial Infrastructure.

Tests CRS handling, geometry validation, vector utilities, raster metadata extraction,
and provider contracts using synthetic test fixtures.
"""

import os
import tempfile

import geopandas as gpd
import pytest
from app.geospatial.crs import CRSManager
from app.geospatial.raster import (
    coordinate_to_pixel,
    extract_raster_metadata,
    pixel_to_coordinate,
)
from app.geospatial.validation import (
    GeometryValidationError,
    ensure_valid_polygon,
    validate_geometry,
)
from app.geospatial.vector import (
    check_contains,
    check_intersects,
    create_envelope,
    extract_bounds,
    reproject_gdf,
    reproject_geometry,
)
from app.schemas.geospatial import BoundingBox, SpatialMetadata
from shapely.geometry import Point

from tests.fixtures.spatial_fixtures import (
    INVALID_BOWTIE_POLYGON,
    SAMPLE_POINT_4326,
    SAMPLE_POLYGON_4326,
    create_synthetic_geotiff,
)


def test_crs_manager_parsing_and_equality():
    """Verify CRS parsing and equality checks."""
    crs_4326 = CRSManager.parse_crs("EPSG:4326")
    assert crs_4326.to_epsg() == 4326
    assert CRSManager.validate_crs("EPSG:4326") is True
    assert CRSManager.validate_crs("INVALID_CRS_STRING") is False

    assert CRSManager.are_crs_equal("EPSG:4326", 4326) is True
    assert CRSManager.are_crs_equal("EPSG:4326", "EPSG:3857") is False


def test_crs_transformations():
    """Test geometric coordinate reprojection across Canonical, Display, and Analysis CRSs."""
    # Transform Point(12.4924, 41.8902) from EPSG:4326 to EPSG:3857 (Display)
    point_display = CRSManager.to_display(SAMPLE_POINT_4326, source_crs="EPSG:4326")
    assert point_display.x != SAMPLE_POINT_4326.x
    assert point_display.y != SAMPLE_POINT_4326.y

    # Transform back to Canonical (EPSG:4326)
    point_canonical = CRSManager.to_canonical(point_display, source_crs="EPSG:3857")
    assert pytest.approx(point_canonical.x, abs=1e-5) == SAMPLE_POINT_4326.x
    assert pytest.approx(point_canonical.y, abs=1e-5) == SAMPLE_POINT_4326.y

    # Transform to configured Analysis CRS
    point_analysis = CRSManager.to_analysis(SAMPLE_POINT_4326, source_crs="EPSG:4326")
    assert point_analysis is not None
    assert point_analysis.x != SAMPLE_POINT_4326.x




def test_geometry_validation_and_repair():
    """Test geometry validation and controlled validity repair."""
    # Valid geometry
    assert validate_geometry(SAMPLE_POLYGON_4326, expected_type="Polygon") is True

    # Type mismatch validation raises GeometryValidationError
    with pytest.raises(GeometryValidationError):
        validate_geometry(SAMPLE_POINT_4326, expected_type="Polygon")

    # Invalid geometry repair
    assert INVALID_BOWTIE_POLYGON.is_valid is False
    repaired = ensure_valid_polygon(INVALID_BOWTIE_POLYGON)
    assert repaired.is_valid is True


def test_vector_utilities():
    """Test vector operations (bounding box, envelope, reprojection, intersection)."""
    bounds = extract_bounds(SAMPLE_POLYGON_4326)
    assert bounds == (12.4900, 41.8900, 12.4950, 41.8950)

    envelope = create_envelope(bounds)
    assert envelope.geom_type == "Polygon"
    assert envelope.bounds == bounds

    # Reproject Shapely geometry
    reprojected = reproject_geometry(SAMPLE_POINT_4326, "EPSG:4326", "EPSG:3857")
    assert reprojected.x > 1000000

    # GeoDataFrame reprojection
    gdf = gpd.GeoDataFrame([{"geometry": SAMPLE_POINT_4326}], crs="EPSG:4326")
    gdf_reprojected = reproject_gdf(gdf, "EPSG:3857")
    assert str(gdf_reprojected.crs) == "EPSG:3857"

    # Spatial intersection & containment
    inner_point = Point(12.4925, 41.8925)
    outside_point = Point(0.0, 0.0)
    assert check_contains(SAMPLE_POLYGON_4326, inner_point) is True
    assert check_contains(SAMPLE_POLYGON_4326, outside_point) is False
    assert check_intersects(SAMPLE_POLYGON_4326, inner_point) is True


def test_raster_utilities():
    """Test raster metadata extraction and pixel/coordinate transforms using synthetic GeoTIFF."""
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp_file:
        tmp_path = tmp_file.name

    try:
        create_synthetic_geotiff(tmp_path, width=4, height=4)
        metadata = extract_raster_metadata(tmp_path)

        assert metadata["width"] == 4
        assert metadata["height"] == 4
        assert metadata["crs"] == "EPSG:4326"
        assert metadata["nodata"] == -9999.0
        assert metadata["count"] == 1

        transform_matrix = metadata["transform"]
        # Top-left corner coordinate (12.4900, 41.8950)
        row, col = coordinate_to_pixel(transform_matrix, 12.4905, 41.8945)
        assert row == 0
        assert col == 0

        # Pixel back to coordinate
        x, y = pixel_to_coordinate(transform_matrix, 0, 0)
        assert pytest.approx(x, abs=1e-3) == 12.4905
        assert pytest.approx(y, abs=1e-3) == 41.8945

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_spatial_pydantic_schemas():
    """Test Pydantic spatial metadata schemas validation."""
    bbox = BoundingBox(minx=10.0, miny=10.0, maxx=20.0, maxy=20.0)
    assert bbox.minx == 10.0

    with pytest.raises(ValueError):
        BoundingBox(minx=20.0, miny=10.0, maxx=10.0, maxy=20.0)

    meta = SpatialMetadata(
        source="TEST_FIXTURE_PROVIDER",
        crs="EPSG:4326",
        bounding_box=bbox,
        units="meters"
    )
    assert meta.source == "TEST_FIXTURE_PROVIDER"
    assert meta.crs == "EPSG:4326"
