"""
Developer Infrastructure Verification Endpoints for Phase 5 Drainage Network Engine.

EXPLICIT SCOPE BOUNDARY:
- DEVELOPER / INFRASTRUCTURE VERIFICATION ONLY.
- Synthetic drainage networks are clearly labeled and MUST NEVER be presented as real municipal infrastructure.
- Network topology is NOT flood simulation.
- Missing capacity is UNKNOWN, NOT zero.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.geospatial.drainage import (
    build_drainage_graph,
    can_reach_outfall,
    get_downstream_nodes,
    get_upstream_nodes,
)
from app.models.drainage import (
    DrainageLink,
    DrainageNode,
    DrainageProcessingRun,
)
from app.providers.drainage import SyntheticDrainageProvider
from app.schemas.drainage import (
    DrainageLinkSchema,
    DrainageNetworkRequest,
    DrainageNetworkResponse,
    DrainageNodeSchema,
    DrainageProcessingRunResponse,
)
from app.services.drainage_service import DrainageProcessingService

router = APIRouter(prefix="/drainage", tags=["Drainage Network Engine"])
drainage_service = DrainageProcessingService()
synthetic_provider = SyntheticDrainageProvider()


@router.post(
    "/analyze",
    response_model=DrainageNetworkResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute drainage network normalization and topology analysis"
)
async def analyze_drainage_network(
    request: DrainageNetworkRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute drainage network analysis (topology validation, spatial snapping, graph analytics, catchment association).
    """
    try:
        response = await drainage_service.execute_drainage_analysis(request, db=db)
        return response
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drainage network processing failed: {exc!s}"
        )


@router.get(
    "/networks/latest",
    response_model=DrainageNetworkResponse,
    summary="Get latest compiled drainage network"
)
async def get_latest_drainage_network(
    fixture_type: str = Query("simple_chain", description="Fixture type"),
    db: AsyncSession = Depends(get_db)
):
    """
    Run or return the latest compiled drainage network response.
    """
    request = DrainageNetworkRequest(dataset_id=f"synthetic_{fixture_type}", provider_type="synthetic", fixture_type=fixture_type)
    return await analyze_drainage_network(request, db=db)


@router.get(
    "/nodes",
    response_model=list[DrainageNodeSchema],
    summary="List drainage nodes"
)
async def list_drainage_nodes(
    fixture_type: str = Query("simple_chain", description="Fixture type"),
    db: AsyncSession = Depends(get_db)
):
    """
    List drainage nodes for a network.
    """
    try:
        stmt = select(DrainageNode).order_by(DrainageNode.node_id).limit(100)
        result = await db.execute(stmt)
        records = result.scalars().all()
        if records:
            return [
                DrainageNodeSchema(
                    node_id=r.node_id,
                    node_type=r.node_type,
                    x=0.0,
                    y=0.0,
                    elevation_m=r.elevation_m,
                    invert_elevation_m=r.invert_elevation_m,
                    ground_elevation_m=r.ground_elevation_m,
                    confidence=r.confidence,
                    geojson_geometry={"type": "Point", "coordinates": [0.0, 0.0]},
                    provenance=r.provenance or {}
                )
                for r in records
            ]
    except Exception:  # noqa: BLE001
        pass

    raw_nodes, _, _ = synthetic_provider.generate_synthetic_network(fixture_type=fixture_type)
    return [
        DrainageNodeSchema(
            node_id=n["node_id"],
            node_type=n["node_type"],
            x=n["x"],
            y=n["y"],
            elevation_m=n.get("elevation_m"),
            invert_elevation_m=n.get("invert_elevation_m"),
            ground_elevation_m=n.get("ground_elevation_m"),
            confidence="SYNTHETIC",
            geojson_geometry={"type": "Point", "coordinates": [n["x"], n["y"]]},
            provenance={"is_test_fixture": True}
        )
        for n in raw_nodes
    ]


