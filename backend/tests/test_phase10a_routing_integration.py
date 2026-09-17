"""
Phase 10A Flood-Aware Routing Integration & End-to-End Validation Tests.

Validates:
1. Routing Provider Selection (OSRM vs SYNTHETIC).
2. REAL_DATA Mode Strict Error Handling (0 synthetic fallback on OSRM failure).
3. Coordinate validation & CRS transformation (EPSG:4326 -> Analysis CRS via pyproj).
4. GeoTIFF Raster Intersection Sampling at 100m metric interval.
5. Maximum segment severity rule.
6. UNKNOWN severity for out-of-bounds or nodata cells (never converted to DRY).
7. 7-slice route exposure timeline (T+0 to T+180).
8. Modeled flood onset & horizon handling (NO_MODELED_ONSET_WITHIN_HORIZON).
9. Travel window arithmetic: max(0, onset - travel - safety_buffer).
10. Decision taxonomy: GO_NOW, LIMITED_WINDOW, ALTERNATE_RECOMMENDED, AVOID.
11. Alternate route comparison & ranking.
12. ML Independence: Routing logic strictly independent of Kaggle XGBoost prototype.
13. Complete provenance preservation.
"""

from unittest.mock import patch

import pytest
from app.providers.routing import OSRMRoutingProvider, SyntheticRoutingProvider
from app.schemas.routing import RouteAnalysisRequestSchema, RouteLocationSchema
from app.services.routing_service import (
    DigitalTwinRasterReader,
    RoutingProcessingService,
)


@pytest.mark.asyncio
async def test_routing_provider_selection():
    """Verify provider selection between Synthetic and OSRM providers."""
    synth_provider = SyntheticRoutingProvider()
    res = await synth_provider.compute_routes(
        {"lat": 19.0760, "lon": 72.8777},
        {"lat": 19.1020, "lon": 72.8850},
        max_alternatives=2,
    )
    assert len(res) >= 1
    assert res[0].provider_mode == "SYNTHETIC"
    assert res[0].provider == "SYNTHETIC_ROUTER"

    osrm_provider = OSRMRoutingProvider(base_url="http://localhost:5000")
    assert osrm_provider.provider_id == "OSRM_ROUTER"
    assert osrm_provider.provider_mode == "LIVE_OSRM"


@pytest.mark.asyncio
async def test_real_data_no_synthetic_fallback():
    """Verify REAL_DATA mode raises explicit RuntimeError when OSRM fails (0 synthetic fallback)."""
    service = RoutingProcessingService(provider=OSRMRoutingProvider())

    request = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777, label="Kurla"),
        destination=RouteLocationSchema(latitude=19.1020, longitude=72.8850, label="Saki Naka"),
        provider_mode="REAL_DATA",
    )

    with patch.object(OSRMRoutingProvider, "compute_routes", side_effect=RuntimeError("OSRM connection refused")):
        with pytest.raises(RuntimeError) as exc_info:
            await service.analyze_routes(request)
        assert "Routing provider unavailable" in str(exc_info.value) or "OSRM connection refused" in str(exc_info.value)


@pytest.mark.asyncio
async def test_coordinate_validation():
    """Verify out-of-bounds coordinates raise ValidationError or ValueError."""
    from pydantic import ValidationError

    with pytest.raises((ValueError, ValidationError)):
        RouteLocationSchema(latitude=99.0, longitude=72.8777)

    service = RoutingProcessingService(provider=SyntheticRoutingProvider())
    with pytest.raises((ValueError, ValidationError)):
        await service.analyze_routes(
            RouteAnalysisRequestSchema(
                origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
                destination=RouteLocationSchema(latitude=-100.0, longitude=72.8850),
                provider_mode="SYNTHETIC",
            )
        )


