import { apiFetch } from './client';

export interface ObservationPayload {
  latitude: number;
  longitude: number;
  location_source?: string;
  observed_at?: string;
  source?: string;
  source_id?: string;
  observer_type?: string;
  observer_reference?: string;
  observation_type?: string;
  flood_presence?: string;
  water_depth_class?: string;
  road_passability?: string;
  description?: string;
  provenance?: Record<string, unknown>;
}

export interface ObservationResponse {
  observation_id: string;
  observation_type: string;
  latitude: number;
  longitude: number;
  location_source: string;
  observed_at: string | null;
  received_at: string;
  source: string;
  source_id: string | null;
  observer_type: string;
  observer_reference: string | null;
  flood_presence: string;
  water_depth_class: string;
  road_passability: string;
  description: string | null;
  media_count: number;
  verification_state: string;
  evidence_strength: string;
  incident_id: string | null;
  model_comparison_status: string;
  provenance: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface IncidentResponse {
  incident_id: string;
  latitude: number;
  longitude: number;
  first_observed_at: string | null;
  last_observed_at: string | null;
  observation_count: number;
  unique_source_count: number;
  verification_state: string;
  evidence_strength: string;
  status: string;
  contributing_observation_ids: string[];
  provenance: Record<string, unknown>;
}

export interface ComparisonResponse {
  comparison_id: string;
  observation_id: string;
  digital_twin_run_id: string;
  model_slice_minutes: number;
  observation_elapsed_minutes: number | null;
  observation_time: string | null;
  time_difference_minutes: number | null;
  spatial_distance_m: number;
  observation_state: string;
  model_state: string;
  comparison_status: string;
  evidence_strength: string;
  verification_state: string;
  explanation: string;
  warnings: string[];
  provenance: Record<string, unknown>;
}

export interface GroundTruthRunResponse {
  run_id: string;
  digital_twin_run_id: string | null;
  status: string;
  started_at: string;
  completed_at: string | null;
  observation_count: number;
  incident_count: number;
  comparison_count: number;
  provider_mode: string;
  warnings: string[];
  provenance: Record<string, unknown>;
}

export async function fetchObservations(): Promise<ObservationResponse[]> {
  return apiFetch<ObservationResponse[]>('/api/v1/ground-truth/observations');
}

export async function createObservation(payload: ObservationPayload): Promise<ObservationResponse> {
  return apiFetch<ObservationResponse>('/api/v1/ground-truth/observations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function uploadObservationMedia(observationId: string, file: File): Promise<Record<string, unknown>> {
  const formData = new FormData();
  formData.append('file', file);

  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  const res = await fetch(`${baseUrl}/api/v1/ground-truth/observations/${observationId}/media`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Upload failed with status ${res.status}`);
  }

  return res.json();
}

export async function fetchIncidents(): Promise<IncidentResponse[]> {
  return apiFetch<IncidentResponse[]>('/api/v1/ground-truth/incidents');
}

export async function triggerGroundTruthRun(providerMode = 'SYNTHETIC'): Promise<GroundTruthRunResponse> {
  return apiFetch<GroundTruthRunResponse>('/api/v1/ground-truth/runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider_mode: providerMode }),
  });
}

export async function fetchObservationComparison(observationId: string): Promise<ComparisonResponse> {
  return apiFetch<ComparisonResponse>(`/api/v1/ground-truth/observations/${observationId}/comparison`);
}
