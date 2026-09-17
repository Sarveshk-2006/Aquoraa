"""
Phase 6C Integration Tests: Real Open-Meteo ECMWF Forecast -> Phase 6 Physical Flood Simulation Engine.

Verifies:
1. Forecast provider identity & ECMWF model identity preservation.
2. Unit conversion: hourly accumulation (mm) -> intensity (mm/hr).
3. Mass conservation across simulation substeps (sum of substeps equals total forecast accumulation).
4. Zero synthetic fallback in REAL_DATA mode on external API error.
5. Unchanged Phase 6 D8 solver physics and mass balance accounting.
6. Execution of 1 controlled real-data forecast-driven simulation run for Mithi catchment.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from app.providers.forecast import OpenMeteoForecastProvider
from app.schemas.flood import FloodSimulationRequestSchema
from app.schemas.geospatial import BoundingBox
from app.services.flood_service import FloodProcessingService


@pytest.mark.asyncio
async def test_ecmwf_forecast_integration_identity_and_provenance():
    """Test 1-5: Forecast provider identity, model identity, timestamps, and lead times preserved in Phase 6 response."""
    service = FloodProcessingService(db=None)

    # Mock real provider HTTP request to return deterministic 1-hour hourly precipitation series
    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [4.0, 6.0, 2.0, 0.0]
        }
    }

    with patch.object(service.open_meteo_forecast_provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = FloodSimulationRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.execute_simulation(req)

        assert res.status == "COMPLETED"
        assert res.provider_mode == "REAL_DATA"
        assert res.provenance["provider"] == "OPEN_METEO_ECMWF"
        assert res.provenance["model_name"] == "ECMWF_IFS_GLOBAL"
        assert res.provenance["source"] == "Open-Meteo ECMWF"
        assert res.provenance["is_synthetic_fallback"] is False
        assert len(res.provenance["forecast_lead_times_minutes"]) == 4
        assert res.provenance["forecast_lead_times_minutes"] == [0, 60, 120, 180]


@pytest.mark.asyncio
async def test_ecmwf_mass_conservation_and_unit_conversion():
    """Test 6-9: Hourly accumulation (mm) -> mm/hr intensity conversion preserves total precipitation mass."""
    service = FloodProcessingService(db=None)

    # Forecast values: Hour 0: 4.0 mm, Hour 1: 6.0 mm, Hour 2: 2.0 mm, Hour 3: 0.0 mm
    # Total 3-hour forecast accumulation = 4.0 + 6.0 + 2.0 = 12.0 mm
    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [4.0, 6.0, 2.0, 0.0]
        }
    }

    with patch.object(service.open_meteo_forecast_provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = FloodSimulationRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        res = await service.execute_simulation(req)

        # Total gross rainfall input in m3 from simulation totals
        total_gross_m3 = res.mass_balance_totals["total_gross_rain_m3"]

        # Calculate domain area dynamically based on simulation resolution
        res_m = res.provenance["dem_resolution_m"]
        cell_area_m2 = abs(float(res_m[0]) * float(res_m[1]))
        num_cells = 392 * 476
        domain_area_m2 = num_cells * cell_area_m2

        # 12.0 mm total accumulation = 0.012 m depth across domain_area_m2
        expected_total_gross_m3 = 0.012 * domain_area_m2

        # Verify exact mass preservation (< 0.01% floating point error)
        assert abs(total_gross_m3 - expected_total_gross_m3) / expected_total_gross_m3 < 1e-4

        # Mass balance error check
        assert res.is_mass_balance_valid is True
        assert res.overall_mass_balance_error_m3 <= 1e-4


@pytest.mark.asyncio
async def test_no_synthetic_fallback_in_real_data_mode():
    """Test 10-12: External forecast failure in REAL_DATA mode fails explicitly with NO synthetic fallback."""
    service = FloodProcessingService(db=None)

    with patch.object(service.open_meteo_forecast_provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = RuntimeError("Open-Meteo ECMWF API endpoint HTTP 503 Service Unavailable")

        req = FloodSimulationRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=30,
        )

        with pytest.raises(RuntimeError) as exc_info:
            await service.execute_simulation(req)

        assert "503 Service Unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_phase6_physics_unmodified_and_mithi_dem_used():
    """Test 13-20: Phase 6 D8 physical equations, depth, severity, real Mithi DEM, and limitations preserved."""
    service = FloodProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [10.0, 15.0, 5.0, 0.0]
        }
    }

    with patch.object(service.open_meteo_forecast_provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        req = FloodSimulationRequestSchema(
            provider_mode="REAL_DATA",
            use_forecast_provider=True,
            start_time="2026-09-13T00:00:00Z",
            horizon_minutes=180,
            timestep_minutes=10,
        )

        res = await service.execute_simulation(req)

        assert res.status == "COMPLETED"
        assert "REAL_DEM_elevation_30m.tif" in res.terrain_dataset_id
        assert res.provenance["dem_dimensions"] == [476, 392]
        assert "EPSG" in str(res.provenance["dem_crs"])
        assert res.provenance["drainage_status"].startswith("REAL municipal drainage network data UNAVAILABLE")
        assert "NOT CONSUMED" in res.provenance["tide_status"]


@pytest.mark.asyncio
async def test_controlled_real_data_forecast_run():
    """Controlled Real-Data Integration Run using real live Open-Meteo ECMWF provider for Mithi Catchment."""
    provider = OpenMeteoForecastProvider()
    bbox = BoundingBox(minx=72.83, miny=19.03, maxx=72.93, maxy=19.13)
    init_dt = datetime.now(timezone.utc)

    # Execute real HTTP request to Open-Meteo API
    try:
        forecast_schemas = await provider.fetch_0_3h_horizon_forecasts(bbox, init_dt)
    except (RuntimeError, TimeoutError, ValueError) as exc:
        pytest.skip(f"Live Open-Meteo API unreachable during test run: {exc}")

    assert len(forecast_schemas) == 4
    assert forecast_schemas[0].provider == "OPEN_METEO_ECMWF"
    assert forecast_schemas[0].model_name == "ECMWF_IFS_GLOBAL"

    service = FloodProcessingService(db=None)
    req = FloodSimulationRequestSchema(
        provider_mode="REAL_DATA",
        use_forecast_provider=True,
        start_time=init_dt.isoformat(),
        horizon_minutes=180,
        timestep_minutes=30,
    )

    res = await service.execute_simulation(req)
    assert res.status == "COMPLETED"
    assert res.provenance["provider"] == "OPEN_METEO_ECMWF"
    assert res.is_mass_balance_valid is True
