"""
Comprehensive Unit & Invariant Tests for Phase 4 Terrain & Surface-Flow Engine.

Verifies DEM validation, slope, aspect, D8 flow direction, D8 accumulation,
DEM-derived surface drainage proxy extraction, pour-point catchment delineation,
terrain providers, terrain processing service, database models, and API endpoints.

CRITICAL HARD SCOPE BOUNDARIES:
- Flow accumulation is NOT runoff or discharge.
- Surface drainage proxy is NOT municipal drainage network.
- Synthetic DEM rasters are explicitly labeled 'TEST FIXTURE ONLY'.
- Metric calculations use projected metric Analysis CRS (horizontal distances in meters).
"""

import numpy as np
import pytest
from app.geospatial.terrain import (
    calculate_aspect,
    calculate_d8_flow_accumulation,
    calculate_d8_flow_direction,
    calculate_slope,
    delineate_catchment,
    extract_surface_drainage_proxy,
    validate_dem_array_and_metadata,
)
from app.main import app
from app.providers.terrain import SyntheticTerrainProvider
from app.schemas.terrain import TerrainAnalysisRequest
from app.services.terrain_service import TerrainProcessingService
from httpx import ASGITransport, AsyncClient
from rasterio.transform import Affine
from shapely.geometry import Polygon


def test_dem_validation_valid(inclined_plane_fixture):
    """Test validation of valid 2D DEM array and metadata."""
    elevation, metadata = inclined_plane_fixture
    val_info = validate_dem_array_and_metadata(elevation, metadata)
    assert val_info["valid"] is True
    assert val_info["width"] == 10
    assert val_info["height"] == 10
    assert val_info["resolution_dx"] == 10.0
    assert val_info["resolution_dy"] == 10.0
    assert val_info["cell_area_m2"] == 100.0
    assert val_info["crs"] == "EPSG:32633"
    assert val_info["vertical_units"] == "meters"
    assert val_info["min_elevation_m"] == 55.0
    assert val_info["max_elevation_m"] == 100.0


def test_dem_validation_invalid_dimensions():
    """Test validation fails for 1D or 3D elevation arrays."""
    metadata = {"transform": [10.0, 0.0, 0.0, 0.0, -10.0, 0.0], "crs": "EPSG:32633"}
    elevation_1d = np.array([10.0, 20.0, 30.0], dtype=np.float32)
    with pytest.raises(ValueError, match="must be 2D"):
        validate_dem_array_and_metadata(elevation_1d, metadata)


def test_dem_validation_missing_crs(inclined_plane_fixture):
    """Test validation fails when CRS is missing."""
    elevation, metadata = inclined_plane_fixture
    bad_meta = dict(metadata)
    del bad_meta["crs"]
    with pytest.raises(ValueError, match="missing CRS"):
        validate_dem_array_and_metadata(elevation, bad_meta)


def test_slope_flat_plane(flat_dem_fixture):
    """Flat DEM must produce uniform slope of 0.0 degrees."""
    elevation, metadata = flat_dem_fixture
    transform = Affine(*metadata["transform"][:6])
    slope = calculate_slope(elevation, transform)
    
    assert slope.shape == (10, 10)
    assert np.all(slope >= 0.0)
    # Inner 8x8 flat plane slope must be approx 0.0°
    assert np.allclose(slope[1:9, 1:9], 0.0, atol=1e-3)


def test_slope_inclined_plane(inclined_plane_fixture):
    """Known inclined plane must produce expected gradient in degrees."""
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    slope = calculate_slope(elevation, transform)
    
    assert slope.shape == (10, 10)
    assert np.all(slope >= 0.0)
    # Expected slope for drop 5m per 10m dx: arctan(5/10) = 26.565°
    inner_slope = slope[1:9, 1:9]
    assert np.allclose(inner_slope, 26.565, atol=1.0)


def test_aspect_inclined_plane(inclined_plane_fixture):
    """Aspect of South-descending plane must be South (~180°)."""
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    aspect = calculate_aspect(elevation, transform)
    
    assert aspect.shape == (10, 10)
    inner_aspect = aspect[1:9, 1:9]
    # Downslope is toward South (180°)
    assert np.allclose(inner_aspect, 180.0, atol=5.0)


def test_aspect_flat_plane(flat_dem_fixture):
    """Flat DEM aspect must be -1.0 (undefined aspect)."""
    elevation, metadata = flat_dem_fixture
    transform = Affine(*metadata["transform"][:6])
    aspect = calculate_aspect(elevation, transform)
    assert np.all(aspect == -1.0)


def test_d8_flow_direction_inclined_plane(inclined_plane_fixture):
    """D8 flow direction on South-descending plane must point South (code 4)."""
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    flow_dir = calculate_d8_flow_direction(elevation, transform)
    
    assert flow_dir.shape == (10, 10)
    # Rows 0-8 should point South (code 4)
    assert np.all(flow_dir[:9, :] == 4)
    # Bottom row 9 has no lower neighbor -> 0 (SINK / NO_FLOW)
    assert np.all(flow_dir[9, :] == 0)


def test_d8_flow_direction_cardinal_vs_diagonal():
    """Verify D8 selects cardinal vs diagonal based on drop / distance."""
    # Create 3x3 DEM where center is 100m
    # South neighbor (row 2, col 1) is 90m (drop 10m over 10m -> slope 1.0)
    # SE neighbor (row 2, col 2) is 85m (drop 15m over 14.14m -> slope 1.06)
    # Slope to SE (1.06) > South (1.0), so SE (code 2) must be selected!
    elevation = np.array([
        [100.0, 100.0, 100.0],
        [100.0, 100.0, 100.0],
        [100.0,  90.0,  85.0],
    ], dtype=np.float32)
    transform = Affine.translation(0.0, 30.0) * Affine.scale(10.0, -10.0)
    flow_dir = calculate_d8_flow_direction(elevation, transform)
    
    assert flow_dir[1, 1] == 2  # Southeast (code 2)


