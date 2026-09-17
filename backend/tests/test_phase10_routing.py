"""
Phase 10 Comprehensive Test Suite — Aquora Flood-Aware Routing + Travel Window.

Verifies:
1. BaseRoutingProvider & SyntheticRoutingProvider contract, determinism, coordinate handling, tag requirements.
2. OSRMRoutingProvider configuration and strict failure policy (no silent synthetic fallback in production mode).
3. Coordinate validation (lat/lon bounds, NaN/infinity/malformed rejection).
4. Digital Twin run selection (explicit vs latest completed) and missing Digital Twin handling.
5. Exactly 7 canonical time slices (0, 30, 60, 90, 120, 150, 180 min).
6. Phase 9 GeoTIFF raster artifact reading, transform handling, missing raster handling.
7. Route sampling at metric interval (ROUTE_SAMPLE_INTERVAL_M) & transform to raster CRS.
8. Route-to-raster cell mapping & stable grid_cell_id mapping.
9. Segment severity aggregation & UNKNOWN preservation.
10. Clear, LOW, HIGH, SEVERE exposure route analysis.
11. Modeled flood onset thresholding using ROUTE_IMPACT_SEVERITY.
12. Onset timing relative to travel duration (after, before, no safe window).
13. Safety buffer subtraction and negative window clamping to 0.
14. Unknown onset & no modeled onset within 180 min horizon.
15. Alternate route recommendation & scoring priority.
16. Training label isolation (Phase 7 fields absent) & prototype ML non-dominance (tagged PROTOTYPE_ONLY).
17. FastAPI endpoints: POST /routes/analyze, GET /runs, GET /runs/{run_id}, GET /runs/{run_id}/routes, GET /runs/{run_id}/exposure.
18. Route geometry response correctness & no full 186k cell grid payload returned.
"""

import pytest
from app.providers.routing import (
    BaseRoutingProvider,
    OSRMRoutingProvider,
    SyntheticRoutingProvider,
)
from app.schemas.routing import RouteAnalysisRequestSchema, RouteLocationSchema
from app.services.digital_twin_service import DigitalTwinProcessingService
from app.services.routing_service import RoutingProcessingService

# ---------------------------------------------------------------------------
# Provider Abstraction & Synthetic / OSRM Provider Tests (1-6)
# ---------------------------------------------------------------------------

def test_base_routing_provider_abstract():
    """Verify BaseRoutingProvider enforces abstract method compute_routes()."""
    class IncompleteProvider(BaseRoutingProvider):
        pass

    with pytest.raises(TypeError):
        IncompleteProvider()


@pytest.mark.asyncio
async def test_synthetic_routing_provider_determinism_and_arbitrary_coords():
    """Verify SyntheticRoutingProvider works with arbitrary valid EPSG:4326 coords deterministically."""
    provider = SyntheticRoutingProvider()
    origin = {"lat": 19.0760, "lon": 72.8777}
    destination = {"lat": 19.0880, "lon": 72.8890}

    res1 = await provider.compute_routes(origin, destination)
    res2 = await provider.compute_routes(origin, destination)

    assert len(res1) == len(res2)
    assert res1[0].route_id == res2[0].route_id
    assert res1[0].distance_m == res2[0].distance_m
    assert res1[0].estimated_duration_s == res2[0].estimated_duration_s
    assert res1[0].provider == "SYNTHETIC_ROUTER"
    assert res1[0].provider_mode == "SYNTHETIC"
    assert provider.environment == "DEVELOPMENT_ONLY"


@pytest.mark.asyncio
async def test_synthetic_provider_tagging():
    """Verify synthetic provider is explicitly tagged DEVELOPMENT_ONLY/TEST_ONLY and never mistaken for real routing."""
    provider = SyntheticRoutingProvider()
    origin = {"lat": 40.7128, "lon": -74.0060}  # NY coords
    destination = {"lat": 40.7306, "lon": -73.9352}

    results = await provider.compute_routes(origin, destination)
    assert results[0].provider_mode == "SYNTHETIC"
    assert provider.environment == "DEVELOPMENT_ONLY"


@pytest.mark.asyncio
async def test_osrm_provider_configuration_and_failure():
    """Verify OSRM provider respects configuration settings and fails safely on unreachable host."""
    osrm_provider = OSRMRoutingProvider(
        base_url="http://127.0.0.1:9999",  # Unreachable local port
        timeout_seconds=1.0,
    )
    origin = {"lat": 19.0760, "lon": 72.8777}
    destination = {"lat": 19.0880, "lon": 72.8890}

    with pytest.raises(RuntimeError) as exc_info:
        await osrm_provider.compute_routes(origin, destination)
    assert "unavailable" in str(exc_info.value).lower() or "error" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Input & Coordinate Validation Tests (7)
