"""
Synthetic Rainfall and Forecast Test Fixtures for Infrastructure Pipeline Testing.

ALL DATA DEFINED IN THIS FILE ARE EXPLICITLY LABELED AS 'TEST FIXTURE ONLY'.
THEY DO NOT REPRESENT REAL WEATHER OBSERVATIONS, REAL WEATHER FORECASTS, OR FLOOD PREDICTIONS.
"""

from datetime import datetime, timedelta

from app.schemas.geospatial import BoundingBox
from app.schemas.rainfall import (
    QualityStatus,
    RainfallForecastSchema,
    RainfallObservationSchema,
    RainfallQuantityType,
)

# Test spatial envelope
SAMPLE_BBOX = BoundingBox(minx=12.4900, miny=41.8900, maxx=12.4950, maxy=41.8950)

# Timestamps
NOW_UTC = datetime.utcnow()
START_30M_AGO = NOW_UTC - timedelta(minutes=30)


# 1. Synthetic Valid Observation Fixture
SAMPLE_VALID_OBSERVATION = RainfallObservationSchema(
    dataset_identifier="GPM_3IMERG_SYNTHETIC_TEST_01",
    provider="NASA_GPM_IMERG",
    product_variant="Final",
    product_version="V07B",
    observation_start=START_30M_AGO,
    observation_end=NOW_UTC,
    duration_minutes=30.0,
    resolution_deg=(0.1, 0.1),
    units="mm",
    quantity_type=RainfallQuantityType.ACCUMULATION,
    quality_status=QualityStatus.VALID,
    bounds=(12.4900, 41.8900, 12.4950, 41.8950),
    provenance={
        "source": "SYNTHETIC_TEST_FIXTURE",
        "label": "TEST FIXTURE ONLY",
        "accumulation_mm": 5.2
    }
)

# 2. Synthetic Zero Rainfall Observation (Measured 0.0 mm)
SAMPLE_ZERO_RAINFALL_OBSERVATION = RainfallObservationSchema(
    dataset_identifier="GPM_3IMERG_SYNTHETIC_ZERO_01",
    provider="NASA_GPM_IMERG",
    product_variant="Final",
    product_version="V07B",
    observation_start=START_30M_AGO,
    observation_end=NOW_UTC,
    duration_minutes=30.0,
    resolution_deg=(0.1, 0.1),
    units="mm",
    quantity_type=RainfallQuantityType.ACCUMULATION,
    quality_status=QualityStatus.VALID,
    bounds=(12.4900, 41.8900, 12.4950, 41.8950),
    provenance={
        "source": "SYNTHETIC_TEST_FIXTURE",
        "label": "TEST FIXTURE ONLY",
        "accumulation_mm": 0.0
    }
)

# 3. Synthetic NODATA Observation (Missing Measurement Sentinel)
SAMPLE_NODATA_OBSERVATION = RainfallObservationSchema(
    dataset_identifier="GPM_3IMERG_SYNTHETIC_NODATA_01",
    provider="NASA_GPM_IMERG",
    product_variant="Final",
    product_version="V07B",
    observation_start=START_30M_AGO,
    observation_end=NOW_UTC,
    duration_minutes=30.0,
    resolution_deg=(0.1, 0.1),
    units="mm",
    quantity_type=RainfallQuantityType.ACCUMULATION,
    quality_status=QualityStatus.NODATA,
    bounds=(12.4900, 41.8900, 12.4950, 41.8950),
    provenance={
        "source": "SYNTHETIC_TEST_FIXTURE",
        "label": "TEST FIXTURE ONLY",
        "nodata_value": -9999.0
    }
)

# 4. Synthetic Invalid Forecast (lead_time > 180 min or valid_time preceding T0)
SAMPLE_FORECAST_HORIZON = RainfallForecastSchema(
    dataset_identifier="FCST_SYNTHETIC_TEST_LEAD_60M",
    provider="SYNTHETIC_FORECAST_PROVIDER",
    model_name="SYNTHETIC_NOWCAST",
    model_version="SYNTHETIC_V1",
    initialization_time=NOW_UTC,
    valid_time=NOW_UTC + timedelta(minutes=60),
    lead_time_minutes=60,
    resolution_deg=(0.1, 0.1),
    units="mm",
    quality_status=QualityStatus.VALID,
    bounds=(12.4900, 41.8900, 12.4950, 41.8950),
    provenance={
        "source": "SYNTHETIC_TEST_FIXTURE",
        "label": "TEST FIXTURE ONLY"
    }
)
