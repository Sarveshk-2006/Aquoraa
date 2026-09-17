"""
Developer Verification Endpoints for Rainfall & Forecast Data Pipeline.

FOR INFRASTRUCTURE VERIFICATION ONLY.
DOES NOT EXPOSE FLOOD PREDICTIONS, RUNOFF, OR FLOOD DEPTH.
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from app.providers.forecast import SyntheticForecastProvider
from app.providers.rainfall import IMERGRainfallProvider
from app.schemas.geospatial import BoundingBox
from app.schemas.rainfall import (
    IngestionRunSchema,
    RainfallForecastSchema,
    RainfallObservationSchema,
)
from app.services.ingestion.rain_service import (
    ForecastIngestionService,
    RainfallIngestionService,
)

router = APIRouter(prefix="/rainfall", tags=["Rainfall Pipeline"])


@router.get(
    "/observations/latest",
    response_model=RainfallObservationSchema,
    summary="Get Latest Rainfall Observation Grid Metadata (IMERG)"
)
async def get_latest_observation(
    variant: str = Query("Final", description="IMERG Product Variant: Final, Late, Early")
) -> RainfallObservationSchema:
    """
    Developer verification endpoint for latest NASA GPM IMERG rainfall observation record.
    """
    provider = IMERGRainfallProvider()
    service = RainfallIngestionService()
    bbox = BoundingBox(minx=12.4, miny=41.8, maxx=12.6, maxy=42.0)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)

    obs, _ = await service.ingest_observation(
        provider=provider,
        bbox=bbox,
        start_time=start_time,
        end_time=end_time,
        product_variant=variant
    )
    return obs


@router.get(
    "/forecasts/latest",
    response_model=list[RainfallForecastSchema],
    summary="Get Latest 0-3 Hour Horizon Forecast Grids"
)
async def get_latest_forecasts() -> list[RainfallForecastSchema]:
    """
    Developer verification endpoint for 0-3 hour precipitation forecast horizons (+0m to +180m).
    """
    provider = SyntheticForecastProvider()
    service = ForecastIngestionService()
    bbox = BoundingBox(minx=12.4, miny=41.8, maxx=12.6, maxy=42.0)
    init_time = datetime.utcnow()

    forecasts, _ = await service.ingest_0_3h_horizon(
        provider=provider,
        bbox=bbox,
        initialization_time=init_time
    )
    return forecasts


@router.get(
    "/ingestion-runs",
    response_model=list[IngestionRunSchema],
    summary="Get Recent Data Ingestion Audit Execution Logs"
)
async def get_ingestion_runs() -> list[IngestionRunSchema]:
    """
    Developer verification endpoint for recent ingestion run audit records.
    """
    provider_rain = IMERGRainfallProvider()
    service_rain = RainfallIngestionService()
    bbox = BoundingBox(minx=12.4, miny=41.8, maxx=12.6, maxy=42.0)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=30)

    _, run_obs = await service_rain.ingest_observation(
        provider=provider_rain,
        bbox=bbox,
        start_time=start_time,
        end_time=end_time
    )

    provider_fcst = SyntheticForecastProvider()
    service_fcst = ForecastIngestionService()
    _, run_fcst = await service_fcst.ingest_0_3h_horizon(
        provider=provider_fcst,
        bbox=bbox,
        initialization_time=end_time
    )

    return [run_obs, run_fcst]