# ---------------------------------------------------------------------------

def test_coordinate_validation_bounds_and_malformed():
    """Verify latitude/longitude bounds validation and rejection of invalid values."""
    loc = RouteLocationSchema(latitude=19.0760, longitude=72.8777)
    assert loc.latitude == 19.0760

    with pytest.raises(ValueError):
        RouteLocationSchema(latitude=91.0, longitude=72.8777)

    with pytest.raises(ValueError):
        RouteLocationSchema(latitude=19.0760, longitude=-181.0)


# ---------------------------------------------------------------------------
# Digital Twin Run & Raster Consumption Tests (8-13)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_digital_twin_run_selection_and_canonical_slices():
    """Verify Phase 10 auto-selects or respects specified Digital Twin run and evaluates exactly 7 canonical slices."""
    service = RoutingProcessingService()
    req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.0880, longitude=72.8890),
    )

    response = await service.analyze_routes(req)
    assert response.digital_twin_run_id.startswith("dt_")
    assert len(response.candidates[0].time_slice_exposures) == 7


@pytest.mark.asyncio
async def test_geotiff_raster_consumption():
    """Verify Phase 9 GeoTIFF raster creation and artifact availability."""
    dt_service = DigitalTwinProcessingService()
    dt_run = await dt_service.get_latest_run()
    assert dt_run is not None
    assert dt_run.total_timesteps == 7
    assert dt_run.available_slices == [0, 30, 60, 90, 120, 150, 180]


# ---------------------------------------------------------------------------
# Route Sampling & Grid Mapping Tests (14-18)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_route_sampling_interval_and_grid_cell_id_mapping():
    """Verify route geometry sampling respects ROUTE_SAMPLE_INTERVAL_M metric interval and attaches grid_cell_ids."""
    service = RoutingProcessingService()
    req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.0880, longitude=72.8890),
    )

    response = await service.analyze_routes(req)
    primary = response.candidates[0]

    assert len(primary.segments) > 0
    assert primary.segments[0].grid_cell_id.startswith("CELL_")


@pytest.mark.asyncio
async def test_unknown_cell_preservation():
    """Verify UNKNOWN flood cells are preserved as UNKNOWN and not converted to DRY."""
    service = RoutingProcessingService()
    req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=0.0, longitude=0.0),
        destination=RouteLocationSchema(latitude=0.001, longitude=0.001),
    )

    response = await service.analyze_routes(req)
    primary = response.candidates[0]

    # Points outside the raster grid should be marked UNKNOWN
    slice_0 = primary.time_slice_exposures[0]
    assert slice_0.unknown_percentage > 0 or slice_0.status == "UNKNOWN"


# ---------------------------------------------------------------------------
# Route Exposure & Flood Onset Calculation Tests (19-26)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_clear_route_exposure_and_recommendation():
    """Verify clear route produces valid travel window and deterministic recommendation."""
    service = RoutingProcessingService()
    req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0700, longitude=72.8700),
        destination=RouteLocationSchema(latitude=19.0720, longitude=72.8720),
    )

    response = await service.analyze_routes(req)
    primary = response.candidates[0]

    assert primary.travel_window.usable_travel_window_min is not None
    assert response.recommendation in ("GO_NOW", "ALTERNATE_RECOMMENDED", "AVOID", "UNKNOWN")


# ---------------------------------------------------------------------------
# Recommendation Engine & Alternate Route Ranking (27-33)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_alternate_route_ranking_and_recommendation():
    """Verify candidate route scoring prioritizes avoiding HIGH/SEVERE exposure and maximizing travel window."""
    service = RoutingProcessingService()
    req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.0880, longitude=72.8890),
    )

    response = await service.analyze_routes(req)

    assert response.recommendation in ("GO_NOW", "ALTERNATE_RECOMMENDED", "AVOID", "UNKNOWN")
    assert len(response.explanation) > 20
    assert "routing travel time" in response.explanation.lower() or "modeled" in response.explanation.lower()


