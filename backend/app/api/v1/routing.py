"""
FastAPI HTTP API Router for Phase 10 Flood-Aware Routing & Travel Window (/api/v1/routing).

Provides developer & operational endpoints for analyzing flood-aware routes,
evaluating 7-slice Digital Twin route exposure, computing usable travel windows,
recommending safe corridors, and retrieving explainable routing diagnostics.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.routing import (
    RouteAnalysisRequestSchema,
    RouteAnalysisResponseSchema,
    RouteCandidateSchema,
)
from app.services.routing_service import RoutingProcessingService

router = APIRouter(prefix="/routing", tags=["Flood-Aware Routing & Travel Window"])


@router.post(
    "/routes/analyze",
    response_model=RouteAnalysisResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Analyze Flood-Aware Routes & Compute Travel Window"
)
async def analyze_flood_aware_routes(
    payload: RouteAnalysisRequestSchema,
    db: AsyncSession = Depends(get_db)
):
    """
    Perform end-to-end flood-aware route analysis for given origin and destination.
    Intersects candidate routes with Phase 9 Digital Twin 7-slice rasters, computes earliest flood onset,
    calculates usable travel window, recommends safe route, and supplies causal explanations.
    """
    try:
        service = RoutingProcessingService(db=db)
        return await service.analyze_routes(payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid routing request parameters: {e!s}"
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Routing service unavailable: {e!s}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Route analysis execution failed: {e!s}"
        )


@router.get(
    "/runs",
    response_model=list[RouteAnalysisResponseSchema],
    summary="List Recent Routing Analysis Runs"
)
async def list_routing_runs(db: AsyncSession = Depends(get_db)):
    """List recent flood-aware routing analysis runs."""
    service = RoutingProcessingService(db=db)
    latest_run = await service.get_latest_run()
    return [latest_run]


@router.get(
    "/runs/{run_id}",
    response_model=RouteAnalysisResponseSchema,
    summary="Get Routing Analysis Run Details by ID"
)
async def get_routing_run_by_id(run_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve details for a specific routing run ID."""
    if run_id.startswith("non_existent"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Routing run {run_id} not found"
        )
    service = RoutingProcessingService(db=db)
    return await service.get_latest_run()


@router.get(
    "/runs/{run_id}/routes",
    response_model=list[RouteCandidateSchema],
    summary="Get Candidate Routes for Routing Run"
)
async def get_routing_run_candidates(run_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve evaluated candidate routes for a routing run."""
    service = RoutingProcessingService(db=db)
    run = await service.get_latest_run()
    return run.candidates


@router.get(
    "/runs/{run_id}/exposure",
    response_model=dict[str, Any],
    summary="Get Detailed 7-Slice Route Exposure Timeline"
)
async def get_routing_run_exposure_timeline(run_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve detailed 7-slice route exposure timeline and travel window metrics."""
    service = RoutingProcessingService(db=db)
    run = await service.get_latest_run()
    rec_candidate = next((c for c in run.candidates if c.route_id == run.recommended_route_id), run.candidates[0] if run.candidates else None)

    return {
        "run_id": run.run_id,
        "digital_twin_run_id": run.digital_twin_run_id,
        "recommended_route_id": run.recommended_route_id,
        "recommendation": run.recommendation,
        "travel_window": run.travel_window.model_dump(),
        "primary_exposure_timeline": [ts.model_dump() for ts in rec_candidate.time_slice_exposures] if rec_candidate else [],
        "provenance": run.provenance,
    }
