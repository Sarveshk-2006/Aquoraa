"""
Critical Facility Provider Implementations for Phase 11 Critical Access Guardian.

Defines abstract BaseCriticalFacilityProvider and implementations:
1. SyntheticCriticalFacilityProvider — Deterministic synthetic facility generator for dev & testing.
2. LocalCriticalFacilityProvider — File-backed reader for verified GeoJSON facility datasets.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import logger

# Controlled Facility Category Taxonomy
FACILITY_CATEGORIES = [
    "HOSPITAL",
    "CLINIC",
    "FIRE_STATION",
    "POLICE_STATION",
    "AMBULANCE_BASE",
    "EMERGENCY_CONTROL",
    "EMERGENCY_CONTROL_CENTER",
    "SHELTER",
    "OTHER_CRITICAL",
]


class FacilityResult:
    """Container for critical facility entity metadata."""

    def __init__(
        self,
        facility_id: str,
        name: str,
        category: str,
        latitude: float,
        longitude: float,
        source: str,
        source_id: str | None = None,
        source_type: str = "SYNTHETIC",
        verification_status: str = "UNVERIFIED",
        operational_status: str = "UNKNOWN",
        provider_mode: str = "SYNTHETIC",
        environment: str = "DEVELOPMENT_ONLY",
        summary: str | None = None,
        provenance: dict[str, Any] | None = None,
    ):
        self.facility_id = facility_id
        self.name = name
        self.category = category if category in FACILITY_CATEGORIES else "OTHER_CRITICAL"
        self.latitude = latitude
        self.longitude = longitude
        self.source = source
        self.source_id = source_id
        self.source_type = source_type
        self.verification_status = verification_status
        self.operational_status = operational_status
        self.provider_mode = provider_mode
        self.environment = environment
        self.summary = summary or f"{name} ({category})"
        self.provenance = provenance or {
            "source": source,
            "source_type": source_type,
            "verification_status": verification_status,
            "environment": environment,
        }


class BaseCriticalFacilityProvider(ABC):
    """Abstract interface for critical facility providers."""

    @abstractmethod
    async def list_facilities(
        self,
        category: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[FacilityResult]:
        """List critical facilities matching query criteria."""

    @abstractmethod
    async def get_facility_by_id(self, facility_id: str) -> FacilityResult | None:
        """Retrieve single critical facility by ID."""


class SyntheticCriticalFacilityProvider(BaseCriticalFacilityProvider):
    """
    Deterministic synthetic critical facility provider for development and testing.
    Generates pilot facilities in Mumbai Mithi catchment (Kurla / Saki Naka / Kalina / Sion corridor).
    Explicitly tags outputs as SYNTHETIC / DEVELOPMENT_ONLY. Never presents synthetic facilities as real.
    """

    def __init__(self):
        self.provider_id = "SYNTHETIC_FACILITY_PROVIDER"
        self.provider_mode = "SYNTHETIC"
        self.environment = "DEVELOPMENT_ONLY"

        # Deterministic pilot test fixtures in Mumbai Mithi River catchment
        self._fixtures: list[FacilityResult] = [
            FacilityResult(
                facility_id="fac_hospital_a",
                name="TEST FACILITY — HOSPITAL A",
                category="HOSPITAL",
                latitude=19.0760,
                longitude=72.8777,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_HOSP_001",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="TEST FACILITY — HOSPITAL A (Kurla)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_hosp_kurla_01",
                name="TEST FACILITY — HOSPITAL A (Kurla Substation)",
                category="HOSPITAL",
                latitude=19.0760,
                longitude=72.8777,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_HOSP_001_ALT",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="Primary Trauma Center (Synthetic Test Fixture)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_fire_station_a",
                name="TEST FACILITY — FIRE STATION A",
                category="FIRE_STATION",
                latitude=19.0880,
                longitude=72.8890,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_FIRE_001",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="TEST FACILITY — FIRE STATION A (Saki Naka)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_fire_sakinaka_01",
                name="TEST FACILITY — FIRE STATION A (Saki Naka Alt)",
                category="FIRE_STATION",
                latitude=19.0880,
                longitude=72.8890,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_FIRE_001_ALT",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="Response Fire Station (Synthetic Test Fixture)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_police_station_a",
                name="TEST FACILITY — POLICE STATION A",
                category="POLICE_STATION",
                latitude=19.0700,
                longitude=72.8700,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_POL_001",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="TEST FACILITY — POLICE STATION A (Kalina)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_pol_kalina_01",
                name="TEST FACILITY — POLICE STATION A (Kalina Alt)",
                category="POLICE_STATION",
                latitude=19.0700,
                longitude=72.8700,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_POL_001_ALT",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="Local Police Station (Synthetic Test Fixture)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_shelter_a",
                name="TEST FACILITY — SHELTER A",
                category="SHELTER",
                latitude=19.0400,
                longitude=72.8600,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_SHELTER_001",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="TEST FACILITY — SHELTER A (Sion)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
            FacilityResult(
                facility_id="fac_shelter_sion_01",
                name="TEST FACILITY — SHELTER A (Sion Alt)",
                category="SHELTER",
                latitude=19.0400,
                longitude=72.8600,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_SHELTER_001_ALT",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                operational_status="UNKNOWN",
                provider_mode=self.provider_mode,
                summary="Evacuation Relief Shelter (Synthetic Test Fixture)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test facility — development/test use only.",
                },
            ),
        ]

    async def list_facilities(
        self,
        category: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[FacilityResult]:
        res = self._fixtures

        if category:
            cat_upper = category.upper()
            res = [f for f in res if f.category == cat_upper]

        if verification_status:
            v_upper = verification_status.upper()
            res = [f for f in res if f.verification_status == v_upper]

        if bbox:
            min_lat = bbox.get("min_lat", -90.0)
            max_lat = bbox.get("max_lat", 90.0)
            min_lon = bbox.get("min_lon", -180.0)
            max_lon = bbox.get("max_lon", 180.0)
            res = [
                f for f in res
                if min_lat <= f.latitude <= max_lat and min_lon <= f.longitude <= max_lon
            ]

        return res

    async def get_facility_by_id(self, facility_id: str) -> FacilityResult | None:
        for f in self._fixtures:
            if f.facility_id == facility_id:
                return f
        return None

    async def get_facility(self, facility_id: str) -> FacilityResult | None:
        return await self.get_facility_by_id(facility_id)


class LocalCriticalFacilityProvider(BaseCriticalFacilityProvider):
    """
    File-backed reader for verified local GeoJSON / JSON critical facility layers.
    """

    def __init__(self, data_path: Path | str | None = None):
        self.provider_id = "LOCAL_FACILITY_PROVIDER"
        self.provider_mode = "LOCAL_VERIFIED"
        path_obj = Path(data_path or settings.CRITICAL_FACILITIES_DATA_PATH)
        if not path_obj.is_absolute():
            repo_root = Path(__file__).resolve().parents[3]
            path_obj = repo_root / path_obj
        self.data_path = path_obj

    async def list_facilities(
        self,
        category: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[FacilityResult]:
        facilities: list[FacilityResult] = []

        if not self.data_path.exists():
            logger.warning("Local critical facilities directory not found, fallback to empty", path=str(self.data_path))
            return facilities

        for file_path in self.data_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:  # noqa: ASYNC230
                    data = json.load(f)

                features = data.get("features", [])
                for idx, feat in enumerate(features):
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [0.0, 0.0])

                    lon, lat = coords[0], coords[1]
                    f_id = props.get("facility_id", f"fac_local_{idx}")
                    name = props.get("name", "Unnamed Facility")
                    cat = props.get("category", "OTHER_CRITICAL").upper()

                    fac_res = FacilityResult(
                        facility_id=f_id,
                        name=name,
                        category=cat,
                        latitude=lat,
                        longitude=lon,
                        source=props.get("source", "Local Vector Dataset"),
                        source_id=props.get("source_id"),
                        source_type=props.get("source_type", "OPEN_GOVERNMENT"),
                        verification_status=props.get("verification_status", "VERIFIED"),
                        operational_status=props.get("operational_status", "UNKNOWN"),
                        provider_mode=self.provider_mode,
                        summary=f"{name} ({cat})",
                        provenance=props.get("provenance"),
                    )

                    if category and fac_res.category != category.upper():
                        continue
                    if verification_status and fac_res.verification_status != verification_status.upper():
                        continue
                    if bbox and not (
                        bbox.get("min_lat", -90) <= lat <= bbox.get("max_lat", 90)
                        and bbox.get("min_lon", -180) <= lon <= bbox.get("max_lon", 180)
                    ):
                        continue

                    facilities.append(fac_res)
            except Exception as err:  # noqa: BLE001
                logger.warning("Failed to parse local facility GeoJSON", file=str(file_path), error=str(err))

        return facilities

    async def get_facility_by_id(self, facility_id: str) -> FacilityResult | None:
        all_facs = await self.list_facilities()
        for f in all_facs:
            if f.facility_id == facility_id:
                return f
        return None

    async def get_facility(self, facility_id: str) -> FacilityResult | None:
        return await self.get_facility_by_id(facility_id)


def get_critical_facility_provider() -> BaseCriticalFacilityProvider:
    """Factory to retrieve configured critical facility provider instance."""
    repo_root = Path(__file__).resolve().parents[3]
    data_dir = repo_root / settings.CRITICAL_FACILITIES_DATA_PATH
    if data_dir.exists() and any(data_dir.glob("*.json")):
        return LocalCriticalFacilityProvider(data_path=data_dir)
    mode = getattr(settings, "FACILITY_PROVIDER", "LOCAL").upper()
    if mode == "SYNTHETIC":
        return SyntheticCriticalFacilityProvider()
    return LocalCriticalFacilityProvider(data_path=data_dir)

