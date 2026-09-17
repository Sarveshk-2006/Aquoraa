import { apiFetch } from './client';

export interface DigitalTwinTimeSlice {
  run_id: string;
  timestamp_iso: string;
  timestamp_ist: string;
  minutes_from_start: number;
  slice_label: string;
  affected_cells_count: number;
  affected_area_km2: number;
  peak_severity: string;
  severity_distribution: Record<string, number>;
  onset_cells_count: number;
  input_completeness: string;
  uncertainty_level: string;
  cause_explanation: string;
  artifact_path: string;
}

export interface DigitalTwinSummary {
  run_id: string;
  study_area_id: string;
  status: string;
  created_at: string;
  simulation_start_time: string;
  horizon_minutes: number;
  timestep_minutes: number;
  total_timesteps: number;
  available_slices: number[];
  max_water_depth_m: number;
  peak_affected_area_km2: number;
  peak_time_minutes: number;
  physical_engine_version: string;
  ml_calibration_version?: string;
  ml_calibration_status: string;
  input_completeness: Record<string, string>;
  provenance: Record<string, any>;
}

export interface DigitalTwinRunResponse {
  run_id: string;
  study_area_id: string;
  status: string;
  started_at: string;
  completed_at?: string;
  simulation_start_time: string;
  horizon_minutes: number;
  timestep_minutes: number;
  total_timesteps: number;
  available_slices: number[];
  summary?: DigitalTwinSummary;
  time_slices: DigitalTwinTimeSlice[];
  output_directory: string;
  error_message?: string;
}

export interface CellInspectionResponse {
  run_id: string;
  grid_cell_id: string;
  minutes_from_start: number;
  timestamp_iso: string;
  latitude: number;
  longitude: number;
  elevation_m: number;
  water_depth_m: number;
  severity: string;
  rainfall_intensity_mm_hr: number;
  drainage_proxy_score: number;
  distance_to_waterway_m: number;
  physical_model_score: number;
  prototype_ml_score?: number;
  ml_status_tag: string;
  input_completeness: string;
  uncertainty_level: string;
  disclaimer: string;
}

export type CellDiagnosticDetail = CellInspectionResponse;

export async function fetchLatestDigitalTwinRun(): Promise<DigitalTwinRunResponse> {
  return apiFetch<DigitalTwinRunResponse>('/api/v1/digital-twin/runs/latest');
}

export async function createDigitalTwinRun(payload: {
  study_area_id?: string;
  start_time?: string;
  horizon_minutes?: number;
  timestep_minutes?: number;
}): Promise<DigitalTwinRunResponse> {
  return apiFetch<DigitalTwinRunResponse>('/api/v1/digital-twin/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function triggerDigitalTwinRun(payload?: any): Promise<DigitalTwinRunResponse> {
  return createDigitalTwinRun(payload || {});
}

export async function inspectCellDiagnostics(
  gridCellId: string,
  minutesFromStart: number = 60,
  runId: string = 'dt_demo_run'
): Promise<CellInspectionResponse> {
  return apiFetch<CellInspectionResponse>(
    `/api/v1/digital-twin/runs/${runId}/inspect?grid_cell_id=${gridCellId}&minutes_from_start=${minutesFromStart}`
  );
}

export async function fetchCellDiagnostics(
  gridCellId: string,
  minutesFromStart: number = 60,
  runId: string = 'dt_demo_run'
): Promise<CellInspectionResponse> {
  return inspectCellDiagnostics(gridCellId, minutesFromStart, runId);
}
