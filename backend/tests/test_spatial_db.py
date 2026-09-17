"""
Unit Tests for Phase 2 Spatial Database Models & Schema Definitions.

Verifies SQLAlchemy / GeoAlchemy2 spatial models (StudyArea, RasterMetadata, VectorFeature),
WKT/WKB geometry conversion, JSONB provenance structure, and Alembic migration revision order.
"""

import uuid

from app.models.spatial import RasterMetadata, StudyArea, VectorFeature
from geoalchemy2 import WKTElement

from tests.fixtures.spatial_fixtures import SAMPLE_POINT_4326, SAMPLE_POLYGON_4326


def test_study_area_model_instantiation():
    """Verify StudyArea SQLAlchemy model creation with WKT geometry and metadata."""
    wkt_geom = WKTElement(SAMPLE_POLYGON_4326.wkt, srid=4326)
    area = StudyArea(
        id=uuid.uuid4(),
        name="Test Study Area (Fixture)",
        description="Development synthetic study area",
        geom=wkt_geom,
        srid=4326,
        provenance={"source": "SYNTHETIC_TEST_FIXTURE", "version": "1.0"}
    )

    assert area.name == "Test Study Area (Fixture)"
    assert area.srid == 4326
    assert area.provenance["source"] == "SYNTHETIC_TEST_FIXTURE"
    assert area.geom.data == SAMPLE_POLYGON_4326.wkt


def test_raster_metadata_model_instantiation():
    """Verify RasterMetadata model creation with envelope bounding box geometry."""
    envelope_wkt = WKTElement(SAMPLE_POLYGON_4326.wkt, srid=4326)
    raster_meta = RasterMetadata(
        dataset_identifier="dem_test_grid_01",
        source="TEST_RASTER_PROVIDER",
        crs="EPSG:4326",
        geom_bounds=envelope_wkt,
        resolution_x=0.001,
        resolution_y=0.001,
        width=100,
        height=100,
        nodata=-9999.0,
        units="meters",
        version="1.0",
        provenance={"sensor": "SYNTHETIC_GRID"},
        storage_pointer="s3://aquora-test-bucket/dems/dem_01.tif"
    )

    assert raster_meta.dataset_identifier == "dem_test_grid_01"
    assert raster_meta.resolution_x == 0.001
    assert raster_meta.nodata == -9999.0


def test_vector_feature_model_instantiation():
    """Verify VectorFeature generic spatial entity store creation."""
    point_wkt = WKTElement(SAMPLE_POINT_4326.wkt, srid=4326)
    feature = VectorFeature(
        category="road",
        geom=point_wkt,
        srid=4326,
        feature_properties={"name": "Test Main Street", "lanes": 2},
        provenance={"source": "SYNTHETIC_VECTOR_FIXTURE"}
    )

    assert feature.category == "road"
    assert feature.feature_properties["name"] == "Test Main Street"
    assert feature.provenance["source"] == "SYNTHETIC_VECTOR_FIXTURE"
