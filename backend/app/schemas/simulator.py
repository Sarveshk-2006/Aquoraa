"""
Pydantic v2 Schemas for Phase 14 Aquora Simulator API.

Defines scenario creation, validation payloads, execution runs,
baseline-vs-scenario metric comparisons, map artifacts, diagnostics,
and provenance contracts.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ScenarioType(str, Enum):
    RAINFALL_MULTIPLIER = "RAINFALL_MULTIPLIER"
    RAINFALL_ADDITION = "RAINFALL_ADDITION"
    DRAINAGE_CAPACITY_REDUCTION = "DRAINAGE_CAPACITY_REDUCTION"
    DRAINAGE_CAPACITY_INCREASE = "DRAINAGE_CAPACITY_INCREASE"
    DRAINAGE_NODE_INTERVENTION = "DRAINAGE_NODE_INTERVENTION"
    TEMPORARY_BARRIER = "TEMPORARY_BARRIER"
    STORAGE_INTERVENTION = "STORAGE_INTERVENTION"
    PUMP_OR_DEWATERING_SCENARIO = "PUMP_OR_DEWATERING_SCENARIO"
    COMBINED_SCENARIO = "COMBINED_SCENARIO"


class ScenarioStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    UNSUPPORTED = "UNSUPPORTED"
    SCENARIO_INCOMPLETE = "SCENARIO_INCOMPLETE"


class OutcomeClassification(str, Enum):
    IMPROVED = "IMPROVED"
    NO_SIGNIFICANT_CHANGE = "NO_SIGNIFICANT_CHANGE"
    WORSE = "WORSE"
    INCONCLUSIVE = "INCONCLUSIVE"


class ScenarioAssumptionSchema(BaseModel):
    """Explicit recorded assumption for a simulation scenario."""

    assumption_type: str = Field(description="Type of assumption (e.g., RAINFALL_TEMPORAL_PROFILE, UNKNOWN_CAPACITY_POLICY)")
    assumption_value: str | float | int | dict[str, Any] = Field(description="Assumption value or policy selection")
    assumption_source: str = Field(description="Source or rationale for assumption")
    assumption_description: str = Field(description="Human-readable explanation of assumption")


class SimulatorScenarioCreateSchema(BaseModel):
    """Payload to define a new simulator scenario."""

    baseline_run_id: str = Field(description="Identifier of completed baseline Digital Twin / flood run")
    scenario_type: ScenarioType = Field(default=ScenarioType.RAINFALL_MULTIPLIER, description="Type of scenario overlay")
    
    parameters: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured scenario parameters (e.g. rainfall_multiplier, rainfall_addition_mm, capacity_multiplier, intervention_candidate_ids)"
    )
    assumptions: list[ScenarioAssumptionSchema] = Field(
        default_factory=list,
        description="User-supplied or auto-generated assumption records"
    )
    unknown_capacity_policy: str | None = Field(
        default=None,
        description="Explicit policy for handling UNKNOWN drainage capacity (PRESERVE_UNKNOWN, REJECT, ASSUME_DEFAULT)"
    )


class SimulatorScenarioValidationResponseSchema(BaseModel):
    """Result of scenario validation check."""

    scenario_id: str = Field(description="Scenario identifier")
    is_valid: bool = Field(description="True if scenario can be executed safely by Phase 6")
    status: ScenarioStatus = Field(description="Evaluated scenario status")
    rejection_reason: str | None = Field(default=None, description="Reason if scenario is invalid or unsupported")
    warnings: list[str] = Field(default_factory=list, description="Non-fatal validation warnings")
    assumptions: list[ScenarioAssumptionSchema] = Field(default_factory=list, description="Assumptions recorded during validation")


class SimulatorScenarioResponseSchema(BaseModel):
    """Full detail of a defined scenario."""

    scenario_id: str = Field(description="Unique scenario identifier")
    baseline_run_id: str = Field(description="Baseline Digital Twin / flood run identifier")
    scenario_type: ScenarioType = Field(description="Scenario taxonomy type")
    parameters: dict[str, Any] = Field(description="Scenario parameter payload")
    assumptions: list[ScenarioAssumptionSchema] = Field(description="Recorded assumptions")
    status: ScenarioStatus = Field(description="Current scenario state")
    provenance: dict[str, Any] = Field(description="Scenario provenance metadata")
    created_at: str = Field(description="ISO8601 creation timestamp")
    updated_at: str = Field(description="ISO8601 last modification timestamp")


class SimulatorArtifactResponseSchema(BaseModel):
    """Metadata representation of a simulator map raster artifact."""

    artifact_id: str = Field(description="Unique artifact identifier")
    run_id: str = Field(description="Simulator execution run identifier")
    artifact_type: str = Field(description="Artifact type (e.g. RASTER_SLICE, DIFFERENCE_MAP)")
    storage_reference: str = Field(description="File-backed relative path")
    checksum: str = Field(description="SHA256 checksum of artifact file")
    crs: str = Field(description="Coordinate reference system EPSG string")
    transform: list[float] = Field(description="Affine transform coefficients [a, b, c, d, e, f]")
    width: int = Field(description="Raster grid width in pixels")
    height: int = Field(description="Raster grid height in pixels")
    nodata: float | None = Field(default=None, description="Raster nodata sentinel value")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Artifact creation metadata")


class SimulatorComparisonResponseSchema(BaseModel):
    """Baseline vs Scenario metric comparison for a given timeline slice."""

    comparison_id: str = Field(description="Unique comparison record identifier")
    run_id: str = Field(description="Simulator execution run identifier")
    slice_minutes: int = Field(description="Horizon minutes from simulation start (0, 30, 60, 90, 120, 150, 180)")
    
    baseline_metrics: dict[str, Any] = Field(description="Baseline inundation metrics")
    scenario_metrics: dict[str, Any] = Field(description="Scenario inundation metrics")
    deltas: dict[str, Any] = Field(description="Absolute and percentage metric deltas")
    
    outcome: OutcomeClassification = Field(description="Outcome classification (IMPROVED, NO_SIGNIFICANT_CHANGE, WORSE, INCONCLUSIVE)")
    created_at: str = Field(description="ISO8601 comparison creation timestamp")


class SimulatorDiagnosticResponseSchema(BaseModel):
    """Hydro-solver execution diagnostic metric."""

    diagnostic_id: str = Field(description="Diagnostic record identifier")
    run_id: str = Field(description="Simulator execution run identifier")
    metric: str = Field(description="Diagnostic metric name (e.g. MASS_BALANCE_ERROR_M3, MAX_COURANT_NUMBER)")
    value: float = Field(description="Numerical value of metric")
    status: str = Field(description="Diagnostic status (VALID, WARNING, FAILED)")
    message: str = Field(description="Diagnostic description or error detail")


class SimulatorRunResponseSchema(BaseModel):
    """Execution status and summary for a scenario run."""

    run_id: str = Field(description="Unique scenario execution run identifier")
    scenario_id: str = Field(description="Scenario identifier")
    baseline_run_id: str = Field(description="Baseline run identifier")
    status: ScenarioStatus = Field(description="Execution status")
    started_at: str = Field(description="ISO8601 start timestamp")
    completed_at: str | None = Field(default=None, description="ISO8601 completion timestamp")
    engine_version: str = Field(description="Phase 6 simulation engine version")
    config_version: str = Field(description="Simulator configuration version")
    warnings: list[str] = Field(default_factory=list, description="Execution warnings")
    provenance: dict[str, Any] = Field(description="Execution provenance tracking metadata")


class SimulatorRunSummarySchema(BaseModel):
    """Comprehensive summary view of a completed scenario run."""

    run: SimulatorRunResponseSchema = Field(description="Run execution record")
    scenario: SimulatorScenarioResponseSchema = Field(description="Scenario definition record")
    comparisons: list[SimulatorComparisonResponseSchema] = Field(description="Timestep comparison metrics")
    diagnostics: list[SimulatorDiagnosticResponseSchema] = Field(description="Hydro-solver diagnostic logs")
    artifacts: list[SimulatorArtifactResponseSchema] = Field(description="Raster output artifact metadata")
    governance_notice: str = Field(
        default="Simulator results are model-based what-if estimates and are not guarantees of real-world outcomes.",
        description="Mandatory governance disclaimer text"
    )
    conditional_benefit_notice: str = Field(
        default="Modeled benefit is conditional on the selected model assumptions, baseline inputs, and intervention representation.",
        description="Mandatory benefit disclaimer text"
    )


class SimulatorProvenanceResponseSchema(BaseModel):
    """Detailed audit provenance chain for a scenario execution."""

    scenario_id: str = Field(description="Scenario identifier")
    run_id: str | None = Field(default=None, description="Execution run identifier")
    baseline_run_id: str = Field(description="Baseline run identifier")
    rainfall_source: str = Field(description="Phase 3 rainfall data source")
    terrain_source: str = Field(description="Phase 4 terrain DEM data source")
    drainage_source: str = Field(description="Phase 5 drainage network data source")
    phase6_engine_version: str = Field(description="Phase 6 flood solver version")
    scenario_type: ScenarioType = Field(description="Scenario type")
    parameters: dict[str, Any] = Field(description="Scenario overlay parameters")
    assumptions: list[ScenarioAssumptionSchema] = Field(description="Recorded scenario assumptions")
    execution_timestamp: str | None = Field(default=None, description="Execution completion timestamp")
    provenance_hash: str = Field(description="SHA256 hash of complete provenance bundle")