@router.get(
    "/links",
    response_model=list[DrainageLinkSchema],
    summary="List drainage links"
)
async def list_drainage_links(
    fixture_type: str = Query("simple_chain", description="Fixture type"),
    db: AsyncSession = Depends(get_db)
):
    """
    List drainage links for a network.
    """
    try:
        stmt = select(DrainageLink).order_by(DrainageLink.link_id).limit(100)
        result = await db.execute(stmt)
        records = result.scalars().all()
        if records:
            return [
                DrainageLinkSchema(
                    link_id=r.link_id,
                    from_node_id=r.from_node_id,
                    to_node_id=r.to_node_id,
                    link_type=r.link_type,
                    length_m=r.length_m,
                    diameter_m=r.diameter_m,
                    capacity_m3s=r.capacity_m3s,
                    direction_status=r.direction_status,
                    confidence=r.confidence,
                    geojson_geometry={"type": "LineString", "coordinates": []},
                    provenance=r.provenance or {}
                )
                for r in records
            ]
    except Exception:  # noqa: BLE001
        pass

    _, raw_links, _ = synthetic_provider.generate_synthetic_network(fixture_type=fixture_type)
    return [
        DrainageLinkSchema(
            link_id=l["link_id"],
            from_node_id=l["from_node_id"],
            to_node_id=l["to_node_id"],
            link_type=l["link_type"],
            length_m=l["length_m"],
            diameter_m=l.get("diameter_m"),
            capacity_m3s=l.get("capacity_m3s"),
            direction_status=l.get("direction_status", "KNOWN"),
            confidence="SYNTHETIC",
            geojson_geometry={"type": "LineString", "coordinates": l.get("coords", [])},
            provenance={"is_test_fixture": True}
        )
        for l in raw_links
    ]


@router.get(
    "/nodes/{node_id}/upstream",
    response_model=list[str],
    summary="Get upstream contributing node IDs for a node"
)
async def get_node_upstream(
    node_id: str,
    fixture_type: str = Query("simple_chain", description="Fixture type")
):
    """
    Traverse graph upstream from node_id.
    """
    nodes, links, _ = synthetic_provider.generate_synthetic_network(fixture_type=fixture_type)
    graph = build_drainage_graph(nodes, links)
    return get_upstream_nodes(graph, node_id)


@router.get(
    "/nodes/{node_id}/downstream",
    response_model=list[str],
    summary="Get downstream reachable node IDs for a node"
)
async def get_node_downstream(
    node_id: str,
    fixture_type: str = Query("simple_chain", description="Fixture type")
):
    """
    Traverse graph downstream from node_id.
    """
    nodes, links, _ = synthetic_provider.generate_synthetic_network(fixture_type=fixture_type)
    graph = build_drainage_graph(nodes, links)
    return get_downstream_nodes(graph, node_id)


@router.get(
    "/nodes/{node_id}/outfalls",
    response_model=dict[str, Any],
    summary="Check outfall reachability for a node"
)
async def check_node_outfall_reachability(
    node_id: str,
    fixture_type: str = Query("simple_chain", description="Fixture type")
):
    """
    Check if node_id can reach an explicit outfall node.
    """
    nodes, links, _ = synthetic_provider.generate_synthetic_network(fixture_type=fixture_type)
    graph = build_drainage_graph(nodes, links)
    can_reach = can_reach_outfall(graph, node_id)
    return {
        "node_id": node_id,
        "can_reach_outfall": can_reach,
        "outfalls": list(graph["outfalls"])
    }


@router.get(
    "/processing-runs",
    response_model=list[DrainageProcessingRunResponse],
    summary="List drainage processing audit run history"
)
async def list_drainage_processing_runs(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    List drainage processing runs.
    """
    try:
        stmt = select(DrainageProcessingRun).order_by(DrainageProcessingRun.started_at.desc()).limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()

        return [
            DrainageProcessingRunResponse(
                run_id=str(r.id),
                dataset_id=r.dataset_id,
                network_id=str(r.network_id) if r.network_id else None,
                processing_type=r.processing_type,
                status=r.status,
                analysis_crs=r.analysis_crs,
                snap_tolerance_m=r.snap_tolerance_m,
                started_at=r.started_at,
                completed_at=r.completed_at,
                error_message=r.error_message,
                provenance=r.provenance or {}
            )
            for r in records
        ]
    except Exception:  # noqa: BLE001
        return []
