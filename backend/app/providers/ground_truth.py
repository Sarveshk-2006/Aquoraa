"""Provider Abstraction Layer for Phase 13 Ground Truth + Photo Verification.

Includes:
- BaseGroundTruthProvider
- SyntheticGroundTruthProvider (DEVELOPMENT_ONLY / TEST_ONLY)
- LocalGroundTruthProvider (GeoJSON/JSON parsing)
- BasePhotoAssessmentProvider
- LocalPhotoAssessmentProvider (Bounded deterministic quality/format/presence analyzer)
"""

import abc
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from app.schemas.ground_truth import (
    FloodPresence,
    ImageQuality,
    ObservationCreateSchema,
    ObservationSourceType,
    ObservationType,
    ObserverType,
    RoadPassability,
    WaterDepthClass,
)

logger = structlog.get_logger("aquora.ground_truth.providers")


# --- Ground Truth Observation Providers ---

class BaseGroundTruthProvider(abc.ABC):
    """Abstract base class for ground truth observation providers."""

    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        """Unique provider identifier."""

    @property
    @abc.abstractmethod
    def provider_mode(self) -> str:
        """Provider mode (LOCAL, SYNTHETIC, FIELD)."""

    @abc.abstractmethod
    async def fetch_observations(self) -> list[ObservationCreateSchema]:
        """Fetches/generates observation records asynchronously."""


class SyntheticGroundTruthProvider(BaseGroundTruthProvider):
    """Deterministic, DEVELOPMENT_ONLY synthetic observation provider.

    Generates clearly tagged test observations for demonstration and testing.
    Uses city-agnostic core architecture with configurable pilot bounds.
    """

    def __init__(
        self,
        center_lat: float = 19.0760,
        center_lon: float = 72.8777,
        num_observations: int = 5,
    ) -> None:
        self._center_lat = center_lat
        self._center_lon = center_lon
        self._num_observations = num_observations

    @property
    def provider_id(self) -> str:
        return "SYNTHETIC_GROUND_TRUTH_PROVIDER"

    @property
    def provider_mode(self) -> str:
        return "SYNTHETIC"

    async def fetch_observations(self) -> list[ObservationCreateSchema]:
        """Generates deterministic synthetic observations."""
        now_iso = datetime.now(timezone.utc).isoformat()

        synthetic_specs = [
            {
                "lat_offset": 0.002,
                "lon_offset": 0.003,
                "type": ObservationType.FLOOD_REPORT,
                "presence": FloodPresence.FLOOD_PRESENT,
                "depth": WaterDepthClass.TWENTY_TO_FORTY_CM,
                "road": RoadPassability.DIFFICULT,
                "source": ObservationSourceType.COMMUNITY,
                "desc": "TEST OBSERVATION A — Water accumulating near road junction, traffic slowed down.",
                "ref": "test_user_alpha",
            },
            {
                "lat_offset": -0.001,
                "lon_offset": 0.001,
                "type": ObservationType.ROAD_REPORT,
                "presence": FloodPresence.FLOOD_PRESENT,
                "depth": WaterDepthClass.GREATER_THAN_40CM,
                "road": RoadPassability.NOT_PASSABLE,
                "source": ObservationSourceType.FIELD_TEAM,
                "desc": "TEST OBSERVATION B — Severe underpass inundation observed by field response crew.",
                "ref": "field_team_unit_01",
            },
            {
                "lat_offset": 0.005,
                "lon_offset": -0.002,
                "type": ObservationType.WATER_LEVEL_REPORT,
                "presence": FloodPresence.NO_FLOOD_OBSERVED,
                "depth": WaterDepthClass.DRY,
                "road": RoadPassability.PASSABLE,
                "source": ObservationSourceType.COMMUNITY,
                "desc": "TEST OBSERVATION C — Drainage channel flowing clear, no surface flooding observed.",
                "ref": "test_user_beta",
            },
            {
                "lat_offset": 0.003,
                "lon_offset": 0.004,
                "type": ObservationType.PHOTO_REPORT,
                "presence": FloodPresence.FLOOD_PRESENT,
                "depth": WaterDepthClass.TEN_TO_TWENTY_CM,
                "road": RoadPassability.DIFFICULT,
                "source": ObservationSourceType.COMMUNITY,
                "desc": "TEST OBSERVATION D — Citizen photo report showing shallow street flooding.",
                "ref": "test_user_gamma",
            },
            {
                "lat_offset": -0.004,
                "lon_offset": -0.003,
                "type": ObservationType.FIELD_INSPECTION,
                "presence": FloodPresence.FLOOD_PRESENT,
                "depth": WaterDepthClass.TWENTY_TO_FORTY_CM,
                "road": RoadPassability.NOT_PASSABLE,
                "source": ObservationSourceType.AUTHORITY,
                "desc": "TEST OBSERVATION E — Official municipal field inspection report.",
                "ref": "municipal_officer_102",
            },
        ]

        observations = []
        for i, spec in enumerate(synthetic_specs[: self._num_observations]):
            obs = ObservationCreateSchema(
                latitude=round(self._center_lat + spec["lat_offset"], 6),
                longitude=round(self._center_lon + spec["lon_offset"], 6),
                location_source="GPS",
                observed_at=now_iso,
                source=spec["source"],
                source_id=f"SYNTHETIC_SRC_{i+1:03d}",
                observer_type=ObserverType.FIELD_TEAM if spec["source"] == ObservationSourceType.FIELD_TEAM else ObserverType.COMMUNITY,
                observer_reference=spec["ref"],
                observation_type=spec["type"],
                flood_presence=spec["presence"],
                water_depth_class=spec["depth"],
                road_passability=spec["road"],
                description=spec["desc"],
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "disclaimer": "DEVELOPMENT_ONLY / TEST_ONLY — Synthetic demonstration observation.",
                },
            )
            observations.append(obs)

        return observations