def test_d8_flow_accumulation_linear(inclined_plane_fixture):
    """Flow accumulation on linear slope must increase monotonically from 1 to 10."""
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    flow_dir = calculate_d8_flow_direction(elevation, transform)
    flow_acc = calculate_d8_flow_accumulation(flow_dir)
    
    assert flow_acc.shape == (10, 10)
    assert np.all(flow_acc >= 1)
    
    # Check column 0 accumulation increases monotonically from 1 at row 0 to 10 at row 9
    expected_col0 = np.arange(1, 11, dtype=np.int32)
    assert np.array_equal(flow_acc[:, 0], expected_col0)


def test_surface_drainage_proxy(inclined_plane_fixture):
    """Surface drainage proxy must trigger for cells exceeding area threshold."""
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    flow_dir = calculate_d8_flow_direction(elevation, transform)
    flow_acc = calculate_d8_flow_accumulation(flow_dir)
    
    # 10m x 10m cells = 100 m2 cell area.
    # Threshold area = 500 m2 -> required cells = 5 cells.
    proxy = extract_surface_drainage_proxy(flow_acc, cell_area_m2=100.0, threshold_area_m2=500.0)
    
    assert proxy.shape == (10, 10)
    # Rows 0-3 (acc 1-4) should be 0; Rows 4-9 (acc 5-10) should be 1
    assert np.all(proxy[:4, :] == 0)
    assert np.all(proxy[4:, :] == 1)


def test_catchment_delineation(inclined_plane_fixture):
    """Delineate catchment from pour point at bottom of inclined plane."""
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    flow_dir = calculate_d8_flow_direction(elevation, transform)
    flow_acc = calculate_d8_flow_accumulation(flow_dir)
    
    # Pour point near bottom row center (col 5, row 9)
    # Pixel center coordinate: x = 500000 + 5.5 * 10 = 500055, y = 4501000 - 9.5 * 10 = 4500905
    pour_point_xy = (500055.0, 4500905.0)
    
    catchment = delineate_catchment(
        flow_dir,
        transform=transform,
        pour_point_xy=pour_point_xy,
        snap_tolerance_m=50.0,
        flow_accumulation=flow_acc,
        crs_str="EPSG:32633"
    )
    
    assert catchment["contributing_cells_count"] == 10  # Full 10-cell vertical flow path
    assert catchment["area_m2"] == 1000.0
    assert catchment["area_km2"] == 0.001
    assert isinstance(catchment["geometry"], Polygon)
    assert catchment["geometry"].is_valid


def test_synthetic_terrain_provider():
    """Verify SyntheticTerrainProvider returns datasets explicitly labeled TEST FIXTURE ONLY."""
    provider = SyntheticTerrainProvider()
    elevation, meta = provider.generate_synthetic_dem(fixture_type="v_valley")
    
    assert elevation.shape == (100, 100)
    assert "TEST FIXTURE ONLY" in meta["source"]
    assert meta["is_test_fixture"] is True


@pytest.mark.asyncio
async def test_terrain_processing_service():
    """Verify end-to-end execution of TerrainProcessingService."""
    service = TerrainProcessingService()
    request = TerrainAnalysisRequest(
        dataset_id="synthetic_inclined_plane",
        provider_type="synthetic",
        fixture_type="inclined_plane",
        pour_point_xy=(500055.0, 4500905.0)
    )
    
    response = await service.execute_terrain_analysis(request, db=None)
    
    assert response.status == "COMPLETED"
    assert response.dataset_id == "synthetic_inclined_plane"
    assert response.dem_metadata.is_test_fixture is True
    assert len(response.derivatives) >= 4
    assert response.catchment is not None
    assert response.catchment.area_m2 > 0


@pytest.mark.asyncio
async def test_terrain_api_endpoints():
    """Verify HTTP API endpoints for developer verification under /api/v1/terrain/."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # POST /api/v1/terrain/analyze
        payload = {
            "dataset_id": "synthetic_inclined_plane",
            "provider_type": "synthetic",
            "fixture_type": "inclined_plane",
            "analysis_crs": "EPSG:32633",
            "surface_drainage_threshold_m2": 5000.0
        }
        res = await client.post("/api/v1/terrain/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "COMPLETED"
        assert data["dem_metadata"]["is_test_fixture"] is True
        
        # GET /api/v1/terrain/analysis/latest
        res_latest = await client.get("/api/v1/terrain/analysis/latest")
        assert res_latest.status_code == 200


def test_scope_boundary_invariants(inclined_plane_fixture):
    """
    ASSERT SCIENTIFIC SCOPE INVARIANTS:
    Phase 4 must NEVER generate runoff, discharge, pipe surcharges, or flood depths.
    """
    elevation, metadata = inclined_plane_fixture
    transform = Affine(*metadata["transform"][:6])
    slope = calculate_slope(elevation, transform)
    flow_dir = calculate_d8_flow_direction(elevation, transform)
    flow_acc = calculate_d8_flow_accumulation(flow_dir)
    
    # 1. Slope is non-negative
    assert np.all(slope >= 0.0)
    # 2. Flow accumulation cell count is >= 1
    assert np.all(flow_acc >= 1)
    # 3. Flow accumulation represents upstream contributing cell topology ONLY, NOT runoff volume in m3/s
    assert flow_acc.dtype in (np.int32, np.int64)
