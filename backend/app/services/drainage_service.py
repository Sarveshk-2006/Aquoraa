"""
Drainage Network Processing Service.

Coordinates drainage dataset loading, geometry validation, controlled spatial snapping,
topology validation, directed graph construction, connected component analysis, Phase 4 catchment association,
artifact persistence, and audit log processing runs.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.geospatial.drainage import (
    associate_catchment_with_node,
    build_drainage_graph,
    find_connected_components,
    snap_node_to_link_endpoints,
    validate_link_geometry,
    validate_network_topology,
    validate_node_geometry,
)
from app.models.drainage import (
    DrainageNetwork,
    DrainageProcessingRun,
)
from app.providers.drainage import LocalDrainageProvider, SyntheticDrainageProvider
from app.schemas.drainage import (
    DrainageCatchmentAssociationSchema,
    DrainageNetworkRequest,
    DrainageNetworkResponse,
    DrainageValidationSummary,
)

logger = structlog.get_logger("aquora.services.drainage")


class DrainageProcessingService:
    """
    Application Service orchestrating Phase 5 Drainage Network Engine processing.
    """

    def __init__(
        self,
        synthetic_provider: SyntheticDrainageProvider | None = None,
        local_provider: LocalDrainageProvider | None = None
    ):
        self.synthetic_provider = synthetic_provider or SyntheticDrainageProvider()
        self.local_provider = local_provider or LocalDrainageProvider()

    async def execute_drainage_analysis(
        self,
        request: DrainageNetworkRequest,
        catchment_geom: dict[str, Any] | None = None,
        db: AsyncSession | None = None
    ) -> DrainageNetworkResponse:
        """
        Execute deterministic end-to-end drainage network normalization and topology analysis.
        """
        run_id = str(uuid.uuid4())
        network_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)

        logger.info(
            "Starting drainage network processing run",
            run_id=run_id,
            dataset_id=request.dataset_id,
            provider_type=request.provider_type
        )

        try:
            # 1. Fetch raw nodes, links, and metadata from provider
            if request.provider_type == "synthetic":
                raw_nodes, raw_links, _raw_meta = self.synthetic_provider.generate_synthetic_network(
                    fixture_type=request.fixture_type,
                    crs=request.analysis_crs
                )
            elif request.provider_type == "local":
                # Local vector reader stub / fallback
                raw_nodes, raw_links, _raw_meta = [], [], {"crs": request.analysis_crs}
            else:
                raise ValueError(f"Unsupported provider type '{request.provider_type}'")

            # 2. Validate Geometries & Perform Controlled Spatial Snapping
            norm_nodes = []
            for n in raw_nodes:
                val_n = validate_node_geometry({"type": "Point", "coordinates": [n["x"], n["y"]]}, crs_str=request.analysis_crs)
                orig_xy = (val_n["x"], val_n["y"])
                snapped_xy = orig_xy
                snapped_bool = False
                snap_dist = 0.0

                # Snap to matching link endpoints if any exist within tolerance
                for l in raw_links:
                    l_coords = l.get("coords", [])
                    if len(l_coords) >= 2:
                        cur_snap_xy, cur_snap_bool, cur_dist = snap_node_to_link_endpoints(
                            orig_xy,
                            l_coords,
                            snap_tolerance_m=request.snap_tolerance_m,
                            analysis_crs_str=request.analysis_crs
                        )
                        if cur_snap_bool and cur_dist < snap_dist or (cur_snap_bool and not snapped_bool):
                            snapped_xy = cur_snap_xy
                            snapped_bool = True
                            snap_dist = cur_dist

                n_copy = dict(n)
                n_copy["x"], n_copy["y"] = snapped_xy
                n_copy["snapped"] = snapped_bool
                n_copy["snap_distance_m"] = snap_dist
                norm_nodes.append(n_copy)

            norm_links = []
            for l in raw_links:
                coords = l.get("coords", [])
                val_l = validate_link_geometry({"type": "LineString", "coordinates": coords}, crs_str=request.analysis_crs)
                l_copy = dict(l)
                l_copy["coords_count"] = val_l["coords_count"]
                norm_links.append(l_copy)

            # 3. Topology Validation
            val_summary_dict = validate_network_topology(norm_nodes, norm_links)
            val_summary_schema = DrainageValidationSummary(**val_summary_dict)

            # 4. Build Directed Drainage Graph
            graph = build_drainage_graph(norm_nodes, norm_links)

            # 5. Graph Analytics (Connected Components & Outfalls)
            components = find_connected_components(graph)
            outfalls_count = len(graph["outfalls"])

            # 6. Optional Catchment Association
            catchment_assoc_schema = None
            if request.associate_phase4_catchment and catchment_geom is not None:
                assoc_dict = associate_catchment_with_node(
                    catchment_geom,
                    norm_nodes,
                    max_tolerance_m=request.snap_tolerance_m,
                    analysis_crs_str=request.analysis_crs
                )
                catchment_assoc_schema = DrainageCatchmentAssociationSchema(**assoc_dict)

            completed_at = datetime.now(timezone.utc)

            # 7. Database Persistence (Safe Fallback)
            if db is not None:
                try:
                    net_db = DrainageNetwork(
                        id=uuid.UUID(network_id),
                        dataset_id=request.dataset_id,
                        analysis_crs=request.analysis_crs,
                        nodes_count=len(norm_nodes),
                        links_count=len(norm_links),
                        connected_components_count=len(components),
                        outfalls_count=outfalls_count,
                        validation_summary=val_summary_dict,
                        provenance={"run_id": run_id, "fixture_type": request.fixture_type}
                    )
                    db.add(net_db)

                    run_db = DrainageProcessingRun(
                        id=uuid.UUID(run_id),
                        dataset_id=request.dataset_id,
                        network_id=uuid.UUID(network_id),
                        processing_type="DRAINAGE_NETWORK_NORMALIZATION",
                        status="COMPLETED",
                        analysis_crs=request.analysis_crs,
                        snap_tolerance_m=request.snap_tolerance_m,
                        started_at=started_at,
                        completed_at=completed_at,
                        provenance={"provider_type": request.provider_type}
                    )
                    db.add(run_db)
                    await db.commit()
                except Exception as db_err:  # noqa: BLE001
                    logger.warning("Database commit skipped (no live DB connection available)", error=str(db_err))

            return DrainageNetworkResponse(
                run_id=run_id,
                network_id=network_id,
                dataset_id=request.dataset_id,
                status="COMPLETED",
                analysis_crs=request.analysis_crs,
                nodes_count=len(norm_nodes),
                links_count=len(norm_links),
                connected_components_count=len(components),
                outfalls_count=outfalls_count,
                validation_summary=val_summary_schema,
                catchment_association=catchment_assoc_schema,
                provenance={
                    "started_at": started_at.isoformat(),
                    "completed_at": completed_at.isoformat(),
                    "algorithm_version": "0.5.0-phase5",
                    "scientific_principles": [
                        "Drainage network topology is NOT flood simulation",
                        "Missing pipe capacity is UNKNOWN, NOT zero",
                        "DEM surface proxy is NOT municipal pipe infrastructure"
                    ]
                }
            )

        except Exception as exc:
            logger.error("Drainage processing run failed", run_id=run_id, error=str(exc))
            if db is not None:
                try:
                    failed_run = DrainageProcessingRun(
                        id=uuid.UUID(run_id),
                        dataset_id=request.dataset_id,
                        processing_type="DRAINAGE_NETWORK_NORMALIZATION",
                        status="FAILED",
                        analysis_crs=request.analysis_crs,
                        snap_tolerance_m=request.snap_tolerance_m,
                        started_at=started_at,
                        completed_at=datetime.now(timezone.utc),
                        error_message=str(exc),
                        provenance={"error": str(exc)}
                    )
                    db.add(failed_run)
                    await db.commit()
                except Exception as db_err:  # noqa: BLE001
                    logger.warning("Database commit for failed run skipped", error=str(db_err))
            raise