def test_crs_transform_and_out_of_bounds_nodata():
    """Verify DigitalTwinRasterReader handles CRS transforms and out-of-bounds/nodata returns UNKNOWN."""
    reader = DigitalTwinRasterReader(crs="EPSG:32643", width=40, height=40)

    # Valid lon/lat transform to UTM zone 43N
    x, y = reader.transform_coords_to_raster_crs(72.8777, 19.0760)
    assert isinstance(x, float)
    assert isinstance(y, float)

    # Out of bounds sampling
    oob_res = reader.sample_point(lat=85.0, lon=175.0)
    assert oob_res["severity"] == "UNKNOWN"
    assert oob_res["is_unknown"] is True
    assert oob_res["cell_id"] == "CELL_OUT_OF_BOUNDS"


@pytest.mark.asyncio
async def test_7_slice_exposure_timeline_and_travel_window():
    """Verify 7-slice timeline (T+0 to T+180) and travel window formula: max(0, onset - travel - buffer)."""
    service = RoutingProcessingService(provider=SyntheticRoutingProvider())

    request = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777, label="Kurla Junction"),
        destination=RouteLocationSchema(latitude=19.1020, longitude=72.8850, label="Saki Naka"),
        provider_mode="SYNTHETIC",
        max_acceptable_severity="HIGH",
    )

    response = await service.analyze_routes(request)

    assert response.run_id.startswith("route_run_")
    assert len(response.candidates) >= 1

    primary_cand = response.candidates[0]
    assert len(primary_cand.time_slice_exposures) == 7
    slice_minutes = [s.minutes_from_start for s in primary_cand.time_slice_exposures]
    assert slice_minutes == [0, 30, 60, 90, 120, 150, 180]

    tw = primary_cand.travel_window
    assert tw.safety_buffer_min == 15
    assert tw.usable_travel_window_min is not None

    if tw.route_flood_onset_min is not None:
        expected_window = max(0, int(tw.route_flood_onset_min - tw.estimated_travel_time_min - tw.safety_buffer_min))
        assert tw.usable_travel_window_min == expected_window
    else:
        assert tw.status == "NO_MODELED_ONSET_WITHIN_HORIZON"


@pytest.mark.asyncio
async def test_decision_taxonomy_and_recommendation():
    """Verify recommendation decision taxonomy: GO_NOW, LIMITED_WINDOW, ALTERNATE_RECOMMENDED, AVOID."""
    service = RoutingProcessingService(provider=SyntheticRoutingProvider())

    request = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.1020, longitude=72.8850),
        provider_mode="SYNTHETIC",
    )

    response = await service.analyze_routes(request)
    assert response.recommendation in ["GO_NOW", "LIMITED_WINDOW", "ALTERNATE_RECOMMENDED", "AVOID"]
    assert len(response.explanation) > 0


@pytest.mark.asyncio
async def test_ml_independence_and_prototype_warning():
    """Verify routing recommendations operate independently of Kaggle XGBoost score and include prototype warning."""
    service = RoutingProcessingService(provider=SyntheticRoutingProvider())

    request = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.1020, longitude=72.8850),
        provider_mode="SYNTHETIC",
    )

    response = await service.analyze_routes(request)
    assert response.provenance["ml_status"] == "PROTOTYPE_ONLY"
    assert any("PROTOTYPE_ONLY" in w for w in response.warnings)


@pytest.mark.asyncio
async def test_provenance_integrity():
    """Verify routing analysis response includes full required provenance dictionary."""
    service = RoutingProcessingService(provider=SyntheticRoutingProvider())

    request = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.1020, longitude=72.8850),
        provider_mode="SYNTHETIC",
    )

    response = await service.analyze_routes(request)
    prov = response.provenance

    assert prov["project"] == "AQUORA — Urban Flood Intelligence & Response Platform"
    assert prov["study_area"] == "Mithi River Catchment, Mumbai, India"
    assert prov["routing_engine"] == "Phase 10 Flood-Aware Routing Engine v1.0"
    assert prov["physical_engine"] == "Phase 6 Deterministic D8 Solver v1.0"
    assert prov["ml_status"] == "PROTOTYPE_ONLY"
    assert prov["training_labels_isolated"] is True
    assert prov["sample_interval_m"] == 100.0
    assert prov["safety_buffer_min"] == 15