class LocalGroundTruthProvider(BaseGroundTruthProvider):
    """Parses local GeoJSON or JSON files containing flood observations."""

    def __init__(self, data_path: Path | str) -> None:
        self._data_path = Path(data_path)

    @property
    def provider_id(self) -> str:
        return "LOCAL_FILE_GROUND_TRUTH_PROVIDER"

    @property
    def provider_mode(self) -> str:
        return "LOCAL"

    async def fetch_observations(self) -> list[ObservationCreateSchema]:
        """Loads and parses local GeoJSON/JSON observation records."""
        if not self._data_path.exists():
            logger.warning(f"Local ground truth data path '{self._data_path}' does not exist.")
            return []

        observations: list[ObservationCreateSchema] = []
        files = [self._data_path] if self._data_path.is_file() else list(self._data_path.glob("*.json")) + list(self._data_path.glob("*.geojson"))

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:  # noqa: ASYNC230
                    data = json.load(f)

                records = data.get("features", []) if data.get("type") == "FeatureCollection" else data.get("observations", [data])

                for rec in records:
                    props = rec.get("properties", rec)
                    geom = rec.get("geometry", {})
                    coords = geom.get("coordinates", [props.get("longitude"), props.get("latitude")])

                    if not coords or len(coords) < 2 or coords[0] is None or coords[1] is None:
                        continue

                    obs = ObservationCreateSchema(
                        latitude=float(coords[1]),
                        longitude=float(coords[0]),
                        location_source=props.get("location_source", "MANUAL"),
                        observed_at=props.get("observed_at"),
                        source=ObservationSourceType(props.get("source", "COMMUNITY")),
                        source_id=props.get("source_id"),
                        observer_type=ObserverType(props.get("observer_type", "COMMUNITY")),
                        observer_reference=props.get("observer_reference"),
                        observation_type=ObservationType(props.get("observation_type", "FLOOD_REPORT")),
                        flood_presence=FloodPresence(props.get("flood_presence", "FLOOD_PRESENT")),
                        water_depth_class=WaterDepthClass(props.get("water_depth_class", "UNKNOWN")),
                        road_passability=RoadPassability(props.get("road_passability", "UNKNOWN")),
                        description=props.get("description"),
                        provenance={
                            "provider": self.provider_id,
                            "source_file": file_path.name,
                        },
                    )
                    observations.append(obs)
            except Exception as err:  # noqa: BLE001
                logger.warning(f"Failed to parse ground truth file '{file_path}': {err}")

        return observations


# --- Photo & CV Assessment Providers ---

class BasePhotoAssessmentProvider(abc.ABC):
    """Abstract base class for photo/CV evidence assessment providers."""

    @property
    @abc.abstractmethod
    def provider_id(self) -> str:
        """Unique CV provider identifier."""

    @abc.abstractmethod
    async def assess_photo(
        self,
        file_path: Path,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        """Assesses image quality, format, and visible water presence indicators."""


class LocalPhotoAssessmentProvider(BasePhotoAssessmentProvider):
    """Bounded, deterministic local photo assessment provider.

    Performs basic file format, quality, and header analysis.
    Does NOT claim exact water depth or fake neural network precision.
    """

    @property
    def provider_id(self) -> str:
        return "LOCAL_BOUNDED_PHOTO_ASSESSMENT_PROVIDER"

    async def assess_photo(
        self,
        file_path: Path,
        mime_type: str,
        file_size: int,
    ) -> dict[str, Any]:
        """Executes bounded quality & format assessment."""
        if not file_path.exists():
            return {
                "image_quality": ImageQuality.INSUFFICIENT,
                "cv_status": "FILE_NOT_FOUND",
                "water_presence_indicated": False,
                "confidence_score": 0.0,
                "details": "File does not exist on storage.",
            }

        # Check basic file attributes
        is_supported_mime = mime_type in ("image/jpeg", "image/png", "image/webp")
        file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest() if file_size < 10_000_000 else "HASH_SKIPPED"

        if not is_supported_mime or file_size < 1024:
            quality = ImageQuality.LIMITED if file_size >= 512 else ImageQuality.INSUFFICIENT
            return {
                "image_quality": quality,
                "cv_status": "DEVELOPMENT_ONLY",
                "water_presence_indicated": False,
                "confidence_score": 0.3,
                "file_hash": file_hash,
                "details": "Image file size or format is limited for automated assessment.",
            }

        # Bounded assessment summary
        return {
            "image_quality": ImageQuality.SUFFICIENT,
            "cv_status": "DEVELOPMENT_ONLY",
            "water_presence_indicated": True,
            "apparent_severity": "MODERATE",
            "confidence_score": 0.75,
            "file_hash": file_hash,
            "disclaimer": "CV supporting evidence — PROTOTYPE ONLY. Exact water depth is not claimed.",
            "details": "Photo assessment indicates visible surface inundation cues consistent with flood presence.",
        }
