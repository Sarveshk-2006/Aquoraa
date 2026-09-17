"""
Comprehensive Unit Tests for Phase 3 Rainfall + Forecast Data Pipeline.

Tests unit conversion, quality semantics (NODATA vs 0.0), IMERG provider adapter,
Synthetic forecast provider, temporal/spatial semantics, ingestion services,
database models, and API endpoints.
"""

from datetime import datetime, timedelta

import pytest
from app.geospatial.units import (
    convert_accumulation_to_intensity,
    convert_inches_to_mm,
    convert_intensity_to_accumulation,
    convert_mm_to_inches,
    is_nodata_value,
)
from app.main import app
from app.models.rainfall import (
    IngestionRun,
    RainfallForecastGrid,
    RainfallObservationGrid,
)
from app.providers.forecast import SyntheticForecastProvider
from app.providers.rainfall import IMERGRainfallProvider
from app.schemas.geospatial import BoundingBox
from app.schemas.rainfall import QualityStatus
from app.services.ingestion.rain_service import (
    ForecastIngestionService,
    RainfallIngestionService,
)
from geoalchemy2 import WKTElement
from httpx import ASGITransport, AsyncClient

from tests.fixtures.rainfall_fixtures import (
    SAMPLE_BBOX,
)


def test_unit_conversion_and_quality_semantics():
    """Test unit conversions and critical NODATA vs 0.0 zero rainfall distinction."""
    # 5.0 mm accumulation over 30 minutes -> 10.0 mm/h intensity
    intensity = convert_accumulation_to_intensity(5.0, 30.0)
    assert intensity == 10.0

    # 12.0 mm/h intensity over 30 minutes -> 6.0 mm accumulation
    accumulation = convert_intensity_to_accumulation(12.0, 30.0)
    assert accumulation == 6.0

    # Inches to mm
    assert convert_inches_to_mm(1.0) == 25.4
    assert convert_mm_to_inches(25.4) == 1.0

    # Negative rainfall raises ValueError
    with pytest.raises(ValueError):
        convert_accumulation_to_intensity(-2.0, 30.0)

    # CRITICAL DISTINCTION: NODATA vs 0.0 zero rainfall
    assert is_nodata_value(-9999.0, nodata_sentinel=-9999.0) is True
    assert is_nodata_value(None) is True
    assert is_nodata_value(0.0, nodata_sentinel=-9999.0) is False  # Measured zero is NOT nodata


@pytest.mark.asyncio
async def test_imerg_rainfall_provider():
    """Test NASA GPM IMERG provider adapter structure and variant support."""
    provider = IMERGRainfallProvider()
    assert provider.provider_id == "NASA_GPM_IMERG"
    assert provider.version == "V07B"

    metadata = await provider.get_dataset_metadata("test_dataset")
    assert metadata.source == "NASA_GPM_IMERG"
    assert metadata.crs == "EPSG:4326"

    # Latitude availability check
    valid_bbox = BoundingBox(minx=12.0, miny=40.0, maxx=13.0, maxy=41.0)
    invalid_bbox = BoundingBox(minx=12.0, miny=70.0, maxx=13.0, maxy=75.0)  # > 60N
    assert await provider.check_availability(valid_bbox, datetime.utcnow()) is True
    assert await provider.check_availability(invalid_bbox, datetime.utcnow()) is False

    # Fetch observation
    now = datetime.utcnow()
    obs = await provider.fetch_observation(
        bbox=valid_bbox,
        start_time=now - timedelta(minutes=30),
        end_time=now,
        product_variant="Final"
    )
    assert obs.product_variant == "Final"
    assert obs.duration_minutes == 30.0
    assert obs.quality_status == QualityStatus.VALID

    # Invalid variant raises ValueError
    with pytest.raises(ValueError):
        await provider.fetch_observation(
            bbox=valid_bbox,
            start_time=now - timedelta(minutes=30),
            end_time=now,
            product_variant="INVALID_VARIANT"
        )


@pytest.mark.asyncio
async def test_synthetic_forecast_provider():
    """Test SyntheticForecastProvider 0-3h forecast horizon generation."""
    provider = SyntheticForecastProvider()
    assert provider.provider_id == "SYNTHETIC_FORECAST_PROVIDER"

    now = datetime.utcnow()
    forecasts = await provider.fetch_0_3h_horizon_forecasts(SAMPLE_BBOX, now)
    assert len(forecasts) == 7  # +0m, +30m, +60m, +90m, +120m, +150m, +180m

    # Lead times match
    expected_leads = [0, 30, 60, 90, 120, 150, 180]
    actual_leads = [f.lead_time_minutes for f in forecasts]
    assert actual_leads == expected_leads

    # Valid times match T0 + lead
    for fcst in forecasts:
        expected_valid = now + timedelta(minutes=fcst.lead_time_minutes)
        assert fcst.valid_time == expected_valid
        assert fcst.provenance["label"] == "TEST FIXTURE ONLY"


