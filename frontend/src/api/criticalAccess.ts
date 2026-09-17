import { apiFetch } from './client';
import { RouteCandidate } from './routing';

export interface CriticalFacility {
  facility_id: string;
  name: string;
  category: string;
  latitude: number;
  longitude: number;
  source: string;
  source_id?: string | null;
  source_type: string;
  verification_status: string;
  operational_status: string;
  provider_mode: string;
  environment: string;
  provenance: Record<string, any>;
}

export interface ResponderOrigin {
  latitude: number;
  longitude: number;
  label?: string | null;
}

export interface SliceAccessibility {
  minutes_from_start: number;
  accessibility_status: string;
  primary_route_state: string;
  primary_route_peak_severity: string;
  acceptable_alternate_available: boolean;
  evaluation_notes: string;
}

export interface AlternateRouteSummary {
  route_id: string;
  summary: string;
  distance_m: number;
  estimated_duration_s: number;
  status: string;
  usable_travel_window_min: number;
  route_flood_onset_min?: number | null;
  recommendation_note: string;
  geometry_geojson?: {
    type: string;
    coordinates: [number, number][];
  } | null;
}

export interface CriticalAccessRequest {
  facility_id: string;
  responder_origin: ResponderOrigin;
  digital_twin_run_id?: string | null;
  departure_time?: string | null;
  critical_access_severity?: string;
  access_mode?: string;
}

export interface CriticalAccessResponse {
  access_run_id: string;
  facility: CriticalFacility;
  origin: ResponderOrigin;
  digital_twin_run_id: string;
  routing_run_id: string;
  current_access_status: string;
  modeled_loss_of_access_min?: number | null;
  modeled_loss_of_access_label?: string | null;
  time_to_loss_of_access_min?: number | null;
  accessibility_timeline: SliceAccessibility[];
  selected_route: RouteCandidate;
  alternate_route?: AlternateRouteSummary | null;
  recommendation: string;
  explanation: string;
  warnings: string[];
  provenance: Record<string, any>;
  facility_operational_status: string;
  facility_verification_status: string;
}

export async function fetchCriticalFacilities(params?: {
  category?: string;
  verification_status?: string;
  bbox?: string;
}): Promise<CriticalFacility[]> {
  const query = new URLSearchParams();
  if (params?.category) query.append('category', params.category);
  if (params?.verification_status) query.append('verification_status', params.verification_status);
  if (params?.bbox) query.append('bbox', params.bbox);

  const qs = query.toString();
  const path = qs ? `/api/v1/critical-access/facilities?${qs}` : '/api/v1/critical-access/facilities';
  return apiFetch<CriticalFacility[]>(path);
}

export async function fetchFacilityById(facilityId: string): Promise<CriticalFacility> {
  return apiFetch<CriticalFacility>(`/api/v1/critical-access/facilities/${facilityId}`);
}

export async function analyzeCriticalAccess(payload: CriticalAccessRequest): Promise<CriticalAccessResponse> {
  return apiFetch<CriticalAccessResponse>('/api/v1/critical-access/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}
