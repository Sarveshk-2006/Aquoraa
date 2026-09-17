"""
Intervention Candidate Provider Implementations for Phase 12 Protect the City.

Defines abstract BaseInterventionCandidateProvider and implementations:
1. SyntheticInterventionCandidateProvider — Deterministic synthetic candidate generator for dev & testing.
2. LocalInterventionCandidateProvider — File-backed reader for verified GeoJSON intervention datasets.
"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import logger
from app.schemas.protect_city import INTERVENTION_TAXONOMY


class CandidateResult:
    """Container for intervention candidate entity metadata."""

    def __init__(
        self,
        candidate_id: str,
        name: str,
        candidate_type: str,
        latitude: float,
        longitude: float,
        source: str,
        source_id: str | None = None,
        source_type: str = "SYNTHETIC",
        verification_status: str = "UNVERIFIED",
        provider_mode: str = "SYNTHETIC",
        environment: str = "DEVELOPMENT_ONLY",
        affected_asset_type: str | None = None,
        affected_asset_id: str | None = None,
        summary: str | None = None,
        provenance: dict[str, Any] | None = None,
    ):
        self.candidate_id = candidate_id
        self.name = name
        self.candidate_type = candidate_type if candidate_type in INTERVENTION_TAXONOMY else "OTHER_REVIEW"
        self.latitude = latitude
        self.longitude = longitude
        self.source = source
        self.source_id = source_id
        self.source_type = source_type
        self.verification_status = verification_status
        self.provider_mode = provider_mode
        self.environment = environment
        self.affected_asset_type = affected_asset_type
        self.affected_asset_id = affected_asset_id
        self.summary = summary or f"{name} ({candidate_type})"
        self.provenance = provenance or {
            "source": source,
            "source_type": source_type,
            "verification_status": verification_status,
            "environment": environment,
        }


class BaseInterventionCandidateProvider(ABC):
    """Abstract interface for intervention candidate providers."""

    @abstractmethod
    async def list_candidates(
        self,
        candidate_type: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[CandidateResult]:
        """List intervention candidates matching query criteria."""

    @abstractmethod
    async def get_candidate_by_id(self, candidate_id: str) -> CandidateResult | None:
        """Retrieve single intervention candidate by ID."""

    async def get_candidate(self, candidate_id: str) -> CandidateResult | None:
        """Alias for get_candidate_by_id."""
        return await self.get_candidate_by_id(candidate_id)

    def get_candidates(self) -> list[CandidateResult]:
        """Synchronous candidate getter for unit test inspection."""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return self.list_candidates_sync()
            return loop.run_until_complete(self.list_candidates())
        except Exception:  # noqa: BLE001
            return self.list_candidates_sync()

    def list_candidates_sync(self) -> list[CandidateResult]:
        """Synchronous list candidates fallback."""
        return []


class SyntheticInterventionCandidateProvider(BaseInterventionCandidateProvider):
    """
    Deterministic synthetic intervention candidate provider for development and testing.
    Generates pilot candidates in Mumbai Mithi catchment (Kurla / Saki Naka / Kalina / Sion corridor).
    Explicitly tags outputs as SYNTHETIC / DEVELOPMENT_ONLY. Never presents synthetic assets as real.
    """

    def __init__(self):
        self.provider_id = "SYNTHETIC_INTERVENTION_PROVIDER"
        self.provider_mode = "SYNTHETIC"
        self.environment = "DEVELOPMENT_ONLY"

        # Deterministic pilot test fixtures in Mumbai Mithi River catchment
        self._fixtures: list[CandidateResult] = [
            CandidateResult(
                candidate_id="cand_kurla_inlet_01",
                name="Planning Candidate - Development Data: Kurla Junction Inlet Clearance",
                candidate_type="DRAINAGE_CLEARANCE",
                latitude=19.0760,
                longitude=72.8777,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_CAND_001",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                provider_mode=self.provider_mode,
                environment=self.environment,
                affected_asset_type="ROAD_CORRIDOR",
                affected_asset_id="ASSET_KURLA_JCT",
                summary="Planning Candidate - Development Data (Kurla Junction Drainage Inlet)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test candidate - development/test use only.",
                },
            ),
            CandidateResult(
                candidate_id="cand_sakinaka_road_01",
                name="Planning Candidate - Development Data: Saki Naka Road Access Protection",
                candidate_type="ROAD_ACCESS_PROTECTION",
                latitude=19.0880,
                longitude=72.8890,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_CAND_002",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                provider_mode=self.provider_mode,
                environment=self.environment,
                affected_asset_type="CRITICAL_ROUTE",
                affected_asset_id="ASSET_SAKI_NAKA_RD",
                summary="Planning Candidate - Development Data (Saki Naka Corridor)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test candidate - development/test use only.",
                },
            ),
            CandidateResult(
                candidate_id="cand_kalina_hospital_01",
                name="Planning Candidate - Development Data: Kalina Hospital Access Protection",
                candidate_type="CRITICAL_FACILITY_ACCESS_PROTECTION",
                latitude=19.0700,
                longitude=72.8700,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_CAND_003",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                provider_mode=self.provider_mode,
                environment=self.environment,
                affected_asset_type="CRITICAL_FACILITY_APPROACH",
                affected_asset_id="fac_hospital_a",
                summary="Planning Candidate - Development Data (Hospital Approach Corridor)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test candidate - development/test use only.",
                },
            ),
            CandidateResult(
                candidate_id="cand_sion_pump_01",
                name="Planning Candidate - Development Data: Sion Dewatering Review Location",
                candidate_type="PUMP_OR_DEWATERING_REVIEW",
                latitude=19.0400,
                longitude=72.8600,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_CAND_004",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                provider_mode=self.provider_mode,
                environment=self.environment,
                affected_asset_type="DRAINAGE_OUTLET",
                affected_asset_id="ASSET_SION_OUTLET",
                summary="Planning Candidate - Development Data (Sion Lowland Dewatering Location)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test candidate - development/test use only.",
                },
            ),
            CandidateResult(
                candidate_id="cand_mithi_outfall_01",
                name="Planning Candidate - Development Data: Mithi River Outfall Capacity Review",
                candidate_type="OUTFALL_CAPACITY_REVIEW",
                latitude=19.0550,
                longitude=72.8550,
                source="AQUORA Synthetic Fixtures v1.0",
                source_id="FIX_CAND_005",
                source_type="SYNTHETIC",
                verification_status="SYNTHETIC_FIXTURE",
                provider_mode=self.provider_mode,
                environment=self.environment,
                affected_asset_type="MUNICIPAL_OUTFALL",
                affected_asset_id="ASSET_MITHI_OUTFALL_1",
                summary="Planning Candidate - Development Data (Mithi River Outfall Bottleneck)",
                provenance={
                    "provider": self.provider_id,
                    "provider_mode": self.provider_mode,
                    "environment": self.environment,
                    "disclaimer": "Synthetic test candidate - development/test use only.",
                },
            ),
        ]

    async def list_candidates(
        self,
        candidate_type: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[CandidateResult]:
        res = list(self._fixtures)
        if candidate_type:
            c_upper = candidate_type.upper()
            res = [f for f in res if f.candidate_type == c_upper]
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

    def list_candidates_sync(
        self,
        candidate_type: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[CandidateResult]:
        res = self._fixtures
        if candidate_type:
            res = [f for f in res if f.candidate_type.upper() == candidate_type.upper()]
        if verification_status:
            res = [f for f in res if f.verification_status.upper() == verification_status.upper()]
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

    async def get_candidate_by_id(self, candidate_id: str) -> CandidateResult | None:
        for f in self._fixtures:
            if f.candidate_id == candidate_id:
                return f
        return None


class LocalInterventionCandidateProvider(BaseInterventionCandidateProvider):
    """
    File-backed reader for verified local GeoJSON / JSON intervention candidate layers.
    """

    def __init__(self, data_path: Path | str | None = None):
        self.provider_id = "LOCAL_INTERVENTION_PROVIDER"
        self.provider_mode = "LOCAL_VERIFIED"
        self.data_path = Path(data_path or settings.INTERVENTION_CANDIDATE_DATA_PATH)

    async def list_candidates(
        self,
        candidate_type: str | None = None,
        verification_status: str | None = None,
        bbox: dict[str, float] | None = None,
    ) -> list[CandidateResult]:
        candidates: list[CandidateResult] = []

        if not self.data_path.exists():
            logger.warning("Local intervention candidates directory not found, fallback to empty", path=str(self.data_path))
            return candidates

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
                    c_id = props.get("candidate_id", f"cand_local_{idx}")
                    name = props.get("name", "Unnamed Candidate")
                    c_type = props.get("candidate_type", "OTHER_REVIEW").upper()

                    cand_res = CandidateResult(
                        candidate_id=c_id,
                        name=name,
                        candidate_type=c_type,
                        latitude=lat,
                        longitude=lon,
                        source=props.get("source", "Local Vector Dataset"),
                        source_id=props.get("source_id"),
                        source_type=props.get("source_type", "OPEN_GOVERNMENT"),
                        verification_status=props.get("verification_status", "VERIFIED"),
                        provider_mode=self.provider_mode,
                        environment=props.get("environment", "PRODUCTION"),
                        affected_asset_type=props.get("affected_asset_type"),
                        affected_asset_id=props.get("affected_asset_id"),
                        summary=f"{name} ({c_type})",
                        provenance=props.get("provenance"),
                    )

                    if candidate_type and cand_res.candidate_type != candidate_type.upper():
                        continue
                    if verification_status and cand_res.verification_status != verification_status.upper():
                        continue
                    if bbox and not (bbox.get("min_lat", -90) <= lat <= bbox.get("max_lat", 90) and
                                    bbox.get("min_lon", -180) <= lon <= bbox.get("max_lon", 180)):
                        continue

                    candidates.append(cand_res)
            except Exception as err:  # noqa: BLE001
                logger.warning("Failed to parse local intervention GeoJSON", file=str(file_path), error=str(err))

        return candidates

    async def get_candidate_by_id(self, candidate_id: str) -> CandidateResult | None:
        all_cands = await self.list_candidates()
        for f in all_cands:
            if f.candidate_id == candidate_id:
                return f
        return None


def get_intervention_candidate_provider() -> BaseInterventionCandidateProvider:
    """Factory to retrieve configured intervention candidate provider instance."""
    mode = getattr(settings, "INTERVENTION_PROVIDER", "SYNTHETIC").upper()
    if mode == "LOCAL":
        return LocalInterventionCandidateProvider()
    return SyntheticInterventionCandidateProvider()