@pytest.mark.asyncio
async def test_rainfall_ingestion_services():
    """Test RainfallIngestionService and ForecastIngestionService execution and audit records."""
    rain_service = RainfallIngestionService()
    provider_rain = IMERGRainfallProvider()

    now = datetime.utcnow()
    start_time = now - timedelta(minutes=30)
    obs, run_audit = await rain_service.ingest_observation(
        provider=provider_rain,
        bbox=SAMPLE_BBOX,
        start_time=start_time,
        end_time=now
    )

    assert obs.dataset_identifier == run_audit.source_identifier
    assert run_audit.status == "SUCCESS"
    assert run_audit.pipeline_type == "RAINFALL"
    assert run_audit.records_ingested == 1

    # Repeat ingestion for exact same source metadata to test idempotency
    obs2, run_audit2 = await rain_service.ingest_observation(
        provider=provider_rain,
        bbox=SAMPLE_BBOX,
        start_time=start_time,
        end_time=now
    )
    assert obs2.dataset_identifier == obs.dataset_identifier
    assert obs2.provenance["idempotency_key"] == obs.provenance["idempotency_key"]

    # Forecast ingestion service
    fcst_service = ForecastIngestionService()
    provider_fcst = SyntheticForecastProvider()

    fcst_list, fcst_audit = await fcst_service.ingest_0_3h_horizon(
        provider=provider_fcst,
        bbox=SAMPLE_BBOX,
        initialization_time=now
    )

    assert len(fcst_list) == 7
    assert fcst_audit.status == "SUCCESS"
    assert fcst_audit.pipeline_type == "FORECAST"
    assert fcst_audit.records_ingested == 7


def test_rainfall_database_models_instantiation():
    """Test SQLAlchemy model creation for observation grids, forecast grids, and ingestion runs."""
    wkt_bounds = WKTElement("POLYGON((12.49 41.89, 12.50 41.89, 12.50 41.90, 12.49 41.90, 12.49 41.89))", srid=4326)
    now = datetime.utcnow()

    obs_grid = RainfallObservationGrid(
        dataset_identifier="GPM_3IMERG_20260912_0000_FINAL",
        provider="NASA_GPM_IMERG",
        product_variant="Final",
        product_version="V07B",
        observation_start=now - timedelta(minutes=30),
        observation_end=now,
        duration_minutes=30.0,
        geom_bounds=wkt_bounds,
        resolution_deg_x=0.1,
        resolution_deg_y=0.1,
        units="mm",
        quantity_type="ACCUMULATION",
        quality_status="VALID",
        provenance={"source": "TEST"},
        storage_pointer="data/processed/rainfall/obs_01.tif"
    )
    assert obs_grid.dataset_identifier == "GPM_3IMERG_20260912_0000_FINAL"
    assert obs_grid.quality_status == "VALID"

    fcst_grid = RainfallForecastGrid(
        dataset_identifier="FCST_20260912_0000_LEAD_60M",
        provider="SYNTHETIC_FORECAST_PROVIDER",
        model_name="SYNTHETIC_NOWCAST",
        model_version="SYNTHETIC_V1",
        initialization_time=now,
        valid_time=now + timedelta(minutes=60),
        lead_time_minutes=60,
        geom_bounds=wkt_bounds,
        resolution_deg_x=0.1,
        resolution_deg_y=0.1,
        units="mm",
        quality_status="VALID",
        provenance={"source": "TEST"},
        storage_pointer="data/processed/rainfall/fcst_60m.tif"
    )
    assert fcst_grid.lead_time_minutes == 60

    ingestion_run = IngestionRun(
        pipeline_type="RAINFALL",
        provider="NASA_GPM_IMERG",
        source_identifier="GPM_3IMERG_20260912_0000_FINAL",
        status="SUCCESS",
        records_ingested=1,
        error_message=None,
        started_at=now,
        completed_at=now + timedelta(seconds=2),
        provenance={"ingested": True}
    )
    assert ingestion_run.pipeline_type == "RAINFALL"
    assert ingestion_run.status == "SUCCESS"


@pytest.mark.asyncio
async def test_developer_rainfall_api_endpoints():
    """Test developer verification API endpoints (/api/v1/rainfall/)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # GET latest observation
        resp_obs = await client.get("/api/v1/rainfall/observations/latest")
        assert resp_obs.status_code == 200
        data_obs = resp_obs.json()
        assert data_obs["provider"] == "NASA_GPM_IMERG"
        assert data_obs["product_variant"] == "Final"

        # GET latest forecasts
        resp_fcst = await client.get("/api/v1/rainfall/forecasts/latest")
        assert resp_fcst.status_code == 200
        data_fcst = resp_fcst.json()
        assert len(data_fcst) == 7
        assert data_fcst[0]["provider"] == "SYNTHETIC_FORECAST_PROVIDER"

        # GET ingestion runs
        resp_runs = await client.get("/api/v1/rainfall/ingestion-runs")
        assert resp_runs.status_code == 200
        data_runs = resp_runs.json()
        assert len(data_runs) == 2
