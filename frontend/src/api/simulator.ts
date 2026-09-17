import { apiFetch } from './client';

export type ScenarioType =
  | 'RAINFALL_MULTIPLIER'
  | 'RAINFALL_ADDITION'
  | 'DRAINAGE_CAPACITY_REDUCTION'
  | 'DRAINAGE_CAPACITY_INCREASE'
  | 'DRAINAGE_NODE_INTERVENTION'
  | 'TEMPORARY_BARRIER'
  | 'STORAGE_INTERVENTION'
  | 'PUMP_OR_DEWATERING_SCENARIO'
  | 'COMBINED_SCENARIO';

export type ScenarioStatus =
  | 'DRAFT'
  | 'VALIDATED'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'UNSUPPORTED'
  | 'SCENARIO_INCOMPLETE';

export type OutcomeClassification =
  | 'IMPROVED'
  | 'NO_SIGNIFICANT_CHANGE'
  | 'WORSE'
  | 'INCONCLUSIVE';

export interface ScenarioAssumption {
  assumption_type: string;
  assumption_value: any;
  assumption_source: string;
  assumption_description: string;
}

export interface SimulatorScenarioCreatePayload {
  baseline_run_id: string;
  scenario_type: ScenarioType;
  parameters: Record<string, any>;
  assumptions?: ScenarioAssumption[];
  unknown_capacity_policy?: string;
}

export interface SimulatorScenario {
  scenario_id: string;
  baseline_run_id: string;
  scenario_type: ScenarioType;
  parameters: Record<string, any>;
  assumptions: ScenarioAssumption[];
  status: ScenarioStatus;
  provenance: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface SimulatorValidationResponse {
  scenario_id: string;
  is_valid: boolean;
  status: ScenarioStatus;
  rejection_reason?: string;
  warnings: string[];
  assumptions: ScenarioAssumption[];
}

export interface SimulatorArtifact {
  artifact_id: string;
  run_id: string;
  artifact_type: string;
  storage_reference: string;
  checksum: string;
  crs: string;
  transform: number[];
  width: number;
  height: number;
  nodata?: number;
  provenance: Record<string, any>;
}

export interface SimulatorComparison {
  comparison_id: string;
  run_id: string;
  slice_minutes: number;
  baseline_metrics: {
    flooded_cells_count: number;
    flooded_area_km2: number;
    high_severe_cells_count: number;
    high_severe_area_km2: number;
    max_depth_m: number;
  };
  scenario_metrics: {
    flooded_cells_count: number;
    flooded_area_km2: number;
    high_severe_cells_count: number;
    high_severe_area_km2: number;
    max_depth_m: number;
  };
  deltas: {
    flooded_cells_delta: number;
    flooded_area_delta_km2: number;
    flooded_area_pct_change: number;
    high_severe_cells_delta: number;
    high_severe_area_delta_km2: number;
  };
  outcome: OutcomeClassification;
  created_at: string;
}

export interface SimulatorDiagnostic {
  diagnostic_id: string;
  run_id: string;
  metric: string;
  value: number;
  status: string;
  message: string;
}

export interface SimulatorRunResponse {
  run_id: string;
  scenario_id: string;
  baseline_run_id: string;
  status: ScenarioStatus;
  started_at: string;
  completed_at?: string;
  engine_version: string;
  config_version: string;
  warnings: string[];
  provenance: Record<string, any>;
}

export interface SimulatorRunSummary {
  run: SimulatorRunResponse;
  scenario: SimulatorScenario;
  comparisons: SimulatorComparison[];
  diagnostics: SimulatorDiagnostic[];
  artifacts: SimulatorArtifact[];
  governance_notice: string;
  conditional_benefit_notice: string;
}

export interface SimulatorProvenance {
  scenario_id: string;
  run_id?: string;
  baseline_run_id: string;
  rainfall_source: string;
  terrain_source: string;
  drainage_source: string;
  phase6_engine_version: string;
  scenario_type: ScenarioType;
  parameters: Record<string, any>;
  assumptions: ScenarioAssumption[];
  execution_timestamp?: string;
  provenance_hash: string;
}

export async function createScenario(payload: SimulatorScenarioCreatePayload): Promise<SimulatorScenario> {
  return apiFetch<SimulatorScenario>('/api/v1/simulator/scenarios', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function validateScenario(scenarioId: string): Promise<SimulatorValidationResponse> {
  return apiFetch<SimulatorValidationResponse>(`/api/v1/simulator/scenarios/${scenarioId}/validate`, {
    method: 'POST',
  });
}

export async function runScenarioSimulation(scenarioId: string): Promise<SimulatorRunSummary> {
  return apiFetch<SimulatorRunSummary>(`/api/v1/simulator/scenarios/${scenarioId}/run`, {
    method: 'POST',
  });
}

export async function getScenarioSummary(runId: string): Promise<SimulatorRunSummary> {
  return apiFetch<SimulatorRunSummary>(`/api/v1/simulator/runs/${runId}/summary`);
}

export async function getScenarioProvenance(scenarioId: string): Promise<SimulatorProvenance> {
  return apiFetch<SimulatorProvenance>(`/api/v1/simulator/scenarios/${scenarioId}/provenance`);
}
