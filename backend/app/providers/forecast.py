"""
Precipitation Forecast Data Provider Contracts and Providers.

Provides vendor-neutral contract for precipitation forecasts (BaseForecastProvider),
real-time Open-Meteo ECMWF IFS global forecast provider (OpenMeteoForecastProvider),
and a synthetic test provider fixture (SyntheticForecastProvider) for DEV/TEST lead time pipelines.

CRITICAL SEPARATION:
ForecastProvider is strictly separated from RainfallProvider.
Precipitation forecasts explicitly specify initialization time T0, valid time T_valid, and lead time Δt.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
import asyncio
from typing import Any

import httpx
import structlog

from app.schemas.geospatial import BoundingBox, SpatialMetadata
from app.schemas.rainfall import (
    QualityStatus,
    RainfallForecastSchema,
    RainfallQuantityType,
)

logger = structlog.get_logger("aquora.providers.forecast")


class BaseForecastProvider(ABC):
    """
    Abstract Vendor-Neutral Contract for Short-Term Precipitation Forecast Providers.
    """

    @abstractmethod
    async def get_forecast_metadata(self, model_id: str) -> SpatialMetadata:
        """Fetch metadata for a specific numerical weather prediction / nowcast forecast model."""

    @abstractmethod
    async def fetch_forecast(
        self,
        bbox: BoundingBox,
        initialization_time: datetime,
        lead_time_minutes: int
    ) -> RainfallForecastSchema:
        """Fetch precipitation forecast record for a specific initialization time and lead time."""

    @abstractmethod
    async def fetch_0_3h_horizon_forecasts(
        self,
        bbox: BoundingBox,
        initialization_time: datetime
    ) -> list[RainfallForecastSchema]:
        """Fetch complete set of 0 to 3 hour lead time forecast horizons."""


class OpenMeteoForecastProvider(BaseForecastProvider):
    """
    Real Short-Range Precipitation Forecast Data Provider using Open-Meteo ECMWF IFS Global Model.

    PROVIDES:
    - Real-time numerical weather prediction (NWP) precipitation forecasts from ECMWF IFS (~9 km resolution).
    - Hourly precipitation accumulation forecast series in millimeters (mm).
    - Explicit provider identity: provider="OPEN_METEO_ECMWF", model_name="ECMWF_IFS_GLOBAL".
    - UTC-aware timestamp parsing.
    - Zero API key requirement (public Open-Meteo endpoint).

    ERROR & DEGRADATION POLICY:
    - In REAL_DATA mode, network errors, HTTP errors, timeouts, or invalid JSON structures raise explicit errors.
    - NO silent fallback to SyntheticForecastProvider in REAL_DATA mode.
    """

    def __init__(
        self,
        base_url: str = "https://api.open-meteo.com/v1/ecmwf",
        timeout_seconds: float = 25.0,
        model_version: str = "1.0",
    ):
        self.provider_id = "OPEN_METEO_ECMWF"
        self.model_name = "ECMWF_IFS_GLOBAL"
        self.model_version = model_version
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds

    async def get_forecast_metadata(self, model_id: str = "ECMWF_IFS_GLOBAL") -> SpatialMetadata:
        """Fetch metadata for Open-Meteo ECMWF IFS forecast model."""
        return SpatialMetadata(
            source=self.provider_id,
            crs="EPSG:4326",
            resolution=(0.09, 0.09),  # ~9 km
            units="mm",
            version=self.model_version,
            provenance={
                "provider": self.provider_id,
                "model_name": self.model_name,
                "source": "Open-Meteo ECMWF",
                "data_mode": "REAL_DATA",
                "resolution": "approximately 9 km (0.09 deg)",
                "temporal_resolution": "1 hour (60 minutes)",
                "quantity": "precipitation",
                "units": "mm",
                "api_key_required": False,
            },
        )

    async def _fetch_raw_ecmwf_payload(
        self, latitude: float, longitude: float, forecast_days: int = 1
    ) -> dict[str, Any]:
        """
        Execute real HTTP request to Open-Meteo ECMWF IFS endpoint.
        Raises explicit exceptions on network, timeout, HTTP, or parsing failures.
        """
        params = {
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "hourly": "precipitation",
            "forecast_days": forecast_days,
        }

        data = None
        last_error = None
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                    response = await client.get(self.base_url, params=params)
                    if response.status_code == 200:
                        data = response.json()
                        break
                    elif response.status_code in (502, 503, 504, 429) and attempt < 3:
                        await asyncio.sleep(0.1 * attempt)
                        continue
                    else:
                        raise RuntimeError(f"Open-Meteo ECMWF API request failed with HTTP status {response.status_code}: {response.text}")
            except httpx.TimeoutException as exc:
                if attempt == 3:
                    raise TimeoutError(f"API request timed out: {exc}")
                await asyncio.sleep(0.1 * attempt)
            except httpx.RequestError as exc:
                if attempt == 3:
                    raise RuntimeError(f"API request failed: {exc}")
                await asyncio.sleep(0.1 * attempt)

        if data is None:
            raise RuntimeError("Failed to retrieve valid forecast data from Open-Meteo API")

        if not isinstance(data, dict):
            raise ValueError("Open-Meteo payload is not a valid JSON dictionary")

        hourly = data.get("hourly")
        if not hourly or not isinstance(hourly, dict):
            raise ValueError("Missing or invalid 'hourly' section in Open-Meteo ECMWF response")

        times = hourly.get("time")
        precip = hourly.get("precipitation")
        if not times or precip is None:
            raise ValueError("Missing 'time' or 'precipitation' arrays in Open-Meteo ECMWF response")

        if len(times) != len(precip):
            raise ValueError("Mismatched length between 'time' and 'precipitation' arrays in Open-Meteo ECMWF response")

        return data

    async def fetch_forecast(
        self,
        bbox: BoundingBox,
        initialization_time: datetime,
        lead_time_minutes: int
    ) -> RainfallForecastSchema:
        """Fetch precipitation forecast record for a specific initialization time and lead time."""
        center_lat = (bbox.miny + bbox.maxy) / 2.0
        center_lon = (bbox.minx + bbox.maxx) / 2.0

        data = await self._fetch_raw_ecmwf_payload(center_lat, center_lon)

        if not isinstance(data, dict) or "hourly" not in data or not isinstance(data.get("hourly"), dict):
            raise ValueError("Missing or invalid 'hourly' section in Open-Meteo ECMWF payload")

        hourly = data["hourly"]
        times = hourly.get("time")
        precip_list = hourly.get("precipitation")

        if not times or precip_list is None:
            raise ValueError("Missing 'time' or 'precipitation' arrays in Open-Meteo ECMWF payload")

        if len(times) != len(precip_list):
            raise ValueError("Mismatched length between 'time' and 'precipitation' arrays in Open-Meteo ECMWF payload")

        init_dt = initialization_time
        if init_dt.tzinfo is None:
            init_dt = init_dt.replace(tzinfo=timezone.utc)
        # Floor initialization time to top of the hour to align with hourly NWP forecast grid
        init_dt_floored = init_dt.replace(minute=0, second=0, microsecond=0)

        target_dt = init_dt_floored + timedelta(minutes=lead_time_minutes)

        matched_idx: int | None = None
        min_delta = timedelta(days=999)

        for idx, t_str in enumerate(times):
            try:
                dt = datetime.fromisoformat(t_str)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)

                check_target = target_dt
                if check_target.tzinfo is None:
                    check_target = check_target.replace(tzinfo=timezone.utc)

                delta = abs(dt - check_target)
                if delta < min_delta:
                    min_delta = delta
                    matched_idx = idx
            except (ValueError, TypeError):
                continue

        if matched_idx is None or matched_idx >= len(precip_list):
            raise ValueError(f"Could not match target forecast time {target_dt.isoformat()} in Open-Meteo response")

        matched_val = float(precip_list[matched_idx])
        if matched_val < 0.0:
            raise ValueError(f"Invalid negative precipitation value ({matched_val}) in Open-Meteo response")

        valid_time_str = times[matched_idx]
        valid_dt = datetime.fromisoformat(valid_time_str)
        if valid_dt.tzinfo is None:
            valid_dt = valid_dt.replace(tzinfo=timezone.utc)

        dataset_id = f"ECMWF_{init_dt_floored.strftime('%Y%m%d_%H%M')}_LEAD_{lead_time_minutes}M"

        return RainfallForecastSchema(
            dataset_identifier=dataset_id,
            provider=self.provider_id,
            model_name=self.model_name,
            model_version=self.model_version,
            initialization_time=init_dt_floored,
            valid_time=valid_dt,
            lead_time_minutes=lead_time_minutes,
            temporal_resolution_minutes=60.0,  # Source 1-hour resolution
            resolution_deg=(0.09, 0.09),        # ~9 km ECMWF IFS grid
            units="mm",
            quantity_type=RainfallQuantityType.ACCUMULATION,
            quality_status=QualityStatus.VALID,
            bounds=(bbox.minx, bbox.miny, bbox.maxx, bbox.maxy),
            provenance={
                "provider": self.provider_id,
                "model_name": self.model_name,
                "model_version": self.model_version,
                "source": "Open-Meteo ECMWF",
                "data_mode": "REAL_DATA",
                "resolution": "approximately 9 km (0.09 deg)",
                "temporal_resolution": "1 hour (60 minutes)",
                "quantity": "precipitation",
                "units": "mm",
                "precipitation_value_mm": matched_val,
                "initialization_time": init_dt.isoformat(),
                "valid_time": valid_dt.isoformat(),
                "lead_time_minutes": lead_time_minutes,
                "api_key_required": False,
            }
        )

    async def fetch_0_3h_horizon_forecasts(
        self,
        bbox: BoundingBox,
        initialization_time: datetime
    ) -> list[RainfallForecastSchema]:
        """Fetch complete set of short-range 0 to 3 hour hourly lead time forecast horizons (0, 60, 120, 180 min)."""
        lead_steps = [0, 60, 120, 180]
        forecasts = []
        for lead in lead_steps:
            fcst = await self.fetch_forecast(bbox, initialization_time, lead)
            forecasts.append(fcst)
        return forecasts


class SyntheticForecastProvider(BaseForecastProvider):
    """
    Synthetic Forecast Provider Fixture for Infrastructure Testing.
    
    LABEL: TEST FIXTURE ONLY.
    DO NOT USE IN PRODUCTION OR PRESENT AS REAL WEATHER FORECASTS.
    """

    def __init__(self, model_version: str = "SYNTHETIC_V1"):
        self.provider_id = "SYNTHETIC_FORECAST_PROVIDER"
        self.model_version = model_version

    async def get_forecast_metadata(self, model_id: str) -> SpatialMetadata:
        """Fetch synthetic forecast metadata."""
        return SpatialMetadata(
            source=self.provider_id,
            crs="EPSG:4326",
            resolution=(0.1, 0.1),
            units="mm",
            version=self.model_version,
            provenance={
                "provider": self.provider_id,
                "label": "TEST FIXTURE ONLY",
                "lead_times_supported_minutes": [0, 30, 60, 90, 120, 150, 180]
            }
        )

    async def fetch_forecast(
        self,
        bbox: BoundingBox,
        initialization_time: datetime,
        lead_time_minutes: int
    ) -> RainfallForecastSchema:
        """Fetch a single synthetic forecast horizon record."""
        valid_time = initialization_time + timedelta(minutes=lead_time_minutes)
        dataset_id = f"FCST_{initialization_time.strftime('%Y%m%d_%H%M')}_LEAD_{lead_time_minutes}M"

        return RainfallForecastSchema(
            dataset_identifier=dataset_id,
            provider=self.provider_id,
            model_name="SYNTHETIC_NOWCAST",
            model_version=self.model_version,
            initialization_time=initialization_time,
            valid_time=valid_time,
            lead_time_minutes=lead_time_minutes,
            temporal_resolution_minutes=30.0,
            resolution_deg=(0.1, 0.1),
            units="mm",
            quantity_type=RainfallQuantityType.ACCUMULATION,
            quality_status=QualityStatus.VALID,
            bounds=(bbox.minx, bbox.miny, bbox.maxx, bbox.maxy),
            provenance={
                "provider": self.provider_id,
                "label": "TEST FIXTURE ONLY",
                "model_name": "SYNTHETIC_NOWCAST",
                "model_version": self.model_version,
                "initialization_time": initialization_time.isoformat(),
                "valid_time": valid_time.isoformat(),
                "lead_time_minutes": lead_time_minutes,
            }
        )

    async def fetch_0_3h_horizon_forecasts(
        self,
        bbox: BoundingBox,
        initialization_time: datetime
    ) -> list[RainfallForecastSchema]:
        """Fetch complete set of 0-3h horizon forecasts (30 min increments)."""
        lead_steps = [0, 30, 60, 90, 120, 150, 180]
        forecasts = []
        for lead in lead_steps:
            fcst = await self.fetch_forecast(bbox, initialization_time, lead)
            forecasts.append(fcst)
        return forecasts
