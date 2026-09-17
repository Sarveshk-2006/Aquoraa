import { apiFetch } from './client';

export interface InterventionCandidate {
  candidate_id: string;
  name: string;
  candidate_type: string;
  latitude: number;
  longitude: number;
  source: string;
  source_id?: string | null;
  source_type: string;
  verification_status: string;
  provider_mode: string;
  environment: string;
  affected_asset_type?: string | null;
  affected_asset_id?: string | null;
  summary: string;
  provenance: Record<string, any>;
}

export interface PriorityComponentBreakdown {
  flood_severity_score: number;
  time_to_threat_score: number;
  critical_access_score: number;
  route_impact_score: number;
  terrain_drainage_score: number;
  evidence_completeness_score: number;
  total_score: number;
  ranking_category: string;
}

export interface ProtectCityRecommendation {
  candidate: InterventionCandidate;
  priority: string;
  priority_score: number;
  priority_component_breakdown: PriorityComponentBreakdown;
  intervention_type: string;
  first_threat_minutes?: number | null;
  first_high_severity_minutes?: number | null;
  peak_severity: string;
  peak_severity_minutes?: number | null;
  expected_benefit: string;
  feasibility_status: string;
  uncertainty_status: string;
  affected_route_count: number;
  affected_critical_facility_count: number;
  affected_facility_ids: string[];
  route_impact_context: string;
  critical_access_context: string;
  drainage_context: string;
  terrain_context: string;
  explanation: string;
  warnings: string[];
  provenance: Record<string, any>;
}

export interface ProtectCityRequest {
  digital_twin_run_id?: string | null;
  routing_run_id?: string | null;
  critical_access_run_id?: string | null;
  minimum_priority?: string;
  candidate_types?: string[] | null;
  priority_limit?: number;
  time_horizon_minutes?: number | null;
}

export interface ProtectCityResponse {
  run_id: string;
  digital_twin_run_id: string;
  routing_run_id?: string | null;
  critical_access_run_id?: string | null;
  generated_at: string;
  total_candidates: number;
  recommendations: ProtectCityRecommendation[];
  priority_counts: Record<string, number>;
  warnings: string[];
  provenance: Record<string, any>;
  uncertainty_summary: Record<string, any>;
}

export async function fetchInterventionCandidates(params?: {
  candidate_type?: string;
  verification_status?: string;
  provider_mode?: string;
}): Promise<InterventionCandidate[]> {
  const query = new URLSearchParams();
  if (params?.candidate_type) query.append('candidate_type', params.candidate_type);
  if (params?.verification_status) query.append('verification_status', params.verification_status);
  if (params?.provider_mode) query.append('provider_mode', params.provider_mode);

  const qs = query.toString();
  const path = qs ? `/api/v1/protect-city/candidates?${qs}` : '/api/v1/protect-city/candidates';
  return apiFetch<InterventionCandidate[]>(path);
}

export async function fetchInterventionCandidateById(candidateId: string): Promise<InterventionCandidate> {
  return apiFetch<InterventionCandidate>(`/api/v1/protect-city/candidates/${candidateId}`);
}

export async function analyzeProtectCity(payload: ProtectCityRequest): Promise<ProtectCityResponse> {
  return apiFetch<ProtectCityResponse>('/api/v1/protect-city/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function fetchProtectCityRuns(): Promise<ProtectCityResponse[]> {
  return apiFetch<ProtectCityResponse[]>('/api/v1/protect-city/runs');
}

export async function fetchLatestProtectCityRun(): Promise<ProtectCityResponse> {
  return apiFetch<ProtectCityResponse>('/api/v1/protect-city/runs/latest');
}

export async function fetchProtectCityRunById(runId: string): Promise<ProtectCityResponse> {
  return apiFetch<ProtectCityResponse>(`/api/v1/protect-city/runs/${runId}`);
}

export async function fetchProtectCityRunRecommendations(runId: string): Promise<ProtectCityRecommendation[]> {
  return apiFetch<ProtectCityRecommendation[]>(`/api/v1/protect-city/runs/${runId}/recommendations`);
}
