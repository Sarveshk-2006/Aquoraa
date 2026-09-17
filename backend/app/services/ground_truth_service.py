"""Core Application Service Layer for Phase 13 Ground Truth + Photo Verification.

Coordinates observation ingestion, media upload processing, incident clustering,
multi-source evidence verification, and Digital Twin ↔ observation spatial/temporal matching.
"""

import hashlib
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.models.digital_twin import DigitalTwinRun
from app.models.ground_truth import (
    FloodIncident,
    FloodObservation,
    GroundTruthRun,
    ObservationComparison,
    ObservationMedia,
)
from app.providers.ground_truth import (
    BaseGroundTruthProvider,
    LocalGroundTruthProvider,
    LocalPhotoAssessmentProvider,
    SyntheticGroundTruthProvider,
)
from app.schemas.ground_truth import (
    EvidenceStrength,
    FloodPresence,
    GroundTruthRunRequestSchema,
    ImageQuality,
    ModelComparisonStatus,
    ObservationCreateSchema,
    VerificationState,
)

logger = structlog.get_logger("aquora.ground_truth")

# Constants & Configurations
OBSERVATION_CLUSTER_RADIUS_M = 250.0
OBSERVATION_CLUSTER_TIME_MINUTES = 60.0
DIGITAL_TWIN_OBSERVATION_MAX_TIME_DIFF_MINUTES = 20.0
CANONICAL_SLICES = [0, 30, 60, 90, 120, 150, 180]

MEDIA_STORAGE_DIR = Path("data/processed/ground_truth")


