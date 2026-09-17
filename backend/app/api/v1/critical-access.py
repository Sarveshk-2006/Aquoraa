"""
FastAPI HTTP API Router for Phase 11 Critical Access Guardian (/api/v1/critical-access).

Provides endpoints to analyze critical facility access, retrieve facility metadata, list accessibility runs,
and inspect 7-slice accessibility timelines and candidate routes.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.critical_access import CriticalAccessResult, CriticalAccessRun
from app.schemas.critical_access import (
    CriticalAccessRequestSchema,
    CriticalAccessResponseSchema,
    CriticalFacilitySchema,
)
from app.services.critical_access_service import CriticalAccessProcessingService

router = APIRouter(prefix="/critical-access", tags=["Critical Access Guardian"])


@router.post(
    "/analyze",
    response_model=CriticalAccessResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Analyze Critical Facility Access & Compute Loss-of-Access Timeline",
)
async def analyze_critical_access(
    payload: CriticalAccessRequestSchema,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluates accessibility of a critical facility for responder origin across 7 canonical Digital Twin slices.
    Determines modeled loss-of-access, evaluates alternate routes, and provides explainable access recommendations.
    """
    try:
        service = CriticalAccessProcessingService(db=db)
        return await service.analyze_critical_access(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid critical access request parameters: {e!s}",
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Critical access service processing failed: {e!s}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Critical access analysis failed: {e!s}",
        )


@router.get(
    "/facilities",
    response_model=list[CriticalFacilitySchema],
    status_code=status.HTTP_200_OK,
    summary="List Critical Facilities",
)
async def list_facilities(
    category: str | None = Query(default=None, description="Optional facility category filter (e.g. HOSPITAL, FIRE_STATION)"),
    verification_status: str | None = Query(default=None, description="Optional verification status filter (e.g. VERIFIED, UNVERIFIED, SYNTHETIC_FIXTURE)"),
    bbox: str | None = Query(default=None, description="Optional bounding box CSV: min_lon,min_lat,max_lon,max_lat"),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves critical facilities with optional category, verification status, and bounding box filters.
    """
    bbox_coords: list[float] | None = None
    if bbox:
        try:
            parts = [float(p.strip()) for p in bbox.split(",")]
            if len(parts) == 4:
                bbox_coords = parts
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bounding box format. Expected 'min_lon,min_lat,max_lon,max_lat'.",
            )

    service = CriticalAccessProcessingService(db=db)
    return await service.list_facilities(
        category=category,
        verification_status=verification_status,
        bbox=bbox_coords,
    )


@router.get(
    "/facilities/{facility_id}",
    response_model=CriticalFacilitySchema,
    status_code=status.HTTP_200_OK,
    summary="Get Critical Facility Metadata",
)
async def get_facility_by_id(
    facility_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves metadata and verification status for a specific critical facility."""
    service = CriticalAccessProcessingService(db=db)
    facility = await service.get_facility_by_id(facility_id)
    if not facility:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Critical facility '{facility_id}' not found.",
        )
    return facility


@router.get(
    "/runs",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="List Recent Critical Access Runs",
)
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves recent Critical Access run audit entries."""
    if not db:
        return []
    try:
        stmt = select(CriticalAccessRun).order_by(CriticalAccessRun.created_at.desc()).limit(limit)
        res = await db.execute(stmt)
        runs = res.scalars().all()
        return [
            {
                "run_identifier": r.run_identifier,
                "facility_id": r.facility_id,
                "digital_twin_run_id": r.digital_twin_run_id,
                "routing_run_id": r.routing_run_id,
                "current_access_status": r.current_access_status,
                "modeled_loss_of_access_min": r.modeled_loss_of_access_min,
                "time_to_loss_of_access_min": r.time_to_loss_of_access_min,
                "recommendation": r.recommendation,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in runs
        ]
    except Exception:
        return []


@router.get(
    "/runs/{run_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Critical Access Run Audit Details",
)
async def get_run_details(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves detailed audit record for a given access run."""
    if not db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Database unavailable.")

    stmt = select(CriticalAccessRun).where(CriticalAccessRun.run_identifier == run_id)
    res = await db.execute(stmt)
    run_db = res.scalar_one_or_none()
    if not run_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found.")

    res_stmt = select(CriticalAccessResult).where(CriticalAccessResult.access_run_id == run_id)
    res_exec = await db.execute(res_stmt)
    result_db = res_exec.scalar_one_or_none()

    return {
        "run_identifier": run_db.run_identifier,
        "facility_id": run_db.facility_id,
        "digital_twin_run_id": run_db.digital_twin_run_id,
        "routing_run_id": run_db.routing_run_id,
        "origin": {"latitude": run_db.origin_lat, "longitude": run_db.origin_lon},
        "critical_access_severity": run_db.critical_access_severity,
        "current_access_status": run_db.current_access_status,
        "modeled_loss_of_access_min": run_db.modeled_loss_of_access_min,
        "time_to_loss_of_access_min": run_db.time_to_loss_of_access_min,
        "recommendation": run_db.recommendation,
        "explanation": run_db.explanation,
        "status": run_db.status,
        "provenance": run_db.provenance,
        "timeline": result_db.accessibility_timeline_json if result_db else [],
        "warnings": result_db.warnings_json if result_db else [],
        "created_at": run_db.created_at.isoformat() if run_db.created_at else None,
    }


@router.get(
    "/runs/{run_id}/timeline",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get Accessibility Timeline for Run",
)
async def get_run_timeline(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves 7-slice accessibility timeline for an access run."""
    run_info = await get_run_details(run_id, db=db)
    return run_info.get("timeline", [])


@router.get(
    "/runs/{run_id}/routes",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get Route References for Access Run",
)
async def get_run_routes(
    run_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieves selected primary and alternate route references for an access run."""
    run_info = await get_run_details(run_id, db=db)
    return {
        "access_run_id": run_id,
        "routing_run_id": run_info.get("routing_run_id"),
        "facility_id": run_info.get("facility_id"),
        "recommendation": run_info.get("recommendation"),
    }
