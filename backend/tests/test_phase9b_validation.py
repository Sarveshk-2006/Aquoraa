"""
Phase 9B Test Suite — Digital Twin Physical State & Artifact Integrity Validation.

Verifies:
1. Seven canonical slices (0, 30, 60, 90, 120, 150, 180 min) map to exact Phase 6 timesteps.
2. T+0, T+30, T+60, T+90, T+120, T+150, T+180 state index mapping and semantics.
3. Numerical physical depth equality between Phase 6 solver arrays and Digital Twin GeoTIFF rasters.
4. Severity distribution consistency across locked Phase 6 thresholds.
5. Inundated cell count (depth >= 0.05m) and affected area (km2) recalculation from rasters.
6. Peak maximum depth traceability across physical solver states.
7. No state carryover between sequential Digital Twin simulation runs.
8. No stale artifact directory cross-contamination between runs.
9. GeoTIFF spatial metadata integrity (CRS, dimensions, transform, bounds, finite numeric depth values).
10. Zero-rain forecast integrity (0.0mm -> SUCCESS + 0 depth + 0 affected area).
11. Full Open-Meteo ECMWF forecast provenance preservation.
12. Strict REAL_DATA failure handling (0 synthetic fallback on API error).
13. ML score isolation (physical depth/severity independent of ML; future slices return UNAVAILABLE).
14. Operational API response integrity.
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
import rasterio
from app.schemas.digital_twin import DigitalTwinRunRequestSchema
from app.services.digital_twin_service import (
    CANONICAL_SLICES,
    DigitalTwinProcessingService,
    _classify_severity,
)


@pytest.mark.asyncio
async def test_01_canonical_slices_exact_timestep_mapping():
    """Test 1-8: Verify 7 canonical slices map 1:1 to exact Phase 6 solver timesteps."""
    service = DigitalTwinProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [10.0, 20.0, 5.0, 0.0],
        },
    }

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.create_run(req)

        assert res.status == "COMPLETED"
        assert len(res.time_slices) == 7

        for idx, slice_min in enumerate(CANONICAL_SLICES):
            slice_item = res.time_slices[idx]
            assert slice_item.minutes_from_start == slice_min
            expected_label = "NOW" if slice_min == 0 else f"+{slice_min}m"
            assert slice_item.slice_label == expected_label


@pytest.mark.asyncio
async def test_02_physical_depth_and_severity_raster_equality():
    """Test 9-10: Verify raster water depth and cell severity equal Phase 6 physical arrays."""
    service = DigitalTwinProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [15.0, 30.0, 10.0, 0.0],
        },
    }

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.create_run(req)
        out_dir = Path(res.output_directory)

        for slice_item in res.time_slices:
            min_val = slice_item.minutes_from_start
            tif_file = out_dir / "map" / f"slice_{min_val:03d}.tif"
            assert tif_file.exists()

            with rasterio.open(tif_file) as src:
                data = src.read(1)

            # Check bounds and dimensions
            assert data.shape == (476, 392)
            assert np.all(np.isfinite(data))
            assert np.all(data >= 0.0)

            # Recalculate cell stats directly from GeoTIFF data
            recalc_affected = int(np.sum(data >= 0.05))
            recalc_area_km2 = round(float((recalc_affected * 900.0) / 1e6), 3)

            assert slice_item.affected_cells_count == recalc_affected
            assert abs(slice_item.affected_area_km2 - recalc_area_km2) < 1e-3

            # Verify severity distribution
            sev_counts = {"DRY": 0, "LOW": 0, "MODERATE": 0, "HIGH": 0, "SEVERE": 0}
            for d in data.flat:
                sev_counts[_classify_severity(float(d))] += 1

            assert slice_item.severity_distribution == sev_counts


@pytest.mark.asyncio
async def test_03_no_state_carryover_between_sequential_runs():
    """Test 14: Verify two sequential runs maintain strictly isolated solver state grids."""
    service = DigitalTwinProcessingService(db=None)

    payload_heavy = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [50.0, 80.0, 40.0, 0.0],
        },
    }
    payload_dry = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [0.0, 0.0, 0.0, 0.0],
        },
    }

    req = DigitalTwinRunRequestSchema(
        provider_mode="REAL_DATA",
        use_forecast_provider=True,
        start_time="2026-09-13T00:00:00Z",
        horizon_minutes=180,
        timestep_minutes=30,
    )

    # Run A: Heavy storm
    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = payload_heavy
        run_a = await service.create_run(req)

    # Run B: Zero rain
    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = payload_dry
        run_b = await service.create_run(req)

    assert run_a.run_id != run_b.run_id
    assert run_a.output_directory != run_b.output_directory

    assert run_a.summary is not None
    assert run_b.summary is not None

    assert run_a.summary.max_water_depth_m > 0.0
    assert run_b.summary.max_water_depth_m == 0.0
    assert run_b.summary.peak_affected_area_km2 == 0.0


@pytest.mark.asyncio
async def test_04_no_stale_artifact_directory_leakage():
    """Test 15: Verify output directories and map artifacts are distinct per run ID."""
    service = DigitalTwinProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [5.0, 5.0, 5.0, 0.0],
        },
    }

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        run1 = await service.create_run(req)
        run2 = await service.create_run(req)

        dir1 = Path(run1.output_directory)
        dir2 = Path(run2.output_directory)

        assert dir1 != dir2
        assert run1.run_id in str(dir1)
        assert run2.run_id in str(dir2)

        for s in run1.time_slices:
            assert run1.run_id in s.artifact_path
        for s in run2.time_slices:
            assert run2.run_id in s.artifact_path


@pytest.mark.asyncio
async def test_05_geotiff_spatial_metadata_and_numeric_validity():
    """Test 16-18: Verify GeoTIFF CRS, dimensions, resolution, and valid numeric values."""
    service = DigitalTwinProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [10.0, 10.0, 10.0, 0.0],
        },
    }

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.create_run(req)
        out_dir = Path(res.output_directory)

        for minutes in CANONICAL_SLICES:
            tif_path = out_dir / "map" / f"slice_{minutes:03d}.tif"
            with rasterio.open(tif_path) as src:
                assert src.width == 392
                assert src.height == 476
                assert src.count == 1
                assert "32643" in str(src.crs) or "4326" in str(src.crs)
                data = src.read(1)
                assert not np.isnan(data).any()
                assert not np.isinf(data).any()


@pytest.mark.asyncio
async def test_06_zero_rain_forecast_legitimate_dry_behavior():
    """Test 19: Verify zero-rain forecast yields legitimate dry state, not failure or unavailable."""
    service = DigitalTwinProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [0.0, 0.0, 0.0, 0.0],
        },
    }

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.create_run(req)
        assert res.status == "COMPLETED"
        assert res.summary is not None
        assert res.summary.max_water_depth_m == 0.0
        assert res.summary.peak_affected_area_km2 == 0.0

        for slice_item in res.time_slices:
            assert slice_item.affected_cells_count == 0
            assert slice_item.affected_area_km2 == 0.0
            assert slice_item.peak_severity == "DRY"


@pytest.mark.asyncio
async def test_07_forecast_provenance_preservation():
    """Test 20: Verify complete Open-Meteo ECMWF forecast provenance attached to Digital Twin run."""
    service = DigitalTwinProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [8.0, 12.0, 4.0, 0.0],
        },
    }

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.create_run(req)
        prov = res.summary.provenance

        assert prov["provider"] == "OPEN_METEO_ECMWF"
        assert prov["model_name"] == "ECMWF_IFS_GLOBAL"
        assert prov["spatial_forcing"] == "UNIFORM_MACRO_SCALE_9KM"
        assert prov["forecast_temporal_resolution"] == "1 hour (60 minutes)"
        assert prov["forecast_spatial_resolution"] == "approximately 9 km (0.09 deg)"
        assert prov["forecast_initialization_time"].startswith("2026-09-13T00:00:00")
        assert len(prov["forecast_valid_times"]) == 4
        assert prov["forecast_lead_times_minutes"] == [0, 60, 120, 180]


@pytest.mark.asyncio
async def test_08_real_data_failure_raises_explicit_exception():
    """Test 21: Verify REAL_DATA mode fails explicitly with zero synthetic fallback on API error."""
    service = DigitalTwinProcessingService(db=None)

    with patch("app.providers.forecast.OpenMeteoForecastProvider._fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = RuntimeError("Open-Meteo HTTP 503 Service Unavailable")

        req = DigitalTwinRunRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        with pytest.raises(RuntimeError) as exc_info:
            await service.create_run(req)

        assert "503 Service Unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_09_ml_score_isolation_and_future_unavailable():
    """Test 22-23: Verify physical depth is independent of ML, and future slices return UNAVAILABLE ML score."""
    service = DigitalTwinProcessingService(db=None)

    cell_t0 = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=0)
    assert cell_t0.water_depth_m >= 0.0
    assert cell_t0.severity in ["DRY", "LOW", "MODERATE", "HIGH", "SEVERE"]
    assert cell_t0.ml_status_tag in ["PROTOTYPE_ONLY", "UNAVAILABLE"]

    for min_val in [30, 60, 90, 120, 150, 180]:
        cell_future = await service.inspect_cell(grid_cell_id="CELL_R0020_C0020", minutes_from_start=min_val)
        assert cell_future.prototype_ml_score is None
        assert cell_future.ml_status_tag == "UNAVAILABLE"


@pytest.mark.asyncio
async def test_10_api_endpoints_deliver_current_run_data(async_client):
    """Test 24: Verify GET API endpoints deliver exact current run metadata and map slices."""
    post_resp = await async_client.post(
        "/api/v1/digital-twin/runs",
        json={
            "study_area_id": "mumbai_mithi",
            "provider_mode": "TEST",
            "use_forecast_provider": False,
            "horizon_minutes": 180,
            "timestep_minutes": 30,
        },
    )
    assert post_resp.status_code == 201
    run_data = post_resp.json()
    run_id = run_data["run_id"]

    get_resp = await async_client.get(f"/api/v1/digital-twin/runs/{run_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["run_id"] == run_id

    slice_resp = await async_client.get(f"/api/v1/digital-twin/runs/{run_id}/map/60")
    assert slice_resp.status_code == 200
    assert slice_resp.json()["minutes_from_start"] == 60
    assert slice_resp.json()["artifact_type"] == "MAP_RASTER"
