import json

import pydantic

if not hasattr(pydantic, "Secret"):
    pydantic.Secret = pydantic.SecretStr

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AQUORA — Urban Flood Intelligence & Response Platform"
    VERSION: str = "0.6.0-phase6"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://aquora:aquora_password@localhost:5432/aquora_db",
        description="Async PostgreSQL / PostGIS connection string"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    ENVIRONMENT: str = Field(
        default="development",
        description="Runtime environment ('development', 'testing', 'production')"
    )
    CORS_ORIGINS: list[str] | str = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:5175",
            "http://127.0.0.1:5175",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://aquora-nine.vercel.app",
        ],
        description="Allowed origins for CORS"
    )
    LOG_LEVEL: str = "INFO"

    MAP_STYLE_URL: str = "https://demotiles.maplibre.org/style.json"
    MAP_TOKEN: str = "placeholder_token"

    # Spatial Reference System Configuration
    GEOSPATIAL_CANONICAL_CRS: str = Field(
        default="EPSG:4326",
        description="Canonical geographic CRS for external interchange and API contracts (WGS84)"
    )
    GEOSPATIAL_DISPLAY_CRS: str = Field(
        default="EPSG:3857",
        description="Display CRS for web mapping visualizations (Web Mercator)"
    )
    GEOSPATIAL_ANALYSIS_CRS: str = Field(
        default="EPSG:32633",
        description="Configurable projected metric analysis CRS for planar spatial calculations (Default UTM 33N for test/dev)"
    )

    # NASA Earthdata & Rainfall Pipeline Configuration
    NASA_EARTHDATA_USERNAME: str | None = Field(
        default=None,
        description="NASA Earthdata Login username for GPM IMERG data access"
    )
    NASA_EARTHDATA_PASSWORD: str | None = Field(
        default=None,
        description="NASA Earthdata Login password/token for GPM IMERG data access"
    )
    RAINFALL_RAW_DATA_PATH: str = Field(
        default="data/raw/rainfall",
        description="Directory path for raw external rainfall payloads"
    )
    RAINFALL_PROCESSED_DATA_PATH: str = Field(
        default="data/processed/rainfall",
        description="Directory path for normalized rainfall data arrays"
    )

    # Terrain Engine & DEM Configuration
    DEM_RAW_DATA_PATH: str = Field(
        default="data/raw/dem",
        description="Directory path for raw external DEM raster payloads"
    )
    DEM_PROCESSED_DATA_PATH: str = Field(
        default="data/processed/dem",
        description="Directory path for processed terrain derivative rasters"
    )
    SURFACE_DRAINAGE_THRESHOLD_AREA_M2: float = Field(
        default=10000.0,
        description="Configurable contributing area threshold in m2 for extracting DEM-derived surface drainage proxy"
    )
    CATCHMENT_SNAP_TOLERANCE_M: float = Field(
        default=100.0,
        description="Configurable pour-point snapping distance tolerance in meters"
    )

    # Drainage Network Engine Configuration
    DRAINAGE_RAW_DATA_PATH: str = Field(
        default="data/raw/drainage",
        description="Directory path for raw external drainage network vector payloads"
    )
    DRAINAGE_PROCESSED_DATA_PATH: str = Field(
        default="data/processed/drainage",
        description="Directory path for normalized drainage network artifacts"
    )
    DRAINAGE_SNAP_TOLERANCE_M: float = Field(
        default=5.0,
        description="Configurable spatial snapping radius tolerance in meters for node-link alignment"
    )
    DRAINAGE_CATCHMENT_ASSOCIATION_TOLERANCE_M: float = Field(
        default=200.0,
        description="Configurable distance tolerance in meters for associating Phase 4 catchments with drainage inlets"
    )

    # Flood Simulation Engine Configuration
    FLOOD_RAW_DATA_PATH: str = Field(
        default="data/raw/flood",
        description="Directory path for raw simulation inputs/manifests"
    )
    FLOOD_PROCESSED_DATA_PATH: str = Field(
        default="data/processed/flood",
        description="Directory path for processed flood simulation artifacts and raster outputs"
    )
    FLOOD_SIMULATION_TIMESTEP_MINUTES: int = Field(
        default=10,
        description="Default simulation timestep in minutes (e.g. 5, 10, 15, 30, 60)"
    )
    FLOOD_SIMULATION_HORIZON_MINUTES: int = Field(
        default=180,
        description="Default maximum simulation horizon in minutes (up to 3 hours)"
    )
    RUNOFF_MODEL: str = Field(
        default="IMPERVIOUS_LOSS",
        description="Configurable runoff generation model ('IMPERVIOUS_LOSS', 'RATIONAL_COEFFICIENT', 'INITIAL_DEPRESSION_LOSS')"
    )
    DEFAULT_RUNOFF_COEFFICIENT: float = Field(
        default=0.7,
        description="Default runoff coefficient C for land area (0.0 - 1.0)"
    )
    DEFAULT_INFILTRATION_RATE_MM_HR: float = Field(
        default=5.0,
        description="Default soil infiltration loss rate in mm/hr"
    )
    DEFAULT_INITIAL_LOSS_MM: float = Field(
        default=2.0,
        description="Default initial abstraction/wetting loss in mm"
    )
    DEFAULT_DEPRESSION_STORAGE_M3: float = Field(
        default=0.05,
        description="Default micro-depression surface storage per m2 cell area"
    )
    MASS_BALANCE_TOLERANCE: float = Field(
        default=1e-4,
        description="Configurable numerical tolerance threshold for mass balance error verification"
    )
    UNKNOWN_CAPACITY_POLICY: str = Field(
        default="EXCLUDE",
        description="Policy for missing pipe capacities ('EXCLUDE', 'CONSERVATIVE_ASSUMPTION', 'SCENARIO')"
    )
    UNKNOWN_DIRECTION_POLICY: str = Field(
        default="EXCLUDE",
        description="Policy for unknown link directions ('EXCLUDE', 'SCENARIO')"
    )
    UNKNOWN_ASSOCIATION_POLICY: str = Field(
        default="EXCLUDE",
        description="Policy for unassociated/ambiguous catchment inlets ('EXCLUDE', 'NEAREST_VALID')"
    )
    RAINFALL_RESAMPLING_METHOD: str = Field(
        default="HOLD",
        description="Method for resampling coarse rainfall to simulation timesteps ('HOLD', 'LINEAR_INTERPOLATION')"
    )

    # Phase 10 Routing & Travel Window Configuration
    ROUTING_PROVIDER: str = Field(
        default="SYNTHETIC",
        description="Active routing provider implementation ('SYNTHETIC', 'OSRM')"
    )
    ROUTING_BASE_URL: str = Field(
        default="https://router.project-osrm.org",
        description="Configurable base URL for external routing service (e.g. OSRM router endpoint)"
    )
    ROUTING_TIMEOUT_SECONDS: float = Field(
        default=10.0,
        description="Bounded HTTP request timeout in seconds for routing provider calls"
    )
    ROUTING_MAX_ALTERNATIVES: int = Field(
        default=3,
        description="Maximum number of candidate routes to request/evaluate"
    )
    ROUTE_SAMPLE_INTERVAL_M: float = Field(
        default=100.0,
        description="Spatial sampling interval along route geometry in metric meters for flood raster lookup"
    )
    ROUTE_SAFETY_BUFFER_MIN: int = Field(
        default=15,
        description="Configurable safety buffer in minutes subtracted during travel window calculation"
    )
    ROUTE_IMPACT_SEVERITY: str = Field(
        default="HIGH",
        description="Minimum modeled flood severity class considered a route hazard ('MODERATE', 'HIGH', 'SEVERE')"
    )
    ROUTE_UNKNOWN_POLICY: str = Field(
        default="PRESERVE_UNCERTAINTY",
        description="Policy for unmapped/nodata flood raster cells along route ('PRESERVE_UNCERTAINTY', 'CONSERVATIVE_HAZARD')"
    )

    # Phase 11 Critical Access Guardian Configuration
    CRITICAL_ACCESS_SEVERITY: str = Field(
        default="HIGH",
        description="Minimum modeled flood severity threshold considered a critical facility access compromise ('MODERATE', 'HIGH', 'SEVERE')"
    )
    CRITICAL_FACILITIES_DATA_PATH: str = Field(
        default="data/raw/facilities",
        description="Directory path for verified critical facility GeoJSON / vector layers"
    )
    FACILITY_PROVIDER: str = Field(
        default="SYNTHETIC",
        description="Active critical facility provider implementation ('SYNTHETIC', 'LOCAL')"
    )

    # Phase 12 Protect the City Configuration
    PROTECT_CITY_PRIORITY_THRESHOLD: str = Field(
        default="HIGH",
        description="Minimum priority threshold for intervention recommendation filtering ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')"
    )
    INTERVENTION_CANDIDATE_DATA_PATH: str = Field(
        default="data/raw/interventions",
        description="Directory path for verified intervention candidate GeoJSON / vector layers"
    )
    INTERVENTION_PROVIDER: str = Field(
        default="SYNTHETIC",
        description="Active intervention candidate provider implementation ('SYNTHETIC', 'LOCAL')"
    )

    # Phase 14 Aquora Simulator Configuration
    SIMULATOR_NO_CHANGE_TOLERANCE: float = Field(
        default=2.0,
        description="Configurable percentage delta tolerance for simulator NO_SIGNIFICANT_CHANGE outcome classification"
    )
    SIMULATOR_NO_CHANGE_DEPTH_TOLERANCE_M: float = Field(
        default=0.02,
        description="Configurable depth delta tolerance in meters for simulator NO_SIGNIFICANT_CHANGE outcome classification (0.02m = 2cm)"
    )
    SIMULATOR_MATERIAL_DEPTH_CHANGE_M: float = Field(
        default=0.05,
        description="Configurable material depth change threshold in meters for simulator WORSE or INCONCLUSIVE outcome classification (0.05m = 5cm)"
    )

    # Phase 15 Alerts & Explainability Configuration
    ALERT_FLOOD_ONSET_LOOKAHEAD_MINUTES: int = Field(
        default=60,
        description="Configurable lookahead window in minutes for generating FLOOD_ONSET alerts"
    )
    ALERT_HIGH_SEVERE_LOOKAHEAD_MINUTES: int = Field(
        default=60,
        description="Configurable lookahead window in minutes for generating HIGH_SEVERE_FLOOD_RISK alerts"
    )
    ALERT_TRAVEL_WINDOW_WARNING_MINUTES: int = Field(
        default=30,
        description="Configurable travel safety window warning threshold in minutes for TRAVEL_WINDOW_CLOSING alerts"
    )
    ALERT_MODEL_INPUT_COMPLETENESS_THRESHOLD: float = Field(
        default=0.8,
        description="Minimum input completeness ratio (0.0-1.0) below which MODEL_INPUT_DEGRADED alerts are triggered"
    )
    ALERT_GROUND_TRUTH_CONFLICT_TOLERANCE: float = Field(
        default=0.1,
        description="Discrepancy tolerance threshold for generating GROUND_TRUTH_CONFLICT alerts"
    )
    ALERT_DEDUPLICATION_WINDOW_MINUTES: int = Field(
        default=60,
        description="Deduplication window in minutes for aggregating continuous alert conditions"
    )
    ALERT_SOURCE_STALE_THRESHOLD_MINUTES: int = Field(
        default=120,
        description="Stale threshold in minutes for flagging degraded upstream model sources"
    )
    ALERT_NOISE_SUPPRESSION_ENABLED: bool = Field(
        default=True,
        description="Toggle for noise suppression of transient/sub-threshold alerts"
    )

    # Phase 8 ML Calibration Configuration
    AQUORA_CALIBRATION_MODEL_PATH: str = Field(
        default="backend/data/models/aquora_xgboost_prototype.joblib",
        description="Path to Kaggle XGBoost prototype model artifact"
    )


    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str] | None) -> list[str]:
        if not v:
            return [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5174",
                "http://localhost:5175",
                "http://127.0.0.1:5175",
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "https://aquora-nine.vercel.app",
            ]

        origins: list[str] = []
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        origins = [str(item) for item in parsed]
                except Exception:
                    raw = v[1:-1]
                    origins = [item.strip() for item in raw.split(",") if item.strip()]
            else:
                origins = [item.strip() for item in v.split(",") if item.strip()]
        elif isinstance(v, list):
            origins = [str(item) for item in v]
        else:
            return []

        cleaned: list[str] = []
        for origin in origins:
            o = origin.strip().strip("'").strip('"').rstrip('/')
            if o and o not in cleaned:
                cleaned.append(o)

        return cleaned

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def parse_database_url(cls, v: str | None) -> str:
        if not v:
            return "postgresql+asyncpg://aquora:aquora_password@localhost:5432/aquora_db"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql+asyncpg://" if "postgresql+asyncpg://" in v else "postgresql://", "postgresql+asyncpg://", 1)
        return v


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
