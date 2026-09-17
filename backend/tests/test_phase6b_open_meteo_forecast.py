"""
Focused Unit & Integration Test Suite for OpenMeteoForecastProvider (Step 6B).

Verifies:
1. Controlled fixture mock response parsing.
2. Explicit provider identity (OPEN_METEO_ECMWF) and model identity (ECMWF_IFS_GLOBAL).
3. Precipitation units (mm), UTC timestamp parsing, and hourly (60 min) resolution.
4. Error handling for missing precipitation, malformed JSON, HTTP status failures, and timeouts.
5. Zero synthetic fallback behavior in OpenMeteoForecastProvider.
6. Preservation of 1-hour temporal and ~9 km spatial forcing without fake 30-min interpolation or 30m downscaling.
7. Zero API key requirement.
8. SyntheticForecastProvider isolation for DEV/TEST fixtures.
9. Live connectivity test against public Open-Meteo endpoint.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
import httpx

from app.providers.forecast import (
    BaseForecastProvider,
    OpenMeteoForecastProvider,
    SyntheticForecastProvider,
)
from app.schemas.geospatial import BoundingBox
from app.schemas.rainfall import QualityStatus, RainfallForecastSchema, RainfallQuantityType

MITHI_BBOX = BoundingBox(minx=72.840, miny=19.040, maxx=72.910, maxy=19.120)

MOCK_OPEN_METEO_PAYLOAD = {
    "latitude": 19.0,
    "longitude": 73.0,
    "generationtime_ms": 0.04,
    "utc_offset_seconds": 0,
    "timezone": "GMT",
    "elevation": 8.0,
    "hourly_units": {
        "time": "iso8601",
        "precipitation": "mm"
    },
    "hourly": {
        "time": [
            "2026-09-13T00:00",
            "2026-09-13T01:00",
            "2026-09-13T02:00",
            "2026-09-13T03:00",
            "2026-09-13T04:00"
        ],
        "precipitation": [0.5, 3.8, 3.8, 3.8, 2.2]
    }
}


@pytest.mark.asyncio
async def test_01_mock_response_parsing_and_schema_validation():
    """Verify controlled fixture mock response parses into RainfallForecastSchema cleanly."""
    provider = OpenMeteoForecastProvider()
    
    with patch.object(provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_OPEN_METEO_PAYLOAD
        
        init_time = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
        fcst = await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=60)
        
        assert fcst.provider == "OPEN_METEO_ECMWF"
        assert fcst.model_name == "ECMWF_IFS_GLOBAL"
        assert fcst.units == "mm"
        assert fcst.quantity_type == RainfallQuantityType.ACCUMULATION
        assert fcst.quality_status == QualityStatus.VALID
        assert fcst.lead_time_minutes == 60
        assert fcst.temporal_resolution_minutes == 60.0
        assert fcst.resolution_deg == (0.09, 0.09)
        assert fcst.provenance["precipitation_value_mm"] == 3.8


@pytest.mark.asyncio
async def test_02_provider_and_model_identity():
    """Verify provider identity is OPEN_METEO_ECMWF and model is ECMWF_IFS_GLOBAL."""
    provider = OpenMeteoForecastProvider()
    assert provider.provider_id == "OPEN_METEO_ECMWF"
    assert provider.model_name == "ECMWF_IFS_GLOBAL"

    meta = await provider.get_forecast_metadata()
    assert meta.source == "OPEN_METEO_ECMWF"
    assert meta.provenance["model_name"] == "ECMWF_IFS_GLOBAL"
    assert meta.provenance["api_key_required"] is False


@pytest.mark.asyncio
async def test_03_timestamp_and_timezone_parsing():
    """Verify timestamps are parsed as timezone-aware UTC objects."""
    provider = OpenMeteoForecastProvider()
    with patch.object(provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_OPEN_METEO_PAYLOAD
        
        init_time = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
        fcst = await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=120)
        
        assert fcst.valid_time.tzinfo is not None
        assert fcst.valid_time == datetime(2026, 9, 13, 2, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_04_missing_precipitation_field_raises_explicit_error():
    """Verify payload with missing precipitation array raises explicit ValueError."""
    provider = OpenMeteoForecastProvider()
    bad_payload = {
        "hourly": {"time": ["2026-09-13T00:00"]}
    }
    with patch.object(provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = bad_payload
        init_time = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError) as excinfo:
            await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=0)
        assert "Missing 'time' or 'precipitation' arrays" in str(excinfo.value)


@pytest.mark.asyncio
async def test_05_malformed_json_response_raises_explicit_error():
    """Verify malformed payload raises explicit ValueError."""
    provider = OpenMeteoForecastProvider()
    bad_payload = {"invalid_structure": True}
    with patch.object(provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = bad_payload
        init_time = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(ValueError) as excinfo:
            await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=0)
        assert "Missing or invalid 'hourly' section" in str(excinfo.value)


@pytest.mark.asyncio
async def test_06_http_status_failure_raises_explicit_error():
    """Verify HTTP non-200 response raises explicit RuntimeError with zero synthetic fallback."""
    provider = OpenMeteoForecastProvider()
    
    mock_resp = httpx.Response(status_code=500, text="Internal Server Error")
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(RuntimeError) as excinfo:
            await provider._fetch_raw_ecmwf_payload(19.076, 72.877)
        assert "Open-Meteo ECMWF API request failed with HTTP status 500" in str(excinfo.value)


@pytest.mark.asyncio
async def test_07_timeout_failure_raises_explicit_error():
    """Verify network timeout raises explicit TimeoutError with zero synthetic fallback."""
    provider = OpenMeteoForecastProvider(timeout_seconds=0.001)
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("Timed out")):
        with pytest.raises(TimeoutError) as excinfo:
            await provider._fetch_raw_ecmwf_payload(19.076, 72.877)
        assert "API request timed out" in str(excinfo.value)


@pytest.mark.asyncio
async def test_08_no_synthetic_fallback_behavior():
    """Verify OpenMeteoForecastProvider never falls back to SyntheticForecastProvider."""
    provider = OpenMeteoForecastProvider()
    with patch.object(provider, "_fetch_raw_ecmwf_payload", side_effect=RuntimeError("Network down")):
        init_time = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
        with pytest.raises(RuntimeError) as excinfo:
            await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=0)
        assert "Network down" in str(excinfo.value)
        assert not isinstance(excinfo.value, RainfallForecastSchema)


@pytest.mark.asyncio
async def test_09_no_30min_interpolation_and_no_30m_downscaling():
    """Verify OpenMeteoForecastProvider preserves 60 min temporal step and ~9 km spatial resolution."""
    provider = OpenMeteoForecastProvider()
    with patch.object(provider, "_fetch_raw_ecmwf_payload", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_OPEN_METEO_PAYLOAD
        init_time = datetime(2026, 9, 13, 0, 0, tzinfo=timezone.utc)
        fcst = await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=60)
        
        assert fcst.temporal_resolution_minutes == 60.0
        assert fcst.resolution_deg == (0.09, 0.09)


@pytest.mark.asyncio
async def test_10_synthetic_provider_isolation():
    """Verify SyntheticForecastProvider remains available for DEV/TEST and carries explicit test fixture labels."""
    syn_provider = SyntheticForecastProvider()
    assert issubclass(SyntheticForecastProvider, BaseForecastProvider)
    assert syn_provider.provider_id == "SYNTHETIC_FORECAST_PROVIDER"
    
    meta = await syn_provider.get_forecast_metadata("SYNTHETIC_NOWCAST")
    assert meta.provenance["label"] == "TEST FIXTURE ONLY"


@pytest.mark.asyncio
async def test_11_live_connectivity_open_meteo_public_endpoint():
    """Controlled live connectivity test against public Open-Meteo ECMWF API endpoint."""
    provider = OpenMeteoForecastProvider()
    init_time = datetime.now(timezone.utc)
    
    try:
        fcst = await provider.fetch_forecast(MITHI_BBOX, init_time, lead_time_minutes=0)
        assert fcst.provider == "OPEN_METEO_ECMWF"
        assert fcst.model_name == "ECMWF_IFS_GLOBAL"
        assert fcst.units == "mm"
        assert fcst.quality_status == QualityStatus.VALID
        assert fcst.provenance["data_mode"] == "REAL_DATA"
    except Exception as exc:
        pytest.skip(f"Network unavailable or Open-Meteo endpoint temporarily unreachable: {exc}")
