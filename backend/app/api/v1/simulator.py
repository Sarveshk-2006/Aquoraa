"""
FastAPI HTTP API Router for Phase 14 Aquora Simulator (/api/v1/simulator).

Provides endpoints for creating scenarios, parameter validation, executing what-if flood
simulations via Phase 6 engine, retrieving baseline-vs-scenario comparison metrics,
diagnostics, raster map artifacts, and audit provenance chains.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.simulator import (
    SimulatorArtifact,
    SimulatorComparison,
    SimulatorDiagnostic,
    SimulatorRun,
    SimulatorScenario,
)
from app.schemas.simulator import (
    OutcomeClassification,
    ScenarioAssumptionSchema,
    ScenarioStatus,
    ScenarioType,
    SimulatorArtifactResponseSchema,
    SimulatorComparisonResponseSchema,
    SimulatorDiagnosticResponseSchema,
    SimulatorProvenanceResponseSchema,
    SimulatorRunResponseSchema,
    SimulatorRunSummarySchema,
    SimulatorScenarioCreateSchema,
    SimulatorScenarioResponseSchema,
    SimulatorScenarioValidationResponseSchema,
)
from app.services.simulator_service import SimulatorService

router = APIRouter(prefix="/simulator", tags=["Aquora Simulator"])


@router.post(
    "/scenarios",
    response_model=SimulatorScenarioResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create What-If Flood Simulation Scenario"
)
async def create_scenario(
    payload: SimulatorScenarioCreateSchema,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Create a new simulator scenario targeting a completed baseline run."""
    try:
        service = SimulatorService(db=db)
        return await service.create_scenario(payload)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )


@router.get(
    "/scenarios",
    response_model=list[SimulatorScenarioResponseSchema],
    summary="List Simulator Scenarios"
)
async def list_scenarios(
    baseline_run_id: str | None = Query(default=None, description="Filter scenarios by baseline run ID"),
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """List defined simulator scenarios."""
    stmt = select(SimulatorScenario)
    if baseline_run_id:
        stmt = stmt.where(SimulatorScenario.baseline_run_id == baseline_run_id)

    res = await db.execute(stmt)
    scenarios = res.scalars().all()

    return [
        SimulatorScenarioResponseSchema(
            scenario_id=s.scenario_id,
            baseline_run_id=s.baseline_run_id,
            scenario_type=ScenarioType(s.scenario_type),
            parameters=s.parameters,
            assumptions=[
                ScenarioAssumptionSchema(
                    assumption_type=str(a.get("assumption_type", "DEFAULT")) if isinstance(a, dict) else "DEFAULT",
                    assumption_value=a.get("assumption_value", str(a)) if isinstance(a, dict) else str(a),
                    assumption_source=str(a.get("assumption_source", "SYSTEM")) if isinstance(a, dict) else "SYSTEM",
                    assumption_description=str(a.get("assumption_description", "")) if isinstance(a, dict) else str(a),
                )
                for a in (s.assumptions or [])
            ],
            status=ScenarioStatus(s.status),
            provenance=s.provenance,
            created_at=s.created_at.isoformat(),
            updated_at=s.updated_at.isoformat(),
        )
        for s in scenarios
    ]


@router.get(
    "/scenarios/{scenario_id}",
    response_model=SimulatorScenarioResponseSchema,
    summary="Get Simulator Scenario Definition"
)
async def get_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Retrieve detailed scenario definition by ID."""
    try:
        service = SimulatorService(db=db)
        return await service.get_scenario(scenario_id)
    except KeyError as err:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err)
        )


@router.post(
    "/scenarios/{scenario_id}/validate",
    response_model=SimulatorScenarioValidationResponseSchema,
    summary="Validate Scenario Parameters & Physical Compatibility"
)
async def validate_scenario(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Run validation checks on scenario parameters without executing simulation."""
    service = SimulatorService(db=db)
    try:
        scen = await service.get_scenario(scenario_id)
        return service.validate_scenario(
            scenario_id=scen.scenario_id,
            scenario_type=scen.scenario_type,
            parameters=scen.parameters,
            assumptions=[a.model_dump() for a in scen.assumptions],
        )
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found"
        )


@router.post(
    "/scenarios/{scenario_id}/run",
    response_model=SimulatorRunSummarySchema,
    status_code=status.HTTP_200_OK,
    summary="Execute Scenario Flood Simulation via Phase 6 Engine"
)
async def run_scenario_simulation(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """
    Execute scenario flood simulation through Phase 6 engine.
    Computes baseline vs scenario deltas, stores map artifacts, and logs diagnostics.
    """
    service = SimulatorService(db=db)
    try:
        return await service.run_simulation(scenario_id)
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err)
        )
    except Exception as err:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scenario execution failed: {err!s}"
        )


