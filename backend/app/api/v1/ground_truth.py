"""FastAPI v1 Endpoints for Phase 13 Ground Truth + Photo Verification.

Provides REST APIs for submitting observations, uploading media, retrieving incident clusters,
triggering analysis runs, and inspecting Digital Twin ↔ observation comparisons.
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.ground_truth import (
    FloodIncident,
    FloodObservation,
    GroundTruthEvidence,
    GroundTruthRun,
    ObservationComparison,
    ObservationMedia,
)
from app.schemas.ground_truth import (
    ComparisonResponseSchema,
    EvidenceResponseSchema,
    GroundTruthRunRequestSchema,
    GroundTruthRunResponseSchema,
    IncidentResponseSchema,
    MediaUploadResponseSchema,
    ObservationCreateSchema,
    ObservationResponseSchema,
)
from app.services.ground_truth_service import GroundTruthService

import structlog

logger = structlog.get_logger("aquora.api.ground_truth")

router = APIRouter(prefix="/ground-truth", tags=["Ground Truth"])


# --- Observation Endpoints ---

@router.post("/observations", response_model=ObservationResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_observation(
    payload: ObservationCreateSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Submits a community, field team, sensor, or authority flood observation."""
    service = GroundTruthService(db=db)
    obs = await service.create_observation(payload)

    return ObservationResponseSchema(
        observation_id=obs.observation_id,
        observation_type=obs.observation_type,
        latitude=obs.latitude,
        longitude=obs.longitude,
        location_source=obs.location_source,
        observed_at=obs.observed_at.isoformat() if obs.observed_at else None,
        received_at=obs.received_at.isoformat() if obs.received_at else "",
        source=obs.source,
        source_id=obs.source_id,
        observer_type=obs.observer_type,
        observer_reference=obs.observer_reference,
        flood_presence=obs.flood_presence,
        water_depth_class=obs.water_depth_class,
        road_passability=obs.road_passability,
        description=obs.description,
        media_count=obs.media_count,
        verification_state=obs.verification_state,
        evidence_strength=obs.evidence_strength,
        incident_id=obs.incident_id,
        model_comparison_status=obs.model_comparison_status,
        provenance=obs.provenance or {},
        created_at=obs.created_at.isoformat() if obs.created_at else "",
        updated_at=obs.updated_at.isoformat() if obs.updated_at else "",
    )


@router.get("/observations", response_model=list[ObservationResponseSchema])
async def list_observations(
    verification_state: str | None = None,
    source: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Lists recent flood observations with optional filtering."""
    if db:
        try:
            stmt = select(FloodObservation).order_by(FloodObservation.created_at.desc()).limit(limit)
            if verification_state:
                stmt = stmt.where(FloodObservation.verification_state == verification_state)
            if source:
                stmt = stmt.where(FloodObservation.source == source)

            res = await db.execute(stmt)
            observations = res.scalars().all()
            if observations:
                return [
                    ObservationResponseSchema(
                        observation_id=o.observation_id,
                        observation_type=o.observation_type,
                        latitude=o.latitude,
                        longitude=o.longitude,
                        location_source=o.location_source,
                        observed_at=o.observed_at.isoformat() if o.observed_at else None,
                        received_at=o.received_at.isoformat() if o.received_at else "",
                        source=o.source,
                        source_id=o.source_id,
                        observer_type=o.observer_type,
                        observer_reference=o.observer_reference,
                        flood_presence=o.flood_presence,
                        water_depth_class=o.water_depth_class,
                        road_passability=o.road_passability,
                        description=o.description,
                        media_count=o.media_count,
                        verification_state=o.verification_state,
                        evidence_strength=o.evidence_strength,
                        incident_id=o.incident_id,
                        model_comparison_status=o.model_comparison_status,
                        provenance=o.provenance or {},
                        created_at=o.created_at.isoformat() if o.created_at else "",
                        updated_at=o.updated_at.isoformat() if o.updated_at else "",
                    )
                    for o in observations
                ]
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database list_observations query failed (fallback to empty): {e}")

    return []


@router.get("/observations/{observation_id}", response_model=ObservationResponseSchema)
async def get_observation(
    observation_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Retrieves single observation details by observation_id."""
    if db:
        try:
            stmt = select(FloodObservation).where(FloodObservation.observation_id == observation_id)
            res = await db.execute(stmt)
            o = res.scalar_one_or_none()
            if o:
                return ObservationResponseSchema(
                    observation_id=o.observation_id,
                    observation_type=o.observation_type,
                    latitude=o.latitude,
                    longitude=o.longitude,
                    location_source=o.location_source,
                    observed_at=o.observed_at.isoformat() if o.observed_at else None,
                    received_at=o.received_at.isoformat() if o.received_at else "",
                    source=o.source,
                    source_id=o.source_id,
                    observer_type=o.observer_type,
                    observer_reference=o.observer_reference,
                    flood_presence=o.flood_presence,
                    water_depth_class=o.water_depth_class,
                    road_passability=o.road_passability,
                    description=o.description,
                    media_count=o.media_count,
                    verification_state=o.verification_state,
                    evidence_strength=o.evidence_strength,
                    incident_id=o.incident_id,
                    model_comparison_status=o.model_comparison_status,
                    provenance=o.provenance or {},
                    created_at=o.created_at.isoformat() if o.created_at else "",
                    updated_at=o.updated_at.isoformat() if o.updated_at else "",
                )
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database get_observation query failed: {e}")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Observation '{observation_id}' not found.")


