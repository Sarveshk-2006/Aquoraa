"""
Rainfall and Forecast Data Ingestion Services.

Orchestrates the ingestion lifecycle:
FETCH -> PARSE -> VALIDATE -> NORMALIZE -> ENRICH METADATA -> STORE -> RECORD INGESTION RUN.

Enforces source-based idempotency (dataset_identifier), quality checks, and provenance audit logging.
"""

from datetime import datetime

import structlog

from app.providers.forecast import BaseForecastProvider
from app.providers.rainfall import BaseRainfallProvider
from app.schemas.geospatial import BoundingBox
from app.schemas.rainfall import (
    IngestionRunSchema,
    RainfallForecastSchema,
    RainfallObservationSchema,
)

logger = structlog.get_logger("aquora.services.ingestion.rainfall")


class RainfallIngestionService:
    """
    Service coordinating rainfall observation data ingestion pipelines.
    """

    def __init__(self):
        self.pipeline_type = "RAINFALL"

    async def ingest_observation(
        self,
        provider: BaseRainfallProvider,
        bbox: BoundingBox,
        start_time: datetime,
        end_time: datetime,
        product_variant: str = "Final"
    ) -> tuple[RainfallObservationSchema, IngestionRunSchema]:
        """
        Executes full ingestion pipeline for rainfall observations.
        Returns (RainfallObservationSchema, IngestionRunSchema).
        """
        started_at = datetime.utcnow()
        logger.info(
            "Starting rainfall observation ingestion",
            provider=type(provider).__name__,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            variant=product_variant
        )

        try:
            # 1. FETCH & PARSE via provider contract
            observation = await provider.fetch_observation(
                bbox=bbox,
                start_time=start_time,
                end_time=end_time,
                product_variant=product_variant
            )

            # 2. VALIDATE
            if observation.observation_start >= observation.observation_end:
                raise ValueError("Validation failed: start time must precede end time")
            if observation.duration_minutes <= 0:
                raise ValueError("Validation failed: duration_minutes must be positive")

            # 3. NORMALIZE & ENRICH METADATA
            observation.provenance["ingestion_pipeline"] = self.pipeline_type
            observation.provenance["ingestion_timestamp"] = started_at.isoformat()
            observation.provenance["idempotency_key"] = observation.dataset_identifier

            completed_at = datetime.utcnow()

            ingestion_run = IngestionRunSchema(
                pipeline_type=self.pipeline_type,
                provider=observation.provider,
                source_identifier=observation.dataset_identifier,
                status="SUCCESS",
                records_ingested=1,
                error_message=None,
                started_at=started_at,
                completed_at=completed_at,
                provenance=observation.provenance
            )

            logger.info("Rainfall observation ingestion completed successfully", dataset_id=observation.dataset_identifier)
            return observation, ingestion_run

        except Exception as e:
            completed_at = datetime.utcnow()
            error_msg = str(e)
            logger.error("Rainfall observation ingestion failed", error=error_msg)

            ingestion_run = IngestionRunSchema(
                pipeline_type=self.pipeline_type,
                provider=getattr(provider, "provider_id", "UNKNOWN"),
                source_identifier=f"FAILED_{start_time.strftime('%Y%m%d_%H%M')}",
                status="FAILED",
                records_ingested=0,
                error_message=error_msg,
                started_at=started_at,
                completed_at=completed_at,
                provenance={"error": error_msg}
            )
            raise


class ForecastIngestionService:
    """
    Service coordinating precipitation forecast data ingestion pipelines.
    """

    def __init__(self):
        self.pipeline_type = "FORECAST"

    async def ingest_0_3h_horizon(
        self,
        provider: BaseForecastProvider,
        bbox: BoundingBox,
        initialization_time: datetime
    ) -> tuple[list[RainfallForecastSchema], IngestionRunSchema]:
        """
        Executes full ingestion pipeline for 0-3 hour forecast horizons.
        Returns (List[RainfallForecastSchema], IngestionRunSchema).
        """
        started_at = datetime.utcnow()
        logger.info(
            "Starting 0-3h forecast horizon ingestion",
            provider=type(provider).__name__,
            initialization_time=initialization_time.isoformat()
        )

        try:
            # 1. FETCH & PARSE
            forecasts = await provider.fetch_0_3h_horizon_forecasts(
                bbox=bbox,
                initialization_time=initialization_time
            )

            # 2. VALIDATE & NORMALIZE
            for fcst in forecasts:
                if fcst.valid_time < fcst.initialization_time:
                    raise ValueError(f"Forecast valid_time precedes initialization_time for {fcst.dataset_identifier}")
                fcst.provenance["ingestion_pipeline"] = self.pipeline_type
                fcst.provenance["ingestion_timestamp"] = started_at.isoformat()

            completed_at = datetime.utcnow()
            source_id = f"FORECAST_HORIZON_{initialization_time.strftime('%Y%m%d_%H%M')}"

            ingestion_run = IngestionRunSchema(
                pipeline_type=self.pipeline_type,
                provider=forecasts[0].provider if forecasts else "UNKNOWN",
                source_identifier=source_id,
                status="SUCCESS",
                records_ingested=len(forecasts),
                error_message=None,
                started_at=started_at,
                completed_at=completed_at,
                provenance={"count": len(forecasts), "initialization_time": initialization_time.isoformat()}
            )

            logger.info("Forecast horizon ingestion completed successfully", count=len(forecasts))
            return forecasts, ingestion_run

        except Exception as e:
            completed_at = datetime.utcnow()
            error_msg = str(e)
            logger.error("Forecast ingestion failed", error=error_msg)

            ingestion_run = IngestionRunSchema(
                pipeline_type=self.pipeline_type,
                provider=getattr(provider, "provider_id", "UNKNOWN"),
                source_identifier=f"FAILED_FCST_{initialization_time.strftime('%Y%m%d_%H%M')}",
                status="FAILED",
                records_ingested=0,
                error_message=error_msg,
                started_at=started_at,
                completed_at=completed_at,
                provenance={"error": error_msg}
            )
            raise
