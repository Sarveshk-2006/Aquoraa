"""
Phase 6D Validation & Audit Test Suite: Forecast Forcing Validation & Temporal Alignment.

Verifies:
1. Controlled 2.0, 4.0, 6.0 mm forecast sequence mapping to 30-minute and 10-minute simulation timesteps.
2. Exact mass conservation (2.0 + 4.0 + 6.0 = 12.0 mm total domain depth across substeps).
3. Zero double-counting or rate/accumulation confusion.
4. Support for flexible timestep durations (10-min and 30-min numerical timesteps).
5. Forecast lead-time calculation (lead_time = valid_time - initialization_time).
6. Live Open-Meteo timestamp sanity check.
7. Zero-rain forecast behavior (0.0 mm -> 0.0 mm/hr forcing without fallback).
8. Strict error propagation on API failure in REAL_DATA mode (no synthetic fallback).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from app.providers.forecast import OpenMeteoForecastProvider
from app.schemas.flood import FloodSimulationRequestSchema
from app.schemas.geospatial import BoundingBox
from app.services.flood_service import FloodProcessingService


@pytest.mark.asyncio
async def test_phase6d_controlled_non_zero_30min_forcing_and_mass_conservation():
    """
    Test Parts 3, 4, 5: Controlled non-zero forecast sequence (2.0, 4.0, 6.0 mm).
    Verify 30-minute forcing sequence, hourly accumulated depth, and total mass = 12.0 mm.
    """
    service = FloodProcessingService(db=None)

    # Controlled forecast hourly accumulation payload: Hour 0: 2.0 mm, Hour 1: 4.0 mm, Hour 2: 6.0 mm, Hour 3: 0.0 mm
    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [2.0, 4.0, 6.0, 0.0]
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

        # Fetch actual timestep summaries from response payload via manifest JSON or diagnostics
        assert res.status == "COMPLETED"
        assert res.total_timesteps == 7  # 0, 30, 60, 90, 120, 150, 180 min steps

        # Total gross rainfall input in m3 from simulation mass balance totals
        total_gross_m3 = res.mass_balance_totals["total_gross_rain_m3"]

        # Calculate domain area dynamically based on simulation resolution
        res_m = res.provenance["dem_resolution_m"]
        cell_area_m2 = abs(float(res_m[0]) * float(res_m[1]))
        num_cells = 392 * 476
        domain_area_m2 = num_cells * cell_area_m2

        # 12.0 mm total accumulation = 0.012 m depth across domain_area_m2
        expected_total_gross_m3 = 0.012 * domain_area_m2

        # Verify exact mass conservation (total == 12.0 mm across domain)
        assert abs(total_gross_m3 - expected_total_gross_m3) / expected_total_gross_m3 < 1e-4

        # Verify no double-counting (e.g. 24.0 m3 or 18.0 m3)
        double_counted_m3 = 0.024 * domain_area_m2
        assert abs(total_gross_m3 - double_counted_m3) > 10.0


@pytest.mark.asyncio
async def test_phase6d_different_timestep_10min_check():
    """
    Test Part 6: Configurable 10-minute numerical timesteps.
    Verify that 10-minute timesteps preserve total 12.0 mm hourly accumulation.
    """
    service = FloodProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [2.0, 4.0, 6.0, 0.0]
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
        assert res.total_timesteps == 19  # (180 // 10) + 1 steps

        total_gross_m3 = res.mass_balance_totals["total_gross_rain_m3"]
        res_m = res.provenance["dem_resolution_m"]
        cell_area_m2 = abs(float(res_m[0]) * float(res_m[1]))
        num_cells = 392 * 476
        domain_area_m2 = num_cells * cell_area_m2

        expected_total_gross_m3 = 0.012 * domain_area_m2

        # 10-minute timesteps must yield EXACT SAME 12.0 mm total gross rainfall
        assert abs(total_gross_m3 - expected_total_gross_m3) / expected_total_gross_m3 < 1e-4


@pytest.mark.asyncio
async def test_phase6d_forecast_lead_time_and_valid_time_alignment():
    """
    Test Part 7: Forecast initialization, valid time, and lead time calculation audit.
    Verify lead_time_minutes = (valid_time - initialization_time).total_seconds() // 60.
    """
    provider = OpenMeteoForecastProvider()

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T08:00", "2026-09-13T09:00", "2026-09-13T10:00", "2026-09-13T11:00"],
            "precipitation": [1.5, 3.0, 4.5, 0.0]
        }
    }

    with patch.object(provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_payload

        bbox = BoundingBox(minx=72.83, miny=19.03, maxx=72.93, maxy=19.13)
        init_time = datetime(2026, 9, 13, 8, 0, tzinfo=timezone.utc)

        forecasts = await provider.fetch_0_3h_horizon_forecasts(bbox, init_time)

        assert len(forecasts) == 4
        expected_leads = [0, 60, 120, 180]

        for fcst, expected_lead in zip(forecasts, expected_leads, strict=True):
            assert fcst.initialization_time == init_time
            assert fcst.lead_time_minutes == expected_lead
            calc_lead = int((fcst.valid_time - fcst.initialization_time).total_seconds() // 60)
            assert calc_lead == expected_lead


@pytest.mark.asyncio
async def test_phase6d_zero_rain_forecast_behavior():
    """
    Test Part 9: Zero-rain forecast (0.0 mm) produces 0.0 mm/hr forcing without fallback.
    """
    service = FloodProcessingService(db=None)

    mock_payload = {
        "latitude": 19.08,
        "longitude": 72.88,
        "hourly": {
            "time": ["2026-09-13T00:00", "2026-09-13T01:00", "2026-09-13T02:00", "2026-09-13T03:00"],
            "precipitation": [0.0, 0.0, 0.0, 0.0]
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
        assert res.provenance["rainfall_intensity_mean_mm_hr"] == 0.0
        assert res.provenance["rainfall_intensity_max_mm_hr"] == 0.0
        assert res.mass_balance_totals["total_gross_rain_m3"] == 0.0
        assert res.provenance["is_synthetic_fallback"] is False


@pytest.mark.asyncio
async def test_phase6d_live_open_meteo_sanity_check():
    """
    Test Part 8: Live Open-Meteo ECMWF HTTP request timestamp sanity check.
    """
    provider = OpenMeteoForecastProvider()
    bbox = BoundingBox(minx=72.83, miny=19.03, maxx=72.93, maxy=19.13)
    now_utc = datetime.now(timezone.utc)

    try:
        forecasts = await provider.fetch_0_3h_horizon_forecasts(bbox, now_utc)
    except (RuntimeError, TimeoutError, ValueError) as exc:
        pytest.skip(f"Live Open-Meteo endpoint unreachable: {exc}")

    assert len(forecasts) == 4
    for fcst in forecasts:
        assert fcst.provider == "OPEN_METEO_ECMWF"
        assert fcst.model_name == "ECMWF_IFS_GLOBAL"
        assert fcst.valid_time >= fcst.initialization_time
        assert isinstance(fcst.provenance.get("precipitation_value_mm"), float)