@router.get(
    "/runs",
    response_model=list[SimulatorRunResponseSchema],
    summary="List Scenario Execution Runs"
)
async def list_runs(
    scenario_id: str | None = Query(default=None, description="Filter runs by scenario ID"),
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """List execution runs for simulator scenarios."""
    stmt = select(SimulatorRun)
    if scenario_id:
        stmt = stmt.where(SimulatorRun.scenario_id == scenario_id)

    res = await db.execute(stmt)
    runs = res.scalars().all()

    return [
        SimulatorRunResponseSchema(
            run_id=r.run_id,
            scenario_id=r.scenario_id,
            baseline_run_id=r.baseline_run_id,
            status=ScenarioStatus(r.status),
            started_at=r.started_at.isoformat(),
            completed_at=r.completed_at.isoformat() if r.completed_at else None,
            engine_version=r.engine_version,
            config_version=r.config_version,
            warnings=r.warnings,
            provenance=r.provenance,
        )
        for r in runs
    ]


@router.get(
    "/runs/{run_id}",
    response_model=SimulatorRunResponseSchema,
    summary="Get Simulator Execution Run Details"
)
async def get_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Get status and detail for a specific simulation execution run."""
    stmt = select(SimulatorRun).where(SimulatorRun.run_id == run_id)
    res = await db.execute(stmt)
    run = res.scalar_one_or_none()

    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulation run '{run_id}' not found"
        )

    return SimulatorRunResponseSchema(
        run_id=run.run_id,
        scenario_id=run.scenario_id,
        baseline_run_id=run.baseline_run_id,
        status=ScenarioStatus(run.status),
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        engine_version=run.engine_version,
        config_version=run.config_version,
        warnings=run.warnings,
        provenance=run.provenance,
    )


@router.get(
    "/runs/{run_id}/summary",
    response_model=SimulatorRunSummarySchema,
    summary="Get Comprehensive Simulator Run Summary"
)
async def get_run_summary(
    run_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Retrieve full summary of run, scenario, comparisons, diagnostics, and artifacts."""
    stmt_run = select(SimulatorRun).where(SimulatorRun.run_id == run_id)
    res_run = await db.execute(stmt_run)
    run = res_run.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found")

    stmt_scen = select(SimulatorScenario).where(SimulatorScenario.scenario_id == run.scenario_id)
    res_scen = await db.execute(stmt_scen)
    scen = res_scen.scalar_one_or_none()
    if not scen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Scenario for run '{run_id}' not found")

    stmt_comp = select(SimulatorComparison).where(SimulatorComparison.run_id == run_id)
    res_comp = await db.execute(stmt_comp)
    comps = res_comp.scalars().all()

    stmt_diag = select(SimulatorDiagnostic).where(SimulatorDiagnostic.run_id == run_id)
    res_diag = await db.execute(stmt_diag)
    diags = res_diag.scalars().all()

    stmt_art = select(SimulatorArtifact).where(SimulatorArtifact.run_id == run_id)
    res_art = await db.execute(stmt_art)
    arts = res_art.scalars().all()

    run_schema = SimulatorRunResponseSchema(
        run_id=run.run_id,
        scenario_id=run.scenario_id,
        baseline_run_id=run.baseline_run_id,
        status=ScenarioStatus(run.status),
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
        engine_version=run.engine_version,
        config_version=run.config_version,
        warnings=run.warnings,
        provenance=run.provenance,
    )

    scen_schema = SimulatorScenarioResponseSchema(
        scenario_id=scen.scenario_id,
        baseline_run_id=scen.baseline_run_id,
        scenario_type=ScenarioType(scen.scenario_type),
        parameters=scen.parameters,
        assumptions=[
            ScenarioAssumptionSchema(
                assumption_type=str(a.get("assumption_type", "DEFAULT")) if isinstance(a, dict) else "DEFAULT",
                assumption_value=a.get("assumption_value", str(a)) if isinstance(a, dict) else str(a),
                assumption_source=str(a.get("assumption_source", "SYSTEM")) if isinstance(a, dict) else "SYSTEM",
                assumption_description=str(a.get("assumption_description", "")) if isinstance(a, dict) else str(a),
            )
            for a in (scen.assumptions or [])
        ],
        status=ScenarioStatus(scen.status),
        provenance=scen.provenance,
        created_at=scen.created_at.isoformat(),
        updated_at=scen.updated_at.isoformat(),
    )

    comp_schemas = [
        SimulatorComparisonResponseSchema(
            comparison_id=c.comparison_id,
            run_id=c.run_id,
            slice_minutes=c.slice_minutes,
            baseline_metrics=c.baseline_metrics,
            scenario_metrics=c.scenario_metrics,
            deltas=c.deltas,
            outcome=OutcomeClassification(c.outcome),
            created_at=c.created_at.isoformat(),
        )
        for c in comps
    ]

    diag_schemas = [
        SimulatorDiagnosticResponseSchema(
            diagnostic_id=d.diagnostic_id,
            run_id=d.run_id,
            metric=d.metric,
            value=d.value,
            status=d.status,
            message=d.message,
        )
        for d in diags
    ]

    art_schemas = [
        SimulatorArtifactResponseSchema(
            artifact_id=a.artifact_id,
            run_id=a.run_id,
            artifact_type=a.artifact_type,
            storage_reference=a.storage_reference,
            checksum=a.checksum,
            crs=a.crs,
            transform=a.transform,
            width=a.width,
            height=a.height,
            nodata=a.nodata,
            provenance=a.provenance,
        )
        for a in arts
    ]

    return SimulatorRunSummarySchema(
        run=run_schema,
        scenario=scen_schema,
        comparisons=comp_schemas,
        diagnostics=diag_schemas,
        artifacts=art_schemas,
    )


@router.get(
    "/runs/{run_id}/comparison",
    response_model=list[SimulatorComparisonResponseSchema],
    summary="Get Baseline vs Scenario Metric Comparisons"
)
async def get_run_comparisons(
    run_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Retrieve baseline vs scenario metric comparison records across canonical timesteps."""
    stmt = select(SimulatorComparison).where(SimulatorComparison.run_id == run_id)
    res = await db.execute(stmt)
    comps = res.scalars().all()

    return [
        SimulatorComparisonResponseSchema(
            comparison_id=c.comparison_id,
            run_id=c.run_id,
            slice_minutes=c.slice_minutes,
            baseline_metrics=c.baseline_metrics,
            scenario_metrics=c.scenario_metrics,
            deltas=c.deltas,
            outcome=OutcomeClassification(c.outcome),
            created_at=c.created_at.isoformat(),
        )
        for c in comps
    ]


@router.get(
    "/runs/{run_id}/map/{minutes}",
    response_model=SimulatorArtifactResponseSchema,
    summary="Get Map Raster Artifact for Time Slice"
)
async def get_run_map_artifact(
    run_id: str,
    minutes: int,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Retrieve file-backed map artifact metadata reference for canonical minute slice."""
    stmt = select(SimulatorArtifact).where(
        SimulatorArtifact.run_id == run_id,
    )
    res = await db.execute(stmt)
    artifacts = res.scalars().all()

    matching = [a for a in artifacts if a.provenance.get("minutes") == minutes]
    if not matching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Map artifact for run '{run_id}' at +{minutes}m not found"
        )

    a = matching[0]
    return SimulatorArtifactResponseSchema(
        artifact_id=a.artifact_id,
        run_id=a.run_id,
        artifact_type=a.artifact_type,
        storage_reference=a.storage_reference,
        checksum=a.checksum,
        crs=a.crs,
        transform=a.transform,
        width=a.width,
        height=a.height,
        nodata=a.nodata,
        provenance=a.provenance,
    )


@router.get(
    "/runs/{run_id}/diagnostics",
    response_model=list[SimulatorDiagnosticResponseSchema],
    summary="Get Hydro-Solver Execution Diagnostics"
)
async def get_run_diagnostics(
    run_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Retrieve hydro-solver diagnostics for a simulation run."""
    stmt = select(SimulatorDiagnostic).where(SimulatorDiagnostic.run_id == run_id)
    res = await db.execute(stmt)
    diags = res.scalars().all()

    return [
        SimulatorDiagnosticResponseSchema(
            diagnostic_id=d.diagnostic_id,
            run_id=d.run_id,
            metric=d.metric,
            value=d.value,
            status=d.status,
            message=d.message,
        )
        for d in diags
    ]


@router.get(
    "/scenarios/{scenario_id}/provenance",
    response_model=SimulatorProvenanceResponseSchema,
    summary="Get Scenario Audit Provenance Chain"
)
async def get_scenario_provenance(
    scenario_id: str,
    db: AsyncSession = Depends(get_db)  # noqa: B008
):
    """Retrieve complete audit provenance tracking record for scenario."""
    service = SimulatorService(db=db)
    try:
        return await service.get_provenance(scenario_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario '{scenario_id}' not found"
        )