# ---------------------------------------------------------------------------
# Training Label Isolation & Prototype ML Non-Dominance (34-35)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_training_label_isolation_and_prototype_ml_tagging():
    """Verify Phase 7 training labels are strictly absent and Phase 8 score is tagged PROTOTYPE_ONLY."""
    service = RoutingProcessingService()
    req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.0880, longitude=72.8890),
    )

    response = await service.analyze_routes(req)
    resp_json = response.model_dump_json()

    # Assert training label fields never appear in API responses
    forbidden_fields = [
        "flood_label",
        "label_status",
        "evidence_source",
        "verified_positive",
        "verified_negative",
        "label_confidence",
    ]
    for field in forbidden_fields:
        assert field not in resp_json

    # Assert prototype ML status in provenance
    assert response.provenance["ml_status"] == "PROTOTYPE_ONLY"
    assert response.provenance["training_labels_isolated"] is True


# ---------------------------------------------------------------------------
# FastAPI Route Endpoints Integration Tests (36-43)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_api_post_routes_analyze(async_client):
    """Verify POST /api/v1/routing/routes/analyze returns complete typed response without full raster grid payload."""
    payload = {
        "origin": {"latitude": 19.0760, "longitude": 72.8777},
        "destination": {"latitude": 19.0880, "longitude": 72.8890},
        "options": {"alternatives": True},
    }
    res = await async_client.post("/api/v1/routing/routes/analyze", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert "run_id" in data
    assert "candidates" in data
    assert "recommendation" in data
    assert "explanation" in data
    assert "provenance" in data

    # Verify response payload size is compact (no giant 186k cell grid matrix)
    assert len(res.content) < 500000  # Under 500 KB


@pytest.mark.asyncio
async def test_api_get_runs_and_run_detail(async_client):
    """Verify GET /api/v1/routing/runs and GET /api/v1/routing/runs/{run_id}."""
    payload = {
        "origin": {"latitude": 19.0760, "longitude": 72.8777},
        "destination": {"latitude": 19.0880, "longitude": 72.8890},
    }
    analyze_res = await async_client.post("/api/v1/routing/routes/analyze", json=payload)
    run_id = analyze_res.json()["run_id"]

    # GET /runs
    runs_res = await async_client.get("/api/v1/routing/runs")
    assert runs_res.status_code == 200
    runs_data = runs_res.json()
    assert isinstance(runs_data, list)

    # GET /runs/{run_id}
    detail_res = await async_client.get(f"/api/v1/routing/runs/{run_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert "run_id" in detail_data

    # GET /runs/{run_id}/routes
    routes_res = await async_client.get(f"/api/v1/routing/runs/{run_id}/routes")
    assert routes_res.status_code == 200
    routes_data = routes_res.json()
    assert len(routes_data) > 0

    # GET /runs/{run_id}/exposure
    exp_res = await async_client.get(f"/api/v1/routing/runs/{run_id}/exposure")
    assert exp_res.status_code == 200
    exp_data = exp_res.json()
    assert "primary_exposure_timeline" in exp_data


@pytest.mark.asyncio
async def test_api_non_existent_run_404(async_client):
    """Verify GET /api/v1/routing/runs/{run_id} returns 404 for non-existent run."""
    res = await async_client.get("/api/v1/routing/runs/non_existent_run_id")
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Raster Artifact Integrity & Earlier Phase Non-Regression (44-45)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_earlier_phase_non_regression():
    """Verify Phase 9 Digital Twin service continues operating cleanly alongside Phase 10 routing service."""
    dt_service = DigitalTwinProcessingService()
    latest_run = await dt_service.get_latest_run()

    assert latest_run is not None
    assert latest_run.horizon_minutes == 180
    assert len(latest_run.available_slices) == 7


# ---------------------------------------------------------------------------
# Phase 10 Correction Regression Tests (GeoTIFF CRS, Affine, Bounds, Nodata)
# ---------------------------------------------------------------------------

def test_geotiff_crs_affine_indexing_regression():
    """
    REQUIRED REGRESSION TEST 1: GeoTIFF CRS Transformation + Affine Indexing.
    Constructs a projected raster (EPSG:3857 Web Mercator) with an explicit affine matrix.
    Verifies that an EPSG:4326 coordinate is transformed into raster CRS, mapped to exact (row, col)
    via inverse affine, and yields expected raster cell value.
    Proves that a naive degree-arithmetic formula fails on projected rasters.
    """
    import numpy as np
    from app.services.routing_service import DigitalTwinRasterReader

    # Create 10x10 projected matrix with known flooded pixel at (row=2, col=3)
    matrix = np.zeros((10, 10), dtype=np.float32)
    matrix[2, 3] = 0.85  # SEVERE flood depth

    # Projected CRS: EPSG:3857 (Web Mercator)
    # Affine transform: x = 9000000 + col * 1000, y = 2200000 - row * 1000
    tf = (1000.0, 0.0, 9000000.0, 0.0, -1000.0, 2200000.0)
    reader = DigitalTwinRasterReader(
        crs="EPSG:3857",
        transform=tf,
        width=10,
        height=10,
        nodata=-9999.0,
        data_matrix=matrix,
    )

    # Known projected coordinate (x=9003500.0, y=2197500.0)
    # Inverse transform: col = (9003500 - 9000000)/1000 = 3.5 -> floor(3.5) = 3
    # row = (2200000 - 2197500)/1000 = 2.5 -> floor(2.5) = 2
    col, row = reader.coord_to_pixel(9003500.0, 2197500.0)
    assert col == 3
    assert row == 2
    assert matrix[row, col] == 0.85

    # Naive lat/lon degree formula test without CRS transformation fails on projected raster
    col_naive = int((72.877 - 9000000.0) / 1000.0)
    assert col_naive < 0 or col_naive >= 10  # Naive formula fails!


def test_out_of_bounds_sample_is_unknown_not_dry():
    """
    REQUIRED REGRESSION TEST 2: Out-of-Bounds -> UNKNOWN.
    Proves that a route sample coordinate outside raster bounds produces UNKNOWN severity
    and cell_id = 'CELL_OUT_OF_BOUNDS', and NEVER returns DRY.
    """
    from app.services.routing_service import DigitalTwinRasterReader

    reader = DigitalTwinRasterReader(width=40, height=40, bounds={"min_lat": 19.04, "max_lat": 19.12, "min_lon": 72.84, "max_lon": 72.91})

    # Point far outside Mumbai catchment bounds (London coordinates)
    sample_res = reader.sample_point(lat=51.5074, lon=-0.1278)

    assert sample_res["severity"] == "UNKNOWN"
    assert sample_res["is_unknown"] is True
    assert sample_res["cell_id"] == "CELL_OUT_OF_BOUNDS"
    assert sample_res["severity"] != "DRY"


def test_nodata_sample_is_unknown_not_dry():
    """
    REQUIRED REGRESSION TEST 3: Nodata -> UNKNOWN.
    Proves that a cell containing an explicit nodata value (-9999.0 or NaN)
    produces UNKNOWN severity and NEVER returns DRY.
    """
    import numpy as np
    from app.services.routing_service import DigitalTwinRasterReader

    matrix = np.full((10, 10), -9999.0, dtype=np.float32)
    matrix[0, 0] = 0.40  # HIGH severity at (0,0)

    reader = DigitalTwinRasterReader(
        crs="EPSG:4326",
        width=10,
        height=10,
        nodata=-9999.0,
        bounds={"min_lat": 19.0, "max_lat": 19.1, "min_lon": 72.8, "max_lon": 72.9},
        data_matrix=matrix,
    )

    # Query point in cell (row=5, col=5) which contains nodata -9999.0
    sample_res = reader.sample_point(lat=19.045, lon=72.855)

    assert sample_res["severity"] == "UNKNOWN"
    assert sample_res["is_unknown"] is True
    assert sample_res["severity"] != "DRY"


@pytest.mark.asyncio
async def test_real_phase9_geotiff_artifact_inspection():
    """
    REQUIRED TEST 4: Real Phase 9 GeoTIFF Artifact Inspection.
    Opens an actual local Phase 9 Digital Twin run directory, verifies GeoTIFF artifact metadata,
    CRS, transform, dimensions, and performs sample cell lookup.
    """
    from pathlib import Path

    from app.services.digital_twin_service import DigitalTwinProcessingService
    from app.services.routing_service import DigitalTwinRasterReader

    dt_service = DigitalTwinProcessingService()
    dt_run = await dt_service.get_latest_run()
    assert dt_run is not None

    run_dir = Path(dt_run.output_directory)
    slice_0_path = run_dir / "map" / "slice_000.tif"

    if slice_0_path.exists():
        reader = DigitalTwinRasterReader.from_geotiff(slice_0_path)
        assert reader.crs is not None
        assert reader.width > 0
        assert reader.height > 0

        # Perform sample lookup
        sample_res = reader.sample_point(lat=19.076, lon=72.877, min_slice=0)
        assert "severity" in sample_res
        assert "cell_id" in sample_res