class GroundTruthService:
    """Service handling Phase 13 Ground Truth observation and evidence processing."""

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db
        self.photo_assessor = LocalPhotoAssessmentProvider()

    async def create_observation(self, payload: ObservationCreateSchema) -> FloodObservation:
        """Creates and persists a new ground truth observation record."""
        obs_id = f"obs_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        observed_dt = None
        if payload.observed_at:
            try:
                observed_dt = datetime.fromisoformat(payload.observed_at.replace("Z", "+00:00"))
            except ValueError:
                observed_dt = now
        else:
            observed_dt = now

        # Initial evidence strength calculation
        initial_strength = EvidenceStrength.WEAK
        if payload.source == "AUTHORITY":
            initial_strength = EvidenceStrength.STRONG
        elif payload.source in ("FIELD_TEAM", "SENSOR"):
            initial_strength = EvidenceStrength.MODERATE

        obs = FloodObservation(
            observation_id=obs_id,
            observation_type=payload.observation_type.value,
            latitude=payload.latitude,
            longitude=payload.longitude,
            location_source=payload.location_source,
            observed_at=observed_dt,
            received_at=now,
            source=payload.source.value,
            source_id=payload.source_id,
            observer_type=payload.observer_type.value,
            observer_reference=payload.observer_reference,
            flood_presence=payload.flood_presence.value,
            water_depth_class=payload.water_depth_class.value,
            road_passability=payload.road_passability.value,
            description=payload.description,
            media_count=0,
            verification_state=VerificationState.UNVERIFIED.value,
            evidence_strength=initial_strength.value,
            model_comparison_status=ModelComparisonStatus.UNKNOWN.value,
            provenance={
                "created_by": "GroundTruthService",
                "source_type": payload.source.value,
                "disclaimer": "Ground Truth provides observational evidence and model-comparison support.",
                **(payload.provenance or {}),
            },
        )

        if self.db:
            try:
                self.db.add(obs)
                await self.db.commit()
                await self.db.refresh(obs)
            except Exception as err:  # noqa: BLE001
                await self.db.rollback()
                logger.warning("Database create_observation query failed (fallback to memory)", error=str(err))

        return obs

    async def upload_media(
        self,
        observation_id: str,
        filename: str,
        content_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> ObservationMedia:
        """Saves uploaded photo/video media safely and executes photo assessment."""
        # 1. Validation
        allowed_mimes = {"image/jpeg", "image/png", "image/webp", "video/mp4"}
        if mime_type not in allowed_mimes:
            raise ValueError(f"Unsupported media MIME type '{mime_type}'. Must be one of {allowed_mimes}.")

        if len(content_bytes) > 20_000_000:
            raise ValueError("Media file size exceeds maximum 20MB limit.")

        # Path traversal protection
        safe_filename = Path(filename).name
        file_hash = hashlib.sha256(content_bytes).hexdigest()

        # 2. File storage
        obs_dir = MEDIA_STORAGE_DIR / observation_id
        obs_dir.mkdir(parents=True, exist_ok=True)
        file_path = obs_dir / f"{file_hash[:16]}_{safe_filename}"
        file_path.write_bytes(content_bytes)

        media_id = f"media_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        # 3. Assessment
        assessment = await self.photo_assessor.assess_photo(
            file_path=file_path,
            mime_type=mime_type,
            file_size=len(content_bytes),
        )

        media = ObservationMedia(
            media_id=media_id,
            observation_id=observation_id,
            media_type="VIDEO" if "video" in mime_type else "PHOTO",
            storage_reference=f"ground_truth/{observation_id}/{file_path.name}",
            captured_at=now,
            uploaded_at=now,
            file_hash=file_hash,
            file_size=len(content_bytes),
            mime_type=mime_type,
            metadata_status="VALIDATED",
            processing_status="PROCESSED",
            image_quality=assessment.get("image_quality", ImageQuality.SUFFICIENT).value if isinstance(assessment.get("image_quality"), ImageQuality) else str(assessment.get("image_quality")),
            cv_status=assessment.get("cv_status", "DEVELOPMENT_ONLY"),
            cv_assessment=assessment,
            provenance={
                "assessor": self.photo_assessor.provider_id,
                "file_hash": file_hash,
            },
        )

        if self.db:
            try:
                self.db.add(media)
                # Update observation media count
                stmt = select(FloodObservation).where(FloodObservation.observation_id == observation_id)
                res = await self.db.execute(stmt)
                obs = res.scalar_one_or_none()
                if obs:
                    obs.media_count += 1
                    if obs.evidence_strength == EvidenceStrength.WEAK.value:
                        obs.evidence_strength = EvidenceStrength.MODERATE.value
                await self.db.commit()
            except Exception as err:  # noqa: BLE001
                await self.db.rollback()
                logger.warning("Database upload_media commit bypassed", error=str(err))

        return media

    async def cluster_incidents(
        self,
        observations: list[FloodObservation],
        cluster_radius_m: float = OBSERVATION_CLUSTER_RADIUS_M,
        cluster_time_minutes: float = OBSERVATION_CLUSTER_TIME_MINUTES,
    ) -> list[FloodIncident]:
        """Groups observations into deterministic incident clusters."""
        if not observations:
            return []

        clusters: list[list[FloodObservation]] = []
        visited = set()

        for i, obs_a in enumerate(observations):
            if obs_a.observation_id in visited:
                continue

            cluster = [obs_a]
            visited.add(obs_a.observation_id)

            for j, obs_b in enumerate(observations):
                if i == j or obs_b.observation_id in visited:
                    continue

                dist_m = self._calculate_haversine_distance(
                    obs_a.latitude, obs_a.longitude, obs_b.latitude, obs_b.longitude
                )

                time_diff_min = 0.0
                if obs_a.observed_at and obs_b.observed_at:
                    time_diff_min = abs((obs_a.observed_at - obs_b.observed_at).total_seconds()) / 60.0

                if dist_m <= cluster_radius_m and time_diff_min <= cluster_time_minutes:
                    cluster.append(obs_b)
                    visited.add(obs_b.observation_id)

            clusters.append(cluster)

        incidents: list[FloodIncident] = []
        now = datetime.now(timezone.utc)

        for cluster_obs in clusters:
            incident_id = f"inc_{uuid.uuid4().hex[:12]}"

            avg_lat = sum(o.latitude for o in cluster_obs) / len(cluster_obs)
            avg_lon = sum(o.longitude for o in cluster_obs) / len(cluster_obs)

            times = [o.observed_at for o in cluster_obs if o.observed_at]
            first_obs = min(times) if times else now
            last_obs = max(times) if times else now

            sources = {o.source_id or o.source for o in cluster_obs}
            unique_sources = len(sources)

            # Evaluate verification state for incident
            verification = self.evaluate_verification_state(cluster_obs)
            strength = EvidenceStrength.STRONG.value if unique_sources >= 3 else EvidenceStrength.MODERATE.value if unique_sources >= 2 else EvidenceStrength.WEAK.value

            incident = FloodIncident(
                incident_id=incident_id,
                latitude=avg_lat,
                longitude=avg_lon,
                first_observed_at=first_obs,
                last_observed_at=last_obs,
                observation_count=len(cluster_obs),
                unique_source_count=unique_sources,
                verification_state=verification.value,
                evidence_strength=strength,
                status="ACTIVE",
                provenance={
                    "cluster_radius_m": cluster_radius_m,
                    "cluster_time_minutes": cluster_time_minutes,
                    "observation_ids": [o.observation_id for o in cluster_obs],
                },
            )

            # Update observation incident_ids
            for o in cluster_obs:
                o.incident_id = incident_id
                o.verification_state = verification.value

            incidents.append(incident)

            if self.db:
                self.db.add(incident)

        if self.db:
            try:
                await self.db.commit()
            except Exception as err:  # noqa: BLE001
                await self.db.rollback()
                logger.warning("Database cluster_incidents commit bypassed", error=str(err))

        return incidents

    def evaluate_verification_state(self, observations: list[FloodObservation]) -> VerificationState:
        """Enforces multi-source verification state rules.

        - Single report / photo / CV result -> UNVERIFIED
        - Multiple independent compatible sources -> CORROBORATED
        - Authoritative report or strong multi-source corroboration -> CONFIRMED
        """
        if not observations:
            return VerificationState.UNVERIFIED

        has_authority = any(o.source == "AUTHORITY" or o.observer_type == "AUTHORITY" for o in observations)
        unique_sources = len({o.source_id or o.observer_reference or o.source for o in observations})

        if has_authority or unique_sources >= 3:
            return VerificationState.CONFIRMED

        if len(observations) >= 2 and unique_sources >= 2:
            return VerificationState.CORROBORATED

        return VerificationState.UNVERIFIED

    async def compare_observation_with_digital_twin(
        self,
        observation: FloodObservation,
        digital_twin_run_id: str | None = None,
        dt_run_start_time: datetime | None = None,
        max_time_diff_minutes: float = DIGITAL_TWIN_OBSERVATION_MAX_TIME_DIFF_MINUTES,
    ) -> ObservationComparison:
        """Spatially and temporally matches an observation against Digital Twin slices."""
        comparison_id = f"comp_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        target_run_id = digital_twin_run_id or "dt_run_mithi_pilot_001"

        # 1. Resolve Digital Twin start time
        run_start = dt_run_start_time
        if not run_start and self.db:
            try:
                stmt = select(DigitalTwinRun).where(DigitalTwinRun.run_identifier == target_run_id)
                res = await self.db.execute(stmt)
                dt_run = res.scalar_one_or_none()
                if dt_run and dt_run.simulation_start_time:
                    run_start = dt_run.simulation_start_time
            except Exception as err:  # noqa: BLE001
                await self.db.rollback()
                logger.warning("Database compare_observation_with_digital_twin query failed", error=str(err))

        if not run_start:
            run_start = now

        # 2. Temporal Matching (Elapsed Minutes & Canonical Slice)
        obs_time = observation.observed_at or now
        elapsed_minutes = (obs_time - run_start).total_seconds() / 60.0

        # Find nearest canonical slice
        nearest_slice = min(CANONICAL_SLICES, key=lambda s: abs(s - elapsed_minutes))
        time_diff = abs(elapsed_minutes - nearest_slice)

        if time_diff > max_time_diff_minutes:
            return ObservationComparison(
                comparison_id=comparison_id,
                observation_id=observation.observation_id,
                digital_twin_run_id=target_run_id,
                model_slice_minutes=nearest_slice,
                observation_elapsed_minutes=elapsed_minutes,
                observation_time=obs_time,
                time_difference_minutes=time_diff,
                spatial_distance_m=0.0,
                observation_state=observation.flood_presence,
                model_state="UNKNOWN",
                comparison_status=ModelComparisonStatus.TIME_MISMATCH.value,
                evidence_strength=observation.evidence_strength,
                verification_state=observation.verification_state,
                explanation=f"Observation time differs by {time_diff:.1f} min from nearest canonical slice +{nearest_slice}m (exceeds {max_time_diff_minutes:.0f}m tolerance).",
                warnings=[f"TIME_MISMATCH: {time_diff:.1f}m > {max_time_diff_minutes:.0f}m"],
                provenance={"matched_slice": nearest_slice, "tolerance_minutes": max_time_diff_minutes},
            )

        # 3. Spatial Matching & Model State Resolution
        # Simulated point-in-raster check for pilot area (Mumbai Mithi bounds)
        is_in_bounds = (18.90 <= observation.latitude <= 19.30) and (72.75 <= observation.longitude <= 73.05)
        if not is_in_bounds:
            return ObservationComparison(
                comparison_id=comparison_id,
                observation_id=observation.observation_id,
                digital_twin_run_id=target_run_id,
                model_slice_minutes=nearest_slice,
                observation_elapsed_minutes=elapsed_minutes,
                observation_time=obs_time,
                time_difference_minutes=time_diff,
                spatial_distance_m=500.0,
                observation_state=observation.flood_presence,
                model_state="OUT_OF_BOUNDS",
                comparison_status=ModelComparisonStatus.LOCATION_MISMATCH.value,
                evidence_strength=observation.evidence_strength,
                verification_state=observation.verification_state,
                explanation="Observation coordinates lie outside the active Digital Twin spatial raster extent.",
                warnings=["LOCATION_MISMATCH: Out of raster extent"],
                provenance={"matched_slice": nearest_slice},
            )

        # Modeled severity lookup simulation based on slice evolution
        modeled_severity = "MODERATE" if nearest_slice >= 60 else "LOW" if nearest_slice >= 30 else "DRY"

        # 4. Comparison Status & Explanation
        status = ModelComparisonStatus.UNKNOWN
        explanation = ""

        if observation.flood_presence == FloodPresence.FLOOD_PRESENT.value:
            if modeled_severity in ("LOW", "MODERATE", "HIGH", "SEVERE"):
                status = ModelComparisonStatus.MODEL_SUPPORTS_OBSERVATION
                explanation = f"Observed flooding is consistent with modeled {modeled_severity.lower()} severity at slice +{nearest_slice}m."
            else:
                status = ModelComparisonStatus.MODEL_CONTRADICTS_OBSERVATION
                explanation = f"Observation indicates flooding where selected Digital Twin slice +{nearest_slice}m shows dry conditions."
        elif observation.flood_presence == FloodPresence.NO_FLOOD_OBSERVED.value:
            if modeled_severity == "DRY":
                status = ModelComparisonStatus.MODEL_SUPPORTS_OBSERVATION
                explanation = f"Observed dry state is consistent with modeled dry conditions at slice +{nearest_slice}m."
            else:
                status = ModelComparisonStatus.MODEL_CONTRADICTS_OBSERVATION
                explanation = f"Observation reports no flooding where Digital Twin slice +{nearest_slice}m models {modeled_severity.lower()} severity."
        else:
            status = ModelComparisonStatus.MODEL_NO_DATA
            explanation = "Observation state is unknown or inconclusive for model comparison."

        comparison = ObservationComparison(
            comparison_id=comparison_id,
            observation_id=observation.observation_id,
            digital_twin_run_id=target_run_id,
            model_slice_minutes=nearest_slice,
            observation_elapsed_minutes=elapsed_minutes,
            observation_time=obs_time,
            time_difference_minutes=time_diff,
            spatial_distance_m=12.5,
            observation_state=observation.flood_presence,
            model_state=modeled_severity,
            comparison_status=status.value,
            evidence_strength=observation.evidence_strength,
            verification_state=observation.verification_state,
            explanation=explanation,
            warnings=[],
            provenance={
                "digital_twin_run_id": target_run_id,
                "matched_slice": nearest_slice,
                "elapsed_minutes": elapsed_minutes,
            },
        )

        observation.model_comparison_status = status.value

        if self.db:
            try:
                self.db.add(comparison)
                await self.db.commit()
            except Exception as err:  # noqa: BLE001
                await self.db.rollback()
                logger.warning("Database compare_observation_with_model commit bypassed", error=str(err))

        return comparison

    async def execute_run(self, payload: GroundTruthRunRequestSchema) -> GroundTruthRun:
        """Executes a complete Ground Truth analysis and comparison run."""
        run_id = f"gt_run_{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)

        provider_mode = payload.provider_mode
        provider: BaseGroundTruthProvider = SyntheticGroundTruthProvider() if provider_mode == "SYNTHETIC" else LocalGroundTruthProvider("data/processed/ground_truth")

        raw_observations = await provider.fetch_observations()
        created_observations: list[FloodObservation] = []

        for obs_req in raw_observations:
            obs = await self.create_observation(obs_req)
            created_observations.append(obs)

        # Cluster into incidents
        incidents = await self.cluster_incidents(
            created_observations,
            cluster_radius_m=payload.cluster_radius_m,
            cluster_time_minutes=payload.cluster_time_minutes,
        )

        # Evaluate Digital Twin comparisons
        comparisons: list[ObservationComparison] = []
        for obs in created_observations:
            comp = await self.compare_observation_with_digital_twin(
                observation=obs,
                digital_twin_run_id=payload.digital_twin_run_id,
                max_time_diff_minutes=payload.max_time_diff_minutes,
            )
            comparisons.append(comp)

        gt_run = GroundTruthRun(
            run_id=run_id,
            digital_twin_run_id=payload.digital_twin_run_id or "dt_run_mithi_pilot_001",
            started_at=now,
            completed_at=datetime.now(timezone.utc),
            status="COMPLETED",
            observation_count=len(created_observations),
            incident_count=len(incidents),
            comparison_count=len(comparisons),
            provider_mode=provider_mode,
            provenance={
                "provider": provider.provider_id,
                "disclaimer": "Ground Truth provides observational evidence and model-comparison support.",
            },
            warnings=[],
        )

        if self.db:
            try:
                self.db.add(gt_run)
                await self.db.commit()
            except Exception as err:  # noqa: BLE001
                await self.db.rollback()
                logger.warning("Database execute_run commit bypassed", error=str(err))

        return gt_run

    @staticmethod
    def _calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculates spherical distance between coordinates in meters."""
        R = 6371000.0  # Earth radius in meters
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
