"""
Developer Infrastructure Verification Endpoints for Phase 4 Terrain & Surface-Flow Engine.

EXPLICIT SCOPE BOUNDARY:
- DEVELOPER / INFRASTRUCTURE VERIFICATION ONLY.
- Synthetic terrain is clearly labeled and MUST NEVER be presented as real operational terrain.
- Flow accumulation is NOT runoff or discharge.
- Surface drainage proxy is NOT municipal sewer network.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.terrain import Catchment, TerrainProcessingRun
from app.schemas.terrain import (
    CatchmentResponse,
    PourPointSchema,
    TerrainAnalysisRequest,
    TerrainAnalysisResponse,
    TerrainProcessingRunResponse,
)
from app.services.terrain_service import TerrainProcessingService

router = APIRouter(prefix="/terrain", tags=["Terrain & Surface-Flow Engine"])
terrain_service = TerrainProcessingService()


@router.post(
    "/analyze",
    response_model=TerrainAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute terrain derivative analysis and flow processing"
)
async def analyze_terrain(
    request: TerrainAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute terrain processing pipeline (slope, aspect, D8 flow direction, D8 accumulation,
    DEM surface drainage proxy, optional pour-point catchment delineation).
    """
    try:
        response = await terrain_service.execute_terrain_analysis(request, db=db)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terrain processing execution failed: {exc!s}"
        )


@router.get(
    "/analysis/latest",
    response_model=TerrainAnalysisResponse,
    summary="Get latest executed terrain analysis summary"
)
async def get_latest_terrain_analysis(
    dataset_id: str = Query("synthetic_inclined_plane", description="Dataset ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Run or return the latest terrain derivative analysis.
    """
    request = TerrainAnalysisRequest(dataset_id=dataset_id, provider_type="synthetic")
    return await analyze_terrain(request, db=db)


@router.get(
    "/catchments",
    response_model=list[CatchmentResponse],
    summary="List delineated terrain catchments"
)
async def list_catchments(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List delineated catchments from database audit store.
    """
    try:
        stmt = select(Catchment).order_by(Catchment.created_at.desc()).limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        responses = []
        for r in records:
            responses.append(
                CatchmentResponse(
                    catchment_id=str(r.id),
                    dataset_id=r.dataset_id,
                    original_pour_point=PourPointSchema(x=r.original_pour_point_x, y=r.original_pour_point_y),
                    snapped_pour_point=PourPointSchema(x=r.snapped_pour_point_x, y=r.snapped_pour_point_y),
                    snapped=r.snapped,
                    snap_distance_m=r.snap_distance_m,
                    contributing_cells_count=r.contributing_cells_count,
                    area_m2=r.area_m2,
                    area_km2=r.area_km2,
                    crs="EPSG:4326",
                    geojson_geometry={"type": "Polygon", "coordinates": []},
                    provenance=r.provenance or {}
                )
            )
        return responses
    except Exception:  # noqa: BLE001
        return []


@router.get(
    "/processing-runs",
    response_model=list[TerrainProcessingRunResponse],
    summary="List terrain processing audit run history"
)
async def list_terrain_processing_runs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List terrain processing runs.
    """
    try:
        stmt = select(TerrainProcessingRun).order_by(TerrainProcessingRun.started_at.desc()).limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()
        
        return [
            TerrainProcessingRunResponse(
                run_id=str(r.id),
                dataset_id=r.dataset_id,
                processing_type=r.processing_type,
                status=r.status,
                analysis_crs=r.analysis_crs,
                surface_drainage_threshold_m2=r.surface_drainage_threshold_m2,
                started_at=r.started_at,
                completed_at=r.completed_at,
                error_message=r.error_message,
                provenance=r.provenance or {}
            )
            for r in records
        ]
    except Exception:  # noqa: BLE001
        return []