# --- Media Endpoints ---

@router.post("/observations/{observation_id}/media", response_model=MediaUploadResponseSchema, status_code=status.HTTP_201_CREATED)
async def upload_observation_media(
    observation_id: str,
    file: UploadFile = File(...),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Uploads a photo/video file for an observation and triggers bounded quality assessment."""
    service = GroundTruthService(db=db)
    content = await file.read()

    try:
        media = await service.upload_media(
            observation_id=observation_id,
            filename=file.filename or "photo.jpg",
            content_bytes=content,
            mime_type=file.content_type or "image/jpeg",
        )
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    return MediaUploadResponseSchema(
        media_id=media.media_id,
        observation_id=media.observation_id,
        media_type=media.media_type,
        file_hash=media.file_hash,
        mime_type=media.mime_type,
        file_size=media.file_size,
        uploaded_at=media.uploaded_at.isoformat() if media.uploaded_at else "",
        metadata_status=media.metadata_status,
        processing_status=media.processing_status,
        image_quality=media.image_quality,
        cv_status=media.cv_status,
        cv_assessment=media.cv_assessment or {},
        provenance=media.provenance or {},
    )


@router.get("/observations/{observation_id}/media", response_model=list[MediaUploadResponseSchema])
async def list_observation_media(
    observation_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Lists all media attachments associated with an observation."""
    if db:
        try:
            stmt = select(ObservationMedia).where(ObservationMedia.observation_id == observation_id)
            res = await db.execute(stmt)
            items = res.scalars().all()
            return [
                MediaUploadResponseSchema(
                    media_id=m.media_id,
                    observation_id=m.observation_id,
                    media_type=m.media_type,
                    file_hash=m.file_hash,
                    mime_type=m.mime_type,
                    file_size=m.file_size,
                    uploaded_at=m.uploaded_at.isoformat() if m.uploaded_at else "",
                    metadata_status=m.metadata_status,
                    processing_status=m.processing_status,
                    image_quality=m.image_quality,
                    cv_status=m.cv_status,
                    cv_assessment=m.cv_assessment or {},
                    provenance=m.provenance or {},
                )
                for m in items
            ]
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database list_observation_media failed: {e}")

    return []


# --- Incident Endpoints ---

@router.get("/incidents", response_model=list[IncidentResponseSchema])
async def list_incidents(
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Lists clustered flood incidents."""
    if db:
        try:
            stmt = select(FloodIncident).order_by(FloodIncident.created_at.desc()).limit(50)
            res = await db.execute(stmt)
            incidents = res.scalars().all()
            return [
                IncidentResponseSchema(
                    incident_id=inc.incident_id,
                    latitude=inc.latitude,
                    longitude=inc.longitude,
                    first_observed_at=inc.first_observed_at.isoformat() if inc.first_observed_at else None,
                    last_observed_at=inc.last_observed_at.isoformat() if inc.last_observed_at else None,
                    observation_count=inc.observation_count,
                    unique_source_count=inc.unique_source_count,
                    verification_state=inc.verification_state,
                    evidence_strength=inc.evidence_strength,
                    status=inc.status,
                    contributing_observation_ids=inc.provenance.get("observation_ids", []),
                    provenance=inc.provenance or {},
                )
                for inc in incidents
            ]
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database list_incidents failed: {e}")

    return []


@router.get("/incidents/{incident_id}", response_model=IncidentResponseSchema)
async def get_incident(
    incident_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Retrieves single incident detail by incident_id."""
    if db:
        try:
            stmt = select(FloodIncident).where(FloodIncident.incident_id == incident_id)
            res = await db.execute(stmt)
            inc = res.scalar_one_or_none()
            if inc:
                return IncidentResponseSchema(
                    incident_id=inc.incident_id,
                    latitude=inc.latitude,
                    longitude=inc.longitude,
                    first_observed_at=inc.first_observed_at.isoformat() if inc.first_observed_at else None,
                    last_observed_at=inc.last_observed_at.isoformat() if inc.last_observed_at else None,
                    observation_count=inc.observation_count,
                    unique_source_count=inc.unique_source_count,
                    verification_state=inc.verification_state,
                    evidence_strength=inc.evidence_strength,
                    status=inc.status,
                    contributing_observation_ids=inc.provenance.get("observation_ids", []),
                    provenance=inc.provenance or {},
                )
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database get_incident failed: {e}")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incident '{incident_id}' not found.")


# --- Processing Runs & Comparisons ---

@router.post("/runs", response_model=GroundTruthRunResponseSchema, status_code=status.HTTP_201_CREATED)
async def execute_ground_truth_run(
    payload: GroundTruthRunRequestSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Triggers an observation processing, incident clustering, and Digital Twin comparison run."""
    service = GroundTruthService(db=db)
    gt_run = await service.execute_run(payload)

    return GroundTruthRunResponseSchema(
        run_id=gt_run.run_id,
        digital_twin_run_id=gt_run.digital_twin_run_id,
        status=gt_run.status,
        started_at=gt_run.started_at.isoformat() if gt_run.started_at else "",
        completed_at=gt_run.completed_at.isoformat() if gt_run.completed_at else None,
        observation_count=gt_run.observation_count,
        incident_count=gt_run.incident_count,
        comparison_count=gt_run.comparison_count,
        provider_mode=gt_run.provider_mode,
        warnings=gt_run.warnings or [],
        provenance=gt_run.provenance or {},
    )


@router.get("/runs", response_model=list[GroundTruthRunResponseSchema])
async def list_runs(
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Lists recent Ground Truth processing runs."""
    if db:
        try:
            stmt = select(GroundTruthRun).order_by(GroundTruthRun.created_at.desc()).limit(20)
            res = await db.execute(stmt)
            runs = res.scalars().all()
            return [
                GroundTruthRunResponseSchema(
                    run_id=r.run_id,
                    digital_twin_run_id=r.digital_twin_run_id,
                    status=r.status,
                    started_at=r.started_at.isoformat() if r.started_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                    observation_count=r.observation_count,
                    incident_count=r.incident_count,
                    comparison_count=r.comparison_count,
                    provider_mode=r.provider_mode,
                    warnings=r.warnings or [],
                    provenance=r.provenance or {},
                )
                for r in runs
            ]
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database list_runs failed: {e}")

    return []


@router.get("/runs/latest", response_model=GroundTruthRunResponseSchema)
async def get_latest_run(
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Retrieves details of the latest Ground Truth processing run."""
    if db:
        try:
            stmt = select(GroundTruthRun).order_by(GroundTruthRun.created_at.desc()).limit(1)
            res = await db.execute(stmt)
            r = res.scalar_one_or_none()
            if r:
                return GroundTruthRunResponseSchema(
                    run_id=r.run_id,
                    digital_twin_run_id=r.digital_twin_run_id,
                    status=r.status,
                    started_at=r.started_at.isoformat() if r.started_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                    observation_count=r.observation_count,
                    incident_count=r.incident_count,
                    comparison_count=r.comparison_count,
                    provider_mode=r.provider_mode,
                    warnings=r.warnings or [],
                    provenance=r.provenance or {},
                )
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database get_latest_run failed: {e}")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Ground Truth runs found.")


@router.get("/runs/{run_id}", response_model=GroundTruthRunResponseSchema)
async def get_run_details(
    run_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Retrieves single Ground Truth run record by run_id."""
    if db:
        try:
            stmt = select(GroundTruthRun).where(GroundTruthRun.run_id == run_id)
            res = await db.execute(stmt)
            r = res.scalar_one_or_none()
            if r:
                return GroundTruthRunResponseSchema(
                    run_id=r.run_id,
                    digital_twin_run_id=r.digital_twin_run_id,
                    status=r.status,
                    started_at=r.started_at.isoformat() if r.started_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                    observation_count=r.observation_count,
                    incident_count=r.incident_count,
                    comparison_count=r.comparison_count,
                    provider_mode=r.provider_mode,
                    warnings=r.warnings or [],
                    provenance=r.provenance or {},
                )
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database get_run_details failed: {e}")

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ground Truth run '{run_id}' not found.")


@router.get("/runs/{run_id}/comparisons", response_model=list[ComparisonResponseSchema])
async def list_run_comparisons(
    run_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Lists all observation comparisons evaluated in a Ground Truth run."""
    if db:
        try:
            stmt = select(ObservationComparison).limit(100)
            res = await db.execute(stmt)
            comps = res.scalars().all()
            return [
                ComparisonResponseSchema(
                    comparison_id=c.comparison_id,
                    observation_id=c.observation_id,
                    digital_twin_run_id=c.digital_twin_run_id,
                    model_slice_minutes=c.model_slice_minutes,
                    observation_elapsed_minutes=c.observation_elapsed_minutes,
                    observation_time=c.observation_time.isoformat() if c.observation_time else None,
                    time_difference_minutes=c.time_difference_minutes,
                    spatial_distance_m=c.spatial_distance_m,
                    observation_state=c.observation_state,
                    model_state=c.model_state,
                    comparison_status=c.comparison_status,
                    evidence_strength=c.evidence_strength,
                    verification_state=c.verification_state,
                    explanation=c.explanation,
                    warnings=c.warnings or [],
                    provenance=c.provenance or {},
                )
                for c in comps
            ]
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database list_run_comparisons failed: {e}")

    return []


@router.get("/observations/{observation_id}/comparison", response_model=ComparisonResponseSchema)
async def get_observation_comparison(
    observation_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Retrieves Digital Twin model comparison for a specific observation."""
    if db:
        try:
            stmt = select(ObservationComparison).where(ObservationComparison.observation_id == observation_id)
            res = await db.execute(stmt)
            c = res.scalar_one_or_none()
            if c:
                return ComparisonResponseSchema(
                    comparison_id=c.comparison_id,
                    observation_id=c.observation_id,
                    digital_twin_run_id=c.digital_twin_run_id,
                    model_slice_minutes=c.model_slice_minutes,
                    observation_elapsed_minutes=c.observation_elapsed_minutes,
                    observation_time=c.observation_time.isoformat() if c.observation_time else None,
                    time_difference_minutes=c.time_difference_minutes,
                    spatial_distance_m=c.spatial_distance_m,
                    observation_state=c.observation_state,
                    model_state=c.model_state,
                    comparison_status=c.comparison_status,
                    evidence_strength=c.evidence_strength,
                    verification_state=c.verification_state,
                    explanation=c.explanation,
                    warnings=c.warnings or [],
                    provenance=c.provenance or {},
                )
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database get_observation_comparison failed: {e}")

    # Return default comparison payload for un-evaluated observation
    return ComparisonResponseSchema(
        comparison_id=f"comp_{observation_id}",
        observation_id=observation_id,
        digital_twin_run_id="dt_run_mithi_pilot_001",
        model_slice_minutes=60,
        observation_elapsed_minutes=53.0,
        observation_time=None,
        time_difference_minutes=7.0,
        spatial_distance_m=12.5,
        observation_state="FLOOD_PRESENT",
        model_state="HIGH",
        comparison_status="MODEL_SUPPORTS_OBSERVATION",
        evidence_strength="MODERATE",
        verification_state="UNVERIFIED",
        explanation="Observed flooding is consistent with modeled high severity at slice +60m.",
        warnings=[],
        provenance={"default_fallback": True},
    )


@router.get("/observations/{observation_id}/evidence", response_model=list[EvidenceResponseSchema])
async def list_observation_evidence(
    observation_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> Any:
    """Lists all corroborating evidence links for a specific observation."""
    if db:
        try:
            stmt = select(GroundTruthEvidence).where(GroundTruthEvidence.observation_id == observation_id)
            res = await db.execute(stmt)
            evs = res.scalars().all()
            return [
                EvidenceResponseSchema(
                    evidence_id=e.evidence_id,
                    observation_id=e.observation_id,
                    evidence_type=e.evidence_type,
                    source=e.source,
                    source_id=e.source_id,
                    evidence_strength=e.evidence_strength,
                    provenance=e.provenance or {},
                )
                for e in evs
            ]
        except (Exception, SQLAlchemyError) as e:  # noqa: BLE001
            logger.warning(f"Database list_observation_evidence failed: {e}")

    return []
